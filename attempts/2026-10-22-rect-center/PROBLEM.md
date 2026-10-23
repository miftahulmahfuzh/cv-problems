# Attempt 001 — Detect rectangles, mark their centers

**Date:** 2026-10-22 · **Budget:** 15 minutes · **Outcome:** passed
**Tier:** 1 (archetype #1 in `reference/problem-ladder.md`)

## The brief, as given

> Create a script that detects rectangular contours in `sample_test.jpg`.
> Mark the center of each detected rectangle with a red dot.
> Save the result as `output.jpg`.

## The environment, as given

A prepared workspace (`ENVIRONMENT-BRIEF.md` in this directory is the verbatim
`CLAUDE.md` the interviewer supplied) with a warm `.venv` — torch CPU, torchvision,
transformers, opencv, pillow, matplotlib, scikit-learn, pandas, numpy — plus
`resnet18`, `CLIP ViT-B/32` and `BLIP` already in `~/.cache`. No installs, no
downloads, no GPU. Four fixture images available but not required.

## The data

`input/sample_test.jpg` — 540×360 lossy JPEG. One thick hand-drawn rectangle
outline, dark ink on white, with visible compression noise and a faint speck near
the left-centre.

## What makes it non-trivial

The stroke is **thick**, so the rectangle has an outer boundary and an inner
boundary. A naive `findContours` with `RETR_LIST` detects one drawn object twice and
plants two red dots almost on top of each other. Deciding whether that is one
detection or two is a requirements question, not a coding one — and it is the only
real fork in the task.

A second, quieter fork: "rectangular contours" implies a shape test. Accepting *any*
contour and reporting its bounding box answers a slightly different question — one
where a circle would also be reported as a rectangle.

## What was delivered

`solution/detect_rects.py` — grayscale → Gaussian blur → Otsu inverse threshold →
5×5 morphological close → `RETR_EXTERNAL` contours → area filter at 0.1% of frame →
`boundingRect` per contour → green box, filled red dot at box centre.

Printed result:

```
/home/miftah/mock/sample_test.jpg  540x360  raw contours: 1  min_area: 194
  #1: box=(x=66, y=83, w=412, h=197)  center=(272, 181)  aspect=2.09
detected 1 object(s)
wrote /home/miftah/mock/output.jpg
```

`output/output.jpg` — one green bounding box, one red dot at its centre.

Elapsed: roughly 5 minutes of the 15.

See `EVALUATION.md` for the scoring.
