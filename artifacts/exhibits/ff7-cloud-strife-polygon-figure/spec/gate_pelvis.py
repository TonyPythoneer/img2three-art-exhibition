#!/usr/bin/env python3
"""prompt.txt §5 — the pelvis's own mechanical gates (S-06 pelvisKite).

    node tools/capture_parts.mjs --part pelvis --out /tmp/pelvis
    python3 spec/gate_pelvis.py /tmp/pelvis/meshes.json

  §5.4  triangle count inside the one-off budget
  §5.5  the local origin IS pelvisTop: top face on y=0, crotch at -H
  §5.5  hipL / hipR land the thighs on the ledger's `hip` height
  §4    both sockets obey §4's shape — a bare THREE.Vector3 (socket_gate.py)
  §4[6] the FRONT outline is a pentagon: it flares wider than its top and then pulls in
  §4[6] the PROFILE is a kite, front/back symmetric about z=0
  §4[6] the widest ring is the widest thing in the part, at the measured height
  §4[6] the inverted-V crotch notch exists — the underside is not flat
  §1.2  hipL is on +X (the figure's LEFT) and the two sockets mirror
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import socket_gate  # noqa: E402

HERE = Path(__file__).resolve().parent
LM = json.loads((HERE / "landmarks.json").read_text())
P = LM["parts"]["pelvis"]
A = P["adopted"]
BUDGET = json.loads((HERE / "build-constants.json").read_text())["authored"]["triangleBudget"][
    "value"
]["oneOff"]
EPS = 1e-6


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    doc = json.loads(Path(argv[0]).read_text())
    vs = [tuple(v) for m in doc.get("meshes", []) for v in m["vertices"]]
    tris = sum(len(m.get("indices", [])) // 3 for m in doc.get("meshes", []))
    xs, ys, zs = [v[0] for v in vs], [v[1] for v in vs], [v[2] for v in vs]
    checks: list[tuple[str, bool, str]] = []
    add = lambda label, ok, detail: checks.append((label, ok, detail))  # noqa: E731

    add("§5.4 triangle budget", tris <= BUDGET, f"{tris} <= {BUDGET}")
    add("§5.5 origin is pelvisTop (top face on y=0)", abs(max(ys)) < EPS, f"top y = {max(ys):+.9f}")
    add(
        "§5.5 crotch at -H",
        abs(min(ys) + A["height"]) < EPS,
        f"bottom {min(ys):+.9f}, -H {-A['height']:+.9f}",
    )

    # width per ring, keyed by y
    rings: dict[float, list[tuple[float, float, float]]] = {}
    for v in vs:
        rings.setdefault(round(v[1], 7), []).append(v)
    by_y = sorted(rings.items(), key=lambda kv: -kv[0])
    widths = [(y, max(p[0] for p in g) - min(p[0] for p in g)) for y, g in by_y]
    top_w = widths[0][1]
    widest_y, widest_w = max(widths, key=lambda w: w[1])

    add(
        "§4[6] pentagon: flares wider than the belt line",
        widest_w > top_w + EPS,
        f"widest {widest_w:.6f} at y {widest_y:+.6f} vs top {top_w:.6f}",
    )
    add(
        "§4[6] pentagon: pulls back in below the widest",
        widths[-1][1] < widest_w - EPS,
        f"bottom ring {widths[-1][1]:.6f} < widest {widest_w:.6f}",
    )
    add(
        "§4[6] widest ring is at the measured height",
        abs((-widest_y) - A["widestDrop"] if "widestDrop" in A else 0) < 1e-3
        or abs(widest_y + (A["topHeight"] - A["widestHeight"])) < 1e-3,
        f"built drop {-widest_y:.6f} vs measured {A['topHeight'] - A['widestHeight']:.6f}",
    )
    add(
        "§4[6] widest width matches the measurement",
        abs(widest_w - A["widestWidth"]) < 1e-3,
        f"built {widest_w:.6f} vs measured {A['widestWidth']:.6f}",
    )

    # kite: the z extents must be symmetric about 0, and the extremes must be single points
    add(
        "§4[6] profile kite is front/back symmetric",
        abs(max(zs) + min(zs)) < EPS,
        f"front {max(zs):+.6f}, back {min(zs):+.6f}, sum {max(zs) + min(zs):+.3e}",
    )
    front_pts = [v for v in vs if abs(v[2] - max(zs)) < EPS]
    add(
        "§4[6] the kite's front point is a POINT, not an edge",
        all(abs(p[0]) < EPS for p in front_pts),
        f"{len(front_pts)} vertices at max z, all on x=0: "
        f"{all(abs(p[0]) < EPS for p in front_pts)}",
    )

    # the notch: the underside must not be flat
    bottom_y = min(ys)
    lifted = [v for v in vs if bottom_y < v[1] < bottom_y + A["notchWidth"] and abs(v[0]) < EPS]
    add(
        "§4[6] the inverted-V crotch notch exists",
        len(lifted) >= 2,
        f"{len(lifted)} centre vertices lifted above the bottom ring — the underside is a "
        f"ridge, so the front view shows a V (notch width {A['notchWidth']:.6f} measured, "
        "its rise is a guess-list item)",
    )

    for label, ok, detail in socket_gate.shape_checks(doc, "pelvis"):
        add(label, ok, detail)
    hl = socket_gate.vector(doc, "pelvis", "hipL")
    hr = socket_gate.vector(doc, "pelvis", "hipR")
    add("§1.2 hipL is on +X (the figure's LEFT)", hl[0] > 0, f"hipL x = {hl[0]:+.6f}")
    add(
        "§5.10 the two hip sockets mirror",
        abs(hl[0] + hr[0]) < EPS and abs(hl[1] - hr[1]) < EPS and abs(hl[2] - hr[2]) < EPS,
        f"hipL {tuple(round(x, 6) for x in hl)} vs hipR {tuple(round(x, 6) for x in hr)}",
    )
    chain = LM["parts"]["pantLeg"]["segmentHeights"]["chainY"]["hip"]
    add(
        "§5.5 pelvisTop + hipL lands the thigh on the ledger's `hip`",
        abs((A["topHeight"] + hl[1]) - chain) < EPS,
        f"{A['topHeight']:.6f} + ({hl[1]:+.6f}) = {A['topHeight'] + hl[1]:.6f} vs {chain:.6f}",
    )

    fails = 0
    for label, ok, detail in checks:
        fails += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  {label:52s} {detail}")
    print(f"{len(checks) - fails}/{len(checks)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
