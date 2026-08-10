#!/bin/zsh
# The render set `measure_relief_visibility.py` consumes, front and rear. Two questions, and the
# hide-sets that answer each of them differentially:
#
#   "is the layer proud of the SHELL"        base / <layer>Only / <layer>Shell
#   "is the diamond proud of the LAYER
#    DIRECTLY UNDER IT"                      gemOnly / gemCore
#
# The second one is not a refinement of the first. The build before this one cleared the shell
# over 93.4% of the gem — 100.0% today — while its whole rhombus outline sat inside the dark core,
# because nothing ever compared the two: the gem cleared the shell and was buried by the layer in
# between. `gemCore` is the frame that makes that comparison possible, and `coreOnly` is what a
# pixel the core won would look like, which is what the survival projection is measured against.
#
#   base   the frame with all three blade reliefs AND the shell hidden
#   *Only  base + one relief layer   -> that layer's own footprint is (only != base)
#   *Shell that layer + the shell     -> where (shell == only) the layer is proud of the shell
#   gemCore the gem + the dark core   -> where (gemCore == gemOnly) the gem is proud of the core
#   shellOnly base + the shell ALONE  -> what a pixel the SHELL wins reads as
#
# `shellOnly` exists because the shell went SOLID on 2026-08-07 and that broke the identity test
# for one layer. `rootGem` is 22% transmissive and three.js resolves transmission against the
# OPAQUE backbuffer; a translucent shell was never in that buffer, a solid one is, so the shell
# now dims the gem's own pixels by about 8% everywhere the gem plainly wins the depth test.
# Identity scored that as occlusion and read 1.2% where the survival projection reads 100.0%. It
# is the same instrument failure the gem-against-the-core test already had to fix, and it needs
# the same third frame: the colour a pixel the SHELL won would actually read as, to project the
# survival against.
#
# Every frame keeps the whole hilt, so capture_ultima's blank-canvas guard never trips and no
# frame is a special case. Run from the repo root, and re-run it whenever the blade reliefs or
# the shell's stations move — the gate reads these PNGs, not the model.
set -e
# `pipefail` is load-bearing for the retry below: every capture is piped into `tail -2`, and
# without it the pipeline reports TAIL's status, so a failed capture looked like a successful one
# and the retry could never fire.
set -o pipefail
cd "$(dirname "$0")/../../../.."
OUT=artifacts/ultima-v2/vis
INSERT=purpleEnergyInsertFront,purpleEnergyInsertRear
CORE=darkCoreTriangleFront,darkCoreTriangleRear
GEM=rootDiamondGemFront,rootDiamondGemRear
SHELL=outerCrystalShell

# Retries, and it is not defensive padding. Puppeteer drops "Execution context was destroyed,
# most likely because of a navigation" on roughly one view in nine here — always the SECOND view
# of a run, i.e. `back-orthographic`, because that is the only one that re-enters the page after
# a hide-set has already been applied. The failure is in the driver, not in the model: the same
# hide-set succeeds on the next attempt with a byte-identical PNG.
#
# What made it worth fixing rather than re-running by hand: `set -e` turned a dropped frame into
# an aborted script, so the run left BOTH a stale `back-orthographic-*` from the previous
# geometry and a fresh `front-orthographic-*` from this one in the same folder — and
# `measure_relief_visibility.py` reads them as a pair and reports front-versus-rear asymmetry
# that no geometry has. A missing frame is loud; a MISMATCHED pair is not.
ATTEMPTS=3
capture() {
  local label=$1 hide=$2 attempt=1
  while true; do
    if node tools/capture_ultima.mjs --route ultima-v2-harness --out "$OUT" --detail full \
         --views front-orthographic,back-orthographic --hide "$hide" --suffix "-$label" | tail -2
    then
      return 0
    fi
    if (( attempt >= ATTEMPTS )); then
      echo "capture_visibility: $label failed $ATTEMPTS times — stopping so the vis set cannot" >&2
      echo "  be scored as a mixed pair of old and new frames" >&2
      return 1
    fi
    echo "capture_visibility: $label attempt $attempt failed, retrying" >&2
    attempt=$(( attempt + 1 ))
  done
}

for spec in \
  "base:$INSERT,$GEM,$CORE,$SHELL" \
  "insertOnly:$GEM,$CORE,$SHELL" \
  "insertShell:$GEM,$CORE" \
  "coreOnly:$INSERT,$GEM,$SHELL" \
  "coreShell:$INSERT,$GEM" \
  "gemOnly:$INSERT,$CORE,$SHELL" \
  "gemShell:$INSERT,$CORE" \
  "gemCore:$INSERT,$SHELL" \
  "shellOnly:$INSERT,$GEM,$CORE"; do
  capture "${spec%%:*}" "${spec#*:}"
done
