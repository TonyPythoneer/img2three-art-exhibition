import * as THREE from "three";
import { MANNEQUIN } from "./parts";
import { CHEST } from "./measurements";

/**
 * S-08 chestSlab — prompt §4[8], and the hub of §4's whole socket ledger: it is the only
 * part that emits four sockets (waistTop, neckBase, shoulderL, shoulderR).
 *
 * A lofted hexagonal prism, widest at the shirt's widest row and tapering to the waist,
 * with every vertical edge chamfered. Stage 1 does NOT build the two chest straps — they
 * are unscheduled in §2 and get no stage without a user order.
 *
 * THREE THINGS §4[8] SAYS THAT THE MEASUREMENT ANSWERS DIFFERENTLY, all recorded in
 * landmarks.json's parts.chest rather than quietly obeyed:
 *
 *   - "widest at the shoulder line" is not where the slab is widest. AT the shoulder line
 *     the shirt is 0.00124 wide — one pixel — because up there the figure is neck, black
 *     pauldron and bare deltoid, and the purple only begins below the collar. The widest
 *     row is 0.1186 BELOW the shoulder line. The slab is still built from chestTop, which
 *     is the ledger's anchor; what moved is where its widest ring sits.
 *   - "front and back near-planar, sides are narrow chamfers" is a slab claim, and the
 *     measured depth/width ratio is 0.622 — nearer a block than a sheet. Stage 0's
 *     C_torsoIsASlab said the same thing from a different direction and came back
 *     INDETERMINATE. No threshold for "slabness" has been pinned with a fake frame, so
 *     nothing is asserted and the chest is built at its MEASURED depth.
 *   - the front/back width spread is 0.0822 against an uncertainty of 0.05447, so this
 *     part's own cross-view check is REVIEW, not PASS. The back reads wider than the front
 *     because the front's purple is cut by the two straps while the back carries one
 *     diagonal panel. Averaged and flagged rather than silently taking the larger.
 *
 * Frame: local origin is chestTop (§1.4) — the trunk anchor, placed in Stage 1B straight
 * from the shoulder-line landmark. Top face on y=0, waist at y=-height.
 */
export function createChest(): THREE.Group {
  const {
    height,
    widestWidth,
    widestDrop,
    widthAtWaistTop,
    depthAtWidest,
    depthAtWaistTop,
    shoulderOffsetX,
  } = CHEST;

  // The top ring is the collar: the shirt is not visible up here, so its section is the
  // widest ring pulled in by the same proportion the waist is. Derived, not measured, and
  // the only ring of the three that is.
  const topWidth = widthAtWaistTop;
  const topDepth = depthAtWaistTop;

  /** Hexagon: two wide faces front and back, two narrow chamfers at the sides (§4[8]). */
  const ring = (w: number, d: number, y: number): Array<[number, number, number]> => [
    [w / 2 - d / 4, y, d / 2],
    [w / 2, y, d / 4],
    [w / 2, y, -d / 4],
    [w / 2 - d / 4, y, -d / 2],
    [-w / 2 + d / 4, y, -d / 2],
    [-w / 2, y, -d / 4],
    [-w / 2, y, d / 4],
    [-w / 2 + d / 4, y, d / 2],
  ];

  const rings = [
    ring(topWidth, topDepth, 0),
    ring(widestWidth, depthAtWidest, -widestDrop),
    ring(widthAtWaistTop, depthAtWaistTop, -height),
  ];
  const n = 8;
  const positions: number[] = [];
  const indices: number[] = [];
  const push = (p: [number, number, number]): number => {
    const i = positions.length / 3;
    positions.push(p[0], p[1], p[2]);
    return i;
  };
  const base = rings.map((r) => r.map(push));

  for (let k = 0; k < rings.length - 1; k += 1) {
    for (let i = 0; i < n; i += 1) {
      const a = base[k]![i]!;
      const b = base[k]![(i + 1) % n]!;
      const c = base[k + 1]![(i + 1) % n]!;
      const d = base[k + 1]![i]!;
      indices.push(a, b, c, a, c, d);
    }
  }
  const t = base[0]!;
  const bt = base[2]!;
  for (let i = 1; i < n - 1; i += 1) {
    indices.push(t[0]!, t[i]!, t[i + 1]!);
    indices.push(bt[0]!, bt[i + 1]!, bt[i]!);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();

  const group = new THREE.Group();
  group.name = "chest";
  group.add(new THREE.Mesh(geometry, MANNEQUIN));
  // §4's ledger. `neckBase` is one of the two UPWARD mates — the neck sits ON the chest,
  // so both parts emit the same name and §5.5 compares them directly. The chest's own
  // neckBase is its top face, i.e. its origin, so the vector is zero and that is correct
  // rather than missing.
  group.userData.sockets = {
    waistTop: new THREE.Vector3(0, -height, 0),
    neckBase: new THREE.Vector3(0, 0, 0),
    shoulderL: new THREE.Vector3(shoulderOffsetX, -widestDrop, 0),
    shoulderR: new THREE.Vector3(-shoulderOffsetX, -widestDrop, 0),
  };
  return group;
}
