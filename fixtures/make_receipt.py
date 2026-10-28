"""Synthetic till receipt: raster PNG in a typewriter font plus ground truth JSON.

    python fixtures/make_receipt.py out_dir

The font is FreeMono, not DejaVu, so a DejaVu glyph matcher cannot read it; OCR can.
Items print on two lines (name, then `qty x unit   total`), there is a negative
discount line and the printed total is tax-inclusive.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
W = 560
ITEMS = [("INDOMIE GORENG", 5, 3500), ("AQUA 600ML", 3, 4000), ("BERAS 5KG", 1, 68500),
         ("TELUR AYAM 1KG", 2, 29000), ("SUSU UHT 1L", 2, 18750)]
DISCOUNT = 5000
PAID = 200000
fmt = lambda n: f"{n:,}"


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    f = ImageFont.truetype(FONT, 26)
    big = ImageFont.truetype(FONT, 34)
    img = Image.new("L", (W, 980), 244)
    d = ImageDraw.Draw(img)
    boxes = []
    y = 40

    def line(text, font=f, x=30, right=None, key=None):
        nonlocal y
        if right is not None:
            x = right - d.textlength(text, font=font)
        d.text((x, y), text, font=font, fill=30)
        bb = d.textbbox((x, y), text, font=font)
        if key:
            boxes.append({"key": key, "text": text, "bbox": [int(v) for v in bb]})
        y += int(font.size * 1.35)

    def two(left, right, key=None):
        nonlocal y
        d.text((30, y), left, font=f, fill=30)
        d.text((W - 30 - d.textlength(right, font=f), y), right, font=f, fill=30)
        bb = d.textbbox((30, y), left + " " * 4, font=f)
        rb = d.textbbox((W - 30 - d.textlength(right, font=f), y), right, font=f)
        if key:
            boxes.append({"key": key, "text": f"{left} | {right}",
                          "bbox": [bb[0], min(bb[1], rb[1]), rb[2], max(bb[3], rb[3])]})
        y += int(f.size * 1.35)

    line("TOKO SINAR JAYA", big, x=(W - d.textlength("TOKO SINAR JAYA", font=big)) / 2, key="store")
    line("Jl. Melati No. 12, Bandung", x=(W - d.textlength("Jl. Melati No. 12, Bandung", font=f)) / 2)
    y += 10
    two("21/10/2026 14:32", "Kasir: DEWI", key="datetime")
    two("No: 004517", "")
    line("-" * 40)
    items_gt = []
    for name, q, p in ITEMS:
        line(name, key=f"item:{name}")
        two(f"  {q} x {fmt(p)}", fmt(q * p), key=f"item:{name}:amount")
        items_gt.append({"name": name, "qty": q, "unit_price": p, "line_total": q * p})
    line("-" * 40)
    sub = sum(i["line_total"] for i in items_gt)
    two("Subtotal", fmt(sub), key="subtotal")
    two("Diskon member", "-" + fmt(DISCOUNT), key="discount")
    total = sub - DISCOUNT
    two("TOTAL", fmt(total), key="total")
    ppn = round(total * 11 / 111)
    two("PPN 11% (incl.)", fmt(ppn), key="ppn")
    line("-" * 40)
    two("Tunai", fmt(PAID), key="cash")
    two("Kembali", fmt(PAID - total), key="change")
    y += 14
    line("Terima kasih", x=(W - d.textlength("Terima kasih", font=f)) / 2)
    img = img.crop((0, 0, W, y + 30))

    rng = np.random.default_rng(7)
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(0.7)), dtype=np.float32)
    a += rng.normal(0, 5, a.shape)
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(out / "receipt.png")

    json.dump({
        "store": "TOKO SINAR JAYA", "date": "2026-10-21", "time": "14:32",
        "items": items_gt, "subtotal": sub, "discount": DISCOUNT, "total": total,
        "ppn_included": ppn, "cash": PAID, "change": PAID - total, "line_boxes": boxes,
    }, open(out / "ground_truth_raw.json", "w"), indent=2)
    print(img.size, "total", total, "ppn", ppn)


if __name__ == "__main__":
    main(sys.argv[1])
