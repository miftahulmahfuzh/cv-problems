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
PDF's own text layer via `pymupdf` rather than OCRing a raster. To add OCR anyway:
`uv pip install easyocr` into a **separate** venv — it pulls its own opencv build
and will fight the one in `.venv`.

## Attempts

| Date | Problem | Tier | Budget | Result |
|---|---|---|---|---|
| 2026-10-22 | Detect rectangles, mark centers | 1 | 15 min | passed — `attempts/2026-10-22-rect-center/` |
| 2026-10-23 | Count duplex receptacles on sheet E-101 | 4 | 30 min | passed in 7.7 min, agent-verified not candidate-verified — `attempts/2026-10-23-count-receptacles/` · [worklog](https://claude.ai/artifact/CbaHefVWbLvUpi8rick9zq) |
