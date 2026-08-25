#!/usr/bin/env python3
"""Extract key sprite frames from the wireframe sheet and emit 8x NEAREST zoom crops.

Rerunnable: python3 zoom_frames.py --sheet ../references/sigma-wireframe-sheet.png --out zoom/
Frames chosen by measurement, not by eye: geometry authority (largest clean 48x69-class),
green palette authority, widest (top/bottom depth evidence), and yaw-family obliques.
"""
import argparse
import json
import os

from PIL import Image

BG = (0, 0, 41)


def load(path):
    return Image.open(path).convert("RGB")


def components(img):
    """Connected components of non-bg pixels (4-neighbour)."""
    w, h = img.size
    px = img.load()
    seen = bytearray(w * h)
    comps = []
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0 * w + x0]:
                continue
            if px[x0, y0] == BG:
                seen[y0 * w + x0] = 1
                continue
            stack = [(x0, y0)]
            seen[y0 * w + x0] = 1
            xs, ys, n = [], [], 0
            while stack:
                x, y = stack.pop()
                xs.append(x)
                ys.append(y)
                n += 1
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and px[nx, ny] != BG:
                        seen[ny * w + nx] = 1
                        stack.append((nx, ny))
            comps.append({
                "x0": min(xs), "y0": min(ys),
                "w": max(xs) - min(xs) + 1, "h": max(ys) - min(ys) + 1,
                "px": n,
            })
    return comps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--zoom", type=int, default=8)
    args = ap.parse_args()

    img = load(args.sheet)
    os.makedirs(args.out, exist_ok=True)
    comps = [c for c in components(img) if c["px"] >= 400 and c["h"] >= 40]
    report = {"fullSizeCount": len(comps)}

    # Geometry authority: closest to modal full size 48x69 with most stroke pixels.
    modal = sorted(comps, key=lambda c: -c["px"])[:12]
    geom = max(modal, key=lambda c: (abs(c["w"] - 48) <= 2) * c["px"])
    report["geometryAuthority"] = geom

    # Green palette authority.
    def has_green(c):
        crop = img.crop((c["x0"], c["y0"], c["x0"] + c["w"], c["y0"] + c["h"]))
        return any(g > 150 and g > r + 60 and g > b + 60 for r, g, b in crop.getdata())

    greens = [c for c in comps if has_green(c)]
    report["greenAuthority"] = greens[0] if greens else None

    # Widest frames = top/bottom depth evidence.
    wide = sorted(comps, key=lambda c: -(c["w"] / c["h"]))[:2]
    report["widest"] = wide

    picks = [("geometry", geom)]
    if greens:
        picks.append(("green", greens[0]))
    for i, c in enumerate(wide):
        picks.append((f"wide{i}", c))

    manifest = []
    for name, c in picks:
        crop = img.crop((c["x0"], c["y0"], c["x0"] + c["w"], c["y0"] + c["h"]))
        z = crop.resize((c["w"] * args.zoom, c["h"] * args.zoom), Image.NEAREST)
        p = os.path.join(args.out, f"{name}.png")
        z.save(p)
        manifest.append({"name": name, **c, "zoom": args.zoom, "path": p})

    with open(os.path.join(args.out, "manifest.json"), "w") as f:
        json.dump({"report": report, "frames": manifest}, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
