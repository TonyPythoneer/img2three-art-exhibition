#!/usr/bin/env python3
"""Derive a filled-silhouette reference variant from an admitted wire-art ref.

The admitted front ref (refs/front.png) is wireframe art: its foreground mask
is thin strokes with ~80% holes, while a rendered model's mask has a solid
interior. IoU between those two mask SEMANTICS can never be high, even for a
perfect model. This repo's established convention (the former
spec/gate_silhouette.py, deleted in cbea4c5, docstring quoted): "Both sides are
reduced the same way - per row, fill between the leftmost and the rightmost
non-background pixel - and the IoU is taken on those filled masks."

This script applies exactly that reduction to the admitted ref, producing
<name>-filled.png next to it. The authority file is never touched; Divine Eye /
Tier-1 then compares filled-vs-filled. Colour/detail evidence continues to use
the original ref.

Rerunnable: python3 make_filled_ref.py refs/front.png
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

BG = (0, 0, 41)
TOL = 30


def main() -> None:
    src = Path(sys.argv[1])
    rgba = Image.open(src).convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opx = out.load()
    tol2 = TOL * TOL

    def is_fg(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
        if a <= 24:
            return False
        d2 = (r - BG[0]) ** 2 + (g - BG[1]) ** 2 + (b - BG[2]) ** 2
        return d2 > tol2

    for y in range(h):
        xs = [x for x in range(w) if is_fg(x, y)]
        if not xs:
            continue
        lo, hi = min(xs), max(xs)
        for x in range(lo, hi + 1):
            r, g, b, _a = px[x, y]
            opx[x, y] = (r, g, b, 255)

    dest = src.with_name(src.stem + "-filled.png")
    out.save(dest)
    print(dest)


if __name__ == "__main__":
    main()
