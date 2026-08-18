import * as THREE from "three";

/** One horizontal cross-section: a closed XZ polygon at a given height. */
export type Ring = { y: number; pts: readonly (readonly [number, number])[] };

/**
 * A chamfered rectangle in XZ — the cross-section every part on this head uses.
 *
 * `chamfer` is the fraction of the half-extent cut off each corner. 0 gives a box, 1 gives a
 * diamond, and the reference's own silhouette (a flat top edge with cut shoulders, a flat side
 * with cut jaw) sits around 0.35. It is the one knob that decides how faceted the head reads,
 * which is why it is a parameter rather than a hard-coded octagon.
 */
export function chamferedRing(
  halfW: number,
  halfD: number,
  chamfer: number,
): (readonly [number, number])[] {
  const cw = halfW * chamfer;
  const cd = halfD * chamfer;
  return [
    [halfW - cw, halfD],
    [halfW, halfD - cd],
    [halfW, -(halfD - cd)],
    [halfW - cw, -halfD],
    [-(halfW - cw), -halfD],
    [-halfW, -(halfD - cd)],
    [-halfW, halfD - cd],
    [-(halfW - cw), halfD],
  ];
}

/**
 * Loft a stack of rings into a faceted shell.
 *
 * Deliberately NON-INDEXED. `computeVertexNormals()` on an indexed mesh averages the normals of
 * every face meeting a vertex, which is exactly the smoothing that turned the previous exhibit's
 * head into a round egg while every dimension gate stayed green. Duplicating the corner vertices
 * per face is what makes each quad keep its own normal, so the facets survive shading.
 *
 * Every ring must have the same point count; the caller builds them from `chamferedRing`.
 */
export function loft(rings: readonly Ring[], opts: { capTop?: boolean; capBottom?: boolean } = {}) {
  const first = rings[0];
  if (!first || rings.length < 2) throw new Error(`loft needs >= 2 rings, got ${rings.length}`);
  const n = first.pts.length;
  for (const r of rings) {
    if (r.pts.length !== n) {
      throw new Error(`loft rings must share a point count: expected ${n}, got ${r.pts.length}`);
    }
  }

  const pos: number[] = [];
  const tri = (a: THREE.Vector3, b: THREE.Vector3, c: THREE.Vector3) => {
    pos.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z);
  };
  const at = (ri: number, pi: number) => {
    const ring = rings[ri];
    const p = ring?.pts[pi];
    if (!ring || !p) throw new Error(`loft ring ${ri} point ${pi} is missing`);
    return new THREE.Vector3(p[0], ring.y, p[1]);
  };

  for (let ri = 0; ri < rings.length - 1; ri += 1) {
    for (let pi = 0; pi < n; pi += 1) {
      const pj = (pi + 1) % n;
      const a = at(ri, pi);
      const b = at(ri, pj);
      const c = at(ri + 1, pj);
      const d = at(ri + 1, pi);
      tri(a, b, c);
      tri(a, c, d);
    }
  }

  const cap = (ri: number, up: boolean) => {
    const centre = new THREE.Vector3(0, rings[ri]?.y ?? 0, 0);
    for (let pi = 0; pi < n; pi += 1) {
      const a = at(ri, pi);
      const b = at(ri, (pi + 1) % n);
      if (up) tri(centre, b, a);
      else tri(centre, a, b);
    }
  };
  if (opts.capTop) cap(rings.length - 1, true);
  if (opts.capBottom) cap(0, false);

  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.computeVertexNormals();
  return g;
}
