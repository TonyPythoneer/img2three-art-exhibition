#!/usr/bin/env python3
"""Measure ankle cuff section + fore-aft offset, following measure_sole.py's shape.

Two things to measure:
  a) cuff cross-section (width in X, depth in Z) — must exceed straightPantTubeWidth
  b) fore-aft offset of cuff center vs sole center — the soleTop socket's z component

The profile view silhouette at the cuff rows shows the TOTAL figure depth, but both
legs are at the same Z position (the ankles share the same zOffset), so the silhouette
is just one cuff's depth.

For the fore-aft offset: in the profile view, measure the cuff center's image-X
position relative to the sole center's image-X position, then convert to model Z.
"""
from __future__ import annotations

import json
from pathlib import Path

import refmask as R

HERE = Path(__file__).resolve().parent
LM = json.loads((HERE / "landmarks.json").read_text())
MU = LM["measurementUncertainty"]
RMS = LM["normalization"]["sole->chin"]["measurementUncertaintyRms"]
SOLE = LM["parts"]["sole"]

# Normalization: px per model unit for each view
UNIT = {}
for vname in ("front", "back", "left", "right"):
    px = LM["views"][vname]["landmarksPx"]
    span = LM["normalization"]["sole->chin"]["spanNormalized"]
    UNIT[vname] = (px["sole"] - px["chin"]) / span


def main() -> int:
    views = {k: R.load(k) for k in ("front", "back", "left", "right")}

    # ═══════ a) CUFF CROSS-SECTION ═══════
    # Front view: cuff width (model X) per foot.
    fv = views["front"]
    fd = LM["views"]["front"]["landmarksPx"]
    cuff_top_f = fd["bootCuffTopHighest"]
    cuff_bot_f = fd["sole"]

    # Measure each foot's width at the cuff rows. Two runs = two feet.
    foot_widths = []  # (row, foot_index, width_px, x0, x1)
    for y in range(cuff_top_f, min(cuff_top_f + 30, cuff_bot_f + 1)):
        runs = fv.row_runs(y)
        for i, (x0, x1) in enumerate(runs):
            w = x1 - x0 + 1
            if w > 20:
                foot_widths.append((y, i, w, x0, x1))

    # The cuff width per foot: take the median of the widest plateau
    if foot_widths:
        max_w = max(e[2] for e in foot_widths)
        plateau = [e for e in foot_widths if max_w - e[2] <= 2]
        cuff_width_px = max_w
        cuff_width_norm = cuff_width_px / UNIT["front"]
    else:
        cuff_width_norm = 0

    # Pant tube width (model X): midway between pantLegCrease and pantHem
    pt_row = int((fd["pantLegCrease"] + fd["pantHem"]) / 2)
    pt_runs = fv.row_runs(pt_row)
    pant_widths = [(r[1] - r[0] + 1) for r in pt_runs if (r[1] - r[0] + 1) > 20]
    pant_width_norm = (sorted(pant_widths)[len(pant_widths) // 2] / UNIT["front"]) if pant_widths else 0

    # Profile views: cuff depth (model Z) and fore-aft offset
    profile_data = {}
    for vname in ("left", "right"):
        v = views[vname]
        dd = LM["views"][vname]["landmarksPx"]
        ct = dd["bootCuffTopHighest"]
        cb = dd["sole"]
        u = UNIT[vname]

        # Cuff silhouette at the cuff zone (rows ct to ct+30)
        cuff_rows = []
        for y in range(ct, min(ct + 30, cb + 1)):
            runs = v.row_runs(y)
            for x0, x1 in runs:
                w = x1 - x0 + 1
                if w > 10:
                    cuff_rows.append((y, w, x0, x1))

        if not cuff_rows:
            continue

        # Max cuff depth and its center
        max_d = max(e[1] for e in cuff_rows)
        plateau = [e for e in cuff_rows if max_d - e[1] <= 2]
        cuff_cx_img = sum((e[2] + e[3]) / 2 for e in plateau) / len(plateau)

        # Sole silhouette at its widest point (rows cb-5 to cb)
        sole_rows = []
        for y in range(max(0, cb - 8), min(v.h, cb + 3)):
            runs = v.row_runs(y)
            for x0, x1 in runs:
                w = x1 - x0 + 1
                if w > 20:
                    sole_rows.append((y, w, x0, x1))

        if sole_rows:
            max_sole = max(e[1] for e in sole_rows)
            sole_plateau = [e for e in sole_rows if max_sole - e[1] <= 3]
            sole_cx_img = sum((e[2] + e[3]) / 2 for e in sole_plateau) / len(sole_plateau)
        else:
            sole_cx_img = cuff_cx_img

        # Fore-aft offset: cuff center vs sole center in image X
        # In left.webp: image +X = model -Z (back), so offset_img > 0 means cuff is backward
        # In right.webp: image +X = model +Z (forward), so offset_img > 0 means cuff is forward
        fwd_sign = -1.0 if vname == "left" else 1.0
        offset_img = cuff_cx_img - sole_cx_img
        offset_z = offset_img * fwd_sign / u  # positive = forward

        profile_data[vname] = {
            "cuffDepthPx": max_d,
            "cuffDepthNorm": max_d / u,
            "cuffCenterImg": round(cuff_cx_img, 1),
            "soleCenterImg": round(sole_cx_img, 1),
            "offsetImgPx": round(offset_img, 1),
            "offsetZ": round(offset_z, 6),
        }

    # Average across profile views
    depths = [v["cuffDepthNorm"] for v in profile_data.values()]
    cuff_depth_norm = sum(depths) / len(depths) if depths else 0
    depth_spread = max(depths) - min(depths) if len(depths) > 1 else 0

    # Pant tube depth from profile: measure silhouette at pant tube rows (above cuff)
    pant_depths = {}
    for vname in ("left", "right"):
        v = views[vname]
        dd = LM["views"][vname]["landmarksPx"]
        ct = dd["bootCuffTopHighest"]
        u = UNIT[vname]
        # The pant tube is above the cuff. Measure at 10 rows above cuff top.
        pant_rows = []
        for y in range(max(0, ct - 20), ct):
            runs = v.row_runs(y)
            for x0, x1 in runs:
                w = x1 - x0 + 1
                if w > 10:
                    pant_rows.append((y, w, x0, x1))
        if pant_rows:
            max_p = max(e[1] for e in pant_rows)
            pant_depths[vname] = max_p / u

    pant_depth_norm = sum(pant_depths.values()) / len(pant_depths) if pant_depths else 0

    # Fore-aft offset: average across views
    offsets = [v["offsetZ"] for v in profile_data.values()]
    fore_aft_offset = sum(offsets) / len(offsets) if offsets else 0
    offset_spread = max(offsets) - min(offsets) if len(offsets) > 1 else 0

    # ═══════ Report ═══════
    print("=" * 60)
    print("ANKLE (BOOT CUFF) MEASUREMENT")
    print("=" * 60)

    print(f"\n--- Cuff cross-section ---")
    print(f"  cuff width (X):     {cuff_width_norm:.6f} (must > pant {pant_width_norm:.6f})")
    print(f"  cuff depth (Z):     {cuff_depth_norm:.6f} (must > pant {pant_depth_norm:.6f})")
    print(f"  wider on X axis:    {'PASS' if cuff_width_norm > pant_width_norm else 'FAIL'}")
    print(f"  wider on Z axis:    {'PASS' if cuff_depth_norm > pant_depth_norm else 'FAIL'}")
    print(f"  depth spread:       {depth_spread:.6f} (< MU {MU:.5f}: {'PASS' if depth_spread < MU else 'REVIEW'})")

    print(f"\n--- Fore-aft offset ---")
    for vn, d in profile_data.items():
        print(f"  {vn}: cuff_cx={d['cuffCenterImg']} sole_cx={d['soleCenterImg']} "
              f"offset={d['offsetImgPx']}px -> z={d['offsetZ']:.6f}")
    print(f"  average z offset:   {fore_aft_offset:.6f}")
    print(f"  spread:             {offset_spread:.6f} (< MU {MU:.5f}: {'PASS' if offset_spread < MU else 'REVIEW'})")

    # Write to landmarks.json
    ankle = {
        "generatedBy": "spec/measure_ankle.py",
        "cuffSection": {
            "widthX": {"normalized": round(cuff_width_norm, 8),
                        "vsPantTube": round(cuff_width_norm - pant_width_norm, 8)},
            "depthZ": {"normalized": round(cuff_depth_norm, 8),
                        "vsPantTube": round(cuff_depth_norm - pant_depth_norm, 8),
                        "perView": {k: round(v["cuffDepthNorm"], 8)
                                    for k, v in profile_data.items()}},
            "pantTubeWidthX": round(pant_width_norm, 8),
            "pantTubeDepthZ": round(pant_depth_norm, 8),
            "widerOnBothAxes": cuff_width_norm > pant_width_norm and cuff_depth_norm > pant_depth_norm,
            "crossViewSpread": round(depth_spread, 8),
        },
        "foreAftOffset": {
            "value": round(fore_aft_offset, 8),
            "perView": {k: v["offsetZ"] for k, v in profile_data.items()},
            "crossViewSpread": round(offset_spread, 8),
        },
        "raw": {vn: d for vn, d in profile_data.items()},
    }

    LM.setdefault("parts", {})["ankle"] = ankle
    (HERE / "landmarks.json").write_text(json.dumps(LM, indent=2) + "\n")
    print(f"\nWrote parts.ankle to landmarks.json")
    print(json.dumps(ankle, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
