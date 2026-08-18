#!/usr/bin/env bash
# Regenerate the reference crops this build was read from. The crops themselves are NOT
# tracked (project rule: artifacts/ keeps measurements and the scripts that make them,
# never reproducible images). Everything lands in $OUT, default /tmp/sigma-crops.
set -euo pipefail
cd "$(dirname "$0")/.."
SHEET=references/sigma-wireframe-sheet.png
OUT=${OUT:-/tmp/sigma-crops}
mkdir -p "$OUT"

crop() { # x y w h zoom name
  python3 - "$SHEET" "$OUT/$6.png" "$1" "$2" "$3" "$4" "$5" <<'PY'
import sys
from PIL import Image
src, out, x, y, w, h, z = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:8])
im = Image.open(src).convert("RGB").crop((x, y, x + w, y + h))
im.resize((w * z, h * z), Image.Resampling.NEAREST).save(out)
print(out, "->", (w * z, h * z))
PY
}

# The geometry authority: the most row-symmetric target frame (front-frame.json).
crop 61 1809 51 73 14 front-geometry-authority
# The colour authority: the green palette frame (p0-triage.json.greenFrame).
crop 494 2571 52 73 14 green-colour-authority
# The palette strip — four frames, identical geometry, four palettes.
crop 380 2560 230 84 5 palette-strip
# The only direct depth evidence: crown-from-above ovoids (guess list G1).
crop 60 1495 220 80 7 crown-from-above
