#!/bin/zsh
# Append one self-correction review per build pass, with the real measured evidence.
# Run from the repo root:  zsh src/exhibits/cloud-ultima-weapon-v2/spec/record_reviews.sh
#
# Reviews are cleared by author_spec.py on every re-author, so this script is the single
# source of the review record and can be re-run from any state.
set +e

SKILL=$HOME/.claude/skills/img2threejs
REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
V=$REPO/src/exhibits/cloud-ultima-weapon-v2
A=$REPO/artifacts/ultima-v2
SPEC=$V/spec/object-sculpt-spec.json
cd "$SKILL"

r() { python3 forge/stage4_review/append_review.py "$SPEC" --in-place "$@"; }
FR="$V/spec/feature-reviews"

r --pass-id blockout --fidelity 0.88 --action continue \
  --feature-reviews-json "$FR/blockout.json" \
  --camera-view artwork-match \
  --render-screenshot "$A/blockout/artwork-match.png" \
  --reference-screenshot "$V/assets/artwork-sword-crop.png" \
  --comparison-image "$A/comparison-artwork-match.png" \
  --map-stripped-render "$A/gate/full-flat.png" \
  --ai-vision-score 0.86 --visual-threshold 0.78 \
  --layer-scores-json '{"silhouetteProportion":0.89,"componentStructure":0.82,"formDetail":0.72,"materialSurface":0.50,"lightingCamera":0.80}' \
  --summary "Macro silhouette holds through both correction passes. Registered silhouette IoU 0.8561; tip 1.00%, pommel 0.59%, lateral extremes 1.00%/1.00% of image height against a 2.5% budget. The tier-1 blockout gate is RED at 0.8175 against a 0.85 floor, and every step down is a user direction rather than a defect: 0.8553 to 0.8478 on 2026-08-11 when both arms came up onto the jaws' outer corners, to 0.8367 on 2026-08-12 when the arms were directed longer so the spinner balls hang lower, to 0.8348 on 2026-08-13 when the caps became frusta widest at the top, and to 0.8175 later that day when the arms were directed longer again and the caps shortened with them. Swept over the arm's length and over CONNECTOR_RADIUS, nothing but reverting the directions recovers it - a documented limitation, CURRENT-MODEL.md section 8. The floor and the IoU computation are untouched." \
  --matched "blade tip at Y=760 and pommel tip at Y=-211 both within 1% of image height;the shell converges from its widest half-width 82 at Y=70 into the two clamp contact points at (+/-31.57, 13), above the jaws' own lowest vertex;four drivers reach the measured endpoints (+/-125, 56) and (+/-155, 12)" \
  --mismatches "the shell's own maximum half-width dropped from 95 to 88 when the base flare was re-read as a projection artifact; that is a deliberate change, not drift" \
  --code-fixes "replaced the shell's flat lower slab with a converging neck: the correction pass called for it, and it also cleared the driver roots, which had needed a Z=+17 hack to stay visible" \
  --evidence "$A/gate/silhouette-blockout.json"

r --pass-id structural-pass --fidelity 0.88 --action continue \
  --feature-reviews-json "$FR/structural-pass.json" \
  --camera-view artwork-match \
  --render-screenshot "$A/structural/artwork-match.png" \
  --reference-screenshot "$V/assets/artwork-sword-crop.png" \
  --comparison-image "$A/comparison-artwork-match.png" \
  --map-stripped-render "$A/gate/full-flat.png" \
  --ai-vision-score 0.86 --visual-threshold 0.78 \
  --layer-scores-json '{"silhouetteProportion":0.89,"componentStructure":0.90,"formDetail":0.80,"materialSurface":0.55,"lightingCamera":0.80}' \
  --summary "Hilt rebuilt to correction pass 2's ownership tree: crystal clamp pair (which IS the blade socket), guard bridge, two leather connectors, two spinner ends, four drivers attached directly to the connectors, grip, independent conical pommel. No centralGripSocket, no driverSocket meshes and no gripEndCollar. check_part_coverage reports 22 specified / 22 built / 0 errors." \
  --matched "every node in correction pass 2's contract exists and is independently selectable, with nothing extra - 19 meshes, since the dark core and the diamond are each two Z=0 halves and the grip end collar is deleted;the four rods are one shared geometry placed by four transforms;the two clamps meet the gem edge-to-edge and no separate socket mesh sits between them" \
  --mismatches "the dark core triangle's base half-width is still directed rather than measured: below the gem's apex the gem's own rim-dark shading shares the crop's dark run, so nothing can separate the two there. Its apex is measured (spec/measure_core_apex.py)" \
  --code-fixes "the four driver sockets and the central grip socket were deleted outright, not resized: correction pass 2 rejects them as components. Each rod's root radius is now solved against the connector's own cylinder surface by driverRootRadius(), so the joint stays flush without a socket to hide it" \
  --evidence "$A/gate/tier1-structural-pass.json"

r --pass-id form-refinement --fidelity 0.86 --action continue \
  --feature-reviews-json "$FR/form-refinement.json" \
  --camera-view artwork-match \
  --render-screenshot "$A/full/artwork-match.png" \
  --reference-screenshot "$V/assets/artwork-sword-crop.png" \
  --comparison-image "$A/comparison-artwork-match.png" \
  --map-stripped-render "$A/gate/full-flat.png" \
  --ai-vision-score 0.84 --visual-threshold 0.78 \
  --layer-scores-json '{"silhouetteProportion":0.89,"componentStructure":0.90,"formDetail":0.85,"materialSurface":0.60,"lightingCamera":0.80}' \
  --summary "Rods cut as faceted cylinders with root tapers and capped ends; clamp jaws faceted to four planes; spinner ends cut as straight-sided frusta widest at the top, derived from the seat so the arm can move without restretching them; grip held at constant width." \
  --matched "only the shell carries a sharpened profile;rods have a circular section at eight radial segments, not a rectangular prism;the grip does not narrow below the guard and carries exactly one collar" \
  --mismatches "the guard's plate geometry is still inferred: the measured steel bbox has no solution as a single rotated rectangle at any rake angle, so the arms are sized to the measured X range and raked per reference 03. Each arm's LENGTH is DERIVED as of 2026-08-13, at 88.7455: the crop pins the arm's outer end as a point, (81.925, -62.806), and with the root and the rake both locked the built end can only slide along one ray that misses that point by 28.947 units at every length, so the length that ships is the perpendicular projection. It solves neither pin - the axis lands 21.974 units wide of the crop's 81.925 and the gold appears 19.45 units high of its -53.45 - and it is still the closest the arm can get. CURRENT-MODEL.md section 11 G4 carries every candidate length with its own miss." \
  --code-fixes "the gem's Z stack was pulled from +30 to +19 after the side view showed its front vertex at Z=45 against a 13-deep blade - it read as bolted onto the front rather than mounted in the hilt" \
  --evidence "$A/gate/tier1-form-refinement.json"

r --pass-id material-pass --fidelity 0.80 --action continue \
  --feature-reviews-json "$FR/material-pass.json" \
  --camera-view artwork-match \
  --render-screenshot "$A/full/artwork-match.png" \
  --reference-screenshot "$V/assets/artwork-sword-crop.png" \
  --comparison-image "$A/comparison-artwork-match.png" \
  --map-stripped-render "$A/gate/full-flat.png" \
  --ai-vision-score 0.78 --visual-threshold 0.78 \
  --layer-scores-json '{"silhouetteProportion":0.89,"componentStructure":0.90,"formDetail":0.85,"materialSurface":0.78,"lightingCamera":0.82}' \
  --summary "Eleven material zones as vertex-colour ramps plus baked facet steps. Two new zones this pass: dark grey connector leather, and a lighter machined metal for the clamp pair. The shell is SOLID by user direction of 2026-08-07 - a departure from the brief, recorded in confidence-report.md conflict 6 - with every blend path off and depthWrite on, and its level paid by a white emissive multiplied by vertex colour because the review rig delivers only 0.322 of albedo." \
  --matched "the connector arms read as dark grey leather rather than black metal;the clamp jaws read as machined metal against that leather;the solid shell depth-culls none of the three inner layers, which stand 97.6 / 93.2 / 100.0 per cent proud of it in the render;no maps anywhere - the source has zero surface relief" \
  --mismatches "tier-1 per-part colour delta-E peaks at 57.55 against a 20.0 threshold; the shell itself now measures (215, 216, 228) against the reference's (216, 217, 227), so what is left sits in the smaller parts rather than the blade" \
  --code-fixes "clamp metal set two stops lighter than the guard steel: at the guard steel's own value the jaws and the leather collapsed into one black mass at exactly the place this pass is about. Every vertex-coloured material also had its material.color forced to white, because Three.js multiplies it into the vertex colour and was squaring the albedo" \
  --visual-notes "PBR extraction ran on five verified crops and was deliberately rejected - see spec/pbr-evidence/README.md." \
  --evidence "$V/spec/pbr-evidence/README.md"

r --pass-id surface-pass --fidelity 0.80 --action continue \
  --feature-reviews-json "$FR/surface-pass.json" \
  --camera-view artwork-match \
  --render-screenshot "$A/full/artwork-match.png" \
  --comparison-image "$A/comparison-artwork-match.png" \
  --map-stripped-render "$A/gate/full-flat.png" \
  --ai-vision-score 0.79 --visual-threshold 0.78 \
  --layer-scores-json '{"silhouetteProportion":0.89,"componentStructure":0.90,"formDetail":0.85,"materialSurface":0.79,"lightingCamera":0.82}' \
  --summary "Per-face value steps hold as flat facets from all six review viewpoints. The grip's wrap is vertex-colour banding on the shaft, with zero protruding ring meshes." \
  --matched "flat facet reading survives the orbit;the two leathers stay distinguishable from each other and from the metal beside them;no normal or displacement map anywhere in the build" \
  --mismatches "same per-part colour delta-E failure as the material pass; it is a colour-level, not a surface-level, defect" \
  --evidence "$A/gate/multi-angle.json"

r --pass-id lighting-pass --fidelity 0.82 --action continue \
  --feature-reviews-json "$FR/lighting-pass.json" \
  --camera-view artwork-match \
  --render-screenshot "$A/full/artwork-match.png" \
  --comparison-image "$A/comparison-artwork-match.png" \
  --ai-vision-score 0.80 --visual-threshold 0.78 \
  --layer-scores-json '{"silhouetteProportion":0.89,"componentStructure":0.90,"formDetail":0.85,"materialSurface":0.80,"lightingCamera":0.84}' \
  --summary "Near-ambient rig: key 0.22, hemisphere 0.62, ambient 0.42, linear tone mapping, white background, no rim. The same rig lights every one of the nine required validation renders." \
  --matched "no invented rim highlight;front and rear renders share camera distance and scale exactly, so they are comparable;linear tone mapping keeps the violet insert and magenta gem saturated where ACES desaturates both" \
  --mismatches "the rig is near-flat by necessity - shading is baked in vertex colour - so it cannot also serve as a physically motivated studio rig" \
  --evidence "$V/spec/object-sculpt-spec.json"

r --pass-id interaction-pass --fidelity 0.90 --action continue \
  --feature-reviews-json "$FR/interaction-pass.json" \
  --camera-view exploded-three-quarter \
  --render-screenshot "$A/full/exploded-three-quarter.png" \
  --comparison-image "$A/comparison-artwork-match.png" \
  --ai-vision-score 0.88 --visual-threshold 0.78 \
  --layer-scores-json '{"silhouetteProportion":0.89,"componentStructure":0.92,"formDetail":0.85,"materialSurface":0.80,"lightingCamera":0.84}' \
  --summary "22 named nodes over 19 meshes; check_part_coverage reports 22 specified / 22 built / 0 errors. The contract is asserted by spec/check_centerline.py, which fails on an extra part and on a missing one." \
  --matched "every node in the correction spec's ownership tree is selectable and explodable;the dark core's and the diamond's two halves carry opposite explode directions, so pulling the model apart separates each relief front from rear instead of sliding one symmetric lump" \
  --mismatches "none" \
  --evidence "$A/gate/part-coverage.json"

r --pass-id optimization-pass --fidelity 0.90 --action continue \
  --feature-reviews-json "$FR/optimization-pass.json" \
  --camera-view artwork-match \
  --render-screenshot "$A/full/artwork-match.png" \
  --comparison-image "$A/comparison-artwork-match.png" \
  --ai-vision-score 0.86 --visual-threshold 0.78 \
  --layer-scores-json '{"silhouetteProportion":0.89,"componentStructure":0.92,"formDetail":0.85,"materialSurface":0.80,"lightingCamera":0.84}' \
  --summary "868 triangles at full detail across 19 meshes — No decimation applied." \
  --matched "still two orders of magnitude under the real-time target;the blockout tier drops to 820 triangles by hiding the inset blade layers and the clamp pair, not by decimating" \
  --mismatches "none" \
  --evidence "$A/full/parts.json"

python3 forge/stage3_build/orchestrate_passes.py sync "$SPEC" --in-place
