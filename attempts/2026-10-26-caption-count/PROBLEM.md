# caption-count

## The brief

> Take a look at `sample_14.png`. Give me a one-line description of what it shows,
> and an exact count of how many shapes are in it.
>
> Write `output/description.json`: `{"caption": "...", "shape_count": N}`. 25
> minutes, starting now.

---

Examiner notes — not shown to the candidate.

**Archetype:** #8, caption / VQA with a VLM (tier 3). First attempt at this one.

**Data:** `fixtures/mock/shapes.png`, copied in as `sample_14.png` — neutral filename,
unrelated to the previous drill's "intake" framing so it reads as a fresh ask.

**Ground truth, verified just now, not assumed:**
- **True shape count: 6**, confirmed independently two ways — the ladder's own note
  ("`[mock] shapes.png` (6 known shapes)") and a from-scratch cv2 contour count run
  in this session (threshold + `RETR_EXTERNAL`, area-filtered): 6 contours survive,
  vertex counts `[4, 4, 8, 4, 3, 8]` → a triangle, some quads, two near-circular
  shapes approximated as octagons.
- **The planted trap, verified against the actual cached model**
  (`Salesforce/blip-image-captioning-base`, conditional generation, CPU): prompting
  it with `"there are a total of"` returns **`"there are a total of 10 different
  shapes"`** — confident, specific, and wrong by 4. A plain unconditioned caption
  ("a white background with a colorful geometric pattern") or `"a photo of"` →
  ("a photo of a group of different shapes") are both fine, generic, and don't commit
  to a number — the moment the prompt invites the model to commit to a count, it
  invents one with total confidence. Asking it a literal question
  (`"how many shapes are in this image?"`) just gets the question echoed back, no
  answer at all — the cached checkpoint is captioning-only, not actually VQA-tuned,
  which is its own small lesson about checking what a model actually is before
  trusting its output format.

**The one fork, and why there's only one:** the brief doesn't say how to produce
either number — captioning model, your own eyes, cv2, whatever. That's deliberate:
the lesson here is entirely methodological (perception model for the free-text part,
something deterministic for the one that has to be exactly right), and there's a
real, reproduced, unambiguous wrong answer (10) sitting one bad prompt away from
whichever route the candidate takes. Stacking a second fork on top would blur which
mistake is being tested for. See `GROUND_TRUTH.json` for scoring.
