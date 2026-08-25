#!/usr/bin/env python3
"""Crop the documented authority frames at exact sheet coordinates, 8x NEAREST."""
from PIL import Image

img = Image.open("../references/sigma-wireframe-sheet.png")
crops = {
    "geom_63_1811": (63, 1811, 48, 69),
    "green_zone": (480, 2540, 130, 104),
}
for name, (x, y, w, h) in crops.items():
    img.crop((x, y, x + w, y + h)).resize((w * 8, h * 8), Image.NEAREST).save(f"zoom/{name}.png")
print("ok")
