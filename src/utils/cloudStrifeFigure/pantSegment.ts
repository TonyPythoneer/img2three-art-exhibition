import * as THREE from "three";
import { MANNEQUIN } from "./parts";
import { PANT_LEG } from "./measurements";

/**
 * The one shape thigh, knee and calf are all made of.
 *
 * §2's rule is that shape codes come from MEASURED DIMENSIONS, not from names: "if two
 * parts measure the same section and length within the tolerance, they get the SAME shape
 * code and only one geometry is authored". Below the crotch this leg's per-leg width
 * varies by less than the measurement uncertainty over its whole length, and there is no
 * corner anywhere in it — the corner §4 describes IS the crotch, where the outer slope
 * goes from 0.53 dx/dy above to 0.073 below. So S-03 pantTube, S-04 pantGather and S-05
 * pantTaper measure as one shape and are authored once here.
 *
 * That also satisfies §4[4]'s "the three parts must share ONE set of section constants so
 * their joins match exactly, or a seam appears that the reference does not have" — they
 * cannot disagree, because there is only one section.
 *
 * The three remain separate PARTS: partInspector reads the object tree and §2's table
 * lists six of them. What they share is geometry, not identity.
 *
 * Frame: the local origin is the segment's own upper socket (§1.4), so the top face sits
 * on y=0 and the bottom on y=-height.
 */
export function pantSegment(name: string, side: "L" | "R", height: number): THREE.Group {
  const sideSign = side === "L" ? 1 : -1;
  const { widthX, depthZ } = PANT_LEG;

  // Same 8% rule the boot cuff uses, so the chamfers read as one family down the leg.
  const chamfer = Math.min(widthX, depthZ) * 0.08;
  const halfW = widthX / 2;
  const halfD = depthZ / 2;

  // §4[3]: "one vertical crease down the front centre". Its DEPTH is not measured — the
  // crease is a shading line in the reference, a few pixels wide, and no view resolves how
  // far it stands out. Defaulted to the chamfer size so it belongs to the same facet
  // family; guess-list item. Without it the front face is one flat quad and the detail
  // inventory's `pant-front-crease` maps to nothing.
  const crease = chamfer;

  // Nine-vertex section, clockwise seen from +y, starting at the crease apex.
  const outline: Array<[number, number]> = [
    [0, halfD + crease],
    [halfW - chamfer, halfD],
    [halfW, halfD - chamfer],
    [halfW, -halfD + chamfer],
    [halfW - chamfer, -halfD],
    [-halfW + chamfer, -halfD],
    [-halfW, -halfD + chamfer],
    [-halfW, halfD - chamfer],
    [-halfW + chamfer, halfD],
  ];

  const n = outline.length;
  const positions: number[] = [];
  const indices: number[] = [];

  const ring = (y: number): number => {
    const base = positions.length / 3;
    for (const [x, z] of outline) positions.push(x, y, z);
    return base;
  };

  const top = ring(0);
  const bottom = ring(-height);

  for (let i = 1; i < n - 1; i += 1) {
    indices.push(top, top + i + 1, top + i);
    indices.push(bottom, bottom + i, bottom + i + 1);
  }

  for (let i = 0; i < n; i += 1) {
    const [x0, z0] = outline[i]!;
    const [x1, z1] = outline[(i + 1) % n]!;
    const a = positions.length / 3;
    positions.push(x0, 0, z0, x1, 0, z1, x1, -height, z1, x0, -height, z0);
    indices.push(a, a + 1, a + 2, a, a + 2, a + 3);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);

  const index = geometry.getIndex()!;
  const flip = () => {
    for (let i = 0; i < index.count; i += 3) {
      const a = index.getX(i);
      index.setX(i, index.getX(i + 2));
      index.setX(i + 2, a);
    }
    index.needsUpdate = true;
  };
  flip();
  // Mirroring negates x, which reverses handedness and turns every face inward; flipping
  // the winding again puts the normals back out. Same convention as createSole/createAnkle.
  if (sideSign < 0) {
    geometry.scale(-1, 1, 1);
    flip();
  }
  geometry.computeVertexNormals();

  const group = new THREE.Group();
  group.name = name;
  group.add(new THREE.Mesh(geometry, MANNEQUIN));
  return group;
}
