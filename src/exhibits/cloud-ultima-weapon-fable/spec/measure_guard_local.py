#!/usr/bin/env python3
"""Second measurement pass: guard-cluster geometry in WEAPON-LOCAL coordinates.

The blockout revealed a systematic authoring error: guard part positions were eyeballed
in image space without applying the 17.67° axis rotation. This script maps every colour
class component into local coords (origin = guard/handle junction, +Y tipward along the
measured axis) and re-measures the rod fan with a 1px-eroded mask so touching left rods
separate. Output: spec/guard-local-measurements.json — the authority for the refine.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, "/Users/tonyyang/.claude/skills/img2threejs")
from forge.stage1_intake.extract_pbr_evidence import build_foreground_mask, read_png  # noqa: E402

HERE = Path(__file__).resolve().parent
REF = HERE.parent / "reference-ultima-weapon.png"

M = json.load(open(HERE / "measurements.json"))
AX_A = M["bladeAxis"]["xAtY0"]
AX_B = M["bladeAxis"]["slopeDxPerDy"]
TILT = math.radians(M["bladeAxis"]["tiltDegFromVertical"])
COS_T, SIN_T = math.cos(TILT), math.sin(TILT)
ORIGIN = (AX_A + AX_B * 245.0, 245.0)


def to_local(x: float, y: float) -> tuple[float, float]:
    dx = x - ORIGIN[0]
    dy = 245.0 - y  # image y down -> up
    lx = (dx * COS_T + dy * SIN_T) / 100.0
    ly = (-dx * SIN_T + dy * COS_T) / 100.0
    return round(lx, 3), round(ly, 3)


def classify(width, height, pixels, fg):
    cls = ["bg"] * (width * height)
    for i, (r, g, b, _a) in enumerate(pixels):
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


def erode(idx_set, width, height):
    out = set()
    for i in idx_set:
        x, y = i % width, i // width
        if all(
            0 <= nx < width and 0 <= ny < height and (ny * width + nx) in idx_set
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
        ):
            out.add(i)
    return out


def components(width, height, mask_idx):
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


def local_stats(idxs, width):
    pts = [to_local(i % width, i // width) for i in idxs]
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - cx) ** 2 for p in pts) / n
    syy = sum((p[1] - cy) ** 2 for p in pts) / n
    sxy = sum((p[0] - cx) * (p[1] - cy) for p in pts) / n
    theta = 0.5 * math.atan2(2 * sxy, sxx - syy)
    dx, dy = math.cos(theta), math.sin(theta)
    proj = [(p[0] - cx) * dx + (p[1] - cy) * dy for p in pts]
    perp = [-(p[0] - cx) * dy + (p[1] - cy) * dx for p in pts]
    lo, hi = min(proj), max(proj)
    return {
        "centroid": [round(cx, 3), round(cy, 3)],
        "angleDegLocal": round(math.degrees(math.atan2(dy, dx)) % 180.0, 1),
        "length": round(hi - lo, 3),
        "thickness": round(max(perp) - min(perp), 3),
        "endA": [round(cx + dx * lo, 3), round(cy + dy * lo, 3)],
        "endB": [round(cx + dx * hi, 3), round(cy + dy * hi, 3)],
        "count": len(idxs),
        "bboxLocal": [round(min(p[0] for p in pts), 3), round(min(p[1] for p in pts), 3),
                      round(max(p[0] for p in pts), 3), round(max(p[1] for p in pts), 3)],
    }


def main():
    width, height, pixels = read_png(REF)
    fg, _s, _w = build_foreground_mask(width, height, pixels)
    cls = classify(width, height, pixels, fg)
    idx = {k: {i for i in range(width * height) if cls[i] == k} for k in ("red", "gold", "dark")}

    result: dict = {"toLocal": {"originImage": [round(ORIGIN[0], 2), 245.0], "tiltDeg": M["bladeAxis"]["tiltDegFromVertical"]}}

    # rods: erode once to split touching rods, keep components >= 8 px, report both
    # raw orientation and the axis-line fit through the radiation centre estimate
    eroded = erode(idx["red"], width, height)
    rods = []
    for comp in components(width, height, eroded):
        if len(comp) < 8:
            continue
        st = local_stats(comp, width)
        if abs(st["centroid"][0]) < 0.13 and st["bboxLocal"][1] < 0.65:
            st["kind"] = "spine"
        else:
            st["kind"] = "rod"
            # distance of the radiation point (0,-0.115) from the rod's axis line
            ax, ay = st["endA"]
            bx, by = st["endB"]
            vx, vy = bx - ax, by - ay
            norm = math.hypot(vx, vy) or 1.0
            dist = abs(vx * (-0.115 - ay) - vy * (0 - ax)) / norm
            st["axisDistToRadiationPoint"] = round(dist, 3)
            st["radiusNear"] = round(min(math.hypot(ax, ay + 0.115), math.hypot(bx, by + 0.115)), 3)
            st["radiusFar"] = round(max(math.hypot(ax, ay + 0.115), math.hypot(bx, by + 0.115)), 3)
        rods.append(st)
    result["redComponents"] = sorted(rods, key=lambda s: s["centroid"][0])

    # gold + dark clusters in local coords (no erosion; report each sizeable component)
    for name in ("gold", "dark"):
        comps = [c for c in components(width, height, idx[name]) if len(c) >= 25]
        result[f"{name}Components"] = sorted(
            (local_stats(c, width) for c in comps), key=lambda s: s["centroid"][0]
        )

    out = HERE / "guard-local-measurements.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
