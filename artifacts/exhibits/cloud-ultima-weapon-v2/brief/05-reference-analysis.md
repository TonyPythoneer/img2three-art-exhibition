# Reference Analysis

## 1. Authority artwork

File: `references/01-authority-artwork.webp`

Use it for:

- overall silhouette and length ratios;
- four visible blade layers;
- four red driver rods;
- guard compactness;
- overlap order between purple insert, dark triangle, gem, guard, and grip;
- color placement;
- low-poly/faceted visual language.

Observed front-layer order near the root:

```text
camera
  -> rootDiamondGem
  -> darkCoreTriangle
  -> purpleEnergyInsert
  -> outerCrystalShell / blade socket
  -> guardCore
```

This order describes the artwork-facing overlap, not necessarily literal physical penetration. Use small depth offsets to avoid z-fighting.

## 2. Community draft

File: `references/02-community-draft.webp`

Use it only to understand that the creator considered the blade, central gem, lateral rods, side carriers, grip, and tail as separable shapes. It is a rough hand drawing and cannot override artwork proportions, rod count, or exact outline.

## 3. Community colored model

File: `references/03-community-colored-model.webp`

Use it as secondary evidence that the object can be built from faceted low-depth solids. It may help infer side thickness and central ridge behavior. Its lighting, proportions, shadows, and exact geometry are not authoritative.

## Positive-source convergence policy

Use only references that contribute affirmative evidence about silhouette, component separation, depth, faceting, or material placement. Do not include failed interpretations in the working reference set. Convergence should come from the authority artwork, measured boundaries, component contracts, and conservative PS1 low-poly geometry.

## Unseen-depth policy

The supplied artwork does not fully define back-side geometry. Therefore:

1. Keep depth shallow and mechanically plausible.
2. Use mirrored or near-mirrored rear geometry unless the artwork proves otherwise.
3. Never let hidden-depth invention alter the front silhouette.
4. Record every depth assumption in the component manifest.
5. Prefer a simple low-poly solution over detailed invented machinery.

## Extra geometry reading

- The artwork implies that the pale outer shell behaves like the actual cutting blade: it narrows to a clear tip and should read as beveled toward its side edges.
- The inner purple crystal behaves like an inset core, not a separately sharpened blade.
