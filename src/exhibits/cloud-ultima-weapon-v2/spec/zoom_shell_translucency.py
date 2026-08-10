#!/usr/bin/env python3
"""Does the ARTWORK show the pale shell letting anything through? 8x NEAREST, plus the arithmetic.

The brief calls `outerCrystalShell` "pale **translucent**", the build carried that as an alpha
blend, and the user has asked for a SOLID shell instead. Before deciding how far that departs
from the supplied reading, the crop itself gets asked — because "translucent" in a written brief
is a look-word, while "translucent" in a picture is a compositing operation and a compositing
operation leaves arithmetic behind:

    if a pale layer of opacity `a` is drawn OVER something, every pixel of that something is
    pulled toward the pale layer's own value. Nothing under it can then be darker than
    `(1 - a) * under + a * shell`.

So two questions the crop CAN answer, whatever it cannot say about depth:

  1. **How dark does the violet field actually get?** The shell means 216 and the crop's own
     background is 255. A translucent shell drawn over the insert at even a = 0.2 puts a floor of
     43 under every channel of it. A field that reaches literally 0 has nothing pale over it.
  2. **How wide is the boundary between the violet field and the pale shell?** A layer seen
     THROUGH a translucent one has a soft edge, because the pale layer's own facet steps keep
     running across it. A hard step of one or two pixels is a layer seen directly.

Both are measured inside the crop's own upper blade, where nothing else overlaps. The zooms are
the picture beside the numbers, at 8x NEAREST, in the same weapon-local frame `zoom_stack_edges.py`
derives (tip and pommel tip as the two landmarks) so a box here means the same place there.

    python3 src/exhibits/cloud-ultima-weapon-v2/spec/zoom_shell_translucency.py

Writes spec/zoom-relief/translucency-*.png and prints the arithmetic.
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

# Weapon-local boxes: (minX, minY, maxX, maxY) in normalized-1000 units. Each one is a place
# where a translucent shell would have to show its hand.
BOXES = {
    # the blade's own outer edge against the background — is there a pale halo outside the body?
    "blade-edge": (30, 300, 95, 400),
    # the violet field's rim against the pale shell, high enough that nothing else overlaps
    "insert-rim": (-70, 230, 70, 300),
    # the dark core's rim against the violet field and the shell, at the core's own apex
    "core-apex": (-45, 150, 45, 215),
    # the guard: the darkest mass in the frame, right where the crystal's root enters it
    "guard-root": (-60, -40, 60, 40),
    # a connector arm running out from under the shell's lower slanted edge
    "arm-root": (18, -20, 95, 45),
}


def foreground(image: Image.Image) -> list[tuple[int, int]]:
    px = image.convert("RGB").load()
    w, h = image.size
    return [(x, y) for y in range(h) for x in range(w) if min(px[x, y]) < 232]


def frame(image: Image.Image):
    pixels = foreground(image)
    tip = min(pixels, key=lambda p: p[1])
    pommel = max(pixels, key=lambda p: p[1])
    span = math.hypot(tip[0] - pommel[0], tip[1] - pommel[1])
    scale = span / (TIP_Y - POMMEL_Y)
    along = ((tip[0] - pommel[0]) / span, (tip[1] - pommel[1]) / span)
    across = (-along[1], along[0])
    return pommel, along, across, scale


def to_image(local, origin, along, across, scale) -> tuple[float, float]:
    x, y = local
    t = (y - POMMEL_Y) * scale
    s = x * scale
    return (origin[0] + along[0] * t + across[0] * s, origin[1] + along[1] * t + across[1] * s)


def box_in_image(box, *frame_args) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    corners = [to_image((x, y), *frame_args) for x in (x0, x1) for y in (y0, y1)]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    return (
        max(0, math.floor(min(xs))),
        max(0, math.floor(min(ys))),
        math.ceil(max(xs)),
        math.ceil(max(ys)),
    )


def violet(c) -> bool:
    """A pixel of the insert's own field: blue clearly over red and green, and not pale."""
    r, g, b = c
    return b > r + 25 and b > g + 40 and max(r, g, b) < 240


def pale(c) -> bool:
    r, g, b = c
    return max(c) - min(c) <= 20 and min(c) >= 170 and max(c) < 250


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    artwork = Image.open(CROP).convert("RGB")
    art_frame = frame(artwork)
    W, H = artwork.size
    px = artwork.load()

    print(f"artwork {CROP.name} {W}x{H}  {art_frame[3]:.4f} px per normalized unit, lean "
          f"{math.degrees(math.atan2(art_frame[1][0], -art_frame[1][1])):+.2f}deg")

    # --- 1. how dark does the violet field get? -------------------------------------------
    field = [px[x, y] for y in range(H) for x in range(W) if violet(px[x, y])]
    shell = [px[x, y] for y in range(H) for x in range(W) if pale(px[x, y])]
    shell_mean = tuple(round(sum(c[i] for c in shell) / len(shell)) for i in range(3))
    print(f"\nviolet field   n={len(field)}   "
          f"min per channel R={min(c[0] for c in field)} G={min(c[1] for c in field)} "
          f"B={min(c[2] for c in field)}")
    darkest = min(field, key=lambda c: sum(c))
    print(f"               darkest pixel {darkest}")
    print(f"pale shell     n={len(shell)}   mean {shell_mean}")
    for a in (0.15, 0.25, 0.35):
        floor = tuple(round(a * shell_mean[i]) for i in range(3))
        print(f"  a shell of opacity {a:.2f} over it would floor every channel at {floor}")

    # --- 2. how wide is the boundary? ------------------------------------------------------
    # Walk each scanline of the upper blade outward from the field's edge and count how many
    # pixels sit between "clearly violet" and "clearly pale".
    widths = []
    for y in range(H):
        row = [px[x, y] for x in range(W)]
        vs = [x for x, c in enumerate(row) if violet(c)]
        ps = [x for x, c in enumerate(row) if pale(c)]
        if len(vs) < 4 or len(ps) < 4:
            continue
        for edge, side in ((min(vs), -1), (max(vs), 1)):
            near = [x for x in ps if (x - edge) * side > 0]
            if not near:
                continue
            widths.append(min(near, key=lambda x: abs(x - edge)) - edge if side > 0
                          else edge - max(near))
    widths = [w for w in widths if 0 <= w < 30]
    widths.sort()
    if widths:
        print(f"\ninsert->shell boundary, {len(widths)} scanline crossings: "
              f"median {widths[len(widths)//2]} px, p90 {widths[int(len(widths)*0.9)]} px, "
              f"max {widths[-1]} px  (1 px = {1/art_frame[3]:.2f} normalized units)")

    # --- 3. the pictures --------------------------------------------------------------------
    render = None
    if RENDER.exists():
        render = Image.open(RENDER).convert("RGB")
        if render.size != artwork.size:
            print(f"! {RENDER} is {render.size}, not the crop's {artwork.size} - skipping it")
            render = None
    else:
        print(f"! {RENDER} is missing - run spec/run_gates.sh for the render panel")

    print()
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
            sheet.paste(panel.resize((w * SCALE, h * SCALE), Image.NEAREST),
                        (i * (w * SCALE + gap), 0))
        path = OUT / f"translucency-{name}-{SCALE}x.png"
        sheet.save(path)
        print(f"wrote {path.relative_to(HERE.parent)}  local {box} -> image {rect}  "
              f"{'artwork | render' if len(panels) == 2 else 'artwork only'}")


if __name__ == "__main__":
    main()
