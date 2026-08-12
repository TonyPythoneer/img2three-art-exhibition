#!/usr/bin/env python3
"""Are the two purple films the same colour on the side that faces the shell? Measured, per cause.

The complaint is about colour, and on this build the cause of a colour symptom has been in the
render path four times out of four. So this never asks "what colour is it" without also asking
"which of the two things that set the colour did it": the model bakes the artwork's key into
vertex colour with `applyFacetSteps`, and the look-dev rig then lights the result with a
DIRECTIONAL light pointing along the SAME measured vector, (-0.42, 0.62, 0.66). Both carry +Z, so
both make a +Z-facing face brighter than a -Z-facing one, and a single lit render cannot separate
them.

`capture_skin_faces.sh` therefore takes each frame twice — once normally and once with `--flat`,
which swaps every material for an unlit `MeshBasicMaterial` carrying the same vertex colours. In
the flat pass the pixel IS the vertex colour, so:

    flat delta   = what the MODEL authored
    lit  delta   = that, plus what the RIG did with it

Each frame shows one half from one camera, so every foreground pixel is a single face of a single
mesh. The front camera sees the REAR half's underside (it faces +Z) and the back camera sees the
FRONT half's underside, which is why the two "shell-facing" readings come from opposite cameras.

Measured on the build this replaces, on the two shell-facing undersides: flat
(78.67, 43.82, 164.43) front against (85.83, 48.18, 178.52) rear, a linear-light ratio of 1.2003;
lit, 1.2748. The two factor cleanly — 1.2748 / 1.2003 = 1.0621 — so 20.0 points of it were the
model and 6.2 were the rig. The model's share is now 1.0000 by construction (`applyFacetSteps`
takes the mirrored key for the rear half) and `check_centerline.py` asserts it from the geometry
on every gate run. What is left is the rig's 1.0629, and a rig cannot be mirrored per half without
lighting the two sides of one blade with two different lamps.

    zsh  src/exhibits/ff7-cloud-strife-ultima-weapon/spec/capture_skin_faces.sh   # captures, then this
    python3 src/exhibits/ff7-cloud-strife-ultima-weapon/spec/measure_skin_faces.py

Writes artifacts/ultima-v2/diag/skin-faces.json. Never exits non-zero: the assertion with teeth is
in `check_centerline.py`, against the geometry. This is the diagnosis, kept reproducible.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[3] / "artifacts" / "ultima-v2" / "diag"

# label -> (file, what that frame actually shows)
FRAMES = {
    ("flat", "shell-facing", "front half"): "back-orthographic-flatInsertFront.png",
    ("flat", "shell-facing", "rear half"): "front-orthographic-flatInsertRear.png",
    ("flat", "outward", "front half"): "front-orthographic-flatInsertFront.png",
    ("flat", "outward", "rear half"): "back-orthographic-flatInsertRear.png",
    ("lit", "shell-facing", "front half"): "back-orthographic-litInsertFront.png",
    ("lit", "shell-facing", "rear half"): "front-orthographic-litInsertRear.png",
    ("lit", "outward", "front half"): "front-orthographic-litInsertFront.png",
    ("lit", "outward", "rear half"): "back-orthographic-litInsertRear.png",
}


def mean_rgb(path: Path) -> tuple[int, tuple[float, float, float]]:
    """Mean sRGB over the frame's foreground — the one film, since nothing else is visible."""
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    width, height = image.size
    total = [0.0, 0.0, 0.0]
    count = 0
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a > 200 and min(r, g, b) < 244:
                total[0] += r
                total[1] += g
                total[2] += b
                count += 1
    if count == 0:
        raise SystemExit(f"{path.name} has no foreground — the hide list took the film out too")
    return count, tuple(round(c / count, 2) for c in total)


def to_linear(value: float) -> float:
    v = value / 255
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def main() -> None:
    report: dict[str, dict] = {}
    for (lighting, face, half), name in FRAMES.items():
        path = DIAG / name
        if not path.exists():
            raise SystemExit(f"{path} is missing — run spec/capture_skin_faces.sh first")
        count, rgb = mean_rgb(path)
        report.setdefault(lighting, {}).setdefault(face, {})[half] = {
            "file": name,
            "pixels": count,
            "srgb": list(rgb),
        }

    for lighting, faces in report.items():
        for face, halves in faces.items():
            front = halves["front half"]["srgb"]
            rear = halves["rear half"]["srgb"]
            # Blue carries most of the film's signal, and the whole difference is a single
            # multiplier on the ramp, so one channel's linear ratio IS the difference.
            ratio = to_linear(rear[2]) / to_linear(front[2]) if front[2] else 1.0
            halves["linearRatio"] = round(ratio, 4)
            print(
                f"{lighting:<4} {face:<12} front {tuple(front)}  rear {tuple(rear)}  "
                f"rear/front in linear light {ratio:.4f}"
            )

    out = DIAG / "skin-faces.json"
    out.write_text(f"{json.dumps(report, indent=2)}\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
