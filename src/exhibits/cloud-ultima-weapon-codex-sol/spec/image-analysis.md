# Codex Sol Ultima Weapon — image analysis

## 1. Identification and classification

- Observation: one fantasy greatsword-like object on a near-white background; no secondary object is present.
- Classification: bladed game prop, `primaryDomain: object`, confidence `0.99`.
- Intended output: stylized real-time browser prop with explodable and selectable parts.

## 2. Overall form and silhouette

- The object is a long, thin assembly with one dominant shaft axis and a bilateral blade envelope.
- The visible blade envelope is an elongated extruded profile: narrow near the guard, wider through its lower half, then tapering to a rounded asymmetric point.
- The grip continues along the shaft axis below the guard and is cropped by the bottom image boundary.
- The reference is a shallow three-quarter projection rather than an orthographic view; the exact object-space thickness is not observable.

## 3. Macro → meso → micro decomposition

- Macro `bladeAssembly`
  - Meso `outerShell`: pale continuous blade envelope.
  - Meso `purpleCore`: inset purple blade with a pointed top and two lower prongs.
  - Meso `magentaSpine`: narrow red-violet wedge rising from the guard into the core.
  - Micro: faceted longitudinal color bands and narrow lower-edge transitions.
- Macro `guardAssembly`
  - Meso `centralHub`: dark connector around the shaft.
  - Meso `leftGuardWing` and `rightGuardWing`: dark polygonal blocks with olive lower fittings.
  - Meso `rodFan`: three narrow crimson rods on each lateral side.
  - Micro: darker rod bases, lighter outer faces, and small pale connector bands near the blade root.
- Macro `handleAssembly`
  - Meso `grip`: long dark rectangular/cylindrical shaft.
  - Micro: a narrow highlight band along the visible front-lateral face.

## 4. Spatial relationships

- `<outerShell, encloses, purpleCore>` by overlap; the shell extends beyond the core on both lateral edges and above its tip.
- `<purpleCore, embedded-in, outerShell>` with its lower prongs terminating immediately above the guard.
- `<magentaSpine, overlaps, purpleCore>` along the shaft axis and connects the core to the central hub.
- `<guardAssembly, separates, bladeAssembly+handleAssembly>` through a central socket around the shaft.
- `<rodFan, attached-to, centralHub>`; the six rods radiate laterally from a center slightly below the blade root.
- `<handleAssembly, socketed-into, centralHub>` and continues below the image crop.

## 5. Materials and surface

- `outerShellMaterial`: dielectric, pale blue-white albedo, semi-translucent appearance, medium-to-high roughness, no observable micro-relief.
- `purpleCoreMaterial`: dielectric or coated surface, deep blue-violet to vivid violet longitudinal variation, satin roughness, opaque in the supplied pixels.
- `magentaSpineMaterial`: dark red-violet albedo, satin finish, opaque.
- `guardMaterial`: near-black/gunmetal albedo, medium roughness, opaque.
- `rodMaterial`: dark crimson albedo with red face variation, medium roughness, opaque.
- `fittingMaterial`: muted olive/bronze albedo, medium-high roughness, opaque; metalness is uncertain because the reference contains no diagnostic highlight.
- `gripMaterial`: near-black albedo, medium roughness, opaque.

## 6. Color and finish

- Outer shell: very high value, low saturation blue-grey with slightly darker lateral edges.
- Core: dark blue-violet at its upper/left facets, increasing to brighter violet along the lower/right facet.
- Spine: low-value red-violet.
- Rods: low-value crimson with slightly brighter red outward faces.
- Guard: near-black neutral surfaces with muted olive fittings at the lower ends.
- The reference is flat-shaded and low resolution; apparent edge steps are raster aliasing, not surface relief.

## 7. Identity-defining features

1. A large pale outer blade shell surrounding a narrower purple inner blade.
2. The purple core's pointed top and two lower prongs around a central magenta spine.
3. Six crimson rods forming bilateral three-rod fans from a low shared radiation center.
4. Two dark guard wings with downward olive polygonal fittings.
5. The long dark grip aligned with the blade axis.

These five systems are critical review targets for silhouette, component structure, and material separation.

## 8. Uncertainty and single-image limits

- Hidden: all rear faces, internal construction, and the complete handle/pommel.
- Occluded: rod attachment sockets behind the guard wings and the blade-to-guard joint.
- Uncertain: exact shell transmission, metalness of olive fittings, cross-section depth, bevel radii, and whether apparent face-color changes are material variation or baked lighting.
- Approximation rule: use conservative symmetric back geometry and shallow extrusions; do not invent engravings, fasteners, or mechanical internals.

## Suitability verdict

`conditional-pass`: the target has one clear silhouette and a procedural primitive path, but the low-resolution single view cannot support exact thickness or hidden-side reconstruction. The accepted target is an approximate/stylized browser prop, not manufacturing geometry or exact mesh extraction.
