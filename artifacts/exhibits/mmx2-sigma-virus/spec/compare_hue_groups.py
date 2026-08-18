"""Are the sheet's hue groups one model recoloured, or genuinely different models?

This has to be measured, because the answer changes what the reference IS. Published sources
say the MMX2 Sigma Virus has no health meter and reports damage purely by colour — green at
full health, then pale blue, dark blue, purple, orange, red. If that ladder is what the sheet's
bands are, then EVERY band is evidence about the same mesh and the target has hundreds of
usable views instead of a hundred.

The test: take the most row-symmetric front-facing frame in each hue group, normalise both to
the same height, and take the IoU of their filled silhouettes. Same mesh at the same pose scores
near 1; different meshes do not. Symmetry picks the frame rather than the eye, for the same
reason as in find_front_frame.py.

Usage: python3 compare_hue_groups.py <sheet.png> <frame-index.json> <out.json>
"""

import json
import sys
from itertools import combinations

from PIL import Image

BG = (0, 0, 41)
BG_TOL = 24
GRID = 160


def is_bg(p):
    return all(abs(a - b) <= BG_TOL for a, b in zip(p, BG))


def row_extents(px, x0, y0, w, h):
    out = []
    for y in range(y0, y0 + h):
        xs = [x - x0 for x in range(x0, x0 + w) if not is_bg(px[x, y])]
        out.append((min(xs), max(xs)) if xs else None)
    return out


def row_asymmetry(extents, w):
    axis = (w - 1) / 2
    errs = [abs((lo + hi) / 2 - axis) / axis for e in extents if e for lo, hi in [e]]
    return sum(errs) / len(errs) if errs else 1.0


def filled(extents, w, h, gw, gh):
    mask = [[False] * gw for _ in range(gh)]
    for gy in range(gh):
        e = extents[min(h - 1, int(gy * h / gh))]
        if not e:
            continue
        for gx in range(gw):
            sx = gx * w / gw
            if e[0] <= sx <= e[1]:
                mask[gy][gx] = True
    return mask


def iou(a, b, gw, gh):
    inter = sum(1 for y in range(gh) for x in range(gw) if a[y][x] and b[y][x])
    union = sum(1 for y in range(gh) for x in range(gw) if a[y][x] or b[y][x])
    return inter / union if union else 0.0


def main():
    sheet, idx, out = sys.argv[1], sys.argv[2], sys.argv[3]
    px = Image.open(sheet).convert("RGB").load()
    frames = json.load(open(idx))["frames"]

    # One representative per hue group: the most row-symmetric frame at the palette strip's own
    # 48x69, so the comparison is front-against-front at a MATCHED pose. Letting the height float
    # compares a frame at one pitch against another at a different one and scores the pitch, not
    # the mesh — that is what first put a different model inside the "same" band at 0.9087.
    reps = {}
    for f in frames:
        if f["strokePx"] < 500 or not (68 <= f["h"] <= 70) or not (46 <= f["w"] <= 50):
            continue
        ext = row_extents(px, f["x0"], f["y0"], f["w"], f["h"])
        a = row_asymmetry(ext, f["w"])
        key = f["hue"]
        if key not in reps or a < reps[key]["rowAsymmetry"]:
            reps[key] = {**f, "rowAsymmetry": round(a, 4), "extents": ext}

    gh = GRID
    masks = {}
    for hue, f in reps.items():
        gw = round(gh * f["w"] / f["h"])
        masks[hue] = (filled(f["extents"], f["w"], f["h"], gw, gh), gw)

    pairs = {}
    for a, b in combinations(sorted(masks), 2):
        # Compare on the narrower of the two grids so neither is stretched into agreement.
        gw = min(masks[a][1], masks[b][1])
        ma = filled(reps[a]["extents"], reps[a]["w"], reps[a]["h"], gw, gh)
        mb = filled(reps[b]["extents"], reps[b]["w"], reps[b]["h"], gw, gh)
        pairs[f"{a}|{b}"] = round(iou(ma, mb, gw, gh), 4)

    rec = {
        "representatives": {
            hue: {k: f[k] for k in ("x0", "y0", "w", "h", "strokePx", "aspect", "rowAsymmetry")}
            for hue, f in reps.items()
        },
        "pairwiseSilhouetteIou": pairs,
        # A recolour of one mesh at one pose should sit near 1.0; the front-frame gate treats
        # 0.90 as "the same shape", so the same threshold decides this.
        "sameModelThreshold": 0.90,
        "sameModel": {k: v >= 0.90 for k, v in pairs.items()},
    }
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))


main()
