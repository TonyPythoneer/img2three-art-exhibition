import * as THREE from "three";
import { ArcballControls } from "three/examples/jsm/controls/ArcballControls.js";
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
  /** Put the weapon back on its rest pose and the camera back on the default framing. */
  resetView: () => void;
  /** Show or hide the three arcball rotation circles. Off still leaves the drag working. */
  setGizmosVisible: (visible: boolean) => void;
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
  // ArcballControls rather than OrbitControls for the three plane gizmos: dragging the red,
  // green or blue circle rotates in the YZ, XZ or XY plane respectively, which is the
  // constrained rotation this exhibit gets reviewed with. The third argument is what draws
  // them — without a scene ArcballControls is gizmo-less.
  // The cast covers `target`, which @types/three 0.185 omits even though the runtime class has
  // had it since it shipped.
  const controls = new ArcballControls(camera, renderer.domElement, scene) as ArcballControls & {
    target: THREE.Vector3;
  };
  controls.target.copy(bounds.center);

  // Pan hands the SAME translation matrix to camera and gizmos — ArcballControls.js:2230
  // `setTransformationMatrices(this._m4_1, this._m4_1)`, both applied at :1553-1574 — so the three
  // circles slide with the screen while the weapon stays in world space, and pan never touches
  // `target` (only reset/setCamera/its own update read it). Pin the gizmo group back onto `target`
  // after every control change: `target` is the visible-bounds centre that reframe() writes, so the
  // circles keep marking the weapon's own rotation centre through pan, preset, explode and isolate.
  // Writing `matrix` too is what carries the correction into the next drag — updateMatrixState()
  // (:2856) seeds the drag from `_gizmos.matrix`, not from `position`.
  const gizmos = (controls as unknown as { _gizmos: THREE.Object3D })._gizmos;
  controls.addEventListener("change", () => {
    if (gizmos.position.equals(controls.target)) return;
    gizmos.position.copy(controls.target);
    gizmos.updateMatrix();
  });

  // It caches the camera matrix on construction and never re-reads it, so every place that moves
  // the camera by hand (reframe, the part inspector's dolly-to-part) has to resync. Those call
  // sites all already end in `update()`, which ArcballControls itself never calls internally and
  // does not need per frame — so `update` is exactly the resync hook.
  controls.update = () => controls.setCamera(camera);

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

  // --------------------------------------------------------------- drag = turn the model
  //
  // A left drag turns the WEAPON, not the camera. The three circles are drawn around the weapon,
  // so they read as a handle on the weapon; ArcballControls' own left-button ROTATE spends them on
  // the camera instead, and orbiting a fixed model under a fixed light changes not one pixel of
  // its shading — the pool and the shadow swing past while the lit face stays the lit face. That
  // is what "the light rotates with the model" looks like from the outside, and the light is not
  // what is wrong. Turning the model is: the rig stays where it is and the key sweeps across the
  // faces.
  //
  // So the left button is taken off the controls and the drag below gets it. Everything else
  // ArcballControls binds is left alone — wheel zoom, middle zoom, right-drag pan, ctrl+left pan —
  // which is why `enabled` stays on and the circles stay visible.
  controls.unsetMouseAction(0);

  let turnLast: { x: number; y: number } | null = null;
  /** Radians per pixel of drag. A full turn takes roughly the width of the stage. */
  const TURN_RATE = 0.009;
  const turnRight = new THREE.Vector3();
  const turnStep = new THREE.Quaternion();
  const turnTilt = new THREE.Quaternion();

  const onTurnDown = (event: PointerEvent) => {
    // ctrl+left is the controls' own pan, and the artwork-match camera is a fixed pose.
    if (event.button !== 0 || event.ctrlKey || event.metaKey || active !== camera) return;
    // A hand on the model outranks the reset still gliding home.
    reset = null;
    turnLast = { x: event.clientX, y: event.clientY };
    renderer.domElement.setPointerCapture(event.pointerId);
  };
  const onTurnMove = (event: PointerEvent) => {
    if (!turnLast) return;
    const dx = event.clientX - turnLast.x;
    const dy = event.clientY - turnLast.y;
    turnLast = { x: event.clientX, y: event.clientY };
    // Horizontal drag turns about the stage's own vertical, vertical drag about the camera's
    // right — so the weapon follows the pointer whatever angle it is being viewed from.
    turnRight.setFromMatrixColumn(active.matrixWorld, 0).normalize();
    turnStep.setFromAxisAngle(THREE.Object3D.DEFAULT_UP, dx * TURN_RATE);
    turnTilt.setFromAxisAngle(turnRight, dy * TURN_RATE);
    // premultiply, not multiply: the step is applied in world space, so a horizontal drag stays
    // horizontal no matter how far the model has already been turned.
    model.quaternion.premultiply(turnStep.multiply(turnTilt));
  };
  const onTurnUp = () => {
    turnLast = null;
  };

  /** Camera controls and their circles are off only under the fixed artwork-match camera. */
  let gizmosWanted = true;
  const syncControls = () => {
    const on = active === camera;
    controls.enabled = on;
    controls.setGizmosVisible(on && gizmosWanted);
  };
  renderer.domElement.addEventListener("pointerdown", onTurnDown);
  renderer.domElement.addEventListener("pointermove", onTurnMove);
  renderer.domElement.addEventListener("pointerup", onTurnUp);
  renderer.domElement.addEventListener("pointercancel", onTurnUp);

  // ------------------------------------------------------------- rotate in place
  //
  // The model's own origin is NOT its centre: the bounding centre sits 2.746 above it, 54% of the
  // 5.12 bounding radius. Rotating the root therefore turns the weapon about a point below itself
  // — measured at 1.432 world units of centre travel for a 30 degree tilt and 2.747 for 60 — so a
  // drag swings it across the stage instead of turning it on the spot, and the three arcball
  // circles, which are drawn on the centre, stop marking where the rotation actually happens.
  //
  // Holding the centre still is one line of algebra. Its world position is `position + R·centre`,
  // so pinning it at `centre` means `position = centre − R·centre`. Identity leaves the position at
  // zero and so does a pure Y spin (the centre is on the Y axis), so this only moves anything where
  // it has to. Called every frame rather than at each mutation site: Auto Rotate, the drag and the
  // preset resets all write the rotation, and one call covers the three of them.
  const spinPivot = bounds.center.clone();
  const spunPivot = new THREE.Vector3();
  const pinCentre = () => {
    model.position.copy(spinPivot).sub(spunPivot.copy(spinPivot).applyQuaternion(model.quaternion));
    model.position.y += explodeLift;
  };

  // Explode pushes the lowest parts straight down, and the stage floor sits only just clear of the
  // pommel, so at full separation the bottom of the fan ends up under it. The floor belongs to the
  // light rig (it is what catches the pool), so the weapon moves instead of the stage: measure how
  // far the exploded bounds break the plane and lift the whole model by exactly that. Zero at
  // explode 0, which leaves every review render and gate untouched.
  const FLOOR_CLEARANCE = bounds.radius * 0.03;
  const liftBox = new THREE.Box3();
  const floorProbe = new THREE.Vector3();
  let explodeLift = 0;

  const clearFloor = () => {
    const floor = lights?.getObjectByName("stageFloor");
    if (!floor) return;
    explodeLift = 0;
    pinCentre();
    model.updateMatrixWorld(true);
    const floorY = floor.getWorldPosition(floorProbe).y;
    const lowest = liftBox.setFromObject(model).min.y;
    explodeLift = Math.max(0, floorY + FLOOR_CLEARANCE - lowest);
    pinCentre();
    model.updateMatrixWorld(true);
  };

  /** Radians per second of Auto Rotate. */
  const SPIN_RATE = 0.45;

  /**
   * Reset flies home rather than cutting there: a cut leaves you working out what just happened,
   * and the whole point of the button is to re-orient. Pose and camera travel together on one
   * eased clock — two clocks would arrive at different times and read as two separate moves.
   */
  const RESET_MS = 800;
  const RESET_HOME = new THREE.Quaternion();
  let reset: {
    t: number;
    fromQuaternion: THREE.Quaternion;
    fromCamera: THREE.Vector3;
    fromTarget: THREE.Vector3;
    toCamera: THREE.Vector3;
    toTarget: THREE.Vector3;
  } | null = null;

  let spinning = false;
  let previous = performance.now();
  let handle = 0;
  const loop = () => {
    handle = requestAnimationFrame(loop);
    const now = performance.now();
    const delta = Math.min((now - previous) / 1000, 0.1);
    previous = now;
    // Composed the same way the drag is, rather than through the factory's `userData.tick`: that
    // writes an absolute `rotation.y`, which would wipe out whatever the pointer had turned. As a
    // premultiplied world-Y step the two simply add, so a drag mid-spin nudges the pose instead of
    // fighting for it and neither control has to switch the other off.
    if (spinning) {
      turnStep.setFromAxisAngle(THREE.Object3D.DEFAULT_UP, delta * SPIN_RATE);
      model.quaternion.premultiply(turnStep);
    }
    if (reset) {
      reset.t = Math.min(1, reset.t + (delta * 1000) / RESET_MS);
      // smoothstep: leaves and arrives at zero speed, which is the whole "glides home" of it.
      const k = reset.t * reset.t * (3 - 2 * reset.t);
      model.quaternion.slerpQuaternions(reset.fromQuaternion, RESET_HOME, k);
      camera.position.lerpVectors(reset.fromCamera, reset.toCamera, k);
      controls.target.lerpVectors(reset.fromTarget, reset.toTarget, k);
      controls.update();
      if (reset.t >= 1) reset = null;
    }
    pinCentre();
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
        spinning = false;
        // Full reset, not just the spin: a tumbled weapon is not the artwork's pose, and this
        // camera exists precisely to reproduce that pose. It happens BEFORE the solve because the
        // solve reads the model's world bounds — run off a tumbled pose it frames the wrong box.
        model.rotation.set(0, 0, 0);
        pinCentre();
        const width = host.clientWidth || 1;
        const height = host.clientHeight || 1;
        referenceCamera = createReviewCamera("artwork-match", model, width / height);
        active = referenceCamera;
        syncControls();
        return;
      }
      active = camera;
      syncControls();
      frame(PRESET_DIRECTIONS[preset], preset === "side" ? 1.05 : 1.15);
    },
    setMode: installRig,
    setBlackBoxIntensity: (value: number) => {
      if (blackBoxSpot) blackBoxSpot.intensity = blackBoxBaseIntensity * value;
    },
    setExplode: (amount) => {
      runtime.setExplode(amount);
      clearFloor();
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
    // Stops where it is rather than snapping back to zero: the pose may be one the pointer turned
    // to, and throwing that away on a pause is not what a pause means. "Reference" is the reset.
    setSpinning: (value) => {
      spinning = value;
    },
    // Everything a hand can move: the pose the drag turned, the spin that would walk away from it
    // again, and the camera's own rotate/zoom/pan.
    resetView: () => {
      spinning = false;
      active = camera;
      syncControls();
      // The destination is solved from the RESTED pose, held for exactly as long as the solve takes.
      // `visibleBounds()` reads the model's world box, and mid-flight that box is whatever the
      // animation happens to be passing through — so aiming at it from here would aim at a moving
      // target. Distance comes from a DIRECTION solve, which is what drops the carried-over zoom.
      const pose = model.quaternion.clone();
      model.quaternion.copy(RESET_HOME);
      pinCentre();
      const home = visibleBounds();
      model.quaternion.copy(pose);
      pinCentre();

      autoDistance = fitDistance(home.radius, 1.15);
      reset = {
        t: 0,
        fromQuaternion: pose,
        fromCamera: camera.position.clone(),
        fromTarget: controls.target.clone(),
        toTarget: home.center.clone(),
        toCamera: home.center
          .clone()
          .addScaledVector(
            new THREE.Vector3(...PRESET_DIRECTIONS["three-quarter"]).normalize(),
            autoDistance,
          ),
      };
    },
    setGizmosVisible: (value) => {
      gizmosWanted = value;
      syncControls();
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
      renderer.domElement.removeEventListener("pointerdown", onTurnDown);
      renderer.domElement.removeEventListener("pointermove", onTurnMove);
      renderer.domElement.removeEventListener("pointerup", onTurnUp);
      renderer.domElement.removeEventListener("pointercancel", onTurnUp);
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
