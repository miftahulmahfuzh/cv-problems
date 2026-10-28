"""Footprint areas from a vector site plan.

The PDF stores each building as a filled polygon, so we read the polygons
directly instead of detecting them in pixels, then cross-check with a raster
contour pass.
"""
import json
import re
from pathlib import Path

import cv2
import numpy as np
import pymupdf

HERE = Path(__file__).parent
PDF = HERE / "input" / "site-plan.pdf"
OUT = HERE / "output"
DPI = 150
SCALE_BAR_M = 20.0  # the "0 ... 20 m" bar on the sheet


def poly_from_items(items):
    """Ordered vertex list from a drawing's line ('l') / quad ('qu') / rect ('re') items."""
    pts = []
    for it in items:
        if it[0] == "l":
            pts.extend([it[1], it[2]])
        elif it[0] == "qu":
            q = it[1]
            pts.extend([q.ul, q.ur, q.lr, q.ll])
        elif it[0] == "re":
            r = it[1]
            pts.extend([r.tl, r.tr, r.br, r.bl])
    out = []
    for p in pts:  # drop consecutive duplicates (line i ends where line i+1 starts)
        p = (float(p.x), float(p.y))
        if not out or np.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 1e-6:
            out.append(p)
    if len(out) > 1 and np.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    return out


def shoelace(poly):
    """Area = 1/2 |sum(x_i*y_{i+1} - x_{i+1}*y_i)| over the closed vertex loop.

    Each term is twice the signed area of the triangle (origin, p_i, p_{i+1});
    the triangles cancel outside the shape and add up to the shape inside it.
    """
    x = np.array([p[0] for p in poly])
    y = np.array([p[1] for p in poly])
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


def clip_to_convex(poly, clip):
    """Sutherland-Hodgman: clip `poly` against a convex polygon `clip` (the parcel)."""
    # make clip counter-clockwise in math sense so "inside" is the left side
    sign = 1 if sum((clip[(i + 1) % len(clip)][0] - clip[i][0]) * (clip[(i + 1) % len(clip)][1] + clip[i][1])
                    for i in range(len(clip))) < 0 else -1
    out = poly
    for i in range(len(clip)):
        a, b = clip[i], clip[(i + 1) % len(clip)]

        def inside(p):
            return sign * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) >= -1e-9

        def cross(p, q):
            d1 = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
            d2 = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
            t = d1 / (d1 - d2)
            return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))

        inp, out = out, []
        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            if inside(p):
                out.append(p)
                if not inside(q):
                    out.append(cross(p, q))
            elif inside(q):
                out.append(cross(p, q))
        if not out:
            return []
    return out


def dist_to_poly(pt, poly):
    """0 if pt is inside, else distance to the nearest edge (for label -> building matching)."""
    if cv2.pointPolygonTest(np.array(poly, np.float32), pt, False) >= 0:
        return 0.0
    return abs(cv2.pointPolygonTest(np.array(poly, np.float32), pt, True))


def main():
    OUT.mkdir(exist_ok=True)
    page = pymupdf.open(PDF)[0]
    words = page.get_text("words")
    drawings = page.get_drawings()

    # --- scale: scale-bar length in pt <-> 20 m ---------------------------------
    bar = next(d for d in drawings if d["fill"] is None and d["width"] == 2.0)
    bar_pt = bar["rect"].width
    m_per_pt = SCALE_BAR_M / bar_pt
    print(f"scale bar {bar_pt:.1f} pt = {SCALE_BAR_M} m  ->  {m_per_pt:.5f} m/pt "
          f"(1:500 on A3 would be {0.0254 / 72 * 500:.5f})")

    # --- parcel: the dashed outline ---------------------------------------------
    parcel_d = next(d for d in drawings if d["dashes"] and "6" in d["dashes"])
    parcel = poly_from_items(parcel_d["items"])

    # --- buildings: grey-filled polygons, minus the legend swatch ---------------
    legend = [w for w in words if w[4] == "STRUCTURE"][0]
    cands = []
    for d in drawings:
        if d["fill"] is None or d["fill"] == (1.0, 1.0, 1.0):
            continue
        poly = poly_from_items(d["items"])
        if len(poly) < 3:
            continue
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        # legend swatch: sits just left of the "EXISTING STRUCTURE" text
        if abs(max(ys) - legend[3]) < 20 and max(xs) < legend[0] and legend[0] - max(xs) < 15:
            continue
        cands.append(poly)

    # label text: "BLDG X" / "SHED X" -> the nearest polygon
    labels = []
    for w in words:
        if w[4] in ("BLDG", "SHED"):
            nxt = next(v for v in words if v[5] == w[5] and v[6] == w[6] and v[7] == 1)
            labels.append((f"{w[4]} {nxt[4]}", ((w[0] + nxt[2]) / 2, (w[1] + w[3]) / 2)))

    entries = []
    for text, c in labels:
        poly = min(cands, key=lambda p: dist_to_poly(c, p))
        area_pt2 = shoelace(poly)
        inside = clip_to_convex(poly, parcel)
        area_in_pt2 = shoelace(inside) if len(inside) >= 3 else 0.0
        k = m_per_pt ** 2
        entries.append({
            "id": text.split()[1],
            "label": text,
            "area_m2": round(float(area_pt2 * k), 2),
            "within_parcel": bool(area_in_pt2 >= area_pt2 - 1e-6),
            "area_inside_parcel_m2": round(float(area_in_pt2 * k), 2),
            "_poly": poly,
        })
    entries.sort(key=lambda e: e["id"])

    (OUT / "buildings.json").write_text(
        json.dumps([{k: v for k, v in e.items() if k != "_poly"} for e in entries], indent=2) + "\n")
    for e in entries:
        print({k: v for k, v in e.items() if k != "_poly"})

    # --- raster cross-check: grey (~199) blobs -> connected components ----------
    pix = page.get_pixmap(dpi=DPI)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].copy()
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    mask = (np.abs(gray.astype(int) - 199) <= 4).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, _, stats, cen = cv2.connectedComponentsWithStats(mask)
    s = DPI / 72
    print("raster cross-check (blob area incl. outline pixels, so expect ~1% under):")
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < 200:
            continue
        cx, cy = cen[i] / s
        a = stats[i, cv2.CC_STAT_AREA] / s**2 * m_per_pt**2
        # an L-shape's centroid can fall outside the shape, so match to the nearest polygon
        near = min(entries, key=lambda e: dist_to_poly((cx, cy), e["_poly"]))
        match = near["id"] if dist_to_poly((cx, cy), near["_poly"]) < 40 else "-"
        ref = next((e["area_m2"] for e in entries if e["id"] == match), None)
        print(f"  blob at ({cx:.0f},{cy:.0f}) pt  {a:8.1f} m2   matches {match}   vector {ref}")

    # --- overlay -----------------------------------------------------------------
    ov = img.copy()
    to_px = lambda p: (int(round(p[0] * s)), int(round(p[1] * s)))
    cv2.polylines(ov, [np.array([to_px(p) for p in parcel], np.int32)], True, (0, 120, 0), 3)
    for e in entries:
        col = (0, 150, 0) if e["within_parcel"] else (220, 0, 0)
        pts = np.array([to_px(p) for p in e["_poly"]], np.int32)
        layer = ov.copy()
        cv2.fillPoly(layer, [pts], col)
        ov = cv2.addWeighted(layer, 0.35, ov, 0.65, 0)
        # outline edge by edge; a courtyard is stored as one keyhole path whose
        # "bridge" edge is traversed in both directions, so skip those edges
        edges = [(tuple(pts[i]), tuple(pts[(i + 1) % len(pts)])) for i in range(len(pts))]
        for a, b in edges:
            if (b, a) not in edges:
                cv2.line(ov, a, b, col, 4, cv2.LINE_AA)
        x, y, w, h = cv2.boundingRect(pts)
        txt = f"{e['id']}: {e['area_m2']:.1f} m2 " + ("IN" if e["within_parcel"] else
                                                        f"OUT ({e['area_inside_parcel_m2']:.1f} in)")
        scale = 0.9
        (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)
        tx, ty = x + 6, y - 10
        cv2.rectangle(ov, (tx - 3, ty - th - 4), (tx + tw + 3, ty + 6), (255, 255, 255), -1)
        cv2.putText(ov, txt, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, scale, col, 2, cv2.LINE_AA)
    cv2.imwrite(str(OUT / "overlay.png"), cv2.cvtColor(ov, cv2.COLOR_RGB2BGR))
    print("wrote", OUT / "buildings.json", "and", OUT / "overlay.png")


if __name__ == "__main__":
    main()
