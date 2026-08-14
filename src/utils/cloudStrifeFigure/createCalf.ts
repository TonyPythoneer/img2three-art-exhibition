import * as THREE from "three";
import { PANT_LEG } from "./measurements";
import { pantSegment } from "./pantSegment";
import { MAT_PANTS } from "./materials";

/**
 * S-03 pantTube — prompt §4[3], the bottom of the three pant-leg segments.
 *
 * This is the one §4 describes correctly: "near-square section with chamfered corners,
 * NEAR-CONSTANT WIDTH (top-to-bottom difference within measurementUncertainty), one
 * vertical crease down the front centre."
 *
 * §5.7 (d), measured rather than asserted: the tube's width goes 0.05707 at the top to
 * 0.05897 at the bottom, a difference of 0.00191 against an uncertainty of 0.05447. It is
 * constant. And it is constant for the WHOLE leg, not just this third — which is why the
 * thigh and knee above share this exact section.
 *
 * The section is cross-checked by a second, independent instrument: `measure_landmarks.py`
 * measures `straightPantTubeWidth` at a different row with different code and gets
 * [0.06097, 0.05843] against this script's 0.05643. That is the only pair of numbers in
 * this model measured twice by two scripts that agree.
 *
 * origin: calfTop / emits: ankleTop (mates with the boot cuff's own origin)
 */
export function createCalf(side: "L" | "R"): THREE.Group {
  const group = pantSegment(`calf${side}`, side, PANT_LEG.calfHeight, MAT_PANTS);
  group.userData.sockets = {
    ankleTop: new THREE.Vector3(0, -PANT_LEG.calfHeight, 0),
  };
  return group;
}
