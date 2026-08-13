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
  ankleTop: 0.16258019,
  calfTop: 0.19520874,
  kneeTop: 0.22783729,
  hip: 0.26046584,
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
  height: 0.10701819,
} as const;

/**
 * S-03/S-04/S-05 collapsed. thigh, knee and calf are three stacked segments of ONE
 * near-square chamfered tube — §2 assigns shape codes from measured dimensions, not
 * from names, and below the crotch this leg's width varies by less than the
 * uncertainty over its whole length with no corner anywhere in it. The corner §4
 * describes IS the crotch: the outer slope is 0.53 dx/dy above it and 0.073 below.
 *
 * So the three factories share this one section and C0 continuity holds by
 * construction. Where the three segments MEET is not measurable — there is no
 * landmark between the crotch and the boot cuff and no width breakpoint — so the two
 * split heights are equal thirds and are a guess-list item.
 */
export const PANT_LEG = {
  widthX: 0.05643412,
  depthZ: 0.05526363,
  crotchY: 0.26046584,
  thighHeight: 0.03262855,
  kneeHeight: 0.03262855,
  calfHeight: 0.03262855,
} as const;

/**
 * S-06 pelvisKite. The largest volume in the LOWER body and the part that decides its
 * silhouette. Front outline a pentagon, profile a front/back-symmetric kite.
 *
 * §4[6] also says 'the widest point must be WIDER THAN THE SHOULDERS'. Measured, that
 * is FALSE: hip 0.28325 against a shoulder line of 0.37978, a gap of 0.0965 against an
 * uncertainty of 0.05447 — decided, not undecided. It IS wider than the chest slab, by
 * 0.0851. §0.6 says the script wins, so these are the measured numbers.
 */
export const PELVIS = {
  height: 0.26283915,
  widthAtTop: 0.12815628,
  depthAtTop: 0.06823672,
  widestWidth: 0.29096941,
  maxDepth: 0.14872306,
  /** How far BELOW pelvisTop the widest ring sits. */
  widestDrop: 0.20262532,
  notchWidth: 0.04953615,
  hipOffsetX: 0.0692236,
} as const;

/**
 * S-08 chestSlab, and the hub of §4's socket ledger — the only part emitting four.
 *
 * `widestDrop` is not zero: §4[8] says the slab is widest at the shoulder line, but AT
 * that row the shirt measures 0.00124 wide because up there the figure is neck, black
 * pauldron and bare deltoid. The widest row is 0.1186 below it.
 *
 * The depth/width ratio is 0.622 — a block, not the 'near-planar' sheet §4[8]
 * describes. Reported and not asserted: no 'slabness' threshold has been pinned with
 * a fake frame, and a guessed one would be worse than none.
 */
export const CHEST = {
  height: 0.13971735,
  widestWidth: 0.17827477,
  widthAtWaistTop: 0.12707511,
  depthAtWidest: 0.11094191,
  depthAtWaistTop: 0.06617856,
  widestDrop: 0.10718329,
  shoulderOffsetX: 0.08913739,
} as const;

/**
 * S-09..S-13, the whole arm chain. ONE record because §4[10] makes upperDeltoid's
 * bottom hexagon IDENTICAL to lowerDeltoid's top, and §4[9] makes lowerDeltoid's quad
 * bottom identical to backArm's section — two shared sections that cannot be measured
 * from inside either part.
 *
 * The pose angles are the MEAN of the two sides. §1.4 bakes the pose in and §1.5 calls
 * these pure mirror pairs; the measured 8.8 deg forward-lean gap between the sides is
 * SMALLER than the 29.23 px residual of the fit that produced it, so the asymmetry is
 * not established and the mirror stands (parts.arm.mirror_1_4_vs_1_5).
 */
export const ARM = {
  shoulderWidth: 0.03641925,
  shoulderDepth: 0.04727935,
  deltoidWaistWidth: 0.09595185,
  deltoidWaistDepth: 0.03685681,
  backArmWidth: 0.04263159,
  backArmDepth: 0.03980044,
  elbowWidth: 0.07841576,
  elbowDepth: 0.08086643,
  gloveWidth: 0.08764088,
  /** The figure's LEFT wrist is the grey bracer. Measured 0.934, not §4[12]'s 1.05;
   * the two wrists differ by 0.0063, far inside the uncertainty. */
  bracerWidthFactor: 0.93421053,
  upperDeltoidHeight: 0.031754,
  lowerDeltoidHeight: 0.08129,
  backArmHeight: 0.063508,
  frontArmHeight: 0.198145,
  abductionDeg: 17.38628285,
  forwardLeanDeg: 6.02733273,
  elbowBreakDeg: 16.43405722,
} as const;

/** S-15 skull. Measured on the FACE (bare skin), never by insetting back.webp:
 * hairThickness is a fringe depth, 0.03863 left vs 0.07137 right. */
export const HEAD = {
  cheekboneWidth: 0.13971735,
  cheekboneHeight: 0.76209465,
  chinWidth: 0.03556442,
  exposedDepth: 0.17088552,
} as const;

/** S-14 neckColumn. CylinderGeometry(r, r, h, radialSegments=8) with flatShading. */
export const NECK = {
  radius: 0.01975886,
  height: 0.01016126,
  radialSegments: 8,
} as const;

/** S-07 belt. A flat band standing proud of chest and pelvis. */
export const WAIST = {
  widthX: 0.13209641,
  depthZ: 0.06270151,
  height: 0.04318536,
} as const;
