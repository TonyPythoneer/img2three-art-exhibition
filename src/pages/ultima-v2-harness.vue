<template>
  <div class="ultima-harness">
    <canvas id="ultima-harness-canvas" ref="canvasEl" />
    <p v-if="error" class="ultima-harness-error">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import * as THREE from "three";
import {
  createUltimaWeaponV2Model,
  type DetailLevel,
  type SculptRuntime,
} from "~/exhibits/cloud-ultima-weapon-v2/createUltimaWeaponV2Model";
import {
  REVIEW_VIEWS,
  createUltimaWeaponV2LookDevLights,
  createReviewCamera,
  reviewRecipe,
  applyMaterialOverrides,
  isLightingMode,
  LIGHTING_MODES,
  type LightingMode,
  type ReviewView,
} from "~/exhibits/cloud-ultima-weapon-v2/createUltimaWeaponV2LookDev";

/**
 * Headless review harness for the v2 rebuild, driven by tools/capture_ultima.mjs with
 * `--route ultima-v2-harness`. The fable and codex-sol rebuilds had their own copies of this
 * contract; both were retired with their exhibits. Deliberately absent from ssgOptions.includedRoutes:
 * Three.js must never run in node during static generation.
 */

type HarnessWindow = Window & {
  __renderReady?: boolean;
  __renderError?: string;
  __sculptRuntime?: unknown;
  __renderHarness?: Record<string, unknown>;
  __partManifest?: Record<string, unknown>;
};

const DEFAULT_WIDTH = 584;
const DEFAULT_HEIGHT = 1168;

const canvasEl = ref<HTMLCanvasElement | null>(null);
const error = ref("");

let disposeScene: (() => void) | null = null;
let restoreChrome: (() => void) | null = null;

const readParams = (search: string) => {
  const q = new URLSearchParams(search);
  const int = (key: string, fallback: number) => {
    const parsed = Number.parseInt(q.get(key) ?? "", 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
  };
  const detail = q.get("detail") ?? "full";
  const explode = Number.parseFloat(q.get("explode") ?? "");
  // Camera-solve overrides. The artwork's roll is measured but its yaw and pitch are
  // estimates, so the review loop sweeps them here rather than editing a constant per trial.
  const angle = (key: string) => {
    const parsed = Number.parseFloat(q.get(key) ?? "");
    return Number.isFinite(parsed) ? parsed : undefined;
  };
  return {
    yaw: angle("yaw"),
    pitch: angle("pitch"),
    roll: angle("roll"),
    view: (q.get("view") ?? "artwork-match") as ReviewView,
    mode: (q.get("mode") ?? "referenceLighting") as LightingMode,
    detail: (["blockout", "structural", "full"].includes(detail) ? detail : "full") as DetailLevel,
    explode: Number.isFinite(explode) ? Math.min(Math.max(explode, 0), 1) : null,
    transparent: q.get("bg") === "transparent",
    // Transparency review needs a patterned backdrop: against flat white, a shell at 0.70
    // opacity and one at 1.0 are indistinguishable.
    checker: q.get("bg") === "checker",
    wireframe: q.get("wireframe") === "1",
    flat: q.get("flat") === "1",
    hide: (q.get("hide") ?? "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean),
    width: int("w", DEFAULT_WIDTH),
    height: int("h", DEFAULT_HEIGHT),
  };
};

/**
 * How far each part reaches INSIDE the surfaces it is supposed to be lying on.
 *
 * Two questions, both pointwise, and neither answerable from a bounding box — every blade
 * layer's box overlaps the shell's by construction, precisely because the layers sit on it:
 *
 *   `shell`  how far past `outerCrystalShell`'s own lofted surface the part reaches. The shell is
 *            a solid body and nothing may be inside it.
 *   `stack`  the same question against everything UNDER this layer in the relief ladder — the
 *            shell, then the insert skin, then the dark-core skin. This is what says the diamond
 *            GROWS OUT OF the dark core rather than merely clearing the crystal.
 *
 * The method is one ray per sample per host: shoot down the +Z axis onto the host, take its first
 * hit as that host's surface depth at this (x, y), and report how far past the deepest of them
 * the sample sits. `Math.abs(sample.z)` is what makes one front-half host answer for a rear-half
 * sample — every pair is asserted to be an exact mirror, and `check_centerline.py` is what asserts
 * it, so the two facts hold each other up.
 *
 * Three defects lived exactly in the gap this closes, and none of them moved a single bounding
 * box: both skins carried a FLAT underside at their own rim depth, which runs under the host's
 * crest everywhere inboard of the rim; the diamond was built as a pair of halves running from
 * `Z = 0` outward, i.e. straight through the crystal; and `loft` closed each end with a fan
 * through the ring's centroid, which for a crescent-shaped ring is a point off the band.
 * `spec/check_centerline.py` reads what this writes.
 *
 * Sampled with a barycentric lattice rather than at vertices only: a flat cap laid across a
 * curved host has every vertex ON the host and its whole middle inside it, which vertex sampling
 * scores as clean.
 *
 * **The lattice order is calibrated, not chosen.** The band in which a flat underside is actually
 * inside its curved host is narrow — the shell's surface falls away from the centre line fast
 * enough that the dark core's old flat underside was buried only over `|x| < 4` of a 42-wide
 * film. At order 3 every sample on that quad landed outside the band and the layer scored a clean
 * 0.000 while it was 0.249 units inside; at order 6 the same geometry reads 0.249. So the
 * instrument was bracketed against a defect known to be there before it was trusted about one
 * that might not be.
 */
const LATTICE_ORDER = 6;
/**
 * World units. How far a HOST query is pulled from the sample toward its own face's centroid
 * before the ray is cast — and it exists because at a host's footprint EDGE the host is
 * two-valued, so a probe that rays at exactly the sample point reads a coin flip there.
 *
 * The stone is the case that forced it. Both films' lower edge is the authority line Y = 55, and
 * the stone's underside carries a matching LEDGE at that height: below it the stone lies on the
 * bare crystal, above it on two films 2.8 units up. The face immediately below the ledge has its
 * top edge at Y = 55 exactly, where the films' own base caps are — so ray straight down and the
 * films answer for a face that is entirely below them, scoring the stone 2.8 units inside a layer
 * it is flush against. Ray a hair inside that face instead and the shell answers, which is the
 * surface the face is actually lying on.
 *
 * 1e-5 world is 1e-3 normalized units — a thousandth of a render pixel, and ~170 float32 steps at
 * the 0.55 world coordinate where it matters, so it survives the vertex buffer. The host surfaces
 * slope by ~0.1, so moving the query by that much moves the answer by ~1e-4 normalized units,
 * which is `PENETRATION_EPSILON`. Capped at a quarter of the way to the centroid so a small
 * triangle cannot have its query pushed out the far side.
 */
const HOST_QUERY_INSET = 1e-5;
/**
 * What is UNDER each blade layer, innermost first. Anything not named here answers to the shell
 * alone. Only the front halves are listed: a rear sample is compared through `|z|`, which is
 * exactly the mirror assertion `check_centerline.py` already holds the pair to.
 */
const RELIEF_STACK: Record<string, string[]> = {
  purpleEnergyInsertFront: [],
  purpleEnergyInsertRear: [],
  darkCoreTriangleFront: ["purpleEnergyInsertFront"],
  darkCoreTriangleRear: ["purpleEnergyInsertFront"],
  rootDiamondGemFront: ["purpleEnergyInsertFront", "darkCoreTriangleFront"],
  rootDiamondGemRear: ["purpleEnergyInsertFront", "darkCoreTriangleFront"],
};
const measureShellPenetration = (runtime: SculptRuntime) => {
  const shell = runtime.nodes.get("outerCrystalShell") as THREE.Mesh | undefined;
  if (!shell?.isMesh) return null;

  // The ray arrives from outside the hosts AND from inside them, so back faces have to count.
  const restore: (() => void)[] = [];
  const doubleSided = (mesh: THREE.Mesh) => {
    const material = mesh.material as THREE.Material;
    const side = material.side;
    material.side = THREE.DoubleSide;
    restore.push(() => {
      material.side = side;
    });
  };
  doubleSided(shell);
  for (const host of new Set(Object.values(RELIEF_STACK).flat())) {
    const mesh = runtime.nodes.get(host) as THREE.Mesh | undefined;
    if (mesh?.isMesh) doubleSided(mesh);
  }

  const raycaster = new THREE.Raycaster();
  const down = new THREE.Vector3(0, 0, -1);
  const from = new THREE.Vector3();
  const sample = new THREE.Vector3();
  const centroid = new THREE.Vector3();
  const query = new THREE.Vector3();
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const c = new THREE.Vector3();

  /**
   * A host's own front-surface depth at (x, y); null where that host has no material there.
   *
   * The Y guard is not a nicety. This probe models a host as a Z-GRAPH — "the surface is at
   * z = f(x, y)" — and that model is wrong at the host's own extremes in Y, where the boundary is
   * the host's END CAP and not its front face. A sample lying exactly ON the shell's lowest plane
   * is on the shell's surface, at distance zero; without the guard the ray still finds the base
   * ring's own triangles and reports the full half-depth, so a part merely TOUCHING the crystal's
   * base cap is scored as buried in it by 11 units.
   *
   * That became reachable with integration #16: the grip column's flat top and the shell's base
   * cap are the same plane now, and this read the contact as `leatherGrip reaches 11.000 inside
   * the shell at (0, 13, 0)`. Nothing is loosened by the guard — at `y = minY` the host has zero
   * extent in Y, so there is no volume left to be inside — and a column pushed even a hundredth
   * of a pixel back up between the jaws is above the guard and scored exactly as before.
   */
  const spanY = new Map<THREE.Mesh, [number, number]>();
  const surfaceAt = (mesh: THREE.Mesh, x: number, y: number): number | null => {
    let span = spanY.get(mesh);
    if (!span) {
      const box = new THREE.Box3().setFromObject(mesh);
      span = [box.min.y, box.max.y];
      spanY.set(mesh, span);
    }
    if (y <= span[0] + PENETRATION_EPSILON || y >= span[1] - PENETRATION_EPSILON) return null;
    from.set(x, y, 10);
    raycaster.set(from, down);
    const hits = raycaster.intersectObject(mesh, false);
    return hits.length === 0 ? null : hits[0]!.point.z;
  };

  /** The sample, pulled a hair toward its own face's centroid — see `HOST_QUERY_INSET`. */
  const queryPoint = (at: THREE.Vector3, towards: THREE.Vector3): THREE.Vector3 => {
    query.subVectors(towards, at);
    const reach = query.length();
    if (reach > 0) query.multiplyScalar(Math.min(HOST_QUERY_INSET, reach * 0.25) / reach);
    return query.add(at);
  };

  const lattice: [number, number, number][] = [];
  for (let i = 0; i <= LATTICE_ORDER; i += 1) {
    for (let j = 0; j <= LATTICE_ORDER - i; j += 1) {
      lattice.push([i / LATTICE_ORDER, j / LATTICE_ORDER, (LATTICE_ORDER - i - j) / LATTICE_ORDER]);
    }
  }

  type Reading = {
    samples: number;
    inside: number;
    worst: number;
    worstAt: [number, number, number];
    insideMaxY: number | null;
  };
  const parts: Record<string, { shell: Reading; stack: Reading }> = {};
  const blank = (): Reading => ({
    samples: 0,
    inside: 0,
    worst: 0,
    worstAt: [0, 0, 0],
    insideMaxY: null,
  });
  const record = (into: Reading, depth: number, at: THREE.Vector3) => {
    into.samples += 1;
    if (depth > into.worst) {
      into.worst = depth;
      // Reported so a failure names a place on the blade instead of a scalar.
      into.worstAt = [at.x, at.y, at.z];
    }
    if (depth > PENETRATION_EPSILON) {
      into.inside += 1;
      // The HIGHEST point at which this part is inside its host. The two jaws and the grip's tang
      // are inside the crystal on purpose — they are the socket its base ring is handed to — and
      // this is what bounds that exception to the socket instead of letting it run up the blade.
      if (into.insideMaxY === null || at.y > into.insideMaxY) into.insideMaxY = at.y;
    }
  };

  for (const [name, node] of runtime.nodes) {
    // Leaf meshes only. An organisational group would re-count its own children, and
    // `bladeGroup` would additionally "penetrate" the shell with the shell.
    if (name === "outerCrystalShell" || !(node as THREE.Mesh).isMesh) continue;
    const under = (RELIEF_STACK[name] ?? [])
      .map((id) => runtime.nodes.get(id) as THREE.Mesh | undefined)
      .filter((mesh): mesh is THREE.Mesh => Boolean(mesh?.isMesh));
    const reading = { shell: blank(), stack: blank() };
    node.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (!mesh.isMesh) return;
      const position = mesh.geometry.getAttribute("position");
      const index = mesh.geometry.getIndex();
      const count = index ? index.count : position.count;
      for (let t = 0; t < count; t += 3) {
        const i0 = index ? index.getX(t) : t;
        const i1 = index ? index.getX(t + 1) : t + 1;
        const i2 = index ? index.getX(t + 2) : t + 2;
        a.fromBufferAttribute(position, i0).applyMatrix4(mesh.matrixWorld);
        b.fromBufferAttribute(position, i1).applyMatrix4(mesh.matrixWorld);
        c.fromBufferAttribute(position, i2).applyMatrix4(mesh.matrixWorld);
        centroid
          .copy(a)
          .add(b)
          .add(c)
          .multiplyScalar(1 / 3);
        for (const [u, v, w] of lattice) {
          sample.set(
            a.x * u + b.x * v + c.x * w,
            a.y * u + b.y * v + c.y * w,
            a.z * u + b.z * v + c.z * w,
          );
          const at = queryPoint(sample, centroid);
          const qx = at.x;
          const qy = at.y;
          const depth = Math.abs(sample.z);
          const crystal = surfaceAt(shell, qx, qy);
          if (crystal !== null) record(reading.shell, crystal - depth, sample);
          let host = crystal;
          for (const layer of under) {
            const face = surfaceAt(layer, qx, qy);
            if (face !== null && (host === null || face > host)) host = face;
          }
          if (host !== null) record(reading.stack, host - depth, sample);
        }
      }
    });
    if (reading.shell.samples > 0 || reading.stack.samples > 0) parts[name] = reading;
  }

  for (const undo of restore) undo();
  return { epsilon: PENETRATION_EPSILON, latticeOrder: LATTICE_ORDER, parts };
};
/**
 * World units. One normalized unit is 0.01 world and the orthographic review captures run about
 * one normalized unit per pixel, so this is a hundredth of a source pixel — small enough that
 * nothing can hide under it, large enough that the loft's own linearization does not trip it.
 */
const PENETRATION_EPSILON = 1e-4;

/**
 * "Flush" is a SIGNED question, and `measureShellPenetration` only ever asked half of it.
 *
 * That probe reports `max(host − |z|)` — how far a layer reaches INSIDE the surface under it — and
 * clamps at zero, so a layer hovering half a unit ABOVE its host scores a perfect 0.000. A film
 * that floats is not laid on anything; it is a second body with a slot of air under it, and the
 * requirement "每一層都完整貼齊 shell 表面" is the two-sided form of the question. This probe asks
 * it that way:
 *
 *   clearance = |sample.z| − hostSurfaceZ      positive = a GAP, negative = PENETRATION
 *
 * and it asks it **only of the faces that are supposed to be touching**. A layer's triangles fall
 * into three families by which way they look, and only one of them answers to the host:
 *
 *   `seat`   normal pointing at the mid-plane — the underside. Flush ⇔ clearance ≡ 0.
 *   `outer`  normal pointing away — the visible face. Flush ⇔ clearance ≡ the layer's own
 *            nominal thickness, which is what says the film has not been thinned or inflated
 *            somewhere in the middle of its footprint.
 *   `rim`    everything steeper than `SEAT_FACE_COSINE`, i.e. the side walls and the stone's
 *            bevels. They span the whole thickness by construction and answer to neither.
 *
 * Both readings are surface-sampled on the same barycentric lattice and the same downward ray as
 * the penetration probe, so the two numbers are the same instrument asked two different questions.
 * Without the split, a mean over all faces reads the layer's own thickness and says nothing.
 */
const SEAT_FACE_COSINE = 0.5;
type Clearance = {
  samples: number;
  min: number;
  max: number;
  mean: number;
  rms: number;
  minAt: [number, number, number];
  maxAt: [number, number, number];
};
const measureStackConformity = (runtime: SculptRuntime) => {
  const shell = runtime.nodes.get("outerCrystalShell") as THREE.Mesh | undefined;
  if (!shell?.isMesh) return null;

  const restore: (() => void)[] = [];
  const doubleSided = (mesh: THREE.Mesh) => {
    const material = mesh.material as THREE.Material;
    const side = material.side;
    material.side = THREE.DoubleSide;
    restore.push(() => {
      material.side = side;
    });
  };
  doubleSided(shell);
  for (const host of new Set(Object.values(RELIEF_STACK).flat())) {
    const mesh = runtime.nodes.get(host) as THREE.Mesh | undefined;
    if (mesh?.isMesh) doubleSided(mesh);
  }

  const raycaster = new THREE.Raycaster();
  const down = new THREE.Vector3(0, 0, -1);
  const from = new THREE.Vector3();
  const sample = new THREE.Vector3();
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const c = new THREE.Vector3();
  const ab = new THREE.Vector3();
  const ac = new THREE.Vector3();
  const normal = new THREE.Vector3();
  const centroid = new THREE.Vector3();
  const query = new THREE.Vector3();

  const surfaceAt = (mesh: THREE.Mesh, x: number, y: number): number | null => {
    from.set(x, y, 10);
    raycaster.set(from, down);
    const hits = raycaster.intersectObject(mesh, false);
    return hits.length === 0 ? null : hits[0]!.point.z;
  };

  const queryPoint = (at: THREE.Vector3, towards: THREE.Vector3): THREE.Vector3 => {
    query.subVectors(towards, at);
    const reach = query.length();
    if (reach > 0) query.multiplyScalar(Math.min(HOST_QUERY_INSET, reach * 0.25) / reach);
    return query.add(at);
  };

  const lattice: [number, number, number][] = [];
  for (let i = 0; i <= LATTICE_ORDER; i += 1) {
    for (let j = 0; j <= LATTICE_ORDER - i; j += 1) {
      lattice.push([i / LATTICE_ORDER, j / LATTICE_ORDER, (LATTICE_ORDER - i - j) / LATTICE_ORDER]);
    }
  }

  const blank = (): Clearance => ({
    samples: 0,
    min: Infinity,
    max: -Infinity,
    mean: 0,
    rms: 0,
    minAt: [0, 0, 0],
    maxAt: [0, 0, 0],
  });
  const record = (into: Clearance, value: number, at: THREE.Vector3) => {
    into.samples += 1;
    into.mean += value;
    into.rms += value * value;
    if (value < into.min) {
      into.min = value;
      into.minAt = [at.x, at.y, at.z];
    }
    if (value > into.max) {
      into.max = value;
      into.maxAt = [at.x, at.y, at.z];
    }
  };
  const close = (reading: Clearance): Clearance =>
    reading.samples === 0
      ? { ...reading, min: 0, max: 0 }
      : {
          ...reading,
          mean: reading.mean / reading.samples,
          rms: Math.sqrt(reading.rms / reading.samples),
        };

  const layers: Record<string, { seat: Clearance; outer: Clearance }> = {};
  for (const name of Object.keys(RELIEF_STACK)) {
    const mesh = runtime.nodes.get(name) as THREE.Mesh | undefined;
    if (!mesh?.isMesh) continue;
    const side = name.endsWith("Rear") ? -1 : 1;
    const under = (RELIEF_STACK[name] ?? [])
      .map((id) => runtime.nodes.get(id) as THREE.Mesh | undefined)
      .filter((host): host is THREE.Mesh => Boolean(host?.isMesh));
    const reading = { seat: blank(), outer: blank() };
    const position = mesh.geometry.getAttribute("position");
    const index = mesh.geometry.getIndex();
    const count = index ? index.count : position.count;
    for (let t = 0; t < count; t += 3) {
      const i0 = index ? index.getX(t) : t;
      const i1 = index ? index.getX(t + 1) : t + 1;
      const i2 = index ? index.getX(t + 2) : t + 2;
      a.fromBufferAttribute(position, i0).applyMatrix4(mesh.matrixWorld);
      b.fromBufferAttribute(position, i1).applyMatrix4(mesh.matrixWorld);
      c.fromBufferAttribute(position, i2).applyMatrix4(mesh.matrixWorld);
      ab.subVectors(b, a);
      ac.subVectors(c, a);
      normal.crossVectors(ab, ac);
      const length = normal.length();
      if (length <= 0) continue;
      // Which way does this face look, relative to its own half's outward direction?
      const facing = (normal.z / length) * side;
      const into =
        facing <= -SEAT_FACE_COSINE
          ? reading.seat
          : facing >= SEAT_FACE_COSINE
            ? reading.outer
            : null;
      if (!into) continue;
      centroid
        .copy(a)
        .add(b)
        .add(c)
        .multiplyScalar(1 / 3);
      for (const [u, v, w] of lattice) {
        sample.set(
          a.x * u + b.x * v + c.x * w,
          a.y * u + b.y * v + c.y * w,
          a.z * u + b.z * v + c.z * w,
        );
        const at = queryPoint(sample, centroid);
        const qx = at.x;
        const qy = at.y;
        let host = surfaceAt(shell, qx, qy);
        for (const layer of under) {
          const face = surfaceAt(layer, qx, qy);
          if (face !== null && (host === null || face > host)) host = face;
        }
        if (host === null) continue;
        record(into, Math.abs(sample.z) - host, sample);
      }
    }
    layers[name] = { seat: close(reading.seat), outer: close(reading.outer) };
  }

  for (const undo of restore) undo();
  return { latticeOrder: LATTICE_ORDER, seatFaceCosine: SEAT_FACE_COSINE, layers };
};

/**
 * Do the two halves of a Z-split pair carry the SAME baked colour on the face that looks INWARD,
 * at the shell, and the same colour on the face that looks outward?
 *
 * They did not, and nothing asked. `applyFacetSteps` quantises each triangle against a key that
 * carries +0.66 in Z, so a face and its mirror image land on opposite sides of the quantiser: the
 * two films' shell-facing undersides measured sRGB (78.67, 43.82, 164.43) on the front half
 * against (85.83, 48.18, 178.52) on the rear, a linear-light ratio of 1.2003 on the same surface.
 * Rendered unlit that is the pixel value itself — `artifacts/ultima-v2/diag/skin-faces.json`.
 *
 * **Face-by-face pairing was tried first and is the wrong instrument**, which is worth writing
 * down because it looks like the obvious one. The two halves are exact mirrors as SURFACES but
 * not as triangle lists: `loft` splits each quad from `lower[i]` to `upper[i+1]`, and
 * `mirrorRearRing` reverses the ring order, so the rear half splits the mirrored quad along the
 * OTHER diagonal. Matching centroids paired only 16 of the insert's 90 faces on a build whose two
 * halves are provably identical in colour.
 *
 * So the comparison is area-weighted and per DIRECTION, which is also the way the requirement is
 * phrased: group each half's faces by whether they look toward the mid-plane or away from it, and
 * compare the two halves group for group. Area weighting makes it independent of how either half
 * happens to be cut up.
 *
 * Measured from the geometry rather than from renders on purpose. This is the value the model
 * authors; what the look-dev rig then does with it is lighting, and the rig's own key is the same
 * Z-facing vector, so a lit render can never separate the two.
 */
const MIRROR_PAIRS: [string, string][] = [
  ["purpleEnergyInsertFront", "purpleEnergyInsertRear"],
  ["darkCoreTriangleFront", "darkCoreTriangleRear"],
  ["rootDiamondGemFront", "rootDiamondGemRear"],
];
const measureMirrorColour = (runtime: SculptRuntime) => {
  /** Area-weighted mean vertex colour of the faces looking inward, and of those looking out. */
  const faces = (id: string, side: 1 | -1) => {
    const mesh = runtime.nodes.get(id) as THREE.Mesh | undefined;
    const totals = {
      inward: { area: 0, colour: [0, 0, 0] as [number, number, number] },
      outward: { area: 0, colour: [0, 0, 0] as [number, number, number] },
    };
    if (!mesh?.isMesh) return totals;
    const position = mesh.geometry.getAttribute("position");
    const colour = mesh.geometry.getAttribute("color");
    if (!colour) return totals;
    const a = new THREE.Vector3();
    const b = new THREE.Vector3();
    const c = new THREE.Vector3();
    const cross = new THREE.Vector3();
    for (let t = 0; t < position.count; t += 3) {
      a.fromBufferAttribute(position, t);
      b.fromBufferAttribute(position, t + 1);
      c.fromBufferAttribute(position, t + 2);
      cross.crossVectors(b.sub(a), c.sub(a));
      const area = cross.length() / 2;
      if (area <= 0) continue;
      // "Inward" is toward the cut plane, i.e. toward the shell this half is lying on.
      const bucket = cross.z * side < 0 ? totals.inward : totals.outward;
      bucket.area += area;
      for (let k = 0; k < 3; k += 1) {
        bucket.colour[0] += (colour.getX(t + k) / 3) * area;
        bucket.colour[1] += (colour.getY(t + k) / 3) * area;
        bucket.colour[2] += (colour.getZ(t + k) / 3) * area;
      }
    }
    return totals;
  };

  const pairs: Record<
    string,
    Record<"inward" | "outward", { front: number[]; rear: number[]; delta: number }>
  > = {};
  for (const [front, rear] of MIRROR_PAIRS) {
    const lhs = faces(front, 1);
    const rhs = faces(rear, -1);
    const entry = {} as (typeof pairs)[string];
    for (const group of ["inward", "outward"] as const) {
      const l = lhs[group];
      const r = rhs[group];
      const mean = (t: typeof l) => t.colour.map((v) => (t.area > 0 ? v / t.area : 0));
      const lm = mean(l);
      const rm = mean(r);
      entry[group] = {
        front: lm,
        rear: rm,
        delta: Math.max(...lm.map((v, i) => Math.abs(v - rm[i]!))),
      };
    }
    pairs[front.replace("Front", "")] = entry;
  }
  return pairs;
};

/** Layers, not `visible`: isolate a part while its ancestors keep rendering children. */
const isolatePart = (model: THREE.Group, only: string) => {
  const runtime = model.userData.sculptRuntime as SculptRuntime | undefined;
  const target = runtime?.nodes.get(only);
  if (!target) {
    const available = [...(runtime?.nodes.keys() ?? [])].sort().join(", ");
    throw new Error(`unknown part "${only}", available parts: ${available}`);
  }
  let meshes = 0;
  target.traverse((object) => {
    if ((object as THREE.Mesh).isMesh) meshes += 1;
  });
  if (meshes === 0) {
    throw new Error(`part "${only}" holds no mesh, so isolating it would render an empty frame`);
  }
  model.traverse((object) => object.layers.disableAll());
  target.traverse((object) => object.layers.enable(0));
  return { isolatedPart: only, isolatedMeshes: meshes, frameTarget: target };
};

const takeOverViewport = (transparent: boolean) => {
  const hidden: HTMLElement[] = [];
  for (const el of document.querySelectorAll<HTMLElement>("header, footer")) {
    hidden.push(el);
    el.style.display = "none";
  }
  const previous = {
    htmlBackground: document.documentElement.style.background,
    htmlOverflow: document.documentElement.style.overflow,
    bodyBackground: document.body.style.background,
    bodyMargin: document.body.style.margin,
  };
  document.documentElement.style.overflow = "hidden";
  document.documentElement.style.background = transparent ? "transparent" : "#ffffff";
  document.body.style.background = "transparent";
  document.body.style.margin = "0";
  return () => {
    for (const el of hidden) el.style.display = "";
    document.documentElement.style.background = previous.htmlBackground;
    document.documentElement.style.overflow = previous.htmlOverflow;
    document.body.style.background = previous.bodyBackground;
    document.body.style.margin = previous.bodyMargin;
  };
};

const start = async () => {
  const canvas = canvasEl.value;
  if (!canvas) throw new Error("the harness canvas is missing");

  const params = readParams(window.location.search);
  if (!(REVIEW_VIEWS as readonly string[]).includes(params.view)) {
    throw new Error(`unknown view "${params.view}", expected one of ${REVIEW_VIEWS.join(", ")}`);
  }
  // `view` has always thrown on an unknown value; `mode` used to cast silently, so a typo landed
  // in the neutral branch and captured a set of evidence renders labelled as something else.
  if (!isLightingMode(params.mode)) {
    throw new Error(`unknown mode "${params.mode}", expected one of ${LIGHTING_MODES.join(", ")}`);
  }
  // The stage floor is opaque geometry that is not part of the weapon, so on a transparent
  // background it lands in the alpha channel and every silhouette-derived measurement reads the
  // floor as blade. render-harness.vue learned this one the same way. Refusing the combination is
  // better than producing a mask that looks plausible and is wrong.
  if (params.mode === "blackBox" && params.transparent) {
    throw new Error(
      "blackBox is a presentation stage and cannot be captured on a transparent " +
        "background: its floor would be baked into the silhouette mask",
    );
  }

  restoreChrome = takeOverViewport(params.transparent);
  canvas.style.width = `${params.width}px`;
  canvas.style.height = `${params.height}px`;

  const model = createUltimaWeaponV2Model({ detail: params.detail });
  const runtime = model.userData.sculptRuntime as SculptRuntime;
  (window as HarnessWindow).__sculptRuntime = runtime;

  // Measured on the model AS BUILT: before the explode is applied, before `--hide` removes a
  // part and before an isolate turns its layers off. Every one of those three would change the
  // answer, and the question is about the model rather than about this frame.
  model.updateWorldMatrix(true, true);
  const shellPenetration = measureShellPenetration(runtime);
  const stackConformity = measureStackConformity(runtime);
  const mirrorColour = measureMirrorColour(runtime);

  const recipe = reviewRecipe(params.view);
  runtime.setExplode(params.explode ?? recipe.explode ?? 0);

  for (const partId of params.hide) runtime.setPartVisible(partId, false);

  const isolated = recipe.isolate ? isolatePart(model, recipe.isolate) : null;

  // A close-up frames one node while everything else keeps rendering — the opposite of an
  // isolate, and the only way a socket close-up can show the rod actually entering it.
  let closeUp: THREE.Object3D | undefined;
  if (recipe.frame) {
    closeUp = runtime.nodes.get(recipe.frame);
    if (!closeUp) {
      const available = [...runtime.nodes.keys()].sort().join(", ");
      throw new Error(`unknown frame target "${recipe.frame}", available: ${available}`);
    }
  }

  const bounds = new THREE.Box3().setFromObject(model).getBoundingSphere(new THREE.Sphere());
  const rig = createUltimaWeaponV2LookDevLights(params.mode, bounds);
  const restoreMaterials = applyMaterialOverrides(runtime.materials, rig.materialOverrides);
  // No-ops while the renderer's shadow map is off, which is every review capture.
  model.traverse((object) => {
    if (object instanceof THREE.Mesh) {
      object.castShadow = true;
      object.receiveShadow = true;
    }
  });
  const aspect = params.width / params.height;
  const camera = createReviewCamera(params.view, model, aspect, isolated?.frameTarget ?? closeUp, {
    yaw: params.yaw,
    pitch: params.pitch,
    roll: params.roll,
  });

  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
    preserveDrawingBuffer: true,
  });
  renderer.setPixelRatio(1);
  renderer.setSize(params.width, params.height, false);
  renderer.toneMapping = rig.toneMapping;
  renderer.toneMappingExposure = rig.toneMappingExposure;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setClearColor(0x000000, 0);
  renderer.shadowMap.enabled = rig.shadows;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  scene.add(model, rig.lights);
  const environment = rig.createEnvironment(renderer);
  scene.environment = environment;
  scene.environmentIntensity = rig.environmentIntensity;
  scene.background = params.transparent ? null : rig.background;
  if (params.checker) {
    const tile = 16;
    const data = new Uint8Array(tile * tile * 4);
    for (let y = 0; y < tile; y += 1) {
      for (let x = 0; x < tile; x += 1) {
        const v = x < tile / 2 === y < tile / 2 ? 214 : 152;
        const i = (y * tile + x) * 4;
        data[i] = v;
        data[i + 1] = v;
        data[i + 2] = v + 6;
        data[i + 3] = 255;
      }
    }
    const texture = new THREE.DataTexture(data, tile, tile, THREE.RGBAFormat);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
    texture.repeat.set(24, 24);
    texture.magFilter = THREE.NearestFilter;
    texture.needsUpdate = true;
    scene.background = texture;
  }

  if (params.wireframe) {
    model.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (!mesh.isMesh) return;
      for (const material of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
        (material as THREE.MeshStandardMaterial).wireframe = true;
      }
    });
  }

  if (params.flat) {
    // Unlit materials. The silhouette gate must measure geometry, not how flattering the
    // look-dev happens to be — and it is what caught a roughnessMap defect on an earlier run.
    model.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (!mesh.isMesh) return;
      const source = (Array.isArray(mesh.material) ? mesh.material[0] : mesh.material) as
        | THREE.MeshStandardMaterial
        | undefined;
      mesh.material = new THREE.MeshBasicMaterial({
        color: source?.color ?? new THREE.Color(0xffffff),
        vertexColors: source?.vertexColors ?? false,
        transparent: false,
        depthWrite: true,
        side: source?.side ?? THREE.FrontSide,
      });
    });
  }

  let meshCount = 0;
  let triangles = 0;
  model.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (!mesh.isMesh) return;
    meshCount += 1;
    const index = mesh.geometry.getIndex();
    const position = mesh.geometry.getAttribute("position");
    triangles += (index ? index.count : position.count) / 3;
  });

  // The area-weighted CENTROID of a node's own triangles, in world space. A bounding box cannot
  // answer correction D: it asks where a part's mass sits, and a rhombus whose waist has drifted
  // off the authority line still has a box centred between its two tips. For a closed body that
  // mirrors across its own waist this equals the volume centroid, which is the quantity the
  // assertion is about.
  const centroidOf = (node: THREE.Object3D): [number, number, number] | null => {
    let area = 0;
    const acc: [number, number, number] = [0, 0, 0];
    const a = new THREE.Vector3();
    const b = new THREE.Vector3();
    const c = new THREE.Vector3();
    node.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (!mesh.isMesh) return;
      const position = mesh.geometry.getAttribute("position");
      const index = mesh.geometry.getIndex();
      const count = index ? index.count : position.count;
      for (let i = 0; i < count; i += 3) {
        const [i0, i1, i2] = index
          ? [index.getX(i), index.getX(i + 1), index.getX(i + 2)]
          : [i, i + 1, i + 2];
        a.fromBufferAttribute(position, i0).applyMatrix4(mesh.matrixWorld);
        b.fromBufferAttribute(position, i1).applyMatrix4(mesh.matrixWorld);
        c.fromBufferAttribute(position, i2).applyMatrix4(mesh.matrixWorld);
        const w = b.clone().sub(a).cross(c.clone().sub(a)).length() / 2;
        if (!(w > 0)) continue;
        area += w;
        acc[0] += ((a.x + b.x + c.x) / 3) * w;
        acc[1] += ((a.y + b.y + c.y) / 3) * w;
        acc[2] += ((a.z + b.z + c.z) / 3) * w;
      }
    });
    return area > 0 ? [acc[0] / area, acc[1] / area, acc[2] / area] : null;
  };

  const parts: {
    name: string;
    kind: string;
    triangles: number;
    bounds: { minX: number; maxX: number; minY: number; maxY: number; minZ: number; maxZ: number };
    centroid: [number, number, number] | null;
  }[] = [];
  let unnamedMeshes = 0;
  model.updateWorldMatrix(true, true);
  for (const [name, node] of runtime.nodes) {
    let tris = 0;
    let namedChildren = 0;
    node.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (!mesh.isMesh) return;
      const index = mesh.geometry.getIndex();
      const position = mesh.geometry.getAttribute("position");
      tris += (index ? index.count : position.count) / 3;
    });
    for (const child of node.children) {
      if (child.name && runtime.nodes.has(child.name)) namedChildren += 1;
    }
    // World-space bounds, exported so the centreline check is a real assertion over the built
    // model rather than a claim about the source. A part whose |minX + maxX| is not ~0 has
    // drifted off the sword's structural axis.
    const box = new THREE.Box3().setFromObject(node);
    parts.push({
      name,
      kind: (node as THREE.Mesh).isMesh ? "part" : namedChildren > 0 ? "container" : "part",
      triangles: Math.round(tris),
      bounds: box.isEmpty()
        ? { minX: 0, maxX: 0, minY: 0, maxY: 0, minZ: 0, maxZ: 0 }
        : {
            minX: box.min.x,
            maxX: box.max.x,
            minY: box.min.y,
            maxY: box.max.y,
            minZ: box.min.z,
            maxZ: box.max.z,
          },
      centroid: centroidOf(node),
    });
  }
  model.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (mesh.isMesh && !mesh.name) unnamedMeshes += 1;
  });

  (window as HarnessWindow).__partManifest = {
    model: "cloud-ultima-weapon-v2",
    parts,
    unnamedMeshes,
    integralMeshes: parts.filter((p) => p.kind === "part").length,
    shellPenetration,
    stackConformity,
    mirrorColour,
  };

  (window as HarnessWindow).__renderHarness = {
    ...params,
    ...(isolated
      ? { isolatedPart: isolated.isolatedPart, isolatedMeshes: isolated.isolatedMeshes }
      : {}),
    cameraName: camera.name,
    namedParts: runtime.nodes.size,
    meshCount,
    triangles: Math.round(triangles),
    drawingBufferWidth: renderer.domElement.width,
    drawingBufferHeight: renderer.domElement.height,
  };

  let frame = 0;
  let handle = 0;
  const loop = () => {
    handle = window.requestAnimationFrame(loop);
    renderer.render(scene, camera);
    frame += 1;
    if (frame === 3) (window as HarnessWindow).__renderReady = true;
  };
  loop();

  disposeScene = () => {
    window.cancelAnimationFrame(handle);
    restoreMaterials();
    rig.lights.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) return;
      object.geometry.dispose();
      const used = Array.isArray(object.material) ? object.material : [object.material];
      for (const material of used) material.dispose();
    });
    environment.dispose();
    renderer.dispose();
  };
};

onMounted(() => {
  if (typeof window === "undefined") return;
  start().catch((cause: unknown) => {
    const message = cause instanceof Error ? cause.message : String(cause);
    error.value = message;
    (window as HarnessWindow).__renderError = message;
    console.error("[ultima-v2-harness]", cause);
  });
});

onBeforeUnmount(() => {
  disposeScene?.();
  restoreChrome?.();
});
</script>

<style scoped>
.ultima-harness {
  position: fixed;
  inset: 0;
  z-index: 999;
  overflow: hidden;
  background: transparent;
}

#ultima-harness-canvas {
  display: block;
  position: absolute;
  top: 0;
  left: 0;
}

.ultima-harness-error {
  position: absolute;
  top: 0;
  left: 0;
  padding: 1rem;
  background: #300;
  color: #fbb;
  font-family: ui-monospace, monospace;
}
</style>
