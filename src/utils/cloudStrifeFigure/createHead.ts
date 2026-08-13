import * as THREE from "three";
import { MANNEQUIN } from "./parts";
import { HEAD, SOCKET_Y } from "./measurements";
import { loft, ngon } from "./armSegment";

/**
 * S-15 skull — prompt §4[14]. Faceted skull and face. NO hair, NO ears, NO eyes: the hair
 * cap and its nine spikes, the two ears and the printed face are all Stage 2.
 *
 * WHERE THE SHAPE COMES FROM, AND WHY NOT FROM §4[14]'s RECIPE
 *
 * §4[14] says "Skull outline = back.webp's outer silhouette inset by one hair thickness".
 * That is unusable and the guess list already said so: `hairThickness` is a FRINGE DEPTH
 * measured forward from the face plane, 0.03863 on the left against 0.07137 on the right —
 * a 1.85x disagreement between two views of one quantity. Insetting by it overshoots, and
 * the previous attempt at this part came out all-green and egg-shaped.
 *
 * So the skull is measured where it is VISIBLE: the face is bare skin, and the skin band
 * gives its width at every row directly. Cheekbones 0.13972 at height 0.76209, chin 0.03556
 * at 0.71637 — §4[14]'s "widest at the cheekbones, tapering to a small pointed chin" comes
 * out as a ratio of 0.356 rather than an adjective.
 *
 * Two things stay guesses, both flagged in parts.head:
 *   - the cranium BEHIND the face plane, which no view sees under the hair cap;
 *   - the crown's height. The ledger's `skullTop` is 1.0, which is the EXTRAPOLATED HAIR
 *     TIP, not bone. The bare crown is somewhere below it. Stage 2's §7.6 — skull plus
 *     hairCap must reproduce back.webp's outer silhouette — is what falsifies both.
 *
 * origin: skullTop / emits: neckTop (mates with the neck's own origin)
 */
export function createHead(): THREE.Group {
  const height = SOCKET_Y.skullTop - SOCKET_Y.neckTop;
  const { cheekboneWidth, cheekboneHeight, chinWidth, exposedDepth } = HEAD;
  const cheekDrop = SOCKET_Y.skullTop - cheekboneHeight;

  // Cranium depth: the face's own depth again behind it (parts.head.craniumBehindFace).
  const depth = exposedDepth * 2;

  const group = loft("head", "L", [
    ngon(6, cheekboneWidth * 0.55, depth * 0.55, 0, 0),
    ngon(6, cheekboneWidth, depth, -cheekDrop, 0),
    ngon(6, chinWidth, depth * 0.6, -height, 0),
  ]);

  const mesh = group.children[0] as THREE.Mesh;
  const geometry = mesh.geometry as THREE.BufferGeometry;
  const index = geometry.getIndex()!;
  const pos = geometry.getAttribute("position");

  // §4[14]'s faceGroups: five regions, every triangle in EXACTLY ONE array, asserted here
  // rather than left to the Stage 2 consumer to discover. Assignment is by the triangle's
  // own centroid, so it is a function of the geometry and not a hand-kept list that drifts
  // the moment a ring changes.
  const groups: Record<string, number[]> = { scalp: [], face: [], jaw: [], nape: [], ear: [] };
  const c = new THREE.Vector3();
  for (let t = 0; t < index.count / 3; t += 1) {
    c.set(0, 0, 0);
    for (let k = 0; k < 3; k += 1) {
      const i = index.getX(t * 3 + k);
      c.x += pos.getX(i) / 3;
      c.y += pos.getY(i) / 3;
      c.z += pos.getZ(i) / 3;
    }
    // The bands are relative to the CHEEKBONE RING, not to the whole head. Cutting at
    // -cheekDrop put 84% of the skull in scalp/nape and left `face` and `ear` EMPTY: the
    // cheekbones sit at 0.76209 against a chin at 0.71637 and a skullTop of 1.0, so the
    // exposed face is only the bottom sixth of the part and everything above it is
    // cranium. An empty `face` array is a partition that satisfies the arithmetic and
    // gives Stage 2's faceDecal nothing to map onto.
    const front = c.z > 0;
    const side = Math.abs(c.x) > cheekboneWidth * 0.28;
    if (c.y > -cheekDrop * 0.75) groups[front ? "scalp" : "nape"]!.push(t);
    else if (c.y < -(cheekDrop + (height - cheekDrop) * 0.55)) groups.jaw!.push(t);
    else if (front && !side) groups.face!.push(t);
    else if (side) groups.ear!.push(t);
    else groups.nape!.push(t);
  }
  const total = Object.values(groups).reduce((n, g) => n + g.length, 0);
  const seen = new Set(Object.values(groups).flat());
  if (total !== index.count / 3 || seen.size !== total) {
    throw new Error(
      `faceGroups must partition the head: ${total} assigned, ${seen.size} distinct, ` +
        `${index.count / 3} triangles`,
    );
  }
  group.userData.faceGroups = groups;
  group.userData.sockets = { neckTop: new THREE.Vector3(0, -height, 0) };
  void MANNEQUIN;
  return group;
}
