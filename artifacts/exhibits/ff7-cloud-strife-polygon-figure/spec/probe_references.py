#!/usr/bin/env python3
"""Reference probes for the FF7 Cloud Strife polygon-figure rebuild.

NOT the Stage 0 deliverables. These are the diagnostics that produced the numbers
carried into prompt.txt §1.5, §2 and §3.1, kept so those numbers can be re-derived
instead of trusted. Prompt §0.6 requires Stage 0 to re-run them and to prefer the
script's output over the prompt's text wherever the two disagree.

The Stage 0 deliverables are separate files and still have to be written:
  measure_landmarks.py  gate_facets.py  sample_palette.py  audit_records.py

Usage:
    python3 probe_references.py silhouette   # extraction, clipping, enclosed white
    python3 probe_references.py mirror       # best-fit axis + banded mirror IoU
    python3 probe_references.py palette      # colour clusters identified by position
    python3 probe_references.py all

Pure stdlib + Pillow.
"""
from __future__ import annotations

import sys
from collections import defaultdict, deque
from pathlib import Path

from PIL import Image

REFS = Path(__file__).resolve().parents[4] / "src/assets/exhibits/ff7-cloud-strife-polygon-figure"
VIEWS = ("front", "back", "left", "right", "more-angle")

# Background tolerance. A pixel is "solid" when it is more than TOL below white on
# its darkest channel. 18 clears the webp compression noise on all five references.
TOL = 18


# ---------------------------------------------------------------- silhouette ---
def figure_mask(view: str, tol: int = TOL):
    """figure = (unreachable from the border) AND (not near-white).

    Both conditions are required. Flood fill alone counts white regions ENCLOSED by
    the subject (the gap between the legs) as subject; the whiteness test alone
    counts compression noise in the backdrop as subject.
    Returns (mask, w, h, enclosed_white_count).
    """
    im = Image.open(REFS / f"{view}.webp").convert("RGB")
    w, h = im.size
    px = im.load()
    assert px is not None

    solid = bytearray(w * h)
    for y in range(h):
        row = y * w
        for x in range(w):
            r, g, b = px[x, y]
            if 255 - min(r, g, b) > tol:
                solid[row + x] = 1

    reach = bytearray(w * h)
    q: deque[tuple[int, int]] = deque()

    def push(x: int, y: int) -> None:
        i = y * w + x
        if not solid[i] and not reach[i]:
            reach[i] = 1
            q.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)
    while q:
        x, y = q.popleft()
        if x > 0:
            push(x - 1, y)
        if x + 1 < w:
            push(x + 1, y)
        if y > 0:
            push(x, y - 1)
        if y + 1 < h:
            push(x, y + 1)

    mask = bytearray(w * h)
    enclosed = 0
    for i in range(w * h):
        if reach[i]:
            continue
        if solid[i]:
            mask[i] = 1
        else:
            enclosed += 1  # unreachable but near-white == a hole inside the subject
    return mask, w, h, enclosed


def probe_silhouette() -> None:
    print("=== silhouette, clipping, enclosed white ===")
    print("A true silhouette tip is 1-2 px wide. A solid run on an edge line means")
    print("the subject is cut off there and that direction is unmeasurable.\n")
    for view in VIEWS:
        mask, w, h, enclosed = figure_mask(view)
        n = sum(mask)
        rows = [y for y in range(h) if any(mask[y * w + x] for x in range(w))]
        cols = [x for x in range(w) if any(mask[y * w + x] for y in range(h))]
        top = sum(mask[0 : w])
        bot = sum(mask[(h - 1) * w : h * w])
        left = sum(mask[y * w] for y in range(h))
        right = sum(mask[y * w + w - 1] for y in range(h))
        print(f"{view}.webp {w}x{h}")
        print(f"  figure rows {rows[0]}..{rows[-1]} (h={rows[-1]-rows[0]+1})  "
              f"cols {cols[0]}..{cols[-1]}")
        print(f"  edge runs: top={top} bottom={bot} left={left} right={right}")
        print(f"  enclosed white: {enclosed} px ({100*enclosed/max(1,n+enclosed):.2f}% "
              f"of everything the flood fill could not reach)")


# -------------------------------------------------------------------- mirror ---
def _iou_about(mask, w: int, h: int, axis2: int) -> float:
    """axis2 = 2 * mirror_x, so half-pixel axes are expressible as integers."""
    inter = union = 0
    for y in range(h):
        row = y * w
        for x in range(w):
            a = mask[row + x]
            mx = axis2 - x
            b = mask[row + mx] if 0 <= mx < w else 0
            if a or b:
                union += 1
                if a and b:
                    inter += 1
    return inter / union if union else 0.0


BANDS = (
    ("head+hair", 0.00, 0.30),
    ("shoulders", 0.30, 0.36),
    ("upper arms", 0.36, 0.45),
    ("forearms+hands", 0.45, 0.64),
    ("pelvis", 0.60, 0.72),
    ("pant legs", 0.72, 0.86),
    ("boots+soles", 0.86, 1.00),
)


def probe_mirror(view: str = "front") -> None:
    """Symmetry is measured, not assumed.

    Two things this reports that are easy to get wrong:
      - the axis must be the BEST-FIT axis found by a half-pixel sweep, not the
        bounding-box centre; the bbox centre drags every band's score down;
      - the whole-figure IoU is the NOISE FLOOR from photographic perspective and
        staging. A band at 0.88 against a floor of 0.86 is not asymmetric. The
        lateral extent difference separates the cases; IoU only corroborates.
    """
    mask, w, h, _ = figure_mask(view)
    rows = [y for y in range(h) if any(mask[y * w + x] for x in range(w))]
    y0, y1 = rows[0], rows[-1]
    height = y1 - y0 + 1
    cols = [x for x in range(w) if any(mask[y * w + x] for y in range(h))]
    bbox_axis2 = cols[0] + cols[-1]

    best_iou, best_axis2 = max(
        ((_iou_about(mask, w, h, a2), a2) for a2 in range(bbox_axis2 - 12, bbox_axis2 + 13)),
        key=lambda t: t[0],
    )
    print(f"=== banded mirror IoU on {view}.webp ===")
    print(f"bbox-centre axis x={bbox_axis2/2:.1f} -> IoU {_iou_about(mask, w, h, bbox_axis2):.4f}")
    print(f"best-fit  axis x={best_axis2/2:.1f} -> IoU {best_iou:.4f}   <-- NOISE FLOOR\n")
    axis = best_axis2 / 2

    for name, a, b in BANDS:
        ya, yb = y0 + int(a * height), min(y1 + 1, y0 + int(b * height))
        inter = union = 0
        lext = rext = 0.0
        for y in range(ya, yb):
            row = y * w
            for x in range(w):
                p = mask[row + x]
                mx = best_axis2 - x
                q = mask[row + mx] if 0 <= mx < w else 0
                if p or q:
                    union += 1
                    if p and q:
                        inter += 1
            xs = [x for x in range(w) if mask[row + x]]
            if xs:
                lext = max(lext, axis - min(xs))
                rext = max(rext, max(xs) - axis)
        iou = inter / union if union else 0.0
        print(f"  {name:16s} mirrorIoU={iou:.4f}  extent L={lext:6.1f} R={rext:6.1f}  "
              f"diff={abs(lext-rext):5.1f}px ({abs(lext-rext)/height*100:.2f}% of height)")


# ------------------------------------------------------------------- palette ---
def probe_palette(view: str, quant: int = 24, top: int = 14) -> None:
    """Identify colours by POSITION, never by hand-picked eye-dropper points.

    A hand-picked point lands on a facet boundary and returns a blend. Clustering
    plus a positional signature is reproducible, and the mean x relative to the
    mirror axis makes asymmetric accessories (bracer, pauldron) fall out on their
    own — which doubles as a handedness cross-check.
    """
    mask, w, h, _ = figure_mask(view)
    im = Image.open(REFS / f"{view}.webp").convert("RGB")
    px = im.load()
    assert px is not None
    rows = [y for y in range(h) if any(mask[y * w + x] for x in range(w))]
    y0, height = rows[0], rows[-1] - rows[0] + 1
    cols = [x for x in range(w) if any(mask[y * w + x] for y in range(h))]
    axis = (cols[0] + cols[-1]) / 2

    buckets: dict[tuple[int, int, int], list[float]] = defaultdict(
        lambda: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    )
    for y in range(h):
        row = y * w
        for x in range(w):
            if not mask[row + x]:
                continue
            r, g, b = px[x, y]
            e = buckets[(r // quant, g // quant, b // quant)]
            e[0] += 1
            e[1] += r
            e[2] += g
            e[3] += b
            e[4] += (y - y0) / height
            e[5] += (x - axis) / height

    total = sum(e[0] for e in buckets.values())
    print(f"\n=== {view}.webp palette clusters (figure px: {total}) ===")
    print("  hex      share   meanY   meanX (+ = image right)")
    for n, r, g, b, sy, sx in sorted(buckets.values(), key=lambda e: -e[0])[:top]:
        print(f"  #{int(r/n):02X}{int(g/n):02X}{int(b/n):02X}  {100*n/total:5.1f}%  "
              f"{sy/n:.3f}  {sx/n:+.3f}")


def main() -> None:
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("silhouette", "all"):
        probe_silhouette()
    if what in ("mirror", "all"):
        print()
        probe_mirror("front")
    if what in ("palette", "all"):
        for v in ("front", "back", "left", "more-angle"):
            probe_palette(v)


if __name__ == "__main__":
    main()
