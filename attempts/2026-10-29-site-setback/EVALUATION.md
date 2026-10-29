# Evaluation — site-setback (2026-10-29)

**Result: passed, in 9.1 min of 30. Numbers right, verification candidate-asserted.**
All six distances are within the 0.3 m tolerance, the violator set is exact
(BLDG D, BLDG E), the legend swatch is excluded, and BLDG D is flagged. The candidate
opened the table and the overlay but never wrote down a number of their own, so
"right" here means right by the agent's defaults plus a sound opening spec, not right
because it was independently established.

Scored against the seven dimensions in `reference/prompting-playbook.md`. A fresh
headless read is in `COLD_READ.md`; where I disagree with it I say so.

## Ground truth vs produced

| Building | Expected | Produced | |
|---|---|---|---|
| BLDG A | 10.0 m, ok | 10.00 m, ok | match |
| BLDG B | 10.0 m, ok | 10.00 m, ok | match |
| BLDG C | 10.0 m, ok | 10.00 m, ok | match |
| BLDG D | 0 (or negative / "crosses"), violates | −10.00 m, violates, short 16.00 m | match (negative is allowed) |
| BLDG E | 4.61 m, violates | 4.61 m, violates, short 1.39 m | match |
| SHED F | 8.0 m, ok | 8.00 m, ok | match |

Reporting note: BLDG D's "16 m" is shortfall against the 6 m rule (6 − (−10)). The
ground truth's 0 would give 6 m. Both are defensible; the sign convention was chosen
by the agent, not the candidate (see drift).

## Traps

- **Rotated BLDG E:** hit deliberately. The candidate wrote "use the top , furthermost
  point of it", so the corner rather than the bbox set the distance. 4.61 m.
- **Dashed boundary:** avoided by accident. The examiner note says many short segments;
  in this file it is one dashed quad. Nothing in the run tested the case where it is
  many segments, and the candidate did not mention dashes until after the agent had
  found them.
- **Legend swatch:** avoided by the agent's default. The candidate never raised it and
  said "thank you for deciding it for me".
- **Units:** avoided deliberately. "use the 20 m scale bar … and 1:500 scale as the
  main anchor". The script cross-checks bar against nominal and asserts they agree.

## 1. Requirement capture: strong

The 351-word opening carried the deliverables, the units, the anchors and the
footprint rules in one message: *"write a script that outputs output/setbacks.json …
and output/overlay.png that visualizes the script decisions"* and *"at the end of
session, you must print the details of the building distance"*. Nothing material
leaked out afterwards.

The gap: two forks that change what is reported were not named, the legend swatch and
how to report a building that is past the boundary. Cheaper: *"ignore the legend
swatch; report a building past the boundary as a negative distance."*

## 2. Data literacy: strong

The candidate looked first and said what they saw: *"there are 6 buildings in there:
BLDG A,B,C,D,E, and SHED F"*, the courtyard in C, the L shape of B, the skew of E, and
proposed the vector layer. That is the best data transfer so far in this series.

Missing: the boundary is dashed, and a legend exists. Both surfaced only in message 2.
Cheaper: *"the boundary is dashed, and the legend holds a sample grey box that is not a
building."*

## 3. Decomposition: adequate

One block, one sign-off. Right for a 9-minute task, but there was no checkpoint between
reading the geometry and computing with it. Cheaper: *"first print the parsed building
polygons and the boundary rectangle, then stop."* That is where a wrong parcel or a
swatch counted as a building would have shown up.

## 4. Verification: adequate, leaning weak

The candidate did open the artifacts: *"i checked the output table AND overlay.png"*.
That is looking at the output, which is the playbook's first requirement. But the only
numbers stated afterwards, *"BLDG E exceed the bottomline by 1.39m and BLDG D by 16m"*,
are read off the agent's table, and *"all detections and distances matched my own
observations"* gives no observation to compare against. One good move: the opening
pre-registered a prediction, *"the obvious building that break the 6m rule is BLDG D"*.

Cheaper, and it fits in the first instruction: *"My eyeball: A, B, C about 10 m, F about
8 m, E about 4.6 m, D crossing. Flag anything that differs by more than 0.3 m."* Then
the check is falsifiable from the transcript. This is the playbook's "verifying
without stating the number" failure, third time in a row.

## 5. Correction quality: not exercised

Nothing was wrong, so nothing was corrected.

## 6. Domain vocabulary: strong

*"vector layer"*, *"external contour"*, *"parcel boundary"*, *"scale bar"* all shorten
the loop. "Contour" is raster vocabulary on a vector PDF, harmless here.

## 7. Scope control: adequate

No ask for one short script and no CLI; the workspace `CLAUDE.md` covered it. *"we can
discuss it further"* and *"ask any confusing things you find"* invite round trips. The
agent asked nothing and added a setback-limit square unprompted, which the candidate
welcomed. Cheaper: *"one script, no CLI. Decide forks yourself and list them at the
end."* That gets the same result with the decisions made visible.

## Requirement drift

1. **Method, E and B.** The brief said "top, furthermost point" for E and "bottom-most
   wall" for B. The agent replaced both with "minimum over all outline vertices and all
   four parcel sides" and the candidate said E and B "matched my expectations". The
   general rule is a superset and gives the same numbers, so nothing was lost, but the
   spec changed and was ratified afterwards.
2. **Disagreement with the cold read.** It calls the E instruction a wrong guess because
   the candidate later said "bottomline". The top vertex is in fact the binding point
   (4.61 m to the top side), so the instruction was right. "Bottomline" was loose wording,
   probably for the setback limit line. I would not score it against them.
3. **Sign convention.** Negative-means-violation was the agent's decision for a real
   fork. The candidate confirmed it without asking about the alternatives.
4. **Legend swatch.** Ceded outright.
5. **The question round was skipped.** The brief said *"ask any confusing things you
   find"*. The agent decided the forks and presented them in its summary instead of
   asking. The candidate accepted all of it in one message.

## Carry into the next attempt

1. **Put your own numbers in the first instruction, then compare.** *"Eyeball: A/B/C
   about 10 m, F about 8 m, E about 4.6 m, D crossing. Flag any difference over 0.3 m."*
2. **Decide the forks yourself.** Name the legend swatch and the reporting of a
   past-the-boundary building in the opening, with your branch for each.
3. **Add a checkpoint before the computation.** *"First print the parsed polygons and
   boundary, then stop."*
4. **State the rule as a goal, and ask for the decisions.** *"Distance is the minimum
   over every footprint vertex and every boundary side. One script, no CLI. List every
   choice I did not specify."*

## Next archetype

A raster version of the same job: a photographed or scanned site plan with no vector
layer, scale recovered from the printed bar, boundary dashed. Every assumption this run
got for free (the vector layer, one dashed path, a clean legend) has to be earned, and
the skewed-statement failure shows aspect and scale need a stated check. It also makes
a correction turn likely, which dimension 5 still has no evidence for.
