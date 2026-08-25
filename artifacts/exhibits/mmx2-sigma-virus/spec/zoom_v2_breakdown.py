#!/usr/bin/env python3
"""From-scratch annotated sprite breakdown for the Sigma Virus head rebuild.

User directive (2026-08-22): break the reference sprites into as many small
pictures as possible, annotating the OBSERVATION ANGLE of each crop, to plan
the 3D reconstruction from.

Sources (all under artifacts/exhibits/mmx2-sigma-virus/references/):
  sigma-front-green-ostation.png  ADMITTED front view, green palette, hi-res
  sigma-wireframe-sheet.png       sprite sheet: red-front / top / side / green-yaw cells

Every crop is upscaled x8 NEAREST (pure repetition, no filtering) and named
<angle>_<region>.png. manifest.json records source + box + angle + reading per
crop; BREAKDOWN.md is the human-readable index.

Rerunnable: python3 zoom_v2_breakdown.py
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REFS = HERE.parent / "references"
OUT = HERE / "zoom-v2"
SCALE = 8

OSTATION = REFS / "sigma-front-green-ostation.png"
SHEET = REFS / "sigma-wireframe-sheet.png"


def crop8(image: Image.Image, box: tuple[int, int, int, int], name: str) -> dict:
    """box = (x0, y0, x1, y1) exclusive-right/bottom; saved x8 NEAREST."""
    region = image.crop(box)
    up = region.resize((region.width * SCALE, region.height * SCALE), Image.NEAREST)
    path = OUT / f"{name}.png"
    up.save(path)
    return {"file": f"zoom-v2/{name}.png", "sourceBox": list(box),
            "outSize": [up.width, up.height]}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    manifest: dict[str, dict] = {}

    # ---- A. OSTation FRONT (green palette authority, hi-res) ------------------
    ost = Image.open(OSTATION).convert("RGB")
    x0, y0, x1, y1 = 117, 1, 426, 358  # measured subject bbox (+1 exclusives)
    W, H = x1 - x0, y1 - y0
    A = "front"

    def obox(fx0: float, fy0: float, fx1: float, fy1: float) -> tuple[int, int, int, int]:
        return (round(x0 + fx0 * W), round(y0 + fy0 * H),
                round(x0 + fx1 * W), round(y0 + fy1 * H))

    crops_a = {
        "front_full": (0.0, 0.0, 1.0, 1.0,
                       "whole head; silhouette profile cross-checks sheet front within ~1%"),
        "front_crown": (0.12, 0.0, 0.88, 0.26,
                        "quad-grid dome; facet lines converge to a short ridge at top centre"),
        "front_brow-band-eyes": (0.10, 0.40, 0.90, 0.62,
                        "angular eye band: two lenses joined by a centre crossing; double-line rims = recessed pocket rim"),
        "front_nose-column": (0.36, 0.44, 0.64, 0.74,
                        "rectangular column descending from between the eyes to the mouth bar"),
        "front_mouth-chin": (0.14, 0.66, 0.86, 0.88,
                        "horizontal mouth bar with centre notch below it on the chin plate"),
        "front_jaw-chintabs": (0.08, 0.82, 0.92, 1.0,
                        "constant-width jaw column ending in two square feet (chin tabs) with centre gap"),
        "front_cheek-lobe-left": (0.0, 0.34, 0.30, 0.68,
                        "left lobe plate: angular shell with diagonal facet strokes, vertical outer edge"),
        "front_cheek-lobe-right": (0.70, 0.34, 1.0, 0.68,
                        "right lobe plate (mirror)"),
        "front_temple-left": (0.02, 0.16, 0.32, 0.42,
                        "left temple shell inside the silhouette band above the lobe"),
        "front_temple-right": (0.68, 0.16, 0.98, 0.42,
                        "right temple shell (mirror)"),
    }
    for name, (a, b, c, d, note) in crops_a.items():
        entry = crop8(ost, obox(a, b, c, d), name)
        entry.update({"source": "references/sigma-front-green-ostation.png",
                      "angle": A, "note": note})
        manifest[name] = entry

    # ---- B-E. Sheet cells ------------------------------------------------------
    sheet = Image.open(SHEET).convert("RGB")
    sheet_cells = {
        "front-red_full": ((63, 1811, 63 + 48, 1811 + 69), "front (red palette)",
                           "geometry authority used before the OSTation front was admitted; identical proportions"),
        "top-down_full": ((12, 2247, 12 + 66, 2247 + 40), "top-down",
                          "depth guess G1 evidence: elongated outline, quad crown facets either side of centre seam"),
        "rear-oblique-side_full": ((142, 1505, 142 + 60, 1505 + 47), "side / rear-oblique",
                          "plain faceted rear continuation, no decorated mechanism (G4)"),
        "three-quarter-yaw_full": ((496, 2573, 496 + 54, 2573 + 75), "three-quarter yaw (green)",
                                   "one dominant eye per side + far lobe behind; ridge seam visible peaked"),
        "three-quarter-yaw_eyes": ((496, 2573 + 28, 496 + 54, 2573 + 52), "three-quarter yaw (green)",
                                   "eye pocket depth cue: lens sits INSIDE the face planes"),
    }
    for name, (box, angle, note) in sheet_cells.items():
        entry = crop8(sheet, box, name)
        entry.update({"source": "references/sigma-wireframe-sheet.png",
                      "angle": angle, "note": note})
        manifest[name] = entry

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))

    lines = ["# Sigma Virus head — annotated sprite breakdown (zoom-v2)",
             "",
             "Generated by `zoom_v2_breakdown.py` (x8 NEAREST crops; angles are canonical probes,",
             "not measured camera data — see guess G5 in object-sculpt-spec.json).",
             "",
             "| crop | angle | reading |",
             "| --- | --- | --- |"]
    for name, e in manifest.items():
        lines.append(f"| `{e['file']}` | {e['angle']} | {e['note']} |")
    (OUT / "BREAKDOWN.md").write_text("\n".join(lines) + "\n")
    print(f"{len(manifest)} crops written to {OUT}")


if __name__ == "__main__":
    main()
