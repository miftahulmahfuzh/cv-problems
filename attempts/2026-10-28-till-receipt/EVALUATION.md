# Evaluation — till-receipt

**Result: passed in 7.3 min of 25. Every value matches `GROUND_TRUTH.json`. The JSON was read against the PNG by the candidate; the overlay was not, and no number was stated aloud.**

Cold read: `COLD_READ.md` (headless `claude -p`, no account of the run supplied).

## Correctness

| Check | Ground truth | Produced | Verdict |
|---|---|---|---|
| store / date / time | TOKO SINAR JAYA, 2026-10-21, 14:32 | identical (plus address, cashier DEWI, receipt_no 004517) | right |
| 5 items (name, qty, unit, line total) | as listed | identical, integers | right |
| subtotal / discount / total | 193500 / 5000 / 188500 | 193500 / **-5000** / 188500 | right (negative kept as printed; discount is not a 6th item) |
| PPN | 18680, included | 18680, rate 11, `included_in_total: true` | right |
| cash / change | 200000 / 11500 | identical | right |
| "Terima kasih" | excluded | excluded | right |
| boxes | one per item spanning both lines, within ~8 px | one per item spanning both lines; edges about 5–8 px outside the GT box | right, borderline; neighbouring boxes touch (about 2 px overlap) |

Verification level: **right, candidate-checked by eye, not stated numerically.** The candidate asked for the JSON to be printed and compared it to the PNG ("so i can validate the script output against the png myself"). That is a real check. But the transcript shows no number from it, and nothing shows the overlay was opened by the candidate (only the agent `Read` it; it was on the worklog page).

Traps:
- Two-line items: **hit and handled** (agent paired a name row with the next `N x unit total` row).
- Dropped spaces, fullwidth comma, `BERAS 5KG` / `1x 68,500` fragments: **hit and handled by the agent** (row clustering by y, normalising `，`, rebuilding spaces from blank character cells). Candidate was not involved.
- Negative discount: **avoided** (field, not item).
- PPN already included: **avoided** (`included_in_total`, check `total × 11/111`).
- Self-check arithmetic: **agent wrote it; candidate said they re-did every check** but gave no figures.
- Bridge discovery: **found by the agent** from the workspace `CLAUDE.md`. The candidate's own "i am proposing a OCR approach" did not name it, so no credit on that examiner check.

## The seven dimensions

**1. Requirement capture — adequate.** The first instruction pinned the totals fork:
> "i am assuming that we need to extract every single details in the total calculation, like: Subtotal, Diskon member, TOTAL, PPN ,Tunai, Kembali"

and the exclusion "the bottom text 'Terima kasih' shouldn't be included". It never settled the box fork or the number format, and ended with "ask me any confusing things you find". Cheaper: *"One box per item covering its name line and its qty/price line. Numbers as integers, discount as its own field."* Both would have been outputs the agent had to guess.

**2. Data literacy — adequate.** "there are five items in the receipt: INDOMIE GORENG, AQUA 600ML, BERAS 5KG, TELUR AYAM 1KG, SUSU UHT 1L" shows a real look at the image. Missing: each item prints on two lines, the discount is negative, it is a monospace scan. Cheaper: *"Each item is a name line then a `qty x unit   total` line; the discount is negative."*

**3. Decomposition — adequate.** Three instructions, in the 3–5 band. The first had no run-and-show clause, so the second ("please print the structured json here") was a round trip that a trailing "then run it and print the JSON" would have saved (about 2.4 min).

**4. Verification — weak.**
> "each items row is correct with the png values … i also check every checklist item in checks myself, and everything is as you said."

Cannot be told from a nod. It also treats the agent's own `checks` block as an independent check. The overlay, which carries the box deliverable, was not mentioned. Cheaper: *"Items sum to 193,500; minus 5,000 is 188,500; 200,000 minus 188,500 is 11,500. That matches the PNG. Show me the overlay."* Credit where due: asking for the JSON to be printed so they could compare it themselves is the right instinct.

**5. Correction quality — strong (thin sample).**
> "remove "currency": "IDR", from json because that is just your assumption, this script only extracts data, not inferring anything from the data."

It names the field, gives the reason, and states a rule for the whole output. One correction only.

**6. Domain vocabulary — adequate.** "OCR approach", "detection box", "structured data" are fine. "gylph matcher" is loose for template or glyph matching; "bounding box", "tokens" and "fragments" would have let them direct the box fork and the OCR splitting.

**7. Scope control — adequate.** "please write a script" and the exclusion of "Terima kasih" kept it small, and the `currency` removal was scope control on the data. No "no CLI" was needed; the agent stayed to one file.

## Requirement drift

- Instruction 1 widened "the totals" to six named fields. Deliberate, stated, and matches ground truth: not drift.
- Instruction 3 accepted the agent-added `cashier`, `receipt_no` and `checks`, and removed `currency`. A small extension and a small cut, both explicit.
- The box fork was never raised, so the agent's choice (one box per item, padded 5–6 px) went through unreviewed. It happened to match the preferred branch.

## Disagreements with the cold read

The cold read scores Requirement capture, Data literacy, Decomposition, Domain vocabulary and Scope control adequate and Verification weak, and Correction quality strong. I agree on every score. Where we differ in tone: it says the candidate "never opened `overlay.png`"; the transcript only shows no mention of it, the page was available to them. I report that as not evidenced, not as not done.

## Carry into the next attempt

1. **Say the numbers you checked.** After comparing, write them: "5 items, they sum to 193,500, minus 5,000 gives 188,500; the PNG shows the same." One sentence turns a nod into evidence.
2. **Ask for, and look at, the overlay in the same turn as the script.** End the first instruction with "run it, print the JSON, show me overlay.png". Then say what you see: "five boxes, each covers a name and its price line."
3. **Name both forks in the first instruction.** For anything drawn per record: "one box per item spanning both printed lines." For numbers: "integers, not strings."
4. **Describe the layout you saw.** "Items print as a name line then `qty x unit   total`; discount is negative." It is free and removes the agent's guesswork.

## Next

Run a model-tier problem next (perception by CLIP/BLIP or resnet, with a deterministic number beside it). The last two OCR runs plus the table run were all deterministic extraction on clean scans; nothing has yet rehearsed the perception-versus-facts split from the playbook, and the caption run forfeited its model call.
