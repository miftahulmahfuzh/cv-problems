# cv-problems

Practice harness and prep kit for a computer-vision live-coding interview, run with
Claude Code. Each practice run is an **attempt**: a brief, a sealed workspace, a
clock, and an evaluation of how the session was driven.

Built for the Boon AI/ML Engineer process — see `reference/boon-domain.md` for what
they actually build (construction drawing understanding: takeoff, bid levelling,
spec clash detection).

## Quickstart

```
/spawn-new-cv-test                 # pick the next problem on the ladder
/spawn-new-cv-test tier 4          # or aim at a tier
/spawn-new-cv-test count symbols on a floor plan
```

That scaffolds an attempt, opens it in a new tmux window running a fresh Claude Code
session, and hands you the brief. You solve it by instructing that session. When you
are done, run `/finish-cv-test` **inside that window** — it stops the clock, pulls
your verbatim instructions back out of the session transcript, scores them and
writes `EVALUATION.md`.

## Read in this order

| | |
|---|---|
| `reference/cv-crash-course.md` | CV vocabulary and reflexes, written for someone coming from NLP. The gap-closer — read it first and twice. |
| `reference/problem-ladder.md` | Twelve problem archetypes, easiest to Boon-grade, each with recipe / trap / verification. |
| `reference/prompting-playbook.md` | How to drive an agent under a 30-minute clock. Contains the seven-dimension rubric the evaluations score against. |
| `reference/boon-domain.md` | What Boon builds, the three hard problems they name, where your background is an advantage. |
| `reference/snippets/` | Code verified to run **on this exact environment**. Copy from here rather than recalling an API. |

## Layout

```
bin/cvtest.py          the harness: new / spawn / finish / status
env/                   environment smoke tests (check.py, warm_models.py, demo_vlm.py)
fixtures/mock/         the four fixtures from the original test environment
fixtures/make_floorplan.py   synthetic plan sheet -> vector PDF + raster + ground truth
reference/             the prep kit
attempts/<date>-<slug>/        everything the exam session must NOT see
    PROBLEM.md         the brief
    GROUND_TRUTH.json  the expected answer, the forks, the planted traps
    TRANSCRIPT.md      what you typed, reconstructed at finish
    EVALUATION.md      the scoring
.runs/<date>-<n>/              the exam session's cwd — a NEUTRAL path
    CLAUDE.md          environment + worklog + integrity rules
    input/  output/    the data, and whatever you produce
    worklog.html       the published artifact: input, outputs, verdict
```

Two things keep the drill honest.

**The workspace path names nothing.** Claude Code is told its working directory in
every system prompt, so a run living in `attempts/count-receptacles/` would hand over
the answer before you said a word. Runs live in `.runs/<date>-<n>/`; the readable
slug stays on the attempt directory, which the session never sees.

**The brief is shown in a tmux pane, not written into the workspace.** You can reread
it any time, including after resuming the session days later. The assistant cannot
read it at all — otherwise "read the brief and do it" is a valid move and nothing is
being measured.

The terminal cannot show you images, so each run publishes a **worklog artifact**:
the input images at boot, every output image as it is produced, and after
`/finish-cv-test` the brief, the ground truth and the verdict underneath them.

## Environment

```bash
source /home/miftah/cv-problems/.venv/bin/activate
python env/check.py            # smoke test: imports, fixtures, cv2, torch forward pass
```

Python 3.12 · torch 2.14 CPU · torchvision · transformers 5.20 · opencv 5.0 ·
pymupdf · scikit-learn · pandas · numpy · matplotlib · pillow.
`CLIP ViT-B/32`, `BLIP captioning` and `resnet18` are warm in `~/.cache`.

**No OCR engine is installed** (no tesseract binary, no easyocr) and that is
deliberate — it matches the original test environment, and it forces the better
answer on document tasks: recover structure with geometry, and read text from the
PDF's own text layer via `pymupdf` rather than OCRing a raster.

**OCR is available on the side, in `.venv-ocr/`** (rapidocr-onnxruntime; its wheel
bundles the models, no download at run time). It has its own opencv build, so it never
goes into `.venv`. Call it from a `.venv` script through the bridge:

```python
import sys; sys.path.insert(0, "/home/miftah/cv-problems/reference/snippets")
from ocr_bridge import ocr          # path or ndarray -> [{"text", "bbox": [x0,y0,x1,y1], "score"}]
```

Or from a shell: `python reference/snippets/ocr_bridge.py image.png`. On the
2026-10-28 statement it read all 30 table cells exactly. Known quirk: it drops the
spaces in multi-word lines (`21October2026`). On monospace text, spaces can be rebuilt from blank character cells in the ink
projection (see `.runs/2026-10-28-3/extract.py`, `respace`); also splits one printed row
into fragments, so group tokens by y-centre before parsing. Rebuild with
`uv venv .venv-ocr --python 3.12 && VIRTUAL_ENV=.venv-ocr uv pip install rapidocr-onnxruntime pymupdf`.

## Attempts

| Date | Problem | Tier | Budget | Result |
|---|---|---|---|---|
| 2026-10-22 | Detect rectangles, mark centers | 1 | 15 min | passed — `attempts/2026-10-22-rect-center/` |
| 2026-10-23 | Count duplex receptacles on sheet E-101 | 4 | 30 min | passed in 7.7 min, agent-verified not candidate-verified — `attempts/2026-10-23-count-receptacles/` · [worklog](https://claude.ai/artifact/CbaHefVWbLvUpi8rick9zq) |
| 2026-10-23 | Structure a two-sheet plan set into bid data | 4 | 30 min | passed in 22.2 min, agent-verified not candidate-verified — `attempts/2026-10-23-plan-set-json/` · [worklog](https://claude.ai/artifact/7vkbwV8iMYZNkGiYEqvsgV) |
| 2026-10-26 | Recover scale, measure wall length and room area on sheet E-101 | 4 | 30 min | passed in 14.5 min, agent-verified not candidate-verified — `attempts/2026-10-26-wall-scale/` · [worklog](https://claude.ai/artifact/PpdtYaUaZKVwDCgR5E4Gyn) |
| 2026-10-26 | Classify an intake image by type and pick a handler | 3 | 30 min | passed in 21.4 min, candidate pushed an overfitting check after an assistant-flagged risk — `attempts/2026-10-26-route-intake/` · [worklog](https://claude.ai/artifact/7sbAhNGTzLSDyitN8bCs27) |
| 2026-10-26 | Caption an image and report an exact count | 3 | 25 min | passed in 10.8 min, **count candidate-verified** (first in series); caption built from detections, no model call &mdash; rubric bonus forfeited &mdash; `attempts/2026-10-26-caption-count/` · [worklog](https://claude.ai/artifact/YUH8SNQefJTLG8nGGshLxn) |
| 2026-10-28 | Footprint areas and parcel containment from a site plan PDF | 4 | 30 min | passed in 14.9 min, all six areas exact; verification candidate-asserted, no numbers stated &mdash; `attempts/2026-10-28-site-footprints/` · [worklog](https://claude.ai/artifact/HzYRcZYQHLqk2LYYFVCRiK) |
| 2026-10-28 | Recover a trades table from a statement image (cells, text, boxes) | 2 | 20 min | passed in 11.0 min, text candidate-verified cell by cell, boxes not; candidate assumed a PDF vector layer, input was a PNG; glyphs read by DejaVu template matching, no OCR &mdash; `attempts/2026-10-28-trade-table/` · [worklog](https://claude.ai/artifact/RxVJziX4chq2JRxpJkL6Fx) |
| 2026-10-28 | Extract a scanned till receipt to JSON | 2 | 25 min | passed in 7.3 min, every value matches; JSON candidate-read, overlay not reviewed, no numbers stated &mdash; `attempts/2026-10-28-till-receipt/` · [worklog](https://claude.ai/artifact/6XFis3ec5pR4ZqbaL6fbiV) |
| 2026-10-28 | Flatten a photographed statement | 2 | 20 min | **failed on aspect** in 4.1 min: corners exact, content candidate-verified, but output 0.894 vs page 0.783 (14% stretch), shadow/gradient untouched, `notes.json` aspect not read before sign-off &mdash; `attempts/2026-10-28-skewed-statement/` · [worklog](https://claude.ai/artifact/NZUPHZi566w3sUHoUVscbb) |
