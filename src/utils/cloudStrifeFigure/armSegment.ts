import * as THREE from "three";
import { MANNEQUIN } from "./parts";
import { ARM } from "./measurements";

/** A ring of `n` points, an inscribed polygon of a w x d rectangle at height y. */
export function ngon(
  n: number,
  w: number,
  d: number,
  y: number,
  lean: number,
): Array<[number, number, number]> {
  const out: Array<[number, number, number]> = [];
  for (let i = 0; i < n; i += 1) {
    const a = (i / n) * Math.PI * 2 + Math.PI / n;
    out.push([Math.cos(a) * (w / 2), y, Math.sin(a) * (d / 2) + lean]);
  }
  return out;
}

/**
 * Loft a stack of rings into one flat-shaded prism.
 *
 * Shared by all four arm factories because §4[9] and §4[10] make two of the sections
 * IDENTICAL across parts — upperDeltoid's bottom hexagon IS lowerDeltoid's top, and
 * lowerDeltoid's bottom quad IS backArm's section. Sharing the builder is what makes them
 * literally the same numbers rather than two copies that agree today.
 *
 * §2's sharing rule is satisfied: three shape codes use this, and no option was added to
 * make that happen.
 */
export function loft(
  name: string,
  side: "L" | "R",
  rings: Array<Array<[number, number, number]>>,
): THREE.Group {
  const positions: number[] = [];
  const indices: number[] = [];
  const push = (p: [number, number, number]): number => {
    const i = positions.length / 3;
    positions.push(p[0], p[1], p[2]);
    return i;
  };
  const base = rings.map((r) => r.map(push));

  for (let k = 0; k < rings.length - 1; k += 1) {
    const a = base[k]!;
    const b = base[k + 1]!;
    // Rings may differ in vertex count (§4[9]: hexagon -> quadrilateral). Walk the LONGER
    // ring and fan onto the shorter one's nearest index, which is what makes a 6->4 loft a
    // legal closed surface instead of a strip with two holes in it.
    const [lo, hi] = a.length >= b.length ? [b, a] : [a, b];
    const flip = a.length >= b.length;
    for (let i = 0; i < hi.length; i += 1) {
      const j0 = Math.floor((i * lo.length) / hi.length);
      const j1 = Math.floor(((i + 1) * lo.length) / hi.length) % lo.length;
      const p = hi[i]!;
      const q = hi[(i + 1) % hi.length]!;
      if (j0 === j1) {
        indices.push(...(flip ? [p, lo[j0]!, q] : [p, q, lo[j0]!]));
      } else {
        indices.push(...(flip ? [p, lo[j0]!, q] : [p, q, lo[j0]!]));
        indices.push(...(flip ? [q, lo[j0]!, lo[j1]!] : [q, lo[j1]!, lo[j0]!]));
      }
    }
  }
  const t = base[0]!;
  const bt = base[base.length - 1]!;
  for (let i = 1; i < t.length - 1; i += 1) indices.push(t[0]!, t[i]!, t[i + 1]!);
  for (let i = 1; i < bt.length - 1; i += 1) indices.push(bt[0]!, bt[i + 1]!, bt[i]!);

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  if (side === "R") {
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
  group.name = name;
  group.add(new THREE.Mesh(geometry, MANNEQUIN));
  return group;
}

/**
 * How far a segment's bottom ring is displaced from its top, from the BAKED pose (§1.4).
 *
 * The adopted angles are the mean of the two sides. §1.5 calls these pure mirror pairs and
 * the measured 8.8 degree forward-lean gap is smaller than the 29.23 px residual of the
 * fit that produced it, so the asymmetry is not established — see
 * parts.arm.mirror_1_4_vs_1_5. Taking the mean means neither side's error is carried whole.
 */
export function poseOffset(height: number, extraBreakDeg = 0): { x: number; z: number } {
  const abd = THREE.MathUtils.degToRad(ARM.abductionDeg);
  const lean = THREE.MathUtils.degToRad(ARM.forwardLeanDeg + extraBreakDeg);
  return { x: Math.tan(abd) * height, z: Math.tan(lean) * height };
}
