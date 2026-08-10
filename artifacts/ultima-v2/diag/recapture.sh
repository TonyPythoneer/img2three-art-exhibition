#!/bin/zsh
# Re-capture the whole v2 review set (RELATIONSHIPS.md §7), on a private port.
set -e
cd "$(dirname "$0")/../../.."
PORT=${CAPTURE_PORT:-3198}
for v in front-orthographic back-orthographic left-side-thickness right-side-thickness \
         assembled-three-quarter rear-three-quarter artwork-match exploded-three-quarter \
         closeup-crystal-clamp closeup-clamp-bases closeup-driver-joints \
         closeup-connectors closeup-spinner-ends closeup-grip-pommel; do
  CAPTURE_PORT=$PORT node tools/capture_ultima.mjs --route ultima-v2-harness \
    --out artifacts/ultima-v2/full --detail full --views $v | tail -1
done
CAPTURE_PORT=$PORT node tools/capture_ultima.mjs --route ultima-v2-harness \
  --out artifacts/ultima-v2/flat --detail full --views artwork-match --flat | tail -1
CAPTURE_PORT=$PORT node tools/capture_ultima.mjs --route ultima-v2-harness \
  --out artifacts/ultima-v2/blockout --detail blockout --views artwork-match | tail -1
CAPTURE_PORT=$PORT node tools/capture_ultima.mjs --route ultima-v2-harness \
  --out artifacts/ultima-v2/structural --detail structural --views artwork-match | tail -1
