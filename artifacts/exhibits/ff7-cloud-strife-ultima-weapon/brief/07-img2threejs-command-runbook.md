# img2threejs 1.4.4 Command Runbook

This runbook follows the reviewed public `SKILL.md` workflow. Run commands from the img2threejs skill root. The checked-out `forge/next.py` output remains the exact next-step authority.

## 1. Copy the review package into the reconstruction workspace

Keep these relative paths available:

```text
assets/artwork-sword-crop.webp
assets/artwork-sword-transparent.webp
references/01-authority-artwork.webp
references/02-community-draft.webp
references/03-community-colored-model.webp
```

Use `assets/artwork-sword-crop.webp` as the pipeline reference. The transparent file is for review/render comparison, not the primary image probe.

## 2. Initialize resumable local state

```bash
python3 forge/state.py init \
  --state .img2threejs/state.json \
  --reference assets/artwork-sword-crop.webp \
  --profile generic

python3 forge/next.py --state .img2threejs/state.json
```

Run `forge/next.py` again at every fresh start, resume, and correction loop. A stopped state or exit code `3` is a hard stop.

## 3. Record the artwork-first analysis

Use `docs/05-reference-analysis.md` as the starting evidence, then expand it with measured landmarks from the crop.

```bash
python3 forge/state.py mark image-analysis \
  --state .img2threejs/state.json \
  --evidence docs/05-reference-analysis.md
```

Only mark a step after its evidence file exists. For later steps, use the exact step ID printed by `forge/next.py`.

## 4. Probe and detail inventory

```bash
python3 forge/stage1_intake/probe_image.py \
  assets/artwork-sword-crop.webp

python3 forge/stage1_intake/build_detail_inventory.py \
  assets/artwork-sword-crop.webp \
  --mode grid-3x3 \
  --out-dir detail-inventory \
  --out detail-inventory.json
```

Map every identity-defining detail to a real `component.localFeatures` or `material.localOverrides` entry. Do not leave details only in prose.

## 5. Pre-spec assessment

```bash
python3 forge/stage2_spec/new_pre_spec_assessment.py \
  "FF7 Ultima Weapon" \
  --image assets/artwork-sword-crop.webp \
  --complexity complex \
  --spec-query "faceted translucent crystal sword layered blade inset gemstone guard drivers leather grip" \
  --out assessment.json
```

Review the generated `qualityContract`, object class, local spec search evidence, and seeded detail inventory before continuing.

## 6. Create and refine ObjectSculptSpec

```bash
python3 forge/stage2_spec/new_sculpt_spec.py \
  "FF7 Ultima Weapon" \
  --image assets/artwork-sword-crop.webp \
  --assessment assessment.json \
  --out object-sculpt-spec.json
```

Replace generic components with the exact hierarchy in `docs/03-component-interface-contract.md`. Add:

- four blade components;
- four hilt part types;
- a four-instance driver repetition system;
- sockets/anchors for assembly;
- material regions and gradients;
- subject-specific feature review targets;
- per-region confidence and hidden-depth assumptions.

## 7. Validate before code generation

```bash
python3 forge/stage2_spec/validate_sculpt_spec.py \
  object-sculpt-spec.json

python3 forge/stage2_spec/validate_sculpt_spec.py \
  object-sculpt-spec.json \
  --strict-quality
```

If strict quality blocks generation, refine the subject-specific spec. Do not use `--allow-nonstrict` for the production reconstruction.

## 8. Locked build passes

```bash
python3 forge/stage3_build/orchestrate_passes.py \
  status object-sculpt-spec.json

python3 forge/stage3_build/generate_threejs_factory.py \
  object-sculpt-spec.json \
  --out src/createUltimaWeaponModel.ts
```

Generate only the currently unlocked pass. After rendering, create one reference-versus-render sheet and append the review using the repository's current commands and the exact evidence paths printed by `forge/next.py`.

## 9. Material evidence

Create verified crops for these visible regions before material analysis:

- outer pale crystal shell;
- outer white shell edge sharpening;
- inner purple insert remains unsharpened;
- inner purple insert;
- dark triangle;
- red/magenta gem;
- muted-gold guard metal;
- wine-red drivers;
- dark leather grip;
- metallic pommel.

For each crop, use the repository's current material analysis command, for example:

```bash
python3 forge/stage1_intake/analyze_texture.py \
  <verified-region-crop> \
  --spec object-sculpt-spec.json \
  --material-id <material-id> \
  --in-place
```

The artwork uses mostly controlled gradients and flat regions, so procedural/vertex gradients are appropriate. Do not project the whole artwork onto wrong geometry to hide structural errors.

## 10. Multi-view and attachment gates

After browser renders and mesh export are available, run the repository gates with real capture paths:

```bash
python3 forge/stage4_review/turntable_gate.py \
  --capture 0=front.png \
  --capture 90=right.png \
  --capture 180=rear.png \
  --capture 270=left.png \
  --json

node runtime/scripts/export_mesh_geometry.mjs \
  --url <preview-url> \
  --out meshes.json

python3 forge/stage4_review/self_intersection.py \
  meshes.json \
  --json

python3 forge/stage4_review/attachment_anchor.py \
  object-sculpt-spec.json \
  --measured measured-anchors.json \
  --json
```

Front-only similarity is not enough. Side/rear views must remain conservative and structurally valid.

## 11. Final evidence

Keep these artifacts together:

```text
.img2threejs/state.json
assessment.json
detail-inventory.json
object-sculpt-spec.json
src/createUltimaWeaponModel.ts
review-history / pass evidence
comparison sheets
front / side / rear / three-quarter renders
transparent render
exploded view
landmark and silhouette metrics
assumptions log
```

Every correction report must state:

1. exact values or parameters changed;
2. why they changed;
3. evidence path;
4. what still does not match.
