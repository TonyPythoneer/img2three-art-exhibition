"""Interior-feature gate: where the eyes sit, and how much of the face they cover.

The silhouette gate cannot see this and never will. It reduces both sides to a per-row filled
outline, so a head whose eyes are half the right size and in the wrong place scores exactly the
same as one whose eyes are right — which is the failure mode CLAUDE.md names ("a gate that only
measures dimensions goes all-green while the model is round"). This gate blocks the thing the
silhouette gate is structurally blind to.

The eyes are the one feature the reference states unambiguously in BOTH authorities: they are
the accent hue in the geometry frame and the C3 orange in the green colour frame, and
`landmarks.json.eyeBand` measures the same band in both. So they are what an interior gate can
honestly be built on; the brow and crest lines are stroke work with no fillable region.

  PASS when every eye-band edge is within --tol of the reference (as a fraction of the head's
  own bbox) AND the eye area fraction is within --area-tol relative.

The area half of that comparison has one trap, and it produced a false PASS on the first run.
`landmarks.json.eyeBand.pixels` counts the reference's accent STROKES — an outline — while the
render's eyes are a filled surface. Comparing 57 outline pixels against a filled region scores
an eye at 44% of its reference size as 32% too LARGE. So the reference eye is filled here the
same way the silhouette gate fills the head: per row, between that row's extents, and per SIDE,
because filling across both eyes would swallow the nose bridge between them.

Usage:
  python3 gate_features.py <render.png> <sheet.png> <landmarks.json> --out gate-features.json
Exit 0 pass, 1 gate failure, 2 error.
"""

import argparse
import json
import sys

from PIL import Image

BG_TOL = 24


def near(p, q, tol):
    return all(abs(a - b) <= tol for a, b in zip(p[:3], q[:3]))


def is_eye_pixel(p):
    """C3 orange, `colors.ts`: #E05000. Wide enough for the shaded faces of a lit fill."""
    r, g, b = p[:3]
    return r > 110 and r > g + 45 and g >= b and b < 90


def hue_family(p):
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


def reference_eye_fill(sheet_path, frame, sheet_bg=(0, 0, 41)):
    """Filled area of the reference's two eyes, as a fraction of the frame, per side.

    Fills per row and per side for the reason in the module docstring: one fill across the whole
    eye band would include the nose bridge, which is not eye.
    """
    px = Image.open(sheet_path).convert("RGB").load()
    x0, y0, w, h = frame["x0"], frame["y0"], frame["w"], frame["h"]
    hues = {}
    pts = []
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            p = px[x, y]
            if near(p, sheet_bg, BG_TOL):
                continue
            fam = hue_family(p)
            hues[fam] = hues.get(fam, 0) + 1
            pts.append((x - x0, y - y0, fam))
    dominant = max(hues, key=lambda k: hues[k])
    accent = [(x, y) for x, y, fam in pts if fam not in (dominant, "other")]
    axis = (w - 1) / 2
    filled = 0
    for side in (0, 1):
        rows = {}
        for x, y in accent:
            if (x < axis) == (side == 0):
                lo, hi = rows.get(y, (x, x))
                rows[y] = (min(lo, x), max(hi, x))
        filled += sum(hi - lo + 1 for lo, hi in rows.values())
    return filled / (w * h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("render")
    ap.add_argument("sheet")
    ap.add_argument("landmarks")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tol", type=float, default=0.06)
    ap.add_argument("--area-tol", type=float, default=0.30)
    a = ap.parse_args()

    ref = json.load(open(a.landmarks))
    band = ref["eyeBand"]
    frame = ref["frame"]
    ref_area = reference_eye_fill(a.sheet, frame)

    im = Image.open(a.render).convert("RGB")
    px = im.load()
    bg = px[0, 0]

    head, eyes = [], []
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if near(p, bg, BG_TOL):
                continue
            head.append((x, y))
            if is_eye_pixel(p):
                eyes.append((x, y))
    if not head:
        raise SystemExit("render is empty — the capture caught a blank canvas")
    if not eyes:
        raise SystemExit("no C3 pixels in the render — the eyes never rendered")

    hx = [p[0] for p in head]
    hy = [p[1] for p in head]
    x0, y0 = min(hx), min(hy)
    w, h = max(hx) - x0 + 1, max(hy) - y0 + 1

    ex = [p[0] - x0 for p in eyes]
    ey = [p[1] - y0 for p in eyes]
    got = {
        "yTopFrac": round(min(ey) / (h - 1), 4),
        "yBottomFrac": round(max(ey) / (h - 1), 4),
        "xLeftFrac": round(min(ex) / (w - 1), 4),
        "xRightFrac": round(max(ex) / (w - 1), 4),
    }
    got_area = len(eyes) / (w * h)

    deltas = {k: round(abs(got[k] - band[k]), 4) for k in got}
    area_err = abs(got_area - ref_area) / ref_area

    edges_ok = all(v <= a.tol for v in deltas.values())
    area_ok = area_err <= a.area_tol

    rec = {
        "render": a.render,
        "headBBox": {"x0": x0, "y0": y0, "w": w, "h": h},
        "eyeBand": {"reference": {k: band[k] for k in got}, "render": got, "delta": deltas,
                    "tol": a.tol, "pass": edges_ok},
        "eyeArea": {"referenceFilledFrac": round(ref_area, 5), "renderFrac": round(got_area, 5),
                    "relError": round(area_err, 4), "tol": a.area_tol, "pass": area_ok},
        "pass": edges_ok and area_ok,
    }
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec, indent=1))
    sys.exit(0 if rec["pass"] else 1)


main()
