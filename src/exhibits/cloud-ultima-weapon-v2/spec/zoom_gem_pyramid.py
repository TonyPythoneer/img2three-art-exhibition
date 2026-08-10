#!/usr/bin/env python3
"""One contact sheet of the isolated stone from six angles, each cropped to the stone itself.

`spec/capture_gem_pyramid.sh` renders the frames at whole-weapon framing, which is the right
framing for the capture and the wrong one for looking: the stone is 84 units of a 970-unit
weapon, so on the side views it lands about 30 pixels tall. This crops each frame to the RED
pixels — the stone is the only red thing left in the frame once the films, the shell and the two
jaws are hidden — pads the box, and scales every panel to the same height so the six can be read
against each other.

What the sheet is for: the apex is one point over the rhombus's centre, and the front view cannot
show that. A ridge and a pyramid both read as a rhombus with a line down the middle from the
front. From the SIDE a ridge is a long flat top and a pyramid is a triangle peaking at the middle
of the stone's own height, and that is the panel to look at.

    zsh  src/exhibits/cloud-ultima-weapon-v2/spec/capture_gem_pyramid.sh
    python3 src/exhibits/cloud-ultima-weapon-v2/spec/zoom_gem_pyramid.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FRAMES = ROOT / "artifacts" / "ultima-v2" / "gem-pyramid"
OUT = FRAMES / "contact-sheet.png"

VIEWS = [
    ("front-orthographic", "front"),
    ("left-side-thickness", "LEFT SIDE"),
    ("right-side-thickness", "RIGHT SIDE"),
    ("assembled-three-quarter", "3/4"),
    ("rear-three-quarter", "rear 3/4"),
    ("closeup-crystal-clamp", "closeup"),
]
PANEL_H = 420
PAD = 6  # source pixels of margin around the stone before scaling


def stone_box(image: Image.Image) -> tuple[int, int, int, int]:
    """The bounding box of the RED pixels — the only red left in these frames is the stone."""
    px = image.convert("RGB").load()
    w, h = image.size
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r > 60 and r > g + 30 and r > b + 20:
                xs.append(x)
                ys.append(y)
    if not xs:
        raise SystemExit("no red pixels — did capture_gem_pyramid.sh run, and did it hide the films?")
    return (
        max(0, min(xs) - PAD), max(0, min(ys) - PAD),
        min(w, max(xs) + 1 + PAD), min(h, max(ys) + 1 + PAD),
    )


panels = []
for name, label in VIEWS:
    path = FRAMES / f"{name}.png"
    if not path.exists():
        raise SystemExit(f"missing {path} — run spec/capture_gem_pyramid.sh first")
    image = Image.open(path).convert("RGB")
    box = stone_box(image)
    crop = image.crop(box)
    scale = PANEL_H / crop.height
    panel = crop.resize((max(1, round(crop.width * scale)), PANEL_H), Image.NEAREST)
    panels.append((panel, label, box))

gap = 10
sheet = Image.new("RGB", (sum(p.width for p, _, _ in panels) + gap * (len(panels) + 1),
                          PANEL_H + 26), "white")
draw = ImageDraw.Draw(sheet)
x = gap
for panel, label, box in panels:
    sheet.paste(panel, (x, 20))
    draw.text((x, 6), f"{label}  {box[2] - box[0]}x{box[3] - box[1]}px", fill="black")
    x += panel.width + gap

sheet.save(OUT)
print(f"wrote {OUT.relative_to(ROOT)}  {sheet.width}x{sheet.height}")
for (panel, label, box) in panels:
    print(f"    {label:10} source box {box}  ->  {panel.width}x{panel.height}")
