#!/usr/bin/env python3
"""prompt.txt §5.5 — prove the socket chain in the RENDER, not on paper.

    node tools/capture_parts.mjs --assembled --out /tmp/asm
    python3 spec/gate_assembly.py /tmp/asm/meshes.json

Every other §5.5 assertion so far has been arithmetic: "this part's ledger height plus its
socket equals that part's ledger height". Those are worth having, but they cannot catch the
failure that actually happened — the pair preview never read `userData.sockets` at all,
agreed on Y by arithmetic because ankleTop minus soleTop IS the cuff height, and silently
dropped the fore-aft offset. Two independent copies of one joint, both plausible, and no
paper check could tell them apart.

This one reads the assembled capture's WORLD positions and asserts that each part's frame
sits exactly where its host's socket says. If the viewer ever stops reading sockets again,
this fails; the arithmetic version would not.

It is not a Stage 1B gate. Stage 1B is a real assembly with an integration file; this is
the review view, and the parts it cannot place (no host built yet) are reported as such
rather than skipped.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LM = json.loads((HERE / "landmarks.json").read_text())
EPS = 1e-6

# §4's socket ledger, as (part, origin-name, host-part, socket-name-on-the-host).
# A sided emitter carries the L/R suffix; unsided names mate directly.
LEDGER = [
    ("soleL", "soleTop", "ankleL", "soleTop"),
    ("soleR", "soleTop", "ankleR", "soleTop"),
    ("ankleL", "ankleTop", "calfL", "ankleTop"),
    ("ankleR", "ankleTop", "calfR", "ankleTop"),
    ("calfL", "calfTop", "kneeL", "calfTop"),
    ("calfR", "calfTop", "kneeR", "calfTop"),
    ("kneeL", "kneeTop", "thighL", "kneeTop"),
    ("kneeR", "kneeTop", "thighR", "kneeTop"),
    ("thighL", "hip", "pelvis", "hipL"),
    ("thighR", "hip", "pelvis", "hipR"),
    ("pelvis", "pelvisTop", "waist", "pelvisTop"),
]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    doc = json.loads(Path(argv[0]).read_text())
    world = {m["name"]: m.get("world") for m in doc.get("meshes", [])}
    sockets = doc.get("sockets", {})
    checks: list[tuple[str, bool, str]] = []

    missing_world = [n for n, w in world.items() if w is None]
    checks.append(
        (
            "every part exports its world frame",
            not missing_world,
            "all present" if not missing_world else f"missing on {missing_world} — recapture",
        )
    )

    placed = 0
    for part, _origin, host, socket_name in LEDGER:
        if part not in world or host not in world:
            checks.append(
                (
                    f"§5.5 {part} sits on {host}.{socket_name}",
                    True,
                    f"skipped: {'host ' + host if host not in world else part} not built yet",
                )
            )
            continue
        entry = (sockets.get(host) or {}).get(socket_name)
        if not entry or not entry.get("isVector3"):
            checks.append(
                (
                    f"§5.5 {part} sits on {host}.{socket_name}",
                    False,
                    f"{host} does not export a bare-Vector3 `{socket_name}`",
                )
            )
            continue
        v = entry["value"]
        want = [world[host][i] + v[i] for i in range(3)]
        got = world[part]
        worst = max(abs(want[i] - got[i]) for i in range(3))
        placed += 1
        checks.append(
            (
                f"§5.5 {part} sits on {host}.{socket_name}",
                worst < EPS,
                f"host {tuple(round(x, 6) for x in world[host])} + socket "
                f"{tuple(round(x, 6) for x in v)} -> want "
                f"{tuple(round(x, 6) for x in want)}, got {tuple(round(x, 6) for x in got)}, "
                f"worst |delta| = {worst:.3e}",
            )
        )

    checks.append(
        (
            "the chain is actually exercised",
            placed >= 2,
            f"{placed} of {len(LEDGER)} joints have both ends built. A gate that skips every "
            "joint passes for the wrong reason, so this refuses to be vacuous.",
        )
    )

    # Feet on the ground: the sole's own origin is soleTop, so its bottom face sits at
    # soleTop's ledger height minus the slab thickness, which must be y=0 (§1.1).
    sole_top = LM["parts"]["sole"]["thickness"]["adopted"]
    for side in ("L", "R"):
        name = f"sole{side}"
        if name not in world or world[name] is None:
            continue
        ground = world[name][1] - sole_top
        checks.append(
            (
                f"§1.1 {name} bottom face is on the ground",
                abs(ground) < 5e-3,
                f"soleTop y {world[name][1]:.6f} - thickness {sole_top:.6f} = {ground:+.6f}",
            )
        )

    fails = 0
    for label, ok, detail in checks:
        fails += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  {label:44s} {detail}")
    print(f"{len(checks) - fails}/{len(checks)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
