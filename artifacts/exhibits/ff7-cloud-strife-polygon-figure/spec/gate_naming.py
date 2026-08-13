#!/usr/bin/env python3
"""prompt.txt §5.6 — the NAMING assertion, read out of partInspector itself.

    node tools/capture_parts.mjs --assembled --out /tmp/asm
    python3 spec/gate_naming.py /tmp/asm/parts.json

§5.6: "group.name matches §2's table exactly, and the part/group attribution that
partInspector DERIVES matches the table — build the part, run createPartInspector over it,
and compare PartInfo.name, PartInfo.module and PartInfo.kind against §2. Wrong names mean
explode and isolate are silently broken."

So this reads the capture's `parts` block, which IS partInspector's own output, and
compares it against §2's table transcribed below. Comparing the factories' `group.name`
against the same table would prove nothing: §1.6 makes the OBJECT TREE the part table, and
what can drift is the attribution partInspector derives from it, not the string a factory
sets.
"""
import json
import sys
from pathlib import Path

# §2's Stage 1 rows: name -> module.
TABLE = {
    "head": "head", "neck": "head",
    "upperDeltoidL": "armLeft", "lowerDeltoidL": "armLeft",
    "backArmL": "armLeft", "frontArmL": "armLeft",
    "upperDeltoidR": "armRight", "lowerDeltoidR": "armRight",
    "backArmR": "armRight", "frontArmR": "armRight",
    "chest": "torso", "waist": "torso", "pelvis": "torso",
    "thighL": "legLeft", "kneeL": "legLeft", "calfL": "legLeft",
    "ankleL": "legLeft", "soleL": "legLeft",
    "thighR": "legRight", "kneeR": "legRight", "calfR": "legRight",
    "ankleR": "legRight", "soleR": "legRight",
}


def main(argv):
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    doc = json.loads(Path(argv[0]).read_text())
    seen = {p["name"]: p for p in doc.get("parts", [])}
    checks = []
    checks.append((
        "§2 all 23 Stage 1 parts are present",
        set(seen) == set(TABLE),
        f"{len(seen)} of {len(TABLE)}; missing {sorted(set(TABLE) - set(seen))}, "
        f"extra {sorted(set(seen) - set(TABLE))}",
    ))
    for name, module in sorted(TABLE.items()):
        p = seen.get(name)
        if not p:
            checks.append((f"§5.6 {name}", False, "partInspector does not report it"))
            continue
        checks.append((
            f"§5.6 {name} module + kind",
            p.get("module") == module and p.get("kind") != "detail",
            f"module {p.get('module')!r} (table says {module!r}), kind {p.get('kind')!r}",
        ))
    fails = 0
    for label, ok, detail in checks:
        fails += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}  {label:34s} {detail}")
    print(f"{len(checks) - fails}/{len(checks)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
