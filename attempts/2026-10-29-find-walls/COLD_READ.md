`★ Insight ─────────────────────────────────────`
- The brief had two forks: openings (7 walls vs 13 segments) and units (px vs m). The candidate named the openings fork but left it half-resolved, and never named the units fork.
- Verification was real but covered one wall out of seven.
`─────────────────────────────────────────────────`

## Scores

**1. Requirement capture: adequate.**
- Quote: "we need to be strict, i mean that each door gap must not be counted into the wall length."
- The first message stated the task, the traps (scale bar, legend) and a fork. It never stated units or the `walls.json` fields.
- "ask me any confusing things you find" handed the rest of the spec to a later round trip.
- Cheaper: "walls.json: `{count, total_length_m, walls:[{id, p1, p2, length_px, length_m}]}`. Metres via the 5 m scale bar."

**2. Data literacy: strong.**
- Quote: "some walls has a thicker line in the middle. for example: the corner of Office 101."
- This is real observation from the image, plus the room list.
- It still omitted the resolution, the wall thickness (about 6 px) and the title-block frame, which it called "the scaling box".
- Cheaper: "2339×1653 scan, walls ~6 px thick, black on white."

**3. Decomposition: adequate.**
- There was one big opening message, then a closing message at T+20.8.
- It had no "run it, show me the counts" step, so the verification step was never asked for.
- Cheaper: end the opener with "run it and print the wall count and total length".

**4. Verification: adequate.**
- Quote: "W01 that crosses over T-junction, the pixel length and the meters length matched… 1581 px length and 19.96 m."
- It states numbers and looked at the overlay, which is good.
- Only 1 of 7 walls was checked, and no total or count was reported.
- 1581 px ÷ 78.74 px/m is 20.08 m, not 19.96 m. The discrepancy went unnoticed, and "matched what plan.png shows" doesn't say how it was measured.
- Cheaper: "I count 7 walls by eye; your table has 7. Exterior should be 20/20/12/12 m. Yours: …"

**5. Correction quality: not exercised.** The candidate gave no corrections. Instruction 2 only accepted the agent's choices.

**6. Domain vocabulary: adequate.**
- Good terms: "external contours", "T-junction", "normalize".
- "instance segmentation" is the wrong term for a binary line drawing.
- "line scale" and "scaling box" are longhand for "scale bar" and "title block".
- Cheaper: "threshold, morphological opening, connected components or probabilistic Hough".

**7. Scope control: weak.**
- Quotes: "(we can discuss it further)" and "the more detailed, the better."
- Both invite expansion, and nothing said "one script, no CLI".
- Cheaper: "one script, ≤80 lines, print results, nothing else."

## Weakest instruction

> "i propose us to use instance segmentation to detect these walls."

It prescribes a learned-model technique for a deterministic raster problem, and no such weights are cached. It also commits to a method before the fork was decided.
- Cheaper: "classical CV only: threshold, open to keep thick strokes, connected components."

## Highest-leverage change

Resolve both forks in the opening message and state the numbers you'll check. For example: "One wall through doors and windows, bridging gaps ≤2 m (state the rule). Metres via the 5 m bar. Print the count and total; I expect about 7 walls and about 95 m."

## Requirement drift

- **Doors vs windows:** the opener says "each door gap must not be counted into the wall length". Instruction 2 then says "windows as part of the wall" and "T-junction wall as one".
- This hybrid matches neither examiner rule: 7 logical walls (95 m) or 13 drawn segments (87.7 m).
- The drift happened in the reply to the agent's options, not in a spec update. The candidate never said it overrides the opener.
- **Units:** never specified at any point. Metres appeared only because the agent chose them.
