/**
 * Every number here traces to `artifacts/exhibits/mmx2-sigma-virus/spec/*.json`. Nothing is
 * copied from a summary, and nothing was picked by eye.
 *
 * Source frame: the GEOMETRY authority `front-frame.json.frontFrame` — the sprite sheet frame
 * at (63, 1811), 47x69px, whose per-row silhouette-extent asymmetry is 0.0101. The green frame
 * the exhibit is named after is the COLOUR authority only; it sits at 0.0555, i.e. it is caught
 * at a small yaw, so measuring geometry off it would bake that yaw into the model.
 *
 * Units: the frame's height is 1.0. So one reference pixel is 1/69, the head is 47/69 = 0.681
 * wide, and y = 0 is the bottom of the jaw block, y = 1 the top of the crown.
 */

/** Reference frame size, `landmarks.json.frame`. */
export const FRAME_W = 47;
export const FRAME_H = 69;

/** One reference pixel, in head-height units. */
export const PX = 1 / FRAME_H;

/** Frame column of the mirror axis: the frame spans px 0..46, so the axis is 23. */
const AXIS_PX = (FRAME_W - 1) / 2;

/** Frame column -> model x. */
export const x = (px: number): number => (px - AXIS_PX) * PX;
/** Frame row -> model y (row 0 is the top of the frame). */
export const y = (py: number): number => (FRAME_H - 1 - py) * PX;
/** A frame-pixel length -> a model length. */
export const len = (px: number): number => px * PX;

/**
 * Head depth. This WAS guess list G1 at 1.25, read off a foreshortened crown-from-above crop.
 * It is now measured, and the measurement only became available once `compare_hue_groups.py`
 * established that the whole sheet is one mesh in six palettes — the six damage states the
 * published sources describe — so all 307 frames are evidence about this head rather than 113.
 *
 * Filter the index to frames whose height matches the front view's 68-70px and the rotation must
 * have stayed about the vertical axis: 87 frames, a pure yaw sweep, widths running 42 -> 67 with
 * the front view at 47 (`profile-width.json`).
 *
 * Width at the peak is not automatically the depth — for a rectangular cross-section the peak is
 * the diagonal at ~45 degrees, which would put depth at 1.02x instead of 1.43x. The model's own
 * captured sweep settles which: it runs 480, 478, 502, 534, 560, 581, 600, 603, 594, 606 across
 * 0..90 degrees, so this cross-section family peaks AT 90 degrees, where width IS depth.
 *
 *   depth / width = 67 / 47 = 1.4255
 *
 * `gate_yaw_sweep.py` is the gate that holds it: it compares the model's own width ratio against
 * the reference's, pose-free, and it is the only gate here that can see depth at all.
 */
export const DEPTH_OVER_WIDTH = 1.4255;

/** Half-depth at the head's widest row. */
export const HALF_DEPTH = (len(FRAME_W) * DEPTH_OVER_WIDTH) / 2;

/**
 * The head's silhouette, ALL 69 rows of it, straight from `landmarks.json.rows` — each entry is
 * `[frameRow, leftPx, rightPx]` on the geometry authority.
 *
 * This started as a hand-thinned 17-row version keeping only the rows where the profile changes
 * direction. That cost real IoU on the band where the outline steps most gently: `helmetSides`
 * sat at 0.885 against 0.96 for the ear pods, because a linear interpolation across rows 14-33
 * cuts the corner the reference actually turns. Thinning a table that the instrument already
 * produced in full buys nothing — the loft samples it, so ring count is set by `step`, not by
 * how many rows live here.
 */
export const SILHOUETTE: readonly (readonly [number, number, number])[] = [
  [0, 13, 32],
  [1, 13, 32],
  [2, 12, 33],
  [3, 11, 34],
  [4, 10, 35],
  [5, 10, 35],
  [6, 9, 36],
  [7, 8, 37],
  [8, 7, 38],
  [9, 7, 38],
  [10, 6, 39],
  [11, 5, 40],
  [12, 4, 41],
  [13, 4, 42],
  [14, 4, 41],
  [15, 4, 41],
  [16, 4, 41],
  [17, 4, 41],
  [18, 4, 41],
  [19, 4, 41],
  [20, 4, 41],
  [21, 4, 41],
  [22, 4, 41],
  [23, 4, 41],
  [24, 4, 41],
  [25, 4, 41],
  [26, 4, 41],
  [27, 4, 41],
  [28, 3, 42],
  [29, 2, 43],
  [30, 1, 44],
  [31, 0, 45],
  [32, 0, 46],
  [33, 0, 46],
  [34, 0, 46],
  [35, 0, 46],
  [36, 0, 46],
  [37, 0, 46],
  [38, 0, 46],
  [39, 0, 46],
  [40, 0, 46],
  [41, 0, 46],
  [42, 0, 46],
  [43, 0, 46],
  [44, 0, 46],
  [45, 2, 44],
  [46, 3, 43],
  [47, 4, 42],
  [48, 5, 41],
  [49, 6, 40],
  [50, 7, 39],
  [51, 7, 38],
  [52, 8, 38],
  [53, 8, 38],
  [54, 8, 38],
  [55, 8, 38],
  [56, 8, 38],
  [57, 8, 38],
  [58, 8, 38],
  [59, 8, 38],
  [60, 8, 38],
  [61, 8, 38],
  [62, 8, 38],
  [63, 8, 38],
  [64, 8, 38],
  [65, 8, 38],
  [66, 8, 38],
  [67, 8, 38],
  [68, 17, 29],
] as const;

/** Part y-bands, in frame rows, read off the row table above. */
export const BANDS = {
  crownPlate: [0, 8],
  skullShell: [4, 52],
  sidePanel: [14, 33],
  earPod: [33, 43],
  browRidge: [22, 32],
  eyePlate: [32, 40],
  jawBlock: [51, 68],
  chinTab: [62, 68],
} as const satisfies Record<string, readonly [number, number]>;

/**
 * Eye band, `landmarks.json.eyeBand` measured on the geometry frame: yTop 0.4706, yBottom
 * 0.5735 of frame height; xLeft 0.1522, xRight 0.8043 of frame width. Converted to frame
 * pixels here so the factories only ever speak one unit.
 */
export const EYE = {
  topPx: 0.4706 * (FRAME_H - 1),
  bottomPx: 0.5735 * (FRAME_H - 1),
  outerPx: 0.1522 * (FRAME_W - 1),
  innerPx: 0.8043 * (FRAME_W - 1),
} as const;

/**
 * The RIGHT eye's actual outline, column by column, from `eye-outline.json` — measured on the
 * geometry authority, cross-checked against the colour authority wherever it has a stroke in the
 * same column. `[xFromAxis, topRow, bottomRow]`, all in frame pixels.
 *
 * This replaced a parallelogram fitted to the eye's bounding box. That bar matched the reference
 * on band position, slant AND filled area — all three gates green — and still read wrong beside
 * it, because the shape is a leaf, not a bar:
 *
 *   - the TOP edge rises almost straight, row 36 at the bridge to row 32 at the outer end;
 *   - the BOTTOM edge drops to row 39 by column 7, holds at 38 through column 12, then cuts
 *     sharply up to 34 by column 14.
 *
 * So the eye is 1px tall at the bridge, 7px at its deepest around column 7, and 3px at the outer
 * tip. The kink is on the bottom edge near the outer end — which is why looking for it on the top
 * edge found nothing.
 */
export const EYE_OUTLINE: readonly (readonly [number, number, number])[] = [
  [1, 36, 36],
  [2, 35, 36],
  [3, 35, 37],
  [4, 34, 37],
  [5, 34, 38],
  [6, 34, 38],
  [7, 33, 39],
  [8, 33, 38],
  [9, 33, 38],
  [10, 33, 38],
  [11, 33, 38],
  [12, 33, 38],
  [13, 32, 36],
  [14, 32, 34],
] as const;

/**
 * The eye as a POLYGON fitted to `EYE_OUTLINE`, walked anticlockwise from the bridge: along the
 * top edge outward, then back along the bottom. `[xFromAxis, row]` in frame pixels.
 *
 * Tracing all 14 measured columns literally was tried first and rendered as a sawtooth — the
 * columns are a 1px rasterisation of straight 3D edges, so following every step reproduces the
 * raster instead of the edges it came from, and at render scale that reads as noise.
 *
 * Six vertices reproduce all 14 columns to within **0.6 reference pixels** at every column:
 *   top    (1,36) -> (7,33): x=4 fits 34.5 vs 34 measured
 *          (7,33) -> (14,32): x=11 fits 32.43 vs 33
 *   bottom (1,36) -> (7,39): x=4 fits 37.5 vs 37
 *          (7,39) -> (12,38): x=9 fits 38.6 vs 38
 *          (12,38) -> (14,34): x=13 fits 36 vs 36 exactly
 */
export const EYE_POLYGON: readonly (readonly [number, number])[] = [
  [1, 36],
  [7, 33],
  [14, 32],
  [14, 34],
  [12, 38],
  [7, 39],
] as const;

/**
 * Half-width per frame row, in model units — `SILHOUETTE` linearly resampled onto every one of
 * the 69 rows once, at module load, rather than searched per call. A dense table also removes
 * the run-off-the-end branches an interpolating lookup needs.
 */
const HALF_WIDTH_BY_ROW: number[] = (() => {
  const table: number[] = [];
  let seg = 0;
  for (let py = 0; py < FRAME_H; py += 1) {
    while (seg < SILHOUETTE.length - 2 && py > (SILHOUETTE[seg + 1]?.[0] ?? 0)) seg += 1;
    const a = SILHOUETTE[seg] ?? SILHOUETTE[0];
    const b = SILHOUETTE[seg + 1] ?? a;
    if (!a || !b) throw new Error("SILHOUETTE must not be empty");
    const span = b[0] - a[0];
    const t = span === 0 ? 0 : Math.min(1, Math.max(0, (py - a[0]) / span));
    const l = a[1] + (b[1] - a[1]) * t;
    const r = a[2] + (b[2] - a[2]) * t;
    table.push(len((r - l) / 2));
  }
  return table;
})();

/** Half-width of the head at a frame row, in model units. Rows outside 0..68 clamp. */
export function halfWidthAt(py: number): number {
  const i = Math.min(FRAME_H - 1, Math.max(0, Math.round(py)));
  return HALF_WIDTH_BY_ROW[i] ?? 0;
}
