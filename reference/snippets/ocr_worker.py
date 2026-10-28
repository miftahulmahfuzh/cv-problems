"""OCR worker. Run with .venv-ocr's python, never .venv's:

    .venv-ocr/bin/python reference/snippets/ocr_worker.py image.png

Prints a JSON list of {"text", "bbox": [x0, y0, x1, y1], "score"} in reading order.
rapidocr's wheel bundles its ONNX models, so nothing is downloaded at run time.
"""
import json
import sys

from rapidocr_onnxruntime import RapidOCR

result, _ = RapidOCR()(sys.argv[1])
out = []
for quad, text, score in result or []:
    xs, ys = [p[0] for p in quad], [p[1] for p in quad]
    out.append({"text": text, "score": round(float(score), 3),
                "bbox": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]})
print(json.dumps(out))
