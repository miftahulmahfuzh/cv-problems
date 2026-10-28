# Evaluation — 2026-10-28 trade-table

**Result: passed, in 11.0 of 20 minutes. Text candidate-verified column by column;
boxes were not candidate-verified.** Five instructions, 19 tool calls, no interrupts.

> **Cold read.** The first attempt, a subagent, refused to score because it inherited
> the workspace rules. After that, `bin/cvtest.py coldread` was added (a headless
> `claude -p` started at the repo root) and run on this attempt; its full text is
> `COLD_READ.md`. Where it disagrees with the scores below:
>
> - **Requirement capture:** cold read says *weak*, I said *adequate*. Its point stands
>   in part: the candidate's own restatement ("each entry's metadata contains every
>   column value") leaves out the per-cell boxes the pasted brief asked for. I keep
>   *adequate* because the brief was pasted whole, but the restatement should have
>   kept boxes.
> - **Correction quality:** cold read says *adequate*, I said *strong*. It wants the
>   correction to specify the fix ("no installs, read cells from pixels") instead of
>   asking which OCR to set up. Fair; asking also produced a good option list, so I
>   keep *strong* with that caveat.
> - The other five dimensions agree. The cold read repeated "900x1165" from the ground
>   truth note; the file is 900x1150.

## Correctness

Run against `GROUND_TRUTH.json`: headers `TICKER, SIDE, QTY (lot), PRICE, VALUE, FEE`,
5 rows, **all 30 cell texts exact** (numbers stripped of commas match the expected
integers). Sum of VALUE 60,952,500 and FEE 104,193 reproduce the checks. Boxes are
tight around the ink (e.g. `18,950,000` at `[602, 277, 684, 289]`), inside the 6 px
tolerance; the overlay was read back and shows 6 blue header boxes and 30 red trade
boxes with nothing around the totals block.

Verification: **right, and verified by the candidate for the text.** Instruction 5
checks ticker, side, qty, price, value and fee against the source. The boxes were
looked at by the assistant only; the candidate never mentions the overlay.

| Fork / trap | Outcome |
|---|---|
| Totals block and header key-values in or out | Excluded, by the assistant's default. It said so once ("left out because they aren't trades"), the candidate never decided it. Avoided by accident. |
| Numbers as strings or parsed | Strings with commas, **never stated** to the candidate. GT accepts strings "if stated". Minor miss. |
| No vertical rules | Avoided: cells come from blank-column gaps, not lines. By the assistant. |
| Totals aligned with PRICE/VALUE | Avoided: table bottom is the last row rule. By the assistant. |
| Faint row rules, shaded header | Avoided: ink threshold 160 ignores both fills. |
| `QTY (lot)` space and paren | Hit and handled: space gap rule plus `(` `)` in the atlas. |
| Self-check on sums | Assistant ran it unprompted. Candidate never asked. |

Note: GT says the image is 900x1165, the file is 900x1150. Boxes were checked on the
actual file; the note in `GROUND_TRUTH.json` is wrong.

## The seven dimensions

**1. Requirement capture: adequate.** The opening restates the brief faithfully and
adds a useful detail: *"each entry's metadata contains every column value"*. It names
the outputs and paths. It never says whether totals are in, or whether numbers are
strings. Cheaper: *"Totals block and the Account lines are not trades, leave them
out. Keep numbers as strings with commas, say so in the JSON."*

**2. Data literacy: weak.** *"it is a vector sheet with exact shapes ... i don't see
any edge cases"*. The file was `statement.png`. One `ls input/` would have shown it.
The no-edge-cases claim was also wrong: the table has no vertical rules and a totals
block sitting under the columns. The wrong premise cost about 4 minutes (the first
script, the manual transcription, instruction 2). Cheaper: *"Check the file type in
input/ and tell me what it is before you pick a method."* Reference: `README.md`
line 81 and `reference/pdf-plan-sets.md` §1 (text layer vs raster).

**3. Decomposition: adequate.** One instruction for one deliverable, then three small
corrections. Fine at this size. Nothing to split.

**4. Verification: adequate.** Strong where it happened: *"at the end of the session,
print the extracted trades and the overlay.png, i will validate the final script
accuracy by comparing its result"* and then instruction 5 actually did the
comparison cell by cell. Weak on two points: no numeric self-check was requested
(`sum(VALUE) == Gross value`), and the boxes were never checked by the candidate.
Cheaper: *"Print sum of VALUE and FEE and compare with the Gross value and Total fees
lines. Show me a crop of one row with its boxes."*

**5. Correction quality: strong.** *"reading it yourself manually is not acceptable
... what happens if this script receive another raster image? you can't keep
injecting the text manually into the script."* This names the failure, states the
requirement it broke (generalise to another raster) and asks for options instead of
dictating one. It took the candidate from a hard-coded script to a working one in 2
messages. Only trim: the apology adds nothing.

**6. Domain vocabulary: adequate.** *"PDF vector"* is real vocabulary used on the
wrong file. *"abstraction layer"* was a good way to ask for a seam; it produced the
`read_cell` function. The reasoning in instruction 4, *"more deterministic ... doesn't
use OCR model"*, is sound. Missing: the names for the two stages, cell detection
(projection profiles, connected components) and glyph reading (template matching,
`cv2.matchTemplate`), which would have let the candidate point at either directly.
Reference: `reference/problem-ladder.md` #4.

**7. Scope control: adequate.** Instruction 2 widened scope from "this image" to "any
raster table". That was the right call for a script, and it was said out loud. The
closing line *"it should be able to extract other pdf tables"* is wrong: the script
takes rasters only. Only the assistant's reply caught it.

## Requirement drift

1. **Instruction 2 changed the deliverable** from "get the trades out of this image"
   to "a script that generalises to other raster table images". Deliberate and
   stated, so legitimate, but it changed what "passed" means: a typed-in answer would
   have scored on the GT and still been rejected.
2. **Instruction 5 claims PDF support** the script does not have. Not a drift in the
   spec; a drift in the candidate's picture of what was built.
3. The totals-block and number-format forks were closed by the assistant's defaults,
   with no candidate input.

## Carry into the next attempt

1. **Name the input type before the method.** Start with: *"First run `ls -la input/`
   and `file input/*`, tell me what each file is, then propose the method."*
2. **Close the forks out loud.** *"Anything that is not a trade row (totals, account
   lines) stays out of the data. Numbers are strings with commas, say that in the
   JSON."*
3. **Ask for a number that can be checked.** *"Print sum(VALUE) and compare it with
   the Gross value line on the page; print both."*
4. **Check the boxes, not only the text.** *"Show me one row cropped with its
   boxes drawn, and print each box as x0,y0,x1,y1."*

## Next archetype

**#6, deskew or flatten a photographed document** (Tier 2, never run). This run's
limits as the candidate named them were noisy scans and anything not DejaVu; #6 is the
step that makes a photographed page usable by the structure stage that worked here,
and it needs `getPerspectiveTransform` and a verification the candidate can see.
