"""Call OCR from a script running in .venv (cv2 5.0, torch, ...) without installing it there.

    from ocr_bridge import ocr
    for w in ocr(img_or_path): print(w["text"], w["bbox"])

`ocr` runs ocr_worker.py in ~/cv-problems/.venv-ocr as a subprocess, so the two cv2
builds never share a process. Accepts a path or a BGR/gray ndarray (e.g. one cell crop).
Each call pays a ~1 s model load; for many crops, OCR the whole page once and assign
the lines to your cells by bbox overlap.
"""
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / ".venv-ocr" / "bin" / "python"
WORKER = Path(__file__).with_name("ocr_worker.py")


def ocr(img):
    if not isinstance(img, (str, Path)):
        import cv2
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        cv2.imwrite(tmp.name, img)
        img = tmp.name
    r = subprocess.run([str(PY), str(WORKER), str(img)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    import sys
    for w in ocr(sys.argv[1]):
        print(w["bbox"], w["text"])
