import base64
import json
import sys
import textwrap
from itertools import groupby
from pathlib import Path
from xml.sax.saxutils import escape

ASCII_JSON, OUT, FONTS = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])

FONT_FACES = "".join(
    f"@font-face{{font-family:'JBM';font-weight:{w};src:url(data:font/woff2;base64,"
    f"{base64.b64encode((FONTS / f'jbm-{w}.woff2').read_bytes()).decode()}) format('woff2')}}"
    for w in (400, 700))
FONT = "'JBM', ui-monospace, SFMono-Regular, 'Cascadia Code', Consolas, 'Liberation Mono', Menlo, monospace"

TN = dict(bg="#1a1b27", panel="#16161e", border="#2f334d", fg="#c0caf5", muted="#565f89",
          key="#70a5fd", title="#ff2e97", p="#ff2e97", s="#bb9af7",
          blocks=["#414868", "#f7768e", "#9ece6a", "#e0af68", "#7aa2f7", "#bb9af7", "#7dcfff", "#c0caf5"])

FIELDS = [
    ("Location", "Ferrara, Italy"),
    ("Languages", "Italian (native), English (B2-C1)"),
    ("Study", "Computer Science @ UNIFE"),
    ("OS", "Unraid"),
    ("Network", "UniFi, Tailscale, Pangolin tunnel on a VPS"),
    ("Cloud", "Nextcloud + Collabora"),
    ("Photos", "Immich"),
    ("Passwords", "Vaultwarden"),
    ("Smart home", "Home Assistant, Zigbee2MQTT, ESPHome, Frigate"),
    ("Media", "Plex, Jellyfin"),
    ("Status", "open to opportunities"),
]

ABOUT = ("I'm a tech enthusiast: if there's a new technology around, I want to try it. "
         "Pretty much everything I use day to day runs on my homelab, and that's where my code comes from too: "
         "small tools, and fixes I send back to the open-source projects I run.")

INTERESTS = [
    ("tech", "open source · Linux · Android"),
    ("homelab", "self-hosting · networking · home automation"),
    ("free time", "sci-fi · movies & TV · gaming"),
]

LOGO = json.loads(ASCII_JSON.read_text(encoding="utf-8"))
W = 880
LH = 23
SIZE = 14


def css(n, start, step=0.1):
    rules = [FONT_FACES,
             ".r{opacity:0;animation:in .35s ease-out forwards}",
             "@keyframes in{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:none}}",
             ".cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}",
             ".logo{animation:glow 4s ease-in-out infinite}@keyframes glow{50%{opacity:.75}}"]
    rules += [f".d{i}{{animation-delay:{start + i * step:.2f}s}}" for i in range(n)]
    return "".join(rules)


def prompt(p, cmd=""):
    return (f'<tspan fill="{p["title"]}">filippo@homelab</tspan><tspan fill="{p["fg"]}">:</tspan>'
            f'<tspan fill="{p["key"]}">~</tspan><tspan fill="{p["fg"]}">$ {escape(cmd)}</tspan>')


def logo(p, x, y, lh, size):
    rows = []
    for n, row in enumerate(LOGO):
        spans = "".join(f'<tspan fill="{p.get(kind, p["muted"])}">{escape("".join(ch for ch, _ in run))}</tspan>'
                        for kind, run in groupby(zip(row["chars"], row["kinds"]), key=lambda t: t[1]))
        rows.append(f'<text x="{x}" y="{y + n * lh}" font-size="{size}" xml:space="preserve">{spans}</text>')
    return f'<g class="logo">{"".join(rows)}</g>'


class Lines:
    def __init__(self):
        self.parts = []
        self.n = 0

    def add(self, x, y, inner, **attrs):
        extra = "".join(f' {k.replace("__", ":").replace("_", "-")}="{v}"' for k, v in attrs.items())
        self.parts.append(f'<text class="r d{self.n}" x="{x}" y="{y}" font-size="{SIZE}"{extra}>{inner}</text>')
        self.n += 1

    def blocks(self, p, x, y):
        for j, c in enumerate(p["blocks"]):
            self.parts.append(f'<rect class="r d{self.n}" x="{x + j * 26}" y="{y - SIZE}" width="24" height="{SIZE + 4}" fill="{c}"/>')
        self.n += 1

    def svg(self):
        return "".join(self.parts)


def neofetch_info(p, out, x, y):
    out.add(x, y, f'<tspan fill="{p["title"]}">filippo</tspan><tspan fill="{p["fg"]}">@</tspan>'
                  f'<tspan fill="{p["title"]}">homelab</tspan>', font_weight=700)
    out.add(x, y + LH, "-" * 15, fill=p["muted"])
    y += 2 * LH
    for k, v in FIELDS:
        out.add(x, y, f'<tspan fill="{p["key"]}" font-weight="700">{escape(k)}</tspan><tspan fill="{p["fg"]}">: {escape(v)}</tspan>')
        y += LH
    out.blocks(p, x, y + LH * 0.4)


def about_block(p, out, x, y):
    out.add(x, y, prompt(p, "cat about.md"))
    y += LH * 1.5
    for line in textwrap.wrap(ABOUT, 92):
        out.add(x, y, escape(line), fill=p["fg"])
        y += LH
    y += LH * 0.5
    out.add(x, y, prompt(p, "cat interests.md"))
    y += LH * 1.5
    for k, v in INTERESTS:
        out.add(x, y, f'<tspan fill="{p["key"]}" font-weight="700">{escape(k.ljust(11))}</tspan>'
                      f'<tspan fill="{p["fg"]}">{escape(v)}</tspan>', xml__space="preserve")
        y += LH
    return y


def frame(p, h, title, body, n, start):
    dots = "".join(f'<circle cx="{22 + i * 20}" cy="20" r="6" fill="{c}"/>' for i, c in enumerate(["#f7768e", "#e0af68", "#9ece6a"]))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h:.0f}" viewBox="0 0 {W} {h:.0f}" font-family="{FONT}">'
            f'<style>{css(n, start)}</style>'
            f'<rect x="1" y="1" width="{W - 2}" height="{h - 2:.0f}" rx="12" fill="{p["bg"]}" stroke="{p["border"]}"/>'
            f'<path d="M1 13a12 12 0 0 1 12-12h{W - 26}a12 12 0 0 1 12 12v27H1z" fill="{p["panel"]}"/>'
            f'<line x1="1" y1="40" x2="{W - 1}" y2="40" stroke="{p["border"]}"/>{dots}'
            f'<text x="{W / 2}" y="25" font-size="13" fill="{p["muted"]}" text-anchor="middle">{escape(title)}</text>'
            f'{body}</svg>')


def window(p):
    out = Lines()
    out.parts.append(f'<text x="20" y="70" font-size="{SIZE}">{prompt(p, "neofetch")}</text>')
    neofetch_info(p, out, 350, 112)
    y = about_block(p, out, 20, 108 + len(LOGO) * 16.5 + 40) + LH * 0.5
    out.add(20, y + 10, prompt(p) + f'<tspan class="cur" fill="{p["fg"]}">█</tspan>')
    body = logo(p, 22, 108, 16.5, 12) + out.svg()
    return frame(p, y + 36, "filippo@homelab: ~", body, out.n, 0.6)


svg = window(TN)
OUT.write_text(svg, encoding="utf-8", newline="\n")
print(OUT, len(svg))
