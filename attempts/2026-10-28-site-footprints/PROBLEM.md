# Footprint areas from a site plan PDF

## The brief

> `input/site-plan.pdf` is a site plan. For every building on the sheet, I want its
> footprint area in square metres, and whether it sits within the parcel boundary.
>
> Write `output/buildings.json` (one entry per building) and `output/overlay.png`
> showing what you picked up. 30 minutes.

## Examiner notes (sealed)

Forks left open: (1) the legend swatch is drawn exactly like a building; (2) "sits
within" for BLDG D, which straddles the east boundary: report inside/outside split or
just a flag; (3) the 3 m x 3 m shed: building or not. Scale is only given as the text
"1:500" plus a 20 m bar; points to metres is 72/25.4*1000/500 = 5.669 pt/m.
Traps: BLDG C has a courtyard hole (area 800, not 900); BLDG E is rotated 30 degrees
so bbox area is wrong; BLDG B is L-shaped; centroid / bbox shortcuts fail.
