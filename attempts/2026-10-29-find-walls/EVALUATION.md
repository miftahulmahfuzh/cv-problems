# Evaluation — Find the walls in a plan image

**Result: passed under a stated rule, partly candidate-verified. 20.9 min of 25.**
The run reported 11 walls and 91.39 m. That is internally exact (7 logical walls plus
4 door splits, doors out of the length, windows in), but it is neither of the examiner's
two headline answers (7 walls / 95.0 m, or 13 segments / 87.7 m). The candidate checked
one wall of eleven and stated its numbers.

Scored against the seven dimensions in `reference/prompting-playbook.md`. The cold read
is in `COLD_READ.md`; where I disagree with it, the section says so.

Clock: the harness first printed "-15.0 min". Cause: `cmd_finish` ended the clock at the
first slash command in the transcript, which was `/output-style` run before the task.
Fixed in `bin/cvtest.py` (stop at `/finish-cv-test` only). Measured from the first
instruction to `/finish-cv-test`: 20.9 min. The second instruction arrived at T+20.8.
The candidate says a toilet break is inside that window; it cannot be separated from
review time, so no adjustment was made. The break message arrived after
`/finish-cv-test` and is not scored as an instruction.

---

## Correctness

| | Ground truth | Produced | Verdict |
|---|---|---|---|
| Wall count, through openings | 7 | 11 | different rule |
| Wall count, drawn segments | 13 | 11 | different rule |
| Count under the candidate's rule (7 + 4 door splits) | 11 | 11 | exact |
| Total, doors out and windows in | 91.3 m (95.0 - 3.7) | 91.39 m | +0.1% |
| Total vs 95.0 m / vs 87.7 m | | | -3.8% / +4.2%, outside 3% |
| Scale | 78.74 px/m | 79.2 px/m | +0.6% |
| W01 (top wall, windows, both T-junctions) | 20.0 m, 1574.8 px | 19.96 m, 1581 px | +0.4% px, -0.2% m |

Verdict category: **right under the stated rule; verified for one wall; count and total
not verified by the candidate.**

Two defects in my own script, both below the 3% tolerance:

- The centre-line trim never fired. `touches()` looks for the perpendicular wall just
  outside each run end, not inside it. Lengths are therefore bounding extents, about one
  wall thickness too long at each junction end (W01 +6.2 px, W06 and W11 +7.1 px,
  total +0.68%). I told the candidate the lengths were trimmed centre-lines; that
  was wrong.
- The scale bar was measured from the component width, which includes the end ticks.
- The two errors point opposite ways, so W01 showed 19.96 m and looked right. At the true
  scale the same pixels give 20.08 m.

Traps:

| Trap | Outcome |
|---|---|
| Legend frame | avoided deliberately: named in instruction 1 |
| Title block | avoided deliberately: named as "the scaling box", dropped by the thickness filter |
| Scale bar | avoided deliberately: named as "the line scale" |
| Door leaves | avoided deliberately: "each door gap must not be counted" |
| Window double lines | handled by a candidate decision in instruction 2, after the agent surfaced it |
| Thick walls, two Canny edges | avoided deliberately: "external contours only" |

---

## 1. Requirement capture: **strong** (cold read: adequate)

Instruction 1 named every planted trap, plus the doors fork and the thick-stroke fork,
before any code:

> *"we need to be strict, i mean that each door gap must not be counted into the wall length."*
> *"the line scale at the bottom left is not a wall … the legend box at the top right is not a wall"*

The deliverable files were stated, and the ask for details to validate against
`plan.png` is a verify clause. It needed no correction round.

Gaps: units were never stated (metres appeared because the agent chose them), the
`walls.json` fields were not specified, and the count rule for a wall broken by a door
was left open. Cheaper: *"walls.json: `{count, total_length_m, walls:[{id, p1, p2,
length_px, length_m}]}`. Metres via the 5 m bar."* I score strong because the traps and
the deliverable were complete. The cold read's adequate is fair on units.

## 2. Data literacy: **strong**

> *"some walls has a thicker line in the middle. for example: the corner of Office 101."*

That is a real observation: the thick bar is a window at the top of Office 101, next to
the partition. Both cold read and I agree. What was not done: connecting it to the
WINDOW symbol in the sheet's own legend, giving the resolution or stroke width, and
naming Store 103 correctly ("office 101 , 102, 103"). Cheaper: *"2339x1653, walls about
6 px, black on white; the two thick bars on the top wall are windows per the legend."*

## 3. Decomposition: **strong** (cold read: adequate)

One instruction for one deliverable, then acceptance. Right for a 25-minute task. The
cold read asks for a "run it and show me" step; the candidate did ask for the details
"at the end of this session … so i can validate it manually", which is the same
request. I do not follow the cold read here.

## 4. Verification: **adequate** (agrees with cold read)

> *"W01 that crosses over T-junction, the pixel length and the meters length matched what the plan.png shows. it has 1581 px length and 19.96 m length."*

Good: the numbers are stated, the check was independent of the agent's narration, and
W01 is the hardest wall (windows, two T-junctions). Not good:

- One wall of eleven. The count (11), the total (91.39 m) and the four door gaps were
  never stated back.
- "Matched what plan.png shows" cannot resolve 1581 px from 1575 px by eye. The check
  that can is arithmetic from the sheet: 84 m2 / 12 m = 7 m, so 7 + 6 + 7 = 20 m.
  Against that, 19.96 m is 0.2% under, and 1581 px at 78.74 px/m is 20.08 m. The
  difference was invisible because the scale was wrong in the opposite direction.
- The cold read says "1 of 7 walls"; the table had 11, so it was 1 of 11.

Cheaper: *"I count 7 logical walls by eye, plus 4 doors splitting walls = 11. Exterior should be
20/20/12/12 m from the room areas; yours: 19.96/12.02/12.02. Total 91.39."*

## 5. Correction quality: **not exercised**

Instruction 2 accepted the agent's choices. Nothing needed correcting.

## 6. Domain vocabulary: **adequate** (agrees with cold read)

Good: "external contours", "outer and an inner contour", "T-junction", "normalize".
Weak: *"i propose us to use instance segmentation to detect these walls."* Instance
segmentation is a learned-model task; this is a binary line drawing and the sealed
environment has no segmentation weights. The right words are *threshold, morphological
opening, connected components* (`reference/cv-crash-course.md` §2). The agent replaced
the method and said so; the candidate never acknowledged it. "line scale" and "scaling
box" are longhand for "scale bar" and "title block".

## 7. Scope control: **strong** (cold read: weak)

One script, no CLI, no tests, two output files. The workspace `CLAUDE.md` carries the
"no CLI" rule, as it did in the rect-center attempt scored strong. The cold read marks
`"(we can discuss it further)"` and `"the more detailed, the better"` as invitations to
expand. They are mild, and nothing expanded. I score on what happened. If you want the
cold read's version of this lens: end with *"one script, print results, nothing else."*

---

## Requirement drift

1. **Door rule widened from length to count.** The opener said door gaps are not counted
   *into the wall length*. The script also split every door-interrupted wall in two,
   taking the count from 7 logical walls to 11. Instruction 2 said *"i agree, we should
   consider T-junction wall as one"*, answering a question about T-junctions. The
   alternative "7 walls, gaps excluded from length only" was never offered. This is
   the examiner's preferred reading, and it satisfies the opener exactly. It was
   closed off by how the options were framed.
2. **Windows in, doors out, for the wrong reason.** *"windows are normally small enough
   and can be considered within a wall."* On this sheet the windows are 1.8 m and the
   doors 0.9 to 1.0 m. The rule is defensible (a window is in the wall plane, a door is
   a void), but the stated reason is the opposite of the geometry. The rule changed the
   answer: counting windows as gaps gives 87.7 m, not 91.4 m.
3. **Method dropped.** "instance segmentation" was the candidate's stated method. The
   run used classical CV and the candidate's reply did not mention it.
4. **Units never specified at any point.**

---

## Carry into the next attempt

1. **State the count and the length rule separately.** *"Report logical walls (a wall
   through a door or window is one wall) and a length with openings removed. Show both
   numbers."* Prevents drift 1; the count would have been 7.
2. **Name the units and the schema in the opener.** *"Metres via the 5 m scale bar
   (200 dpi, 1:100 so about 78.7 px/m). `walls.json`: `{count, total_length_m, walls:[…]}`."*
3. **Verify with arithmetic from the sheet, and say the total.** *"Room areas 84, 72,
   42 m2 give 7, 6, 7 by 12 m, so the top wall is 20 m. Yours is 19.96. Total 91.39."*
   One wall plus the total beats one wall.
4. **Say the technique in words that exist in the environment.** *"Threshold, open to
   keep 6 px strokes, connected components, external contours."* Drops "instance
   segmentation", which has no weights here.

## Next archetype

Rung 10 (scale: pixels to real units) on a sheet with no scale bar, so the scale has to
come from a labelled dimension or a room area. This sheet gave a clean bar and a 1:100
note, and the 0.6% scale error went unnoticed because of that. Pair it with rung 11
(count repeated symbols) to drill carry-forward 3: the candidate writes down the
expected count and total before the agent prints them.
