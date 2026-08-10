#!/usr/bin/env python3
"""The user's hand sketch of the guard, read at 6-8x NEAREST, and the build beside it.

`references/04-user-sketch-guard.png` is the highest-authority reference for the HILT — above the
artwork crop, which is a projected 3/4 render of a different pose and cannot referee which part a
dark pixel belongs to. Three integrations are read off it and nothing else:

  #15  the shell's lowest edge is the two jaws' floor edges laid end to end;
  #16  the grip column's flat top lies against that floor, parallel and touching, NOT inserted;
  #17  each connector arm grows out of its jaw's OUTER lower corner.

This script is what "read at 6-8x" means for those three, and it exists so that the readings can
be re-checked rather than taken on trust. It crops nothing by material — every crop is cut around
a JOINT, which is the rule the whole exhibit is built to.

What the sketch does NOT give, recorded here rather than fitted anyway:

  * **scale.** Measured off the crops below, one jaw is 164 px wide against 118 px tall, i.e. an
    aspect of 1.39 where the model's outline is 34 / 42 = 0.81. The sketch is a schematic of which
    part meets which, and its proportions are not evidence. Only its TOPOLOGY is used.
  * **the shell's own width.** Its lower boundary is drawn as one flat line, not as a trapezoid,
    so the 1.1667 taper cannot come from here. What does come from here is that the line's LENGTH
    matches one jaw's floor: 143 px against 155 px on the left, 8% apart.

    python3 src/exhibits/cloud-ultima-weapon-v2/spec/zoom_sketch_guard.py

Writes six PNGs into `spec/zoom-guard/`. Reads the sketch and the built front-orthographic
capture; runs after a capture, and it is not a gate.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
V = HERE.parent
ROOT = V.parent.parent.parent
SKETCH = V / "references/04-user-sketch-guard.png"
RENDER = ROOT / "artifacts/ultima-v2/full/closeup-connectors.png"
OUT = HERE / "zoom-guard"

# Every box is cut around a joint, in the sketch's own pixels. The names say which joint.
CROPS: dict[str, tuple[tuple[int, int, int, int], int, str]] = {
    # The whole guard, for the part map: two triangles, two arms, the column, the blade above.
    "sketch-guard-3x": ((60, 320, 1060, 1000), 3, "the guard entire"),
    # #17, both sides: the arm's two long edges converge on the triangle's outer lower corner.
    "sketch-arm-root-left-8x": ((250, 720, 470, 900), 8, "left arm root vs the jaw's outer corner"),
    "sketch-arm-root-right-8x": ((650, 720, 880, 900), 8,
                                 "right arm root vs the jaw's outer corner"),
    # #16: the column's top edge is a CLOSED horizontal line under the jaws' floor, not a shaft
    # running up between them.
    "sketch-grip-top-6x": ((420, 730, 700, 900), 6, "the column's top vs the jaws' floor"),
    # #15 and the jaw's own three vertices: apex up, floor horizontal, outer corner at full width.
    "sketch-clamp-triangle-6x": ((290, 600, 620, 810), 6, "the left jaw's three vertices"),
}


def grid(image: Image.Image, box: tuple[int, int, int, int], scale: int,
         step: int = 10) -> Image.Image:
    x0, y0, x1, y1 = box
    out = image.crop(box).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.NEAREST)
    draw = ImageDraw.Draw(out)
    for gx in range(0, x1 - x0, step):
        major = (gx + x0) % (step * 5) == 0
        draw.line([(gx * scale, 0), (gx * scale, out.height)],
                  fill=(255, 0, 0) if major else (255, 205, 205))
        if major:
            draw.text((gx * scale + 3, 4), str(gx + x0), fill=(200, 0, 0))
    for gy in range(0, y1 - y0, step):
        major = (gy + y0) % (step * 5) == 0
        draw.line([(0, gy * scale), (out.width, gy * scale)],
                  fill=(0, 120, 255) if major else (205, 228, 255))
        if major:
            draw.text((4, gy * scale + 3), str(gy + y0), fill=(0, 80, 200))
    return out


def side_by_side(left: Image.Image, right: Image.Image, path: Path) -> None:
    """Sketch and render at a common HEIGHT, so the two guards are compared and not two scales."""
    height = max(left.height, right.height)
    scaled = [
        img.resize((round(img.width * height / img.height), height), Image.NEAREST)
        for img in (left, right)
    ]
    sheet = Image.new("RGB", (sum(i.width for i in scaled) + 12, height), (250, 246, 236))
    sheet.paste(scaled[0], (0, 0))
    sheet.paste(scaled[1], (scaled[0].width + 12, 0))
    sheet.save(path)
    print(f"wrote {path.relative_to(V)} {sheet.width}x{sheet.height}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sketch = Image.open(SKETCH).convert("RGB")
    for name, (box, scale, what) in CROPS.items():
        image = grid(sketch, box, scale)
        image.save(OUT / f"{name}.png")
        print(f"wrote zoom-guard/{name}.png {image.width}x{image.height} — {what}")

    if RENDER.exists():
        side_by_side(
            sketch.crop((70, 500, 1050, 1000)),
            Image.open(RENDER).convert("RGB").crop((180, 180, 830, 512)),
            OUT / "compare-sketch-guard.png",
        )
    else:
        print(f"skipped the side-by-side: {RENDER} has not been captured")


if __name__ == "__main__":
    main()
