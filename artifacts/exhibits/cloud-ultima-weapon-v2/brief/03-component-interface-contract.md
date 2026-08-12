# Component Interface Contract

This document is the merge contract for independent subagents. The repository-native schema may rename fields, but it should preserve the same meaning.

## Scene axes and root

```text
SwordRoot.position = (0, 0, 0)
SwordRoot.rotation = (0, 0, 0)
SwordRoot.scale    = (1, 1, 1)
+Y = blade direction
-Y = grip direction
+Z = artwork-facing side
```

The model is authored upright. Artwork tilt belongs to the validation transform, not component geometry.

## Required nodes

| Path                                      | Ownership           | May contain                                                    |
| ----------------------------------------- | ------------------- | -------------------------------------------------------------- |
| `SwordRoot/BladeGroup/outerCrystalShell`  | Outer crystal agent | One shell mesh or a small shell mesh set with one public node  |
| `SwordRoot/BladeGroup/purpleEnergyInsert` | Purple insert agent | One independent inset crystal node                             |
| `SwordRoot/BladeGroup/darkCoreTriangle`   | Core-and-gem agent  | One triangular core node                                       |
| `SwordRoot/BladeGroup/rootDiamondGem`     | Core-and-gem agent  | One faceted gem node                                           |
| `SwordRoot/HiltGroup/guardCore`           | Guard agent         | Central socket plus mirrored side carriers and their gold caps |
| `SwordRoot/HiltGroup/driverArray/*`       | Driver agent        | Four transforms sharing one geometry/material definition       |
| `SwordRoot/HiltGroup/leatherTGrip`        | Grip agent          | Grip shaft and subtle wrap detail under one public node        |
| `SwordRoot/HiltGroup/metalSpinnerPommel`  | Pommel agent        | One compact faceted pommel node                                |

## Required anchors

| Owner                | Anchor                | Meaning                                                                       |
| -------------------- | --------------------- | ----------------------------------------------------------------------------- |
| `guardCore`          | `blade_socket_anchor` | Main blade root connection at guard center                                    |
| `guardCore`          | `gem_mount_anchor`    | Front-center placement of root gem                                            |
| `guardCore`          | `grip_anchor`         | Top-center of grip                                                            |
| `guardCore`          | `driver_anchor_0..3`  | Four driver origins, ordered left upper, left lower, right upper, right lower |
| `outerCrystalShell`  | `root_anchor`         | Matches guard blade socket                                                    |
| `outerCrystalShell`  | `inner_insert_anchor` | Origin for purple insert                                                      |
| `outerCrystalShell`  | `core_anchor`         | Origin for dark core triangle                                                 |
| `purpleEnergyInsert` | `root_anchor`         | Insert root registration point                                                |
| `darkCoreTriangle`   | `base_anchor`         | Lower-center of triangle                                                      |
| `rootDiamondGem`     | `center_anchor`       | Gem geometric center                                                          |
| `leatherTGrip`       | `top_anchor`          | Matches guard grip anchor                                                     |
| `leatherTGrip`       | `pommel_anchor`       | Bottom-center of grip                                                         |
| `metalSpinnerPommel` | `top_anchor`          | Matches grip pommel anchor                                                    |
| each driver          | `root_anchor`         | Matches one guard driver anchor                                               |

## Subagent result manifest

Return the repository-native equivalent of this record:

```json
{
  "node": "outerCrystalShell",
  "parent": "SwordRoot/BladeGroup",
  "units": "normalized-1000",
  "pivot": [0, 0, 0],
  "bounds": {
    "min": [-90, 0, -16],
    "max": [90, 760, 16]
  },
  "anchors": {
    "root_anchor": [0, 0, 0],
    "inner_insert_anchor": [0, 18, 11],
    "core_anchor": [0, 25, 16]
  },
  "materials": ["mat_outer_crystal"],
  "geometryStats": {
    "vertices": 0,
    "faces": 0
  },
  "assumptions": [
    "Depth is inferred conservatively because the artwork mainly shows the front view."
  ]
}
```

Replace zero geometry counts with real values. Do not omit assumptions.

## Driver indexing

The four drivers are indexed from the artwork-facing front view:

```text
0 = left upper
1 = left lower
2 = right upper
3 = right lower
```

Create one base driver in its own local axis, then apply four transforms. Do not independently remodel four slightly different drivers unless the authority measurement proves an intentional asymmetry.

## Merge rules

- The assembly agent may change parent transforms and adapter transforms.
- The assembly agent may not edit component vertices without returning the component to its owner.
- No component may reach into another component's internal child meshes.
- Materials are referenced by stable IDs.
- Transparent crystal meshes must use a deterministic render order and avoid coplanar surfaces.
- Front silhouette has higher priority than guessed depth.
- One exploded-view transform set must be kept separate from production assembly transforms.

## Geometry notes

- `outerCrystalShell` is the only blade layer that should present a sharpened cutting profile. Its tip and left/right outer margins must taper into visible bevelled edges.
- `purpleEnergyInsert` must remain a faceted inset prism/mass. It may taper in silhouette, but it must not use the same knife-edge bevel profile as `outerCrystalShell`.
