<template>
  <div class="render-harness">
    <canvas id="render-harness-canvas" ref="canvasEl" />
    <p v-if="error" class="render-harness-error">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import * as THREE from "three";
import {
  createBalambGardenCenter,
  type SculptRuntime,
} from "~/exhibits/balamb-garden-center/createBalambGardenCenter";
import {
  createReferenceCamera,
  loadReferenceCameraParameters,
  modelBounds,
} from "~/exhibits/balamb-garden-center/createReferenceCamera";
import {
  REVIEW_CAMERA_NAMES,
  createLighting,
  createReviewCamera,
  createThreeQuarterOppositeCamera,
  type LightingMode,
  type ReviewCameraName,
} from "~/exhibits/balamb-garden-center/createReviewCameras";

/**
 * Headless render harness. Not part of the gallery: it exists so tools/capture.mjs
 * can produce every acceptance-gate image at a fixed pixel size.
 *
 *   /render-harness?camera=<name>&mode=<referenceLighting|neutralReview>
 *                  &bg=<transparent|neutral>&wireframe=<0|1>
 *                  &detail=<blockout|structural|full>&w=2684&h=2012
 *                  &only=<partName>
 *
 * `only` renders a single part and its descendants, which is what
 * prompt-v3-amendment-02 section 3.2 needs for the per component form-lock gate.
 * An unknown part name is a hard error, never an empty frame: an empty silhouette
 * looks exactly like a legitimate render of something tiny, and the gate would
 * then score a real component against nothing.
 *
 * This route is deliberately absent from ssgOptions.includedRoutes in
 * vite.config.ts. Prerendering it would evaluate this module in node, where
 * there is no WebGL context, so every WebGL call is inside onMounted behind a
 * typeof window check.
 */

type HarnessWindow = Window & {
  __renderReady?: boolean;
  __renderError?: string;
  __sculptRuntime?: unknown;
  __renderHarness?: Record<string, unknown>;
};

const CAMERA_NAMES = [...REVIEW_CAMERA_NAMES, "reference", "three-quarter-opposite"] as const;
type CameraName = (typeof CAMERA_NAMES)[number];

const DEFAULT_WIDTH = 2684;
const DEFAULT_HEIGHT = 2012;

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
  const camera = (q.get("camera") ?? "reference") as CameraName;
  const mode = (q.get("mode") ?? "referenceLighting") as LightingMode;
  const detail = q.get("detail") ?? "full";
  return {
    camera,
    mode,
    detail: (["blockout", "structural", "full"].includes(detail) ? detail : "full") as
      | "blockout"
      | "structural"
      | "full",
    transparent: q.get("bg") === "transparent",
    wireframe: q.get("wireframe") === "1",
    only: (q.get("only") ?? "").trim(),
    width: int("w", DEFAULT_WIDTH),
    height: int("h", DEFAULT_HEIGHT),
  };
};

/**
 * Restricts rendering to one named part and its descendants.
 *
 * The hiding is done with layers rather than `visible`, because `visible = false`
 * prunes the whole subtree in WebGLRenderer.projectObject while a layer miss
 * skips only the object itself and still descends into its children. That is the
 * difference between being able to isolate a leaf mesh and having to keep every
 * ancestor renderable to reach it. Lights and the environment live outside the
 * model root, so they keep their default layer and the isolated part stays lit
 * exactly as it was in the full render.
 */
const isolatePart = (model: THREE.Group, only: string) => {
  const runtime = model.userData.sculptRuntime as SculptRuntime | undefined;
  const parts = runtime?.parts;
  if (!(parts instanceof Map)) {
    throw new Error(
      `only=${only} needs root.userData.sculptRuntime.parts, which this model does not expose`,
    );
  }

  const target = parts.get(only);
  if (!target) {
    const available = [...parts.keys()].sort().join(", ");
    throw new Error(`unknown part "${only}", available parts: ${available}`);
  }

  let ancestor: THREE.Object3D | null = target;
  while (ancestor && ancestor !== model) ancestor = ancestor.parent;
  if (!ancestor) {
    throw new Error(`part "${only}" is not attached under the model root, so it cannot render`);
  }

  let hidden = 0;
  let shown = 0;
  model.traverse((object) => {
    object.layers.disableAll();
    hidden += 1;
  });
  target.traverse((object) => {
    object.layers.enable(0);
    shown += 1;
  });

  let meshes = 0;
  target.traverse((object) => {
    if ((object as THREE.Mesh).isMesh) meshes += 1;
  });
  if (meshes === 0) {
    throw new Error(
      `part "${only}" holds no mesh, so only=${only} would render an empty frame that ` +
        "cannot be told apart from a real silhouette",
    );
  }

  return { onlyObjects: shown, onlyMeshes: meshes, hiddenObjects: hidden - shown };
};

/**
 * The gallery header and footer would composite into a transparent capture,
 * because the canvas sits above them and alpha shows whatever is behind. The
 * harness owns the whole viewport instead.
 */
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
  document.documentElement.style.background = transparent ? "transparent" : "#808080";
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

const buildCamera = async (
  name: CameraName,
  model: THREE.Group,
  aspect: number,
): Promise<{ camera: THREE.PerspectiveCamera; cameraSource: string }> => {
  const bounds = modelBounds(model);
  if ((REVIEW_CAMERA_NAMES as readonly string[]).includes(name)) {
    return {
      camera: createReviewCamera(name as ReviewCameraName, model, { aspect }),
      cameraSource: "review-preset",
    };
  }
  const resolved = await loadReferenceCameraParameters(model);
  if (name === "three-quarter-opposite") {
    return {
      camera: createThreeQuarterOppositeCamera(resolved.parameters, model, aspect),
      cameraSource: resolved.source,
    };
  }
  return {
    camera: createReferenceCamera(resolved.parameters, aspect, bounds),
    cameraSource: resolved.source,
  };
};

const start = async () => {
  const canvas = canvasEl.value;
  if (!canvas) throw new Error("render harness canvas is missing");

  const params = readParams(window.location.search);
  if (!(CAMERA_NAMES as readonly string[]).includes(params.camera)) {
    throw new Error(
      `unknown camera "${params.camera}", expected one of ${CAMERA_NAMES.join(", ")}`,
    );
  }

  restoreChrome = takeOverViewport(params.transparent);
  canvas.style.width = `${params.width}px`;
  canvas.style.height = `${params.height}px`;

  const model = createBalambGardenCenter({ detail: params.detail });
  (window as HarnessWindow).__sculptRuntime = model.userData.sculptRuntime;

  const aspect = params.width / params.height;
  const { camera, cameraSource } = await buildCamera(params.camera, model, aspect);

  // A shadow catcher plane would land in the alpha channel and break the
  // silhouette mask, and a wireframe render has nothing to catch.
  const rig = createLighting(params.mode, model, {
    contactShadows: !params.transparent && !params.wireframe,
  });

  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
    preserveDrawingBuffer: true,
  });
  renderer.setPixelRatio(1);
  renderer.setSize(params.width, params.height, false);
  renderer.shadowMap.enabled = !params.transparent && !params.wireframe;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = rig.toneMapping;
  renderer.toneMappingExposure = rig.toneMappingExposure;
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  scene.add(model, rig.lights);
  const environment = rig.createEnvironment(renderer);
  scene.environment = environment;
  scene.environmentIntensity = rig.environmentIntensity;
  scene.background = params.transparent ? null : rig.background;

  if (params.wireframe) {
    model.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (!mesh.isMesh) return;
      for (const material of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
        (material as THREE.MeshStandardMaterial).wireframe = true;
      }
    });
  }

  // After the camera and the lighting rig, both of which frame the whole model.
  // Isolating first would size them to one part and change what the reference
  // camera means, and amendment 02 section 3.1 keeps the camera global.
  const isolated = params.only ? isolatePart(model, params.only) : null;

  (window as HarnessWindow).__renderHarness = {
    ...params,
    ...isolated,
    cameraSource,
    cameraName: camera.name,
    drawingBufferWidth: renderer.domElement.width,
    drawingBufferHeight: renderer.domElement.height,
  };

  let frame = 0;
  let handle = 0;
  const loop = () => {
    handle = window.requestAnimationFrame(loop);
    renderer.render(scene, camera);
    frame += 1;
    // Set only on the third scheduled frame: by then the first two have been
    // committed and presented, so a screenshot cannot catch an empty canvas.
    if (frame === 3) (window as HarnessWindow).__renderReady = true;
  };
  loop();

  disposeScene = () => {
    window.cancelAnimationFrame(handle);
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
    console.error("[render-harness]", cause);
  });
});

onBeforeUnmount(() => {
  disposeScene?.();
  restoreChrome?.();
});
</script>

<style scoped>
.render-harness {
  position: fixed;
  inset: 0;
  z-index: 999;
  overflow: hidden;
  background: transparent;
}

#render-harness-canvas {
  display: block;
  position: absolute;
  top: 0;
  left: 0;
}

.render-harness-error {
  position: absolute;
  top: 0;
  left: 0;
  padding: 1rem;
  background: #300;
  color: #fbb;
  font-family: ui-monospace, monospace;
}
</style>
