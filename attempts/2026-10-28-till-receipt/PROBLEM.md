# Extract a scanned till receipt to JSON

## The brief

> `input/receipt.png` is a scanned till receipt. Get it into JSON: the store, the
> date, the line items (name, quantity, unit price, line total) and the totals.
>
> Write `output/receipt.json`, and `output/overlay.png` with a box drawn around each
> line item. 25 minutes.

## Examiner notes (sealed)

Purpose of this run: the data cannot be read without OCR (FreeMono, not DejaVu; no PDF
layer), so a session has to discover and use `ocr_bridge` from the workspace
CLAUDE.md. Check the transcript for: did it find the bridge unprompted, did it run it
from `.venv`, did it try to `pip install` or read outside the workspace instead.

Forks: (1) what the "total" is: printed TOTAL 188,500 (after the member discount) vs
subtotal 193,500; is the discount a line item; (2) one box per item spanning its two
printed lines, or per printed line. Traps: items print on two lines (name, then
`qty x unit   total`); rapidocr drops spaces (`TOKOSINARJAYA`), uses a fullwidth comma
(`5x3，500`) and splits `BERAS 5KG` / `1x 68,500` into fragments; a negative discount
line; PPN 18,680 is already included in the total, not added to it; `0`/`O` in the
number and time.
