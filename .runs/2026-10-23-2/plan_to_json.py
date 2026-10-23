#!/usr/bin/env python3
"""Structure input/E-set.pdf into bid data -> output/plan.json.

Everything is derived from the PDF's own geometry and text; nothing about this
particular set is hardcoded. The pipeline:

  1. Pick the scaled sheet (title block says "SCALE 1:N", not "NO SCALE").
  2. Establish pt-per-metre from the stated scale, cross-check against the
     graphic scale bar.
  3. Rebuild rooms: thick lines are walls -> a grid of cells -> merge cells that
     no wall separates (a door gap is not a separation) -> one region per room
     label.
  4. Area per room from wall-centreline geometry; cross-check the printed label.
  5. Receptacles: the circle symbol, kept only where it lands inside a room (so
     the legend's specimen symbol drops out), with "TYP. OF n" multiplying the
     one symbol the note sits over.
  6. Cross-check the per-room totals against the panel schedule on the
     unscaled sheet.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
PDF = HERE / "input" / "E-set.pdf"
OUT_JSON = HERE / "output" / "plan.json"
OUT_IMG = HERE / "output" / "verify_rooms.png"

WALL_WIDTH = 2.0        # pt; thinner strokes are doors, windows, scale bar
SYMBOL_MAX = 12.0       # pt; a receptacle circle is ~8 pt across
EDGE_COVERED = 0.5      # a shared edge this covered by wall = a real partition
MM_PER_INCH = 25.4
PT_PER_INCH = 72.0

ROOM_LABEL = re.compile(r"^([A-Z][A-Z/&. ]*[A-Z])\s+(\d{2,4})$")
AREA_LABEL = re.compile(r"^([\d.]+)\s*m2$", re.I)
TYP_NOTE = re.compile(r"TYP\.?\s*OF\s*(\d+)", re.I)
SCALE_RATIO = re.compile(r"SCALE\s+1\s*:\s*(\d+)", re.I)
SHEET_NO = re.compile(r"SHEET\s+([A-Z]+-?\d+)", re.I)
REVISION = re.compile(r"REV\s+(\S+)\s+(\d{4}-\d{2}-\d{2})", re.I)


# ---------------------------------------------------------------- text helpers

def text_lines(page):
    """[(text, (x0, y0, x1, y1))] with words regrouped into their source line."""
    groups = defaultdict(list)
    for x0, y0, x1, y1, word, blk, ln, _ in page.get_text("words"):
        groups[(blk, ln)].append((x0, y0, x1, y1, word))
    out = []
    for key in sorted(groups):
        ws = sorted(groups[key], key=lambda w: w[0])
        out.append((
            " ".join(w[4] for w in ws),
            (min(w[0] for w in ws), min(w[1] for w in ws),
             max(w[2] for w in ws), max(w[3] for w in ws)),
        ))
    return out


# ------------------------------------------------------------ vector geometry

def segments(page):
    """Split every stroked path into horizontal and vertical runs."""
    horiz, vert, circles = [], [], []
    for path in page.get_drawings():
        if path["type"] != "s":
            continue
        width = path.get("width") or 0.0
        rect = path["rect"]
        kinds = "".join(it[0] for it in path["items"])
        if set(kinds) == {"c"} and max(rect.width, rect.height) <= SYMBOL_MAX:
            circles.append(((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2))
            continue
        for it in path["items"]:
            if it[0] == "l":
                a, b = it[1], it[2]
                if abs(a.y - b.y) < 0.1 and abs(a.x - b.x) > 0.1:
                    horiz.append((round((a.y + b.y) / 2, 1),
                                  min(a.x, b.x), max(a.x, b.x), width, "line"))
                elif abs(a.x - b.x) < 0.1 and abs(a.y - b.y) > 0.1:
                    vert.append((round((a.x + b.x) / 2, 1),
                                 min(a.y, b.y), max(a.y, b.y), width, "line"))
            elif it[0] == "re":
                r = it[1]
                for y in (r.y0, r.y1):
                    horiz.append((round(y, 1), r.x0, r.x1, width, "rect"))
                for x in (r.x0, r.x1):
                    vert.append((round(x, 1), r.y0, r.y1, width, "rect"))
    return horiz, vert, circles


def covered(spans, lo, hi):
    """Fraction of [lo, hi] covered by the union of `spans`."""
    span = hi - lo
    if span <= 0:
        return 0.0
    clipped = sorted((max(a, lo), min(b, hi)) for a, b in spans
                     if min(b, hi) > max(a, lo))
    total, reach = 0.0, lo
    for a, b in clipped:
        a = max(a, reach)
        if b > a:
            total += b - a
            reach = b
    return total / span


def build_rooms(horiz, vert, labels):
    """Merge the wall grid's cells into one region per room label."""
    walls_h = [s for s in horiz if s[3] >= WALL_WIDTH]
    walls_v = [s for s in vert if s[3] >= WALL_WIDTH]
    if not walls_h or not walls_v:
        raise SystemExit("no walls found -- wall width filter is wrong")

    xs = sorted({s[0] for s in walls_v})
    ys = sorted({s[0] for s in walls_h})
    by_x = defaultdict(list)
    for c, a, b, *_ in walls_v:
        by_x[c].append((a, b))
    by_y = defaultdict(list)
    for c, a, b, *_ in walls_h:
        by_y[c].append((a, b))

    cells = [(i, j) for i in range(len(xs) - 1) for j in range(len(ys) - 1)]
    parent = {c: c for c in cells}

    def find(c):
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i, j in cells:
        # neighbour to the right: separated by the vertical wall at xs[i+1]?
        if (i + 1, j) in parent:
            if covered(by_x.get(xs[i + 1], []), ys[j], ys[j + 1]) < EDGE_COVERED:
                union((i, j), (i + 1, j))
        # neighbour below: separated by the horizontal wall at ys[j+1]?
        if (i, j + 1) in parent:
            if covered(by_y.get(ys[j + 1], []), xs[i], xs[i + 1]) < EDGE_COVERED:
                union((i, j), (i, j + 1))

    regions = defaultdict(list)
    for c in cells:
        regions[find(c)].append(c)

    rooms = []
    for cells_in in regions.values():
        boxes = [(xs[i], ys[j], xs[i + 1], ys[j + 1]) for i, j in cells_in]
        area_pt2 = sum((b[2] - b[0]) * (b[3] - b[1]) for b in boxes)
        hit = [lb for lb in labels
               if any(b[0] <= lb["x"] <= b[2] and b[1] <= lb["y"] <= b[3]
                      for b in boxes)]
        if len(hit) != 1:
            continue  # unlabelled region (corridor, shaft) or a merge failure
        rooms.append({
            "label": hit[0],
            "boxes": boxes,
            "area_pt2": area_pt2,
            "bbox": (min(b[0] for b in boxes), min(b[1] for b in boxes),
                     max(b[2] for b in boxes), max(b[3] for b in boxes)),
        })
    return rooms, len(regions)


# -------------------------------------------------------------------- parsing

def read_scale_bar(lines, horiz):
    """Graphic scale bar: '0 ... N m' with a rule running between the ticks."""
    metres = y_text = None
    for text, box in lines:                       # "0 5 m" as a single line
        m = re.fullmatch(r"0\s+([\d.]+)\s*m", text, re.I)
        if m:
            metres, y_text = float(m.group(1)), (box[1] + box[3]) / 2
            break
    if metres is None:                            # ticks split across lines
        end = next((l for l in lines
                    if re.fullmatch(r"[\d.]+\s*m", l[0], re.I)), None)
        zero = next((l for l in lines if l[0] == "0"), None)
        if not end or not zero:
            return None
        metres = float(re.match(r"([\d.]+)", end[0]).group(1))
        y_text = (zero[1][1] + zero[1][3]) / 2
    near = [s for s in horiz
            if s[4] == "line" and abs(s[0] - y_text) < 15 and s[2] - s[1] > 20]
    if not near or not metres:
        return None
    bar = max(near, key=lambda s: s[2] - s[1])
    return (bar[2] - bar[1]) / metres


def read_schedule(page):
    """Panel schedule rows -> {room: qty}. Columns are CKT ROOM DEVICE QTY."""
    raw = [l[0].strip() for l in text_lines(page)]
    try:
        start = next(i for i, t in enumerate(raw) if t.upper() == "QTY") + 1
    except StopIteration:
        return {}, None
    qty, total, i = {}, None, start
    while i < len(raw):
        if raw[i].upper() == "TOTAL":
            total = int(raw[i + 1]) if i + 1 < len(raw) else None
            break
        if i + 3 < len(raw) and raw[i].isdigit() and raw[i + 3].isdigit():
            qty[raw[i + 1].strip()] = int(raw[i + 3])
            i += 4
        else:
            i += 1
    return qty, total


# ----------------------------------------------------------------------- main

def main():
    doc = pymupdf.open(PDF)
    pages = [(p, p.get_text()) for p in doc]

    plan_page = next((p for p, t in pages if SCALE_RATIO.search(t)), None)
    if plan_page is None:
        raise SystemExit("no sheet carries a 'SCALE 1:N' title block")
    sched_page = next((p for p, t in pages if p.number != plan_page.number
                       and "SCHEDULE" in t.upper()), None)

    plan_text = plan_page.get_text()
    ratio = int(SCALE_RATIO.search(plan_text).group(1))
    sheet = SHEET_NO.search(plan_text).group(1)

    lines = text_lines(plan_page)
    horiz, vert, circles = segments(plan_page)

    # pt per metre: from the stated ratio, cross-checked against the scale bar
    pt_per_m_stated = PT_PER_INCH / MM_PER_INCH * 1000.0 / ratio
    pt_per_m_bar = read_scale_bar(lines, horiz)
    pt_per_m = pt_per_m_stated

    # room labels: "OFFICE 101" with "84 m2" on the line below
    labels = []
    for text, box in lines:
        m = ROOM_LABEL.match(text)
        if not m:
            continue
        printed = None
        for other, obox in lines:
            a = AREA_LABEL.match(other)
            if a and abs(obox[0] - box[0]) < 6 and 0 < obox[1] - box[3] < 15:
                printed = float(a.group(1))
                break
        labels.append({
            "room": text, "name": m.group(1), "number": m.group(2),
            "printed_area_m2": printed,
            "x": (box[0] + box[2]) / 2, "y": (box[1] + box[3]) / 2,
        })

    rooms, n_regions = build_rooms(horiz, vert, labels)
    rooms.sort(key=lambda r: r["label"]["number"])

    # receptacle symbols: keep only those landing inside a room
    placed = []
    for cx, cy in circles:
        for r in rooms:
            if any(b[0] <= cx <= b[2] and b[1] <= cy <= b[3] for b in r["boxes"]):
                placed.append({"x": cx, "y": cy, "room": r["label"]["room"],
                               "counts_as": 1, "note": None})
                break

    # "TYP. OF n" multiplies the single symbol the note sits over
    notes = []
    for text, box in lines:
        m = TYP_NOTE.search(text)
        if not m:
            continue
        n = int(m.group(1))
        under = [s for s in placed if box[0] <= s["x"] <= box[2]]
        pool = under or placed
        if not pool:
            continue
        target = min(pool, key=lambda s: (s["y"] - box[3]) if s["y"] > box[3]
                     else abs(s["y"] - box[1]) + 1e4)
        target["counts_as"] = n
        target["note"] = text
        notes.append({"note": text, "multiplier": n, "room": target["room"],
                      "at": [round(target["x"], 1), round(target["y"], 1)]})

    from_plan, symbols = defaultdict(int), defaultdict(int)
    for s in placed:
        from_plan[s["room"]] += s["counts_as"]
        symbols[s["room"]] += 1

    sched_qty, sched_total = read_schedule(sched_page) if sched_page else ({}, None)

    # quantities only transfer between sheets if both are the same issue
    revs = {}
    for pg, txt in pages:
        sm, rm = SHEET_NO.search(txt), REVISION.search(txt)
        if sm and rm:
            revs[sm.group(1)] = {"rev": rm.group(1), "date": rm.group(2)}

    out_rooms = []
    for r in rooms:
        lb = r["label"]
        area = r["area_pt2"] / (pt_per_m ** 2)
        printed = lb["printed_area_m2"]
        qty_plan = from_plan.get(lb["room"], 0)
        qty_sched = sched_qty.get(lb["room"])
        out_rooms.append({
            "room": lb["room"],
            "name": lb["name"],
            "number": lb["number"],
            "area_m2": round(area, 1),
            "receptacles": qty_sched if qty_sched is not None else qty_plan,
            "checks": {
                "area_printed_m2": printed,
                "area_from_geometry_m2": round(area, 2),
                "area_agrees": printed is not None and abs(printed - area) <= 0.5,
                "receptacles_from_schedule": qty_sched,
                "receptacles_from_plan_symbols": qty_plan,
                "symbols_drawn": symbols.get(lb["room"], 0),
                "sources_agree": qty_sched is not None and qty_sched == qty_plan,
            },
        })

    data = {
        "source_pdf": PDF.name,
        "sheet": sheet,
        "scale": f"1:{ratio}",
        "units": {"area": "m2"},
        "rooms": out_rooms,
        "totals": {
            "rooms": len(out_rooms),
            "area_m2": round(sum(r["area_m2"] for r in out_rooms), 1),
            "receptacles": sum(r["receptacles"] for r in out_rooms),
        },
        "provenance": {
            "areas": "wall-centreline geometry, cross-checked against printed labels",
            "receptacle_quantities": (
                f"panel schedule on {SHEET_NO.search(sched_page.get_text()).group(1)}"
                if sched_page else "plan symbols"),
            "scale_pt_per_m_stated": round(pt_per_m_stated, 3),
            "scale_pt_per_m_from_bar": round(pt_per_m_bar, 3) if pt_per_m_bar else None,
            "scale_bar_agrees": (pt_per_m_bar is not None
                                 and abs(pt_per_m_bar - pt_per_m_stated) / pt_per_m_stated < 0.01),
            "wall_grid_regions": n_regions,
            "symbols_on_sheet": len(circles),
            "symbols_inside_rooms": len(placed),
            "typical_of_notes": notes,
            "sheet_revisions": revs,
            "revisions_match": len({(r["rev"], r["date"]) for r in revs.values()}) == 1,
            "schedule_rooms_not_on_plan": sorted(
                set(sched_qty) - {r["room"] for r in out_rooms}),
            "plan_rooms_not_in_schedule": sorted(
                {r["room"] for r in out_rooms} - set(sched_qty)),
            "rooms_where_sources_disagree": sorted(
                r["room"] for r in out_rooms if not r["checks"]["sources_agree"]),
            "schedule_total": sched_total,
            "schedule_total_matches_rows": (
                sched_total == sum(sched_qty.values()) if sched_total else None),
        },
    }

    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))

    draw_overlay(plan_page, rooms, placed, pt_per_m)
    print(f"\nwrote {OUT_JSON.relative_to(HERE)} and {OUT_IMG.relative_to(HERE)}")
    return data


def draw_overlay(page, rooms, placed, pt_per_m):
    """Render what the script decided, so the reading can be eyeballed."""
    zoom = 2
    doc = pymupdf.open()
    new = doc.new_page(width=page.rect.width, height=page.rect.height)
    new.show_pdf_page(page.rect, page.parent, page.number)
    shape = new.new_shape()
    def edge_is_interior(box, side, boxes):
        """An edge shared with another cell of the same room is not a wall."""
        x0, y0, x1, y1 = box
        eq = lambda a, b: abs(a - b) < 0.5
        for o in boxes:
            if o is box:
                continue
            if side == "bottom" and eq(o[1], y1) and eq(o[0], x0) and eq(o[2], x1):
                return True
            if side == "top" and eq(o[3], y0) and eq(o[0], x0) and eq(o[2], x1):
                return True
            if side == "right" and eq(o[0], x1) and eq(o[1], y0) and eq(o[3], y1):
                return True
            if side == "left" and eq(o[2], x0) and eq(o[1], y0) and eq(o[3], y1):
                return True
        return False

    for r in rooms:
        # outline the merged region only -- drawing every cell would invent a
        # wall across rooms that span more than one grid cell
        for box in r["boxes"]:
            x0, y0, x1, y1 = box
            sides = {"top": ((x0, y0), (x1, y0)), "bottom": ((x0, y1), (x1, y1)),
                     "left": ((x0, y0), (x0, y1)), "right": ((x1, y0), (x1, y1))}
            for side, (a, b) in sides.items():
                if not edge_is_interior(box, side, r["boxes"]):
                    shape.draw_line(pymupdf.Point(*a), pymupdf.Point(*b))
        shape.finish(color=(0.11, 0.37, 0.55), width=1.4, dashes="[4 3] 0")
        x0, y0, x1, y1 = r["bbox"]
        shape.insert_text(
            (x0 + 5, y1 - 7),
            f"{r['label']['room']}  {r['area_pt2'] / pt_per_m ** 2:.1f} m2",
            fontsize=8, color=(0.11, 0.37, 0.55))
    for s in placed:
        c = pymupdf.Point(s["x"], s["y"])
        shape.draw_circle(c, 7)
        shape.finish(color=(0.80, 0.22, 0.12), width=1.4)
        if s["counts_as"] != 1:
            shape.insert_text((s["x"] + 9, s["y"] + 3), f"x{s['counts_as']}",
                              fontsize=9, color=(0.80, 0.22, 0.12))
    shape.commit()
    OUT_IMG.parent.mkdir(exist_ok=True)
    new.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(OUT_IMG)
    doc.close()


if __name__ == "__main__":
    main()
