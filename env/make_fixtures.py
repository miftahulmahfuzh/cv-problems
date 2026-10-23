#!/usr/bin/env python3
"""Generate deterministic sample images into ./images for a coding test.

No network. Run once:  python make_fixtures.py
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(7)


def _truetype(size):
    """DejaVuSans ships with matplotlib, so this works with no system fonts."""
    path = os.path.join(os.path.dirname(matplotlib.__file__),
                        "mpl-data", "fonts", "ttf", "DejaVuSans.ttf")
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def candlestick():
    """A realistic trading-app chart screenshot: OHLC + MA20 + volume + markers."""
    n = 120
    close = 100 + np.cumsum(RNG.normal(0.15, 1.8, n))
    open_ = close + RNG.normal(0, 0.8, n)
    high = np.maximum(open_, close) + np.abs(RNG.normal(0, 0.9, n))
    low = np.minimum(open_, close) - np.abs(RNG.normal(0, 0.9, n))
    vol = np.abs(RNG.normal(1.0, 0.4, n)) * 1e6
    vol[-15:] *= 2.1  # a visible recent volume expansion

    ma20 = np.convolve(close, np.ones(20) / 20, mode="valid")

    fig, (ax, axv) = plt.subplots(
        2, 1, figsize=(12, 8), dpi=100, sharex=True,
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05},
    )
    fig.patch.set_facecolor("#ffffff")

    for i in range(n):
        up = close[i] >= open_[i]
        color = "#26a69a" if up else "#ef5350"
        ax.vlines(i, low[i], high[i], color=color, linewidth=0.9)
        ax.add_patch(Rectangle(
            (i - 0.3, min(open_[i], close[i])), 0.6,
            max(abs(close[i] - open_[i]), 0.05),
            facecolor=color, edgecolor=color,
        ))

    ax.plot(range(19, n), ma20, color="#2962ff", linewidth=1.4, label="MA20")

    # a shaded support band + a user-drawn resistance line
    band_lo, band_hi = float(np.percentile(close, 22)), float(np.percentile(close, 32))
    ax.axhspan(band_lo, band_hi, color="#ffb74d", alpha=0.25)
    ax.text(1, band_hi, f"  support {band_lo:.0f}-{band_hi:.0f}",
            fontsize=8, color="#e65100", va="bottom")
    res = float(close.max() * 0.985)
    ax.axhline(res, color="#7b1fa2", linestyle="--", linewidth=1.2)
    ax.text(n - 2, res, f"{res:.0f} ", fontsize=8, color="#7b1fa2",
            va="bottom", ha="right")

    # buy / sell markers clustered in one price range
    buys = [14, 21, 29, 36]
    sells = [94, 101]
    ax.scatter(buys, [low[i] - 1.6 for i in buys], marker="^", s=90,
               color="#1b5e20", zorder=5, label="Buy")
    ax.scatter(sells, [high[i] + 1.6 for i in sells], marker="v", s=90,
               color="#b71c1c", zorder=5, label="Sell")

    hi_i, lo_i = int(close.argmax()), int(close.argmin())
    ax.annotate(f"H {high[hi_i]:.0f}", (hi_i, high[hi_i]),
                textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    ax.annotate(f"L {low[lo_i]:.0f}", (lo_i, low[lo_i]),
                textcoords="offset points", xytext=(0, -14), ha="center", fontsize=8)

    pad = (high.max() - low.min()) * 0.06
    ax.set_ylim(low.min() - pad, high.max() + pad)

    ax.set_title("BBCA  ·  PT Bank Central Asia Tbk  ·  1D  ·  6M",
                 loc="left", fontsize=12, fontweight="bold")
    ax.set_ylabel("Price (IDR)")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax.grid(alpha=0.2)

    axv.bar(range(n), vol, color=["#26a69a" if close[i] >= open_[i] else "#ef5350"
                                 for i in range(n)], width=0.6)
    axv.set_ylabel("Volume")
    axv.grid(alpha=0.2)

    months = ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]
    ticks = np.linspace(0, n - 1, len(months)).astype(int)
    axv.set_xticks(ticks)
    axv.set_xticklabels(months)

    path = os.path.join(OUT, "candlestick_chart.png")
    fig.savefig(path, bbox_inches="tight", facecolor="#ffffff")
    plt.close(fig)
    # matplotlib writes RGBA; flatten to RGB so a forgotten .convert("RGB") in a
    # timed test does not produce a 4-channel tensor and a baffling conv error.
    with Image.open(path) as im:
        im.convert("RGB").save(path)
    return path


def shapes():
    """Classic CV fixture: distinct colored shapes for contours/threshold/detection."""
    img = Image.new("RGB", (800, 600), "#f7f7f7")
    d = ImageDraw.Draw(img)
    d.ellipse([60, 60, 220, 220], fill="#e53935", outline="#000000", width=3)
    d.rectangle([300, 80, 480, 230], fill="#1e88e5", outline="#000000", width=3)
    d.polygon([(600, 220), (680, 70), (760, 220)], fill="#43a047", outline="#000000")
    d.ellipse([120, 330, 240, 450], fill="#fdd835", outline="#000000", width=3)
    d.rectangle([340, 330, 430, 540], fill="#8e24aa", outline="#000000", width=3)
    d.polygon([(560, 540), (640, 340), (740, 540), (650, 500)],
              fill="#00897b", outline="#000000")
    arr = np.asarray(img).astype(np.int16)
    arr += RNG.integers(-9, 10, arr.shape, dtype=np.int16)  # mild sensor noise
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    path = os.path.join(OUT, "shapes.png")
    out.save(path)
    return path


def document():
    """A text-bearing image: OCR / VLM text-extraction / table-parsing fixture."""
    W, H = 900, 1150
    img = Image.new("RGB", (W, H), "#ffffff")
    d = ImageDraw.Draw(img)
    f_title, f_head, f_body, f_small = (_truetype(30), _truetype(17),
                                        _truetype(15), _truetype(12))

    d.text((50, 45), "TRADE CONFIRMATION", font=f_title, fill="#111111")
    d.line([50, 90, W - 50, 90], fill="#111111", width=3)

    meta = [("Account", "TT-9920-4471"), ("Statement date", "21 October 2026"),
            ("Settlement", "T+2"), ("Currency", "IDR")]
    y = 110
    for k, v in meta:
        d.text((50, y), f"{k}", font=f_body, fill="#555555")
        d.text((250, y), f"{v}", font=f_body, fill="#111111")
        y += 26

    y += 24
    cols = [("TICKER", 50), ("SIDE", 180), ("QTY (lot)", 290), ("PRICE", 450),
            ("VALUE", 600), ("FEE", 780)]
    d.rectangle([50, y - 6, W - 50, y + 24], fill="#eeeeee")
    for name, x in cols:
        d.text((x, y), name, font=f_head, fill="#111111")
    y += 36

    rows = [
        ("BBCA", "BUY", "20", "9,475", "18,950,000", "28,425"),
        ("BBRI", "BUY", "50", "4,310", "21,550,000", "32,325"),
        ("TLKM", "SELL", "35", "2,870", "10,045,000", "25,112"),
        ("ASII", "BUY", "15", "5,125", "7,687,500", "11,531"),
        ("GOTO", "SELL", "400", "68", "2,720,000", "6,800"),
    ]
    for r in rows:
        for (_, x), val in zip(cols, r):
            d.text((x, y), val, font=f_body, fill="#111111")
        d.line([50, y + 24, W - 50, y + 24], fill="#dddddd", width=1)
        y += 34

    y += 16
    d.text((450, y), "Gross value", font=f_body, fill="#555555")
    d.text((600, y), "60,952,500", font=f_body, fill="#111111")
    y += 26
    d.text((450, y), "Total fees", font=f_body, fill="#555555")
    d.text((600, y), "104,193", font=f_body, fill="#111111")
    y += 26
    d.text((450, y), "NET DEBIT", font=f_head, fill="#111111")
    d.text((600, y), "61,056,693", font=f_head, fill="#b71c1c")

    d.text((50, H - 70),
           "Not an offer or recommendation. Figures are illustrative test data.",
           font=f_small, fill="#777777")

    path = os.path.join(OUT, "document_table.png")
    img.save(path)
    return path


def photo():
    """A real lossy JPEG, so file-format handling is exercised too."""
    W, H = 1024, 768
    yy = np.linspace(0, 1, H)[:, None]
    sky = np.zeros((H, W, 3), dtype=np.float64)
    sky[..., 0] = 60 + 150 * (1 - yy)
    sky[..., 1] = 110 + 120 * (1 - yy)
    sky[..., 2] = 190 + 60 * (1 - yy)
    xx = np.linspace(0, 1, W)[None, :]
    ridge = 0.62 + 0.10 * np.sin(xx * 7.1) + 0.05 * np.sin(xx * 19.3)
    mask = yy > ridge
    sky[mask] = sky[mask] * 0.22 + np.array([34, 58, 42]) * 0.78
    sun = np.exp(-(((xx - 0.72) ** 2) / 0.004 + ((yy - 0.20) ** 2) / 0.004))
    sky += (sun * 90)[..., None]
    sky += RNG.normal(0, 3.0, sky.shape)
    img = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8))
    path = os.path.join(OUT, "photo_landscape.jpg")
    img.save(path, quality=85)
    return path


if __name__ == "__main__":
    for fn in (candlestick, shapes, document, photo):
        p = fn()
        with Image.open(p) as im:
            size = im.size
        print(f"{os.path.getsize(p):>9,} bytes  {size[0]}x{size[1]}  {p}")
