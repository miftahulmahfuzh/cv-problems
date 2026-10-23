# Computer vision for someone who does NLP

You already have the hard half. Embeddings, transformers, fine-tuning, evaluation
discipline, "the model is confidently wrong, prove it" — that all transfers. What
you are missing is a **vocabulary** and a **reflex for which tool a task wants**.
This document is those two things. It is not a tutorial; it is the glossary you
wish you had at 16:49 yesterday.

---

## 0. The one mental model

An image is `numpy.ndarray` of shape `(H, W, 3)`, `dtype=uint8`, values 0–255.

That is it. Everything else is array manipulation with domain-specific names.

```python
img = cv2.imread("x.jpg")       # (H, W, 3), BGR order, or None on failure
h, w = img.shape[:2]            # NOT img.shape[0], img.shape[1] as (x, y)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)   # (H, W), one channel
```

**Two indexing conventions coexist and they are transposed from each other.**
Array indexing is `img[y, x]` (row first). Every cv2 *function* takes points as
`(x, y)` (column first). This is the single most common bug. When you write
`cv2.circle(img, (cx, cy), ...)` that is x-then-y; when you write `img[cy, cx]`
that is y-then-x. Both appear in the same five lines constantly.

**cv2 is BGR, everything else is RGB.** PIL, matplotlib, torchvision and every
model you load are RGB. `cv2.imread` then feeding straight to a model without
`cv2.cvtColor(img, cv2.COLOR_BGR2RGB)` gives you a model that sees blue skies as
orange. It usually still "works" — slightly worse — which is why it survives.

**`cv2.imread` returns `None` on a missing or unreadable file. It does not
raise.** You then get `AttributeError: 'NoneType' object has no attribute 'shape'`
forty lines later. Always check.

---

## 1. The two worlds, and which one a task wants

| | **Classical CV** (`cv2`) | **Learned CV** (`torch`, `transformers`) |
|---|---|---|
| What it is | Deterministic pixel arithmetic | A trained model |
| Good at | Clean synthetic input, geometry, structure, repeatable shapes, anything with a crisp edge | Messy real photos, semantics, "what is this", open vocabulary |
| Bad at | Natural photos, anything needing meaning, lighting variation | Exact geometry, counting, guaranteeing determinism |
| Cost | Microseconds | Hundreds of ms on CPU, and weights must be cached |
| Explains itself | Yes — you can print every intermediate | No |

**The reflex to build:** a technical drawing, a chart, a scanned form, a screenshot
— anything *drawn by a computer* — is a classical CV problem first. A photograph of
the world is a learned-model problem first. Boon's domain (CAD-exported PDF plan
sets) is overwhelmingly the first kind, which is good news: it is the kind you can
debug.

The strongest answers usually **combine** them: classical CV to find and crop
candidate regions, a model to label them. That is also the architecture Boon
describes, and it is the architecture to propose out loud in an interview.

---

## 2. The vocabulary

### Threshold / binarize
Turn a grayscale image into pure black-and-white so shapes become findable.

```python
_, bw = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)              # fixed cut
_, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)  # auto cut
bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                           cv2.THRESH_BINARY, 31, 5)                  # per-region cut
```

- **Otsu** picks the cut automatically by maximising between-class variance. Use it
  whenever lighting is even. It is one flag and it removes a magic number from your
  code — say that out loud.
- **Adaptive** computes a different cut for every neighbourhood. Use it for scans,
  photos of paper, anything with a shadow across the page.
- **`THRESH_BINARY_INV`** flips it. You almost always want INV for documents and
  drawings, because the ink is *dark* and every downstream function (contours,
  connected components) looks for **white blobs on black**. Getting this backwards
  makes your "object" the page itself.

### Morphology — erode, dilate, open, close
Grow or shrink white regions with a structuring element (a "kernel").

```python
k = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
cv2.erode(bw, k)                          # shrink white, kill specks
cv2.dilate(bw, k)                         # grow white, join near-touching things
cv2.morphologyEx(bw, cv2.MORPH_OPEN, k)   # erode then dilate: remove noise, keep size
cv2.morphologyEx(bw, cv2.MORPH_CLOSE, k)  # dilate then erode: fill gaps, keep size
```

The NLP analogue is a stopword filter and a gap-filling regex. **Close** repairs a
dashed or broken line into a solid one — which is exactly what a hand-drawn stroke
or a JPEG-mangled wall needs. **Open** deletes speckle. A tall thin kernel
`(1, 25)` only joins things vertically; that asymmetry is how you isolate the
vertical walls of a floor plan and ignore the horizontal ones.

### Contour
The ordered list of points tracing the boundary of a white blob. The workhorse.

```python
contours, hierarchy = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```

- `RETR_EXTERNAL` — outermost boundaries only. **A thick drawn outline has an outer
  edge and an inner edge; this collapses them to one object.** That is the flag that
  made yesterday's answer correct.
- `RETR_LIST` — every contour, flat, no nesting info.
- `RETR_TREE` — every contour *plus* `hierarchy`, telling you which contour is
  inside which. This is how you find "a room that contains a door symbol", or count
  holes.
- `CHAIN_APPROX_SIMPLE` compresses straight runs to their endpoints. Always use it.

Per contour:

```python
area = cv2.contourArea(c)               # pixels enclosed
peri = cv2.arcLength(c, True)           # perimeter, closed
x, y, w, h = cv2.boundingRect(c)        # axis-aligned box
(cx, cy), (bw_, bh_), angle = cv2.minAreaRect(c)   # ROTATED box — for tilted scans
hull = cv2.convexHull(c)                # rubber band around it
approx = cv2.approxPolyDP(c, 0.02 * peri, True)    # simplify to corners
```

**`approxPolyDP` is how you classify a shape.** It is Douglas–Peucker: drop points
that are within `epsilon` of the line between their neighbours. `len(approx) == 3`
is a triangle, `4` a quadrilateral, `> 8` roughly a circle. The epsilon is almost
always `0.01–0.04 * arcLength` — a fraction of the perimeter, so it scales with the
shape instead of being a pixel constant.

### Bounding box vs rotated box vs convex hull
- **Bounding box** `boundingRect` — axis-aligned, `(x, y, w, h)`. Fast, and what
  every detection model and dataset format means by "box". Center is
  `(x + w//2, y + h//2)`.
- **Rotated box** `minAreaRect` — the *smallest* box at any angle. Use it the
  moment the input might be tilted (a photographed or scanned drawing). Its `angle`
  is also how you measure skew in order to correct it.
- **Convex hull** — the tightest convex outline. Use it to repair a shape broken
  into pieces, or to measure *solidity* = `contourArea / hullArea`, which separates
  a solid blob from a spidery one.

### Moments and centroid
The "center of mass" of a shape, as opposed to the center of its box.

```python
M = cv2.moments(c)
cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])   # guard m00 == 0
```

For an L-shaped room the centroid can fall **outside** the shape, while the box
center is meaningless for a different reason. Which one is "the center" is a
question worth asking rather than assuming — yesterday you asked it, and that was
the right instinct.

### Canny edges
Gradient-based edge detector producing thin white lines on black.

```python
edges = cv2.Canny(gray, 50, 150)    # low, high hysteresis thresholds
```

Reach for it when you want *boundaries* rather than *regions* — specifically as the
input to Hough. For clean synthetic images a threshold is usually better; Canny
earns its place on photographs and gradients.

### Hough transform — lines and circles
Finds straight lines and circles even when broken or partially occluded. **This is
the most important single tool for floor plans**, because a floor plan is walls, and
walls are long straight lines.

```python
lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=80,
                        minLineLength=50, maxLineGap=10)   # -> [[x1,y1,x2,y2], ...]
circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                           param1=100, param2=30, minRadius=5, maxRadius=40)
```

`minLineLength` and `maxLineGap` are the two knobs that matter: the first rejects
short noise, the second decides whether a dashed line is one line or twenty. A wall
interrupted by a door is one wall with a gap — tune `maxLineGap` and you have made a
domain decision, not a parameter tweak.

### Template matching + non-maximum suppression
Slide a small patch over the image and score every position. **This is how you count
repeated symbols on a drawing** when you have one clean example of the symbol.

```python
res = cv2.matchTemplate(gray, templ, cv2.TM_CCOEFF_NORMED)   # (H-h+1, W-w+1) scores
ys, xs = np.where(res >= 0.8)
```

It is fast, exact, needs no training and **no model download** — a real advantage in
a sealed environment. Its weaknesses are the thing to say out loud: it is not
rotation-invariant, not scale-invariant, and it returns a cluster of near-duplicate
hits around every match. The fix for the last one is NMS (below). Rotation is
handled by matching several rotated copies of the template.

### IoU and NMS
**IoU** (intersection over union) = overlap area / union area of two boxes. `0` is
disjoint, `1` is identical. It is the standard "are these the same detection"
measure and the basis of every detection metric.

**NMS** (non-maximum suppression): sort candidate boxes by score, keep the best,
delete everything overlapping it above an IoU threshold, repeat. Without it, one
real object yields fifty boxes.

```python
idx = cv2.dnn.NMSBoxes(boxes, scores, score_threshold=0.5, nms_threshold=0.3)
```

The NLP analogue is deduplicating near-identical retrieved passages before you
rerank them. Same idea, same reason.

### Connected components
A faster, simpler alternative to contours when you only want blobs and their stats.

```python
n, labels, stats, centroids = cv2.connectedComponentsWithStats(bw, connectivity=8)
# stats[i] = [x, y, w, h, area]; centroids[i] = (cx, cy); label 0 is background
```

It hands you the box, the area and the centroid for every blob in one call, already
vectorised. For "count the things and give me their centers" this is often shorter
and faster than the contour loop — and it gives you `area` to filter on for free.

### Color spaces
`BGR` (cv2 default), `RGB` (everyone else), `GRAY`, `HSV`.

**HSV** separates *hue* (which color) from *saturation* and *value* (how bright).
Selecting "the red things" in BGR means a 3D box that changes with lighting; in HSV
it is a hue range and it survives shadow. Any "find the colored X" task should go
through HSV. Note cv2's hue is 0–179, not 0–360.

### Blur
```python
cv2.GaussianBlur(img, (5, 5), 0)   # general denoise; kernel must be ODD
cv2.medianBlur(img, 5)             # kills salt-and-pepper specks, keeps edges
cv2.bilateralFilter(img, 9, 75, 75)  # smooths flat areas, preserves edges; slow
```
A small Gaussian before thresholding is nearly free and stops JPEG artifacts from
becoming contours. It is the cheapest robustness you can buy.

### Resize, interpolation, letterbox
```python
cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)  # shrinking
cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)  # growing
```
`INTER_AREA` for down, `INTER_CUBIC`/`INTER_LINEAR` for up. **Every coordinate you
computed before a resize is wrong after it** — keep the scale factor and multiply
back, or do all detection at native resolution and only resize for display.
*Letterboxing* is resizing while preserving aspect ratio and padding the remainder;
models want fixed input sizes, and squashing a wide drawing into a square distorts
every symbol on it.

### Perspective transform / homography
A 3×3 matrix mapping one plane onto another. Four point correspondences define it.

```python
M = cv2.getPerspectiveTransform(src_4pts, dst_4pts)
flat = cv2.warpPerspective(img, M, (W, H))
```

This is how you flatten a *photograph* of a document into a scan-like rectangle —
find the page's four corners (largest 4-point `approxPolyDP`), warp them to a
rectangle. If the next test hands you a phone photo of a drawing rather than a PDF,
this is the first move.

---

## 3. Task types — the words that name what you are being asked for

| Name | Output | Typical tool |
|---|---|---|
| **Classification** | one label per image | resnet18, CLIP zero-shot |
| **Detection** | boxes + labels + scores | contours/template matching; YOLO/DETR if available |
| **Segmentation** (semantic) | a label per *pixel* | threshold/watershed; U-Net, SAM |
| **Instance segmentation** | a mask per *object* | Mask R-CNN, SAM |
| **Keypoints / landmarks** | named points | pose models; corner detection |
| **OCR** | text + boxes | tesseract/easyocr; or the PDF's own text layer |
| **Captioning / VQA** | a sentence / an answer | BLIP, modern VLMs |
| **Retrieval / similarity** | nearest neighbours | CLIP embeddings + cosine |

Say the right word and the whole conversation gets shorter. "This is instance
segmentation, not detection, because two adjacent rooms share a wall" is a sentence
that demonstrates more than a working script does.

### CLIP, in NLP terms
CLIP is a bi-encoder trained with a contrastive loss — the exact architecture as a
sentence-embedding retrieval model, with an image tower instead of a second text
tower. Zero-shot classification is just retrieval: embed the image, embed
`"a photo of a {label}"` for each candidate label, take the argmax cosine. You
already know this model; it was only ever wearing a different hat.

```python
from transformers import CLIPModel, CLIPProcessor
m = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
p = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
inp = p(text=["a floor plan", "a photograph", "a chart"], images=pil_img,
        return_tensors="pt", padding=True)
probs = m(**inp).logits_per_image.softmax(-1)
```

Its real limits, worth stating: it is a global descriptor, so it is good at "what
kind of image is this" and bad at "how many of X are in it" or "where is X". Do not
ask CLIP to count. For counting, use geometry.

---

## 4. The gotchas that actually bite

1. **`imread` returns `None` silently.** Check it, every time.
2. **`(x, y)` in functions, `[y, x]` in arrays.** Transposed, in the same breath.
3. **BGR vs RGB** between cv2 and everything else.
4. **Ink is dark; blobs must be white.** Forget `THRESH_BINARY_INV` on a document
   and you have segmented the paper.
5. **Thick outlines produce two contours.** `RETR_EXTERNAL`, or dedupe by hierarchy.
6. **`contourArea` ≠ bounding-box area.** Their ratio (*extent*) is a free feature:
   a filled rectangle is ~1.0, a diagonal line is ~0.1.
7. **uint8 wraps around.** `img + 50` darkens your highlights. Use
   `cv2.add` / `cv2.convertScaleAbs`, or cast to int16 first.
8. **Kernel sizes must be odd** for Gaussian and median blur.
9. **JPEG artifacts become contours.** Blur first, filter by area after.
10. **Coordinates do not survive a resize.** Keep the scale factor.
11. **`cv2.imshow` has no display in WSL.** Write a file and look at it instead —
    and *actually look at it*. Reading back the annotated output is the one
    verification step that catches everything else on this list.

---

## 5. The decision tree

```
Is the input a PDF?
├── Does it have a text layer?  (pymupdf: page.get_text("words"))
│   ├── yes -> you have text AND coordinates for free. No OCR. Start here.
│   │          Plan set (walls, symbols, a schedule sheet)?
│   │          -> reference/pdf-plan-sets.md
│   └── no  -> render to raster at 200-300 dpi, then treat as an image
└── not a PDF -> it is an image

Was the image drawn by a computer (chart, CAD, form, screenshot)?
├── yes -> classical CV. Threshold -> morphology -> contours/Hough. Deterministic.
│          Need to find a repeated symbol? template matching + NMS.
│          Need structure (rows, walls, grid)? Hough lines, or projection profiles
│          (sum pixels along an axis -- peaks are the lines).
└── no (a photograph) -> a model.
           "what is it?"            -> CLIP zero-shot / resnet18
           "describe it"            -> BLIP
           "find instances of X"    -> a detector; if none is installed, say so
                                       and fall back to color/shape heuristics

Counting anything?  -> never ask a VLM. Geometry, then NMS, then sanity-check
                       the number against something independent.
Measuring anything? -> you need SCALE. Find the scale bar or a known dimension
                       first; pixels are not metres and nobody wants pixels.
```

---

## 6. What to say out loud

Interviewers hire the narration as much as the code. Four lines that land:

- *"This is drawn by a computer, so I'll do it deterministically with cv2 rather
  than reach for a model — it'll be exact and I can show you every intermediate."*
- *"Let me write the intermediate mask to disk and look at it before I trust the
  count."*
- *"A thick stroke gives an outer and an inner contour, so I'll take external
  contours only — otherwise every object is detected twice."*
- *"I don't have an OCR engine in this environment, so I can recover the table's
  structure but not its glyphs. Here's the half that needs vision."*

See `prompting-playbook.md` for how to get Claude to produce that code fast, and
`problem-ladder.md` for the problem archetypes themselves.
