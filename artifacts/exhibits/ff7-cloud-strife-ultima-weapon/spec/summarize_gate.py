"""Print one line per deterministic gate report.

`diagnose_render.py --json` prints a STATUS banner before its JSON, so the payload has to be
sliced off the first brace rather than parsed straight from the file.
"""

import json
import sys
from pathlib import Path

for path in sys.argv[1:]:
    raw = Path(path).read_text()
    data = json.loads(raw[raw.index("{") :])
    checks = data.get("checks", {})
    print(
        f"{data.get('passId', Path(path).stem):<18} passed={data.get('passed')} "
        f"IoU={checks.get('silhouetteIoU')} aspect={checks.get('aspectRatioDelta')} "
        f"scale={checks.get('scaleDelta')} failures={data.get('failures')}"
    )
