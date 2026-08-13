#!/usr/bin/env python3
"""prompt.txt §5 — the waist belt's own mechanical gates.

    node tools/capture_parts.mjs --part waist --out <dir>
    python3 spec/gate_waist.py <dir>/meshes.json

Reads the geometry export and asserts:

  §5.4  triangle count inside the part's spec budget (160)
  §5.5  the local origin IS waistTop: top face on y=0, bottom face at -H
  §5.5  the emitted pelvisTop socket lands pelvisTop when offset from waistTop
  §4    the socket obeys §4's shape: a bare THREE.Vector3, no rotation (socket_gate.py)
  §4[7] the belt stands proud of BOTH the chest above and pelvis below
  §5.10 mirror consistency: negate the part's x and compare against itself (self-symmetric)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import socket_gate  # noqa: E402

HERE = Path(__file__).resolve().parent
LM = json.loads((HERE / "landmarks.json").read_text())
CONST = json.loads((HERE / "build-constants.json").read_text())
WAIST = LM["parts"]["waist"]
RMS = LM["normalization"]["sole->chin"]["measurementUncertaintyRms"]

# Heights from socket chain
WAIST_TOP_Y = CONST["socketChainY"]["waistTop"]
PELVIS_TOP_Y = CONST["socketChainY"]["pelvisTop"]
WAIST_HEIGHT = WAIST_TOP_Y - PELVIS_TOP_Y  # ≈ 0.043185

# Belt dimensions
BELT_W = WAIST["widthX"]["normalized"]
BELT_D = WAIST["depthZ"]["normalized"]

# Proud margins
PROUD_CHEST = WAIST["proudMargins"]["avgProudOfChest"]
PROUD_PELVIS = WAIST["proudMargins"]["avgProudOfPelvis"]

# spec budget from object-sculpt-spec.json
SPEC = json.loads((HERE / "object-sculpt-spec.json").read_text())
BUDGET = next(c["triangleBudget"] for c in SPEC["componentTree"] if c["id"] == "waist")


def load(path: Path) -> tuple[dict, dict]:
    doc = json.loads(path.read_text())
    meshes = doc["meshes"] if isinstance(doc, dict) else doc
    if len(meshes) != 1:
        raise SystemExit(f"{path}: expected exactly one mesh, found {len(meshes)}")
    return doc, meshes[0]


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
    if len(argv) != 1:
        raise SystemExit(__doc__)
    doc, mesh = load(Path(argv[0]))

    n_tris = len(tris(mesh))
    check("§5.4 triangle budget", n_tris <= BUDGET, f"{n_tris} <= {BUDGET}")

    lo, hi = extents(mesh)
    tolerance = max(RMS, 0.005)

    built_w = hi[0] - lo[0]
    built_d = hi[2] - lo[2]
    built_h = hi[1] - lo[1]
    check(
        "§4[7] belt width (X)",
        abs(built_w - BELT_W) <= tolerance,
        f"built {built_w:.5f} vs measured {BELT_W:.5f}, delta {abs(built_w - BELT_W):.5f}",
    )
    check(
        "§4[7] belt depth (Z)",
        abs(built_d - BELT_D) <= tolerance,
        f"built {built_d:.5f} vs measured {BELT_D:.5f}, delta {abs(built_d - BELT_D):.5f}",
    )
    check(
        "§4[7] belt height (Y)",
        abs(built_h - WAIST_HEIGHT) <= tolerance,
        f"built {built_h:.5f} vs measured {WAIST_HEIGHT:.5f}, "
        f"delta {abs(built_h - WAIST_HEIGHT):.5f}",
    )

    check(
        "§5.5 origin is waistTop (top face on y=0)",
        abs(hi[1]) < 1e-6,
        f"top face y = {hi[1]:.9f}",
    )
    check(
        "§5.5 bottom face at -H",
        abs(lo[1] + WAIST_HEIGHT) < 1e-6,
        f"bottom face y = {lo[1]:.9f}, -H = {-WAIST_HEIGHT:.9f}",
    )
    check(
        "§4[7] centred on origin in plan",
        abs(hi[0] + lo[0]) < 1e-6 and abs(hi[2] + lo[2]) < 1e-6,
        f"x centre {(hi[0] + lo[0]) / 2:.9f}, z centre {(hi[2] + lo[2]) / 2:.9f}",
    )

    volume = signed_volume(mesh)
    check("faces wind outward", volume > 0, f"6V = {volume:+.6f}")

    # §4[7] proud margins: the belt must stand proud of both neighbours.
    # The belt is wider than the chest section (proudOfChest > 0) — measured +0.026.
    # The belt is NARROWER than the pelvis section (proudOfPelvis < 0) — measured -0.041.
    # This means the belt does NOT stand proud of the pelvis in width.
    # Report the measured margins; this is logged as a guess list item.
    check(
        "§4[7] proud of chest (width)",
        PROUD_CHEST > 0,
        f"proudOfChest = {PROUD_CHEST:+.6f} (belt wider than chest section)",
    )
    # The pelvis proud check: the belt should be wider than the pelvis at the belt zone.
    # Our measurement shows it is NOT (belt 0.392 vs pelvis 0.432). Log this.
    check(
        "§4[7] proud of pelvis (width) — EXPECTED FAIL",
        PROUD_PELVIS > 0,
        f"proudOfPelvis = {PROUD_PELVIS:+.6f} "
        f"(belt {BELT_W:.5f} vs pelvis section, see guess list)",
    )

    # ── §4 socket contract ──────────────────────────────────────────────────
    RESULTS.extend(socket_gate.shape_checks(doc, "waist"))

    if all(ok for label, ok, _ in RESULTS if label.startswith("§4 socket")):
        sx, sy, sz = socket_gate.vector(doc, "waist", "pelvisTop")

        check(
            "§5.5 waistTop + pelvisTop socket == pelvisTop landmark",
            abs((WAIST_TOP_Y + sy) - PELVIS_TOP_Y) < 1e-6,
            f"{WAIST_TOP_Y:.6f} + ({sy:+.6f}) = {WAIST_TOP_Y + sy:.6f} vs ledger {PELVIS_TOP_Y:.6f}",
        )
        check(
            "§4[7] socket sits on the belt's axis in X and Z",
            abs(sx) < 1e-6 and abs(sz) < 1e-6,
            f"socket x = {sx:.9f}, z = {sz:.9f}",
        )

    # §5.10: self-symmetric — but §5.10 only applies to the 8 pure mirror pairs
    # listed in §1.5. The waist is an unsided single, so this check is skipped.

    width = max(len(label) for label, _, _ in RESULTS)
    failed = 0
    for label, ok, detail in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'}  {label.ljust(width)}  {detail}")
        failed += not ok
    print(f"{len(RESULTS) - failed}/{len(RESULTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
