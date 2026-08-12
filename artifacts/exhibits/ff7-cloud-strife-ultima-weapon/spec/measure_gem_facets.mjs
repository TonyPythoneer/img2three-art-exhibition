/**
 * Where the stone's apex sits in its own box, and how close its four crown flanks are to being
 * four PLANES. Both read off the built mesh, because both are claims about a shape the user
 * directed and neither is something a render can settle.
 *
 * **The apex line is the one to read first.** `0.500 across, 0.500 up` is a point over the
 * rhombus's centre, which is what the directive of 2026-08-09 asked for and what the side render
 * shows worst: the stone is 84 units tall against 15.6 of depth, so its side silhouette is a
 * sliver and the eye reads the girdle before it reads the peak.
 *
 * The flanks are exactly planar because the stone is SET rather than seated — its girdle line and
 * its base are both single planes, so every flank is bounded by three straight edges. That was not
 * true of the seated stone this replaces: its rim followed `bladeStackTop`, a ratio of linears in
 * `y`, which bowed each flank off its own chord by 0.11–0.19 units.
 *
 * Two numbers per flank, both in the model's own normalized-1000 units:
 *
 *   bow    the largest distance from any of the flank's vertices to the least-squares plane
 *          through all of them — how far the built surface departs from the ideal face;
 *   kink   the largest angle between any two of the flank's own triangle normals — what a
 *          flat-shaded render actually shows, since `applyFacetSteps` colours per triangle.
 *
 * A kink under about 5° cannot cross `applyFacetSteps`' quantiser except at a step boundary, so
 * that is the threshold below which "four faces" is a fair description of the render and not just
 * of the intent. Recorded, not gated: the shape is directed and the number is the caveat on it.
 *
 * Run:  node src/exhibits/ff7-cloud-strife-ultima-weapon/spec/measure_gem_facets.mjs
 */
import * as THREE from "three";

import { createUltimaWeaponV2Model } from "../createUltimaWeaponV2Model.ts";

const U = 0.01; // the factory's own scale: normalized-1000 units × U are world units
const WAIST_Y = 55 * U;

/** Every triangle of one mesh as {centroid, normal, verts}. */
function triangles(mesh) {
  const pos = mesh.geometry.getAttribute("position");
  const out = [];
  for (let t = 0; t < pos.count / 3; t += 1) {
    const v = [0, 1, 2].map((c) => new THREE.Vector3().fromBufferAttribute(pos, t * 3 + c));
    const normal = new THREE.Vector3().crossVectors(v[1].clone().sub(v[0]), v[2].clone().sub(v[0]));
    if (normal.lengthSq() === 0) continue;
    out.push({
      verts: v,
      normal: normal.normalize(),
      centroid: v[0].clone().add(v[1]).add(v[2]).divideScalar(3),
    });
  }
  return out;
}

/** Least-squares plane through a point cloud, by the smallest eigenvector of its covariance. */
function bestPlane(points) {
  const c = points.reduce((a, p) => a.add(p), new THREE.Vector3()).divideScalar(points.length);
  // Power-iterate on (trace·I − C), whose dominant eigenvector is C's smallest — three axes are
  // enough to be robust here because the flanks are nowhere near degenerate.
  const m = [0, 0, 0, 0, 0, 0]; // xx xy xz yy yz zz
  for (const p of points) {
    const d = p.clone().sub(c);
    m[0] += d.x * d.x;
    m[1] += d.x * d.y;
    m[2] += d.x * d.z;
    m[3] += d.y * d.y;
    m[4] += d.y * d.z;
    m[5] += d.z * d.z;
  }
  const trace = m[0] + m[3] + m[5];
  const apply = (v) =>
    new THREE.Vector3(
      trace * v.x - (m[0] * v.x + m[1] * v.y + m[2] * v.z),
      trace * v.y - (m[1] * v.x + m[3] * v.y + m[4] * v.z),
      trace * v.z - (m[2] * v.x + m[4] * v.y + m[5] * v.z),
    );
  let best = null;
  for (const seed of [
    new THREE.Vector3(1, 0, 0),
    new THREE.Vector3(0, 1, 0),
    new THREE.Vector3(0, 0, 1),
  ]) {
    let v = seed.clone();
    for (let i = 0; i < 200; i += 1) {
      const next = apply(v);
      if (next.lengthSq() === 0) break;
      v = next.normalize();
    }
    const spread = Math.max(...points.map((p) => Math.abs(p.clone().sub(c).dot(v))));
    if (!best || spread < best.spread) best = { normal: v, spread };
  }
  return { centre: c, normal: best.normal };
}

const root = createUltimaWeaponV2Model({ detail: "full" });
let failures = 0;

for (const face of ["Front", "Rear"]) {
  const mesh = root.getObjectByName(`rootDiamondGem${face}`);
  if (!mesh) throw new Error(`no rootDiamondGem${face} in the model`);
  const sign = face === "Front" ? 1 : -1;
  const all = triangles(mesh);

  // The base looks toward the mid-plane; the socket wall is vertical; everything else is a crown
  // flank, split by which side of the axis and of the waist it sits on.
  const flanks = new Map();
  let base = 0;
  let wall = 0;
  for (const tri of all) {
    if (tri.normal.z * sign < 0) {
      base += 1;
      continue;
    }
    // The socket WALL is vertical, so its normal lies in the XY plane. It is part of the stone and
    // most of it is inside the crystal; what it is not is a crown facet, and averaging the two
    // into one plane fit reports a 68 degree kink that neither of them has.
    if (Math.abs(tri.normal.z) < 0.3) {
      wall += 1;
      continue;
    }
    const name = `${tri.centroid.x < 0 ? "left" : "right"}-${tri.centroid.y < WAIST_Y ? "lower" : "upper"}`;
    if (!flanks.has(name)) flanks.set(name, []);
    flanks.get(name).push(tri);
  }

  // Where the apex actually is, as a fraction of the stone's own front-view box. This is the
  // claim the side render is being asked to show and the one it shows worst — the stone is 84
  // units tall against 9.8 of depth per half, so its side silhouette is a sliver and the eye
  // reads the ledge before it reads the peak. 0.500 / 0.500 is a point over the rhombus's centre.
  const verts = all.flatMap((t) => t.verts);
  const box = new THREE.Box3().setFromPoints(verts);
  const peak = verts.reduce((a, v) => (Math.abs(v.z) > Math.abs(a.z) ? v : a));
  const frac = (v, lo, hi) => (hi === lo ? 0 : (v - lo) / (hi - lo));
  console.log(
    `${`rootDiamondGem${face}`}  ${all.length} triangles: ${base} base, ${wall} socket wall, ${all.length - base - wall} crown, ${flanks.size} flanks\n` +
      `    apex at (${(peak.x / U).toFixed(1)}, ${(peak.y / U).toFixed(1)}) = ` +
      `${frac(peak.x, box.min.x, box.max.x).toFixed(3)} across, ` +
      `${frac(peak.y, box.min.y, box.max.y).toFixed(3)} up its own box`,
  );
  for (const name of [...flanks.keys()].sort()) {
    const tris = flanks.get(name);
    const plane = bestPlane(tris.flatMap((t) => t.verts));
    let bow = 0;
    let worst = null;
    for (const v of tris.flatMap((t) => t.verts)) {
      const d = Math.abs(v.clone().sub(plane.centre).dot(plane.normal)) / U;
      if (d > bow) {
        bow = d;
        worst = v;
      }
    }
    const at = `(${(worst.x / U).toFixed(1)}, ${(worst.y / U).toFixed(1)}, ${(worst.z / U).toFixed(2)})`;
    let kink = 0;
    for (const a of tris) {
      for (const b of tris) {
        kink = Math.max(kink, a.normal.angleTo(b.normal) * (180 / Math.PI));
      }
    }
    const verdict = kink <= 5 ? "flat" : "NOT FLAT";
    if (kink > 5) failures += 1;
    console.log(
      `    ${name.padEnd(12)} ${String(tris.length).padStart(3)} tris   bow ${bow.toFixed(4)} u at ${at}   kink ${kink.toFixed(2)}°   ${verdict}`,
    );
  }
  if (flanks.size !== 4) {
    failures += 1;
    console.log(`    NOT FOUR FLANKS — ${flanks.size}`);
  }
}

console.log(
  failures === 0
    ? "\nfour flanks per half, each flat to the render"
    : `\n${failures} flank(s) are not flat`,
);
