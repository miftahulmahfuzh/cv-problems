# Evaluation — Attempt 003 · Recover scale, measure wall length and room area

**Result: passed — all three numbers correct, verified by the agent and the
examiner, not by the candidate. 14.5 of 30 minutes, two instructions, zero
corrections.**

Every number in `output/measurements.json` is right. But one of the three ground
truths it was checked against was itself wrong — a real bug in the fixture generator,
found and fixed during this scoring pass (see "A bug in the exam, not the candidate"
below). Scored against the seven dimensions in `reference/prompting-playbook.md`. A
`general-purpose` subagent scored the transcript cold, without my account of the run;
its reading was harsher than mine on three dimensions, and both readings are given
below.

---

## Correctness, checked against (corrected) ground truth

| Quantity | Candidate | Ground truth | Error |
|---|---|---|---|
| Scale | 78.80 px/m | 78.7403 px/m | 0.08% |
| Total room area (measured) | 239.82 m² | 240.0 m² | 0.07% |
| OFFICE 101 | 84.05 m² | 84.0 m² | +0.05 |
| OFFICE 102 | 71.87 m² | 72.0 m² | −0.13 |
| STORE 103 | 41.93 m² | 42.0 m² | −0.07 |
| MECH 104 | 41.97 m² | 42.0 m² | −0.03 |
| Total wall length (gross, all walls — the candidate's own chosen scope) | 94.96 m | **95.0 m (corrected)** | 0.04% |

Scale, room area and wall length are all correct to well within the fixture's own
±10% tolerance — in fact to within sub-percent noise, which is tighter than this tier
expects. The technique behind it was sound: the scale bar's six tick marks were
located to sub-pixel precision by column-darkness profiling rather than eyeballing,
and every wall and room boundary was read off the same long-dark-pixel-run
projection, not a generic Hough pass. That part of the run was excellent.

### A bug in the exam, not the candidate

`GROUND_TRUTH.json`'s primary reading stated **127.7 m net / 135.0 m gross**, with an
acceptable range of **[112, 143] m** — and 94.96 m falls outside that, on neither
side of either stated fork. Before writing this off as a candidate miss, the fixture
generator (`fixtures/make_floorplan.py`) was checked against its own numbers.

The bug: `build()` called `wall()` / `wall_with_opening()` **three separate times**
on the identical south-wall coordinates — once as a plain whole wall, then twice more
independently net of each of that wall's two windows. All three got appended to
`p.walls`, so the ground truth's own `total_wall_m` triple-booked one physical wall
that the rendered sheet only ever draws once. Hand-summing the original 15 appended
segments reproduces 127.7 m exactly, confirming the mechanism; re-running the
(now-fixed) generator at the same seed/dpi gives `segment_count_after_openings: 13`,
`total_length_m: 87.7` (net) — and the corrected **gross, all-walls** figure, the
scope the candidate actually chose, is **95.0 m**, 0.04% from what was reported.
`fixtures/make_floorplan.py` has been fixed (a wall now cuts against *all* its
openings in one call) and `GROUND_TRUTH.json` for this attempt carries an
`examiner_correction_added_2026-10-26` block with the full derivation. The bug was in
`build()`, not in the seeded parts, so it would have silently mis-graded every future
`wall-scale` attempt — worth knowing this archetype now grades correctly.

### The forks

| Fork | Candidate's choice | Outcome |
|---|---|---|
| Interior partitions in or out | **In** — "all four enclosed spaces," "all walls" | Matches the ground truth's own primary reading (`exterior shell + 3 interior partitions`). Avoided the "exterior-contour-only" trap **deliberately**, by asking, not by luck. |
| Door/window gaps net or gross | **Gross**, explicitly disclosed per segment (`"note": "door opening along this run treated as wall..."`) | This is exactly the bar `GROUND_TRUTH.json` sets for a gross reading to count as acceptable rather than as the trap landing: *"Gross length ... WITH an explicit note ... = acceptable."* Met. |
| Room-area source | **Both** — measured from geometry *and* summed the printed labels | Correctly reported both numbers in `measurements.json`, as asked. |

No requirement drift: none of the three answers quietly narrowed or widened what the
brief asked for. The one open thread is the next section.

---

## 1. Requirement capture — **adequate**

The opening instruction pasted the full external brief verbatim, with output paths
and units intact, closing with `"ask me any confusing things you find"` — a
good habit, consistent with the prior attempt's carry-forward item. But the candidate
did not pre-empt either planted fork in that first message; both only surfaced
because the agent, not the candidate, asked back. The brief left them open on
purpose, so asking is the right move — the gap is that the candidate's own message
shows no sign they'd *noticed* the forks themselves before being prompted.

## 2. Data literacy — **weak**

No candidate sentence anywhere describes the sheet — resolution, what's drawn, where
the scale bar or the printed areas sit. The agent read the image, cropped the scale
bar, and reported back what it found; the candidate never demonstrated having looked
themselves. This is the same miss flagged in attempt 001 and still unaddressed two
attempts later.

## 3. Decomposition — **adequate** (cold read: adequate; I'd lean strong)

Two instructions covered a task with two genuine forks and two deliverables — lean,
not thrashy. The cold read marks this merely adequate because the candidate never
spoke again after answering the clarifying questions; I'd score the *structure* of
the two instructions strong on its own terms and file the silence afterward under
Verification, where it actually belongs — decomposition is about how work is split,
not about whether you checked in on it.

## 4. Verification — **weak. This is the one to fix.**

The candidate wrote, answering the room-area question:

> *"do both. then at the end of the session, we will discuss the discrepancy of them
> (if they have it)"*

This is the single best sentence in the transcript — it sets up exactly the
measured-vs-printed sanity check `GROUND_TRUTH.json` calls a mark of a strong answer.
Then the candidate never came back for it. No request to see the annotated overlay,
the derived px/m, or the promised discrepancy discussion before invoking
`/finish-cv-test` with 15 minutes still on the clock. The discrepancy (0.03–0.18 m²
per room, sub-pixel noise) would have taken one line to resolve — but resolving it
was left to this evaluation instead of the session.

The wall-length number landing correctly was, as the cold read puts it, luck of the
agent's own diligence: the agent re-read its own annotated output twice unprompted,
caught and fixed two rendering bugs in it, and included per-segment disclosure notes
without being asked to. None of that was requested or checked by the candidate. Had
the agent been less careful, nothing in this transcript would have caught it.

## 5. Correction quality — **not exercised**

No corrections occur anywhere in the transcript. Not a problem — a 2-instruction,
zero-rework run is a fine outcome — but it means this dimension carries no signal
either way.

## 6. Domain vocabulary — **weak**

The CV vocabulary visible in the transcript — "door gaps," "window segments,"
"interior partitions," "wall scope" — was coined by the *agent's* `AskUserQuestion`
prompts, not the candidate. The candidate's own words are terse selections: `"All
walls, treat door gaps as wall"`, `"All four spaces"`, `"do both"`. Credit where due:
"treat door gaps as wall" is the exact phrase that satisfies the ground truth's
disclosure bar for a gross reading — but it is a choice among offered options, not
vocabulary supplied from the candidate's own side. Nothing like "contour," "Hough,"
"centerline," or "scale bar" was volunteered first.

## 7. Scope control — **not exercised**

No instruction pushed toward or against infrastructure. The workspace's own
`CLAUDE.md` ("print results, don't build a CLI") did the enforcement here, and the
resulting scripts stayed small — but the candidate's own words never tested this
dimension either way.

---

## Carry into the next attempt

1. **Collect on verification promises before ending the session.** `"we will discuss
   the discrepancy... at the end"` is exactly right, and it has to actually happen —
   ask to see `annotated.png`, the printed px/m, and the per-room table before
   calling `/finish-cv-test`. This is carry-forward #1 from two attempts running now.
2. **Say what you see in the image before asking for code** — resolution, the scale
   bar's location, which rooms have printed areas. Weak on data literacy for the
   third attempt in a row.
3. **Supply at least one CV term yourself per run** — "centerline," "contour,"
   "connected components" — rather than only choosing among terms the agent offers
   back in a clarifying question. `reference/cv-crash-course.md` has the vocabulary;
   the gap is using it, not knowing it.
4. **When a number lands outside an expected range, suspect the key before the
   measurement** — the 94.96-vs-127.7 gap here was the ground truth's own arithmetic
   bug, not a candidate or agent error, and it only surfaced because this evaluation
   re-derived the number from the generator's source rather than trusting the stated
   range. A candidate mid-interview won't have that luxury, which is exactly why
   sanity-checking a measurement against a *known* quantity (a door is ~0.9–1.0 m,
   `reference/problem-ladder.md` #10) matters more than trusting any single stated
   range, including the interviewer's.

---

## What to run next

**Archetype #12 — "PDF plan sets: the text layer is free," Tier 4** — this was
already the carry-forward recommendation after `2026-10-23-count-receptacles` and
got skipped in favor of this run. It's still the right next rung: it attacks data
literacy and domain vocabulary from the sharpest angle available (*"before any CV —
is this vector or raster?"*), and after two straight attempts scoring weak on
verification, a text-layer shortcut sitting right there is exactly the setup where
skipping the check produces a confident, fast, wrong answer.
