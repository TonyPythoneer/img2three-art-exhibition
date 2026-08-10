#!/bin/zsh
# The stone alone, from six angles — the evidence that its apex is ONE point over the rhombus's
# centre and not a ridge.
#
# The shape was directed on 2026-08-09 as a 四角錐: four triangular flanks and a seated base. From
# the front that is nearly indistinguishable from the girdled, banded solid it replaces — both
# show a rhombus with a line down the middle — so the front view cannot settle it and neither can
# the artwork crop, which is 5–13 pixels across here. The SIDE can: a ridge reads as a long flat
# top, a pyramid as a triangle peaking at the middle of the stone's own height.
#
# Everything the stone hides behind is hidden: both films, the shell, and the two jaws that cradle
# its lower half. **The four drivers go too, and not because they occlude anything** — they are
# the only other RED thing on the weapon, and `zoom_gem_pyramid.py` finds the stone by looking for
# red. Left in, they stretch its crop box across the whole guard fan and every panel comes out
# 5× too wide.
#
# The two arms and their spinner caps go as well, and that one IS occlusion: from the side an arm
# is a 16-radius cylinder projecting straight onto the stone's lower half, so the first cut of
# this sheet had the bottom third of every side panel behind a grey block. The grip column and
# the pommel stay — they are entirely below `Y = 13`, so they hide nothing, and they keep enough
# pixels in frame for `capture_ultima`'s blank-canvas guard (>40 of a 64×128 probe).
#
# `spec/measure_gem_facets.mjs` is the numeric half of the same claim — how flat each flank
# actually is, off the built mesh. Run both after a geometry change.
set -e
set -o pipefail
cd "$(dirname "$0")/../../../.."
OUT=artifacts/ultima-v2/gem-pyramid
HIDE=purpleEnergyInsertFront,purpleEnergyInsertRear,darkCoreTriangleFront,darkCoreTriangleRear
HIDE=$HIDE,outerCrystalShell,crystalClampLeft,crystalClampRight
HIDE=$HIDE,driverLeftUpper,driverRightUpper,driverLeftLower,driverRightLower
HIDE=$HIDE,leatherConnectorLeft,leatherConnectorRight,spinnerEndLeft,spinnerEndRight

# One view per invocation, each retried, and both halves of that are load-bearing. Playwright
# drops "Execution context was destroyed" on roughly one view in nine here — always a view that
# re-enters the page after a hide-set is already applied — and with all six in one invocation
# `set -e` turned that into an aborted run that left ONE fresh frame beside five from the previous
# geometry. `zoom_gem_pyramid.py` then laid the six out as though they were one build, which is a
# worse failure than no sheet at all: a mixed sheet is not loud, it is just wrong. Same defect and
# same fix as `capture_visibility.sh`'s.
ATTEMPTS=3
for view in front-orthographic left-side-thickness right-side-thickness \
            assembled-three-quarter rear-three-quarter closeup-crystal-clamp; do
  attempt=1
  until node tools/capture_ultima.mjs --route ultima-v2-harness --out "$OUT" --detail full \
          --hide "$HIDE" --views "$view" | tail -1
  do
    if (( attempt >= ATTEMPTS )); then
      echo "capture_gem_pyramid: $view failed $ATTEMPTS times — stopping so the sheet cannot be" >&2
      echo "  built from a mix of this geometry and the last one" >&2
      exit 1
    fi
    echo "capture_gem_pyramid: $view attempt $attempt failed, retrying" >&2
    attempt=$(( attempt + 1 ))
  done
done
