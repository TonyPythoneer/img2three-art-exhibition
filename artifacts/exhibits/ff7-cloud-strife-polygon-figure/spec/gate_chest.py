#!/usr/bin/env python3
"""prompt.txt §5 — the chest slab's gates (S-08 chestSlab).

    node tools/capture_parts.mjs --part chest --out /tmp/chest
    python3 spec/gate_chest.py /tmp/chest/meshes.json

The chest is the hub of the socket ledger — the only part that emits four
(waistTop, neckBase, shoulderL, shoulderR).  Every later part's assembly
agrees or disagrees here, so its gates matter more than the gates of parts that
merely consume one socket.

  §5.4  triangle count inside the chest's spec budget (slab)
  §5.5  the local origin IS chestTop: top face on y=0, waist at -H
  §4    every socket obeys §4's shape (socket_gate.py): a bare THREE.Vector3
  §4[8] widest ring at the measured widestDrop
  §4[8] pentagon: wider than the top at the widest, narrower than the widest
        at the bottom
  §4[8] shoulder sockets at the chest's TOP face, not at the widest ring —
        see the §5.1 retraction narrative in HANDOFF.md
  §4[8] shoulderL/R offset equals half the slab's widestWidth (per
        measure_chest.py: shoulderOffsetX = widestWidth / 2)

A nonexistent gate_chest.py meant the chest shipped unchecked, and the
shoulder-socket-at-widestDrop defect survived all eleven part gates and 200+
assertions (hand-off: "an IoU of 0.201 in a model nobody had compared to
the reference").  THIS gate is what catches that defect.
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
CHEST = LM["parts"]["chest"]
C = CHEST["adopted"]
CONST = json.loads((HERE / "build-constants.json").read_text())
# Triangle budgets live in build-constants.json — separate document from the
# sculpt spec (it does not store them inline).
BUDGET = json.loads((HERE / "build-constants.json").read_text())["authored"]["triangleBudget"]["value"]["slab"]
RMS = LM["normalization"]["sole->chin"]["measurementUncertaintyRms"]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    doc = json.loads(Path(argv[0]).read_text())
    meshes = doc.get("meshes", [])
    if not meshes:
        print("FAIL  no meshes in capture", file=sys.stderr)
        return 2
    vs = [(v[0], v[1], v[2]) for m in meshes for v in m.get("vertices", [])]
    tris = sum(len(m.get("indices", [])) // 3 for m in meshes)
    ys = [v[1] for v in vs]
    xs = [v[0] for v in vs]
    zs = [v[2] for v in vs]
    checks: list[tuple[str, bool, str]] = []
    add = lambda l, ok, d: checks.append((l, ok, d))  # noqa: E731

    add("§5.4 triangle budget", tris <= BUDGET, f"{tris} <= {BUDGET}")
    add(
        "§5.5 origin is chestTop (top face on y=0)",
        abs(max(ys)) < 1e-6,
        f"top y = {max(ys):+.9f}",
    )
    add(
        "§5.5 the waist mate is at -H",
        abs(min(ys) + C["height"]) < 1e-5,
        f"bottom {min(ys):+.6f}, -H {-C['height']:+.6f}",
    )

    # §4 sockets: shape and the retracted-shoulder-at-top contract.
    for label, ok, detail in socket_gate.shape_checks(doc, "chest"):
        add(label, ok, detail)

    # §4[8] shape: per-ring width, widest at widestHeight inside the slab.
    rings: dict[float, list] = {}
    for v in vs:
        rings.setdefault(round(v[1], 6), []).append(v)
    ring_widths = sorted(
        ((y, max(p[0] for p in g) - min(p[0] for p in g)) for y, g in rings.items()),
        key=lambda t: -t[0],
    )
    if not ring_widths:
        print("FAIL  no rings in capture", file=sys.stderr)
        return 2
    top_w = float(ring_widths[0][1])
    widest_y, widest_w = max(ring_widths, key=lambda t: t[1])
    widest_w = float(widest_w)
    bottom_w = float(ring_widths[-1][1])
    # The measurement's widest height is in absolute figure coords (e.g. 0.599).
    # Convert to chest-local y by subtracting chestTop: local y = -(chestTop_world - widest_world)
    chest_top_y_world = CONST.get("socketChainY", {}).get("chestTop", 0.7062)
    widest_y_world = C["widestHeight"]
    expected_local_y = -(chest_top_y_world - widest_y_world)
    add(
        "§4[8] widest ring at measured widestHeight",
        abs(widest_y - expected_local_y) <= RMS,
        f"widest at local y {widest_y:+.6f}, expected {expected_local_y:+.6f} (RMS {RMS:.5f})",
    )
    add(
        "§4[8] pentagon: widest > top (flares wider than its own collar)",
        widest_w > top_w + 1e-6,
        f"widest {widest_w:.6f} > top {top_w:.6f}",
    )
    add(
        "§4[8] pentagon: bottom < widest (pulls in below the widest)",
        bottom_w < widest_w - 1e-6,
        f"bottom {bottom_w:.6f} < widest {widest_w:.6f}",
    )

    # §4[8] shoulder sockets at the TOP face, not at the widest ring.
    # Direct read from the world position of the captured socket pairs.
    world_y_by_topic: dict[str, float | None] = {}
    for sname in ("shoulderL", "shoulderR", "waistTop", "neckBase"):
        v = socket_gate.vector(doc, "chest", sname)
        world_y_by_topic[sname] = v[1] if v is not None else None
    shoulder_y_min = min(
        (world_y_by_topic[k] for k in ("shoulderL", "shoulderR")
         if world_y_by_topic[k] is not None),
        default=None,
    )
    add(
        "§4[8] shoulder sockets at the chest TOP face (y=0)",
        shoulder_y_min is not None and abs(shoulder_y_min) <= RMS,
        f"min shoulder world y = {shoulder_y_min}, expected 0 (±RMS {RMS:.5f})",
    )

    # §4[8] shoulderL/R offset equals half the slab's widestWidth.
    sw_l = socket_gate.vector(doc, "chest", "shoulderL")
    sw_r = socket_gate.vector(doc, "chest", "shoulderR")
    if sw_l is not None and sw_r is not None:
        shoulder_offset = max(abs(sw_l[0]), abs(sw_r[0]))
        add(
            "§4[8] shoulder offset equals half the slab's widestWidth",
            abs(shoulder_offset - C["widestWidth"] / 2) <= RMS,
            f"measured offset {shoulder_offset:.6f}, widestWidth/2 = {C['widestWidth']/2:.6f}",
        )
        add(
            "§4[8] shoulderL and shoulderR are mirror-symmetric in X",
            abs(abs(sw_l[0]) - abs(sw_r[0])) <= 1e-6,
            f"L x = {sw_l[0]:+.6f}, R x = {sw_r[0]:+.6f}",
        )

    # §4[8] the slab identifies as one mesh (not split into straps at Stage 1).
    add(
        "§4[8] one mesh, no Stage-2/3 straps",
        len(meshes) == 1,
        f"{len(meshes)} mesh(es)",
    )

    fails = 0
    for label, ok, detail in checks:
        fails += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  {label:62s} {detail}")
    print(f"{len(checks) - fails}/{len(checks)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
