# wall-scale

## The brief

> You've got one sheet, `E-101.png` — a level-1 power plan. Raster only this time, no
> PDF, no coordinate list.
>
> I need two numbers off it: the total length of the walls, in metres, and the total
> floor area of the rooms, in square metres. The sheet gives you what you need to
> recover scale — use it, and be able to show me how you got from pixels to metres,
> not just hand me the final numbers.
>
> Write `output/measurements.json` with your two numbers and the scale factor you
> derived, and `output/annotated.png` showing what you detected and measured. 30
> minutes, starting now.

---

Examiner notes — not shown to the candidate.

**Archetype:** #10, Scale: pixels → real units (tier 4). First attempt at this one.

**Data:** `fixtures/make_floorplan.py --seed 11 --dpi 200`, page 1 only (E-101 power
plan), rasterised to PNG. The PDF and the receptacle/notation trap (archetype #11,
already drilled in `2026-10-23-count-receptacles`) are deliberately withheld — this
sheet is pixels-only so the candidate cannot shortcut scale recovery via a text layer
or `get_drawings()`.

**The two forks left open on purpose:**

1. **What counts as "the walls."** The brief says "the walls," not "the exterior
   walls" or "every wall including partitions." Ground truth's primary number sums
   *all* 15 segments (exterior shell + 3 interior partitions). A candidate who asks
   "interior partitions too, or just the envelope?" has found the fork; either answer
   is gradeable as long as they say which they picked and the number matches that
   choice.
2. **Whether door/window openings reduce the length.** A wall with a door in it is
   geometrically one run interrupted by a gap. The generator already encodes this as
   two separate segments (the gap is not wall), so the net reading is the intended
   one — but a candidate who merges collinear Hough segments across the gap and
   reports the gross run, *and says so*, has made a defensible and explained choice,
   not a silent error. Reporting the gross number with no acknowledgment that a door
   or window sits in that run is the trap landing.

See `GROUND_TRUTH.json` for the acceptable numeric ranges for every combination of
the two forks above.
