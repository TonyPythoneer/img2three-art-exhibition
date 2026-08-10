"""Cut one verified crop per material region out of the authority artwork.

The runbook requires material analysis to run on a crop that is actually on the part it
claims. Rather than eyeballing rectangles, this reuses `measure_authority.classify` and takes
the largest inscribed axis-aligned box of each region's dominant connected component, so a
crop can never straddle two materials.

Run:  python3 spec/make_material_crops.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from measure_authority import classify, components  # noqa: E402

EXHIBIT = HERE.parent
OUT = HERE / "pbr-evidence" / "crops"

# material id -> (colour class, which connected component by size rank, min box side)
REGIONS = {
    "outerCrystalMaterial": ("shell", 0, 8),
    "purpleInsertMaterial": ("insert", 0, 8),
    "guardSteelMaterial": ("steel", 0, 4),
    "guardGoldMaterial": ("gold", 0, 4),
    "gripLeatherMaterial": ("grip", 0, 3),
}


def largest_box(blob: set[tuple[int, int]], min_side: int) -> tuple[int, int, int, int] | None:
    """Largest axis-aligned rectangle fully inside the blob. ponytail: histogram scan over the
    blob's bounding box — O(w*h), fine for a 210x434 image."""
    xs = [p[0] for p in blob]
    ys = [p[1] for p in blob]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w = x1 - x0 + 1
    heights = [0] * w
    best = None
    best_area = 0
    for y in range(y0, y1 + 1):
        for i in range(w):
            heights[i] = heights[i] + 1 if (x0 + i, y) in blob else 0
        stack: list[tuple[int, int]] = []  # (start index, height)
        for i in range(w + 1):
            h = heights[i] if i < w else 0
            start = i
            while stack and stack[-1][1] >= h:
                si, sh = stack.pop()
                area = sh * (i - si)
                if area > best_area and sh >= min_side and (i - si) >= min_side:
                    best_area = area
                    best = (x0 + si, y - sh + 1, x0 + i, y + 1)
                start = si
            stack.append((start, h))
    return best


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    crop = Image.open(EXHIBIT / "assets/artwork-sword-crop.webp").convert("RGB")
    cut = Image.open(EXHIBIT / "assets/artwork-sword-transparent.webp").convert("RGBA")
    w, h = crop.size
    cp, ap = crop.load(), cut.load()
    assert cp is not None and ap is not None

    labels: list[list[str | None]] = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if ap[x, y][3] > 96:
                labels[y][x] = classify(*cp[x, y])

    for material_id, (klass, rank, min_side) in REGIONS.items():
        ccs = components(labels, klass, w, h)
        if len(ccs) <= rank:
            print(f"{material_id}: no component for class {klass!r}")
            continue
        box = largest_box(set(ccs[rank]), min_side)
        if box is None:
            print(f"{material_id}: no inscribed box >= {min_side}px in class {klass!r}")
            continue
        patch = crop.crop(box)
        # Upsample so the extractor has enough samples; nearest keeps the flat values exact.
        scale = max(1, -(-64 // min(patch.size)))
        patch = patch.resize((patch.width * scale, patch.height * scale), Image.Resampling.NEAREST)
        dst = OUT / f"crop-{material_id}.png"
        patch.save(dst)
        print(f"{material_id}: box={box} -> {dst.name} {patch.size}")


if __name__ == "__main__":
    main()
