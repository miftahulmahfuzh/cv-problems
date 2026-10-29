**Scores**

1. **Requirement capture: strong.** The first message contained the task, the output files, the units and the footprint rules. Examples: "work in metres. use the 20 m scale bar… and 1:500 scale as the main anchor", "SHED F… should still be included as a building", and "at the end of session, you must print the details". The one gap is the legend swatch fork, which they never raised. Cheaper alternative: add "ignore the legend swatch; it is not a building."

2. **Data literacy: strong.** They counted the buildings ("6 buildings… BLDG A,B,C,D,E, and SHED F") and named the courtyard in C, the L-shape of B and the skew of E. They did not mention the dashed boundary. That only surfaced in message 2 ("parcel is dashed line"), after the agent found it. Cheaper alternative: "the boundary is dashed, so it's many short segments."

3. **Decomposition: adequate.** The whole spec went in one block, then a sign-off. That suits a 9-minute run, but there was no checkpoint. A better split would be "extract the geometry and print it, then compute distances." Cheaper alternative: "first print the parsed building polygons and boundary segments; stop there."

4. **Verification: adequate, leaning weak.** They checked the artifacts ("i checked the output table AND overlay.png"). The only independent numbers were 1.39 m and 16 m, and both were read off the agent's output. "all detections and distances matched my expectations" is unfalsifiable. The playbook asks for the number and the breakdown. Cheaper alternative: "I eyeballed A/B/C/F at about 10 m, E at about 4.6 m, D crossing; your table matches."

5. **Correction quality: not exercised.** There was no wrong output and no correction turn.

6. **Domain vocabulary: strong.** They used "vector layer", "external contour", "parcel boundary", "scale bar" and "outer contours". These shorten the loop. "contour" is raster vocabulary applied to a vector PDF, but it was harmless.

7. **Scope control: adequate.** "write a script that outputs…" did not ask for one short script with no CLI. The workspace `CLAUDE.md` probably covered that. "we can discuss it further" and "ask any confusing things you find" invite round-trips, and the agent produced extras (the setback-limit square). Cheaper alternative: "one script, no CLI; decide forks yourself and list them at the end."

**Weakest instruction (verbatim):**
> "there is a skewed, diagonal BLDG E, use the top , furthermost point of it to calculate the building distance to the parcel boundary"

This prescribes a guess about geometry the candidate had not measured. Their own later words ("BLDG E exceed the bottomline by 1.39m") show the binding edge was the bottom. The agent silently replaced it with "minimum over all outline vertices", and the candidate accepted that.

**Highest-leverage change:** state the rule as a goal and leave the geometry to the script. For example: "distance = minimum over all footprint vertices and all boundary segments, for every building." Then close the loop with independent numbers: "my eyeball estimates are A/B/C ≈10, E ≈4.6, D crossing. Flag any disagreement over 0.3 m."

**Requirement drift:**
- Message 1 fixed the method: "top, furthermost point" for E, "bottom-most wall" for B, and "closest wall". Message 2 accepts "minimum over all outline vertices and all four parcel sides", and the candidate calls E and B "matched my expectations". The spec changed and was ratified after the fact rather than stated up front.
- The sign convention was introduced by the agent ("negative distance means breaking the rule. confirmed"). The brief asked "by how much", and the reporting format for D, a real fork, was chosen by the agent. The candidate confirmed it without asking about the tradeoff. This is acceptable under the examiner notes, but it was the agent's decision.
- The legend swatch fork was ceded: "thank you for deciding it for me." The result is correct, but the candidate never decided it.
- The setback-limit dashed square was added by the agent and welcomed: "i forgot to instruct you…". This is a small scope addition, accepted as an improvement.

**Examiner-note cross-check:** the 4.61 m result for E is consistent with the 1.39 m excess. D crossing the boundary and the exclusion of the legend swatch also match. The candidate's reported "16m" for D is a different reporting convention from the ground truth's 0, but the notes allow that.
