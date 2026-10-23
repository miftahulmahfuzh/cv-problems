# Evaluation — Attempt 003 · Structure a two-sheet plan set into bid data

**Result: passed — every number correct, in 22.2 of 30 minutes. But agent-verified,
not candidate-verified.** All fourteen checked values match ground truth, all four
planted traps were avoided, and both free cross-checks in the text layer were taken.
None of that was asked for. The verification that makes this run look strong was the
agent's initiative, not the candidate's instruction — which is the same finding as
attempt 001, now with a harder trap and a bigger margin of luck.

Scored against the seven dimensions in `reference/prompting-playbook.md`.

A cold-read subagent scored the transcript independently, without my account of the
run. Where we disagree it is marked **[disagreement]**, with both positions.

---

## Correctness — right, and verified during the run

| | expected | produced | |
|---|---|---|---|
| sheet / scale | E-101 · 1:100 | E-101 · 1:100 | OK |
| OFFICE 101 / 102 / STORE 103 / MECH 104 | 84 / 72 / 42 / 42 m² | identical | OK |
| total area | 240.0 m² | 240.0 m² | OK |
| receptacles per room | 3 / 7 / 1 / 1 | identical | OK |
| receptacle total | 12 | 12 | OK |
| symbols drawn on plan | 8 | 8 | OK |
| symbols including legend | 9 | 9 | OK |

**Traps:**

1. **Two pages, brief implies one** — *avoided deliberately.* `len(doc)` and a page
   loop were the second tool call of the run, before any other analysis.
2. **Rasterise and do pixel CV** — *avoided deliberately.* `get_text("words")` and
   `get_drawings()` throughout. Pixels were used only to draw the verification
   overlay, never to measure.
3. **Legend inflates the symbol count by one** — *avoided deliberately.* 9 circles
   found, 8 inside rooms; the legend specimen falls outside the building envelope and
   was excluded by the point-in-room test, then stated explicitly.
4. **`TYP. OF n` is the only on-plan evidence that drawn ≠ installed** — *hit, with
   candidate help.* The agent found the note and the 3-vs-7 discrepancy on its own
   but could not decode the convention, and asked. See §Drift.

**Harness bugs this run exposed, now fixed:**

- `GROUND_TRUTH.json` said the note reads `TYP. OF 6`. The fixture says `TYP. OF 5`.
  `.exam/generator-truth.json` is authoritative — `"means": "the leftmost banked
  symbol stands for 5 devices"` — and the candidate's reading matched the
  generator's intent exactly. Corrected in two places.
- `make_floorplan.py` hardcoded `"TYP. OF 4"` in its own truth prose while the
  derived `notes` array said 5. Now interpolated from the actual value.
- **`cvtest.py` lost one of the candidate's four instructions.** A message typed
  while the agent is mid-turn persists as a `queued_command` attachment, never as
  `type: user`, so `load_turns` never saw it. The cold read scored this transcript
  without it. Fixed; `TRANSCRIPT.md` regenerated with all four.

---

## 1. Requirement capture — **adequate**

The brief was pasted verbatim, which is the right instinct — the output contract
(`output/plan.json`, "print it", the closing stake-a-bid question) transferred intact
and nothing leaked out later. The candidate added two things:

> *"let's start to implement ONE script. ask me any confusing things you find"*

The second half earned its keep. It produced one `AskUserQuestion` that surfaced both
genuine forks in a single round-trip instead of three correction cycles. This is the
same move that worked in attempt 001 and it is becoming a reliable habit — keep it.

What is still missing is the playbook's CONTEXT and VERIFY parts: no statement of
what the data is, and no statement of what evidence to produce. See §2 and §4.

## 2. Data literacy — **weak**

Not one observation about the input appears in any instruction before the agent had
already parsed the file. No page count, no "it's vector with a text layer", no
mention of a legend. The hinge of the entire problem reached the candidate *from the
agent*:

> agent: *"The set has two sheets — E-101 (1:100) and E-601 (NO SCALE)"*
> candidate: *"Only the scaled sheet"*

That is a reaction to news, not a prior. The playbook's line for this archetype is
blunt: *"You looked at the image"* is the point of the dimension, and here the
candidate looked at the PDF only after the agent rendered it into the worklog.

Real credit where it is due, and it is substantial: at T+8.6 the candidate correctly
identified the banked-run convention —

> *"one recepticle icon represent 5 recepticles (hence the text: TYP. OF 5). so the
> total is 7"*

— which matches the generator's intent word for word. That is genuine domain
knowledge the agent did not have and could not derive. It arrived eight minutes late
and only because the agent asked.

## 3. Decomposition — **adequate**

Four instructions in 22.2 minutes with zero thrash, inside the playbook's 3–5 band.
But count what they were: one scoped the whole build, one answered the agent's own
question, one asked a policy question, one asked for narration. That is **one work
instruction** for the entire task.

Between T+8.6 and T+14.4 the candidate typed nothing while the agent wrote the
script, ran it, corrected itself four times and rendered a verification overlay. The
playbook's 12–22 band is "one or two targeted corrections"; the candidate made zero,
because the agent caught its own bugs first.

## 4. Verification — **weak. This is the repeat finding and the one to fix.**

The candidate never asked to see anything. No "show me the overlay", no "print the
per-room counts before you write the JSON", no "check the schedule TOTAL against the
sum of its rows" — which `GROUND_TRUTH.json` names as one of two free cross-checks
sitting in the text layer. The nearest thing was:

> *"walk me through it"*

which is a request for narration, not for an artifact. `verify_rooms.png` exists, and
it is the thing that proves the room-merge and the symbol assignment are right — the
agent built it, read it back twice, and found a real bug in it (a phantom wall drawn
across rooms spanning two grid cells). The candidate saw it only as a side effect of
the mandated worklog.

**[disagreement]** The cold read called this dimension untouched by the candidate. I
disagree in part — the T+8.6 message is verification *thinking*:

> *"what do you think we should do if these 2 gives different receptacle quantity?"*

That question directly caused the `sources_agree`, `rooms_where_sources_disagree`,
`schedule_rooms_not_on_plan` and `plan_rooms_not_in_schedule` fields to exist, and
the last two closed a real silent-failure hole where a room present in one source and
absent from the other would have priced as zero. The cold read never saw this message
because the harness had dropped it.

It still scores **weak**, and the reason matters: the dimension asks *"did you check
the output artifact"* and *"did you ask for intermediate evidence"*. Both answers are
no. Designing a good discrepancy *policy* is not the same as checking a number, and
8-drawn-vs-12-scheduled is precisely the plausible-wrong-number trap this dimension
exists to catch.

## 5. Correction quality — **not exercised**

Zero interrupts, zero corrections. Nothing the candidate typed names a wrong
observation and an expected one. The dimension never came up — partly because the
agent self-corrected before anything reached the candidate, and partly because the
candidate never looked at an intermediate result closely enough for it to come up.

## 6. Domain vocabulary — **weak**

**[disagreement]** The cold read found "not one term of art" and scored on three
instructions. With the recovered fourth, the candidate used *plan*, *table*, *sheet*,
*source of data*, *more reliable* — real provenance reasoning. So the finding is not
absence of vocabulary. It is sharper than that:

> *"second is **OCR** of the table in the second sheet"*

This is the one technical term the candidate reached for, and it is **wrong**. There
is no OCR anywhere in this problem. Both sheets carry a real text layer; the schedule
arrives as exact characters from `get_text()`, and the symbols are vector circles
from `get_drawings()`. The candidate ranked the two sources correctly but for a
reason that does not hold — and the term that *would* have held, **"text layer"**, is
the single phrase this entire archetype is built around. It never appeared.

`receptacle` is misspelled twice, which costs nothing mechanically but would be
noticed in a room.

## 7. Scope control — **adequate**

> *"let's start to implement ONE script"*

Capitalising ONE is a cheap constraint and it held: one `plan_to_json.py`, no CLI, no
argparse, no test suite. Credit — this was explicitly a failure mode in the playbook
and the candidate pre-empted it in two words.

Against it: the agent spent its first nine tool calls and roughly eight minutes
building `build_worklog.py` and `worklog.tmpl.html` before properly parsing the PDF,
and the candidate never redirected. The worklog is mandated by the workspace
`CLAUDE.md` so it is not chargeable as a scope violation — but a quarter of the clock
passed unsupervised before the actual problem was touched.

---

## Requirement drift

**Instance 1 — the sheet answer narrowed the deliverable.**

`PROBLEM.md` says "the sheet number and drawing scale", singular, with two sheets in
the set. That is fork 1, and the acceptable resolutions are *"report both, **or**
report E-101's **and say why E-601 has none**."*

> *"Only the scaled sheet"*

Four words that took the half of that branch which drops information and omitted the
half that preserves it. The brief never said to exclude the unscaled sheet; the
candidate asserted it. In the shipped artifact, `plan.json` opens `"sheet": "E-101",
"scale": "1:100"` with no top-level acknowledgment that a second sheet exists.

**[disagreement]** The cold read calls this the problem's primary failure mode. I
don't, and the ground truth's own wording is the reason: that failure is *"silently
answering for page 1 only, **without ever noting a page 2 exists**."* Page 2 was
noticed in the second tool call, quoted verbatim to the candidate, used for every
quantity, and survives in the output under `provenance.receptacle_quantities` and
`provenance.sheet_revisions`, which lists both sheets at REV 2. Nothing was silent.
It is a real narrowing, and a reviewer loading the JSON cannot see at a glance that
the quantities came off a different sheet than the one named — but it is the mild
version of the failure, not the primary one.

One thing I own here: I offered "Only the scaled sheet" as a menu option. I did state
the consequence in the option text, so the choice was informed — but a fork offered
as a tidy multiple choice invites a tidy answer, and the candidate took it.

**Instance 2 — the `TYP. OF 5` answer collapsed the cross-check into itself.**

This is the subtle one and it is worth the space.

The agent asked a *which-source-governs* question: the schedule says 7, the plan
shows 3 symbols and an unreconcilable note — which goes in the field? The candidate
did not rule on the source. They asserted that the two sources *do* reconcile, and
the agent coded that assertion. OFFICE 102 now carries
`"receptacles_from_schedule": 7, "receptacles_from_plan_symbols": 7,
"sources_agree": true`, and globally `"rooms_where_sources_disagree": []`.

**[disagreement]** The cold read calls the result "the same number written twice". I
think that overstates it. The multiplier 5 was read off the plan's own text, and
which symbol receives it was decided by geometry — the note spans x 302.4–330.8 and
only the symbol at x 311.0 falls inside it. The arithmetic path really is plan-side
and never touches the schedule.

But the cold read's underlying point is correct and the distinction it is pointing at
is the right one: **the rule was supplied by a human who already knew the target
number.** The derivation is independent; the *choice of derivation* is not. A rule
validated against the single case whose answer you were handed has a sample size of
one, and `sources_agree: true` claims more confidence than that evidence supports.
Both readings the geometry cannot exclude — "this row of 3 is typical of 5 rows" (15)
and "5 in this room" (5) — are only ruled out by the schedule, which is the thing the
check was supposed to be independent of.

The candidate's reading was *right*, and confirmed right by the generator. The
problem is that nothing in this run could have distinguished "knew the drafting
convention" from "proposed something that happens to reconcile" — and neither can the
JSON. The strongest available answer is the opposite shape: **8 drawn, 12 scheduled,
bid 12**, preserving the disagreement as the finding rather than dissolving it.

The pattern across both instances: the agent asked twice *which interpretation to
adopt*, and both times the candidate answered with a fact about the drawing instead
of a ruling on the deliverable. Choosing between valid interpretations of a vague
requirement is the human's job in this drill; supplying drawing trivia and letting
the interpretation fall out of it is a different, weaker move.

---

## Carry into the next attempt

1. **Never answer a clarifying question without attaching what you want to see.**
   The single highest-leverage change. At T+5.6 this reply costs the same round-trip
   and fixes both drifts and the verification score at once: *"Both sheets, scale per
   sheet. Keep drawn and scheduled as two separate fields per room, and show me every
   room where they disagree before you write the JSON."*

2. **Type one observation about the data before the first instruction.** Open the
   file, say what it is: *"two-page vector PDF, real text layer on both sheets, don't
   rasterise."* Three facts, one line, and it pre-empts the entire fork round. The
   phrase **"text layer"** is the one to own for this archetype —
   `reference/pdf-plan-sets.md` covers `get_text("words")` bounding boxes and
   `get_drawings()` path extraction.

3. **Ask for the artifact, not the narration.** *"walk me through it"* got prose;
   *"show me the overlay with each room outlined and each counted symbol marked"*
   gets the thing that proves the answer. The overlay existed and caught a real bug —
   the candidate just never asked for it.

4. **When two sources disagree, preserve the disagreement.** Report both labelled,
   name which one the bid uses, and say why. Reconciling them with a rule you supplied
   destroys the only independent check you had.

---

## Next archetype

**Run a problem with no schedule and no reconciling note** — a single-sheet symbol
count where the drawn geometry is the *only* source, with an occluded or overlapping
symbol so the count has to be defended from the image rather than confirmed by a
table. This run's quantities were ultimately settled by a text table that stated its
own authority; the candidate was never forced to defend a number with nothing to
check it against. That is the gap.

Secondary candidate: the same plan-set archetype at a seed where `TYP. OF n` makes
the plan and schedule *genuinely* disagree, so that asserting a reconciliation
produces a visibly wrong answer instead of a right one.
