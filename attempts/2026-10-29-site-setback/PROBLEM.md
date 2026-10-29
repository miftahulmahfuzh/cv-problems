# Setback check on a site plan PDF

## The brief

> `input/site-plan.pdf` is a site plan, 1:500. Planning rules say no building may be
> closer than 6 m to the parcel boundary. Tell me which ones break that, and by how
> much.
>
> Write `output/setbacks.json` (one entry per building) and `output/overlay.png`
> marking the offenders. 30 minutes.

## Examiner notes (sealed)

Forks: (1) BLDG D crosses the boundary: distance is 0 and it is a violation, but how
it is reported (0, negative, or an inside/outside flag) is the candidate's call;
(2) legend swatch looks like a building; (3) the 3 m shed: included or thresholded,
stated. Traps: BLDG E is rotated, so its nearest corner (not its bbox) sets the
distance, 4.61 m; the dashed boundary is many short segments, not one path, so a
naive line read misses edges; points to metres at 1:500 is 5.669 pt/m.
