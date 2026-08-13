import * as THREE from "three";
import { MANNEQUIN } from "./parts";
import { WAIST } from "./measurements";

/**
 * S-07 belt — prompt §4[7], a flat band wrapping all the way round.
 *
 * Hard steps on both its top and bottom edges; it stands proud of both the
 * chest above and the pelvis below. A box geometry with chamfered vertical
 * edges, same pattern as createAnkle.
 *
 * Frame. The part's local origin is `waistTop` (§1.4), so the top face sits on
 * y=0 and the bottom face at y=-height; placing the part at waistTop's figure
 * height in Stage 1B lands the bottom face at pelvisTop's figure height.
 */
export function createWaist(): THREE.Group {
  const { widthX, depthZ, height } = WAIST;

  // Chamfer size: ~8% of the shorter cross-section axis, same as createAnkle.
  const chamfer = Math.min(widthX, depthZ) * 0.08;

  const halfW = widthX / 2;
  const halfD = depthZ / 2;

  // The cross-section outline at y=0: a rectangle with its four vertical edges chamfered.
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

  geometry.computeVertexNormals();

  const group = new THREE.Group();
  group.name = "waist";
  group.add(new THREE.Mesh(geometry, MANNEQUIN));

  // Sockets: the bottom face emits pelvisTop for the pelvis to connect from below.
  // §4 fixes the shape as `{ <name>: THREE.Vector3 }` — a bare vector, no rotation.
  group.userData.sockets = {
    pelvisTop: new THREE.Vector3(0, -height, 0),
  };

  return group;
}
