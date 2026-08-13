import * as THREE from "three";
import { PANT_LEG } from "./measurements";
import { pantSegment } from "./pantSegment";

/**
 * S-04 pantGather — prompt §4[4], the middle of the three pant-leg segments.
 *
 * §4[4] gives it exactly one job: "turn the taper above into the vertical below. The
 * corner lives inside this segment." Measured, there is no such corner down here.
 *
 * §5.7 (a)'s literal test could not have found that out: it compares a two-segment fit's
 * residual against measurementUncertainty, which is 43 px of front.webp, while the real
 * residuals are 2.4-6.8 px — both fits pass by a factor of six and the test can never
 * fail. The quantity with signal is the RATIO res3/res2, and its threshold was pinned
 * against fake frames (a clean one-corner polyline must pass; a smooth arc and a genuine
 * two-corner line must fail) exactly the way the facet gate's angle was. Pinned at 0.574
 * with a separation of 0.848, the measured leg comes out at 0.357: BELOW the crotch a
 * second corner buys enough to be noise-fitting, which is what a straight line does.
 *
 * The corner is the crotch itself. So this segment is the middle third of the same tube,
 * carrying the same section as the thigh above and the calf below — which is §4[4]'s
 * "the three parts must share ONE set of section constants" holding by construction
 * rather than by assertion.
 *
 * origin: kneeTop / emits: calfTop
 */
export function createKnee(side: "L" | "R"): THREE.Group {
  const group = pantSegment(`knee${side}`, side, PANT_LEG.kneeHeight);
  group.userData.sockets = {
    calfTop: new THREE.Vector3(0, -PANT_LEG.kneeHeight, 0),
  };
  return group;
}
