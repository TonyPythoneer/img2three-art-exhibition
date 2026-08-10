#!/usr/bin/env python3
"""8× NEAREST crops of the three joints in the blade stack — artwork beside render, same box.

The 2026-08-08 correction changes where each layer's UNDERSIDE sits: the two films now conform to
the shell instead of closing flat at their own rim depth, and the diamond grows out of the dark
core instead of running from the blade's mid-plane outward. Depth is the one thing a single flat
crop cannot answer — §5 of CURRENT-MODEL.md files every Z on this build as directed at confidence
0.35 — so what these crops are for is the *boundary* evidence, which the crop CAN answer: is each
layer's edge a step with a lit side and a shaded side, or a hairline with no body?

Three joints, each named for the pair it holds:

  gem-jaw     the diamond's lower flank against the two jaws — the seat the stone grows from
  gem-core    the diamond's upper flank against the dark wedge — the layer it is now seated on
  film-shell  the violet film's own rim against the pale shell, high enough up the blade that
              nothing else overlaps it

The frame is DERIVED from the crop rather than typed in: the blade tip is its topmost foreground
pixel and the pommel tip its bottommost, and those two are the landmarks `measure_authority.py`
already fixes at weapon-local Y = 760 and Y = −210.7. So a box below is written in the model's own
coordinates and lands on the same place in both pictures.

The render side is `artifacts/ultima-v2/gate/full.png`, which `run_gates.sh` re-frames to exactly
the crop's 210×434 framing — that is what makes a side-by-side a comparison rather than a collage.
Run the gates first; without it the script writes the artwork panel alone and says so.

    python3 src/exhibits/cloud-ultima-weapon-v2/spec/zoom_stack_edges.py
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CROP = HERE.parent / "assets" / "artwork-sword-crop.png"
RENDER = ROOT / "artifacts" / "ultima-v2" / "gate" / "full.png"
OUT = HERE / "zoom-relief"
SCALE = 8

TIP_Y = 760.0
POMMEL_Y = -210.7

# Weapon-local boxes: (minX, minY, maxX, maxY) in normalized-1000 units.
BOXES = {
    "gem-jaw": (-45, 0, 45, 60),
    "gem-core": (-35, 60, 35, 130),
    "film-shell": (-60, 190, 60, 260),
}


def foreground(image: Image.Image) -> list[tuple[int, int]]:
    """Every pixel that is not the near-white background."""
    px = image.convert("RGB").load()
    w, h = image.size
    return [
        (x, y)
        for y in range(h)
        for x in range(w)
        if min(px[x, y]) < 232
    ]


def frame(image: Image.Image):
    """(origin, along, across, pixels-per-unit) for the weapon's own axes, read off the picture."""
    pixels = foreground(image)
    tip = min(pixels, key=lambda p: p[1])
    pommel = max(pixels, key=lambda p: p[1])
    span = math.hypot(tip[0] - pommel[0], tip[1] - pommel[1])
    scale = span / (TIP_Y - POMMEL_Y)
    along = ((tip[0] - pommel[0]) / span, (tip[1] - pommel[1]) / span)
    across = (-along[1], along[0])  # +X to the weapon's right, image Y pointing down
    return pommel, along, across, scale


def to_image(local, origin, along, across, scale) -> tuple[float, float]:
    x, y = local
    t = (y - POMMEL_Y) * scale
    s = x * scale
    return (origin[0] + along[0] * t + across[0] * s, origin[1] + along[1] * t + across[1] * s)


def box_in_image(box, *frame_args) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    corners = [
        to_image((x, y), *frame_args) for x in (x0, x1) for y in (y0, y1)
    ]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    return (
        max(0, math.floor(min(xs))),
        max(0, math.floor(min(ys))),
        math.ceil(max(xs)),
        math.ceil(max(ys)),
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    artwork = Image.open(CROP).convert("RGB")
    art_frame = frame(artwork)
    print(f"artwork {CROP.name} {artwork.size[0]}×{artwork.size[1]}  "
          f"{art_frame[3]:.4f} px per normalized unit, lean "
          f"{math.degrees(math.atan2(art_frame[1][0], -art_frame[1][1])):+.2f}°")

    render = None
    if RENDER.exists():
        render = Image.open(RENDER).convert("RGB")
        if render.size != artwork.size:
            print(f"! {RENDER} is {render.size}, not the crop's {artwork.size} — skipping it")
            render = None
    else:
        print(f"! {RENDER} is missing — run spec/run_gates.sh for the render panel")

    for name, box in BOXES.items():
        rect = box_in_image(box, *art_frame)
        panels = [artwork.crop(rect)]
        if render is not None:
            panels.append(render.crop(rect))
        w, h = panels[0].size
        gap = 6
        sheet = Image.new(
            "RGB", (w * SCALE * len(panels) + gap * (len(panels) - 1), h * SCALE), (255, 255, 255)
        )
        for i, panel in enumerate(panels):
            sheet.paste(panel.resize((w * SCALE, h * SCALE), Image.NEAREST), (i * (w * SCALE + gap), 0))
        path = OUT / f"stack-{name}-{SCALE}x.png"
        sheet.save(path)
        print(f"wrote {path.relative_to(HERE.parent)}  local {box} → image {rect}  "
              f"{'artwork | render' if len(panels) == 2 else 'artwork only'}")


if __name__ == "__main__":
    main()
