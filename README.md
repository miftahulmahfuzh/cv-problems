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
attempts/<date>-<slug>/
    PROBLEM.md         the brief            <- the exam session must never read this
    GROUND_TRUTH.json  the expected answer  <- nor this
    workspace/         the exam session's cwd; input/ holds the data
    TRANSCRIPT.md      what you typed, reconstructed at finish
    EVALUATION.md      the scoring
```

The split between `attempts/<slug>/` and `attempts/<slug>/workspace/` is the whole
integrity mechanism: the session works inside `workspace/`, and its `CLAUDE.md`
forbids reading the parent. Otherwise "read PROBLEM.md and do it" would be a valid
move and the drill would teach nothing.

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
