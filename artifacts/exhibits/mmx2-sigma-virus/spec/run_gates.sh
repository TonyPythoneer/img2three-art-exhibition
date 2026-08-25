#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../.."
RENDERS=${RENDERS:-/tmp/sigma-clean-renders}
rm -rf "$RENDERS"
node tools/capture_sigma.mjs --out "$RENDERS" --each-part --yaw-sweep 10
node tools/verify_sigma_parts.mjs
printf 'PASS: fresh canonical and yaw captures written to %s\n' "$RENDERS"
