#!/usr/bin/env python3
"""Silhouette + colour-band segmentation shared by the Stage 0 deliverables.

Two jobs, both of which prompt.txt names explicitly:

  figure_mask()   §3.1's extraction rule. The figure test needs BOTH conditions —
                  flood fill alone counts white regions ENCLOSED by the figure (the
                  gap between the legs) as figure, and the whiteness test alone
                  counts webp compression noise in the backdrop as figure.

  band_map()      §2's "clusters are identified BY POSITION, not by eye-dropper
                  guesswork". Quantise, merge, then LABEL each cluster from its
                  centroid ordering and its mean y — never from a hand-picked pixel.

measure_landmarks.py and sample_palette.py both import this, so the two deliverables
cannot drift apart on what counts as "the figure" or as "the belt".

Pure stdlib + Pillow.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

REFS = Path(__file__).resolve().parents[4] / "src/assets/exhibits/ff7-cloud-strife-polygon-figure"
VIEWS = ("front", "back", "left", "right", "more-angle")
ORTHO = ("front", "back", "left", "right")

# Background tolerance: a pixel is "solid" when its darkest channel is more than
# TOL below white. 18 clears webp compression noise on all five references.
TOL = 18


@dataclass
class View:
    name: str
    w: int
    h: int
    px: object
    mask: bytearray
    enclosed_white: int
    # bbox of the figure
    x0: int = 0
    x1: int = 0
    y0: int = 0
    y1: int = 0
    bands: dict[str, bytearray] = field(default_factory=dict)
    clusters: list[dict] = field(default_factory=list)

    def m(self, x: int, y: int) -> int:
        return self.mask[y * self.w + x]

    def row_runs(self, y: int, mask: bytearray | None = None) -> list[tuple[int, int]]:
        """Contiguous [x0, x1] runs of set pixels on row y."""
        src = self.mask if mask is None else mask
        runs: list[tuple[int, int]] = []
        start = -1
        row = y * self.w
        for x in range(self.w):
            if src[row + x]:
                if start < 0:
                    start = x
            elif start >= 0:
                runs.append((start, x - 1))
                start = -1
        if start >= 0:
            runs.append((start, self.w - 1))
        return runs

    def row_extent(self, y: int, mask: bytearray | None = None) -> tuple[int, int] | None:
        runs = self.row_runs(y, mask)
        return (runs[0][0], runs[-1][1]) if runs else None


def load(view: str, tol: int = TOL) -> View:
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
            enclosed += 1

    v = View(view, w, h, px, mask, enclosed)
    xs = [x for x in range(w) if any(mask[y * w + x] for y in range(h))]
    ys = [y for y in range(h) if any(mask[y * w + x] for x in range(w))]
    v.x0, v.x1, v.y0, v.y1 = xs[0], xs[-1], ys[0], ys[-1]
    return v


# ------------------------------------------------------------------ clusters ---
QUANT = 24
MERGE_DIST = 26.0     # squared-free RGB distance under which two buckets are one cluster
MIN_SHARE = 0.0035    # a cluster below 0.35% of the figure is a facet-boundary blend


def cluster(v: View) -> list[dict]:
    """Quantise into 24-level buckets, then greedily merge nearby bucket centroids.

    Returns clusters sorted by descending pixel share, each carrying its centroid,
    share, and POSITIONAL signature (mean y as a fraction of figure height, mean x
    relative to the figure's horizontal centre, in units of figure height).
    """
    w, h = v.w, v.h
    height = v.y1 - v.y0 + 1
    axis = (v.x0 + v.x1) / 2.0
    buckets: dict[tuple[int, int, int], list[float]] = {}
    for y in range(h):
        row = y * w
        for x in range(w):
            if not v.mask[row + x]:
                continue
            r, g, b = v.px[x, y]
            key = (r // QUANT, g // QUANT, b // QUANT)
            e = buckets.get(key)
            if e is None:
                e = buckets[key] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            e[0] += 1
            e[1] += r
            e[2] += g
            e[3] += b
            e[4] += (y - v.y0) / height
            e[5] += (x - axis) / height

    raw = sorted(buckets.values(), key=lambda e: -e[0])
    merged: list[list[float]] = []
    for e in raw:
        n = e[0]
        c = (e[1] / n, e[2] / n, e[3] / n)
        for m in merged:
            mn = m[0]
            mc = (m[1] / mn, m[2] / mn, m[3] / mn)
            d = sum((a - b) ** 2 for a, b in zip(c, mc)) ** 0.5
            if d < MERGE_DIST:
                for i in range(6):
                    m[i] += e[i]
                break
        else:
            merged.append(list(e))

    total = sum(m[0] for m in merged)
    out = []
    for m in sorted(merged, key=lambda e: -e[0]):
        n = m[0]
        if n / total < MIN_SHARE:
            continue
        out.append(
            {
                "rgb": (m[1] / n, m[2] / n, m[3] / n),
                "share": n / total,
                "meanY": m[4] / n,
                "meanX": m[5] / n,
                "pixels": int(n),
            }
        )
    v.clusters = out
    return out


def _hex(rgb) -> str:
    return "#%02X%02X%02X" % tuple(int(round(c)) for c in rgb)


def label_clusters(v: View) -> list[dict]:
    """Attach a semantic label to each cluster from colour ORDERING plus position.

    No hand-picked pixels and no hardcoded hex values: every test below is a
    relation between the cluster's own channels, or a comparison of its mean y
    against another cluster's. That is what makes it reproducible on a view whose
    white balance differs (more-angle).
    """
    cs = v.clusters or cluster(v)
    for c in cs:
        r, g, b = c["rgb"]
        mx, mn = max(r, g, b), min(r, g, b)
        val = (r + g + b) / 3.0
        chroma = mx - mn
        yellowness = (r + g) / 2.0 - b
        label = "other"
        if val < 48 and chroma < 24:
            label = "black"
        elif yellowness > 45 and r > b and g > b:
            label = "hair"
        elif chroma < 12 and 84 < val < 150:
            label = "grey"
        elif b > r and b - g >= 12:
            label = "purple"
        elif r > g >= b and 130 <= val < 235 and 14 < r - b < 95:
            label = "skin"
        elif r >= g > b and 50 <= val < 105:
            label = "olive"
        c["label"] = label
        c["hex"] = _hex(c["rgb"])
    return cs


# Deliberately NOT split here: shirt-purple vs pants-purple, and belt-olive vs
# boot-olive. Both pairs were tried as a cluster-mean-y split and both failed —
# measured, not assumed:
#   - the two purples' cluster mean y differ by 0.007 of figure height (front), so the
#     split was decided by floating-point noise, and back.webp put its whole pants mass
#     on the shirt side;
#   - the olive family also catches shadowed skin (a val-118 arm cluster at mean y
#     0.332 in right.webp), which the split then promoted to "belt".
# What separates them is a SPATIAL boundary — the belt's own rows — not a colour
# statistic. split_rows() below does that, and it is the caller's job to ask for it.


BANDS = ("skin", "hair", "purple", "olive", "black", "grey")


def band_map(v: View) -> dict[str, bytearray]:
    """Per-pixel band assignment by nearest labelled cluster centroid.

    Pixels whose nearest labelled centroid is further than MAX_DIST are dropped into
    no band at all: they are the anti-aliased facet edges, and forcing them into a
    band is what turns a boundary measurement into a one-pixel lie.
    """
    if v.bands:
        return v.bands
    cs = label_clusters(v)
    named = [c for c in cs if c["label"] in BANDS]
    out = {b: bytearray(v.w * v.h) for b in BANDS}
    max_dist = 44.0
    for y in range(v.h):
        row = y * v.w
        for x in range(v.w):
            if not v.mask[row + x]:
                continue
            r, g, b = v.px[x, y]
            best, bestd = None, max_dist
            for c in named:
                cr, cg, cb = c["rgb"]
                d = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2) ** 0.5
                if d < bestd:
                    best, bestd = c["label"], d
            if best:
                out[best][row + x] = 1
    v.bands = out
    return out


def row_counts(v: View, band: str) -> list[int]:
    m = band_map(v)[band]
    return [sum(m[y * v.w : (y + 1) * v.w]) for y in range(v.h)]


def split_rows(v: View, band: str, min_rows: int = 4, min_px: int = 6) -> list[dict]:
    """Contiguous row groups of a band, largest first.

    This is what separates belt-olive from boot-olive and shirt-purple from
    pants-purple: they are the same colour family occupying different, disjoint
    stretches of rows. `min_px` drops the one- and two-pixel anti-aliasing specks
    that would otherwise bridge two groups into one.
    """
    counts = row_counts(v, band)
    groups: list[dict] = []
    start = -1
    for y, n in enumerate(counts + [0]):
        if n >= min_px:
            if start < 0:
                start = y
        elif start >= 0:
            if y - start >= min_rows:
                groups.append({"y0": start, "y1": y - 1, "pixels": sum(counts[start:y])})
            start = -1
    groups.sort(key=lambda g: -g["pixels"])
    return groups


def band_bbox(v: View, band: str) -> dict | None:
    m = band_map(v)[band]
    ys = [y for y in range(v.h) if any(m[y * v.w + x] for x in range(v.w))]
    if not ys:
        return None
    xs = [x for x in range(v.w) if any(m[y * v.w + x] for y in range(v.h))]
    return {"x0": xs[0], "x1": xs[-1], "y0": ys[0], "y1": ys[-1], "pixels": sum(m)}
