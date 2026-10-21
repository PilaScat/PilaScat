# Profilo GitHub: come è fatto e come si aggiorna

Il repo `PilaScat/PilaScat` è il README del profilo GitHub. Tutto quello che si vede sta in
[`README.md`](../README.md), tranne il terminale (`assets/neofetch.svg`) e il serpente.

## Regole del contenuto

- Ogni informazione compare **in un posto solo**: dati personali, servizi di casa, about e
  interessi nel terminale; competenze nei badge; contatti in "Get in touch".
- Tutto in Tokyo Night (`#1a1b27`, blu `#70a5fd`, viola `#bb9af7`) con il magenta del logo
  (`#ff2e97`), anche quando GitHub è in tema chiaro.

## Il terminale

GitHub mostra il testo del README sempre col suo font: per usare JetBrains Mono, about e
interessi stanno dentro l'SVG del terminale, col font incorporato in base64 (`scripts/fonts`,
licenza OFL). L'`alt` dell'immagine nel README ripete il testo, per chi non vede le immagini.

Testi e campi stanno in `scripts/neofetch.py` (`FIELDS`, `ABOUT`, `INTERESTS`). Dopo averli
cambiati, dalla radice del repo:

```
python scripts/neofetch.py scripts/logo-ascii.json assets/neofetch.svg scripts/fonts
```

e si aggiorna l'`alt` nel README.

Il logo in ASCII (`scripts/logo-ascii.json`) viene da `scripts/logo.svg` (il logo degli asset
Twitch) rasterizzato con Edge headless; si rifà solo se cambia il logo:

```
node scripts/logo2ascii.mjs scripts/logo.svg scripts/logo-ascii.json 40 0.5
```

I primi tre path del logo sono la S (viola), gli altri la P e le schegge (magenta).

## Il serpente

`.github/workflows/snake.yml` genera `github-snake-dark.svg` ogni notte alle 03:00 UTC e lo
pubblica sul ramo `output`; parte anche a mano (`workflow_dispatch`).

## Servizi esterni, cose da sapere

- **github-readme-stats** (istanza pubblica): `include_all_commits=true` la manda in
  "Something went wrong!", quindi non si usa.
- **github-readme-activity-graph**: l'istanza pubblica è disattivata (402).
- **simple-icons** non ha più Azure, AWS, LinkedIn né C#: per AWS, C# e LinkedIn il logo dei
  badge è l'icona di skillicons.dev in base64 nel parametro `logo`.
- Nelle catture headless, header, stats e streak sembrano vuoti: sono animazioni ferme al primo
  fotogramma, nel browser si vedono.
