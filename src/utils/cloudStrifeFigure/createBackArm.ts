import * as THREE from "three";
import { ARM } from "./measurements";
import { loft, ngon, poseOffset } from "./armSegment";

/**
 * S-11 upperArm — prompt §4[11]. "A very slender rectangular prism, near-square section
 * with chamfered corners. Markedly thinner than BOTH the deltoid above and the forearm
 * below — that contrast is an identity feature."
 *
 * §5.8 lists it among the features whose failure blocks `continue` even when the global
 * score passes, so it is measured rather than asserted:
 *
 *   deltoidWaist 0.09595   >   backArmTop 0.04263   <   elbow 0.07842      PASS
 *
 * That check returned REVIEW until the deltoid was read on the figure's RIGHT shoulder
 * (§4[9]) — the left one is under the black pauldron and is not skin. The instrument was
 * wrong, not the shape.
 *
 * origin: backArmTop / emits: elbow
 */
export function createBackArm(side: "L" | "R"): THREE.Group {
  const h = ARM.backArmHeight;
  const off = poseOffset(h);
  const group = loft(`backArm${side}`, side, [
    ngon(4, ARM.backArmWidth, ARM.backArmDepth, 0, 0),
    ngon(4, ARM.backArmWidth, ARM.backArmDepth, -h, off.z),
  ]);
  group.userData.sockets = {
    elbow: new THREE.Vector3(off.x * (side === "L" ? 1 : -1), -h, off.z),
  };
  return group;
}
