#!/usr/bin/env python3
"""Crop + NEAREST magnify a reference, for the 6-8x joint inspection AGENTS.md demands.

Not a measurement tool and not a Stage 0 deliverable: it produces throwaway images.
Write its output to a scratch directory, look at it, delete it. The repo keeps the
script, never the crop (AGENTS.md, "Directory rules").

    python3 zoom.py <view> <x0> <y0> <x1> <y1> <scale> <out.png>

<view> is a reference stem (front / back / left / right / more-angle) or a path.
Coordinates are in the reference's own pixels, x1/y1 exclusive.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

REFS = Path(__file__).resolve().parents[4] / "src/assets/exhibits/ff7-cloud-strife-polygon-figure"


def main() -> int:
    if len(sys.argv) != 8:
        print(__doc__, file=sys.stderr)
        return 2
    view, x0, y0, x1, y1, scale, out = sys.argv[1:]
    src = Path(view) if "/" in view or view.endswith(".webp") else REFS / f"{view}.webp"
    im = Image.open(src).convert("RGB")
    box = (int(x0), int(y0), int(x1), int(y1))
    crop = im.crop(box)
    s = int(scale)
    crop = crop.resize((crop.width * s, crop.height * s), Image.NEAREST)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    crop.save(out)
    print(f"{src.name} {box} x{s} -> {out} ({crop.width}x{crop.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
