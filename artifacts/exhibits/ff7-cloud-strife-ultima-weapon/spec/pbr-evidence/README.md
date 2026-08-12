# PBR evidence — extracted, recorded, deliberately rejected

The runbook requires material analysis to run on verified per-region crops. It did. The output
is kept here in full. **None of it is applied to the model**, and this file is why.

## What ran

`spec/make_material_crops.py` cuts one crop per material region by taking the largest
axis-aligned rectangle fully inside that region's dominant connected component, so no crop can
straddle two materials. Then, per crop:

```bash
python3 forge/stage1_intake/analyze_texture.py <crop> --spec object-sculpt-spec.json \
  --material-id <id> --in-place
python3 forge/stage1_intake/extract_pbr_evidence.py <crop> --out-dir <id> \
  --material-id <id> --target-threshold 0.7
```

| Material               | Extractor verdict | Confidence |
| ---------------------- | ----------------- | ---------: |
| `guardSteelMaterial`   | pass              |      0.820 |
| `purpleInsertMaterial` | pass              |      0.760 |
| `outerCrystalMaterial` | pass              |      0.756 |
| `guardGoldMaterial`    | pass              |      0.726 |
| `gripLeatherMaterial`  | conditional       |      0.634 |

Four of five cleared the 0.70 threshold. The scores are still rejected.

## Why it is rejected

**1. The maps encode rasterization, not relief.** The source is a 210×434 vertex-lit 1997
render. Every region's interior is flat by construction — the extractor's own diagnostics say
so ("low value range weakens height/roughness inference", "low high-frequency detail weakens
normal/roughness inference"). The only high-frequency signal in any crop is the 1-px
antialiasing ring along contours. Applying the extracted height/normal maps would stamp
raster stair-stepping onto the model as physical bumps that the object does not have.

**2. The finish classifier inverted two of the five materials.** `analyze_texture.py --in-place`
wrote:

| Material               | Classified finish | Applied metalness | What the artwork shows                        |
| ---------------------- | ----------------- | ----------------: | --------------------------------------------- |
| `outerCrystalMaterial` | `brushed-steel`   |              1.00 | a pale non-metallic translucent crystal       |
| `guardGoldMaterial`    | `painted-metal`   |              0.00 | the most obviously metallic part in the frame |
| `purpleInsertMaterial` | `painted-metal`   |              0.00 | an emissive-reading energy crystal            |
| `guardSteelMaterial`   | `worn-composite`  |                 — | dark steel, no wear visible anywhere          |
| `gripLeatherMaterial`  | `worn-composite`  |                 — | plausible, but no wear is visible either      |

The classifier is tuned for photographs of real surfaces. Fed flat colour patches, it reads
value spread as brushing and saturation as paint. Its confidence score measures how cleanly it
could fit _some_ finish, not whether that finish is the right one.

**3. The skill's own rule.** `SKILL.md`: _"Never let a script score visuals — that is the
agent's job."_ Confidence ≥ 0.7 is a permission to proceed, not a verdict.

## What is used instead

The PBR scalars in `spec/object-sculpt-spec.json` come from the observation table in
`spec/image-analysis.md` Layer 5, which separates observable fact (flat value bands, one thin
bright edge per driver, no specular hot-spots anywhere else) from inference (the
metalness/roughness numbers themselves). The albedo stops come from the measured HSV census in
Layer 6, sampled with the antialiasing ring excluded.

Every material carries `referencePbr.usable = false` with `verdict: "rejected"` and this
reason inline, so the rejection travels with the spec rather than living only in this file.

## Contents

```
crops/                          one verified crop per material region
<materialId>/pbr-evidence.json  the extractor's full report, verbatim
<materialId>/*_albedo.png       extracted maps, kept unapplied
<materialId>/*_roughness.png
<materialId>/*_normal.png
<materialId>/*_height.png
<materialId>/*_ao.png
```
