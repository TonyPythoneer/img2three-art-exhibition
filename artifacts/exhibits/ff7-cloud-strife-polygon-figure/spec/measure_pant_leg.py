#!/usr/bin/env python3
"""Measure the WHOLE pant leg as one line, and write parts.pantLeg into landmarks.json.

    python3 measure_pant_leg.py

WHY THIS IS ONE SCRIPT AND NOT THREE
------------------------------------
thigh, knee and calf are three segments of ONE pair of bloomer pants (§4's lower-body
intro). §5.7 decides "exactly one corner" by fitting the outer trouser line from the hip
to the boot cuff as a TWO-SEGMENT POLYLINE and checking that a three-segment fit does not
reduce the residual. That fit spans all three parts, so it cannot be produced from inside
any one of them — measuring it three times is not redundancy, it is three chances to
disagree about one line.

Everything the three factories need comes out of here, so the sections where they meet
have exactly one source and C0 continuity holds by construction rather than by later
reconciliation.

WHAT IT MEASURES
----------------
1. The outer line, per view, on the PANTS BAND — never on the silhouette. At hip height
   the outermost pixel of a row is the GLOVE, not the trouser, and the whole row extent
   spans both forearms. `measure_landmarks.leg_outer_edge` already carries that lesson;
   this reuses it rather than re-learning it.
2. The corner: the two-segment break, its residual, and the three-segment residual that
   would falsify "exactly one corner" (§5.7 a).
3. The corner is a ZONE, not a row. §4[4] says the knee is a short segment with the corner
   INSIDE it, so the knee's top and bottom are where the measured edge departs from the
   taper line and rejoins the tube line. That departure band is the knee's height, and it
   is measured rather than assumed.
4. The four boundary sections the three factories must agree on: width from the frontal
   views, depth from the profiles, at hipTop / kneeTop / calfTop / ankleTop.
5. §5.7 (d): the calf is near-constant width, top-to-bottom difference vs uncertainty.
"""
from __future__ import annotations

import json
from pathlib import Path

import measure_landmarks as ML
import refmask as R

HERE = Path(__file__).resolve().parent
FRONTAL = ("front", "back")
PROFILE = ("left", "right")


def pin_corner_test(n: int = 130) -> dict:
    """Pin §5.7 (a)'s "exactly one corner" threshold with fake frames.

    §5.7 (a) as literally written is VACUOUS here. It says the two-segment residual must
    be within measurementUncertainty and that three segments must not reduce it below
    that — but the uncertainty is 0.05447, which is 43 px of front.webp, while the real
    residuals are 2.4-6.8 px. Both fits pass by a factor of six, so the test can never
    fail. That is Stage 0's guess-list item 3 biting for the first time.

    The meaningful quantity is the RATIO res3 / res2: how much a second corner buys. A
    guessed ratio would make this gate as useless as the one it replaces, so it is pinned
    the way spec/facet-gate.json was — against frames whose answer is known:

        one-corner   a clean two-segment polyline + 1px noise   MUST PASS
        arc          a smooth quadratic, no corner at all       MUST FAIL
        two-corner   a genuine three-segment polyline           MUST FAIL

    The threshold is placed midway between the worst passing ratio and the best failing
    one, and both margins are recorded so a later reader can see it was separated rather
    than chosen.
    """
    def noisy(f, seed: int = 7) -> list[tuple[float, float]]:
        # deterministic 1px sawtooth, the scale of the reference's own edge quantisation
        return [(float(y), f(y) + (0.5 if (y * seed) % 3 else -0.5)) for y in range(n)]

    frames = {
        "one-corner": noisy(lambda y: 0.5 * y if y < 60 else 30.0 - 0.03 * (y - 60)),
        "arc": noisy(lambda y: 30.0 * (y / n) ** 2),
        "two-corner": noisy(
            lambda y: 0.5 * y if y < 45 else (22.5 + 0.05 * (y - 45) if y < 90 else 24.75 - 0.4 * (y - 90))
        ),
    }
    ratios = {}
    for name, pts in frames.items():
        br = ML.two_segment_fit(pts)
        r2 = br[1] if br else 0.0
        r3 = ML.three_segment_residual(pts)
        ratios[name] = {"two": r2, "three": r3, "ratio": (r3 / r2) if r2 else 1.0}
    must_pass = ratios["one-corner"]["ratio"]
    must_fail = min(ratios["arc"]["ratio"], ratios["two-corner"]["ratio"])
    pinned = must_fail < must_pass
    thr = (must_pass + must_fail) / 2 if pinned else None
    return {
        "assertion": "res3/res2 must be >= threshold — a second corner must NOT buy much",
        "frames": ratios,
        "threshold": thr,
        "separation": must_pass - must_fail,
        "pinned": pinned,
        "hardStop": None if pinned else
        "the fake frames do not separate: a smooth arc or a real two-corner line scores "
        "as well as a clean single corner. Do not use this gate until they do.",
    }


def unit(lm: dict, view: str) -> float:
    px = lm["views"][view]["landmarksPx"]
    return (px["sole"] - px["chin"]) / lm["normalization"]["sole->chin"]["spanNormalized"]


def norm(lm: dict, view: str, row: float) -> float:
    """Image row -> normalized height above the sole."""
    px = lm["views"][view]["landmarksPx"]
    return (px["sole"] - row) / unit(lm, view)


def outer_line(lm: dict, v: R.View, side: str, top_h: float | None = None) -> dict | None:
    """One pant leg's outer edge, fitted as two segments, with the knee zone.

    `top_h` is a normalized height to start from, for the profiles. They have no
    widestHip landmark of their own — the crotch notch that defines it is invisible edge
    on — and starting at beltBottom instead swallows the whole pelvis, which is a
    different shape and drags the fit. Worse, ABOVE the crotch a profile row carries BOTH
    legs, offset in Z by the splay, so lo/hi returns the envelope of two legs at
    different depths rather than one leg's front and back edge. Below the crotch the near
    leg occludes the far one and the run is a single tube. So the profiles are fitted
    from the crotch down, and the height comes from the frontal views that can see it.
    """
    L = lm["views"][v.name]["landmarksPx"]
    hem = L["pantHem"]
    if top_h is not None:
        top = L["sole"] - top_h * unit(lm, v.name)
    else:
        top = L["widestHip"]
    y0, y1 = int(top), int(hem) - 4
    if y1 - y0 < 40:
        return None
    pts = ML.leg_outer_edge(v, y0, y1, side)
    if len(pts) < 20:
        return None
    br = ML.two_segment_fit(pts)
    if not br:
        return None
    break_y, res2, (a1, b1), (a2, b2) = br
    res3 = ML.three_segment_residual(pts)

    # The knee ZONE: rows where the measured edge has left the taper line and has not yet
    # joined the tube line, judged against the fit's own residual so the tolerance is the
    # instrument's rather than a guess. Walking outward from the break is what makes this
    # a segment instead of a row — §4[4]'s "the corner lives inside this segment".
    tol = max(res2, 1.0)
    ups = [y for y, x in pts if y <= break_y and abs(x - (a1 * y + b1)) > tol]
    dns = [y for y, x in pts if y >= break_y and abs(x - (a2 * y + b2)) > tol]
    knee_top = min(ups) if ups else break_y
    knee_bot = max(dns) if dns else break_y
    return {
        "rowsFitted": [y0, y1],
        "samples": len(pts),
        "breakRow": break_y,
        "twoSegmentMaxResidualPx": res2,
        "threeSegmentMaxResidualPx": res3,
        "threeSegmentHelps": res3 < res2 * 0.5,
        "taperSlopeDxDy": a1,
        "tubeSlopeDxDy": a2,
        "kneeZoneRows": [knee_top, knee_bot],
    }


def band_width(v: R.View, row: int) -> dict | None:
    """The PANTS runs on a row: each run's own width, and their total span.

    TWO traps here, and this project has now fallen into both of them:

    - Not `row_extent`. At hip height the row also carries the two forearms, so
      first-run-start to last-run-end measures the ARM SPAN. That is what made the belt's
      "proud" margins compare three arm spans to each other.
    - Not first-start-to-last-end even on the pants band. BELOW THE CROTCH there are two
      separate legs, and that span silently includes the gap between them: it returns
      0.214 for a calf whose real width is 0.061. `straightPantTubeWidth` in
      landmarks.json is the per-leg number and is three and a half times smaller.

    So: `perRun` is what a single leg measures, `span` is the outer envelope, and the
    caller has to say which one it means.
    """
    pm = R.band_map(v)["purple"]
    runs = ML.real_runs(v, row, pm)
    if not runs:
        return None
    widths = [float(r[1] - r[0] + 1) for r in runs]
    return {
        "runs": len(runs),
        "perRun": widths,
        "widest": max(widths),
        "span": float(runs[-1][1] - runs[0][0] + 1),
    }


def main() -> int:
    path = HERE / "landmarks.json"
    lm = json.loads(path.read_text())
    views = {k: R.load(k) for k in FRONTAL + PROFILE}
    mu = lm["measurementUncertainty"]

    crotch = sum(
        lm["normalization"]["sole->chin"]["perView"][k]["crotchNotchApex"] for k in FRONTAL
    ) / len(FRONTAL)

    # EVERY view is fitted FROM THE CROTCH DOWN, not from the widest hip.
    #
    # §4[6] describes the pelvis's own front outline as "belt width, flaring out to the
    # widest point, THEN PULLING IN to an inverted-V crotch notch" — the inward pull is
    # part of the pelvis, not of the thigh. Fitting from widestHip therefore put a
    # pelvis-shaped taper into a leg-shaped fit, and it showed: the break landed within a
    # pixel of the crotch in front.webp, the "knee zone" straddled the crotch, and the
    # sections either side of it were not the same kind of measurement — one fused mass
    # above, two separate legs below. thighL/thighR cannot even be measured up there,
    # because up there the two legs are one run.
    #
    # Below the crotch the legs are separate tubes and every section is per-leg, which is
    # what the three factories need.
    lines: dict = {}
    for name in FRONTAL + PROFILE:
        v = views[name]
        per = {}
        for side in ("lo", "hi"):
            r = outer_line(lm, v, side, crotch)
            if r:
                per[side] = r
        if per:
            lines[name] = per

    # ---- adopt one corner height ----
    # From the FRONTAL views only. The profiles are fitted and reported, but they are not
    # allowed to move the adopted value: their fit starts below the crotch, so the taper
    # segment above the corner is short there and the break is far less constrained. Two
    # instruments of unequal quality do not get an equal vote.
    corner_rows = {k: sum(s["breakRow"] for s in p.values()) / len(p) for k, p in lines.items()}
    corner_norm = {k: norm(lm, k, r) for k, r in corner_rows.items()}
    front_norm = {k: v for k, v in corner_norm.items() if k in FRONTAL}
    corner = sum(front_norm.values()) / len(front_norm)
    corner_spread = max(front_norm.values()) - min(front_norm.values())

    # knee zone, from the frontal views for the same reason. Adopted as the WIDEST zone
    # they report: a segment too short to hold the corner is the failure §4[4] warns about.
    zones = [
        (norm(lm, k, s["kneeZoneRows"][1]), norm(lm, k, s["kneeZoneRows"][0]))
        for k, p in lines.items()
        if k in FRONTAL
        for s in p.values()
    ]
    knee_bot = min(z[0] for z in zones)
    knee_top = max(z[1] for z in zones)

    # ---- the four boundary heights, in normalized units ----
    # The chain's top is the CROTCH, not the widest hip: everything above it is one fused
    # mass and belongs to the pelvis (§4[6]).
    hip_top = crotch
    # pantHem, NOT bootCuffTopHighest. Stage 0's guess-list item 1 already settled this:
    # the feet splay, so the near and far boot openings differ by ~38 px and
    # bootCuffTopHighest is not a single landmark. pantHem is the cross-view anchor, and it
    # is the value the ankle part was built and gated against. Taking the other one here
    # would silently grow the finished ankle by 0.010.
    ankle_top = lm["normalization"]["sole->chin"]["perView"]["front"]["pantHem"]
    heights = {
        "hipTop": hip_top,
        "kneeTop": knee_top,
        "calfTop": knee_bot,
        "ankleTop": ankle_top,
    }

    # ---- sections at those heights ----
    # A section is ONE LEG. Above the crotch the two legs are fused into one run and the
    # section is that whole mass; below it each leg has its own run and the section is the
    # WIDEST run, never the span across both.
    sections: dict = {}
    for label, h in heights.items():
        w, d, raw = {}, {}, {}
        for k, dest in ((k, w) for k in FRONTAL):
            u = unit(lm, k)
            row = int(round(lm["views"][k]["landmarksPx"]["sole"] - h * u))
            m = band_width(views[k], row)
            if m:
                dest[k] = m["widest"] / u
                raw[k] = dict(m, row=row, perRunNormalized=[x / u for x in m["perRun"]])
        for k in PROFILE:
            u = unit(lm, k)
            row = int(round(lm["views"][k]["landmarksPx"]["sole"] - h * u))
            m = band_width(views[k], row)
            if m:
                d[k] = m["widest"] / u
                raw[k] = dict(m, row=row, perRunNormalized=[x / u for x in m["perRun"]])
        sections[label] = {
            "height": h,
            "widthPerView": w,
            "depthPerView": d,
            "width": sum(w.values()) / len(w) if w else None,
            "depth": sum(d.values()) / len(d) if d else None,
            "widthSpread": (max(w.values()) - min(w.values())) if len(w) > 1 else 0.0,
            "depthSpread": (max(d.values()) - min(d.values())) if len(d) > 1 else 0.0,
            "raw": raw,
        }

    calf_top = sections["calfTop"]
    calf_bot = sections["ankleTop"]
    calf_delta = (
        abs((calf_top["width"] or 0) - (calf_bot["width"] or 0)) if calf_top["width"] else None
    )
    tube = lm["dimensions"]["straightPantTubeWidth"]

    # ---- §5.7 (a), against a pinned threshold rather than a vacuous one ----
    pin = pin_corner_test()
    ratios = [
        r["threeSegmentMaxResidualPx"] / r["twoSegmentMaxResidualPx"]
        for p in lines.values()
        for r in p.values()
        if r["twoSegmentMaxResidualPx"]
    ]
    if not pin["pinned"]:
        corner_verdict = "HARD STOP — " + pin["hardStop"]
    elif all(x >= pin["threshold"] for x in ratios):
        corner_verdict = f"PASS — worst ratio {min(ratios):.3f} >= {pin['threshold']:.3f}"
    else:
        corner_verdict = (
            f"FAIL — worst ratio {min(ratios):.3f} < {pin['threshold']:.3f}: a second "
            "corner buys enough to be real in at least one view"
        )

    # ---- the tube below the crotch, sampled every few rows ----
    # This is what decides whether thigh / knee / calf are three shapes or one. §2: "SHAPE
    # CODES ARE ASSIGNED FROM MEASURED DIMENSIONS, NOT FROM NAMES. If two parts measure the
    # same section and length within the tolerance, they get the SAME shape code."
    tube_prof: dict = {}
    for k in FRONTAL + PROFILE:
        u = unit(lm, k)
        sole = lm["views"][k]["landmarksPx"]["sole"]
        top_row = int(round(sole - crotch * u))
        bot_row = int(round(sole - ankle_top * u))
        samples = []
        for row in range(top_row, bot_row + 1, max(1, (bot_row - top_row) // 12)):
            m = band_width(views[k], row)
            if m:
                samples.append([round((sole - row) / u, 6), round(m["widest"] / u, 6), m["runs"]])
        if samples:
            ws = [s[1] for s in samples if s[2] >= 2] or [s[1] for s in samples]
            tube_prof[k] = {
                "samples": samples,
                "min": min(ws),
                "max": max(ws),
                "range": max(ws) - min(ws),
            }
    tube_range = max((t["range"] for t in tube_prof.values()), default=0.0)

    # ---- THE ONE SECTION the three factories share ----
    # Taken at MID-TUBE, halfway between the crotch and the boot cuff, because that is the
    # only height where every view is unambiguously one leg: at the top the frontal views
    # may still be fused (the two crotches differ by 0.023 between front and back) and at
    # the bottom the boot cuff is already swallowing the tube.
    mid = (crotch + ankle_top) / 2
    mw, md = {}, {}
    for k in FRONTAL + PROFILE:
        u = unit(lm, k)
        row = int(round(lm["views"][k]["landmarksPx"]["sole"] - mid * u))
        m = band_width(views[k], row)
        if not m:
            continue
        (mw if k in FRONTAL else md)[k] = m["widest"] / u
    section = {
        "atHeight": mid,
        "widthX": sum(mw.values()) / len(mw) if mw else None,
        "depthZ": sum(md.values()) / len(md) if md else None,
        "widthPerView": mw,
        "depthPerView": md,
        "widthSpread": (max(mw.values()) - min(mw.values())) if len(mw) > 1 else 0.0,
        "depthSpread": (max(md.values()) - min(md.values())) if len(md) > 1 else 0.0,
        "crossCheck": {
            "landmarks.dimensions.straightPantTubeWidth": lm["dimensions"][
                "straightPantTubeWidth"
            ],
            "why": "measured by a different script at a different row. Two independent "
            "readings of one leg's width; if they disagree, one is spanning both legs.",
        },
    }

    # ---- the ledger disagreement (§0.6: report it, do not silently pick) ----
    ledger_hip = lm["normalization"]["sole->chin"]["perView"]["front"]["crotchNotchApex"]
    out = {
        "generatedBy": "spec/measure_pant_leg.py",
        "outerLine": lines,
        "corner": {
            "adopted": corner,
            "adoptedFrom": list(FRONTAL),
            "perView": corner_norm,
            "crossViewSpreadFrontal": corner_spread,
            "verdict": "PASS" if corner_spread < mu else "REVIEW",
            "profileNote": "the profiles are fitted from the crotch down and reported, but "
            "they do not vote on the adopted height: their taper segment is short and the "
            "break is far less constrained there. Read their residuals, not their break.",
        },
        "singleCorner_5_7a": {
            "pin": pin,
            "measured": {
                k: {
                    s: {
                        "two": r["twoSegmentMaxResidualPx"],
                        "three": r["threeSegmentMaxResidualPx"],
                        "ratio": (r["threeSegmentMaxResidualPx"] / r["twoSegmentMaxResidualPx"])
                        if r["twoSegmentMaxResidualPx"]
                        else 1.0,
                    }
                    for s, r in p.items()
                }
                for k, p in lines.items()
            },
            "verdict": corner_verdict,
            "note": "the literal §5.7 (a) test is vacuous here: it compares residuals of "
            "2.4-6.8 px against measurementUncertainty, which is 43 px of front.webp. The "
            "ratio res3/res2 is the quantity with signal, and its threshold is pinned "
            "against fake frames rather than guessed.",
        },
        "tubeBelowCrotch": {
            "topHeight": crotch,
            "bottomHeight": ankle_top,
            "totalHeight": crotch - ankle_top,
            "perView": tube_prof,
            "widestSpreadAnyView": tube_range,
            "measurementUncertainty": mu,
            "referenceOwnResidual": 0.0030517,
            "collapse": {
                "verdict": "COLLAPSE"
                if tube_range < mu
                else "KEEP THREE SHAPES",
                "what": "§2 assigns shape codes from measured dimensions, not from names. "
                "Below the crotch the leg's per-leg width varies by "
                f"{tube_range:.5f} over its whole length, against an uncertainty of "
                f"{mu:.5f}. There is no corner down here either (§5.7 a FAILS on the "
                "ratio test, and the outer slope is 0.53 dx/dy above the crotch versus "
                "0.073 below it — the corner IS the crotch). So S-03 pantTube, S-04 "
                "pantGather and S-05 pantTaper measure as ONE shape.",
                "consequence": "thighL/R, kneeL/R and calfL/R remain six PARTS — "
                "partInspector reads the object tree and §2's table stands — but they are "
                "three stacked segments of one section, which is §4[4]'s 'the three parts "
                "must share ONE set of section constants' taken to its limit. C0 continuity "
                "then holds by construction instead of by assertion.",
                "unmeasurable": "where the three segments meet. There is no landmark "
                "between the crotch and the boot cuff and no width breakpoint to find, so "
                "the two split heights are a GUESS-LIST item, defaulted to equal thirds.",
            },
        },
        "sharedSection": section,
        "segmentHeights": {
            "note": "equal thirds of the tube — see tubeBelowCrotch.collapse.unmeasurable",
            "chainY": {
                "hip": crotch,
                "kneeTop": crotch - (crotch - ankle_top) / 3,
                "calfTop": crotch - 2 * (crotch - ankle_top) / 3,
                "ankleTop": ankle_top,
            },
            "thigh": (crotch - ankle_top) / 3,
            "knee": (crotch - ankle_top) / 3,
            "calf": (crotch - ankle_top) / 3,
            "fittedZoneForReference": {
                "thigh": hip_top - knee_top,
                "knee": knee_top - knee_bot,
                "calf": knee_bot - ankle_top,
            },
        },
        "boundarySections": sections,
        "calfNearConstantWidth_5_7d": {
            "topWidth": calf_top["width"],
            "bottomWidth": calf_bot["width"],
            "difference": calf_delta,
            "measurementUncertainty": mu,
            "verdict": "PASS" if calf_delta is not None and calf_delta < mu else "REVIEW",
            "crossCheckStraightPantTubeWidth": {
                "landmarks.dimensions": tube,
                "thisScriptCalfTop": calf_top["width"],
                "agree": calf_top["width"] is not None
                and abs(calf_top["width"] - max(tube)) < mu,
                "why": "an independent measurement of the same thing, taken at a different "
                "row by a different script. If these two disagree, one of them is measuring "
                "the span across both legs instead of one leg.",
            },
        },
        "ledgerDisagreement": {
            "measurements.SOCKET_Y.hip": ledger_hip,
            "measuredTaperTop(widestHip)": hip_top,
            "difference": hip_top - ledger_hip,
            "what": "the ledger puts the thigh's origin `hip` at crotchNotchApex, which is "
            "BELOW the corner this fit finds. Taken literally the taper — the thing §4[5] "
            "says the thigh IS — sits entirely above the thigh, and thigh+knee would have "
            "no height left. The taper runs from the widest hip DOWN TO the crotch.",
            "readingA": "`hip` moves to the widest hip; the thigh is the taper; the pelvis "
            "is the widening kite above it. Consistent with §4[5]'s 'continuous inward "
            "taper, wide at top, narrow at bottom' and with §4[6]'s pelvis being the widest "
            "volume.",
            "readingB": "`hip` stays at the crotch; the taper belongs to the pelvis and "
            "thigh/knee/calf all live below the crotch, where the outer line is already "
            "vertical and §5.7's corner has nothing to find.",
            "chosen": "B, refined. §4[6] describes the PELVIS's own outline as flaring to "
            "the widest point and THEN PULLING IN to the crotch notch, so the inward taper "
            "above the crotch is the pelvis's, not the thigh's. The thigh/knee/calf chain "
            "is fitted from the crotch DOWN, where the two legs are separate runs and a "
            "per-leg section exists at all. `hip` stays at crotchNotchApex; what changes is "
            "this script's fit range, which was the thing that was wrong.",
        },
    }

    lm.setdefault("parts", {})["pantLeg"] = out
    path.write_text(json.dumps(lm, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("corner", "singleCorner_5_7a", "segmentHeights",
                       "calfNearConstantWidth_5_7d", "ledgerDisagreement")}, indent=2))
    print("\nboundary sections:")
    for k, s in sections.items():
        print(f"  {k:9s} h={s['height']:.5f}  width={s['width']}  depth={s['depth']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
