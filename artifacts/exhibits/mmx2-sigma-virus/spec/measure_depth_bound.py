"""Bound the head's depth from the tumble itself, instead of guessing it (guess list G1).

This became possible only after `compare_hue_groups.py` showed the whole sheet is ONE mesh in
six palettes. A rigid body photographed in many orientations gives its own 3D caliper diameter
away for free: the largest distance between two silhouette points, maximised over every frame,
IS the body's longest 3D chord. Nothing about pose needs to be known for that to hold.

So:
  Dmax  = max over all full-scale frames of that frame's 2D caliper   -> the 3D diameter
  Cfront= the front view's own 2D caliper, which spans X and Y only

If the head had a large Z extent, some orientation would swing it into the image plane and
produce a caliper noticeably larger than Cfront. How much larger bounds the depth:

  Zbound = sqrt(max(0, Dmax^2 - Cfront^2))

That is a bound, not a measurement — it is exact only if the chord achieving Dmax pairs a
front-extreme point with a depth-extreme one. It is still evidence, which 1.25-from-a-
foreshortened-crop was not.

The caliper runs on the silhouette's convex hull, not on all 800+ stroke pixels: the diameter of
a point set is the diameter of its hull, and the hull is ~20 points instead of ~900.

Usage: python3 measure_depth_bound.py <sheet.png> <frame-index.json> <out.json>
"""

import json
import math
import sys

from PIL import Image

BG = (0, 0, 41)
BG_TOL = 24
FRONT = (63, 1811, 47, 69)


def is_bg(p):
    return all(abs(a - b) <= BG_TOL for a, b in zip(p, BG))


def hull(points):
    """Monotone chain. Returns the convex hull in order."""
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2:
                (ax, ay), (bx, by) = out[-2], out[-1]
                if (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) > 0:
                    break
                out.pop()
            out.append(p)
        return out

    return half(pts)[:-1] + half(reversed(pts))[:-1]


def caliper(px, x0, y0, w, h):
    pts = [(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w) if not is_bg(px[x, y])]
    if len(pts) < 2:
        return 0.0
    hp = hull(pts)
    best = 0.0
    for i in range(len(hp)):
        for j in range(i + 1, len(hp)):
            d = math.dist(hp[i], hp[j])
            if d > best:
                best = d
    return best


def main():
    sheet, idx, out = sys.argv[1], sys.argv[2], sys.argv[3]
    px = Image.open(sheet).convert("RGB").load()
    frames = json.load(open(idx))["frames"]

    # Full animation scale only. The sequence shrinks the head as it recedes, and a scaled-down
    # frame's caliper is a scaled-down chord that would drag the maximum the wrong way.
    full = [f for f in frames if f["strokePx"] >= 600 and max(f["w"], f["h"]) >= 60]

    scored = []
    for f in full:
        c = caliper(px, f["x0"], f["y0"], f["w"], f["h"])
        scored.append({**f, "caliper": round(c, 3)})
    scored.sort(key=lambda f: -f["caliper"])

    fx, fy, fw, fh = FRONT
    c_front = caliper(px, fx, fy, fw, fh)
    d_max = scored[0]["caliper"] if scored else 0.0
    z_bound = math.sqrt(max(0.0, d_max**2 - c_front**2))

    rec = {
        "framesConsidered": len(full),
        "frontFrame": {"x0": fx, "y0": fy, "w": fw, "h": fh, "caliper": round(c_front, 3)},
        "widestChord": {k: scored[0][k] for k in ("x0", "y0", "w", "h", "caliper")} if scored else None,
        "top5Calipers": [{k: f[k] for k in ("x0", "y0", "w", "h", "caliper")} for f in scored[:5]],
        "depthBoundPx": round(z_bound, 3),
        "depthOverWidth": round(z_bound / fw, 4),
        "note": (
            "Bound, not a measurement: exact only if the chord achieving the maximum pairs a "
            "front-extreme point with a depth-extreme one. Compare against the previous G1 "
            "default of 1.25, which came from a foreshortened crown-from-above crop."
        ),
    }
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))


main()
