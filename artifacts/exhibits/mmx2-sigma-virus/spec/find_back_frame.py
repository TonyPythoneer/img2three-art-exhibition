"""Close guess G2: find the BACK view, by the absence of the thing that marks the front.

The eyes are the only accent-coloured feature on the model. At 180 degrees of yaw they are
occluded by the skull, so the frame's accent pixel count collapses while its height stays at the
front view's 68-70px. That is a front/back discriminator that needs no pose solve:

  backness = 1 - accentPx / (accentPx of the most frontal same-scale frame)

A frame with zero accent and full height is either the back or the top; height alone rules the
top out, since a top view is short.

The tie-break is the silhouette itself. The front view's row profile has the crown notch at rows
0-13 and the jaw block at 51-68; the back has no jaw block cut, so its lower rows stay wide. The
script reports both frames' row profiles so the difference is visible rather than asserted.

Usage: python3 find_back_frame.py <sheet.png> <frame-index.json> <out.json>
"""

import json
import sys

from PIL import Image

BG = (0, 0, 41)
BG_TOL = 24


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


def profile(px, f):
    x0, y0, w, h = f["x0"], f["y0"], f["w"], f["h"]
    hues, rows, accent = {}, [], 0
    for y in range(y0, y0 + h):
        xs = []
        for x in range(x0, x0 + w):
            p = px[x, y]
            if is_bg(p):
                continue
            xs.append(x - x0)
            hues[hue_family(p)] = hues.get(hue_family(p), 0) + 1
        rows.append((min(xs), max(xs)) if xs else None)
    dominant = max(hues, key=lambda k: hues[k]) if hues else "other"
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            p = px[x, y]
            if not is_bg(p) and hue_family(p) not in (dominant, "other"):
                accent += 1
    return rows, accent


def main():
    sheet, idx, out = sys.argv[1], sys.argv[2], sys.argv[3]
    px = Image.open(sheet).convert("RGB").load()
    frames = json.load(open(idx))["frames"]

    # EVERY full-scale frame, not just the pure-yaw ones: a back view could arrive at any pitch,
    # and restricting to matched height would report "no back view" without having looked for one.
    # Height floor of 40 drops the credit text and the palette swatch strip, which are wide, short
    # components with plenty of stroke pixels and no relation to the head.
    pool = [f for f in frames if f["strokePx"] >= 600 and f["h"] >= 40 and max(f["w"], f["h"]) >= 55]
    scored = []
    for f in pool:
        rows, accent = profile(px, f)
        scored.append({**f, "accentPx": accent, "rows": rows})

    max_accent = max(s["accentPx"] for s in scored) or 1
    for s in scored:
        s["backness"] = round(1 - s["accentPx"] / max_accent, 4)

    # Among the accent-free frames, the back view is the WIDEST: at 180 degrees the full width
    # of the head faces the camera again, whereas a partly-turned frame is narrower.
    blind = [s for s in scored if s["accentPx"] == 0]
    back = max(blind, key=lambda s: s["w"]) if blind else max(scored, key=lambda s: s["backness"])
    front = min(scored, key=lambda s: s["backness"])

    def strip(s):
        return {k: s[k] for k in ("x0", "y0", "w", "h", "strokePx", "accentPx", "backness")}

    rec = {
        "pool": len(scored),
        "accentFreeFrames": len(blind),
        "front": strip(front),
        "back": strip(back),
        "backRowProfile": [
            {"y": i, "left": r[0], "right": r[1], "span": r[1] - r[0] + 1} if r else None
            for i, r in enumerate(back["rows"])
        ],
        "frontRowProfile": [
            {"y": i, "left": r[0], "right": r[1], "span": r[1] - r[0] + 1} if r else None
            for i, r in enumerate(front["rows"])
        ],
    }
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps({k: rec[k] for k in ("pool", "accentFreeFrames", "front", "back")}, indent=1))
    print("\nrow  front(l-r span)   back(l-r span)")
    for i in range(0, back["h"], 3):
        fr = rec["frontRowProfile"][i] if i < len(rec["frontRowProfile"]) else None
        bk = rec["backRowProfile"][i]
        fs = f'{fr["left"]:2d}-{fr["right"]:2d} {fr["span"]:2d}' if fr else "  --  "
        bs = f'{bk["left"]:2d}-{bk["right"]:2d} {bk["span"]:2d}' if bk else "  --  "
        print(f"{i:3d}  {fs}        {bs}")


main()
