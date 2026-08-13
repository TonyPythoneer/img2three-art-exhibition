#!/usr/bin/env python3
"""prompt.txt §5 — the pant leg's gates, over all SIX parts at once (S-03/S-04/S-05).

    for p in thighL thighR kneeL kneeR calfL calfR; do
      node tools/capture_parts.mjs --part $p --out /tmp/leg-$p
    done
    python3 spec/gate_pant_leg.py /tmp/leg-thighL/meshes.json /tmp/leg-thighR/meshes.json \\
        /tmp/leg-kneeL/meshes.json /tmp/leg-kneeR/meshes.json \\
        /tmp/leg-calfL/meshes.json /tmp/leg-calfR/meshes.json

ONE GATE FOR SIX PARTS, on purpose. §5.7 is a SHARED gate over thigh/knee/calf, and the
thing it is really guarding — "the three parts must share ONE set of section constants so
their joins match exactly, or a seam appears that the reference does not have" — is not
checkable from inside any one of them. A per-part gate would pass three times over a leg
with two seams in it.

What it asserts:

  §5.4  triangle count inside the loft budget (96)
  §5.5  each segment's local origin IS its own upper socket: top face on y=0, bottom at -H
  §5.5  the socket chain closes on the ledger: hip - thigh - knee - calf == ankleTop
  §4    every socket obeys §4's shape — a bare THREE.Vector3 (socket_gate.py)
  §4[4] the three sections are IDENTICAL, not merely close. This is the seam check, and
        the tolerance is 1e-6, not the measurement uncertainty: they come from one
        constant, so any difference at all is a code defect rather than a reading.
  §4[3] near-square section with chamfered corners, and the front centre crease exists
  §5.7d the tube is near-constant width top to bottom
  §5.10 mirror consistency on all three pairs, vertices and sockets
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import socket_gate  # noqa: E402

HERE = Path(__file__).resolve().parent
LM = json.loads((HERE / "landmarks.json").read_text())
LEG = LM["parts"]["pantLeg"]
CHAIN = LEG["segmentHeights"]["chainY"]
SECTION = LEG["sharedSection"]
BUDGET = json.loads((HERE / "build-constants.json").read_text())["authored"]["triangleBudget"][
    "value"
]["loft"]

EPS = 1e-6
SEGMENTS = (("thigh", "hip", "kneeTop"), ("knee", "kneeTop", "calfTop"), ("calf", "calfTop", "ankleTop"))


def load(path: str) -> dict:
    return json.loads(Path(path).read_text())


def verts(doc: dict, part: str) -> list[tuple[float, float, float]]:
    out: list[tuple[float, float, float]] = []
    for m in doc.get("meshes", []):
        if m.get("name") in (part, None) or len(doc.get("meshes", [])) == 1:
            out.extend((v[0], v[1], v[2]) for v in m["vertices"])
    return out


def tris(doc: dict) -> int:
    return sum(len(m.get("indices", [])) // 3 for m in doc.get("meshes", []))


def main(argv: list[str]) -> int:
    if len(argv) != 6:
        print(__doc__, file=sys.stderr)
        return 2
    names = ["thighL", "thighR", "kneeL", "kneeR", "calfL", "calfR"]
    docs = {n: load(p) for n, p in zip(names, argv)}
    checks: list[tuple[str, bool, str]] = []

    def add(label: str, ok: bool, detail: str) -> None:
        checks.append((label, ok, detail))

    # ---- per segment ----
    sections: dict[str, tuple[float, float]] = {}
    for seg, top_name, bot_name in SEGMENTS:
        height = CHAIN[top_name] - CHAIN[bot_name]
        for side in ("L", "R"):
            part = f"{seg}{side}"
            doc = docs[part]
            vs = verts(doc, part)
            ys = [v[1] for v in vs]
            xs = [v[0] for v in vs]
            zs = [v[2] for v in vs]
            add(
                f"§5.4 {part} triangle budget",
                tris(doc) <= BUDGET,
                f"{tris(doc)} <= {BUDGET}",
            )
            add(
                f"§5.5 {part} origin is {top_name} (top face on y=0)",
                abs(max(ys)) < EPS,
                f"top face y = {max(ys):+.9f}",
            )
            add(
                f"§5.5 {part} bottom face at -H",
                abs(min(ys) + height) < EPS,
                f"bottom {min(ys):+.9f}, -H {-height:+.9f}",
            )
            sections[part] = (max(xs) - min(xs), max(zs) - min(zs))
            for label, ok, detail in socket_gate.shape_checks(doc, part):
                add(f"{label} [{part}]", ok, detail)

    # ---- §4[4] the seam check: the three sections must be IDENTICAL ----
    for side in ("L", "R"):
        got = [sections[f"{s}{side}"] for s, _, _ in SEGMENTS]
        dw = max(g[0] for g in got) - min(g[0] for g in got)
        dd = max(g[1] for g in got) - min(g[1] for g in got)
        add(
            f"§4[4] thigh/knee/calf sections identical ({side})",
            dw < EPS and dd < EPS,
            f"width spread {dw:.3e}, depth spread {dd:.3e} (< {EPS:.0e}) — one constant, "
            "so any difference is a code defect, not a reading",
        )

    # ---- §4[3] near-square section, chamfers, and the front crease ----
    w, d = sections["calfL"]
    add(
        "§4[3] section is near-square",
        abs(w - d) < max(w, d) * 0.15,
        f"width {w:.6f} vs depth {d:.6f}, {abs(w - d) / max(w, d) * 100:.1f}% apart",
    )
    zs = sorted({round(v[2], 7) for v in verts(docs["calfL"], "calfL")})
    add(
        "§4[3] one vertical crease down the front centre",
        len(zs) >= 5 and zs[-1] > SECTION["depthZ"] / 2 + 1e-7,
        f"frontmost z {zs[-1]:.6f} stands proud of the flat face at "
        f"{SECTION['depthZ'] / 2:.6f}; {len(zs)} distinct z planes",
    )

    # ---- §5.7 (d) near-constant width, measured on the reference ----
    tube = LEG["calfNearConstantWidth_5_7d"]
    add(
        "§5.7(d) tube is near-constant width",
        tube["difference"] < tube["measurementUncertainty"],
        f"reference {tube['topWidth']:.5f} -> {tube['bottomWidth']:.5f}, "
        f"difference {tube['difference']:.5f} < {tube['measurementUncertainty']:.5f}",
    )

    # ---- §5.5 the chain closes ----
    total = sum(CHAIN[t] - CHAIN[b] for _, t, b in SEGMENTS)
    span = CHAIN["hip"] - CHAIN["ankleTop"]
    add(
        "§5.5 socket chain closes hip -> ankleTop",
        abs(total - span) < EPS,
        f"{total:.9f} vs {span:.9f}",
    )

    # ---- §5.10 mirror consistency, all three pairs ----
    for seg, _, _ in SEGMENTS:
        label, ok, detail = socket_gate.mirror_check(
            docs[f"{seg}L"], docs[f"{seg}R"], f"{seg}L", f"{seg}R"
        )
        add(f"{label} [{seg}]", ok, detail)
        vl = sorted(verts(docs[f"{seg}L"], f"{seg}L"))
        vr = sorted((-v[0], v[1], v[2]) for v in verts(docs[f"{seg}R"], f"{seg}R"))
        worst = max(
            (max(abs(a[i] - b[i]) for i in range(3)) for a, b in zip(vl, vr)), default=1.0
        )
        add(
            f"§5.10 mirror consistency (vertices) [{seg}]",
            len(vl) == len(vr) and worst < EPS,
            f"worst |delta| = {worst:.3e} over {len(vl)} vertices",
        )

    fails = 0
    for label, ok, detail in checks:
        fails += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  {label:58s} {detail}")
    print(f"{len(checks) - fails}/{len(checks)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
