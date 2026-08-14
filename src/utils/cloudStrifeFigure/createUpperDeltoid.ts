import * as THREE from "three";
import { ARM } from "./measurements";
import { loft, ngon, poseOffset } from "./armSegment";
import { MAT_SKIN } from "./materials";

/**
 * S-10 deltoidUpper — prompt §4[10]. Loft: TOP QUADRILATERAL -> BOTTOM HEXAGON, and that
 * bottom hexagon is IDENTICAL to lowerDeltoid's top. They meet at the hexagonal waistline,
 * a horizontal crease visible under zoom.
 *
 * Both shoulders are geometrically identical in Stage 1. The figure's left black pauldron
 * is a separate Stage 3 part covering exactly this piece, with its lower edge on that same
 * waistline — which is also why the DELTOID could only be measured on the figure's RIGHT
 * (§4[9]: "bare, no pauldron occlusion, the cleanest read"). Reading the left one returned
 * 0.03937, identical to the neck's width, because up there the left shoulder is not skin.
 *
 * origin: shoulder (mates with chest's shoulderL / shoulderR) / emits: deltoidWaist
 */
export function createUpperDeltoid(side: "L" | "R"): THREE.Group {
  const h = ARM.upperDeltoidHeight;
  const off = poseOffset(h);
  const group = loft(
    `upperDeltoid${side}`,
    side,
    [
      ngon(4, ARM.shoulderWidth, ARM.shoulderDepth, 0, 0),
      ngon(6, ARM.deltoidWaistWidth, ARM.deltoidWaistDepth, -h, off.z),
    ],
    MAT_SKIN,
  );
  group.userData.sockets = {
    deltoidWaist: new THREE.Vector3(off.x * (side === "L" ? 1 : -1), -h, off.z),
  };
  return group;
}
