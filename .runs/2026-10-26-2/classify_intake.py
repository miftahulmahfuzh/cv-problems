import json
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

MODEL_NAME = "openai/clip-vit-base-patch32"
IMAGE_PATH = "input/intake_07.png"
OUTPUT_PATH = "output/classification.json"

# class -> (handler, prompt variants to average)
CLASSES = {
    "chart": (
        "chart_handler",
        [
            "a chart or graph showing data trends",
            "a bar chart",
            "a line chart with axes",
            "a pie chart with statistics",
        ],
    ),
    "diagram": (
        "diagram_parser",
        [
            "a technical diagram with labeled parts",
            "a schematic drawing",
            "a flowchart with boxes and arrows",
            "an architectural or engineering diagram",
        ],
    ),
    "photo": (
        "photo_handler",
        [
            "a photograph of a real-world scene",
            "a photo taken with a camera",
            "a picture of people or objects in real life",
        ],
    ),
    "scanned_document": (
        "ocr_pipeline",
        [
            "a scanned page of printed paragraph text",
            "a scanned document with blocks of text",
            "a photocopy of a text document",
        ],
    ),
    "table": (
        "ocr_table_extractor",
        [
            "a table of data with rows and columns",
            "a spreadsheet with numbers and columns",
            "a financial statement table with rows of figures",
        ],
    ),
    "other": (
        "manual_review",
        [
            "a miscellaneous image",
            "an image that does not fit chart, diagram, photo, scanned document, or table categories",
        ],
    ),
}

model = CLIPModel.from_pretrained(MODEL_NAME)
processor = CLIPProcessor.from_pretrained(MODEL_NAME)
model.eval()

image = Image.open(IMAGE_PATH).convert("RGB")

with torch.no_grad():
    image_inputs = processor(images=image, return_tensors="pt")
    image_features = model.get_image_features(**image_inputs).pooler_output
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)

    class_names = list(CLASSES.keys())
    class_embeddings = []
    for name in class_names:
        _, prompts = CLASSES[name]
        text_inputs = processor(text=prompts, return_tensors="pt", padding=True)
        text_features = model.get_text_features(**text_inputs).pooler_output
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        mean_embedding = text_features.mean(dim=0)
        mean_embedding = mean_embedding / mean_embedding.norm()
        class_embeddings.append(mean_embedding)

    text_matrix = torch.stack(class_embeddings)  # [num_classes, dim]
    logit_scale = model.logit_scale.exp()
    logits = logit_scale * image_features @ text_matrix.T  # [1, num_classes]
    probs = logits.softmax(dim=-1).squeeze(0)

confidence_breakdown = {
    name: round(probs[i].item(), 4) for i, name in enumerate(class_names)
}
ranked = sorted(confidence_breakdown.items(), key=lambda kv: kv[1], reverse=True)
predicted_type, top_confidence = ranked[0]
handler = CLASSES[predicted_type][0]

result = {
    "image": IMAGE_PATH,
    "model": MODEL_NAME,
    "method": "clip_zero_shot",
    "predicted_type": predicted_type,
    "confidence": top_confidence,
    "handler": handler,
    "confidence_breakdown": confidence_breakdown,
}

os.makedirs("output", exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    json.dump(result, f, indent=2)

print(json.dumps(result, indent=2))
