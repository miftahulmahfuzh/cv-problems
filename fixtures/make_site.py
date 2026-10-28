"""Synthetic site plan: one vector PDF page + ground-truth JSON.

A parcel boundary (dashed), building footprints (grey fills) and a legend whose
swatch looks like a building. Footprints include an L-shape, a courtyard ring
(hole via even-odd), a rotated rectangle, a building straddling the boundary and
a tiny shed. Scale 1:500 on an A3 sheet.
"""
import argparse, json, math
from pathlib import Path

import pymupdf
from shapely import affinity
from shapely.geometry import Polygon, box

PT_PER_M = 72 / 25.4 * 1000 / 500          # 1:500
X0, Y0 = 90, 120                           # sheet origin of parcel's SW corner (pt)
H = 842


def pt(x, y):
    return (X0 + x * PT_PER_M, H - Y0 - y * PT_PER_M)


def build():
    parcel = box(0, 0, 120, 80)
    b = {
        "BLDG A": box(10, 10, 30, 25),
        "BLDG B": Polygon([(45, 10), (75, 10), (75, 22), (60, 22), (60, 40), (45, 40)]),
        "BLDG C": Polygon([(10, 40), (40, 40), (40, 70), (10, 70)]).difference(box(20, 50, 30, 60)),
        "BLDG D": box(100, 30, 130, 50),
        "BLDG E": affinity.rotate(box(60, 50, 90, 62), 30, origin=(60, 50)),
        "SHED F": box(85, 8, 88, 11),
    }
    return parcel, b


def draw_poly(sh, poly):
    for ring in [poly.exterior, *poly.interiors]:
        sh.draw_polyline([pt(*c) for c in ring.coords])
    sh.finish(color=(0, 0, 0), fill=(0.78, 0.78, 0.78), width=0.8, even_odd=True, closePath=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).parent / "site"))
    a = ap.parse_args()
    parcel, bl = build()
    doc = pymupdf.open()
    page = doc.new_page(width=1191, height=842)
    sh = page.new_shape()
    sh.draw_polyline([pt(*c) for c in parcel.exterior.coords])
    sh.finish(color=(0, 0, 0), width=1.4, dashes="[6 3] 0", closePath=True)
    for p in bl.values():
        draw_poly(sh, p)
    # legend swatch: same fill as a building, NOT a building
    lx, ly = 900, 700
    sh.draw_rect(pymupdf.Rect(lx, ly, lx + 28, ly + 16))
    sh.finish(color=(0, 0, 0), fill=(0.78, 0.78, 0.78), width=0.8)
    sh.commit()
    page.insert_text((lx + 36, ly + 12), "EXISTING STRUCTURE", fontsize=9)
    page.insert_text((lx, ly + 34), "- - -  PARCEL BOUNDARY", fontsize=9)
    for n, p in bl.items():
        c = p.representative_point()
        page.insert_text(pt(c.x, c.y), n, fontsize=8)
    page.insert_text((900, 790), "SITE PLAN   SCALE 1:500   (A3)", fontsize=11)
    page.insert_text((900, 805), "ALL DIMENSIONS METRES UNLESS NOTED", fontsize=8)
    sh = page.new_shape()                    # scale bar, 20 m
    sh.draw_line(pt(0, -8), pt(20, -8)); sh.finish(color=(0, 0, 0), width=2)
    sh.commit()
    page.insert_text(pt(0, -12), "0", fontsize=8); page.insert_text(pt(18, -12), "20 m", fontsize=8)
    out = Path(a.out)
    doc.save(out.with_suffix(".pdf"))
    gt = {"scale": "1:500", "pt_per_m": PT_PER_M, "parcel_area_m2": parcel.area,
          "buildings": {n: {"area_m2": round(p.area, 2),
                            "area_inside_parcel_m2": round(p.intersection(parcel).area, 2),
                            "area_outside_parcel_m2": round(p.difference(parcel).area, 2),
                            "centroid_m": [round(p.centroid.x, 2), round(p.centroid.y, 2)]}
                        for n, p in bl.items()}}
    out.with_suffix(".json").write_text(json.dumps(gt, indent=2))
    print("wrote", out.with_suffix(".pdf"))


if __name__ == "__main__":
    main()
