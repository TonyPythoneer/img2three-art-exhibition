import * as THREE from "three";
import { MANNEQUIN } from "./parts";
import { ANKLE } from "./measurements";

/**
 * A-01 ankleCuff — prompt §4[2], a rectangular prism boot cuff.
 *
 * The cuff's cross-section is LARGER than the straight pant tube it swallows, so the
 * pant leg disappears inside it with a visible step all round. Four vertical edges are
 * chamfered, each catching its own tone.
 *
 * Frame. The part's local origin is `ankleTop` (§1.4), so the top face sits on y=0 and
 * the bottom on y=-height; placing the part at ankleTop's figure height in Stage 1B
 * lands the bottom face at soleTop's figure height.
 */
export function createAnkle(side: "L" | "R"): THREE.Group {
  const sideSign = side === "L" ? 1 : -1;
  const { cuffWidthX, cuffDepthZ, height } = ANKLE;

  // Chamfer size: ~8% of the shorter cross-section axis, enough to catch light on each
  // vertical edge without visibly shrinking the cuff's footprint.
  const chamfer = Math.min(cuffWidthX, cuffDepthZ) * 0.08;

  const halfW = cuffWidthX / 2;
  const halfD = cuffDepthZ / 2;

  // The cross-section outline at y=0: a rectangle with its four vertical edges chamfered.
  // Eight vertices, same pattern as createSole's plan outline.
  const outline: Array<[number, number]> = [
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

  // Top and bottom caps — outline is CW when viewed from +y, so top cap needs CCW winding
  for (let i = 1; i < n - 1; i += 1) {
    indices.push(top, top + i + 1, top + i); // top cap (CCW = outward from +y)
    indices.push(bottom, bottom + i, bottom + i + 1); // bottom cap (CW = outward from -y)
  }

  // Vertical walls
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

  // Ensure outward-facing normals: reverse winding if volume is negative
  geometry.computeBoundingSphere();
  const index = geometry.getIndex()!;
  for (let i = 0; i < index.count; i += 3) {
    const a = index.getX(i);
    index.setX(i, index.getX(i + 2));
    index.setX(i + 2, a);
  }
  index.needsUpdate = true;

  // Mirror for the right side, same convention as createSole: negate x, reverse winding.
  if (sideSign < 0) {
    geometry.scale(-1, 1, 1);
    for (let i = 0; i < index.count; i += 3) {
      const a = index.getX(i);
      index.setX(i, index.getX(i + 2));
      index.setX(i + 2, a);
    }
    index.needsUpdate = true;
  }
  geometry.computeVertexNormals();

  const group = new THREE.Group();
  group.name = `ankle${side}`;
  group.add(new THREE.Mesh(geometry, MANNEQUIN));

  // Sockets: the bottom face emits soleTop for the sole to attach to.
  group.userData.sockets = {
    soleTop: {
      localPosition: new THREE.Vector3(0, -height, 0),
      localRotation: new THREE.Euler(0, 0, 0),
    },
  };

  return group;
}
