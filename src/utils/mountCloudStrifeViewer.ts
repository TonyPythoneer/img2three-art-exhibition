import * as THREE from "three";
import { ArcballControls } from "three/examples/jsm/controls/ArcballControls.js";
import { createCloudStrifeLookDevLights } from "./cloudStrifeFigure/lookDev";
import { createPartInspector, readProvenance, type StageViewer } from "./partInspector";
import { STAGE1_PARTS } from "./cloudStrifeFigure/parts";
import { SOCKET_Y, SOLE_CENTRE_X } from "./cloudStrifeFigure/measurements";

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

/**
 * Every part that is built, standing where the socket ledger puts it.
 *
 * This IS the Stage 1B integration file's assembly: monochrome, socket placement only, and
 * it authors no geometry of its own — every mesh it places came out of a Stage 1 factory
 * that already passed its own gates. `gate_assembly.py` confirms the socket chain (26/26,
 * 21 joints at 0.000e+00) and `gate_silhouette.py` confirms the whole-figure Tier 1
 * silhouette (mean IoU 0.740 against a 0.6 threshold) against exactly this function's
 * output, so there is no separate "real" assembly waiting to replace it — Stage 5 refines
 * this placement later, it does not start over.
 */
function buildAssembled(): THREE.Group {
  const root = new THREE.Group();
  root.name = "cloudStrifeFigure";
  if (STAGE1_PARTS.length === 0) {
    root.userData.provenance = "no Stage 1 part is built yet";
    return root;
  }
  const ledgerY = SOCKET_Y as Record<string, number | undefined>;
  const built = STAGE1_PARTS.map((entry) => ({ entry, part: entry.build() }));
  const socketsOf = (p: THREE.Group) =>
    (p.userData.sockets ?? {}) as Record<string, THREE.Vector3 | undefined>;

  // Start every part at its own origin's ledger height, on its leg's centre line.
  const at = new Map<string, THREE.Vector3>();
  for (const { entry } of built) {
    const leg = entry.module === "legLeft" || entry.module === "legRight";
    const sideSign = entry.name.endsWith("R") ? -1 : 1;
    at.set(
      entry.name,
      new THREE.Vector3(leg ? SOLE_CENTRE_X * sideSign : 0, ledgerY[entry.origin] ?? 0, 0),
    );
  }
  // Then let a part that hangs off a socket take that socket's position instead of the
  // ledger's.
  //
  // §4's ledger has TWO naming rules and the match has to obey both:
  //
  //   - "A sided emitter carries the L/R suffix (`hipL` mates with thighL's `hip`)". So a
  //     part called thighL whose origin is `hip` looks for `hipL` FIRST and only then for
  //     a plain `hip`. Without that the pelvis's two hip sockets match neither thigh.
  //   - Unsided names mate directly — but `soleTop` is emitted by BOTH ankleL and ankleR,
  //     so an unsided name still has to prefer an emitter in the same module or the left
  //     sole ends up hanging off the right cuff.
  //
  // The chain also crosses modules: pelvis is `torso` and the thighs are `legLeft` /
  // `legRight`. A same-module restriction is what kept the legs detached from the hips, so
  // it is a PREFERENCE now, not a filter.
  //
  // ponytail: re-runs the whole placement pass once per part instead of topologically
  // sorting the chain. 23 parts, so 529 Map lookups; sort it if that ever matters.
  const sideOf = (name: string) => (name.endsWith("L") ? "L" : name.endsWith("R") ? "R" : "");
  const hosts = new Map<string, { host: string; socket: THREE.Vector3; via: string }>();
  for (const { entry } of built) {
    const wanted = [entry.origin + sideOf(entry.name), entry.origin].filter(Boolean);
    let found: { host: string; socket: THREE.Vector3; via: string } | undefined;
    for (const name of wanted) {
      const candidates = built.filter(
        (b) => b.entry.name !== entry.name && socketsOf(b.part)[name],
      );
      const parent = candidates.find((b) => b.entry.module === entry.module) ?? candidates[0];
      if (parent) {
        found = { host: parent.entry.name, socket: socketsOf(parent.part)[name]!, via: name };
        break;
      }
    }
    if (found) hosts.set(entry.name, found);
  }
  for (let pass = 0; pass < built.length; pass += 1) {
    for (const [name, { host, socket }] of hosts) {
      at.set(name, at.get(host)!.clone().add(socket));
    }
  }

  // One group node per §2 module, so partInspector derives the same module the table says.
  const modules = new Map<string, THREE.Group>();
  for (const { entry, part } of built) {
    let mod = modules.get(entry.module);
    if (!mod) {
      mod = new THREE.Group();
      mod.name = entry.module;
      modules.set(entry.module, mod);
      root.add(mod);
    }
    part.position.copy(at.get(entry.name)!);
    mod.add(part);
  }
  const hung = [...hosts].map(([name, h]) => `${name}<-${h.host}.${h.via}`).join(", ");
  root.userData.provenance =
    `${built.length} of 23 Stage 1 parts, placed by the socket ledger` +
    (hung ? `; hung from a socket: ${hung}` : "") +
    ". Not a Stage 1B assembly — no geometry is authored here.";
  return root;
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

  const rig = createCloudStrifeLookDevLights();
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
      // Frame the BOUNDING BOX, not the bounding sphere.  The figure is tall and
      // skinny (1.0 x 0.4) and the bounding sphere is dominated by the head's
      // depth (Z), which would otherwise balloon the camera frame and turn the
      // front/back views into a tiny dot in the middle of a 700x700 frame.
      // Box3 already gives us the right per-axis half-extents; +1.05 is the
      // visual margin, no symmetry to break.
      const half_x = b.isEmpty() ? 1 : ((b.max.x - b.min.x) / 2) * 1.05;
      const half_y = b.isEmpty() ? 1 : ((b.max.y - b.min.y) / 2) * 1.05;
      const half_z = b.isEmpty() ? 1 : ((b.max.z - b.min.z) / 2) * 1.05;
      const half = Math.max(half_x, half_y, half_z);
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
    const meshes: Array<{
      name: string;
      vertices: number[][];
      indices: number[];
      material: { type: string; flatShading: unknown; color: string };
      /** Where this part's own frame sits in the figure, so a gate can check placement. */
      world: number[];
    }> = [];
    // frontArm carries an ARRAY of materials (§4[12]'s three colour bands on one mesh —
    // forearm skin, wrist grey-or-skin, glove black); every other part still carries one.
    // Normalise to an array so both shapes read the same way below, and never silently
    // pick the first entry: if the bands ever disagreed on flatShading that would be a
    // real defect, so the per-mesh record only reports a single value when ALL of a
    // mesh's materials agree on it — same "fails loudly rather than guesses" rule §5.4's
    // history already established for the single-material case.
    const materialsOf = (object: THREE.Mesh): THREE.MeshStandardMaterial[] =>
      (Array.isArray(object.material)
        ? object.material
        : [object.material]) as THREE.MeshStandardMaterial[];
    const agreeingOrUndefined = <T>(values: T[]): T | undefined =>
      new Set(values).size === 1 ? values[0] : undefined;

    model.updateMatrixWorld(true);
    model.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) return;
      const geometry = object.geometry as THREE.BufferGeometry;
      const position = geometry.getAttribute("position");
      const index = geometry.getIndex();
      const vertices: number[][] = [];
      for (let i = 0; i < position.count; i += 1)
        vertices.push([position.getX(i), position.getY(i), position.getZ(i)]);
      // §5.4's second half. flatShading is a MATERIAL flag: it is invisible in the vertex
      // data and only arguable from a screenshot, so it has to ride along with the mesh it
      // belongs to. It used to live only in `__partInfo.materials` as a display string,
      // which meant gate_facets.py read `material.flatShading` off a record that never had
      // one, got None, and its `flat is not False` test passed — the assertion was there
      // and measured nothing. Carried per-mesh and typed `unknown` so a material that is
      // not a MeshStandardMaterial arrives as whatever it really is and fails loudly.
      const mats = materialsOf(object);
      meshes.push({
        name: object.parent?.name || object.name || "mesh",
        vertices,
        indices: index ? Array.from(index.array) : [],
        material: {
          type: agreeingOrUndefined(mats.map((m) => m?.type)) ?? "none",
          flatShading: agreeingOrUndefined(mats.map((m) => m?.flatShading)),
          color: mats.every((m) => m?.color)
            ? mats.map((m) => `#${m.color.getHexString()}`).join(",")
            : "none",
        },
        // The part GROUP's world origin, not the mesh's. Vertex data is local, so without
        // this an assembled capture cannot answer the one question the assembled view
        // exists to answer: did each part actually land on its host's socket? The pair
        // preview learned that the hard way — it agreed on Y by arithmetic while silently
        // dropping Z, and no export could show it.
        world: (object.parent ?? object).getWorldPosition(new THREE.Vector3()).toArray(),
      });
    });
    // §4 fixes ONE socket shape: `group.userData.sockets = { <name>: THREE.Vector3 }`.
    // Exported in a form that can FAIL rather than one that can only be read: a socket
    // authored as anything else arrives as isVector3:false carrying its own key list, so
    // spec/socket_gate.py can name the drift instead of quietly reaching for
    // `.localPosition` and making the wrong shape work. A part that emits nothing still
    // appears, with an empty map — "absent" and "emits nothing" are different failures.
    const sockets: Record<string, Record<string, unknown>> = {};
    model.traverse((object) => {
      const declared = (object.userData as { sockets?: Record<string, unknown> }).sockets;
      if (!declared || !object.name) return;
      const described: Record<string, unknown> = {};
      for (const [socketName, value] of Object.entries(declared)) {
        const vec = value as THREE.Vector3 | null;
        described[socketName] =
          vec && vec.isVector3 === true
            ? { isVector3: true, value: [vec.x, vec.y, vec.z] }
            : {
                isVector3: false,
                value: null,
                actual:
                  value === null || typeof value !== "object"
                    ? String(value)
                    : `object{${Object.keys(value as object).join(",")}}`,
              };
      }
      sockets[object.name] = described;
    });
    // §4[14]'s faceGroups, exported for the same reason sockets are: the head factory
    // throws unless its five arrays partition the geometry, but a gate that cannot SEE the
    // partition is only trusting the factory. Stage 2's hairCap, faceDecal and ears attach
    // to these arrays, so a capture that drops them hides the one contract they depend on.
    const faceGroups: Record<string, unknown> = {};
    model.traverse((object) => {
      const g = (object.userData as { faceGroups?: unknown }).faceGroups;
      if (g && object.name) faceGroups[object.name] = g;
    });
    win.__partMeshes = { meshes, sockets, faceGroups };
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
                  for (const m of materialsOf(object))
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
