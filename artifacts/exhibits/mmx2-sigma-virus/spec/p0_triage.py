"""P0 reference triage for the MMX2 Sigma wireframe head.

The project recipe (corner flood fill + whiteness test) assumes a FILLED subject on a
light ground. This reference is the opposite: coloured 1px strokes on a uniform dark
navy. Flood fill would reach every interior cell through the gaps between strokes and
report the subject as empty. So the mask here is a stroke mask keyed on hue, and the
clipping / scale checks run against that instead.

Usage: python3 p0_triage.py <sheet.png> <out.json>
"""
import json, sys
from collections import Counter
from PIL import Image

BG = (16, 16, 64)          # measured below; asserted, not assumed
BG_TOL = 24


def is_bg(p):
    return all(abs(a - b) <= BG_TOL for a, b in zip(p, BG))


def hue_family(p):
    r, g, b = p
    if g > r + 40 and g > b + 40:
        return "green"
    if r > g + 40 and r > b + 40:
        return "red-orange"
    if r > g + 40 and b > g + 40:
        return "purple"
    if b > r + 40 and b > g + 20:
        return "blue"
    return "other"


def bbox(px, x0, y0, x1, y1, want):
    xs, ys = [], []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if hue_family(px[x, y]) == want and not is_bg(px[x, y]):
                xs.append(x); ys.append(y)
    if not xs:
        return None
    return {"x0": min(xs), "y0": min(ys), "x1": max(xs), "y1": max(ys),
            "w": max(xs) - min(xs) + 1, "h": max(ys) - min(ys) + 1, "strokePx": len(xs)}


def main():
    sheet, out = sys.argv[1], sys.argv[2]
    im = Image.open(sheet).convert("RGB")
    px = im.load()
    W, H = im.size

    corners = Counter(px[x, y] for x in (0, W - 1) for y in (0, H - 1))
    measured_bg = corners.most_common(1)[0][0]

    # The palette strip: four same-geometry frames, bottom right.
    STRIP = (380, 2560, 610, 2644)
    green = bbox(px, *STRIP, "green")

    # Every distinct non-background colour inside the green frame's box.
    gc = Counter()
    for y in range(green["y0"], green["y1"] + 1):
        for x in range(green["x0"], green["x1"] + 1):
            p = px[x, y]
            if not is_bg(p):
                gc[p] += 1

    # Clipping: does the green frame touch the sheet edge on any side?
    clip = {
        "top": green["y0"] == 0,
        "bottom": green["y1"] == H - 1,
        "left": green["x0"] == 0,
        "right": green["x1"] == W - 1,
    }

    # Cross-frame scale: the same geometry in the four palette frames must measure the
    # same. Segment the strip on background-only columns rather than hand-placed boxes —
    # a box that clips one frame invents an error the reference does not have. Any
    # surviving spread is the instrument's own error and becomes the uncertainty floor.
    sy0, sy1 = 2560, 2644
    hit_cols = {x for x in range(380, 610)
                if any(not is_bg(px[x, y]) for y in range(sy0, sy1))}
    runs, start = [], None
    for x in range(380, 611):
        if x in hit_cols and start is None:
            start = x
        elif x not in hit_cols and start is not None:
            if x - start >= 20:          # 20px floor drops the tiny tail-end frames
                runs.append((start, x))
            start = None
    variants = {}
    for i, (x0, x1) in enumerate(runs):
        fams = Counter(hue_family(px[x, y]) for x in range(x0, x1)
                       for y in range(sy0, sy1) if not is_bg(px[x, y]))
        fam = fams.most_common(1)[0][0]
        variants[f"frame{i}-{fam}"] = bbox(px, x0, sy0, x1, sy1, fam)

    hs = [v["h"] for v in variants.values() if v]
    ws = [v["w"] for v in variants.values() if v]
    spread_h = (max(hs) - min(hs)) / (sum(hs) / len(hs))
    spread_w = (max(ws) - min(ws)) / (sum(ws) / len(ws))

    rec = {
        "sheet": sheet, "sheetSize": [W, H],
        "measuredBackground": list(measured_bg),
        "assumedBackground": list(BG),
        "backgroundMatches": is_bg(measured_bg),
        "greenFrame": green,
        "greenFrameColours": [
            {"rgb": list(c), "count": n, "family": hue_family(c)}
            for c, n in gc.most_common(12)
        ],
        "clipping": clip,
        "paletteVariants": variants,
        "crossVariantSpread": {"height": round(spread_h, 4), "width": round(spread_w, 4)},
        "measurementUncertainty": round(max(spread_h, spread_w), 4),
    }
    with open(out, "w") as f:
        json.dump(rec, f, indent=2)
    print(json.dumps({k: rec[k] for k in
                      ("measuredBackground", "backgroundMatches", "greenFrame",
                       "clipping", "crossVariantSpread", "measurementUncertainty")}, indent=2))
    print("colours:", json.dumps(rec["greenFrameColours"][:8]))


main()
