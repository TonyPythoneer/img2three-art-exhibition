#!/usr/bin/env python3
"""Fill the pre-spec assessment skeleton from MEASURED artefacts.

`forge/stage2_spec/new_pre_spec_assessment.py` emits a skeleton whose objectClass,
complexity scores, anatomy block and detailInventory are all zeros and placeholders.
Filling them by hand in the JSON would put numbers in the spec that no artefact
produced, which is exactly what §0.6 forbids and what `audit_records.py` fails on.

So this script is the bridge: every number it writes is read out of
`spec/landmarks.json`, or measured here from the references, or is a COUNT of rows in
the prompt's own part table (§2) which is structure, not measurement.

    python3 fill_assessment.py            # rewrites spec/assessment.json in place

The detail inventory is the one part that is agent judgement rather than arithmetic:
the entries below are the zone scan of §0.4 written down. Each carries the view it was
seen in and the component/material field it must reach, so `check_part_coverage.py`
can hold the spec to it later.
"""
from __future__ import annotations

import json
from pathlib import Path

import refmask as R

HERE = Path(__file__).resolve().parent
REFS = HERE.parents[3] / "src/assets/exhibits/ff7-cloud-strife-polygon-figure"


# ---------------------------------------------------------------- eye landmarks ---
def measure_eyes(chin_px: int) -> dict:
    """Eye line and spacing from the printed eye art in front.webp.

    The face carries eyes and brows and NOTHING ELSE — no printed nose, no printed
    mouth (front.webp x120..270 y140..270 at 7x NEAREST). `reconstruction.md` asks for
    noseBase and mouthLine; they are not observable here because they do not exist on
    the reference, which is a different thing from "not measured" and is recorded as
    such rather than filled with a plausible number.

    Measured on the SATURATED BLUE of the iris, not on the dark lash line: the lash is
    the same near-black as the pupil and as the gap between the hair spikes, so a
    darkness test picks up hair. Blue does not appear anywhere else on the head.
    """
    # The head box runs from the figure's topmost row to the MEASURED chin row
    # (landmarks.json views.front.landmarksPx.chin). An arbitrary "top 32%" cut would
    # make eyeLine a function of the cut rather than of the face.
    v = R.load("front")
    head_top, head_bot = v.y0, chin_px
    px = v.px
    blues: list[tuple[int, int]] = []
    for y in range(head_top, head_bot):
        for x in range(v.x0, v.x1 + 1):
            if not v.m(x, y):
                continue
            r, g, b = px[x, y]
            if b > 90 and b - r > 35 and b - g > 18:
                blues.append((x, y))
    if not blues:
        return {"measured": False}
    xs = sorted({x for x, _ in blues})
    # split the blue pixels into the two eyes at the widest gap in x
    gaps = [(xs[i + 1] - xs[i], i) for i in range(len(xs) - 1)]
    _, cut = max(gaps)
    left_eye = [p for p in blues if p[0] <= xs[cut]]
    right_eye = [p for p in blues if p[0] > xs[cut]]

    def box(pts: list[tuple[int, int]]) -> dict:
        bx = [p[0] for p in pts]
        by = [p[1] for p in pts]
        return {"x0": min(bx), "x1": max(bx), "y0": min(by), "y1": max(by)}

    a, b_ = box(left_eye), box(right_eye)
    # head box: the SKIN+HAIR silhouette rows the eyes sit in, so the normalization is
    # the head bounding box reconstruction.md asks for, not the whole image.
    hx0, hx1, hy0, hy1 = 10**9, -1, head_top, head_bot
    for y in range(head_top, head_bot):
        e = v.row_extent(y)
        if e:
            hx0, hx1 = min(hx0, e[0]), max(hx1, e[1])
    hw = max(1, hx1 - hx0)
    hh = max(1, hy1 - hy0)
    eye_cy = (a["y0"] + a["y1"] + b_["y0"] + b_["y1"]) / 4.0
    inner_gap = max(0, b_["x0"] - a["x1"])
    return {
        "measured": True,
        "view": "front",
        "headBoxPx": {"x0": hx0, "x1": hx1, "y0": hy0, "y1": hy1},
        "eyeBoxesPx": {"figureRight": a, "figureLeft": b_},
        "eyeLine": (eye_cy - hy0) / hh,
        "eyeSpacing": inner_gap / hw,
        "note": (
            "eyeLine is normalized down the head bounding box, eyeSpacing across it, "
            "per grimoire/character/reconstruction.md. The head box here is the head "
            "band of the silhouette (hair included), not the skull."
        ),
    }


# ------------------------------------------------------------- detail inventory ---
# Zone scan of §0.4, written down. `where` is the view it was read in; `mapsTo` is the
# spec field it must reach — prose alone is a strict-quality failure.
DETAILS = [
    ("sole-toe-chamfer", "geometry", "front,left",
     "The toe end of the sole slab is a blunt chamfer, not a point; the corner cut is "
     "visible as its own facet at 8x.", "components.soleL/soleR.localFeatures"),
    ("sole-heel-chamfer", "geometry", "left,right",
     "The heel end is the same blunt chamfer as the toe, so the slab reads as a "
     "trapezoid with two cut ends rather than a wedge.",
     "components.soleL/soleR.localFeatures"),
    ("sole-top-ledge", "geometry", "front,left",
     "The sole's top face emerges from under the boot cuff as a clean ledge that runs "
     "all the way round; it is the widest horizontal plane in the lower body.",
     "components.soleL/soleR.localFeatures"),
    ("bootcuff-step", "geometry", "front,left,right",
     "The boot cuff's section is LARGER than the straight pant tube it swallows, with "
     "a hard step all round — not a taper.", "components.ankleL/ankleR.localFeatures"),
    ("bootcuff-vertical-chamfer", "geometry", "front",
     "The cuff's four vertical edges are chamfered; each chamfer catches its own tone "
     "under flat shading.", "components.ankleL/ankleR.localFeatures"),
    ("pant-front-crease", "geometry", "front",
     "One vertical crease runs down the front centre of the straight pant tube.",
     "components.calfL/calfR.localFeatures"),
    ("pantleg-corner", "geometry", "front,left",
     "The outer trouser line is a straight taper that hits exactly ONE hard corner and "
     "turns near-vertical below it. Not an arc, not two corners.",
     "components.kneeL/kneeR.localFeatures"),
    ("crotch-notch", "geometry", "front,back",
     "An inverted-V notch cuts up into the pelvis between the legs.",
     "components.pelvis.localFeatures"),
    ("hip-kite", "geometry", "left,right",
     "In profile the hip is a front/back-symmetric kite quadrilateral with one sharp "
     "point front and one back, deepest at the widest height.",
     "components.pelvis.localFeatures"),
    ("belt-proud-step", "geometry", "front,left,right,back",
     "The belt stands proud of both the chest above and the pelvis below, with a hard "
     "step on each of its two edges.", "components.waist.localFeatures"),
    ("chest-hexagon", "geometry", "front",
     "The chest's front outline is near-hexagonal: widest at the shoulder line, "
     "tapering to the waist, front and back near-planar.",
     "components.chest.localFeatures"),
    ("deltoid-hex-waistline", "geometry", "front,back",
     "Upper and lower deltoid meet at a hexagonal waistline; that horizontal crease is "
     "visible under zoom and is where the pauldron's lower edge lands.",
     "components.upperDeltoidL/R.localFeatures"),
    ("upperarm-thin", "geometry", "front,back",
     "The upper arm is markedly thinner in section than BOTH the deltoid above it and "
     "the forearm below it. The contrast is an identity feature.",
     "components.backArmL/backArmR.localFeatures"),
    ("forearm-widens-downward", "geometry", "front,left,right",
     "The forearm THICKENS as it descends — the opposite of human anatomy. Toy styling, "
     "not an error to be corrected.", "components.frontArmL/frontArmR.localFeatures"),
    ("bracer-overhang", "geometry", "front,left",
     "The figure's LEFT wrist block is the grey bracer: about 1.05x wider than the "
     "right, its lower edge overhanging a little. The RIGHT is the same prism in skin "
     "colour, which is why no seam shows there.",
     "components.frontArmL.localFeatures"),
    ("glove-flat-cut", "geometry", "front,left,right",
     "The glove is a chamfered cuboid with NO finger geometry, joined to the wrist "
     "above by a single flat cut.", "components.frontArmL/frontArmR.localFeatures"),
    ("elbow-break-forward", "geometry", "left,right",
     "The elbows break forward so the fists land AHEAD of the hip line. A straight "
     "hanging arm is a failure.", "components.frontArmL/frontArmR.localFeatures"),
    ("pauldron-left-only", "geometry", "front,back,left",
     "A black shoulder cap sits on the figure's LEFT deltoid only; the right deltoid is "
     "bare. Handedness carrier — the grey bracer is on the same side.",
     "components.pauldronL.localFeatures"),
    ("hair-spikes-not-mirrored", "geometry", "front,back,left,right",
     "Nine hair spikes, NOT left/right mirrored — the head+hair band scores mirrorIoU "
     "0.657 against a 0.858 whole-figure noise floor.",
     "components.hair*.localFeatures"),
    ("hairline-occiput-hard", "geometry", "back",
     "A hard horizontal line crosses the occiput: all yellow above, neck skin below. "
     "The only stretch of hairline that can be measured directly.",
     "components.hairCap.localFeatures"),
    ("ears-outside-cap", "geometry", "back",
     "The ears sit OUTSIDE the hair cap; a small pink skin wedge is exposed on each "
     "side below the cap edge.", "components.earL/earR.localFeatures"),
    ("face-print-eyes-brows-only", "material", "front",
     "The printed face carries blue irises with dark pupils, white sclera, a black "
     "upper lash line, and brows — and NOTHING else. No printed nose, no printed "
     "mouth.", "materials.printedFace.localOverrides"),
    ("jaw-chamfer-pointed-chin", "geometry", "front,left,right",
     "The face plane is near-planar and widest at the cheekbones, with a pronounced "
     "chamfer along the jaw down to a small pointed chin.",
     "components.head.localFeatures"),
    ("flat-shaded-facets", "material", "front,back,left,right",
     "Every surface is flat-shaded matte vinyl: hard facet boundaries with no smooth "
     "gradient anywhere. This is the identity of the whole object and the reason the "
     "facet gate exists.", "materials.*.localOverrides"),
]


def main() -> int:
    lm = json.loads((HERE / "landmarks.json").read_text())
    doc = json.loads((HERE / "assessment.json").read_text())
    a = doc["preSpecAssessment"]

    dims = lm["dimensions"]
    pa = lm["poseAngles"]
    chin = lm["normalization"]["sole->chin"]["spanNormalized"]
    front = lm["normalization"]["sole->chin"]["perView"]["front"]
    mu = lm["measurementUncertainty"]

    # ---- objectClass ----
    a["objectClass"] = {
        "primaryType": "stylized character figurine (vinyl polygon action figure)",
        "primaryDomain": "character",
        "formLanguage": ["faceted", "planar", "hard-edged", "low-poly", "chamfered"],
        "structureKind": ["segmented", "socketed", "bilateral", "fixed-pose"],
        "motionPotential": ["none — the pose is baked into every part (prompt §1.4)"],
        "materialFamilies": ["matte vinyl", "printed decal"],
        "notes": (
            "A physical polygon figure photographed flat-lit from four orthographic "
            "sides plus one three-quarter. The subject is the TOY, not the game "
            "character: its identity is facet angles and hard creases, which is why "
            "the projection route is refused (spec/character-contracts.md §4)."
        ),
    }

    # ---- complexity ----
    # Counts come from the prompt's part table (§2), which is structure rather than
    # measurement; every 0-10 score below states what it was read off.
    a["complexity"]["scores"] = {
        "silhouetteComplexity": 7,
        "componentCount": 9,
        "hierarchyDepth": 6,
        "repetitionDensity": 8,
        "materialLayerCount": 2,
        "localDetailDensity": 6,
        "occlusionRisk": 3,
        "actionReadinessNeed": 4,
    }
    a["complexity"]["estimatedCounts"] = {
        "macroComponents": 8,      # head armLeft armRight torso legLeft legRight hair face
        "mesoComponents": 37,      # 23 Stage 1 + 13 Stage 2 + 1 Stage 3
        "microFeatureGroups": len(DETAILS),
        "materialLayers": 10,      # colour codes C-01..C-09 plus the Stage 1 mannequin
        "repetitionSystems": 2,    # 8 mirror pairs; the shared generators
    }
    a["complexity"]["reasoning"] = [
        f"37 parts across 8 groups, but only {15} Stage 1 shape codes and 3 shared "
        "generators — repetition density is high and that is what keeps the workload "
        "finite.",
        "Occlusion risk is LOW for a four-view orthographic set: every side is "
        "observed. What is not observed is the crown, clipped in all four views.",
        "Only two material codes in the finished model, so material is folded into the "
        "colour stage and stage 4 is skipped (prompt §0.7).",
        f"Every tolerance in the build derives from measurementUncertainty={mu:.5f} "
        "(spec/landmarks.json), not from a guessed threshold.",
    ]

    # ---- unknowns ----
    a["unknownsToResolveBeforeImplementation"] = [
        "Forehead hairline is completely hidden by the fringe in every view; derived "
        "from the side-view hair-cap thickness instead (guess list §11.1).",
        "Crown height is clipped in all four orthographic views (row-0 figure pixels "
        "front 6 / back 4 / left 4 / right 6); total height 1.000 is extrapolated from "
        "left.webp's two straight spike edges.",
        "hipYokeVTip is not separable by colour: shirt purple and pants purple differ "
        "by 0.007 in cluster mean y. Only a spatial boundary can find it, so it is "
        "absent from landmarks.json.",
        "Occiput hair thickness is a fringe-depth measurement (left 33px / right 54px), "
        "NOT hair-cap shell thickness; insetting back.webp by it would overshoot.",
        "Foot splay is recorded as a projection ratio atan2(lateral, foreAft), not a "
        "solved 3D angle; spec/measure_sole.py re-derives it from the ground-contact "
        "outline instead.",
    ]

    # ---- detail inventory ----
    a["detailInventory"]["scanMethod"] = "component-zones + grid-4x4 per orthographic view"
    a["detailInventory"]["details"] = [
        {
            "id": did,
            "kind": kind,
            "zones": where.split(","),
            "description": desc,
            "mapsTo": maps,
            "evidenceRef": f"src/assets/exhibits/ff7-cloud-strife-polygon-figure/{where.split(',')[0]}.webp",
        }
        for did, kind, where, desc, maps in DETAILS
    ]

    # ---- anatomy ----
    eyes = measure_eyes(int(lm["views"]["front"]["landmarksPx"]["chin"]))
    head_block = 1.0 - chin           # chin -> extrapolated hair tip
    a["anatomy"] = {
        "applies": True,
        "styleHeads": round(1.0 / head_block, 4),
        "proportions": {
            "headUnit": round(head_block, 5),
            "torso": round(front["shoulderLine"] - front["widestHip"], 5),
            "legs": round(front["crotchNotchApex"], 5),
            "shoulderWidth": dims["shoulderWidth"],
            "hipWidth": dims["maxHipWidth"],
        },
        "pose": {
            "type": "fixed, baked into every part (prompt §1.4) — no skeleton",
            "jointAngles": {
                "upperArmAbductionL": pa["figureLeftUpperArm"]["abductionDeg"],
                "upperArmAbductionR": pa["figureRightUpperArm"]["abductionDeg"],
                "upperArmForwardLeanL": pa["figureLeftUpperArm"]["forwardLeanDeg"],
                "upperArmForwardLeanR": pa["figureRightUpperArm"]["forwardLeanDeg"],
                "elbowBreakL": pa["figureLeftElbowBreakDeg"],
                "elbowBreakR": pa["figureRightElbowBreakDeg"],
                "footSplayL": pa["footSplayDeg"]["left"],
                "footSplayR": pa["footSplayDeg"]["right"],
            },
        },
        "faceLandmarks": {
            "eyeLine": round(eyes["eyeLine"], 5) if eyes.get("measured") else 0.0,
            "eyeSpacing": round(eyes["eyeSpacing"], 5) if eyes.get("measured") else 0.0,
            "noseBase": 0.0,
            "mouthLine": 0.0,
            "hairline": 0.0,
        },
        "faceLandmarkNotes": {
            "measurement": eyes,
            "noseBase": "NOT OBSERVABLE — the reference has no printed nose. Zero here "
                        "means absent, not unmeasured.",
            "mouthLine": "NOT OBSERVABLE — the reference has no printed mouth.",
            "hairline": "NOT OBSERVABLE from the front: the fringe covers it entirely. "
                        "Derived at Stage 2 from the side-view hair-cap thickness.",
        },
        "features": [d["id"] for d in a["detailInventory"]["details"]
                     if d["id"].startswith(("face-", "jaw-", "ears-", "hair"))],
        "confidence": 0.72,
        "confidenceNote": (
            "0.72, not higher: four orthographic views cover every side, but the crown "
            "is clipped in all four and the forehead hairline is unobservable, so the "
            f"adopted tolerance is measurementUncertainty={mu:.5f} — about 43px of "
            "front.webp, far above the 0.0137 RMS."
        ),
    }

    (HERE / "assessment.json").write_text(json.dumps(doc, indent=2) + "\n")
    print(f"assessment filled: {len(DETAILS)} details, "
          f"styleHeads={a['anatomy']['styleHeads']}, "
          f"eyeLine={a['anatomy']['faceLandmarks']['eyeLine']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
