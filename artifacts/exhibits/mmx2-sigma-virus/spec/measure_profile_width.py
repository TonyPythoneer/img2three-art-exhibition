"""Resolve guess G1 — head depth — from the yaw sweep instead of a foreshortened crop.

Filtering the index to frames whose height matches the front view's (68-70px) isolates PURE YAW:
a pitched head is shorter, so a height match means the rotation stayed about the vertical axis.
Across those 87 frames the width sweeps 42 -> 67 while the height holds, which is a yaw sweep
and nothing else.

Width alone cannot finish the job. For a rectangular cross-section W x D the width at yaw t is
W|cos t| + D|sin t|, peaking at sqrt(W^2 + D^2); for an elliptical one it is
2*sqrt(a^2cos^2 t + b^2sin^2 t), peaking at max(W, D). The same 67px peak therefore means
D = 47.7 under one model and D = 67 under the other — a 1.02x vs 1.43x difference in the answer.

So find the frame that is actually at 90 degrees, and read its width directly. At 90 degrees the
two eyes overlap into ONE accent cluster jammed against the silhouette's leading edge, whereas at
0 degrees they straddle the centre. Scoring the accent centroid's offset from the silhouette
centre, normalised by the half-width, orders every frame by exactly that.

Usage: python3 measure_profile_width.py <sheet.png> <frame-index.json> <out.json>
"""

import json
import sys

from PIL import Image

BG = (0, 0, 41)
BG_TOL = 24
FRONT_W = 47


def is_bg(p):
    return all(abs(a - b) <= BG_TOL for a, b in zip(p, BG))


def hue_family(p):
    r, g, b = p
    if g > r + 40 and g > b + 40:
        return "green"
    if r > g + 40 and b > g + 40:
        return "purple"
    if r > g + 40 and r > b + 40:
        return "orange" if g > 60 else "red"
    if b > r + 40 and b > g + 20:
        return "blue"
    return "other"


def score(px, f):
    x0, y0, w, h = f["x0"], f["y0"], f["w"], f["h"]
    body, accent = [], []
    hues = {}
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            p = px[x, y]
            if is_bg(p):
                continue
            fam = hue_family(p)
            hues[fam] = hues.get(fam, 0) + 1
            body.append(x - x0)
    dominant = max(hues, key=lambda k: hues[k])
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            p = px[x, y]
            if is_bg(p):
                continue
            if hue_family(p) not in (dominant, "other"):
                accent.append(x - x0)
    if not accent or not body:
        return None
    centre = (min(body) + max(body)) / 2
    half = (max(body) - min(body)) / 2 or 1
    mean_accent = sum(accent) / len(accent)
    # Spread of the accent across x: two straddling eyes are wide, one overlapped pair is narrow.
    spread = (max(accent) - min(accent) + 1) / (2 * half)
    return {
        "offset": round(abs(mean_accent - centre) / half, 4),
        "accentSpread": round(spread, 4),
        "accentPx": len(accent),
    }


def main():
    sheet, idx, out = sys.argv[1], sys.argv[2], sys.argv[3]
    px = Image.open(sheet).convert("RGB").load()
    frames = json.load(open(idx))["frames"]

    yaw = [f for f in frames if 68 <= f["h"] <= 70 and f["strokePx"] >= 600 and f["accents"]]
    scored = []
    for f in yaw:
        s = score(px, f)
        if s:
            scored.append({**{k: f[k] for k in ("x0", "y0", "w", "h", "strokePx")}, **s})

    # Most profile-like first: the accent shoved furthest off centre AND collapsed narrowest.
    scored.sort(key=lambda f: -(f["offset"] - f["accentSpread"]))
    best = scored[0]
    frontal = min(scored, key=lambda f: f["offset"])

    rec = {
        "yawCandidates": len(scored),
        "widthRange": [min(f["w"] for f in scored), max(f["w"] for f in scored)],
        "mostFrontal": frontal,
        "mostProfile": best,
        "runnersUp": scored[1:5],
        "depthPx": best["w"],
        "depthOverWidth": round(best["w"] / FRONT_W, 4),
        "note": (
            "depthOverWidth is read off the most-profile frame's width. The two cross-section "
            "models bracket it at 1.02 (rectangular) to 1.43 (elliptical) from the 67px peak "
            "alone; this picks the frame instead of picking a model."
        ),
    }
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))


main()
