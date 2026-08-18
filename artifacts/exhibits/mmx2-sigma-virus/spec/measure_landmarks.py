"""Landmarks for the green Sigma-virus frame, in fractions of the frame's own bbox.

Front view only. The green frame is 48x69px with pixel-identical geometry to the other
three palette frames (p0-triage.json: crossVariantSpread 0.0), so width and height carry
no cross-view scale error at all. Depth does NOT come from here — the reference has no
clean side view of this head; see reading.md's guess list.

Everything below is measured from the stroke mask, never eyeballed off a zoom:
  - per-row stroke extent  -> where the silhouette is widest, and where it steps in
  - the orange cluster     -> eye band top/bottom/left/right
  - the lowest closed box  -> the neck/collar block

Usage: python3 measure_landmarks.py <sheet.png> <out.json>
"""
import json
import sys

from PIL import Image

BG = (0, 0, 41)
BG_TOL = 24
FRAME = (496, 2573, 544, 2642)          # from p0-triage.json greenFrame, x1/y1 exclusive


def is_bg(p):
    return all(abs(a - b) <= BG_TOL for a, b in zip(p, BG))


def is_eye(p):
    r, g, b = p
    return r > 150 and 30 < g < 140 and b < 60          # the #E05000 orange


def main():
    sheet, out = sys.argv[1], sys.argv[2]
    px = Image.open(sheet).convert("RGB").load()
    x0, y0, x1, y1 = FRAME
    W, H = x1 - x0, y1 - y0

    rows = []
    for y in range(y0, y1):
        xs = [x for x in range(x0, x1) if not is_bg(px[x, y])]
        rows.append({"y": y - y0, "yFrac": round((y - y0) / (H - 1), 4),
                     "left": min(xs) - x0 if xs else None,
                     "right": max(xs) - x0 if xs else None,
                     "span": (max(xs) - min(xs) + 1) if xs else 0,
                     "count": len(xs)})

    widest = max(rows, key=lambda r: r["span"])
    eye = [(x - x0, y - y0) for y in range(y0, y1) for x in range(x0, x1) if is_eye(px[x, y])]
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
