"""Find the true front view of the Sigma-virus head by measuring, not by eye.

The green palette frame is NOT it. Its per-row extents are lopsided (row 0 runs 12-31,
centre 21.5; row 36 runs 0-47, centre 23.5), so that frame is caught at a small yaw and
is only the COLOUR authority. Geometry has to come from whichever frame is most nearly
mirror-symmetric.

Symmetry is measured on per-row silhouette EXTENTS, never on stroke pixels. The strokes
are 1px wide, so a mirrored stroke almost never lands on another stroke and a pixel-wise
mirror test reports ~0.65 mismatch for a perfectly symmetric wireframe — it measures
raster registration, not shape.

  rowAsymmetry = mean over occupied rows of |centre(row) - centre(bbox)| / halfWidth

Usage: python3 find_front_frame.py <sheet.png> <frame-index.json> <out.json>
"""
import json
import sys

from PIL import Image

BG = (0, 0, 41)
BG_TOL = 24


def is_bg(p):
    return all(abs(a - b) <= BG_TOL for a, b in zip(p, BG))


def row_asymmetry(px, f):
    x0, y0, w, h = f["x0"], f["y0"], f["w"], f["h"]
    axis = (w - 1) / 2
    errs = []
    for y in range(y0, y0 + h):
        xs = [x - x0 for x in range(x0, x0 + w) if not is_bg(px[x, y])]
        if len(xs) < 2:
            continue
        centre = (min(xs) + max(xs)) / 2
        errs.append(abs(centre - axis) / axis)
    return (sum(errs) / len(errs)) if errs else 1.0, len(errs)


def main():
    sheet, idx, out = sys.argv[1], sys.argv[2], sys.argv[3]
    px = Image.open(sheet).convert("RGB").load()
    frames = json.load(open(idx))["frames"]

    # The target model: red strokes with a blue eye accent, at full animation scale
    # (48x69 is the size the palette strip is drawn at, so same-scale frames compare
    # against the colour authority without any resampling).
    target = [f for f in frames
              if f["hue"] == "red" and "blue" in f["accents"]
              and 46 <= f["w"] <= 50 and 66 <= f["h"] <= 72]

    scored = []
    for f in target:
        a, rows = row_asymmetry(px, f)
        scored.append({**f, "rowAsymmetry": round(a, 4), "occupiedRows": rows})
    scored.sort(key=lambda f: f["rowAsymmetry"])

    green = {"x0": 496, "y0": 2573, "w": 48, "h": 69}
    ga, _ = row_asymmetry(px, green)

    rec = {
        "candidateCount": len(scored),
        "greenColourFrame": {**green, "rowAsymmetry": round(ga, 4)},
        "frontFrame": scored[0] if scored else None,
        "runnersUp": scored[1:5],
        "worst": scored[-1] if scored else None,
    }
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))


main()
