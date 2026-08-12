# Subagent Execution Plan

## Goal

Produce an artwork-faithful, independently reviewable component model and assemble it through stable anchors.

## Phase 0 — Repository mapping

The coordinator reads the current img2threejs checkout and records:

- actual spec/schema name;
- component source locations;
- generation commands;
- render/test commands;
- supported model output;
- existing conventions for materials, pivots, and grouped objects.

No geometry work starts until this map is written.

## Phase 1 — Authority measurement

The measurement agent uses `assets/artwork-sword-crop.webp` and records normalized landmarks:

- outer tip;
- outer blade left/right edges at several Y levels;
- purple insert apex and lower corners;
- dark triangle apex/base;
- gem four vertices and center;
- guard center and carrier endpoints;
- four driver roots/endpoints;
- grip top/bottom;
- pommel tip.

The output is a machine-readable landmark file plus a human-readable diagram or table.

Authority measurement must also explicitly estimate where the outer shell begins to taper into side cutting edges and where the tip contracts into its final sharpened point.

## Phase 2 — Independent blockouts

Run these jobs independently:

| Worker        | Output                                                     |
| ------------- | ---------------------------------------------------------- |
| Outer crystal | `outerCrystalShell` blockout                               |
| Purple insert | `purpleEnergyInsert` blockout                              |
| Core and gem  | Separate `darkCoreTriangle` and `rootDiamondGem` blockouts |
| Guard         | `guardCore` with compact mirrored carriers                 |
| Driver        | One driver geometry plus four transforms                   |
| Grip          | `leatherTGrip`                                             |
| Pommel        | `metalSpinnerPommel`                                       |

Each worker receives the same coordinate system, normalized dimensions, reference priority, and anchor contract.

## Phase 3 — Structural review

The coordinator checks:

- exact node names and parents;
- exact part counts;
- pivots and anchors;
- mirrored driver order;
- no mesh intersection at public interfaces;
- no component silently owns another component's geometry.

Reject structural errors before form refinement.

## Phase 4 — Form refinement

Owners refine only their own component:

- outer shell cross-sections, ridges, and sharpened edge-bevel profile;
- purple insert triangle-to-trapezoid silhouette;
- dark core scale;
- gem faceting;
- compact guard carriers and caps;
- driver slenderness and angles;
- grip taper/wrap;
- pommel point and facets.
- confirm that only the outer shell receives a sharpened blade-edge treatment, while the purple insert stays faceted/blunt by comparison.

## Phase 5 — Materials

Apply materials only after silhouette approval. Keep gradients restrained and preserve flat/faceted plane changes. Resolve transparent crystal sorting with explicit render order and physical spacing.

## Phase 6 — Assembly

The assembly agent connects components only through declared anchors. It may tune transforms within the measured tolerance but must return geometry corrections to the owning worker.

## Phase 7 — Validation

The validation agent produces fixed renders, overlay images, silhouette IoU, landmark errors, part counts, and a discrepancy report. Failed checks are routed back to the owning component agent.

## Phase 8 — Final packaging

Deliver the repository-native model, component manifest, renders, exploded view, validation report, and assumptions log.
