# Character contract read — what the three grimoire documents change for THIS model

Evidence for the `character-contract-read` state gate. Read in full:

- `grimoire/character/reconstruction.md` (proportions, landmarks, pose, materials)
- `grimoire/character/likeness_maximization.md` (projection-first pipeline)
- `grimoire/character/structure_decomposition.md` (the nine-layer ontology)

Everything below is a decision, not a summary. Numbers come from `spec/landmarks.json`
(§0.6: no number is quoted from prose).

## 1. Proportion system — head-units are NOT the authority here

`reconstruction.md` measures everything in head-units. This model does not, and the
reason is measured: the head's top is **clipped in all four orthographic views**
(row-0 figure-pixel counts front 6 / back 4 / left 4 / right 6), so head height is a
derived quantity, not a measured one. `landmarks.json.totalHeight` extrapolates the
hair tip from left.webp's two straight spike edges (max residual 2.37 px / 1.84 px,
`clippedAbovePx` 9.31, `totalHeightPx` 854.31).

Adopted instead: the **sole→chin anchor**, `spanNormalized` 0.71637, because both
landmarks are complete in all five references. Head-units are reported below for the
contract's sake but are not used as a tolerance anywhere.

| reconstruction.md field | value | source |
|---|---|---|
| chin (sole→chin anchor) | 0.71637 | `normalization["sole->chin"].spanNormalized` |
| shoulderLine | 0.70621 (front) | per-view landmark |
| shoulderWidth | 0.37978 | `dimensions.shoulderWidth` |
| hipWidth | 0.28325 | `dimensions.maxHipWidth` |
| head+hair above chin | 0.28363 = 1 − 0.71637 | derived |

Style axis: with hair, head-block ≈ 0.284 of total height → **≈3.5 HU**, the
figurine end of `reconstruction.md`'s scale. Consistent with the subject being a
vinyl action figure, not a person.

⚠ `reconstruction.md`'s "if the image crops the legs or feet, mark inferred" clause
applies here to the **crown**, not the feet. `hairTopVisible` is recorded per view
(front 1.0326 / back 1.0126 / left 0.9833 / right 1.0878, spread 0.1045) and every one
of those is a clipped read — the adopted 1.000 is the extrapolation, and the spread is
why `measurementUncertainty` is 0.05447 rather than the 0.01374 RMS.

## 2. Facial landmark layout — deferred to Stage 2, and it is a DECAL

`reconstruction.md` §"Facial Landmark Layout" wants eyeLine / eyeSpacing / noseBase /
mouthLine as head-box-normalized coordinates. §2 c) of the prompt rules eyes, pupils and
brows out of geometry: they are printed flat art, built as ONE `faceDecal` CanvasTexture
(shape code S-27, material code M-02, the only textured surface in the model).

So the landmark layout is **texture registration data, not geometry data**. It is
authored at Stage 2 against the `face` entry of `head.userData.faceGroups`, and Stage 1
does not read it. Nothing in Stage 1 is blocked on it.

## 3. Pose / skeleton — there is NO skeleton, and that is a spec decision

`reconstruction.md` §"Pose / Skeleton" and `structure_decomposition.md`'s whole rig
column assume a `SkinnedMesh`. Prompt §1.4: **the pose is baked into the parts.** This is
a fixed-pose toy with no animation requirement; each part's local origin is its own upper
socket as posed, so Stage 1B assembly is pure translation.

Consequence, stated so it cannot be mistaken for an omission:

- No bones, no `W(p)` weight function, no L3 weight overrides, no pose sweep.
- `structure_decomposition.md` checklist items **6–14** (bind-pose scale, four-influence
  cap, weight sums, L3 forced weights, pose sweep, joint centres, L4 clipping, colliders)
  are **not applicable**. They measure a rig this model does not have.
- Items **1, 2, 3, 4, 5, 10, 15** remain live and are enforced elsewhere: layer
  assignment (below), the L-1 scaffold (`landmarks.json`), degenerate faces and coincident
  seams (§5.5's `‖delta‖ < 1e-6` socket assertion), naming (§5.6), evidence refs (§0.6 and
  `spec/audit_records.py`).

The measured pose angles that get baked in instead of rigged:

| angle | value | landmarks.json path |
|---|---|---|
| upper-arm abduction L / R | 18.667° / 16.106° | `poseAngles.figureLeftUpperArm.abductionDeg`, `...Right...` |
| upper-arm forward lean L / R | 1.629° / 10.426° | `...forwardLeanDeg` |
| elbow break L / R | 11.097° / 21.771° | `poseAngles.figureLeftElbowBreakDeg`, `...Right...` |
| foot splay L / R | 47.158° / 44.406° | `poseAngles.footSplayDeg` |

⚠ The arm angles are **3D direction vectors solved from the front AND side projections**,
per §3.1. They are not front-view readings.

## 4. Likeness maximization — the projection route is REFUSED, with a reason

`likeness_maximization.md` is the default high-likeness path for the `character` domain,
and its central claim is that hand-authored primitives cannot reach high likeness — put
the photo's own pixels on the mesh instead. That claim is about **photographs of people**.

This subject is a **flat-shaded vinyl polygon figure**. Its identity is carried by facet
angles and hard creases, and the entire model has exactly two material codes (M-01 matte
vinyl, M-02 the printed face). Projection would:

- bake the product shot's own facet shading into the albedo, which is the specific thing
  `likeness_maximization.md` §(c) exists to prevent, and
- destroy the one identity signal the facet gate (`spec/facet-gate.json`, angle 42°,
  threshold 0.3357) is built to measure.

Decision: **route = procedural, exactness = image-only.** The single textured surface is
the Stage 2 `faceDecal`, authored as a CanvasTexture from measured landmark positions —
not a camera-solved projection of a reference crop. `solve_camera_pose.py`,
`delight_albedo.py` and `bake_projected_texture.py` are not run.

Honesty note, per §"Honesty Note": four orthographic views plus one three-quarter do
cover every side of this figure, so the usual "hidden sides are unobservable" caveat is
weaker here than for a single photo. What remains unobservable is listed in the guess
list (§11 plus the three Stage 0 additions), not hand-waved.

## 5. Layer assignment — every Stage 1 part, one primary layer each

`structure_decomposition.md` checklist item 1: every component maps to exactly one
primary geometry layer. Without a rig the layer no longer selects a skinning path, so it
selects **build method and boundary rule** only.

| part | primary | modifiers | why |
|---|---|---|---|
| head, neck, chest, waist, pelvis | L0 | L-1 | continuous central mass |
| upperDeltoidL/R, lowerDeltoidL/R, backArmL/R, frontArmL/R | L0 | L-1 | limbs are core volume |
| thighL/R, kneeL/R, calfL/R | L0 | L-1 | the pants ARE the leg silhouette here — there is no separate skin leg under them (§4 "bloomer pants, not fitted trousers"), so they are core volume, not an L4 shell |
| ankleL/R (boot cuff) | L4 | — | offset shell: its section is LARGER than the pant tube it swallows, with a visible step all round |
| soleL/R | L3 | — | wholly inside one region, does not cross any joint |
| pauldronL (Stage 3) | L4 | — | armour plate lying over upperDeltoidL |
| hairCap, 9 spikes (Stage 2) | L3 | — | rigid masses on the skull; `structure_decomposition.md` explicitly forbids strand-level hair and forces it into solid masses |
| earL/R (Stage 2) | L3 | — | does not cross a joint; the concha is not modelled, so no L-Void |
| faceDecal (Stage 2) | — | L5 on head | zero geometric footprint, `userData.explodeWithParent = true` |

⚠ Two departures from the document, both deliberate:

1. **No L-Void anywhere.** `structure_decomposition.md` builds ears with a concha cavity
   and mouths with a subtracted bag. This figure has neither: §2 c) rules the face to a
   decal, and the ears are triangular prisms (S-16, `triWedge`). No SDF, no CSG, no
   marching cubes — every part is an authored `BufferGeometry`, so the build DAG's
   subtraction choke point (step 3) does not exist.
2. **thigh/knee/calf as L0, not L4.** Classified by the document's own test — "does this
   part cross a joint?" — they would still be L0; but the stronger reason is that they are
   the outermost surface, not an offset over anything.

## 6. Materials — `reconstruction.md`'s recipes do not apply

The document's skin / hair / eyes / cloth recipes assume a stylized-realistic character:
soft roughness, rim light, glossy eye spheres with catchlights, fold-line creasing.

This model has **two material codes total** (§2), both `flatShading: true`,
`metalness: 0`, `roughness: 0.85`, no maps except the face. All variation lives on the
COLOUR axis, which means Stage 3's job is sampling colour, not tuning material. Explicitly
NOT built: glossy eye spheres, catchlights, rim/backlight terms, normal or bump maps.

Stage 1 goes further and carries no colour at all: one shared M-00 mannequin grey
(`0xb0b0b0`) instance across all 23 parts.
