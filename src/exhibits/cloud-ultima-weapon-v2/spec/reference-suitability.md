# Reference suitability verdict

Rubric: `grimoire/intake/validation_rubric.md`. Subject: FF7 Ultima Weapon,
`assets/artwork-sword-crop.webp` (210×434).

## Verdict: **conditional → low-poly procedural reconstruction**

### Pass criteria met

- One obvious target object, isolated on white; foreground coverage 0.233, largest connected
  component 0.9992 of the mask (no fragmentation).
- A single strong silhouette with unambiguous boundaries — the source is a flat-shaded render,
  so every edge is a hard 1-px transition rather than a soft photographic contour.
- All nine visually distinct materials are visible and separable by hue/value
  (see `spec/image-analysis.md` Layer 6).
- Every part maps to a procedural primitive: extruded profiles, prisms, bipyramids,
  truncated cones, instanced bars. No smoke, liquid, caustics, or lace.

### Conditional, not pass

- **One view only, and the object is not rotationally symmetric.** Depth (`Z`) is entirely
  unobservable. Handled by the contract's shallow-depth policy (shell ±14, guard ±20) and
  mirrored rear geometry; every depth choice is logged as an assumption (U1).
- **Occlusion at the hilt.** The blade root, the four driver roots, and most of
  `darkCoreTriangle` are hidden behind the guard. Reference 03 supplies conservative
  front-view evidence where the authority crop is silent (U2, U3, U4).
- **Low resolution.** 210×434 for a 970-unit-tall subject means ~2.2 normalized units per
  pixel; sub-10-unit features cannot be resolved. This is acceptable because the subject is a
  PS1-era asset whose real geometry has no sub-10-unit features.

### Not rejected

The target is neither ambiguous nor a scene, no important macro shape is cropped, and the
brief explicitly asks for a low-poly procedural rebuild rather than mesh extraction or
manufacturing-grade dimensions.

### Requested-but-unavailable input

Front, side, and rear views would remove U1/U6 entirely. They do not exist for this asset;
reference 03 (a community rebuild, near-orthographic front) is admitted as *secondary* evidence
only, per `brief/05-reference-analysis.md`'s priority table.

## Admission record

`spec/reference-admission.json` — admitted, viewpoint `artwork-three-quarter`,
pHash `13040450875322664320`, no duplicate.
