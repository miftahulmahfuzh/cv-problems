import json
import cv2
import numpy as np

img = cv2.imread("input/photo.jpg")
H, W = img.shape[:2]

# 1. Segment paper: low saturation + bright (desk is saturated brown)
hsv = cv2.cvtColor(cv2.GaussianBlur(img, (7, 7), 0), cv2.COLOR_BGR2HSV)
mask = ((hsv[..., 1] < 60) & (hsv[..., 2] > 150)).astype(np.uint8) * 255
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((25, 25), np.uint8))

# 2. Largest blob -> 4 corners
cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
c = max(cnts, key=cv2.contourArea)
hull = cv2.convexHull(c)
quad = None
for eps in np.linspace(0.005, 0.05, 40):
    a = cv2.approxPolyDP(hull, eps * cv2.arcLength(hull, True), True)
    if len(a) == 4:
        quad = a.reshape(4, 2).astype(np.float32)
        break
assert quad is not None, "no 4-corner approximation"

# order TL, TR, BR, BL
s, d = quad.sum(1), np.diff(quad, axis=1).ravel()
src = np.array([quad[s.argmin()], quad[d.argmin()], quad[s.argmax()], quad[d.argmax()]], np.float32)

# 3. Output size from edge lengths
wd = lambda p, q: float(np.linalg.norm(p - q))
w = int(round((wd(src[0], src[1]) + wd(src[3], src[2])) / 2))
h = int(round((wd(src[0], src[3]) + wd(src[1], src[2])) / 2))
dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], np.float32)

# 4. Warp
M = cv2.getPerspectiveTransform(src, dst)
flat = cv2.warpPerspective(img, M, (w, h), flags=cv2.INTER_CUBIC)
cv2.imwrite("output/flat.png", flat)

dbg = img.copy()
cv2.polylines(dbg, [src.astype(int)], True, (0, 255, 0), 4)
cv2.imwrite("output/debug_corners.png", dbg)

json.dump({
    "method": "HSV threshold (low saturation, high value) -> morphology -> largest contour -> convex hull -> approxPolyDP to 4 corners -> getPerspectiveTransform + warpPerspective",
    "input_size": [W, H],
    "corners_tl_tr_br_bl": src.round(1).tolist(),
    "output_size": [w, h],
    "output_aspect_w_over_h": round(w / h, 3),
    "a4_aspect": 0.707,
    "interpolation": "cubic",
    "rotation_applied": "none beyond what the homography implies",
}, open("output/notes.json", "w"), indent=2)
print(src, w, h, w / h)
