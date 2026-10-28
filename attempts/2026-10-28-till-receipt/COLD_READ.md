# Scoring: till-receipt (7.3 of 25 min)

| # | Dimension | Score |
|---|---|---|
| 1 | Requirement capture | adequate |
| 2 | Data literacy | adequate |
| 3 | Decomposition | adequate |
| 4 | Verification | weak |
| 5 | Correction quality | strong |
| 6 | Domain vocabulary | adequate |
| 7 | Scope control | adequate |

**1. Requirement capture: adequate.**
- Instruction 1 resolved the totals fork: "i am assuming that we need to extract every single details in the total calculation, like: Subtotal, Diskon member, TOTAL, PPN, Tunai, Kembali". It also set a boundary: "the bottom text 'Terima kasih' shouldn't be included".
- Missing: the box fork. "shows the detection box for each line item" never says one box per item or per printed line. The output format is also unstated: parsed integers or strings, and where the discount goes.
- Cheaper alternative: "One box per item spanning its name and qty/price lines. Numbers as integers. Discount as its own field, not an item."

**2. Data literacy: adequate.**
- "there are five items in the receipt: INDOMIE GORENG, AQUA 600ML…" shows they looked at the image and counted.
- They did not pass on what an agent needs: the two-line item layout, the negative discount, or the resolution and font.
- Cheaper alternative: "Each item prints as a name line, then a `qty x unit  total` line. The discount is negative."

**3. Decomposition: adequate.** Three instructions: build, show the output, accept with one fix. That fits the 3–5 target. The first message did carry context, goal and output, but it had no VERIFY clause, which forced instruction 2.
- Cheaper alternative: add "then run it and print the JSON" to instruction 1. That saves about 2.4 minutes.

**4. Verification: weak.**
- "please print the structured json here, so i can validate the script output against the png myself" was a good move.
- The candidate never opened `overlay.png`. Only the agent `Read` it. Boxes were a graded deliverable (within ~8 px).
- Their reported checks are unfalsifiable: "each items row is correct with the png values" and "i also check every checklist item in checks myself, and everything is as you said." No number appears anywhere.
- Cheaper alternative: "Items sum to 193,500, minus 5,000 gives 188,500, and cash 200,000 minus total gives change 11,500. All match the PNG. Show me the overlay."

**5. Correction quality: strong.** "remove "currency": "IDR", from json because that is just your assumption, this script only extracts data, not inferring anything from the data." It names the exact field, gives the reason and states a rule that applies to the rest of the output. There was only one correction, so the sample is thin.

**6. Domain vocabulary: adequate.** "OCR approach", "detection box" and "structured data" are fine. "using gylph matcher is not 'generic' enough" is a loose term for template or glyph matching. Terms like bounding box, tokens and fragments would let them direct the box fork and the OCR traps the agent hit.

**7. Scope control: adequate.** "please write a script" implies one file. The candidate never said "no CLI", but the agent stayed small, so this was lightly tested. The ban on "Terima kasih" and the removal of `currency` do count as keeping the data in scope.

## Weakest instruction (verbatim)
> "i also check every checklist item in checks myself, and everything is as you said."

It gives no numbers, so an interviewer cannot tell a real check from a nod. It also accepts the agent's self-written `checks` block as verification, and says nothing about the overlay.

## Highest-leverage change
Look at `overlay.png` yourself, and say the numbers out loud. The overlay is where the unresolved box fork would show up. Stating "193,500 − 5,000 = 188,500" costs one sentence and makes the check visible.

## Requirement drift
- **Instruction 1:** "the totals" was expanded to six fields (Subtotal, Diskon member, TOTAL, PPN, Tunai, Kembali). This was a deliberate interpretation made at the start. It matches `GROUND_TRUTH` and is not drift.
- **Instruction 3:**
  - The candidate removed `currency` and approved the agent-added `receipt_no` and `cashier`. This narrows or extends the spec, but it is small and explained.
  - The box fork was never raised, so the agent's choice went through unreviewed.
- **OCR discovery:** the candidate proposed OCR in instruction 1 without mentioning the bridge. The agent found `ocr_bridge` itself, so the candidate's instructions give no credit on that examiner check.
