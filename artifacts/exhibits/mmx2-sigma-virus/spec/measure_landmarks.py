"""Landmarks for one Sigma-virus frame, in fractions of the frame's own bbox.

Front view only. Depth does NOT come from here — the reference has no clean side view of
this head; see reading.md's guess list G1.

Default frame is the GEOMETRY authority from front-frame.json, not the green one: the
green palette frame is caught at a yaw (rowAsymmetry 0.0555 vs 0.0101). Pass
`--frame x0 y0 w h` to measure a different one — `--frame 496 2573 48 69` is the green
colour authority, which is where the eye band and the palette come from.

Everything below is measured from the stroke mask, never eyeballed off a zoom:
  - per-row stroke extent  -> where the silhouette is widest, and where it steps in
  - the accent-hue cluster -> eye band top/bottom/left/right
  - the lowest closed box  -> the neck/collar block

Usage: python3 measure_landmarks.py <sheet.png> <out.json>
"""
import json
import sys
from collections import Counter

from PIL import Image

BG = (0, 0, 41)
BG_TOL = 24
FRONT = (63, 1811, 47, 69)              # front-frame.json frontFrame — geometry authority
GREEN = (496, 2573, 48, 69)             # p0-triage.json greenFrame — colour authority


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


def main():
    argv = sys.argv[1:]
    if "--frame" in argv:
        i = argv.index("--frame")
        x0, y0, W, H = map(int, argv[i + 1:i + 5])
        del argv[i:i + 5]
    else:
        x0, y0, W, H = FRONT
    sheet, out = argv[0], argv[1]
    px = Image.open(sheet).convert("RGB").load()
    x1, y1 = x0 + W, y0 + H

    rows = []
    for y in range(y0, y1):
        xs = [x for x in range(x0, x1) if not is_bg(px[x, y])]
        rows.append({"y": y - y0, "yFrac": round((y - y0) / (H - 1), 4),
                     "left": min(xs) - x0 if xs else None,
                     "right": max(xs) - x0 if xs else None,
                     "span": (max(xs) - min(xs) + 1) if xs else 0,
                     "count": len(xs)})

    widest = max(rows, key=lambda r: r["span"])

    # The eyes are the frame's ACCENT hue, whatever that hue happens to be: blue in the
    # red geometry frame, orange in the green colour frame. Keying on one literal colour
    # silently returns an empty eye band on the other frame, so key on "not the dominant
    # stroke hue" instead.
    hues = Counter(hue_family(px[x, y]) for y in range(y0, y1) for x in range(x0, x1)
                   if not is_bg(px[x, y]))
    dominant = hues.most_common(1)[0][0]
    eye = [(x - x0, y - y0) for y in range(y0, y1) for x in range(x0, x1)
           if not is_bg(px[x, y]) and hue_family(px[x, y]) not in (dominant, "other")]
    exs = [p[0] for p in eye]
    eys = [p[1] for p in eye]

    # Mirror symmetry about the frame's own vertical centre: the head is authored
    # symmetric, so any residual is the rasteriser's, and it sets the symmetry gate's
    # tolerance instead of being guessed.
    axis = (W - 1) / 2
    mism = 0
    total = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            if is_bg(px[x, y]):
                continue
            total += 1
            mx = x0 + int(round(2 * axis - (x - x0)))
            if not (x0 <= mx < x1) or is_bg(px[mx, y]):
                mism += 1

    rec = {
        "frame": {"x0": x0, "y0": y0, "w": W, "h": H},
        "aspectWOverH": round(W / H, 4),
        "widestRow": {"yFrac": widest["yFrac"], "span": widest["span"],
                      "spanFrac": round(widest["span"] / W, 4)},
        "eyeBand": {
            "yTopFrac": round(min(eys) / (H - 1), 4),
            "yBottomFrac": round(max(eys) / (H - 1), 4),
            "xLeftFrac": round(min(exs) / (W - 1), 4),
            "xRightFrac": round(max(exs) / (W - 1), 4),
            "pixels": len(eye),
        },
        "mirrorMismatch": round(mism / total, 4),
        "rows": rows,
    }
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)

    print(json.dumps({k: rec[k] for k in
                      ("frame", "aspectWOverH", "widestRow", "eyeBand", "mirrorMismatch")}, indent=1))
    print("\nrow profile (yFrac : left-right span):")
    for r in rows[::3]:
        bar = "#" * r["span"]
        print(f'  {r["yFrac"]:.2f}  {str(r["left"]):>3}-{str(r["right"]):<3} {bar}')


main()
