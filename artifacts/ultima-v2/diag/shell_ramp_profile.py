#!/usr/bin/env python3
"""The artwork's pale-shell value as a function of weapon-local Y, in LINEAR light.

`applyRamp` interpolates its three stops in linear light along weapon-local Y, so the stops can
only be derived from a profile measured the same way. Same frame as
`spec/zoom_shell_translucency.py`: tip and pommel tip are the two landmarks, so image rows map to
weapon-local Y.

    python3 artifacts/ultima-v2/diag/shell_ramp_profile.py [<a 210x434 render to profile too>]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
CROP = ROOT / "src/exhibits/cloud-ultima-weapon-v2/assets/artwork-sword-crop.png"
TIP_Y = 760.0
POMMEL_Y = -210.7


def to_linear(v: float) -> float:
    s = v / 255
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


def to_srgb(u: float) -> float:
    u = max(0.0, min(1.0, u))
    s = u * 12.92 if u <= 0.0031308 else 1.055 * u ** (1 / 2.4) - 0.055
    return s * 255


def frame(image: Image.Image):
    px = image.convert("RGB").load()
    w, h = image.size
    pixels = [(x, y) for y in range(h) for x in range(w) if min(px[x, y]) < 232]
    tip = min(pixels, key=lambda p: p[1])
    pommel = max(pixels, key=lambda p: p[1])
    span = math.hypot(tip[0] - pommel[0], tip[1] - pommel[1])
    scale = span / (TIP_Y - POMMEL_Y)
    along = ((tip[0] - pommel[0]) / span, (tip[1] - pommel[1]) / span)
    return pommel, along, scale


def profile(path: Path, label: str) -> None:
    image = Image.open(path).convert("RGB")
    origin, along, scale = frame(image)
    px = image.load()
    w, h = image.size
    bands: dict[int, list[tuple[int, int, int]]] = {}
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if not (max(c) - min(c) <= 20 and min(c) >= 110 and max(c) < 250):
                continue
            # project onto the weapon's own long axis
            t = (x - origin[0]) * along[0] + (y - origin[1]) * along[1]
            local = t / scale + POMMEL_Y
            bands.setdefault(int(local // 50) * 50, []).append(c)
    print(f"\n{label}  ({path.name})")
    print("  localY   n     median sRGB   median LINEAR")
    for key in sorted(bands):
        vals = bands[key]
        if len(vals) < 40:
            continue
        lum = sorted(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2] for c in vals)
        med = lum[len(lum) // 2]
        print(f"  {key:5d}  {len(vals):5d}      {med:6.1f}        {to_linear(med):.4f}")


profile(CROP, "ARTWORK")
for extra in sys.argv[1:]:
    profile(Path(extra), "RENDER")
