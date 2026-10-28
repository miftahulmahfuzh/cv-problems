# CLAUDE.md

Practice harness for a computer-vision live-coding interview. See `README.md`.

## Environment

`.venv/` at the repo root — Python 3.12, torch CPU, torchvision, transformers,
opencv (`cv2`), pymupdf, scikit-learn, pandas, numpy, matplotlib, pillow. Model
weights for `resnet18`, `CLIP ViT-B/32` and `BLIP captioning` are warm in `~/.cache`.

```bash
source /home/miftah/cv-problems/.venv/bin/activate
```

- **No `pip install` / `uv pip install` into `.venv`.** It is a mirror of the sealed
  interview environment; adding to it makes practice runs unrepresentative. If
  something is genuinely missing, say so and work around it — that is the skill being
  rehearsed. A separate venv for an experiment is fine. `.venv-ocr/` is one: OCR via
  `reference/snippets/ocr_bridge.py`, which calls it as a subprocess (see README).
- **No model downloads.** Load the cached names above.
- **CPU only.** No `.cuda()`.
- `cv2.imshow` has no display under WSL. Write the image and read it back.

## Exam integrity — the one invariant

`attempts/<slug>/PROBLEM.md` and `attempts/<slug>/GROUND_TRUTH.json` are **sealed
from the session sitting in `attempts/<slug>/workspace/`**. That session's own
`CLAUDE.md` forbids reading its parent directory, and the ban holds even when the
candidate asks — the requirements have to come out of their mouth, which is the
entire point of the drill.

A session opened at the **repo root** (this file) is a coaching session, not an exam
session, and may read everything.

Never write a problem's answer, its ground truth, or a hint into `workspace/`.

## Adding an attempt

Use the harness rather than making directories by hand — it writes the workspace
`CLAUDE.md` carrying the integrity rules, and it records the start time the
evaluation measures against.

```bash
python bin/cvtest.py new   --slug count-outlets --title "..." --minutes 30
python bin/cvtest.py spawn --attempt attempts/2026-10-23-count-outlets
python bin/cvtest.py finish --attempt attempts/2026-10-23-count-outlets
```

`/spawn-new-cv-test` drives `new` + `spawn`; `/finish-cv-test` drives `finish` and
writes the evaluation.

## Writing a brief

An interviewer's brief is **terse and slightly under-specified** — that is realistic
and it is what the drill tests. Leave exactly one or two genuine forks in it (what
counts as one object; whether the legend is included; pixels or metres) and record
the acceptable resolutions in `GROUND_TRUTH.json`, not in the brief. Do not leave it
*ambiguous about the deliverable* — the output artifact and its path are always
stated, because a real interviewer states those too.

## Evaluations

Score against the seven dimensions in `reference/prompting-playbook.md`. Be specific
and quote the candidate's actual words from `TRANSCRIPT.md`. An evaluation that says
"good communication" is worthless; one that quotes the instruction and names the
cheaper alternative is not.

> [!IMPORTANT]
> if user typed "i": for each points in Carry into the next attempt, you need to write a ready to paste example of the instruction that i can use. i like practical things, this way i can write similar instructions in the future. use haiku model for this task.
