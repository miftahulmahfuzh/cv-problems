# Scratch workspace for a live coding test

Interview mock-up test, 15 minutes, AI-assisted. **Speed matters more than polish.**

## Rules for the assistant

- **Never run `pip install` / `uv pip install`.** Everything needed is already in `.venv`.
  If an import fails, say so — do not try to fix it by installing.
- **Never download model weights.** `resnet18`, `CLIP ViT-B/32` and `BLIP captioning`
  are already in `~/.cache`. Load them by the exact names in `warm_models.py`.
- **No GPU.** CPU only. Keep batch sizes and image counts small; never call `.cuda()`.
- Write new work into `scratch/`. Leave the files at the repo root alone.
- Prefer one short runnable file over a package. Print results; don't build a CLI.

## Environment

- `.venv` (Python 3.12) — torch (CPU), torchvision, transformers, pillow, opencv,
  matplotlib, scikit-learn, pandas, numpy. Already activated if the prompt shows `(.venv)`.
- Activate manually: `source .venv/bin/activate`

## Fixtures in `images/` (no network needed)

| file | what it is | good for |
|---|---|---|
| `candlestick_chart.png` | 1200x800 trading chart: OHLC, MA20, volume, shaded support band, dashed resistance, buy/sell markers, month axis | chart reading, VLM grounding, OCR of axis labels |
| `shapes.png` | 800x600, 6 colored shapes on near-white, mild noise | thresholding, contours, segmentation, shape classification |
| `document_table.png` | 900x1150 trade confirmation with a 6-column numeric table | OCR, table extraction, document VQA |
| `photo_landscape.jpg` | 1024x768 lossy JPEG, sky/ridge/sun | classification, embeddings, augmentation, format handling |

Regenerate any time: `python make_fixtures.py` (deterministic, seeded).

## Scripts

- `python check.py` — smoke test: imports, fixtures, a cv2 contour pass, a torch forward pass, cache status. Run this first.
- `python warm_models.py` — re-verify the model cache (already done; instant on a warm cache).
- `python demo_vlm.py` — 30-second proof that CLIP + BLIP load and run offline.
