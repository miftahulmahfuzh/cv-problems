"""Extract a trades table from a raster statement image.

    python extract_trades.py [input/statement.png]

Writes output/trades.json and output/overlay.png.

Stages
  1. detect_cells: pixel segmentation -> rows of cell boxes (no text knowledge).
  2. read_cell:    glyph matching against an atlas rendered from DejaVu Sans
                   (bundled with matplotlib). No OCR engine is available here, so
                   this reads DejaVu-style text only; swap read_cell for a real OCR
                   engine to read other fonts.
  3. the first row is the header; its text names the columns.
"""
import json
import re
import sys

import cv2
import matplotlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

INK = 160  # grey level below which a pixel is text; row rules / header fill are lighter
SPACE_GAP = 0.35  # blank gap between glyphs, in font sizes, that counts as a space
CELL_GAP = 15  # px of blank columns separating two cells
CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789,.()-/:%+"
FONT = matplotlib.get_data_path() + "/fonts/ttf/DejaVuSans.ttf"
SIZES = np.arange(8, 26.01, 0.5)


def runs(mask):
    """(start, end) inclusive runs of True in a 1-D bool array."""
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(mask) - 1))
    return out


def merge(rs, gap):
    out = [list(rs[0])]
    for a, b in rs[1:]:
        if a - out[-1][1] <= gap:
            out[-1][1] = b
        else:
            out.append([a, b])
    return out


def detect_cells(gray):
    """Rows of cell boxes [x0, y0, x1, y1] for the table, header row first."""
    ink = gray < INK
    # header band: a wide, flat, light-grey fill
    band = (gray > 225) & (gray < 245)
    band_rows = np.where(band.sum(axis=1) > 0.5 * gray.shape[1])[0]
    top = int(band_rows.min())
    # last horizontal rule of the table: wide light-grey line, bottom-most
    rules = np.where(((gray > 200) & (gray < 235)).sum(axis=1) > 0.6 * gray.shape[1])[0]
    bottom = int(rules.max())

    rows = []
    for ra, rb in runs(ink[top:bottom + 1].any(axis=1)):
        ys, ye = ra + top, rb + top
        cells = []
        for xa, xb in merge(runs(ink[ys:ye + 1].any(axis=0)), CELL_GAP):
            sub = ink[ys:ye + 1, xa:xb + 1]
            r = np.where(sub.any(axis=1))[0]
            cells.append([int(xa), int(ys + r.min()), int(xb), int(ys + r.max())])
        rows.append(cells)
    return rows


# ---- glyph reading ---------------------------------------------------------

_atlas_cache = {}


def atlas(size):
    """{char: tight ink mask} of CHARSET rendered at this font size."""
    if size not in _atlas_cache:
        font = ImageFont.truetype(FONT, size)
        out = {}
        for ch in CHARSET:
            im = Image.new("L", (int(size * 2), int(size * 2)), 255)
            ImageDraw.Draw(im).text((size * 0.4, size * 0.3), ch, font=font, fill=0)
            m = np.array(im) < INK
            ys, xs = np.where(m)
            out[ch] = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        _atlas_cache[size] = out
    return _atlas_cache[size]


def iou(a, b):
    """Overlap of two masks aligned at their top-left, best over +-1 px shifts."""
    h, w = max(a.shape[0], b.shape[0]) + 2, max(a.shape[1], b.shape[1]) + 2
    best = 0.0
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            A = np.zeros((h, w), bool)
            B = np.zeros((h, w), bool)
            A[1:1 + a.shape[0], 1:1 + a.shape[1]] = a
            B[dy:dy + b.shape[0], dx:dx + b.shape[1]] = b
            u = (A | B).sum()
            best = max(best, (A & B).sum() / u if u else 0.0)
    return best


def glyphs_of(ink, box):
    """Left-to-right glyph masks in a cell, as (x0, mask). Pieces that share
    columns (the dot of an i, the stem of a colon) are merged into one glyph."""
    x0, y0, x1, y1 = box
    sub = ink[y0:y1 + 1, x0:x1 + 1].astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(sub, connectivity=8)
    parts = sorted([list(st[i][:4]) for i in range(1, n)])  # x, y, w, h
    merged = []
    for x, y, w, h in parts:
        small = min(h, merged[-1][3] if merged else h) <= 0.35 * sub.shape[0]
        if merged and small and x <= merged[-1][0] + merged[-1][2] - 1:
            px, py, pw, ph = merged[-1]
            nx, ny = min(x, px), min(y, py)
            merged[-1] = [nx, ny, max(x + w, px + pw) - nx, max(y + h, py + ph) - ny]
        else:
            merged.append([x, y, w, h])
    return [(x, sub[y:y + h, x:x + w].astype(bool), y) for x, y, w, h in merged]


def classify(mask, size):
    at = atlas(size)
    scores = {ch: iou(mask, m) for ch, m in at.items()}
    ch = max(scores, key=scores.get)
    return ch, scores[ch]


def best_size(ink, boxes):
    """Font size (px) whose atlas best explains every glyph in these cells."""
    all_glyphs = [g for b in boxes for g in glyphs_of(ink, b)]
    totals = []
    for s in SIZES:
        totals.append(sum(classify(m, s)[1] for _, m, _ in all_glyphs))
    return float(SIZES[int(np.argmax(totals))])


def trim(mask):
    ys, xs = np.where(mask)
    return mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else None


def read_component(mask, size, depth=2):
    """(text, mean score) for one connected blob. A blob that matches no single
    glyph well is touching glyphs (kerned pairs like TY): try every vertical cut."""
    ch, s1 = classify(mask, size)
    if s1 >= 0.8 or depth == 0 or mask.shape[1] < 4:
        return ch, s1
    best = (ch, s1)
    for c in range(2, mask.shape[1] - 1):
        left, right = trim(mask[:, :c]), trim(mask[:, c:])
        if left is None or right is None:
            continue
        (t1, a), (t2, b) = read_component(left, size, depth - 1), read_component(right, size, depth - 1)
        score = (a * len(t1) + b * len(t2)) / (len(t1) + len(t2))
        if score > best[1] + 0.05 and min(a, b) >= 0.6:
            best = (t1 + t2, score)
    return best


def read_cell(ink, box, size):
    """Text of one cell. Spaces are inferred from gaps between glyphs."""
    out, prev_end = "", None
    for x, mask, _ in glyphs_of(ink, box):
        if prev_end is not None and x - prev_end >= SPACE_GAP * size:
            out += " "
        out += read_component(mask, size)[0]
        prev_end = x + mask.shape[1]
    return out


# ---- main ------------------------------------------------------------------

def main(path):
    img = cv2.imread(path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ink = gray < INK
    rows = detect_cells(gray)

    texts = []
    for r in rows:
        size = best_size(ink, r)
        texts.append([read_cell(ink, b, size) for b in r])

    cols = [re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_") for t in texts[0]]
    trades = []
    for r, t in zip(rows[1:], texts[1:]):
        cells = {c: {"text": s, "bbox": b} for c, s, b in zip(cols, t, r)}
        trades.append({"metadata": {c: cells[c]["text"] for c in cols}, "cells": cells})

    result = {
        "image": path,
        "bbox_format": "[x0, y0, x1, y1] pixels, inclusive, tight around the ink",
        "header": [{"text": t, "bbox": b} for t, b in zip(texts[0], rows[0])],
        "trades": trades,
    }
    with open("output/trades.json", "w") as f:
        json.dump(result, f, indent=2)

    ov = img.copy()
    for ri, r in enumerate(rows):
        color = (255, 120, 0) if ri == 0 else (0, 0, 255)
        for x0, y0, x1, y1 in r:
            cv2.rectangle(ov, (x0 - 2, y0 - 2), (x1 + 2, y1 + 2), color, 1)
    cv2.imwrite("output/overlay.png", ov)

    for t in trades:
        print(t["metadata"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "input/statement.png")
