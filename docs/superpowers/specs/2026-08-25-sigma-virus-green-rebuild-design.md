# Sigma Virus — green sprite fix + pipeline rerun (design)

**Date:** 2026-08-25
**Scope:** `mmx2-sigma-virus` exhibit
**Goal:** make the green split sprites faithful evidence of the green Sigma, then re-execute the img2threejs pipeline end-to-end against the existing spec, gated by the 1.5.1 gate set.

## Background

The exhibit is `status: building` in `src/utils/exhibits.ts`. A previous run produced
`src/utils/sigmaVirusHead/createSigmaVirusHead.ts` (1743 lines) plus 60+ gate JSONs in
`artifacts/exhibits/mmx2-sigma-virus/spec/gates/`. The two REBUILD_PLAN / PLAN_FROM_SCRATCH_GREEN
documents in `spec/` are mid-run; the user wants the work consolidated against a corrected sprite
layer.

The user observed: *"some of the split sprites are wrong, focus on the green one, you can edit
the split sprites if there is any noise."* Translation: the green split crops in
`artifacts/exhibits/mmx2-sigma-virus/split/` are not all green, and at least one is poorly cropped.

## Diagnosis (evidence)

Sheet source: `artifacts/exhibits/mmx2-sigma-virus/references/sigma-wireframe-sheet.png`,
610×2644, navy `(0,0,41)` background.

The four cells at `sheet_row7c{62,63,64,65}.png` are the bottom-right palette-swatch row. Color
histograms (256-level RGB, ignoring alpha 0 and pure navy):

| file | bbox in sheet | size | dominant non-navy color | variant |
|---|---|---|---|---|
| `sheet_row7c62.png` | `[383,2564,431,2641]` | 48×77 | `(160,0,0)` ≈ `#A00000` | **red** |
| `sheet_row7c63.png` | `[441,2564,489,2640]` | 48×76 | `(160,32,224)` ≈ magenta | **purple** |
| `sheet_row7c64.png` | `[496,2564,544,2643]` | 48×79 | `(0,192,32)` ≈ `#00C020` | **green** ✓ (miscalibrated) |
| `sheet_row7c65.png` | `[553,2573,600,2641]` | 47×68 | `(224,32,0)` ≈ `#E02000` | **red/orange** |

Only `c64` is green. The other three are non-green palette variants that look superficially
similar in cell shape but read wrong colors. **Splitting them under a `sheet_row7c{NN}.png` naming
scheme with no palette tag invites the misread that all four are green.**

`c64` itself is miscalibrated: its bbox `[496,2564,544,2643]` overlaps the **true** green yaw cell
at `[496,2573,550,2648]` (the cell `green-breakdown/manifest.json` already names `sheet_green_yaw_full`
and which `green-breakdown/sheet_green_yaw_full.png` cuts at the correct 54×75), but the split
version starts 9px too early in y (capturing 9 rows of palette-swatch bleed above) and ends 6px too
early in x (clipping the right edge).

The existing pipeline (`green-breakdown/`, `object-sculpt-spec.json`, `createSigmaVirusHead.ts`)
uses the **correct** `sheet_green_yaw_full.png` from `green-breakdown/`, not the broken
`split/sheet_row7c64.png`. The model is not poisoned; the defect is at the `split/` layer.

## What this design does

Three phases, in this order. Each is independent, with its own evidence, so a phase that fails
does not poison the next.

### Phase 1 — Correct the `split/` layer (image + manifest)

- Re-cut `split/sheet_row7c64.png` from the true green cell at sheetBox
  `[496, 2573, 550, 2648]` (54×75) using PIL with `Image.NEAREST` upscaling only for the
  side-by-side evidence (the crop itself stays at native resolution). Overwrite the file and
  update `split-manifest.json` so `sheet_row7c64` reads `bboxInSheet: [496, 2573, 550, 2648]`,
  `size: [54, 75]`.
- Rename `split/sheet_row7c62.png` → `split/sheet_row7c62_red.png`,
  `split/sheet_row7c63.png` → `split/sheet_row7c63_purple.png`,
  `split/sheet_row7c65.png` → `split/sheet_row7c65_red.png`. Update
  `split-manifest.json` entries with `paletteVariant: "red" | "purple"` and `notGreen: true`.
- Write `artifacts/exhibits/mmx2-sigma-virus/split/PHASE1_NOTES.md` containing:
  - the per-cell color histograms (the table above, sourced from the actual file contents);
  - a side-by-side 12× NEAREST strip of c62/c63/c64/c65 at original 48×77 scale (one PNG, written to `.tmp/sigma/` then referenced from the notes file);
  - a one-line note that **only `sheet_row7c64.png` is a green input**; the others are
    palette-swap evidence for non-green readings and must not enter any "green" pipeline.
- Preserve everything else in `split/` exactly as it is. The other 62 crops are not in scope
  (per the user's "only the green one").

### Phase 2 — Re-execute the img2threejs pipeline end-to-end

- `mkdir -p .img2threejs/mmx2-sigma-virus/`
- `python3 ~/.claude/skills/img2threejs/forge/state.py init --state .img2threejs/mmx2-sigma-virus/state.json --reference artifacts/exhibits/mmx2-sigma-virus/references/sigma-front-green-ostation.png --profile generic --max-per-pass 3 --max-total 42 --spec artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json`
- `python3 ~/.claude/skills/img2threejs/forge/next.py --state .img2threejs/mmx2-sigma-virus/state.json artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json` repeatedly until it returns `status=stopped` or every stage is reviewed `continue`. The skill mandates this — never reconstruct from chat memory.
- For each `pass-id` the script unlocks: run the relevant gates listed in
  `grimoire/review/gates_reference.md` (Tier-1 `diagnose_render.py`, multi-angle, turntable,
  interior-difference, material-comparison, attachment-anchor, self-intersection, part-coverage,
  chirality). Capture the side-by-side sheet. Decide `continue | refine-spec | refine-code |
  request-input | stop` myself on the evidence, and record it with
  `forge/stage4_review/append_review.py`.
- `strict-quality` is a hard gate: if the new spec fails it, do **not** regenerate the factory.
  The existing `createSigmaVirusHead.ts` stays.
- The skill's per-pass default of 3 corrections is preserved. After 3 refine loops on the same
  pass, the reading is wrong, not the code — re-read the reference. The skill says this in
  AGENTS.md; it is the AGENTS.md rule, not a preference.

### Phase 3 — Wire and verify (only if the new factory clears Phase 2)

- If `forge/stage3_build/generate_threejs_factory.py` produces a factory that differs from
  `artifacts/exhibits/mmx2-sigma-virus/spec/generated-factory.ts` AND the new one passes the
  gate set, port the diff into `src/utils/sigmaVirusHead/createSigmaVirusHead.ts` using the
  existing adapter (it already ports verbatim: SDF polygonizer, extrude builder, palette
  constants `#000029`/`#10D830`/`#10B010`/`#E05000`, named parts as direct children).
- If the new factory does not clear the gates, leave `createSigmaVirusHead.ts` untouched and
  record why.
- `pnpm run typecheck`; the project's existing test commands; `node tools/capture_sigma.mjs`
  for a fresh preview; eyeball the result against the reference zoom.

## Global constraints (verbatim from the project)

- `artifacts/` keeps only measurement records and the scripts that produce them. No renders,
  no PBR maps, no detail-inventory crops. (AGENTS.md "Directory rules".)
- Page assets (images, prompt.txt) live under `src/assets/exhibits/mmx2-sigma-virus/`, flat.
  (AGENTS.md "Adding an exhibit means wiring five places".)
- `ctx_*` MCP tools replace native Read/Grep/Glob/Shell. `magick` and `python3 -c` need native
  `Bash` (`docs/agents/claude.md`). The zoom/inspect scripts write to `.tmp/` (project root,
  added to `.gitignore`).
- AGENTS.md "Work split": never `/orchestration`, never opencode dispatch, never subagents
  to split the work. "Run the plan" = `executing-plans` in this session.
- "Decide, then keep going. Do not ask for `continue`." Decisions are the agent's, on the
  evidence. Only stop when all three hold: the decision changes committed work, the evidence
  does not settle it, and proceeding would waste effort.

## File-level map (added/modified)

- **Modified:** `artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c64.png` (re-cut)
- **Renamed:** `split/sheet_row7c62.png` → `_red.png`; `c63.png` → `_purple.png`; `c65.png` → `_red.png`
- **Modified:** `artifacts/exhibits/mmx2-sigma-virus/split/split-manifest.json` (bbox fix + `notGreen` flags)
- **Created:** `artifacts/exhibits/mmx2-sigma-virus/split/PHASE1_NOTES.md`
- **Created:** `.img2threejs/mmx2-sigma-virus/state.json` (forge-managed; one per exhibit)
- **Possibly modified:** `src/utils/sigmaVirusHead/createSigmaVirusHead.ts` (only if Phase 2 produces a different factory and the gates clear)

No new files outside these paths. No deletion of existing evidence.

## What this design does NOT do

- Does not touch `src/utils/sigmaVirusHead/createSigmaVirusHead.ts` unless Phase 2 produces a
  new factory that clears the gates.
- Does not edit `src/utils/exhibits.ts`, `src/utils/exhibitSlugs.ts`, the page route, the
  content yml, or the assets folder — those are already wired and not in scope.
- Does not regenerate `green-breakdown/` — it already has the correct green yaw. Only the
  `split/` layer needed correction.
- Does not introduce new dependencies.
- Does not commit, push, merge, or deploy.

## Rerun command (single line)

```bash
python3 ~/.claude/skills/img2threejs/forge/state.py init \
  --state .img2threejs/mmx2-sigma-virus/state.json \
  --reference artifacts/exhibits/mmx2-sigma-virus/references/sigma-front-green-ostation.png \
  --profile generic --max-per-pass 3 --max-total 42 \
  --spec artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json \
  && python3 ~/.claude/skills/img2threejs/forge/next.py \
       --state .img2threejs/mmx2-sigma-virus/state.json \
       artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json
```

## Failure modes and exit criteria

- **Phase 1 fail** (e.g. PIL cannot open a file, manifest edit syntax error): stop, the split
  layer is left as-is, Phase 2/3 do not run.
- **Phase 2 fail** (`status=stopped` from `next.py`, gate failure not explainable, or 3 failed
  refine loops on one pass): stop, the existing factory and gates stay, evidence recorded
  in `spec/PHASE2_NOTES.md`.
- **Phase 3 fail** (typecheck, test, or visual regression): the new factory is reverted, the
  old factory stays, evidence recorded.

Exit criterion (success): `tools/capture_sigma.mjs` produces a fresh preview that matches the
reference zoom side by side, all gates green, and `src/utils/sigmaVirusHead/createSigmaVirusHead.ts`
is either unchanged (old factory still good) or updated to the new factory whose gates cleared.
