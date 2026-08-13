#!/usr/bin/env python3
"""Measure the sole slab (§4[1], shape code S-01) and append it to landmarks.json.

§4 says a part factory may only read landmarks.json, so this writes into that file
under `parts.sole` rather than opening a second artefact next to it.

    python3 measure_sole.py            # rewrites spec/landmarks.json in place

WHAT IS AND IS NOT RECOVERABLE FROM FOUR ORTHOGRAPHIC VIEWS
-----------------------------------------------------------
The slab's axis-aligned bounding box in model space IS recoverable, because each
orthographic view hands over one axis directly:

    A  lateral extent (model X)   front.webp / back.webp, ground row, per foot
    B  fore-aft extent (model Z)  left.webp / right.webp, ground row
    T  thickness     (model Y)    the plate's run height at its forward extreme

The slab's PLAN OUTLINE is not. A trapezoid of length L and width W rotated by a splay
angle theta has

    A = L sin(theta) + W cos(theta)
    B = L cos(theta) + W sin(theta)

which is two equations in three unknowns, and near theta = 45 degrees the 2x2 system
is singular anyway (det = -cos 2*theta). Since there is no top-down reference, the
aspect ratio r = L/W is ADOPTED, not measured, and theta follows from the measured A/B:

    A/B = (r sin + cos) / (r cos + sin)   ->   solve for theta by bisection

That adoption is a guess-list item. It is also invisible to every gate except the
three-quarter orbit view (§5.2): A, B and T alone fix all four orthographic
silhouettes, so the orbit render is the thing that can falsify r.

Note what this replaces. landmarks.json's existing poseAngles.footSplayDeg is
atan2(lateral, foreAft) = atan2(A, B), which is the angle of the bounding box's
diagonal, not the splay. For a zero-width foot the two coincide; for a real one
atan2(A, B) is pulled toward 45 degrees, so the true splay is always FURTHER from 45
than that number. Both are recorded; the derived one is the one the factory reads.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import refmask as R

HERE = Path(__file__).resolve().parent

# Adopted shoe aspect ratio L/W for the sole slab. Guess-list item: the plan outline is
# unobservable from four orthographic views (see the module docstring). 2.4 is the
# chunky-toy-boot end of the 2.2-2.6 range; the orbit render is what can falsify it.
ADOPTED_ASPECT = 2.4

# Toe end is narrower than the heel end (§4[1] "wide at the heel end, narrow at the toe
# end"). Also unobservable in plan; adopted, and also falsifiable only by the orbit view.
ADOPTED_TOE_TAPER = 0.72

# Blunt chamfer at both ends, as a fraction of the slab thickness. Read off
# front.webp x5..165 y700..821 at 8x: the corner cut reads as its own facet roughly one
# third of the plate's edge height.
ADOPTED_END_CHAMFER = 0.34


def unit(lm: dict, view: str) -> float:
    """Pixels per normalized unit for a view, from the adopted sole->chin anchor."""
    px = lm["views"][view]["landmarksPx"]
    span = lm["normalization"]["sole->chin"]["spanNormalized"]
    return (px["sole"] - px["chin"]) / span


def boot_band(lm: dict, v: R.View) -> tuple[int, int]:
    """Rows from the ground up to the boot-cuff top, i.e. everything below the pants."""
    top = int(lm["views"][v.name]["landmarksPx"]["bootCuffTopHighest"])
    return top, v.y1


def slab_profile(lm: dict, v: R.View) -> dict:
    """Total silhouette extent per row across the boot band, and the sole's own step.

    The last row is NOT the slab's full section: the plate's bottom edge is a blunt
    chamfer, so the very lowest row carries only the chamfer's tip — measuring there
    returns 4 px of foot and a nonsense answer. The slab's section is the band MAXIMUM.

    soleTop is then the row where that maximum collapses to the boot cuff, which is a
    real step: §4[1] says the sole's top face emerges from under the cuff as a clean
    ledge all round, so the slab is wider than the cuff in every direction and the
    transition is the largest single-row drop in the profile.
    """
    y0, y1 = boot_band(lm, v)
    prof = []
    for y in range(y0, y1 + 1):
        runs = v.row_runs(y)
        if not runs:
            prof.append((y, 0, []))
            continue
        prof.append((y, runs[-1][1] - runs[0][0] + 1, runs))
    widths = [w for _, w, _ in prof]
    wmax = max(widths)
    y_at_max = prof[widths.index(wmax)][0]
    return {
        "band": [y0, y1],
        "maxWidthPx": wmax,
        "rowAtMaxWidth": y_at_max,
        "runsAtMaxWidth": prof[widths.index(wmax)][2],
        "widthProfile": [[y, w] for y, w, _ in prof],
    }


def plate_thickness(v: R.View, run: tuple[int, int], far_side: str, frac: float = 0.15) -> dict:
    """Slab thickness, read at the plate's FAR TIP where nothing else is above it.

    Not "ground row to the ledge row". Both faces of the slab are horizontal planes, so
    under an orthographic camera their outlines project to the same shape offset
    vertically by exactly the thickness — but the product shot is very slightly
    ELEVATED, which spreads the ground-contact outline itself over dozens of rows. In
    left.webp the silhouette's total width climbs from 121 px at row 776 to 160 px at
    806 and then tapers to 6 px at row 845: those last 37 rows are the near corner of
    the plate opening up, not 37 rows of plate edge. Measuring the band height there
    returns roughly three times the real thickness.

    At the plate's far tip the plate is the only thing in the column and its own depth
    is nearly zero, so the contiguous vertical run through the column's lowest figure
    pixel IS the thickness.
    """
    x0, x1 = run
    n = max(3, int((x1 - x0 + 1) * frac))
    cols = list(range(x0, x0 + n)) if far_side == "low" else list(range(x1 - n + 1, x1 + 1))
    heights = []
    for x in cols:
        bottom = next((y for y in range(v.y1, -1, -1) if v.m(x, y)), None)
        if bottom is None:
            continue
        y = bottom
        while y >= 0 and v.m(x, y):
            y -= 1
        heights.append(bottom - y)
    heights.sort()
    if not heights:
        return {"px": 0, "samples": 0}
    return {
        "px": heights[len(heights) // 2],
        "p10": heights[int(len(heights) * 0.1)],
        "p90": heights[min(len(heights) - 1, int(len(heights) * 0.9))],
        "samples": len(heights),
        "columns": [cols[0], cols[-1]],
    }


def plan_extents(w: float, theta_deg: float, c: float) -> tuple[float, float]:
    """The (lateral, fore-aft) bbox of the CHAMFERED trapezoid as posed.

    The same eight-point outline `src/utils/cloudStrifeFigure/createSole.ts` builds, because
    solving against a shape the factory does not build is how the first solve here went
    wrong: it inverted the 2x2 for a SHARP-cornered trapezoid, then emitted a chamfer that
    cuts exactly the two corners the bbox is attained at. The built slab came out 17% short
    of the measured A and B, and every orthographic gate would have scored that as a
    modelling error rather than as the solve's own omission.
    """
    hl = ADOPTED_ASPECT * w / 2
    hw, tw = w / 2, w * ADOPTED_TOE_TAPER / 2
    pts = [(-tw + c, hl), (tw - c, hl), (tw, hl - c), (hw, -hl + c),
           (hw - c, -hl), (-hw + c, -hl), (-hw, -hl + c), (-tw, hl - c)]
    t = math.radians(theta_deg)
    xs = [x * math.cos(t) + z * math.sin(t) for x, z in pts]
    zs = [-x * math.sin(t) + z * math.cos(t) for x, z in pts]
    return max(xs) - min(xs), max(zs) - min(zs)


def _bisect(f, lo: float, hi: float) -> float:
    if f(lo) * f(hi) > 0:
        return float("nan")
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def solve_plan(a: float, b: float, c: float) -> tuple[float, float]:
    """(heelWidth, splayDeg) whose chamfered, splayed outline has bbox exactly (a, b).

    Nested bisection rather than a closed form: the chamfer is an absolute length (0.34 T)
    while the trapezoid scales with W, so the system is not homogeneous and there is no 2x2
    to invert. Inner solves W for the lateral extent at a fixed theta; outer solves theta
    for the fore-aft extent, which falls monotonically as the foot turns.
    """
    def width_for(theta: float) -> float:
        return _bisect(lambda w: plan_extents(w, theta, c)[0] - a, 1e-5, 1.0)

    theta = _bisect(lambda th: plan_extents(width_for(th), th, c)[1] - b, 1.0, 89.0)
    return width_for(theta), theta


def main() -> int:
    path = HERE / "landmarks.json"
    lm = json.loads(path.read_text())

    views = {k: R.load(k) for k in ("front", "back", "left", "right")}
    out: dict = {"generatedBy": "spec/measure_sole.py", "adopted": {
        "aspectLtoW": ADOPTED_ASPECT,
        "toeTaper": ADOPTED_TOE_TAPER,
        "endChamferOfThickness": ADOPTED_END_CHAMFER,
        "why": "plan outline is unobservable from four orthographic views; see the "
               "module docstring of spec/measure_sole.py",
    }, "raw": {}}

    # §1.2 fixes which image side is the plate's far tip. front/back: the two feet splay
    # apart, so each foot's OWN outer end is its toe; take the outermost run's outer
    # end. left/right: model +Z = -image x in left.webp and +image x in right.webp, so
    # the toe tip is image-low in left and image-high in right.
    far = {"front": "low", "back": "high", "left": "low", "right": "high"}
    prof = {k: slab_profile(lm, v) for k, v in views.items()}
    for k, p in prof.items():
        runs = p["runsAtMaxWidth"]
        span = (runs[0][0], runs[-1][1])
        t = plate_thickness(views[k], span, far[k])
        t["normalized"] = t["px"] / unit(lm, k)
        p["thickness"] = t
        p["thicknessNormalized"] = t["normalized"]
        out["raw"][k] = p

    # ---- A: lateral extent per foot, from the two frontal views ----
    # Per FOOT, not per row-extent: the row extent spans both feet plus the gap.
    lateral: dict[str, list[float]] = {}
    for key in ("front", "back"):
        u = unit(lm, key)
        lateral[key] = [(b - a + 1) / u for a, b in prof[key]["runsAtMaxWidth"]]

    # ---- B: fore-aft extent, from the two profile views ----
    # The two feet are mirror images about the sagittal plane, so they share one Z
    # range: the union of both feet's runs is one foot's fore-aft extent, not two
    # feet's. That is what makes a profile view usable here at all.
    foreaft: dict[str, float] = {}
    for key in ("left", "right"):
        foreaft[key] = prof[key]["maxWidthPx"] / unit(lm, key)

    # ---- adopt one value per axis ----
    # A: the two feet in front.webp, cross-checked against back.webp. Mean of every
    # ground run that is a foot (a run narrower than a third of the widest is a stray
    # sliver of the far foot showing between the near one and the frame).
    def feet(vals: list[float]) -> list[float]:
        big = max(vals)
        return [x for x in vals if x > big / 3]

    a_front, a_back = feet(lateral["front"]), feet(lateral["back"])
    A = sum(a_front) / len(a_front)
    B = (foreaft["left"] + foreaft["right"]) / 2
    # Thickness is read in all four views: the step is the same physical ledge whichever
    # side it is seen from, so four reads is four chances to catch a bad step detection.
    t_all = {k: prof[k]["thicknessNormalized"] for k in views}
    T = sum(t_all.values()) / len(t_all)

    C = T * ADOPTED_END_CHAMFER
    W, theta = solve_plan(A, B, C)
    L = ADOPTED_ASPECT * W
    built_a, built_b = plan_extents(W, theta, C)

    prior = lm["poseAngles"]["footSplayDeg"]
    out.update({
        "lateralExtent": {"adopted": A, "front": a_front, "back": a_back,
                          "crossViewSpread": abs(sum(a_front) / len(a_front)
                                                 - sum(a_back) / len(a_back))},
        "foreAftExtent": {"adopted": B, "left": foreaft["left"], "right": foreaft["right"],
                          "crossViewSpread": abs(foreaft["left"] - foreaft["right"])},
        "thickness": {"adopted": T, "perView": t_all,
                      "crossViewSpread": max(t_all.values()) - min(t_all.values())},
        "splayDeg": {
            "derived": theta,
            "priorProjectionRatio": prior,
            "method": "solved from A/B with the adopted L/W AND the end chamfer, against "
                      "the same eight-point outline the factory builds; "
                      "poseAngles.footSplayDeg is atan2(A, B), the bounding-box diagonal, "
                      "which is biased toward 45",
        },
        "planCheck": {
            "builtLateral": built_a,
            "builtForeAft": built_b,
            "lateralResidual": abs(built_a - A),
            "foreAftResidual": abs(built_b - B),
            "note": "the chamfered outline's own bbox, recomputed from the solved plan. "
                    "Both residuals must be ~0: they are what the first solve got wrong.",
        },
        "planTrapezoid": {
            "heelWidth": W,
            "toeWidth": W * ADOPTED_TOE_TAPER,
            "length": L,
            "endChamfer": T * ADOPTED_END_CHAMFER,
            "frame": "foot-local: +z toward the toe, +x toward the figure's left, "
                     "origin at the slab's plan centroid, bottom face on y=0",
        },
    })

    mu = lm["measurementUncertainty"]
    out["crossViewCheck"] = {
        "measurementUncertainty": mu,
        "worst": max(out["lateralExtent"]["crossViewSpread"],
                     out["foreAftExtent"]["crossViewSpread"],
                     out["thickness"]["crossViewSpread"]),
        "verdict": "PASS" if max(out["lateralExtent"]["crossViewSpread"],
                                 out["foreAftExtent"]["crossViewSpread"],
                                 out["thickness"]["crossViewSpread"]) < mu else "REVIEW",
    }

    lm.setdefault("parts", {})["sole"] = out
    path.write_text(json.dumps(lm, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("lateralExtent", "foreAftExtent", "thickness", "splayDeg",
                       "planTrapezoid", "planCheck", "crossViewCheck")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
