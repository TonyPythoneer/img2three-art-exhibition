#!/usr/bin/env python3
"""prompt.txt §3.1 — reference triage and the landmark table.

    python3 measure_landmarks.py            # writes landmarks.json, prints the report
    python3 measure_landmarks.py --print     # report only, writes nothing

The real output of this step is a MEASUREMENT UNCERTAINTY. Every "within tolerance"
in §3/§4/§5 and §6's IoU threshold is derived from the cross-view alignment residual
computed here, not guessed.

Everything below is re-derived from the five references. Where a number disagrees
with prompt.txt, this file's number is the one to record (§0.6) — the report prints
both so the disagreement is visible rather than silent.

Pure stdlib + Pillow. Silhouette and colour bands come from refmask.py.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import refmask as R

OUT = Path(__file__).resolve().parent / "landmarks.json"

# prompt.txt's carried-in numbers, quoted here ONLY so the report can diff against
# them. Nothing downstream may read this dict; it is evidence about the prompt, not
# about the figure.
PROMPT_CLAIMS = {
    "topClipRow0": {"front": 6, "back": 4, "left": 4, "right": 6, "more-angle": 0},
    "pixelHeight": {"front": 820, "back": 823, "left": 846, "right": 829},
    "bboxX": {"front": (5, 379), "back": (1, 390), "left": (2, 213), "right": (0, 205)},
    "edgeCols": {"front": (0, 0), "back": (0, 1), "left": (0, 8), "right": (9, 2)},
}


# ------------------------------------------------------------------ utilities ---
def fit_line(pts: list[tuple[float, float]]) -> tuple[float, float, float]:
    """Least squares x = a*y + b over (y, x) samples. Returns (a, b, max_residual)."""
    n = len(pts)
    sy = sum(p[0] for p in pts)
    sx = sum(p[1] for p in pts)
    syy = sum(p[0] * p[0] for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    den = n * syy - sy * sy
    if abs(den) < 1e-9:
        return 0.0, sx / n, 0.0
    a = (n * sxy - sy * sx) / den
    b = (sx - a * sy) / n
    res = max(abs(x - (a * y + b)) for y, x in pts)
    return a, b, res


def two_segment_fit(pts: list[tuple[float, float]], margin: int = 6):
    """Best breakpoint for a two-segment polyline through (y, x) samples.

    Returns (break_y, max_residual, seg1, seg2). §5.7 decides "exactly one corner"
    by comparing this residual against measurementUncertainty, so the objective is
    the MAXIMUM residual, not the mean — a mean would hide a single sharp miss.

    The margin scales with the sample count. A fixed 6 let the break land 6 rows from
    the end, and a 6-row segment fits any slope at all: right.webp's forearm came back
    at -2.2 dx/dy, a 66-degree lean, from a tail nobody would call a segment.
    """
    margin = max(margin, len(pts) // 8)
    best = None
    for i in range(margin, len(pts) - margin):
        a1, b1, r1 = fit_line(pts[: i + 1])
        a2, b2, r2 = fit_line(pts[i:])
        r = max(r1, r2)
        if best is None or r < best[1]:
            best = (pts[i][0], r, (a1, b1), (a2, b2))
    return best


def three_segment_residual(pts: list[tuple[float, float]], margin: int = 6) -> float:
    best = None
    n = len(pts)
    for i in range(margin, n - 2 * margin):
        for j in range(i + margin, n - margin):
            r = max(
                fit_line(pts[: i + 1])[2],
                fit_line(pts[i : j + 1])[2],
                fit_line(pts[j:])[2],
            )
            if best is None or r < best:
                best = r
    return best if best is not None else 0.0


def runs_at(v: R.View, y: int, band: bytearray | None = None) -> list[tuple[int, int]]:
    return v.row_runs(y, band)


def band_runs(v: R.View, band: str, y: int) -> list[tuple[int, int]]:
    return v.row_runs(y, R.band_map(v)[band])


def real_runs(v: R.View, y: int, band: bytearray, frac: float = 0.20):
    """Runs carrying at least `frac` of the row's total width in that band.

    A shadow speck out by the glove is purple too. Measuring the hip as the full
    purple EXTENT of a row let one such speck put the widest hip 77 rows above where
    it is, which then dragged the pant-crease fit with it.
    """
    rs = v.row_runs(y, band)
    if not rs:
        return []
    total = sum(r[1] - r[0] + 1 for r in rs)
    return [r for r in rs if (r[1] - r[0] + 1) >= frac * total]


# --------------------------------------------------------------- triage (§3.1) ---
def triage(v: R.View) -> dict:
    """The three cropping defects, measured rather than assumed."""
    w, h, m = v.w, v.h, v.mask
    top = sum(m[0:w])
    bottom = sum(m[(h - 1) * w : h * w])
    left_rows = [y for y in range(h) if m[y * w]]
    right_rows = [y for y in range(h) if m[y * w + w - 1]]
    top_cols = [x for x in range(w) if m[x]]
    bottom_cols = [x for x in range(w) if m[(h - 1) * w + x]]

    def ranges(vals: list[int]) -> list[list[int]]:
        out: list[list[int]] = []
        for i in vals:
            if out and i == out[-1][1] + 1:
                out[-1][1] = i
            else:
                out.append([i, i])
        return out

    return {
        "size": [w, h],
        "figurePixels": sum(m),
        "enclosedWhitePixels": v.enclosed_white,
        "bbox": {"x0": v.x0, "x1": v.x1, "y0": v.y0, "y1": v.y1},
        "pixelHeight": v.y1 - v.y0 + 1,
        "clipping": {
            "topRowFigurePixels": top,
            "bottomRowFigurePixels": bottom,
            "leftColumnFigurePixels": len(left_rows),
            "rightColumnFigurePixels": len(right_rows),
            "clippedRowRanges": {"left": ranges(left_rows), "right": ranges(right_rows)},
            "clippedColumnRanges": {"top": ranges(top_cols), "bottom": ranges(bottom_cols)},
        },
    }


# ------------------------------------------------- total height (§3.1 handling) ---
def extrapolate_hair_tip(v: R.View, rows: int = 34) -> dict:
    """The tallest spike is cut off. Extend its two straight edges and intersect.

    left.webp only: right.webp is clipped through the hair band as well (§3.1 (2)),
    so its spike has no intact second edge to fit.
    """
    w = v.w
    top_runs = v.row_runs(0)
    assert top_runs, "no figure pixels on row 0 — nothing to extrapolate"
    run = max(top_runs, key=lambda r: r[1] - r[0])
    lo, hi = run
    left_pts: list[tuple[float, float]] = []
    right_pts: list[tuple[float, float]] = []
    for y in range(rows):
        rs = v.row_runs(y)
        # follow the run that overlaps the previous one, so a neighbouring spike
        # entering the crop does not capture the fit
        cand = [r for r in rs if r[1] >= lo - 3 and r[0] <= hi + 3]
        if not cand:
            break
        r = max(cand, key=lambda r: r[1] - r[0])
        lo, hi = r
        left_pts.append((y, r[0]))
        right_pts.append((y, r[1]))
    a1, b1, res1 = fit_line(left_pts)
    a2, b2, res2 = fit_line(right_pts)
    # x = a*y + b for both; apex where they meet
    apex_y = (b2 - b1) / (a1 - a2)
    apex_x = a1 * apex_y + b1
    return {
        "view": v.name,
        "rowsFitted": len(left_pts),
        "leftEdge": {"slope": a1, "intercept": b1, "maxResidualPx": res1},
        "rightEdge": {"slope": a2, "intercept": b2, "maxResidualPx": res2},
        "apexPx": [apex_x, apex_y],
        "clippedAbovePx": -apex_y,
    }


# ---------------------------------------------------------------- landmark set ---
def belt_group(v: R.View) -> dict | None:
    """The olive row-group that lies between the two largest purple row-groups.

    The olive family also contains the boots and the two chest straps, so "the
    highest olive" and "the biggest olive in the torso" are both wrong. What makes
    the belt the belt is that the shirt is immediately above it and the pants
    immediately below.
    """
    purple = R.split_rows(v, "purple")[:2]
    if len(purple) < 2:
        return None
    purple.sort(key=lambda g: g["y0"])
    shirt, pants = purple[0], purple[1]
    for g in R.split_rows(v, "olive"):
        if shirt["y1"] - 8 <= g["y0"] <= pants["y0"] + 8 and g["y1"] >= shirt["y1"]:
            return g
    return None


def leg_outer_edge(v: R.View, y0: int, y1: int, side: str) -> list[tuple[float, float]]:
    """Outer edge of one pant leg, as (y, x) samples. side is 'lo'/'hi' in IMAGE x.

    Taken on the PANTS band, not the silhouette. The taper starts at the widest hip,
    which is above the crotch, and down there the outermost silhouette pixel on a row
    is the glove, not the trouser.
    """
    pm = R.band_map(v)["purple"]
    pts = []
    for y in range(y0, y1 + 1):
        rs = real_runs(v, y, pm)
        if not rs:
            continue
        pts.append((float(y), float(rs[0][0] if side == "lo" else rs[-1][1])))
    return pts


def measure_view(v: R.View) -> dict:
    """Every landmark this view can carry, in the view's own pixels."""
    w, h = v.w, v.h
    bands = R.band_map(v)
    out: dict = {"landmarksPx": {}, "notes": []}
    L = out["landmarksPx"]

    L["sole"] = v.y1

    olive_groups = R.split_rows(v, "olive")
    bottom_olive = max(olive_groups, key=lambda g: g["y1"]) if olive_groups else None
    if bottom_olive:
        # The HIGHEST olive pixel in the boot group is not a cross-view landmark: in a
        # profile the two splayed feet stagger, so it reports the FAR boot's cuff
        # while the front view reports both at once. Measured on left.webp the two
        # cuff tops sit ~38px apart. Recorded, but not cross-validated.
        L["bootCuffTopHighest"] = bottom_olive["y0"]

    bg = belt_group(v)
    if bg:
        L["beltTop"], L["beltBottom"] = bg["y0"], bg["y1"]

    hair_groups = R.split_rows(v, "hair")
    if hair_groups:
        L["hairTopVisible"] = min(g["y0"] for g in hair_groups)

    # crotch notch: the topmost row below the belt where the PANTS split into two
    # runs. Measured on the pants band, not on the silhouette — at hip height the
    # silhouette already carries three runs because both arms are clear of the torso,
    # and a silhouette test locks onto the armpit gap instead of the crotch. Only
    # front-facing views can see it at all; a profile has no notch.
    pants_group = None
    if "beltBottom" in L:
        below = [g for g in R.split_rows(v, "purple") if g["y1"] > L["beltBottom"]]
        if below:
            pants_group = max(below, key=lambda g: g["pixels"])
            # the pant hem — the lowest row the pant leg is still visible on before the
            # boot cuff swallows it (§4[2]). Unlike the olive top this is the SAME
            # physical edge in every view: the nearest cuff's step.
            L["pantHem"] = pants_group["y1"]

    pants = None
    if v.name in ("front", "back", "more-angle") and "beltBottom" in L:
        groups = [g for g in R.split_rows(v, "purple") if g["y1"] > L["beltBottom"]]
        if groups:
            pants = max(groups, key=lambda g: g["pixels"])
            pm = R.band_map(v)["purple"]

            def split_row(y: int) -> bool:
                """Two comparable pants runs with a real gap between them.

                Three things had to be excluded before this stopped firing on the
                belt's own bottom edge: fragmented anti-aliasing rows (require
                exactly two runs), the 1px facet seams down the pant front (require
                a gap), and a stray shadow speck out by the glove (require both runs
                to carry at least a quarter of the row's pants width).
                """
                rs = [r for r in v.row_runs(y, pm) if r[1] - r[0] >= 4]
                if len(rs) != 2 or rs[1][0] - rs[0][1] < 6:
                    return False
                widths = [r[1] - r[0] + 1 for r in rs]
                return min(widths) >= 0.25 * sum(widths)

            for y in range(max(pants["y0"], L["beltBottom"]), pants["y1"] - 12):
                # persistence: a crotch stays open, a seam does not
                if all(split_row(yy) for yy in range(y, y + 12)):
                    L["crotchNotchApex"] = y
                    break

    # widest hip: max PANTS extent between belt bottom and the crotch notch
    if pants and "crotchNotchApex" in L:
        pm = R.band_map(v)["purple"]
        best = None
        for y in range(L["beltBottom"], L["crotchNotchApex"] + 1):
            rs = real_runs(v, y, pm)
            if rs and (best is None or rs[-1][1] - rs[0][0] > best[1]):
                best = (y, rs[-1][1] - rs[0][0])
        if best:
            L["widestHip"] = best[0]
            out["hipWidthPx"] = best[1] + 1

    # neck + chin, from the SILHOUETTE run that contains the head's own axis.
    #
    # Not from the skin band's total width: that sums the face, the neck, and every
    # sliver of forearm and hand that happens to share the row, and the sum then
    # narrows and widens for reasons that have nothing to do with the jaw. The head
    # axis comes from the hair band's bounding box, which is the one part of the head
    # visible in all five views.
    hair_bottom = max((g["y1"] for g in hair_groups), default=v.y0)
    hair_m = bands["hair"]
    hx = [x for x in range(w) if any(hair_m[y * w + x] for y in range(h))]
    head_axis = (hx[0] + hx[-1]) // 2 if hx else (v.x0 + v.x1) // 2
    out["headAxisPx"] = head_axis

    def central_width(y: int) -> int:
        for r in v.row_runs(y):
            if r[0] <= head_axis <= r[1]:
                return r[1] - r[0] + 1
        return 0

    zone = [(y, central_width(y)) for y in range(hair_bottom - 20, min(hair_bottom + 90, h))]
    zone = [(y, n) for y, n in zone if n > 0]
    if zone:
        neck_y, neck_w = min(zone, key=lambda t: t[1])
        L["neckNarrowest"] = neck_y
        out["neckWidthPx"] = neck_w
        # the chin is where the jaw narrows FASTEST into the neck. A width threshold
        # needs a magic multiplier and lands wherever that multiplier is set; the
        # steepest-gradient row is the same point without the magic number.
        grads = [
            (y, central_width(y - 2) - central_width(y + 2))
            for y in range(max(v.y0 + 2, neck_y - 40), neck_y)
        ]
        if grads:
            L["chin"] = max(grads, key=lambda t: t[1])[0]

    # shoulder line: below the neck, the row where the silhouette widens fastest.
    if "neckNarrowest" in L:
        widths = []
        for y in range(L["neckNarrowest"], min(L["neckNarrowest"] + 120, v.y1)):
            e = v.row_extent(y)
            widths.append((y, (e[1] - e[0] + 1) if e else 0))
        grad = [
            (widths[i + 1][0], widths[i + 1][1] - widths[i][1]) for i in range(len(widths) - 1)
        ]
        if grad:
            L["shoulderLine"] = max(grad, key=lambda t: t[1])[0]

    return out


def measure_front_like(v: R.View, out: dict) -> None:
    """Landmarks that need the arms to be separable from the torso (front / back)."""
    L = out["landmarksPx"]
    if "shoulderLine" not in L:
        return
    # The armpit gap is NOT open the whole way down. Measured on front.webp it opens
    # at the shoulder cap (y 264-273), CLOSES again where the deltoid meets the torso
    # (y 276-327), then reopens for good below the armpit. Fitting the arm axis over
    # "every three-run row" therefore splices two disjoint stretches together and
    # returns a slope of 1.67 dx/dy for a nearly vertical arm.
    # down to the crotch, not to the belt: the fists sit BELOW the belt line (§5.8's
    # "forward-broken elbow, fists ahead of the hip"), so stopping at beltTop cuts the
    # fit off above the elbow and the two-segment break lands inside the upper arm.
    lo, hi = L["shoulderLine"], L.get("crotchNotchApex", L.get("beltTop", v.y1))
    tri = [y for y in range(lo, hi) if len(v.row_runs(y)) >= 3]
    if not tri:
        out["notes"].append("no three-run rows: arms never separate from the torso in this view")
        return
    blocks: list[list[int]] = []
    for y in tri:
        if blocks and y == blocks[-1][-1] + 1:
            blocks[-1].append(y)
        else:
            blocks.append([y])
    gap = max(blocks, key=len)
    out["armGapRows"] = [gap[0], gap[-1]]
    out["armGapBlocks"] = [[b[0], b[-1]] for b in blocks]

    # deltoid hexagonal waistline: the deltoid is FUSED to the torso in the silhouette
    # (that is why the gap closes above it), so it has no arm run of its own to
    # measure. What it does have is the figure's widest row — the hexagon's waist is
    # the shoulder's maximum lateral extent.
    best = None
    for y in range(lo, gap[0]):
        e = v.row_extent(y)
        if e and (best is None or e[1] - e[0] > best[1]):
            best = (y, e[1] - e[0])
    if best:
        L["deltoidWaistline"] = best[0]
        out["shoulderExtentPx"] = best[1] + 1
    # arm medial axis, both sides, as a two-segment polyline -> elbow break.
    # Stop at the glove. A row centroid is a fair medial axis for a limb, but the
    # glove is a wide block whose run collapses over its last rows, and those rows
    # drag the lower segment's slope to -2.4 dx/dy (67 degrees) for a forearm that
    # reads as near-vertical in the reference.
    black = R.split_rows(v, "black")
    glove_top = max(black, key=lambda g: g["pixels"])["y0"] if black else gap[-1]
    fit_rows = [y for y in gap if y < glove_top] or gap
    out["armFitRows"] = [fit_rows[0], fit_rows[-1]]
    # thinnest arm row: §5.8's "the upper arm is thinner than both its neighbours".
    # Over fit_rows, not over the whole gap — the last rows of the gap are the glove
    # tapering out of frame, which is always the narrowest thing on the arm.
    thin = min(
        ((y, min(r[1] - r[0] + 1 for r in (v.row_runs(y)[0], v.row_runs(y)[-1]))) for y in fit_rows),
        key=lambda t: t[1],
    )
    L["upperArmNarrowest"] = thin[0]
    out["upperArmWidthPx"] = thin[1]
    for idx, tag in ((0, "imageLeftArm"), (-1, "imageRightArm")):
        pts = []
        for y in fit_rows:
            rs = v.row_runs(y)
            r = rs[idx]
            pts.append((float(y), (r[0] + r[1]) / 2.0))
        if len(pts) >= 20:
            br = two_segment_fit(pts)
            if br:
                out[tag] = {
                    "breakY": br[0],
                    "maxResidualPx": br[1],
                    "upperSlopeDxDy": br[2][0],
                    "lowerSlopeDxDy": br[3][0],
                }


def measure_pant_crease(v: R.View, out: dict) -> None:
    """§5.7's corner, measured on the reference so the gate has something to hit."""
    L = out["landmarksPx"]
    if "widestHip" not in L or "pantHem" not in L:
        return
    # from the WIDEST HIP, not from the crotch. §4's "straight taper, hard corner,
    # near-vertical below it" describes the whole outer line of the trouser, and the
    # taper begins where the pants are widest — 126 rows above the crotch notch in
    # front.webp. Starting at the crotch fits two segments to the vertical part alone
    # and puts the corner 45px too low.
    y0, y1 = L["widestHip"], L["pantHem"] - 4
    if y1 - y0 < 40:
        return
    res: dict = {}
    for side in ("lo", "hi"):
        pts = leg_outer_edge(v, y0, y1, side)
        br = two_segment_fit(pts)
        if not br:
            continue
        r3 = three_segment_residual(pts)
        res[side] = {
            "breakY": br[0],
            "twoSegmentMaxResidualPx": br[1],
            "threeSegmentMaxResidualPx": r3,
            "taperSlopeDxDy": br[2][0],
            "tubeSlopeDxDy": br[3][0],
        }
    if res:
        out["pantCrease"] = res
        L["pantLegCrease"] = sum(r["breakY"] for r in res.values()) / len(res)


def measure_hair_thickness(v: R.View) -> dict | None:
    """§3.1: normal distance from the exposed face plane to the outer hair silhouette.

    In a profile view the face plane is vertical, so its normal is horizontal and the
    measurement is a horizontal distance on rows that carry both bands. Reported as a
    distribution, not a single number: the spread is what tells you whether guess-list
    item 5 ("is the occiput thicker?") is even answerable from this view.
    """
    skin, hair = R.band_map(v)["skin"], R.band_map(v)["hair"]
    facing = -1 if v.name == "left" else 1  # left.webp: the figure faces image -x
    samples = []
    for y in range(v.h):
        sr = [r for r in v.row_runs(y, skin) if r[1] - r[0] >= 8]
        hr = v.row_runs(y, hair)
        if not sr or not hr:
            continue
        # the face plane is the front edge of the LARGEST skin run on the row.
        # Taking the leftmost skin pixel instead picks up the slivers of cheek
        # showing BETWEEN two fringe spikes and returns a negative thickness.
        face_run = max(sr, key=lambda r: r[1] - r[0])
        if facing < 0:
            face = face_run[0]
            ahead = [r[0] for r in hr if r[0] < face]
            d = face - min(ahead) if ahead else None
        else:
            face = face_run[1]
            ahead = [r[1] for r in hr if r[1] > face]
            d = max(ahead) - face if ahead else None
        if d and d > 0:
            samples.append((y, d))
    if not samples:
        return None
    ds = sorted(s[1] for s in samples)
    return {
        "view": v.name,
        "measures": "fringe depth: face plane -> outermost hair silhouette ahead of it",
        "rowRange": [samples[0][0], samples[-1][0]],
        "rows": len(ds),
        "medianPx": ds[len(ds) // 2],
        "p10Px": ds[len(ds) // 10],
        "p90Px": ds[len(ds) * 9 // 10],
        "minPx": ds[0],
        "maxPx": ds[-1],
    }


# ------------------------------------------------------------------------ main ---
def main(argv: list[str]) -> int:
    write = "--print" not in argv
    views = {name: R.load(name) for name in R.VIEWS}
    doc: dict = {
        "schema": "ff7-cloud-strife-landmarks/1",
        "generatedBy": "artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/measure_landmarks.py",
        "silhouetteRule": "figure = (unreachable by 4-neighbour flood fill from the border) AND (255 - min(r,g,b) > 18)",
        "tol": R.TOL,
        "views": {},
    }

    for name, v in views.items():
        d = triage(v)
        d.update(measure_view(v))
        if name in ("front", "back", "more-angle"):
            measure_front_like(v, d)
        measure_pant_crease(v, d)
        doc["views"][name] = d

    # ---- total height, from left.webp's clipped spike ----
    tip = extrapolate_hair_tip(views["left"])
    doc["totalHeight"] = tip
    left = views["left"]
    total_px = left.y1 - tip["apexPx"][1]
    tip["totalHeightPx"] = total_px
    tip["measuredPixelHeight"] = left.y1 - left.y0 + 1

    # ---- cross-view scale: two candidate anchors, both measured ----
    anchors = {}
    for pair in (("sole", "chin"), ("sole", "beltBottom")):
        key = f"{pair[0]}->{pair[1]}"
        spans = {}
        for name, d in doc["views"].items():
            L = d["landmarksPx"]
            if pair[0] in L and pair[1] in L:
                spans[name] = L[pair[0]] - L[pair[1]]
        anchors[key] = {"spanPx": spans, "measurableIn": sorted(spans)}
    doc["anchorCandidates"] = anchors

    # normalized units: 1.000 = left.webp's sole -> extrapolated hair tip
    def normalize(anchor_key: str) -> dict:
        spans = anchors[anchor_key]["spanPx"]
        if "left" not in spans:
            return {}
        span_norm = spans["left"] / total_px
        per_view = {}
        for name, d in doc["views"].items():
            if name not in spans:
                continue
            sole = d["landmarksPx"]["sole"]
            k = span_norm / spans[name]
            per_view[name] = {
                lm: (sole - y) * k for lm, y in d["landmarksPx"].items() if lm != "sole"
            }
            per_view[name]["sole"] = 0.0
        # Residual: the spread of the CROSS-VALIDATION SET only.
        #
        # Not "every landmark". Three kinds have to be excluded or the residual stops
        # measuring alignment and starts measuring something else:
        #   - the anchor's own two endpoints, which agree by construction;
        #   - anything derived from a CLIPPED extreme (hairTopVisible), where the
        #     views disagree because they are cut by different amounts, not because
        #     they are misaligned;
        #   - anything a view cannot see (the crotch notch in a profile).
        # What is left is four landmarks that every view measures independently, by a
        # method that does not know about the anchor.
        # more-angle is excluded from the residual as well: it is a lit three-quarter
        # PERSPECTIVE shot, so a height ratio measured there is not comparable with an
        # orthographic one, and its silhouette additionally swallows the white base
        # plate the figure stands on (2968 enclosed-white px against 0-274 elsewhere).
        cross_set = ("pantHem", "beltTop", "shoulderLine", "neckNarrowest")
        spread: dict[str, list[float]] = {}
        for name, lms in per_view.items():
            if name not in R.ORTHO:
                continue
            for lm, val in lms.items():
                spread.setdefault(lm, []).append(val)
        residuals = {lm: max(v) - min(v) for lm, v in spread.items() if len(v) >= 2}
        cross = {
            lm: r
            for lm, r in residuals.items()
            if lm in cross_set and lm not in anchor_key.split("->")
        }
        # Two statistics, because they answer different questions and a later gate
        # should be able to say which one it is using. The MAX spread is the
        # conservative tolerance §3.1 asks for; the RMS deviation about the median
        # says how much of that max is one outlier view.
        devs = []
        for lm in cross:
            vals = sorted(spread[lm])
            med = vals[len(vals) // 2]
            devs += [abs(x - med) for x in vals]
        rms = (sum(d * d for d in devs) / len(devs)) ** 0.5 if devs else 0.0
        return {
            "anchor": anchor_key,
            "spanNormalized": span_norm,
            "perView": per_view,
            "landmarkSpread": residuals,
            "crossValidationSet": sorted(cross),
            "crossValidationViews": sorted(n for n in per_view if n in R.ORTHO),
            "measurementUncertainty": max(cross.values()) if cross else 0.0,
            "measurementUncertaintyRms": rms,
            "worstLandmark": max(cross, key=lambda k: cross[k]) if cross else None,
        }

    doc["normalization"] = {k: normalize(k) for k in anchors}

    # adopt the anchor with the smaller residual — §0.6: measured, not assumed
    usable = {k: n for k, n in doc["normalization"].items() if n}
    adopted = min(usable, key=lambda k: usable[k]["measurementUncertainty"])
    doc["adoptedAnchor"] = adopted
    doc["measurementUncertainty"] = usable[adopted]["measurementUncertainty"]
    N = usable[adopted]["perView"]

    # ---- widths, depths, angles, hair thickness in adopted units ----
    def unit(name: str) -> float:
        """pixels per normalized unit in view `name`."""
        spans = anchors[adopted]["spanPx"]
        return spans[name] / usable[adopted]["spanNormalized"]

    dims: dict = {}
    fv, bv, lv, rv = views["front"], views["back"], views["left"], views["right"]
    fd, ld, rd = doc["views"]["front"], doc["views"]["left"], doc["views"]["right"]

    if "hipWidthPx" in fd:
        dims["maxHipWidth"] = fd["hipWidthPx"] / unit("front")
    # Hip DEPTH has to be read in profile, but a profile has no crotch notch to find
    # the widest hip with. Carry the height across instead: take front.webp's
    # widestHip in NORMALIZED units and convert it into each profile's own pixel row.
    hip_n = N.get("front", {}).get("widestHip") if (N := usable[adopted]["perView"]) else None
    #
    # Both profile depths are measured on the PURPLE band, not on the silhouette. In
    # profile the forearm and the glove stand in FRONT of the body, so a silhouette
    # depth at chest height is arm-plus-torso: it read 0.155 against a hip of 0.138
    # and failed §3.1's self-check A for a reason that has nothing to do with the hip.
    #
    # Scanned over a band and then MAXIMISED across the two profiles, because the
    # glove hangs in front of the hip and hides part of the pants: at the single row
    # the hip height maps to, left.webp reports 0.054 and right.webp 0.135 for the
    # same measurement. Occlusion can only remove purple, never add it, so the larger
    # reading is the one that saw the whole hip.
    if hip_n is not None:
        for vv, key in ((lv, "left"), (rv, "right")):
            pm = R.band_map(vv)["purple"]
            centre = vv.y1 - hip_n * unit(key)
            span = 0.03 * unit(key)
            best = None
            for y in range(int(centre - span), int(centre + span) + 1):
                e = vv.row_extent(y, pm)
                if e and (best is None or e[1] - e[0] > best[1]):
                    best = (y, e[1] - e[0])
            if best:
                dims.setdefault("maxHipDepthPerView", {})[key] = (best[1] + 1) / unit(key)
                dims.setdefault("maxHipDepthRow", {})[key] = best[0]
        if dims.get("maxHipDepthPerView"):
            dims["maxHipDepth"] = max(dims["maxHipDepthPerView"].values())
    if "shoulderLine" in fd["landmarksPx"] and "deltoidWaistline" in fd["landmarksPx"]:
        best = 0
        for y in range(fd["landmarksPx"]["shoulderLine"], fd["landmarksPx"]["deltoidWaistline"] + 1):
            e = fv.row_extent(y)
            if e:
                best = max(best, e[1] - e[0] + 1)
        dims["shoulderWidth"] = best / unit("front")
    # chest slab width, on the SHIRT band, between the shoulder line and the belt.
    # Kept separate from shoulderWidth because §3.1's self-check A turns on which of
    # the two "the shoulders" means, and the two differ by 0.09 of figure height.
    if "beltTop" in fd["landmarksPx"] and "deltoidWaistline" in fd["landmarksPx"]:
        pm = R.band_map(fv)["purple"]
        best = 0
        for y in range(fd["landmarksPx"]["deltoidWaistline"], fd["landmarksPx"]["beltTop"] + 1):
            rs = real_runs(fv, y, pm)
            if rs:
                best = max(best, rs[-1][1] - rs[0][0] + 1)
        dims["chestWidth"] = best / unit("front")
    for vv, key in ((lv, "left"), (rv, "right")):
        dd = doc["views"][key]["landmarksPx"]
        if "beltTop" in dd and "shoulderLine" in dd:
            best = 0
            pm = R.band_map(vv)["purple"]
            for y in range(dd["shoulderLine"], dd["beltTop"] + 1):
                e = vv.row_extent(y, pm)
                if e:
                    best = max(best, e[1] - e[0] + 1)
            dims.setdefault("torsoDepth", {})[key] = best / unit(key)
    if "neckWidthPx" in fd:
        dims["neckWidth"] = fd["neckWidthPx"] / unit("front")
    # head + hair-cap width from back.webp: per row take only the run that contains the
    # figure axis, which excludes the detached spikes without naming them.
    bd = doc["views"]["back"]["landmarksPx"]
    if "chin" in bd or "neckNarrowest" in bd:
        axis = (bv.x0 + bv.x1) // 2
        hair = R.band_map(bv)["hair"]
        best = 0
        crown = None
        for y in range(bv.y0, bd.get("neckNarrowest", bv.y1)):
            for r in bv.row_runs(y, hair):
                if r[0] <= axis <= r[1]:
                    wdt = r[1] - r[0] + 1
                    if wdt > best:
                        best = wdt
                    if crown is None and wdt > 0:
                        crown = y
        dims["hairCapWidth"] = best / unit("back")
        # crown = topmost row whose central hair run is at least half the cap width
        for y in range(bv.y0, bd.get("neckNarrowest", bv.y1)):
            for r in bv.row_runs(y, hair):
                if r[0] <= axis <= r[1] and (r[1] - r[0] + 1) >= 0.5 * best:
                    doc["views"]["back"]["landmarksPx"]["hairCapCrown"] = y
                    break
            else:
                continue
            break
    # feet — measured on the WIDEST sole row, not on an arbitrary row near the
    # bottom. The last two rows of the frame catch the chamfer, not the slab.
    for vv, key in ((fv, "front"), (lv, "left"), (rv, "right")):
        dd = doc["views"][key]["landmarksPx"]
        if "bootCuffTopHighest" not in dd:
            continue
        rows = range(dd["bootCuffTopHighest"], vv.y1 + 1)
        if key == "front":
            best = max(
                (vv.row_runs(y) for y in rows),
                key=lambda rs: sum(r[1] - r[0] + 1 for r in rs),
            )
            dims["footWidthEach"] = [(r[1] - r[0] + 1) / unit("front") for r in best]
        else:
            best_y = max(rows, key=lambda y: (lambda e: e[1] - e[0] if e else -1)(vv.row_extent(y)))
            e = vv.row_extent(best_y)
            dims.setdefault("footLength", {})[key] = (e[1] - e[0] + 1) / unit(key)
    # straight pant tube width, front view, midway between crease and boot cuff
    if "pantLegCrease" in fd["landmarksPx"] and "pantHem" in fd["landmarksPx"]:
        y = int((fd["landmarksPx"]["pantLegCrease"] + fd["landmarksPx"]["pantHem"]) / 2)
        rs = fv.row_runs(y)
        dims["straightPantTubeWidth"] = [(r[1] - r[0] + 1) / unit("front") for r in rs]
    doc["dimensions"] = dims

    # ---- 3D pose angles from the two orthogonal projections ----
    # A front view yields a PROJECTED angle. dx/dy from the front and dz/dy from the
    # side give the real direction vector; the angle comes from the vector.
    #
    # §1.2 fixes the frames. front.webp: the figure faces the camera, so image +x IS
    # model +X and the figure's LEFT arm is the IMAGE-RIGHT run. left.webp: the figure
    # faces image -x, so model +Z = -image x; right.webp is the other way round.
    # Pairing front's image-LEFT arm with left.webp would splice the figure's right
    # arm onto its left arm's depth.
    angles: dict = {}
    fl = fd.get("imageRightArm")   # figure's LEFT
    side_arm = {}
    for key, vv in (("left", lv), ("right", rv)):
        dd = doc["views"][key]["landmarksPx"]
        if "shoulderLine" not in dd:
            continue
        black = R.split_rows(vv, "black")
        glove_top = max(black, key=lambda g: g["pixels"])["y0"] if black else vv.y1
        lo_y, hi_y = dd["shoulderLine"], glove_top
        # the arm's skin group is the one that OVERLAPS shoulder->glove most, not the
        # one that starts below the shoulder line: in right.webp the arm's skin group
        # opens at y=266, 24px ABOVE the detected shoulder line at 290, so a
        # "starts below the shoulder" test rejected the only arm in the view.
        cand = [
            (min(g["y1"], hi_y) - max(g["y0"], lo_y), g)
            for g in R.split_rows(vv, "skin")
        ]
        cand = [c for c in cand if c[0] >= 40]
        if not cand:
            continue
        arm = max(cand, key=lambda c: c[0])[1]
        pts = []
        for y in range(max(arm["y0"], lo_y), min(arm["y1"], hi_y) + 1):
            rs = vv.row_runs(y, R.band_map(vv)["skin"])
            if rs:
                r = max(rs, key=lambda r: r[1] - r[0])
                pts.append((float(y), (r[0] + r[1]) / 2.0))
        if len(pts) >= 20:
            br = two_segment_fit(pts)
            if br:
                fwd = -1.0 if key == "left" else 1.0   # model +Z in this view's image x
                side_arm[key] = {
                    "breakY": br[0],
                    "maxResidualPx": br[1],
                    "upperSlopeDzDy": br[2][0] * fwd,
                    "lowerSlopeDzDy": br[3][0] * fwd,
                    "imageXtoModelZ": fwd,
                }
    angles["sideArmFit"] = side_arm

    def combine(dxdy: float, dzdy: float, label: str) -> dict:
        # y points DOWN in image space; the limb runs downward, so take -y as the axis
        vec = (dxdy, -1.0, dzdy)
        n = math.sqrt(sum(c * c for c in vec))
        return {
            "part": label,
            "directionXYZimage": [c / n for c in vec],
            "abductionDeg": math.degrees(math.atan2(abs(dxdy), 1.0)),
            "forwardLeanDeg": math.degrees(math.atan2(abs(dzdy), 1.0)),
            "totalTiltFromVerticalDeg": math.degrees(math.atan2(math.hypot(dxdy, dzdy), 1.0)),
        }

    for tag, front_key, side_key in (
        ("figureLeft", "imageRightArm", "left"),
        ("figureRight", "imageLeftArm", "right"),
    ):
        fa, sa = fd.get(front_key), side_arm.get(side_key)
        if not fa or not sa:
            continue
        angles[tag + "UpperArm"] = combine(
            fa["upperSlopeDxDy"], sa["upperSlopeDzDy"], f"upperArm({tag})"
        )
        angles[tag + "ForeArm"] = combine(
            fa["lowerSlopeDxDy"], sa["lowerSlopeDzDy"], f"foreArm({tag})"
        )
        u = angles[tag + "UpperArm"]["directionXYZimage"]
        f = angles[tag + "ForeArm"]["directionXYZimage"]
        dot = max(-1.0, min(1.0, sum(a * b for a, b in zip(u, f))))
        angles[tag + "ElbowBreakDeg"] = math.degrees(math.acos(dot))
        angles[tag + "ElbowRowPx"] = {"front": fa["breakY"], side_key: sa["breakY"]}
    # foot splay: apparent length in the front view vs in the side view
    if "footWidthEach" in dims and "footLength" in dims:
        for key in dims["footLength"]:
            lat = max(dims["footWidthEach"])
            fwd = dims["footLength"][key]
            angles.setdefault("footSplayDeg", {})[key] = math.degrees(math.atan2(lat, fwd))
    doc["poseAngles"] = angles

    # ---- hair thickness ----
    ht = {k: measure_hair_thickness(views[k]) for k in ("left", "right")}
    for k, d in ht.items():
        if d:
            d["medianNormalized"] = d["medianPx"] / unit(k)
    doc["hairThickness"] = ht

    # ---- self checks ----
    checks = {}
    sw = dims.get("shoulderWidth")
    hw = dims.get("maxHipWidth")
    hdm = dims.get("maxHipDepth")
    td = dims.get("torsoDepth", {})
    mu = doc["measurementUncertainty"]

    def verdict(a: float, b: float, want_greater: bool) -> str:
        """PASS / FAIL / INDETERMINATE against the measured uncertainty.

        A check that fails by less than measurementUncertainty has not been failed —
        it has not been decided. §12 makes the same distinction for hard stops: only a
        gap LARGER than the uncertainty is a contradiction of the prompt.
        """
        if abs(a - b) < mu:
            return "INDETERMINATE"
        return "PASS" if ((a > b) == want_greater) else "FAIL"

    cw = dims.get("chestWidth")
    if sw and hw:
        checks["A_hipWiderThanShoulderLine"] = {
            "hipWidth": hw, "shoulderWidth": sw, "margin": hw - sw,
            "verdict": verdict(hw, sw, True),
        }
    if cw and hw:
        checks["A1_hipWiderThanChestSlab"] = {
            "hipWidth": hw, "chestWidth": cw, "margin": hw - cw,
            "verdict": verdict(hw, cw, True),
        }
    # B — in profile the hip reads as a front/back-symmetric KITE, not a cylinder and
    # not a skirt. Decidable form: each side of the pants outline between the belt and
    # the crotch has ONE apex (a two-segment fit clearly beats one segment), and the
    # two apices sit at the same height.
    for key, vv in (("left", lv), ("right", rv)):
        dd = doc["views"][key]["landmarksPx"]
        hip_row = dims.get("maxHipDepthRow", {}).get(key)
        if "beltBottom" not in dd or hip_row is None:
            continue
        y0, y1 = dd["beltBottom"], hip_row + int(0.06 * unit(key))
        front_pts = leg_outer_edge(vv, y0, y1, "lo")
        back_pts = leg_outer_edge(vv, y0, y1, "hi")
        if len(front_pts) < 30 or len(back_pts) < 30:
            continue
        bf, bb = two_segment_fit(front_pts), two_segment_fit(back_pts)
        if not bf or not bb:
            continue
        one_f, one_b = fit_line(front_pts)[2], fit_line(back_pts)[2]
        apex_gap = abs(bf[0] - bb[0]) / unit(key)
        corner = bf[1] < 0.5 * one_f and bb[1] < 0.5 * one_b
        # A two-segment fit whose own residual is 20-57px is not describing a
        # quadrilateral, it is describing an outline with a hole in it: the black
        # glove hangs in FRONT of the hip in both profiles and eats the pants' front
        # edge over exactly the rows the kite apex would be on. That is an
        # unmeasurable, not a failure — say so instead of scoring it.
        occluded = max(bf[1], bb[1]) > 0.02 * unit(key)
        checks[f"B_hipKite_{key}"] = {
            "frontApexRow": bf[0], "backApexRow": bb[0],
            "apexHeightGap": apex_gap,
            "twoSegmentResidualPx": [bf[1], bb[1]],
            "oneSegmentResidualPx": [one_f, one_b],
            "outlineCleanThresholdPx": 0.02 * unit(key),
            "cornerIsReal": corner,
            "margin": mu - apex_gap,
            "verdict": (
                "INDETERMINATE(glove occludes the hip outline)"
                if occluded
                else ("PASS" if apex_gap < mu and corner else "FAIL")
            ),
        }

    if hdm and td:
        tdm = max(td.values())
        checks["A2_hipDeeperThanShoulders"] = {
            "hipDepth": hdm, "shoulderDepth": tdm, "margin": hdm - tdm,
            "verdict": verdict(hdm, tdm, True),
        }
        if sw:
            checks["C_torsoIsASlab"] = {
                "torsoDepth": tdm, "halfShoulderWidth": sw / 2,
                "margin": sw / 2 - tdm,
                "verdict": verdict(tdm, sw / 2, False),
            }
    doc["selfChecks"] = checks

    # ---- prompt diff (§0.6) ----
    diffs = []
    for name, d in doc["views"].items():
        c = d["clipping"]
        want = PROMPT_CLAIMS["topClipRow0"].get(name)
        if want is not None and want != c["topRowFigurePixels"]:
            diffs.append(f"{name}: row-0 figure px prompt={want} measured={c['topRowFigurePixels']}")
        want = PROMPT_CLAIMS["pixelHeight"].get(name)
        if want is not None and want != d["pixelHeight"]:
            diffs.append(f"{name}: pixel height prompt={want} measured={d['pixelHeight']}")
        want = PROMPT_CLAIMS["bboxX"].get(name)
        if want is not None and list(want) != [d["bbox"]["x0"], d["bbox"]["x1"]]:
            diffs.append(f"{name}: bbox x prompt={want} measured=({d['bbox']['x0']},{d['bbox']['x1']})")
        want = PROMPT_CLAIMS["edgeCols"].get(name)
        got = (c["leftColumnFigurePixels"], c["rightColumnFigurePixels"])
        if want is not None and tuple(want) != got:
            diffs.append(f"{name}: edge column figure px prompt={want} measured={got}")
    for name, c in doc["selfChecks"].items():
        if c["verdict"] == "FAIL":
            diffs.append(f"self-check {name} FAILS by {abs(c['margin']):.4f} (> uncertainty)")
    doc["promptDisagreements"] = diffs

    if write:
        OUT.write_text(json.dumps(doc, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    report(doc)
    return 0


def report(doc: dict) -> None:
    print("=== §3.1 reference triage ===")
    for name, d in doc["views"].items():
        c = d["clipping"]
        print(
            f"{name:11s} {d['size'][0]}x{d['size'][1]}  figH={d['pixelHeight']:4d}  "
            f"bbox x{d['bbox']['x0']}..{d['bbox']['x1']}  "
            f"edge px T{c['topRowFigurePixels']} B{c['bottomRowFigurePixels']} "
            f"L{c['leftColumnFigurePixels']} R{c['rightColumnFigurePixels']}  "
            f"enclosedWhite={d['enclosedWhitePixels']}"
        )
    t = doc["totalHeight"]
    print(
        f"\nhair tip (extrapolated on {t['view']} from {t['rowsFitted']} rows): "
        f"apex=({t['apexPx'][0]:.1f}, {t['apexPx'][1]:.1f})  clipped {t['clippedAbovePx']:.1f}px "
        f"above frame;  edge fit max residual L={t['leftEdge']['maxResidualPx']:.2f}px "
        f"R={t['rightEdge']['maxResidualPx']:.2f}px"
    )
    print(f"total height = {t['totalHeightPx']:.1f}px in left.webp (= 1.000)")

    print("\n=== anchor candidates ===")
    for k, a in doc["anchorCandidates"].items():
        n = doc["normalization"].get(k) or {}
        u = n.get("measurementUncertainty")
        print(
            f"{k:20s} measurable in {a['measurableIn']}  "
            f"residual={u if u is None else f'{u:.5f}'}  worst={n.get('worstLandmark')}"
        )
    print(f"ADOPTED: {doc['adoptedAnchor']}   measurementUncertainty = {doc['measurementUncertainty']:.5f}")

    print("\n=== landmarks (normalized, 0 = sole, 1.000 = hair tip) ===")
    per = doc["normalization"][doc["adoptedAnchor"]]["perView"]
    keys: list[str] = []
    for lms in per.values():
        for k in lms:
            if k not in keys:
                keys.append(k)
    print(f"{'landmark':20s} " + "".join(f"{n:>12s}" for n in per))
    for k in keys:
        row = "".join(f"{per[n][k]:12.4f}" if k in per[n] else f"{'-':>12s}" for n in per)
        print(f"{k:20s} {row}")

    print("\n=== dimensions (normalized) ===")
    print(json.dumps(doc["dimensions"], indent=2))
    print("\n=== pose angles ===")
    print(json.dumps(doc["poseAngles"], indent=2))
    print("\n=== hair thickness ===")
    print(json.dumps(doc["hairThickness"], indent=2))
    print("\n=== self checks ===")
    for k, c in doc["selfChecks"].items():
        print(f"  {k}: {c['verdict']:14s} margin={c['margin']:+.4f}  {c}")
    print("\n=== disagreements with prompt.txt (§0.6 — the script wins) ===")
    print("\n".join("  " + d for d in doc["promptDisagreements"]) or "  none")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
