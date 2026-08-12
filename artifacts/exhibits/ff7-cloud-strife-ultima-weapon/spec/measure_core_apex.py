#!/usr/bin/env python3
"""Where does the artwork's dark core actually stop? Measured, not inferred.

`darkCoreTriangle` was authored from reference 03 at confidence 0.45 because the record said the
crop could not answer it: `measure_authority.py` reported the core's apex at `Y = 98.8` and every
document repeated that the crop occludes everything above it. **It does not.** That 98.8 is an
artifact of the instrument, not of the artwork:

    classify() sorts a pixel into "red" only when (h >= 300 or h <= 22) and s >= 0.35,

and the core is only red-tinted where it flanks the gem. Above the gem it is a near-black wedge on
violet, so its hue lands inside the "insert" family and its darkest rows land in "grip". The
red-family measurement therefore stops at the gem's own shoulder and says nothing about the wedge
above it. At 8x and 16x NEAREST, upright in the same weapon-local frame (`spec/zoom-relief/
core-apex-8x-grid.png`, `core-apex-16x-grid.png`), that wedge is plainly there and runs most of the
way up the violet insert.

So this measures it the way the feature actually presents: as a DARKENING of the insert along the
blade's centre line, against the insert's own body a few units outboard.

    contrast(y) = median V over |x| in [30, 36]   -   min V over |x| <= 26

The reference band is inboard of the insert's own dark rim and outboard of the wedge, so it tracks
the insert's shading down the blade instead of assuming a constant. Two numbers come out of the
same profile and they are independent of each other:

  * the ROW CROSSING: the topmost y where contrast is still at half its plateau. One row, so it is
    sensitive to noise, and it is quoted as a cross-check rather than as the answer.
  * the EDGE FIT: the wedge's half-width per row, least-squares fitted over every row above the
    gem's apex, extrapolated to zero width. 87 rows instead of one.

**The fit is the answer, and the reason is that it also validates the part of the outline the crop
cannot see.** Below the gem's apex the wedge and the gem are the same dark run — the gem is
centre-bright but rim-dark, so a threshold on darkness cannot separate them — and no measurement
of the core's width down there is possible. The fit answers it anyway: extrapolated to the gem's
waist it lands within one source pixel of `CORE_HALF_WIDTH`, the value that was DIRECTED there.
A straight line through a directed base and a measured tip, agreeing with 87 measured rows in
between at an RMS well under one source pixel, is a stronger claim than either end alone — and it
is what makes `CORE_OUTLINE` two points rather than three. The knee it used to carry was never
measured; it was the shape a triangle has to take when its tip is cut off at Y = 118.

    python3 src/exhibits/ff7-cloud-strife-ultima-weapon/spec/measure_core_apex.py

Writes spec/core-apex.json and the two zoom PNGs. Reads nothing but the artwork.
"""

from __future__ import annotations

import colorsys
import json
import math
import statistics
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
V = HERE.parent

# --- the wedge's own presentation, and the two bands it is read against ---------------------
# |x| <= CORE_BAND can only ever contain the wedge: the insert is 36-43 half-wide over this
# span, so its own dark rim is far outboard. REF is inboard of that rim and outboard of the
# wedge, i.e. the insert's own body at the same height.
CORE_BAND = 26.0
REF_LO, REF_HI = 30.0, 36.0
STEP = 0.25
# Above the gem's measured apex (97.3) the wedge is alone in the core band. Below it the gem's
# rim-dark shading is inside the same band and no threshold can separate the two.
GEM_APEX_Y = 98
# Where the fit stops looking. Well past any plausible apex; rows with no dark run drop out.
SCAN_TOP = 200
# The insert's own centre-dark shading, measured where the wedge is certainly gone (Y >= 240).
# The half-maximum sits between this and the wedge's plateau.
BASELINE_FROM = 240


def farthest_pair(pts):
    best = (0.0, pts[0], pts[0])
    for i, a in enumerate(pts):
        for b in pts[i + 1:]:
            d = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
            if d > best[0]:
                best = (d, a, b)
    return best[1], best[2]


def classify(r, g, b):
    """measure_authority's own classifier, verbatim — the frame has to be the same frame."""
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h *= 360
    if 225 <= h <= 285 and s >= 0.40 and v >= 0.15:
        return "insert"
    if (h >= 300 or h <= 22) and s >= 0.35 and v >= 0.12:
        return "red"
    if 35 <= h <= 80 and s >= 0.15 and v >= 0.25:
        return "gold"
    if v >= 0.55 and s <= 0.30:
        return "shell"
    if v <= 0.13:
        return "grip"
    return "steel"


def build_frame():
    """measure_authority.py's weapon-local frame, rebuilt here and then PROVED identical.

    Re-deriving it rather than importing is unavoidable — that script is one `main()` that
    writes files — so the landmarks it produced are asserted against instead. If the frame ever
    drifts, this stops rather than quietly measuring in a different coordinate system.
    """
    crop = Image.open(V / "assets/artwork-sword-crop.webp").convert("RGB")
    cut = Image.open(V / "assets/artwork-sword-transparent.webp").convert("RGBA")
    w, h = crop.size
    cp, ap = crop.load(), cut.load()

    labels: list[list[str | None]] = [[None] * w for _ in range(h)]
    rows: dict[int, list[int]] = {}
    for y in range(h):
        for x in range(w):
            if ap[x, y][3] <= 96:
                continue
            labels[y][x] = classify(*cp[x, y])
            rows.setdefault(y, []).append(x)

    cand = []
    for y, xs in rows.items():
        cand.append((float(min(xs)), float(y)))
        cand.append((float(max(xs)), float(y)))
    tip_img, pommel_img = farthest_pair(cand)
    if tip_img[1] > pommel_img[1]:
        tip_img, pommel_img = pommel_img, tip_img
    dx, dy = pommel_img[0] - tip_img[0], pommel_img[1] - tip_img[1]
    n = math.hypot(dx, dy)
    uy = (-dx / n, -dy / n)
    ux = (-uy[1], uy[0])

    def comps(want):
        seen = [[False] * w for _ in range(h)]
        out = []
        for sy in range(h):
            for sx in range(w):
                if seen[sy][sx] or labels[sy][sx] != want:
                    continue
                stack, blob = [(sx, sy)], []
                seen[sy][sx] = True
                while stack:
                    x, y = stack.pop()
                    blob.append((x, y))
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and labels[ny][nx] == want:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
                out.append(blob)
        out.sort(key=len, reverse=True)
        return out

    gold, steel, shell, grip = comps("gold"), comps("steel"), comps("shell"), comps("grip")
    guard = [p for b in gold[:6] for p in b] + [p for b in steel[:6] for p in b]
    gcx = sum(p[0] for p in guard) / len(guard)
    gcy = sum(p[1] for p in guard) / len(guard)
    t = (gcx - tip_img[0]) * uy[0] + (gcy - tip_img[1]) * uy[1]
    origin = [tip_img[0] + uy[0] * t, tip_img[1] + uy[1] * t]

    def local(x, y):
        vx, vy = x - origin[0], y - origin[1]
        return (vx * ux[0] + vy * ux[1], vx * uy[0] + vy * uy[1])

    socket = (min(local(float(x), float(y))[1] for x, y in shell[0])
              + max(local(float(x), float(y))[1] for x, y in grip[0])) / 2
    origin = [origin[0] + uy[0] * socket, origin[1] + uy[1] * socket]
    scale = 760.0 / local(*tip_img)[1]

    def norm(x, y):
        vx, vy = x - origin[0], y - origin[1]
        return ((vx * ux[0] + vy * ux[1]) * scale, (vx * uy[0] + vy * uy[1]) * scale)

    def inv(lx, ly):
        vx = (lx / scale) * ux[0] + (ly / scale) * uy[0]
        vy = (lx / scale) * ux[1] + (ly / scale) * uy[1]
        return (origin[0] + vx, origin[1] + vy)

    want = json.loads((HERE / "measurements.json").read_text())["landmarks"]
    for name, got in (("tip", norm(*tip_img)), ("pommelTip", norm(*pommel_img))):
        for i, axis in enumerate("XY"):
            if abs(got[i] - want[name][i]) > 0.05:
                raise SystemExit(
                    f"frame drift: {name}.{axis} is {got[i]:.2f} here and {want[name][i]:.2f} in "
                    "measurements.json — this script and measure_authority.py disagree about "
                    "where the weapon is, so nothing below is in the same units"
                )
    return crop, cut, norm, inv, 1 / scale


CROP, CUT, NORM, INV, PX_PER_UNIT = build_frame()
CP, AP = CROP.load(), CUT.load()
IW, IH = CROP.size


def value(lx: float, ly: float) -> float | None:
    """HSV value, 0–255, at a weapon-local point; None outside the silhouette."""
    px, py = INV(lx, ly)
    ix, iy = int(round(px)), int(round(py))
    if not (0 <= ix < IW and 0 <= iy < IH) or AP[ix, iy][3] <= 96:
        return None
    r, g, b = CP[ix, iy]
    return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[2] * 255


def scan(lo: int, hi: int):
    """Per row: the insert's own brightness beside the wedge, and every sample in the core band."""
    out = {}
    for yi in range(lo, hi + 1):
        ref, core = [], []
        x = -40.0
        while x <= 40.0:
            v = value(x, float(yi))
            if v is not None:
                if abs(x) <= CORE_BAND:
                    core.append((x, v))
                elif REF_LO <= abs(x) <= REF_HI:
                    ref.append(v)
            x += STEP
        if len(ref) >= 6 and len(core) >= 20:
            out[yi] = (statistics.median(ref), core)
    return out


def fit_apex(rows, threshold: float):
    """Least-squares line through the wedge's half-width per row; apex = where it reaches 0."""
    pts = []
    for y in sorted(rows):
        ref, core = rows[y]
        dark = [x for x, v in core if ref - v >= threshold]
        if dark:
            pts.append((float(y), (max(dark) - min(dark)) / 2))
    if len(pts) < 10:
        return None
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    b = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)
    a = my - b * mx
    rms = math.sqrt(sum((y - (a + b * x)) ** 2 for x, y in pts) / n)
    return {"slope": b, "intercept": a, "apexY": -a / b, "rows": n, "rmsUnits": rms,
            "halfWidthAt55": a + b * 55, "points": pts}


def zoom(x0, x1, y0, y1, mag, path, gx, gy):
    """The crop, de-rotated upright into weapon-local units, NEAREST, with a unit grid."""
    upu = mag * PX_PER_UNIT  # output px per normalized unit = `mag` per SOURCE pixel
    w, h = int(round((x1 - x0) * upu)), int(round((y1 - y0) * upu))
    img = Image.new("RGB", (w, h), (255, 255, 255))
    ip = img.load()
    for oy in range(h):
        ly = y1 - (oy + 0.5) / upu
        for ox in range(w):
            lx = x0 + (ox + 0.5) / upu
            px, py = INV(lx, ly)
            ix, iy = int(round(px)), int(round(py))
            if 0 <= ix < IW and 0 <= iy < IH and AP[ix, iy][3] > 96:
                ip[ox, oy] = CP[ix, iy]
    d = ImageDraw.Draw(img)
    for y in range(int(math.ceil(y0 / gy)) * gy, int(y1) + 1, gy):
        oy = int(round((y1 - y) * upu))
        d.line([(0, oy), (w, oy)], fill=(255, 0, 255))
        d.text((3, oy + 2), str(y), fill=(255, 0, 255))
    for x in range(int(math.ceil(x0 / gx)) * gx, int(x1) + 1, gx):
        ox = int(round((x - x0) * upu))
        d.line([(ox, 0), (ox, h)], fill=(0, 190, 0))
        d.text((ox + 2, 2), str(x), fill=(0, 150, 0))
    img.save(path)
    return path.name, img.size


def main() -> None:
    rows = scan(GEM_APEX_Y, 300)
    plateau = statistics.median(rows[y][0] - min(v for _, v in rows[y][1])
                                for y in range(100, 141) if y in rows)
    tail = [rows[y][0] - min(v for _, v in rows[y][1]) for y in rows if y >= BASELINE_FROM]
    baseline = statistics.median(tail)
    half = (plateau + baseline) / 2

    # --- cross-check: the topmost single row still at half contrast --------------------------
    crossing = max(y for y in rows
                   if rows[y][0] - min(v for _, v in rows[y][1]) >= half)

    # --- the answer: the wedge's own edges, fitted -------------------------------------------
    fitted = {y: rows[y] for y in rows if y <= SCAN_TOP}
    fit = fit_apex(fitted, half)
    assert fit

    # --- and how much of that depends on where the threshold was put -------------------------
    sweep = {}
    for frac in (0.35, 0.45, 0.5, 0.55, 0.65):
        t = baseline + frac * (plateau - baseline)
        f = fit_apex(fitted, t)
        if f:
            sweep[f"{frac:.2f}"] = {"threshold": round(t, 1), "apexY": round(f["apexY"], 1),
                                    "halfWidthAt55": round(f["halfWidthAt55"], 2),
                                    "rmsUnits": round(f["rmsUnits"], 2)}

    report = {
        "what": "the artwork's dark core wedge, in measure_authority's weapon-local units",
        "sourcePixelInUnits": round(1 / PX_PER_UNIT, 3),
        "contrast": {"plateauY100to140": round(plateau, 1),
                     "baselineAboveY240": round(baseline, 1),
                     "halfMaximum": round(half, 1)},
        "rowCrossingApexY": crossing,
        "edgeFit": {
            "rowsUsed": fit["rows"],
            "spanY": [fit["points"][0][0], fit["points"][-1][0]],
            "halfWidth": f"{fit['intercept']:.3f} {fit['slope']:+.4f} * Y",
            "apexY": round(fit["apexY"], 1),
            "halfWidthExtrapolatedTo55": round(fit["halfWidthAt55"], 2),
            "rmsResidualUnits": round(fit["rmsUnits"], 2),
        },
        "thresholdSweep": sweep,
        "profile": [[y, round(hw, 2)] for y, hw in fit["points"]],
    }
    (HERE / "core-apex.json").write_text(json.dumps(report, indent=2) + "\n")

    print(f"contrast   plateau {plateau:.1f}   baseline {baseline:.1f}   half-max {half:.1f}")
    print(f"row crossing            apex Y = {crossing}")
    print(f"edge fit ({fit['rows']} rows)     apex Y = {fit['apexY']:.1f}   "
          f"halfWidth = {fit['intercept']:.3f} {fit['slope']:+.4f} Y   "
          f"RMS {fit['rmsUnits']:.2f} units ({1 / PX_PER_UNIT:.2f} units = 1 source px)")
    print(f"                        extrapolated to Y=55: {fit['halfWidthAt55']:.2f} "
          "(CORE_HALF_WIDTH is directed at 21)")
    for frac, s in sweep.items():
        print(f"  threshold {frac} of plateau ({s['threshold']:5.1f}) -> apex {s['apexY']:6.1f}"
              f"   base {s['halfWidthAt55']:5.2f}   RMS {s['rmsUnits']:.2f}")

    out = HERE / "zoom-relief"
    for args in ((-70, 70, -20, 300, 8, out / "core-apex-8x-grid.png", 20, 20),
                 (-40, 40, 80, 220, 16, out / "core-apex-16x-grid.png", 10, 10)):
        name, size = zoom(*args)
        print(f"wrote zoom-relief/{name} {size[0]}x{size[1]}")
    print(f"wrote spec/core-apex.json")


if __name__ == "__main__":
    main()
