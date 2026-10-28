# Evaluation — skewed-statement (run 2026-10-28-4)

**Result: failed on output geometry, in 4.1 of 20 minutes.** The four corners were
found to within 2 px of ground truth and the content survived intact, but
`flat.png` is 935x1046 (w/h 0.894) against a page of 900x1150 (0.783, tolerance
3%). The page is stretched about 14% horizontally. The candidate saw the number
and signed off anyway.

Scored against the seven dimensions in `reference/prompting-playbook.md`. A cold
read (`COLD_READ.md`) was taken and agrees with this scoring on every dimension.

---

## Correctness

- **Corners:** exact. Detected TL(310,141) TR(1179,96) BR(1247,1119) BL(251,1207)
  vs truth (310,140) (1180,95) (1250,1120) (250,1210). Ordering TL,TR,BR,BL right.
- **Aspect (fork 1): out of tolerance.** 0.894 vs 0.783. Cause: the agent sized the
  output from the mean of opposite edge lengths of the photographed quadrilateral.
  Under perspective that does not recover the page's true aspect. The agent also
  wrote "text proportions look right", which was wrong; the stretch is there.
  Fixing it needs either a stated size (900x1150) or a homography-based aspect
  estimate.
- **Margin (fork 2):** none, unstated.
- **Content:** verified by the candidate. 1 header + 5 rows, five tickers, values
  unchanged. Verified during the run, and by the candidate, not the agent.
- **Traps:** dark desk, hit and handled (HSV mask). Perspective not affine,
  avoided deliberately (`getPerspectiveTransform`). Corner ordering, avoided
  (sum/diff ordering). **Shadow and lighting gradient: untouched**; the left-to-right
  gradient is still plainly visible in `flat.png`. The brief says "as if it had been
  scanned", so this is a miss against the brief, though the ground-truth check is
  geometry only.

Verdict split: content **right, verified by the candidate**; geometry **wrong**,
with the evidence on screen in `notes.json` and not read.

---

## 1. Requirement capture — **weak**

> "the requirement is for us to straighten it."

That narrows "flat, upright, filling the frame, as if scanned" to a skew fix, and
resolves neither fork (output size, margin).

Cheaper: *"Output 900x1150 portrait, no margin. Print the output size and aspect, then show flat.png."*

## 2. Data literacy — **weak**

> "i see a skewed photograph of a trade confirmation table."

Nothing about the dark desk, the shadow along two edges, or the uneven lighting.

Cheaper: *"White sheet on a dark desk, shot at an angle, shadow on two edges, lighting uneven left to right."*

## 3. Decomposition — **adequate**

> "let's discuss the approaches first." … "you need to write a script"

Two modes in one message; the agent skipped the discussion and the candidate did not
push back. The task itself is one deliverable, correctly one script.

Cheaper: *"Give me two approaches in three lines, then implement the simpler one."*

## 4. Verification — **weak**

> "do not forget to show me the flat.png so i can evaluate the correctness of the script myself"

The right instinct, and the best line of the run. The check was content only: rows
and tickers. The pasted `notes.json` carried `"output_aspect_w_over_h": 0.894` right
beside `"a4_aspect": 0.707`, and neither was mentioned. The agent's own notes were
disagreeing with the A4 reference in the candidate's face.

Cheaper: *"Aspect is 0.894 but A4 is 0.707 and the page looks about 0.78. Why? Resize to 900x1150 and print the angle of the header band."*

## 5. Correction quality — **not exercised**

The one correction that was needed (aspect) never happened.

## 6. Domain vocabulary — **weak**

"skewed", "straighten", "flatten". "Perspective", "homography", "deskew" and
"document rectification" never appear. Message 2: "this is new to me, so i just
learned about 'HSV threshold..->warpPerspective'". Learning it from the agent is
fine; the cost is that the agent's choices went unchallenged.

Cheaper: *"Perspective-correct with a 4-point homography; output at the page's real size."*

## 7. Scope control — **adequate**

One script, two outputs, no CLI. The extra `debug_corners.png` was harmless and
useful for checking.

---

## Requirement drift

Message 2 swapped the acceptance test. The brief's test is "as if it had been
scanned" (geometry and cleanliness). The candidate's test became "no value
changes". That is a lower bar, and geometry was never put through it. Shadow and
gradient dropped out of the spec at the same moment.

## Carry into the next attempt

1. **Fix the output size before the first run.** State the target (A4 portrait, or
   the size you expect) in the first instruction. The size fork is the main trap
   for this archetype.
2. **Read every number in notes.json aloud before accepting.** If two values sit
   next to each other and disagree (0.894 vs 0.707), ask why.
3. **Check geometry, not just content.** Ask for the header band's angle in the
   output, and for the output resized to the expected size.
4. **Name the problem in the right words in the opening line:** perspective, 4-point
   homography, document rectification.

## Next archetype

Another tier 2 image-geometry task with a fork on units or size, such as measuring
from a flattened page, so size choices cannot be skipped: for example, recover a
real-world length from a photo with a known reference object.
