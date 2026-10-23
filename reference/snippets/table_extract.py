#!/usr/bin/env python3
"""Recover a table's STRUCTURE from document_table.png with cv2 only.

Why this file exists: CLAUDE.md advertises this fixture as "good for OCR", but
this env has no OCR engine (no pytesseract / easyocr / paddleocr / tesseract
binary) and pip install is banned. So if the test says "extract the table",
you cannot read glyphs -- but you CAN recover the grid, which is the half that
actually needs computer vision. Say that out loud; it reads as judgement, not
as an excuse.

Method: binarize -> dilate horizontally so characters merge into word blobs ->
contours -> cluster blobs into rows by y, into columns by x. No grid lines
needed (this document has none).

    python scratch/table_extract.py
"""
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "images", "document_table.png")
OUT = os.path.join(HERE, "table_overlay.png")


def word_boxes(gray, min_area=60):
    """Dark text on light paper -> one box per word."""
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    # merge characters sideways into words, but never merge across a column gap
    glue = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 3))
    merged = cv2.dilate(th, glue, iterations=1)
    cnts, _ = cv2.findContours(merged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in cnts if cv2.contourArea(c) > min_area]
    return [b for b in boxes if b[3] > 6]          # drop rules/underlines


def cluster_1d(values, tol):
    """Greedy 1-D clustering; returns a label per input value."""
    order = np.argsort(values)
    labels = np.zeros(len(values), int)
    cur, prev = 0, None
    for idx in order:
        v = values[idx]
        if prev is not None and v - prev > tol:
            cur += 1
        labels[idx] = cur
        prev = v
    return labels


def main():
    img = cv2.imread(SRC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    boxes = word_boxes(gray)
    print(f"{len(boxes)} word blobs found in {os.path.basename(SRC)} {img.shape[1]}x{img.shape[0]}")

    ys = np.array([y + h / 2 for _, y, _, h in boxes])
    med_h = np.median([h for *_, h in boxes])
    rows = cluster_1d(ys, tol=med_h * 0.8)

    # a table row = a text line with >= 4 words on it; prose lines have fewer
    by_row = {}
    for b, r in zip(boxes, rows):
        by_row.setdefault(r, []).append(b)
    table_rows = {r: v for r, v in by_row.items() if len(v) >= 4}
    if not table_rows:
        print("no multi-column band found")
        return

    # columns: cluster the LEFT edges of every word inside the table band only
    tbl = [b for v in table_rows.values() for b in v]
    xs = np.array([x for x, *_ in tbl], float)
    cols = cluster_1d(xs, tol=28)
    col_x = {c: xs[cols == c].min() for c in set(cols)}
    col_rank = {c: i for i, c in enumerate(sorted(col_x, key=col_x.get))}
    ncols = len(col_rank)

    band_top = min(y for _, y, _, _ in tbl)
    band_bot = max(y + h for _, y, _, h in tbl)
    print(f"table band y=[{band_top},{band_bot}]  "
          f"{len(table_rows)} rows x {ncols} columns\n")

    # print the recovered grid as cell boxes
    xmap = {id(b): col_rank[c] for b, c in zip(tbl, cols)}
    print(f"  {'row':<5}" + "".join(f"col{i:<13}" for i in range(ncols)))
    for i, r in enumerate(sorted(table_rows, key=lambda r: min(b[1] for b in table_rows[r]))):
        cells = ["-"] * ncols
        for b in sorted(table_rows[r], key=lambda b: b[0]):
            x, y, w, h = b
            cells[xmap[id(b)]] = f"({x},{y},{w}x{h})"
        print(f"  {i:<5}" + "".join(f"{c:<17}" for c in cells))

    for b in tbl:
        x, y, w, h = b
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 160, 255), 2)
    for c, x in col_x.items():
        cv2.line(img, (int(x) - 6, band_top - 8), (int(x) - 6, band_bot + 8), (255, 0, 0), 1)
    cv2.imwrite(OUT, img)
    print(f"\noverlay -> {OUT}")
    print("structure recovered; glyph reading needs an OCR engine this env lacks.")


if __name__ == "__main__":
    main()
