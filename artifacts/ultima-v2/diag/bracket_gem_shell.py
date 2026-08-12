#!/usr/bin/env python3
"""Bracket the gem-proud-of-the-SHELL floor now that it is scored by survival, not identity.

Changing how a gate scores is a change to the gate, so the 0.70 floor has to be shown to sit
between geometry the test must REJECT and geometry it must ACCEPT — measured through the same
script, on doctored frames rather than on an argument.

Three variants, each written by editing ONE captured frame (`*-gemShell.png`, the frame that says
who won) inside the gem's own footprint:

  shell-wins-all    every pixel of the overlap takes the colour it reads in `shellOnly` — the
                    shell in front of the whole stone, which is what the gate exists to reject
  shell-wins-rim    only the footprint's outer 3 px take it, the interior untouched — a stone
                    whose OUTLINE is buried while its plateau still stands proud. This is the
                    defect an area score is worst at seeing and it is the one that shipped once
  built             the frames as captured

Writes one scratch render dir per variant and runs `measure_relief_visibility.py` on each.

    python3 artifacts/ultima-v2/diag/bracket_gem_shell.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
VIS = ROOT / "artifacts/ultima-v2/vis"
HERE = Path(__file__).resolve().parent
SCRIPT = ROOT / "artifacts/exhibits/ff7-cloud-strife-ultima-weapon/spec/measure_relief_visibility.py"
OWN = 14
VIEWS = ("front-orthographic", "back-orthographic")


def footprint(d: Path, view: str) -> tuple[set[int], int, int]:
    base = Image.open(d / f"{view}-base.png").convert("RGB")
    only = Image.open(d / f"{view}-gemOnly.png").convert("RGB")
    b, o = base.load(), only.load()
    w, h = base.size
    return (
        {
            y * w + x
            for y in range(h)
            for x in range(w)
            if max(abs(o[x, y][c] - b[x, y][c]) for c in range(3)) >= OWN
        },
        w,
        h,
    )


def erode(mask: set[int], w: int, h: int, times: int) -> set[int]:
    cur = mask
    for _ in range(times):
        cur = {
            p
            for p in cur
            if p % w not in (0, w - 1)
            and p // w not in (0, h - 1)
            and {p - 1, p + 1, p - w, p + w} <= cur
        }
    return cur


def variant(name: str, pixels_for: "callable") -> None:
    out = HERE / f"bracket-{name}"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for f in VIS.glob("*.png"):
        shutil.copy(f, out / f.name)
    for view in VIEWS:
        mask, w, h = footprint(VIS, view)
        target = pixels_for(mask, w, h)
        over = Image.open(out / f"{view}-gemShell.png").convert("RGB")
        alone = Image.open(VIS / f"{view}-shellOnly.png").convert("RGB")
        px, ap = over.load(), alone.load()
        for p in target:
            x, y = p % w, p // w
            px[x, y] = ap[x, y]
        over.save(out / f"{view}-gemShell.png")
    print(f"\n=== {name} ===")
    subprocess.run([sys.executable, str(SCRIPT), str(out)], check=False)


variant("shell-wins-all", lambda mask, w, h: mask)
# A sweep rather than one rim, because the floor is 0.70 and the question is not "does a 3 px rim
# fail" (that is SEAT_FLOOR's job at 0.95) but "where does 0.70 actually cut". Each variant buries
# one more ring of the stone's outline under the shell.
for n in (3, 4, 5, 6, 8):
    variant(f"shell-wins-rim{n}", lambda mask, w, h, n=n: mask - erode(mask, w, h, n))
print("\n=== built ===")
subprocess.run([sys.executable, str(SCRIPT), str(VIS)], check=False)
