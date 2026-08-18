"""The eye's actual outline, column by column — not a parallelogram fitted to its bounding box.

The build's first eye was a straight-edged bar that matched the reference on band position, slant
and filled area, and still read wrong beside it: the reference eye kinks partway along. Neither
the band gate nor the area gate can see that, so the outline has to be measured directly and
handed to the factory as a polygon.

Per column of the RIGHT eye (the authored side; the left is its mirror), record the topmost and
bottommost accent row. Averaging the two authorities — the red geometry frame and the green
colour frame — is deliberate: each is one rasterisation of the same 3D edge, and the pair brackets
the rounding.

Output is in FRAME units (column relative to the mirror axis, row from the frame top) so the
factory converts once with the same helpers as everything else.

Usage: python3 measure_eye_outline.py <sheet.png> <out.json>
"""

import json
import sys

from PIL import Image

BG = (0, 0, 41)
BG_TOL = 24
AUTHORITIES = {
    "geometry": (63, 1811, 47, 69),
    "colour": (496, 2573, 48, 69),
}


def is_bg(p):
    return all(abs(a - b) <= BG_TOL for a, b in zip(p, BG))


def hue_family(p):
    r, g, b = p
    if g > r + 40 and g > b + 40:
        return "green"
    if r > g + 40 and b > g + 40:
        return "purple"
    if r > g + 40 and r > b + 40:
        return "orange" if g > 60 else "red"
    if b > r + 40 and b > g + 20:
        return "blue"
    return "other"


def eye_columns(px, box):
    """Right-eye accent extents per column, keyed by column offset from the mirror axis."""
    x0, y0, w, h = box
    hues = {}
    pts = []
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            p = px[x, y]
            if is_bg(p):
                continue
            fam = hue_family(p)
            hues[fam] = hues.get(fam, 0) + 1
            pts.append((x - x0, y - y0, fam))
    dominant = max(hues, key=lambda k: hues[k])
    axis = (w - 1) / 2
    cols = {}
    for cx, cy, fam in pts:
        if fam in (dominant, "other") or cx <= axis:
            continue
        # Integer key: the two authorities are 47px and 48px wide, so their mirror axes sit at
        # 23.0 and 23.5 and raw offsets never coincide. Rounding is what lets them be compared.
        off = int(round(cx - axis))
        lo, hi = cols.get(off, (cy, cy))
        cols[off] = (min(lo, cy), max(hi, cy))
    return cols


def main():
    sheet, out = sys.argv[1], sys.argv[2]
    px = Image.open(sheet).convert("RGB").load()

    per = {name: eye_columns(px, box) for name, box in AUTHORITIES.items()}

    # The GEOMETRY frame carries the outline; the colour frame is a cross-check where it happens
    # to have a stroke in the same column. Intersecting the two instead only left 4 columns out of
    # the eye's 13 — the accent is a 1px OUTLINE, so most columns are empty in any one frame, and
    # requiring both authorities to agree per column throws away most of the shape.
    merged = []
    for off in sorted(per["geometry"]):
        g = per["geometry"][off]
        c = per["colour"].get(off)
        merged.append({
            "xFromAxis": off,
            "topRow": g[0],
            "bottomRow": g[1],
            "height": g[1] - g[0] + 1,
            "colourCrossCheck": list(c) if c else None,
        })

    # Where the outline kinks: the column at which the top edge stops rising and starts falling
    # (rows count downward, so the top edge's MINIMUM row is the eye's high point).
    if merged:
        peak = min(merged, key=lambda m: m["topRow"])
        inner = merged[0]
        outer = merged[-1]
    else:
        peak = inner = outer = None

    rec = {
        "authorities": {k: {"box": list(v)} for k, v in AUTHORITIES.items()},
        "columnCount": len(merged),
        "columns": merged,
        "innerEnd": inner,
        "outerEnd": outer,
        "kinkAt": peak,
        "note": (
            "Rows count downward: a smaller topRow is higher on the head. The eye is a chevron "
            "when kinkAt sits strictly between innerEnd and outerEnd; it is a straight bar when "
            "the peak is at one end."
        ),
    }
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)

    print(f"columns: {len(merged)}")
    print("xFromAxis  top  bottom  height   colour cross-check")
    for m in merged:
        print(f'{m["xFromAxis"]:9.1f} {m["topRow"]:5.1f} {m["bottomRow"]:6.1f} {m["height"]:6.1f}'
              f'   {m["colourCrossCheck"]}')
    if peak:
        print(f'\nkink (highest top edge) at xFromAxis {peak["xFromAxis"]}, '
              f'inner end {inner["xFromAxis"]}, outer end {outer["xFromAxis"]}')


main()
