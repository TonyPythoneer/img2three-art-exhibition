#!/bin/zsh
# Deterministic review gates for the v2 rebuild, in the order forge/next.py enforces.
# Run from the repo root:  zsh src/exhibits/ff7-cloud-strife-ultima-weapon/spec/run_gates.sh
set +e

SKILL=$HOME/.claude/skills/img2threejs
REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
V=$REPO/src/exhibits/ff7-cloud-strife-ultima-weapon
A=$REPO/artifacts/ultima-v2
STATE=$REPO/.img2threejs/ff7-cloud-strife-ultima-weapon/state.json
SPEC=$V/spec/object-sculpt-spec.json
REF=$V/assets/artwork-sword-crop.png

mkdir -p "$A/gate"

# Re-frame every capture the tier-1 gate consumes. This step used to be run by hand, which made
# the script unusable by anyone who did not already know it was needed: diagnose_render.py
# compares raw pixels, so a 584x1168 capture against the 210x434 crop measures framing, not shape.
for pass in blockout structural full; do
  python3 "$V/spec/compare_render.py" --gate-render "$A/$pass/artwork-match.png" "$A/gate/$pass.png" > /dev/null
  python3 "$V/spec/compare_render.py" "$A/$pass/artwork-match.png" > "$A/gate/silhouette-$pass.json"
done
python3 "$V/spec/compare_render.py" --gate-render "$A/flat/artwork-match.png" "$A/gate/full-flat.png" > /dev/null
python3 "$V/spec/compare_render.py" "$A/full/artwork-match.png" "$A/overlay-artwork-match.png" > "$V/spec/silhouette-report.json"
python3 "$V/spec/front_rear_overlay.py" "$A/full/front-orthographic.png" "$A/full/back-orthographic.png" "$A/front-rear-overlay.png"

cd "$SKILL"

# Tier 1 runs on the re-framed render, not the raw one: diagnose_render.py compares raw pixels,
# so a 584x1168 render against a 210x434 crop measures framing rather than shape.
for pass in blockout structural-pass form-refinement material-pass surface-pass; do
  case $pass in
    blockout) render=$A/gate/blockout.png ;;
    structural-pass) render=$A/gate/structural.png ;;
    *) render=$A/gate/full.png ;;
  esac
  echo "--- tier1 $pass ---"
  python3 forge/stage4_review/diagnose_render.py \
    --reference "$REF" --render "$render" \
    --map-stripped-render "$A/gate/full-flat.png" \
    --spec "$SPEC" --pass-id "$pass" --in-place --json > "$A/gate/tier1-$pass.json"
  python3 "$V/spec/summarize_gate.py" "$A/gate/tier1-$pass.json"
done

echo "--- multi-angle ---"
python3 forge/stage4_review/diagnose_render_multi_angle.py \
  --reference "$A/full/artwork-match.png" \
  --orbit "$A/full/front-orthographic.png" \
  --orbit "$A/full/assembled-three-quarter.png" \
  --orbit "$A/full/left-side-thickness.png" \
  --orbit "$A/full/right-side-thickness.png" \
  --orbit "$A/full/back-orthographic.png" \
  --json > "$A/gate/multi-angle.json"

echo "--- comparison sheets ---"
for view in artwork-match front-orthographic assembled-three-quarter; do
  python3 forge/stage4_review/make_comparison_sheet.py \
    --reference "$REF" --render "$A/full/$view.png" \
    --out "$A/comparison-$view.png" > /dev/null
done

echo "--- part coverage ---"
python3 forge/stage4_review/check_part_coverage.py \
  --spec "$SPEC" --manifest "$A/full/parts.json" \
  --json "$A/gate/part-coverage.json" --warn-only || true

echo "--- component contract + centreline ---"
python3 "$V/spec/check_centerline.py" "$A/full/parts.json" | tail -6

# Depth is not visibility: a relief can clear the shell at its centre with its whole outline
# buried. This reads the split layers' renders, so it fails if a layer sinks back inside the
# shell even while the ladder's bbox ratios still pass. Capture with spec/capture_visibility.sh.
echo "--- relief visibility, front and rear ---"
python3 "$V/spec/measure_relief_visibility.py"

# Records rather than gates, and it runs here so the JSON can never be stale: the shell is the
# largest surface in the frame and its level has been wrong twice, both times for a reason in the
# render path rather than in the palette.
echo "--- the shell's level against the artwork's ---"
python3 "$V/spec/measure_shell_value.py"

# Which way the crop's spinner caps taper, and which way the BUILT outline does — read off the
# same front-orthographic capture the gates above consume. Recording, not gating: the clause with
# teeth is audit_records.py's exposed-ramp check below, which re-derives the profile from the ARM.
# It runs HERE so the JSON can never be stale, for the same reason measure_shell_value.py does:
# this is the measurement the factory's own comment quotes, and a stale copy of it would be a
# record of the previous geometry describing the current one.
echo "--- which way the spinner caps taper, crop and render ---"
python3 "$V/spec/measure_spinner_taper.py"

echo "--- records match the artifacts ---"
python3 "$V/spec/audit_records.py"

echo "--- pipeline sync ---"
python3 forge/stage3_build/orchestrate_passes.py sync "$SPEC" --in-place
python3 forge/next.py --state "$STATE" "$SPEC" | head -4
