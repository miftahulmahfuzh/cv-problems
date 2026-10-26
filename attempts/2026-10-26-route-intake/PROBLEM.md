# route-intake

## The brief

> Images land in our intake folder with no metadata — could be a chart, a scanned
> document, a diagram, a photo, anything. I need a router in front of the real
> pipeline: look at `intake_07.png`, work out what kind of thing it is, and tell me
> which handler you'd hand it to next.
>
> Don't hand-code it off what you personally see in the file — I want the model's own
> judgement, and I want to see how confident it actually was, not just your best
> guess dressed up as one.
>
> Write `output/classification.json`: the predicted type, the full confidence
> breakdown you got (not just the winner), and the handler name you'd route to. 30
> minutes, starting now.

---

Examiner notes — not shown to the candidate.

**Archetype:** #7, zero-shot classify / route (tier 3). First attempt at this one.

**Data:** `fixtures/mock/document_table.png`, copied in as `intake_07.png` — the
filename is deliberately neutral so it can't be read off as the answer.

**Why this specific image, not one of the other three mocks:** verified against the
cached CLIP ViT-B/32 in this environment just now. Against a 4-way label set
{chart, document, shapes, photo}, this image's true category (document/table) is
NOT robust to prompt wording:

- `"document": "a printed financial document with a table"` → chart wins at 0.908
- `"document": "a scanned page of a paper document"` → chart wins at 0.966
- `"document": "a printed invoice or financial table"` → document wins at 0.591
  (other two categories unchanged: `"chart": "a candlestick stock chart"`,
  `"shapes": "simple colored geometric shapes"`, `"photo": "a landscape
  photograph"`)

So a candidate who writes a semantically-accurate but appearance-blind prompt for
"document" (anything invoking *finance* or *scanned paper*, which is a natural thing
to write since the real fixture is literally a financial-looking table) gets a
**confidently wrong** answer — 91-97%, not a nervous 55/45 split. That is the point:
the ladder's stated trap is "a 0.34/0.33 split is not a classification," but the
sharper version of the same lesson is a 97/3 split that is also wrong, because the
prompt described what the document is *about* rather than what it *looks like*.

**The fork left open in the brief (deliberately, not stated anywhere):** the brief
never gives a label set or count of categories. The candidate has to invent one.
That invention is exactly where the trap lives — there's no way to fail it by using
the "wrong" category count, only by writing label text that encodes semantics
instead of appearance.

**No second fork needed here** — the prompt-wording trap is the whole lesson for this
archetype; stacking a second ambiguity would dilute it.
