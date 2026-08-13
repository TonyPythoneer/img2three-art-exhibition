import * as THREE from "three";
import { ARM } from "./measurements";
import { loft, ngon, poseOffset } from "./armSegment";

/**
 * S-09 deltoidLower — prompt §4[9]. Loft: TOP HEXAGON -> BOTTOM QUADRILATERAL. §4[9] says
 * the quad bottom "exists so it mates with backArm's rectangular prism at an identical
 * section", and the top hexagon is upperDeltoid's bottom. Both come from the same two
 * constants, so neither seam can drift.
 *
 * origin: deltoidWaist (the hexagonal waistline) / emits: backArmTop
 */
export function createLowerDeltoid(side: "L" | "R"): THREE.Group {
  const h = ARM.lowerDeltoidHeight;
  const off = poseOffset(h);
  const group = loft(`lowerDeltoid${side}`, side, [
    ngon(6, ARM.deltoidWaistWidth, ARM.deltoidWaistDepth, 0, 0),
    ngon(4, ARM.backArmWidth, ARM.backArmDepth, -h, off.z),
  ]);
  group.userData.sockets = {
    backArmTop: new THREE.Vector3(off.x * (side === "L" ? 1 : -1), -h, off.z),
  };
  return group;
}
