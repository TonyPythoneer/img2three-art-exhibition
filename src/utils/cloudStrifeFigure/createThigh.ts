import * as THREE from "three";
import { PANT_LEG } from "./measurements";
import { pantSegment } from "./pantSegment";
import { MAT_PANTS } from "./materials";

/**
 * S-05 pantTaper — prompt §4[5], the topmost of the three pant-leg segments.
 *
 * §4[5] calls it "a continuous inward TAPER, wide at top, narrow at bottom", running
 * "from the crotch down". The reference does not agree, and the disagreement is recorded
 * rather than papered over (prompt §0.6, and `parts.pantLeg` in landmarks.json):
 *
 *   - The taper is REAL, but it is ABOVE the crotch. The outer trouser line runs at 0.53
 *     dx/dy from the widest hip down to the crotch and 0.073 dx/dy below it. §4[6]
 *     describes the pelvis's own outline as flaring to the widest point and THEN PULLING
 *     IN to the crotch notch, so that taper belongs to the pelvis.
 *   - Above the crotch the two legs are ONE run in every view, so a per-leg thigh section
 *     cannot be measured up there at all.
 *
 * So the thigh is the top third of the near-constant tube below the crotch, and it shares
 * its section with the knee and calf. Its height is a guess-list item: nothing between the
 * crotch and the boot cuff marks where the three segments meet.
 *
 * origin: hip (mates with pelvis's hipL / hipR) / emits: kneeTop
 */
export function createThigh(side: "L" | "R"): THREE.Group {
  const group = pantSegment(`thigh${side}`, side, PANT_LEG.thighHeight, MAT_PANTS);
  group.userData.sockets = {
    kneeTop: new THREE.Vector3(0, -PANT_LEG.thighHeight, 0),
  };
  return group;
}
