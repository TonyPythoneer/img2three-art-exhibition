#!/usr/bin/env python3
"""Pixel-grid viewer for the reference sheet — the agent's eyes.

This harness has no image display, so every "look" at a reference frame is a
character grid: one char per source pixel, printed at 6-8x-nearest equivalent
(--zoom repeats the char without resampling, which IS NEAREST on a raster).

Usage:
  python3 frame_view.py --auto            # one representative per size bucket
  python3 frame_view.py 3,17,88           # observation ids
  python3 frame_view.py 3 --crop 0,30,48,20 --zoom 4   # a joint, 4x

Shape view: ' ' = background, '#' = any foreground. '--both' adds a per-frame
bright('#')/dim(+) split and the accent (eye) overlay.
"""
from __future__ import annotations

import json
import pathlib
import sys

EXHIBIT = pathlib.Path(__file__).resolve().parents[1]
SHEET = EXHIBIT / "references" / "sigma-wireframe-sheet.png"
OBS = EXHIBIT / "spec" / "all-sprite-observations.json"

BG_TOL = 8
SHEET_BG = (0, 0, 41)


def load():
    from PIL import Image

    im = Image.open(SHEET).convert("RGB")
    obs = json.loads(OBS.read_text())["observations"]
    return im, obs


def is_bg(pixel) -> bool:
    return all(abs(a - b) <= BG_TOL for a, b in zip(pixel, SHEET_BG))


def is_accent(pixel) -> bool:
    r, g, b = pixel
    if r > g + 40 and r > b + 40:
        return True
    if g > 150 and r > 120 and b < 80:
        return True
    return False


def shape_char(pixel) -> str:
    return "#" if not is_bg(pixel) else " "


def frame_grid(im, obs: dict, id_: int, crop=None, zoom=1) -> str:
    bbox = obs["bbox"]
    x0, y0, w, h = bbox["x0"], bbox["y0"], bbox["width"], bbox["height"]
    if crop:
        cx, cy, cw, ch = crop
        x0, y0, w, h = bbox["x0"] + cx, bbox["y0"] + cy, cw, ch
    px = im.load()
    lines = []
    for row in range(y0, min(y0 + h, im.size[1])):
        line = ""
        for col in range(x0, min(x0 + w, im.size[0])):
            line += shape_char(px[col, row])
        lines.append(line * zoom if zoom > 1 else line)
    ruler = "    +" + "-" * (w * zoom if zoom > 1 else w) + "+"
    base = (w // 2) * zoom
    mid = "    |" + " " * base + "|" + " " * (w * zoom if zoom > 1 else w - w // 2 - 1) + "|"
    return f"\n{ruler}\n{''.join(lines)}\n{ruler}\n{mid}\n"


def frame_bright_map(im, obs: dict, id_: int, crop=None, zoom=1) -> str:
    """Bright '#' / dim '+' split: per-frame Otsu on max-channel of the foreground."""
    bbox = obs["bbox"]
    x0, y0, w, h = bbox["x0"], bbox["y0"], bbox["width"], bbox["height"]
    if crop:
        cx, cy, cw, ch = crop
        x0, y0, w, h = bbox["x0"] + cx, bbox["y0"] + cy, cw, ch
    px = im.load()
    vals = []
    for row in range(y0, y0 + h):
        for col in range(x0, x0 + w):
            p = px[col, row]
            if not is_bg(p):
                vals.append(max(p))
    if not vals:
        return ""
    best_t, best_err = 0, None
    for t in range(60, 256, 2):
        lo = [v for v in vals if v < t]
        hi = [v for v in vals if v >= t]
        if not lo or not hi:
            continue
        ml = sum(lo) / len(lo)
        mh = sum(hi) / len(hi)
        err = len(lo) * (ml - sum(lo) / len(lo)) ** 2 + len(hi) * (mh - sum(hi) / len(hi)) ** 2
        if best_err is None or err < best_err:
            best_err, best_t = err, t
    lines = []
    for row in range(y0, min(y0 + h, im.size[1])):
        line = ""
        for col in range(x0, min(x0 + w, im.size[0])):
            p = px[col, row]
            c = " " if is_bg(p) else ("#" if max(p) >= best_t else "+")
            line += c * zoom if zoom > 1 else c
        lines.append(line)
    return f"\n(threshold {best_t})\n" + "".join(lines) + "\n"


def accent_map(im, obs: dict, id_: int, zoom=1) -> str:
    bbox = obs["bbox"]
    px = im.load()
    lines = []
    for row in range(bbox["y0"], bbox["y0"] + bbox["height"]):
        line = ""
        for col in range(bbox["x0"], bbox["x0"] + bbox["width"]):
            p = px[col, row]
            line += ("o" * zoom if is_accent(p) else " ") if zoom > 1 else ("o" if is_accent(p) else " ")
        lines.append(line)
    return "".join(lines) + "\n"


def bucket_id(obs: dict) -> str:
    return f"({obs['bbox']['width']},{obs['bbox']['height']})"


def main() -> None:
    im, obs = load()
    args = sys.argv[1:]
    if "--auto" in args:
        picked = {}
        for o in obs:
            key = (bucket_id(o), o["dominantHue"])
            if key not in picked:
                picked[key] = o["id"]
        print(f"{'bucket':>12}  hue      id")
        for key in sorted(picked, key=lambda k: k[1]):
            print(f"{key[0]:>12}  {key[1]:<8} {picked[key]}")
        return

    ids = [int(x) for x in args[0].split(",")]
    for i in ids:
        o = obs[i]
        print(f"== frame {i}  bucket {bucket_id(o)}  hue {o['dominantHue']}  "
              f"bbox sheet=({o['bbox']['x0']},{o['bbox']['y0']})  stroke={o['strokePixels']}")
        print(frame_grid(im, o, i))
        if "--both" not in args:
            continue
        print("-- bright/dim split --")
        print(frame_bright_map(im, o, i))
        print("-- accent (eye) --")
        print(accent_map(im, o, i))


if __name__ == "__main__":
    main()
