# English Master Prompt

Copy everything below into the main implementation agent after the img2threejs repository and this review package are available in the same workspace.

---

## BEGIN PROMPT

You are the lead geometry and integration agent for an artwork-faithful Three.js reconstruction of the **Final Fantasy VII Ultima Weapon** shown in `references/01-authority-artwork.webp` and isolated in `assets/artwork-sword-crop.webp`.

Your job is not to design a new sword. Your job is to convert the artwork into a clear component hierarchy, dispatch isolated subagents, assemble their outputs, and validate the result against the artwork.

### 1. Start through the real img2threejs skill workflow

The reviewed skill is img2threejs `SKILL.md` version 1.4.4. Use the checked-out repository as runtime authority.

1. Initialize the generic resumable state once:

```bash
python3 forge/state.py init \
  --state .img2threejs/state.json \
  --reference assets/artwork-sword-crop.webp \
  --profile generic
```

2. At every start, resume, and correction loop, run this before touching implementation code:

```bash
python3 forge/next.py --state .img2threejs/state.json
```

3. Obey a hard stop or exit code `3`. Never reconstruct progress from chat memory.
4. Use the repository's real `ObjectSculptSpec`, `detailInventory`, `qualityContract`, repetition systems, sockets, materials, review history, and generated TypeScript `THREE.Group` factory.
5. Use the actual current schema, file paths, commands, pass locks, and output contracts. Do not invent repository internals.
6. Preserve existing repository patterns and keep each component independently reviewable.

### 2. Reference authority

Use the references with this strict priority:

| Priority | Reference                                                              | Permitted use                                                                                       |
| -------: | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
|        1 | `references/01-authority-artwork.webp` and both extracted sword assets | Authoritative silhouette, proportions, part count, overlap, color placement, and low-poly character |
|        2 | `references/03-community-colored-model.webp`                           | Conservative hidden-depth and faceting hints only where the artwork is silent                       |
|        3 | `references/02-community-draft.webp`                                   | Rough separation and attachment hints only                                                          |

When any reference conflicts with the artwork, follow the artwork.

This is a **PS1-era low-poly weapon**. Prefer clean planar faces, straight or gently faceted transitions, and a compact low-poly silhouette. Do not add ornamental micro-curves, extra grooves, or smoothed modern detail. Derive every visible boundary directly from the authority artwork and the measured landmark data.

### 3. Non-negotiable hierarchy

```text
SwordRoot
├── BladeGroup
│   ├── outerCrystalShell
│   ├── purpleEnergyInsert
│   ├── darkCoreTriangle
│   └── rootDiamondGem
└── HiltGroup
    ├── guardCore
    ├── driverArray
    │   ├── driver01_left_upper
    │   ├── driver02_left_lower
    │   ├── driver03_right_upper
    │   └── driver04_right_lower
    ├── leatherTGrip
    └── metalSpinnerPommel
```

There are exactly **four blade parts** and **four hilt part types**. `driverArray` contains exactly four repeated drivers, two on each side.

### 4. Component specification

#### BladeGroup

| Group      | Part name            | Qty | Color treatment                                           | Suggested colors                                                            | Material                                                                                              | Part description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ---------- | -------------------- | --: | --------------------------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BladeGroup | `outerCrystalShell`  |   1 | Pale translucent gradient with faceted light/shadow zones | highlight `#F8F8FF`; body `#E4E5F3`; shadow `#B8BBD6`; cool edge `#D7D9EE`  | Non-metallic faceted crystal; low roughness; controlled transparency/transmission; flat-shaded planes | The classic broad outer blade. It is a long leaf/spear crystal with a sharp tip, a narrow upper section, and a wider lower body that closes around the blade root. It must remain visibly larger than the purple insert on every side. The **outer crystal shell must be sharpened**: the tip must taper into a clear blade point, and both left/right sides must visibly thin into bevelled cutting edges. From the blade tip looking downward, the shell should read as a wedge-like blade body that contracts toward its edges, not as a blunt slab. Use a shallow, ridged cross-section rather than a flat card or a thick rounded sword. |
| BladeGroup | `purpleEnergyInsert` |   1 | Vertical dark-to-bright violet gradient                   | apex `#19106E`; upper `#2B168F`; middle `#4822C0`; lower glow `#7C3CFF`     | Opaque-to-slightly-translucent energy crystal; subtle emissive response; faceted                      | An inset inner blade. Its top is a small triangular point. Below that point, its sides expand into a long tapered trapezoid toward the guard. It ends above/behind the root gem. It does not reach the outer blade tip and does not fill the outer shell. **Do not sharpen it into a knife edge**. The inner crystal should stay as a faceted inset mass with visible side faces, not a second outer cutting blade.                                                                                                                                                                                                                           |
| BladeGroup | `darkCoreTriangle`   |   1 | Mostly solid deep violet/burgundy with a small gradient   | tip `#210A38`; body `#3A0B43`; lower face `#64123F`                         | Dense opaque crystal; sharper and darker than the purple insert                                       | A narrow, simple upward-pointing triangle laid in front of the lower purple insert. Keep it thin and centered. It is not a long second blade and must not widen into a large central panel.                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| BladeGroup | `rootDiamondGem`     |   1 | Faceted magenta-red crystal gradient                      | highlight `#FF3866`; main `#C0184D`; shadow `#5A0B34`; deep facet `#330820` | Small transparent/faceted gemstone, elongated rhombus or low-poly bipyramid                           | An elongated diamond crystal at the blade root, directly in front of the guard. Its upper point overlaps the dark triangle; its lower point crosses slightly into the guard area. It must read as a gem, not a flat red arrow.                                                                                                                                                                                                                                                                                                                                                                                                                |

#### HiltGroup

| Group     | Part name            |                 Qty | Color treatment                                             | Suggested colors                                                                     | Material                                                 | Part description                                                                                                                                                                                                                                                                                                                      |
| --------- | -------------------- | ------------------: | ----------------------------------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| HiltGroup | `guardCore`          | 1 mirrored assembly | Mostly solid blocks with restrained metal shading           | charcoal `#202126`; dark steel `#353640`; muted gold `#8D8450`; olive gold `#6F6A3D` | Faceted dark metal plus muted gold/olive metal           | The central blade socket and two mirrored side carriers. Each carrier angles outward/downward and ends in a compact gold faceted cap/counterweight. Keep the shapes compact, mechanical, and close to the artwork silhouette. The side carriers should remain narrow, angled, and visually subordinate to the blade and four drivers. |
| HiltGroup | `driverArray`        |         4 instances | Wine-red/magenta rods with dark edges and a small highlight | main `#7C102F`; highlight `#BB2A50`; shadow `#2E0716`                                | Narrow faceted metallic or energy-conductor bars         | Exactly four drivers: two on the left and two on the right. They radiate outward and slightly upward from the guard, in mirrored pairs. They are slim rectangular/faceted rods, not six fins, not a fan of many blades, and not thick cuboids.                                                                                        |
| HiltGroup | `leatherTGrip`       |                   1 | Near-black with subtle value variation                      | base `#111216`; raised wrap `#292A30`; edge `#3B3C43`                                | Rough leather or leather-wrapped dark grip; non-metallic | A straight, narrow grip below the guard. The sword's combined guard-and-grip silhouette reads as a T. Do not add an extra literal T-shaped crossbar. Use a slightly tapered, faceted shaft with restrained wrap ridges or a subtle helical band.                                                                                      |
| HiltGroup | `metalSpinnerPommel` |                   1 | Muted gold metallic gradient                                | highlight `#B8A45C`; main `#958044`; shadow `#5E512D`                                | Faceted metal                                            | A small pointed tail shaped like a compact spinning top/cone. It is centered under the grip, narrower than the grip, and clearly metallic. Do not make it a large sphere or decorative fantasy ornament.                                                                                                                              |

### 5. Canonical coordinate system and proportions

Use a canonical model coordinate system:

- `+Y`: from guard toward blade tip.
- `-Y`: from guard toward pommel.
- `+Z`: front face shown in the artwork.
- `X`: left/right across the guard.
- `guard_center_anchor = (0, 0, 0)`.

Use normalized overall length `1000` units as the initial blockout:

| Measurement                                 | Initial target |
| ------------------------------------------- | -------------: |
| Outer blade tip to guard center             |          `760` |
| Grip from guard center to pommel connection |          `205` |
| Pommel extension                            |           `35` |
| Maximum outer blade width                   |      `175–190` |
| Maximum purple insert width                 |       `85–105` |
| Overall guard span including drivers        |      `330–370` |
| Outer blade maximum depth                   |        `22–32` |
| Guard maximum depth                         |        `35–50` |
| Grip width                                  |        `24–32` |

These values are a starting contract, not permission to ignore the image. Refine them using overlay comparison while preserving the ratios visible in the artwork.

The outer blade should use a small number of intentional cross-sections and longitudinal ridges. The cross-section must narrow from the center ridge toward both side edges so the outer shell reads as sharpened. The tip must also contract into a crisp point. Do not use a rounded capsule profile, a uniformly thick slab, or a blunt front edge. The inner purple insert should remain comparatively blunt/faceted and should not receive the same cutting-edge bevel treatment. Keep the low-poly PlayStation-era visual language.

### 6. Required subagent split

Dispatch independent workers with strict ownership:

1. **Authority/measurement agent** — measures the artwork crop, records landmarks and ratios, and produces no geometry.
2. **Outer crystal agent** — owns only `outerCrystalShell`.
3. **Purple insert agent** — owns only `purpleEnergyInsert`.
4. **Core-and-gem agent** — owns `darkCoreTriangle` and `rootDiamondGem`, but exports them as separate nodes.
5. **Guard agent** — owns only `guardCore`.
6. **Driver agent** — creates one reusable driver geometry and four transforms; owns only `driverArray`.
7. **Grip agent** — owns only `leatherTGrip`.
8. **Pommel agent** — owns only `metalSpinnerPommel`.
9. **Assembly agent** — may change transforms and attachment adapters only; it may not silently remodel a component.
10. **Validation agent** — renders fixed views, overlays the authority crop, and reports errors without changing geometry.

Each geometry subagent must return:

- node name and parent name;
- local pivot;
- local bounding box;
- attachment anchors;
- material IDs;
- vertex/face count;
- assumptions made because depth was not visible;
- a preview render on white and transparent backgrounds.

### 7. Intake, spec, and locked build order

Use the skill's enforced sequence. `forge/next.py` decides the exact next action and pass. The minimum intake/spec commands are:

```bash
python3 forge/stage1_intake/probe_image.py assets/artwork-sword-crop.webp

python3 forge/stage1_intake/build_detail_inventory.py \
  assets/artwork-sword-crop.webp \
  --mode grid-3x3 \
  --out-dir detail-inventory \
  --out detail-inventory.json

python3 forge/stage2_spec/new_pre_spec_assessment.py \
  "FF7 Ultima Weapon" \
  --image assets/artwork-sword-crop.webp \
  --complexity complex \
  --spec-query "faceted translucent crystal sword layered blade inset gemstone guard drivers leather grip" \
  --out assessment.json

python3 forge/stage2_spec/new_sculpt_spec.py \
  "FF7 Ultima Weapon" \
  --image assets/artwork-sword-crop.webp \
  --assessment assessment.json \
  --out object-sculpt-spec.json

python3 forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json
python3 forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json --strict-quality
```

Before code generation, replace generic starter targets with the real identity-defining systems in this prompt. Every visible detail must map to a `component.localFeatures` or `material.localOverrides` entry, not prose only.

For each locked build pass:

```bash
python3 forge/stage3_build/orchestrate_passes.py status object-sculpt-spec.json
python3 forge/stage3_build/generate_threejs_factory.py \
  object-sculpt-spec.json \
  --out src/createUltimaWeaponModel.ts
```

Preserve this visual logic inside the repository's pass locks:

1. authority measurement;
2. blockout silhouette;
3. structure/hierarchy, pivots, sockets, repetition systems, and attachments;
4. form and faceting;
5. material regions and gradients;
6. lighting;
7. interaction/runtime exposure when required;
8. optimization.

Render and compare every unlocked pass. Do not begin material polish while the silhouette or part count is wrong. Record exactly what changed, what still differs, and the evidence path.

### 8. Assembly contract

Use these shared anchors or equivalent names in the repository schema:

```text
outerCrystalShell.root_anchor      -> guardCore.blade_socket_anchor
purpleEnergyInsert.root_anchor     -> outerCrystalShell.inner_insert_anchor
darkCoreTriangle.base_anchor       -> outerCrystalShell.core_anchor
rootDiamondGem.center_anchor       -> guardCore.gem_mount_anchor
guardCore.grip_anchor              -> leatherTGrip.top_anchor
leatherTGrip.pommel_anchor         -> metalSpinnerPommel.top_anchor
guardCore.driver_anchor[0..3]      -> driverArray.driver[0..3].root_anchor
```

Use instancing or shared geometry for the four drivers. Mirroring must preserve face normals and material orientation.

### 9. Artwork matching and camera validation

Build upright. Then create two fixed validation views:

1. **Canonical front orthographic view** — checks symmetry, hierarchy, and proportions.
2. **Artwork-match view** — uses a mild three-quarter angle and approximately the same screen roll/tilt as the supplied artwork.

For the artwork-match view:

- use an orthographic camera or very weak perspective;
- use a white background;
- use soft upper-left lighting to reveal crystal facets;
- avoid cinematic bloom that hides the silhouette;
- align the rendered guard center, tip, grip axis, and driver endpoints to the crop;
- export an overlay/difference image.

Review targets after alignment:

- silhouette IoU: `>= 0.90`;
- tip, guard center, gem center, grip end, and four driver endpoint errors: each `<= 2.5%` of image height;
- blade-to-hilt length ratio error: `<= 3%`;
- exact driver count: `4`;
- exact blade part count: `4`.

### 10. Positive convergence conditions

Accept the reconstruction only when all of the following are true:

- the authority artwork controls the silhouette and component placement;
- the pale outer crystal reads as a shallow, sharpened, faceted blade shell;
- the purple insert remains smaller, inset, and visibly unsharpened;
- the dark core remains a compact centered triangle;
- the root gem reads as a dimensional elongated diamond crystal;
- exactly four slim drivers are present in two mirrored pairs;
- the guard remains compact, narrow, and mechanically connected to the blade socket;
- the grip reads as a narrow leather-wrapped shaft;
- the pommel reads as a small pointed metallic spinner;
- planar PS1-era low-poly geometry is preserved;
- all eight public part types remain independently reviewable before assembly;
- hidden-depth choices preserve the artwork-facing silhouette.

### 11. Final deliverables

Produce:

1. the repository-native object/component spec;
2. one source file per independently owned component or the closest repository-native equivalent;
3. a component manifest with hierarchy, materials, pivots, anchors, dimensions, and assumptions;
4. canonical front, artwork-match, side, and three-quarter renders;
5. a transparent render;
6. artwork overlay and difference images;
7. validation metrics and a short discrepancy report;
8. an exploded view showing all eight part types and four driver instances;
9. `object-sculpt-spec.json`;
10. `src/createUltimaWeaponModel.ts`, returning a `THREE.Group` and exposing the repository-standard runtime nodes/sockets;
11. preserved `.img2threejs/state.json`, review history, and comparison evidence.

Stop and report a conflict rather than silently changing the artwork-defined hierarchy.

## END PROMPT
