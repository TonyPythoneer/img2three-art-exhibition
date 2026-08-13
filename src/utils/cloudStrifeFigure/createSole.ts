import * as THREE from "three";
import { MANNEQUIN } from "./parts";
import { SOLE } from "./measurements";

/**
 * S-01 soleSlab — prompt §4[1], the first Stage 1 part.
 *
 * A flat slab of uniform thickness, not a curved shoe sole. In plan it is a TRAPEZOID,
 * wide at the heel and narrow at the toe, with both ends cut by a blunt chamfer, and the
 * splay angle baked in.
 *
 * Frame. The part's local origin is its own upper socket `soleTop` (§1.4), so the top face
 * sits on y=0 and the bottom on y=-thickness; placing the part at soleTop's figure height
 * in Stage 1B is what lands the bottom face on the ground at Y=0.
 *
 * The splay is baked into the VERTICES, not into `group.rotation`. §5.10 compares the two
 * sides by negating x and diffing point for point, and a rotation carried on the node
 * would never reach that comparison.
 *
 * What is measured and what is adopted, because the difference decides which gate can
 * falsify what (`spec/landmarks.json` → `parts.sole`):
 *
 *   measured  the three extents A (lateral), B (fore-aft) and T (thickness), and the plan
 *             trapezoid solved from them.
 *   adopted   L/W = 2.4, toe taper 0.72, end chamfer 0.34 T. Four orthographic views fix
 *             A, B and T and nothing else — every (L, W, theta) reproducing them scores
 *             IDENTICALLY on all four orthographic silhouettes, so only the three-quarter
 *             orbit render can falsify these three.
 */
export function createSole(side: "L" | "R"): THREE.Group {
  const sideSign = side === "L" ? 1 : -1;

  const { thickness, splayDeg, plan } = SOLE;
  const halfLength = plan.length / 2;
  const heelHalf = plan.heelWidth / 2;
  const toeHalf = plan.toeWidth / 2;
  const chamfer = plan.endChamfer;

  // The plan outline, foot-local: +z toward the toe, +x toward the figure's left. Eight
  // vertices — four corners, each replaced by its own chamfer facet, which is what reads
  // as a blunt end at 8x instead of a point.
  const outline: Array<[number, number]> = [
    [-toeHalf + chamfer, halfLength],
    [toeHalf - chamfer, halfLength],
    [toeHalf, halfLength - chamfer],
    [heelHalf, -halfLength + chamfer],
    [heelHalf - chamfer, -halfLength],
    [-heelHalf + chamfer, -halfLength],
    [-heelHalf, -halfLength + chamfer],
    [-toeHalf, halfLength - chamfer],
  ];

  // Winding decides which way every normal points, and getting it wrong renders an
  // inside-out slab that still passes a dimension gate. Rather than reason about it, force
  // the outline positive-area once; the caps and walls below are then outward by
  // construction.
  const signedArea = outline.reduce((sum, [x0, z0], i) => {
    const [x1, z1] = outline[(i + 1) % outline.length]!;
    return sum + (x0 * z1 - x1 * z0);
  }, 0);
  if (signedArea < 0) outline.reverse();

  const n = outline.length;
  const positions: number[] = [];
  const indices: number[] = [];

  // Caps and walls get their OWN vertices. A shared vertex would average the normals
  // across a crease and undo the flat shading the facet gate exists to protect.
  const ring = (y: number): number => {
    const base = positions.length / 3;
    for (const [x, z] of outline) positions.push(x, y, z);
    return base;
  };

  const top = ring(0);
  const bottom = ring(-thickness);
  for (let i = 1; i < n - 1; i += 1) {
    indices.push(top, top + i + 1, top + i); // top cap, facing +y
    indices.push(bottom, bottom + i, bottom + i + 1); // bottom cap, facing -y
  }

  for (let i = 0; i < n; i += 1) {
    const [x0, z0] = outline[i]!;
    const [x1, z1] = outline[(i + 1) % n]!;
    const a = positions.length / 3;
    positions.push(x0, 0, z0, x1, 0, z1, x1, -thickness, z1, x0, -thickness, z0);
    indices.push(a, a + 1, a + 2, a, a + 2, a + 3);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  // The splay, baked in. rotateY(a) sends local +z to (sin a, cos a), so the figure's LEFT
  // foot turns its toe toward +x — the figure's own left — which is what "splayed outward"
  // means on that side.
  geometry.rotateY(THREE.MathUtils.degToRad(splayDeg));

  // Re-centre the plan on the origin AFTER the splay: the socket sits over the middle of
  // the slab's footprint. Which point of the sole the ankle actually stands over is not
  // measured from four orthographic views, so the bbox centre is an adopted convention,
  // recorded in the spec's assumptions rather than smuggled in here.
  geometry.computeBoundingBox();
  const bb = geometry.boundingBox!;
  geometry.translate(-(bb.min.x + bb.max.x) / 2, 0, -(bb.min.z + bb.max.z) / 2);

  // The right sole is the left one MIRRORED, not the left one rotated the other way: only
  // a mirror survives §5.10's "negate x and compare point by point", because it keeps the
  // vertex order the comparison walks. Mirroring flips face orientation, so the winding is
  // reversed to keep the normals pointing out.
  if (sideSign < 0) {
    geometry.scale(-1, 1, 1);
    const index = geometry.getIndex()!;
    for (let i = 0; i < index.count; i += 3) {
      const a = index.getX(i);
      index.setX(i, index.getX(i + 2));
      index.setX(i + 2, a);
    }
    index.needsUpdate = true;
  }
  geometry.computeVertexNormals();

  const group = new THREE.Group();
  group.name = `sole${side}`;
  group.add(new THREE.Mesh(geometry, MANNEQUIN));
  // Emits nothing: the sole is the bottom of the chain and its own origin is the only
  // mating point it has (§4's socket ledger).
  group.userData.sockets = {};
  return group;
}
