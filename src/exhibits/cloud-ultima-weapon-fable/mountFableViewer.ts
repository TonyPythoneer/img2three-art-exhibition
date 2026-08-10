import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import {
  createCloudUltimaWeaponFableModel,
  type SculptRuntime,
} from "./createCloudUltimaWeaponFableModel";
import {
  createCloudUltimaWeaponFableLookDevLights,
  createReviewCamera,
  type LightingMode,
} from "./createCloudUltimaWeaponFableLookDev";

/**
 * Client-only mount for the Fable 5 xhigh rerun on the exhibit page. Same contract as
 * mountUltimaViewer.ts (the Opus run): everything WebGL lives behind this dynamic import
 * so vite-ssg never touches a renderer during static generation.
 *
 * The two runs differ in model geometry, look-dev rig and reference camera; the viewer
 * surface is deliberately identical — explode slider and per-assembly isolation walk the
 * same `sculptRuntime` the review harness and the gates measured.
 */

import { createPartInspector, readProvenance, type PartInfo } from "../partInspector";

export type ViewerPreset = "reference" | "front" | "side" | "three-quarter";

export type IsolationTarget = "none" | "shell" | "core" | "spine" | "guard" | "handle";

export type FableMountOptions = {
  onPartChange?: (selected: PartInfo | null, isolated: boolean) => void;
};

export type FableViewerApi = {
  setPreset: (preset: ViewerPreset) => void;
  setMode: (mode: LightingMode) => void;
  setExplode: (amount: number) => void;
  setIsolation: (target: IsolationTarget) => void;
  setSpinning: (spinning: boolean) => void;
  stats: { parts: number; meshes: number; triangles: number };
  /** Every selectable component, in model tree order. */
  parts: PartInfo[];
  selectPart: (name: string | null) => void;
  setIsolate: (on: boolean) => void;
  provenance?: string;
  dispose: () => void;
};

/** Which top-level nodes stay visible for each isolation target. */
const ISOLATION: Record<IsolationTarget, string[] | null> = {
  none: null,
  shell: ["outerBladeShell"],
  core: ["purpleEnergyCore"],
  spine: ["magentaCentralSpine"],
  guard: ["guardAssembly"],
  handle: ["handleAssembly"],
};

const TOGGLEABLE = [
  "outerBladeShell",
  "purpleEnergyCore",
  "magentaCentralSpine",
  "bladeMount",
  "guardAssembly",
  "handleAssembly",
];

// Camera positions as a direction from the model centre; distance comes from the bounding
// sphere so the framing survives any change to the global scale.
const PRESET_DIRECTIONS: Record<Exclude<ViewerPreset, "reference">, [number, number, number]> = {
  front: [0, 0, 1],
  side: [1, 0, 0.08],
  "three-quarter": [0.62, 0.16, 0.77],
};

export function mountFableViewer(
  host: HTMLElement,
  options: FableMountOptions = {},
): FableViewerApi {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  host.appendChild(renderer.domElement);
  renderer.domElement.style.width = "100%";
  renderer.domElement.style.height = "100%";
  renderer.domElement.style.display = "block";

  const model = createCloudUltimaWeaponFableModel({ detail: "full" });
  const runtime = model.userData.sculptRuntime as SculptRuntime;
  const bounds = new THREE.Box3().setFromObject(model).getBoundingSphere(new THREE.Sphere());

  const scene = new THREE.Scene();
  scene.add(model);

  let rig = createCloudUltimaWeaponFableLookDevLights("referenceLighting");
  let lights = rig.lights;
  let environment = rig.createEnvironment(renderer);
  scene.add(lights);
  scene.environment = environment;
  scene.environmentIntensity = rig.environmentIntensity;
  scene.background = rig.background;
  renderer.toneMapping = rig.toneMapping;
  renderer.toneMappingExposure = rig.toneMappingExposure;

  const camera = new THREE.PerspectiveCamera(32, 1, 0.01, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.copy(bounds.center);

  // Distance the last automatic reframe chose. Any difference between this and the camera's
  // real distance is the viewer's own zoom, and it is carried through the next reframe so
  // dragging the explode slider does not throw away a zoom they set by hand.
  let autoDistance = 0;

  const fitDistance = (radius: number, margin: number) => {
    const vertical = THREE.MathUtils.degToRad(camera.fov) / 2;
    const horizontal = Math.atan(Math.tan(vertical) * camera.aspect);
    return (radius * margin) / Math.sin(Math.min(vertical, horizontal));
  };

  /**
   * Bounds of what is actually on screen. `Box3.setFromObject` walks hidden children too, so
   * isolating a part would otherwise leave the frame sized for the whole weapon.
   */
  const visibleBounds = (): THREE.Sphere => {
    const box = new THREE.Box3();
    model.updateWorldMatrix(true, true);
    model.traverseVisible((object) => {
      if ((object as THREE.Mesh).isMesh) box.expandByObject(object);
    });
    if (box.isEmpty()) return bounds;
    return box.getBoundingSphere(new THREE.Sphere());
  };

  /** Reframe on the CURRENT visible bounds — they grow as the explode separates the parts. */
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

  // The reference view is an exact orthographic reproduction of the reference frame
  // (measured 17.67° roll), which OrbitControls cannot express. It gets its own camera
  // and the controls are suspended while it is active.
  let referenceCamera: THREE.Camera | null = null;
  let active: THREE.Camera = camera;

  const resize = () => {
    const width = host.clientWidth || 1;
    const height = host.clientHeight || 1;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    if (referenceCamera)
      referenceCamera = createReviewCamera(
        "reference-matched-three-quarter",
        model,
        width / height,
      );
    if (active !== camera && referenceCamera) active = referenceCamera;
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
        referenceCamera = createReviewCamera(
          "reference-matched-three-quarter",
          model,
          width / height,
        );
        active = referenceCamera;
        controls.enabled = false;
        // Spinning under a fixed reference camera would defeat the point of the view.
        spinning = false;
        model.rotation.y = 0;
        return;
      }
      active = camera;
      controls.enabled = true;
      frame(PRESET_DIRECTIONS[preset], preset === "side" ? 1.05 : 1.15);
    },
    setMode: (mode) => {
      scene.remove(lights);
      environment.dispose();
      rig = createCloudUltimaWeaponFableLookDevLights(mode);
      lights = rig.lights;
      environment = rig.createEnvironment(renderer);
      scene.add(lights);
      scene.environment = environment;
      scene.environmentIntensity = rig.environmentIntensity;
      scene.background = rig.background;
      renderer.toneMapping = rig.toneMapping;
      renderer.toneMappingExposure = rig.toneMappingExposure;
    },
    setExplode: (amount) => {
      runtime.setExplode(amount);
      // Separating the parts both grows and shifts the layout, so the frame has to follow
      // the new bounds — pulling back alone would leave the blade above the viewport.
      if (active === camera) reframe(1.15);
    },
    setIsolation: (target) => {
      const keep = ISOLATION[target];
      for (const id of TOGGLEABLE) {
        runtime.setPartVisible(id, keep === null || keep.includes(id));
      }
      // Hiding everything but the guard leaves a much smaller object; without a reframe it
      // would sit as a speck in a frame sized for the whole weapon.
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
    provenance: readProvenance(model),
    dispose: () => {
      inspector.dispose();
      cancelAnimationFrame(handle);
      observer.disconnect();
      controls.dispose();
      environment.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    },
  };
}
