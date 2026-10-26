"""Regenerate worklog.html: every input embedded, every output embedded newest-first."""
import base64, glob, io, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))

# newest first; each output gets a one-line caption saying what it shows
OUTPUTS = [
    ("shapes_annotated.png",
     "Every counted blob outlined in red and indexed. 6/6 — the arrow's notch is "
     "traced correctly, nothing double-counted, nothing missed."),
]

RASTER = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp"}


def raster(path, caption=None):
    with Image.open(path) as im:
        w, h, mode = im.width, im.height, im.mode
    ext = os.path.splitext(path)[1].lower()
    mime = MIME.get(ext)
    if mime is None:
        with Image.open(path) as im:
            buf = io.BytesIO(); im.convert("RGB").save(buf, "PNG")
            raw, mime = buf.getvalue(), "image/png"
    else:
        raw = open(path, "rb").read()
    return dict(label=os.path.basename(path),
                meta=f"{w} x {h} px &middot; {mode} &middot; {len(raw)/1024:.0f} KB",
                w=w, h=h, mime=mime, b64=base64.b64encode(raw).decode(),
                caption=caption)


def pdf_pages(path):
    import fitz
    doc, name, out = fitz.open(path), os.path.basename(path), []
    for i, page in enumerate(doc):
        pm = page.get_pixmap(dpi=150)
        raw = pm.tobytes("png")
        out.append(dict(
            label=f"{name} &mdash; page {i+1}/{len(doc)}",
            meta=f"{pm.width} x {pm.height} px @150dpi &middot; "
                 f"page {page.rect.width:.0f} x {page.rect.height:.0f} pt &middot; {len(raw)/1024:.0f} KB",
            w=pm.width, h=pm.height, mime="image/png",
            b64=base64.b64encode(raw).decode(), caption=None))
    doc.close()
    return out


inputs = []
for p in sorted(glob.glob(os.path.join(HERE, "input", "*"))):
    ext = os.path.splitext(p)[1].lower()
    if ext in RASTER:
        inputs.append(raster(p))
    elif ext == ".pdf":
        inputs.extend(pdf_pages(p))

outputs = [raster(os.path.join(HERE, "output", fn), cap)
           for fn, cap in OUTPUTS if os.path.exists(os.path.join(HERE, "output", fn))]


def figure(it, idx):
    cap = f'\n      <p class="cap">{it["caption"]}</p>' if it["caption"] else ""
    return f"""    <figure class="asset">
      <figcaption>
        <span class="fname">{it['label']}</span>
        <span class="fmeta">{it['meta']}</span>
        <span class="zoom" role="group" aria-label="zoom {it['label']}">
          <button type="button" id="z{idx}a" class="zb is-on" data-t="{idx}" data-s="1">1&times;</button>
          <button type="button" id="z{idx}b" class="zb" data-t="{idx}" data-s="2">2&times;</button>
          <button type="button" id="z{idx}c" class="zb" data-t="{idx}" data-s="4">4&times;</button>
        </span>
      </figcaption>
      <div class="mat" id="mat{idx}">
        <img id="img{idx}" src="data:{it['mime']};base64,{it['b64']}" width="{it['w']}" height="{it['h']}" alt="{it['label']}">
      </div>{cap}
    </figure>"""


HTML = """<title>Drill Worklog 2026-10-26-3</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
  :root {
    --ground:#f2f2ef; --surface:#ffffff; --mat:#e7e7e2; --ink:#1a1c1f;
    --muted:#6a6f76; --rule:#d3d4ce; --accent:#2f6d8c; --accent-ink:#ffffff;
    --grid:rgba(26,28,31,.07);
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --ground:#141619; --surface:#1c1f23; --mat:#0e1013; --ink:#e4e6e8;
      --muted:#8d939b; --rule:#2e3338; --accent:#6fb4d2; --accent-ink:#10181c;
      --grid:rgba(228,230,232,.07);
    }
  }
  :root[data-theme="dark"] {
    --ground:#141619; --surface:#1c1f23; --mat:#0e1013; --ink:#e4e6e8;
    --muted:#8d939b; --rule:#2e3338; --accent:#6fb4d2; --accent-ink:#10181c;
    --grid:rgba(228,230,232,.07);
  }
  body { background:var(--ground); color:var(--ink);
    font-family:"IBM Plex Sans",system-ui,-apple-system,sans-serif;
    font-size:15px; line-height:1.5; }
  .wrap { max-width:1120px; margin:0 auto; padding-block:28px 64px;
    padding-left:20px; padding-right:20px; display:flex; flex-direction:column; gap:28px; }
  header.top { display:flex; flex-direction:column; gap:4px;
    border-bottom:1px solid var(--rule); padding-bottom:16px; }
  header.top h1 { margin:0; font-size:1.3rem; font-weight:600; letter-spacing:-.01em; }
  header.top .path { font-family:"IBM Plex Mono",ui-monospace,monospace;
    font-size:.78rem; color:var(--muted); }
  h2.sec { margin:0; font-family:"IBM Plex Mono",ui-monospace,monospace;
    font-size:.72rem; font-weight:600; letter-spacing:.14em; text-transform:uppercase;
    color:var(--muted); display:flex; align-items:center; gap:12px; }
  h2.sec::after { content:""; flex:1; height:1px; background:var(--rule); }
  section { display:flex; flex-direction:column; gap:14px; }
  .asset { margin:0; background:var(--surface); border:1px solid var(--rule);
    display:flex; flex-direction:column; }
  .asset figcaption { display:flex; flex-wrap:wrap; align-items:baseline; gap:6px 14px;
    padding:9px 12px; border-bottom:1px solid var(--rule);
    font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.78rem; }
  .fname { font-weight:600; }
  .fmeta { color:var(--muted); font-variant-numeric:tabular-nums; }
  .zoom { margin-left:auto; display:flex; gap:4px; }
  .zb { font:inherit; font-size:.72rem; padding:2px 8px; border:1px solid var(--rule);
    background:transparent; color:var(--muted); cursor:pointer; border-radius:2px; }
  .zb:hover { color:var(--ink); border-color:var(--muted); }
  .zb.is-on { background:var(--accent); border-color:var(--accent); color:var(--accent-ink); }
  .zb:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
  .mat { background-color:var(--mat);
    background-image:linear-gradient(var(--grid) 1px,transparent 1px),
                     linear-gradient(90deg,var(--grid) 1px,transparent 1px);
    background-size:25px 25px; overflow:auto; padding:14px;
    display:flex; justify-content:center; }
  .mat img { display:block; max-width:100%; height:auto; }
  .mat.is-zoomed { justify-content:flex-start; }
  .mat.is-zoomed img { max-width:none; image-rendering:pixelated; }
  .cap { margin:0; padding:9px 12px; border-top:1px solid var(--rule);
    color:var(--muted); font-size:.82rem; line-height:1.45; }
  .verdict { border:1px solid var(--rule); border-left:3px solid var(--accent);
    background:var(--surface); padding:14px 16px; display:flex;
    flex-direction:column; gap:6px; }
  .verdict .line { font-weight:600; font-size:1.02rem; }
  .verdict .sub { color:var(--muted); font-size:.88rem; }
  blockquote.brief { margin:0; background:var(--surface); border:1px solid var(--rule);
    border-left:3px solid var(--muted); padding:14px 16px; white-space:pre-wrap;
    font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.82rem; line-height:1.6; }
  table.gt { width:100%; border-collapse:collapse; background:var(--surface);
    border:1px solid var(--rule); font-size:.86rem; }
  table.gt th, table.gt td { text-align:left; padding:8px 11px;
    border-bottom:1px solid var(--rule); vertical-align:top; }
  table.gt th { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.7rem;
    letter-spacing:.1em; text-transform:uppercase; color:var(--muted); font-weight:600; }
  table.gt tr:last-child td { border-bottom:0; }
  table.gt td.num { font-variant-numeric:tabular-nums; }
  .tablewrap { overflow-x:auto; }
  ul.scores { list-style:none; margin:0; padding:0; display:grid;
    grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:7px; }
  ul.scores li { display:flex; align-items:baseline; gap:9px; background:var(--surface);
    border:1px solid var(--rule); padding:7px 11px; font-size:.86rem; }
  ul.scores .dim { flex:1; }
  .pill { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.66rem;
    letter-spacing:.07em; text-transform:uppercase; padding:2px 7px; border-radius:2px;
    border:1px solid currentColor; white-space:nowrap; }
  .s-strong { color:#2e7d5b; } .s-adequate { color:#9a6b1e; }
  .s-weak { color:#b03a34; } .s-none { color:var(--muted); }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .s-strong{color:#6fcfa0}
    :root:not([data-theme="light"]) .s-adequate{color:#d6a44a}
    :root:not([data-theme="light"]) .s-weak{color:#e8766e} }
  :root[data-theme="dark"] .s-strong{color:#6fcfa0}
  :root[data-theme="dark"] .s-adequate{color:#d6a44a}
  :root[data-theme="dark"] .s-weak{color:#e8766e}
  ol.carry { margin:0; padding-left:1.25em; display:flex; flex-direction:column; gap:9px; }
  ol.carry li { padding-left:4px; }
  ol.carry b { font-weight:600; }
  p.note { margin:0; color:var(--muted); font-size:.88rem; }
  .empty { border:1px dashed var(--rule); padding:22px 16px; text-align:center;
    color:var(--muted); font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.78rem; }
</style>

<div class="wrap">
  <header class="top">
    <h1>Drill Worklog 2026-10-26-3</h1>
    <span class="path">/home/miftah/cv-problems/.runs/2026-10-26-3</span>
  </header>

  <section>
    <h2 class="sec">Inputs</h2>
__INPUTS__
  </section>

  <section>
    <h2 class="sec">Outputs</h2>
__OUTPUTS__
  </section>

  <section>
    <h2 class="sec">The brief &mdash; as given</h2>
    <blockquote class="brief">Take a look at `sample_14.png`. Give me a one-line description of what it shows,
and an exact count of how many shapes are in it.

Write `output/description.json`: `{"caption": "...", "shape_count": N}`. 25
minutes, starting now.</blockquote>
    <p class="note">Archetype #8 &mdash; caption / VQA with a VLM, tier 3. One fork left open:
    how to produce either number was deliberately unstated.</p>
  </section>

  <section>
    <h2 class="sec">Ground truth vs what was produced</h2>
    <div class="tablewrap"><table class="gt">
      <tr><th>Item</th><th>Ground truth</th><th>Produced</th><th></th></tr>
      <tr><td>shape_count</td><td class="num">6</td><td class="num">6</td><td>&#9989;</td></tr>
      <tr><td>Count method</td><td>anything deterministic / verifiable</td>
          <td>HSV S&ge;60 &or; V&le;110 mask &rarr; RETR_EXTERNAL &rarr; 6 contours, 0 rejected</td><td>&#9989;</td></tr>
      <tr><td>Independent recount<br><span class="sub">this session, Otsu not HSV</span></td>
          <td class="num">[4,4,8,4,3,8]</td><td class="num">[4,4,8,4,3,8]</td><td>&#9989;</td></tr>
      <tr><td>Caption text</td><td>any plausible one-liner</td>
          <td>&ldquo;A plain light background with six flat-coloured geometric shapes&hellip;&rdquo;</td><td>&#9989;</td></tr>
      <tr><td>Caption <i>provenance</i></td><td>generated with an actual model call</td>
          <td>f-string in build_caption(); no model loaded all session</td><td>&#10060;</td></tr>
      <tr><td><b>Trap 1</b> &mdash; BLIP says &ldquo;a total of 10 different shapes&rdquo;</td>
          <td>don't take a count from model free text</td>
          <td><b>avoided by accident</b> &mdash; BLIP never run, never named; the stated instinct (YOLO/DETR) ran toward a model, not away</td><td>&#9888;&#65039;</td></tr>
      <tr><td><b>Trap 2</b> &mdash; the word &ldquo;exact&rdquo; in the brief</td>
          <td>treat it as a promise needing proof</td>
          <td><b>avoided deliberately</b> &mdash; carried into their own goal line, drove the per-class table and the manual recount</td><td>&#9989;</td></tr>
      <tr><td><b>Trap 3</b> &mdash; checkpoint is captioning-only, echoes questions</td>
          <td>check what a model is before trusting its format</td>
          <td><b>not exercised</b> &mdash; no model loaded</td><td>&mdash;</td></tr>
      <tr><td>Bonus clause</td><td>run a captioner, notice the bad count, say so</td>
          <td>option 3 (&ldquo;Both: BLIP printed&rdquo;, ~20s CPU) was on screen and not taken</td><td>&#10060;</td></tr>
    </table></div>
  </section>

  <section>
    <h2 class="sec">Verdict</h2>
    <div class="verdict">
      <span class="line">Passed &mdash; 10.8 min of 25. Count correct, and candidate-verified for the first time in six attempts.</span>
      <span class="sub">3 instructions &middot; 262-word opener &middot; 0 interrupts &middot; 14 tool calls.
      The count half of the archetype was done properly; the model half was never attempted.</span>
    </div>
    <ul class="scores">
      <li><span class="dim">1 &middot; Requirement capture</span><span class="pill s-strong">strong</span></li>
      <li><span class="dim">2 &middot; Data literacy</span><span class="pill s-weak">weak</span></li>
      <li><span class="dim">3 &middot; Decomposition</span><span class="pill s-strong">strong</span></li>
      <li><span class="dim">4 &middot; Verification</span><span class="pill s-strong">strong</span></li>
      <li><span class="dim">5 &middot; Correction quality</span><span class="pill s-none">not exercised</span></li>
      <li><span class="dim">6 &middot; Domain vocabulary</span><span class="pill s-adequate">adequate</span></li>
      <li><span class="dim">7 &middot; Scope control</span><span class="pill s-strong">strong</span></li>
    </ul>
    <p class="note"><b>Requirement drift.</b> The agent asked a two-part clarifying question and
    labelled one option in each &ldquo;(Recommended)&rdquo;. Both were accepted verbatim, with no words
    of the candidate's own. The second one removed the only model call from a model-tier problem.
    Attempt 001 flagged the identical pattern &mdash; this is a repeat finding.</p>

    <h2 class="sec">Carry into the next attempt</h2>
    <ol class="carry">
      <li><b>Say where each output comes from, in the opening instruction.</b> &ldquo;Caption: generate it
      with the cached BLIP captioner and print what it returns. shape_count: deterministic contour pass
      only &mdash; I won't ship a number that came out of a model's free text.&rdquo;</li>
      <li><b>Treat &ldquo;(Recommended)&rdquo; as the agent's prior, not the spec.</b> Ask: does this change
      what gets <i>measured</i>, or only how it gets built? When one option strictly dominates another for
      a few seconds of compute, take it.</li>
      <li><b>When you verify, state your number.</b> Not &ldquo;it is correct compared to my manual
      counting&rdquo; but &ldquo;I count 6 &mdash; 2 circles, 2 rectangles, 1 triangle, 1 arrow; your table
      matches.&rdquo; An unfalsifiable claim buys none of the credit the real check earned.</li>
      <li><b>Finish the sentence after &ldquo;I looked at the image&rdquo;.</b> Count it, give resolution and
      background, name the one object unlike the others. &ldquo;etc.&rdquo; is where this run's only bug was
      hiding.</li>
    </ol>
    <p class="note">Full text: <code>attempts/2026-10-26-caption-count/EVALUATION.md</code>.
    Next archetype: <b>#9, perception &rarr; structured JSON</b> &mdash; it forces both halves of the
    perception-vs-facts split, with no contour-only route to sidestep the model.</p>
  </section>
</div>

<script>
  document.querySelectorAll(".zb").forEach(function (b) {
    b.addEventListener("click", function () {
      var t = b.dataset.t, s = parseFloat(b.dataset.s);
      var img = document.getElementById("img" + t);
      var mat = document.getElementById("mat" + t);
      document.querySelectorAll('.zb[data-t="' + t + '"]').forEach(function (o) {
        o.classList.toggle("is-on", o === b);
      });
      if (s === 1) { mat.classList.remove("is-zoomed"); img.style.width = ""; }
      else { mat.classList.add("is-zoomed"); img.style.width = (img.naturalWidth * s) + "px"; }
    });
  });
</script>
"""

html = HTML.replace("__INPUTS__", "\n".join(figure(it, i) for i, it in enumerate(inputs)))
html = html.replace("__OUTPUTS__",
                    "\n".join(figure(it, 100 + i) for i, it in enumerate(outputs))
                    or '    <p class="empty">nothing written to output/ yet</p>')
out = os.path.join(HERE, "worklog.html")
open(out, "w").write(html)
print(f"wrote worklog.html  {os.path.getsize(out)/1024/1024:.2f} MB  "
      f"({len(inputs)} inputs, {len(outputs)} outputs)")
