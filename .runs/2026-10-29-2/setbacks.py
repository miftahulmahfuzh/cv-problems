"""Setback check: read building footprints and parcel boundary from the PDF vector layer.

Run from this directory:  python setbacks.py
Writes output/setbacks.json and output/overlay.png.
"""
import json
from pathlib import Path

import cv2
import numpy as np
import pymupdf

PDF = "input/site-plan.pdf"
OUT = Path("output")
SETBACK_M = 6.0
ZOOM = 2.0

OUT.mkdir(exist_ok=True)
page = pymupdf.open(PDF)[0]
drawings = page.get_drawings()
words = page.get_text("words")

# ---- scale: 20 m bar (measured) cross-checked against 1:500 on an A3 sheet ----
bar = next(d for d in drawings if d["width"] == 2.0 and d["rect"].height == 0)
pt_per_m = bar["rect"].width / 20.0
pt_per_m_nominal = 72 / 25.4 * 1000 / 500  # 1 m on the ground = 2 mm on paper = 5.669 pt
assert abs(pt_per_m - pt_per_m_nominal) / pt_per_m < 0.005, (pt_per_m, pt_per_m_nominal)

# ---- parcel: the dashed, unfilled outline ----
parcel = next(d for d in drawings if d["dashes"] not in (None, "", "[] 0") and d["fill"] is None)
px0, py0, px1, py1 = parcel["rect"]

# ---- buildings: grey-filled closed paths; drop the legend swatch ----
legend_labels = [w for w in words if w[4] == "EXISTING"]


def is_legend_swatch(r):
    return any(abs((r.y0 + r.y1) / 2 - (w[1] + w[3]) / 2) < 6 and 0 <= w[0] - r.x1 < 20 for w in legend_labels)


def outer_contour(items):
    """Split a path into closed sub-paths and return the largest by area (drops courtyards)."""
    loops, cur = [], []
    for it in items:
        if it[0] != "l":
            continue
        a, b = it[1], it[2]
        if cur and (abs(cur[-1].x - a.x) > 1e-3 or abs(cur[-1].y - a.y) > 1e-3):
            loops.append(cur)
            cur = []
        if not cur:
            cur.append(a)
        cur.append(b)
    loops.append(cur)
    polys = [np.array([(p.x, p.y) for p in l[:-1]]) for l in loops]
    return max(polys, key=lambda q: abs(cv2.contourArea(q.astype(np.float32))))


fills = [d for d in drawings if d["fill"] is not None and d["color"] is None and not is_legend_swatch(d["rect"])]
fills += [d for d in drawings if d["fill"] is not None and d["color"] is not None and not is_legend_swatch(d["rect"])]  # B is fill+stroke in one path
fills.sort(key=lambda d: (d["rect"].y0, d["rect"].x0))


def name_for(poly):
    cx, cy = poly.mean(axis=0)
    inside = [w for w in words if cv2.pointPolygonTest(poly.astype(np.float32), ((w[0] + w[2]) / 2, (w[1] + w[3]) / 2), False) >= 0]
    near = inside or sorted(words, key=lambda w: (((w[0] + w[2]) / 2 - cx) ** 2 + ((w[1] + w[3]) / 2 - cy) ** 2))[:2]
    toks = sorted(near, key=lambda w: w[0])
    toks = [w[4] for w in toks if w[4] in ("BLDG", "SHED") or len(w[4]) == 1]
    return " ".join(toks)


results = []
for d in fills:
    poly = outer_contour(d["items"])
    # signed distance (m) from each parcel side to the building; negative means past the boundary
    sides = {
        "left": poly[:, 0].min() - px0,
        "right": px1 - poly[:, 0].max(),
        "top": poly[:, 1].min() - py0,
        "bottom": py1 - poly[:, 1].max(),
    }
    sides = {k: v / pt_per_m for k, v in sides.items()}
    side = min(sides, key=sides.get)
    dist = sides[side]
    results.append({
        "name": name_for(poly),
        "polygon_pt": poly.round(2).tolist(),
        "distance_by_side_m": {k: round(v, 2) for k, v in sides.items()},
        "nearest_side": side,
        "distance_m": round(dist, 2),
        "required_m": SETBACK_M,
        "violates": bool(dist < SETBACK_M),
        "shortfall_m": round(max(0.0, SETBACK_M - dist), 2),
        "outside_parcel": bool(dist < 0),
    })

results.sort(key=lambda r: r["name"])
doc = {
    "units": "metres",
    "scale": {"pt_per_m": round(pt_per_m, 4), "bar_20m_pt": round(bar["rect"].width, 3), "nominal_1_500_pt_per_m": round(pt_per_m_nominal, 4)},
    "parcel_m": {"width": round((px1 - px0) / pt_per_m, 2), "height": round((py1 - py0) / pt_per_m, 2)},
    "rule": f"no building closer than {SETBACK_M} m to the parcel boundary; negative distance = past the boundary",
    "buildings": results,
}
(OUT / "setbacks.json").write_text(json.dumps(doc, indent=2))

# ---- overlay ----
pix = page.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM))
img = cv2.cvtColor(np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n), cv2.COLOR_RGB2BGR)
RED, GREEN, BLUE = (40, 40, 220), (60, 150, 40), (200, 120, 0)
S = lambda x, y: (int(round(x * ZOOM)), int(round(y * ZOOM)))

# 6 m inner limit, dashed
m = SETBACK_M * pt_per_m
corners = [S(px0 + m, py0 + m), S(px1 - m, py0 + m), S(px1 - m, py1 - m), S(px0 + m, py1 - m)]
for a, b in zip(corners, corners[1:] + corners[:1]):
    n = max(1, int(np.hypot(b[0] - a[0], b[1] - a[1]) // 16))
    for i in range(0, n, 2):
        p0 = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
        p1 = (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + (b[1] - a[1]) * (i + 1) / n)
        cv2.line(img, tuple(map(int, p0)), tuple(map(int, p1)), BLUE, 2)
cv2.putText(img, "6 m setback limit", (corners[0][0] + 8, corners[0][1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, BLUE, 2)

overlay = img.copy()
for r in results:
    poly = np.array(r["polygon_pt"])
    col = RED if r["violates"] else GREEN
    cv2.fillPoly(overlay, [np.array([S(*p) for p in poly])], col)
img = cv2.addWeighted(overlay, 0.35, img, 0.65, 0)

for r in results:
    poly = np.array(r["polygon_pt"])
    col = RED if r["violates"] else GREEN
    cv2.polylines(img, [np.array([S(*p) for p in poly])], True, col, 4)
    side = r["nearest_side"]
    # measurement line from the controlling vertex/edge to its parcel side
    if side in ("left", "right"):
        v = poly[poly[:, 0].argmin()] if side == "left" else poly[poly[:, 0].argmax()]
        tgt = (px0 if side == "left" else px1, v[1])
    else:
        v = poly[poly[:, 1].argmin()] if side == "top" else poly[poly[:, 1].argmax()]
        tgt = (v[0], py0 if side == "top" else py1)
    cv2.arrowedLine(img, S(*v), S(*tgt), col, 3, tipLength=0.05)
    label = f"{r['name']}: {r['distance_m']:.2f} m"
    if r["violates"]:
        label += f"  (short {r['shortfall_m']:.2f} m)"
    tx, ty = S(*poly.mean(axis=0))
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    org = (tx - tw // 2, ty + 28 if r["name"] != "BLDG C" else ty + 70)
    cv2.rectangle(img, (org[0] - 4, org[1] - th - 4), (org[0] + tw + 4, org[1] + 6), (255, 255, 255), -1)
    cv2.putText(img, label, org, cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)

cv2.imwrite(str(OUT / "overlay.png"), img)

print(f"scale {pt_per_m:.3f} pt/m (1:500 nominal {pt_per_m_nominal:.3f}); parcel {doc['parcel_m']['width']} x {doc['parcel_m']['height']} m")
for r in results:
    print(f"{r['name']:7s} nearest={r['nearest_side']:6s} {r['distance_m']:7.2f} m  "
          f"{'VIOLATES, short by %.2f m' % r['shortfall_m'] if r['violates'] else 'ok'}")
