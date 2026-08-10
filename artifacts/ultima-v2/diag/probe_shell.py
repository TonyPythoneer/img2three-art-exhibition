#!/usr/bin/env python3
"""The shell's own value with NOTHING else in the frame, and no colour mask at all.

`spec/measure_shell_value.py` censuses the composite render, which is right for comparing against
the artwork but needs a colour mask to find the shell in it — and a mask with a floor cannot
report a shell that has fallen BELOW that floor. This one takes a capture where every other mesh
is hidden, so every non-background pixel is the shell and there is nothing to threshold.

It is what measured the two numbers the `outerCrystal` JSDoc turns on: with the alpha blend off
and the palette still the census bands, the shell alone renders at a median of 122 — the "opaque
grey plastic" the material was rescued from — against the artwork's 218.

    node tools/capture_ultima.mjs --route ultima-v2-harness \\
      --out artifacts/ultima-v2/diag/shell-only --detail full --views artwork-match \\
      --hide <every mesh but outerCrystalShell>
    python3 artifacts/ultima-v2/diag/probe_shell.py artifacts/ultima-v2/diag/shell-only/artwork-match.png
"""
import sys
from pathlib import Path

from PIL import Image


def census(path):
    im = Image.open(path).convert("RGB")
    px = im.load()
    w, h = im.size
    vals = [px[x, y] for y in range(h) for x in range(w) if min(px[x, y]) < 244]
    n = len(vals)
    if not n:
        print(f"{path}: EMPTY")
        return
    lum = sorted(round(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) for c in vals)
    q = lambda t: lum[min(n - 1, int(t * n))]
    mean = tuple(round(sum(c[i] for c in vals) / n) for i in range(3))
    print(
        f"{Path(path).parent.name}/{Path(path).name:22s} n={n:7d} mean={mean} "
        f"p5={q(.05)} p25={q(.25)} p50={q(.5)} p75={q(.75)} p95={q(.95)} max={lum[-1]}  "
        f"p95/p50={q(.95)/max(q(.5),1):.3f}"
    )


for p in sys.argv[1:]:
    census(p)
