# PDF plan sets — the text layer is free

The archetype where the expensive wrong road is most tempting. A drawing *looks* like
an image problem. It almost never is.

`reference/cv-crash-course.md` routes you here: *"Does it have a text layer? → yes →
you have text AND coordinates for free. No OCR."* This document is what to do next.

---

## Before anything else, three lines

```python
import pymupdf
doc = pymupdf.open(path)
print(len(doc))                       # how many sheets? the brief often won't say
print(bool(doc[0].get_text().strip()))  # text layer? -> no OCR
print(len(doc[0].get_drawings()))     # vector paths? -> no pixel CV
```

**Say the page count out loud.** A plan set is a *set*. The quantities usually live
on a schedule sheet, not the plan, and briefs say "the sheet number" in the singular
while handing you four pages. Attempt 003's entire difficulty was that page 2
existed.

**There is no OCR engine in this environment, deliberately.** If you catch yourself
saying "OCR the table", you have mis-identified the problem — the table is text with
bounding boxes. The term to use is **text layer**.

---

## Text with coordinates

`get_text()` gives you a string; `get_text("words")` gives you the string *and where
it is*, which is what lets you associate a label with a place:

```python
for x0, y0, x1, y1, word, block, line, word_no in page.get_text("words"):
    ...
```

Regroup words into lines with `(block, line)` as the key — room labels and their area
captions arrive as separate "lines" a fixed distance apart, so a label like
`OFFICE 101` is matched to `84 m2` by testing *"same left edge, 10–15 pt below"*,
not by string proximity.

---

## Vector geometry, not pixels

`page.get_drawings()` returns stroked/filled paths. Each has `"items"` (the
primitives), `"rect"` (its bounding box), `"width"` (the **lineweight**) and
`"type"` (`"s"` stroke, `"f"` fill).

Two tricks carry most plan-set work:

**Classify by shape signature.** Build a string of item kinds and bucket on it:

```python
kinds = "".join(it[0] for it in path["items"])   # "l" line, "re" rect, "c" curve
# "cccc" in an 8x8 box = a circle = one symbol instance
```

**Separate walls from everything else by lineweight.** Walls are drawn heavy, doors
and windows and scale bars light. `width >= 2.0` is usually a clean cut — print the
distinct widths first and look.

> `width` is a **lineweight, not a thickness.** A 2.2 pt wall stroke at 1:100 is not
> a 78 mm partition. Plans carry no wall thickness; areas you compute are
> **centreline gross**, and no amount of cross-checking inside the PDF will tell you
> otherwise. Say so when you report an area.

**Areas of filled shapes.** A building footprint on a vector sheet is a filled path;
take its vertices from the `l` / `qu` / `re` items and use the shoelace formula,
`0.5 * abs(sum(x_i*y_{i+1} - x_{i+1}*y_i))`. No contour and no bounding box, so L-shapes
and rotated rectangles come out exact. A **courtyard** is usually one keyhole path:
outer ring, a bridge edge walked in both directions, then the inner ring wound the
other way. Shoelace over the whole path gives outer minus hole with no special case
(the bridge cancels). To get the part inside a boundary, clip with Sutherland-Hodgman
against the (convex) parcel, then shoelace the result. A legend swatch is drawn with
the same fill as the buildings, so exclude it by position or by its neighbouring text.
Scale: derive it from the scale bar (`rect.width` of the heavy line = the labelled
length) and check it against the printed ratio (`pt_per_m = 72/25.4*1000/ratio`).

---

## Reconstructing rooms from walls

Don't try to trace polygons. Build a grid and merge it:

1. Collect the distinct `x` of vertical walls and `y` of horizontal walls → a grid.
2. Each grid cell is a candidate room fragment.
3. Two adjacent cells belong to the **same** room if no wall covers their shared
   edge. Compute *coverage*: the union of wall segments along that edge, over the
   edge length. Threshold at ~0.5.
4. Union-find the cells; each merged region should contain exactly one room label.

Coverage with a threshold is what makes **doors work correctly**. A door is a gap in
a wall — a 25 pt gap in a 340 pt wall is 92% covered, still a wall. A missing
partition is 0% covered. A hard "is there any segment here" test gets this wrong in
both directions.

**Free check:** the room areas should sum to the building envelope with no remainder.
If they don't, your merge is wrong. This catches a bad threshold instantly.

---

## Scale

Two independent sources, and they should agree:

```python
# stated: "SCALE 1:100" in the title block
pt_per_m = 72 / 25.4 * 1000 / ratio          # 1:100 -> 28.3465 pt/m

# measured: the graphic scale bar, "0 ———— 5 m"
pt_per_m = bar_length_pt / bar_metres
```

Agreement proves the drawing hasn't been rescaled. When you hunt the bar, filter to
segments **derived from lines, not from rectangle edges** — a title-block rectangle
sitting at a similar `y` is longer than the bar and will win a naive `max(length)`.

---

## The three traps, every time

**1. The legend.** It holds one specimen of every symbol, outside the building
outline. It inflates any count by exactly one per symbol type. Don't special-case the
legend box — invert it: **count only symbols that fall inside a reconstructed room.**
Anything outside the envelope drops out for free, and you get the drawn-vs-placed
numbers as a by-product (`9 on sheet, 8 inside rooms`).

**2. `TYP. OF n`.** A note meaning one drawn symbol stands for *n* installed devices.
It is **text**, parseable, and it is the only on-plan evidence that drawn ≠ installed.
Attach it to the symbol whose x-span the note sits over — not to the nearest symbol,
and not to the whole room:

```python
under = [s for s in symbols if note_x0 <= s["x"] <= note_x1]
```

A pixel-perfect symbol detector still gets the quantity wrong. That is the point of
the trap.

**3. The schedule governs.** When a set has a panel/device schedule, it typically
says in print that its quantities govern over the symbols. Find that sentence and
quote it. The schedule is the bid number; the drawn count is the cross-check.

---

## Reporting: keep the disagreement

The strongest answer reports **both numbers labelled** and names which one a bid uses:

```json
"receptacles": 7,
"checks": {
  "receptacles_from_schedule": 7,
  "receptacles_from_plan_symbols": 7,
  "symbols_drawn": 3,
  "sources_agree": true
}
```

Two rules about this shape, both learned the hard way in attempt 003:

- **Never reconcile two sources with a rule supplied by someone who knows the target
  number.** The arithmetic may be independent; the *choice of rule* is not. A rule
  validated only against the case whose answer you were given has a sample size of
  one, and a `sources_agree: true` built that way claims more than it has earned.
- **A room present in one source and absent from the other is worse than a numeric
  mismatch** — it prices as zero or vanishes silently. Check set membership both
  ways, not just the values.

Free cross-checks that cost nothing and belong in every run of this archetype:

| check | catches |
|---|---|
| schedule `TOTAL` row vs sum of its rows | a mis-parsed table |
| computed areas vs printed labels | a bad scale or a bad merge |
| room areas vs building envelope | a wrong wall threshold |
| scale bar vs stated ratio | a rescaled drawing |
| same REV on every sheet | quantities transferred between out-of-sync issues |

---

## Draw the overlay

Render the decisions back onto the sheet — room outlines, counted symbols, the
multiplier — and *look at it*. In attempt 003 this caught a phantom wall drawn across
rooms spanning two grid cells. When you outline a merged region, skip edges shared
with another cell of the same room or you will draw walls that don't exist.

```python
new.show_pdf_page(page.rect, page.parent, page.number)   # original underneath
shape = new.new_shape()                                   # annotations on top
```

## Dashed boundaries and legend swatches in `get_drawings()` (site-setback, 2026-10-29)

- A dashed parcel line may be **one** path with a `dashes` pattern (`dashes != "[] 0"`, no fill)
  or many short segments. Select by `dashes`, then take `rect`; if you get several, union them.
  Do not assume either form: print the count first.
- The legend swatch is a filled rect with the same grey as the buildings. Drop any fill whose
  vertical centre matches a legend word (`EXISTING`) and sits just left of it. "Inside the parcel"
  is not a safe test, because a building can legitimately cross the boundary.
- Setback = min over footprint vertices and the four parcel sides, signed so that past the
  boundary is negative. A rotated building is then handled by its corner, not its bbox.
