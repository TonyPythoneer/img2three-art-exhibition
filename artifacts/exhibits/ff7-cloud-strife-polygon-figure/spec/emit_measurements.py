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


def num(value: float) -> str:
    return repr(round(float(value), 8))


def main() -> None:
    y = CONST["socketChainY"]
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
    ]
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT.relative_to(REPO)} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
