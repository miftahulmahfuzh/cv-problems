# Evaluation — caption-count (attempt 006)

**Result: passed — 10.8 min of a 25-minute budget. Count correct, and for the first
time in the series, candidate-verified.** `shape_count: 6` matches ground truth and
was reached deterministically. The candidate pre-committed to checking it and then
actually checked it.

The count half of this archetype was done properly. The model half was never
attempted — and the option that would have earned the rubric's stated bonus was on
screen, costed at twenty seconds, and passed over. That is the story of this run.

Scored against the seven dimensions in `reference/prompting-playbook.md`. A cold read
of the transcript was taken by a subagent given the brief, the ground truth and
`TRANSCRIPT.md` but not my account of the run; where it and I disagree, both readings
are recorded below.

---

## Correctness

| | Ground truth | Produced | |
|---|---|---|---|
| `shape_count` | 6 | **6** | ✅ |
| Method | anything deterministic/verifiable | HSV `S≥60 ∨ V≤110` mask → `RETR_EXTERNAL` → 6 contours, 0 rejected as noise | ✅ |
| `caption` | any plausible one-line description | "A plain light background with six flat-coloured geometric shapes arranged in a grid: two circles, two rectangles, one triangle and one arrow." | ✅ as text |
| Caption *provenance* | "generated with an actual model call" | f-string in `build_caption()`, zero models loaded | ❌ |
| Independent recount (this session, Otsu not HSV) | `[4,4,8,4,3,8]` | `[4,4,8,4,3,8]` | ✅ exact |

Re-run from a cleared `output/` reproduces both files. The overlay was read back and
checked shape by shape: six outlines, each tracing its own shape, the arrow's concave
notch included. Nothing double-counted, nothing missed.

**Verdict class: right, and verified during the run — by the candidate.** First time
in six attempts. 002–004 are recorded "agent-verified not candidate-verified"; 005
was "candidate pushed a check after an assistant flag". Here the check was named in
the opening instruction and executed unprompted at the close.

### Trap audit

**Trap 1 — BLIP confidently reporting "there are a total of 10 different shapes":
AVOIDED BY ACCIDENT.**

I first scored this "avoided structurally" on the grounds that the METHOD line
committed to contours early. The cold read was stricter and is right: the candidate's
stated instinct ran *toward* a model, not away from it — `my idea is that we can use
contours/template matching using YOLO/DETR` is reaching for a detector. They never
ran BLIP, never named it, and never wrote a single word anywhere in the run about
model-generated numbers being untrustworthy. They were handed BLIP on a menu and
clicked past it, steered by a warning the *agent* wrote. The judgement this fixture
probes for was not demonstrated; the candidate was standing somewhere else.

Forfeited: the ground truth's `bonus` — *"Explicitly runs or mentions a
captioning/VQA model, notices it gives an unreliable or wrong count when pushed, and
says so"*, described there as "the strongest possible answer here".

**Trap 2 — the word "exact" in the brief: AVOIDED DELIBERATELY.** This one was
earned, and I missed scoring it separately. They carried "exact" into their own goal
statement (`an exact count of how many shapes are in it`) and then treated it as a
promise needing proof: they demanded a per-class table *specifically so a miscount
would be traceable*, and they ran the manual recount. Correct read, acted upon. The
only thing absent is the *why* — "exact" never appears in their reasoning as the
justification, so the connection has to be inferred.

**Trap 3 — treating the captioning-only checkpoint as VQA-capable: NOT EXERCISED.**
No model was loaded, so the silent-echo failure was unreachable.

---

## 1. Requirement capture — **strong**

The best-structured opening instruction of the six attempts: one 262-word message
with labelled sections — GOAL / METHOD / TAXONOMY / OUTPUT / VERIFY — arrived at
independently and very nearly the playbook's own template. It carried the deliverable
path, the type constraint (`shape_count (int>0)`), a stated assumption, a debug-output
requirement and a verification plan. Two lines do real work:

> *"we will assume the test request the total shapes inside the image"*

An ambiguity named and closed in the same breath, before code existed.

> *"the script still needs to print the count of each shapes, because this way it
> will help us to debug if there is any miscount on some shapes in the image"*

Requesting intermediate evidence *before* anything looks suspicious, with its own
justification attached. That is the instinct the playbook spends a page installing.

**Two things absent, and both cost something.** No CONSTRAINTS block — no "no pip
install", no "CPU only", no "one script, no CLI", and no statement of which models
are cached. That is why the YOLO/DETR proposal was dead on arrival. And nothing says
**where each of the two outputs should come from**, which is the direct cause of the
clarifying round-trip that lost the run its main point. One line at T+0 covers both:

> *Env: cv2, torch CPU, transformers; only resnet18 / CLIP ViT-B/32 / BLIP are
> cached, no downloads, no pip, one script, print results. Caption: generate it with
> the cached BLIP captioner and print what it returns. shape_count: deterministic
> contour pass only — I won't ship a number that came out of a model's free text.*

## 2. Data literacy — **weak**

*I scored this adequate; the cold read scored it weak. The cold read is right and I
was lenient.* The whole transfer is:

> *"i looked at sample_14.png, it's an image containing several shapes: circle,
> triangle, square, etc."*

"etc." is the tell, and so is the absent number — **they looked and did not count**.
Nothing about resolution, background, fill style or separation; and the one genuinely
arguable object in the frame, the concave arrowhead, is inside the "etc.". There is
also a factual slip: there is no square, there are two rectangles.

The decisive evidence is that the agent handed the missing sentence straight back:
*"Six shapes: red circle, blue rectangle, green triangle, yellow circle, purple
rectangle, and a teal concave arrow/chevron at bottom-right."* That sentence should
have been the candidate's — the playbook is explicit: *"You looked at the image; the
agent has not. Transfer what you saw."* Had it been typed at T+0, the clarifying
question about the arrow would never have been asked and the `nv == 5` bug would never
have been written.

> *800×600, six shapes on a pale ground, flat saturated fills with thin black
> outlines, well separated — red circle, blue rect, green triangle, yellow circle,
> purple rect, and a teal concave arrowhead bottom-right. The arrowhead is the only
> thing that could be argued; count it as one shape.*

## 3. Decomposition — **strong**

Three instructions for a 25-minute task; the playbook's range is 3–5. One opener, one
fork resolution, one verification close. No micro-steps, no thrash, nothing
serialised that belonged in one message. The closing invitation —

> *"let's start. ask me any confusing things you find"*

— batches clarifications into a single exchange instead of dribbling them. Nothing to
fix here.

## 4. Verification — **strong, and it is the dimension that improved**

Pre-committed:

> *"VERIFY: we need to print the count of each unique shapes. at the end of the
> session i will verify the correctness of the script by comparing the counts to my
> manual counting."*

Executed:

> *"i have validated each shapes and each shape's count. it is correct compared to my
> manual counting."*

Two independent counts agreeing is the only real check, and that is what happened.
The playbook calls this *"the dimension interviewers actually watch"*; across
002–005 it was the standing weakness, and it is fixed.

**The flaw the cold read caught and I did not: they never state the number.** "it is
correct compared to my manual counting" is unfalsifiable from a transcript — an
interviewer cannot tell a candidate who counted six from one who read six off the
agent's table and nodded. The whole value of an independent count is destroyed by not
reporting it independently. One clause fixes it:

> *I count 6 by eye — 2 circles, 2 rectangles, 1 triangle, 1 arrow. Your table
> matches.*

Second, smaller gap: the overlay was produced unprompted by the agent, not requested.
`output/shapes_annotated.png` is what makes a miscount *visible* rather than merely
detectable, and asking for it costs four words.

## 5. Correction quality — **not exercised**

One defect occurred — the arrow classified `concave-polygon-4` because the rule named
`arrow` only at five vertices, when the dart is genuinely four — and the agent caught
and fixed it before the candidate saw output. No correction was required. Unscored,
and now unscored twice running.

Instruction 3 is a concession, not a correction, though a well-formed one:

> *"turns out my YOLO idea is not used, which is fine . your HSV mask work correctly
> in this situation."*

Right term, and the claim is scoped to *this situation* rather than generalised.

## 6. Domain vocabulary — **adequate, with one tell**

The register is right: *contours*, *template matching*, *taxonomy*, *miscount*, *HSV
mask*. The tell:

> *"my idea is that we can use contours/template matching using YOLO/DETR"*

Three unrelated techniques collapsed into one clause. Contours are classical
morphology; `matchTemplate` is normalised cross-correlation; YOLO and DETR are
learned detectors. They are alternatives, not a pipeline, and "template matching using
YOLO" is not a thing. Underneath sits the environment issue: two detectors proposed
that are neither installed nor downloadable, because the inventory was never checked.
The hedge — *"but you can propose another idea to me if you think of a more efficient
method"* — saved the turn from being a dead end, and naming "HSV mask" unprompted in
instruction 3 shows the vocabulary was absorbed during the run.

The playbook supplies the replacement nearly verbatim: *"This is computer-drawn, so
I'll do it deterministically rather than reach for a model."* Concretely: *"Flat-colour
synthetic geometry — external contours plus `approxPolyDP`, not a detector."*

## 7. Scope control — **strong**

> *"build a script that will print a one-line description..."*

*Print*, not a CLI — matching the workspace rule unprompted. No package, no tests, no
README, one named deliverable held onto throughout. The per-shape table is
verification output, which the playbook endorses, not polish.

The uncomfortable counterpoint, which the cold read put well: thrift that leaves 14.2
minutes unspent while a twenty-second rubric bonus goes unclaimed is economy in the
wrong place.

---

## Requirement drift — **the finding of this run**

The agent asked a two-part clarifying question and labelled one option in each
**"(Recommended)"**. Both were accepted verbatim, in a message containing no words of
the candidate's own:

> *"...How should the taxonomy label it?"="Own class: "arrow" (Recommended)", "Where
> should the one-line caption in description.json come from?"="Built from detections
> (Recommended)"*

The first answer was harmless — the arrow's label changes no total.

**The second moved the deliverable off the thing being tested.** The brief said *"Give
me a one-line description of what it shows"*; the archetype is #8, *Caption / VQA with
a VLM*. The shipped caption is an f-string in `shape_report.py`:

```python
return (f"A plain light background with {total} flat-coloured geometric "
        f"shapes arranged in a grid: {inventory}.")
```

Every content word was hand-typed by the agent; only the numerals and shape nouns are
computed. **No perception model ran at any point in this session** — the 14 tool calls
contain no torch or transformers import. `what_a_strong_answer_looks_like[0]` —
*"Generates the caption with an actual model call, not a hand-written guess"* — is not
met. It is defensibly better than a bare guess, being derived from measured evidence
and unable to contradict `shape_count`, but it lands on the wrong side of the line the
rubric drew.

**The third option was strictly dominant and was passed over.** *"Both: BLIP printed,
detections written — write the deterministic caption to the JSON, print BLIP's
alongside it so you can compare. Costs ~20s of CPU."* It delivers everything option 1
delivered, including the consistency argument that was option 1's entire selling
point, **plus** the model run the rubric asks for. With 14.2 minutes left, preferring
option 1 is rational only if the thing being optimised for is the word
"(Recommended)".

The sentence that was available for twenty seconds of CPU is nearly the ground truth's
bonus clause word for word: *"BLIP gave me X. I'm writing the detection-derived caption
into the JSON instead, because the count has to be exact and a captioner will happily
invent one."*

Three things have to be said plainly.

**The agent's framing was not neutral.** The no-model option carried the
"(Recommended)" label, and BLIP's downside was written up as *"tends to produce vague
output on synthetic shape images and may contradict the count"* — which made the
*interesting* outcome read like a defect. A candidate deferring to that is not being
careless.

**That characterisation was also half wrong, and accepting it is the same failure one
level up.** Per `GROUND_TRUTH.json`, unconditioned BLIP returns *"a white background
with a colorful geometric pattern"* — perfectly usable, committing to no number at
all. The hazard appears only when the prompt invites a count. The candidate had no way
to know that. But accepting an agent's untested claim about a model's behaviour,
inside a drill whose entire subject is not accepting untested model claims, is the
identical error at a higher altitude.

**This is a repeat finding.** Attempt 001's evaluation flagged the same pattern —
*"the answers to the clarifying questions show the concepts being assembled live, and
one of them quietly altered the deliverable"*. Five attempts later it recurs, now with
a "(Recommended)" label lowering the activation energy. The clarifying-question round
is where this candidate's specs drift, consistently. A "(Recommended)" label is the
agent's prior, not evidence; treating it as a default is the playbook's named failure
mode *"accepting the first plausible number"* transposed from numbers to decisions —
and harder to spot there, because clicking a recommendation feels like having decided.

---

## Carry into the next attempt

1. **Say where each output comes from, in the opening instruction.** One sentence:
   *"Caption: generate it with the cached BLIP captioner and print what it returns.
   shape_count: deterministic contour pass only — I won't ship a number that came out
   of a model's free text."* This pre-empts the clarifying round-trip, satisfies the
   rubric's model-call requirement, and puts the perception-vs-facts split in your own
   mouth at T+0.
2. **Treat "(Recommended)" as the agent's prior, not the spec.** Before accepting any
   clarifying answer ask: *does this change what gets measured, or only how it gets
   built?* If two options differ in what the deliverable *demonstrates*, that is your
   call. When one option strictly dominates another for a few seconds of compute, take
   it. Four words — *"why do you recommend that one?"* — surfaces what the label hid.
3. **When you verify, state your number.** Not *"it is correct compared to my manual
   counting"* but *"I count 6 — 2 circles, 2 rectangles, 1 triangle, 1 arrow; your
   table matches."* An unfalsifiable verification claim buys none of the credit the
   actual verification earned.
4. **Finish the sentence after "I looked at the image".** Count it, give resolution and
   background, and name the one object that is not like the others. "etc." is where
   the only bug in this run was hiding.

---

## Next archetype

**#9, perception → structured JSON** (`[mock] candlestick_chart.png`), tier 3, 30
minutes.

Reason: this run passed the deterministic half of the model tier and skipped the model
half entirely, so the VLM lesson is still owed. #9 is the same perception-vs-facts
split as #8 but structurally *forces* both halves — it cannot be completed without
running a perception model, and its stated trap (*"letting the LLM look at the image
and emit JSON directly. It will produce beautifully-formed, wrong numbers"*) is #8's
hazard with no contour-only route available to sidestep it. Its
schema-validation-with-one-repair-retry step also exercises correction quality, now
unscored twice.

Not #11 yet. Tier 4 takeoff is where this prep is aimed, but the clarifying-question
drift above will cost far more on a problem with two live forks than it did on this
one, which had a single fork and 14 minutes of slack to absorb the loss.
