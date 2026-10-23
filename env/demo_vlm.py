#!/usr/bin/env python3
"""30-second proof the warm model cache works offline. Not test work -- a check.

    python demo_vlm.py
"""
import os
import time

import torch
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IMGS = os.path.join(HERE, "images")
torch.set_grad_enabled(False)


def clip_zero_shot():
    from transformers import CLIPModel, CLIPProcessor
    name = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(name).eval()
    proc = CLIPProcessor.from_pretrained(name)

    labels = [
        "a candlestick stock chart",
        "a printed invoice or financial table",
        "simple colored geometric shapes",
        "a landscape photograph",
    ]
    files = ["candlestick_chart.png", "document_table.png",
             "shapes.png", "photo_landscape.jpg"]

    print("\nCLIP zero-shot (no training, just image-text similarity)")
    print(f"  {'file':<26}{'top label':<38}conf")
    hits = 0
    for i, f in enumerate(files):
        with Image.open(os.path.join(IMGS, f)) as im:
            inputs = proc(text=labels, images=im.convert("RGB"),
                          return_tensors="pt", padding=True)
        probs = model(**inputs).logits_per_image.softmax(dim=1)[0]
        j = int(probs.argmax())
        mark = "+" if j == i else "x"
        hits += j == i
        print(f"  {mark} {f:<24}{labels[j]:<38}{probs[j]:.2f}")
    print(f"  {hits}/{len(files)} matched the expected label")


def blip_caption():
    from transformers import BlipForConditionalGeneration, BlipProcessor
    name = "Salesforce/blip-image-captioning-base"
    model = BlipForConditionalGeneration.from_pretrained(name).eval()
    proc = BlipProcessor.from_pretrained(name)

    print("\nBLIP captioning (image in, text out -- the VLM shape)")
    for f in ["photo_landscape.jpg", "candlestick_chart.png"]:
        with Image.open(os.path.join(IMGS, f)) as im:
            inputs = proc(im.convert("RGB"), return_tensors="pt")
        out = model.generate(**inputs, max_new_tokens=25)
        print(f"  {f:<24}\"{proc.decode(out[0], skip_special_tokens=True)}\"")


if __name__ == "__main__":
    t0 = time.time()
    clip_zero_shot()
    blip_caption()
    print(f"\ntotal {time.time() - t0:.1f}s, fully offline\n")
