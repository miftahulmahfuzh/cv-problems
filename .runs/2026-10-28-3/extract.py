import json, re, sys
import cv2
import numpy as np

sys.path.insert(0, "/home/miftah/cv-problems/reference/snippets")
from ocr_bridge import ocr

SRC = "input/receipt.png"
img = cv2.imread(SRC)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
H, W = gray.shape


# ---------- OCR -> rows ----------
toks = ocr(SRC)
for t in toks:
    t["text"] = t["text"].replace("，", ",").replace("（", "(").replace("）", ")")

# group tokens whose vertical centres are close into one printed row
toks.sort(key=lambda t: (t["bbox"][1] + t["bbox"][3]) / 2)
rows = []
for t in toks:
    cy = (t["bbox"][1] + t["bbox"][3]) / 2
    if rows and abs(cy - rows[-1]["cy"]) < 10:
        rows[-1]["toks"].append(t)
    else:
        rows.append({"cy": cy, "toks": [t]})
for r in rows:
    r["toks"].sort(key=lambda t: t["bbox"][0])
    bb = [t["bbox"] for t in r["toks"]]
    r["bbox"] = [min(b[0] for b in bb), min(b[1] for b in bb), max(b[2] for b in bb), max(b[3] for b in bb)]


# ---------- put back the spaces the OCR drops (monospace font) ----------
ink = cv2.threshold(cv2.GaussianBlur(gray, (3, 3), 0), 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1] > 0


def respace(tok):
    """Rebuild spaces inside one OCR token from blank character cells."""
    text = tok["text"]
    chars = text.replace(" ", "")
    x0, y0, x1, y1 = tok["bbox"]
    w = x1 - x0
    # only free-text tokens; numbers, amounts and "Key:value" tokens are parsed as printed
    if not re.fullmatch(r"[A-Za-z0-9.,]+", chars) or sum(c.isalpha() for c in chars) < 4:
        return text
    prof = ink[y0:y1, x0:x1].sum(axis=0)
    best = None
    for p in np.arange(10, 30, 0.1):
        n = int(round(w / p))
        if n < len(chars) or n > len(chars) + 6:
            continue
        cells = [prof[int(i * w / n): max(int((i + 1) * w / n), int(i * w / n) + 1)].sum() for i in range(n)]
        mid = [prof[int((i + .3) * w / n): max(int((i + .7) * w / n), int((i + .3) * w / n) + 1)].sum() for i in range(n)]
        filled = [m > 1 for m in mid]
        if sum(filled) == len(chars):
            score = abs(w / n - w / len(chars)) * 0  # all matches equal; keep first
            best = filled
            break
    if best is None:
        return text
    it = iter(chars)
    return "".join(next(it) if f else " " for f in best).strip()


def row_text(r):
    return " ".join(respace(t) for t in r["toks"])


def row_raw(r):
    return " ".join(t["text"] for t in r["toks"])


def num(s):
    s = s.replace(" ", "").replace(",", "").replace(".", "")
    neg = s.startswith("-")
    return -int(s.lstrip("-")) if neg else int(s)


for r in rows:
    r["text"] = row_text(r)
    r["raw"] = row_raw(r)

for r in rows:
    print(r["bbox"], repr(r["text"]))

# ---------- parse ----------
QTY = re.compile(r"^(\d+)\s*x\s*([\d,]+)$")
AMT = re.compile(r"^-?[\d,]+$")
DASH = re.compile(r"^-{5,}$")


def split_amount(r):
    """(left text, amount) for a row ending with a right-aligned amount."""
    last = r["toks"][-1]
    if last["bbox"][0] > W * 0.7 and AMT.match(last["text"].replace(" ", "")):
        left = " ".join(t["text"] for t in r["toks"][:-1])
        if left.strip().isalpha() or re.search(r"[A-Za-z]{4,}", left):
            left = " ".join(respace(t) for t in r["toks"][:-1])
        return left.strip(), num(last["text"]), last["bbox"]
    return None


store, date, time_, cashier, receipt_no, address = None, None, None, None, None, None
items, totals = [], {}
header = []
for i, r in enumerate(rows):
    tx = r["raw"]
    if "Terima" in tx:
        continue
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})\s*(\d{2}:\d{2})", tx)
    if m:
        d, mo, y, time_ = m.groups()
        date = f"{y}-{mo}-{d}"
        c = re.search(r"Kasir:\s*(\S.*)$", tx)
        cashier = c.group(1).strip() if c else None
        continue
    m = re.match(r"No:\s*(\S+)", tx)
    if m:
        receipt_no = m.group(1)
        continue
    if date is None:
        header.append(r["text"])

store, address = header[0], " ".join(header[1:])

# line items: a name row followed by an "N x price ... total" row
i = 0
while i < len(rows) - 1:
    name_row, qty_row = rows[i], rows[i + 1]
    sa = split_amount(qty_row)
    if sa and QTY.match(sa[0].replace(" ", "")) and not split_amount(name_row):
        q = QTY.match(sa[0].replace(" ", ""))
        qty, unit, total = int(q.group(1)), num(q.group(2)), sa[1]
        box = [min(name_row["bbox"][0], qty_row["bbox"][0]), name_row["bbox"][1],
               max(name_row["bbox"][2], qty_row["bbox"][2]), qty_row["bbox"][3]]
        items.append({"name": name_row["text"], "quantity": qty, "unit_price": unit,
                      "line_total": total, "_box": box})
        i += 2
    else:
        i += 1

# totals: label + amount rows below the last item
last_y = items[-1]["_box"][3]
LABELS = {"subtotal": "subtotal", "diskon": "member_discount", "total": "total",
          "ppn": "ppn", "tunai": "cash", "kembali": "change"}
for r in rows:
    if r["bbox"][1] <= last_y:
        continue
    sa = split_amount(r)
    if not sa:
        continue
    label, amt, _ = sa
    key = next((v for k, v in LABELS.items() if label.lower().startswith(k)), None)
    if key == "ppn":
        rate = re.search(r"PPN\s*(\d+)\s*%", label)
        totals["ppn"] = {"rate_percent": int(rate.group(1)) if rate else None,
                         "included_in_total": "incl" in label.lower(), "amount": amt}
    elif key:
        totals[key] = amt

# ---------- consistency checks (reported, not forced) ----------
checks = {
    "sum_of_line_totals_equals_subtotal": sum(i["line_total"] for i in items) == totals["subtotal"],
    "each_line_total_equals_qty_x_unit": all(i["quantity"] * i["unit_price"] == i["line_total"] for i in items),
    "subtotal_plus_discount_equals_total": totals["subtotal"] + totals["member_discount"] == totals["total"],
    "cash_minus_total_equals_change": totals["cash"] - totals["total"] == totals["change"],
    "ppn_matches_total_x_11_over_111": round(totals["total"] * 11 / 111) == totals["ppn"]["amount"],
}

out = {
    "store": {"name": store, "address": address},
    "date": date,
    "time": time_,
    "cashier": cashier,
    "receipt_no": receipt_no,
    "items": [{k: v for k, v in it.items() if k != "_box"} for it in items],
    "totals": totals,
    "checks": checks,
}
with open("output/receipt.json", "w") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print(json.dumps(out, indent=2, ensure_ascii=False))

# ---------- overlay ----------
ov = img.copy()
for n, it in enumerate(items, 1):
    x0, y0, x1, y1 = it["_box"]
    cv2.rectangle(ov, (x0 - 6, y0 - 5), (x1 + 6, y1 + 5), (0, 0, 220), 2)
    cv2.putText(ov, str(n), (x0 - 24, y0 + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 220), 1, cv2.LINE_AA)
cv2.imwrite("output/overlay.png", ov)
