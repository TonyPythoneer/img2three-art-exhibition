"""Front-silhouette gate: the render against the reference frame it was measured from.

The reference is a WIREFRAME, so it has no filled silhouette to compare against directly.
Both sides are therefore reduced the same way — per row, fill between the leftmost and the
rightmost non-background pixel — and the IoU is taken on those filled masks. Comparing stroke
pixels to stroke pixels instead would score line placement, which is a rendering choice, not
the shape.

Both masks are normalised onto the reference frame's own 47x69 grid before comparison, so the
score is about proportion and outline, never about how many pixels the capture happened to be.

  PASS when iou >= --min-iou (default 0.90) AND the aspect error is within --max-aspect-err.

Usage:
  python3 gate_silhouette.py <render.png> <sheet.png> --out gate-silhouette.json
Exit 0 pass, 1 gate failure, 2 error.
"""

import argparse
import json
import sys

from PIL import Image

FRONT = (63, 1811, 47, 69)          # front-frame.json frontFrame — the geometry authority
SHEET_BG = (0, 0, 41)
BG_TOL = 24


def near(p, q, tol):
    return all(abs(a - b) <= tol for a, b in zip(p[:3], q[:3]))


def row_extents(px, x0, y0, w, h, bg, tol):
    """Per-row [left, right] of the non-background pixels, in frame-local columns."""
    out = []
    for y in range(y0, y0 + h):
        xs = [x - x0 for x in range(x0, x0 + w) if not near(px[x, y], bg, tol)]
        out.append((min(xs), max(xs)) if xs else None)
    return out


def filled_mask(extents, w, h, grid_w, grid_h):
    """Resample the per-row extents onto a grid_w x grid_h filled mask."""
    mask = [[False] * grid_w for _ in range(grid_h)]
    for gy in range(grid_h):
        sy = min(h - 1, int(gy * h / grid_h))
        ext = extents[sy]
        if not ext:
            continue
        for gx in range(grid_w):
            sx = gx * w / grid_w
            if ext[0] <= sx <= ext[1]:
                mask[gy][gx] = True
    return mask


def bbox_of(px, w, h, bg, tol):
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            if not near(px[x, y], bg, tol):
                xs.append(x)
                ys.append(y)
    if not xs:
        raise SystemExit("render is empty — the capture caught a blank canvas")
    return min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("render")
    ap.add_argument("sheet")
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-iou", type=float, default=0.90)
    ap.add_argument("--max-aspect-err", type=float, default=0.06)
    ap.add_argument("--grid", type=int, default=138)   # 2x the reference frame's height
    a = ap.parse_args()

    ref_im = Image.open(a.sheet).convert("RGB")
    ref_px = ref_im.load()
    rx, ry, rw, rh = FRONT
    ref_ext = row_extents(ref_px, rx, ry, rw, rh, SHEET_BG, BG_TOL)

    ren_im = Image.open(a.render).convert("RGB")
    ren_px = ren_im.load()
    # The render's own ground is the viewer's background colour, read off its top-left corner
    # rather than assumed — a background change in the viewer must not silently empty the mask.
    ren_bg = ren_px[0, 0]
    bx, by, bw, bh = bbox_of(ren_px, ren_im.width, ren_im.height, ren_bg, BG_TOL)
    ren_ext = row_extents(ren_px, bx, by, bw, bh, ren_bg, BG_TOL)

    gw = round(a.grid * (rw / rh))
    gh = a.grid
    ref_mask = filled_mask(ref_ext, rw, rh, gw, gh)
    ren_mask = filled_mask(ren_ext, bw, bh, gw, gh)

    inter = sum(1 for y in range(gh) for x in range(gw) if ref_mask[y][x] and ren_mask[y][x])
    union = sum(1 for y in range(gh) for x in range(gw) if ref_mask[y][x] or ren_mask[y][x])
    iou = inter / union if union else 0.0

    ref_aspect = rw / rh
    ren_aspect = bw / bh
    aspect_err = abs(ren_aspect - ref_aspect) / ref_aspect

    # Per-band IoU, because a global score hides a defect that is confined to one band — an
    # ear pod that never protrudes costs about two points globally and fails its own band.
    bands = {}
    for name, (lo, hi) in {
        "crown": (0.00, 0.20),
        "helmetSides": (0.20, 0.48),
        "earPods": (0.48, 0.63),
        "jaw": (0.63, 0.75),
        "neck": (0.75, 1.00),
    }.items():
        y0, y1 = int(lo * gh), int(hi * gh)
        i = sum(1 for y in range(y0, y1) for x in range(gw) if ref_mask[y][x] and ren_mask[y][x])
        u = sum(1 for y in range(y0, y1) for x in range(gw) if ref_mask[y][x] or ren_mask[y][x])
        bands[name] = round(i / u, 4) if u else None

    passed = iou >= a.min_iou and aspect_err <= a.max_aspect_err
    rec = {
        "render": a.render,
        "referenceFrame": {"x0": rx, "y0": ry, "w": rw, "h": rh},
        "renderBBox": {"x0": bx, "y0": by, "w": bw, "h": bh},
        "grid": [gw, gh],
        "iou": round(iou, 4),
        "minIou": a.min_iou,
        "aspect": {"reference": round(ref_aspect, 4), "render": round(ren_aspect, 4),
                   "error": round(aspect_err, 4), "max": a.max_aspect_err},
        "bandIou": bands,
        "pass": passed,
    }
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))
    sys.exit(0 if passed else 1)


main()
