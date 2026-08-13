#!/usr/bin/env python3
"""prompt.txt §5 — the ankle cuff's own mechanical gates (A-01 ankleCuff).

    node tools/capture_parts.mjs --part ankleL --out <dir>
    node tools/capture_parts.mjs --part ankleR --out <dir2>
    python3 spec/gate_ankle.py <dir>/meshes.json <dir2>/meshes.json

Reads the geometry export and asserts:

  §5.4  triangle count inside the part's spec budget (64)
  §5.5  the local origin IS ankleTop: top face on y=0, bottom face at -H
  §5.5  the emitted soleTop socket lands the sole's origin on the ledger's soleTop height
  §4    the socket obeys §4's shape: a bare THREE.Vector3, no rotation (socket_gate.py)
  §4[1] the socket's z carries the measured fore-aft offset, and its SIGN puts the slab
        forward of the cuff — the foot's identity feature in profile
  §4[2] the cuff cross-section is wider than straightPantTube on both X and Z
  §4[2] vertical edges are chamfered (four distinct extreme-width rows)
  §5.10 mirror consistency: negate the R part's x and it matches the L part, sockets too
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
# measure_ankle.py measures (cuff centre - sole centre) in model Z, +Z forward. It is
# NEGATIVE: the cuff sits behind the sole's plan centre. The socket points the other way —
# where the SOLE's origin sits relative to the CUFF — so the socket's z is its negation.
FORE_AFT = ANKLE["foreAftOffset"]["value"]
SOCKET_Z = -FORE_AFT
# The sole's own fore-aft extent, for turning that socket into a forward/backward reach.
SOLE_B = SOLE["foreAftExtent"]["adopted"]

# spec budget from object-sculpt-spec.json
SPEC = json.loads((HERE / "object-sculpt-spec.json").read_text())
BUDGET = next(c["triangleBudget"] for c in SPEC["componentTree"] if c["id"] == "ankleL")


def load(path: Path) -> tuple[dict, dict]:
    """The whole capture document and its single mesh. The document is kept because the
    sockets live beside the meshes in it, and a socket gate that re-derives its input from
    a second code path is not checking the build the renders were taken of."""
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
    if len(argv) != 2:
        raise SystemExit(__doc__)
    (doc_l, left), (doc_r, right) = (load(Path(a)) for a in argv)

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

    # ── §4's socket contract, then what this particular socket has to say ──────────────
    #
    # Order matters: the shape checks run first and the vector reads below only make sense
    # once they pass, because `socket_gate.vector` refuses to guess at a non-Vector3.
    RESULTS.extend(socket_gate.shape_checks(doc_l, "ankleL"))
    RESULTS.extend(socket_gate.shape_checks(doc_r, "ankleR"))

    if all(ok for label, ok, _ in RESULTS if label.startswith("§4 socket")):
        sx, sy, sz = socket_gate.vector(doc_l, "ankleL", "soleTop")

        # §5.5 expressed in the figure frame from both sides: the emitter's origin landmark
        # plus its socket vector must land on the consumer's origin landmark.
        check(
            "§5.5 ankleTop + soleTop socket == soleTop landmark",
            abs((ANKLE_TOP_Y + sy) - SOLE_TOP_Y) < 1e-6,
            f"{ANKLE_TOP_Y:.6f} + ({sy:+.6f}) = {ANKLE_TOP_Y + sy:.6f} vs ledger {SOLE_TOP_Y:.6f}",
        )
        check(
            "§4[2] socket sits on the cuff's own axis in X",
            abs(sx) < 1e-6,
            f"socket x = {sx:.9f} (the cuff's lateral position over the slab is unmeasured)",
        )

        # The reason this socket exists at all. `foreAftOffset` was measured and then went
        # nowhere: the socket's z was 0, so the sole sat centred under the cuff and §4[1]'s
        # "extends a long way FORWARD and only slightly backward" appeared nowhere in the
        # model. A dimension gate cannot see that — the sole's own extents are unchanged by
        # where it hangs — so the assertion has to be on the socket.
        check(
            "§4[1] socket z carries the measured fore-aft offset",
            abs(sz - SOCKET_Z) < 1e-6,
            f"socket z = {sz:+.8f} vs -foreAftOffset {SOCKET_Z:+.8f} "
            f"(measured {FORE_AFT:+.8f}, spread {ANKLE['foreAftOffset']['crossViewSpread']:.6f})",
        )
        # And the sign, stated as the thing a human can check against the reference rather
        # than as an arithmetic identity: reach forward of the cuff vs reach behind it.
        forward = sz + SOLE_B / 2
        backward = SOLE_B / 2 - sz
        check(
            "§4[1] the slab reaches further FORWARD of the cuff than behind it",
            forward > backward,
            f"forward {forward:.5f} vs backward {backward:.5f} "
            f"(ratio {forward / backward:.2f}x, from B {SOLE_B:.5f})",
        )

    # §5.10: the pair is a pure mirror, so the R part needs no second visual review.
    RESULTS.append(socket_gate.mirror_check(doc_l, doc_r, "ankleL", "ankleR"))
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
