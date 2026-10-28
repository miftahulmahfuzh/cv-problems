# Recover the trades table from a statement image

## The brief

> `input/statement.png` is a broker statement. Get me the trades out of it as data:
> one record per trade, with each cell's text and its pixel bounding box.
>
> Write `output/trades.json` and `output/overlay.png` with your boxes drawn on the
> image. 20 minutes.

## Examiner notes (sealed)

Forks: (1) the totals block (Gross value / Total fees / NET DEBIT) and the header
key-values (Account, date...) sit near the table: in or out, say which; (2) numbers as
strings with commas or parsed to numbers. Traps: no vertical rules, only faint row
rules and a shaded header; "QTY (lot)" header has a space/paren; totals block aligns
with the PRICE and VALUE columns and can be swallowed into the table.
