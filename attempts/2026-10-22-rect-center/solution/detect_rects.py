"""Detect rectangular objects, mark each center with a red dot.

Strategy (per the brief):
  - binarize (dark ink on light paper)
  - external contours only, so a thick outline = ONE object, not outer+inner
  - every surviving contour -> its bounding box = the detection
  - center = bounding box center, drawn as a red dot
"""
import sys
import cv2

SRC = sys.argv[1] if len(sys.argv) > 1 else "/home/miftah/mock/sample_test.jpg"
DST = sys.argv[2] if len(sys.argv) > 2 else "/home/miftah/mock/output.jpg"
MIN_AREA_FRAC = 0.001  # drop JPEG speckle / dust

img = cv2.imread(SRC)
if img is None:
    raise SystemExit(f"could not read {SRC}")
h, w = img.shape[:2]
min_area = MIN_AREA_FRAC * h * w

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray = cv2.GaussianBlur(gray, (5, 5), 0)
# ink is dark on a light page -> THRESH_BINARY_INV makes the strokes white
_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
# close small gaps in a hand-drawn / noisy stroke so the outline stays one blob
binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE,
                          cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)))

contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

out = img.copy()
print(f"{SRC}  {w}x{h}  raw contours: {len(contours)}  min_area: {min_area:.0f}")
n = 0
for c in contours:
    if cv2.contourArea(c) < min_area:
        continue
    x, y, bw, bh = cv2.boundingRect(c)
    cx, cy = x + bw // 2, y + bh // 2
    n += 1
    cv2.rectangle(out, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
    cv2.circle(out, (cx, cy), 6, (0, 0, 255), -1)  # BGR red, filled
    print(f"  #{n}: box=(x={x}, y={y}, w={bw}, h={bh})  center=({cx}, {cy})  "
          f"aspect={bw / bh:.2f}")

print(f"detected {n} object(s)")
cv2.imwrite(DST, out)
print(f"wrote {DST}")
