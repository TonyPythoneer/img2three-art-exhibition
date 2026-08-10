#!/usr/bin/env python3
"""Deterministic pixel measurements of the Ultima Weapon reference.

Reuses forge's stdlib PNG/mask primitives (no PIL/numpy). Emits measurements.json:
blade axis angle, leaf width profile, violet core profile + gradient stops, spine,
emitter-rod axes + radiation centre, guard/handle extents, per-region palettes.
Every number downstream (spec transforms, referenceCamera, silhouette gates) traces here.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

SKILL_ROOT = Path("/Users/tonyyang/.claude/skills/img2threejs")
sys.path.insert(0, str(SKILL_ROOT))
from forge.stage1_intake.extract_pbr_evidence import (  # noqa: E402
    build_foreground_mask,
    read_png,
    rgb_to_hex,
    sample_corner_background,
)

HERE = Path(__file__).resolve().parent
REF = HERE.parent / "reference-ultima-weapon.png"


def classify(width, height, pixels, fg):
    """Per-pixel colour class within the foreground mask."""
    cls = ["bg"] * (width * height)
    for i, (r, g, b, a) in enumerate(pixels):
        if not fg[i]:
            continue
        luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if r - max(g, b) > 25 and r > 60:
            cls[i] = "red"
        elif b - r > 25 and b - g > 40 and b > 70:
            cls[i] = "violet"
        elif r - b >= 18 and g - b >= 15 and luma > 45:
            cls[i] = "gold"
        elif luma < 90:
            cls[i] = "dark"
        elif luma > 165:
            cls[i] = "shell"
        else:
            cls[i] = "mid"
    return cls


def rows_of(cls, width, height, name, y0=0, y1=None):
    y1 = height if y1 is None else y1
    out = {}
    for y in range(y0, y1):
        xs = [x for x in range(width) if cls[y * width + x] == name]
        if xs:
            out[y] = xs
    return out


def fit_axis(rows):
    """Least squares x = a + b*y over per-row centroids. Returns a, b, r2."""
    pts = [(y, sum(xs) / len(xs)) for y, xs in rows.items()]
    n = len(pts)
    sy = sum(p[0] for p in pts)
    sx = sum(p[1] for p in pts)
    syy = sum(p[0] * p[0] for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    b = (n * sxy - sy * sx) / (n * syy - sy * sy)
    a = (sx - b * sy) / n
    mean_x = sx / n
    ss_tot = sum((p[1] - mean_x) ** 2 for p in pts)
    ss_res = sum((p[1] - (a + b * p[0])) ** 2 for p in pts)
    r2 = 1.0 - (ss_res / ss_tot if ss_tot else 0.0)
    return a, b, r2


def components(width, height, mask_idx):
    """4-connected components over a set of flat indices."""
    todo = set(mask_idx)
    comps = []
    while todo:
        seed = todo.pop()
        comp = [seed]
        stack = [seed]
        while stack:
            i = stack.pop()
            x, y = i % width, i // width
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < width and 0 <= ny < height:
                    j = ny * width + nx
                    if j in todo:
                        todo.remove(j)
                        comp.append(j)
                        stack.append(j)
        comps.append(comp)
    return comps


def pca(idxs, width):
    pts = [(i % width, i // width) for i in idxs]
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - cx) ** 2 for p in pts) / n
    syy = sum((p[1] - cy) ** 2 for p in pts) / n
    sxy = sum((p[0] - cx) * (p[1] - cy) for p in pts) / n
    theta = 0.5 * math.atan2(2 * sxy, sxx - syy)
    dx, dy = math.cos(theta), math.sin(theta)
    proj = [((p[0] - cx) * dx + (p[1] - cy) * dy) for p in pts]
    perp = [(-(p[0] - cx) * dy + (p[1] - cy) * dx) for p in pts]
    length = max(proj) - min(proj)
    thickness = max(perp) - min(perp)
    return {
        "centroid": [round(cx, 2), round(cy, 2)],
        "dir": [round(dx, 4), round(dy, 4)],
        "angleDegImage": round(math.degrees(math.atan2(dy, dx)), 2),
        "length": round(length, 1),
        "thickness": round(thickness, 1),
        "count": n,
    }


def median_of(pixels, idxs):
    if not idxs:
        return None
    rs = sorted(pixels[i][0] for i in idxs)
    gs = sorted(pixels[i][1] for i in idxs)
    bs = sorted(pixels[i][2] for i in idxs)
    m = len(idxs) // 2
    return rgb_to_hex((rs[m], gs[m], bs[m]))


def main():
    width, height, pixels = read_png(REF)
    fg, _stats, _warnings = build_foreground_mask(width, height, pixels)
    cls = classify(width, height, pixels, fg)

    # ---- blade axis: shell+violet centroids over rows clear of the guard ----
    blade_rows = {}
    for y in range(0, 186):
        xs = [x for x in range(width) if cls[y * width + x] in ("shell", "violet", "mid")]
        if len(xs) >= 3:
            blade_rows[y] = xs
    a, b, r2 = fit_axis(blade_rows)
    tilt_deg = math.degrees(math.atan(b))  # from vertical; +ve = leans right going down
    assert r2 > 0.95, f"axis fit too weak: r2={r2}"
    cos_t = math.cos(math.radians(tilt_deg))

    def axis_x(y):
        return a + b * y

    # ---- leaf width profile (perpendicular distances from axis) ----
    profile = []
    for y in range(0, 206, 5):
        xs = [x for x in range(width) if cls[y * width + x] in ("shell", "violet", "mid")]
        if len(xs) < 3:
            continue
        left = (min(xs) - axis_x(y)) * cos_t
        right = (max(xs) - axis_x(y)) * cos_t
        profile.append({"y": y, "left": round(left, 1), "right": round(right, 1)})

    # ---- violet core ----
    core_rows = rows_of(cls, width, height, "violet")
    core_ys = sorted(core_rows)
    notch_top = None
    for y in core_ys:
        runs = 1
        xs = core_rows[y]
        for i in range(1, len(xs)):
            if xs[i] - xs[i - 1] > 2:
                runs += 1
        if runs >= 2 and y > 140:
            notch_top = y
            break
    core_profile = []
    for y in core_ys[::5]:
        xs = core_rows[y]
        core_profile.append({
            "y": y,
            "left": round((min(xs) - axis_x(y)) * cos_t, 1),
            "right": round((max(xs) - axis_x(y)) * cos_t, 1),
        })
    violet_idx = [i for i in range(width * height) if cls[i] == "violet"]
    # gradient stops along y, 5 bins
    vy0, vy1 = core_ys[0], core_ys[-1]
    stops = []
    for k in range(5):
        lo = vy0 + (vy1 - vy0) * k / 5
        hi = vy0 + (vy1 - vy0) * (k + 1) / 5
        bin_idx = [i for i in violet_idx if lo <= i // width < hi]
        stops.append({"t": round((k + 0.5) / 5, 2), "color": median_of(pixels, bin_idx)})

    # ---- red family: spine vs rods ----
    red_idx = [i for i in range(width * height) if cls[i] == "red"]
    red_comps = [c for c in components(width, height, red_idx) if len(c) >= 12]
    spine_comps, rod_stats = [], []
    for comp in red_comps:
        st = pca(comp, width)
        cx, cy = st["centroid"]
        dist_from_axis = abs((cx - axis_x(cy)) * cos_t)
        if dist_from_axis < 14:
            spine_comps.append((comp, st))
        else:
            # intersection of rod line with blade axis: solve p + s*d on x = a + b*y
            dx, dy = st["dir"]
            denom = dx - b * dy
            if abs(denom) > 1e-6:
                s = (a + b * cy - cx) / denom
                yi = cy + s * dy
            else:
                yi = None
            st["axisIntersectY"] = round(yi, 1) if yi is not None else None
            st["side"] = "left" if cx < axis_x(cy) else "right"
            rod_stats.append(st)

    spine_all = [i for comp, _ in spine_comps for i in comp]
    spine_bbox = None
    if spine_all:
        xs = [i % width for i in spine_all]
        ys = [i // width for i in spine_all]
        spine_bbox = [min(xs), min(ys), max(xs), max(ys)]
    upper = [i for i in spine_all if i // width < (spine_bbox[1] + spine_bbox[3]) / 2]
    lower = [i for i in spine_all if i // width >= (spine_bbox[1] + spine_bbox[3]) / 2]

    # ---- guard + handle ----
    gold_idx = [i for i in range(width * height) if cls[i] == "gold"]
    dark_idx = [i for i in range(width * height) if cls[i] == "dark"]
    dark_comps = [c for c in components(width, height, dark_idx) if len(c) >= 20]
    handle = None
    gunmetal = []
    for comp in dark_comps:
        st = pca(comp, width)
        # handle: elongated, extends to bottom edge
        if max(i // width for i in comp) >= height - 3 and st["length"] > 40:
            st["medianColor"] = median_of(pixels, comp)
            handle = st
        else:
            st["medianColor"] = median_of(pixels, comp)
            gunmetal.append(st)
    gold_bbox = None
    if gold_idx:
        xs = [i % width for i in gold_idx]
        ys = [i // width for i in gold_idx]
        gold_bbox = [min(xs), min(ys), max(xs), max(ys)]

    shell_idx = [i for i in range(width * height) if cls[i] == "shell"]
    result = {
        "image": {"width": width, "height": height},
        "counts": {k: sum(1 for c in cls if c == k) for k in ("shell", "violet", "red", "gold", "dark", "mid")},
        "bladeAxis": {
            "xAtY0": round(a, 2),
            "slopeDxPerDy": round(b, 4),
            "tiltDegFromVertical": round(tilt_deg, 2),
            "fitR2": round(r2, 4),
            "note": "x = xAtY0 + slope*y; positive tilt = blade leans right going down (tip up-left)",
        },
        "leafWidthProfile": profile,
        "core": {
            "topApexY": core_ys[0],
            "bottomY": core_ys[-1],
            "notchTopY": notch_top,
            "profile": core_profile,
            "gradientStopsTopToBottom": stops,
        },
        "spine": {"bbox": spine_bbox, "upperColor": median_of(pixels, upper), "lowerColor": median_of(pixels, lower)},
        "rods": rod_stats,
        "gunmetal": gunmetal,
        "handle": handle,
        "goldBbox": gold_bbox,
        "palette": {
            "shell": median_of(pixels, shell_idx),
            "violet": median_of(pixels, violet_idx),
            "gold": median_of(pixels, gold_idx),
        },
    }
    out = HERE / "measurements.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
