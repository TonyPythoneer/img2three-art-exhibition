"""Which end of the reference eye rides high: the outer end or the inner one?

The render read as wrong-way-slanted by eye. It was not. Both authorities agree the OUTER end
rides high and the inner end drops toward the bridge, by 0.75-1.3 reference rows, which is what
sets `drop` in createSigmaVirusHead.ts. Column means, not single pixels: one pixel of a 1px
stroke is noise.

Usage: python3 measure_eye_slant.py
"""
from PIL import Image

SHEET = "artifacts/exhibits/mmx2-sigma-virus/references/sigma-wireframe-sheet.png"
BG, TOL = (0, 0, 41), 24


def near(p, q, t):
    return all(abs(a - b) <= t for a, b in zip(p[:3], q[:3]))


def fam(p):
    r, g, b = p[:3]
    if g > r + 40 and g > b + 40:
        return "green"
    if r > g + 40 and b > g + 40:
        return "purple"
    if r > g + 40 and r > b + 40:
        return "orange" if g > 60 else "red"
    if b > r + 40 and b > g + 20:
        return "blue"
    return "other"


px = Image.open(SHEET).convert("RGB").load()
for label, (x0, y0, w, h) in {
    "front-geometry (63,1811)": (63, 1811, 47, 69),
    "green-colour  (496,2573)": (496, 2573, 48, 69),
}.items():
    counts, pts = {}, []
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            p = px[x, y]
            if near(p, BG, TOL):
                continue
            f = fam(p)
            counts[f] = counts.get(f, 0) + 1
            pts.append((x - x0, y - y0, f))
    dom = max(counts, key=lambda k: counts[k])
    acc = [(x, y) for x, y, f in pts if f not in (dom, "other")]
    axis = (w - 1) / 2
    print(f"\n{label}  dominant={dom}  accent px={len(acc)}")
    for side, name in ((0, "left "), (1, "right")):
        s = [(x, y) for x, y in acc if (x < axis) == (side == 0)]
        if not s:
            continue
        xs = [p[0] for p in s]
        inner_x = max(xs) if side == 0 else min(xs)
        outer_x = min(xs) if side == 0 else max(xs)
        # mean row within 2px of each end — one pixel is noise, a column mean is not
        inner_y = sum(y for x, y in s if abs(x - inner_x) <= 2) / max(
            1, sum(1 for x, _ in s if abs(x - inner_x) <= 2))
        outer_y = sum(y for x, y in s if abs(x - outer_x) <= 2) / max(
            1, sum(1 for x, _ in s if abs(x - outer_x) <= 2))
        # rows count DOWN, so a smaller mean row = higher on the head
        print(f"  {name} eye: inner end mean row {inner_y:.2f}, outer end mean row {outer_y:.2f}"
              f"  -> {'INNER rides high' if inner_y < outer_y else 'OUTER rides high'}")
