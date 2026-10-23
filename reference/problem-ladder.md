# The problem ladder

Twelve archetypes, easiest first. Together they cover nearly everything a 30-minute
CV live-coding test can ask, and the top of the ladder is what Boon actually does
all day.

For each one: **the ask** (how an interviewer says it), **the recipe** (the steps,
in order), **the trap** (what goes wrong), **verify** (how you know you are right),
and **the line** (what to say while it runs).

Practice data for each is named at the end of its section. `[synthetic]` means
`fixtures/make_*.py` generates it with known ground truth; `[mock]` means one of the
four fixtures in `fixtures/mock/`; `[real]` means fetch a public drawing.

---

## Tier 1 — Shapes and geometry

### 1. Detect objects, mark their centers
*Yesterday's test. The warm-up of warm-ups.*

**The ask:** "Find the rectangles in this image and put a dot at the center of each."

**Recipe**
1. `imread` → check for `None` → `cvtColor` to gray.
2. `GaussianBlur(5,5)` — buys robustness against compression noise for free.
3. `threshold(... THRESH_BINARY_INV | THRESH_OTSU)` — ink becomes white blobs.
4. `morphologyEx(MORPH_CLOSE, (5,5))` — repairs broken strokes.
5. `findContours(RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)`.
6. Filter by `contourArea` against a fraction of the frame, not a pixel constant.
7. Per survivor: `boundingRect` → center `(x + w//2, y + h//2)` → draw.
8. Print the boxes and centers as numbers, then write the annotated image.

**The trap:** a thick outline has two edges, so `RETR_LIST` detects every object
twice. And forgetting `_INV` segments the paper instead of the ink.

**Verify:** open the output image and count the dots yourself. Print `len(contours)`
before and after the area filter — if the filter removed 400 things, your threshold
is wrong, not your filter.

**The line:** *"External contours only, so a thick stroke counts once."*

*Data: `[mock] shapes.png`, `attempts/2026-10-22-rect-center/input/sample_test.jpg`*

### 2. Classify each shape (triangle / rectangle / circle)
**The ask:** "...and tell me what kind of shape each one is."

**Recipe:** as above, then per contour `approx = approxPolyDP(c, 0.02*arcLength(c,True), True)`
and branch on `len(approx)`: 3 triangle, 4 quad (square if the box aspect is within
~10% of 1), 5 pentagon, >8 circle. Cross-check a circle with *circularity*
`4*pi*area/peri**2` ≈ 1.

**The trap:** the epsilon. Too small and a rectangle has nine corners; too large and
a pentagon collapses to a triangle. It must be a fraction of the perimeter so it
scales with shape size.

**Verify:** draw the label onto each shape and look. Eight shapes, eight labels.

*Data: `[mock] shapes.png` (6 known shapes)*

### 3. Measure and sort
**The ask:** "Give me the three largest objects, with their areas and dimensions."

**Recipe:** contours → `contourArea` → `sorted(key=..., reverse=True)[:3]`. Report
both `contourArea` (true pixels) and `boundingRect` (w×h), and say which one the
question meant. If a real-world unit is wanted, you need **scale** — see #10.

**The trap:** answering in pixels when the asker meant millimetres, and not saying so.

---

## Tier 2 — Structure

### 4. Recover a table's grid
**The ask:** "Extract the table from this document."

**Recipe**
1. Binarize inverted.
2. Isolate the rules with directional kernels: horizontal lines survive
   `morphologyEx(OPEN, getStructuringElement(MORPH_RECT, (40, 1)))`; vertical lines
   survive `(1, 40)`.
3. Intersect the two masks (`cv2.bitwise_and`) → the grid's corner points.
4. Or skip morphology: a **projection profile** — `bw.sum(axis=1)` — has a peak at
   every horizontal rule. Peaks are row boundaries. Fewer knobs, easier to explain.
5. Cell `(i, j)` is the crop between consecutive boundaries.
6. Read the glyphs only if you have an OCR engine. **This environment does not.**

**The trap:** borderless tables, where there are no rules to find — then you cluster
the *text* blobs by their y-centres instead, which is the more general algorithm.

**Verify:** overlay the detected grid on the original and look at it. Print
`rows × cols` and check it against what your eye sees.

**The line:** *"No OCR engine here, so I can recover the structure but not the
glyphs — structure is the half that needs vision, and it's what I'd hand to OCR."*

*Data: `[mock] document_table.png`; worked solution in `reference/snippets/table_extract.py`*

### 5. Find the lines (walls, rules, axes)
**The ask:** "Find the walls in this floor plan." / "Find the gridlines."

**Recipe**
1. Gray → `Canny(50, 150)` (or threshold, for clean CAD output).
2. `HoughLinesP(threshold=80, minLineLength=<1-2% of the diagonal>, maxLineGap=10)`.
3. Classify each segment by `atan2(y2-y1, x2-x1)`: horizontal, vertical, or neither.
4. **Merge collinear segments.** Hough returns a wall broken into pieces. Group by
   (orientation, offset) and take the union of extents. Skipping this step is the
   most common reason a wall count comes out at 300.
5. Report: count, total length, the extremes.

**The trap:** `maxLineGap` silently decides whether a doorway splits a wall in two.
Pick it deliberately and say why.

**Verify:** draw the merged lines in color over the original at 50% opacity.

*Data: `[synthetic] fixtures/make_floorplan.py`, `[real]` any public plan sheet*

### 6. Deskew / flatten a photographed document
**The ask:** "This was photographed at an angle — straighten it first."

**Recipe:** largest contour → `approxPolyDP` down to 4 points → order them
(top-left, top-right, bottom-right, bottom-left by sum and difference of
coordinates) → `getPerspectiveTransform` to a clean rectangle → `warpPerspective`.
For pure rotation without perspective, `minAreaRect().angle` gives the skew and
`getRotationMatrix2D` + `warpAffine` fixes it.

**The trap:** corner *ordering*. Unordered corners produce a mirrored or
hourglass-warped image. There is a standard sum/diff trick; use it.

**Verify:** the output's edges should be parallel to the frame.

---

## Tier 3 — Models

### 7. Zero-shot classify / route by image type
**The ask:** "Work out what kind of image this is and handle it accordingly."

**Recipe:** CLIP embed image; embed `"a photo of a {label}"` for each candidate;
softmax over cosine similarities; branch on the argmax. This is the *router* that
makes a multimodal pipeline look designed rather than hardcoded.

**The trap:** the prompt template matters more than people expect; bare label words
are measurably worse than `"a photo of a ..."`. And CLIP cannot count or localise —
do not route counting through it.

**Verify:** print the full probability vector, not just the argmax. A 0.34/0.33
split is not a classification.

*Data: all four `[mock]` fixtures; worked solution in `reference/snippets/route.py`*

### 8. Caption / VQA with a VLM
**The ask:** "What's in this image?" / "Does this drawing have a title block?"

**Recipe:** BLIP conditional generation for a caption; for a question, ask it as
conditional text. Keep images small on CPU.

**The trap:** VLMs hallucinate specifics with total confidence — counts, numbers,
labels that are not there. The senior move is to use the VLM for *perception* and
something deterministic for *facts*, then validate.

**The line:** *"I'd use the VLM to tell me what kind of sheet this is, and cv2 to
tell me how many of them there are. Asking the VLM to count is how you ship a wrong
number."*

*Data: `[mock] photo_landscape.jpg`; worked solution in `reference/snippets/pipeline.py`*

### 9. Perception → structured JSON
**The ask:** "Turn this image into structured data my backend can consume."

**Recipe:** perception layer (CLIP tags + BLIP caption + cv2 measurements) →
a small LLM or a template that composes those *facts* into JSON → **schema
validation with one repair retry**. Never let the model invent a field it was not
given evidence for.

**The trap:** letting the LLM look at the image and emit JSON directly. It will
produce beautifully-formed, wrong numbers.

**Verify:** assert the schema; assert every number appears in the evidence.

*Data: `[mock] candlestick_chart.png`; worked solution in `reference/snippets/pipeline.py`*

---

## Tier 4 — Boon-grade

### 10. Scale: pixels → real units
**The ask:** "How long is that wall?" / "How many metres of conduit?"

**Recipe**
1. Find the scale reference. In order of reliability: the PDF's own coordinate
   system (points → inches → the sheet's stated scale), a dimension string with
   leader lines, a drawn scale bar.
2. Derive `units_per_pixel` from it, and **print it**.
3. Multiply measured pixel lengths by it.
4. Sanity-check against a known quantity: a door is ~0.9 m, a storey is ~3 m. If
   your wall comes out at 400 m, your scale is wrong, not the building.

**The trap:** rendering the PDF at a different dpi than you computed the scale at.
Pin the dpi in one constant and use it everywhere.

**The line:** *"Pixels aren't an answer. Let me pin the scale first, then every
measurement is in metres and checkable."*

### 11. Count repeated symbols
*The actual Boon task: "takeoff".*

**The ask:** "Count the electrical outlets / doors / sprinkler heads on this sheet."

**Recipe**
1. Get one clean instance of the symbol — ideally cropped **from the legend**,
   which is where drawings define their own vocabulary.
2. `matchTemplate(TM_CCOEFF_NORMED)` over the sheet.
3. Threshold the score map (~0.75–0.85), collect candidate boxes.
4. **NMS** — otherwise each symbol yields a cluster of hits.
5. Repeat for rotated copies of the template (0/90/180/270 at minimum) and NMS
   across the union.
6. Report the count **and** the coordinates, and overlay them for inspection.

**The trap:** template matching is neither scale- nor rotation-invariant, and a
symbol drawn at two sizes on one sheet needs two templates. Also: a legend contains
one of every symbol — remember to exclude the legend region from the count, or your
total is always one too high.

**And the real trap, which is Boon's whole pitch:** drawings use *notation*, not
repetition. A run of outlets may be drawn as one symbol with a "typ. of 6" note, or
a banked run with an end marker. Pixel counting gets that wrong no matter how good
it is. **Say this out loud** — recognising it is the difference between a candidate
who did the exercise and one who understood the domain.

**Then read the note correctly, which is a second trap underneath the first.**
"TYP. OF 4" beside a row of three symbols has two plausible readings and they give
different totals:

- *the note describes the group* → the row stands for 4 devices, one of which was
  not drawn;
- *the note multiplies the symbol it sits beside* → that one symbol is 4 devices and
  the others are 1 each, so the row is 4 + 1 + 1 = 6.

The second is the normal drafting reading and it is what `make_floorplan.py` emits
(`{"kind": "banked", "represents": 4}`). Attempt 002 named the fork — full marks —
and then offered the wrong alternative total, so the stronger answer was never on
the table. **Naming a fork is only half of it: price every branch before choosing.**
Say *"7 drawn, 10 specified, and here is why they differ"* — one sentence, both
numbers, and the reason. A fork with a mis-costed branch is worse than a fork left
unnamed, because it puts a confident wrong alternative on the record.

**Verify:** overlay and count by eye on a small crop; compare with the schedule
table if the sheet has one. Two independent counts agreeing is the only real check.

*Data: `[synthetic] fixtures/make_floorplan.py` emits a known symbol count*

### 12. PDF plan sets: the text layer is free
**The ask:** "Here's a PDF of a building's internal plan. Pull out X."

**Recipe**
1. **Check for a text layer first.** Most CAD-exported PDFs are vector with real
   text, and `pymupdf` hands you every string *with its bounding box* — no OCR, no
   error, instant.
   ```python
   import pymupdf
   doc = pymupdf.open("plan.pdf")
   page = doc[0]
   words = page.get_text("words")      # [(x0,y0,x1,y1, word, block, line, word_no)]
   drawings = page.get_drawings()      # vector strokes: lines, rects, curves
   ```
   `get_drawings()` is the quiet superpower: on a vector plan you get the **actual
   wall geometry as line segments**, exactly, with no Hough and no thresholding.
2. Only if there is no text layer, render and treat it as an image:
   ```python
   pix = page.get_pixmap(dpi=200)
   img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)
   ```
3. Use the text layer to find the **title block** (sheet number, scale, revision)
   and the **legend**, then use geometry for everything else.
4. Multi-sheet: index sheets by their number before trying to reason across them.

**The trap:** rendering a vector PDF to pixels and then doing CV on it is throwing
away exact data to recover it approximately. Check `get_text()` first, every time.

**The line:** *"Before any CV — is this vector or raster? If it's vector I already
have the geometry and the text with coordinates, and the problem is bookkeeping, not
perception."*

*Data: `[real]` any public plan-set PDF; `[synthetic] fixtures/make_floorplan.py --pdf`*

---

## How to use this ladder

Run one practice attempt per archetype, in order, with `/spawn-new-cv-test`. Tiers 1
and 2 should become muscle memory — you should be able to narrate the recipe without
looking. Tier 4 is where the interview is actually decided, and #11 and #12 are the
two that are worth rehearsing more than once.

The single highest-leverage habit across all twelve: **write the intermediate image
to disk and look at it.** Not the final answer — the mask, the contours, the
template-match heat map. Every bug on this page is visible in one glance at an
intermediate, and invisible in the final number.
