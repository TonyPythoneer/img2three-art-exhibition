import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { createUltimaWeaponV2Model, type SculptRuntime } from "./createUltimaWeaponV2Model";
import {
  applyMaterialOverrides,
  createUltimaWeaponV2LookDevLights,
  createReviewCamera,
  type LightingMode,
  type LookDevRig,
} from "./createUltimaWeaponV2LookDev";
import { createPartInspector, readProvenance, type PartInfo } from "../partInspector";

/**
 * Client-only mount for the v2 rebuild. Same viewer contract as the Opus, Codex Sol and Fable
 * runs so the exhibit page can swap between all four without special-casing any of them —
 * everything WebGL lives behind this dynamic import so vite-ssg never touches a renderer.
 */

export type ViewerPreset = "reference" | "front" | "side" | "three-quarter";

export type IsolationTarget = "none" | "shell" | "core" | "spine" | "guard" | "handle";

export type V2MountOptions = {
  onPartChange?: (selected: PartInfo | null, isolated: boolean) => void;
};

export type V2ViewerApi = {
  setPreset: (preset: ViewerPreset) => void;
  setMode: (mode: LightingMode) => void;
  setBlackBoxIntensity: (value: number) => void;
  setExplode: (amount: number) => void;
  setIsolation: (target: IsolationTarget) => void;
  setSpinning: (spinning: boolean) => void;
  stats: { parts: number; meshes: number; triangles: number };
  parts: PartInfo[];
  selectPart: (name: string | null) => void;
  setIsolate: (on: boolean) => void;
  setPartVisible: (id: string, visible: boolean) => void;
  isPartVisible: (id: string) => boolean;
  toggleableParts: string[];
  provenance?: string;
  dispose: () => void;
};

/**
 * The shared isolation vocabulary, mapped onto this build's eight public part types. "spine"
 * is the earlier runs' name for the frontal red mass, which here is two separate nodes — the
 * dark core and the root gem — so it keeps both.
 */
const ISOLATION: Record<IsolationTarget, string[] | null> = {
  none: null,
  shell: ["outerCrystalShell"],
  core: ["purpleEnergyInsertFront", "purpleEnergyInsertRear"],
  // The frontal red mass is two layers here — a dark-core skin on each face and the stone above
  // them — plus the jaws that hold them, and those jaws are the blade socket, so isolating the
  // "spine" isolates the whole blade-to-hilt junction.
  spine: [
    "darkCoreTriangleFront",
    "darkCoreTriangleRear",
    "rootDiamondGemFront",
    "rootDiamondGemRear",
    "crystalClampLeft",
    "crystalClampRight",
  ],
  guard: [
    "leatherConnectorLeft",
    "leatherConnectorRight",
    "spinnerEndLeft",
    "spinnerEndRight",
    "driverArray",
  ],
  handle: ["leatherGrip", "pointedMetalPommel"],
};

const TOGGLEABLE = [
  "outerCrystalShell",
  "purpleEnergyInsertFront",
  "purpleEnergyInsertRear",
  "darkCoreTriangleFront",
  "darkCoreTriangleRear",
  "rootDiamondGemFront",
  "rootDiamondGemRear",
  "crystalClampLeft",
  "crystalClampRight",
  "leatherConnectorLeft",
  "leatherConnectorRight",
  "spinnerEndLeft",
  "spinnerEndRight",
  "driverArray",
  "leatherGrip",
  "pointedMetalPommel",
];

const PRESET_DIRECTIONS: Record<Exclude<ViewerPreset, "reference">, [number, number, number]> = {
  front: [0, 0, 1],
  side: [1, 0, 0.06],
  "three-quarter": [0.6, 0.14, 0.79],
};

export function mountV2Viewer(host: HTMLElement, options: V2MountOptions = {}): V2ViewerApi {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  host.appendChild(renderer.domElement);
  renderer.domElement.style.width = "100%";
  renderer.domElement.style.height = "100%";
  renderer.domElement.style.display = "block";

  const model = createUltimaWeaponV2Model({ detail: "full" });
  const runtime = model.userData.sculptRuntime as SculptRuntime;
  const bounds = new THREE.Box3().setFromObject(model).getBoundingSphere(new THREE.Sphere());
  const visibleState = new Map<string, boolean>();
  for (const id of TOGGLEABLE) visibleState.set(id, true);

  const scene = new THREE.Scene();
  scene.add(model);

  // Harmless under the two review rigs — with `renderer.shadowMap.enabled` off these flags cost
  // nothing and change no pixel — so they are set once here rather than toggled per mode.
  model.traverse((object) => {
    if (object instanceof THREE.Mesh) {
      object.castShadow = true;
      object.receiveShadow = true;
    }
  });
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  let rig!: LookDevRig;
  let lights: THREE.Group | null = null;
  let environment!: THREE.Texture;
  let restoreMaterials: () => void = () => {};
  let blackBoxSpot: THREE.SpotLight | null = null;
  let blackBoxBaseIntensity = 0;

  /**
   * Swap the whole look-dev rig, tearing the previous one down completely first.
   *
   * Three things a rig owns leak if this is done piecemeal, and the black box owns all three:
   * the light group's own meshes (its floor lives there), the PMREM environment, and the material
   * overrides. Restoring the materials BEFORE building the next rig is what makes the deviation
   * reversible rather than cumulative — mode A's overrides must never become mode B's baseline.
   */
  const installRig = (mode: LightingMode) => {
    if (lights) {
      restoreMaterials();
      restoreMaterials = () => {};
      blackBoxSpot = null;
      blackBoxBaseIntensity = 0;
      scene.remove(lights);
      lights.traverse((object) => {
        if (!(object instanceof THREE.Mesh)) return;
        object.geometry.dispose();
        const used = Array.isArray(object.material) ? object.material : [object.material];
        for (const material of used) material.dispose();
      });
      environment.dispose();
    }
    rig = createUltimaWeaponV2LookDevLights(mode, bounds);
    lights = rig.lights;
    environment = rig.createEnvironment(renderer);
    restoreMaterials = applyMaterialOverrides(runtime.materials, rig.materialOverrides);
    if (mode === "blackBox") {
      lights.traverse((object) => {
        if (object instanceof THREE.SpotLight && !blackBoxSpot) {
          blackBoxSpot = object;
          blackBoxBaseIntensity = object.intensity;
        }
      });
    }
    scene.add(lights);
    scene.environment = environment;
    scene.environmentIntensity = rig.environmentIntensity;
    scene.background = rig.background;
    renderer.toneMapping = rig.toneMapping;
    renderer.toneMappingExposure = rig.toneMappingExposure;
    renderer.shadowMap.enabled = rig.shadows;
  };

  installRig("referenceLighting");

  // A read-only handle for tools/verify_v2_modes.mjs. It has to assert two things the public API
  // deliberately does not expose — that a mode switch leaves exactly one stage floor and one key
  // in the scene rather than accumulating them, and that the factory's material values come back
  // byte-identical after a round trip. Same arrangement as the harness's `window.__sculptRuntime`.
  (window as Window & { __v2Viewer?: unknown }).__v2Viewer = {
    scene,
    materials: runtime.materials,
  };

  const camera = new THREE.PerspectiveCamera(32, 1, 0.01, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.copy(bounds.center);

  // Distance the last automatic reframe chose; the difference against the camera's real
  // distance is the viewer's own zoom, carried through the next reframe.
  let autoDistance = 0;

  const fitDistance = (radius: number, margin: number) => {
    const vertical = THREE.MathUtils.degToRad(camera.fov) / 2;
    const horizontal = Math.atan(Math.tan(vertical) * camera.aspect);
    return (radius * margin) / Math.sin(Math.min(vertical, horizontal));
  };

  /** Bounds of what is actually visible — isolating a part must not keep the whole-weapon frame. */
  const visibleBounds = (): THREE.Sphere => {
    const box = new THREE.Box3();
    model.updateWorldMatrix(true, true);
    model.traverseVisible((object) => {
      if ((object as THREE.Mesh).isMesh) box.expandByObject(object);
    });
    if (box.isEmpty()) return bounds;
    return box.getBoundingSphere(new THREE.Sphere());
  };

  const reframe = (margin: number, direction?: readonly [number, number, number]) => {
    const current = visibleBounds();
    const offset = camera.position.clone().sub(controls.target);
    const userZoom =
      autoDistance > 0 && !direction
        ? THREE.MathUtils.clamp(offset.length() / autoDistance, 0.45, 2.5)
        : 1;
    const distance = fitDistance(current.radius, margin) * userZoom;
    const dir = direction ? new THREE.Vector3(...direction).normalize() : offset.normalize();
    controls.target.copy(current.center);
    camera.position.copy(current.center).addScaledVector(dir, distance);
    autoDistance = distance;
    controls.update();
  };

  const frame = (direction: readonly [number, number, number], margin: number) =>
    reframe(margin, direction);

  // The reference view is the orthographic artwork-match camera (18.13° roll), which
  // OrbitControls cannot express, so it gets its own camera and suspends the controls.
  let referenceCamera: THREE.Camera | null = null;
  let active: THREE.Camera = camera;

  const resize = () => {
    const width = host.clientWidth || 1;
    const height = host.clientHeight || 1;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    if (referenceCamera) {
      referenceCamera = createReviewCamera("artwork-match", model, width / height);
      if (active !== camera) active = referenceCamera;
    }
  };
  const observer = new ResizeObserver(resize);
  observer.observe(host);
  resize();
  frame(PRESET_DIRECTIONS["three-quarter"], 1.15);

  let spinning = false;
  let previous = performance.now();
  let handle = 0;
  const loop = () => {
    handle = requestAnimationFrame(loop);
    const now = performance.now();
    const delta = Math.min((now - previous) / 1000, 0.1);
    previous = now;
    if (spinning) model.userData.tick(delta);
    controls.update();
    renderer.render(scene, active);
  };
  loop();

  const inspector = createPartInspector({
    root: model,
    domElement: renderer.domElement,
    getCamera: () => active,
    controls,
    onChange: (selected, isolated) => options.onPartChange?.(selected, isolated),
  });

  let meshes = 0;
  let triangles = 0;
  model.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (!mesh.isMesh) return;
    meshes += 1;
    const index = mesh.geometry.getIndex();
    const position = mesh.geometry.getAttribute("position");
    triangles += (index ? index.count : position.count) / 3;
  });

  return {
    stats: { parts: runtime.nodes.size, meshes, triangles: Math.round(triangles) },
    setPreset: (preset) => {
      if (preset === "reference") {
        const width = host.clientWidth || 1;
        const height = host.clientHeight || 1;
        referenceCamera = createReviewCamera("artwork-match", model, width / height);
        active = referenceCamera;
        controls.enabled = false;
        spinning = false;
        model.rotation.y = 0;
        return;
      }
      active = camera;
      controls.enabled = true;
      frame(PRESET_DIRECTIONS[preset], preset === "side" ? 1.05 : 1.15);
    },
    setMode: installRig,
    setBlackBoxIntensity: (value: number) => {
      if (blackBoxSpot) blackBoxSpot.intensity = blackBoxBaseIntensity * value;
    },
    setExplode: (amount) => {
      runtime.setExplode(amount);
      if (active === camera) reframe(1.15);
    },
    setIsolation: (target) => {
      const keep = ISOLATION[target];
      for (const id of TOGGLEABLE) {
        const visible = keep === null || keep.includes(id);
        runtime.setPartVisible(id, visible);
        visibleState.set(id, visible);
      }
      if (active === camera) reframe(target === "none" ? 1.15 : 1.25);
    },
    setSpinning: (value) => {
      spinning = value;
      if (!value) model.rotation.y = 0;
      model.userData.setDisplayRotation?.(value);
    },
    parts: inspector.parts,
    selectPart: inspector.selectByName,
    setIsolate: inspector.setIsolate,
    setPartVisible: (id: string, visible: boolean) => {
      runtime.setPartVisible(id, visible);
      visibleState.set(id, visible);
      if (active === camera) reframe(1.15);
    },
    isPartVisible: (id: string) => visibleState.get(id) ?? true,
    toggleableParts: TOGGLEABLE,
    provenance: readProvenance(model),
    dispose: () => {
      inspector.dispose();
      cancelAnimationFrame(handle);
      observer.disconnect();
      controls.dispose();
      // Same teardown the mode switch does: the factory's materials outlive this viewer only if
      // something else holds them, but leaving them overridden would be a lie either way.
      restoreMaterials();
      lights?.traverse((object) => {
        if (!(object instanceof THREE.Mesh)) return;
        object.geometry.dispose();
        const used = Array.isArray(object.material) ? object.material : [object.material];
        for (const material of used) material.dispose();
      });
      environment.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    },
  };
}
