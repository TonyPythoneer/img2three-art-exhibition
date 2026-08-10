#!/usr/bin/env python3
"""Which way do the spinner caps taper — and which way does the BUILD taper? Both measured.

`SPINNER_PROFILE` was authored from five sampled rows and a sentence — "21.4 at the bulge" — and
nobody ever asked the crop whether there IS a bulge, or asked a render what the built silhouette
does between the seat and that row. This asks both, in `measure_authority.py`'s weapon-local
frame, and it answers three separate questions that had been collapsed into one:

  * **the crop's caps.** Per-row half-widths of each gold blob, taken TWICE: once along weapon
    Y, and once along the cap's OWN principal axis. The two differ because the crop's caps hang
    about 12 degrees off vertical in opposite directions, and a horizontal row across a tilted
    cone is wider than a section perpendicular to its axis. A lathe has no tilt to give, so the
    axis reading is the one a profile should be built from and the row reading is what the front
    view will be compared against.
  * **is the edge straight?** A line and a parabola are both fitted to the same points. If the
    quadratic term is inside its own noise the cap is a straight-sided frustum; if it is not, the
    sign says whether the flank bulges out or is dished in.
  * **the BUILD, from a render rather than from the source.** Per-row half-widths of the run
    that contains the spinner's axis in `full/front-orthographic.png`, so what is reported is
    the outline a viewer actually sees — arm and cap together, exactly as the eye takes it.
    Below the arm's end-cap plane that run is the spinner alone, and the crossing height is
    computed from the arm's own constants rather than guessed at.

**Why the render and not the profile table.** The visible shape is not the table: the seat ring
is derived from the arm, the first profile row is at a fixed absolute Y, and the lathe
INTERPOLATES between them — so moving the arm restretches that section without a single number
in the table changing. That is how the caps came to read as spinning tops with the widest ring
half way down while every row in the table still said what it always said.

    python3 src/exhibits/cloud-ultima-weapon-v2/spec/measure_spinner_taper.py

Writes `spec/spinner-taper.json` and four 8x/16x NEAREST zooms into `spec/zoom-spinner/`. Reads
the artwork, the factory source and `artifacts/ultima-v2/full/{front-orthographic,parts}.json`.
Not a gate — the assertion with teeth is `check_centerline.py`'s monotone-taper clause, which
reads the factory. This is the measurement that clause was written against.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

# The frame is built once, in measure_core_apex, and asserted there against measurements.json.
# The render mapping is built once, in measure_guard_joints. Both are imported for the same
# reason: a second copy is how two scripts end up reporting one feature at two different heights.
from measure_core_apex import AP, CP, IH, IW, INV, NORM, PX_PER_UNIT, classify, zoom
from measure_guard_joints import render_frame, side_by_side

HERE = Path(__file__).resolve().parent
V = HERE.parent
ROOT = V.parent.parent.parent

# --- the crop's three pins on the arm-and-cap assembly, from measurements.json's gold blobs -----
# Means of the two caps, which is all a symmetric model can answer to: the crop's own left/right
# asymmetry is 12% on the axis, 29% on the tops and 13% on the bottoms.
CROP_CAP_TOP = -53.45        # (-61.5 + -45.4) / 2, the topmost GOLD pixel of each blob
CROP_CAP_BOTTOM = -109.65    # (-117.0 + -102.3) / 2
CROP_CAP_AXIS = 81.925       # mean of both blobs' bbox centres and pixel centroids
# The crop's arm across a horizontal row, from `spec/guard-joints.json` — the build's own section
# is 31% wider and that is recorded in CURRENT-MODEL §11 item 2c rather than chased.
CROP_ARM_SECTION = 32.0
CONNECTOR_ROOT = (46.1481047, 23.4126631)   # locked; asserted against the factory below

STEP = 0.25          # the sampling pitch every other measurement in this exhibit uses
ROW = 1.0            # weapon-local rows, ~0.43 source pixels apart — NEAREST, so oversampled
BIN = 2.5            # bins along a cap's own axis; ~1 source pixel
# The two caps are the only gold blobs below the guard and outboard of the grip. The pommel's
# gold is on the axis and the collar's is above it, so this separates all four without a
# hand-picked index.
CAP_MAX_Y = -35.0
CAP_MIN_ABS_X = 40.0


# --- the crop's two caps --------------------------------------------------------------------

def gold_blobs() -> list[list[tuple[int, int]]]:
    """Connected gold components, in IMAGE pixels, largest first."""
    seen = [[False] * IW for _ in range(IH)]
    out: list[list[tuple[int, int]]] = []
    for sy in range(IH):
        for sx in range(IW):
            if seen[sy][sx]:
                continue
            seen[sy][sx] = True
            if AP[sx, sy][3] <= 96 or classify(*CP[sx, sy]) != "gold":
                continue
            stack, blob = [(sx, sy)], []
            while stack:
                x, y = stack.pop()
                blob.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if not (0 <= nx < IW and 0 <= ny < IH) or seen[ny][nx]:
                        continue
                    seen[ny][nx] = True
                    if AP[nx, ny][3] > 96 and classify(*CP[nx, ny]) == "gold":
                        stack.append((nx, ny))
            out.append(blob)
    out.sort(key=len, reverse=True)
    return out


def caps() -> dict[str, dict]:
    """The two spinner caps, keyed by side, each with its image pixels and its local bbox.

    Selected by WHERE they are rather than by index into `measurements.json`, and then checked
    against that file's bboxes — so a re-segmentation that moves a blob fails loudly instead of
    measuring the pommel and calling it a spinner.
    """
    want = {b["centroid"][0] > 0 and "right" or "left": b
            for b in json.loads((HERE / "measurements.json").read_text())["gold"]
            if b["bbox"]["maxY"] < CAP_MAX_Y and abs(b["centroid"][0]) > CAP_MIN_ABS_X}
    if len(want) != 2:
        raise SystemExit("measurements.json no longer has exactly two gold blobs below the guard")

    got: dict[str, dict] = {}
    for blob in gold_blobs():
        pts = [NORM(float(x), float(y)) for x, y in blob]
        cx = sum(p[0] for p in pts) / len(pts)
        ys = [p[1] for p in pts]
        if max(ys) >= CAP_MAX_Y or abs(cx) <= CAP_MIN_ABS_X:
            continue
        side = "right" if cx > 0 else "left"
        if side in got:
            continue  # blobs arrive largest first, and the crop carries 2-pixel gold specks
        got[side] = {"pixels": set(blob), "local": pts,
                     "bbox": {"minX": min(p[0] for p in pts), "maxX": max(p[0] for p in pts),
                              "minY": min(ys), "maxY": max(ys)}}
    if set(got) != {"left", "right"}:
        raise SystemExit(f"found {sorted(got)} gold caps below the guard, expected left and right")

    for side, cap in got.items():
        for key, mine in cap["bbox"].items():
            theirs = want[side]["bbox"][key]
            if abs(mine - theirs) > 0.5:
                raise SystemExit(
                    f"{side} cap {key} is {mine:.1f} here and {theirs:.1f} in measurements.json — "
                    "the two scripts are not segmenting the same blob"
                )
    return got


def inside(cap: dict, lx: float, ly: float) -> bool:
    px, py = INV(lx, ly)
    return (int(round(px)), int(round(py))) in cap["pixels"]


def row_profile(cap: dict) -> list[tuple[float, float]]:
    """Half-width per weapon-local row, top row first, as (drop below the cap's top, halfWidth)."""
    b = cap["bbox"]
    out = []
    y = b["maxY"]
    while y >= b["minY"] - ROW:
        xs = []
        x = b["minX"] - 4
        while x <= b["maxX"] + 4:
            if inside(cap, x, y):
                xs.append(x)
            x += STEP
        if xs:
            out.append((round(b["maxY"] - y, 2), (max(xs) - min(xs)) / 2))
        y -= ROW
    return out


def axis_profile(cap: dict) -> tuple[list[tuple[float, float]], float]:
    """Half-width per bin along the cap's OWN principal axis, and that axis's tilt from vertical.

    PCA over the finely sampled interior rather than over the 300-odd source pixels: same shape,
    but the bins are not one pixel wide and empty.
    """
    b = cap["bbox"]
    pts = []
    y = b["maxY"]
    while y >= b["minY"] - ROW:
        x = b["minX"] - 4
        while x <= b["maxX"] + 4:
            if inside(cap, x, y):
                pts.append((x, y))
            x += STEP
        y -= ROW / 4
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts) / n
    syy = sum((p[1] - my) ** 2 for p in pts) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts) / n
    theta = 0.5 * math.atan2(2 * sxy, sxx - syy)
    # The MAJOR axis, pointed downward — a cap is longer than it is wide, so the eigenvector with
    # the larger eigenvalue is its length.
    ux, uy = math.cos(theta), math.sin(theta)
    if (sxx - syy) * math.cos(2 * theta) + 2 * sxy * math.sin(2 * theta) < 0:
        ux, uy = -uy, ux
    if uy > 0:
        ux, uy = -ux, -uy
    vx, vy = -uy, ux

    ts = [(p[0] - mx) * ux + (p[1] - my) * uy for p in pts]
    ss = [(p[0] - mx) * vx + (p[1] - my) * vy for p in pts]
    t0 = min(ts)
    bins: dict[int, list[float]] = {}
    for t, s in zip(ts, ss):
        bins.setdefault(int((t - t0) // BIN), []).append(s)
    prof = [((k + 0.5) * BIN, (max(v) - min(v)) / 2) for k, v in sorted(bins.items()) if len(v) > 3]
    return prof, math.degrees(math.atan2(ux, -uy))


def leather_above(cap: dict) -> float | None:
    """The dark run's half-width just above the cap's top, on the cap's own axis.

    What the joint has to answer: does the crop's gold stand PROUD of the leather at the boundary,
    or is it flush with it? Read 4 units above the topmost gold row, which is one and a half
    source pixels clear of the boundary's own anti-aliasing.
    """
    b = cap["bbox"]
    axis = (b["minX"] + b["maxX"]) / 2
    y = b["maxY"] + 4.0
    xs = []
    x = axis
    while x <= axis + 40:
        if _dark(x, y):
            xs.append(x)
            x += STEP
        else:
            break
    x = axis - STEP
    while x >= axis - 40:
        if _dark(x, y):
            xs.append(x)
            x -= STEP
        else:
            break
    return (max(xs) - min(xs)) / 2 if len(xs) > 4 else None


def _dark(lx: float, ly: float) -> bool:
    px, py = INV(lx, ly)
    ix, iy = int(round(px)), int(round(py))
    if not (0 <= ix < IW and 0 <= iy < IH) or AP[ix, iy][3] <= 96:
        return False
    return classify(*CP[ix, iy]) in {"grip", "steel", "gold"}


# --- fits -----------------------------------------------------------------------------------

def fits(prof: list[tuple[float, float]]) -> dict:
    """Straight line and parabola through the same points; the quadratic term against its noise."""
    n = len(prof)
    xs = [p[0] for p in prof]
    ys = [p[1] for p in prof]
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in prof) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    lin_rms = math.sqrt(sum((y - (a + b * x)) ** 2 for x, y in prof) / n)

    # y = c0 + c1 u + c2 u^2 on centred u, solved by 3x3 normal equations.
    us = [x - mx for x in xs]
    m = [[float(n), sum(us), sum(u * u for u in us)],
         [sum(us), sum(u * u for u in us), sum(u ** 3 for u in us)],
         [sum(u * u for u in us), sum(u ** 3 for u in us), sum(u ** 4 for u in us)]]
    r = [sum(ys), sum(u * y for u, y in zip(us, ys)), sum(u * u * y for u, y in zip(us, ys))]
    c = _solve3(m, r)
    quad_rms = math.sqrt(sum((y - (c[0] + c[1] * u + c[2] * u * u)) ** 2
                             for u, y in zip(us, ys)) / n)
    # The curvature's own standard error, from the residual and the design matrix's (2,2) inverse.
    inv22 = _inv3(m)[2][2]
    se = quad_rms * math.sqrt(max(inv22, 0.0)) * math.sqrt(n / max(n - 3, 1))
    # How much the fitted flank actually bows away from the straight chord, in units. The sigma
    # beside it is optimistic and is not the figure to quote: rows are sampled every 1.0 units
    # against a 2.34-unit source pixel, so consecutive residuals are the SAME pixel read twice
    # and the fit sees 2.3x more independent points than the crop contains. The sagitta does not
    # care — it is a distance, and it is what decides whether a straight-sided lathe can carry
    # the crop's flank.
    span = max(xs) - min(xs)
    return {"halfWidth": f"{a:.3f} {b:+.4f} * drop", "slope": b, "intercept": a,
            "linearRmsUnits": lin_rms, "quadratic": c[2], "quadraticStdErr": se,
            "quadraticSigma": abs(c[2]) / se if se else float("inf"),
            "bowFromChordUnits": abs(c[2]) * span * span / 8,
            "quadRmsUnits": quad_rms, "points": n}


def _solve3(m, r):
    a = [row[:] + [v] for row, v in zip(m, r)]
    for i in range(3):
        p = max(range(i, 3), key=lambda k: abs(a[k][i]))
        a[i], a[p] = a[p], a[i]
        for k in range(3):
            if k == i:
                continue
            f = a[k][i] / a[i][i]
            for j in range(i, 4):
                a[k][j] -= f * a[i][j]
    return [a[i][3] / a[i][i] for i in range(3)]


def _inv3(m):
    n = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    a = [row[:] for row in m]
    for i in range(3):
        p = max(range(i, 3), key=lambda k: abs(a[k][i]))
        a[i], a[p] = a[p], a[i]
        n[i], n[p] = n[p], n[i]
        d = a[i][i]
        a[i] = [v / d for v in a[i]]
        n[i] = [v / d for v in n[i]]
        for k in range(3):
            if k == i:
                continue
            f = a[k][i]
            a[k] = [v - f * w for v, w in zip(a[k], a[i])]
            n[k] = [v - f * w for v, w in zip(n[k], n[i])]
    return n


def widest(prof: list[tuple[float, float]], px: float = 0.0) -> dict:
    """Where the widest section sits, and how far the flank ever widens on the way DOWN.

    **The top rows are skipped, and not to flatter the answer.** The crop's leather does not stop
    on a horizontal line — it cuts each cap on a slant — so the topmost rows of gold are partial
    sections of a full-width piece, and they ramp up over two or three rows on the right cap and
    four on the left. Reading those as the cap getting wider downward is reading the leather's
    boundary, not the cap. The ramp is defined as the leading rows narrower than the maximum by
    more than one source pixel, it is REPORTED rather than quietly dropped, and every widening
    figure below it is over the rows that remain.
    """
    top = max(p[1] for p in prof)
    ramp = 0
    while ramp < len(prof) - 1 and prof[ramp][1] < top - px:
        ramp += 1
    body = prof[ramp:]
    span = body[-1][0] - body[0][0]
    i = max(range(len(body)), key=lambda k: body[k][1])
    rise = max((body[k + 1][1] - body[k][1] for k in range(len(body) - 1)), default=0.0)
    return {"boundaryRampRows": ramp,
            "atDrop": body[i][0], "halfWidth": body[i][1],
            "fractionFromTop": (body[i][0] - body[0][0]) / span if span else 0.0,
            "widensAnywhere": round(rise, 3),
            "widensAnywherePx": round(rise / px, 2) if px else None}


# --- the three pins the arm's length and the cap's length are answerable to --------------------

def gold_extent_in_render(rp, rw, rh, px, axis_x: float) -> tuple[float | None, float | None]:
    """Where the GOLD starts and stops in the render, beside one spinner's axis.

    The like-for-like reading of `measurements.json`'s two gold blobs: the crop's cap tops are the
    topmost GOLD PIXEL of each blob, so the build's must be measured the same way rather than
    derived from the arm's end-cap corner. Same classifier as the crop, on the render's own pixels.
    """
    top = bottom = None
    y = 40.0
    while y >= -200.0:
        x = axis_x - 40.0
        while x <= axis_x + 40.0:
            ix, iy = px(x, y)
            if 0 <= ix < rw and 0 <= iy < rh and classify(*rp[ix, iy]) == "gold":
                if sum(rp[ix, iy]) < 720:
                    top = y if top is None else top
                    bottom = y
                    break
            x += STEP
        y -= 0.5
    return top, bottom


def length_solves(cap_top_render: float, rake_deg: float, length: float, emerge: float) -> dict:
    """Where the crop puts the arm's outer end, and what each candidate LENGTH does about it.

    **The crop pins that end as a POINT, and the point is not on the ray the length slides along.**
    The root and the rake are both locked, so `CONNECTOR_ROOT + L·(cos a, sin a)` is a ray, and the
    crop's own arm end is `(81.925, capTop − emerge)` — its X read four ways off the two gold
    blobs, its Y the height at which the crop's gold first appears, carried down by the same
    emergence offset the build itself has between its end-cap centre and its topmost gold pixel.
    So there is one length that solves X, one that solves Y, and one that minimises the DISTANCE
    to the point; none of them solves both, and the shortfall of the best of them is a property of
    the locked rake rather than of any length. All three are reported with their total misses, so
    which one ships is a choice made in the open.

    `emerge` is analytic, not read off the render: the shoulder's flank crosses the arm's end-cap
    plane at a height `capCentreY + emerge`, and `audit_records.py` re-derives it the same way.
    """
    a = math.radians(rake_deg)
    root_x, root_y = CONNECTOR_ROOT
    l_y = length + (cap_top_render - CROP_CAP_TOP) / abs(math.sin(a))
    l_x = (CROP_CAP_AXIS - root_x) / math.cos(a)
    crop_end = (CROP_CAP_AXIS, CROP_CAP_TOP - emerge)
    v = (crop_end[0] - root_x, crop_end[1] - root_y)
    l_proj = v[0] * math.cos(a) + v[1] * math.sin(a)
    perp = abs(-v[0] * math.sin(a) + v[1] * math.cos(a))

    def total(l: float) -> float:
        end = (root_x + l * math.cos(a), root_y + l * math.sin(a))
        return math.hypot(end[0] - crop_end[0], end[1] - crop_end[1])

    return {
        "emergenceOffsetAnalytic": round(emerge, 3),
        "capTopInRender": round(cap_top_render, 2),
        "capTopAnalytic": round(root_y + length * math.sin(a) + emerge, 2),
        "cropArmEndPoint": [round(crop_end[0], 2), round(crop_end[1], 2)],
        "irreduciblePerpendicularMiss": round(perp, 3),
        "candidates": {
            f"{name}": {"length": round(l, 3),
                        "axis": round(root_x + l * math.cos(a), 3),
                        "capTop": round(root_y + l * math.sin(a) + emerge, 3),
                        "totalMissToCropsArmEnd": round(total(l), 3)}
            for name, l in (("solvesTheAxisX", l_x), ("asBuilt", length),
                            ("projectsTheCropsArmEnd", l_proj), ("solvesTheCapTop", l_y))
        },
    }


# --- the build, out of a render ---------------------------------------------------------------

def built() -> dict:
    """The assembly's own outline around the spinner's axis, per row, from the capture.

    The run reported is the one that CONTAINS the axis, which above the arm's end-cap plane is
    arm-and-cap together and below it is the cap alone. That is the outline a viewer sees, and
    the crossing height is computed from the arm's constants rather than eyeballed.
    """
    src = (V / "createUltimaWeaponV2Model.ts").read_text()

    def c(p):
        return float(re.search(p, src, re.M).group(1))

    root_x = c(r"const CONNECTOR_ROOT: \[number, number\] = \[([-\d.]+),")
    root_y = c(r"const CONNECTOR_ROOT: \[number, number\] = \[[-\d.]+, ([-\d.]+)\]")
    if abs(root_x - CONNECTOR_ROOT[0]) > 1e-6 or abs(root_y - CONNECTOR_ROOT[1]) > 1e-6:
        raise SystemExit("CONNECTOR_ROOT moved; the pin solves in this file assume it is locked")
    rake = math.radians(c(r"const CONNECTOR_ANGLE_DEG = ([-\d.]+)"))
    length = c(r"const CONNECTOR_LENGTH = ([\d.]+)")
    radius = c(r"const CONNECTOR_RADIUS = ([\d.]+)")
    sides = c(r"const CONNECTOR_SIDES = ([\d.]+)")
    clearance = c(r"const SPINNER_SEAT_CLEARANCE = ([\d.]+)")

    down, out = abs(math.sin(rake)), abs(math.cos(rake))
    inradius = radius * math.cos(math.pi / sides)
    seat_r = down * inradius - clearance * (down + out)
    lift = (out * seat_r + clearance) / down
    seat_x = root_x + length * math.cos(rake)
    seat_y = root_y + length * math.sin(rake) + lift
    cap_centre_y = root_y + length * math.sin(rake)
    # The arm's end-cap plane, in the front view: a line through the cap's centre with slope
    # cot(|rake|), so a flank `w` outboard of the spinner's axis leaves the arm below this.
    def cap_plane(w: float) -> float:
        return cap_centre_y + w * out / down

    parts = json.loads((ROOT / "artifacts/ultima-v2/full/parts.json").read_text())
    box = next(p for p in parts["parts"] if p["name"] == "spinnerEndRight")["bounds"]
    top_y, bot_y = box["maxY"] * 100, box["minY"] * 100

    _r, rp, rw, rh, px, scale = render_frame()

    def reach(y: float, sign: int) -> float:
        """How far the ink runs from the spinner's axis before the background starts."""
        d = 0.0
        while d <= 60:
            ix, iy = px(seat_x + sign * d, y)
            if not (0 <= ix < rw and 0 <= iy < rh and sum(rp[ix, iy]) < 720):
                break
            d += STEP
        return d - STEP

    rows = []
    y = top_y
    while y >= bot_y - 2:
        outward, inward = reach(y, +1), reach(y, -1)
        if outward > 0 and inward > 0:
            # The cap is a lathe about the spinner's own axis, so a row it owns ALONE is
            # symmetric about that axis. Where the arm is still in the run the two reaches
            # differ by tens of units, because the arm rakes inboard and the cap does not.
            rows.append({"y": round(y, 1), "outward": round(outward, 2),
                         "inward": round(inward, 2),
                         "halfWidth": round((outward + inward) / 2, 2),
                         "capAlone": abs(outward - inward) <= 1.0})
        y -= ROW

    alone = [r for r in rows if r["capAlone"]]
    out = {
        "seat": {"x": round(seat_x, 3), "y": round(seat_y, 3), "radius": round(seat_r, 3)},
        "armEndCapCentreY": round(cap_centre_y, 3),
        "armCapPlaneAtFullWidth": round(cap_plane(
            c(r"const SPINNER_TOP_RADIUS = ([\d.]+)") * math.cos(math.pi / 6)), 2),
        "unitsPerRenderPixel": round(scale, 4),
        "manifestBoundsY": [round(bot_y, 2), round(top_y, 2)],
        "rows": rows,
        "capAloneFrom": alone[0]["y"] if alone else None,
        "widestOfCapAlone": max(alone, key=lambda r: r["halfWidth"]) if alone else None,
        "widestOverall": max(rows, key=lambda r: r["halfWidth"]) if rows else None,
    }
    if alone:
        w = out["widestOfCapAlone"]
        out["exposedCap"] = {
            "firstExposedRow": alone[0],
            "widensDownwardOver": round(alone[0]["y"] - w["y"], 1),
            "widensDownwardBy": round(w["halfWidth"] - alone[0]["halfWidth"], 2),
            "profile": [[r["y"], r["halfWidth"]] for r in alone],
        }

    # --- the three pins, like for like ------------------------------------------------------
    g_top, g_bot = gold_extent_in_render(rp, rw, rh, px, seat_x)
    out["goldInRender"] = {"top": g_top, "bottom": g_bot,
                           "length": round(g_top - g_bot, 2) if g_top and g_bot else None}
    out["pins"] = {
        "capTop": {"crop": CROP_CAP_TOP, "built": g_top,
                   "miss": round((g_top - CROP_CAP_TOP), 2) if g_top else None},
        "capBottom": {"crop": CROP_CAP_BOTTOM, "built": g_bot,
                      "miss": round((g_bot - CROP_CAP_BOTTOM), 2) if g_bot else None},
        "capLength": {"crop": round(CROP_CAP_TOP - CROP_CAP_BOTTOM, 2),
                      "built": round(g_top - g_bot, 2) if g_top and g_bot else None},
        "axisX": {"crop": CROP_CAP_AXIS, "built": round(seat_x, 3),
                  "miss": round(seat_x - CROP_CAP_AXIS, 3)},
    }
    # The analytic emergence offset: how far ABOVE the arm's end-cap centre the topmost gold sits.
    # The shoulder runs from the seat ring out to the widest ring, and its flank leaves the arm's
    # end-cap plane part way along; that crossing is the topmost gold pixel. Same solve as
    # `audit_records.exposed_widening`, in the one place that needs the height rather than the run.
    top_r = c(r"const SPINNER_TOP_RADIUS = ([\d.]+)")
    drop = clearance                                  # SPINNER_SHOULDER_DROP = SPINNER_SEAT_CLEARANCE
    k = math.cos(math.pi / 6)
    cot = abs(math.cos(rake)) / abs(math.sin(rake))
    f0 = seat_y - (cap_centre_y + k * seat_r * cot)
    f1 = (seat_y - drop) - (cap_centre_y + k * top_r * cot)
    s = 0.0 if f0 <= 0 else (1.0 if f1 >= 0 else f0 / (f0 - f1))
    emerge = k * (seat_r + s * (top_r - seat_r)) * cot
    if g_top is not None:
        out["lengthSolves"] = length_solves(g_top, math.degrees(rake), length, emerge)
    return out


# --- report -----------------------------------------------------------------------------------

def main() -> None:
    px = 1 / PX_PER_UNIT
    cap = caps()
    report: dict = {
        "what": "the crop's two gold spinner caps, and the built cap's own front-view outline",
        "unitsPerSourcePixel": round(px, 3),
        "latheFrontViewFactor": round(math.cos(math.pi / 6), 4),
        "crop": {},
    }
    print(f"one source pixel = {px:.2f} normalized units\n")

    means: dict[str, list[tuple[float, float]]] = {}
    for side in ("right", "left"):
        c = cap[side]
        rows = row_profile(c)
        axis, tilt = axis_profile(c)
        report["crop"][side] = {
            "bbox": {k: round(v, 1) for k, v in c["bbox"].items()},
            "axisTiltFromVerticalDeg": round(tilt, 1),
            "leatherHalfWidthAbove": round(leather_above(c), 2) if leather_above(c) else None,
            "rowProfile": [[d, round(w, 2)] for d, w in rows],
            "axisProfile": [[round(t, 2), round(w, 2)] for t, w in axis],
            "rowWidest": {k: (round(v, 3) if isinstance(v, float) else v)
                          for k, v in widest(rows, px).items()},
            "axisWidest": {k: (round(v, 3) if isinstance(v, float) else v)
                           for k, v in widest(axis, px).items()},
            "rowFit": {k: (round(v, 4) if isinstance(v, float) else v)
                       for k, v in fits(rows[widest(rows, px)["boundaryRampRows"]:]).items()},
        }
        means.setdefault("row", []).append(rows)
        means.setdefault("axis", []).append(axis)
        w = report["crop"][side]
        print(f"{side:5} cap  bbox X {c['bbox']['minX']:7.1f}…{c['bbox']['maxX']:6.1f}  "
              f"Y {c['bbox']['minY']:7.1f}…{c['bbox']['maxY']:6.1f}   "
              f"own axis {tilt:+.1f} deg off vertical")
        for kind in ("row", "axis"):
            k = w[f"{kind}Widest"]
            print(f"      per {kind:4}  widest at {k['fractionFromTop'] * 100:3.0f}% of its length "
                  f"from the top (half-width {k['halfWidth']:5.2f}); largest widening going down "
                  f"{k['widensAnywhere']:+.2f} units = {k['widensAnywherePx']:.2f} px "
                  f"(after {k['boundaryRampRows']} boundary rows)")
        f = w["rowFit"]
        print(f"      straight-edge fit  halfWidth = {f['halfWidth']}   RMS {f['linearRmsUnits']:.2f} "
              f"units ({f['linearRmsUnits'] / px:.2f} px)")
        print(f"      curvature {f['quadratic']:+.5f} — the flank bows "
              f"{'OUT' if f['quadratic'] < 0 else 'IN'} from the straight chord by "
              f"{f['bowFromChordUnits']:.2f} units = {f['bowFromChordUnits'] / px:.2f} source px "
              f"({'inside one pixel: straight' if f['bowFromChordUnits'] < px else 'READABLE CURVE'})")
        print(f"      leather half-width 4 units above the gold: "
              f"{w['leatherHalfWidthAbove']}, cap's own widest {w['rowWidest']['halfWidth']:.2f} "
              f"(ratio {w['rowWidest']['halfWidth'] / w['leatherHalfWidthAbove']:.3f})\n")

    # --- the two caps averaged, each aligned on its own top --------------------------------
    for kind in ("row", "axis"):
        a, b = means[kind]
        n = min(len(a), len(b))
        merged = [[round((a[i][0] + b[i][0]) / 2, 2), round((a[i][1] + b[i][1]) / 2, 2)]
                  for i in range(n)]
        report["crop"][f"mean{kind.capitalize()}Profile"] = merged
        report["crop"][f"mean{kind.capitalize()}Widest"] = {
            k: (round(v, 3) if isinstance(v, float) else v)
            for k, v in widest([(p[0], p[1]) for p in merged], px).items()}
        ramp = report["crop"][f"mean{kind.capitalize()}Widest"]["boundaryRampRows"]
        report["crop"][f"mean{kind.capitalize()}Fit"] = {
            k: (round(v, 4) if isinstance(v, float) else v)
            for k, v in fits([(p[0], p[1]) for p in merged[ramp:]]).items()}

    m = report["crop"]["meanRowFit"]
    mw = report["crop"]["meanRowWidest"]
    prof = report["crop"]["meanRowProfile"]
    body = prof[mw["boundaryRampRows"]:]
    k = math.cos(math.pi / 6)
    print("MEAN of both caps, aligned on each cap's own top, per weapon-local row:")
    print(f"      halfWidth = {m['halfWidth']}   linear RMS {m['linearRmsUnits']:.2f} units "
          f"({m['linearRmsUnits'] / px:.2f} px)   bows out from the chord by "
          f"{m['bowFromChordUnits'] / px:.2f} px")
    print(f"      widest at {mw['fractionFromTop'] * 100:.0f}% from the top; "
          f"largest widening going down {mw['widensAnywhere']:+.2f} units "
          f"= {mw['widensAnywherePx']:.2f} source pixels")
    print(f"      as a LATHE RADIUS (divide by {k:.4f}): top {body[0][1] / k:.2f} at drop "
          f"{body[0][0]:.0f}, bottom {body[-1][1] / k:.2f} at drop {body[-1][0]:.0f}\n")

    # --- and what the build actually shows --------------------------------------------------
    b = built()
    report["built"] = b
    print(f"BUILT  seat ({b['seat']['x']:.3f}, {b['seat']['y']:.3f}) r={b['seat']['radius']:.3f}; "
          f"arm end-cap centre Y {b['armEndCapCentreY']:.3f}")
    print(f"       front-orthographic, {b['unitsPerRenderPixel']:.4f} units per render pixel")
    if b.get("exposedCap"):
        e = b["exposedCap"]
        print(f"       the cap owns the row alone from Y {b['capAloneFrom']:.1f} down; "
              f"its first exposed row is half-width {e['firstExposedRow']['halfWidth']:.2f}")
        print(f"       widest exposed row  Y {b['widestOfCapAlone']['y']:8.1f}  "
              f"half-width {b['widestOfCapAlone']['halfWidth']:.2f}")
        if e["widensDownwardOver"] > 1:
            print(f"       >>> the exposed cap WIDENS DOWNWARD by {e['widensDownwardBy']:+.2f} "
                  f"units over {e['widensDownwardOver']:.1f} units of drop before it narrows — "
                  "a spinning top, not a frustum")
        else:
            print("       the exposed cap narrows from its first exposed row down — a frustum")

    # --- the three pins, and the one length that has to answer to two of them ----------------
    p = b["pins"]
    print("\nPINS   (crop, mean of both caps) vs (build, the same classifier on the render)")
    for what, unit in (("capTop", "gold's topmost row"), ("capBottom", "gold's lowest row")):
        row = p[what]
        if row["built"] is None:
            print(f"       {unit:20} crop {row['crop']:8.2f}   build   n/a")
            continue
        print(f"       {unit:20} crop {row['crop']:8.2f}   build {row['built']:8.2f}   "
              f"miss {row['miss']:+7.2f} = {abs(row['miss']) / px:5.2f} source px")
    print(f"       {'gold cap length':20} crop {p['capLength']['crop']:8.2f}   "
          f"build {p['capLength']['built']:8.2f}")
    print(f"       {'axis |x|':20} crop {p['axisX']['crop']:8.2f}   build {p['axisX']['built']:8.2f}"
          f"   miss {p['axisX']['miss']:+7.2f} = {abs(p['axisX']['miss']) / px:5.2f} source px")
    if "lengthSolves" in b:
        s = b["lengthSolves"]
        print(f"       gold appears {s['emergenceOffsetAnalytic']:.3f} above the arm's end-cap "
              f"centre by construction; analytic cap top {s['capTopAnalytic']:.2f} against the "
              f"render's measured {s['capTopInRender']:.2f}")
        print(f"       the crop's own arm end reads ({s['cropArmEndPoint'][0]}, "
              f"{s['cropArmEndPoint'][1]}); root and rake are LOCKED, so the arm's end slides on "
              f"ONE ray and misses that point by {s['irreduciblePerpendicularMiss']:.2f} units "
              "perpendicular at every length")
        print(f"       {'candidate length':26} {'L':>8} {'axis':>9} {'cap top':>9} {'total miss':>11}")
        for name, v in s["candidates"].items():
            print(f"       {name:26} {v['length']:8.2f} {v['axis']:9.2f} {v['capTop']:9.2f} "
                  f"{v['totalMissToCropsArmEnd']:11.2f}")

    (HERE / "spinner-taper.json").write_text(json.dumps(report, indent=2) + "\n")

    out = HERE / "zoom-spinner"
    for args in ((44, 112, -125, -30, 8, out / "taper-right-8x-grid.png", 10, 10),
                 (-118, -56, -110, -18, 8, out / "taper-left-8x-grid.png", 10, 10),
                 (52, 106, -122, -55, 16, out / "taper-right-16x-grid.png", 10, 5),
                 (-110, -62, -106, -40, 16, out / "taper-left-16x-grid.png", 10, 5)):
        name, size = zoom(*args)
        print(f"wrote zoom-spinner/{name} {size[0]}x{size[1]}")
    # The whole arm-and-cap assembly, artwork beside render in one frame and one set of units.
    # This is the picture the length directive is judged on, so it has to be reproducible.
    name, size = side_by_side(-140, 140, -130, 40, out / "compare-arms-4x.png", 4)
    print(f"wrote zoom-spinner/{name} {size[0]}x{size[1]}")
    print("wrote spec/spinner-taper.json")


if __name__ == "__main__":
    main()
