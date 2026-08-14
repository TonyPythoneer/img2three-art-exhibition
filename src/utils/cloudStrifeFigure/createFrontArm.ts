import * as THREE from "three";
import { ARM } from "./measurements";
import { loft, ngon, poseOffset } from "./armSegment";
import { MAT_BLACK, MAT_GREY, MAT_SKIN } from "./materials";

/**
 * S-12 / S-13 forearm + wrist + glove — prompt §4[12]. ONE part, three sub-segments, and
 * the sub-segments stay UNNAMED: §1.6 makes the object tree the part table, so a named
 * child would become a fifth arm part that §2 does not list.
 *
 * Three segments, top to bottom:
 *   a. forearm — narrow at the top, WIDE at the bottom. It thickens as it descends, the
 *      opposite of human anatomy; that is toy styling, not an error to be corrected.
 *   b. wrist   — the figure's LEFT is the grey bracer, the RIGHT the same prism in skin.
 *   c. glove   — a chamfered cuboid, NO finger geometry, joined by a single flat cut.
 *
 * THE ONE NON-MIRROR PAIR, and the factor is measured rather than quoted. §4[12] says the
 * left wrist is "slightly wider, factor ~1.05". Measured: bracer 0.09018 against a plain
 * wrist of 0.09653, a factor of 0.934 — the bracer is NARROWER, not wider. The absolute
 * difference is 0.0063 against an uncertainty of 0.05447, so the two wrists are the same
 * within tolerance and the asymmetry §1.5 relies on is not visible in width at all. Built
 * to the MEASURED factor (§0.6: the script wins), which keeps the pair non-mirror as §1.5
 * requires while not inventing a 5% bulge the reference does not show.
 *
 * The elbow break is baked in on top of the shared forward lean, so the fist lands AHEAD
 * of the hip line. §5.8: a straight hanging arm is a FAIL.
 *
 * origin: elbow / emits: fist (terminal — emitted and never consumed)
 */
export function createFrontArm(side: "L" | "R"): THREE.Group {
  const h = ARM.frontArmHeight;
  const wristFactor = side === "L" ? ARM.bracerWidthFactor : 1;
  // Three sub-segments over the part's height. Where they meet is not measurable — there
  // is no landmark between the elbow and the fist — so the split is 0.45 / 0.25 / 0.30,
  // read off the reference's own proportions at 8x and logged as a guess-list item.
  const hForearm = h * 0.45;
  const hWrist = h * 0.25;
  const hGlove = h * 0.3;
  const breakDeg = ARM.elbowBreakDeg;
  const oF = poseOffset(hForearm, breakDeg);
  const oW = poseOffset(hWrist, breakDeg);
  const oG = poseOffset(hGlove, breakDeg);

  const wristW = ARM.elbowWidth * wristFactor;
  const y1 = -hForearm;
  const y2 = y1 - hWrist;
  const y3 = y2 - hGlove;
  const z1 = oF.z;
  const z2 = z1 + oW.z;
  const z3 = z2 + oG.z;

  // §4[12]'s three sub-segments, three colour codes on the one mesh: forearm skin, wrist
  // grey ONLY on the figure's left (the bracer), glove near-black on both.
  const group = loft(
    `frontArm${side}`,
    side,
    [
      ngon(4, ARM.backArmWidth, ARM.backArmDepth, 0, 0),
      ngon(4, ARM.elbowWidth, ARM.elbowDepth, y1, z1),
      ngon(4, wristW, ARM.elbowDepth * wristFactor, y2, z2),
      ngon(4, ARM.gloveWidth, ARM.gloveWidth, y3, z3),
    ],
    [MAT_SKIN, side === "L" ? MAT_GREY : MAT_SKIN, MAT_BLACK],
  );
  const sign = side === "L" ? 1 : -1;
  group.userData.sockets = {
    fist: new THREE.Vector3((oF.x + oW.x + oG.x) * sign, y3, z3),
  };
  return group;
}
