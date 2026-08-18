import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

import { COLORS } from "./colors";
import { createSigmaVirusHead } from "./createSigmaVirusHead";
import { createPartInspector, readProvenance, type PartInfo } from "../partInspector";

/**
 * Client-only mount for the MMX2 Sigma virus head. Same viewer contract as the other exhibits,
 * so `ExhibitStage` drives it without special-casing — everything WebGL lives behind this
 * module so vite-ssg never evaluates a renderer in node.
 *
 * There is no lighting-mode control here on purpose. The reference has exactly ONE material
 * code (flat emissive wireframe, no PBR response anywhere on the sheet), so a rig switcher
 * would be three buttons that all render the same thing.
 */

export type SigmaPreset = "front" | "side" | "three-quarter" | "top";

export type SigmaViewerApi = {
  setPreset: (preset: SigmaPreset) => void;
  setSpinning: (spinning: boolean) => void;
  /**
   * Yaw the head about its own vertical axis, in degrees, from the front view. Exists for the
   * yaw-sweep gate: the reference's own width sweep across 87 pure-yaw frames is the only
   * pose-free measurement of the head's depth, and the model has to reproduce its range.
   */
  setYaw: (degrees: number) => void;
  setExplode: (amount: number) => void;
  resetView: () => void;
  parts: PartInfo[];
  selectPart: (name: string | null) => void;
  setIsolate: (on: boolean) => void;
  setPartVisible: (id: string, visible: boolean) => void;
  toggleableParts: string[];
  stats: { meshes: number; triangles: number };
  provenance?: string;
  dispose: () => void;
};

const PRESET_DIRECTIONS: Record<SigmaPreset, THREE.Vector3> = {
  front: new THREE.Vector3(0, 0, 1),
  side: new THREE.Vector3(1, 0, 0),
  "three-quarter": new THREE.Vector3(0.8, 0.28, 1),
  top: new THREE.Vector3(0, 1, 0.001),
};

export function mountSigmaVirusViewer(
  host: HTMLElement,
  opts: { onPartChange?: (selected: PartInfo | null, isolated: boolean) => void } = {},
): SigmaViewerApi {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(COLORS.ground);

  const model = createSigmaVirusHead();
  scene.add(model);

  // Enough light to separate the facets of the dark fill without washing out the edges, which
  // are the actual subject here and are toneMapped: false so they stay at full green.
  scene.add(new THREE.AmbientLight(0xffffff, 0.35));
  const key = new THREE.DirectionalLight(0xffffff, 0.9);
  key.position.set(1.2, 1.6, 2.0);
  scene.add(key);

  const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 100);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  host.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  const bounds = new THREE.Box3().setFromObject(model);
  const size = bounds.getSize(new THREE.Vector3()).length();
  const centre = bounds.getCenter(new THREE.Vector3());

  const frame = (dir: THREE.Vector3, pad = 1.5) => {
    const d = dir
      .clone()
      .normalize()
      .multiplyScalar(size * pad);
    camera.position.copy(centre).add(d);
    controls.target.copy(centre);
    controls.update();
  };

  const resize = () => {
    const w = host.clientWidth || 1;
    const h = host.clientHeight || 1;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };
  const ro = new ResizeObserver(resize);
  ro.observe(host);
  resize();
  frame(PRESET_DIRECTIONS["three-quarter"]);

  const inspector = createPartInspector({
    root: model,
    domElement: renderer.domElement,
    getCamera: () => camera,
    controls,
    onChange: (sel, iso) => opts.onPartChange?.(sel, iso),
  });

  // Rest positions captured before anything moves, so explode is always relative to the
  // assembled pose rather than to wherever the last explode left each part.
  const rest = new Map<THREE.Object3D, THREE.Vector3>();
  for (const child of model.children) rest.set(child, child.position.clone());

  let spinning = false;
  let raf = 0;
  let frames = 0;
  const tick = () => {
    raf = requestAnimationFrame(tick);
    if (spinning) model.rotation.y += 0.006;
    controls.update();
    renderer.render(scene, camera);
    frames += 1;
    // The capture harness waits on this instead of a timeout, so a screenshot cannot catch an
    // empty canvas on a slow first frame.
    if (frames === 3) (window as unknown as { __renderReady?: boolean }).__renderReady = true;
  };
  tick();

  let meshes = 0;
  let triangles = 0;
  model.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    meshes += 1;
    const g = m.geometry;
    triangles += (g.index ? g.index.count : (g.attributes.position?.count ?? 0)) / 3;
  });

  const toggleable = model.children.map((c) => c.name).filter(Boolean);

  const api: SigmaViewerApi = {
    setPreset: (preset) => {
      spinning = false;
      model.rotation.set(0, 0, 0);
      frame(PRESET_DIRECTIONS[preset], preset === "top" ? 1.7 : 1.5);
    },
    setSpinning: (value) => {
      spinning = value;
    },
    setYaw: (degrees) => {
      spinning = false;
      model.rotation.set(0, (degrees * Math.PI) / 180, 0);
    },
    // Separate by SCALING the layout about the model centre. Pushing every part the same
    // distance translates the arrangement without opening any gap between neighbours.
    setExplode: (amount) => {
      for (const [child, home] of rest) {
        child.position.copy(home).multiplyScalar(1 + amount * 2.2);
      }
    },
    resetView: () => {
      spinning = false;
      model.rotation.set(0, 0, 0);
      frame(PRESET_DIRECTIONS["three-quarter"]);
    },
    get parts() {
      return inspector.parts;
    },
    selectPart: inspector.selectByName,
    setIsolate: inspector.setIsolate,
    setPartVisible: (id, visible) => {
      const target = model.getObjectByName(id);
      if (target) target.visible = visible;
    },
    toggleableParts: toggleable,
    stats: { meshes, triangles: Math.round(triangles) },
    provenance: readProvenance(model),
    dispose: () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      inspector.dispose();
      controls.dispose();
      renderer.dispose();
      scene.traverse((o) => {
        const m = o as THREE.Mesh;
        if (m.geometry) m.geometry.dispose();
        const mat = (o as THREE.Mesh).material;
        if (Array.isArray(mat)) mat.forEach((x) => x.dispose());
        else mat?.dispose();
      });
      renderer.domElement.remove();
      delete (window as unknown as { __sigmaViewer?: SigmaViewerApi }).__sigmaViewer;
    },
  };

  // The capture harness drives this instead of clicking the page's chips: a chip lives inside a
  // collapsible panel, so a DOM-driven capture silently depends on the panel's open state and
  // on the button copy. Handing it the API makes the render evidence independent of both.
  (window as unknown as { __sigmaViewer?: SigmaViewerApi }).__sigmaViewer = api;
  return api;
}
