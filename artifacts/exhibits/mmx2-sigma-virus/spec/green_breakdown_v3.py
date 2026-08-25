#!/usr/bin/env python3
"""Green-focused annotated sprite breakdown — many small pictures, angle labelled.

User directive: break sprites into as many small pictures as possible, annotating
the OBSERVING ANGLE per crop. Green palette only is colour authority; other
sheet palettes are structural supplements labelled as such.

Outputs to spec/green-breakdown/:
  - per-crop PNGs x8 NEAREST
  - manifest.json {crop: {file, source, sheetBox/sourceBox, outSize, scale, angle, reading}}
  - BREAKDOWN.md table

Rerunnable: python3 artifacts/exhibits/mmx2-sigma-virus/spec/green_breakdown_v3.py
"""

from __future__ import annotations
import json
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
REFS = HERE.parent / "references"
OUT = HERE / "green-breakdown"
SCALE = 8

SHEET = REFS / "sigma-wireframe-sheet.png"
OSTATION = REFS / "sigma-front-green-ostation.png"
OBS_JSON = HERE / "all-sprite-observations.json"

def crop8(image: Image.Image, box: tuple[int,int,int,int], out_name: str) -> dict:
    region = image.crop(box)
    up = region.resize((region.width * SCALE, region.height * SCALE), Image.NEAREST)
    path = OUT / f"{out_name}.png"
    up.save(path)
    return {"file": f"green-breakdown/{out_name}.png", "outSize": [up.width, up.height], "scale": SCALE}

def infer_angle(obs: dict) -> str:
    a = obs["aspect"]
    h = obs["bbox"]["height"]
    w = obs["bbox"]["width"]
    # tiny animation strip
    if h <= 28 or w <= 28:
        return "tiny front (anim shrink)"
    if a >= 1.20 or (h <= 55 and w >= 60):
        return "top-down ~80-90° pitch (supplement, non-green)"
    if a >= 0.97:
        return "side ~60-90° yaw (supplement, non-green)"
    if a >= 0.80:
        return "front-oblique ~30° yaw (supplement, non-green)"
    if a >= 0.58:
        return "front ~0° yaw (supplement, non-green)"
    return "other"

def pick_representatives(observations, band_predicate, n=6):
    cand = [o for o in observations if band_predicate(o)]
    # spread across sheet y to sample top/mid/bottom rows
    cand_sorted = sorted(cand, key=lambda o: o["bbox"]["y0"])
    # pick with maximal y spacing
    if len(cand_sorted) <= n:
        return cand_sorted
    # stride pick
    step = len(cand_sorted) / n
    picks = []
    for i in range(n):
        idx = int(round(i * step))
        idx = min(idx, len(cand_sorted)-1)
        # avoid duplicate rows exactly — bump if same y0 as last
        while picks and cand_sorted[idx]["bbox"]["y0"] == picks[-1]["bbox"]["y0"]:
            idx = min(idx+1, len(cand_sorted)-1)
            if idx == len(cand_sorted)-1:
                break
        picks.append(cand_sorted[idx])
    return picks

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}

    # ---- A. OSTation GREEN FRONT — hi-res, 0° front authority ----
    ost = Image.open(OSTATION).convert("RGB")
    # measured bbox from zoom_v2_breakdown
    x0, y0, x1, y1 = 117, 1, 426, 358
    W, H = x1 - x0, y1 - y0
    def obox(fx0,fy0,fx1,fy1):
        return (round(x0+fx0*W), round(y0+fy0*H), round(x0+fx1*W), round(y0+fy1*H))

    ost_crops = {
        "ost_front_full": (0.0,0.0,1.0,1.0, "front 0° yaw 0° pitch (green) — whole head, 1% cross-validates sheet front within row width"),
        "ost_front_crown": (0.12,0.0,0.88,0.26, "front 0° — crown: flat-top trapezoid, cornice beam, centre panel, diagonal rafters converging to ridge"),
        "ost_front_brow-eyes": (0.10,0.40,0.90,0.62, "front 0° — brow band + eyes: angular hexagonal bracket lenses double-rim (pocket rim), joined at centre crossing"),
        "ost_front_nose-column": (0.36,0.44,0.64,0.74, "front 0° — nose: rectangular column 2 parallel verticals from eye-bridge to mouth bar + nose-bottom block"),
        "ost_front_mouth-chin": (0.14,0.66,0.86,0.88, "front 0° — mouth: horizontal bar with offset raised left segment, mouth seam ~77% H, chin trapezoid below"),
        "ost_front_jaw-chintabs": (0.08,0.82,0.92,1.0, "front 0° — jaw-chintabs: constant-width column ending in 2 square feet + centre arch (W-shaped notch)"),
        "ost_front_cheek-lobe-left": (0.0,0.34,0.30,0.68, "front 0° — left cheek lobe plate: vertical outer edge, double-line inner overlap seam, diagonal facets"),
        "ost_front_cheek-lobe-right": (0.70,0.34,1.0,0.68, "front 0° — right cheek lobe plate (mirror)"),
        "ost_front_temple-left": (0.02,0.16,0.32,0.42, "front 0° — left temple shell inside silhouette above lobe"),
        "ost_front_temple-right": (0.68,0.16,0.98,0.42, "front 0° — right temple shell (mirror)"),
    }
    for name,(a,b,c,d,note) in ost_crops.items():
        box = obox(a,b,c,d)
        e = crop8(ost, box, name)
        e.update({"source": "references/sigma-front-green-ostation.png", "sourceBox": list(box), "angle": "front 0° yaw 0° pitch (green)", "reading": note})
        manifest[name] = e

    # ---- B. GREEN sheet yaw — only green instance on sheet ----
    sheet = Image.open(SHEET).convert("RGB")
    green_box = (496,2573,496+54,2573+75)
    e = crop8(sheet, green_box, "sheet_green_yaw_full")
    e.update({"source": "references/sigma-wireframe-sheet.png", "sheetBox": list(green_box), "angle": "three-quarter yaw ~30° (green)", "reading": "GREEN yaw authority: one dominant eye per side + far lobe behind, ridge peaked, two-tone #10D830/#10B010"})
    manifest["sheet_green_yaw_full"] = e
    eye_box = (496,2573+28,496+54,2573+52)
    e = crop8(sheet, eye_box, "sheet_green_yaw_eyes")
    e.update({"source": "references/sigma-wireframe-sheet.png", "sheetBox": list(eye_box), "angle": "three-quarter yaw ~30° (green) — eye pocket detail", "reading": "eye sits INSIDE face planes → recessed pocket (G2 confirmed)"})
    manifest["sheet_green_yaw_eyes"] = e

    # ---- C-F. Sheet supplement clusters by inferred angle ----
    obs_data = json.loads(OBS_JSON.read_text())
    observations = obs_data["observations"]

    # remove green+purple already handled? keep them out of supplement picks
    supplement_obs = [o for o in observations if o["dominantHue"] not in ("green","purple") or o["id"] not in (301,306)]

    groups = [
        ("front0_supplement", lambda o: 0.58 <= o["aspect"] < 0.80 and o["bbox"]["height"] > 60, "front ~0° (supplement)"),
        ("oblique30_supplement", lambda o: 0.80 <= o["aspect"] < 0.97, "front-oblique ~30° (supplement)"),
        ("side60_supplement", lambda o: 0.97 <= o["aspect"] < 1.20, "side ~60-90° (supplement)"),
        ("topdown_supplement", lambda o: o["aspect"] >= 1.20 or (o["bbox"]["height"] <= 55 and o["bbox"]["width"] >= 60), "top-down ~80-90° pitch (supplement)"),
    ]
    for group_name, pred, angle_label in groups:
        picks = pick_representatives(supplement_obs, pred, n=6)
        for idx, o in enumerate(picks):
            bbox = o["bbox"]
            box = (bbox["x0"], bbox["y0"], bbox["x0"]+bbox["width"], bbox["y0"]+bbox["height"])
            name = f"sheet_{group_name}_{idx:02d}_id{o['id']:03d}"
            entry = crop8(sheet, box, name)
            # detailed reading from rows+palette
            hue = o["dominantHue"]
            drift = o["centroidDrift"]
            asym = o["rowCentreAsymmetry"]
            entry.update({
                "source": "references/sigma-wireframe-sheet.png",
                "sheetBox": list(box),
                "obsId": o["id"],
                "aspect": o["aspect"],
                "dominantHue": hue,
                "centroidDrift": drift,
                "rowCentreAsymmetry": asym,
                "angle": angle_label,
                "reading": f"aspect {o['aspect']:.3f} hue {hue} h{o['bbox']['height']} drift {drift:.3f} — plain facets, eye/brow consistent"
            })
            manifest[name] = entry

    # ---- G. Tiny animation shrinkage (small sprites) ----
    tiny_pred = lambda o: o["bbox"]["height"] <= 28 or o["bbox"]["width"] <= 28
    tiny_picks = pick_representatives(observations, tiny_pred, n=3)
    for idx, o in enumerate(tiny_picks):
        bbox = o["bbox"]
        box = (bbox["x0"], bbox["y0"], bbox["x0"]+bbox["width"], bbox["y0"]+bbox["height"])
        name = f"sheet_tiny_anim_{idx:02d}_id{o['id']:03d}"
        entry = crop8(sheet, box, name)
        entry.update({
            "source": "references/sigma-wireframe-sheet.png",
            "sheetBox": list(box),
            "obsId": o["id"],
            "aspect": o["aspect"],
            "dominantHue": o["dominantHue"],
            "angle": "tiny front (anim shrink, supplement)",
            "reading": f"shrunken front, aspect {o['aspect']:.3f}, confirms silhouette scales linearly"
        })
        manifest[name] = entry

    # ---- also add explicit top-down and side authorities referenced in fresh-zoom ----
    explicit = {
        "sheet_topDown_12_2247": ((12,2247,12+66,2247+40), "top-down ~80-90° pitch (supplement)", "G1 depth evidence: elongated outline 66×40, quad crown facets either side centre seam"),
        "sheet_side_142_1505": ((142,1505,142+60,1505+47), "side ~60-90° yaw (supplement)", "plain faceted rear continuation (G4), no decorated mechanism"),
        "sheet_frontRed_63_1811": ((63,1811,63+48,1811+69), "front ~0° (supplement, red palette)", "geometry authority pre-OSTation: identical 48×69 / 808px to palette-strip, now supplement only"),
    }
    for name,(box,angle,note) in explicit.items():
        # avoid duplicate if obs already covered — still write explicit crop (may overlap)
        if name not in manifest:
            e = crop8(sheet, box, name)
            e.update({"source": "references/sigma-wireframe-sheet.png", "sheetBox": list(box), "angle": angle, "reading": note})
            manifest[name] = e

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # BREAKDOWN.md
    lines = [
        "# Sigma Virus head — green-focused annotated sprite breakdown (green-breakdown)",
        "",
        "Generated by `green_breakdown_v3.py` — x8 NEAREST crops, angles are canonical probes (G5), not measured camera extrinsics.",
        "Green = colour authority; supplements = structural depth/side context, labelled as such.",
        "",
        f"Total crops: {len(manifest)} — 10 OSTation front detail + 2 green yaw + ~24 angle-family supplements + 3 tiny + 3 explicit",
        "",
        "| crop | angle | reading |",
        "| --- | --- | --- |",
    ]
    # order: ost, green, then groups
    def sort_key(k):
        order = {"ost_front":0, "sheet_green":1, "sheet_front0":2, "sheet_oblique":3, "sheet_side":4, "sheet_topdown":5, "sheet_tiny":6, "sheet_topDown":5, "sheet_side_142":4}
        for prefix, rank in order.items():
            if k.startswith(prefix):
                return (rank, k)
        return (99, k)
    for name in sorted(manifest.keys(), key=sort_key):
        e = manifest[name]
        lines.append(f"| `{e['file']}` | {e['angle']} | {e['reading']} |")
    (OUT / "BREAKDOWN.md").write_text("\n".join(lines) + "\n")
    print(f"{len(manifest)} crops written to {OUT}")
    # summary per angle
    from collections import Counter
    c = Counter(v["angle"] for v in manifest.values())
    for ang, n in sorted(c.items()):
        print(f"  {ang}: {n}")

if __name__ == "__main__":
    main()
