import * as THREE from "three";
import { MANNEQUIN } from "./parts";
import { NECK } from "./measurements";

/**
 * S-14 neckColumn — prompt §4[13], a faceted cylinder.
 *
 * CylinderGeometry(r, r, h, radialSegments = 8) with flatShading. The user
 * specified a cylinder; the reference reads as a faceted column; a low-segment
 * cylinder satisfies both. Short and thin.
 *
 * Frame. The part's local origin is `neckTop` (§1.4), so the top face sits on
 * y=0 and the bottom face at y=-height; placing the part at neckTop's figure
 * height in Stage 1B lands the bottom face at chestTop's figure height.
 */
export function createNeck(): THREE.Group {
  const { radius, height, radialSegments } = NECK;

  const geometry = new THREE.CylinderGeometry(radius, radius, height, radialSegments);

  // CylinderGeometry is centred at origin; translate so top face is at y=0.
  geometry.translate(0, -height / 2, 0);

  const group = new THREE.Group();
  group.name = "neck";
  group.add(new THREE.Mesh(geometry, MANNEQUIN));

  // Sockets: the bottom face emits neckBase for the chest to connect to.
  // §4 fixes the shape as `{ <name>: THREE.Vector3 }` — a bare vector, no rotation.
  // neckBase sits at chestTop in the figure frame, so the socket vector is (0, -height, 0).
  group.userData.sockets = {
    neckBase: new THREE.Vector3(0, -height, 0),
  };

  return group;
}
