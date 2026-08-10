#!/usr/bin/env python3
"""`compare_render.mask_from`'s own mask, as a bbox — where a brighter shell costs silhouette."""
import sys
from pathlib import Path

from PIL import Image

for p in sys.argv[1:]:
    im = Image.open(p).convert("RGBA")
    px = im.load()
    w, h = im.size
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if c[3] > 96 and min(c[:3]) < 244:
                xs.append(x)
                ys.append(y)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    # what the first eight mask rows look like, top-down
    rows = []
    for y in range(y0, min(y0 + 40, h), 5):
        n = sum(1 for x in range(w) if px[x, y][3] > 96 and min(px[x, y][:3]) < 244)
        rows.append(f"y{y}:{n}")
    print(
        f"{Path(p).parent.name}/{Path(p).name:20s} {w}x{h}  bbox x[{x0},{x1}] y[{y0},{y1}]  "
        f"bw={x1-x0+1} bh={y1-y0+1} aspect={(x1-x0+1)/(y1-y0+1):.4f}  n={len(xs)}"
    )
    print("   top rows:", " ".join(rows))
