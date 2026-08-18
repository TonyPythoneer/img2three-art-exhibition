import * as THREE from "three";

import { COLORS } from "./colors";
import { chamferedRing, loft, type Ring } from "./loft";
import { BANDS, EYE_POLYGON, HALF_DEPTH, halfWidthAt, len, x, y } from "./measurements";

/**
 * The MMX2 wireframe Sigma head, green variant.
 *
 * The reference is itself a wireframe render of a low-poly mesh, so the reconstruction medium
 * IS the target: faceted shells with a bright-green edge overlay on the sheet's own navy. That
 * is faithful here rather than stylised — see `artifacts/exhibits/mmx2-sigma-virus/spec/reading.md`.
 *
 * Eight shape codes, thirteen instances. Every mirror pair is authored once and negated in x,
 * which is also what the symmetry assertion checks.
 */

/**
 * How the wireframe is DRAWN, which on this subject is part of the subject.
 *
 * `gate_edge_density.py` measures total line length over head height: the reference carries 11.9
 * head-heights of line, and the first build carried 59.8 — 5x, which reads as a mesh preview
 * rather than as the sprite. Two causes, both here:
 *
 * - RING_STEP: a ring every 2 reference rows put 24 rings through the skull alone. The
 *   silhouette table is dense enough that a ring every 7 rows still lands on measured extents;
 *   only the segments BETWEEN rings straighten.
 * - EDGE_ANGLE: `EdgesGeometry` at 1 degree draws every quad's triangulation diagonal, because a
 *   lofted quad between two different rings is not planar and its two triangles never agree to
 *   within a degree. Raising the threshold drops the diagonals and keeps the real creases.
 */
const RING_STEP = 7;
const EDGE_ANGLE = 30;

/** The widest the skull proper gets — rows 14..27 run px 3..41, so half-width 19px. */
const SKULL_MAX_HALF = len(19);

/**
 * Depth follows width: a row that is 80% of the widest row is 80% as deep.
 *
 * ponytail: one global depth ratio, no per-row front/back taper. The upgrade path is a per-row
 * profile read off the yawed frames, which would need each frame's yaw solved first.
 */
const halfDepthAt = (py: number): number => HALF_DEPTH * (halfWidthAt(py) / halfWidthAt(37));

/**
 * The face plane: where the eyes and brow sit on the shell's front surface.
 *
 * The yawed frames — `profile-width.json.mostProfile` at (336, 1095) and (540, 957), both ~60°
 * off frontal — put the eye accent hard against the leading edge with the whole faceted dome
 * filling the frame behind it. Anchoring the face parts to the shell's front surface already
 * satisfies that: the eyes end up with ~0.1 of the depth ahead of them and ~1.9 behind.
 *
 * A stronger reading was tried and REJECTED by its own render: giving every ring a per-row
 * z-centre so all their FRONTS aligned on one plane. Narrow rows have shallow depth, so that
 * rule pushed the crown and the chin tabs forward while the wide ear-pod rows stayed back —
 * under perspective the near extremes magnified and the front view grew from 476x695 to
 * 480x796, failing the aspect gate at 0.1147 against a 0.06 tolerance. The reference says the
 * face is at the front; it says nothing about the crown's z-centre, and inventing a rule for it
 * cost 11% of aspect. So the shells stay centred.
 */
const FACE_Z = halfDepthAt(36);

/** Rings sampled every `step` frame rows through a band, with a per-row half-width override. */
function bandRings(
  from: number,
  to: number,
  opts: {
    step?: number;
    chamfer?: number;
    halfWidth?: (py: number) => number;
    halfDepth?: (py: number) => number;
  } = {},
): Ring[] {
  const step = opts.step ?? RING_STEP;
  const chamfer = opts.chamfer ?? 0.35;
  const hw = opts.halfWidth ?? halfWidthAt;
  const hd = opts.halfDepth ?? halfDepthAt;
  const rings: Ring[] = [];
  for (let py = from; py <= to; py += step) {
    rings.push({ y: y(py), pts: chamferedRing(hw(py), hd(py), chamfer) });
  }
  const last = to;
  if (rings.length === 0 || (to - from) % step !== 0) {
    rings.push({ y: y(last), pts: chamferedRing(hw(last), hd(last), chamfer) });
  }
  return rings;
}

const wireMat = () =>
  new THREE.LineBasicMaterial({ color: COLORS.wire, toneMapped: false, transparent: false });

const eyeWireMat = () =>
  new THREE.LineBasicMaterial({ color: COLORS.eye, toneMapped: false, transparent: false });

/**
 * The fill sits a hair behind its own edges. Without the polygon offset the edge overlay
 * z-fights the surface it outlines and the wireframe breaks into speckle at grazing angles —
 * the same failure the part-inspector highlight has to solve.
 */
const fillMat = (color: string) =>
  new THREE.MeshStandardMaterial({
    color,
    roughness: 0.85,
    metalness: 0,
    flatShading: true,
    polygonOffset: true,
    polygonOffsetFactor: 1,
    polygonOffsetUnits: 1,
  });

/** A named part: a faceted fill plus the edge overlay that rides it. */
function part(name: string, geometry: THREE.BufferGeometry, opts: { eye?: boolean } = {}) {
  const mesh = new THREE.Mesh(geometry, fillMat(opts.eye ? COLORS.eye : COLORS.ground));
  mesh.name = name;
  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(geometry, EDGE_ANGLE),
    opts.eye ? eyeWireMat() : wireMat(),
  );
  edges.name = `${name}Edges`;
  // Relief that rides its shell, not a component you could hold: the inspector must treat it as
  // one part with its fill, and explode must carry it along instead of flying it off alone.
  edges.userData.explodeWithParent = true;
  mesh.add(edges);
  return mesh;
}

/** Mirror an authored part to the other side by negating x — never by re-authoring it. */
function mirrored(name: string, build: () => THREE.Mesh): [THREE.Mesh, THREE.Mesh] {
  const right = build();
  right.name = `${name}R`;
  const left = build();
  left.name = `${name}L`;
  left.scale.x = -1;
  return [left, right];
}

function createSkullShell() {
  const [from, to] = BANDS.skullShell;
  return part(
    "skullShell",
    loft(
      // The skull is the part that OWNS the silhouette, so it keeps a fine ring step while the
      // rest of the assembly runs at RING_STEP. Coarsening this one alone cost 0.006 of front IoU
      // and most of the crown band; coarsening the others cost nothing measurable.
      bandRings(from, to, {
        step: 3,
        halfWidth: (py) => Math.min(halfWidthAt(py), SKULL_MAX_HALF),
      }),
      { capTop: true, capBottom: true },
    ),
  );
}

function createCrownPlate() {
  const [from, to] = BANDS.crownPlate;
  return part(
    "crownPlate",
    loft(bandRings(from, to, { step: 4, chamfer: 0.45 }), { capTop: true, capBottom: true }),
  );
}

/** The tall vertical helmet plate on each side, sitting proud of the skull's outer face. */
function createSidePanel() {
  const [from, to] = BANDS.sidePanel;
  const thickness = len(2.5);
  const rings: Ring[] = [];
  for (let py = from; py <= to; py += 6) {
    const outer = Math.min(halfWidthAt(py), SKULL_MAX_HALF);
    const d = halfDepthAt(py) * 0.62;
    rings.push({
      y: y(py),
      pts: [
        [outer + thickness, d],
        [outer + thickness, -d],
        [outer - thickness, -d],
        [outer - thickness, d],
      ],
    });
  }
  return part("sidePanel", loft(rings, { capTop: true, capBottom: true }));
}

/** The rounded lobe that makes rows 34..42 the widest on the whole head (full frame width). */
function createEarPod() {
  const [from, to] = BANDS.earPod;
  const rings: Ring[] = [];
  for (let py = from; py <= to; py += 5) {
    const outer = halfWidthAt(py);
    const inner = SKULL_MAX_HALF - len(1);
    const d = halfDepthAt(py) * 0.5;
    // The lobe reaches the measured full frame width at EVERY row of its band — rows 34..42 all
    // run px 0..46 in the reference. Easing the tip in and out with the bulge kept it inside the
    // skull and cost the whole protrusion; the bulge belongs on the depth instead.
    const bulge = 0.45 + 0.55 * Math.sin(((py - from) / (to - from)) * Math.PI);
    rings.push({
      y: y(py),
      pts: [
        [outer, d * bulge],
        [outer, -d * bulge],
        [inner, -d],
        [inner, d],
      ],
    });
  }
  return part("earPod", loft(rings, { capTop: true, capBottom: true }));
}

/**
 * The triangular ridge over one eye. Its mirror meets it in a V at the nose bridge, but the two
 * are separate parts — the reference draws two distinct triangles, not one tent across the whole
 * face, which is what an over-wide `outer` produced on the first pass.
 */
function createBrowRidge() {
  const [from, to] = BANDS.browRidge;
  const outer = len(13);
  const inner = len(3);
  const zFront = FACE_Z;
  const rings: Ring[] = [];
  for (let py = from + 2; py <= to; py += 2) {
    const t = (py - (from + 2)) / (to - (from + 2));
    // The ridge starts as a point at the top and opens out into the brow bar.
    const half = inner + (outer - inner) * t;
    const d = len(1.2 + 1.6 * t);
    rings.push({
      y: y(py),
      pts: [
        [half, zFront],
        [half, zFront - d],
        [inner * 0.6, zFront - d],
        [inner * 0.6, zFront],
      ],
    });
  }
  return part("browRidge", loft(rings, { capTop: true, capBottom: true }));
}

/**
 * The eye: the one part that carries colour code C3, and the only interior feature the gates can
 * score. Traced straight from `EYE_OUTLINE` — the reference's own per-column top and bottom rows —
 * rather than fitted to the eye's bounding box.
 *
 * The bounding-box version came first and passed every gate: right band, right slant, right
 * filled area. It still read wrong next to the reference, because the eye is a leaf that tapers
 * to a point at the bridge and cuts sharply up at the outer tip, not a bar. Gates that score a
 * band and an area cannot tell those apart, so the outline is measured instead of inferred.
 *
 * Guess list G3 reads the eye as recessed into the face plane, so it is extruded backwards from
 * the brow's front face rather than standing proud of it.
 */
function createEyePlate() {
  // Recessed, per guess G3: the eye sits BEHIND the brow front face, not flush with it. Moving
  // it to within 0.4px of the face plane pushed it toward the camera and perspective grew its
  // area from 24.0% to 30.6% relative error — over the gate. 0.9 of the face plane is where it
  // passes.
  const zFront = FACE_Z * 0.9;

  const shape = new THREE.Shape();
  const first = EYE_POLYGON[0];
  if (!first) throw new Error("EYE_POLYGON must not be empty");
  shape.moveTo(len(first[0]), y(first[1]));
  for (const [px, row] of EYE_POLYGON.slice(1)) shape.lineTo(len(px), y(row));
  shape.closePath();

  const g = new THREE.ExtrudeGeometry(shape, { depth: len(2), bevelEnabled: false });
  g.translate(0, 0, zFront - len(2));
  return part("eyePlate", g.toNonIndexed(), { eye: true });
}

function createJawBlock() {
  const [from, to] = BANDS.jawBlock;
  return part(
    "jawBlock",
    loft(bandRings(from, to, { step: 6, chamfer: 0.15 }), { capTop: true, capBottom: true }),
  );
}

/**
 * Guess list G4: the two feet at the block's bottom corners appear in every same-scale front
 * frame at the same place, so they are geometry rather than one frame's rasterisation. What
 * they represent is not resolvable, and does not change the build.
 */
function createChinTab() {
  const [from, to] = BANDS.chinTab;
  const outer = halfWidthAt(65);
  const inner = outer - len(5);
  const d = halfDepthAt(65) * 0.4;
  const rings: Ring[] = [
    {
      y: y(from),
      pts: [
        [outer, d],
        [outer, -d],
        [inner, -d],
        [inner, d],
      ],
    },
    {
      y: y(to),
      pts: [
        [outer, d],
        [outer, -d],
        [inner, -d],
        [inner, d],
      ],
    },
  ];
  return part("chinTab", loft(rings, { capTop: true, capBottom: true }));
}

export type SigmaVirusHeadOptions = {
  /** Scale applied to the whole head. 1 = the reference frame's height. */
  scale?: number;
};

/**
 * Build the head. The returned group authors NO geometry of its own — every vertex comes from
 * a part factory above, which is what keeps the assembly file honest.
 */
export function createSigmaVirusHead(opts: SigmaVirusHeadOptions = {}): THREE.Group {
  const root = new THREE.Group();
  root.name = "sigmaVirusHead";

  const [earL, earR] = mirrored("earPod", createEarPod);
  const [panelL, panelR] = mirrored("sidePanel", createSidePanel);
  const [browL, browR] = mirrored("browRidge", createBrowRidge);
  const [eyeL, eyeR] = mirrored("eyePlate", createEyePlate);
  const [footL, footR] = mirrored("chinTab", createChinTab);

  root.add(
    createSkullShell(),
    createCrownPlate(),
    panelL,
    panelR,
    earL,
    earR,
    browL,
    browR,
    eyeL,
    eyeR,
    createJawBlock(),
    footL,
    footR,
  );

  // Recentre on the model's own bounds so the viewer orbits the head, not the origin the
  // measurements happen to be expressed in.
  const box = new THREE.Box3().setFromObject(root);
  const centre = box.getCenter(new THREE.Vector3());
  root.children.forEach((c) => c.position.sub(centre));

  root.scale.setScalar(opts.scale ?? 1);
  root.userData.provenance =
    "reference-measured · front view only · depth is guess G1 (1.25 x width), back of head is guess G2";
  return root;
}

/** Named for the assertions and the part-coverage gate: 8 shape codes, 13 instances. */
export const SIGMA_VIRUS_PARTS = [
  "skullShell",
  "crownPlate",
  "sidePanelL",
  "sidePanelR",
  "earPodL",
  "earPodR",
  "browRidgeL",
  "browRidgeR",
  "eyePlateL",
  "eyePlateR",
  "jawBlock",
  "chinTabL",
  "chinTabR",
] as const;

export { x as frameX, y as frameY };
