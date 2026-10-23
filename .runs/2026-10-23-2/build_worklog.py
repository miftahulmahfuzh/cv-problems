#!/usr/bin/env python3
"""Regenerate worklog.html from input/ and output/.

Inputs are rendered once (PDF pages at 3x) and embedded as base64 data URIs.
Outputs are listed newest-first with captions read from output/captions.txt
(one "filename<TAB>caption" line per image), if present.
"""
import base64, io, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IN, OUT = HERE / "input", HERE / "output"
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
ZOOM = 3  # 216 DPI


def b64(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def png_of(path: Path):
    """-> (data_uri, w, h, kb) for a raster file on disk."""
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size
    data = path.read_bytes()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp", ".bmp": "image/bmp", ".tif": "image/tiff",
            ".tiff": "image/tiff"}[path.suffix.lower()]
    return b64(data, mime), w, h, len(data) / 1024


def pdf_pages(path: Path):
    import pymupdf
    doc = pymupdf.open(path)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM))
        data = pix.tobytes("png")
        pts = page.rect
        yield {
            "label": f"{path.name} — page {i + 1} of {len(doc)}",
            "meta": f"{pix.width} x {pix.height} px rendered at {ZOOM}x "
                    f"(216 dpi) from {pts.width:.0f} x {pts.height:.0f} pt",
            "w": pix.width, "h": pix.height,
            "uri": b64(data, "image/png"), "kb": len(data) / 1024,
        }
    doc.close()


def collect(d: Path, newest_first=False):
    if not d.is_dir():
        return []
    files = [p for p in d.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXT | {".pdf"}]
    files.sort(key=lambda p: (p.stat().st_mtime, p.name), reverse=newest_first)
    items = []
    for p in files:
        if p.suffix.lower() == ".pdf":
            items.extend(pdf_pages(p))
        else:
            uri, w, h, kb = png_of(p)
            items.append({"label": p.name, "meta": f"{w} x {h} px",
                          "w": w, "h": h, "uri": uri, "kb": kb})
    return items


def captions():
    f = OUT / "captions.txt"
    if not f.is_file():
        return {}
    out = {}
    for line in f.read_text().splitlines():
        if "\t" in line:
            k, v = line.split("\t", 1)
            out[k.strip()] = v.strip()
    return out


def figure(it, caption=None):
    cap = f'<p class="caption">{caption}</p>' if caption else ""
    return f"""      <figure class="plate">
        <div class="plate-head">
          <span class="plate-name">{it['label']}</span>
          <span class="plate-meta">{it['meta']}</span>
        </div>
        <div class="mount" data-w="{it['w']}">
          <img src="{it['uri']}" alt="{it['label']}" width="{it['w']}" height="{it['h']}">
        </div>
        <div class="plate-foot">
          <button type="button" class="zoom" aria-pressed="false">Actual size &middot; {it['w']} px</button>
          <span class="weight">{it['kb']:.0f} KB</span>
        </div>{cap}
      </figure>"""


def main():
    ins = collect(IN)
    outs = collect(OUT, newest_first=True)
    caps = captions()

    in_html = "\n".join(figure(i) for i in ins) or \
        '      <p class="empty">No images or PDFs in <code>input/</code>.</p>'
    if outs:
        out_html = "\n".join(
            figure(i, caps.get(i["label"].split(" — ")[0])) for i in outs)
    else:
        out_html = ('      <p class="empty">Nothing written to <code>output/</code> yet. '
                    'Images land here as the work proceeds, newest first.</p>')

    src = "E-set.pdf" if (IN / "E-set.pdf").exists() else ", ".join(
        p.name for p in sorted(IN.iterdir()) if p.is_file())

    html = TEMPLATE
    for key, val in (("__IN_HTML__", in_html), ("__OUT_HTML__", out_html),
                     ("__VERDICT_HTML__", (HERE / "verdict.html").read_text()
                      if (HERE / "verdict.html").is_file() else ""),
                     ("__N_IN__", str(len(ins))), ("__N_OUT__", str(len(outs))),
                     ("__SRC__", src)):
        html = html.replace(key, val)
    (HERE / "worklog.html").write_text(html)
    print(f"worklog.html written: {len(ins)} input plate(s), {len(outs)} output plate(s), "
          f"{(HERE / 'worklog.html').stat().st_size / 1024:.0f} KB")


TEMPLATE = open(HERE / "worklog.tmpl.html").read() if (HERE / "worklog.tmpl.html").exists() else None

if __name__ == "__main__":
    if TEMPLATE is None:
        sys.exit("worklog.tmpl.html missing")
    main()
