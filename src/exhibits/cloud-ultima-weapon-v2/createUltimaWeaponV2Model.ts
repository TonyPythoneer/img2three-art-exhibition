import * as THREE from "three";

/**
 * FF7 Ultima Weapon — v2 reconstruction.
 *
 * Built from the review package's authority artwork rather than from the earlier runs' 47-node
 * reading. Every number below is in **normalized-1000 weapon-local units** divided by 100, and
 * traces to `spec/measurements.json` (emitted by `spec/measure_authority.py`) or to a numbered
 * assumption in `spec/image-analysis.md` Layer 8.
 *
 * Frame: +Y guard→tip, −Y guard→pommel, +Z artwork-facing, origin at the blade socket.
 * The artwork's 18.13° roll is a camera transform, not geometry — see `createUltimaWeaponV2LookDev`.
 *
 * The component contract is exact: these physical parts, no others, none merged. `SwordRoot`,
 * `BladeGroup`, `HiltGroup` and `driverArray` are organisational groups and carry no geometry.
 *
 *   SwordRoot
 *   ├── BladeGroup  { outerCrystalShell, purpleEnergyInsertFront/Rear,
 *   │                 darkCoreTriangleFront/Rear, rootDiamondGemFront/Rear }
 *   └── HiltGroup   { crystalClampLeft/Right, leatherConnectorLeft/Right,
 *                     driverArray{4 rods}, spinnerEndLeft/Right,
 *                     leatherGrip, pointedMetalPommel }
 *
 * There is deliberately NO central grip socket and NO driver socket meshes: the two triangular
 * clamps are the blade socket, and each rod's root cap lands directly on its connector's
 * surface. Both were components in an earlier pass and both were structurally wrong. There is
 * also NO grip end collar: the crop shows the leather running straight into the gold. And there
 * is NO guardCore bridge and NO grip tang — integration #16 butts the grip's flat top against the
 * jaws' own floor — so the guard is a joint between three existing parts rather than a fourth part
 * sitting in the middle of them.
 *
 * All three inner layers are each TWO meshes, front and rear, and the pair is still one component
 * of the contract. All three are **seated**: every one of the six meshes sits on the surface
 * under it and none of them reaches `Z = 0`.
 *
 *   · the insert and the dark core are **skins** — films laid ON the shell's own front and rear
 *     surfaces, following it in X and in Y, one `SKIN_STEP` thick, top AND bottom.
 *   · the diamond is a **stone** — a girdled rhombus grown out of the dark core's outer face and
 *     standing well clear of it. It is a raised body, not a flat inlay, and the depth ladder is
 *     what says so; what it is NOT any more is a half-body driven through the blade from the
 *     mid-plane outward.
 *
 * `outerCrystalShell` is therefore a SOLID with nothing inside it, and that is asserted
 * pointwise: the harness measures every blade-layer sample against the shell's own lofted
 * surface and `spec/check_centerline.py` fails on any penetration. The one deliberate exception
 * is the hilt — the two jaws pass through the shell's base ring on purpose, because they ARE the
 * socket carrying it. See §3 of `spec/CURRENT-MODEL.md`.
 *
 * The read the artwork asks for is a flat inlay under a raised stone, and `check_centerline.py`
 * still asserts the two kinds separately by their STEP over the layer below — a skin's inside
 * 0.035–0.060 T, the stone's at least 0.25 T — so a skin cannot quietly grow back into a boss
 * and the stone cannot flatten into a plate.
 */

/** Matches the spec's locked build passes: silhouette only, +all parts, +micro detail. */
export type DetailLevel = "blockout" | "structural" | "full";

export type SculptRuntime = {
  nodes: Map<string, THREE.Object3D>;
  /**
   * The built materials, by the name `buildMaterials()` gives them.
   *
   * Exposed so a look-dev mode can deviate from them REVERSIBLY — see `applyMaterialOverrides`.
   * The values here stay the single source of truth: a mode borrows a material for as long as it
   * is active and hands back the original on the way out. Nothing should write to these directly.
   */
  materials: Readonly<Record<string, THREE.Material>>;
  setExplode: (amount: number) => void;
  setPartVisible: (id: string, visible: boolean) => void;
  provenance: {
    route: string;
    exactnessTier: string;
    thicknessConfidence: number;
  };
};

export type ModelOptions = {
  detail?: DetailLevel;
};

// --- measured constants (normalized-1000 / 100) -----------------------------

const U = 0.01;
const n = (value: number) => value * U;

/**
 * Depth reference for the whole blade.
 *
 * `T` is the shell's total front-to-back thickness through the lower-middle blade. Nothing on
 * the blade is authored as an absolute Z any more: every inner layer is written as *the surface
 * under it plus its own step*, evaluated at the point it is asked about. The chain is the point —
 * the order cannot be reversed, and no layer can sink back inside the one below it, by editing
 * one number.
 *
 *   shell surface  →  + SKIN_STEP (insert)  →  + SKIN_STEP (core)  →  the diamond's seat
 *
 * **The two inner crystals are skins, not bosses.** The crop is what settles that. At 16×
 * NEAREST in `measure_authority`'s own weapon-local frame (`spec/zoom-relief/`), the purple
 * field's boundary against the pale shell measures 0–3 units across at every height sampled
 * (Y = 140…360, both sides) — one source pixel or less, with no bevel ramp inside it. And the
 * purple's own cross-section is rim-BRIGHT, centre-DARK by 20–25 luminance levels from Y = 160
 * upward, which is the inverse of what a plateau raised toward the viewer would shade like. The
 * diamond is the opposite reading and it is unambiguous: centre-bright over rim-dark, by +32 at
 * Y = 80 and +46 at Y = 90, with a specular apex. So the artwork carries one raised body on this
 * blade, and it is the stone.
 *
 * Depth itself the crop cannot answer — it is one flat view — so `SKIN_STEP` is directed at the
 * build's standing thickness confidence of 0.35. Its size is set by the review captures: the
 * orthographic views run 584 × 1168 px over a frame of ~11.4 world units, i.e. ~1.02 normalized
 * units per pixel, so 0.05 T = 1.4 units is about 1.4 px of visible rim in the side-thickness
 * views — the thinnest layer this rig resolves at all.
 */
const SHELL_HALF_DEPTH_REF = 14;
const T = SHELL_HALF_DEPTH_REF * 2;
/** One skin's thickness, front and rear, measured normal to nothing — it is a pure Z offset. */
const SKIN_STEP = 0.05 * T;

/**
 * The leather grip is a plain octagonal COLUMN — one constant width from the guard to its
 * measured lower edge — and the hilt is organised around that fact. It carries no widened tang
 * and no collar, and since integration #16 the two jaws do not close on its flanks either: its
 * flat top lies UNDER their floor.
 *
 * `GRIP_HALF_WIDTH` is the CIRCUMRADIUS `polygonSection` wants. An 8-gon's front-view half-width
 * is that times `cos(π/8)` = 11.087, which is the number the jaws' floor has to cover; it is not
 * a constant here because nothing in the factory needs it any more — the pair that did
 * (`OCTAGON_REACH`, `GRIP_REACH_X`) fed only the retired `CLAMP_INNER_X`, and `audit_records.py`
 * re-derives the reach itself when it checks the coverage. Measured grip width is 20 against the
 * master prompt's 24–32 starting contract — the artwork wins.
 */
const GRIP_HALF_WIDTH = 12;

/**
 * Where the crop's dark guard mass stops. **No longer a structural plane, and that is a
 * correction, not a measurement changing.**
 *
 * MEASURED, and the measurement stands. Walking the crop's rows in weapon-local units
 * (`spec/zoom-guard/family-map-8x-grid.png`), the guard's solid mass runs unbroken across the
 * whole width down to Y = −8; the background first opens beside the grip at Y = −12 (a slot at
 * x = 5…14) and has reached x = 33 by Y = −16.
 *
 * What changed is which PART is down there. The user's own sketch
 * (`references/04-user-sketch-guard.png`) draws the two jaws with a flat floor and the two arms
 * growing out of their OUTER corners, and it draws open paper between the grip column and each
 * arm below that floor. So the hilt's structural floor is `CLAMP_FLOOR_Y` = 13 — the jaws' own
 * lower edge — and everything below it is the grip column and the two raked arms, which do not
 * meet. The crop reads unbroken dark there and the sketch does not; the sketch is the higher
 * authority for the guard and this build follows it. Recorded in the guess list rather than
 * split the difference.
 *
 * All that still reads this number is one subdivision station in the grip's own loft, which is
 * why it keeps its measured value and its name.
 */
const GUARD_UNDERSIDE_Y = -13;

/**
 * The crystal clamp jaws ARE the blade socket, and now they are also the guard's own floor.
 * There is no separate central socket component, no bridge under them and no grip tang: the two
 * prisms carry the blade into the hilt on their own, and the grip's column butts their floor face
 * to face (#16) rather than being clamped between them.
 *
 * Right side, mirrored for the left. **A TRIANGLE — three points, no fourth.** Correction, the
 * user's own sketch `references/04-user-sketch-guard.png` (the shapes it labels ① and ②): the jaw
 * is a general triangle whose inner slanted edge runs along the central stone, not a right
 * triangle with a vertical inner face. Every vertex is a vertex of a part this jaw actually meets:
 *
 *  1. `[17, 55]` — the gem's waist vertex, `(GEM_HALF_WIDTH, GEM_WAIST_Y)`. The AUTHORITY point:
 *     the diamond's own widest line, the height the shell's lower taper starts from and the base
 *     of both blade skins. Nothing may move it.
 *  2. `[0, 13]` — the gem's CULET, `(0, GEM_BASE_Y)`. So the edge 1→2 IS the diamond's own
 *     lower-right edge: the jaw and `rootDiamondGem{Front,Rear}` are parallel and flush along its
 *     whole length, meeting on a line with no gap and no overlap, which is what the sketch draws
 *     and what the four-point outline had lost. The four-point version replaced this edge below
 *     Y = 37.4 with a VERTICAL plane at the grip column's own flank so the column could be inserted
 *     between the two jaws; that plane is what made the jaw read as a right triangle, and it also
 *     opened a wedge — 9.89 units wide at the culet, closing at the knee — through which the pale
 *     shell showed between the stone's flank and the jaw, where the artwork has one dark block.
 *     That wedge was on the previous pass's own guess list as the price of the plane. The column
 *     is no longer inserted between the jaws (its top lands flat on their floor instead), so the
 *     plane has no job left and the outline returns to the stone's own edge.
 *  3. `[34, 13]` — the outer lower vertex. Its 34 is directed and unchanged; its HEIGHT is the
 *     culet's, which is what makes the lower edge ONE HORIZONTAL LINE from the axis outward.
 *
 * Two relations fall out of that and both are construction rather than coincidence:
 *
 *  · the two jaws' lower edges TILE, end to end: `[0, 13]…[34, 13]` and its mirror lay side by
 *    side across `−34…34` with no gap and no overlap, so their combined length is exactly the
 *    shell's own lowest edge — integration #15, and `SHELL_STATIONS`' base row is that vertex;
 *  · the grip column's flat top (front-view half-width 11.087) sits entirely under them, face to
 *    face on this same plane — integration #16, and `GRIP_TOP_Y` is `CLAMP_FLOOR_Y`;
 *  · each connector arm's root cap has its LOWER RIM on the outer vertex — integration #17, and
 *    `CONNECTOR_ROOT` is that vertex plus one `CONNECTOR_RADIUS` along the cap's own normal.
 *
 * Y = 13 is the guard's structural floor, not `GUARD_UNDERSIDE_Y` = −13 any more. All three edits
 * that follow from that ARE made: see `SHELL_STATIONS`' base row, `GRIP_TOP_Y` and
 * `CONNECTOR_ROOT`.
 *
 * It is declared before the shell because the shell's base plane is derived FROM it.
 */
// Typed as a fixed 3-tuple, not `[number, number][]`, so the three constants below can index it
// without a null check — and so that adding a fourth point is a compile error rather than a
// silently ignored row.
const CLAMP_OUTLINE: [[number, number], [number, number], [number, number]] = [
  [17, 55], // inner upper — the gem's waist vertex, the authority line
  [0, 13], // inner lower — the gem's culet: edge 1→2 is the stone's own lower-right edge
  [34, 13], // outer lower — the horizontal floor, on the culet's plane
];
/** Real thickness, extending equally front and rear. Deeper than the shell so it shows both sides. */
const CLAMP_HALF_DEPTH = 16;

/**
 * The three numbers the rest of the hilt is hung on, read OUT of the outline rather than typed a
 * second time. Move a vertex in the table above and the shell's base, the grip's top face and
 * both connector arms follow it in the same edit.
 *
 *  · `CLAMP_FLOOR_Y` — the jaws' one horizontal lower edge. The hilt's structural floor: the
 *    plane the shell's base row and `GRIP_TOP_Y` both sit on.
 *  · `CLAMP_FLOOR_SPAN` — the LENGTH of one jaw's floor edge, `[0, 13]…[34, 13]`, i.e. 34. The
 *    two of them tile end to end across `−34…34` with no gap and no overlap, so their combined
 *    length is 68 — and because the inner one of the two vertices is on the axis, one jaw's floor
 *    LENGTH is also the shell's base HALF-width. `SHELL_STATIONS`' base row is therefore this
 *    constant, and integration #15's "the shell's lowest edge equals the two jaws' floor edges
 *    added together" is one substitution rather than a coincidence to re-check in a comment.
 *
 * The outer vertex `(CLAMP_FLOOR_SPAN, CLAMP_FLOOR_Y)` = `(34, 13)` is where three parts meet and
 * nowhere else: the jaw's own corner, the shell's lowest corner (#15) and the connector arm's
 * root cap's LOWER RIM (#17). `CONNECTOR_ROOT` is that vertex offset by one `CONNECTOR_RADIUS`
 * along the cap's normal and has to be written as literals for the audit's parser, and
 * `audit_records.py` recomputes it from this table so the two cannot drift apart in silence.
 */
const CLAMP_FLOOR_Y = CLAMP_OUTLINE[2][1];
const CLAMP_FLOOR_SPAN = CLAMP_OUTLINE[2][0] - CLAMP_OUTLINE[1][0];

// DELETED here, all under one rule: a factory copy of a formula a gate re-derives is a second
// definition waiting to disagree with the first. Safe because nothing outside this file names
// them — `audit_records.py` and `measure_guard_joints.py` are the only parsers and both read the
// NUMERIC tables (`CLAMP_OUTLINE`, `SHELL_STATIONS`, `INSERT_OUTLINE`) plus named scalars.
//   · `clampOuterEdgeX` / `clampInnerEdgeX` — the audit's daylight sweep rebuilds both edges from
//     `CLAMP_OUTLINE` itself, on purpose, so it cannot inherit a bug from the code it audits.
//   · `CLAMP_GRIP_OVERLAP` / `CLAMP_INNER_X` — #15 gave the shell a base edge of its own and #16
//     landed the grip's top under the jaws, so neither the plane nor the tenon describes anything.
//   · `SHELL_BASE_Y` — an alias with no reader (TS 6133); `SHELL_STATIONS`' base row indexes
//     `CLAMP_OUTLINE` directly, which is the whole point of #15.

/**
 * Blade shell cross-sections: [Y, halfWidth, halfDepth]. See image-analysis Layer 7 #2.
 *
 * The crop's own profile is authority from Y=110 up, where it agrees with reference 03's
 * orthographic front view to within 3 units. Below Y=110 the crop reads a 96-unit half-width
 * on the left against 81 on the right — a one-sided flare that reference 03 shows is a
 * projection/occlusion artifact, not geometry: its front view is monotonic, peaking at 83 just
 * above the socket.
 */
const SHELL_STATIONS: [number, number, number][] = [
  // Below the diamond's waist the shell is a TRAPEZOID: ONE straight taper, from Y=55 down to the
  // two clamps' outer edges, with no station in between. Correction pass 2 §5 sanctions exactly
  // this shape ("the lower white shell may taper inward toward the red diamond and clamp
  // assembly, but it must stop at the upper boundary of the clamps"). It replaces a neck that
  // pinched at Y=42 and then fell away at twice that rate below it, which read as a step.
  //
  // Measured off the crop at 8× NEAREST in measure_authority's own weapon-local frame, taking the
  // RIGHT edge because the left carries the known one-sided flare: the pale blade body holds a
  // flat 81–83 half-width from Y=110 all the way down to Y≈46, then tapers to ≈35 at Y=4 where
  // the hilt occludes it. A least-squares fit through those 18 rows (Y=4…46, skipping 24–30
  // where the pale run merges with a rod's specular highlight) gives 1.131 per unit of height,
  // RMS residual 1.71 — sub-pixel, since one source pixel is 2.34 units. So the 82 below is
  // measured. Two departures are deliberate and neither can be read off the crop:
  //   · the taper STARTS at the diamond's waist (Y=55), not at the measured knee at Y≈46;
  //   · it STOPS on the jaws' floor, at their own outer vertex, and the trapezoid's slope is
  //     that stop divided by that start rather than a number of its own: (83 − 34) / (55 − 13)
  //     = 1.1667 per unit of height, against the crop's least-squares 1.131 — 3.1% apart, and
  //     the fit's own RMS residual is 1.71, so the two lines are inside each other's error over
  //     the whole 42-unit run. Integration #15 is what pins the lower end there, and it is an
  //     equality of LENGTHS: the shell's lowest edge is 2 × 34 = 68 and the two jaws' floor
  //     edges are 34 each, laid end to end across the same span on the same plane.
  //
  // This shape also stops paying for driver clearance with width: the old Y=42 station was held
  // 12% under the crop to buy the correction spec's 1.00-diameter front-view gap, and the
  // trapezoid gets 1.19 without it. `audit_records.py` recomputes that gap from these stations,
  // and its parser reads NUMERIC literals only — so the 55 has to stay written as 55 even though
  // it is GEM_WAIST_Y, or the audit would silently score a different blade from the built one.
  //
  // THE BASE ROW, and it IS `CLAMP_OUTLINE`'s outer lower vertex — written as the two constants
  // rather than as literals, so that moving that vertex moves the shell's base with it in the
  // same edit. This is also why it is the ONE row here that is not numeric: `audit_records.py`'s
  // row regex deliberately skips it and prepends the vertex from the outline instead, so a base
  // typed as a second pair of literals somewhere would show up there as a duplicated first row
  // rather than being silently accepted. Every other row has to stay literal for the same parser
  // (see the 55 note above).
  //
  // The two jaws' floor edges are `CLAMP_FLOOR_SPAN` = 34 each and tile across `−34…34`; this row
  // is `CLAMP_FLOOR_SPAN` again, so the shell's lowest edge is 68 and their sum is 68. That equality
  // is integration #15 and it is one substitution, not a coincidence.
  //
  // It replaces TWO rows: a near-degenerate tenon at Y = −13 of half-width 11.087, and the
  // 31.735 the taper happened to reach at Y = 13. The tenon was the stub that plugged into the
  // slot between the two jaws, and integration #16 took the slot away — the grip column's top
  // lands flat UNDER the jaws now, so there is no slot for a tenon to enter. What the tenon was
  // worth is worth keeping in mind anyway: collapsed to a POINT its last band was eight slivers
  // off a degenerate ring, the shell's front and rear surfaces stopped being triangulated as
  // mirrors, and the stone read 93.6% proud on the front against 54.3% on the rear with the
  // GEOMETRY symmetric throughout. This row is a full-width ring, so that failure mode is gone by
  // construction rather than by a margin.
  //
  // 11 is the half-depth this build has always had at the socket, and it is here so that seating
  // the crystal's root on the jaws does not thin the blade where the diamond sits on it. Without
  // a depth knee the stone's mirror-colour residual goes to 0.0156 against a tolerance of 0.0039
  // — the two halves' quad diagonals straddle a quantiser boundary — which is how it was found.
  [CLAMP_FLOOR_Y, CLAMP_FLOOR_SPAN, 11],
  // The trapezoid's own quarter points, carrying NO shape: 58.5 is the 13 → 55 line evaluated at
  // 34 and 12.25 is the depth knee's, so the analytic surface is exactly the two end rows and
  // `audit_records.py`'s taper check — every station below the waist on one straight line —
  // passes on them unchanged. They are here because the SURFACE and the MESH are not the same
  // thing.
  //
  // Between two rings `loft` writes two triangles per quad, and a triangulated quad is not the
  // ruled surface through its four corners: it agrees on the rails and departs in the middle, by
  // more the longer the band and the faster the section moves along it. Y = 13 → 55 was this
  // shell's longest band and its fastest — 42 units of height over which the half-width more than
  // doubles — and the stone is seated on the ANALYTIC surface across the whole of it. Measured by
  // the harness's conformity probe with this row deleted: the stone's underside stands +0.6203
  // units clear of the crystal at (−8.5, 34) and reaches 0.2017 INSIDE it at (+4.3, 23.5). The
  // two signs are not a contradiction; they are the same fact seen on the two sides of the blade,
  // because `loft` splits every quad from `lower[i]` to `upper[i+1]` and that rule is not
  // mirror-symmetric. Halving the band takes the pair to the figures §8 records.
  [23.5, 46.25, 11.625],
  [34, 58.5, 12.25],
  [44.5, 70.75, 12.875],
  [55, 83, 13.5], // = GEM_WAIST_Y: the diamond's widest line, where the trapezoid starts
  [70, 83, SHELL_HALF_DEPTH_REF], // the widest point, moved up 25 from Y=45 (budget is 29)
  [110, 81, SHELL_HALF_DEPTH_REF],
  [300, 73, 13],
  [500, 63, 11],
  [575, 54, 10], // the taper's knee
  [650, 34, 8],
  [760, 0, 0], // tip
];

/**
 * `ridgedSection`'s two shape ratios, hoisted out of it because `shellFrontDepth` below has to
 * evaluate the same surface. Two copies of 0.58 is how the gem's girdle would quietly stop
 * clearing the shell the day the blade's bevel is re-cut.
 */
const RIDGE_SHOULDER_X = 0.58;
const RIDGE_SHOULDER_Z = 0.72;

/**
 * The shell's own front-surface depth at `(x, y)` — the surface an inner crystal has to break
 * through to be seen as an inner crystal at all.
 *
 * The shell is SOLID, so it is discarded by the depth test wherever an inner layer is nearer the
 * camera and it OCCLUDES that layer outright everywhere else. An inner crystal therefore renders
 * exactly where its own Z clears this value, and not at all anywhere behind it. That single
 * inequality is the whole "can you read the diamond" criterion, which is why the gem's girdle
 * below is derived from it instead of tuned against a render until it looked right.
 *
 * **The criterion did not change when the shell stopped being translucent, and that is worth
 * saying because the failure mode did.** A translucent shell washed a buried layer out; a solid
 * one deletes it. The inequality that decides which happens is this one, and it is enforced
 * pointwise by `check_centerline.py`'s stack probe rather than by how the shell composites — see
 * `RELATIONSHIPS.md` §5, "revealing the crystals by dropping the shell's opacity fails here".
 */
const shellSectionAt = (y: number): { halfWidth: number; halfDepth: number } => {
  const found = SHELL_STATIONS.findIndex(([stationY]) => stationY >= y);
  const i = found <= 0 ? 1 : found;
  const [y0, w0, d0] = SHELL_STATIONS[i - 1]!;
  const [y1, w1, d1] = SHELL_STATIONS[i]!;
  const t = y1 === y0 ? 0 : Math.min(1, Math.max(0, (y - y0) / (y1 - y0)));
  return { halfWidth: w0 + (w1 - w0) * t, halfDepth: d0 + (d1 - d0) * t };
};

const shellFrontDepth = (x: number, y: number): number => {
  const { halfWidth, halfDepth } = shellSectionAt(y);
  const shoulderX = halfWidth * RIDGE_SHOULDER_X;
  const shoulderZ = halfDepth * RIDGE_SHOULDER_Z;
  const ax = Math.abs(x);
  if (ax >= halfWidth) return 0; // the section falls to zero depth at the cutting edge
  return ax <= shoulderX
    ? halfDepth + (shoulderZ - halfDepth) * (ax / shoulderX)
    : shoulderZ * (1 - (ax - shoulderX) / (halfWidth - shoulderX));
};

/**
 * Where `shellFrontDepth` changes slope at height `y` — the shell's own ridge shoulder.
 *
 * A skin has to carry a ring point exactly here or its outer polyline cuts the corner and dips
 * back inside the shell near its own rim. Read from the shell rather than from the skin's width,
 * which is a different number entirely: at Y=42 the shell's shoulder is at 38.9 while the
 * insert's own half-width is 43.
 */
const shellShoulderXAt = (y: number): number => shellSectionAt(y).halfWidth * RIDGE_SHOULDER_X;

/**
 * Linear interpolation over a `[Y, halfWidth]` outline, returning 0 outside its span.
 *
 * Shared by the insert and the dark core so `bladeStackTop` can ask "is this point inside that
 * layer, and how wide is the layer here" with one rule.
 */
function outlineHalfWidthAt(outline: [number, number][], y: number): number {
  const first = outline[0]!;
  const last = outline[outline.length - 1]!;
  if (y < first[0] || y > last[0]) return 0;
  for (let i = 1; i < outline.length; i += 1) {
    const [y0, w0] = outline[i - 1]!;
    const [y1, w1] = outline[i]!;
    if (y0 <= y && y <= y1) return y1 === y0 ? w0 : w0 + ((w1 - w0) * (y - y0)) / (y1 - y0);
  }
  return 0;
}

/**
 * The insert's OUTLINE — `[Y, halfWidth]`, measured. It carries no depth of its own any more:
 * the skin's depth is the shell's own surface at each point, plus one `SKIN_STEP`.
 *
 * The three measured stations are the base (Y=42, half-width 43), the knee (Y=380, 28) and the
 * apex (Y=480). **The four shell stations between them are interpolated in and listed too**, and
 * that is a correctness condition, not tidiness: a skin whose rings only sit at 42, 380 and 480
 * is a ruled surface between those heights, and the shell bulges above the chord in exactly that
 * span — 14.0 at Y=110 against a chord of 12.62. The skin would have cleared it by 0.02 instead
 * of by 1.40 and z-fought the shell down the middle of the blade. A skin follows its host in Y
 * as well as in X or it is not a skin.
 */
const INSERT_APEX_Y = 480;
const INSERT_OUTLINE: [number, number][] = [
  // Correction D: the film's lower edge is the AUTHORITY line — `CLAMP_OUTLINE`'s inner-upper
  // vertex at Y = 55, the same line the dark core's base, the diamond's waist and the shell's
  // lower taper all start from. It used to sit at the crop's own lowest violet row, 42.6, which
  // put the film's base 13 units below every other feature at the socket and left it hanging
  // over the jaws. The half-width is NOT re-typed: it is this outline's own measured taper
  // (43 at Y=42, 28 at Y=380) evaluated at 55, so the film is truncated at the authority line
  // rather than re-shaped by it.
  [55, 42.42], // = GEM_WAIST_Y
  [380, 28],
  [INSERT_APEX_Y, 0],
];
/** The insert's front-view half-width at height `y`; 0 outside its own span. */
const insertHalfWidthAt = (y: number): number => outlineHalfWidthAt(INSERT_OUTLINE, y);

/**
 * The root diamond. Apex, base and half-width are measured: bright-red pixels run Y = 12.9…97.3
 * and the waist measures 34.2 wide. Its waist is the line two other components are pinned to —
 * the dark core's base sits on it and the shell's trapezoid starts from it — so it is named.
 *
 * `GEM_WAIST_Y` is the rhombus's own vertical centre, not the crop's widest row: the crop reads
 * widest at Y = 50, five units low. 55 is kept because `CLAMP_OUTLINE`'s inner-upper vertex is
 * already there — the jaws' contact line IS this waist, by correction pass 2 §3 — and moving it
 * would drag the clamp outline, the shell's derived base and the driver clearance along with it.
 */
const GEM_APEX_Y = 97;
const GEM_BASE_Y = 13;
const GEM_HALF_WIDTH = 17;
const GEM_WAIST_Y = (GEM_APEX_Y + GEM_BASE_Y) / 2; // 55 — CLAMP_OUTLINE's inner-upper vertex

/** The rhombus outline: the diamond's front-view half-width at height `y`. */
const gemHalfWidthAt = (y: number): number =>
  GEM_HALF_WIDTH * Math.max(0, 1 - Math.abs(y - GEM_WAIST_Y) / (GEM_WAIST_Y - GEM_BASE_Y));

// U2 WAS "authored from reference 03, confidence 0.45, because the crop occludes it above
// Y=98.8". **The apex is MEASURED now, and 98.8 was an instrument artifact.** `classify()` in
// `measure_authority.py` only admits a pixel to the "red" family at s ≥ 0.35 with a red hue, and
// the core is red-tinted only where it flanks the gem; above the gem it is a near-black wedge on
// violet, so its hue falls into the "insert" family and its darkest rows into "grip". The
// red-family blob therefore stops at the gem's shoulder and says nothing about the wedge above
// it. At 8× and 16× NEAREST that wedge is plainly in the crop and runs most of the way up the
// violet insert — `spec/zoom-relief/core-apex-{8,16}x-grid.png`.
//
// `spec/measure_core_apex.py` reads it the way it presents: as a darkening of the insert along
// the centre line, against the insert's own body at |x| = 30…36. Least-squares over the wedge's
// own half-width, every row from the gem's apex up (86 rows), gives
//
//     halfWidth = 26.152 − 0.1400 · Y      RMS residual 0.60 units = 0.26 SOURCE PIXELS
//
// so the wedge is straight-sided, and it reaches zero width at **Y = 186.9**. A single-row
// half-maximum crossing puts it at 183, and sweeping the threshold across 0.35…0.65 of the
// wedge's own contrast moves the fit only between 178 and 195 — the number is the wedge's
// GEOMETRY, not the threshold. 187 is that fit, rounded.
//
// Two consequences, and the second is why this outline lost a point:
//
//  1. The base stays DIRECTED at 21 on the diamond's waist, so the dark triangle rises out of the
//     diamond's widest line and the two share one horizontal edge. The same fit extrapolated down
//     to Y = 55 reads 18.45 — within 1.1 source pixels of that directed 21 — so the measurement
//     now CORROBORATES the directed base instead of being silent about it. (The crop's own dark
//     pixels do run to Y≈10, far below the waist, and reach 44 wide at Y=38…42; that is the gem's
//     rim-dark shading, not the core, and directed still wins there.)
//  2. **The knee at (100, 0.184 × half-width) is gone.** It was never measured: it was the shape a
//     triangle is forced into when its tip is cut off at 118. It put the core at 3.86 half-width
//     at Y = 100 where the artwork measures 13.1 — nine units, four source pixels, in the wrong
//     direction. Two points now, base to apex, which is also what the part is called.
//
// Like the insert, this is an OUTLINE only — the second skin's depth is the first skin's surface
// plus one more `SKIN_STEP`. `skinStations` still lists the shell stations inside its span
// (70, 110), for the reason INSERT_OUTLINE gives.
const CORE_APEX_Y = 187;
const CORE_BASE_Y = GEM_WAIST_Y;
const CORE_HALF_WIDTH = 21;
const CORE_OUTLINE: [number, number][] = [
  [CORE_BASE_Y, CORE_HALF_WIDTH],
  [CORE_APEX_Y, 0],
];
/** The dark core's front-view half-width at height `y`; 0 outside its own span. */
const coreHalfWidthAt = (y: number): number => outlineHalfWidthAt(CORE_OUTLINE, y);

/**
 * The depth of the topmost blade layer at `(x, y)` — the surface the diamond has to sit ON.
 *
 * This is the whole relief chain in one function: the shell's own front surface, plus one
 * `SKIN_STEP` wherever the insert skin covers the point, plus one more wherever the dark-core
 * skin covers it. It is evaluated POINTWISE rather than compared as bounding boxes, which is the
 * thing the old ladder could not do: a bbox says how deep a layer's deepest vertex is, and the
 * defect this replaces was the diamond's rim at 15.53 sitting under the dark core's plateau at
 * 18.62 over the whole of their overlap (Y = 56…97). The gem passed every depth assertion and
 * measured 93.4% proud OF THE SHELL while its rhombus outline was buried in the layer directly
 * beneath it, because nothing compared the two.
 *
 * Changing a skin's thickness, or either outline, now moves the diamond's seat automatically.
 *
 * **A layer of zero half-width covers NOTHING, and not even its own axis.** The containment test
 * used to be `|x| <= halfWidthAt(y)` against an interpolation that returns 0 outside the layer's
 * span, and `0 <= 0` is true — so on the centre line, at every height where a film does not
 * exist, this function still added that film's `SKIN_STEP`. It is one x-coordinate wide, which is
 * why it survived: the only geometry that samples the seat exactly at `x = 0` is the stone's own
 * ring, and the stone is the only thing seated on this surface. Measured by the harness's
 * conformity probe on the build this replaces, the stone's underside stood **+2.8 units — both
 * skin steps — clear of the crystal on the centre line at Y = 23.5**, where neither film exists.
 * `covers()` asks the span first, so a film that is not there cannot lift anything.
 */
const covers = (outline: [number, number][], x: number, y: number): boolean => {
  const halfWidth = outlineHalfWidthAt(outline, y);
  return halfWidth > 0 && Math.abs(x) <= halfWidth;
};
const bladeStackTop = (x: number, y: number): number =>
  shellFrontDepth(x, y) +
  (covers(INSERT_OUTLINE, x, y) ? SKIN_STEP : 0) +
  (covers(CORE_OUTLINE, x, y) ? SKIN_STEP : 0);

/**
 * The stone is SET INTO the blade, and these three depths are the setting. Directed 2026-08-09.
 *
 * Every other layer on this blade LIES ON the surface under it and follows it. The stone did too
 * until this pass, and that is what the directive rejects: `bladeStackTop` climbs **5.8 units**
 * from the culet to the stone's top vertex — 1.2 of that is the shell's own taper and 2.8 of it
 * is one STEP, where both skins begin on the authority line at `GEM_WAIST_Y`. A body that follows
 * that surface has its upper half standing 2.8 further out than its lower half, which is exactly
 * what the side view showed. No shape of stone fixes it, because it is not the stone.
 *
 * So the stone stops following it. Three constants, all derived by sampling the surface under the
 * stone's own footprint rather than typed:
 *
 *  · `GEM_SOCKET_FLOOR` — the stone's flat BASE plane, at the LOWEST the surface gets under the
 *    footprint. Being the lowest is what makes it a socket rather than a shelf: the base is at or
 *    below the crystal at every point, so there is no air anywhere under the stone. The two halves
 *    take it with opposite sign, so their bases are two parallel planes — the directive's words.
 *  · `GEM_GIRDLE_DEPTH` — the LEVEL girdle line, one `GEM_RELIEF_STEP` above the HIGHEST the
 *    surface gets. Highest, not lowest, and not an average: the whole rhombus outline has to break
 *    the surface, and the top vertex is where the surface is highest. Level is the entire point —
 *    it is the line the eye reads as the stone's edge, and it is now one plane instead of a
 *    stepped curve.
 *  · `GEM_HALF_DEPTH` — the apex, `GEM_CROWN_RISE` above the girdle. The rise stays a fraction of
 *    the stone's own half-width rather than a depth: give it a fixed depth and narrowing the
 *    rhombus turns it into a spike.
 *
 * **What this costs is the five-face count, and the geometry is what charges it.** A flat base
 * under a level girdle over a surface that climbs 5.8 units needs a wall between them, and a wall
 * around a rhombus is four faces. 4 crown + 4 socket wall + 1 base. The alternative is a stone
 * that floats over the crystal near the culet, and the wall is the thing the word 鑲嵌 means.
 */
const GEM_RELIEF_STEP = 0.12 * T;
const GEM_CROWN_RISE = 0.38 * GEM_HALF_WIDTH;
const [GEM_SOCKET_FLOOR, GEM_GIRDLE_DEPTH] = (() => {
  // Sampled rather than reasoned: `bladeStackTop` is monotone in neither argument over this
  // footprint — it rises with Y, falls with |x|, and STEPS at the two films' base — so the
  // extremes are not at corners that can be named in a comment. 41 × 41 over the rhombus is
  // finer than the surface's own knees, which are what the extremes actually sit on.
  let lo = Infinity;
  let hi = -Infinity;
  for (let i = 0; i <= 40; i += 1) {
    const y = GEM_BASE_Y + ((GEM_APEX_Y - GEM_BASE_Y) * i) / 40;
    const halfWidth = gemHalfWidthAt(y);
    for (let j = 0; j <= 40; j += 1) {
      const depth = bladeStackTop(-halfWidth + (2 * halfWidth * j) / 40, y);
      lo = Math.min(lo, depth);
      hi = Math.max(hi, depth);
    }
  }
  return [lo, hi + GEM_RELIEF_STEP];
})();
const GEM_HALF_DEPTH = GEM_GIRDLE_DEPTH + GEM_CROWN_RISE;

/**
 * The stone's three cross-sections: `[Y, halfWidth, the RIDGE's depth on the axis]`.
 *
 * **Three rows, and that is what makes the crown a pyramid rather than a roof.** The middle row is
 * the one APEX; the outer two are the rhombus's own culet and top vertex, both on the girdle
 * plane, so the axis profile is two straight segments meeting at a point over the rhombus's
 * centre. Those two segments ARE the crown's two axial lateral edges.
 *
 * **It carried two BAND stations until 2026-08-09**, at `±0.75` of the way out to the tips, both
 * holding the depth at `GEM_HALF_DEPTH` — a plateau three quarters as long as the stone, which is
 * why the side view showed a flat ridge and not a point. They were there to keep the outline
 * proud, and that job belongs to the girdle now, which does it with one plane instead of a band.
 */
const GEM_STATIONS: [number, number, number][] = [
  [GEM_BASE_Y, 0, GEM_GIRDLE_DEPTH],
  [GEM_WAIST_Y, GEM_HALF_WIDTH, GEM_HALF_DEPTH],
  [GEM_APEX_Y, 0, GEM_GIRDLE_DEPTH],
];

/**
 * The heights each skin puts a ring at. Three sources, all derived, none typed in:
 *
 *  1. the layer's own outline knees;
 *  2. every `SHELL_STATIONS` height inside its span — without these the film is a ruled surface
 *     across a curved host and dips back inside it (measured: 2.60 inside the shell at Y ≈ 70,
 *     against a film only 1.40 thick);
 *  3. **every height where the shell's ridge shoulder crosses the film's own rim.** Below that
 *     crossing the ring's shoulder sample is a real shoulder; above it the shoulder has moved
 *     outboard of the film and the sample collapses onto the rim. The ring changes shape there,
 *     and a flat quad spanning the change cuts the corner: without this station the insert dips
 *     0.59 inside the shell at Y ≈ 47.4, x ≈ 42.8. Bisected rather than solved in closed form
 *     because both sides are piecewise linear with knees of their own.
 *
 * The apex is left as the list's last entry and closed by the caller as a zero-width EDGE, so the
 * film's underside is still on its host at the tip.
 */
function skinStations(outline: [number, number][]): number[] {
  const lo = outline[0]![0];
  const hi = outline[outline.length - 1]![0];
  const ys = new Set<number>(outline.map(([y]) => y));
  for (const [y] of SHELL_STATIONS) if (y > lo && y < hi) ys.add(y);
  const sorted = [...ys].sort((a, b) => a - b);
  for (const y of signChangeStations(
    sorted,
    (at) => shellShoulderXAt(at) - outlineHalfWidthAt(outline, at),
  )) {
    ys.add(y);
  }
  return [...ys].sort((a, b) => a - b);
}

/**
 * Every height between two known stations at which `gap` changes sign, found by bisection.
 *
 * Shared by the skins and by the stone, because both need the same thing for the same reason: a
 * ring's SHAPE changes wherever a profile break of the surface under it crosses the layer's own
 * rim, and a flat quad spanning that change cuts the corner. It is bisected rather than solved
 * because both sides are piecewise linear with knees of their own.
 *
 * `gap` must be CONTINUOUS over the range. A layer that simply starts at some height is a STEP in
 * the surface, not a crossing, and feeding one to this would converge on the step from below and
 * plant a spurious ring a float away from it. Steps are handled where they belong — as two rings
 * at the same height, in `GEM_SEAT_RINGS`.
 */
function signChangeStations(known: number[], gap: (y: number) => number): number[] {
  const found: number[] = [];
  for (let i = 1; i < known.length; i += 1) {
    let a = known[i - 1]!;
    let b = known[i]!;
    if (gap(a) === 0 || gap(b) === 0 || gap(a) > 0 === gap(b) > 0) continue;
    for (let step = 0; step < 40; step += 1) {
      const mid = (a + b) / 2;
      if (gap(a) > 0 === gap(mid) > 0) a = mid;
      else b = mid;
    }
    found.push((a + b) / 2);
  }
  return found;
}

const INSERT_SKIN_STATIONS = skinStations(INSERT_OUTLINE);
const CORE_SKIN_STATIONS = skinStations(CORE_OUTLINE);

/**
 * The RIDGE's depth at height `y` — `GEM_STATIONS` interpolated, nothing else.
 *
 * A station added so the stone's UNDERSIDE can follow the surface it is lying on must not move
 * the stone's OUTSIDE, and reading a three-row table is what guarantees it: the table's two
 * segments ARE the pyramid's two axial lateral edges, so a ring inserted anywhere between the
 * culet and the apex lands exactly on the edge that is already there. Anything that re-derived a
 * depth per station would not — the retired `gemDepthAt` returned 20.99 just under `GEM_WAIST_Y`,
 * where the two skins stop, against the 24.785 the apex carries, and would have cut a 3.8-unit
 * notch into the flank at the one height the seat steps.
 */
const gemCrownDepthAt = (y: number): number => {
  for (let i = 1; i < GEM_STATIONS.length; i += 1) {
    const [y0, , d0] = GEM_STATIONS[i - 1]!;
    const [y1, , d1] = GEM_STATIONS[i]!;
    if (y0 <= y && y <= y1) return y1 === y0 ? d0 : d0 + ((d1 - d0) * (y - y0)) / (y1 - y0);
  }
  return 0;
};

/**
 * The heights the stone puts a ring at, and there are only three of them.
 *
 * **This list was derived and eleven entries long until 2026-08-09**, and every one of its sources
 * existed to make the stone's UNDERSIDE follow `bladeStackTop`: the shell's own knees inside the
 * stone's span, the heights where the shell's ridge shoulder or either film's rim crossed the
 * stone's, and a `SEAT_STEP_SPAN` ledge pair at the two films' base, because a stone lying on a
 * ledge has a ledge. A SET stone has no underside to follow — its base is one plane and its wall
 * is vertical — so all of that goes and the ring list is `GEM_STATIONS`' own three heights.
 *
 * Between them the stone's surface is exactly what the constants say: the base and the wall do
 * not move with `y` at all, and the ridge is two straight segments. A station added anywhere
 * would land on geometry that is already there, which is the property the derived list spent
 * eight extra rings buying.
 */
const GEM_SEAT_STATIONS: number[] = GEM_STATIONS.map(([y]) => y);

/**
 * The dark-grey leather connector arms are the horizontal limbs of the T: complete closed
 * cylinders of constant radius, raked outward and downward. Not beams, plates or open channels.
 *
 * **The root and the rake are both derived from the jaw, and that is integration #17.** The
 * user's sketch (`references/04-user-sketch-guard.png`) draws each arm growing out of its
 * triangle's OUTER corner — at 8× the two long edges of each arm converge on the same heavy ink
 * junction the triangle's outer lower vertex sits on (`spec/zoom-guard/sketch-arm-root-*-8x.png`).
 * So:
 *
 *  · **the cap's LOWER RIM is `CLAMP_OUTLINE`'s outer lower vertex**, not the cap's centre. The
 *    root cap is a diameter laid along the flank, and the directive of 2026-08-11 is which END of
 *    that diameter the jaw's corner is: the arm hangs OFF the corner and runs up the flank, it
 *    does not straddle the corner with half of itself under the guard's floor.
 *  · `CONNECTOR_ANGLE_DEG` is `−atan((83 − 34) / (55 − 13))`, the shell's lower taper turned into
 *    an angle. A cap perpendicular to that axis has its diameter along `(−sin a, cos a)`, whose
 *    x:y ratio is then exactly the taper's — so the cap's WHOLE diameter lies ON the crystal's
 *    lower slanted flank, from `(34, 13)` at the lower rim through `(46.148, 23.413)` at the
 *    centre to `(58.296, 33.825)` at the upper rim, and the front-view residual against
 *    `shellSectionAt` is 0.000005 at worst over the whole span, rim to rim.
 *
 * **`CONNECTOR_ROOT` is therefore DERIVED and not read**: it is that corner plus one
 * `CONNECTOR_RADIUS` along the cap's own in-plane unit normal `(−sin a, cos a)`. What it was
 * until 2026-08-11 is the corner itself, which put the cap's lower rim at `(21.852, 2.587)` —
 * 10.413 units BELOW the guard's floor, hanging in open air under the jaws. That is the defect
 * this replaces; the arm moved perpendicular to its own axis, so its rake, its length and its
 * inner silhouette LINE are all untouched.
 *
 * Written as literals because `spec/audit_records.py`'s parser reads named scalars out of this
 * file; it recomputes both from `CLAMP_OUTLINE`, `SHELL_STATIONS` and `CONNECTOR_RADIUS` and
 * fails if they drift, the same contract `CLAMP_OUTLINE` itself is held to. Seven decimals
 * because the audit holds the derived lower rim to 1e-6 of the corner and five would leave only
 * a factor of 4 in hand.
 *
 * What this REPLACES is correction C's `CONNECTOR_INSET` — see the note below it. What it does
 * not touch is `CONNECTOR_RADIUS`, still directed at 16 against a crop reading 32.0 units across
 * a row (31% narrow) and still recorded rather than chased, because changing it moves
 * `driverRootRadius()`, `spinnerSeat()`, the driver-clearance gate and the silhouette at once.
 *
 * **One consequence is deliberate and is recorded rather than hidden.** The rim this pins is the
 * octagon's CIRCUMSCRIBED one; an 8-gon's front-view silhouette is carried by its FACES, one
 * apothem in. So the leather's own lower face starts `16 × (1 − cos(π/8))` = 1.218 further along
 * the cap, at `(34.925, 13.793)`, and a notch `1.604` wide and `0.793` tall opens between the
 * jaw's corner and the arm. `audit_records.py`'s handover clause asserts that notch is EXACTLY
 * `R(1 − cos(π/8)) / |sin a|` and nothing more — an equality in closed form, not a slackened
 * threshold.
 */
const CONNECTOR_ROOT: [number, number] = [46.1481047, 23.4126631]; // = corner + 16·(−sin a, cos a)
const CONNECTOR_ANGLE_DEG = -49.3987; // = −atan((83 − 34) / (55 − 13)), the shell's lower taper
/**
 * **DERIVED as of 2026-08-13, and it stopped being directed the moment the crop was asked a
 * different question.**
 *
 * The user directed the arms LONGER and the spinner caps SHORTER against the artwork. What that
 * turned into is not a bigger directed number: it is the observation that the crop pins the arm's
 * outer end as a POINT, and that a length has one closed-form best answer to a point.
 *
 * - **X.** `spec/measurements.json` segments both gold caps out of the artwork and each blob gives
 *   two estimates of the spinner's axis, its bbox centre and its pixel centroid: |x| = 76.50,
 *   77.75, 86.00, 87.45, mean **81.925**.
 * - **Y.** Those same caps' tops — their topmost GOLD pixels — sit at −61.5 and −45.4, mean
 *   **−53.45**. That is not the end-cap centre: the build's own topmost gold pixel sits
 *   `9.428` ABOVE its end-cap centre, where the shoulder's flank crosses the arm's end-cap plane,
 *   and the same offset carries the crop's reading down to an end-cap centre of **−62.878**.
 *
 * So the crop's arm end is **(81.925, −62.878)** — and `CONNECTOR_ROOT` and `CONNECTOR_ANGLE_DEG`
 * are both locked, so the built end can only sit on the ray `CONNECTOR_ROOT + L·(cos a, sin a)`.
 * That point is **28.993 units off that ray**, at every length, and no length recovers it: the
 * shortfall belongs to the rake. The length that gets CLOSEST is the perpendicular projection,
 *
 *     L = (cropArmEnd − CONNECTOR_ROOT) · (cos a, sin a) = 88.8001
 *
 * and `spec/audit_records.py` recomputes it every run and fails if this literal drifts, exactly as
 * it does for `CONNECTOR_ROOT`. Seven-decimal-adjacent for the same reason: the clause is an
 * equality to 5e-4, not a slackened band.
 *
 * It moved 0.055 on 2026-08-08, and not by hand: widening `SPINNER_TOP_RADIUS` moves where the
 * shoulder's flank crosses the arm's end-cap plane, so the offset that carries the crop's gold-cap
 * top down to an arm end moves with it, and this length is a function of that offset.
 *
 * **What it does not do is solve either pin, and both misses got worse than the value it
 * replaces.** The axis lands at 103.938 against 81.925 — 22.013 units, 9.4 source pixels, where
 * the directed 72 was 4.73 — and the cap top lands at −34.58 against −53.45, 18.9 units high where
 * 72 was 31.6. It is still the value that ships, because it is the only one on the ray that no
 * other length beats on DISTANCE to the point the crop actually pins:
 *
 * | length | what it solves | axis \| cap top | miss to the crop's arm end |
 * |---|---|---|---:|
 * | 54.97 | the X pin exactly | 81.92 \| −8.90 | 44.554 |
 * | 72 | nothing; directed 2026-08-12 | 93.01 \| −21.83 | 33.509 |
 * | **88.8001** | **the distance** | 103.94 \| −34.58 | **28.993** |
 * | 113.65 | the cap-top pin exactly | 120.11 \| −53.45 | 38.187 |
 *
 * All four rows are run as brackets by `audit_records.py`. The silhouette is what it costs and it
 * is recorded red rather than re-floored — see `spec/CURRENT-MODEL.md` §8 for the chain and §11 G4
 * for why one parameter cannot hold two pins.
 */
const CONNECTOR_LENGTH = 88.8001;
const CONNECTOR_RADIUS = 16;
const CONNECTOR_SIDES = 8;

// `CONNECTOR_SHELL_OVERLAP`, `CONNECTOR_INSET` and `connectorInnerEdgeX` are DELETED here.
// The first two were correction C's bisected burial depth, and the bisection existed only because
// its anchor (28, 8) was a point on the arm's axis rather than a joint. #17 makes the cap coplanar
// with the shell's flank BY CONSTRUCTION, so correction C's sentence — "the arm's inner silhouette
// edge and the shell's slanted edge are ONE line" — holds to 0.000000 with nothing to search for.
// Its measurement stands and is unaffected: the crop's slanted edge fits `30.62 + 1.2616·Y`
// against this build's `34 + 1.1667·Y`, 7.5% on the slope; `spec/guard-joints.json`.
// The third goes by the rule the clamp edges went by — the daylight sweep re-derives the inner
// edge from `CONNECTOR_ROOT`, the rake and the 8-gon's inradius, and no TypeScript called it.

/**
 * Spinner end piece: a faceted frustum hanging STRAIGHT DOWN, the same orientation as
 * `pointedMetalPommel` — lathed about the Y axis, so its rotation is identically zero. It used
 * to continue along the connector's own −50° axis so the two end caps met flush.
 *
 * The crop asks for vertical too, so this is not a directive overriding a measurement. De-rotated
 * to weapon-local upright, the vector from each arm's outer end to its own cap centroid reads
 * −100.1° (right) and −75.0° (left) — mean −87.6°, against the pommel's −93.8° — and PCA of the
 * two gold blobs gives −99.8° and −75.2°. Nothing in the crop reads −50°. The ±12° spread about
 * vertical is the crop's own left/right asymmetry, which a symmetric model cannot carry.
 *
 * That reading is REPRODUCED rather than remembered: `measure_spinner_taper.py` re-does the PCA
 * on every run and writes each cap's tilt to `spec/spinner-taper.json` —
 * `crop.right.axisTiltFromVerticalDeg` = −10.2 and `crop.left` = +14.8 — with the caps drawn
 * upright in the same frame at 8× and 16× in `spec/zoom-spinner/taper-*-grid.png`.
 *
 * **The piece is a straight-sided frustum, widest at the top, and this used to be a table of five
 * absolute heights that could not hold that shape.** `spec/measure_spinner_taper.py` re-reads both
 * caps per weapon-local row: after the leading rows the crop's slanted leather boundary cuts off a
 * full-width piece, each flank is straight to within one source pixel (linear RMS 0.57 px, bowing
 * out from its own chord by 0.77 px, so a curve is not resolvable), and neither cap ever widens
 * downward by as much as one source pixel — the largest is 0.61 px on the two-cap mean, 1.01 px on
 * the right cap alone. `spec/spinner-taper.json`, `spec/zoom-spinner/taper-*-16x-grid.png`.
 *
 * The table could not hold it because only the seat is derived and every row it carried was at an
 * ABSOLUTE height, so the lathe interpolated between a ring that moved and a first row that did
 * not. At `CONNECTOR_LENGTH` = 55 the seat sat at −31.884 and the arm's own end cap covered almost
 * all of that ramp; the 2026-08-12 return to 72 lifted the seat to −21.471 and pulled the arm's
 * cover up with it, and 13.0 units of ramp came out from under it. Measured off
 * `full/front-orthographic.png` rather than argued: the exposed cap widened downward by +4.00
 * units of half-width from Y = −37.5 to Y = −50.5 before it narrowed — a spinning top. Not one
 * number in the table had changed.
 *
 * So the profile is DERIVED from `spinnerSeat()` now, and the shape is stated as the shape rather
 * than sampled into rows:
 *
 *  · **the seat ring**, buried, radius and height both from the arm.
 *  · **the shoulder**, `SPINNER_SHOULDER_DROP` below it, at the widest radius the crop reads. This
 *    is the only place the piece widens going down, and it is as short as a non-degenerate cone
 *    can be, so the widening a camera can see is the sliver of it outside the arm's end-cap plane
 *    — 1.1 units, one render pixel. `audit_records.py` holds that to 2.0 and RE-DERIVES it from
 *    the arm, so moving the arm again fails the audit instead of re-opening the ramp.
 *  · **a straight line from there to the blunt bottom.** The intermediate rings are interpolated
 *    rather than measured, and are here only to give `applyFacetSteps` its shading bands; the ring
 *    count is what keeps the two spinners at 68 triangles each.
 *
 * Why the top ring rides with the seat instead of staying at the crop's −53.5: that row is not at
 * an absolute height in the weapon, it is at the boundary where the leather stops, and the model's
 * leather stops 12 units higher than the crop's because the arm's length is directed. Pinning it
 * at −53.5 is what forced a ramp above it. What that used to cost was the cap's LENGTH; the
 * 2026-08-08 direction spent `SPINNER_BOTTOM_Y` on it instead, so the visible cap is now 56.22
 * against the crop's 56.20 and the cost has moved onto the flank: 14.03 of half-width comes off
 * over 55.07 units, a slope of 0.2547 against the crop's fitted
 * `halfWidth = 21.049 − 0.2135·drop`, 19% steeper. Where that line puts the crop's own bottom —
 * 9.05 half-width — this build reads 7.01, a gap of 2.03 units or **0.87 of a source pixel**, so
 * `SPINNER_BOTTOM_RADIUS` is left at its measured 8.1 rather than churned for a sub-pixel.
 */
/**
 * Radius at the shoulder = the crop's own flank fit at the row the shoulder IS — where the
 * leather stops — 21.049 front-view half-width ÷ cos(π/6). **Widened from 21.4 on 2026-08-08 by
 * user direction, and the widening is a correction, not a concession.** 21.4 was the widest
 * SAMPLED row, and `spec/spinner-taper.json` flags the four rows above it as `boundaryRampRows`:
 * the crop's slanted leather boundary still cuts them, so they read narrow and drag the sampled
 * maximum down with them. The mean fit over all 53 clean rows extrapolates to 21.049 at drop 0
 * (linear RMS 1.34 units). The shoulder itself sits a little ABOVE that boundary, so the visible
 * flank still reads a shade narrower than the crop's — that residual is left on the record rather
 * than closed by inflating the number past what the fit says.
 */
const SPINNER_TOP_RADIUS = 24.3;
/** Blunt truncation, never a point. The crop cannot separate this from the tilt of the cap's own
 *  bottom face — see `spec/confidence-report.md` and §11 — so the shipped reading stands. */
const SPINNER_BOTTOM_RADIUS = 8.1;
/**
 * **DIRECTED 2026-08-08.** This was the crop's mean cap bottom, −109.65, and the one pin on this
 * assembly the build actually hit: the render's lowest gold row read −110.0, 0.15 of a source
 * pixel. The user directed the caps shorter a second time, and by then there was nothing left to
 * pay with — the 2026-08-13 directive had already spent the arm — so the pin is spent instead.
 * The measured value stays here as the evidence it was.
 *
 * What it buys: the visible gold is 56.22 units against the crop's 56.20. What it costs: the
 * cap's bottom now sits 18.9 units above the crop's own. Those are the same 18.9 units, and that
 * is the finding — **the caps were never too long, they are too HIGH.** Gold emerges 9.428 above
 * an arm end-cap centre that the locked root and rake put at −44.0 where the crop reads −62.9.
 * Lengthening the arm to close that is the `L = 113.65` row of the `CONNECTOR_LENGTH` table,
 * which that clause rejects on distance. So the build now matches the crop's cap PROPORTION and
 * not its position, and the silhouette pays for the swap; §11 G4 owns the rest.
 */
const SPINNER_BOTTOM_Y = -90.8;
/** Interpolated rings between the shoulder and the bottom. Four keeps the lathe at six rings and
 *  each spinner at 68 triangles, exactly as the five-row table did. */
const SPINNER_BANDS = 4;

/**
 * Clearance kept between the spinner's buried top ring and the connector's wall and end cap, in
 * normalized units. Non-zero on purpose: at zero the ring is coplanar with the arm's end cap and
 * the two z-fight.
 */
const SPINNER_SEAT_CLEARANCE = 1.5;

/**
 * How far below the seat the widest ring sits. The same number as the clearance, and not by
 * coincidence — it is the shortest drop that is not a degenerate zero-height cone, and a flat
 * annulus here would put a horizontal plate on the end of the arm with open air above its rim.
 * Anything larger is a ramp, which is the defect this replaces.
 */
const SPINNER_SHOULDER_DROP = SPINNER_SEAT_CLEARANCE;

/** All four driver axes cross X=0 at Y=−62 — the radiation centre is not the guard. */
const DRIVER_CENTRE: [number, number] = [0, -62];
// Pair means of the four measured PCA axes (upper 45.9/40.7, lower 29.1/21.6). A +2.5 deg bias
// was tried against the overlay and made the silhouette IoU worse (0.8859 -> 0.8849), so the
// measured means stand.
const DRIVER_ELEVATION_DEG = { upper: 43.3, lower: 25.4 };
const DRIVER_RADIAL_END = 172;
/** Radius, not half-width: the rods are faceted cylinders, not rectangular prisms. */
const DRIVER_RADIUS = 11;
const DRIVER_SIDES = 8;
/**
 * Anti-gap margin at the joint, as a fraction of the rod's DIAMETER. The brief's budget for this
 * is 5%. It is margin ON TOP OF the depth `driverRootRadius()` derives for burying the cap — that
 * depth is geometry, not slack, and spending the 5% on it would leave nothing for the gap.
 */
const DRIVER_JOINT_OVERLAP = 0.05;

/**
 * Measured: the leather's own lower edge reads −180.3 in `measurements.json` (`grip[0].bbox`),
 * and at 16× the crop shows near-black leather holding full width right down to it and gold
 * starting immediately below. It used to stop at −168 with a turned collar filling −166…−180;
 * with that collar gone (see `pointedMetalPommel`) the leather runs to its measured edge, which
 * is also what closes the junction — the grip's own bottom cap and the cone's base ring are the
 * same plane, so no section face is ever exposed.
 */
const GRIP_BOTTOM_Y = -180;

/**
 * Where the grip column's flat TOP face lands — and it is the jaws' floor, not an offset from
 * anything.
 *
 * **There is no tang, and that is correction A.** The column ran up into a swollen T-head that
 * filled the whole guard and was clamped by the two jaws from outside; it is one constant width
 * from `GRIP_BOTTOM_Y` to here.
 *
 * **It is also not inserted, and that is integration #16.** The pass before this one had the
 * column going up BETWEEN the jaws, into a slot whose walls were two vertical planes biting 5% of
 * a diameter into its flanks, with the top pushed `GRIP_BURIAL` = 3 past the diamond's culet so
 * the stone sat inside the leather rather than balanced on it. Both of those are gone. The jaws
 * are triangles on the stone's own lower edges now, meeting on the axis AT the culet, so there is
 * no slot to insert anything into; and the user's sketch draws the column's top edge as a closed
 * horizontal line lying directly under the two triangles' floor, not running up between them
 * (`spec/zoom-guard/sketch-grip-top-6x.png`: the jaws' floor and the column's top are 12 px apart
 * at 6×, against a jaw 118 px tall, and the two triangles never enclose the column).
 *
 * So the contact is FACE TO FACE on one plane, and there is nothing left to derive: `GRIP_TOP_Y`
 * IS `CLAMP_FLOOR_Y`. What used to be bought with a burial is bought by coverage instead — the
 * column's top face reaches 11.087 in x and 11.087 in z, against two jaws that together span
 * `±CLAMP_FLOOR_SPAN` = ±34 across the same plane at `±CLAMP_HALF_DEPTH` = ±16 deep, so the face is
 * inside their footprint by 22.9 units on every side at once and no camera can reach it. The
 * seam cannot open a gap because there is no gap to open: one plane, three parts, no offset.
 */
const GRIP_TOP_Y = CLAMP_FLOOR_Y;

/**
 * A plain cone, and nothing above it.
 *
 * There is **no finishing collar**. The build carried one at radius 14 across −166…−180 as a
 * directed component at confidence 0.60, and the crop does not support it: at 16× NEAREST the
 * grip runs uniform near-black leather from −160 to its edge at −180 and the warm gold starts on
 * the very next row. No ring, no band, no second material. The component is removed rather than
 * narrowed.
 *
 * The profile was a four-point lathe with a belly at −188 and a waist at −200. It is now one
 * straight cone: base ring at the leather's edge, apex at the measured tip. Half-angle
 * `atan(12 / 30.7)` = 21.3°, so the apex angle is 42.7°.
 *
 * **The base ring IS the grip's bottom ring** — same facet count, same circumradius, derived from
 * `GRIP_HALF_WIDTH` and never written as a second number, so re-cutting the column moves the cone
 * with it. It used to be a 6-gon of radius 11 against the column's 8-gon of 12, on the argument
 * that staying "inside the grip's 12" kept the pommel from reading thicker than the shaft. That
 * argument mistook which number a viewer sees. `polygonSection`'s phase puts a FACE CENTRE on
 * the +X axis rather than a vertex, so what the front view measures is each prism's INRADIUS —
 * `12·cos(π/8)` = 11.087 for the column against `11·cos(π/6)` = 9.526 for the cone. The cone was
 * stepped in 1.56 units per side, 14% of the shaft's own half-width, and that step is what the
 * correction is about.
 *
 * **Circumscribed or inscribed?** For two prisms of DIFFERENT facet counts the two answers
 * disagree — matching circumradii leaves a 0.69-unit step in the front view, matching front-view
 * reach needs radius 12.80 and puts the cone's vertices 0.80 outside the column's. The crop
 * cannot referee it: one source pixel is 2.34 normalized units, so the whole question is 0.30 of
 * a pixel wide, and at 8× NEAREST (`spec/zoom-spinner/pommel-junction-8x.png`,
 * `spec/zoom_pommel_junction.py`) the seam is a three-row blend from near-black to gold with no
 * edge in it to measure. What the crop DOES say is that the two parts are the same width there:
 * `measurements.json` reads the gold cone's bbox 19.3 wide against the leather's 20.0, a 0.7-unit
 * difference — 0.30 px again.
 *
 * So the question is dissolved rather than guessed: give the cone the COLUMN'S OWN SECTION and
 * both readings coincide, exactly, at 12. That is also the only choice that keeps the recorded
 * joint intact. The two rings share the plane at `GRIP_BOTTOM_Y` and the grip's own end cap is
 * what closes the junction, which needs one ring to cover the other; a 6-gon and an 8-gon of the
 * same circumradius cross six times, and either mismatch leaves alternating slivers of both end
 * faces exposed. Identical rings butt.
 *
 * Against the crop the cone still runs about 1.7 units narrow through Y ≈ −190, where the visible
 * gold measures a half-width near 9.8 while this cone gives 8.09. That is under one source pixel
 * and it is the price of a straight cone that also starts at the leather's measured edge: a cone
 * fitted to the −190 width instead would need radius 14.7 at the junction, wider than the grip.
 */
const POMMEL_TIP_Y = -210.7;
/**
 * The column's facet count, which the cone inherits. Written here rather than imported because
 * the grip spells its own `8` inline in `polygonSection`; `tests/ultima-v2-solid.test.mjs`
 * compares the two BUILT rings vertex for vertex, so the pair cannot drift apart silently.
 */
const POMMEL_SIDES = 8;
const POMMEL_RADIUS = GRIP_HALF_WIDTH;

// --- palette (measured HSV census, image-analysis Layer 6) ------------------

const srgb = (hex: string) => new THREE.Color().setStyle(hex, THREE.SRGBColorSpace);

const PALETTE = {
  // The shell's three stops are the artwork's own value profile ALONG WEAPON-LOCAL Y, and they
  // are not the census's three bands. Layer 6's census reads #E6E7F2 / #CDCFD8 / #B5B6BF and this
  // build fed those straight into `applyRamp` — but a census is a histogram, it has no axis, and
  // measuring where those bands actually sit shows them running ACROSS the blade, not up it.
  // Along Y the artwork is nearly flat and then climbs into the tip. Measured as the median of
  // the pale-neutral census per 50-unit band (producer: `artifacts/ultima-v2/diag/
  // shell_ramp_profile.py`, which shares `zoom_shell_translucency.py`'s weapon-local frame),
  // in LINEAR light because that is the space `applyRamp` interpolates in:
  //
  //     Y   50   100   150   200   250   300   350   400   450   500   550   600   650   700  750
  //     L  .698  .686  .679  .682  .686  .678  .681  .643  .655  .662  .697  .738  .771  .810 .837
  //
  // Flat at 0.684 to Y ~ 400, a 0.03 dip through 400-500, then a straight climb into the tip.
  // Three stops at Y = 200 / 480 / 760 reproduce it; the ramp's own middle stop is what carries
  // the dip, which is why it sits BELOW the root stop. What the build renders through them:
  //
  //     Y   50   100   150   200   250   300   350   400   450   500   550   600   650   700  750
  //     L  .683  .685  .685  .678  .678  .671  .669  .664  .662  .657  .692  .727  .759  .797 .829
  //
  // Worst residual +0.021 at Y = 400, RMS 0.011 over the whole visible blade.
  //
  // Each stop is its target divided by the rig's transfer, then corrected once against a render —
  // one Newton step, because the transfer is not the same number at every height (1.28 through
  // the flat blade, 1.12 into the tip, since the section's faces turn as the blade narrows).
  // **The tip stop needed a second correction and the reason is a gate, not a colour.**
  // `compare_render`'s foreground test is `min(rgb) < 244` at the render's own 584x1168, where the
  // last 3% of the blade is a needle whose pixels are mostly background: at a tip of 245 that
  // needle stops being foreground, the mask loses 31 rows of length, and normalizing by height
  // then inflates the whole silhouette. Measured, the same geometry three ways — tip stop
  // #E0E1EB: mask bbox 430x1000, IoU 0.8587; #D4D5DF: 432x1031, IoU 0.8893; and the translucent
  // build this replaces: 432x1031, IoU 0.8895. So the tip is solved against the mask it has to
  // survive and lands 0.008 linear under the artwork rather than 0.09 over it.
  //
  // The census's own bands are still in the build — they are what `applyFacetSteps` produces
  // across the blade, on the axis they were actually measured on.
  shellRoot: "#C1C2CC",
  shellMid: "#BBBCC6",
  shellTip: "#D4D5DF",
  // The insert's gradient runs along weapon-local Y and along nothing else: regressed against the
  // artwork's per-scanline medians it scores R2 0.826 / 0.662 / 0.643 on Y and 0.000 / 0.001 /
  // 0.000 on X, so there is no left-right and no centre-to-edge term to model. These three stops
  // are fitted so `applyRamp` — which interpolates in LINEAR light, not sRGB — reproduces that
  // measured profile. Producer and evidence: spec/pbr-evidence/insert-gradient/.
  //
  // The three values they replace were real colours off the same ramp, placed at the wrong
  // heights: #7F3CF2 is the artwork at Y=62 (applyRamp put it at 42), #2F238C is Y=303 (put at
  // 261), #160D59 is Y=419 (put at 480). The apex is what cost the most — the ramp stopped
  // darkening 61 units early, so the top eighth never reached the artwork's near-black tip, where
  // interior pixels read R and G at literally 0. Layer 6's census was never wrong; the build took
  // three of its four stops and re-spaced them evenly, which moved every one of them.
  // Pixel-weighted RMS against the artwork, R/G/B: 7.54/4.30/5.64 before, 4.03/2.55/3.41 after.
  insertApex: "#080444",
  insertMid: "#3A2491",
  insertBase: "#7D40EC",
  coreTip: "#210A38",
  coreBody: "#3A0B43",
  gemHighlight: "#FF3866",
  gemMain: "#C0184D",
  gemShadow: "#5A0B34",
  steel: "#353640",
  steelShadow: "#202126",
  // The clamp jaws and driver sockets are machined metal read against dark leather right next
  // to them, so they run two stops lighter than the guard steel or the whole hilt collapses
  // into one black mass at the exact place the correction pass is about.
  clampMetal: "#9698A6",
  clampMetalShadow: "#55565F",
  // spinnerEnd{Left,Right} ONLY, and these are NOT the crop's own colours — they are the crop's
  // colours divided by this rig's measured metal transfer. Measured inside the projected spinner
  // footprint of artifacts/ultima-v2/full/artwork-match.png, an opaque METAL.mid surface renders
  // at 0.215 of its vertex colour in linear light, while a metalness-0 surface next to it renders
  // at 0.447 — so the old #8D8450/#6F6A3D pair landed the caps on (59,55,32) against the crop's
  // (106,105,74), half the value, with a p90/p10 range of 1.27 against the crop's 1.68. That is
  // the §6 trap measured rather than asserted: the metalness eats the value, so the albedo has to
  // be pre-divided by it. Through 0.215 these two land shade/mid/lit on (82,81,56) / (106,105,74)
  // / (125,124,88) against the crop's (75,75,55) / (106,105,74) / (132,130,98).
  gold: "#F9F7B3",
  goldShadow: "#A8A677",
  driverHighlight: "#BB2A50",
  driverShadow: "#2E0716",
  // The connector arms read as dark GREY leather, distinct from the near-black grip leather.
  connectorSeam: "#787985",
  connectorShadow: "#43444C",
  grip: "#111216",
  gripWrap: "#292A30",
  pommel: "#958044",
  pommelShadow: "#5E512D",
} as const;

// --- geometry helpers ------------------------------------------------------

/**
 * Loft a ring stack into flat-shaded geometry.
 *
 * Rings may be degenerate (all points equal) so a station can collapse to a point — that is how
 * the blade tip and the insert apex close without a separate cap. Non-indexed on purpose: every
 * quad gets its own normals, which is what makes the PS1 facet read survive.
 */
function loft(input: THREE.Vector3[][]): THREE.BufferGeometry {
  // A ring given as a single point (an apex) is broadcast to the stack's width, so callers can
  // write `[[apex], ring, [apex]]` for a bipyramid without padding it by hand.
  const width = Math.max(...input.map((ring) => ring.length));
  const rings = input.map((ring) =>
    ring.length === width ? ring : Array.from({ length: width }, () => ring[0]!.clone()),
  );
  const positions: number[] = [];
  const push = (a: THREE.Vector3, b: THREE.Vector3, c: THREE.Vector3) => {
    if (
      a.distanceToSquared(b) < 1e-12 ||
      b.distanceToSquared(c) < 1e-12 ||
      a.distanceToSquared(c) < 1e-12
    ) {
      return; // collapsed triangle at a degenerate ring
    }
    positions.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z);
  };
  // Each quad is split along its SHORTER diagonal, and that choice is the whole reason a
  // mirrored pair can be asserted to shade identically.
  //
  // It used to split `lower[i] → upper[i+1]` unconditionally. `mirrorRearRing` reverses the ring
  // order, so the rear half met the same quad with `i` and `i+1` swapped and cut it on the OTHER
  // diagonal — and a quad between two stations is WARPED, so the two halves then carried
  // different face normals over the same surface. `applyFacetSteps` quantises those normals into
  // three steps, so wherever a facet sat near a step boundary the pair shaded like two different
  // parts. That is measured, not reasoned: it is why `mirrorColour` read 0.000311 rather than 0
  // on a pair that is provably an exact mirror, and it is what made a POINTED crown on the stone
  // (facet dot 0.469 against a boundary at 0.5) fail `MIRROR_COLOUR_TOLERANCE` at 2.6× over while
  // a blunter one passed. The stone is pointed because the brief says so, so the cliff had to go
  // rather than be steered around.
  //
  // Diagonal length is invariant under the mirror and the label swap it comes with, so both
  // halves now cut the same geometric diagonal and their triangle lists are exact mirrors. A tie
  // is the one case that can still split the two ways, and a quad with equal diagonals whose two
  // triangulations carry different normals is warped AND symmetric at once — `check_centerline.py`
  // measures the outcome either way, so it is left to fail loudly rather than special-cased.
  for (let s = 0; s < rings.length - 1; s += 1) {
    const lower = rings[s]!;
    const upper = rings[s + 1]!;
    for (let i = 0; i < lower.length; i += 1) {
      const j = (i + 1) % lower.length;
      const a = lower[i]!;
      const b = lower[j]!;
      const c = upper[j]!;
      const d = upper[i]!;
      // Either split writes `a → b` along the lower ring and `c → d` along the upper one, which
      // is the boundary the end caps below read their winding off.
      if (a.distanceToSquared(c) <= b.distanceToSquared(d)) {
        push(a, b, c);
        push(a, c, d);
      } else {
        push(a, b, d);
        push(b, c, d);
      }
    }
  }
  // Cap the two ends, when they are not already degenerate, by TRIANGULATING the ring IN ITS OWN
  // PLANE — not by fanning it through its centroid, and not in a fixed projection.
  //
  // The fan was wrong for any ring that is not star-shaped about its own centroid, and the skins
  // are exactly that: a skin's ring is a thin crescent following the shell's ridge, so its
  // centroid falls off the band, BELOW it. Measured on the build this replaces, the insert's base
  // ring at Y = 42 spans Z = 12.73…14.13 on the centre line while its centroid sits at 10.04 —
  // so the cap's own apex was 2.69 units INSIDE the shell, and the fan's triangles swept the
  // crystal to reach it. That was the whole of the insert's residual penetration
  // (`artifacts/ultima-v2/diag/parts.json`: worst 2.683 normalized units, 119 of 920 samples).
  //
  // `ShapeUtils.triangulateShape` is three.js's own ear clipper and handles the concavity. Two
  // things it needs that it does not supply, and both were got wrong the first time this replaced
  // the fan — measured, not argued, by `tests/ultima-v2-solid.test.mjs`:
  //
  // · **A PLANE.** It is a 2D routine, so the ring has to be flattened first. Flattening to
  //   (x, z) is only correct for rings written in XZ, and `radialSectionX`'s rings are in YZ:
  //   every point shares one x, the contour collapses to a segment, the ear clipper returns
  //   nothing at all, and the part ships as an OPEN TUBE. That cost the four drivers and the two
  //   connectors both caps and 16 triangles each — `driverRightUpper` went from 48 triangles and
  //   0 boundary edges to 32 and 16, and a rod you can see into is a rod that is not solid. The
  //   basis is therefore built from the ring's own NEWELL normal, which is defined whatever plane
  //   the ring lies in and costs one pass over the points.
  //
  // · **A DIRECTION.** The ear clipper's output winding is not contracted, and "anticlockwise in
  //   the projection" is not a usable target either — it depends on which way the basis happens
  //   to face. The target that is always right is CLOSURE. The side wall already wrote the
  //   directed edge `ring[i] → ring[i+1]` along the first ring and `ring[i+1] → ring[i]` along
  //   the last one — EITHER diagonal writes both, which is what leaves the split above free to
  //   be chosen per quad — so a cap seals the surface exactly when it walks its ring the OTHER
  //   way:
  //   backward at the start, forward at the end. Both are read off the sign of a signed area, so
  //   no assumption about Y-up, about the stack ascending, or about the projection survives here.
  //   Getting this wrong is silent under backface culling — an inward-facing cap simply is not
  //   drawn, and the grip, the pommel and the two spinners all shipped with both caps inverted.
  for (const [ring, atStart] of [
    [rings[0]!, true],
    [rings[rings.length - 1]!, false],
  ] as [THREE.Vector3[], boolean][]) {
    const first = ring[0]!;
    if (ring.every((p) => p.distanceToSquared(first) < 1e-12)) continue;
    // Earcut cannot see repeated points, and a ring repeats one whenever a profile break lands on
    // the rim (the shell's shoulder outboard of a skin's own half-width, say).
    const source: THREE.Vector3[] = [];
    for (const p of ring) {
      if (!source.length || p.distanceToSquared(source[source.length - 1]!) >= 1e-12)
        source.push(p);
    }
    if (source.length >= 2 && source[0]!.distanceToSquared(source[source.length - 1]!) < 1e-12) {
      source.pop();
    }
    if (source.length < 3) continue;
    // The ring's own plane, by Newell — zero only for a ring that encloses no area, which has
    // nothing to cap anyway.
    const normal = new THREE.Vector3();
    for (let i = 0; i < source.length; i += 1) {
      const p = source[i]!;
      const q = source[(i + 1) % source.length]!;
      normal.x += (p.y - q.y) * (p.z + q.z);
      normal.y += (p.z - q.z) * (p.x + q.x);
      normal.z += (p.x - q.x) * (p.y + q.y);
    }
    if (normal.lengthSq() < 1e-18) continue;
    normal.normalize();
    const u = Math.abs(normal.x) > 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
    u.crossVectors(u, normal).normalize();
    const v = new THREE.Vector3().crossVectors(normal, u);
    const flat = source.map((p) => new THREE.Vector2(p.dot(u), p.dot(v)));
    let ringArea = 0;
    for (let i = 0; i < flat.length; i += 1) {
      const p = flat[i]!;
      const q = flat[(i + 1) % flat.length]!;
      ringArea += p.x * q.y - q.x * p.y;
    }
    // Backward at the first ring, forward at the last: the reverses of what the wall already
    // wrote. Whichever way the basis faces, both signs move together, so this stays correct.
    const wantSign = Math.sign(ringArea) * (atStart ? -1 : 1);
    for (const [i0, i1, i2] of THREE.ShapeUtils.triangulateShape(flat, [])) {
      const a = flat[i0!]!;
      const b = flat[i1!]!;
      const c = flat[i2!]!;
      const area = (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
      if (Math.abs(area) < 1e-18) continue;
      if (Math.sign(area) === wantSign) push(source[i0!]!, source[i1!]!, source[i2!]!);
      else push(source[i0!]!, source[i2!]!, source[i1!]!);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.computeVertexNormals();
  return geometry;
}

/**
 * The shell's cross-section: eight points forming a centre ridge that falls to **zero**
 * thickness at both side edges. That zero is what makes the shell read as sharpened — a
 * hexagon with a flat plateau would read as a slab. The insert deliberately does not use this.
 */
function ridgedSection(y: number, halfWidth: number, halfDepth: number): THREE.Vector3[] {
  const a = halfWidth * RIDGE_SHOULDER_X;
  const shoulder = halfDepth * RIDGE_SHOULDER_Z;
  const pts: [number, number][] = [
    [-halfWidth, 0],
    [-a, shoulder],
    [0, halfDepth],
    [a, shoulder],
    [halfWidth, 0],
    [a, -shoulder],
    [0, -halfDepth],
    [-a, -shoulder],
  ];
  return pts.map(([x, z]) => new THREE.Vector3(n(x), n(y), n(z)));
}

/**
 * How far out along its own axis a driver's root cap sits, buried inside its leather connector.
 *
 * Derived, not chosen. Solving against the connector's OUTER surface — the obvious reading, and
 * what this did until the cap was inspected at 4× — buries the rod's CENTRE LINE and nothing
 * else: the cap is a flat disc containing the Z axis, so its rim reaches DRIVER_RADIUS out in Z
 * where the arm's wall has already curved away, and it floated 5.6 (upper) / 5.8 (lower) units
 * proud of the leather. That is the visible gap the correction spec's "the root cap must meet the
 * connector surface cleanly" forbids, and no anti-gap margin inside the spec's own 5% budget can
 * close it — the shortfall is 25% of a diameter, so the depth has to be geometry.
 *
 * So the target is the offset surface, not the outer one: the 8-gon's INRADIUS (its thinnest
 * wall, since a rim can land on a face centre rather than a vertex) pulled in by the rod's own
 * radius. Solving `|(Q(t) − A) × d| = that` and taking the far crossing gives 76.4 (upper) and
 * 78.9 (lower), and DRIVER_JOINT_OVERLAP comes off on top. Both stay far outside the connector's
 * central axis at 66.6 and 68.7, which the rods are forbidden to cross.
 *
 * Front-view silhouette is untouched by any of this. What the artwork measures is where each rod
 * emerges from BEHIND the arm, and that is the arm's own outline — the buried length is occluded,
 * the outer end is pinned at DRIVER_RADIAL_END, and the visible rod is the same rod.
 */
function driverRootRadius(elevationDeg: number): number {
  const e = THREE.MathUtils.degToRad(elevationDeg);
  const a = THREE.MathUtils.degToRad(CONNECTOR_ANGLE_DEG);
  const [ax, ay] = CONNECTOR_ROOT;
  const [dx, dy] = [Math.cos(a), Math.sin(a)];
  // The wall the cap's rim has to clear, offset inward by the rod's radius.
  const inradius = CONNECTOR_RADIUS * Math.cos(Math.PI / CONNECTOR_SIDES);
  const capSurface = Math.sqrt(inradius ** 2 - DRIVER_RADIUS ** 2);
  // (Q(t) − A) × d, expanded in t: cross(t) = k0 + k1·t
  const k0 = (0 - ax) * dy - (DRIVER_CENTRE[1] - ay) * dx;
  const k1 = Math.cos(e) * dy - Math.sin(e) * dx;
  // |k0 + k1·t| = capSurface has two roots; the far crossing is the larger.
  const roots = [(capSurface - k0) / k1, (-capSurface - k0) / k1];
  return Math.max(...roots) - DRIVER_JOINT_OVERLAP * 2 * DRIVER_RADIUS;
}

/**
 * Where a spinner's flat top ring hides inside its connector arm, and how wide it may be.
 *
 * Same lesson as `driverRootRadius()`, one part along. Turning the cap off the arm's −50° axis to
 * vertical un-mates the two end faces — the arm's cap is a disc raked at −50°, the spinner's is
 * now horizontal, so a wedge opens on one side and the ring's rim breaks the wall on the other.
 * Sinking the ring's CENTRE into the arm does not close it: the ring is a disc containing the Z
 * axis, so it reaches its own radius out in Z, where the arm's octagonal wall has already curved
 * away. The surface to solve against is the arm's INRADIUS — its thinnest wall, since a rim can
 * land on a face centre and not only on a vertex — and the whole ring has to fit inside it at
 * once, not just its centre.
 *
 * With the ring centred ON the arm's own axis its farthest point from that axis is exactly its
 * radius, which collapses the problem to two constraints: `radius + clearance ≤ inradius`, and
 * the ring's outermost point staying `clearance` short of the arm's end cap. Both tight gives a
 * closed form, no search:
 *
 *     radius = sin|a|·inradius − clearance·(sin|a| + cos|a|)
 *
 * 9.11 here, seated 9.78 above the arm's end-cap centre — both of them functions of
 * `CONNECTOR_ANGLE_DEG`, so they moved when integration #17 derived the rake from the shell's
 * taper and replaced the directed −50°. 9.21 / 9.69 was that −50°.  The whole flat face then sits
 * SPINNER_SEAT_CLEARANCE inside the leather in every direction, so it is hidden from every
 * camera and not only from the front — and no spinner vertex still inside the arm's length rises
 * above the arm's own upper edge, so the cap never reads as poking THROUGH the arm.
 *
 * X is unchanged by any of this: the spinner's axis is still the vertical line through the
 * connector's outer end-cap centre, which is exactly where the old flush cap sat.
 */
function spinnerSeat(): { x: number; y: number; radius: number } {
  const a = THREE.MathUtils.degToRad(CONNECTOR_ANGLE_DEG);
  const down = Math.abs(Math.sin(a));
  const out = Math.abs(Math.cos(a));
  const inradius = CONNECTOR_RADIUS * Math.cos(Math.PI / CONNECTOR_SIDES);
  const radius = down * inradius - SPINNER_SEAT_CLEARANCE * (down + out);
  // Raising the ring by this much along Y walks it back inside the end cap by exactly the
  // clearance, because moving down the vertical axis moves you OUT along the raked arm.
  const lift = (out * radius + SPINNER_SEAT_CLEARANCE) / down;
  return {
    x: CONNECTOR_ROOT[0] + CONNECTOR_LENGTH * Math.cos(a),
    y: CONNECTOR_ROOT[1] + CONNECTOR_LENGTH * Math.sin(a) + lift,
    radius,
  };
}

/**
 * The spinner's lathe profile, `[radius, weapon-local Y]`, top ring first — DERIVED from the seat
 * rather than tabulated, so the arm can move without restretching the cap's shape.
 *
 * That is the whole point of it being a function. The five-row table this replaces held its rows
 * at absolute heights while its top ring came from the arm, so every time the arm moved the lathe
 * interpolated a different piece out of the same numbers, and the ramp that produced was invisible
 * to every gate because no number had changed. See the comment on `SPINNER_TOP_RADIUS`.
 *
 * Below the shoulder the radius is strictly decreasing by construction: one line, both of whose
 * ends the crop measured.
 */
function spinnerProfile(): [number, number][] {
  const seat = spinnerSeat();
  const shoulderY = seat.y - SPINNER_SHOULDER_DROP;
  const rings: [number, number][] = [[seat.radius, seat.y]];
  for (let i = 0; i <= SPINNER_BANDS; i += 1) {
    const t = i / SPINNER_BANDS;
    rings.push([
      SPINNER_TOP_RADIUS + (SPINNER_BOTTOM_RADIUS - SPINNER_TOP_RADIUS) * t,
      shoulderY + (SPINNER_BOTTOM_Y - shoulderY) * t,
    ]);
  }
  return rings;
}

/**
 * ONE FACE of the diamond: two of the pyramid's four flanks on a single side of Z = 0, closed off
 * underneath by the surface it is MOUNTED ON. `sign` picks the side — `+1` front, `−1` rear.
 *
 * This is how the diamond is built as two independent meshes instead of one Z-symmetric solid.
 * Each half carries its own explode direction and has to break the stack under it on its own
 * side to be seen.
 *
 * **Each half is a 四角錐 — four triangular flanks and a base, five faces, DIRECTED by the user on
 * 2026-08-09** — and the section is what that solid looks like cut at one height: the rim on the
 * seat at `±halfWidth`, one straight run up to the ridge on the axis, one straight run back down.
 * The ridge is `GEM_STATIONS` interpolated, which is two straight segments meeting at the single
 * apex over the rhombus's centre, so every flank is bounded by three straight edges and there is
 * exactly one peak.
 *
 * **The section had a GIRDLE and the crown had a BAND until that directive**, and between them
 * they are the four extra faces and the flat ridge:
 *
 *  · the girdle was a straight WALL at `x = ±halfWidth`, `GEM_RELIEF_STEP` tall, which held the
 *    whole rhombus outline one step proud of the layer under it;
 *  · the band held the crown at `GEM_HALF_DEPTH` across the middle 75% of the stone's height, so
 *    the peak was a plateau three quarters as long as the stone and not a point at all.
 *
 * **Both were load-bearing, and removing them is a trade the directive makes explicitly.** The
 * shape correction pass 2 rejected also ran its rim at zero relief — but its rim sat at `Z = 0`,
 * i.e. 12.17 units INSIDE a shell whose own front surface is at 12.17, so the outline was buried
 * rather than flush and only a central lozenge broke the surface. This rim sits ON `bladeStackTop`,
 * the dark core's own outer face, so the stone still wins the depth test everywhere strictly inside
 * its footprint; what it loses is the STEP that made the outline read as an edge. Against
 * `bladeStackTop` at the waist, `crown − seat` now runs from `+8.485` on the axis to `0.000` at the
 * rim instead of stopping at `+3.36`. Whether the rhombus still reads is a render question and
 * `measure_relief_visibility.py` is the instrument; §8 of `CURRENT-MODEL.md` carries the number.
 *
 * **The flanks are planar to within the seat's own bow.** A flank is bounded by the ridge (exactly
 * straight) and by the rim, and the rim follows `bladeStackTop`, which is a ratio of linears in
 * `y` rather than a linear — so it bows off the chord between its two corners. Measured by
 * `spec/measure_gem_facets.py`: the deviation and the resulting kink are printed there, and they
 * are what stands between "four faces" and "four faces to within a fraction of a source pixel".
 *
 * **Winding.** Whichever diagonal `loft` picks, the ring carries the directed ring edge
 * `lower[i] → lower[j]`, and a triangle on that edge has the normal `h · (−dz, 0, dx)` for the
 * edge `d` — the edge turned a quarter-turn anticlockwise in
 * X-right/Z-up. So a ring only faces outward if it is listed CLOCKWISE in that plane, which is
 * what the front list below does and what `skinSection` does. Mirroring Z flips handedness, so
 * the rear list is the front one REVERSED and then negated; reversing alone, or negating alone,
 * lofts the rear half inside-out. That failure is silent on a flat-shaded Z-symmetric part —
 * one pass shipped all three inner crystals inverted and only the diamond's colour gave it
 * away — so it is derived here rather than eyeballed against a render, and every Z-split part in
 * this file goes through `mirrorRearRing` rather than repeating the transform.
 */
function mirrorRearRing(front: [number, number][]): [number, number][] {
  return [...front].reverse().map(([x, z]) => [x, -z] as [number, number]);
}

/**
 * ONE FACE of a SKIN: a film laid on the blade's own surface, `thickness` deep, following that
 * surface across the whole half-width. `seat` is the depth the film's underside sits at — the
 * shell's front surface for the insert, the insert's own outer surface for the dark core.
 *
 * This is the section that makes the insert and the dark core decals rather than bosses, and
 * every part of it is load-bearing:
 *
 * · **It follows `shellFrontDepth` in X, exactly.** The ring carries the shell's own two profile
 *   breaks — the shoulder at `RIDGE_SHOULDER_X · halfWidth` and the rim — so the outer polyline
 *   is the shell's piecewise-linear profile translated by a constant, with zero interpolation
 *   error. Sample it uniformly instead and the film cuts the corner at the shoulder and dips
 *   BACK INSIDE the shell over a band near its own rim, which is the one thing a skin must never
 *   do. When the shoulder falls outside the film's own half-width the two samples coincide and
 *   `loft` drops the collapsed triangles, so the ring width stays constant either way — which it
 *   has to, because `loft` broadcasts any ring that is not the stack's width.
 * · **The underside CONFORMS as well**, on `seatAt(x)` — the same polyline as the outer face,
 *   translated down by `thickness` instead of flattened to the rim. It used to be flat, at the
 *   film's own rim depth, on the argument that it is invisible from every camera. That argument
 *   is about *rendering*, and the film is a solid: a flat underside at the rim depth runs BELOW
 *   the host's own crest everywhere inboard of the rim, so the film's lower half was buried in
 *   the shell it is supposed to be lying on. Measured on the build this replaces, the insert's
 *   underside at Y = 110 sat at 10.66 against a shell crest of 14.00 on the centre line — 3.34
 *   units, 70% of the film's own section, inside the crystal. The shell is a solid body with
 *   nothing in it, and that is now asserted rather than argued.
 * · **The film never touches Z = 0.** Nothing on this blade does any more — the stone stopped
 *   doing it in the same pass — and `spec/check_centerline.py` asserts it for all three pairs.
 */
function skinSection(
  y: number,
  halfWidth: number,
  seatAt: (x: number) => number,
  thickness: number,
  sign: 1 | -1,
): THREE.Vector3[] {
  const shoulder = Math.min(shellShoulderXAt(y), halfWidth);
  const outer = (x: number): number => seatAt(x) + thickness;
  // Clockwise in the XZ plane: up the left rim, across the outer face, down the right rim, then
  // BACK along the seat through the same three x-breaks. Sharing the breaks is what makes the
  // underside the host's own surface rather than an approximation of it — both polylines are the
  // shell's piecewise-linear profile, one translated by `thickness` and one not.
  const front: [number, number][] = [
    [-halfWidth, seatAt(-halfWidth)],
    [-halfWidth, outer(-halfWidth)],
    [-shoulder, outer(-shoulder)],
    [0, outer(0)],
    [shoulder, outer(shoulder)],
    [halfWidth, outer(halfWidth)],
    [halfWidth, seatAt(halfWidth)],
    [shoulder, seatAt(shoulder)],
    [0, seatAt(0)],
    [-shoulder, seatAt(-shoulder)],
  ];
  const pts = sign > 0 ? front : mirrorRearRing(front);
  return pts.map(([x, z]) => new THREE.Vector3(n(x), n(y), n(z)));
}

/**
 * The diamond's own half-section: a SET stone, cut at one height. Five points and not one of them
 * reads the surface the stone is mounted on.
 *
 * · `±halfWidth` at `GEM_SOCKET_FLOOR` — the flat base, the same plane at every height.
 * · `±halfWidth` at `GEM_GIRDLE_DEPTH` — the socket wall, vertical, its top a LEVEL line.
 * · `0` at the ridge — the crown, two flanks meeting on the axis.
 *
 * **That is the 2026-08-09 directive and it is a reversal.** Every version of this stone since
 * 2026-08-08 closed underneath on `bladeStackTop`, evaluated at each ring point, because "lying on
 * the surface it is mounted on" is what the other five blade meshes do and what the flush gate
 * asserts. The reason the stone stops is that the surface is not level: it climbs 5.8 units under
 * the stone's own footprint, 2.8 of it in one step at the waist, so a stone that follows it comes
 * out with its upper half standing further out than its lower half. Reported from the side view,
 * measured off `bladeStackTop`, and not fixable by any change to the stone's shape.
 *
 * So the stone is SET IN instead: a flat base sunk to the lowest the surface gets, a vertical wall
 * up to a level girdle, and the crown above that. What the eye reads as the stone's edge is the
 * girdle line, and it is now one plane. The wall's own HEIGHT above the crystal varies — most at
 * the culet where the crystal is lowest, least at the top vertex — and that is the setting being
 * honest about a slanted mount rather than the stone being crooked.
 *
 * **Three things this gives up, all of them deliberate.** The stone is no longer flush on anything
 * (`check_centerline.py`'s seat family drops it and an INLAID family replaces it); it is inside
 * `outerCrystalShell` by up to the socket's own depth, which needs the same kind of named
 * exception the two jaws have; and it is nine faces rather than the five a bare 四角錐 has.
 */
function gemHalfSection(
  y: number,
  halfWidth: number,
  ridgeDepth: number,
  sign: 1 | -1,
): THREE.Vector3[] {
  // Clockwise in the XZ plane: up the left socket wall, up the left crown flank to the ridge on
  // the axis, down the right flank and wall, then BACK across the flat base.
  const front: [number, number][] = [
    [-halfWidth, GEM_SOCKET_FLOOR],
    [-halfWidth, GEM_GIRDLE_DEPTH],
    [0, ridgeDepth],
    [halfWidth, GEM_GIRDLE_DEPTH],
    [halfWidth, GEM_SOCKET_FLOOR],
  ];
  const pts = sign > 0 ? front : mirrorRearRing(front);
  return pts.map(([x, z]) => new THREE.Vector3(n(x), n(y), n(z)));
}

/** A faceted prism ring in the XZ plane at height y. */
function polygonSection(
  y: number,
  radiusX: number,
  radiusZ: number,
  sides: number,
): THREE.Vector3[] {
  const ring: THREE.Vector3[] = [];
  for (let i = 0; i < sides; i += 1) {
    const t = (i / sides) * Math.PI * 2 + Math.PI / sides;
    ring.push(new THREE.Vector3(n(radiusX) * Math.cos(t), n(y), n(radiusZ) * Math.sin(t)));
  }
  return ring;
}

/**
 * A faceted ring in the YZ plane at distance x — the section for anything laid along +X.
 *
 * Circular, not the flat 5-point prism the drivers used to get: a rectangular bar reads as
 * pasted onto whatever surface it crosses, and the correction pass calls for rods with a real
 * circular cross-section and real depth.
 */
function radialSectionX(x: number, radius: number, sides: number): THREE.Vector3[] {
  const ring: THREE.Vector3[] = [];
  for (let i = 0; i < sides; i += 1) {
    const t = (i / sides) * Math.PI * 2 + Math.PI / sides;
    ring.push(new THREE.Vector3(n(x), n(radius) * Math.cos(t), n(radius) * Math.sin(t)));
  }
  return ring;
}

/** Revolve a `[radius, y]` profile about the Y axis into flat-shaded geometry. */
function lathe(profile: [number, number][], sides: number): THREE.BufferGeometry {
  return loft(profile.map(([radius, y]) => polygonSection(y, radius, radius, sides)));
}

/**
 * Extrude a 2D outline in XY through ±halfDepth in Z, flat shaded.
 *
 * Uses ExtrudeGeometry rather than lofting two rings: the guard collar's outline is concave
 * (it dips at the centre to seat the gem), and a centroid fan across a concave polygon folds
 * the cap into a bowtie.
 */
function extrudeOutline(outline: [number, number][], halfDepth: number): THREE.BufferGeometry {
  const shape = new THREE.Shape();
  shape.moveTo(n(outline[0]![0]), n(outline[0]![1]));
  for (const [x, y] of outline.slice(1)) shape.lineTo(n(x), n(y));
  shape.closePath();
  const geometry = new THREE.ExtrudeGeometry(shape, {
    depth: n(halfDepth * 2),
    bevelEnabled: false,
    curveSegments: 1,
    steps: 1,
  });
  geometry.translate(0, 0, n(-halfDepth));
  return geometry.toNonIndexed();
}

/**
 * Paint a linear vertex-colour ramp along Y.
 *
 * The source has no texture maps at all: every gradient in the artwork is per-vertex colour
 * interpolation. Reproducing them as vertex colours rather than as generated textures keeps
 * that true, and keeps the facet steps hard where the artwork has them hard.
 */
function applyRamp(
  geometry: THREE.BufferGeometry,
  yBottom: number,
  yTop: number,
  stops: string[],
): void {
  const position = geometry.getAttribute("position");
  const colors = new Float32Array(position.count * 3);
  const ramp = stops.map(srgb);
  const scratch = new THREE.Color();
  for (let i = 0; i < position.count; i += 1) {
    const t = THREE.MathUtils.clamp((position.getY(i) - yBottom) / (yTop - yBottom || 1), 0, 1);
    const span = t * (ramp.length - 1);
    const lo = Math.min(Math.floor(span), ramp.length - 2);
    scratch.copy(ramp[lo]!).lerp(ramp[lo + 1]!, span - lo);
    colors.set([scratch.r, scratch.g, scratch.b], i * 3);
  }
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
}

/**
 * Leather wrap, as banding rather than geometry.
 *
 * The shaft used to carry three protruding ring meshes; they read as hard collars, and the
 * correction pass calls for subtle wrapping with exactly one real collar at the bottom. A
 * banded vertex-colour ramp gives the wrap without adding a single ring back.
 */
function applyWrapBanding(
  geometry: THREE.BufferGeometry,
  yBottom: number,
  yTop: number,
  base: string,
  raised: string,
): void {
  const position = geometry.getAttribute("position");
  const colors = new Float32Array(position.count * 3);
  const low = srgb(base);
  const high = srgb(raised);
  const scratch = new THREE.Color();
  const span = yTop - yBottom || 1;
  for (let i = 0; i < position.count; i += 1) {
    const t = (position.getY(i) - yBottom) / span;
    // 9 wraps over the shaft, squared so the lit edge of each wrap stays narrow.
    const wrap = (Math.sin(t * Math.PI * 2 * 9) * 0.5 + 0.5) ** 2;
    scratch.copy(low).lerp(high, wrap * 0.8);
    colors.set([scratch.r, scratch.g, scratch.b], i * 3);
  }
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
}

/**
 * Step every triangle's colour by how much its own normal faces the artwork's key.
 *
 * This is what produces the flat facet bands the reference actually shows. Doing it in vertex
 * colour rather than leaving it to the shader means the bands stay hard-edged at any lighting
 * setting, which is the identity feature; the lights then only tint them.
 *
 * **`keyZ` mirrors the key for the rear half of a Z-split pair, and it is load-bearing.** The key
 * carries +0.66 in Z, so a face and its mirror image across `Z = 0` land on opposite sides of the
 * quantiser: normal `(0, 0, +1)` scores step 1 and normal `(0, 0, −1)` scores step 0, which at
 * the insert's `strength` of 0.55 is a multiplier of 1.088 against 0.901. Two meshes asserted to
 * be exact mirrors therefore shaded a factor of 1.20 apart on the *same* surface — measured, not
 * reasoned: captured unlit (`--flat`, so the pixel IS the vertex colour) with everything but one
 * half hidden, the two films' shell-facing undersides read sRGB (78.67, 43.82, 164.43) on the
 * front half and (85.83, 48.18, 178.52) on the rear, a linear-light ratio of 1.2003 against the
 * 1.2076 this arithmetic predicts. Producer and evidence: `spec/capture_skin_faces.sh` and
 * `spec/measure_skin_faces.py`, into `artifacts/ultima-v2/diag/skin-faces.json`.
 *
 * Passing the mirrored key to the rear half makes mirror-image faces score the same step, so a
 * mirrored pair is a mirrored pair in colour as well as in geometry. The lift ladder already
 * asserts that each layer protrudes equally front and rear; this is the same symmetry in the one
 * channel that had no assertion on it.
 */
function applyFacetSteps(
  geometry: THREE.BufferGeometry,
  light: string,
  dark: string,
  strength = 1,
  keyZ: 1 | -1 = 1,
): void {
  const position = geometry.getAttribute("position");
  const normal = geometry.getAttribute("normal");
  const existing = geometry.getAttribute("color");
  const colors = new Float32Array(position.count * 3);
  const key = new THREE.Vector3(-0.42, 0.62, 0.66 * keyZ).normalize();
  const lit = srgb(light);
  const shade = srgb(dark);
  const scratch = new THREE.Color();
  const face = new THREE.Vector3();
  for (let i = 0; i < position.count; i += 3) {
    face.set(normal.getX(i), normal.getY(i), normal.getZ(i));
    // Three flat steps, not a smooth ramp: the source is Gouraud over few faces.
    const raw = (face.dot(key) + 1) / 2;
    const step = Math.round(raw * 2) / 2;
    for (let k = 0; k < 3; k += 1) {
      const v = i + k;
      if (existing) {
        scratch.setRGB(existing.getX(v), existing.getY(v), existing.getZ(v));
        // Narrow band on purpose: this is the *whole* shading model for the flat-shaded
        // source, and the rig on top is near-ambient. A wider band double-darkens.
        scratch.lerp(scratch.clone().multiplyScalar(0.82 + 0.34 * step), strength);
      } else {
        scratch.copy(shade).lerp(lit, step);
      }
      colors.set([scratch.r, scratch.g, scratch.b], v * 3);
    }
  }
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
}

// --- materials -------------------------------------------------------------

/**
 * Every material here is driven by vertex colour, so `color` MUST stay white.
 *
 * Three.js multiplies `material.color` by the vertex colour. Setting both to the measured
 * albedo squares it: #CDCFD8 (0.80 linear-ish) became 0.64 and the whole weapon rendered a
 * flat mid-grey against a reference that is near-white. This is the same defect class as the
 * roughnessMap squaring that cost the earlier run two misattributed passes.
 */
const VERTEX_ALBEDO = 0xffffff;

/**
 * Metalness is deliberately low across the whole build, even on parts that read as metal.
 *
 * The look-dev rig is near-ambient (shading is baked into vertex colour) over a featureless
 * environment, and a metalness-0.85 surface in that rig has almost nothing to reflect, so it
 * renders near-black. The first correction pass set the clamp and socket metal two stops
 * lighter in *albedo* and they still came out black — the albedo was never the problem, the
 * metalness was. These values keep the metal reading as metal through vertex colour instead.
 */
const METAL = { bright: 0.35, mid: 0.3, dark: 0.25 } as const;

function buildMaterials() {
  /**
   * SOLID crystal, and every blend path off. Directed by the user on 2026-08-07.
   *
   * This departs from the supplied brief, which asks for "pale **translucent**" — the departure
   * and its evidence are `confidence-report.md` conflict 7. The short version is that the crop
   * carries no compositing to lose: a pale layer of opacity `a` drawn over anything floors every
   * channel under it at `a x 216`, and the artwork's violet field reaches literally **(0, 0, 45)**
   * with its boundary against the shell two pixels wide at the median. Measured by
   * `spec/zoom_shell_translucency.py` into `spec/zoom-relief/translucency-*-8x.png`.
   *
   * **What the alpha blend was actually paying for was LEVEL, not translucency, and that is the
   * trap in removing it.** Measured over the whole re-framed render by `spec/measure_shell_value.py`
   * (`artifacts/ultima-v2/gate/shell-value.json`), the artwork's shell means (216, 217, 227). With
   * `opacity: 0.35` this material lit to 128 and the remaining 0.65 came from the WHITE BACKGROUND,
   * which is what put it on 210. Turn the blend off and the background stops contributing: with
   * the palette still the census bands, the shell ALONE renders at a median of **122**
   * (`artifacts/ultima-v2/diag/shell-only/`, read by `diag/probe_shell.py` with no colour mask at
   * all), which is the "opaque grey plastic" this material was rescued from in the first place.
   *
   * So the level has to be paid explicitly, and it cannot be paid out of the palette. The rig
   * delivers **0.322 of albedo** in linear light (median vertex colour 0.6052 -> median render
   * 0.1946), while the artwork's shell sits at 0.701 against a measured albedo of 0.610 — i.e. it
   * reads BRIGHTER than its own albedo, which is a statement about the light, not the paint. The
   * shortfall is 3.6x and the palette's whole remaining headroom is 1.11x (its highlight stop is
   * already at 0.899 of white), so raising `PALETTE.shell*` cannot reach it by arithmetic. Doing it
   * anyway would also break rule 1 of §6: vertex colour IS the measured albedo here.
   *
   * **`envMapIntensity` — the lever this build's records name for exactly this job — is a NO-OP.**
   * three r0.185 `three.module.js:18690` overwrites the uniform with `scene.environmentIntensity`
   * whenever a standard/physical material has no `envMap` of its own and the scene has an
   * `environment`, which is every material in this build. Measured, not read: at 1, 7.5 and 40 the
   * re-framed render is byte-identical (`artifacts/ultima-v2/diag/opaque-trial{,2}/`). `guardGold`
   * carries the same dead lever and its comment now says so.
   *
   * That leaves `emissive`, and it is the same pattern `purpleInsert` below already uses: white
   * emissive multiplied by `vColor` in the shader, so the term is proportional to the vertex colour
   * rather than a flat floor under it. Proportional is the load-bearing word — the facet steps and
   * the Y ramp are carried entirely in vertex colour, so a term proportional to it raises the LEVEL
   * and leaves the SHAPE alone, which a flat emissive would flatten (see `purpleInsert`'s JSDoc for
   * the pass that cost). The intensity is solved, not dialled: `0.322 + E` has to reach
   * `0.701 / 0.6052 = 1.158`, so E = 0.836.
   */
  const outerCrystal = new THREE.MeshPhysicalMaterial({
    color: VERTEX_ALBEDO,
    vertexColors: true,
    metalness: 0.0,
    roughness: 0.2,
    transparent: false,
    opacity: 1,
    transmission: 0,
    emissive: 0xffffff,
    emissiveIntensity: 0.836,
    side: THREE.FrontSide,
    depthWrite: true,
    flatShading: true,
  });
  outerCrystal.onBeforeCompile = (shader) => {
    shader.fragmentShader = shader.fragmentShader.replace(
      "#include <emissivemap_fragment>",
      // `vColor` is a vec4 in three r152+, for USE_COLOR as well as USE_COLOR_ALPHA.
      "#include <emissivemap_fragment>\n\ttotalEmissiveRadiance *= vColor.rgb;",
    );
  };
  outerCrystal.needsUpdate = true;

  /**
   * The glow follows the ramp. A flat emissive is what was flattening the gradient.
   *
   * `emissive` is added per-pixel *after* lighting and is NOT modulated by vertex colour, so
   * `emissive: insertBase * 0.22` was a constant floor of (61, 25, 122) sRGB under every pixel of
   * the part. That floor is brighter than the artwork itself over the whole upper blade — the
   * artwork falls below it in R from Y=283 and in B from Y=342, which is 34% of the insert's
   * projected area in R — so that region was unreachable no matter what the palette said. It is
   * the same defect class as rule 1 and as `outerCrystal`'s two blend paths: a second, flat
   * brightness path competing with the one that carries the shape, and flattening it.
   *
   * Multiplying the emissive by `vColor` puts the glow back on the ramp. `emissive` therefore goes
   * white — the hue now comes from the vertex colour, and leaving it purple would square it, which
   * is what `VERTEX_ALBEDO` exists to prevent. `emissiveIntensity` is then set to the value that
   * leaves the part's mean emissive energy exactly where it was, computed against B because B
   * carries most of the signal: 0.19534 linear / 0.40273 mean vertex colour = 0.484. So this
   * changes the gradient's SHAPE and deliberately not its level — a render should show the mean
   * roughly unmoved and the base-to-apex spread several times wider.
   */
  const purpleInsert = new THREE.MeshPhysicalMaterial({
    color: VERTEX_ALBEDO,
    vertexColors: true,
    roughness: 0.35,
    metalness: 0.0,
    emissive: 0xffffff,
    emissiveIntensity: 0.48,
    flatShading: true,
  });
  purpleInsert.onBeforeCompile = (shader) => {
    shader.fragmentShader = shader.fragmentShader.replace(
      "#include <emissivemap_fragment>",
      // `vColor` is a vec4 in three r152+, for USE_COLOR as well as USE_COLOR_ALPHA.
      "#include <emissivemap_fragment>\n\ttotalEmissiveRadiance *= vColor.rgb;",
    );
  };

  const darkCore = new THREE.MeshStandardMaterial({
    color: VERTEX_ALBEDO,
    vertexColors: true,
    roughness: 0.45,
    metalness: 0.0,
    flatShading: true,
  });

  const rootGem = new THREE.MeshPhysicalMaterial({
    color: VERTEX_ALBEDO,
    vertexColors: true,
    roughness: 0.15,
    metalness: 0.0,
    transmission: 0.22,
    thickness: 0.2,
    ior: 1.6,
    flatShading: true,
  });

  const guardSteel = new THREE.MeshStandardMaterial({
    color: VERTEX_ALBEDO,
    vertexColors: true,
    roughness: 0.5,
    metalness: METAL.dark,
    flatShading: true,
  });

  // Two stops lighter than the guard steel: the jaws sit against dark grey leather, and at the
  // guard steel's own value the whole junction collapsed into one black mass.
  //
  // **`polygonOffset` is the only render-path setting in this file and it answers a geometric
  // fact, not an appearance.** Integrations #15 and #16 put three downward faces on ONE plane at
  // `CLAMP_FLOOR_Y`: the two jaws' floors (±16 deep), the shell's base cap (±11) and the grip
  // column's top (±11.087). That is the specification — `check_centerline.py` asserts
  // `shell.minY = clamp.minY` to 0.001 and would reject any of them being nudged off it — and
  // three exactly coplanar faces are a depth-buffer tie, which resolves per triangle and shows as
  // a pale band of crystal cutting across the guard's underside in `closeup-clamp-bases.png`.
  // Biasing the JAWS toward the camera settles the tie the way the object does: the jaws' floor
  // IS the guard's underside, and it covers both of the other two faces outright (±34 × ±16
  // against ±34 × ±11 and ±11.087 × ±11.087), so nothing that ought to be seen is hidden by it.
  //
  // Two things this deliberately is NOT. It is not `renderOrder`, which was deleted from the
  // shell when that went solid: draw order cannot fix a tie between two opaque faces, only a
  // depth bias can. And it is not slack in the flush assertion — the geometry is unchanged and
  // the assertion still reads +0.000000.
  const clampMetal = new THREE.MeshStandardMaterial({
    color: VERTEX_ALBEDO,
    vertexColors: true,
    roughness: 0.42,
    metalness: METAL.bright,
    flatShading: true,
    polygonOffset: true,
    polygonOffsetFactor: -1,
    polygonOffsetUnits: -1,
  });

  // spinnerEnd{Left,Right} only. The crop says these caps are metal and not painted olive: both
  // caps' cross-sections run 90 → 120 → 84 from inner rim to outer rim, i.e. a bright band in the
  // MIDDLE with both silhouette edges falling away, and both sides show the same band even though
  // they face opposite ways. A diffuse ramp off an upper-left key would run the same absolute
  // direction on both and would therefore be inner-bright on one and outer-bright on the other.
  // A view-centred band is a specular event. Top-3%/median is 1.38 here against 1.16 for the
  // matte shell and 1.91 for the pommel, so: metal, and softer-peaked than the pommel — which is
  // why roughness stays at 0.4 and is NOT tightened.
  //
  // metalness goes to METAL.bright because that is the documented ceiling and these caps sit at
  // it; anything above it has nothing to reflect in this rig and turns black.
  //
  // **`envMapIntensity` below does NOTHING and is kept only as the record of what was tried.** It
  // was documented here as "the one lever that buys more reflection without touching the
  // environment", and that is false in this three: r0.185 `three.module.js:18690` overwrites the
  // uniform with `scene.environmentIntensity` for any standard/physical material whose own
  // `envMap` is null, which is every material in this build — what they reflect is the SCENE
  // environment. Measured on `outerCrystal`, where the shell's value makes it easy to read: at 1,
  // 7.5 and 40 the re-framed render is byte-identical (`artifacts/ultima-v2/diag/opaque-trial{,2}/`).
  // Anything that needs a per-material gain in this rig has to use a term the renderer actually
  // reads — `outerCrystal` uses emissive x vColor and says why.
  const guardGold = new THREE.MeshStandardMaterial({
    color: VERTEX_ALBEDO,
    vertexColors: true,
    roughness: 0.4,
    metalness: METAL.bright,
    envMapIntensity: 1.6,
    flatShading: true,
  });

  const driver = new THREE.MeshStandardMaterial({
    color: VERTEX_ALBEDO,
    vertexColors: true,
    roughness: 0.35,
    metalness: METAL.dark,
    flatShading: true,
  });

  // Dark GREY leather, deliberately not the near-black grip leather and not metal: the arms
  // under the drivers are leather-covered components, and reading them as black metal cubes was
  // the defect. Same non-metallic response as the grip, two stops lighter.
  const connectorLeather = new THREE.MeshStandardMaterial({
    color: VERTEX_ALBEDO,
    vertexColors: true,
    roughness: 0.75,
    metalness: 0.0,
    flatShading: true,
  });

  const gripLeather = new THREE.MeshStandardMaterial({
    color: VERTEX_ALBEDO,
    vertexColors: true,
    roughness: 0.8,
    metalness: 0.0,
    flatShading: true,
  });

  const pommelGold = new THREE.MeshStandardMaterial({
    color: VERTEX_ALBEDO,
    vertexColors: true,
    roughness: 0.35,
    metalness: METAL.mid,
    flatShading: true,
  });

  return {
    outerCrystal,
    purpleInsert,
    darkCore,
    rootGem,
    guardSteel,
    clampMetal,
    guardGold,
    driver,
    connectorLeather,
    gripLeather,
    pommelGold,
  };
}

// --- model -----------------------------------------------------------------

type PartMeta = { id: string; explodeDirection?: [number, number, number] };

export function createUltimaWeaponV2Model(options: ModelOptions = {}): THREE.Group {
  const detail = options.detail ?? "full";
  const sides = detail === "blockout" ? 4 : 6;
  const materials = buildMaterials();

  const root = new THREE.Group();
  root.name = "ultimaWeaponV2";

  const nodes = new Map<string, THREE.Object3D>();
  // `rest` is filled in after the whole tree is built, never here: callers set a part's
  // position *after* registering it, so snapshotting at registration captured (0,0,0) and the
  // very first setExplode(0) then slammed every driver, gem and cap back to the origin.
  const explodeParts: { object: THREE.Object3D; rest: THREE.Vector3; offset: THREE.Vector3 }[] = [];

  const register = (object: THREE.Object3D, meta: PartMeta, parent: THREE.Object3D) => {
    object.name = meta.id;
    parent.add(object);
    nodes.set(meta.id, object);
    if (meta.explodeDirection) {
      explodeParts.push({
        object,
        rest: new THREE.Vector3(),
        offset: new THREE.Vector3(...meta.explodeDirection),
      });
    }
    return object;
  };

  const group = (meta: PartMeta, parent: THREE.Object3D) =>
    register(new THREE.Group(), meta, parent);

  const mesh = (
    geometry: THREE.BufferGeometry,
    material: THREE.Material,
    meta: PartMeta,
    parent: THREE.Object3D,
  ) => register(new THREE.Mesh(geometry, material), meta, parent) as THREE.Mesh;

  const bladeGroup = group({ id: "bladeGroup" }, root);
  const hiltGroup = group({ id: "hiltGroup" }, root);

  // ---- outerCrystalShell -------------------------------------------------
  const shellGeometry = loft(SHELL_STATIONS.map(([y, hw, hd]) => ridgedSection(y, hw, hd)));
  // Y = 200 and Y = 760 because that is where the measured profile's two straight pieces meet —
  // the ramp's knot lands at Y = 480, which is the elbow. It used to run from Y = −46, putting
  // the knot at 357 and forcing one straight line across an elbow the artwork plainly has;
  // fitted that way the tip came out 0.083 linear high, which is what pushed the blade's last
  // tenth past `compare_render`'s `min(rgb) < 244` foreground test and cost 0.17 of silhouette
  // IoU. Below Y = 200 the ramp clamps to its root stop, and the measurement says flat there.
  applyRamp(shellGeometry, n(200), n(760), [PALETTE.shellRoot, PALETTE.shellMid, PALETTE.shellTip]);
  // The two colour arguments are DEAD for this part and every other part that ramps first:
  // `applyFacetSteps` only reads them when the geometry has no colour attribute yet. Kept so the
  // call still says which pair the bands are meant to reach.
  applyFacetSteps(shellGeometry, PALETTE.shellTip, PALETTE.shellRoot, 0.85);
  mesh(
    shellGeometry,
    materials.outerCrystal,
    { id: "outerCrystalShell", explodeDirection: [0, 0.9, 0] },
    bladeGroup,
  );

  // The blockout pass carries the macro silhouette: shell, guard, DRIVERS, grip, pommel. The
  // drivers belong here even though they are small — they contribute about a tenth of the
  // silhouette, and leaving them to the structural pass capped the blockout gate's IoU at
  // 0.65 against a 0.85 threshold for a blockout that was otherwise correct. Only the inset
  // blade layers (insert, core, gem), which change no outline, wait for the structural pass.
  const structural = detail !== "blockout";

  // ---- the two skins ------------------------------------------------------
  // `purpleEnergyInsert{Front,Rear}` and `darkCoreTriangle{Front,Rear}` are films laid ON the
  // shell's front and rear surfaces, one `SKIN_STEP` thick, stacked: the dark core's underside
  // is the insert's outer face. They are NOT the bosses this build used to carry — see the
  // reasoning on `SKIN_STEP`, and `spec/check_centerline.py`, which now asserts the skin band
  // and the diamond's step separately so neither can turn into the other.
  //
  // Each pair is lofted from the same station list on both sides, so the two halves are exact
  // mirrors by construction rather than by luck.
  const skin = (
    stations: number[],
    halfWidthAt: (y: number) => number,
    seatUnder: (x: number, y: number) => number,
    sign: 1 | -1,
  ): THREE.BufferGeometry => {
    const apexY = stations[stations.length - 1]!;
    const body = stations
      .slice(0, -1)
      .map((y) => skinSection(y, halfWidthAt(y), (x) => seatUnder(x, y), SKIN_STEP, sign));
    // The tip closes with a zero-width EDGE, not with a point, and that is the 2026-08-09
    // correction. It used to be one point at the film's OUTER depth, broadcast across the ring —
    // which is a point the film's own UNDERSIDE has to climb to. Over the insert's last band,
    // Y = 380…480, the seat therefore left the shell and rose a whole `SKIN_STEP` above it: the
    // film's tip was a wedge of air 100 units long. Measured by the harness's conformity probe on
    // the build this replaces, seat clearance +1.4000 at (0, 480) and +1.4000 at (0, 187) — one
    // full skin thickness, on both films, at both apexes.
    //
    // A film of constant thickness whose FOOTPRINT closes to a point ends in a zero-width,
    // full-thickness edge. `skinSection` at half-width 0 is exactly that — two distinct points on
    // the axis, seat and outer — and it keeps the ring the stack's own width, so `loft` still does
    // not broadcast. Every triangle around the collapsed x-breaks is degenerate and dropped, and
    // the end cap is skipped because fewer than three distinct points survive de-duplication. So
    // the tip closes with its underside still ON the host, which is what "貼齊" means at the tip.
    const apex = skinSection(apexY, 0, (x) => seatUnder(x, apexY), SKIN_STEP, sign);
    return loft([...body, apex]);
  };

  // ---- purpleEnergyInsert{Front,Rear} --------------------------------------
  for (const face of ["Front", "Rear"] as const) {
    const sign = face === "Front" ? 1 : -1;
    const geometry = skin(INSERT_SKIN_STATIONS, insertHalfWidthAt, shellFrontDepth, sign);
    applyRamp(geometry, n(42), n(INSERT_APEX_Y), [
      PALETTE.insertBase,
      PALETTE.insertMid,
      PALETTE.insertApex,
    ]);
    applyFacetSteps(geometry, PALETTE.insertBase, PALETTE.insertApex, 0.55, sign);
    const half = mesh(
      geometry,
      materials.purpleInsert,
      { id: `purpleEnergyInsert${face}`, explodeDirection: [0, 0.45, 0.55 * sign] },
      bladeGroup,
    );
    half.visible = structural;
  }

  // ---- darkCoreTriangle{Front,Rear} ---------------------------------------
  // The second film, seated on the first: its underside is `shellFrontDepth + SKIN_STEP`, so it
  // rides the insert wherever the two overlap and the order cannot invert by editing a number.
  for (const face of ["Front", "Rear"] as const) {
    const sign = face === "Front" ? 1 : -1;
    const geometry = skin(
      CORE_SKIN_STATIONS,
      coreHalfWidthAt,
      (x, y) => shellFrontDepth(x, y) + SKIN_STEP,
      sign,
    );
    applyRamp(geometry, n(CORE_BASE_Y), n(CORE_APEX_Y), [PALETTE.coreBody, PALETTE.coreTip]);
    applyFacetSteps(geometry, PALETTE.coreBody, PALETTE.coreTip, 0.5, sign);
    const half = mesh(
      geometry,
      materials.darkCore,
      // Each half explodes onto its own side, so pulling the model apart shows that there are
      // two of them. A shared direction would slide them as one and hide the split.
      { id: `darkCoreTriangle${face}`, explodeDirection: [0, 0.2, 0.8 * sign] },
      bladeGroup,
    );
    half.visible = structural;
  }

  // ---- rootDiamondGem{Front,Rear} -----------------------------------------
  // A SET stone, directed 2026-08-09: a flat base plane sunk to the lowest the blade's surface
  // gets under the rhombus, a vertical socket wall up to a LEVEL girdle line, and a 四角錐 crown
  // closing on one apex over the rhombus's centre at (0, GEM_WAIST_Y).
  //
  // It is the only mesh on this blade that does NOT follow the surface it is mounted on, and the
  // reason is that the surface climbs 5.8 units under the stone's own footprint — so a stone that
  // follows it has its upper half standing further out than its lower half. See gemHalfSection.
  //
  // Both tips are RINGS, not points: at the culet and at the top vertex the half-width is zero, so
  // the ring collapses to the vertical segment from the base plane to the girdle — the prism's own
  // corner edge. `loft` drops the degenerate triangles and skips the end caps, and the solid closes
  // on that edge; `tests/ultima-v2-solid.test.mjs` is what says so.
  for (const face of ["Front", "Rear"] as const) {
    const sign = face === "Front" ? 1 : -1;
    const geometry = loft(
      GEM_SEAT_STATIONS.map((y) => gemHalfSection(y, gemHalfWidthAt(y), gemCrownDepthAt(y), sign)),
    );
    // Bright through the middle, not dark at the base: the diamond is the sword's visual centre,
    // and a shadow-to-highlight ramp bottom-to-top left its lower half reading as maroon dead
    // weight between the two jaws.
    applyRamp(geometry, n(GEM_BASE_Y), n(GEM_APEX_Y), [
      PALETTE.gemMain,
      PALETTE.gemHighlight,
      PALETTE.gemMain,
    ]);
    applyFacetSteps(geometry, PALETTE.gemHighlight, PALETTE.gemShadow, 0.9, sign);
    // The most raised layer, 1.57 T for the pair: each half's whole outline clears the dark core
    // on its own face, so the diamond is readable from the front and from the rear without the
    // shell needing to be see-through. The artwork's overlap order is reproduced by depth.
    const half = mesh(
      geometry,
      materials.rootGem,
      { id: `rootDiamondGem${face}`, explodeDirection: [0, 0, 1.1 * sign] },
      bladeGroup,
    );
    half.visible = structural;
  }

  // ---- crystalClamp -------------------------------------------------------
  // Two mirrored triangular prisms cradling the diamond's lower half, each one flush against the
  // stone's own lower edge (`CLAMP_OUTLINE`). The load path the whole hilt is organised around
  // runs: shell neck -> purple stack -> diamond -> these two jaws -> the socket's shoulders ->
  // the grip. A single block under the diamond would not read as a mechanical clamp, and a
  // floating diamond would not read as mounted at all.
  //
  // The two meet on the axis at the culet and NOWHERE else: they share that one vertical edge and
  // have no overlapping face, so there is no coplanar pair to z-fight even though both prisms are
  // extruded to the same ±`CLAMP_HALF_DEPTH`.
  for (const side of ["Left", "Right"] as const) {
    const sign = side === "Right" ? 1 : -1;
    const outline = CLAMP_OUTLINE.map(([x, y]) => [sign * x, y] as [number, number]);
    const geometry = extrudeOutline(sign > 0 ? outline : [...outline].reverse(), CLAMP_HALF_DEPTH);
    applyFacetSteps(geometry, PALETTE.clampMetal, PALETTE.clampMetalShadow);
    const jaw = mesh(
      geometry,
      materials.clampMetal,
      { id: `crystalClamp${side}`, explodeDirection: [sign * 0.7, 0.1, 0.0] },
      hiltGroup,
    );
    // No Z offset: the jaw is a prism centred on the middle plane, so it reads identically
    // from the front and the rear. Its depth exceeds the shell's, so it shows on both faces.
    jaw.visible = structural;
  }

  const driverDefs: [string, 1 | -1, "upper" | "lower"][] = [
    ["driverLeftUpper", -1, "upper"],
    ["driverLeftLower", -1, "lower"],
    ["driverRightUpper", 1, "upper"],
    ["driverRightLower", 1, "lower"],
  ];

  // ---- leatherConnector{Left,Right} ---------------------------------------
  // The horizontal limbs of the T: complete closed cylinders of constant radius, capped at both
  // ends, centred on Z=0. The rods attach to their surface; there are no socket components.
  for (const side of ["Left", "Right"] as const) {
    const sign = side === "Right" ? 1 : -1;
    // The root cap is AT the root, x = 0, with no inset — integration #17. The rake is the shell's
    // own taper and the cap's LOWER RIM is the jaw's outer corner, so the cap's whole diameter
    // lies on the crystal's lower slanted flank and there is nothing to slide inward. Nothing of
    // the cap hangs below the guard's floor any more: the arm rakes away from that corner and
    // downward, which is what the sketch draws, and it no longer starts 10.4 units under it.
    const geometry = loft([
      radialSectionX(0, CONNECTOR_RADIUS, CONNECTOR_SIDES),
      radialSectionX(CONNECTOR_LENGTH, CONNECTOR_RADIUS, CONNECTOR_SIDES),
    ]);
    applyFacetSteps(geometry, PALETTE.connectorSeam, PALETTE.connectorShadow);
    const arm = mesh(
      geometry,
      materials.connectorLeather,
      { id: `leatherConnector${side}`, explodeDirection: [sign * 0.85, -0.35, 0] },
      hiltGroup,
    );
    arm.position.set(n(sign * CONNECTOR_ROOT[0]), n(CONNECTOR_ROOT[1]), 0);
    arm.rotation.z = THREE.MathUtils.degToRad(
      sign > 0 ? CONNECTOR_ANGLE_DEG : 180 - CONNECTOR_ANGLE_DEG,
    );
  }

  // ---- spinnerEnd{Left,Right} ---------------------------------------------
  // Hangs straight down from inside its connector arm, exactly as pointedMetalPommel does: the
  // profile is lathed about Y, so `rotation` stays zero and the two sides differ only in X.
  // Nothing here is flush against anything — the joint is hidden by burial, not by mating two
  // faces, because two faces cannot mate once the axes differ by 40°. See spinnerSeat().
  //
  // The seat ring is inside `spinnerProfile()` now rather than spliced on here: splicing it on
  // was what let the seat move while the rows below it stayed put, which is the whole of the ramp
  // defect. One caller, one profile, one place the shape is decided.
  const seat = spinnerSeat();
  const profile = spinnerProfile();
  for (const side of ["Left", "Right"] as const) {
    const sign = side === "Right" ? 1 : -1;
    const geometry = lathe(profile, sides);
    applyFacetSteps(geometry, PALETTE.gold, PALETTE.goldShadow);
    const spinner = mesh(
      geometry,
      materials.guardGold,
      // Explodes along its own axis now that the axis is vertical, not along the arm's rake.
      { id: `spinnerEnd${side}`, explodeDirection: [sign * 0.6, -1.05, 0] },
      hiltGroup,
    );
    spinner.position.set(n(sign * seat.x), 0, 0);
  }

  // ---- driverArray --------------------------------------------------------
  // Four transforms over ONE unit-length cylinder. Each rod's root cap is buried inside its
  // connector — deep enough that the whole cap clears the wall, never so deep that it reaches the
  // arm's central axis — and the rod runs outward from there. The two bands need different
  // lengths for that: their axes meet the same cylinder at different distances. So the shared
  // geometry is a unit cylinder and the length lives in the transform's X scale, which keeps one
  // reusable geometry AND a closed joint; a single fixed length can satisfy one or the other,
  // never both.
  const driverArray = group({ id: "driverArray" }, hiltGroup);
  const unitRod = loft([
    radialSectionX(0, DRIVER_RADIUS, DRIVER_SIDES), // root cap, sunk inside the connector
    radialSectionX(0.94, DRIVER_RADIUS, DRIVER_SIDES),
    radialSectionX(1, DRIVER_RADIUS * 0.86, DRIVER_SIDES), // capped outer end
  ]);
  applyFacetSteps(unitRod, PALETTE.driverHighlight, PALETTE.driverShadow);
  for (const [id, sign, band] of driverDefs) {
    const elevation = THREE.MathUtils.degToRad(DRIVER_ELEVATION_DEG[band]);
    const rootRadius = driverRootRadius(DRIVER_ELEVATION_DEG[band]);
    const rod = mesh(
      unitRod,
      materials.driver,
      { id, explodeDirection: [sign * 1.0, Math.sin(elevation) * 0.9, 0] },
      driverArray,
    );
    rod.position.set(
      n(DRIVER_CENTRE[0] + sign * rootRadius * Math.cos(elevation)),
      n(DRIVER_CENTRE[1] + rootRadius * Math.sin(elevation)),
      0,
    );
    rod.rotation.z = sign > 0 ? elevation : Math.PI - elevation;
    // Scaling along the rod's own axis only: the circular section stays exactly circular.
    rod.scale.x = DRIVER_RADIAL_END - rootRadius;
  }

  // ---- leatherGrip --------------------------------------------------------
  // ONE column, one width, one mesh. Correction A: no tang, no T-head, no step at the guard's
  // underside — the octagonal shaft runs from the leather's measured lower edge straight up to
  // GRIP_TOP_Y, where its flat top face lies against the two jaws' floor (integration #16). It is
  // not inserted between them and they do not close on its flanks. There is no waist under
  // the guard and none of the repeated protruding ring bands it used to carry; the wrap is
  // vertex-colour banding on the same shaft, which is what "subtle wrapping rather than multiple
  // hard collars" means when the source has no relief at all.
  const gripGeometry = loft([
    polygonSection(GRIP_TOP_Y, GRIP_HALF_WIDTH, GRIP_HALF_WIDTH, 8),
    polygonSection(GUARD_UNDERSIDE_Y, GRIP_HALF_WIDTH, GRIP_HALF_WIDTH, 8),
    polygonSection(-58, GRIP_HALF_WIDTH, GRIP_HALF_WIDTH, 8),
    polygonSection(-112, GRIP_HALF_WIDTH, GRIP_HALF_WIDTH, 8),
    polygonSection(GRIP_BOTTOM_Y, GRIP_HALF_WIDTH, GRIP_HALF_WIDTH, 8),
  ]);
  // Banded from the guard's underside down, so the nine wraps keep the pitch they were fitted at;
  // the length inside the guard continues the same phase rather than compressing nine wraps into
  // a longer part.
  applyWrapBanding(
    gripGeometry,
    n(GUARD_UNDERSIDE_Y),
    n(GRIP_BOTTOM_Y),
    PALETTE.grip,
    PALETTE.gripWrap,
  );
  applyFacetSteps(gripGeometry, PALETTE.gripWrap, PALETTE.grip, 0.6);
  mesh(
    gripGeometry,
    materials.gripLeather,
    { id: "leatherGrip", explodeDirection: [0, -0.7, 0] },
    hiltGroup,
  );

  // ---- pointedMetalPommel -------------------------------------------------
  // A cone, and the piece directly below the leather — there is no collar between them, because
  // the crop has none. Its base ring is the GRIP'S OWN bottom ring: same plane at GRIP_BOTTOM_Y,
  // same facet count, same circumradius, so the two end faces butt exactly and the joint reads
  // flush from the front AND from every rotation. `sides` is deliberately not used here — the
  // cone follows the column it is bolted to, not the pass's global detail level, and the column
  // is an 8-gon in every pass.
  const pommelGeometry = lathe(
    [
      [POMMEL_RADIUS, GRIP_BOTTOM_Y],
      [0, POMMEL_TIP_Y],
    ],
    POMMEL_SIDES,
  );
  applyFacetSteps(pommelGeometry, PALETTE.pommel, PALETTE.pommelShadow);
  mesh(
    pommelGeometry,
    materials.pommelGold,
    { id: "pointedMetalPommel", explodeDirection: [0, -1.15, 0] },
    hiltGroup,
  );

  // ---- runtime ------------------------------------------------------------
  for (const part of explodeParts) part.rest.copy(part.object.position);

  const runtime: SculptRuntime = {
    nodes,
    materials,
    setExplode: (amount: number) => {
      const t = THREE.MathUtils.clamp(amount, 0, 1);
      for (const part of explodeParts) {
        part.object.position.copy(part.rest).addScaledVector(part.offset, t * 1.6);
      }
    },
    setPartVisible: (id: string, visible: boolean) => {
      const node = nodes.get(id);
      if (node) node.visible = visible;
    },
    provenance: {
      route: "artwork-measured procedural rebuild (review package v2)",
      exactnessTier: "measured silhouette, inferred depth",
      thicknessConfidence: 0.35,
    },
  };

  let spin = 0;
  let spinning = false;
  root.userData.sculptRuntime = runtime;
  root.userData.setDisplayRotation = (value: boolean) => {
    spinning = value;
    if (!value) {
      spin = 0;
      root.rotation.y = 0;
    }
  };
  root.userData.tick = (delta: number) => {
    if (!spinning) return;
    spin += delta * 0.45;
    root.rotation.y = spin;
  };

  return root;
}
