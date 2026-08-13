#!/usr/bin/env python3
"""prompt.txt §3.1 — hand the part factories their measurements, as generated TypeScript.

    python3 spec/emit_measurements.py    # rewrites src/utils/cloudStrifeFigure/measurements.ts

§3.1 says "every part factory may only read from landmarks.json; magic numbers inside a
part file are forbidden". AGENTS.md says gate evidence under artifacts/ never enters the
bundle. Both hold at once only if the numbers are COPIED by a script: the factories import
a generated module, the module is generated from landmarks.json, and a drifted constant is
impossible because nobody types one.

Re-run this whenever a measurement lands. The generated file is checked in so the build
does not depend on artifacts/, and `spec/audit_records.py` reads it as a source, which is
only sound because this script is the sole thing that writes it.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OUT = REPO / "src/utils/cloudStrifeFigure/measurements.ts"

LM = json.loads((HERE / "landmarks.json").read_text())
CONST = json.loads((HERE / "build-constants.json").read_text())

NORM = LM["normalization"]["sole->chin"]
SOLE = LM["parts"]["sole"]
ANKLE = LM["parts"]["ankle"]
NECK = LM["parts"]["neck"]
WAIST = LM["parts"]["waist"]
LEG = LM["parts"]["pantLeg"]
PELVIS = LM["parts"]["pelvis"]
CHEST = LM["parts"]["chest"]
ARM = LM["parts"]["arm"]
HEAD = LM["parts"]["head"]

def num(value: float) -> str:
    return repr(round(float(value), 8))


def main() -> None:
    # The pant leg's four heights come from parts.pantLeg, not from build-constants.json.
    # build-constants had `hip` (0.271814) BELOW `kneeTop` (0.286825) and `calfTop`
    # (0.273084) — geometrically impossible, the hip cannot be under the knee — because
    # they were seeded from separate landmarks before the leg was fitted as one line.
    # spec/measure_pant_leg.py fits it once, so the four heights are monotonic and share a
    # source. Overriding here rather than editing build-constants keeps ONE writer.
    y = dict(CONST["socketChainY"])
    y.update(LEG["segmentHeights"]["chainY"])
    lines = [
        "// GENERATED FILE — do not edit.",
        "//",
        "// Source: artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/landmarks.json",
        "// Writer: artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/emit_measurements.py",
        "//",
        "// prompt.txt §3.1: a part factory reads its numbers from here and nowhere else.",
        "// Every value is normalized so the whole figure is 1.000 tall, ground at Y=0 (§1.1).",
        "",
        "/** Cross-view landmark agreement. NOT a per-part shape tolerance — see RMS. */",
        f"export const MEASUREMENT_UNCERTAINTY = {num(LM['measurementUncertainty'])};",
        "",
        "/**",
        " * The per-part shape tolerance. `MEASUREMENT_UNCERTAINTY` is about 43px of front.webp",
        " * against a 4.7px reference fit residual, so using it for a part's own shape would make",
        " * that gate vacuous (prompt §11, Stage 0 addition 3).",
        " */",
        f"export const MEASUREMENT_RMS = {num(NORM['measurementUncertaintyRms'])};",
        "",
        "/** S-01 soleSlab. `plan` is in the foot-local frame: +z toward the toe, +x toward the",
        "  * figure's left, origin at the slab's plan centre, bottom face on y=0. */",
        "export const SOLE = {",
        f"  lateralExtent: {num(SOLE['lateralExtent']['adopted'])},",
        f"  foreAftExtent: {num(SOLE['foreAftExtent']['adopted'])},",
        f"  thickness: {num(SOLE['thickness']['adopted'])},",
        f"  splayDeg: {num(SOLE['splayDeg']['derived'])},",
        "  plan: {",
        f"    heelWidth: {num(SOLE['planTrapezoid']['heelWidth'])},",
        f"    toeWidth: {num(SOLE['planTrapezoid']['toeWidth'])},",
        f"    length: {num(SOLE['planTrapezoid']['length'])},",
        f"    endChamfer: {num(SOLE['planTrapezoid']['endChamfer'])},",
        "  },",
        "} as const;",
        "",
        "/** The socket chain's heights, front view (prompt §4's ledger). */",
        "export const SOCKET_Y = {",
        *[f"  {k}: {num(v)}," for k, v in y.items()],
        "} as const;",
        "",
        "/** Half the gap between the two feet plus half a foot's width: where a sole sits in X. */",
        f"export const SOLE_CENTRE_X = {num(CONST['derived']['soleCentreX']['value'])};",
        "",
        "/** A-01 ankleCuff. Boot cuff: a prism whose section is LARGER than the pant tube it swallows. */",
        "export const ANKLE = {",
        f"  cuffWidthX: {num(ANKLE['cuffSection']['widthX']['normalized'])},",
        f"  cuffDepthZ: {num(ANKLE['cuffSection']['depthZ']['normalized'])},",
        f"  pantTubeWidthX: {num(ANKLE['cuffSection']['pantTubeWidthX'])},",
        f"  pantTubeDepthZ: {num(ANKLE['cuffSection']['pantTubeDepthZ'])},",
        f"  foreAftOffset: {num(ANKLE['foreAftOffset']['value'])},",
        f"  height: {num(y['ankleTop'] - y['soleTop'])},",
        "} as const;",
        "",
        "/**",
        " * S-03/S-04/S-05 collapsed. thigh, knee and calf are three stacked segments of ONE",
        " * near-square chamfered tube — §2 assigns shape codes from measured dimensions, not",
        " * from names, and below the crotch this leg's width varies by less than the",
        " * uncertainty over its whole length with no corner anywhere in it. The corner §4",
        " * describes IS the crotch: the outer slope is 0.53 dx/dy above it and 0.073 below.",
        " *",
        " * So the three factories share this one section and C0 continuity holds by",
        " * construction. Where the three segments MEET is not measurable — there is no",
        " * landmark between the crotch and the boot cuff and no width breakpoint — so the two",
        " * split heights are equal thirds and are a guess-list item.",
        " */",
        "export const PANT_LEG = {",
        f"  widthX: {num(LEG['sharedSection']['widthX'])},",
        f"  depthZ: {num(LEG['sharedSection']['depthZ'])},",
        f"  crotchY: {num(LEG['segmentHeights']['chainY']['hip'])},",
        f"  thighHeight: {num(y['hip'] - y['kneeTop'])},",
        f"  kneeHeight: {num(y['kneeTop'] - y['calfTop'])},",
        f"  calfHeight: {num(y['calfTop'] - y['ankleTop'])},",
        "} as const;",
        "",
        "/**",
        " * S-06 pelvisKite. The largest volume in the LOWER body and the part that decides its",
        " * silhouette. Front outline a pentagon, profile a front/back-symmetric kite.",
        " *",
        " * §4[6] also says 'the widest point must be WIDER THAN THE SHOULDERS'. Measured, that",
        " * is FALSE: hip 0.28325 against a shoulder line of 0.37978, a gap of 0.0965 against an",
        " * uncertainty of 0.05447 — decided, not undecided. It IS wider than the chest slab, by",
        " * 0.0851. §0.6 says the script wins, so these are the measured numbers.",
        " */",
        "export const PELVIS = {",
        f"  height: {num(PELVIS['adopted']['height'])},",
        f"  widthAtTop: {num(PELVIS['adopted']['widthAtTop'])},",
        f"  depthAtTop: {num(PELVIS['adopted']['depthAtTop'])},",
        f"  widestWidth: {num(PELVIS['adopted']['widestWidth'])},",
        f"  maxDepth: {num(PELVIS['adopted']['maxDepth'])},",
        "  /** How far BELOW pelvisTop the widest ring sits. */",
        f"  widestDrop: {num(PELVIS['adopted']['topHeight'] - PELVIS['adopted']['widestHeight'])},",
        f"  notchWidth: {num(PELVIS['adopted']['notchWidth'])},",
        f"  hipOffsetX: {num(PELVIS['hipSocketX']['adopted'])},",
        "} as const;",
        "",
        "/**",
        " * S-08 chestSlab, and the hub of §4's socket ledger — the only part emitting four.",
        " *",
        " * `widestDrop` is not zero: §4[8] says the slab is widest at the shoulder line, but AT",
        " * that row the shirt measures 0.00124 wide because up there the figure is neck, black",
        " * pauldron and bare deltoid. The widest row is 0.1186 below it.",
        " *",
        " * The depth/width ratio is 0.622 — a block, not the 'near-planar' sheet §4[8]",
        " * describes. Reported and not asserted: no 'slabness' threshold has been pinned with",
        " * a fake frame, and a guessed one would be worse than none.",
        " */",
        "export const CHEST = {",
        f"  height: {num(CHEST['adopted']['height'])},",
        f"  widestWidth: {num(CHEST['adopted']['widestWidth'])},",
        f"  widthAtWaistTop: {num(CHEST['adopted']['widthAtWaistTop'])},",
        f"  depthAtWidest: {num(CHEST['adopted']['depthAtWidest'])},",
        f"  depthAtWaistTop: {num(CHEST['adopted']['depthAtWaistTop'])},",
        f"  widestDrop: {num(CHEST['adopted']['topHeight'] - CHEST['adopted']['widestHeight'])},",
        f"  shoulderOffsetX: {num(CHEST['shoulderSocketX']['value'])},",
        "} as const;",
        "",
        "/**",
        " * S-09..S-13, the whole arm chain. ONE record because §4[10] makes upperDeltoid's",
        " * bottom hexagon IDENTICAL to lowerDeltoid's top, and §4[9] makes lowerDeltoid's quad",
        " * bottom identical to backArm's section — two shared sections that cannot be measured",
        " * from inside either part.",
        " *",
        " * The pose angles are the MEAN of the two sides. §1.4 bakes the pose in and §1.5 calls",
        " * these pure mirror pairs; the measured 8.8 deg forward-lean gap between the sides is",
        " * SMALLER than the 29.23 px residual of the fit that produced it, so the asymmetry is",
        " * not established and the mirror stands (parts.arm.mirror_1_4_vs_1_5).",
        " */",
        "export const ARM = {",
        f"  shoulderWidth: {num(ARM['sections']['shoulder']['width'])},",
        f"  shoulderDepth: {num(ARM['sections']['shoulder']['depth'])},",
        f"  deltoidWaistWidth: {num(ARM['sections']['deltoidWaist']['width'])},",
        f"  deltoidWaistDepth: {num(ARM['sections']['deltoidWaist']['depth'])},",
        f"  backArmWidth: {num(ARM['sections']['backArmTop']['width'])},",
        f"  backArmDepth: {num(ARM['sections']['backArmTop']['depth'])},",
        f"  elbowWidth: {num(ARM['sections']['elbow']['width'])},",
        f"  elbowDepth: {num(ARM['sections']['elbow']['depth'])},",
        f"  gloveWidth: {num(ARM['glove']['width'])},",
        "  /** The figure's LEFT wrist is the grey bracer. Measured 0.934, not §4[12]'s 1.05;",
        "    * the two wrists differ by 0.0063, far inside the uncertainty. */",
        f"  bracerWidthFactor: {num(ARM['bracer']['widthFactor'])},",
        f"  upperDeltoidHeight: {num(y['chestTop'] - y['deltoidWaist'])},",
        f"  lowerDeltoidHeight: {num(y['deltoidWaist'] - y['backArmTop'])},",
        f"  backArmHeight: {num(y['backArmTop'] - y['elbow'])},",
        f"  frontArmHeight: {num(y['elbow'] - y['fist'])},",
        f"  abductionDeg: {num(ARM['mirror_1_4_vs_1_5']['adoptedAbductionDeg'])},",
        f"  forwardLeanDeg: {num(ARM['mirror_1_4_vs_1_5']['adoptedForwardLeanDeg'])},",
        f"  elbowBreakDeg: {num(ARM['mirror_1_4_vs_1_5']['adoptedElbowBreakDeg'])},",
        "} as const;",
        "",
        "/** S-15 skull. Measured on the FACE (bare skin), never by insetting back.webp:",
        "  * hairThickness is a fringe depth, 0.03863 left vs 0.07137 right. */",
        "export const HEAD = {",
        f"  cheekboneWidth: {num(HEAD['adopted']['cheekboneWidth'])},",
        f"  cheekboneHeight: {num(HEAD['adopted']['cheekboneHeight'])},",
        f"  chinWidth: {num(HEAD['adopted']['chinWidth'])},",
        f"  exposedDepth: {num(HEAD['adopted']['exposedDepth'])},",
        "} as const;",
        "",
        "/** S-14 neckColumn. CylinderGeometry(r, r, h, radialSegments=8) with flatShading. */",
        "export const NECK = {",
        f"  radius: {num(NECK['cylinderRadius'])},",
        f"  height: {num(NECK['heightY']['normalized'])},",
        f"  radialSegments: 8,",
        "} as const;",
        "",
        "/** S-07 belt. A flat band standing proud of chest and pelvis. */",
        "export const WAIST = {",
        f"  widthX: {num(WAIST['widthX']['normalized'])},",
        f"  depthZ: {num(WAIST['depthZ']['normalized'])},",
        f"  height: {num(abs(WAIST['heightY']))},",
        "} as const;",
        "",
    ]
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT.relative_to(REPO)} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
