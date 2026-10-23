# Evaluation — Attempt 002 · Count duplex receptacles on sheet E-101

**Result: passed — correct count, correct positions, verified by the agent and not
by the candidate. 7.7 of 30 minutes, one substantive instruction, zero corrections.**

The number is right and the overlay proves it. But the candidate finished with 22
minutes unspent and no independent basis for believing 7 — which is the same gap
this harness flagged in attempt 001, after it was written down as carry-forward item
number one.

Scored against the seven dimensions in `reference/prompting-playbook.md`. A
`general-purpose` subagent scored the transcript cold, without my account of the run;
where it and I disagree, both readings are given.

> **Note on the numbers.** The first `finish` run reported 12.1 minutes and six
> instructions. Both were wrong: the transcript renderer was counting harness-injected
> turns — skill bodies, the automatic `[Image: original WxH ...]` notes — as candidate
> words, which inflated the opening instruction to 2739 words, and it was dropping the
> candidate's `AskUserQuestion` answers entirely. `bin/cvtest.py` was fixed during
> scoring (`isMeta` turns excluded, the answer prefix corrected, the clock stopped at
> `/finish-cv-test` so re-running no longer bills the write-up to the candidate). The
> corrected figures — **7.7 minutes, two instructions, a 63-word opener** — are used
> throughout.

---

## Correctness, checked against the fixture

`fixtures/floorplan.json → positions.receptacles_pt`, converted at 200/72:

| # | ground truth (px) | reported (px) | error |
|---|---|---|---|
| 1 | 351.9, 435.2 | 351.5, 436.1 | 1.0 px |
| 2 | 981.9, 435.2 | 981.5, 436.0 | 0.9 px |
| 3 | 351.9, 1025.8 | 351.5, 1026.9 | 1.2 px |
| 4 | 1493.7, 1065.2 | 1493.3, 1066.6 | 1.5 px |
| 5 | 863.8, 1104.6 | 863.2, 1105.2 | 0.8 px |
| 6 | 989.7, 1104.6 | 989.2, 1105.2 | 0.8 px |
| 7 | 1115.7, 1104.6 | 1115.1, 1105.7 | 1.2 px |

All seven found, none spurious, worst error 1.5 px — the systematic ~1 px y-bias is
the ink centroid sitting below the symbol's anchor because of the stem, and it is
irrelevant at this scale. `symbols_drawn_in_the_plan_area: 7` matched exactly.

**This was verified during the run, by the agent:** the overlay was rendered and read
back by eye against the printed table, and an independent whole-sheet
`matchTemplate` sweep was run as a second count that agreed. That is two independent
counts, which the ladder calls "the only real check". It is the right standard — it
was simply not the candidate who applied it.

### The traps

| Trap | Outcome |
|---|---|
| Legend holds one of every symbol | **Avoided deliberately.** The legend glyph was used *as the template* and excluded geometrically, by testing whether a detection falls inside the building footprint rather than by hardcoding a box. |
| Banked run of three merged by over-eager NMS | **Avoided structurally**, not by reasoning about the trap. Connected components don't cluster, so the primary pass is immune; the cross-check sweep used a 20 px suppression radius against 126 px spacing. Had the method been match-map-first, this is where it would have broken. |
| Sloppy template with wall pixels in it | **Avoided.** Template cropped from the legend component's own bbox with 3 px padding — scores 0.80–0.92 on the seven devices. |
| `TYP. OF 4` is the only evidence drawn ≠ installed | **Named, unprompted — and then mis-priced. See below.** |

### The one real defect in the deliverable

The overlay's grey `KEY - not counted` label overlaps the word `LEGEND`. It was moved
there to escape a *different* collision, and the fixed image was republished without
being read back a second time. Cosmetic, no effect on the count — but it is the
verification habit failing in miniature, inside the very run whose weakest dimension
is verification.

---

## 1. Requirement capture — **weak**

The output contract was transferred verbatim, which was the right instinct:

> *from the test: "One script in this directory. Print the count and the coordinates. Write the overlay to `output/E-101_marked.png`"*

Quoting beats paraphrasing and it carried the path, the print requirement and the
one-script constraint through intact. But the quote stopped one sentence early. The
brief's fourth deliverable —

> *At the end, tell me what you'd want to fix before this ran against a real plan set.*

— never reached the agent in any form. Also dropped: "the level 1 power plan from a
small office fit-out", "2339×1653", "I need to be able to check it", and the
30-minute budget.

The agent volunteered three robustness notes at the end anyway (the wall-merge
failure mode, STORE 103's genuine zero, the notation risk). That is the requested
deliverable arriving **by luck**. On a sheet where the agent was less forthcoming,
the brief's closing ask would simply have gone unanswered and the candidate would
not have known it was missing.

## 2. Data literacy — **weak**

The whole description of the input: *"we have an image input : input/E-101.png"*.

The brief handed over the subject and the resolution for free and neither was passed
on. Nothing about the legend box, the symbol size, the fact that the sheet is
computer-drawn rather than scanned — all of which bear directly on whether template
matching is even the right tool.

**Where I disagree with the cold read:** it scored this weak on the transcript alone
and could not see that the candidate's *first* act of the session was to commission
an image viewer — *"embed every image in input/ as a base64 data URI at a size I can
actually inspect, each labelled with its filename and pixel dimensions"*. That is a
deliberate investment in being able to look, and it is why this harness has a worklog
at all. The score stays weak because none of what that viewer showed was ever
transferred into the instruction — but the instinct behind it is sound and worth
keeping. Build the viewer, then *use* it in the next message.

## 3. Decomposition — **strong**

One message carried the task, the constraint and the output contract, and did not
serialise write / run / print into three round-trips. Twelve minutes, no thrash, no
interrupts. For a task this size that is the correct shape.

**Where I disagree with the cold read:** it scored this *adequate* on the grounds
that one message was also the *only* message. That conflates two dimensions. The
deficit in this run is verification, not decomposition, and the same fact should not
be charged twice. Decomposition was right.

## 4. Verification — **weak. Second run running, same dimension, after it was carried forward.**

There is no verify clause anywhere in the run. The candidate never asked for the
printed count, never asked to see the overlay, never counted seven by eye, and never
pushed back on a number. The agent checked its own work — which it did thoroughly —
and the candidate's confidence in `7` rests entirely on that.

Attempt 001's carry-forward item #1 was:

> **End every first instruction with "run it and show me the output."**

It was not carried in. The brief even supplied the motive sentence — *"I need to be
able to check it"* — and that sentence was dropped, so the overlay reached the agent
as an output format rather than as the candidate's checking instrument.

Nine words, in the slot where *"ask any confusing things you find"* already sits:

> *then run it, print the count and the coordinates, and show me the overlay.*

Twenty-two minutes of budget went unspent. There was no cost to checking.

## 5. Correction quality — **not exercised**

Zero corrections were issued; none were needed. Nothing to score and nothing to fix.

## 6. Domain vocabulary — **weak**

Nothing beyond the brief's own nouns: "receptacle count", "position", "overlay". No
"template", "match map", "threshold", "non-maximum suppression", "connected
components", "legend region" — and NMS radius on the banked run was a planted trap
the candidate had already read about in `reference/problem-ladder.md` §11.

It cost nothing here because the agent chose well without steering. The exposure is
that the candidate had no vocabulary with which to *challenge* the method — and on
this sheet the method it chose (connected components first, template match as
cross-check) is not the one the ladder prescribes. That was a good deviation, but
nobody in the room would have known whether to trust it.

`reference/cv-crash-course.md` §186 (template matching + NMS) and §217 (connected
components) are the two sections to have in the mouth, not just on disk.

## 7. Scope control — **adequate**

Quoting *"One script in this directory"* verbatim did real work: no CLI, no package,
no argparse, no test suite.

But the directory ends the run with **two** Python files — `count_receptacles.py` and
`make_worklog.py`. The second exists because the candidate's own session-setup
instruction commissioned a republishing worklog, and the workspace `CLAUDE.md`
requires it be updated on every output image. It is session infrastructure, not
takeoff code, and that defence is sound. It is still a literal miss against a
constraint the candidate chose to quote, and in a real room it invites exactly one
awkward question.

**Where I disagree with the cold read:** it scored this *strong* from the transcript,
having no view of the filesystem. With the directory listing in hand, adequate.

---

## Requirement drift

Two instances, one of them material.

**1. A deliverable was dropped in transmission.** Covered in §1: the brief's closing
"tell me what you'd want to fix before this ran against a real plan set" never
reached the agent. Answered anyway, by luck.

**2. The notation fork was named, ratified — and mis-priced by the agent.** This is
the subtle one, and the fault is mine rather than the candidate's.

Ground truth calls this "the single most Boon-relevant sentence available here", and
it *was* said, unprompted, before any code was written. The candidate was offered a
choice and picked a branch:

> *(b) for the row annotated "TYP. OF 4", count the 3 glyphs actually drawn rather
> than honour the note*

Per `GROUND_TRUTH.json`, naming the distinction or asking which is wanted is full
marks, and both happened. But the alternative branch was costed wrong. I offered
"honour the note → the row is 4, total 8". The fixture says otherwise:

```json
{"x": 310.9, "y": 397.7, "kind": "banked", "represents": 4}
```

The `TYP. OF 4` note multiplies **the one symbol it sits beside**, not the group. So
the row is 4 + 1 + 1 = 6 and `devices_actually_specified` is **10**, not 8. The
candidate chose between two options, one of which was a number that does not exist
on this sheet. Nobody in the run ever produced 10.

The habit this buys, for both sides of the conversation: when a fork is surfaced,
**price every branch before choosing** — *"what's the total under each reading?"* A
fork with one branch costed wrong is worse than a fork left unnamed, because it
closes with a confident wrong alternative on the record.

---

## Carry into the next attempt

1. **Paste the brief verbatim into the first message — every sentence, nothing
   summarised.** This run dropped an entire deliverable in transmission and got away
   with it. Transcription is free; deciding which sentence doesn't matter is not.
2. **Append the verify clause: *"then run it, print the count and the coordinates,
   and show me the overlay."*** This is carry-forward #1 from attempt 001, unactioned.
   Verification is now 0 for 2 and it is the dimension interviewers watch hardest.
3. **When a fork comes back, make the agent price every branch before you pick
   one** — *"what's the total under each reading?"* Had that been asked here, the
   8-vs-10 error surfaces in one line and the strongest available answer ("7 drawn,
   10 specified, here's why they differ") lands.
4. **Spend two of the twenty-two unused minutes reading the input yourself, then
   transfer what you saw** — resolution, what's drawn, where the legend sits. You already built the
   viewer in the first instruction of the session; the next step is quoting it back.

---

## What to run next

**Archetype #12 — "PDF plan sets: the text layer is free", Tier 4, 30 minutes**, on
the vector PDF of this same sheet (`fixtures/make_floorplan.py --pdf`).

Three reasons it is the right next rung. It is the run `PROBLEM.md` explicitly
reserved — *"Raster only... That is archetype #12 and belongs to its own run."* It
attacks the dimension that just scored weakest from a different angle: with
`get_text("words")` the string `TYP. OF 4` arrives with a bounding box attached, so
the notation problem stops being a thing you notice and becomes a thing you have to
*parse and act on* — and the 10 that nobody reached this time is sitting right there.
And it rewards the one sentence this candidate has not yet had to say out loud:
*"before any CV — is this vector or raster?"*

Risk to watch: with a text layer available, an unverified run can produce a confident
wrong answer faster than this one did. Item 2 above matters more there, not less.
