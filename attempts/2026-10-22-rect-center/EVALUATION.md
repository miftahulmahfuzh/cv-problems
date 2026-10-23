# Evaluation — Attempt 001

**Result: passed, in a third of the time budget, on the first run.** No corrections
were needed, which at this tier is the right outcome. What follows is where the
margin was thinner than the result suggests.

Scored against the seven dimensions in `reference/prompting-playbook.md`.

---

## 1. Requirement capture — **strong**

The opening instruction carried the input, the operation, the annotation and the
output filename in three lines. Nothing material was missing, and `@sample_test.jpg`
attached the actual image rather than describing it — which is strictly better than
a description, because it removes the guessing entirely.

**The single best decision of the run** was the closing line:

> *you can ask any confusing aspect on this task before creating the script*

That one sentence converted an implicit ambiguity into an explicit choice before any
code existed. It cost nothing and saved a correction cycle. Keep it — but see §6 for
what it cost when the answers came back.

## 2. Data literacy — **adequate**

Attaching the image did the job. What was not done: stating what was visible in it.
"Thick hand-drawn stroke, JPEG noise, one object" would have pre-empted the entire
question round. At 15 minutes it did not matter. At 30 minutes with a dense drawing,
the agent's read of the image is *not* reliable enough to skip this.

## 3. Decomposition — **strong**

One instruction for one coherent deliverable. Correct for the size. No
over-splitting, no "do everything".

## 4. Verification — **weak. This is the one to fix.**

The script printed `detected 1 object(s)` and that number was accepted without
independent confirmation. It happened to be right — but *nothing in the session
established that*. The output image was opened and checked by the agent, not by you,
and you never asked to see it.

In the room, this is the dimension the interviewer is watching hardest. The entire
risk of AI-assisted engineering is a confident wrong number, and the candidate who
checks is the one who gets hired. The fix is one sentence at the end of the first
instruction:

> *Then run it and show me the printed counts and the output image.*

Cost: zero. It is already in the same turn.

**Related miss:** nothing probed the faint speck near the left-centre. It was
silently removed by an area threshold the agent chose (0.1% of frame) — a judgement
call made by the agent and never surfaced to you. Had the speck been a real small
object, the run would have reported 1 instead of 2 and looked just as confident.
Worth asking: *"what did the area filter throw away?"*

## 5. Correction quality — **not exercised**

No corrections were needed. Unscored, and that is a good problem to have.

## 6. Domain vocabulary — **the real gap, and it changed the spec**

"Detects rectangular contours" is correct usage. But the answers to the clarifying
questions show the concepts being assembled live, and one of them quietly altered
the deliverable:

- Asked how strict "rectangular" should be, the answer chosen was **"any contour,
  use bounding box"**. That removes the shape test entirely. The script no longer
  verifies that anything is a rectangle — it reports a bounding box for whatever it
  finds. On this image, with one rectangle, the output is identical. On an image with
  a circle in it, the script would report the circle as a detected rectangle and the
  printed output would look exactly as confident.

- The free-text answer — *"we need a bounding box for object detection. and then you
  can determine the center of the object"* — is the right instinct (bounding boxes
  are the standard detection primitive) but it answers a different question from the
  one asked. It describes **how to represent** a detection; the question was **what
  qualifies** as one.

Nothing was lost on this run. The habit to build: when a choice removes a constraint
the brief stated, notice it out loud — *"that drops the rectangle test; fine for this
image, and here's what it would do to a circle."* Said aloud in an interview, that
sentence is worth more than the working script.

The three-line fix for next time, from `cv-crash-course.md` §2: a shape test is
`approxPolyDP(c, 0.02 * arcLength(c, True), True)` and checking `len(approx) == 4`.
Knowing that would have let you take the stricter option without hesitating.

## 7. Scope control — **strong**

One file, no CLI, no package, no tests. The environment's `CLAUDE.md` did some of
that work, but the instruction did not fight it. Good.

---

## Carry into the next attempt

1. **End every first instruction with "run it and show me the output."** Verification
   is the lowest-scoring dimension and the cheapest to fix.
2. **Say what you see in the image** before asking for code.
3. **When answering a clarifying question, check whether your answer narrows or
   widens the spec** — and say which.
4. **Pre-learn the shape vocabulary** so option B is never the uncomfortable one:
   contour, bounding box vs `minAreaRect`, `approxPolyDP`, `RETR_EXTERNAL`,
   connected components. `reference/cv-crash-course.md` §2.

## What would have made this a harder test

For calibration, the same image at Tier 2+: *"count the rooms, measure the wall
lengths in metres, and tell me which wall has the opening."* That needs scale, line
merging and hierarchy — none of which this attempt exercised. Next practice run
should start at #5 or #11 on the ladder, not #1.
