# Driving Claude Code under a 30-minute clock

The test is not "can you write OpenCV". It is "can you direct an agent to produce
correct work faster than a person could, and can you tell whether what came back is
right". The second half is where candidates lose.

---

## The budget

| Minutes | What happens | Failure if you skip it |
|---|---|---|
| 0–2 | **You** read the task and the data. Open the image. State the task back. | You solve the wrong problem for 25 minutes |
| 2–4 | First instruction: full context, constraints, output contract | Ten clarifying round-trips |
| 4–8 | Claude writes v1; you read it while it runs | You accept code you have not read |
| 8–12 | Run it. **Look at the output image.** Read the printed numbers. | You ship a wrong count confidently |
| 12–22 | One or two targeted corrections | Thrash — five vague "still wrong" messages |
| 22–27 | Robustness and edge cases; a second verification | "Works on the sample" is all you have |
| 27–30 | Narrate what it does, what it assumes, what would break | Silence at the end reads as not understanding |

The clock pressure is real but the first two minutes are never the thing that makes
you late. Thrashing in the middle is.

---

## The opening instruction

One message, five parts. This is the single highest-leverage habit.

```
[CONTEXT]  Input is <what it actually is>. The env has <venv path>, cv2/torch/
           transformers, no internet, no OCR engine, CPU only.
[GOAL]     <the deliverable, in one sentence>
[CONSTRAINTS] One file at <path>. No pip install. Deterministic — no model
           downloads. Keep it under ~60 lines.
[OUTPUT]   Print <the exact numbers I want to see>. Save the annotated image to
           <path>.
[VERIFY]   Then run it and show me the printed output.
```

Why each part pays for itself:

- **Context** stops the three wasted turns where it tries `pip install pytesseract`.
- **Goal** in one sentence forces *you* to decide what you are asking for.
- **Constraints** are what keep a 30-minute task from becoming a package with a CLI,
  a config file and a test suite. Claude will happily build all three.
- **Output** is the contract. "Print the box and center of each detection" means you
  can check the answer without reading the code.
- **Verify** gets the run included in the same turn instead of a separate round trip.

### Say what the data *is*, not just where it is
"Detect rectangles in image.jpg" versus "image.jpg is a 540×360 scan of a
hand-drawn rectangle on white paper, with JPEG noise" produce different code. The
second gets you a blur and a morphological close without asking. **You looked at the
image; the agent has not. Transfer what you saw.**

### Name the ambiguity before it bites
Yesterday's genuinely good move: deciding what "one rectangle" means when a thick
stroke has two edges. If you can see a fork — a thick outline, a nested shape, a
legend that would be double-counted, a tilted scan — *name it in the instruction*
and state which branch you want. Leaving it implicit costs a full correction cycle.

---

## The seven things being graded

This is the rubric `/finish-cv-test` scores against.

**1. Requirement capture.** Did the first instruction contain the task, the
constraints and the output contract? Or did the real requirements leak out over four
messages?

**2. Data literacy.** Did you look at the input before instructing? Did you tell the
agent what you saw — resolution, noise, colour, what is actually drawn?

**3. Decomposition.** One instruction per coherent step. Not "do everything", not
fifteen micro-steps. A 30-minute task is usually 3–5 instructions.

**4. Verification.** Did you check the *output artifact*, not just that the script
exited 0? Did you ask for intermediate evidence when the answer looked suspicious?
**This is the dimension interviewers actually watch.** An agent that returns a
plausible wrong number and a candidate who accepts it is the whole risk of
AI-assisted engineering, and they are testing for exactly that.

**5. Correction quality.** When something was wrong, did you say *what* was wrong
and *what you expected instead* — or just "that's not right, try again"? A
correction without an observation is a coin flip.

**6. Domain vocabulary.** Did you say "contour", "bounding box", "non-maximum
suppression", "the text layer" — or describe them longhand? The right word shortens
the loop and signals that you know the field.

**7. Scope control.** Did you stop the agent from building a CLI, a package, a test
suite, a README? Did *you* stay on the deliverable? Time spent on polish is time not
spent on being correct.

---

## Failure modes, in order of how often they happen

**Vague correction.** "It's still wrong." → Say: *"It found 2 objects; there is 1.
The thick stroke is being detected as an outer and an inner contour."* Observation,
then expectation. Now it is one fix instead of three guesses.

**Accepting the first plausible number.** The script runs, prints `detected 7
objects`, and you move on. Seven is only right if you counted seven yourself. Open
the overlay.

**Accepting the option labelled "(Recommended)".** When the agent asks you a
clarifying question, it will often mark one answer as recommended. That label is its
opinion about *implementation cleanliness* — it has no idea what the exercise is for,
what the interviewer is probing, or which branch demonstrates more. Before accepting
any clarifying answer, ask yourself one question: **does this change what gets
measured, or only how it gets built?** If two options differ in what the deliverable
*demonstrates*, that is your call and not the agent's. The cheapest counter is four
words: *"why do you recommend that one?"* — it costs one line and surfaces the
tradeoff the label hid. Observed twice: attempt 001 (a clarifying answer silently
loosened "rectangular" to "any contour") and attempt 006 (a recommended caption
source removed the only model call from a model-tier problem).

**Letting it build infrastructure.** Claude defaults to engineering: argparse, a
`main()`, a config, error handling for cases that cannot occur. In a 30-minute test
that is pure loss. Say "one short script, print results, no CLI" in the first
message — and it is in the workspace `CLAUDE.md` precisely so you do not have to.

**Verifying without stating the number.** *"I checked, it's correct"* is
unfalsifiable from a transcript. An interviewer cannot distinguish a candidate who
counted six from one who read six off the agent's table and nodded — so an
independent count that is not reported independently buys none of the credit it
earned. Say the number, and say the breakdown: *"I count 6 by eye — 2 circles, 2
rectangles, 1 triangle, 1 arrow. Your table matches."* The check was the expensive
part; the clause that makes it legible is free.

**Not looking at the input yourself.** You cannot tell whether a result is right if
you never looked at the data. Thirty seconds with the image is the cheapest
verification available.

**Serialising what could be one message.** "Write the script." … "Now run it." …
"Now print the centers." Three round-trips, each ~45 s of model time. One message
with all three costs one.

**Going quiet.** The interviewer is evaluating your thinking, and an agent working
in silence shows them nothing. Narrate the approach and the tradeoff while it types.

---

## Things worth saying out loud in the room

- *"Let me look at the image first."* — then actually describe what you see.
- *"This is computer-drawn, so I'll do it deterministically rather than reach for a
  model."*
- *"I'll use the model for what it's good at — telling me what this *is* — and
  something deterministic for anything that has to be a number."* — the perception /
  facts split, said as a reason rather than a tool list.
- *"Before I trust that number, let me have it write the mask out and look at it."*
- *"That's a fork: a thick outline has an inner and an outer edge. I want one
  detection per drawn object, so — external contours only."*
- *"I don't have an OCR engine in this environment. I can give you the table's
  structure, which is the part that needs vision."*
- *"Pixels aren't the answer — let me pin the scale first."*

Each of these is a sentence that makes the interviewer's notes easier to write.

---

## What the agent is good and bad at, in 30 minutes

**Good:** recalling exact API signatures you half-remember; writing the boilerplate
loop; trying three thresholds in one run; explaining what a flag does; producing a
clean overlay for you to inspect.

**Bad without guidance:** choosing between two valid interpretations of a vague
requirement; knowing what the image looks like; deciding when "good enough" is
reached; resisting the urge to generalise. Those four are your job, and they are
precisely what the interview is scoring.
