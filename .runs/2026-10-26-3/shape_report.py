"""
Count and classify the shapes in an image of flat-coloured geometry.

Pipeline is purely classical: the background is a near-uniform light grey and
every shape is a saturated fill inside a dark outline, so a saturation-or-darkness
mask separates figure from ground exactly. No detector is involved -- contour
extraction is deterministic here, where a detector would only be approximate.

Prints a per-shape table (so a miscount can be traced to a specific blob) and
writes output/description.json.
"""

import json
import os
import sys
from collections import Counter

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "input", "sample_14.png")
OUT_DIR = os.path.join(HERE, "output")
JSON_PATH = os.path.join(OUT_DIR, "description.json")
OVERLAY_PATH = os.path.join(OUT_DIR, "shapes_annotated.png")

# --- tunables, all stated rather than buried -------------------------------
SAT_MIN = 60        # a fill counts as "coloured" above this HSV saturation
VAL_MAX = 110       # ...or counts as "outline" below this HSV value
MIN_AREA_FRAC = 2e-4  # blobs smaller than this fraction of the frame are noise
CIRCULARITY_MIN = 0.85
SOLIDITY_MIN = 0.90   # below this the polygon is concave
SQUARE_TOL = 0.08     # |1 - w/h| under this reads as a square, not a rectangle

NAMED_COLOURS = {
    "red": (220, 50, 45), "orange": (235, 140, 40), "yellow": (250, 215, 60),
    "green": (60, 160, 75), "teal": (20, 150, 140), "blue": (40, 130, 220),
    "purple": (150, 50, 190), "pink": (235, 110, 170), "brown": (140, 90, 55),
    "black": (25, 25, 25), "white": (245, 245, 245), "grey": (140, 140, 140),
}


def figure_mask(bgr):
    """Everything that is not background: saturated fill OR dark outline."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    sat, val = hsv[:, :, 1], hsv[:, :, 2]
    mask = ((sat >= SAT_MIN) | (val <= VAL_MAX)).astype(np.uint8) * 255
    # close hairline gaps in antialiased outlines, then drop speckle
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    return mask


def fill_colour(bgr, contour):
    """Median colour well inside the contour, so the dark outline is excluded."""
    m = np.zeros(bgr.shape[:2], np.uint8)
    cv2.drawContours(m, [contour], -1, 255, cv2.FILLED)
    eroded = cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    if cv2.countNonZero(eroded) < 20:
        eroded = m
    px = bgr[eroded > 0]
    b, g, r = (int(v) for v in np.median(px, axis=0))
    name = min(NAMED_COLOURS,
               key=lambda n: sum((a - c) ** 2 for a, c in
                                 zip(NAMED_COLOURS[n], (r, g, b))))
    return name, (r, g, b)


def vertex_count(contour, perim):
    """approxPolyDP vertex count, taken as the mode over an epsilon sweep so a
    single unlucky tolerance cannot change the classification."""
    votes = Counter()
    for eps in (0.010, 0.015, 0.020, 0.025, 0.030, 0.035, 0.040):
        votes[len(cv2.approxPolyDP(contour, eps * perim, True))] += 1
    return votes.most_common(1)[0][0], dict(sorted(votes.items()))


def classify(contour):
    area = cv2.contourArea(contour)
    perim = cv2.arcLength(contour, True)
    circularity = 4 * np.pi * area / (perim ** 2) if perim else 0.0
    hull_area = cv2.contourArea(cv2.convexHull(contour))
    solidity = area / hull_area if hull_area else 0.0
    nv, votes = vertex_count(contour, perim)

    if solidity < SOLIDITY_MIN:
        # an arrowhead/chevron is a concave dart: apex, two tips, one notch
        kind = "arrow" if nv in (4, 5) else f"concave-polygon-{nv}"
    elif circularity >= CIRCULARITY_MIN and nv > 5:
        kind = "circle"
    elif nv == 3:
        kind = "triangle"
    elif nv == 4:
        _, (w, h), _ = cv2.minAreaRect(contour)
        ratio = min(w, h) / max(w, h) if max(w, h) else 0
        kind = "square" if abs(1 - ratio) <= SQUARE_TOL else "rectangle"
    else:
        kind = f"polygon-{nv}"

    return dict(kind=kind, area=area, perimeter=perim, vertices=nv,
                votes=votes, circularity=circularity, solidity=solidity)


def plural(kind, n):
    if n == 1:
        return kind
    return kind + ("es" if kind.endswith(("s", "x", "ch")) else "s")


def build_caption(shapes):
    """Caption derived from what was actually detected, so it can never
    disagree with shape_count."""
    counts = Counter(s["kind"] for s in shapes)
    order = ["circle", "square", "rectangle", "triangle", "arrow"]
    keys = ([k for k in order if k in counts] +
            sorted(k for k in counts if k not in order))
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
             7: "seven", 8: "eight", 9: "nine", 10: "ten"}
    parts = [f"{words.get(counts[k], counts[k])} {plural(k, counts[k])}" for k in keys]
    inventory = (", ".join(parts[:-1]) + " and " + parts[-1]) if len(parts) > 1 else parts[0]
    total = words.get(len(shapes), len(shapes))
    return (f"A plain light background with {total} flat-coloured geometric "
            f"shapes arranged in a grid: {inventory}.")


def main():
    bgr = cv2.imread(IN_PATH)
    if bgr is None:
        sys.exit(f"could not read {IN_PATH}")
    h, w = bgr.shape[:2]
    print(f"image      : {os.path.relpath(IN_PATH, HERE)}  {w}x{h}")

    mask = figure_mask(bgr)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = MIN_AREA_FRAC * w * h
    kept, rejected = [], []
    for c in contours:
        (kept if cv2.contourArea(c) >= min_area else rejected).append(c)
    print(f"contours   : {len(contours)} external, {len(kept)} above "
          f"{min_area:.0f}px area, {len(rejected)} rejected as noise")
    if rejected:
        print(f"             rejected areas: "
              f"{sorted(round(cv2.contourArea(c), 1) for c in rejected)}")

    shapes = []
    for c in sorted(kept, key=lambda c: (cv2.boundingRect(c)[1] // 50,
                                         cv2.boundingRect(c)[0])):
        info = classify(c)
        info["colour"], info["rgb"] = fill_colour(bgr, c)
        M = cv2.moments(c)
        info["centroid"] = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        info["contour"] = c
        shapes.append(info)

    print(f"\nper-shape detail ({len(shapes)} blobs)")
    print(f"{'#':>2}  {'kind':<10} {'colour':<7} {'centroid':<12} {'area':>9} "
          f"{'verts':>5} {'circ':>5} {'solid':>5}  epsilon-sweep votes")
    print("-" * 104)
    for i, s in enumerate(shapes, 1):
        print(f"{i:>2}  {s['kind']:<10} {s['colour']:<7} "
              f"{str(s['centroid']):<12} {s['area']:>9.0f} {s['vertices']:>5} "
              f"{s['circularity']:>5.2f} {s['solidity']:>5.2f}  {s['votes']}")

    counts = Counter(s["kind"] for s in shapes)
    print("\ncount by shape")
    for kind, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {kind:<10} {n}")
    print(f"  {'-' * 10} --")
    print(f"  {'TOTAL':<10} {len(shapes)}")

    caption = build_caption(shapes)
    os.makedirs(OUT_DIR, exist_ok=True)
    payload = {"caption": caption, "shape_count": len(shapes)}
    with open(JSON_PATH, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(f"\ncaption    : {caption}")
    print(f"wrote      : {os.path.relpath(JSON_PATH, HERE)}  -> {payload}")

    # annotated overlay, so the count can be checked by eye against the image
    vis = bgr.copy()
    for i, s in enumerate(shapes, 1):
        cv2.drawContours(vis, [s["contour"]], -1, (0, 0, 255), 3)
        cx, cy = s["centroid"]
        label = f"{i}:{s['kind']}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.rectangle(vis, (cx - tw // 2 - 4, cy - th - 6),
                      (cx + tw // 2 + 4, cy + 6), (255, 255, 255), cv2.FILLED)
        cv2.rectangle(vis, (cx - tw // 2 - 4, cy - th - 6),
                      (cx + tw // 2 + 4, cy + 6), (0, 0, 255), 1)
        cv2.putText(vis, label, (cx - tw // 2, cy), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (0, 0, 180), 2, cv2.LINE_AA)
    cv2.imwrite(OVERLAY_PATH, vis)
    print(f"wrote      : {os.path.relpath(OVERLAY_PATH, HERE)}  "
          f"(red outline + index per counted blob)")


if __name__ == "__main__":
    main()
