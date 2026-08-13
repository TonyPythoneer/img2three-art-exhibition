#!/usr/bin/env python3
"""prompt.txt §4 — the socket CONTRACT, checked mechanically. Shared by every part gate.

§4 fixes exactly one shape:

    group.userData.sockets = { <name>: THREE.Vector3 }   // in the part's local frame

and §1.4 is why the shape is not negotiable: the pose is baked into the vertices, so a
per-socket rotation is not extra information, it is a SECOND copy of the pose that can
disagree with the baked one without anything noticing. The first ankle shipped
`{ soleTop: { localPosition, localRotation } }` and every gate stayed green, because no
gate looked at the sockets at all. At two parts that is cosmetic; at fourteen it is a
defect surface, and by then the shape is load-bearing in whatever read `.localPosition`.

So this module is the gate that blocks the thing actually feared: it fails when a socket
value is anything other than a bare three-component vector. Import it from a part's gate:

    import socket_gate
    RESULTS += socket_gate.shape_checks(doc, "ankleL")
    z = socket_gate.vector(doc, "ankleL", "soleTop")[2]

`doc` is the parsed `meshes.json` written by `tools/capture_parts.mjs`, which carries a
`sockets` block alongside `meshes` — the SAME build the renders were taken of. A file
without that block is a stale capture, and that is reported as a failure rather than
skipped: a socket gate that silently passes when it cannot see the sockets is worse than
no gate.

Pure stdlib.
"""
from __future__ import annotations

import math
from typing import Any

Check = tuple[str, bool, str]


def _block(doc: Any, part: str) -> tuple[dict | None, Check | None]:
    """The part's socket map, or the check that explains why there isn't one."""
    if not isinstance(doc, dict) or "sockets" not in doc:
        return None, (
            "§4 socket export present",
            False,
            "meshes.json carries no `sockets` block — stale capture, re-run capture_parts.mjs",
        )
    sockets = doc["sockets"]
    if part not in sockets:
        return None, (
            "§4 socket export present",
            False,
            f"no socket map exported for `{part}`; exported: {sorted(sockets) or 'none'}",
        )
    return sockets[part], None


def shape_checks(doc: Any, part: str) -> list[Check]:
    """One check per socket: is the value a bare Vector3, and is it finite?

    A part that legitimately emits nothing (the sole — it is the bottom of the chain and
    its own origin is its only mating point) still has to declare `sockets = {}`, so an
    empty map is a PASS and a MISSING map is a FAIL.
    """
    block, failure = _block(doc, part)
    if failure is not None:
        return [failure]
    assert block is not None
    results: list[Check] = [
        ("§4 socket export present", True, f"`{part}` exports {len(block)} socket(s)")
    ]
    if not block:
        results.append(("§4 socket shape", True, "emits nothing (empty map, per the ledger)"))
        return results
    for name in sorted(block):
        entry = block[name]
        ok = isinstance(entry, dict) and entry.get("isVector3") is True
        value = entry.get("value") if isinstance(entry, dict) else None
        if ok:
            ok = (
                isinstance(value, list)
                and len(value) == 3
                and all(isinstance(c, (int, float)) and math.isfinite(c) for c in value)
            )
        if ok:
            detail = f"Vector3({value[0]:+.6f}, {value[1]:+.6f}, {value[2]:+.6f})"
        else:
            actual = entry.get("actual") if isinstance(entry, dict) else repr(entry)
            detail = f"not a bare THREE.Vector3 — got {actual}"
        results.append((f"§4 socket `{name}` is a bare Vector3", ok, detail))
    return results


def vector(doc: Any, part: str, name: str) -> tuple[float, float, float]:
    """The socket as three floats. Raises unless it passed `shape_checks`."""
    block, failure = _block(doc, part)
    if failure is not None:
        raise SystemExit(failure[2])
    assert block is not None
    if name not in block:
        raise SystemExit(f"`{part}` emits no socket named `{name}`; has {sorted(block)}")
    entry = block[name]
    if not (isinstance(entry, dict) and entry.get("isVector3") is True):
        raise SystemExit(f"`{part}`.{name} is not a bare THREE.Vector3")
    x, y, z = entry["value"]
    return float(x), float(y), float(z)


def mirror_check(doc_l: Any, doc_r: Any, part_l: str, part_r: str) -> Check:
    """§5.10's 'compare the sockets too': negate the R side's x and the maps must match."""
    block_l, fail_l = _block(doc_l, part_l)
    block_r, fail_r = _block(doc_r, part_r)
    for failure in (fail_l, fail_r):
        if failure is not None:
            return ("§5.10 mirror consistency (sockets)", False, failure[2])
    assert block_l is not None and block_r is not None
    if sorted(block_l) != sorted(block_r):
        return (
            "§5.10 mirror consistency (sockets)",
            False,
            f"socket names differ: {sorted(block_l)} vs {sorted(block_r)}",
        )
    if not block_l:
        return ("§5.10 mirror consistency (sockets)", True, "both emit nothing")
    worst = 0.0
    for name in sorted(block_l):
        # Report, do not raise: a mirror check that dies on a malformed socket takes the
        # whole PASS/FAIL table with it, and the table is the deliverable.
        pair = [block_l[name], block_r[name]]
        if any(not (isinstance(e, dict) and e.get("isVector3") is True) for e in pair):
            return (
                "§5.10 mirror consistency (sockets)",
                False,
                f"`{name}` is not a bare Vector3 on both sides — nothing to compare",
            )
        (lx, ly, lz), (rx, ry, rz) = (e["value"] for e in pair)
        worst = max(worst, math.dist((lx, ly, lz), (-rx, ry, rz)))
    return (
        "§5.10 mirror consistency (sockets)",
        worst < 1e-6,
        f"worst |delta| over {len(block_l)} socket(s) = {worst:.3e} < 1e-06",
    )
