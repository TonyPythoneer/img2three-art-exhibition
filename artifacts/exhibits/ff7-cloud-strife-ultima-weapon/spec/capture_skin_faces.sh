#!/bin/zsh
# The four frames that separate "the two films are different colours" into its two causes.
#
# Each frame shows exactly ONE of the two insert halves, from exactly one of the two orthographic
# cameras, so every pixel belongs to a single face of a single mesh:
#
#   front camera + only the REAR half   -> the rear film's UNDERSIDE, the face touching the shell
#   back  camera + only the FRONT half  -> the front film's UNDERSIDE, the same face on the other
#                                          half. These two are what the correction is about.
#   front camera + only the FRONT half  -> the front film's outer face
#   back  camera + only the REAR half   -> the rear film's outer face
#
# Captured TWICE, and that is the whole diagnostic: `--flat` swaps every material for an unlit
# MeshBasic, so the pixel IS the baked vertex colour, while the lit pass adds the look-dev rig on
# top. The rig's key and `applyFacetSteps`' key are the SAME measured vector (-0.42, 0.62, 0.66),
# so only this pair of captures can say which of the two produced a difference. Measured on the
# build this replaces, the two shell-facing undersides were 1.2748 apart in linear light: 1.2003
# of that was vertex colour and the remaining 1.0621 was the rig.
#
# Run from the repo root; `spec/measure_skin_faces.py` reads what this writes.
set -e
cd "$(dirname "$0")/../../../.."
OUT=artifacts/ultima-v2/diag
ALL=(outerCrystalShell purpleEnergyInsertFront purpleEnergyInsertRear darkCoreTriangleFront \
     darkCoreTriangleRear rootDiamondGemFront rootDiamondGemRear crystalClampLeft \
     crystalClampRight leatherConnectorLeft leatherConnectorRight driverLeftUpper \
     driverLeftLower driverRightUpper driverRightLower spinnerEndLeft spinnerEndRight \
     leatherGrip pointedMetalPommel)

for keep in purpleEnergyInsertFront purpleEnergyInsertRear; do
  hide=${(j:,:)${ALL:#$keep}}
  label=${keep#purpleEnergyInsert}
  for lighting in flat lit; do
    [[ $lighting == flat ]] && flag=(--flat) || flag=()
    node tools/capture_ultima.mjs --route ultima-v2-harness --out "$OUT" --detail full \
      --views front-orthographic,back-orthographic --hide "$hide" $flag \
      --suffix "-${lighting}Insert${label}" | tail -2
  done
done

python3 src/exhibits/ff7-cloud-strife-ultima-weapon/spec/measure_skin_faces.py
