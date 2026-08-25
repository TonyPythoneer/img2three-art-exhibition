#!/usr/bin/env python3
"""P0 census of the reference sheet: exact palette, component layout, frame population.

Inputs:
  references/sigma-wireframe-sheet.png   (the irreproducible source)
  spec/all-sprite-observations.json      (307 per-component records, 2-deep pixels aside)

Output: spec/sheet-census.json + a readable summary on stdout.
"""
from __future__ import annotations

import collections
import json
import pathlib

EXHIBIT = pathlib.Path(__file__).resolve().parents[1]
ROOT = pathlib.Path(__file__).resolve().parents[4]
SHEET = EXHIBIT / "references" / "sigma-wireframe-sheet.png"
OBS = EXHIBIT / "spec" / "all-sprite-observations.json"
OUT = EXHIBIT / "spec" / "sheet-census.json"


def hue_family(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    if g > r + 40 and g > b + 40:
        return "green"
    if b > r + 40 and b > g + 20:
        return "blue"
    if r > g + 40 and b > g + 40:
        return "purple"
    if r > g + 40 and r > b + 40:
        return "orange" if g > 60 else "red"
    return "other"


def main() -> None:
    from PIL import Image

    im = Image.open(SHEET).convert("RGB")
    w, h = im.size
    px = im.load()

    colour = collections.Counter()
    for y in range(h):
        for x in range(w):
            colour[px[x, y]] += 1

    top = [
        {"rgb": list(c), "hex": "#" + "".join(f"{v:02X}" for v in c), "px": n, "family": hue_family(c)}
        for c, n in colour.most_common(14)
    ]
    bg = tuple(colour.most_common(1)[0][0])

    obs = json.loads(OBS.read_text())["observations"]

    rows: dict[int, list[dict]] = {}
    for o in obs:
        rows.setdefault(o["bbox"]["y0"], []).append(o)

    layout = []
    for y0 in sorted(rows):
        cells = sorted(rows[y0], key=lambda o: o["bbox"]["x0"])
        sizes = {(o["bbox"]["width"], o["bbox"]["height"]) for o in cells}
        heights = [o["bbox"]["height"] for o in cells]
        aspects = sorted({round(o["aspect"], 3) for o in cells})
        families = collections.Counter(o["dominantHue"] for o in cells)
        layout.append(
            {
                "sheetRow": y0,
                "count": len(cells),
                "x0s": [o["bbox"]["x0"] for o in cells],
                "sizes": [list(s) for s in sorted(sizes)],
                "heights": heights,
                "aspMin": min(aspects),
                "aspMax": max(aspects),
                "families": dict(families),
            }
        )

    heights_all = collections.Counter(o["bbox"]["height"] for o in obs)
    widths_all = collections.Counter(o["bbox"]["width"] for o in obs)
    aspects_all = collections.Counter(round(o["aspect"], 3) for o in obs)
    fam_all = collections.Counter(o["dominantHue"] for o in obs)

    census = {
        "sheet": {"path": str(SHEET.relative_to(ROOT)), "size": [w, h], "bg": list(bg)},
        "topColours": top,
        "componentCount": len(obs),
        "heightCensus": dict(heights_all.most_common()),
        "widthCensus": dict(widths_all.most_common()),
        "aspectCensus": dict(sorted(aspects_all.items())),
        "familyCensus": dict(fam_all),
        "layoutRows": layout,
    }
    OUT.write_text(json.dumps(census, indent=2))

    print(f"sheet {w}x{h} bg={tuple(bg)} components={len(obs)}")
    print("top colours:")
    for c in top:
        print(f"  {c['hex']} {c['family']:>7} {c['px']:>7}px")
    print(f"families: {dict(fam_all.most_common())}")
    print(f"heights: {dict(heights_all.most_common())}")
    print(f"widths:  {dict(widths_all.most_common())}")
    print(f"aspects: {dict(sorted(aspects_all.items()))}")
    print(f"layout rows: {len(layout)}")
    for r in layout:
        fam = ",".join(f"{k}:{v}" for k, v in r["families"].items())
        print(
            f"  y0={r['sheetRow']:>4} n={r['count']:>2} size={r['sizes']} "
            f"asp=[{r['aspMin']}..{r['aspMax']}] {fam}"
        )


if __name__ == "__main__":
    main()
