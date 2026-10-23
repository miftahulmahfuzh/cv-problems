#!/usr/bin/env python3
"""Chart image -> structured JSON, fully offline. The multimodal shape the JD asks for.

    perception          CLIP zero-shot tags  +  BLIP caption  +  cv2 colour stats
         |
    reasoning           Qwen2.5-Coder-1.5B turns that evidence into strict JSON
         |
    validation          parse + schema-check, with a repair retry on bad JSON

The point to make out loud: a small VLM alone hallucinates ("the btc and btc
chart" -- it has never seen BBCA). Feeding it *measured* evidence from cv2 and
CLIP instead of asking it to free-associate is what makes the output usable.

    python scratch/pipeline.py
"""
import json
import os
import re
import time

import cv2
import numpy as np
import torch
from PIL import Image

torch.set_grad_enabled(False)
os.environ.setdefault("HF_HUB_OFFLINE", "1")

IMGS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images")
TARGET = os.path.join(IMGS, "candlestick_chart.png")

SCHEMA = {"instrument_kind": str, "timeframe_hint": str,
          "dominant_direction": str, "has_volume_panel": bool, "confidence": float}


# ------------------------------------------------------------- 1. perception
def clip_tags(im, groups):
    from transformers import CLIPModel, CLIPProcessor
    n = "openai/clip-vit-base-patch32"
    model, proc = CLIPModel.from_pretrained(n).eval(), CLIPProcessor.from_pretrained(n)
    out = {}
    for field, labels in groups.items():
        inp = proc(text=labels, images=im, return_tensors="pt", padding=True)
        p = model(**inp).logits_per_image.softmax(-1)[0]
        i = int(p.argmax())
        out[field] = (labels[i], float(p[i]))
    return out


def blip_caption(im):
    from transformers import BlipForConditionalGeneration, BlipProcessor
    n = "Salesforce/blip-image-captioning-base"
    model, proc = BlipForConditionalGeneration.from_pretrained(n).eval(), BlipProcessor.from_pretrained(n)
    out = model.generate(**proc(im, text="a financial chart showing", return_tensors="pt"),
                         max_new_tokens=24)
    return proc.decode(out[0], skip_special_tokens=True)


def cv_evidence(path):
    """Measured, not guessed: count green vs red candle pixels, detect a
    separate lower panel by finding a wide horizontal run of background."""
    bgr = cv2.imread(path)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, (70, 60, 60), (95, 255, 255)).sum() / 255
    red = (cv2.inRange(hsv, (0, 60, 60), (10, 255, 255)).sum()
           + cv2.inRange(hsv, (170, 60, 60), (180, 255, 255)).sum()) / 255

    ink = (cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) < 230).sum(axis=1)
    h = len(ink)
    gaps = [i for i in range(int(h * 0.4), int(h * 0.9)) if ink[i] < h * 0.01]
    return {"green_px": int(green), "red_px": int(red),
            "green_share": round(green / max(green + red, 1), 3),
            "panel_split_row": int(np.median(gaps)) if gaps else None,
            "size": [bgr.shape[1], bgr.shape[0]]}


# -------------------------------------------------------------- 2. reasoning
def ask_llm(prompt, max_new_tokens=160):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    n = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    tok = AutoTokenizer.from_pretrained(n)
    model = AutoModelForCausalLM.from_pretrained(n, dtype=torch.float32).eval()
    enc = tok.apply_chat_template([{"role": "user", "content": prompt}],
                                  add_generation_prompt=True,
                                  return_dict=True, return_tensors="pt")
    out = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False)
    return tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)


# ------------------------------------------------------------- 3. validation
def parse_json(text):
    """Small models fence their JSON and sometimes trail commentary."""
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S) or re.search(r"(\{.*\})", text, re.S)
    if not m:
        return None, "no JSON object found"
    try:
        return json.loads(m.group(1).strip()), None
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"


def validate(obj):
    problems = []
    for k, t in SCHEMA.items():
        if k not in obj:
            problems.append(f"missing {k!r}")
        elif not isinstance(obj[k], t) and not (t is float and isinstance(obj[k], int)):
            problems.append(f"{k!r} should be {t.__name__}, got {type(obj[k]).__name__}")
    return problems


def main():
    t0 = time.time()
    im = Image.open(TARGET).convert("RGB")
    print(f"target: {os.path.basename(TARGET)} {im.size[0]}x{im.size[1]}\n")

    print("[1/3] perception")
    ev = cv_evidence(TARGET)
    print(f"  cv2      green={ev['green_px']:,}px red={ev['red_px']:,}px "
          f"share={ev['green_share']}  panel split @y={ev['panel_split_row']}")
    tags = clip_tags(im, {
        "instrument_kind": ["a candlestick chart", "a line chart", "a bar chart", "a photograph"],
        "timeframe_hint": ["intraday minutes", "daily bars over months", "yearly data"],
        "dominant_direction": ["an uptrend", "a downtrend", "a sideways range"],
    })
    for k, (v, c) in tags.items():
        print(f"  CLIP     {k:<20} {v:<28} {c:.2f}")
    cap = blip_caption(im)
    print(f'  BLIP     "{cap}"   <- note the hallucination; evidence overrides it')

    print("\n[2/3] reasoning")
    prompt = (
        "You are a vision analyst. Convert the measured evidence into JSON.\n"
        "Trust the MEASUREMENTS over the caption; the caption comes from a small "
        "model that often invents tickers.\n\n"
        f"CLIP tags: {json.dumps({k: v for k, (v, _) in tags.items()})}\n"
        f"Measurements: {json.dumps(ev)}\n"
        f"Caption (unreliable): {cap!r}\n\n"
        "Reply with ONLY a JSON object with exactly these keys:\n"
        '  instrument_kind (string), timeframe_hint (string), '
        'dominant_direction (string), has_volume_panel (boolean), '
        'confidence (number 0-1).\n'
        "has_volume_panel is true if panel_split_row is not null."
    )
    raw = ask_llm(prompt)
    obj, err = parse_json(raw)

    print("\n[3/3] validation")
    if err:
        print(f"  first attempt failed: {err} -- retrying with a repair prompt")
        raw = ask_llm(prompt + f"\n\nYour previous reply was invalid ({err}). "
                               "Output the raw JSON object and nothing else.")
        obj, err = parse_json(raw)
    if err:
        print(f"  still invalid: {err}\n  raw:\n{raw}")
        return

    problems = validate(obj)
    print("  schema OK" if not problems else "  schema problems: " + "; ".join(problems))
    print("\nresult:")
    print("\n".join("  " + l for l in json.dumps(obj, indent=2).splitlines()))
    print(f"\ntotal {time.time() - t0:.1f}s, fully offline, CPU only\n")


if __name__ == "__main__":
    main()
