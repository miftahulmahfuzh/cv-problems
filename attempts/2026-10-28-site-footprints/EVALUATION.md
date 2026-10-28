# Evaluation — Attempt 2026-10-28 site-footprints

**Result: passed in 14.9 min of 30. Output correct on every field; verification was
asserted by the candidate, never stated as a number.** All six entries match
`GROUND_TRUTH.json` within 1% (they match exactly): A 300, B 630, C 800, D 600
(400 in / 200 out, `within_parcel: false`), E 360, shed F 9. The legend swatch was
excluded and the scale came from the 20 m bar (0.17639 m/pt, identical to the 1:500
figure). The candidate sent 3 instructions; no interrupts, no corrections.

Scored against the seven dimensions in `reference/prompting-playbook.md`. A cold read
of the transcript (a subagent that saw only the brief, ground truth and transcript)
was taken; disagreements are marked.

---

## Correctness: right, verified by the agent, not by the candidate

- **Agent-verified:** the script cross-checked the vector areas against a raster
  connected-components pass (every blob 2-4% under, as expected from outline pixels),
  and the overlay was read back.
- **Candidate:** "i checked your overlay.png . all good from me." and "every fields is
  there in every entry." That is a check, but it contains no count, no area and no
  breakdown, so a reader of the transcript cannot tell it from agreeing with the
  agent's table. Per the playbook this is *right, unverified from the record*.

### Traps

| Trap | Outcome |
|---|---|
| Legend swatch has the building fill | Avoided deliberately: the agent asked, the candidate confirmed "EXISTING STRUCTURE is just a legend item" |
| BLDG C courtyard (800 not 900) | Avoided by the agent's method (polygon area, keyhole path). The agent flagged it; the candidate only confirmed afterwards: "i forgot to mention the inside square of C" |
| BLDG E rotated, bbox would be wrong | Avoided by accident of method (polygons, no bbox). Never discussed |
| BLDG B L-shape | Same as E |
| Several path items per building | Handled by the agent; never discussed |
| Shed F (fork) | Included, decided by the candidate with a reason: "we need to assume that what the task required is EVERY building" |
| BLDG D straddles (fork) | Candidate chose `within_parcel: false` plus the 400 inside figure. This is the ideal resolution |

---

## 1. Requirement capture — **adequate**

The brief was pasted whole, both output paths were stated, and the closing line
*"let's start , ask any confusing things you find"* produced both forks (shed,
straddler) before any code existed. That sentence is the best decision of the run, for
the same reason it was in attempt 001.

What was missing was any constraint or a named fork. Cheaper alternative:
*"One script `measure.py`, no pip, print each building's area and inside/outside split.
Forks I can see: the legend swatch, the shed, the one that crosses the boundary."*
The workspace `CLAUDE.md` covered no-pip and no-CLI, so nothing went wrong.

## 2. Data literacy — **weak**

> *from my understanding, this task is a detection task, we need to detect each
> building then calculate its footprint area*

> *there are two methods that i could think of... 1. contours/template matching 2.
> YOLO/DETR*

Nothing in the transcript shows the PDF was opened before this was written, and both
methods are pixel methods for an input that is vector (14 paths, no raster, a 3 KB
file). The agent found that in one call and changed the method; the candidate
invited that ("you can propose other methods if it is more accurate"), which saved the
run but should not be the plan. Cheaper alternative, 30 seconds before typing:
*"I opened it: A3 vector sheet, six grey shapes, a dashed parcel, a 20 m scale bar, a
legend. Shapes are exact, so read the paths rather than detect."*
`reference/pdf-plan-sets.md` §"Vector geometry, not pixels" and `problem-ladder.md`
#12 ("Before any CV, is this vector or raster?").

## 3. Decomposition — **adequate**

Three instructions: task and questions, answers and go, accept. Right size for the
problem. Instruction 1 handed the method decision to the agent rather than making it.

## 4. Verification — **weak** (cold read agrees)

> *i checked your overlay.png . all good from me.*

The first instruction set this up well: *"at the end of this session, you must present
the overlay.png so i can check it manually and see if the detection result is 100%
correct."* Asking to see the artifact is exactly right. The follow-through stopped one
clause short. Cheaper alternative, ten extra words:
*"I count six outlines: A, B, C, D, E and the shed, legend excluded. D crosses the
east line, C has a hole, your areas match."* The check was already done; this just
makes it legible. (Playbook: "Verifying without stating the number".)

**Where I differ slightly from the cold read:** it scores this purely from the
transcript, which is the right standard here. I note only that the intent was good and
the artifact was opened, so the gap is reporting, not effort.

## 5. Correction quality — **not exercised**

Nothing was wrong. The courtyard remark was a spec confirmation, not a correction.

## 6. Domain vocabulary — **adequate**

"footprint", "within_parcel", "shoelace" (picked up and then asked about:
*"please explain the gist of it to me as well so i can understand the final script
better"*). Asking for the explanation is the right habit, since it is exactly what the
last five minutes of the real session are for. The weak spot is YOLO/DETR next to
"contours" for a vector sheet, which is a data-literacy slip more than a vocabulary
one. Words that would have shortened the loop: "vector paths", "polygon area",
"hole / courtyard", "clip to the parcel".

## 7. Scope control — **adequate** (cold read: adequate)

One script, no CLI, no tests, 16 tool calls. The agent added a raster cross-check the
candidate did not ask for; it was cheap and useful, but it was the agent's call, and
the candidate never said what they wanted held back.

---

## Requirement drift

None. Both answers narrowed or kept the spec and match the ground truth. Worth naming
the one place it came close: the candidate answered both clarifying questions with
agreement ("i agree", "yes... let's do it as you say") on the agent's stated defaults,
but each answer carried the candidate's own reason, and neither changed what gets
measured. On the courtyard, the candidate asserted a rule the brief never states
("we shouldn't include the inside square courtyard into the footprint area"). It is
the right rule, and it came from the candidate rather than from a "(Recommended)"
label, but it arrived *after* the agent had already decided. Saying it first would
have been the stronger version.

---

## Carry into the next attempt

1. **Open the input yourself and say what it is before instruction 1.** Vector or
   raster, how many objects, what the legend and scale look like. One sentence. Drop
   any method you cannot defend for that input (here, YOLO/DETR).
2. **Approve with your own numbers.** *"I count N: X, Y, Z. Your table matches."*
   Never just "all good".
3. **Name the forks you can see in instruction 1, with the branch you want.** Here:
   legend swatch out, shed in, boundary straddler flagged with a split, courtyard not
   counted. You got all four right, but the agent found two of them for you.
4. **Add one constraint line:** *"One script, no pip, print the table."* Do not rely on
   the workspace `CLAUDE.md` to carry it.

## Next archetype

**#6 Deskew / flatten a photographed document** (Tier 2). Every recent run has had a
vector or model shortcut around raster CV (#10, #11, #12 and this one), and
Tier 2 has not been practised since attempt 001. A photo has no `get_drawings()` to
fall back on, which forces point 1 above: you have to look at the image and say what
you see, and then say the number you verified.
