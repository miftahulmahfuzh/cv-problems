# Scoring: trade-table (11.0 min of 20, passed)

**1. Requirement capture: weak.**
- Instruction 1 pasted the brief and added: "write a script that extract the trades , outputs output/trades.json , each entry's metadata contains every column value".
- It dropped the brief's per-cell pixel boxes. It also gave no constraints and named neither fork (totals block, numbers as strings or numbers).
- The real requirement, "what happens if this script receive another raster image?", only appeared in instruction 2.
- Cheaper: "One record per trade; each cell = {text, bbox[x0,y0,x1,y1]}. Exclude the totals block. Numbers parsed to int. One script, no CLI."

**2. Data literacy: weak.**
- The candidate described the content correctly: "5 rows… BBCA, BBRI, TLKM, ASII, GOTO", plus the six columns.
- They called the input a PDF twice ("detect the PDF vector, it is a vector sheet with exact shapes"), but `statement.png` is a raster. That wrong premise cost instructions 2–4.
- They also said "i don't see any edge cases". The brief has no vertical rules, a shaded header and a totals block aligned with the PRICE and VALUE columns.
- Cheaper: "It's a 900×1165 PNG. There are no vertical rules, only faint row rules and a shaded header. A totals block sits under the table."

**3. Decomposition: adequate.**
- There were five messages, but three (2–4) were a detour caused by the wrong data assumption.
- The build, run and check happened in one pass, which is good.

**4. Verification: adequate.**
- Instruction 5 is falsifiable: "5 content rows plus a header row… side values… B,B,S,B,S", then "the qty_lot matches, the price matches… the fee values matches". That is a stated per-column check.
- It checked only the text. It never mentioned the overlay boxes, the 6 px tolerance, the totals block, or the self-check sums (VALUE 60,952,500 and FEE 104,193).
- It also compared against "the original pdf input", which does not exist.
- Cheaper: "Sum VALUE and FEE and print them against the statement's totals. Open overlay.png and confirm each box hugs its text."

**5. Correction quality: adequate.**
- Instruction 2 names the observation: "reading it yourself manually is not acceptable… you can't keep injecting the text manually into the script."
- It states the expected behaviour (generalise to another raster) and then asks a question ("should we set up an OCR engine…?") instead of specifying.
- Cheaper: "Don't hardcode text. Read cells from pixels, with no new installs. Propose the approach in two lines, then build it."

**6. Domain vocabulary: adequate.**
- Good terms: "OCR engine", "raster image", "detect table cells", "abstraction layer".
- "PDF vector" was misapplied to a PNG.
- Missing terms: "bounding box", "row rules", "header shading", "template matching".

**7. Scope control: adequate.**
- Nothing in the transcript shows infrastructure creep, and the candidate asked for "a script". But no constraint was ever stated; it just wasn't needed.
- "installing a new OCR dependency wouldn't be enough" in instruction 4 is good time-budget reasoning.

## Weakest instruction (verbatim)
> "from my perspective, the method we can use here is to detect the PDF vector , it is a vector sheet with exact shapes, i don't think we will have any problem extracting the data because i don't see any edge cases"

It asserts the wrong file type, dismisses the traps, and picks a method before the data was checked.

## Highest-leverage change
Spend the first minute confirming the file type and the actual pixels, for example `file input/statement.png`. Then open with the five-part instruction: data (PNG, no vertical rules, totals block), per-cell bbox contract, both forks decided, constraints, and a verify step that prints the sums. That would have removed instructions 2–4 and given you a way to check the boxes.

## Requirement drift
- **Instruction 1:** "pixel bounding box" per cell became "metadata contains every column value". Boxes were demoted from the contract.
- **Instruction 2:** a new requirement was added, that the script must generalise to other raster images and must not hand-transcribe. It was discovered only after the agent had apparently injected the text manually.
- **Instructions 3–4:** "opt 1" was chosen without the options visible here. The stated reason (deterministic, no OCR install) is sound, but it is a spec decision made mid-run.
- **Never decided:** the totals block, the header key-values, and string versus numeric values.
