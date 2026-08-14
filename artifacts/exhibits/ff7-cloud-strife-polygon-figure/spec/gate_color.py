#!/usr/bin/env python3
"""prompt.txt §2's colour table, Stage 3 — did the right C-xx code land on the right part.

    python3 gate_color.py <meshes.json>

This is a WIRING gate, not a photometric one. It compares each mesh's exported
`material.color` (the material's own authored hex, read straight off
`THREE.Color.getHexString()` in mountCloudStrifeViewer.ts — never a rendered pixel) against
spec/palette.json's ADOPTED hex for the C-xx code prompt.txt §2's group table assigns that
part. It answers "does createChest.ts actually use C-03", not "does the chest look purple
under the showcase lookdev lights" — the second question is lighting/tone-mapping, a Stage
5 concern, and sampling rendered PIXELS against palette.json would conflate the two: this
scene's referenceLighting rig (built for the Ultima Weapon prop, reused here) renders every
material at roughly half its authored brightness regardless of hue, uniformly, so a
pixel-vs-hex ΔE gate would fail every part identically and prove nothing about wiring.

Multi-band parts (frontArm's forearm/wrist/glove — §4[12]) export `material.color` as a
comma-joined list, one hex per band in ring order; PART_COLOR_CODES lists the same order.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PALETTE = json.loads((HERE / "palette.json").read_text())
CODES = PALETTE["codes"]

# prompt.txt §2's group table, reduced to "which C-xx code(s) this part's mesh should
# carry, in band order". Parts absent here (hair/ears/faceDecal/pauldron/straps) are not
# built yet — Stage 2/unscheduled — and are deliberately not asserted on.
PART_COLOR_CODES: dict[str, list[str]] = {
    "soleL": ["C-05b"], "soleR": ["C-05b"],
    "ankleL": ["C-05b"], "ankleR": ["C-05b"],
    "thighL": ["C-04"], "thighR": ["C-04"],
    "kneeL": ["C-04"], "kneeR": ["C-04"],
    "calfL": ["C-04"], "calfR": ["C-04"],
    "pelvis": ["C-04"],
    "waist": ["C-05"],
    "chest": ["C-03"],
    "upperDeltoidL": ["C-01"], "upperDeltoidR": ["C-01"],
    "lowerDeltoidL": ["C-01"], "lowerDeltoidR": ["C-01"],
    "backArmL": ["C-01"], "backArmR": ["C-01"],
    # forearm / wrist / glove. The figure's LEFT wrist is the grey bracer (§4[12]); the
    # right wrist is "the same prism in skin".
    "frontArmL": ["C-01", "C-08", "C-07"],
    "frontArmR": ["C-01", "C-01", "C-07"],
    "neck": ["C-01"],
    "head": ["C-01"],
}


def load_meshes(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        meshes = payload.get("meshes") or payload.get("components")
        if isinstance(meshes, dict):
            return [dict(v, name=k) for k, v in meshes.items()]
        if isinstance(meshes, list):
            return meshes
        return [payload]
    return payload


def check(path: Path) -> int:
    by_name: dict[str, dict] = {}
    for mesh in load_meshes(path):
        by_name.setdefault(mesh.get("name", "<unnamed>"), mesh)

    failures = 0
    checked = 0
    for part, codes in PART_COLOR_CODES.items():
        mesh = by_name.get(part)
        why = []
        if mesh is None:
            why.append("no mesh in the capture (stale meshes.json — recapture)")
            got: list[str] = []
        else:
            color = (mesh.get("material") or {}).get("color", "none")
            got = [c.strip().upper() for c in color.split(",")] if color != "none" else []
            want = []
            for code in codes:
                adopted = CODES.get(code, {}).get("adopted")
                if adopted is None:
                    why.append(f"{code} has no adopted value in palette.json")
                    want.append(None)
                else:
                    want.append(adopted.upper())
            if len(got) != len(want):
                why.append(f"{len(got)} colour band(s) exported, {len(want)} expected ({','.join(codes)})")
            else:
                for i, (g, w) in enumerate(zip(got, want)):
                    if w is not None and g != w:
                        why.append(f"band {i} ({codes[i]}) got {g}, want {w}")
        checked += 1
        failures += 0 if not why else 1
        print(
            f"{'PASS' if not why else 'FAIL'} {part:16s} codes={','.join(codes):18s} "
            f"got={','.join(got) if got else '(none)'}"
            + (f"  <- {'; '.join(why)}" if why else "")
        )
    print(f"{checked - failures}/{checked} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(check(Path(sys.argv[1])))
