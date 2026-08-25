# Sigma Virus From-Scratch Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> **This repo overrides the subagent option:** AGENTS.md forbids spawning subagents/orchestration without an explicit user order. Execute INLINE with superpowers:executing-plans.

**Goal:** Rebuild the mmx2-sigma-virus exhibit's Three.js model from scratch through the img2threejs forge pipeline (fresh state → assessment → spec → generated factory → gates), discarding the current hand-written model.

**Architecture:** The sprite sheet (`artifacts/exhibits/mmx2-sigma-virus/references/sigma-wireframe-sheet.png`, 610×2644, bg `#000029`) is the only geometry/colour authority. The img2threejs forge (`/Users/tonyyang/.claude/skills/img2threejs`) enforces staged passes and deterministic gates; its generator emits the factory TypeScript that replaces `src/utils/sigmaVirusHead/createSigmaVirusHead.ts` while preserving the existing viewer contract in `mountSigmaVirusViewer.ts`.

**Tech Stack:** Python 3.10+ stdlib (forge), Three.js + Vue/Nuxt exhibit page, headless-browser capture for gate renders.

## Global Constraints

- Reference: `artifacts/exhibits/mmx2-sigma-virus/references/sigma-wireframe-sheet.png` — never regenerate, never edit.
- Palette (colour authority): wire bright `#10D830`, wire dim `#10B010`, eyes `#E05000`, ground `#000029`.
- Geometry authorities: front frame (63,1811); green yaw frame ~(496,2573); top frame (12,2247); side frame (142,1505).
- Depth guess G1 default: depth ≈ 1.3 × width (foreshortened lower bound 1.25).
- Forge runs from the skill root; pure stdlib; never let a script score visuals.
- Correction budget: `--max-per-pass 3 --max-total 8`; never loosen an assertion to pass.
- Every number reported traces to a file under `artifacts/exhibits/mmx2-sigma-virus/spec/`.
- Keep page contract: `createSigmaVirusHead(): THREE.Group` named parts, `SIGMA_PARTS`, `userData.provenance`; mount returns `setExplode` so `ExhibitStage` shows the explode control.
- Gate evidence lives under `artifacts/exhibits/mmx2-sigma-virus/spec/`; nothing heavy enters `src/assets/`.

---

### Task 1: Fresh forge state

**Files:**

- Create: `.img2threejs/state.json` (repo root)

- [ ] **Step 1: Init**

```bash
cd /Users/tonyyang/.claude/skills/img2threejs && python3 forge/state.py init \
  --state /Users/tonyyang/git/personal/img2three-art-exhibition/.img2threejs/state.json \
  --reference /Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/references/sigma-wireframe-sheet.png \
  --profile generic \
  --max-per-pass 3 --max-total 8
```

Expected: state file created, first mandatory step printed.

### Task 2: Intake evidence marks

**Files:**

- Create: `artifacts/exhibits/mmx2-sigma-virus/spec/admission.json`

- [ ] **Step 1: Reference admission gate**

```bash
cd /Users/tonyyang/.claude/skills/img2threejs && python3 forge/stage1_intake/check_reference_admission.py \
  <repo>/artifacts/exhibits/mmx2-sigma-virus/references/sigma-wireframe-sheet.png --json out
```

- [ ] **Step 2: Mark image-analysis** with evidence `spec/fresh-zoom-scan.md` (+ probe already run: technicalSuitability=conditional, extreme-aspect warning explained by sprite-sheet layout).

### Task 3: Pre-spec assessment + detail inventory

**Files:**

- Create: `artifacts/exhibits/mmx2-sigma-virus/spec/assessment.json`, `detail-inventory.json`, `detail-crops/`

- [ ] **Step 1:** `new_pre_spec_assessment.py "Sigma Virus Head" --image <sheet> --complexity moderate --out assessment.json` (object domain; fills detailInventory seed).
- [ ] **Step 2:** `build_detail_inventory.py <sheet> --mode grid-3x3 --out-dir detail-crops --out detail-inventory.json`.
- [ ] **Step 3:** Edit `assessment.json`: primaryDomain `object`; every inventory detail maps to a component/material entry (eye outlines, crown ridge seam, cheek lobe overlap seam, nose ridge, chin notch, mouth band, wire dim/bright two-tone).

### Task 4: Sculpt spec + strict validation

**Files:**

- Create: `artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json`

- [ ] **Step 1:** `new_sculpt_spec.py "Sigma Virus Head" --image <sheet> --assessment assessment.json --out object-sculpt-spec.json`
- [ ] **Step 2:** Author component tree (part table = tree names; measured px → units where 69 px = 1.0 height):
      crown, forehead, templeShellL/R, cheekShellL/R, faceCavity, eyePlateL/R, midFaceBridge, lowerFaceJaw, chinTabL/R, rearShell — silhouette rows and depths from `measurements.json` + `zoom/geom_63_1811.png` readings; depth/width 1.3 (G1); eyes recessed (G2); chin tabs independent (G3); rear symmetric plain facets (G4).
- [ ] **Step 3:** Replace featureReviewTargets: critical = eye-placement, cheek-lobe-width-band, crown-facet-ridge, jaw-taper, silhouette-front-IoU; important = mouth-band, chin-notch, wire-two-tone.
- [ ] **Step 4:** `validate_sculpt_spec.py` then `--strict-quality` — both must PASS before codegen.

### Task 5: Generate factory, preserve page contract

**Files:**

- Modify: `src/utils/sigmaVirusHead/createSigmaVirusHead.ts` (replace wholesale)
- Unchanged: `mountSigmaVirusViewer.ts`, `src/pages/mmx2-sigma-virus/index.vue`

- [ ] **Step 1:** `generate_threejs_factory.py object-sculpt-spec.json --out src/utils/sigmaVirusHead/createSigmaVirusHead.ts`
- [ ] **Step 2:** Adapt exports to contract (`createSigmaVirusHead(opts?: {scale?: number})`, `SIGMA_PARTS`, named meshes, edges `LineSegments` with `explodeWithParent`, `userData.provenance`) — hand refinement carried back into spec JSON, not only into TS.

### Task 6: Build proof

- [ ] **Step 1:** `npx nuxi typecheck` (or repo's typecheck script) — zero errors.
- [ ] **Step 2:** Serve dev build; confirm fresh render differs from old model (crown ridge + lobe plates visible).

### Task 7: Deterministic gates

**Files:**

- Create: `artifacts/exhibits/mmx2-sigma-virus/spec/gates/` (captures + json)

- [ ] **Step 1:** Capture 13 preset views via headless browser driving `window.__sigmaViewer.setPreset` (front, ±30°, ±60°, left, right, rear, top, bottom) at 480×690 (48×69 × 10).
- [ ] **Step 2:** `diagnose_render.py` Tier-1 (silhouette IoU/proportion/symmetry) recorded `--in-place`.
- [ ] **Step 3:** `diagnose_render_multi_angle.py` fixed + ≥2 orbit views — no `degenerate-view`.
- [ ] **Step 4:** `make_comparison_sheet.py` reference vs render → inspect visually.
- [ ] **Step 5:** `orchestrate_passes.py check` for the pass.

### Task 8: Review records + bounded corrections

- [ ] **Step 1:** `append_review.py` with fidelity + verdict `continue|refine-spec|refine-code`.
- [ ] **Step 2:** Corrections ≤3 per pass / ≤8 total; each iteration re-runs Task 7 gates; never loosen thresholds.
- [ ] **Step 3:** `check_part_coverage.py` — every specified component built, none fused.

### Task 9: Final report

- [ ] Side-by-side reference vs final render at 8× NEAREST; all gate numbers incl. failures; guess list G1–G5 restated; files + rerunnable commands listed.

## Self-Review

- Spec coverage: Tasks 1–9 cover init→intake→assessment→spec→codegen→build→gates→corrections→report; page wiring untouched by design (contract preserved).
- Placeholders: none — every step names exact paths/commands; measured values live in referenced artifact JSONs, not invented here.
- Type consistency: factory export names match `mountSigmaVirusViewer.ts` imports (`createSigmaVirusHead` only; `SIGMA_PARTS` re-exported for tests).
