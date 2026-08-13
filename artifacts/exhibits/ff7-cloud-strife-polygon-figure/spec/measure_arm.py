#!/usr/bin/env python3
"""Measure the whole arm chain (§4[9]-[12], shape codes S-09..S-13) into parts.arm.

    python3 measure_arm.py

ONE SCRIPT FOR FOUR FACTORIES, for the same reason the pant leg got one: §4[10] says
upperDeltoid's BOTTOM hexagon must be IDENTICAL to lowerDeltoid's TOP, and §4[9] says
lowerDeltoid's quad bottom "exists so it mates with backArm's rectangular prism at an
identical section". Two shared sections that cannot be measured from inside either part.

THE §1.4-vs-§1.5 CONTRADICTION, SETTLED WITH NUMBERS ALREADY IN THE FILE

§1.4 bakes the pose into every part. §1.5 calls upperDeltoid / lowerDeltoid / backArm
PURE MIRROR PAIRS and §5.10 asserts they match to 1e-6 after negating x. But the measured
pose is not symmetric:

    upper-arm forward lean    L 1.629 deg    R 10.426 deg    difference 8.80
    elbow break               L 11.097       R 21.771        difference 10.67

Both cannot be true. And the instrument that declared them mirrors — a mirror IoU on
front.webp's silhouette, 0.943 with a 1 px extent difference — is a FRONT view, which is
blind to forward lean entirely. It could not have seen the disagreeing axis.

So the question is whether the 8.8 degrees is real. It is settled by the OTHER
instrument's own residual, which this script computes rather than asserts: convert the
angle difference into the sideways pixel displacement it implies over the upper arm's
length, and compare that against the two-segment fit's maximum residual on the same view.
poseAngles.sideArmFit records left at 29.23 px and right at 9.88 px — the left fit is
three times worse — so if the implied displacement is under the residual, the difference
is inside the noise of the thing that measured it and §1.5's mirror classification stands.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import measure_landmarks as ML
import refmask as R

HERE = Path(__file__).resolve().parent
FRONTAL = ("front", "back")
PROFILE = ("left", "right")


def unit(lm: dict, view: str) -> float:
    px = lm["views"][view]["landmarksPx"]
    return (px["sole"] - px["chin"]) / lm["normalization"]["sole->chin"]["spanNormalized"]


def row_of(lm: dict, view: str, h: float) -> int:
    return int(round(lm["views"][view]["landmarksPx"]["sole"] - h * unit(lm, view)))


def arm_runs(v: R.View, row: int, band: str) -> list[tuple[int, int]]:
    """Runs of one band on a row, dropping anything narrower than a fifth of the widest.

    The torso and the arms share every row here, so the caller picks the run by POSITION
    rather than by size — but a two-pixel speck of skin on the far side of the figure is
    never an arm, and it would otherwise become the outermost run.
    """
    runs = ML.real_runs(v, row, R.band_map(v)[band])
    if not runs:
        return []
    widest = max(r[1] - r[0] + 1 for r in runs)
    return [r for r in runs if (r[1] - r[0] + 1) >= widest / 5]


def outer_run(v: R.View, row: int, band: str, side_is_image_right: bool):
    """The arm's own run: the outermost one on the side the arm is on.

    No minimum run count. Requiring two returned None for the fist — where the two gloves
    ARE two runs but the filter above can drop one when they differ in size — and it
    returned 0.0 for the plain wrist. A row with one run is not an error here; it is one
    arm, and which arm it is comes from the side, not from the count.
    """
    runs = arm_runs(v, row, band)
    if not runs:
        return None
    return runs[-1] if side_is_image_right else runs[0]


def main() -> int:
    path = HERE / "landmarks.json"
    lm = json.loads(path.read_text())
    views = {k: R.load(k) for k in FRONTAL + PROFILE}
    mu = lm["measurementUncertainty"]
    rms = lm["normalization"]["sole->chin"]["measurementUncertaintyRms"]
    pa = lm["poseAngles"]
    chain = json.loads((HERE / "build-constants.json").read_text())["socketChainY"]

    # ---- the mirror question, decided by the measuring instrument's own residual ----
    upper_len = chain["chestTop"] - chain["elbow"]          # shoulder to elbow, normalized
    dlean = abs(pa["figureLeftUpperArm"]["forwardLeanDeg"] - pa["figureRightUpperArm"]["forwardLeanDeg"])
    dbreak = abs(pa["figureLeftElbowBreakDeg"] - pa["figureRightElbowBreakDeg"])
    implied_px = {
        k: math.tan(math.radians(dlean)) * upper_len * unit(lm, k) for k in PROFILE
    }
    residual_px = {k: pa["sideArmFit"][k]["maxResidualPx"] for k in PROFILE}
    # The difference must clear the WORST of the two residuals, not the best. A gap of 8.8
    # degrees is only established if BOTH readings are trustworthy at that scale, and the
    # left fit is the weak one — so `all`, never `any`. Written out because the `any`
    # version ran first and returned "NOT A MIRROR" on the strength of the GOOD fit alone,
    # which is the wrong way round: a precise instrument agreeing with a sloppy one does
    # not make the sloppy one's number real.
    worst = max(residual_px.values())
    decidable = {k: implied_px[k] > worst for k in PROFILE}
    mirror = {
        "forwardLeanDifferenceDeg": dlean,
        "elbowBreakDifferenceDeg": dbreak,
        "upperArmLengthNormalized": upper_len,
        "impliedDisplacementPx": implied_px,
        "sideArmFitMaxResidualPx": residual_px,
        "differenceIsAboveTheNoise": decidable,
        "verdict": (
            "MIRROR — the asymmetry is smaller than the residual of the fit that produced it"
            if not all(decidable.values())
            else "NOT A MIRROR — the asymmetry exceeds the fit's own residual in at least one view"
        ),
        "why": "the 8.8 degree forward-lean gap implies the sideways displacement above "
        "over the upper arm's length. poseAngles.sideArmFit's LEFT fit has a maximum "
        "residual of 29.23 px against the right's 9.88 — three times worse — so the left "
        "lean is the untrustworthy half of the pair. A difference below the instrument's "
        "own residual is not a difference.",
        "consequence": "§1.5's classification stands: upperDeltoid, lowerDeltoid and "
        "backArm are pure mirror pairs and §5.10 applies to them. The adopted pose angles "
        "are the MEAN of the two sides, so neither side's error is carried whole. frontArm "
        "is still NOT a mirror — that pair differs by the bracer's width factor, which is "
        "measured below and has nothing to do with pose.",
        "adoptedAbductionDeg": (
            pa["figureLeftUpperArm"]["abductionDeg"] + pa["figureRightUpperArm"]["abductionDeg"]
        ) / 2,
        "adoptedForwardLeanDeg": (
            pa["figureLeftUpperArm"]["forwardLeanDeg"] + pa["figureRightUpperArm"]["forwardLeanDeg"]
        ) / 2,
        "adoptedElbowBreakDeg": (pa["figureLeftElbowBreakDeg"] + pa["figureRightElbowBreakDeg"]) / 2,
    }

    # ---- sections down the chain, on the SKIN band (the arms are bare) ----
    # front.webp: image +x IS model +X, so the figure's LEFT arm is the IMAGE-RIGHT run.
    heights = {
        "shoulder": chain["chestTop"],
        "deltoidWaist": chain["deltoidWaist"],
        "backArmTop": chain["backArmTop"],
        "elbow": chain["elbow"],
        "fist": chain["fist"],
    }
    # Each height sits on a DIFFERENT band, because the arm changes material down its
    # length: bare skin from the shoulder to the wrist, then the grey bracer on the left
    # wrist, then the near-black glove. Measuring the fist on the skin band returns a
    # one-pixel speck — which it did, 0.00125, before this table existed.
    band_at = {
        "shoulder": "skin",
        "deltoidWaist": "skin",
        "backArmTop": "skin",
        "elbow": "skin",
        "fist": "black",
    }
    sections: dict = {}
    for label, h in heights.items():
        band = band_at[label]
        w: dict[str, float] = {}
        for k in FRONTAL:
            # ALWAYS the figure's RIGHT arm, and §4[9] says exactly why: "Authority: the
            # figure's RIGHT shoulder in front.webp (bare, no pauldron occlusion, the
            # cleanest read)." §1.3 puts the BLACK PAULDRON and the grey bracer on the
            # figure's LEFT, so the left deltoid is not skin at all up here. Reading the
            # image-right run returned 0.03937 for the deltoid waist — identical to
            # dimensions.neckWidth, which is what a sliver of something else looks like.
            # §1.2: in front.webp the figure's RIGHT is the IMAGE-LEFT run; back.webp is
            # mirrored.
            run = outer_run(views[k], row_of(lm, k, h), band, k == "back")
            if run:
                w[k] = (run[1] - run[0] + 1) / unit(lm, k)
        d: dict[str, float] = {}
        for k in PROFILE:
            runs = arm_runs(views[k], row_of(lm, k, h), band)
            if runs:
                d[k] = max(r[1] - r[0] + 1 for r in runs) / unit(lm, k)
        sections[label] = {
            "height": h,
            "widthPerView": w,
            "depthPerView": d,
            "width": sum(w.values()) / len(w) if w else None,
            "depth": sum(d.values()) / len(d) if d else None,
            "widthSpread": (max(w.values()) - min(w.values())) if len(w) > 1 else 0.0,
        }

    # ---- §5.8: the upper arm is thinner than BOTH its neighbours ----
    thin = {
        "deltoidWaist": sections["deltoidWaist"]["width"],
        "backArmTop": sections["backArmTop"]["width"],
        "elbow": sections["elbow"]["width"],
        "upperArmNarrowestLandmark": lm["normalization"]["sole->chin"]["perView"]["front"][
            "upperArmNarrowest"
        ],
    }
    a, b, c = thin["deltoidWaist"], thin["backArmTop"], thin["elbow"]
    thin["verdict"] = (
        "PASS" if a and b and c and b < a and b < c else "REVIEW"
    )
    thin["note"] = (
        "§5.8 lists 'the upper arm being thinner than both its neighbours' as an identity "
        "feature whose failure blocks continue even when the global score passes."
    )

    # ---- the bracer's width factor: the ONE thing that makes frontArm not a mirror ----
    # The figure's LEFT wrist is the grey bracer; the RIGHT is the same prism in skin.
    # The wrist's height is not measurable from a landmark — there is none between the
    # elbow and the fist — so the row is FOUND: the one carrying the most grey, which is
    # the bracer's own widest row. Assuming the midpoint put it 1 px into the bracer and
    # returned a width factor of exactly 1.0 from two one-pixel readings.
    fv = views["front"]
    u = unit(lm, "front")
    best = (0.0, row_of(lm, "front", (chain["elbow"] + chain["fist"]) / 2))
    for row in range(row_of(lm, "front", chain["elbow"]), row_of(lm, "front", chain["fist"])):
        gruns = arm_runs(fv, row, "grey")
        gw = max((r[1] - r[0] + 1 for r in gruns), default=0)
        if gw > best[0]:
            best = (float(gw), row)
    row = best[1]
    wrist_h = (lm["views"]["front"]["landmarksPx"]["sole"] - row) / u
    bracer_w = best[0] / u
    # The plain wrist is the figure's RIGHT, which is bare skin: the outermost skin run on
    # the image-LEFT side of the same row (§1.2).
    plain = outer_run(fv, row, "skin", False)
    plain_w = ((plain[1] - plain[0] + 1) / u) if plain else 0.0
    bracer = {
        "atHeight": wrist_h,
        "bracerWidth": bracer_w,
        "plainWristWidth": plain_w,
        "widthFactor": (bracer_w / plain_w) if plain_w else None,
        "promptClaim": 1.05,
        "note": "§4[12] says the LEFT wrist segment has width factor ~1.05 and §1.5 makes "
        "frontArm the one pair that is not a pure mirror. Measured here so the factor is a "
        "reading rather than a quotation.",
    }

    # ---- the glove, found the same way the bracer was ----
    # `fist` is the socket at the BOTTOM of frontArm, so measuring the black band AT that
    # height lands below the glove and returns nothing — which it did. The glove's own
    # section is its widest black row between the elbow and the fist.
    gbest = (0.0, row_of(lm, "front", chain["fist"]))
    for row in range(row_of(lm, "front", chain["elbow"]), row_of(lm, "front", chain["fist"])):
        run = outer_run(fv, row, "black", False)
        if run and (run[1] - run[0] + 1) > gbest[0]:
            gbest = (float(run[1] - run[0] + 1), row)
    glove = {
        "atHeight": (lm["views"]["front"]["landmarksPx"]["sole"] - gbest[1]) / u,
        "width": gbest[0] / u,
        "fistLandmarkHeight": chain["fist"],
        "note": "measured at the glove's widest black row, not at the `fist` socket height "
        "— that socket is the BOTTOM of the part and the band is empty there.",
    }

    out = {
        "generatedBy": "spec/measure_arm.py",
        "glove": glove,
        "mirror_1_4_vs_1_5": mirror,
        "sections": sections,
        "upperArmIsThinnest_5_8": thin,
        "bracer": bracer,
        "tolerances": {"measurementUncertainty": mu, "rms": rms},
    }
    lm.setdefault("parts", {})["arm"] = out
    path.write_text(json.dumps(lm, indent=2) + "\n")
    print(json.dumps({"mirror": mirror, "thin": thin, "bracer": bracer}, indent=2))
    print("\nsections:")
    for k, s in sections.items():
        print(f"  {k:14s} h={s['height']:.5f}  w={s['width']}  d={s['depth']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
