#!/usr/bin/env python3
"""Trim an image to its subject's own bounding box, for prompt.txt §5.1 and §5.3.

    python3 tight_crop.py <in.png|view.webp> <out.png> [--pad N]

Why this exists: §5.1's silhouette IoU compares a reference crop against a render, and
those two images are framed by different machines — the reference by whatever rectangle
the crop was cut on, the render by the viewer's own camera fit. Comparing them as-is
measures the FRAMING, not the shape: the first run of the sole scored IoU 0.173 with a
part whose three measured extents were all exact. Trimming both sides to their subject's
own bbox removes the one difference neither image is trying to express.

Subject test, per AGENTS.md P0: corner flood fill AND a whiteness test, the same rule
spec/refmask.py uses, so a white region enclosed by the subject is not mistaken for
background and compression noise around the edge is not mistaken for subject.
"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from PIL import Image

TOL = 18


def subject_bbox(im: Image.Image) -> tuple[int, int, int, int]:
    w, h = im.size
    px = im.load()
    bg = [[False] * w for _ in range(h)]
    queue: deque[tuple[int, int]] = deque()
    for x in range(w):
        for y in (0, h - 1):
            queue.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        if not (0 <= x < w and 0 <= y < h) or bg[y][x]:
            continue
        r, g, b = px[x, y][:3]
        if 255 - min(r, g, b) > TOL:
            continue
        bg[y][x] = True
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y][:3]
            if not bg[y][x] and 255 - min(r, g, b) > TOL:
                xs.append(x)
                ys.append(y)
    if not xs:
        raise SystemExit("no subject pixels: the whole frame reads as background")
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit(__doc__)
    pad = int(argv[argv.index("--pad") + 1]) if "--pad" in argv else 2
    src, dst = Path(argv[0]), Path(argv[1])
    im = Image.open(src).convert("RGB")
    x0, y0, x1, y1 = subject_bbox(im)
    box = (max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad))
    im.crop(box).save(dst)
    print(f"{src.name} {im.size} -> {dst} {box} {(box[2] - box[0], box[3] - box[1])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
