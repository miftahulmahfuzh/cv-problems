#!/usr/bin/env python3
"""Smoke test: prove the environment is ready before the clock starts.

    python check.py
"""
import os
import sys
import time

FAIL = []


def ok(label, value=""):
    print(f"  \033[32m+\033[0m {label:<22} {value}")


def bad(label, err):
    print(f"  \033[31mx\033[0m {label:<22} {err}")
    FAIL.append(label)


print(f"\npython  {sys.version.split()[0]}  ({sys.executable})\n")
print("imports")

t0 = time.time()
try:
    import numpy
    ok("numpy", numpy.__version__)
except Exception as e:
    bad("numpy", e)

try:
    import torch
    ok("torch", f"{torch.__version__}  cuda={torch.cuda.is_available()}  threads={torch.get_num_threads()}")
except Exception as e:
    bad("torch", e)

try:
    import torchvision
    ok("torchvision", torchvision.__version__)
except Exception as e:
    bad("torchvision", e)

try:
    import transformers
    ok("transformers", transformers.__version__)
except Exception as e:
    bad("transformers", e)

try:
    import PIL
    ok("pillow", PIL.__version__)
except Exception as e:
    bad("pillow", e)

try:
    import cv2
    ok("opencv", cv2.__version__)
except Exception as e:
    bad("opencv", e)

try:
    import matplotlib
    ok("matplotlib", matplotlib.__version__)
except Exception as e:
    bad("matplotlib", e)

try:
    import sklearn
    ok("scikit-learn", sklearn.__version__)
except Exception as e:
    bad("scikit-learn", e)

try:
    import pandas
    ok("pandas", pandas.__version__)
except Exception as e:
    bad("pandas", e)

print(f"\n  (import time {time.time() - t0:.1f}s)")

print("\nfixtures")
here = os.path.dirname(os.path.abspath(__file__))
imgdir = os.path.join(here, "images")
expected = ["candlestick_chart.png", "shapes.png", "document_table.png",
            "photo_landscape.jpg"]
for name in expected:
    p = os.path.join(imgdir, name)
    if not os.path.exists(p):
        bad(name, "MISSING - run: python make_fixtures.py")
        continue
    try:
        from PIL import Image
        with Image.open(p) as im:
            ok(name, f"{im.size[0]}x{im.size[1]} {im.mode} {os.path.getsize(p):,}B")
    except Exception as e:
        bad(name, e)

print("\nround-trip")
try:
    import cv2
    import numpy as np
    a = cv2.imread(os.path.join(imgdir, "shapes.png"))
    g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(g, 240, 255, cv2.THRESH_BINARY_INV)
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    big = [c for c in cnts if cv2.contourArea(c) > 500]
    ok("cv2 contours", f"{len(big)} shapes found (expect 6)")
except Exception as e:
    bad("cv2 contours", e)

try:
    import torch
    import torchvision.transforms as T
    from PIL import Image
    with Image.open(os.path.join(imgdir, "photo_landscape.jpg")) as im:
        x = T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor()])(im.convert("RGB"))
    ok("torch transform", f"tensor {tuple(x.shape)} {x.dtype}")
    y = torch.nn.Conv2d(3, 8, 3)(x.unsqueeze(0))
    ok("torch forward", f"conv out {tuple(y.shape)}")
except Exception as e:
    bad("torch transform", e)

print("\nwarm model cache")
hub = os.path.expanduser("~/.cache/torch/hub/checkpoints")
hf = os.path.expanduser("~/.cache/huggingface/hub")
for label, d in (("torchvision weights", hub), ("huggingface hub", hf)):
    if os.path.isdir(d):
        files = [f for f in os.listdir(d)]
        total = sum(
            os.path.getsize(os.path.join(dp, f))
            for dp, _, fs in os.walk(d) for f in fs
        )
        ok(label, f"{len(files)} entries, {total / 1e6:.0f} MB")
    else:
        bad(label, "empty - run: python warm_models.py")

print()
if FAIL:
    print(f"\033[31mFAILED: {len(FAIL)} -> {', '.join(FAIL)}\033[0m\n")
    sys.exit(1)
print("\033[32mALL GREEN - environment is ready.\033[0m\n")
