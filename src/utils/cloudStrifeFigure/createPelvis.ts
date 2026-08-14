import * as THREE from "three";
import { PELVIS, PANT_LEG } from "./measurements";
import { MAT_PANTS } from "./materials";

/**
 * S-06 pelvisKite — prompt §4[6], the bloomer pants' main volume.
 *
 * Front outline a PENTAGON: belt width, flaring out to the widest point, then pulling in
 * to an inverted-V crotch notch. Profile a KITE: one sharp point front and one back,
 * front/back symmetric, deepest at the widest height. Few facets, large areas, hard
 * creases — so three hexagonal rings, not a subdivided tube.
 *
 * Two things §4[6] gets wrong against the reference, both recorded rather than obeyed:
 *
 *   - "the widest point must be WIDER THAN THE SHOULDERS" is FALSE. Hip 0.28325 against a
 *     shoulder line of 0.37978 — a gap of 0.0965 against an uncertainty of 0.05447, so it
 *     is decided, not undecided. It IS wider than the chest slab, by 0.0851. §0.6: the
 *     script wins, so this is built at its measured width.
 *   - Self-check B ("the profile reads as a kite") was INDETERMINATE in Stage 0 because
 *     the glove sits in front of the hip in both profile views. That is true of the
 *     SILHOUETTE only: the gloves are near-black and the pants purple, so measuring the
 *     outline on the purple band removes the occlusion entirely. Measured that way the
 *     kite's front/back asymmetry is 0.0375, inside the uncertainty — it IS symmetric.
 *
 * Frame: local origin is pelvisTop (§1.4), top face on y=0, crotch at y=-height.
 */
export function createPelvis(): THREE.Group {
  const {
    height,
    widthAtTop,
    depthAtTop,
    widestWidth,
    maxDepth,
    widestDrop,
    notchWidth,
    hipOffsetX,
  } = PELVIS;

  // At the crotch the mass is already becoming two legs, so the bottom ring is as wide as
  // the two leg centres plus one leg, and as deep as a leg. Both come from PANT_LEG, which
  // is the same constant the thigh below reads — the join cannot disagree.
  const bottomWidth = 2 * hipOffsetX + PANT_LEG.widthX;
  const bottomDepth = PANT_LEG.depthZ;

  /** Hexagon with a sharp point front and back: that is what makes the PROFILE a kite. */
  const ring = (w: number, d: number, y: number): Array<[number, number, number]> => [
    [0, y, d / 2],
    [w / 2, y, d / 6],
    [w / 2, y, -d / 6],
    [0, y, -d / 2],
    [-w / 2, y, -d / 6],
    [-w / 2, y, d / 6],
  ];

  const rings = [
    ring(widthAtTop, depthAtTop, 0),
    ring(widestWidth, maxDepth, -widestDrop),
    ring(bottomWidth, bottomDepth, -height),
  ];
  const n = 6;
  const positions: number[] = [];
  const indices: number[] = [];
  const push = (p: [number, number, number]): number => {
    const i = positions.length / 3;
    positions.push(p[0], p[1], p[2]);
    return i;
  };

  const base = rings.map((r) => r.map(push));

  // Walls
  for (let k = 0; k < rings.length - 1; k += 1) {
    for (let i = 0; i < n; i += 1) {
      const a = base[k]![i]!;
      const b = base[k]![(i + 1) % n]!;
      const c = base[k + 1]![(i + 1) % n]!;
      const d = base[k + 1]![i]!;
      indices.push(a, b, c, a, c, d);
    }
  }
  // Top cap
  const t = base[0]!;
  for (let i = 1; i < n - 1; i += 1) indices.push(t[0]!, t[i]!, t[i + 1]!);

  // Bottom cap, as the inverted-V CROTCH NOTCH rather than a flat face. The two x=0
  // vertices of the bottom ring are lifted, so the underside is a tent ridged front-to-back
  // and the front view shows a V cutting up between the legs. Its RISE is not measurable —
  // no view sees under the figure — so it is half the measured notch width, i.e. a 45
  // degree V. Guess-list item; the notch's WIDTH is measured, its depth is not.
  const rise = notchWidth / 2;
  const b = base[2]!;
  const bottomRing = rings[2]!;
  const apexF = push([0, -height + rise, bottomRing[0]![2]]);
  const apexB = push([0, -height + rise, bottomRing[3]![2]]);
  indices.push(apexF, b[1]!, b[2]!, apexF, b[2]!, apexB);
  indices.push(apexB, b[4]!, b[5]!, apexB, b[5]!, apexF);

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();

  const group = new THREE.Group();
  group.name = "pelvis";
  group.add(new THREE.Mesh(geometry, MAT_PANTS));
  // §4's ledger: pelvis emits hipL and hipR, one per leg, and a sided emitter carries the
  // suffix. thighL's origin is `hip`, so `hipL` is what it hangs from (§1.2: +X is the
  // figure's LEFT).
  group.userData.sockets = {
    hipL: new THREE.Vector3(hipOffsetX, -height, 0),
    hipR: new THREE.Vector3(-hipOffsetX, -height, 0),
  };
  return group;
}
