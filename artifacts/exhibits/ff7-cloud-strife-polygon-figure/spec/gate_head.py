#!/usr/bin/env python3
"""prompt.txt §5 — the bare skull's gates (S-15), plus §4[14]'s faceGroups contract.

    node tools/capture_parts.mjs --part head --out /tmp/head
    python3 spec/gate_head.py /tmp/head/meshes.json

  §5.4   triangle budget
  §5.5   the origin IS skullTop: top face on y=0, neck mate at -H
  §4     the neckTop socket is a bare THREE.Vector3
  §4[14] widest at the cheekbones, tapering to a small pointed chin
  §4[14] faceGroups partitions the head into five regions — EVERY triangle in exactly one
         array. The factory throws if it does not, so this gate proves the export carries
         the partition rather than that the factory could build one.
  §4[14] NO hair, NO ears, NO eyes: the part is one mesh, and the five regions are index
         arrays rather than separate geometry.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import socket_gate  # noqa: E402

HERE = Path(__file__).resolve().parent
LM = json.loads((HERE / "landmarks.json").read_text())
H = LM["parts"]["head"]["adopted"]
BUD = json.loads((HERE / "build-constants.json").read_text())["authored"]["triangleBudget"]["value"]
EPS = 1e-6


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    doc = json.loads(Path(argv[0]).read_text())
    meshes = doc.get("meshes", [])
    vs = [(v[0], v[1], v[2]) for m in meshes for v in m["vertices"]]
    tris = sum(len(m.get("indices", [])) // 3 for m in meshes)
    ys = [v[1] for v in vs]
    height = LM["parts"]["pantLeg"]["segmentHeights"]["chainY"] and (1.0 - H["chinHeight"])
    checks: list[tuple[str, bool, str]] = []
    add = lambda l, ok, d: checks.append((l, ok, d))  # noqa: E731

    add("§5.4 triangle budget", tris <= BUD["oneOff"], f"{tris} <= {BUD['oneOff']}")
    add("§4[14] one mesh, no hair/ears/eyes", len(meshes) == 1, f"{len(meshes)} mesh(es)")
    add("§5.5 origin is skullTop (top face on y=0)", abs(max(ys)) < EPS, f"top y = {max(ys):+.9f}")
    add(
        "§5.5 the neck mate is at -H",
        abs(min(ys) + height) < 1e-5,
        f"bottom {min(ys):+.6f}, -H {-height:+.6f} (skullTop 1.0 - chin {H['chinHeight']:.6f})",
    )

    # §4[14] the taper: the widest ring must be above the bottom, and the bottom narrower
    rings: dict[float, list] = {}
    for v in vs:
        rings.setdefault(round(v[1], 7), []).append(v)
    widths = {y: max(p[0] for p in g) - min(p[0] for p in g) for y, g in rings.items()}
    wy, ww = max(widths.items(), key=lambda kv: kv[1])
    bottom_w = widths[min(widths)]
    add(
        "§4[14] widest at the cheekbones",
        wy > min(widths) + EPS,
        f"widest ring {ww:.6f} at y {wy:+.6f}, above the chin at {min(widths):+.6f}",
    )
    add(
        "§4[14] tapering to a small pointed chin",
        bottom_w < ww,
        f"chin {bottom_w:.6f} vs cheekbones {ww:.6f}, ratio "
        f"{bottom_w / ww:.4f} (reference measured {H['chinWidth'] / H['cheekboneWidth']:.4f})",
    )

    # `faceGroups` is exported keyed by PART NAME, the same shape `sockets` uses, so a
    # capture of the whole figure carries one entry per part rather than one flat map.
    groups = (doc.get("faceGroups") or {}).get("head") or {}
    if groups:
        flat = [i for g in groups.values() for i in g]
        add(
            "§4[14] faceGroups has the five regions",
            set(groups) == {"scalp", "face", "jaw", "nape", "ear"},
            f"{sorted(groups)}",
        )
        add(
            "§4[14] every triangle in EXACTLY one region",
            len(flat) == tris and len(set(flat)) == tris,
            f"{len(flat)} assigned, {len(set(flat))} distinct, {tris} triangles; "
            + ", ".join(f"{k}={len(v)}" for k, v in sorted(groups.items())),
        )
        empty = [k for k, v in groups.items() if not v]
        add(
            "§4[14] no region is EMPTY",
            not empty,
            "every region carries triangles"
            if not empty
            else f"{empty} are empty — Stage 2's hairCap conforms to `scalp`, faceDecal maps "
            "to `face` and the ears grow from `ear`, so an empty array is a partition that "
            "satisfies the arithmetic and hands the consumer nothing",
        )
    else:
        add(
            "§4[14] faceGroups reaches the capture",
            False,
            "the head factory builds userData.faceGroups and throws unless it partitions, "
            "but the mesh export does not carry it — so Stage 2's hairCap, faceDecal and "
            "ears have nothing to attach to and this gate cannot see the partition. Export "
            "it alongside `sockets`.",
        )

    for label, ok, detail in socket_gate.shape_checks(doc, "head"):
        add(label, ok, detail)

    fails = 0
    for label, ok, detail in checks:
        fails += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  {label:46s} {detail}")
    print(f"{len(checks) - fails}/{len(checks)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
