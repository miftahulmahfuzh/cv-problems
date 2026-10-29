# Find the walls in a plan image

## The brief

> `input/plan.png` is a scanned floor plan sheet. Find the walls: how many there are,
> and how long they are in total.
>
> Write `output/walls.json` and `output/overlay.png` with each wall you found drawn
> in a different colour. 25 minutes.

## Examiner notes (sealed)

Forks: (1) a wall interrupted by a door or window: one wall or two (13 drawn
segments vs 7 logical walls); (2) length in pixels or metres (the sheet carries a
5 m scale bar and the text 1:100; 200 dpi raster = 78.74 px/m).
Traps: legend frame and title-block frame are long straight lines but are not walls;
scale bar is a thick horizontal line; thin door leaves and window double-lines;
walls are thick (about 6 px) so Canny gives two edges per wall unless thresholded.
