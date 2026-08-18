"""Which frames are ACTUALLY pure yaw — and the ones that only looked it.

Everything downstream of "the sheet is one mesh" leaned on a filter that is necessary but not
sufficient: a rotation about the vertical axis preserves the head's height, so frames whose
height matches the front view's 68-70px were taken to be a yaw sweep. The converse does not hold.
A head tumbling on three axes passes through plenty of orientations that happen to land on 68-70px
of height while being nothing like a yaw.

That is not hypothetical. The frame at (311, 694), 67x68, was the widest in that set and was what
put the head's depth at 67/47 = 1.4255. At 10x it is rolled and pitched, lying on a diagonal with
its eyes down near the bottom of the frame. Its width says nothing about the head's depth.

The discriminator is the eyes' HEIGHT. A pure yaw slides them sideways and leaves their row alone;
any pitch or roll moves it. So:

  pure yaw  <=>  height in [68, 70]  AND  |accent centre row / height - front value| <= tol

with the front value measured on the geometry authority rather than assumed.

Usage: python3 pure_yaw_set.py <sheet.png> <frame-index.json> <out.json> [--tol 0.05]
"""

import json
import sys

from PIL import Image

BG = (0, 0, 41)
BG_TOL = 24
FRONT = (63, 1811, 47, 69)


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


def accent_rows(px, x0, y0, w, h):
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
    if not hues:
        return None
    dominant = max(hues, key=lambda k: hues[k])
    ys = [cy for _, cy, fam in pts if fam not in (dominant, "other")]
    return ys or None


def main():
    sheet, idx, out = sys.argv[1], sys.argv[2], sys.argv[3]
    tol = float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 0.05
    px = Image.open(sheet).convert("RGB").load()
    frames = json.load(open(idx))["frames"]

    fx, fy, fw, fh = FRONT
    front_ys = accent_rows(px, fx, fy, fw, fh)
    if not front_ys:
        raise SystemExit("no accent in the geometry authority — check FRONT")
    front_centre = (sum(front_ys) / len(front_ys)) / fh

    kept, rejected = [], []
    for f in frames:
        if not (68 <= f["h"] <= 70 and f["strokePx"] >= 600 and f["accents"]):
            continue
        ys = accent_rows(px, f["x0"], f["y0"], f["w"], f["h"])
        if not ys:
            continue
        centre = (sum(ys) / len(ys)) / f["h"]
        rec = {**{k: f[k] for k in ("x0", "y0", "w", "h", "strokePx")},
               "accentCentreFrac": round(centre, 4),
               "delta": round(abs(centre - front_centre), 4)}
        (kept if rec["delta"] <= tol else rejected).append(rec)

    kept.sort(key=lambda r: r["w"])
    rejected.sort(key=lambda r: -r["w"])
    rec = {
        "frontAccentCentreFrac": round(front_centre, 4),
        "tol": tol,
        "heightFilteredCount": len(kept) + len(rejected),
        "pureYawCount": len(kept),
        "rejectedCount": len(rejected),
        "pureYawWidthRange": [kept[0]["w"], kept[-1]["w"]] if kept else None,
        "widestRejected": rejected[:5],
        "pureYaw": kept,
    }
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)

    print(f"front accent centre {front_centre:.4f} of height, tol {tol}")
    print(f"height filter kept {rec['heightFilteredCount']}; of those "
          f"{len(kept)} are pure yaw and {len(rejected)} are tumbled")
    print(f"pure-yaw width range: {rec['pureYawWidthRange']}")
    print("widest REJECTED (these are what inflated the old depth number):")
    for r in rejected[:5]:
        print(f'  ({r["x0"]},{r["y0"]}) {r["w"]}x{r["h"]}  accent centre {r["accentCentreFrac"]}'
              f'  delta {r["delta"]}')


main()
