# Clean Sigma head sculpt specification

## Coordinate contract

`X` left/right, `Y` bottom/top, `Z` rear/front. `+Z` is the face. The normalized head height is
1.0 and the origin is the assembled bounds centre. `X=0` is a coordinate reference, not a
symmetry constraint; left/right and front/rear surfaces are independently parameterized.

## Component hierarchy

```text
SigmaHead
├── Crown
├── Forehead
├── TempleShellL/R
├── CheekShellL/R
├── FaceCavity
├── EyePlateL/R
├── MidFaceBridge
├── LowerFaceJaw
├── ChinTabL/R
└── RearShell
```

The root integration function must author no geometry. Each named component owns its geometry,
material, and inspection identity.

## Geometry contract

- Use explicit low-poly rings and planar custom volumes, never sphere-scale as the base.
- Keep crown and broad side planes sparse.
- Spend additional edges only on silhouette transitions, cavity boundaries, eyes, cheeks, and jaw.
- Use actual recessed eye geometry; do not use a texture plane.
- Keep the rear as the simplest continuation supported by oblique views; do not force front/rear
  symmetry or invent unsupported rear decorations.
- Keep fills in the reference navy and draw crease edges as the visible subject.
- Use deterministic but independently parameterized left/right components; sharing a generator is
  allowed, but never copy one side's measured dimensions into the other without evidence.

## Pass contract

1. Structural cage: crown, forehead, independent left/right temples and cheeks, jaw, chin, rear shell.
2. Major planes: cavity, bridge, side-to-jaw transitions, crown-to-rear transition.
3. Facial geometry: eyes and face relief.
4. Wire topology and depth colour.
5. Canonical multi-view review and bounded correction.

## Validation contract

Fresh captures must include front, front-left/right 30° and 60°, left/right, rear-left/right 30°
and 60°, rear, top, and bottom. Numeric gates cover the authoritative front silhouette, eye
footprint, yaw width ratio, per-part coverage, and 14-part explodability. Canonical rear/top/bottom
views are qualitative because the source does not label their exact camera poses.

A passing numeric gate never overrides a visible mismatch. Every correction records what changed,
why, and which view supplied the evidence.
