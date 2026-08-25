#!/usr/bin/env python3
"""Produce alpha-channel authority-frame refs from the navy sprite sheet.

The admission/Tier-1 mask primitive (build_foreground_mask) misclassifies a
saturated dark background (#000029) as foreground via its
`sat > 0.16 and luma < 0.94` clause, so coverage reads 1.000. Converting exact
background pixels to alpha=0 routes those tools through their transparency
branch (mask = alpha > 24), which is the correct silhouette. Subject pixels are
untouched: wires are far from navy in colour distance; only bg-exact pixels go.

Refs are additionally upscaled x8 NEAREST because native sprite frames are
48x69-class and the admission gate has a 64px short-side floor. NEAREST scaling
preserves the silhouette and colours exactly (pure repetition, no filtering);
the manifest records `scale` so downstream consumers can divide back.

Rerunnable: python3 make_alpha_refs.py
Inputs:  ../references/sigma-wireframe-sheet.png
Outputs: refs/<name>.png + refs/manifest.json
"""
import json
import os

from PIL import Image

BG = (0, 0, 41)
TOL = 12  # colour-distance tolerance for bg match
SCALE = 8  # NEAREST upscale factor (native frames < admission 64px floor)

# name -> (x, y, w, h, margin)
FRAMES = {
    "front": (63, 1811, 48, 69, 3),
    "top": (12, 2247, 66, 40, 3),
    "side": (142, 1505, 60, 47, 3),
}


def find_green(img):
    """Locate the green palette-authority frame by pixel scan."""
    w, h = img.size
    px = img.load()
    xs, ys = [], []
    for y in range(2400, min(h, 2644)):
        for x in range(w):
            r, g, b = px[x, y][:3]
            if g > 150 and g > r + 60 and g > b + 60:
                xs.append(x)
                ys.append(y)
    if not xs:
        raise SystemExit("no green frame found")
    return min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sheet = Image.open(os.path.join(here, "..", "references", "sigma-wireframe-sheet.png")).convert("RGBA")
    gx, gy, gw, gh = find_green(sheet)
    frames = dict(FRAMES)
    frames["green-yaw"] = (gx, gy, gw, gh, 3)

    out_dir = os.path.join(here, "refs")
    os.makedirs(out_dir, exist_ok=True)
    manifest = {}
    for name, (x, y, w, h, m) in frames.items():
        crop = sheet.crop((x - m, y - m, x + w + m, y + h + m))
        px = crop.load()
        cw, ch = crop.size
        changed = 0
        for yy in range(ch):
            for xx in range(cw):
                r, g, b, a = px[xx, yy]
                d2 = (r - BG[0]) ** 2 + (g - BG[1]) ** 2 + (b - BG[2]) ** 2
                if d2 <= TOL * TOL:
                    px[xx, yy] = (r, g, b, 0)
                    changed += 1
        crop = crop.resize((cw * SCALE, ch * SCALE), Image.NEAREST)
        path = os.path.join(out_dir, f"{name}.png")
        crop.save(path)
        manifest[name] = {
            "sheetBox": [x - m, y - m, x + w + m, y + h + m],
            "nativeSize": [cw, ch],
            "size": [cw * SCALE, ch * SCALE],
            "scale": SCALE,
            "bgPixelsCleared": changed,
            "path": path,
        }
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
