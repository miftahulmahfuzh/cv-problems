#!/usr/bin/env python3
"""Regenerate worklog.html from input/ and output/.

Inputs are listed once, sorted by name. Outputs are listed newest-first by
mtime. Captions for outputs come from output/captions.json ({filename: text}).
Run after writing any new image into output/, then republish worklog.html.
"""
import base64, json, mimetypes, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"}


def dims(p):
    from PIL import Image
    with Image.open(p) as im:
        return im.size, im.mode


def human(n):
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def data_uri(p):
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def collect(d):
    if not d.is_dir():
        return []
    return [p for p in d.iterdir() if p.suffix.lower() in EXTS and p.is_file()]


def figure(p, caption=None):
    (w, h), mode = dims(p)
    meta = [
        ("file", p.name),
        ("size", f"{w} x {h} px"),
        ("mode", mode),
        ("bytes", human(p.stat().st_size)),
    ]
    cells = "".join(
        f'<div class="m"><span class="k">{k}</span><span class="v">{v}</span></div>'
        for k, v in meta
    )
    cap = f'<p class="caption">{caption}</p>' if caption else ""
    sid = p.name.replace(".", "-")
    return f"""<figure class="plate" id="fig-{sid}">
  <div class="plate-head">
    <div class="meta">{cells}</div>
    <div class="zoom" role="group" aria-label="Zoom {p.name}">
      <button type="button" class="on" data-z="fit" data-t="{sid}" id="z-fit-{sid}">Fit</button>
      <button type="button" data-z="1" data-t="{sid}" id="z-1-{sid}">100%</button>
      <button type="button" data-z="2" data-t="{sid}" id="z-2-{sid}">200%</button>
    </div>
  </div>
  {cap}
  <div class="mat" data-mat="{sid}">
    <img src="{data_uri(p)}" alt="{p.name}" width="{w}" height="{h}" data-img="{sid}">
  </div>
</figure>"""


def main():
    inputs = sorted(collect(ROOT / "input"), key=lambda p: p.name)
    outs = sorted(collect(ROOT / "output"), key=lambda p: p.stat().st_mtime, reverse=True)
    capfile = ROOT / "output" / "captions.json"
    caps = json.loads(capfile.read_text()) if capfile.exists() else {}

    in_html = "\n".join(figure(p) for p in inputs) or '<p class="empty">No images in input/.</p>'
    out_html = "\n".join(figure(p, caps.get(p.name)) for p in outs) or \
        '<p class="empty">Nothing written to output/ yet.</p>'

    html = TEMPLATE.replace("{{INPUTS}}", in_html).replace("{{OUTPUTS}}", out_html) \
                   .replace("{{NIN}}", str(len(inputs))).replace("{{NOUT}}", str(len(outs)))
    (ROOT / "worklog.html").write_text(html)
    print(f"worklog.html: {len(inputs)} input(s), {len(outs)} output(s), "
          f"{human((ROOT / 'worklog.html').stat().st_size)}")


TEMPLATE = r"""<title>Drill Worklog 2026-10-23-1</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
  :root {
    --paper: #f4f5f3;
    --panel: #fbfbfa;
    --ink: #16191c;
    --ink-2: #5c646c;
    --rule: #ccd1d2;
    --accent: #1d5f80;
    --mat: #ffffff;
    --mat-rule: #d8dcdc;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --paper: #14181a;
      --panel: #1b2023;
      --ink: #e6eaea;
      --ink-2: #93a0a4;
      --rule: #2e373b;
      --accent: #6fb5d6;
      --mat: #f2f3f1;
      --mat-rule: #39444a;
    }
  }
  :root[data-theme="dark"] {
    --paper: #14181a;
    --panel: #1b2023;
    --ink: #e6eaea;
    --ink-2: #93a0a4;
    --rule: #2e373b;
    --accent: #6fb5d6;
    --mat: #f2f3f1;
    --mat-rule: #39444a;
  }

  body {
    background: var(--paper);
    color: var(--ink);
    font-family: "IBM Plex Sans", system-ui, sans-serif;
    font-size: 15px;
    line-height: 1.5;
  }
  .wrap {
    max-width: 1180px;
    margin: 0 auto;
    padding-inline: 20px;
    padding-block: 28px 56px;
    display: flex;
    flex-direction: column;
    gap: 28px;
  }

  header.sheet {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 8px 20px;
    border-bottom: 2px solid var(--ink);
    padding-bottom: 10px;
  }
  header.sheet h1 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    letter-spacing: -0.01em;
  }
  header.sheet .run {
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-size: 12px;
    color: var(--ink-2);
    letter-spacing: 0.04em;
  }

  h2.section {
    margin: 0 0 2px;
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--accent);
    display: flex;
    align-items: center;
    gap: 10px;
  }
  h2.section::after {
    content: "";
    flex: 1;
    height: 1px;
    background: var(--rule);
  }
  section {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .count {
    color: var(--ink-2);
    font-weight: 400;
    letter-spacing: 0.08em;
  }

  .plate {
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .plate-head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px 18px;
  }
  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 18px;
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-size: 12.5px;
    font-variant-numeric: tabular-nums;
  }
  .m { display: flex; gap: 6px; align-items: baseline; }
  .k { color: var(--ink-2); letter-spacing: 0.06em; }
  .v { color: var(--ink); font-weight: 500; }

  .zoom { display: flex; }
  .zoom button {
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-size: 11.5px;
    letter-spacing: 0.06em;
    padding: 4px 11px;
    background: var(--panel);
    color: var(--ink-2);
    border: 1px solid var(--rule);
    margin-left: -1px;
    cursor: pointer;
  }
  .zoom button:first-child { margin-left: 0; }
  .zoom button:hover { color: var(--ink); }
  .zoom button.on {
    background: var(--accent);
    border-color: var(--accent);
    color: var(--paper);
  }
  .zoom button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

  .caption {
    margin: 0;
    max-width: 68ch;
    font-size: 13.5px;
    color: var(--ink-2);
  }

  .mat {
    background: var(--mat);
    border: 1px solid var(--mat-rule);
    overflow: auto;
    line-height: 0;
  }
  .mat img {
    display: block;
    width: 100%;
    height: auto;
    max-width: 100%;
  }
  .mat[data-fit="px"] img { width: auto; max-width: none; }

  .empty {
    margin: 0;
    padding: 22px;
    border: 1px dashed var(--rule);
    color: var(--ink-2);
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-size: 13px;
    background: var(--panel);
  }
</style>

<div class="wrap">
  <header class="sheet">
    <h1>Drill Worklog</h1>
    <span class="run">RUN 2026-10-23-1</span>
  </header>

  <section>
    <h2 class="section">Input <span class="count">{{NIN}}</span></h2>
    {{INPUTS}}
  </section>

  <section>
    <h2 class="section">Outputs <span class="count">{{NOUT}}</span></h2>
    {{OUTPUTS}}
  </section>
</div>

<script>
  document.querySelectorAll(".zoom button").forEach(function (b) {
    b.addEventListener("click", function () {
      var t = b.dataset.t;
      var mat = document.querySelector('[data-mat="' + t + '"]');
      var img = document.querySelector('[data-img="' + t + '"]');
      document.querySelectorAll('.zoom button[data-t="' + t + '"]').forEach(function (o) {
        o.classList.toggle("on", o === b);
      });
      if (b.dataset.z === "fit") {
        mat.removeAttribute("data-fit");
        img.style.width = "";
      } else {
        mat.dataset.fit = "px";
        img.style.width = img.naturalWidth * parseFloat(b.dataset.z) + "px";
      }
    });
  });
</script>
"""

if __name__ == "__main__":
    sys.exit(main())
