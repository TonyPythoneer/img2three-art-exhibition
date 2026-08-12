/**
 * Mechanical gates for the two things a render cannot show you about the v2 hilt.
 *
 * 1. **Every part is a closed solid.** Backface culling hides an inside-out or a MISSING end cap:
 *    the part just looks a bit odd from one angle and perfectly fine from the next. This is
 *    measured instead — every undirected edge used exactly twice, once in each direction, and a
 *    positive divergence-theorem volume so the surface is outward-facing and not inverted. The
 *    regression that produced this file lofted end caps by flattening each ring to (x, z), which
 *    is a degenerate segment for every ring `radialSectionX` makes: the four drivers and the two
 *    connectors shipped as open tubes (`driverRightUpper` 32 triangles / 16 boundary edges,
 *    against 44 / 0 once capped), and the grip, the pommel and both spinners shipped with their
 *    caps facing inward.
 *
 * 2. **The pommel's base ring is the grip's bottom ring.** Not "the same number" — the same ring,
 *    compared vertex for vertex. A second hardcoded radius, or a different facet count, fails
 *    here rather than at the next review.
 *
 * Run:  node --test tests/ultima-v2-solid.test.mjs
 */
import test from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";

import { createUltimaWeaponV2Model } from "../src/utils/ultimaWeaponV2/createUltimaWeaponV2Model.ts";

const QUANTUM = 1e4; // positions are ~1e-2, so 1e-4 of a unit is far below any real gap
const key = (x, y, z) =>
  `${Math.round(x * QUANTUM)},${Math.round(y * QUANTUM)},${Math.round(z * QUANTUM)}`;

/** Boundary edges, doubled directed edges, triangle count and signed volume of one geometry. */
export function survey(geometry) {
  const pos = geometry.getAttribute("position");
  const triangles = pos.count / 3;
  const directed = new Map();
  let volume = 0;
  for (let t = 0; t < triangles; t += 1) {
    const k = [];
    const v = [];
    for (let c = 0; c < 3; c += 1) {
      const i = t * 3 + c;
      const p = new THREE.Vector3(pos.getX(i), pos.getY(i), pos.getZ(i));
      v.push(p);
      k.push(key(p.x, p.y, p.z));
    }
    volume += v[0].dot(new THREE.Vector3().crossVectors(v[1], v[2])) / 6;
    for (let c = 0; c < 3; c += 1)
      directed.set(
        `${k[c]}|${k[(c + 1) % 3]}`,
        (directed.get(`${k[c]}|${k[(c + 1) % 3]}`) ?? 0) + 1,
      );
  }
  let boundary = 0;
  for (const [edge, count] of directed) {
    const [a, b] = edge.split("|");
    if ((directed.get(`${b}|${a}`) ?? 0) === 0) boundary += count;
  }
  return { triangles, boundary, volume };
}

/** Every mesh in the tree, by part id. */
function meshes(model) {
  const out = new Map();
  model.traverse((o) => {
    if (o.isMesh) out.set(o.name, o);
  });
  return out;
}

/** The ring of a geometry at one end of its own Y span, as sorted "x,z" keys. */
function ringAt(geometry, wantMaxY) {
  const pos = geometry.getAttribute("position");
  let edge = wantMaxY ? -Infinity : Infinity;
  for (let i = 0; i < pos.count; i += 1) {
    const y = pos.getY(i);
    if (wantMaxY ? y > edge : y < edge) edge = y;
  }
  const seen = new Set();
  for (let i = 0; i < pos.count; i += 1) {
    if (Math.abs(pos.getY(i) - edge) > 1e-9) continue;
    seen.add(`${Math.round(pos.getX(i) * QUANTUM)},${Math.round(pos.getZ(i) * QUANTUM)}`);
  }
  return { y: edge, ring: [...seen].sort() };
}

for (const detail of ["blockout", "structural", "full"]) {
  test(`ultima v2 (${detail}): every part is a closed, outward-facing solid`, () => {
    const parts = meshes(createUltimaWeaponV2Model({ detail }));
    assert.ok(parts.size > 0, "the model must build at least one mesh");
    for (const [id, part] of parts) {
      const { triangles, boundary, volume } = survey(part.geometry);
      assert.equal(
        boundary,
        0,
        `${id}: ${boundary} boundary edges — an end cap is missing or inverted`,
      );
      assert.ok(triangles > 0, `${id}: no triangles`);
      assert.ok(volume > 0, `${id}: signed volume ${volume} — the surface is inside-out`);
    }
  });
}

test("ultima v2: the four drivers are one geometry, four positive-length transforms", () => {
  const parts = meshes(createUltimaWeaponV2Model({ detail: "full" }));
  const ids = ["driverLeftUpper", "driverLeftLower", "driverRightUpper", "driverRightLower"];
  const rods = ids.map((id) => {
    const rod = parts.get(id);
    assert.ok(rod, `${id} must exist`);
    return rod;
  });
  // One shared geometry: a per-rod difference in solidity is impossible by construction, so a
  // report that only ONE rod is hollow is always a report about the shared loft or a transform.
  for (const rod of rods)
    assert.equal(rod.geometry, rods[0].geometry, `${rod.name} must share the unit rod`);
  // 8 sides x 2 bands x 2 triangles + 2 caps x (8 - 2) = 44. Both caps present, neither fanned.
  assert.equal(survey(rods[0].geometry).triangles, 44, "the unit rod must carry both end caps");
  for (const rod of rods) {
    assert.ok(
      rod.scale.x > 0,
      `${rod.name}: scale.x ${rod.scale.x} — a negative length turns the rod inside out`,
    );
    assert.equal(rod.scale.y, 1);
    assert.equal(rod.scale.z, 1);
    const det = new THREE.Matrix4().compose(rod.position, rod.quaternion, rod.scale).determinant();
    assert.ok(det > 0, `${rod.name}: transform determinant ${det} mirrors the rod`);
  }
});

test("ultima v2: the pommel's base ring IS the grip's bottom ring", () => {
  const parts = meshes(createUltimaWeaponV2Model({ detail: "full" }));
  const grip = ringAt(parts.get("leatherGrip").geometry, false);
  const pommel = ringAt(parts.get("pointedMetalPommel").geometry, true);
  assert.ok(
    Math.abs(grip.y - pommel.y) < 1e-9,
    `junction planes differ: grip ${grip.y}, pommel ${pommel.y}`,
  );
  assert.deepEqual(
    pommel.ring,
    grip.ring,
    "the pommel's base ring must be the grip's own bottom ring — same facet count, same radius, " +
      "derived from GRIP_HALF_WIDTH rather than written as a second number",
  );
});
