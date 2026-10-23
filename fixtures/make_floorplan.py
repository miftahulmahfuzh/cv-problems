#!/usr/bin/env python3
"""Deterministic synthetic floor plan -- vector PDF, raster PNG, and ground truth.

    python fixtures/make_floorplan.py                 # -> fixtures/floorplan.{pdf,png,json}
    python fixtures/make_floorplan.py --seed 7 --dpi 200 --out /tmp/x

Why it is built as a PDF first and rasterised second: real construction drawings are
CAD exports -- vector geometry with a real text layer -- and the single most valuable
habit on this kind of input is to check for that text layer before doing any pixel
work. A fixture that only existed as a PNG would quietly teach the wrong reflex.

It also plants the trap Boon's own writing is about: the plan draws six receptacles
explicitly and then writes "TYP. OF 4" beside a banked run of three. Counting drawn
symbols gives one answer; counting installed devices gives another. Both numbers are
in the ground truth, under names that say which is which.
"""
import argparse
import json
import math
import random
from pathlib import Path

import pymupdf

PT_PER_M = 28.3465          # 1:100 scale -- 1 m on site = 10 mm on paper = 28.35 pt
MARGIN = 40.0
INK = (0.1, 0.1, 0.1)
THIN = (0.45, 0.45, 0.45)


def m(v):
    """Metres -> PDF points."""
    return v * PT_PER_M


class Plan:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.walls = []       # (x0, y0, x1, y1) in points
        self.rooms = []
        self.outlets = []
        self.doors = []
        self.windows = []
        self.notes = []

    # ------------------------------------------------------------------ geometry
    def wall(self, x0, y0, x1, y1):
        self.walls.append((x0, y0, x1, y1))

    def wall_with_opening(self, x0, y0, x1, y1, at, width, kind):
        """A wall interrupted by a door or window -- two segments and a symbol.

        Openings are why `maxLineGap` is a domain decision: this is one wall with a
        hole in it, not two walls, and the ground truth counts it as one.
        """
        horiz = abs(y1 - y0) < 1e-6
        length = (x1 - x0) if horiz else (y1 - y0)
        a, b = at - width / 2, at + width / 2
        if horiz:
            self.wall(x0, y0, x0 + a, y0)
            self.wall(x0 + b, y0, x1, y1)
            cx, cy = x0 + at, y0
        else:
            self.wall(x0, y0, x1, y0 + a)
            self.wall(x0, y0 + b, x1, y1)
            cx, cy = x0, y0 + at
        rec = {"x": round(cx, 2), "y": round(cy, 2), "width_m": round(width / PT_PER_M, 2),
               "orientation": "horizontal" if horiz else "vertical"}
        (self.doors if kind == "door" else self.windows).append(rec)
        return length


def build(seed):
    """A five-room single-storey plan. Fixed layout, seeded jitter on the symbols."""
    p = Plan(seed)
    W, H = m(20.0), m(12.0)          # 20 m x 12 m building
    ox, oy = MARGIN + 30, MARGIN + 60

    # Exterior shell, with two windows on the long walls and the entry door.
    p.wall(ox, oy, ox + W, oy)
    p.wall_with_opening(ox, oy + H, ox + W, oy + H, at=m(4.0), width=m(1.0), kind="door")
    p.wall(ox, oy, ox, oy + H)
    p.wall(ox + W, oy, ox + W, oy + H)
    p.wall_with_opening(ox, oy, ox + W, oy, at=m(6.0), width=m(1.8), kind="window")
    p.wall_with_opening(ox, oy, ox + W, oy, at=m(14.0), width=m(1.8), kind="window")

    # Interior partitions. Two vertical, one horizontal in the right half.
    vx1, vx2 = ox + m(7.0), ox + m(13.0)
    p.wall_with_opening(vx1, oy, vx1, oy + H, at=m(8.0), width=m(0.9), kind="door")
    p.wall_with_opening(vx2, oy, vx2, oy + H, at=m(3.0), width=m(0.9), kind="door")
    hy = oy + m(6.0)
    p.wall_with_opening(vx2, hy, ox + W, hy, at=m(4.0), width=m(0.9), kind="door")

    p.rooms = [
        {"name": "OFFICE 101", "x": ox, "y": oy, "w": m(7.0), "h": m(12.0), "area_m2": 84.0},
        {"name": "OFFICE 102", "x": vx1, "y": oy, "w": m(6.0), "h": m(12.0), "area_m2": 72.0},
        {"name": "STORE 103", "x": vx2, "y": oy, "w": m(7.0), "h": m(6.0), "area_m2": 42.0},
        {"name": "MECH 104", "x": vx2, "y": hy, "w": m(7.0), "h": m(6.0), "area_m2": 42.0},
    ]

    # Receptacles: four placed singly, then a banked run of three carrying a
    # "TYP. OF 4" note -- so the drawn count and the installed count differ.
    singles = [(ox + m(2.0), oy + m(2.0)), (ox + m(2.0), oy + m(9.5)),
               (vx1 + m(3.0), oy + m(2.0)), (vx2 + m(3.5), hy + m(4.0))]
    for x, y in singles:
        p.outlets.append({"x": round(x, 2), "y": round(y, 2), "kind": "single",
                          "represents": 1})
    bank_y = oy + m(10.5)
    for i in range(3):
        x = vx1 + m(1.5 + 1.6 * i)
        p.outlets.append({"x": round(x, 2), "y": round(bank_y, 2), "kind": "banked",
                          "represents": 4 if i == 0 else 1})
    p.notes.append({"text": "TYP. OF 4", "x": round(vx1 + m(1.2), 2),
                    "y": round(bank_y - 12, 2),
                    "means": "the leftmost banked symbol stands for 4 devices"})
    return p, (ox, oy, W, H)


# ---------------------------------------------------------------------- drawing

def sym_outlet(page, x, y, r=4.0):
    """Duplex receptacle: a half-circle on a short stem. Rotation-invariant enough
    for template matching to work, small enough that scale matters."""
    page.draw_circle((x, y), r, color=INK, width=0.9)
    page.draw_line((x - r, y), (x + r, y), color=INK, width=0.9)
    page.draw_line((x, y), (x, y + r * 1.8), color=INK, width=0.9)


def sym_door(page, d):
    """Quarter-circle swing arc, the universal door notation."""
    w = d["width_m"] * PT_PER_M
    x, y = d["x"], d["y"]
    if d["orientation"] == "horizontal":
        a, b = (x - w / 2, y), (x - w / 2, y - w)
        page.draw_line((x - w / 2, y), (x + w / 2, y), color=THIN, width=0.6)
    else:
        a, b = (x, y - w / 2), (x + w, y - w / 2)
        page.draw_line((x, y - w / 2), (x, y + w / 2), color=THIN, width=0.6)
    page.draw_line(a, b, color=THIN, width=0.6)


def sym_window(page, d):
    w = d["width_m"] * PT_PER_M
    x, y = d["x"], d["y"]
    for off in (-1.5, 1.5):
        page.draw_line((x - w / 2, y + off), (x + w / 2, y + off), color=INK, width=0.7)


def render(p, box, path, scale_note="SCALE 1:100"):
    doc = pymupdf.open()
    page = doc.new_page(width=842, height=595)      # A4 landscape, points
    ox, oy, W, H = box

    for x0, y0, x1, y1 in p.walls:
        page.draw_line((x0, y0), (x1, y1), color=INK, width=2.2)
    for d in p.doors:
        sym_door(page, d)
    for d in p.windows:
        sym_window(page, d)
    for o in p.outlets:
        sym_outlet(page, o["x"], o["y"])
    for r in p.rooms:
        page.insert_text((r["x"] + 10, r["y"] + 16), r["name"], fontsize=7, color=INK)
        page.insert_text((r["x"] + 10, r["y"] + 26),
                         f'{r["area_m2"]:.0f} m2', fontsize=6, color=THIN)
    for n in p.notes:
        page.insert_text((n["x"], n["y"]), n["text"], fontsize=6, color=INK)

    # Legend -- where a drawing defines its own vocabulary, and the reason a naive
    # template count comes out one too high per symbol type.
    lx, ly = ox + W + 18, oy
    page.draw_rect(pymupdf.Rect(lx, ly, lx + 110, ly + 72), color=THIN, width=0.8)
    page.insert_text((lx + 6, ly + 13), "LEGEND", fontsize=7, color=INK)
    sym_outlet(page, lx + 14, ly + 28)
    page.insert_text((lx + 28, ly + 31), "DUPLEX RECEPTACLE", fontsize=5, color=INK)
    page.draw_line((lx + 8, ly + 46), (lx + 22, ly + 46), color=THIN, width=0.6)
    page.insert_text((lx + 28, ly + 48), "DOOR", fontsize=5, color=INK)
    for off in (-1.5, 1.5):
        page.draw_line((lx + 8, ly + 62 + off), (lx + 22, ly + 62 + off), color=INK, width=0.7)
    page.insert_text((lx + 28, ly + 64), "WINDOW", fontsize=5, color=INK)

    # Title block, bottom right -- sheet number and scale, as every real sheet has.
    tb = pymupdf.Rect(842 - 200 - MARGIN, 595 - 70 - MARGIN, 842 - MARGIN, 595 - MARGIN)
    page.draw_rect(tb, color=INK, width=1.0)
    page.insert_text((tb.x0 + 8, tb.y0 + 16), "LEVEL 1 - POWER PLAN", fontsize=8, color=INK)
    page.insert_text((tb.x0 + 8, tb.y0 + 32), scale_note, fontsize=7, color=INK)
    page.insert_text((tb.x0 + 8, tb.y0 + 46), "SHEET E-101", fontsize=7, color=INK)
    page.insert_text((tb.x0 + 8, tb.y0 + 60), "REV 2  2026-10-23", fontsize=6, color=THIN)

    # Scale bar: 5 m, ticked every metre. The redundant, visual way to recover scale
    # when the title block's stated scale cannot be trusted.
    sbx, sby = MARGIN, 595 - MARGIN - 10
    page.draw_line((sbx, sby), (sbx + m(5.0), sby), color=INK, width=1.2)
    for i in range(6):
        page.draw_line((sbx + m(i), sby - 4), (sbx + m(i), sby + 4), color=INK, width=0.8)
    page.insert_text((sbx + m(5.0) + 6, sby + 3), "0        5 m", fontsize=6, color=INK)

    doc.save(str(path))
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--out", default=str(Path(__file__).parent / "floorplan"))
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    p, box = build(args.seed)
    doc = render(p, box, out.with_suffix(".pdf"))

    page = doc[0]
    pix = page.get_pixmap(dpi=args.dpi)
    pix.save(str(out.with_suffix(".png")))

    px_per_pt = args.dpi / 72.0
    total_wall_m = sum(math.dist((a, b), (c, d)) for a, b, c, d in p.walls) / PT_PER_M
    truth = {
        "seed": args.seed,
        "png_dpi": args.dpi,
        "scale": {"drawing": "1:100", "points_per_metre": round(PT_PER_M, 4),
                  "pixels_per_metre_at_dpi": round(PT_PER_M * px_per_pt, 4),
                  "scale_bar_length_m": 5.0},
        "rooms": {"count": len(p.rooms),
                  "names": [r["name"] for r in p.rooms],
                  "total_area_m2": round(sum(r["area_m2"] for r in p.rooms), 1)},
        "walls": {"segment_count_after_openings": len(p.walls),
                  "total_length_m": round(total_wall_m, 2)},
        "doors": {"count": len(p.doors)},
        "windows": {"count": len(p.windows)},
        "receptacles": {
            "symbols_drawn_on_plan": len(p.outlets),
            "symbols_drawn_including_legend": len(p.outlets) + 1,
            "devices_actually_specified": sum(o["represents"] for o in p.outlets),
            "note": "the 'TYP. OF 4' note makes the installed count differ from the "
                    "drawn count -- a pixel-perfect detector still gets the quantity "
                    "wrong, which is the point",
        },
        "positions": {"receptacles_pt": p.outlets, "doors_pt": p.doors,
                      "windows_pt": p.windows, "notes": p.notes},
    }
    out.with_suffix(".json").write_text(json.dumps(truth, indent=2) + "\n")

    print(f"wrote {out.with_suffix('.pdf')}")
    print(f"wrote {out.with_suffix('.png')}  ({pix.width}x{pix.height} @ {args.dpi} dpi)")
    print(f"wrote {out.with_suffix('.json')}")
    print(f"  rooms={truth['rooms']['count']} walls={truth['walls']['segment_count_after_openings']} "
          f"doors={truth['doors']['count']} windows={truth['windows']['count']}")
    print(f"  receptacles drawn={truth['receptacles']['symbols_drawn_on_plan']} "
          f"specified={truth['receptacles']['devices_actually_specified']}")


if __name__ == "__main__":
    main()
