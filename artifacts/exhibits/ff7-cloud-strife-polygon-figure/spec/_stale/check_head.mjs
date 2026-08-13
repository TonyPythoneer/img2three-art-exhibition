/**
 * Mechanical gate for Part 1 (head). Asserts the things a render cannot show you and
 * the things a render would show you but nobody would notice. Run from the repo root:
 *
 *     node artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/check_head.mjs
 *
 * Every expected number traces to prompt.txt §1/§3 or spec/head-measurements.json —
 * none is copied from a summary.
 */
import assert from "node:assert/strict";
import * as THREE from "three";

// The face print is a CanvasTexture; node has no DOM. A 1x1 stub is enough: this gate
// is about geometry, and the texture's content is checked by eye in the review sheet.
globalThis.document = {
  createElement: () => ({
    width: 0,
    height: 0,
    getContext: () => new Proxy({}, { get: () => () => {} }),
  }),
};

const { createHead, HEAD_SOCKET_Y, HEAD_GUESSES } = await import(
  "../../../../src/utils/cloudStrifeFigure/parts/createHead.ts"
);

const head = createHead();
const near = (actual, expected, tol, what) =>
  assert.ok(
    Math.abs(actual - expected) <= tol,
    `${what}: got ${actual.toFixed(4)}, expected ${expected} ±${tol}`,
  );

// --- the part is a part, not a scene ---------------------------------------
assert.equal(head.name, "head");
assert.deepEqual(
  head.userData.sockets.neck.toArray(),
  [0, 0, 0],
  "socket origin must be the part origin so Stage 2 is pure placement",
);
assert.ok(HEAD_GUESSES.length >= 5, "the guess list ships with the model");

const meshes = [];
head.traverse((o) => {
  if (o.isMesh) meshes.push(o);
});

// --- flat faceting is the identity; a smoothed mesh is a fail --------------
for (const m of meshes) {
  assert.ok(m.material.flatShading, `${m.name} lost flatShading`);
  assert.equal(m.material.metalness, 0, `${m.name} metalness must be 0`);
  near(m.material.roughness, 0.85, 0.05, `${m.name} roughness`);
}

// --- named parts, each individually clickable ------------------------------
const names = meshes.map((m) => m.name);
for (const id of ["head", "neck", "choker", "hair-cap", "face-print", "ear-l", "ear-r"]) {
  assert.ok(names.includes(id), `missing part ${id}`);
}
const spikes = head.getObjectByName("hair-spikes").children;
const fringe = head.getObjectByName("hair-fringe").children;
assert.ok(spikes.length >= 9 && spikes.length <= 11, `spikes: ${spikes.length}, want 9-11`);
assert.ok(fringe.length >= 1 && fringe.length <= 2, `fringe: ${fringe.length}, want 1-2`);
assert.equal(new Set(names).size, names.length, "part names must be unique to be clickable");
assert.ok(!names.some((n) => /eye|iris|pupil/.test(n)), "the eyes are printed, not modelled");

// --- measured silhouette ---------------------------------------------------
const box = new THREE.Box3().setFromObject(head);
const size = box.getSize(new THREE.Vector3());

// prompt.txt §1: the tallest spike tip defines total height 1.000.
near(box.max.y + HEAD_SOCKET_Y, 1.0, 0.006, "tallest spike tip (figure Y)");
// head-measurements.json: hair span incl. lateral spikes is 0.295 (front) / 0.319 (back).
assert.ok(
  size.x >= 0.285 && size.x <= 0.330,
  `hair span width incl. lateral spikes: ${size.x.toFixed(3)}, want 0.285-0.330`,
);
// head-measurements.json left/right: max head depth 0.225.
near(size.z, 0.225, 0.030, "head depth front-to-back");
// The part hangs above its socket; nothing may dip below the shoulder line.
near(box.min.y, 0, 0.002, "part must start at the socket, not below it");

// Guess-list item 5: the cap shell is as deep as it is wide, not flattened front-to-back.
// Compared against the cap alone -- the lateral spikes make the full span meaningless here.
const capBox = new THREE.Box3().setFromObject(head.getObjectByName("hair-cap"));
const capSize = capBox.getSize(new THREE.Vector3());
near(capSize.x, 0.216, 0.012, "hair cap width excluding spikes");
// left.webp puts the occiput at z = -0.120; that is the cap shell, not a spike.
near(capBox.min.z, -0.118, 0.012, "cap rear (occiput)");
// The claim being gated is head depth 0.225 versus cap width 0.216 -- the head is
// round in plan. Comparing cap depth alone would exclude the fringe, which is part
// of what fills the profile.
assert.ok(
  size.z > capSize.x * 0.92,
  `head depth ${size.z.toFixed(3)} vs cap width ${capSize.x.toFixed(3)} — read as flattened`,
);

// The dominant spike leans to the figure's right (-X) and forward (+Z).
const tallest = spikes.reduce((best, s) => {
  const b = new THREE.Box3().setFromObject(s);
  return !best || b.max.y > best.y ? { y: b.max.y, node: s, box: b } : best;
}, null);
assert.equal(tallest.node.name, "spike-crown-r", "the tallest spike is the crown-right one");
assert.ok(tallest.box.min.x < -0.09, "dominant spike must lean to the figure's right");

// Face print sits in front of the head surface, at the measured eye line.
const print = head.getObjectByName("face-print");
near(print.position.y + HEAD_SOCKET_Y, 0.752, 0.006, "face print centre (measured eye line)");
assert.ok(print.position.z > 0.05, "face print must sit proud of the face plane");

// Indexed geometry (the face card is a PlaneGeometry) counts triangles from the index,
// not from the vertex count -- otherwise the total comes out fractional.
const triangles = meshes.reduce((n, m) => {
  const g = m.geometry;
  return n + (g.index ? g.index.count : g.getAttribute("position").count) / 3;
}, 0);
console.log(
  `PASS  ${meshes.length} meshes, ${triangles} tris, ` +
    `bbox ${size.x.toFixed(3)} x ${size.y.toFixed(3)} x ${size.z.toFixed(3)}, ` +
    `${spikes.length} spikes + ${fringe.length} fringe`,
);
