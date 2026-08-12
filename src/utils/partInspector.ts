import * as THREE from "three";
/**
 * The three bits of a controls object the inspector actually touches. Structural rather than
 * `OrbitControls`, so an exhibit can hand over ArcballControls (or anything else) instead.
 */
export type InspectorControls = {
  /** `Object3D` because that is how the base `Controls` class types it; it is always a camera. */
  object: THREE.Object3D;
  target: THREE.Vector3;
  update: () => unknown;
};
import type { Exhibit } from "./exhibits.js";

/**
 * Click-to-inspect part tree, ported from img2threejs-showcase's scene.ts.
 *
 * Deliberately model-agnostic: it reads the object graph, not a per-exhibit
 * registry, so any procedural build whose nodes are named gets a part list for
 * free. A model whose meshes are unnamed simply yields an empty list rather
 * than selecting nonsense.
 */

/** A component a click can resolve to: what gets named, highlighted, isolated. */
export type PartInfo = {
  name: string;
  /** Nearest named ancestor — the assembly this part belongs to. */
  module: string | null;
  /**
   * `detail` = relief that rides a shell (a badge face, a window band) rather
   * than a component you could hold. Marked by `userData.explodeWithParent`.
   */
  kind: "part" | "detail";
  triangles: number;
  /** One human-readable line per material slot, with the PBR scalars spelled out. */
  materials: string[];
  object: THREE.Object3D;
};

const isRealMesh = (o: THREE.Object3D): o is THREE.Mesh =>
  (o as THREE.Mesh).isMesh === true && !!(o as THREE.Mesh).geometry && !o.userData.isHighlight;

function triangleCount(root: THREE.Object3D): number {
  let n = 0;
  root.traverse((o) => {
    if (!isRealMesh(o)) return;
    const g = o.geometry;
    n += (g.index ? g.index.count : (g.attributes.position?.count ?? 0)) / 3;
  });
  return Math.round(n);
}

/**
 * Label a material by what it reads as, then give the numbers behind the label.
 * The numbers matter: "steel" is a claim, `metal 1.00 · rough 0.46` is what was
 * actually authored. A channel driven by a texture prints "map" — the scalar is
 * only a multiplier over it there, so printing it would be a lie.
 */
function describeMaterial(mat: THREE.Material): string {
  const m = mat as THREE.MeshPhysicalMaterial;
  if (typeof m.metalness !== "number" || typeof m.roughness !== "number") return mat.type;
  const trans = m.transmission ?? 0;
  const kind =
    trans > 0.05
      ? "translucent polymer"
      : m.metalnessMap || m.roughnessMap
        ? "mapped surface"
        : m.metalness >= 0.85
          ? "steel"
          : m.metalness >= 0.45
            ? "gunmetal"
            : m.roughness >= 0.55
              ? "matte polymer"
              : "polymer";
  const bits = [
    kind,
    `metal ${m.metalnessMap ? "map" : m.metalness.toFixed(2)}`,
    `rough ${m.roughnessMap ? "map" : m.roughness.toFixed(2)}`,
  ];
  if (trans > 0.05) bits.push(`transmission ${trans.toFixed(2)}`);
  return bits.join(" · ");
}

/** What every exhibit stage renders, whichever viewer it wraps. */
export type ExhibitStageProps = {
  exhibit: Exhibit;
  prompt: string;
  images: { src: string; caption: string }[];
  docHref: (file: string) => string;
  note?: string;
};

/** The slice of a viewer API the exhibit page drives. Every exhibit viewer exposes it. */
export type StageViewer = {
  parts: PartInfo[];
  selectPart: (name: string | null) => void;
  setIsolate: (on: boolean) => void;
  /** Present when the model can be pulled apart. Omit and the page hides the control. */
  setExplode?: (t: number) => void;
  /** Model-level honesty note printed under the part list, when the build records one. */
  provenance?: string;
  dispose: () => void;
};

/**
 * The build's own record of how it was made, as one line. Model-level, not
 * per-part: it is the honest caption for every number above it in the panel.
 * Reads either shape the exhibits use — a plain string, or the structured
 * record upstream writes onto `sculptRuntime`.
 */
export function readProvenance(root: THREE.Object3D): string | undefined {
  const plain = root.userData.provenance;
  if (typeof plain === "string") return plain;
  const rt = root.userData.sculptRuntime as
    | { provenance?: { route?: string; exactnessTier?: string; thicknessConfidence?: number } }
    | undefined;
  const p = rt?.provenance;
  if (!p) return undefined;
  const line = [
    p.route,
    p.exactnessTier,
    p.thicknessConfidence !== undefined ? `z-depth confidence ${p.thicknessConfidence}` : null,
  ]
    .filter(Boolean)
    .join(" · ");
  return line || undefined;
}

export type PartInspector = {
  readonly parts: PartInfo[];
  readonly selected: PartInfo | null;
  readonly isolated: boolean;
  /** False for a single-mesh model — nothing to pull apart. */
  readonly canExplode: boolean;
  selectByName: (name: string | null) => void;
  setIsolate: (on: boolean) => void;
  /** 0 = assembled, 1 = fully separated. Eased on its own animation frame. */
  setExplode: (t: number) => void;
  dispose: () => void;
};

export function createPartInspector(opts: {
  root: THREE.Object3D;
  domElement: HTMLElement;
  /** The camera currently rendering. A getter, not a value: exhibits swap cameras. */
  getCamera: () => THREE.Camera;
  /** Supplied when isolate should also dolly onto the part. Omit and isolate only hides. */
  controls?: InspectorControls;
  onChange: (selected: PartInfo | null, isolated: boolean) => void;
}): PartInspector {
  const { root, domElement, getCamera, controls, onChange } = opts;

  // Deliberately not the site accent: the accent also tints the exhibits
  // themselves, and a selection has to read as *not* part of the object.
  const highlightMat = new THREE.MeshBasicMaterial({
    color: new THREE.Color("#6fe3ff"),
    transparent: true,
    opacity: 0.38,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    toneMapped: false,
    side: THREE.DoubleSide,
    // The overlay shares the source geometry exactly, so without a depth nudge
    // it z-fights the surface it tints and the glow breaks into speckle.
    polygonOffset: true,
    polygonOffsetFactor: -1,
    polygonOffsetUnits: -1,
  });

  const raycaster = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  const highlightMeshes: THREE.Mesh[] = [];
  const hiddenByIsolate: THREE.Object3D[] = [];
  let selection: PartInfo | null = null;
  let isolateOn = false;
  let camRest: { target: THREE.Vector3; position: THREE.Vector3 } | null = null;
  let frustumRest: { near: number; far: number } | null = null;

  /**
   * Move the orbit camera to `dist` from its target and widen the frustum to match.
   *
   * The exhibits fit near/far tightly to the assembled model (balamb's reference camera is
   * `near = d - 2r`, `far = d + 4r`), so dollying out for an explode or in for an isolate
   * puts the subject outside the authored planes and clips the whole model away. Only ever
   * widens; the authored values are remembered and put back at rest.
   */
  const setCameraDistance = (dist: number, reach: number): void => {
    if (!controls) return;
    const cam = controls.object as THREE.PerspectiveCamera;
    const dir = cam.position.clone().sub(controls.target);
    if (dir.lengthSq() < 1e-8) return;
    cam.position.copy(controls.target).addScaledVector(dir.normalize(), dist);
    frustumRest ??= { near: cam.near, far: cam.far };
    cam.near = Math.max(0.01, Math.min(frustumRest.near, dist - reach));
    cam.far = Math.max(frustumRest.far, dist + reach);
    cam.updateProjectionMatrix();
    controls.update();
  };

  const restoreFrustum = (): void => {
    if (!controls || !frustumRest) return;
    const cam = controls.object as THREE.PerspectiveCamera;
    cam.near = frustumRest.near;
    cam.far = frustumRest.far;
    cam.updateProjectionMatrix();
    frustumRest = null;
  };

  /** World-space radius of the assembled model — the unit every reach below is measured in. */
  const rootRadius = Math.max(
    new THREE.Box3().setFromObject(root).getBoundingSphere(new THREE.Sphere()).radius,
    1e-4,
  );
  let pickDown: { x: number; y: number } | null = null;
  let pickKey = "";
  let pickIndex = 0;

  /**
   * A named Mesh is a part. A named Group is a *container* — `tower`,
   * `lowerHull` — and must be descended through, EXCEPT when it holds no
   * selectable descendant, which is what a group of anonymous meshes looks
   * like: that group is the part itself.
   */
  const isSelectable = (o: THREE.Object3D): boolean => {
    if (!o.name || o.userData.isHighlight) return false;
    if (isRealMesh(o)) return true;
    let hasMesh = false;
    o.traverse((c) => {
      if (isRealMesh(c)) hasMesh = true;
    });
    return hasMesh && !hasSelectableDescendant(o);
  };

  const hasSelectableDescendant = (o: THREE.Object3D): boolean =>
    o.children.some((c) => isSelectable(c) || hasSelectableDescendant(c));

  const moduleOf = (o: THREE.Object3D): string | null => {
    let n = o.parent;
    while (n && n !== root) {
      if (n.name) return n.name;
      n = n.parent;
    }
    return null;
  };

  const describePart = (o: THREE.Object3D): PartInfo => {
    const meshes: THREE.Mesh[] = [];
    o.traverse((c) => {
      if (isRealMesh(c)) meshes.push(c);
    });
    const first = meshes[0];
    const kind =
      isRealMesh(o) || meshes.some((m) => !m.userData.explodeWithParent) ? "part" : "detail";
    const mats = first ? (Array.isArray(first.material) ? first.material : [first.material]) : [];
    return {
      name: o.name,
      module: moduleOf(o),
      kind,
      triangles: triangleCount(o),
      materials: [...new Set(mats.map(describeMaterial))],
      object: o,
    };
  };

  const parts: PartInfo[] = [];
  const walk = (o: THREE.Object3D): void => {
    if (o !== root && isSelectable(o)) parts.push(describePart(o));
    for (const c of o.children) walk(c);
  };
  walk(root);

  /** Walk up from any mesh to the component that owns it, bounded by the root. */
  const resolveOwner = (hit: THREE.Object3D): THREE.Object3D | null => {
    let n: THREE.Object3D | null = hit;
    while (n && n !== root) {
      if (isSelectable(n)) return n;
      n = n.parent;
    }
    return null;
  };

  const visibleUpTo = (o: THREE.Object3D): boolean => {
    let n: THREE.Object3D | null = o;
    while (n && n !== root) {
      if (!n.visible) return false;
      n = n.parent;
    }
    return true;
  };

  /** Components under the pointer, front to back, deduped. */
  const pickAt = (e: PointerEvent): THREE.Object3D[] => {
    const rect = domElement.getBoundingClientRect();
    ndc.set(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1,
    );
    raycaster.setFromCamera(ndc, getCamera());
    const out: THREE.Object3D[] = [];
    for (const hit of raycaster.intersectObject(root, true)) {
      if (hit.object.userData.isHighlight || !visibleUpTo(hit.object)) continue;
      const node = resolveOwner(hit.object);
      if (node && !out.includes(node)) out.push(node);
    }
    return out;
  };

  const clearHighlight = (): void => {
    for (const g of highlightMeshes) g.removeFromParent();
    highlightMeshes.length = 0;
  };

  const addHighlight = (node: THREE.Object3D): void => {
    const targets: THREE.Mesh[] = [];
    node.traverse((c) => {
      if (isRealMesh(c)) targets.push(c);
    });
    for (const t of targets) {
      const glow = new THREE.Mesh(t.geometry, highlightMat);
      glow.userData.isHighlight = true;
      glow.renderOrder = 999;
      t.add(glow);
      highlightMeshes.push(glow);
    }
  };

  const restoreHidden = (): void => {
    for (const m of hiddenByIsolate) m.visible = true;
    hiddenByIsolate.length = 0;
  };

  /** Pull the orbit onto the part's bounding sphere, remembering where to return to.
   *  Skipped while a fixed camera is active — reframing there would break the very
   *  thing that camera exists to reproduce. */
  const focusOn = (node: THREE.Object3D): void => {
    if (!controls || controls.object !== getCamera()) return;
    const box = new THREE.Box3().setFromObject(node);
    if (box.isEmpty()) return;
    const cam = controls.object as THREE.PerspectiveCamera;
    camRest ??= { target: controls.target.clone(), position: cam.position.clone() };
    const center = box.getCenter(new THREE.Vector3());
    const radius = Math.max(box.getBoundingSphere(new THREE.Sphere()).radius, 1e-4);
    controls.target.copy(center);
    setCameraDistance((radius / Math.tan((cam.fov * Math.PI) / 360)) * 2.2, rootRadius);
  };

  const applyIsolate = (): void => {
    restoreHidden();
    const keep = new Set<THREE.Object3D>();
    selection!.object.traverse((o) => keep.add(o));
    root.traverse((o) => {
      if (!isRealMesh(o) || keep.has(o) || !o.visible) return;
      o.visible = false;
      hiddenByIsolate.push(o);
    });
    focusOn(selection!.object);
  };

  const clearIsolate = (): void => {
    restoreHidden();
    if (!camRest || !controls) return;
    controls.target.copy(camRest.target);
    (controls.object as THREE.PerspectiveCamera).position.copy(camRest.position);
    controls.update();
    camRest = null;
    if (explodeT === 0) restoreFrustum();
  };

  const applySelection = (part: PartInfo | null): void => {
    clearHighlight();
    selection = part;
    if (part) addHighlight(part.object);
    if (isolateOn) {
      if (part) applyIsolate();
      else setIsolate(false);
    }
    onChange(selection, isolateOn);
  };

  function setIsolate(on: boolean): void {
    if (on && !selection) return;
    isolateOn = on;
    if (on) applyIsolate();
    else clearIsolate();
    onChange(selection, isolateOn);
  }

  const selectByName = (name: string | null): void => {
    applySelection(name ? (parts.find((p) => p.name === name) ?? null) : null);
  };

  /**
   * Clicking the same spot again steps to the next component along the same
   * ray, which walks you inward: hull → tower drum → window band. Without it
   * anything behind a surface is unreachable.
   */
  const handlePick = (e: PointerEvent): void => {
    const hits = pickAt(e);
    if (!hits.length) {
      applySelection(null);
      return;
    }
    const key = hits.map((h) => h.name).join(">");
    pickIndex = key === pickKey ? (pickIndex + 1) % hits.length : 0;
    pickKey = key;
    applySelection(describePart(hits[pickIndex]!));
  };

  const onDown = (e: PointerEvent) => {
    pickDown = { x: e.clientX, y: e.clientY };
  };
  const onUp = (e: PointerEvent) => {
    const d = pickDown;
    pickDown = null;
    // An orbit drag ends in a pointerup too; only a near-stationary release is a click.
    if (!d || Math.hypot(e.clientX - d.x, e.clientY - d.y) > 4) return;
    handlePick(e);
  };
  const onMove = (e: PointerEvent) => {
    if (pickDown) return; // mid-drag: leave the cursor alone
    domElement.style.cursor = pickAt(e).length ? "pointer" : "";
  };
  const onKey = (e: KeyboardEvent) => {
    if (e.key !== "Escape") return;
    if (isolateOn) setIsolate(false);
    else selectByName(null);
  };

  // ---------------------------------------------------------------- explode

  type ExplodePart = { object: THREE.Object3D; rest: THREE.Vector3; offset: THREE.Vector3 };
  let explodeParts: ExplodePart[] | null = null;
  let explodeT = 0;
  let explodeTarget = 0;
  let explodeZoom = 1;
  let explodeBaseDist = 0;
  let explodeRaf = 0;

  /**
   * The things the explode moves: exactly the components the inspector can
   * select, so the two never disagree about what "a part" is. A mesh belonging
   * to no named component falls back to being its own unit, which keeps a model
   * with no naming at all still explodable.
   */
  const explodeUnits = (): THREE.Object3D[] => {
    const units: THREE.Object3D[] = [];
    const seen = new Set<THREE.Object3D>();
    root.traverse((o) => {
      if (!isRealMesh(o) || o.userData.explodeWithParent) return;
      const owner = resolveOwner(o) ?? o;
      if (seen.has(owner)) return;
      seen.add(owner);
      units.push(owner);
    });
    return units;
  };

  /**
   * Snapshot each unit's rest position plus the direction it flies out along.
   *
   * All the maths is done in the ROOT's local frame, not world space, so a model
   * whose `userData.tick` spins it does not drag the offsets around. The offset
   * is then rotated into each unit's own parent frame, so parts nested under a
   * pivot group separate correctly too.
   */
  const prepareExplode = (): void => {
    root.updateWorldMatrix(true, true);
    const rootInv = new THREE.Matrix4().copy(root.matrixWorld).invert();
    const units = explodeUnits();

    const centres = units.map((m) =>
      new THREE.Box3().setFromObject(m).getCenter(new THREE.Vector3()).applyMatrix4(rootInv),
    );
    const bounds = new THREE.Box3();
    for (const c of centres) bounds.expandByPoint(c);
    const origin = bounds.getCenter(new THREE.Vector3());
    const span = bounds.getSize(new THREE.Vector3());
    const radius = Math.max(1e-4, bounds.getBoundingSphere(new THREE.Sphere()).radius);

    // Parts stacked concentrically (a drum inside a collar) have almost no radial
    // direction and would stay buried. Push those apart along the model's THINNEST
    // axis instead — exactly the axis a layered assembly hides things along.
    const thin =
      span.x <= span.y && span.x <= span.z
        ? new THREE.Vector3(1, 0, 0)
        : span.y <= span.z
          ? new THREE.Vector3(0, 1, 0)
          : new THREE.Vector3(0, 0, 1);

    // Expanding the LAYOUT is what separates parts: displacing every unit by the
    // same distance slides the arrangement outward without opening the gaps
    // between neighbours. The base push then guarantees a visible gap near the
    // centre, where the scaling term alone is almost nothing.
    const SCALE = 2.1;
    const base = Math.max(radius * 0.3, 0.18);

    const explodedBounds = new THREE.Box3();
    let concentric = 0;

    explodeParts = units.map((unit, i) => {
      const radial = centres[i]!.clone().sub(origin);
      let local: THREE.Vector3;
      if (radial.length() < radius * 0.08) {
        // Fan the buried stack out along the thin axis in alternating, growing
        // steps, so three or more concentric parts land as a readable row.
        const rank = concentric++;
        const step = (Math.floor(rank / 2) + 1) * base * 1.4;
        local = thin.clone().multiplyScalar(rank % 2 === 0 ? step : -step);
      } else {
        local = radial
          .clone()
          .multiplyScalar(SCALE - 1)
          .addScaledVector(radial.clone().normalize(), base);
      }
      explodedBounds.expandByPoint(centres[i]!.clone().add(local));

      // root-local displacement -> this unit's parent frame. transformDirection
      // normalises, so the length comes off first and goes back on after.
      const toParent = new THREE.Matrix4()
        .multiplyMatrices(rootInv, unit.parent!.matrixWorld)
        .invert();
      const len = local.length();
      const offset = local.transformDirection(toParent).multiplyScalar(len);
      return { object: unit, rest: unit.position.clone(), offset };
    });

    // Dolly by how far the layout actually grew rather than by a fixed guess.
    const grown = explodedBounds.getBoundingSphere(new THREE.Sphere()).radius;
    explodeZoom = Math.min(3.4, Math.max(1, grown / radius));
  };

  const applyExplode = (): void => {
    if (!explodeParts) prepareExplode();
    for (const p of explodeParts!) {
      p.object.position.copy(p.rest).addScaledVector(p.offset, explodeT);
    }
    // Pull the camera back as things come apart, otherwise the outermost parts
    // leave the frame. Only while the animation runs, so zoom stays the viewer's.
    if (!controls || controls.object !== getCamera()) return;
    setCameraDistance(
      explodeBaseDist * (1 + (explodeZoom - 1) * explodeT),
      rootRadius * explodeZoom,
    );
    if (explodeT === 0 && !isolateOn) restoreFrustum();
  };

  const stepExplode = (): void => {
    explodeRaf = 0;
    const delta = explodeTarget - explodeT;
    explodeT = Math.abs(delta) < 0.002 ? explodeTarget : explodeT + delta * 0.16;
    applyExplode();
    if (explodeT !== explodeTarget) explodeRaf = requestAnimationFrame(stepExplode);
  };

  const setExplode = (t: number): void => {
    const next = Math.min(1, Math.max(0, t));
    // Capture the framing distance the moment we leave the assembled pose, so the
    // dolly has a stable base even if the viewer zoomed since the last explode.
    if (explodeT === 0 && next > 0 && controls) {
      explodeBaseDist = (controls.object as THREE.PerspectiveCamera).position.distanceTo(
        controls.target,
      );
    }
    explodeTarget = next;
    if (!explodeRaf) explodeRaf = requestAnimationFrame(stepExplode);
  };

  let meshCount = 0;
  root.traverse((o) => {
    if (isRealMesh(o)) meshCount++;
  });

  domElement.addEventListener("pointerdown", onDown);
  domElement.addEventListener("pointerup", onUp);
  domElement.addEventListener("pointermove", onMove);
  window.addEventListener("keydown", onKey);

  return {
    parts,
    get selected() {
      return selection;
    },
    get isolated() {
      return isolateOn;
    },
    canExplode: meshCount > 1,
    selectByName,
    setIsolate,
    setExplode,
    dispose() {
      domElement.removeEventListener("pointerdown", onDown);
      domElement.removeEventListener("pointerup", onUp);
      domElement.removeEventListener("pointermove", onMove);
      window.removeEventListener("keydown", onKey);
      cancelAnimationFrame(explodeRaf);
      // Hand the parts back at rest: the exhibit's own ticker owns them again.
      for (const p of explodeParts ?? []) p.object.position.copy(p.rest);
      clearHighlight();
      restoreHidden();
      highlightMat.dispose();
    },
  };
}
