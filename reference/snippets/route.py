#!/usr/bin/env python3
"""Classify any image four ways with CLIP, then extract a type-appropriate fact.

    CLIP zero-shot  ->  chart     -> cv2: MA-line slope -> trend
                        document  -> cv2: layout -> rows x cols
                        shapes    -> cv2: contours -> count + kinds
                        photo     -> resnet18 -> top-1 label

    python scratch/route.py
"""
import os
import time

import cv2
import numpy as np
import torch
from PIL import Image

torch.set_grad_enabled(False)
os.environ.setdefault("HF_HUB_OFFLINE", "1")

IMGS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images")

# Prompt wording is load-bearing, not cosmetic. Measured over 4 variants:
#   "a printed financial document with a table"  -> document misread as chart, 0.94
#   "a scanned page of a paper document"         -> document misread as chart, 1.00
#   "a printed invoice or financial table"       -> 4/4 correct            <- this one
# CLIP cannot read glyphs, so a finance word in the document label pulls its
# embedding toward the chart label. Describe what the image LOOKS like, not
# what it is about. Re-measure whenever you touch these strings.
KINDS = {
    "chart":    "a candlestick stock chart",
    "document": "a printed invoice or financial table",
    "shapes":   "simple colored geometric shapes",
    "photo":    "a landscape photograph",
}
_cache = {}


# ------------------------------------------------------------------ classify
def classify(im):
    if "clip" not in _cache:
        from transformers import CLIPModel, CLIPProcessor
        n = "openai/clip-vit-base-patch32"
        _cache["clip"] = (CLIPModel.from_pretrained(n).eval(), CLIPProcessor.from_pretrained(n))
    model, proc = _cache["clip"]
    keys, prompts = list(KINDS), list(KINDS.values())
    inp = proc(text=prompts, images=im, return_tensors="pt", padding=True)
    p = model(**inp).logits_per_image.softmax(-1)[0]
    i = int(p.argmax())
    return keys[i], float(p[i])


# ------------------------------------------------------------------ handlers
def fact_chart(path, im):
    """Isolate the blue MA line, fit a slope over it -> trend direction."""
    bgr = cv2.imread(path)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    ma = cv2.inRange(hsv, (105, 120, 120), (125, 255, 255))     # the #2962ff MA20 line

    cols, ys = [], []
    for x in range(ma.shape[1]):
        on = np.flatnonzero(ma[:, x])
        if on.size:
            cols.append(x)
            ys.append(on.mean())
    if len(cols) < 30:                                          # no MA line -> fall back
        g = cv2.inRange(hsv, (70, 60, 60), (95, 255, 255)).sum()
        r = (cv2.inRange(hsv, (0, 60, 60), (10, 255, 255)).sum()
             + cv2.inRange(hsv, (170, 60, 60), (180, 255, 255)).sum())
        share = g / max(g + r, 1)
        return {"method": "candle colour share", "green_share": round(float(share), 3),
                "trend": "up" if share > 0.55 else "down" if share < 0.45 else "sideways"}

    # y grows downward in image space, so negate the slope to get price direction
    slope = -np.polyfit(cols, ys, 1)[0]
    span = (max(ys) - min(ys)) / bgr.shape[0]
    trend = "up" if slope > 0.01 else "down" if slope < -0.01 else "sideways"
    return {"method": "MA-line regression", "ma_px": len(cols),
            "slope_px_per_col": round(float(slope), 4),
            "vertical_span_frac": round(float(span), 3), "trend": trend}


def fact_document(path, im):
    """Word blobs -> cluster into rows and columns -> table dimensions."""
    gray = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    merged = cv2.dilate(th, cv2.getStructuringElement(cv2.MORPH_RECT, (11, 3)))
    cnts, _ = cv2.findContours(merged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in cnts if cv2.contourArea(c) > 60]
    boxes = [b for b in boxes if b[3] > 6]
    if not boxes:
        return {"error": "no text found"}

    def cluster(vals, tol):
        lab, cur, prev = {}, 0, None
        for v in sorted(vals):
            if prev is not None and v - prev > tol:
                cur += 1
            lab[v], prev = cur, v
        return lab

    med_h = float(np.median([h for *_, h in boxes]))
    rowlab = cluster([y + h / 2 for _, y, _, h in boxes], med_h * 0.8)
    rows = {}
    for b in boxes:
        rows.setdefault(rowlab[b[1] + b[3] / 2], []).append(b)
    table = {r: v for r, v in rows.items() if len(v) >= 4}      # table lines are wide
    if not table:
        return {"words": len(boxes), "table_detected": False}

    tbl = [b for v in table.values() for b in v]
    collab = cluster([float(b[0]) for b in tbl], 28)
    return {"words": len(boxes), "table_detected": True,
            "rows": len(table), "cols": len(set(collab.values())),
            "band_y": [min(b[1] for b in tbl), max(b[1] + b[3] for b in tbl)]}


def fact_shapes(path, im):
    """Contours -> vertex count + circularity -> shape inventory."""
    bgr = cv2.imread(path)
    gray = cv2.medianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), 5)
    _, th = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    found = []
    for c in cnts:
        a = cv2.contourArea(c)
        if a < 500:
            continue
        peri = cv2.arcLength(c, True)
        v = len(cv2.approxPolyDP(c, 0.04 * peri, True))
        circ = 4 * np.pi * a / (peri * peri)
        found.append({3: "triangle", 4: "quad", 5: "pentagon"}.get(
            v, "circle" if circ > 0.8 else f"{v}-gon"))
    return {"count": len(found),
            "kinds": {k: found.count(k) for k in sorted(set(found))}}


def fact_photo(path, im):
    """resnet18 ImageNet top-1, loaded only if a photo actually shows up."""
    if "resnet" not in _cache:
        from torchvision.models import ResNet18_Weights, resnet18
        w = ResNet18_Weights.DEFAULT
        _cache["resnet"] = (resnet18(weights=w).eval(), w.transforms(), w.meta["categories"])
    model, pre, cats = _cache["resnet"]
    p = model(pre(im).unsqueeze(0)).softmax(-1)[0]
    top = p.topk(3)
    return {"top1": cats[int(top.indices[0])], "conf": round(float(top.values[0]), 3),
            "runners_up": [cats[int(i)] for i in top.indices[1:]]}


HANDLERS = {"chart": fact_chart, "document": fact_document,
            "shapes": fact_shapes, "photo": fact_photo}


def main():
    t0 = time.time()
    files = sorted(f for f in os.listdir(IMGS) if f.lower().endswith((".png", ".jpg", ".jpeg")))
    for f in files:
        path = os.path.join(IMGS, f)
        im = Image.open(path).convert("RGB")
        kind, conf = classify(im)
        fact = HANDLERS[kind](path, im)
        print(f"\n{f}  ({im.size[0]}x{im.size[1]})")
        print(f"  kind  {kind}  [{conf:.2f}]")
        for k, v in fact.items():
            print(f"  {k:<18} {v}")
    print(f"\n{len(files)} images in {time.time() - t0:.1f}s\n")


if __name__ == "__main__":
    main()
