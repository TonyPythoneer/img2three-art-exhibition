"""Front/rear 50% overlay — the correction spec's §6 symmetry check, made measurable.

Mirrors the rear render horizontally (a rear view sees the same object from the other side, so
its X runs the other way) and composites it over the front at 50%. A model whose rear was built
as a flat closing polygon, or whose components are not centred on Z=0, shows up here as coloured
fringes; a symmetric solid shows grey.

Also prints the silhouette IoU between the two, which is the number the acceptance table cites.

Run:  python3 spec/front_rear_overlay.py <front.png> <rear.png> <out.png>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageOps

FOREGROUND_MAX = 244


def mask(image: Image.Image) -> list[list[bool]]:
    rgba = image.convert("RGBA")
    px = rgba.load()
    assert px is not None
    w, h = rgba.size
    return [[px[x, y][3] > 96 and min(px[x, y][:3]) < FOREGROUND_MAX for x in range(w)] for y in range(h)]


def main() -> None:
    front = Image.open(sys.argv[1]).convert("RGB")
    rear = ImageOps.mirror(Image.open(sys.argv[2]).convert("RGB"))
    if rear.size != front.size:
        rear = rear.resize(front.size, Image.Resampling.BOX)

    fm, rm = mask(front), mask(rear)
    w, h = front.size
    inter = sum(1 for y in range(h) for x in range(w) if fm[y][x] and rm[y][x])
    union = sum(1 for y in range(h) for x in range(w) if fm[y][x] or rm[y][x])
    print(f"front/rear silhouette IoU: {inter / union:.4f}" if union else "empty")
    # Written, not only printed: `audit_records.py` holds every document to this figure, and a
    # number that exists only in a terminal scrollback is a number that drifts.
    Path(sys.argv[3]).with_suffix(".json").write_text(
        json.dumps({"intersection": inter, "union": union,
                    "iou": round(inter / union, 4) if union else None}, indent=2) + "\n"
    )

    Image.blend(front, rear, 0.5).save(sys.argv[3])
    # A difference image alongside it: grey means agreement, colour means a real mismatch.
    ImageChops.difference(front, rear).point(lambda v: min(255, v * 4)).save(
        Path(sys.argv[3]).with_name(Path(sys.argv[3]).stem + "-difference.png")
    )
    print(f"overlay -> {sys.argv[3]}")


if __name__ == "__main__":
    main()
