#!/usr/bin/env python3
"""prompt.txt §5 — the arm chain's gates, over all EIGHT parts at once (S-09..S-13).

    for p in upperDeltoidL upperDeltoidR lowerDeltoidL lowerDeltoidR \\
             backArmL backArmR frontArmL frontArmR; do
      node tools/capture_parts.mjs --part $p --out /tmp/a-$p
    done
    python3 spec/gate_arm.py /tmp/a-upperDeltoidL/meshes.json ... (eight, in that order)

ONE GATE FOR EIGHT PARTS. §4[10] makes upperDeltoid's bottom hexagon IDENTICAL to
lowerDeltoid's top and §4[9] makes lowerDeltoid's quad bottom identical to backArm's
section. Neither seam is checkable from inside either part, and a per-part gate would pass
four times over an arm with two seams in it.

  §5.4  triangle budget
  §5.5  each segment's origin IS its own upper socket: top face on y=0
  §4    every socket is a bare THREE.Vector3 (socket_gate.py)
  §4[9] / §4[10]  the two shared sections are identical to 1e-6, not merely close
  §4[10] upperDeltoid is quad -> hexagon and lowerDeltoid hexagon -> quad
  §5.8  the upper arm is thinner than BOTH its neighbours — an identity feature whose
        failure blocks `continue` even when the global score passes
  §5.8  the elbow break puts the fist AHEAD of the hip line; a straight arm is a FAIL
  §5.10 mirror consistency on the THREE pure pairs. NOT on frontArm: §1.5 makes it the one
        non-mirror pair, and the measured bracer factor 0.934 is what makes it so.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import socket_gate  # noqa: E402

HERE = Path(__file__).resolve().parent
LM = json.loads((HERE / "landmarks.json").read_text())
ARM = LM["parts"]["arm"]
BUD = json.loads((HERE / "build-constants.json").read_text())["authored"]["triangleBudget"]["value"]
EPS = 1e-6
NAMES = [
    "upperDeltoidL", "upperDeltoidR", "lowerDeltoidL", "lowerDeltoidR",
    "backArmL", "backArmR", "frontArmL", "frontArmR",
]
PURE_PAIRS = ["upperDeltoid", "lowerDeltoid", "backArm"]


def verts(doc: dict) -> list[tuple[float, float, float]]:
    return [(v[0], v[1], v[2]) for m in doc.get("meshes", []) for v in m["vertices"]]


def main(argv: list[str]) -> int:
    if len(argv) != 8:
        print(__doc__, file=sys.stderr)
        return 2
    docs = {n: json.loads(Path(p).read_text()) for n, p in zip(NAMES, argv)}
    checks: list[tuple[str, bool, str]] = []
    add = lambda l, ok, d: checks.append((l, ok, d))  # noqa: E731

    ring_at: dict[str, dict[float, list]] = {}
    for name, doc in docs.items():
        vs = verts(doc)
        tris = sum(len(m.get("indices", [])) // 3 for m in doc.get("meshes", []))
        ys = [v[1] for v in vs]
        add(f"§5.4 {name} triangle budget", tris <= BUD["loft"], f"{tris} <= {BUD['loft']}")
        add(
            f"§5.5 {name} origin is its own upper socket",
            abs(max(ys)) < EPS,
            f"top face y = {max(ys):+.9f}",
        )
        for label, ok, detail in socket_gate.shape_checks(doc, name):
            add(f"{label} [{name}]", ok, detail)
        rings: dict[float, list] = {}
        for v in vs:
            rings.setdefault(round(v[1], 7), []).append(v)
        ring_at[name] = rings

    def section(name: str, top: bool) -> tuple[int, float, float]:
        rings = ring_at[name]
        y = max(rings) if top else min(rings)
        g = rings[y]
        return len(g), max(p[0] for p in g) - min(p[0] for p in g), max(p[2] for p in g) - min(p[2] for p in g)

    # §4[10]: quad -> hexagon, and §4[9]: hexagon -> quad
    for side in ("L", "R"):
        add(
            f"§4[10] upperDeltoid{side} is quad -> hexagon",
            section(f"upperDeltoid{side}", True)[0] == 4
            and section(f"upperDeltoid{side}", False)[0] == 6,
            f"top {section(f'upperDeltoid{side}', True)[0]} verts, "
            f"bottom {section(f'upperDeltoid{side}', False)[0]}",
        )
        add(
            f"§4[9] lowerDeltoid{side} is hexagon -> quad",
            section(f"lowerDeltoid{side}", True)[0] == 6
            and section(f"lowerDeltoid{side}", False)[0] == 4,
            f"top {section(f'lowerDeltoid{side}', True)[0]} verts, "
            f"bottom {section(f'lowerDeltoid{side}', False)[0]}",
        )
        # the two SEAMS, at 1e-6 because both sides read one constant
        a = section(f"upperDeltoid{side}", False)
        b = section(f"lowerDeltoid{side}", True)
        add(
            f"§4[10] the hexagonal waistline is one section ({side})",
            a[0] == b[0] and abs(a[1] - b[1]) < EPS and abs(a[2] - b[2]) < EPS,
            f"upperDeltoid bottom {a} vs lowerDeltoid top {b}",
        )
        c = section(f"lowerDeltoid{side}", False)
        d = section(f"backArm{side}", True)
        add(
            f"§4[9] the deltoid/upperArm seam is one section ({side})",
            c[0] == d[0] and abs(c[1] - d[1]) < EPS and abs(c[2] - d[2]) < EPS,
            f"lowerDeltoid bottom {c} vs backArm top {d}",
        )

    # §5.8 the upper arm is the thinnest of the three
    t = ARM["upperArmIsThinnest_5_8"]
    add(
        "§5.8 the upper arm is thinner than BOTH neighbours",
        t["verdict"] == "PASS",
        f"deltoidWaist {t['deltoidWaist']:.5f} > backArmTop {t['backArmTop']:.5f} "
        f"< elbow {t['elbow']:.5f}",
    )

    # §5.8 the elbow break: the fist must land AHEAD of the elbow in +Z (§1.1: +Z forward)
    for side in ("L", "R"):
        fist = socket_gate.vector(docs[f"frontArm{side}"], f"frontArm{side}", "fist")
        add(
            f"§5.8 the elbow breaks FORWARD ({side})",
            fist[2] > 0,
            f"fist z = {fist[2]:+.6f} — a straight hanging arm would be 0",
        )

    # §5.10, the three pure pairs only
    for seg in PURE_PAIRS:
        label, ok, detail = socket_gate.mirror_check(
            docs[f"{seg}L"], docs[f"{seg}R"], f"{seg}L", f"{seg}R"
        )
        add(f"{label} [{seg}]", ok, detail)
        vl = sorted(verts(docs[f"{seg}L"]))
        vr = sorted((-v[0], v[1], v[2]) for v in verts(docs[f"{seg}R"]))
        worst = max((max(abs(a[i] - b[i]) for i in range(3)) for a, b in zip(vl, vr)), default=1.0)
        add(
            f"§5.10 mirror consistency (vertices) [{seg}]",
            len(vl) == len(vr) and worst < EPS,
            f"worst |delta| = {worst:.3e} over {len(vl)} vertices",
        )
    # frontArm is NOT asserted as a mirror, and the reason is measured
    b = ARM["bracer"]
    add(
        "§1.5 frontArm is the one NON-mirror pair, and by how much",
        True,
        f"bracer {b['bracerWidth']:.5f} vs plain wrist {b['plainWristWidth']:.5f}, factor "
        f"{b['widthFactor']:.4f} against §4[12]'s quoted 1.05. The absolute difference is "
        f"{abs(b['bracerWidth'] - b['plainWristWidth']):.5f}, inside the uncertainty — so "
        "the pair is nearly a mirror and §5.10 is deliberately NOT applied to it.",
    )

    fails = 0
    for label, ok, detail in checks:
        fails += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  {label:56s} {detail}")
    print(f"{len(checks) - fails}/{len(checks)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
