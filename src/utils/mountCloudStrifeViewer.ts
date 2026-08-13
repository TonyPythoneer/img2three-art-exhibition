import * as THREE from "three";
import { ArcballControls } from "three/examples/jsm/controls/ArcballControls.js";
import { createUltimaWeaponV2LookDevLights } from "./ultimaWeaponV2/createUltimaWeaponV2LookDev";
import { createPartInspector, readProvenance, type StageViewer } from "./partInspector";
import { STAGE1_PARTS } from "./cloudStrifeFigure/parts";

/**
 * The FF7 Cloud Strife polygon figure's viewer.
 *
 * Three jobs in one mount, because src/pages/ is the URL surface and one extra `.vue`
 * is one extra junk route:
 *
 *   mode "assembled"  the figure, once Stage 1B has built one
 *   mode "gallery"    every Stage 1 part laid out in a row, each turned independently
 *   `part` + `view`   ONE part from a fixed orthographic camera, and a
 *                     `window.__renderReady` / `__partInfo` contract for headless
 *                     capture — this is what the deleted head-capture-harness.vue did,
 *                     moved here so the review stage is the exhibit route itself.
 */

/** Figure frame: +X is the figure's LEFT, +Z its front (§1.2). */
export const VIEW_DIRS: Record<string, [number, number, number]> = {
  front: [0, 0, 1],
  back: [0, 0, -1],
  left: [1, 0, 0],
  right: [-1, 0, 0],
  /** three-quarter from the figure's right-front */
  orbit: [-0.6, 0.14, 0.79],
  /** the opposite three-quarter — the second angle the multi-angle gate needs */
  orbit2: [0.6, 0.14, -0.79],
  /**
   * Near-top-down. The two orbits above sit at y=0.14 and read a flat part almost edge-on,
   * which is fine for the degenerate-view check and useless for judging a PLAN shape. The
   * sole's L/W, toe taper and end chamfer are adopted, not measured, and this is the only
   * view that can falsify them (§5.2). Tilted 10 degrees off vertical on purpose: a camera
   * looking straight down its own up vector produces a degenerate lookAt and a NaN frame.
   */
  plan: [0, 0.985, 0.174],
};

export type CloudMountOptions = {
  /** Overrides everything below; used by tests and by the home hero. */
  model?: () => THREE.Group;
  mode?: "assembled" | "gallery";
  /** Show one part alone, by its §2 name. */
  part?: string;
  /** A key of VIEW_DIRS. Set it and the camera goes fixed + orthographic. */
  view?: string;
};

export type { StageViewer };

/** Every mount option that changes what is built, as one string ExhibitStage can watch. */
export const cloudVariantKey = (o: CloudMountOptions): string =>
  [o.mode ?? "assembled", o.part ?? "", o.view ?? ""].join("|");

/**
 * Lay the parts out along X in their registry order, spaced by their own widths.
 *
 * Each part keeps its own group so `partInspector` still sees one named node per part,
 * and the turn-drag below rotates the picked part rather than the row.
 */
function buildGallery(): THREE.Group {
  const row = new THREE.Group();
  row.name = "cloudStrifeFigurePartsGallery";
  const GAP = 0.25;
  let cursor = 0;
  const widths: number[] = [];
  const built = STAGE1_PARTS.map((entry) => {
    const g = entry.build();
    const size = new THREE.Box3().setFromObject(g).getSize(new THREE.Vector3());
    widths.push(Math.max(size.x, 1e-3));
    return g;
  });
  const total = widths.reduce((a, b) => a + b, 0) + GAP * Math.max(0, widths.length - 1);
  cursor = -total / 2;
  built.forEach((g, i) => {
    const holder = new THREE.Group();
    // Named for the part's §2 GROUP, not `<part>Slot`: partInspector reports a part's
    // module as its nearest named ancestor, so a made-up slot name would make §5.6's
    // attribution check read "soleLSlot" where the table says "legLeft".
    holder.name = STAGE1_PARTS[i]!.module;
    holder.position.x = cursor + widths[i]! / 2;
    holder.add(g);
    row.add(holder);
    cursor += widths[i]! + GAP;
  });
  row.userData.provenance =
    STAGE1_PARTS.length === 0
      ? "Stage 0 complete; Stage 1 has built 0 of 23 parts, so the gallery is empty by construction"
      : `Stage 1 gallery: ${STAGE1_PARTS.length} of 23 parts built`;
  return row;
}

function buildAssembled(): THREE.Group {
  const g = new THREE.Group();
  g.name = "cloudStrifeFigure";
  g.userData.provenance =
    "Stage 1B has not run: no assembly exists yet. Switch to the parts gallery.";
  return g;
}

export function mountCloudStrifeViewer(
  host: HTMLElement,
  options: CloudMountOptions = {},
): StageViewer {
  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    preserveDrawingBuffer: true,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  host.appendChild(renderer.domElement);
  renderer.domElement.style.width = "100%";
  renderer.domElement.style.height = "100%";
  renderer.domElement.style.display = "block";

  const buildModel = (): THREE.Group => {
    if (options.model) return options.model();
    if (options.part) {
      const entry = STAGE1_PARTS.find((p) => p.name === options.part);
      const g = new THREE.Group();
      g.name = "cloudStrifeFigurePart";
      if (entry) {
        // Wrapped in its §2 group node even when it stands alone. partInspector derives a
        // part's module from its nearest named ancestor, so a bare part reports module
        // null and §5.6 ("the attribution matches the table") could never be checked in
        // the very harness the review runs in.
        const module = new THREE.Group();
        module.name = entry.module;
        module.add(entry.build());
        g.add(module);
      } else g.userData.provenance = `no part named "${options.part}" is built yet`;
      return g;
    }
    return options.mode === "gallery" ? buildGallery() : buildAssembled();
  };

  const model = buildModel();
  const scene = new THREE.Scene();
  scene.add(model);

  // An empty group has an EMPTY Box3, whose bounding sphere radius is -Infinity; every
  // camera and light distance derived from it becomes NaN and the canvas renders black
  // with no error. Stage 0 ships with zero parts built, so this is the normal case here,
  // not an edge case.
  const box = new THREE.Box3().setFromObject(model);
  const bounds = box.isEmpty()
    ? new THREE.Sphere(new THREE.Vector3(), 1)
    : box.getBoundingSphere(new THREE.Sphere());

  const rig = createUltimaWeaponV2LookDevLights("referenceLighting", bounds);
  const lights = rig.lights;
  scene.add(lights);
  scene.environment = rig.createEnvironment(renderer);
  scene.environmentIntensity = rig.environmentIntensity;
  scene.background = rig.background;
  renderer.toneMapping = rig.toneMapping;
  renderer.toneMappingExposure = rig.toneMappingExposure;

  const fixedDir = options.view ? VIEW_DIRS[options.view] : undefined;
  const camera = fixedDir
    ? new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 100)
    : new THREE.PerspectiveCamera(32, 1, 0.01, 100);

  const controls = new ArcballControls(camera, renderer.domElement, scene) as ArcballControls & {
    target: THREE.Vector3;
  };
  controls.target.copy(bounds.center);
  // A fixed review camera exists to be reproducible; letting the user turn it defeats
  // the gate that reads the frame. The arcball gizmo goes with it: it draws three tinted
  // circles INTO the WebGL frame, and every silhouette gate then reads two faint
  // full-width lines as subject — which is exactly how the sole's first tight crop came
  // back as the whole 700x700 canvas.
  if (fixedDir) {
    controls.enabled = false;
    controls.setGizmosVisible(false);
  }

  const fitDistance = (radius: number, margin: number) => {
    const cam = camera as THREE.PerspectiveCamera;
    const vertical = THREE.MathUtils.degToRad(cam.fov) / 2;
    const horizontal = Math.atan(Math.tan(vertical) * cam.aspect);
    return (radius * margin) / Math.sin(Math.min(vertical, horizontal));
  };

  const reframe = () => {
    const b = new THREE.Box3().setFromObject(model);
    const sphere = b.isEmpty()
      ? new THREE.Sphere(new THREE.Vector3(), 1)
      : b.getBoundingSphere(new THREE.Sphere());
    controls.target.copy(sphere.center);
    if (fixedDir) {
      const cam = camera as THREE.OrthographicCamera;
      const half = sphere.radius * 1.15;
      const aspect = (host.clientWidth || 1) / (host.clientHeight || 1);
      cam.left = -half * aspect;
      cam.right = half * aspect;
      cam.top = half;
      cam.bottom = -half;
      cam.near = 0.01;
      cam.far = sphere.radius * 8 + 1;
      cam.position
        .copy(sphere.center)
        .addScaledVector(new THREE.Vector3(...fixedDir).normalize(), sphere.radius * 4);
      cam.lookAt(sphere.center);
      cam.updateProjectionMatrix();
      return;
    }
    const distance = fitDistance(sphere.radius, 1.15);
    const dir = new THREE.Vector3(0.6, 0.14, 0.79).normalize();
    camera.position.copy(sphere.center).addScaledVector(dir, distance);
    controls.update();
  };

  const resize = () => {
    const width = host.clientWidth || 1;
    const height = host.clientHeight || 1;
    renderer.setSize(width, height, false);
    if (!fixedDir) {
      const cam = camera as THREE.PerspectiveCamera;
      cam.aspect = width / height;
      cam.updateProjectionMatrix();
    } else {
      reframe();
    }
  };

  const observer = new ResizeObserver(resize);
  observer.observe(host);
  resize();
  reframe();

  // Left-drag turns the model, not the camera. In gallery mode it turns the ONE part
  // under the pointer, which is what "each independently orbitable" means — turning the
  // whole row instead would make every part share one attitude and hide exactly the
  // per-part silhouette the gallery exists to show.
  controls.unsetMouseAction(0);

  const raycaster = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  const pickTurnTarget = (event: PointerEvent): THREE.Object3D => {
    if (options.mode !== "gallery") return model;
    const rect = renderer.domElement.getBoundingClientRect();
    ndc.set(
      ((event.clientX - rect.left) / rect.width) * 2 - 1,
      -((event.clientY - rect.top) / rect.height) * 2 + 1,
    );
    raycaster.setFromCamera(ndc, camera);
    const hit = raycaster.intersectObject(model, true)[0];
    if (!hit) return model;
    let node: THREE.Object3D | null = hit.object;
    while (node && node.parent !== model) node = node.parent;
    return node ?? model;
  };

  let turnLast: { x: number; y: number } | null = null;
  let turnTargetNode: THREE.Object3D = model;
  const TURN_RATE = 0.009;
  const turnRight = new THREE.Vector3();
  const turnStep = new THREE.Quaternion();
  const turnTilt = new THREE.Quaternion();

  const onTurnDown = (event: PointerEvent) => {
    if (fixedDir || event.button !== 0 || event.ctrlKey || event.metaKey) return;
    turnTargetNode = pickTurnTarget(event);
    turnLast = { x: event.clientX, y: event.clientY };
    renderer.domElement.setPointerCapture(event.pointerId);
  };
  const onTurnMove = (event: PointerEvent) => {
    if (!turnLast) return;
    const dx = event.clientX - turnLast.x;
    const dy = event.clientY - turnLast.y;
    turnLast = { x: event.clientX, y: event.clientY };
    turnRight.setFromMatrixColumn(camera.matrixWorld, 0).normalize();
    turnStep.setFromAxisAngle(THREE.Object3D.DEFAULT_UP, dx * TURN_RATE);
    turnTilt.setFromAxisAngle(turnRight, dy * TURN_RATE);
    turnTargetNode.quaternion.premultiply(turnStep.multiply(turnTilt));
  };
  const onTurnUp = () => {
    turnLast = null;
  };

  renderer.domElement.addEventListener("pointerdown", onTurnDown);
  renderer.domElement.addEventListener("pointermove", onTurnMove);
  renderer.domElement.addEventListener("pointerup", onTurnUp);
  renderer.domElement.addEventListener("pointercancel", onTurnUp);

  let handle = 0;
  const loop = () => {
    handle = requestAnimationFrame(loop);
    renderer.render(scene, camera);
  };
  loop();

  const inspector = createPartInspector({
    root: model,
    domElement: renderer.domElement,
    getCamera: () => camera,
    controls,
    onChange: () => {},
  });

  // Headless capture contract, only on a fixed review camera. `capture_parts.mjs` polls
  // __renderReady and then reads __partInfo; a blank frame must never set ready, or the
  // gate scores an empty canvas as a passing silhouette.
  if (fixedDir) {
    renderer.render(scene, camera);
    const win = window as unknown as {
      __renderReady?: boolean;
      __partInfo?: Record<string, unknown>;
      __partMeshes?: unknown;
      __renderError?: string;
    };
    const b = new THREE.Box3().setFromObject(model);
    // The geometry itself, in the shape gate_facets.py and self_intersection.py consume.
    // Exported from the SAME build the screenshot is taken of: a gate that re-derives the
    // mesh from a second code path is measuring something the reviewer never saw.
    const meshes: Array<{ name: string; vertices: number[][]; indices: number[] }> = [];
    model.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) return;
      const geometry = object.geometry as THREE.BufferGeometry;
      const position = geometry.getAttribute("position");
      const index = geometry.getIndex();
      const vertices: number[][] = [];
      for (let i = 0; i < position.count; i += 1)
        vertices.push([position.getX(i), position.getY(i), position.getZ(i)]);
      meshes.push({
        name: object.parent?.name || object.name || "mesh",
        vertices,
        indices: index ? Array.from(index.array) : [],
      });
    });
    win.__partMeshes = { meshes };
    win.__partInfo = {
      mode: options.mode ?? "assembled",
      part: options.part ?? null,
      view: options.view,
      parts: inspector.parts.map((p) => ({
        name: p.name,
        module: p.module,
        kind: p.kind,
        triangles: p.triangles,
      })),
      bbox: b.isEmpty() ? null : { min: b.min.toArray(), max: b.max.toArray() },
      // §5.4 asserts flatShading === true. It is a material flag, invisible in the mesh
      // export and only arguable from a screenshot, so it is reported explicitly.
      materials: meshes.length
        ? [
            ...new Set(
              (() => {
                const seen: string[] = [];
                model.traverse((object) => {
                  if (!(object instanceof THREE.Mesh)) return;
                  const m = object.material as THREE.MeshStandardMaterial;
                  seen.push(`${m.type}:flatShading=${m.flatShading}`);
                });
                return seen;
              })(),
            ),
          ]
        : [],
    };
    if (b.isEmpty()) win.__renderError = "nothing to render: no part built for this request";
    else win.__renderReady = true;
  }

  return {
    parts: inspector.parts,
    selectPart: inspector.selectByName,
    setIsolate: inspector.setIsolate,
    // Forwarded unconditionally, not gated on `inspector.canExplode`: ExhibitStage renders
    // the explode control `v-if="viewer?.setExplode"`, so a mount that keeps it to itself
    // silently hides the control and §5.9 ("the explode slider is present") becomes
    // untestable. Gating it on the mesh count would hide the control for a one-mesh part
    // and fail §5.9 for a reason that is not a defect; exploding one part is a no-op.
    setExplode: inspector.setExplode,
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
      lights.traverse((object) => {
        if (!(object instanceof THREE.Mesh)) return;
        object.geometry.dispose();
        const mats = Array.isArray(object.material) ? object.material : [object.material];
        for (const m of mats) m.dispose();
      });
      renderer.dispose();
      renderer.domElement.remove();
    },
  };
}
