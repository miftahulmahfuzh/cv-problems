import json
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

MODEL_NAME = "openai/clip-vit-base-patch32"
IMAGE_PATH = "input/intake_07.png"

# Same prompt set as classify_intake.py, with the one image-tailored
# prompt under "table" ("...tickers, quantities and prices") called out
# separately so we can test with and without it.
CLASSES = {
    "chart": [
        "a chart or graph showing data trends",
        "a bar chart",
        "a line chart with axes",
        "a pie chart with statistics",
    ],
    "diagram": [
        "a technical diagram with labeled parts",
        "a schematic drawing",
        "a flowchart with boxes and arrows",
        "an architectural or engineering diagram",
    ],
    "photo": [
        "a photograph of a real-world scene",
        "a photo taken with a camera",
        "a picture of people or objects in real life",
    ],
    "scanned_document": [
        "a scanned page of printed paragraph text",
        "a scanned document with blocks of text",
        "a photocopy of a text document",
    ],
    "table": [
        "a table of data with rows and columns",
        "a spreadsheet with numbers and columns",
        "a financial statement table with rows of figures",
    ],
    "other": [
        "a miscellaneous image",
        "an image that does not fit chart, diagram, photo, scanned document, or table categories",
    ],
}
LEAKY_TABLE_PROMPT = "a trade confirmation table listing tickers, quantities and prices"

model = CLIPModel.from_pretrained(MODEL_NAME)
processor = CLIPProcessor.from_pretrained(MODEL_NAME)
model.eval()

image = Image.open(IMAGE_PATH).convert("RGB")


def embed_texts(prompts):
    inputs = processor(text=prompts, return_tensors="pt", padding=True)
    features = model.get_text_features(**inputs).pooler_output
    return features / features.norm(dim=-1, keepdim=True)


def class_confidence(class_prompt_map, logit_scale, image_features):
    names = list(class_prompt_map.keys())
    embeddings = []
    for name in names:
        feats = embed_texts(class_prompt_map[name])
        mean_emb = feats.mean(dim=0)
        mean_emb = mean_emb / mean_emb.norm()
        embeddings.append(mean_emb)
    matrix = torch.stack(embeddings)
    logits = logit_scale * image_features @ matrix.T
    probs = logits.softmax(dim=-1).squeeze(0)
    return {name: round(probs[i].item(), 4) for i, name in enumerate(names)}


with torch.no_grad():
    image_inputs = processor(images=image, return_tensors="pt")
    image_features = model.get_image_features(**image_inputs).pooler_output
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    logit_scale = model.logit_scale.exp()

    # --- Diagnostic 2: per-prompt similarity, not averaged away ---
    print("=" * 70)
    print("PER-PROMPT SIMILARITY (cosine sim, scaled by CLIP logit_scale,")
    print("softmax taken over ALL individual prompts across ALL classes)")
    print("=" * 70)

    all_prompts = []
    all_labels = []
    for name, prompts in CLASSES.items():
        for p in prompts:
            all_prompts.append(p)
            all_labels.append(name)
    all_prompts.append(LEAKY_TABLE_PROMPT)
    all_labels.append("table [LEAKY]")

    text_feats = embed_texts(all_prompts)
    logits = logit_scale * image_features @ text_feats.T
    probs = logits.softmax(dim=-1).squeeze(0)

    ranked = sorted(
        zip(all_labels, all_prompts, probs.tolist()), key=lambda x: x[2], reverse=True
    )
    for label, prompt, p in ranked:
        print(f"  [{label:<18}] {p:7.4f}  \"{prompt}\"")

    # --- Diagnostic 1: class-level result with vs without the leaky prompt ---
    print()
    print("=" * 70)
    print("CLASS-LEVEL CONFIDENCE: with vs without the image-tailored")
    print('table prompt ("%s")' % LEAKY_TABLE_PROMPT)
    print("=" * 70)

    classes_with_leak = {k: list(v) for k, v in CLASSES.items()}
    classes_with_leak["table"] = classes_with_leak["table"] + [LEAKY_TABLE_PROMPT]

    conf_with_leak = class_confidence(classes_with_leak, logit_scale, image_features)
    conf_without_leak = class_confidence(CLASSES, logit_scale, image_features)

    print(f"{'class':<20}{'with leaky prompt':<22}{'generic prompts only':<22}")
    for name in CLASSES:
        print(f"{name:<20}{conf_with_leak[name]:<22}{conf_without_leak[name]:<22}")

    top_with = max(conf_with_leak.items(), key=lambda kv: kv[1])
    top_without = max(conf_without_leak.items(), key=lambda kv: kv[1])
    print()
    print(f"Top class WITH leaky prompt:    {top_with[0]} ({top_with[1]})")
    print(f"Top class WITHOUT leaky prompt: {top_without[0]} ({top_without[1]})")

    report = {
        "per_prompt_similarity": [
            {"class": label, "prompt": prompt, "softmax_weight": round(p, 4)}
            for label, prompt, p in ranked
        ],
        "class_confidence_with_leaky_prompt": conf_with_leak,
        "class_confidence_generic_prompts_only": conf_without_leak,
    }

with open("output/prompt_diagnosis.json", "w") as f:
    json.dump(report, f, indent=2)
print()
print("Wrote output/prompt_diagnosis.json")
