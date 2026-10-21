import { spawn } from "node:child_process";
import { readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [, , svgPath, outPath, cols = "34", aspect = "0.5"] = process.argv;
const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const PORT = 9334;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const svg = readFileSync(svgPath, "utf8");
const viewBox = svg.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
const paths = [...svg.matchAll(/<path[^>]* d="([^"]+)"/g)].map((m) => m[1]);
const S_PATHS = new Set([0, 1, 2]);
const groups = { p: paths.filter((_, i) => !S_PATHS.has(i)), s: paths.filter((_, i) => S_PATHS.has(i)) };

const edge = spawn(EDGE, [
  "--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "edge-"))}`,
  "--no-first-run", "--no-default-browser-check", "--disable-gpu",
], { stdio: "ignore" });

let version;
for (let i = 0; i < 40 && !version; i++) {
  try { version = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json(); } catch { await sleep(250); }
}
const ws = new WebSocket(version.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let seq = 0;
const pending = new Map();
ws.addEventListener("message", (e) => {
  const msg = JSON.parse(e.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
});
const send = (method, params = {}, sessionId) => new Promise((resolve) => {
  const id = ++seq;
  pending.set(id, resolve);
  ws.send(JSON.stringify({ id, method, params, sessionId }));
});

const { result: { targetId } } = await send("Target.createTarget", { url: "about:blank" });
const { result: { sessionId } } = await send("Target.attachToTarget", { targetId, flatten: true });

const rasterize = (groups, viewBox, cols, aspect) => {
  const [vx, vy, vw, vh] = viewBox;
  const sub = 6;
  const cellW = vw / cols;
  const cellH = cellW / aspect;
  const rows = Math.ceil(vh / cellH);
  const W = cols * sub;
  const H = rows * sub * 2;
  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d");
  const masks = {};
  for (const [name, ds] of Object.entries(groups)) {
    ctx.clearRect(0, 0, W, H);
    const sx = W / vw;
    const sy = H / (rows * cellH);
    ctx.setTransform(sx, 0, 0, sy, -vx * sx, -vy * sy);
    ctx.fillStyle = "#000";
    for (const d of ds) ctx.fill(new Path2D(d), "nonzero");
    masks[name] = ctx.getImageData(0, 0, W, H).data;
  }
  const ramp = " .:-=+*#%@";
  const out = [];
  for (let r = 0; r < rows; r++) {
    let chars = "";
    let kinds = "";
    for (let c = 0; c < cols; c++) {
      const cover = {};
      for (const name of Object.keys(masks)) {
        let n = 0;
        for (let y = 0; y < sub * 2; y++) for (let x = 0; x < sub; x++) {
          const idx = ((r * sub * 2 + y) * W + (c * sub + x)) * 4 + 3;
          if (masks[name][idx] > 127) n++;
        }
        cover[name] = n / (sub * sub * 2);
      }
      const kind = cover.p >= cover.s ? "p" : "s";
      const v = Math.max(cover.p, cover.s);
      const ch = v < 0.08 ? " " : ramp[Math.min(ramp.length - 1, Math.round(v * (ramp.length - 1)))];
      chars += ch;
      kinds += ch === " " ? " " : kind;
    }
    out.push({ chars, kinds });
  }
  return out;
};

const res = await send("Runtime.evaluate", {
  expression: `JSON.stringify((${rasterize.toString()})(${JSON.stringify(groups)}, ${JSON.stringify(viewBox)}, ${Number(cols)}, ${Number(aspect)}))`,
  returnByValue: true,
}, sessionId);
if (res.result.exceptionDetails) { console.error(JSON.stringify(res.result.exceptionDetails)); process.exit(1); }
const rows = JSON.parse(res.result.result.value);
while (rows.length && !rows.at(-1).chars.trim()) rows.pop();
while (rows.length && !rows[0].chars.trim()) rows.shift();
writeFileSync(outPath, JSON.stringify(rows, null, 1));
for (const r of rows) console.log(r.chars + "   " + r.kinds);
ws.close();
edge.kill();
process.exit(0);
