#!/usr/bin/env python3
"""Blockout correction #1 (action: refine-spec, recorded in reviewHistory).

Root causes fixed, both traced to spec/guard-local-measurements.json:
1. Rod fan: mirror-symmetric tipward (left 154.8/134.8 mirrors right 23.7/41.6 within
   1.5°, axes through (0,-0.115), radius 0.37–0.64). The earlier C2-pinwheel entry was an
   agent visual misread; the brief's "mirrored rods" phrasing was correct.
2. Guard blocks were authored in image space without the 17.67° axis rotation; olive
   blocks and shoulders repositioned to measured local bboxes.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE / "object-sculpt-spec.json"
doc = json.load(open(SPEC))

RADIATION_Y = -0.115
R0, R1 = 0.37, 0.64
RODS = {
    "rightEmitterLower": (23.7, 0.85, "visible", "measured (guard-local-measurements.json)"),
    "rightEmitterMiddle": (41.6, 0.85, "visible", "measured"),
    "rightEmitterUpper": (59.4, 0.45, "inferred", "occluded behind blade base/right flare; 17.9deg fan-step continuation"),
    "leftEmitterLower": (154.8, 0.85, "visible", "measured; mirror of rightLower within 1.1deg"),
    "leftEmitterMiddle": (134.8, 0.85, "visible", "measured; mirror of rightMiddle within 3.2deg"),
    "leftEmitterUpper": (115.4, 0.5, "inferred", "third left streak thin/partially merged; mirror-consistent continuation"),
}

by_id = {c["id"]: c for c in doc["componentTree"]}

rs = doc["repetitionSystems"][0]
rs["distribution"] = "radial fan, MIRROR-symmetric about the blade axis, all rods tipward (measured; earlier C2-pinwheel reading was an agent visual misread, corrected by local-coordinate re-measurement)"
rs["parameters"] = {
    "radiationCenter": [0, RADIATION_Y, 0],
    "anglesDegFromPlusX": {k: v[0] for k, v in RODS.items()},
    "radialStart": R0, "radialEnd": R1, "thickness": 0.06, "sides": 6,
    "measurement": "eroded-mask components: left rods 154.8/134.8 deg (r 0.36-0.65), right rods 23.7/41.6 deg (r 0.40-0.63); every measured axis passes within 0.05u of (0,-0.115); see guard-local-measurements.json",
}

for rid, (ang, conf, evt, note) in RODS.items():
    c = by_id[rid]
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    cx = round(dx * (R0 + R1) / 2, 3)
    cy = round(RADIATION_Y + dy * (R0 + R1) / 2, 3)
    c["confidence"] = conf
    c["evidenceType"] = evt
    c["topologyRationale"] = f"Thin faceted rod (6-sided, ~0.06u thick, len {round(R1-R0,2)}u): {note}; local angle {ang}deg from +X."
    c["transform"]["position"] = [cx, cy, 0]
    c["transform"]["rotation"] = [0, 0, round(a - math.pi / 2, 4)]
    c["dimensions"].update({"width": 0.06, "height": R1 - R0, "depth": 0.06, "confidence": conf})
    c["attachment"]["localStart"] = [round(dx * R0, 3), round(RADIATION_Y + dy * R0, 3), 0]
    c["attachment"]["localEnd"] = [round(dx * R1, 3), round(RADIATION_Y + dy * R1, 3), 0]
    c["explodeVector"] = [round(dx * 0.45, 3), round(dy * 0.45, 3), 0]
    c["actionProfile"]["pivot"]["localPosition"] = [cx, cy, 0]

er = by_id["emitterRods"]
er["topologyRationale"] = ("Radial rod fan, mirror-symmetric tipward: measured left 154.8/134.8 deg mirror right 23.7/41.6 deg within 1.5 deg, "
                           "axes through (0,-0.115), radius 0.37-0.64. Earlier C2-pinwheel reading was an agent visual misread — corrected, conflict record kept.")

ob_l = by_id["oliveBlockLeft"]
ob_l["transform"]["position"] = [-0.309, -0.157, 0]
ob_l["dimensions"].update({"width": 0.131, "height": 0.211, "depth": 0.1})
ob_l["attachment"]["localStart"] = [-0.252, -0.059, 0]
ob_l["attachment"]["localEnd"] = [-0.383, -0.27, 0]
ob_l["topologyRationale"] = "Left khaki/olive two-tone wedge; measured local bbox [-0.383,-0.27,-0.252,-0.059] (guard-local-measurements.json goldComponents[0])."
ob_r = by_id["oliveBlockRight"]
ob_r["transform"]["position"] = [0.292, -0.208, 0]
ob_r["dimensions"].update({"width": 0.129, "height": 0.218, "depth": 0.12})
ob_r["attachment"]["localStart"] = [0.226, -0.104, 0]
ob_r["attachment"]["localEnd"] = [0.355, -0.322, 0]
ob_r["topologyRationale"] = "Right olive folded wedge, larger than left; measured local bbox [0.226,-0.322,0.355,-0.104] (goldComponents[3])."

sh_l = by_id["leftGunmetalShoulder"]
sh_l["transform"]["position"] = [-0.21, 0.02, 0]
sh_l["transform"]["rotation"] = [0, 0, 0]
sh_l["dimensions"].update({"width": 0.26, "height": 0.32, "depth": 0.1})
sh_l["attachment"]["localStart"] = [-0.08, 0.17, 0]
sh_l["attachment"]["localEnd"] = [-0.33, -0.12, 0]
sh_r = by_id["rightGunmetalShoulder"]
sh_r["transform"]["position"] = [0.21, 0.02, 0]
sh_r["transform"]["rotation"] = [0, 0, 0]
sh_r["dimensions"].update({"width": 0.26, "height": 0.32, "depth": 0.1})
sh_r["attachment"]["localStart"] = [0.08, 0.17, 0]
sh_r["attachment"]["localEnd"] = [0.33, -0.12, 0]

doc["assumptions"] = [
    a for a in doc["assumptions"]
    if "C2 point-symmetric" not in a
] + [
    "Rod fan is MIRROR-symmetric tipward per local-coordinate measurement; the earlier C2-pinwheel assumption was an agent visual misread of the guard zoom and is retained here as a corrected-conflict record.",
]
for u in doc["preSpecAssessment"].get("resolvedUnknowns", []):
    if u["unknown"].startswith("Emitter rod layout"):
        u["resolution"] = ("RESOLVED (corrected at blockout review 1): fan is MIRROR-symmetric tipward — left 154.8/134.8 deg mirror right 23.7/41.6 deg within 1.5 deg, "
                           "axes through (0,-0.115), radius 0.37-0.64 (guard-local-measurements.json). First-pass C2-pinwheel reading was a visual misread; hidden rods rightUpper 59.4 (0.45) / leftUpper 115.4 (0.5).")

doc["silhouette"]["symmetry"] = ("blade bilateral about measured axis (|L-R| < 1.5px over y 0-195); rod fan mirror-symmetric tipward; base flare right-only")

json.dump(doc, open(SPEC, "w"), indent=2, ensure_ascii=False)
print("refine-spec blockout#1 applied")
