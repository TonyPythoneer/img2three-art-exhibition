#!/usr/bin/env python3
"""Measure neck cylinder dimensions from the four orthographic references.

The neck is a CylinderGeometry(r, r, h, radialSegments=8) with flatShading.

Uses the pre-measured neckWidthPx values from landmarks.json. The neck is a
cylinder, so width (X) = depth (Z) = 2*r. Profile views are unreliable for
depth because the chin/jaw silhouette overlaps the neck zone.

Cross-checks the measured height against the socket chain gap.
"""
from __future__ import annotations

import json
from pathlib import Path

import refmask as R

HERE = Path(__file__).resolve().parent
LM = json.loads((HERE / "landmarks.json").read_text())
MU = LM["measurementUncertainty"]

# Normalization: px per model unit for each view
UNIT = {}
for vname in ("front", "back", "left", "right"):
    px = LM["views"][vname]["landmarksPx"]
    span = LM["normalization"]["sole->chin"]["spanNormalized"]
    UNIT[vname] = (px["sole"] - px["chin"]) / span


def main() -> int:
    views = {k: R.load(k) for k in ("front", "back", "left", "right")}

    # ═══════ a) WIDTH (model X) from pre-measured neckWidthPx ═══════
    # neckWidthPx is already measured in measure_landmarks.py — it is the narrowest
    # run of the neck zone, not the entire figure width at the narrowest row.
    width_per_view: dict[str, float] = {}
    for vname in ("front", "back"):
        neck_px = LM["views"][vname].get("neckWidthPx")
        if neck_px:
            width_per_view[vname] = neck_px / UNIT[vname]

    neck_width = sum(width_per_view.values()) / len(width_per_view) if width_per_view else 0
    width_spread = max(width_per_view.values()) - min(width_per_view.values()) if len(width_per_view) > 1 else 0

    # ═══════ b) DEPTH (model Z) ═══════
    # The neck is a cylinder, so depth = width. Profile views are unreliable
    # because the chin/jaw silhouette overlaps the neck zone. Use the same
    # neckWidthPx values — for a cylinder the diameter is the same in all axes.
    neck_depth = neck_width
    depth_spread = width_spread  # same source, same spread

    # ═══════ c) HEIGHT (model Y) from front view ═══════
    fv = views["front"]
    fd = LM["views"]["front"]["landmarksPx"]
    chin_y = fd["chin"]        # neckTop
    shoulder_y = fd["shoulderLine"]  # chestTop
    neck_height_px = shoulder_y - chin_y
    neck_height = neck_height_px / UNIT["front"]

    # Socket chain gap
    socket_gap = LM["normalization"]["sole->chin"]["perView"]["front"]["chin"] - \
                 LM["normalization"]["sole->chin"]["perView"]["front"].get("shoulderLine", 0)
    gap_diff = abs(neck_height - socket_gap)

    # ═══════ Report ═══════
    print("=" * 60)
    print("NECK MEASUREMENT")
    print("=" * 60)

    print(f"\n--- Width (X) from neckWidthPx ---")
    for vn, w in width_per_view.items():
        neck_px = LM["views"][vn].get("neckWidthPx", "?")
        print(f"  {vn}: {neck_px}px -> {w:.6f}")
    print(f"  adopted:   {neck_width:.6f}")
    print(f"  spread:    {width_spread:.6f} (< MU {MU:.5f}: {'PASS' if width_spread < MU else 'REVIEW'})")

    print(f"\n--- Depth (Z) = width (cylinder symmetry) ---")
    print(f"  adopted:   {neck_depth:.6f}")

    print(f"\n--- Height (Y) ---")
    print(f"  front: {neck_height_px:.1f}px -> {neck_height:.6f}")
    print(f"  socket chain gap: {socket_gap:.6f}")
    print(f"  difference: {gap_diff:.6f} (< MU {MU:.5f}: {'PASS' if gap_diff < MU else 'REVIEW'})")
    if gap_diff > MU:
        print(f"  ⚠ MEASURED HEIGHT ({neck_height:.6f}) DISAGREES WITH SOCKET CHAIN ({socket_gap:.6f})")
        print(f"    by {gap_diff:.6f}, which exceeds measurementUncertainty {MU:.5f}")

    # Cylinder radius = diameter / 2
    cylinder_diameter = neck_width
    cylinder_radius = cylinder_diameter / 2

    print(f"\n--- Cylinder parameters ---")
    print(f"  diameter: {cylinder_diameter:.6f}")
    print(f"  radius:   {cylinder_radius:.6f}")
    print(f"  height:   {neck_height:.6f}")

    # Write to landmarks.json
    neck = {
        "generatedBy": "spec/measure_neck.py",
        "widthX": {
            "normalized": round(neck_width, 8),
            "perView": {k: round(v, 8) for k, v in width_per_view.items()},
        },
        "depthZ": {
            "normalized": round(neck_depth, 8),
            "note": "cylinder symmetry: depth = width",
        },
        "heightY": {
            "normalized": round(neck_height, 8),
            "socketChainGap": round(socket_gap, 8),
            "gapDifference": round(gap_diff, 8),
        },
        "cylinderRadius": round(cylinder_radius, 8),
        "crossViewSpread": {
            "width": round(width_spread, 8),
            "depth": round(depth_spread, 8),
        },
    }

    LM.setdefault("parts", {})["neck"] = neck
    (HERE / "landmarks.json").write_text(json.dumps(LM, indent=2) + "\n")
    print(f"\nWrote parts.neck to landmarks.json")
    print(json.dumps(neck, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
