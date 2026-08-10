import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import {
  createCodexSolUltimaWeaponModel,
  type CodexSolPart,
  type CodexSolSculptRuntime,
} from "./createCodexSolUltimaWeaponModel";
import { createPartInspector, readProvenance, type PartInfo } from "../partInspector";

export type CodexSolPreset = "reference" | "front" | "side" | "three-quarter";
export type CodexSolIsolation = CodexSolPart["category"] | "none";
export type CodexSolLighting = "referenceLighting" | "neutralReview";

export type CodexSolMountOptions = {
  onPartChange?: (selected: PartInfo | null, isolated: boolean) => void;
};

export function mountCodexSolViewer(host: HTMLElement, options: CodexSolMountOptions = {}) {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true;
  renderer.domElement.style.cssText = "display:block;width:100%;height:100%";
  host.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const model = createCodexSolUltimaWeaponModel();
  const runtime = model.userData.sculptRuntime as CodexSolSculptRuntime;
  scene.add(model);

  const lights = new THREE.Group();
  scene.add(lights);
  const setMode = (mode: CodexSolLighting) => {
    lights.clear();
    const reference = mode === "referenceLighting";
    scene.background = new THREE.Color(reference ? 0xffffff : 0x16131f);
    lights.add(
      new THREE.HemisphereLight(reference ? 0xf4f1ff : 0xaea4d8, 0x17101f, reference ? 2.1 : 1.25),
    );
    const key = new THREE.DirectionalLight(reference ? 0xffffff : 0xd8d0ff, reference ? 3.2 : 2.2);
    key.position.set(-4, 7, 6);
    key.castShadow = true;
    lights.add(key);
    const rim = new THREE.DirectionalLight(0xc52cff, reference ? 1.1 : 2.4);
    rim.position.set(4, 2, -5);
    lights.add(rim);
  };
  setMode("referenceLighting");
  if (new URLSearchParams(window.location.search).get("silhouette") === "1") {
    scene.background = new THREE.Color(0xffffff);
    model.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (mesh.isMesh)
        mesh.material = new THREE.MeshBasicMaterial({ color: 0x15151a, side: THREE.DoubleSide });
    });
  }

  const camera = new THREE.PerspectiveCamera(30, 1, 0.01, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  let autoDistance = 0;
  const visibleBounds = () => {
    const box = new THREE.Box3();
    model.updateWorldMatrix(true, true);
    model.traverseVisible((object) => {
      if ((object as THREE.Mesh).isMesh) box.expandByObject(object);
    });
    return box;
  };
  const frame = (direction?: readonly [number, number, number], margin = 1.14) => {
    const box = visibleBounds();
    const center = box.getCenter(new THREE.Vector3());
    const halfV = THREE.MathUtils.degToRad(camera.fov) / 2;
    const halfH = Math.atan(Math.tan(halfV) * camera.aspect);
    const offset = camera.position.clone().sub(controls.target);
    const zoom =
      autoDistance && !direction
        ? THREE.MathUtils.clamp(offset.length() / autoDistance, 0.45, 2.5)
        : 1;
    const vector = direction ? new THREE.Vector3(...direction).normalize() : offset.normalize();
    const right = new THREE.Vector3().crossVectors(new THREE.Vector3(0, 1, 0), vector).normalize();
    const up = new THREE.Vector3().crossVectors(vector, right).normalize();
    let halfWidth = 0;
    let halfHeight = 0;
    let halfDepth = 0;
    for (const x of [box.min.x, box.max.x])
      for (const y of [box.min.y, box.max.y])
        for (const z of [box.min.z, box.max.z]) {
          const corner = new THREE.Vector3(x, y, z).sub(center);
          halfWidth = Math.max(halfWidth, Math.abs(corner.dot(right)));
          halfHeight = Math.max(halfHeight, Math.abs(corner.dot(up)));
          halfDepth = Math.max(halfDepth, Math.abs(corner.dot(vector)));
        }
    const distance =
      (Math.max(halfWidth / Math.tan(halfH), halfHeight / Math.tan(halfV)) * margin + halfDepth) *
      zoom;
    controls.target.copy(center);
    camera.position.copy(center).addScaledVector(vector, distance);
    autoDistance = distance;
    controls.update();
  };

  const directions: Record<Exclude<CodexSolPreset, "reference">, [number, number, number]> = {
    front: [0, 0, 1],
    side: [1, 0, 0.08],
    "three-quarter": [0.62, 0.16, 0.77],
  };
  const frameReference = () => {
    const target = new THREE.Vector3(-0.59, 2.76, 0);
    const direction = new THREE.Vector3(0.08, 0.03, 1).normalize();
    const distance = 3.78 / Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
    controls.target.copy(target);
    camera.position.copy(target).addScaledVector(direction, distance);
    autoDistance = distance;
    controls.update();
  };
  frame(directions["three-quarter"]);

  const resize = () => {
    const width = host.clientWidth || 1;
    const height = host.clientHeight || 1;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  };
  const observer = new ResizeObserver(resize);
  observer.observe(host);
  resize();

  let spinning = false;
  let handle = 0;
  let previous = performance.now();
  const loop = () => {
    handle = requestAnimationFrame(loop);
    const now = performance.now();
    if (spinning) model.rotation.y += Math.min((now - previous) / 1000, 0.1) * 0.45;
    previous = now;
    controls.update();
    renderer.render(scene, camera);
  };
  loop();

  const inspector = createPartInspector({
    root: model,
    domElement: renderer.domElement,
    getCamera: () => camera,
    controls,
    onChange: (selected, isolated) => options.onPartChange?.(selected, isolated),
  });

  return {
    stats: runtime.stats,
    parts: inspector.parts,
    selectPart: inspector.selectByName,
    setIsolate: inspector.setIsolate,
    provenance: readProvenance(model),
    setPreset(preset: CodexSolPreset) {
      model.rotation.set(0, 0, preset === "reference" ? THREE.MathUtils.degToRad(17.67) : 0);
      if (preset === "reference") frameReference();
      else frame(directions[preset], preset === "side" ? 1.06 : 1.14);
      if (preset === "reference") spinning = false;
    },
    setMode,
    setExplode(amount: number) {
      runtime.setExplode(amount);
      frame();
    },
    setIsolation(target: CodexSolIsolation) {
      for (const part of runtime.parts)
        part.object.visible = target === "none" || part.category === target;
      frame(undefined, target === "none" ? 1.14 : 1.3);
    },
    setSpinning(value: boolean) {
      spinning = value;
      if (!value) model.rotation.y = 0;
    },
    dispose() {
      inspector.dispose();
      cancelAnimationFrame(handle);
      observer.disconnect();
      controls.dispose();
      model.traverse((object) => {
        const mesh = object as THREE.Mesh;
        if (!mesh.isMesh) return;
        mesh.geometry.dispose();
        const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
        for (const material of materials) material.dispose();
      });
      renderer.dispose();
      renderer.domElement.remove();
    },
  };
}
