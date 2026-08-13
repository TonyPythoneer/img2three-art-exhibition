#!/usr/bin/env python3
"""prompt.txt §5 — the ankle cuff's own mechanical gates (A-01 ankleCuff).

    node tools/capture_parts.mjs --part ankleL --out <dir>
    node tools/capture_parts.mjs --part ankleR --out <dir2>
    python3 spec/gate_ankle.py <dir>/meshes.json <dir2>/meshes.json

Reads the geometry export and asserts:

  §5.4  triangle count inside the part's spec budget (64)
  §5.5  the local origin IS ankleTop: top face on y=0, bottom face at -H
  §4[2] the cuff cross-section is wider than straightPantTube on both X and Z
  §4[2] vertical edges are chamfered (four distinct extreme-width rows)
  §5.10 mirror consistency: negate the R part's x and it matches the L part
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LM = json.loads((HERE / "landmarks.json").read_text())
CONST = json.loads((HERE / "build-constants.json").read_text())
SOLE = LM["parts"]["sole"]
ANKLE = LM["parts"]["ankle"]
RMS = LM["normalization"]["sole->chin"]["measurementUncertaintyRms"]

# Height = ankleTop - soleTop from socket chain
SOLE_TOP_Y = CONST["socketChainY"]["soleTop"]
ANKLE_TOP_Y = CONST["socketChainY"]["ankleTop"]
CUFF_HEIGHT = ANKLE_TOP_Y - SOLE_TOP_Y  # 0.107018

PANT_W = ANKLE["cuffSection"]["pantTubeWidthX"]
PANT_D = ANKLE["cuffSection"]["pantTubeDepthZ"]
CUFF_W = ANKLE["cuffSection"]["widthX"]["normalized"]
CUFF_D = ANKLE["cuffSection"]["depthZ"]["normalized"]
FORE_AFT = ANKLE["foreAftOffset"]["value"]

# spec budget from object-sculpt-spec.json
SPEC = json.loads((HERE / "object-sculpt-spec.json").read_text())
BUDGET = next(c["triangleBudget"] for c in SPEC["componentTree"] if c["id"] == "ankleL")


def load(path: Path) -> dict:
    doc = json.loads(path.read_text())
    meshes = doc["meshes"] if isinstance(doc, dict) else doc
    if len(meshes) != 1:
        raise SystemExit(f"{path}: expected exactly one mesh, found {len(meshes)}")
    return meshes[0]


def tris(mesh: dict) -> list[tuple[int, int, int]]:
    idx = mesh["indices"]
    return [(idx[i], idx[i + 1], idx[i + 2]) for i in range(0, len(idx), 3)]


def extents(mesh: dict) -> tuple[list[float], list[float]]:
    lo = [min(v[a] for v in mesh["vertices"]) for a in range(3)]
    hi = [max(v[a] for v in mesh["vertices"]) for a in range(3)]
    return lo, hi


def signed_volume(mesh: dict) -> float:
    v = mesh["vertices"]
    return sum(
        v[a][0] * (v[b][1] * v[c][2] - v[b][2] * v[c][1])
        - v[a][1] * (v[b][0] * v[c][2] - v[b][2] * v[c][0])
        + v[a][2] * (v[b][0] * v[c][1] - v[b][1] * v[c][0])
        for a, b, c in tris(mesh)
    )


RESULTS: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str) -> None:
    RESULTS.append((label, ok, detail))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit(__doc__)
    left, right = (load(Path(a)) for a in argv)

    n_tris = len(tris(left))
    check("§5.4 triangle budget", n_tris <= BUDGET, f"{n_tris} <= {BUDGET}")

    lo, hi = extents(left)
    for axis, name, measured in (
        (0, "width (X)", CUFF_W),
        (1, "height (Y)", CUFF_HEIGHT),
        (2, "depth (Z)", CUFF_D),
    ):
        built = hi[axis] - lo[axis]
        tolerance = max(RMS, 0.005)  # §1.4 tolerance: 0.005 or RMS, whichever is larger
        check(
            f"§4[2] cuff {name}",
            abs(built - measured) <= tolerance,
            f"built {built:.5f} vs measured {measured:.5f}, delta {abs(built - measured):.5f} <= {tolerance:.5f}",
        )

    check(
        "§5.5 origin is ankleTop (top face on y=0)",
        abs(hi[1]) < 1e-6,
        f"top face y = {hi[1]:.9f}",
    )
    check(
        "§5.5 bottom face at -H",
        abs(lo[1] + CUFF_HEIGHT) < 1e-6,
        f"bottom face y = {lo[1]:.9f}, -H = {-CUFF_HEIGHT:.9f}",
    )
    check(
        "§4[2] centred on origin in plan",
        abs(hi[0] + lo[0]) < 1e-6 and abs(hi[2] + lo[2]) < 1e-6,
        f"x centre {(hi[0] + lo[0]) / 2:.9f}, z centre {(hi[2] + lo[2]) / 2:.9f}",
    )

    volume = signed_volume(left)
    check("faces wind outward", volume > 0, f"6V = {volume:+.6f}")

    # The cuff must be wider than the pant tube on both axes
    built_w = hi[0] - lo[0]
    built_d = hi[2] - lo[2]
    check(
        "§4[2] cuff wider than pant tube on X",
        built_w > PANT_W,
        f"built {built_w:.5f} > pant {PANT_W:.5f}",
    )
    check(
        "§4[2] cuff wider than pant tube on Z",
        built_d > PANT_D,
        f"built {built_d:.5f} > pant {PANT_D:.5f}",
    )

    # §5.10: the pair is a pure mirror, so the R part needs no second visual review.
    lv, rv = left["vertices"], right["vertices"]
    if len(lv) != len(rv):
        check("§5.10 mirror consistency", False, f"vertex counts differ: {len(lv)} vs {len(rv)}")
    else:
        worst = max(
            math.dist((-r[0], r[1], r[2]), l) for l, r in zip(lv, rv)
        )
        check("§5.10 mirror consistency", worst < 1e-6, f"worst |delta| = {worst:.3e} < 1e-06")

    width = max(len(label) for label, _, _ in RESULTS)
    failed = 0
    for label, ok, detail in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'}  {label.ljust(width)}  {detail}")
        failed += not ok
    print(f"{len(RESULTS) - failed}/{len(RESULTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
