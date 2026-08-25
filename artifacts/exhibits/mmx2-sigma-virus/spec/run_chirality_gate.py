#!/usr/bin/env python3
"""Run the img2threejs 1.5.1 sagittal chirality check for Sigma lateral pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SKILL = Path.home() / ".claude" / "skills" / "img2threejs"
sys.path.insert(0, str(SKILL / "forge" / "_shared"))
from chirality import check_pair, mirror_point  # noqa: E402

HERE = Path(__file__).resolve().parent
SPEC = HERE / "object-sculpt-spec.json"
OUT = HERE / "gates" / "chirality-1.5.1-final.json"

spec = json.loads(SPEC.read_text(encoding="utf-8"))
by_id = {item["id"]: item for item in spec["componentTree"]}
pairs = [("templeShellR", "templeShellL"), ("cheekShellR", "cheekShellL"),
         ("eyePlateR", "eyePlateL"), ("chinTabR", "chinTabL")]
results = []
for right_id, left_id in pairs:
    right = by_id[right_id]["transform"]["position"]
    left = by_id[left_id]["transform"]["position"]
    ok, message = check_pair(right_id.removesuffix("R"), right, left)
    results.append({
        "right": right_id,
        "left": left_id,
        "rightPosition": right,
        "leftPosition": left,
        "expectedLeft": list(mirror_point(right)),
        "passed": ok,
        "message": message,
    })
report = {
    "schemaVersion": 1,
    "kind": "img2threejs.chirality-gate",
    "coordinateFrame": "lateral X, up Y, forward Z; character-left is +X",
    "pairs": results,
    "passed": all(item["passed"] for item in results),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": report["passed"], "pairs": len(results), "out": str(OUT)}, indent=2))
raise SystemExit(0 if report["passed"] else 1)
