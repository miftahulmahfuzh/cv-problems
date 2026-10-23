#!/usr/bin/env python3
"""Count duplex receptacles on sheet E-101 and mark them.

Approach
--------
The sheet carries its own symbol key, so the LEGEND glyph is used as the
template rather than anything hand-drawn:

1. Binarize and take connected components. Every receptacle glyph on this
   sheet is one isolated component (nothing touches a wall).
2. Keep components matching the glyph's shape signature (size, fill ratio).
3. The building footprint is the largest component (the walls). A candidate
   inside it is a placed device; one outside it is the legend key entry.
4. Verify every candidate by normalized cross-correlation against the legend
   glyph, so each detection carries a score.
5. Cross-check with a full-sheet template-match sweep; disagreement is printed.

Decisions taken from the brief (asked and confirmed):
  - the LEGEND key entry is NOT counted, only reported;
  - the "TYP. OF 4" row counts as the 3 glyphs actually drawn;
  - coordinates are pixels, (x, y) from the top-left of the 2339x1653 PNG.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE / "input" / "E-101.png"
DST = HERE / "output" / "E-101_marked.png"

INK = 128              # grayscale below this is ink
GLYPH_W = (18, 45)     # candidate bbox width range, px
GLYPH_H = (18, 50)     # candidate bbox height range, px
FILL = (0.20, 0.50)    # ink area / bbox area for the open circle+stem glyph
NCC_MIN = 0.55         # min correlation against the legend template
SWEEP_MIN = 0.60       # threshold for the independent template sweep
NMS_DIST = 20          # px, peak suppression radius in the sweep


def load():
    img = cv2.imread(str(SRC), cv2.IMREAD_GRAYSCALE)
    if img is None:
        sys.exit(f"cannot read {SRC}")
    return img, (img < INK).astype(np.uint8)


def components(mask):
    n, labels, stats, cent = cv2.connectedComponentsWithStats(mask, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        out.append(dict(x=x, y=y, w=w, h=h, area=int(area),
                        cx=float(cent[i][0]), cy=float(cent[i][1])))
    return out


def footprint(comps):
    """The building outline: the component with the largest bounding box."""
    return max(comps, key=lambda c: c["w"] * c["h"])


def glyph_candidates(comps):
    keep = []
    for c in comps:
        if not (GLYPH_W[0] <= c["w"] <= GLYPH_W[1]):
            continue
        if not (GLYPH_H[0] <= c["h"] <= GLYPH_H[1]):
            continue
        fill = c["area"] / (c["w"] * c["h"])
        if not (FILL[0] <= fill <= FILL[1]):
            continue
        c["fill"] = fill
        keep.append(c)
    return keep


def inside(c, box, pad=2):
    return (box["x"] + pad <= c["cx"] <= box["x"] + box["w"] - pad and
            box["y"] + pad <= c["cy"] <= box["y"] + box["h"] - pad)


def crop(mask, c, pad=3):
    y0, y1 = max(0, c["y"] - pad), c["y"] + c["h"] + pad
    x0, x1 = max(0, c["x"] - pad), c["x"] + c["w"] + pad
    return (mask[y0:y1, x0:x1] * 255).astype(np.uint8)


def ncc(mask, c, template):
    """Best correlation of the template over a window around the candidate."""
    th, tw = template.shape
    cy, cx = int(round(c["cy"])), int(round(c["cx"]))
    half_y, half_x = th // 2 + 8, tw // 2 + 8
    y0, y1 = max(0, cy - half_y), min(mask.shape[0], cy + half_y)
    x0, x1 = max(0, cx - half_x), min(mask.shape[1], cx + half_x)
    win = (mask[y0:y1, x0:x1] * 255).astype(np.uint8)
    if win.shape[0] < th or win.shape[1] < tw:
        return 0.0
    return float(cv2.matchTemplate(win, template, cv2.TM_CCOEFF_NORMED).max())


def sweep(mask, template, thr=SWEEP_MIN, nms=NMS_DIST):
    """Independent whole-sheet template match, for cross-checking."""
    th, tw = template.shape
    res = cv2.matchTemplate((mask * 255).astype(np.uint8), template,
                            cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(res >= thr)
    peaks = sorted(((float(res[y, x]), int(x), int(y)) for y, x in zip(ys, xs)),
                   reverse=True)
    hits = []
    for score, x, y in peaks:
        cx, cy = x + tw / 2, y + th / 2
        if any((cx - h[0]) ** 2 + (cy - h[1]) ** 2 < nms ** 2 for h in hits):
            continue
        hits.append((cx, cy, score))
    return hits


def overlay(gray, devices, keys, build):
    out = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    red, grey, blue = (60, 60, 220), (150, 150, 150), (190, 120, 40)

    cv2.rectangle(out, (build["x"], build["y"]),
                  (build["x"] + build["w"], build["y"] + build["h"]), blue, 2)

    for i, d in enumerate(devices, 1):
        cx, cy = int(round(d["cx"])), int(round(d["cy"]))
        cv2.circle(out, (cx, cy), 28, red, 3)
        cv2.putText(out, str(i), (cx + 32, cy - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, red, 2, cv2.LINE_AA)
        # coordinates centred under the ring: neighbours in the "TYP. OF 4"
        # row are only ~126 px apart, so a label set to the right collides.
        label = f"({cx},{cy})"
        (lw, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
        cv2.putText(out, label, (cx - lw // 2, cy + 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, red, 1, cv2.LINE_AA)

    for k in keys:
        cx, cy = int(round(k["cx"])), int(round(k["cy"]))
        cv2.circle(out, (cx, cy), 28, grey, 3)
        # above the glyph: to its right is the legend's own wording.
        cv2.putText(out, "KEY - not counted", (cx - 28, cy - 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, grey, 1, cv2.LINE_AA)

    x, y = 200, 90
    cv2.putText(out, f"DUPLEX RECEPTACLES: {len(devices)}", (x, y),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, red, 3, cv2.LINE_AA)
    cv2.putText(out, "red = counted device   grey = legend key (excluded)",
                (x, y + 36), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (90, 90, 90), 1,
                cv2.LINE_AA)
    cv2.putText(out, "blue = building footprint used to separate the two",
                (x, y + 62), cv2.FONT_HERSHEY_SIMPLEX, 0.6, blue, 1, cv2.LINE_AA)
    cv2.putText(out, 'note: OFFICE 102 bottom row is tagged "TYP. OF 4" -'
                     " 3 glyphs are drawn and 3 are counted",
                (x, y + 88), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (90, 90, 90), 1,
                cv2.LINE_AA)
    return out


def main():
    gray, mask = load()
    comps = components(mask)
    build = footprint(comps)
    cands = glyph_candidates(comps)

    outside = [c for c in cands if not inside(c, build)]
    if not outside:
        sys.exit("no symbol found outside the building footprint; "
                 "cannot identify the legend key to use as a template")
    legend = min(outside, key=lambda c: c["cy"])   # key entry, top of the box
    template = crop(mask, legend)

    for c in cands:
        c["score"] = ncc(mask, c, template)
    verified = [c for c in cands if c["score"] >= NCC_MIN]

    devices = sorted((c for c in verified if inside(c, build)),
                     key=lambda c: (round(c["cy"] / 40), c["cx"]))
    keys = [c for c in verified if not inside(c, build)]

    print(f"sheet            : {SRC.name}  {gray.shape[1]}x{gray.shape[0]} px")
    print(f"building footprint: x {build['x']}-{build['x']+build['w']}, "
          f"y {build['y']}-{build['y']+build['h']}")
    print(f"template         : legend glyph at ({legend['cx']:.0f}, "
          f"{legend['cy']:.0f}), {template.shape[1]}x{template.shape[0]} px")
    print(f"candidates       : {len(cands)} by shape, {len(verified)} verified "
          f"at NCC >= {NCC_MIN}")
    print()
    print(f"DUPLEX RECEPTACLE COUNT: {len(devices)}")
    print()
    print("  #     x      y    bbox      ncc")
    print("  " + "-" * 36)
    for i, d in enumerate(devices, 1):
        print(f"  {i:<3d} {d['cx']:6.1f} {d['cy']:6.1f}   "
              f"{d['w']}x{d['h']}   {d['score']:.3f}")
    print()
    for k in keys:
        print(f"  excluded: legend key entry at ({k['cx']:.1f}, {k['cy']:.1f})"
              f"  ncc={k['score']:.3f}")
    print('  note: the OFFICE 102 bottom row is annotated "TYP. OF 4"; '
          "3 glyphs are drawn, 3 are counted.")

    hits = sweep(mask, template)
    in_plan = [h for h in hits if inside({"cx": h[0], "cy": h[1]}, build)]
    print()
    print(f"cross-check: whole-sheet template sweep at NCC >= {SWEEP_MIN} found "
          f"{len(hits)} glyph(s), {len(in_plan)} inside the footprint")
    if len(in_plan) != len(devices):
        print("  WARNING: sweep and component pass disagree")
        for cx, cy, s in in_plan:
            near = min(abs(cx - d["cx"]) + abs(cy - d["cy"]) for d in devices) \
                if devices else 999
            if near > 12:
                print(f"    sweep-only hit at ({cx:.0f}, {cy:.0f}) score={s:.3f}")
    else:
        print("  agrees with the component pass")

    DST.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(DST), overlay(gray, devices, keys, build))
    print(f"\noverlay written: {DST.relative_to(HERE)}")


if __name__ == "__main__":
    main()
