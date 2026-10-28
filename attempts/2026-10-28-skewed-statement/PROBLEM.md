# Flatten a photographed statement

## The brief

> `input/photo.jpg` is a phone photo of a printed broker statement on a desk.
> Give me back the page as if it had been scanned: flat, upright, filling the frame.
>
> Write `output/flat.png`, and `output/notes.json` with whatever you used to get there.
> 20 minutes.

## Examiner notes (sealed)

Forks: (1) output size / aspect ratio: original page is 900x1150 (A4-ish 0.783), any
aspect within ~3% of that is fine, a stated choice beats a default; (2) whether to
keep a margin around the page edge. Traps: dark desk behind the page, drop shadow
along two edges, left-to-right lighting gradient, page is 4-corner perspective not
just rotation (affine will leave visible keystone), corner ordering (TL,TR,BR,BL)
easy to get wrong and yields a mirrored/rotated output.
