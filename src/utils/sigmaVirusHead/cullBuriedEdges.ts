import * as THREE from "three";

import { FRAME_H, HALF_DEPTH, halfWidthAt, len } from "./measurements";

/**
 * Drop the edge segments that are buried inside the skull.
 *
 * This is the upgrade path `gate_edge_density.py` named. The reference is a see-through
 * wireframe of ONE shell, so it does draw hidden lines — but they are one shell's hidden lines.
 * This build is the 13-part assembly the project's assembly gate requires, and each part draws
 * its own complete closed box, including the faces pressed into its neighbours. Those edges have
 * no counterpart in the reference at all: they are an artefact of decomposing a shell into parts,
 * not something the sprite ever drew.
 *
 * The test is against the skull's own measured envelope rather than against the other parts'
 * meshes. The skull is the volume everything else is embedded in, its cross-section is already a
 * pure function of the frame row, and a point-in-envelope test costs two comparisons — where a
 * general mesh-vs-mesh containment test would need BVHs and a watertightness guarantee none of
 * these shells offer.
 *
 * `margin` shrinks the envelope so a part's own surface, which sits exactly ON the envelope, is
 * never mistaken for being inside it.
 */

/** The widest the skull proper gets — rows 14..27 run px 3..41, so half-width 19px. */
const SKULL_MAX_HALF = len(19);

/** Model y back to a frame row. Inverse of `measurements.y`. */
const rowAt = (yModel: number): number => FRAME_H - 1 - yModel * FRAME_H;

function insideSkull(v: THREE.Vector3, margin: number): boolean {
  const py = rowAt(v.y);
  // Outside the skull's own row band there is nothing to be buried in.
  if (py < 4 || py > 52) return false;
  const hw = Math.min(halfWidthAt(py), SKULL_MAX_HALF) * margin;
  const hd = HALF_DEPTH * (Math.min(halfWidthAt(py), SKULL_MAX_HALF) / halfWidthAt(37)) * margin;
  return Math.abs(v.x) < hw && Math.abs(v.z) < hd;
}

/**
 * Returns a new geometry with the buried segments removed. A segment goes only when BOTH ends
 * and its midpoint are inside — an edge that crosses the envelope is partly visible and stays,
 * because dropping it would open a gap in the silhouette.
 */
export function cullBuriedEdges(edges: THREE.BufferGeometry, margin = 0.97): THREE.BufferGeometry {
  const pos = edges.getAttribute("position");
  if (!pos) return edges;

  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const mid = new THREE.Vector3();
  const kept: number[] = [];
  for (let i = 0; i < pos.count; i += 2) {
    a.fromBufferAttribute(pos, i);
    b.fromBufferAttribute(pos, i + 1);
    mid.addVectors(a, b).multiplyScalar(0.5);
    if (insideSkull(a, margin) && insideSkull(b, margin) && insideSkull(mid, margin)) continue;
    kept.push(a.x, a.y, a.z, b.x, b.y, b.z);
  }

  const out = new THREE.BufferGeometry();
  out.setAttribute("position", new THREE.Float32BufferAttribute(kept, 3));
  return out;
}
