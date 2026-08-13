#!/usr/bin/env python3
"""Measure face skin width column-by-column using HSV hue thresholds.

Background: spec/measure_head.py dropped skin because RGB-distance cannot
separate blown-out hair highlights from lit vinyl skin -- they land in the
same RGB neighbourhood. But hue (HSV) separates them cleanly: skin is
orange-red (hue 5--35 degrees), hair is yellow (hue 40--70 degrees).
Specular highlights shift only value, not hue.

Run from repo root:
    python3 artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/measure_skin.py

Coordinate convention (same as measure_head.py):
  - Y normalized so 1.000 = top of the image, 0.000 = bottom.
  - X measured from image centre, divided by image height (not width).
"""
import colorsys
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
ASSETS = ROOT / "src/assets/exhibits/ff7-cloud-strife-polygon-figure"
OUT = pathlib.Path(__file__).with_name("skin-measurements.json")

SHOULDER_Y = 0.673  # same as measure_head.py; head/neck region only

# --- HSV thresholds (hue in degrees 0-360; s, v in 0-1) ---
BG_V_MIN = 0.93
BG_S_MAX = 0.10
HAIR_H_LO, HAIR_H_HI = 40, 70
HAIR_S_MIN = 0.25
SKIN_H_LO, SKIN_H_HI = 5, 35   # [5, 35)
SKIN_S_MIN = 0.08
SKIN_V_MIN = 0.45
HIST_BIN_DEG = 5


def load_rgb(path):
    """webp -> (w, h, bytes) via ImageMagick, so there is no PIL dependency."""
    txt = subprocess.run(
        ["magick", str(path), "-depth", "8", "-type", "TrueColor", "ppm:-"],
        check=True, capture_output=True,
    ).stdout
    fields, idx = [], 0
    while len(fields) < 4:  # P6, width, height, maxval
        while txt[idx:idx + 1].isspace():
            idx += 1
        if txt[idx:idx + 1] == b"#":
            idx = txt.index(b"\n", idx)
            continue
        start = idx
        while not txt[idx:idx + 1].isspace():
            idx += 1
        fields.append(txt[start:idx])
    idx += 1
    w, h = int(fields[1]), int(fields[2])
    return w, h, txt[idx:idx + w * h * 3]


def to_hsv(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return h * 360.0, s, v


def find_runs(mask):
    """Return list of (start, end) inclusive pixel-index ranges for True runs."""
    runs = []
    in_run = False
    start = 0
    for i, v in enumerate(mask):
        if v and not in_run:
            in_run = True
            start = i
        elif not v and in_run:
            in_run = False
            runs.append((start, i - 1))
    if in_run:
        runs.append((start, len(mask) - 1))
    return runs


def longest_run(runs):
    """Return (x0, x1, width_px) of the longest run, or (None, None, 0)."""
    if not runs:
        return None, None, 0
    lo, hi = max(runs, key=lambda r: r[1] - r[0])
    return lo, hi, hi - lo + 1


def scan_image(path):
    w, h, body = load_rgb(path)
    n_bins = int(360 / HIST_BIN_DEG)
    hue_hist = [0] * n_bins
    head_limit = int(h * (1.0 - SHOULDER_Y))

    skin_rows = []
    for y in range(head_limit):
        base = y * w * 3
        mask = bytearray(w)
        for x in range(w):
            o = base + x * 3
            r, g, b = body[o], body[o + 1], body[o + 2]
            hueDeg, s, v = to_hsv(r, g, b)
            if v > BG_V_MIN and s < BG_S_MAX:
                continue  # background
            # non-background -> hue histogram
            bin_idx = int(hueDeg // HIST_BIN_DEG) % n_bins
            hue_hist[bin_idx] += 1
            if SKIN_H_LO <= hueDeg < SKIN_H_HI and s >= SKIN_S_MIN and v >= SKIN_V_MIN:
                mask[x] = 1
        skin_rows.append(mask)

    return w, h, skin_rows, hue_hist


def build_profile(skin_rows, w, h, step_frac=0.005):
    step = max(1, int(h * step_frac))
    profile = []
    for y in range(0, len(skin_rows), step):
        mask = skin_rows[y]
        if not any(mask):
            continue
        runs = find_runs(mask)
        x0, x1, width = longest_run(runs)
        yNorm = round((h - y) / h, 4)
        x0Norm = round((x0 - w / 2) / h, 4)
        x1Norm = round((x1 - w / 2) / h, 4)
        widthNorm = round(width / h, 4)
        profile.append({
            "yNorm": yNorm,
            "x0Norm": x0Norm,
            "x1Norm": x1Norm,
            "widthNorm": widthNorm,
            "runs": len(runs),
        })
    return profile


def find_chin(skin_rows, h):
    """Scan skin rows from bottom (near shoulders) to top.

    The neck is narrow and roughly constant; the face/jaw is wider.
    Neck width = median of bottom-3 row widths. Chin = first row (from
    bottom) where width > 1.5x neck width. Returns yNorm or None.
    """
    skin_ys = [y for y in range(len(skin_rows)) if any(skin_rows[y])]
    if len(skin_ys) < 5:
        return None

    skin_ys.sort(reverse=True)  # bottom to top

    widths = []
    for y in skin_ys:
        runs = find_runs(skin_rows[y])
        _, _, wd = longest_run(runs)
        widths.append((y, wd))

    neck_widths = [wd for _, wd in widths[:3]]
    neck_width = sorted(neck_widths)[len(neck_widths) // 2]
    if neck_width == 0:
        return None

    for y, wd in widths:
        if wd > neck_width * 1.5:
            return round((h - y) / h, 4)

    return None


def summarize(path, step_frac=0.005):
    w, h, skin_rows, hue_hist = scan_image(path)

    all_skin_ys = [y for y in range(len(skin_rows)) if any(skin_rows[y])]
    if all_skin_ys:
        top_skin_y = min(all_skin_ys)
        topVisibleYNorm = round((h - top_skin_y) / h, 4)
    else:
        topVisibleYNorm = None

    chinYNorm = find_chin(skin_rows, h)

    profile = build_profile(skin_rows, w, h, step_frac)

    if chinYNorm is not None:
        face_profile = [p for p in profile if p["yNorm"] > chinYNorm]
    else:
        face_profile = profile

    if face_profile:
        widest = max(face_profile, key=lambda p: p["widthNorm"])
        maxWidthNorm = widest["widthNorm"]
        maxWidthAtYNorm = widest["yNorm"]
    else:
        maxWidthNorm = None
        maxWidthAtYNorm = None

    skin_pixels = sum(sum(row) for row in skin_rows)

    n_bins = int(360 / HIST_BIN_DEG)
    histogram = [
        {"hueDegBin": i * HIST_BIN_DEG, "pixels": hue_hist[i]}
        for i in range(n_bins)
    ]

    return {
        "image": path.name,
        "size": [w, h],
        "skinPixels": skin_pixels,
        "profileStepY": round(step_frac, 4),
        "profile": profile,
        "maxWidthNorm": maxWidthNorm,
        "maxWidthAtYNorm": maxWidthAtYNorm,
        "chinYNorm": chinYNorm,
        "topVisibleYNorm": topVisibleYNorm,
        "histogram": histogram,
    }


def main():
    method = (
        "HSV hue-based classification via colorsys.rgb_to_hsv (hue x 360 = degrees;\n"
        "s, v in 0-1). Thresholds:\n"
        "  Background: v > 0.93 and s < 0.10.\n"
        "  Hair:      40 <= hueDeg <= 70 and s >= 0.25.\n"
        "  Skin:      5 <= hueDeg < 35 and s >= 0.08 and v >= 0.45.\n"
        "  Other:     everything else non-background.\n"
        "\n"
        "Why hue instead of RGB: measure_head.py dropped skin because RGB-distance\n"
        "cannot separate blown-out hair highlights from lit vinyl skin (same RGB\n"
        "neighbourhood). HSV hue separates them -- skin is orange-red (5-35 deg),\n"
        "hair is yellow (40-70 deg). Specular highlights shift only value (brightness),\n"
        "not hue, so classification stays stable under lighting.\n"
        "\n"
        "Chin detection: scan skin rows from bottom (near shoulders) upward.\n"
        "Neck width = median of bottom-3 row widths (longest skin run per row).\n"
        "Chin = first row where width exceeds 1.5x neck width. Face measurements\n"
        "(maxWidthNorm etc.) use only rows above chinYNorm; neck rows are excluded.\n"
        "\n"
        "Histogram: all non-background pixels binned by hueDeg, 5-degree bins,\n"
        "72 bins covering 0-355 degrees."
    )

    result = {
        "generatedBy": "spec/measure_skin.py",
        "method": method,
        "histogram": {},
        "views": {},
    }
    for name in ("front", "more-angle"):
        view = summarize(ASSETS / f"{name}.webp")
        result["histogram"][name] = view.pop("histogram")
        result["views"][name] = view

    OUT.write_text(json.dumps(result, indent=2) + "\n")
    for name, v in result["views"].items():
        print(
            f"{name:12s} skinPixels {v['skinPixels']}"
            f"  maxW {v['maxWidthNorm']} @ {v['maxWidthAtYNorm']}"
            f"  chin {v['chinYNorm']}"
            f"  top {v['topVisibleYNorm']}"
            f"  rows {len(v['profile'])}"
        )
    print("->", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
