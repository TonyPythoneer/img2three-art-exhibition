# Rebuild plan — Sigma Virus (mmx2) from split sprites

Created 2026-08-24. Rebuilds the Sigma Virus head from a clean per-sprite split of the two
references. This document is the executable source: run it end to end to go from the split crops
to a fresh spec + generated factory wired to the exhibit page.

## Status: BLOCKED at one point — the img2threejs forge pipeline is not installed

"Run img2three" cannot execute in this checkout because the img2threejs **skill is not
installed on this machine.** Evidence:

- No `forge/` directory exists in the repo (`find . -path '*/forge/*'` = empty).
- `~/.claude/` and `~/.config/` do not exist, so the skill base path the plan assumes
  (`~/.claude/skills/img2threejs/forge/…`) resolves to nothing.
- `.img2threejs/state.json` and `.img2threejs/mmx2-sigma-virus/state.json` reference
  `forge/stage1_intake/…`, `forge/stage2_spec/…`, `forge/stage3_build/…` scripts that do not
  exist in this checkout — so even the `state.py init` / `next.py` calls in the old green plan
  are dead.
- The skill was only loaded inline by opencode; its supporting files (`forge/`, `grimoire/`)
  are not on disk. Nothing in python site-packages, the pnpm store, or pipx provides it.
- Network is available, but the two candidate GitHub repos (`TonyPythoneer/img2threejs`,
  `yvgude/img2threejs`) both 404. The correct skill repo is not known from this checkout, so it
  must be supplied (cloned + symlinked) before `img2three` can run.

This is not a reading ambiguity to "decide and move on" — it is an installed tool that is
missing. Re-authoring 674 lines of SDF geometry blind (no browser, no showcase, no render loop)
is exactly the wasted-effort case the repo rules tell us to avoid, so the work stops here and
hands over a precise remediation.

## What IS done (reproducible, in this checkout)

Clean, properly-named per-sprite split — the prerequisite work "check sprites and split them,
name them properly":

- `artifacts/exhibits/mmx2-sigma-virus/references/sigma-wireframe-sheet.png` (610×2644, navy
  `(0,0,41)` background, 84%) was sliced by content rows and, within each row, by horizontal
  gaps into **66 crops** in `artifacts/exhibits/mmx2-sigma-virus/split/`:
  - rows 0–2: small blue-white wireframe heads at several yaws (9/7/9 copies);
  - row 3: one wide gallery row (multi-view);
  - rows 4–5: red-palette variant at several yaws (7/9 copies);
  - row 6: one wide red/gold gallery row;
  - row 7: a multicolour **palette-swatch** row (20 usable crops; near-empty ones skipped).
  - naming: `sheet_row{R}c{NN}.png`; each manifest entry records its `bboxInSheet` and size.
- Manifest: `artifacts/exhibits/mmx2-sigma-virus/split/split-manifest.json`.
- Green front reference `references/sigma-front-green-ostation.png` (480×360) characterised:
  green helmeted head, bright-green centered visor/eye slit, at the cheek-lobe width, narrowing
  to a jaw + separate chin; **bilateral channel diff R/G/B ≈ 6.3 / 19.5 / 7.3** → not a perfect
  mirror (green channel is the asymmetric one). Reading: model each side independently rather
  than assuming pure reflection (see below).

## Reference reading (decomposition → codes)

One editable low-poly head; geometry from the most symmetric full-scale crop of the sheet,
colour authority from the green front + the green cell(s) of the sheet:

Parts: crown shell, forehead shell, L/R temple shells, L/R cheek lobes (widest band), recessed
face cavity, L/R eye plates, mid-face bridge, lower jaw, L/R chin tabs, rear shell.

Codes (assigned before geometry, per repo rules):

- Shape code S — from measured crop dimensions (side pairs share one generator only when they
  measure the same; here L/R are *not* identical — the green-channel asymmetry is real — so each
  side keeps its own geometry).
- Colour code C — green helm body (approx. `(20,120,20)`–`(63,255,71)` variant), bright-green
  visor accent (approx. `(63,255,71)`), red-palette alternate (approx. `(189,0,8)`), navy fill
  `(0,0,41)` as reference.
- Material code M — structural wire = low-roughness metallic flatShading; eye accent = emissive
  green. Only two material families → folded into the colour stage (no separate material stage).

Symmetry decision: the green-channel bilateral diff (≈19.5) clears the noise floor, so the head
is **slightly asymmetric**. Read each side's own surface parameters from the sheet rather than
mirroring one side across the other.

Guess list (references do not resolve these; a default is recorded):

- G1 rear shell: broad symmetric continuation, no invented panels (from oblique rows 3/6).
- G2 eye depth: recessed (eye outline sits inside the face planes).
- G3 chin tabs: independent geometry (recur at the same lower-head position across copies).
- G4 exact yaw of each row cell: use canonical inspection probes, not assumed frame labels.

## Remediation — how to make "run img2three" actually run

Supply the img2threejs skill once (network is up; the repo just isn't named here):

```bash
# 1. Obtain the img2threejs skill (repo must be supplied — neither candidate above exists).
git clone <img2threejs-skill-repo-url> ~/.claude/skills/img2threejs
ln -s ~/.claude/skills/img2threejs ~/.config/opencode/skills/img2threejs   # opencode view

# 2. From this exhibit, reset forge state to a fresh generic run on the green front.
SKILL="$HOME/.claude/skills/img2threejs"
python3 "$SKILL/forge/state.py" init \
  --state .img2threejs/state.json \
  --reference artifacts/exhibits/mmx2-sigma-virus/references/sigma-front-green-ostation.png \
  --profile generic \
  --spec artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json

# 3. Ask forge for the next mandatory command and obey it (never continue from memory).
python3 "$SKILL/forge/next.py" --state .img2threejs/state.json \
  artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json
```

`next.py` prints the exact next command, current pass/step, loop count, and `loop/max`. When it
reports `loop` is reached or `status=stopped`, stop and report — do not push past `loop/max`.

From a fresh, `strict-quality`-passed spec, generate the factory and wire the page:

```bash
# 4. Generate the TypeScript factory (fail-closed: strict-quality must pass first).
python3 "$SKILL/forge/stage3_build/generate_threejs_factory.py" \
  artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json \
  --out artifacts/exhibits/mmx2-sigma-virus/spec/generated-factory.ts

# 5. Wire src/pages/mmx2-sigma-virus/index.vue + createSigmaVirusHead/ to the generated factory.
#    The viewer contract (mountSigmaVirusViewer.ts) requires: a THREE.Group whose children are
#    named parts, each mesh with Material.userData.sigmaBaseColor, and group.userData.sculptRuntime
#    as ProceduralModelRuntime.
node --test tests/**/*.test.mjs       # repo tests
pnpm run typecheck                    # vue-tsc --noEmit
```

The split crops are the geometry inputs: feed them via `new_pre_spec_assessment.py` /
`build_detail_inventory.py` (grid-3×3) or the low-poly bounding boxes in `split-manifest.json`
when authoring the spec, so every part name maps to a real crop.

## Rerun one-liner (once the skill is cloned)

```bash
SKILL="$HOME/.claude/skills/img2threejs"
python3 "$SKILL/forge/state.py" init --state .img2threejs/state.json \
  --reference artifacts/exhibits/mmx2-sigma-virus/references/sigma-front-green-ostation.png \
  --profile generic --spec artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json && \
python3 "$SKILL/forge/next.py" --state .img2threejs/state.json \
  artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json
```
