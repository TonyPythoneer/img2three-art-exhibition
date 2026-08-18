#!/usr/bin/env bash
# Every gate for the Sigma virus head, in one run, from a FRESH capture.
#
#   artifacts/exhibits/mmx2-sigma-virus/spec/run_gates.sh
#
# Renders are written to $RENDERS (default /tmp/sigma-renders) and are NOT tracked — the
# numbers live in the JSON next to this script, and the renders regenerate from capture_sigma.
# The capture is always re-run: a gate scored against a stale PNG is the failure mode CLAUDE.md
# spends a paragraph on.
set -uo pipefail
cd "$(dirname "$0")/../../../.."          # repo root

SHEET=artifacts/exhibits/mmx2-sigma-virus/references/sigma-wireframe-sheet.png
SPEC=artifacts/exhibits/mmx2-sigma-virus/spec
RENDERS=${RENDERS:-/tmp/sigma-renders}
fail=0

echo "== capture =="
node tools/capture_sigma.mjs --out "$RENDERS" --yaw-sweep 10 || exit 2

echo
echo "== gate: front silhouette (IoU vs the geometry-authority frame) =="
python3 "$SPEC/gate_silhouette.py" "$RENDERS/front.png" "$SHEET" \
  --out "$SPEC/gate-silhouette.json" || fail=1

echo
echo "== gate: interior features (eye band + filled eye area) =="
python3 "$SPEC/gate_features.py" "$RENDERS/front.png" "$SHEET" "$SPEC/landmarks.json" \
  --out "$SPEC/gate-features.json" || fail=1

echo
echo "== gate: depth (yaw-sweep width ratio vs the reference's 87 pure-yaw frames) =="
python3 "$SPEC/gate_yaw_sweep.py" "$RENDERS" "$SHEET" "$SPEC/frame-index.json" \
  --out "$SPEC/gate-yaw.json" || fail=1

echo
echo "== gate: structure (13 named parts, none fused, explode separates) =="
node tools/verify_sigma_parts.mjs > "$SPEC/gate-parts.json" || fail=1
tail -1 "$SPEC/gate-parts.json"

echo
if [ "$fail" -ne 0 ]; then
  echo "GATES FAILED"
  exit 1
fi
echo "ALL GATES PASSED"
