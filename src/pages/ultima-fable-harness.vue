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
  createCloudUltimaWeaponFableModel,
  type DetailLevel,
  type SculptRuntime,
} from "~/exhibits/cloud-ultima-weapon-fable/createCloudUltimaWeaponFableModel";
import {
  REVIEW_VIEWS,
  createCloudUltimaWeaponFableLookDevLights,
  createReviewCamera,
  reviewRecipe,
  type LightingMode,
  type ReviewView,
} from "~/exhibits/cloud-ultima-weapon-fable/createCloudUltimaWeaponFableLookDev";

/**
 * Headless review harness for the FABLE-run Ultima Weapon reconstruction (independent
 * second run of the same brief). Same contract as ultima-harness.vue; only the imports
 * differ, so tools/capture_ultima.mjs drives it with --route ultima-fable-harness.
 * Deliberately absent from ssgOptions.includedRoutes (Three.js must not run in node).
 */

type HarnessWindow = Window & {
  __renderReady?: boolean;
  __renderError?: string;
  __sculptRuntime?: unknown;
  __renderHarness?: Record<string, unknown>;
  __partManifest?: Record<string, unknown>;
};

const DEFAULT_WIDTH = 1168;
const DEFAULT_HEIGHT = 2336;

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
  return {
    view: (q.get("view") ?? "reference-matched-three-quarter") as ReviewView,
    mode: (q.get("mode") ?? "referenceLighting") as LightingMode,
    detail: (["blockout", "structural", "full"].includes(detail) ? detail : "full") as DetailLevel,
    explode: Number.isFinite(explode) ? Math.min(Math.max(explode, 0), 1) : null,
    transparent: q.get("bg") === "transparent",
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
  document.documentElement.style.background = transparent ? "transparent" : "#f4f4f7";
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

  restoreChrome = takeOverViewport(params.transparent);
  canvas.style.width = `${params.width}px`;
  canvas.style.height = `${params.height}px`;

  const model = createCloudUltimaWeaponFableModel({ detail: params.detail });
  const runtime = model.userData.sculptRuntime as SculptRuntime;
  (window as HarnessWindow).__sculptRuntime = runtime;

  const recipe = reviewRecipe(params.view);
  runtime.setExplode(params.explode ?? recipe.explode ?? 0);

  const isolated = recipe.isolate ? isolatePart(model, recipe.isolate) : null;

  const rig = createCloudUltimaWeaponFableLookDevLights(params.mode);
  const aspect = params.width / params.height;
  const camera = createReviewCamera(params.view, model, aspect, isolated?.frameTarget);

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

  for (const partId of params.hide) runtime.setPartVisible(partId, false);

  if (params.flat) {
    model.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (!mesh.isMesh) return;
      const source = (Array.isArray(mesh.material) ? mesh.material[0] : mesh.material) as
        | THREE.MeshStandardMaterial
        | undefined;
      mesh.material = new THREE.MeshBasicMaterial({
        color: source?.color ?? new THREE.Color(0xffffff),
        vertexColors: source?.vertexColors ?? false,
        transparent: source?.transparent ?? false,
        opacity: source?.opacity ?? 1,
        depthWrite: source?.depthWrite ?? true,
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

  const parts: { name: string; kind: string; triangles: number }[] = [];
  let unnamedMeshes = 0;
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
    for (const child of node.children)
      if (child.name && runtime.nodes.has(child.name)) namedChildren += 1;
    parts.push({
      name,
      kind: (node as THREE.Mesh).isMesh ? "part" : namedChildren > 0 ? "container" : "part",
      triangles: Math.round(tris),
    });
  }
  model.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (mesh.isMesh && !mesh.name) unnamedMeshes += 1;
  });

  (window as HarnessWindow).__partManifest = {
    model: "cloud-ultima-weapon-fable",
    parts,
    unnamedMeshes,
    integralMeshes: parts.filter((p) => p.kind === "part").length,
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
    console.error("[ultima-fable-harness]", cause);
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
