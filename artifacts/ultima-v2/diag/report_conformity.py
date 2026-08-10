"""Print the harness's stackConformity block in normalized units.

Diagnosis only — the gate with teeth is `spec/check_centerline.py`. Reads whatever parts.json
it is pointed at, so a before/after pair is two runs of this against two capture folders.
"""

import json
import sys
from pathlib import Path

U = 0.01


def main() -> None:
    for path in sys.argv[1:]:
        data = json.loads(Path(path).read_text())
        print(f"=== {path}")
        conform = data.get("stackConformity")
        pen = data.get("shellPenetration")
        if conform:
            print(
                f"{'layer':24} {'face':5} {'n':>5} {'min':>9} {'max':>9} "
                f"{'mean':>9} {'rms':>8}  worst at"
            )
            for name, entry in conform["layers"].items():
                for face in ("seat", "outer"):
                    e = entry[face]
                    lo, hi = e["minAt"], e["maxAt"]
                    print(
                        f"{name:24} {face:5} {e['samples']:5d} {e['min'] / U:9.4f} "
                        f"{e['max'] / U:9.4f} {e['mean'] / U:9.4f} {e['rms'] / U:8.4f}  "
                        f"min@({lo[0] / U:7.1f},{lo[1] / U:7.1f},{lo[2] / U:7.2f}) "
                        f"max@({hi[0] / U:7.1f},{hi[1] / U:7.1f},{hi[2] / U:7.2f})"
                    )
        if pen:
            print("--- one-sided penetration probe (max only)")
            for name, entry in sorted(pen["parts"].items()):
                if not name.startswith(("purple", "darkCore", "rootDiamond")):
                    continue
                print(
                    f"{name:24} shell {entry['shell']['worst'] / U:8.4f}   "
                    f"stack {entry['stack']['worst'] / U:8.4f}"
                )
        print()


if __name__ == "__main__":
    main()
