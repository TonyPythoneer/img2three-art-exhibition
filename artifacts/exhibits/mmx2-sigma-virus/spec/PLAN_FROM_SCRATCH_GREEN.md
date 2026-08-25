# Plan — Sigma Virus green rebuild from scratch

Generated 2026-08-24. This plan is the executable source for a fresh green-focused intake run.

## Scope and authority

- Colour authority: `artifacts/exhibits/mmx2-sigma-virus/references/sigma-front-green-ostation.png` and the single green yaw crop in `sigma-wireframe-sheet.png`.
- Non-green sheet sprites are labelled structural supplements only; they may inform depth and canonical probe angles, never palette.
- Preserve irreproducible references and existing source model files until a later forge pass explicitly replaces them.
- All generated breakdown output is disposable and is recreated by the command below.

## From-scratch reset contract

Before running the forge intake:

1. Recreate `spec/green-breakdown/` from `green_breakdown_v3.py`.
2. Preserve any existing `.img2threejs/state.json` as `state.before-from-scratch-<timestamp>.json` in the plan ledger directory.
3. Remove only `.img2threejs/state.json`, then initialise a fresh state using the green OSTation reference and `generic` profile.
4. Do not delete references, source model code, existing measurement evidence, or unrelated dirty-worktree files.
5. Run `forge/next.py` and record the next mandatory step; this plan intentionally stops at the forge-selected step rather than claiming the entire pipeline is complete.

## Global constraints

- Use x8 `Image.NEAREST` crops at joints and observation clusters.
- The breakdown must contain one manifest entry and PNG for every generated crop.
- Green and non-green evidence must remain explicitly labelled.
- State reset must be recoverable from the preserved backup.
- No automatic commit, push, merge, deployment, or destructive cleanup.

## Task 1 — Rebuild angle-labelled green breakdown

Run:

```bash
python3 artifacts/exhibits/mmx2-sigma-virus/spec/green_breakdown_v3.py
```

Expected result: `spec/green-breakdown/` contains `manifest.json`, `BREAKDOWN.md`, and 42 x8 NEAREST PNG crops.

## Task 2 — Reset forge state from scratch

Preserve the existing state in the plan ledger directory, remove only `.img2threejs/state.json`, then run:

```bash
python3 /Users/tonyyang/.claude/skills/img2threejs/forge/state.py init \
  --state .img2threejs/state.json \
  --reference artifacts/exhibits/mmx2-sigma-virus/references/sigma-front-green-ostation.png \
  --profile generic \
  --spec artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json
```

The forge state must report `status=active`, `step=image-analysis`, and a fresh loop count.

## Task 3 — Ask forge for the next mandatory action and verify outputs

Run:

```bash
python3 /Users/tonyyang/.claude/skills/img2threejs/forge/next.py \
  --state .img2threejs/state.json \
  artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json
```

Verify:

- manifest has 42 entries;
- 42 PNG crops exist;
- `BREAKDOWN.md` exists;
- state is active and the next mandatory step is recorded in the ledger.

## Rerun command

```bash
python3 artifacts/exhibits/mmx2-sigma-virus/spec/green_breakdown_v3.py && \
  cp .img2threejs/state.json .superpowers/sdd/PLAN_FROM_SCRATCH_GREEN/state.before-from-scratch-$(date +%Y%m%d_%H%M%S).json 2>/dev/null || true
```

For a complete reset, execute Tasks 1–3 in order; do not use the convenience command above as a substitute for the explicit backup/reset sequence.

## Completed 1.5.1 continuation

The user-authorized continuation after the original intake checkpoint completed the full locked pipeline through `optimization-pass` using img2threejs `v1.5.1` (`dede5909be4e494b228c801a55dda47439143932`). The continuation evidence is recorded in `spec/gates/`, including strict validation, material, Tier-1, turntable, interior-difference, attachment, chirality, interaction runtime, optimization, and final part-coverage gates. The live exhibit model is `src/utils/sigmaVirusHead/createSigmaVirusHead.ts`; `src/createObjectModel.ts` is the regenerated 1.5.1 forge factory artifact.
