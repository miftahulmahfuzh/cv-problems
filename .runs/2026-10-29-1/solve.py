import json
import cv2
import numpy as np

SRC = "input/plan.png"
MIN_RUN = 60          # px; shortest straight run that counts as a wall
SCALE_BAR_M = 5.0     # the bar at bottom-left is labelled 0 .. 5 m

img = cv2.imread(SRC)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ink = (gray < 128).astype(np.uint8)          # hairline door swings are grey, dropped here

# ---- 1. thick-stroke mask: walls are ~6-7 px, text / boxes / receptacles are 1-3 px
thick = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((4, 4), np.uint8))

# ---- 2. connected components: walls form one network, scale bar / legend / title
#         block are separate islands
n, lab, stats, _ = cv2.connectedComponentsWithStats(thick, connectivity=8)
order = np.argsort(-stats[1:, cv2.CC_STAT_AREA]) + 1
walls_cc = order[0]
print("components by area:", [(int(i), stats[i, :4].tolist(), int(stats[i, 4])) for i in order[:6]])
net = (lab == walls_cc).astype(np.uint8)

# scale bar: the biggest remaining component that is wide and flat
#             (the thick-stroke opening already dropped it, so look in the plain ink mask)
bar = None
n2, _, st2, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
for i in range(1, n2):
    x, y, w, h, a = st2[i]
    if w > 200 and h < 40 and y > img.shape[0] * 0.7 and x < img.shape[1] * 0.5:
        bar = (x, y, w, h)
        break
px_per_m = None
if bar:
    # bar ticks stick up; its length is the width of the component
    px_per_m = bar[2] / SCALE_BAR_M
    print("scale bar", bar, "px_per_m", px_per_m)

# ---- 3. split the network into horizontal and vertical straight runs
H = cv2.morphologyEx(net, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (MIN_RUN, 1)))
V = cv2.morphologyEx(net, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, MIN_RUN)))


def runs(mask, orient):
    # external contours only: a stroke yields an outer and an inner contour otherwise
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in cs:
        x, y, w, h = cv2.boundingRect(c)
        out.append((orient, x, y, w, h, c))
    return out


raw = runs(H, "h") + runs(V, "v")

walls = []
for orient, x, y, w, h, c in raw:
    comp = np.zeros_like(net)
    cv2.drawContours(comp, [c], -1, 1, -1)
    if orient == "h":
        thickness_profile = comp[y:y + h, x:x + w].sum(axis=0)    # per column
        t = int(np.median(thickness_profile))                       # window bulge ignored
        rows = np.where(comp[y:y + h, x:x + w].sum(axis=1) >= w * 0.5)[0]
        cy = y + (rows.min() + rows.max()) / 2.0 if len(rows) else y + h / 2.0
        a0, a1, c0 = x, x + w, cy
        bulge = int(h - t)
    else:
        thickness_profile = comp[y:y + h, x:x + w].sum(axis=1)
        t = int(np.median(thickness_profile))
        cols = np.where(comp[y:y + h, x:x + w].sum(axis=0) >= h * 0.5)[0]
        cx = x + (cols.min() + cols.max()) / 2.0 if len(cols) else x + w / 2.0
        a0, a1, c0 = y, y + h, cx
        bulge = int(w - t)
    walls.append(dict(orient=orient, a0=a0, a1=a1, c=c0, t=t, bulge=bulge))

# ---- 4. centre-line length: an end that lands on a perpendicular wall is trimmed by
#         half a thickness so the corner is not counted by both walls
def touches(orient, a, c, t, side):
    perp = V if orient == "h" else H
    r = max(t, 4)
    if orient == "h":
        x0 = a - r if side == 0 else a
        y0 = int(c - t)
        reg = perp[y0:int(c + t) + 1, max(x0, 0):max(x0, 0) + r]
        # perpendicular wall must continue past the band on at least one side
    else:
        y0 = a - r if side == 0 else a
        x0 = int(c - t)
        reg = perp[max(y0, 0):max(y0, 0) + r, x0:int(c + t) + 1]
    return reg.size > 0 and reg.sum() > 0.25 * reg.size


for w in walls:
    t = w["t"]
    lo = w["a0"] + (t / 2.0 if touches(w["orient"], w["a0"], w["c"], t, 0) else 0)
    hi = w["a1"] - (t / 2.0 if touches(w["orient"], w["a1"], w["c"], t, 1) else 0)
    w["lo"], w["hi"] = lo, hi
    w["len"] = hi - lo

walls.sort(key=lambda w: (w["orient"] != "h", w["c"], w["lo"]))
for i, w in enumerate(walls, 1):
    w["id"] = f"W{i:02d}"
    if w["orient"] == "h":
        w["p0"], w["p1"] = (w["lo"], w["c"]), (w["hi"], w["c"])
    else:
        w["p0"], w["p1"] = (w["c"], w["lo"]), (w["c"], w["hi"])

# door gaps = free space between collinear runs
gaps = []
for a in walls:
    for b in walls:
        if a is b or a["orient"] != b["orient"] or abs(a["c"] - b["c"]) > 4:
            continue
        if a["hi"] <= b["lo"] and b["lo"] - a["hi"] < 200:
            gaps.append(dict(between=[a["id"], b["id"]], orient=a["orient"],
                             at=round(float(a["c"]), 1), from_=round(float(a["hi"]), 1),
                             to=round(float(b["lo"]), 1), width_px=round(float(b["lo"] - a["hi"]), 1)))

# ---- 5. outputs
COLORS = [(230, 25, 75), (60, 180, 75), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 240, 240),
          (240, 50, 230), (210, 245, 60), (0, 128, 128), (170, 110, 40), (128, 0, 0), (0, 0, 128)]
over = (img * 0.35 + 255 * 0.65).astype(np.uint8)          # fade the plan so colours read
for i, w in enumerate(walls):
    col = COLORS[i % len(COLORS)][::-1]                      # RGB -> BGR
    t = w["t"]
    (x0, y0), (x1, y1) = w["p0"], w["p1"]
    cv2.line(over, (int(round(x0)), int(round(y0))), (int(round(x1)), int(round(y1))), col, t + 2, cv2.LINE_AA)
    mx, my = int((x0 + x1) / 2), int((y0 + y1) / 2)
    off = (0, -18) if w["orient"] == "h" else (18, 0)
    cv2.putText(over, w["id"], (mx + off[0] - 14, my + off[1] + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.65, col, 2, cv2.LINE_AA)
cv2.imwrite("output/overlay.png", over)

total_px = sum(w["len"] for w in walls)
doc = dict(
    image=SRC, image_size_px=[img.shape[1], img.shape[0]],
    wall_count=len(walls),
    total_length_px=round(float(total_px), 1),
    scale_px_per_m=round(px_per_m, 2) if px_per_m else None,
    total_length_m=round(float(total_px / px_per_m), 2) if px_per_m else None,
    method="thick-stroke mask -> largest connected network -> horizontal/vertical straight runs "
           "(external contours); centre-line length; door gaps excluded; window thickening ignored",
    excluded=["scale bar (bottom-left)", "title/scale box (bottom-right)", "legend box (top-right)",
              "text, receptacles, hairline door swings"],
    walls=[dict(id=w["id"], orientation="horizontal" if w["orient"] == "h" else "vertical",
                p0=[round(float(w["p0"][0]), 1), round(float(w["p0"][1]), 1)],
                p1=[round(float(w["p1"][0]), 1), round(float(w["p1"][1]), 1)],
                length_px=round(float(w["len"]), 1),
                length_m=round(float(w["len"] / px_per_m), 2) if px_per_m else None,
                thickness_px=w["t"], thickness_bulge_ignored_px=w["bulge"]) for w in walls],
    door_gaps=gaps,
)
json.dump(doc, open("output/walls.json", "w"), indent=2)

print(f"{len(walls)} walls, total {total_px:.1f} px" + (f" = {total_px / px_per_m:.2f} m" if px_per_m else ""))
for w in doc["walls"]:
    print(w)
print("gaps:", *gaps, sep="\n  ")
