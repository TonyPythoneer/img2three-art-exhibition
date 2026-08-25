"""Per-sprite observation pass for Sigma's wireframe reference.

This is intentionally not a model-fitting script. It records each detected sprite independently:
foreground bounds, row-wise left/right extents, centroid drift, accent/eye placement, palette
families, and regional stroke density. Geometry decisions remain review decisions made from these
records and the source pixels.
"""

from __future__ import annotations

import collections
import json
import math
import pathlib
import sys
from typing import Iterable

from PIL import Image

BG_TOL = 8
BRIDGE = 2
# The sheet's smallest legitimate sprite fragments have 60 stroke pixels. This threshold yields
# the 307-frame population without admitting isolated antialias noise.
MIN_PIXELS = 60
SHEET_BG = (0, 0, 41)


def is_bg(pixel: tuple[int, int, int]) -> bool:
    return all(abs(a - b) <= BG_TOL for a, b in zip(pixel, SHEET_BG))


def hue_family(pixel: tuple[int, int, int]) -> str:
    r, g, b = pixel
    if g > r + 40 and g > b + 40:
        return "green"
    if b > r + 40 and b > g + 20:
        return "blue"
    if r > g + 40 and b > g + 40:
        return "purple"
    if r > g + 40 and r > b + 40:
        return "orange" if g > 60 else "red"
    return "other"


def neighbours(x: int, y: int, width: int, height: int) -> Iterable[tuple[int, int]]:
    for dy in range(-BRIDGE, BRIDGE + 1):
        for dx in range(-BRIDGE, BRIDGE + 1):
            if not dx and not dy:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                yield nx, ny


def components(image: Image.Image) -> list[list[tuple[int, int]]]:
    width, height = image.size
    pixels = image.load()
    foreground = {(x, y) for y in range(height) for x in range(width) if not is_bg(pixels[x, y][:3])}
    found: set[tuple[int, int]] = set()
    result = []
    for seed in foreground:
        if seed in found:
            continue
        found.add(seed)
        queue = collections.deque([seed])
        component = []
        while queue:
            x, y = queue.popleft()
            component.append((x, y))
            for neighbour in neighbours(x, y, width, height):
                if neighbour in foreground and neighbour not in found:
                    found.add(neighbour)
                    queue.append(neighbour)
        if len(component) >= MIN_PIXELS:
            result.append(component)
    return result


def median(values: list[float]) -> float:
    values = sorted(values)
    if not values:
        return 0.0
    return values[len(values) // 2]


def observe(image: Image.Image, component: list[tuple[int, int]], index: int) -> dict:
    pixels = image.load()
    x0 = min(x for x, _ in component)
    x1 = max(x for x, _ in component)
    y0 = min(y for _, y in component)
    y1 = max(y for _, y in component)
    width = x1 - x0 + 1
    height = y1 - y0 + 1
    points = set(component)
    hues = collections.Counter(hue_family(pixels[x, y][:3]) for x, y in component)
    dominant = hues.most_common(1)[0][0] if hues else "other"
    accents = [(x, y) for x, y in component if hue_family(pixels[x, y][:3]) not in (dominant, "other")]

    rows = []
    for y in range(y0, y1 + 1):
        xs = [x for x in range(x0, x1 + 1) if (x, y) in points]
        if not xs:
            rows.append(None)
            continue
        rows.append({"row": y - y0, "left": min(xs) - x0, "right": max(xs) - x0, "width": max(xs) - min(xs) + 1})

    bands = []
    for band_name, start, end in (("top", 0.0, 1 / 3), ("middle", 1 / 3, 2 / 3), ("bottom", 2 / 3, 1.0)):
        selected = [(x, y) for x, y in component if y0 + height * start <= y < y0 + height * end]
        bands.append({"name": band_name, "strokePixels": len(selected), "density": round(len(selected) / max(1, width * height * (end - start)), 5)})

    occupied = [row for row in rows if row is not None]
    row_centres = [((row["left"] + row["right"]) / 2, row["row"]) for row in occupied]
    if row_centres:
        first = row_centres[0][0]
        last = row_centres[-1][0]
        centre_drift = (last - first) / max(1, width)
        asymmetry = median([abs((row["left"] + row["right"]) / 2 - (width - 1) / 2) for row in occupied]) / max(1, width)
    else:
        centre_drift = 0.0
        asymmetry = 0.0

    accent_record = None
    if accents:
        ax = [x - x0 for x, _ in accents]
        ay = [y - y0 for _, y in accents]
        accent_record = {
            "count": len(accents),
            "left": min(ax), "right": max(ax), "top": min(ay), "bottom": max(ay),
            "centreX": round(sum(ax) / len(ax), 3),
            "centreY": round(sum(ay) / len(ay), 3),
            "width": max(ax) - min(ax) + 1,
            "height": max(ay) - min(ay) + 1,
        }

    return {
        "id": index,
        "bbox": {"x0": x0, "y0": y0, "width": width, "height": height},
        "strokePixels": len(component),
        "aspect": round(width / max(1, height), 5),
        "palette": dict(hues),
        "dominantHue": dominant,
        "accent": accent_record,
        "centroidDrift": round(centre_drift, 5),
        "rowCentreAsymmetry": round(asymmetry, 5),
        "regionalDensity": bands,
        "rows": rows,
    }


def main() -> None:
    source, output = sys.argv[1:3]
    image = Image.open(source).convert("RGB")
    detected = components(image)
    observations = [observe(image, component, index) for index, component in enumerate(detected)]
    observations.sort(key=lambda item: (item["bbox"]["y0"], item["bbox"]["x0"]))
    for index, observation in enumerate(observations):
        observation["id"] = index
    record = {
        "source": source,
        "sheetSize": list(image.size),
        "background": SHEET_BG,
        "bridgePx": BRIDGE,
        "componentCount": len(observations),
        "observations": observations,
        "notes": [
            "Each sprite is measured independently; no mirror or camera symmetry is assumed.",
            "rowCentreAsymmetry is a projection observation, not proof of physical asymmetry by itself.",
            "Accent is a proxy for the eye/face region and can be occluded in oblique frames.",
        ],
    }
    pathlib.Path(output).write_text(json.dumps(record, indent=2))
    print(json.dumps({"componentCount": len(observations), "sheetSize": list(image.size)}, indent=2))
    print("first frames:", [(o["id"], o["bbox"], o["aspect"]) for o in observations[:8]])
    print("last frames:", [(o["id"], o["bbox"], o["aspect"]) for o in observations[-8:]])


if __name__ == "__main__":
    main()
