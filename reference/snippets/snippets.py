#!/usr/bin/env python3
"""Verified snippets for the 15-minute test. Every block below actually ran
on THIS env (torch 2.14 CPU, transformers 5.20). Copy blocks out; don't recall
them from memory -- the 4.x API you remember is wrong in two places (marked !!).

    python scratch/snippets.py          # runs everything, ~25s warm
    python scratch/snippets.py clip     # run one section
"""
import os
import sys
import time

import numpy as np
import torch
from PIL import Image

torch.set_grad_enabled(False)                      # !! always, for inference
os.environ.setdefault("HF_HUB_OFFLINE", "1")       # never let it phone home

IMGS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images")
P = lambda f: os.path.join(IMGS, f)


def sec(name):
    print(f"\n\033[1m── {name}\033[0m")


# ---------------------------------------------------------------- cv2 basics
def cv2_shapes():
    """Threshold -> contours -> classify by vertex count. The classic CV warmup."""
    sec("cv2: contours + shape classification")
    import cv2
    img = cv2.imread(P("shapes.png"))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)                 # fixture has mild noise
    _, th = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in sorted(cnts, key=cv2.contourArea, reverse=True):
        area = cv2.contourArea(c)
        if area < 500:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        circularity = 4 * np.pi * area / (peri * peri)
        name = {3: "triangle", 4: "quad", 5: "pentagon"}.get(
            len(approx), "circle" if circularity > 0.8 else f"{len(approx)}-gon")
        x, y, w, h = cv2.boundingRect(c)
        # mean BGR inside the shape -> dominant colour
        mask = np.zeros(gray.shape, np.uint8)
        cv2.drawContours(mask, [c], -1, 255, -1)
        b, g, r, _ = cv2.mean(img, mask=mask)
        print(f"  {name:<9} area={area:7.0f} box=({x},{y},{w},{h}) rgb=({r:.0f},{g:.0f},{b:.0f})")


# ------------------------------------------------------------------ resnet18
def resnet():
    """Supervised classifier + a 512-d penultimate feature vector."""
    sec("torchvision: resnet18 classify + embed")
    from torchvision.models import ResNet18_Weights, resnet18
    w = ResNet18_Weights.DEFAULT
    model = resnet18(weights=w).eval()
    pre = w.transforms()                           # !! use the weights' own transform
    cats = w.meta["categories"]

    im = Image.open(P("photo_landscape.jpg")).convert("RGB")
    x = pre(im).unsqueeze(0)
    probs = model(x).softmax(-1)[0]
    top = probs.topk(3)
    for p, i in zip(top.values, top.indices):
        print(f"  {cats[i]:<28} {p:.3f}")

    feat = torch.nn.Sequential(*list(model.children())[:-1])(x).flatten(1)
    print(f"  embedding {tuple(feat.shape)}  (strip the fc layer for features)")


# ---------------------------------------------------------------------- CLIP
def clip():
    """Zero-shot classification AND the image/text embeddings behind it."""
    sec("CLIP: zero-shot + embeddings")
    from transformers import CLIPModel, CLIPProcessor
    n = "openai/clip-vit-base-patch32"
    model, proc = CLIPModel.from_pretrained(n).eval(), CLIPProcessor.from_pretrained(n)

    labels = ["a stock chart", "a financial document", "colored shapes", "a landscape photo"]
    files = ["candlestick_chart.png", "document_table.png", "shapes.png", "photo_landscape.jpg"]
    ims = [Image.open(P(f)).convert("RGB") for f in files]

    inp = proc(text=labels, images=ims, return_tensors="pt", padding=True)
    out = model(**inp)
    probs = out.logits_per_image.softmax(-1)       # (n_images, n_labels)
    for f, row in zip(files, probs):
        print(f"  {f:<24} {labels[int(row.argmax())]:<24} {row.max():.2f}")

    # embeddings for retrieval / clustering / dedup -- ALWAYS L2-normalise
    emb = out.image_embeds / out.image_embeds.norm(dim=-1, keepdim=True)
    sim = emb @ emb.T
    print(f"  image-image cosine matrix {tuple(sim.shape)}, "
          f"max off-diagonal {(sim - torch.eye(len(files))).max():.2f}")


# ---------------------------------------------------------------------- BLIP
def blip():
    """Caption-only. blip-vqa-base is NOT cached -- do not promise VQA."""
    sec("BLIP: captioning (+ prompted continuation)")
    from transformers import BlipForConditionalGeneration, BlipProcessor
    n = "Salesforce/blip-image-captioning-base"
    model, proc = BlipForConditionalGeneration.from_pretrained(n).eval(), BlipProcessor.from_pretrained(n)

    im = Image.open(P("candlestick_chart.png")).convert("RGB")
    out = model.generate(**proc(im, return_tensors="pt"), max_new_tokens=25)
    print(f'  unconditional: "{proc.decode(out[0], skip_special_tokens=True)}"')

    # conditional: seed the decoder with a prefix to steer it
    out = model.generate(**proc(im, text="a chart showing", return_tensors="pt"), max_new_tokens=25)
    print(f'  prompted:      "{proc.decode(out[0], skip_special_tokens=True)}"')


# ---------------------------------------------------------------------- Qwen
def qwen():
    """Local 1.5B LLM, offline. ~8 tok/s on CPU -- keep max_new_tokens small."""
    sec("Qwen2.5-Coder-1.5B: structured JSON out")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    n = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    tok = AutoTokenizer.from_pretrained(n)
    model = AutoModelForCausalLM.from_pretrained(n, dtype=torch.float32).eval()  # !! dtype=, not torch_dtype=

    msgs = [{"role": "user", "content":
             "Extract to JSON with keys ticker, side, lots, price. "
             "Reply with JSON only.\nTrade: sold 35 lots TLKM at 2870."}]
    # !! return_dict=True is REQUIRED in transformers 5.x; return_tensors alone crashes generate()
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                  return_dict=True, return_tensors="pt")
    t0 = time.time()
    out = model.generate(**enc, max_new_tokens=64, do_sample=False)
    txt = tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
    print(f"  ({time.time() - t0:.1f}s)\n" + "\n".join("  " + l for l in txt.strip().splitlines()))


SECTIONS = {"cv2": cv2_shapes, "resnet": resnet, "clip": clip, "blip": blip, "qwen": qwen}

if __name__ == "__main__":
    want = sys.argv[1:] or list(SECTIONS)
    t0 = time.time()
    for k in want:
        SECTIONS[k]()
    print(f"\ntotal {time.time() - t0:.1f}s\n")
