#!/usr/bin/env python3
"""prompt.txt §5 — the sole's own mechanical gates (S-01 soleSlab).

    node tools/capture_parts.mjs --part soleL --out <dir>
    node tools/capture_parts.mjs --part soleR --out <dir2>
    python3 spec/gate_sole.py <dir>/meshes.json <dir2>/meshes.json

Reads the SAME geometry export the review renders were taken of, and asserts, each with a
number rather than a verdict:

  §5.4  triangle count inside the part's spec budget          (the facet gate itself is
        `gate_facets.py check`, run separately on the same file)
  §5.5  the local origin IS the upper socket `soleTop`: the top face is on y=0 and the
        bottom on y=-T, so translating the part to soleTop's figure height lands the
        bottom face on the ground at Y=0
  §5.10 mirror consistency: negate the R part's x and it matches the L part point for point
  §4[1] the measured extents A (lateral), B (fore-aft) and T (thickness), the trapezoid's
        wide-heel/narrow-toe direction, and the two blunt end chamfers

Every expected value comes from spec/landmarks.json; nothing here is typed in. Pure stdlib.

⚠ The plan outline's L/W, toe taper and end chamfer are ADOPTED, not measured, and this
  gate cannot falsify them: A, B and T fix all four orthographic silhouettes for every
  (L, W, theta) that reproduces them. Only §5.2's three-quarter orbit render can.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import socket_gate  # noqa: E402  (same directory; the sys.path line above is what enables it)

HERE = Path(__file__).resolve().parent
LM = json.loads((HERE / "landmarks.json").read_text())
SPEC = json.loads((HERE / "object-sculpt-spec.json").read_text())
SOLE = LM["parts"]["sole"]
RMS = LM["normalization"]["sole->chin"]["measurementUncertaintyRms"]
BUDGET = next(c["triangleBudget"] for c in SPEC["componentTree"] if c["id"] == "soleL")


def load(path: Path) -> tuple[dict, dict]:
    """The whole capture document and its single mesh — the sockets live beside the meshes
    in it, and `socket_gate` reads them from there."""
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
    """Six times the enclosed volume. Positive means the faces wind outward — a slab built
    inside-out still passes every dimension check and still renders as a hole."""
    v = mesh["vertices"]
    return sum(
        v[a][0] * (v[b][1] * v[c][2] - v[b][2] * v[c][1])
        - v[a][1] * (v[b][0] * v[c][2] - v[b][2] * v[c][0])
        + v[a][2] * (v[b][0] * v[c][1] - v[b][1] * v[c][0])
        for a, b, c in tris(mesh)
    )


def foot_local(mesh: dict, side_sign: float) -> list[tuple[float, float]]:
    """The built vertices turned back into the foot's OWN frame: +z along the sole's long
    axis toward the toe, +x across it.

    Measuring the taper in the figure frame does not work and looked like it did: at 45
    degrees of splay the x-extent of a z-band is dominated by the slab's own diagonal, so
    the first version of this gate reported heel 0.068 > toe 0.049 for a slab whose toe end
    is visibly the wider one in a top-down render. Un-rotating first is what makes 'wide at
    the heel, narrow at the toe' a statement about the trapezoid instead of about the pose.
    """
    t = math.radians(SOLE["splayDeg"]["derived"]) * side_sign
    cos, sin = math.cos(-t), math.sin(-t)
    return [(v[0] * cos + v[2] * sin, -v[0] * sin + v[2] * cos) for v in mesh["vertices"]]


def width_at(pts: list[tuple[float, float]], z_lo: float, z_hi: float) -> float:
    """The slab's spread across its own long axis over a band of that axis."""
    xs = [x for x, z in pts if z_lo <= z <= z_hi]
    return max(xs) - min(xs) if len(xs) > 1 else 0.0


RESULTS: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str) -> None:
    RESULTS.append((label, ok, detail))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit(__doc__)
    (doc_l, left), (doc_r, right) = (load(Path(a)) for a in argv)

    n_tris = len(tris(left))
    check("§5.4 triangle budget", n_tris <= BUDGET, f"{n_tris} <= {BUDGET}")

    lo, hi = extents(left)
    for axis, name, expected in (
        (0, "A lateral (X)", SOLE["lateralExtent"]["adopted"]),
        (1, "T thickness (Y)", SOLE["thickness"]["adopted"]),
        (2, "B fore-aft (Z)", SOLE["foreAftExtent"]["adopted"]),
    ):
        built = hi[axis] - lo[axis]
        check(
            f"§4[1] {name}",
            abs(built - expected) <= RMS,
            f"built {built:.5f} vs measured {expected:.5f}, delta {abs(built - expected):.5f} <= RMS {RMS:.5f}",
        )

    check(
        "§5.5 origin is soleTop (top face on y=0)",
        abs(hi[1]) < 1e-6,
        f"top face y = {hi[1]:.9f}",
    )
    check(
        "§5.5 bottom face at -T (lands on the ground when placed)",
        abs(lo[1] + SOLE["thickness"]["adopted"]) < 1e-6,
        f"bottom face y = {lo[1]:.9f}, -T = {-SOLE['thickness']['adopted']:.9f}",
    )
    check(
        "§4[1] centred on its own origin in plan",
        abs(hi[0] + lo[0]) < 1e-6 and abs(hi[2] + lo[2]) < 1e-6,
        f"x centre {(hi[0] + lo[0]) / 2:.9f}, z centre {(hi[2] + lo[2]) / 2:.9f}",
    )

    volume = signed_volume(left)
    check("faces wind outward", volume > 0, f"6V = {volume:+.6f}")

    pts = foot_local(left, 1.0)
    z_lo = min(z for _, z in pts)
    z_hi = max(z for _, z in pts)
    span_z = z_hi - z_lo
    check(
        "§4[1] plan length matches the solved trapezoid",
        abs(span_z - SOLE["planTrapezoid"]["length"]) <= RMS,
        f"foot-local length {span_z:.5f} vs solved {SOLE['planTrapezoid']['length']:.5f}",
    )

    heel = width_at(pts, z_lo, z_lo + span_z / 4)
    toe = width_at(pts, z_hi - span_z / 4, z_hi)
    check(
        "§4[1] wide at the heel, narrow at the toe",
        heel > toe,
        f"heel-quarter width {heel:.5f} > toe-quarter width {toe:.5f} "
        f"(taper {toe / heel:.3f} against the adopted {SOLE['adopted']['toeTaper']})",
    )

    # Both ends are blunt: a chamfered end contributes its own facet, so the extreme rows
    # carry real width instead of converging on a point.
    c = SOLE["planTrapezoid"]["endChamfer"]
    for name, z0, z1 in (("heel", z_lo, z_lo + c / 4), ("toe", z_hi - c / 4, z_hi)):
        blunt = width_at(pts, z0, z1)
        check(
            f"§4[1] {name} end is a blunt chamfer, not a point",
            blunt > 0.0,
            f"width at the extreme {name} band = {blunt:.5f}",
        )

    # §4's socket contract. The sole is the bottom of the chain and emits nothing, so what
    # this proves is that `sockets = {}` is DECLARED — "emits nothing" and "forgot to
    # declare" are the same file to a reader and different bugs to the assembly.
    RESULTS.extend(socket_gate.shape_checks(doc_l, "soleL"))
    RESULTS.extend(socket_gate.shape_checks(doc_r, "soleR"))
    RESULTS.append(socket_gate.mirror_check(doc_l, doc_r, "soleL", "soleR"))

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
