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
 * wide, and y = 0 is the bottom of the neck block, y = 1 the top of the crown.
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
 * GUESS LIST G1 — head depth is NOT resolved by the reference.
 *
 * The 113 frames of this head all tumble on three axes while flying at the camera, so no frame
 * has a known pose to measure a profile against. The only direct depth evidence is the
 * crown-from-above ovoids near y=1500 on the sheet — (209,1508) 61x47 and (142,1505) 60x48,
 * i.e. 1.25-1.30 depth-over-width. Those are foreshortened, which makes 1.25 a LOWER bound
 * rather than a centre estimate; taken as the default anyway, and recorded in reading.md.
 */
export const DEPTH_OVER_WIDTH = 1.25;

/** Half-depth at the head's widest row, from the same guess. */
export const HALF_DEPTH = (len(FRAME_W) * DEPTH_OVER_WIDTH) / 2;

/**
 * The per-row silhouette from `landmarks.json.rows`, thinned to the rows where the profile
 * actually changes direction. Each entry is [frameRow, leftPx, rightPx]; the model's rings are
 * built by interpolating between them, so adding a row here refines the silhouette without
 * touching any factory.
 */
export const SILHOUETTE: readonly (readonly [number, number, number])[] = [
  [0, 13, 32], // crown top edge, flat
  [6, 9, 36],
  [13, 5, 42], // crown chamfer bottoms out
  [14, 4, 41], // side panels take over the silhouette
  [27, 3, 41],
  [30, 3, 43],
  [33, 1, 45],
  [34, 0, 46], // ear pods reach full frame width
  [42, 0, 46],
  [43, 1, 45],
  [47, 3, 42],
  [51, 7, 38], // jaw closes onto the collar
  [52, 8, 37], // neck block, constant width
  [58, 8, 37],
  [62, 5, 37], // neck feet flare
  [67, 5, 33],
  [68, 7, 21], // bottom notch
] as const;

/** Part y-bands, in frame rows, read off the row table above. */
export const BANDS = {
  crownPlate: [0, 8],
  skullShell: [4, 52],
  sidePanel: [14, 33],
  earPod: [33, 43],
  browRidge: [22, 32],
  eyePlate: [32, 40],
  neckBlock: [51, 68],
  neckFoot: [62, 68],
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
