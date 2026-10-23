#!/usr/bin/env python3
"""Pre-download model weights so nothing hits the network during the test.

    python warm_models.py

Downloads ~1.6 GB once, into ~/.cache. After this, every model below loads
offline in seconds.
"""
import sys
import time

STEPS = []


def step(label, fn):
    t0 = time.time()
    sys.stdout.write(f"  {label:<34} ... ")
    sys.stdout.flush()
    try:
        detail = fn()
        print(f"ok  {time.time() - t0:5.1f}s   {detail}")
        STEPS.append((label, True))
    except Exception as e:
        print(f"FAIL  {type(e).__name__}: {e}")
        STEPS.append((label, False))


def resnet18():
    """Classic CNN classifier — ImageNet-1k, ~45 MB."""
    from torchvision.models import ResNet18_Weights, resnet18 as _r
    w = ResNet18_Weights.DEFAULT
    m = _r(weights=w)
    m.eval()
    return f"{sum(p.numel() for p in m.parameters()) / 1e6:.1f}M params, {len(w.meta['categories'])} classes"


def clip():
    """Image-text contrastive model — zero-shot classification, ~600 MB."""
    from transformers import CLIPModel, CLIPProcessor
    name = "openai/clip-vit-base-patch32"
    m = CLIPModel.from_pretrained(name)
    CLIPProcessor.from_pretrained(name)
    return f"{sum(p.numel() for p in m.parameters()) / 1e6:.0f}M params"


def blip():
    """Vision-language captioner — image in, text out. The closest thing
    here to the VLM shape in the job description. ~990 MB."""
    from transformers import BlipForConditionalGeneration, BlipProcessor
    name = "Salesforce/blip-image-captioning-base"
    m = BlipForConditionalGeneration.from_pretrained(name)
    BlipProcessor.from_pretrained(name)
    return f"{sum(p.numel() for p in m.parameters()) / 1e6:.0f}M params"


if __name__ == "__main__":
    print("\nwarming model cache (first run downloads; later runs are instant)\n")
    step("torchvision resnet18", resnet18)
    step("transformers CLIP ViT-B/32", clip)
    step("transformers BLIP captioning", blip)
    failed = [l for l, good in STEPS if not good]
    print()
    if failed:
        print(f"  {len(failed)} failed: {', '.join(failed)}")
        print("  (network issue — rerun; the successful ones are cached already)\n")
        sys.exit(1)
    print("  all cached. check with: python check.py\n")
