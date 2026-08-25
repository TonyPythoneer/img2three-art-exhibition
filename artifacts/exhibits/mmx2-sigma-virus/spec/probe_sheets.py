#!/usr/bin/env python3
"""Probe the reference sheets: size + coarse non-white density per candidate grid cell.

Coarse pass only (counts dark-ish pixels per cell). The proper P0 silhouette
(flood fill + whiteness) runs separately per admitted cell.
"""
import json
from PIL import Image

ROOT = "artifacts/exhibits/mmx2-sigma-virus"
SHEETS = [
    f"{ROOT}/references/sigma-wireframe-sheet.png",
    "src/assets/exhibits/mmx2-sigma-virus/reference-sprite-sheet.png",
    "src/assets/exhibits/mmx2-sigma-virus/front-geometry-authority.png",
    "src/assets/exhibits/mmx2-sigma-virus/crown-from-above.png",
    "src/assets/exhibits/mmx2-sigma-virus/green-colour-authority.png",
    "src/assets/exhibits/mmx2-sigma-virus/palette-strip.png",
]
NONWHITE = 12  # 255 - min(r,g,b) > NONWHITE counts as subject candidate


def cell_stats(im, x0, y0, x1, y1):
    px = im.load()
    sub = 0
    minx = miny = 10**9
    maxx = maxy = -1
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b = px[x, y]
            if 255 - min(r, g, b) > NONWHITE:
                sub += 1
                if x < minx:
                    minx = x
                if x > maxx:
                    maxx = x
                if y < miny:
                    miny = y
                if y > maxy:
                    maxy = y
    if sub == 0:
        return None
    return {"px": sub, "bbox": [minx, miny, maxx, maxy]}


def main():
    out = {}
    for path in SHEETS:
        im = Image.open(path).convert("RGB")
        W, H = im.size
        rec = {"size": [W, H]}
        for gw in (1, 2, 3, 4, 5, 6, 8):
            for gh in (1, 2, 3, 4):
                if W % gw or H % gh:
                    continue
                stats = []
                for gy in range(gh):
                    for gx in range(gw):
                        x0, x1 = W * gx // gw, W * (gx + 1) // gw
                        y0, y1 = H * gy // gh, H * (gy + 1) // gh
                        s = cell_stats(im, x0, y0, x1, y1)
                        stats.append(s)
                rec[f"grid_{gw}x{gh}"] = {"cells": stats, "nonempty": sum(1 for s in stats if s)}
        out[path] = rec
    print(json.dumps(out))


if __name__ == "__main__":
    main()
