#!/usr/bin/env python3
"""Measure waist (belt) band dimensions from the four orthographic references.

The belt is a flat band wrapping all the way round, standing proud of both the
chest above and the pelvis below.

Measurements:
  a) width (model X) from front view at the belt midpoint
  b) depth (model Z) from profile views at the belt midpoint
  c) proud margins: how far the belt stands proud of chest and pelvis sections

The proud margins require the chest and pelvis silhouettes at the belt zone,
neither of which is built yet. Measure them from the reference silhouettes
at the belt top and bottom rows.
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

    # ═══════ a) WIDTH (model X) from front view ═══════
    fv = views["front"]
    fd = LM["views"]["front"]["landmarksPx"]
    belt_top = fd["beltTop"]
    belt_bot = fd["beltBottom"]
    belt_mid = int((belt_top + belt_bot) / 2)

    # Belt width: measure silhouette at the belt midpoint
    ext = fv.row_extent(belt_mid)
    belt_width_px = (ext[1] - ext[0] + 1) if ext else 0
    belt_width = belt_width_px / UNIT["front"]

    # Also measure at belt top and bottom for cross-check
    ext_top = fv.row_extent(belt_top)
    ext_bot = fv.row_extent(belt_bot)
    belt_top_width = (ext_top[1] - ext_top[0] + 1) / UNIT["front"] if ext_top else 0
    belt_bot_width = (ext_bot[1] - ext_bot[0] + 1) / UNIT["front"] if ext_bot else 0

    # ═══════ b) DEPTH (model Z) from profile views ═══════
    depths_px: dict[str, float] = {}
    depth_per_view: dict[str, float] = {}
    for vname in ("left", "right"):
        v = views[vname]
        dd = LM["views"][vname]["landmarksPx"]
        bt = dd["beltTop"]
        bb = dd["beltBottom"]
        bm = int((bt + bb) / 2)
        ext = v.row_extent(bm)
        if ext:
            depths_px[vname] = ext[1] - ext[0] + 1
            depth_per_view[vname] = depths_px[vname] / UNIT[vname]

    belt_depth = sum(depth_per_view.values()) / len(depth_per_view) if depth_per_view else 0
    depth_spread = max(depth_per_view.values()) - min(depth_per_view.values()) if len(depth_per_view) > 1 else 0

    # ═══════ c) PROUD MARGINS ═══════
    # The belt stands proud of both chest (above) and pelvis (below).
    # Measure the silhouette width of the chest section at belt top and the
    # pelvis section at belt bottom, then compare against the belt width.
    proud_margins: dict[str, dict] = {}

    for vname in ("front", "back"):
        v = views[vname]
        dd = LM["views"][vname]["landmarksPx"]
        bt = dd["beltTop"]
        bb = dd["beltBottom"]

        # Chest section: measure at belt top - 1 (just above the belt)
        chest_row = max(0, bt - 1)
        chest_ext = v.row_extent(chest_row)
        chest_w = (chest_ext[1] - chest_ext[0] + 1) / UNIT[vname] if chest_ext else 0

        # Pelvis section: measure at belt bottom + 1 (just below the belt)
        pelvis_row = min(v.h - 1, bb + 1)
        pelvis_ext = v.row_extent(pelvis_row)
        pelvis_w = (pelvis_ext[1] - pelvis_ext[0] + 1) / UNIT[vname] if pelvis_ext else 0

        # Belt width at this view's midpoint
        belt_ext = v.row_extent(int((bt + bb) / 2))
        belt_w = (belt_ext[1] - belt_ext[0] + 1) / UNIT[vname] if belt_ext else 0

        proud_margins[vname] = {
            "chestWidth": round(chest_w, 8),
            "pelvisWidth": round(pelvis_w, 8),
            "beltWidth": round(belt_w, 8),
            "proudOfChest": round(belt_w - chest_w, 8),
            "proudOfPelvis": round(belt_w - pelvis_w, 8),
        }

    # Average proud margins across views
    avg_proud_chest = sum(d["proudOfChest"] for d in proud_margins.values()) / len(proud_margins)
    avg_proud_pelvis = sum(d["proudOfPelvis"] for d in proud_margins.values()) / len(proud_margins)

    # ═══════ Height ═══════
    belt_height = (belt_top - belt_bot) / UNIT["front"]  # positive since beltTop is above beltBot

    # ═══════ Report ═══════
    print("=" * 60)
    print("WAIST (BELT) MEASUREMENT")
    print("=" * 60)

    print(f"\n--- Width (X) ---")
    print(f"  front mid: {belt_width:.6f}")
    print(f"  front top: {belt_top_width:.6f}")
    print(f"  front bot: {belt_bot_width:.6f}")

    print(f"\n--- Depth (Z) ---")
    for vn, d in depth_per_view.items():
        print(f"  {vn}: {depths_px[vn]:.1f}px -> {d:.6f}")
    print(f"  adopted:   {belt_depth:.6f}")
    print(f"  spread:    {depth_spread:.6f} (< MU {MU:.5f}: {'PASS' if depth_spread < MU else 'REVIEW'})")

    print(f"\n--- Height (Y) ---")
    print(f"  belt height: {belt_height:.6f}")

    print(f"\n--- Proud margins ---")
    for vn, m in proud_margins.items():
        print(f"  {vn}: belt={m['beltWidth']:.6f} chest={m['chestWidth']:.6f} "
              f"pelvis={m['pelvisWidth']:.6f} "
              f"proud-of-chest={m['proudOfChest']:+.6f} proud-of-pelvis={m['proudOfPelvis']:+.6f}")
    print(f"  avg proud of chest: {avg_proud_chest:+.6f}")
    print(f"  avg proud of pelvis: {avg_proud_pelvis:+.6f}")

    # Write to landmarks.json
    waist = {
        "generatedBy": "spec/measure_waist.py",
        "widthX": {
            "normalized": round(belt_width, 8),
            "perView": {"front": round(belt_width, 8)},
            "frontTop": round(belt_top_width, 8),
            "frontBottom": round(belt_bot_width, 8),
        },
        "depthZ": {
            "normalized": round(belt_depth, 8),
            "perView": {k: round(v, 8) for k, v in depth_per_view.items()},
        },
        "heightY": round(belt_height, 8),
        "proudMargins": {
            "perView": proud_margins,
            "avgProudOfChest": round(avg_proud_chest, 8),
            "avgProudOfPelvis": round(avg_proud_pelvis, 8),
        },
        "crossViewSpread": {
            "width": 0.0,  # single front view only
            "depth": round(depth_spread, 8),
        },
    }

    LM.setdefault("parts", {})["waist"] = waist
    (HERE / "landmarks.json").write_text(json.dumps(LM, indent=2) + "\n")
    print(f"\nWrote parts.waist to landmarks.json")
    print(json.dumps(waist, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
