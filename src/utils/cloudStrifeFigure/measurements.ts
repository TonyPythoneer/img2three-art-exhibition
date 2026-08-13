// GENERATED FILE — do not edit.
//
// Source: artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/landmarks.json
// Writer: artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/emit_measurements.py
//
// prompt.txt §3.1: a part factory reads its numbers from here and nowhere else.
// Every value is normalized so the whole figure is 1.000 tall, ground at Y=0 (§1.1).

/** Cross-view landmark agreement. NOT a per-part shape tolerance — see RMS. */
export const MEASUREMENT_UNCERTAINTY = 0.05447382;

/**
 * The per-part shape tolerance. `MEASUREMENT_UNCERTAINTY` is about 43px of front.webp
 * against a 4.7px reference fit residual, so using it for a part's own shape would make
 * that gate vacuous (prompt §11, Stage 0 addition 3).
 */
export const MEASUREMENT_RMS = 0.01374117;

/** S-01 soleSlab. `plan` is in the foot-local frame: +z toward the toe, +x toward the
 * figure's left, origin at the slab's plan centre, bottom face on y=0. */
export const SOLE = {
  lateralExtent: 0.19814461,
  foreAftExtent: 0.19673669,
  thickness: 0.05556227,
  splayDeg: 45.3812008,
  plan: {
    heelWidth: 0.09716576,
    toeWidth: 0.06995935,
    length: 0.23319783,
    endChamfer: 0.01889117,
  },
} as const;

/** The socket chain's heights, front view (prompt §4's ledger). */
export const SOCKET_Y = {
  ground: 0.0,
  soleTop: 0.055562,
  ankleTop: 0.16258,
  calfTop: 0.273084,
  kneeTop: 0.286825,
  hip: 0.271814,
  pelvisTop: 0.523305,
  waistTop: 0.56649,
  chestTop: 0.706208,
  deltoidWaist: 0.674454,
  backArmTop: 0.593164,
  elbow: 0.529656,
  fist: 0.331511,
  neckTop: 0.716369,
  skullTop: 1.0,
} as const;

/** Half the gap between the two feet plus half a foot's width: where a sole sits in X. */
export const SOLE_CENTRE_X = 0.10097754;

/** A-01 ankleCuff. Boot cuff: a prism whose section is LARGER than the pant tube it swallows. */
export const ANKLE = {
  cuffWidthX: 0.10288278,
  cuffDepthZ: 0.15187617,
  pantTubeWidthX: 0.06096757,
  pantTubeDepthZ: 0.0772598,
  foreAftOffset: -0.0606725,
  height: 0.107018,
} as const;
