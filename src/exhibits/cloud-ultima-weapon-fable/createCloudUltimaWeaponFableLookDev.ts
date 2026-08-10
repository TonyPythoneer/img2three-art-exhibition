import * as THREE from "three";

/**
 * Look-dev + review cameras for the Fable-run Ultima Weapon reconstruction.
 *
 * The reference-matched view is an exact orthographic reproduction of the reference
 * framing, derived from measurements.json: blade axis x = 12.78 + 0.3185·y (tilt
 * 17.67° from vertical), origin at image (90.83, 245), 100 px = 1 unit. The camera
 * up vector carries the roll, so the model itself stays axis-vertical.
 */

export const REVIEW_VIEWS = [
  "reference-matched-three-quarter",
  "front-orthographic",
  "back-orthographic",
  "left-side-thickness",
  "right-side-thickness",
  "assembled-three-quarter",
  "exploded-three-quarter",
  "isolated-outer-shell",
  "isolated-purple-core",
  "isolated-guard-assembly",
] as const;

export type ReviewView = (typeof REVIEW_VIEWS)[number];
export type LightingMode = "referenceLighting" | "neutralReview" | "grazing";

const TILT = THREE.MathUtils.degToRad(17.67);

/** What each view needs beyond a camera. */
export function reviewRecipe(view: ReviewView): { explode?: number; isolate?: string } {
  switch (view) {
    case "exploded-three-quarter":
      return { explode: 1 };
    case "isolated-outer-shell":
      return { isolate: "outerBladeShell" };
    case "isolated-purple-core":
      return { isolate: "purpleEnergyCore" };
    case "isolated-guard-assembly":
      return { isolate: "guardAssembly" };
    default:
      return {};
  }
}

function frameBox(object: THREE.Object3D): THREE.Box3 {
  return new THREE.Box3().setFromObject(object);
}

export function createReviewCamera(
  view: ReviewView,
  model: THREE.Object3D,
  aspect: number,
  frameTarget?: THREE.Object3D,
): THREE.Camera {
  if (view === "reference-matched-three-quarter") {
    // Exact reference window: image centre (73,146)px → world (0.131, 0.997, 0);
    // window 1.46×2.92 units; image-up = world +Y rotated by the measured tilt.
    const halfH = 1.46;
    const halfW = halfH * aspect;
    const camera = new THREE.OrthographicCamera(-halfW, halfW, halfH, -halfH, 0.1, 30);
    camera.name = "reference-matched-ortho";
    camera.up.set(Math.sin(TILT), Math.cos(TILT), 0);
    camera.position.set(0.131, 0.997, 10);
    camera.lookAt(0.131, 0.997, 0);
    return camera;
  }

  const box = frameBox(frameTarget ?? model);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());

  const ortho = (dir: THREE.Vector3, name: string) => {
    const spanY = size.y * 1.08;
    const spanX = Math.max(size.x, size.z) * 1.15;
    const halfH = Math.max(spanY / 2, spanX / (2 * aspect));
    const halfW = halfH * aspect;
    const camera = new THREE.OrthographicCamera(-halfW, halfW, halfH, -halfH, 0.1, 40);
    camera.name = name;
    camera.up.set(0, 1, 0);
    camera.position.copy(center.clone().add(dir.multiplyScalar(12)));
    camera.lookAt(center);
    return camera;
  };

  switch (view) {
    case "front-orthographic":
      return ortho(new THREE.Vector3(0, 0, 1), "front-ortho");
    case "back-orthographic":
      return ortho(new THREE.Vector3(0, 0, -1), "back-ortho");
    case "left-side-thickness":
      return ortho(new THREE.Vector3(-1, 0, 0), "left-side-ortho");
    case "right-side-thickness":
      return ortho(new THREE.Vector3(1, 0, 0), "right-side-ortho");
    case "isolated-outer-shell":
    case "isolated-purple-core":
      return ortho(new THREE.Vector3(0.25, 0, 1).normalize(), `${view}-ortho`);
    case "isolated-guard-assembly":
      return ortho(new THREE.Vector3(0.3, 0.25, 1).normalize(), "isolated-guard-ortho");
    default: {
      const camera = new THREE.PerspectiveCamera(30, aspect, 0.1, 60);
      camera.name = `${view}-perspective`;
      const radius = Math.max(size.x, size.y, size.z);
      const margin = view === "exploded-three-quarter" ? 1.6 : 1.15;
      const distance = (radius * margin) / (2 * Math.tan(THREE.MathUtils.degToRad(15)));
      const azimuth = THREE.MathUtils.degToRad(28);
      const elevation = THREE.MathUtils.degToRad(12);
      camera.position.set(
        center.x + distance * Math.sin(azimuth) * Math.cos(elevation),
        center.y + distance * Math.sin(elevation),
        center.z + distance * Math.cos(azimuth) * Math.cos(elevation),
      );
      camera.up.set(0, 1, 0);
      camera.lookAt(center);
      return camera;
    }
  }
}

export type LookDevRig = {
  lights: THREE.Group;
  toneMapping: THREE.ToneMapping;
  toneMappingExposure: number;
  background: THREE.Color;
  environmentIntensity: number;
  createEnvironment: (renderer: THREE.WebGLRenderer) => THREE.Texture;
};

/**
 * Lighting per spec lightingFromPhoto: key from front-upper-right (core bevel is the
 * lighter plane; bright rim lower-right), hemisphere fill, low ambient, LinearToneMapping
 * (ACES desaturates the violet core — recorded risk), white background like the reference.
 */
export function createCloudUltimaWeaponFableLookDevLights(
  mode: LightingMode = "referenceLighting",
): LookDevRig {
  const lights = new THREE.Group();
  lights.name = `fable-lookdev-${mode}`;

  if (mode === "grazing") {
    const grazing = new THREE.DirectionalLight(0xffffff, 1.6);
    grazing.position.set(4, 0.4, 0.6);
    lights.add(grazing, new THREE.AmbientLight(0x9a9aa8, 0.12));
  } else if (mode === "neutralReview") {
    const key = new THREE.DirectionalLight(0xffffff, 1.0);
    key.position.set(2, 3, 4);
    const fill = new THREE.HemisphereLight(0xe8e8f0, 0xb8b8c4, 0.6);
    lights.add(key, fill, new THREE.AmbientLight(0xffffff, 0.2));
  } else {
    const key = new THREE.DirectionalLight(0xffffff, 1.1);
    key.position.set(0.35 * 6, 0.5 * 6 + 1, 0.85 * 6);
    const fill = new THREE.HemisphereLight(0xe8e8f0, 0xb8b8c4, 0.5);
    lights.add(key, fill, new THREE.AmbientLight(0x9a9aa8, 0.25));
  }

  return {
    lights,
    toneMapping: THREE.LinearToneMapping,
    toneMappingExposure: 1.0,
    background: new THREE.Color("#ffffff"),
    environmentIntensity: 0.35,
    createEnvironment: (renderer: THREE.WebGLRenderer) => {
      // Minimal neutral studio: two soft panels, PMREM-baked. Keeps metal facets alive
      // without adding reflections the flat-shaded reference does not show.
      const pmrem = new THREE.PMREMGenerator(renderer);
      const scene = new THREE.Scene();
      scene.background = new THREE.Color("#dcdce4");
      const panelTop = new THREE.Mesh(
        new THREE.PlaneGeometry(8, 8),
        new THREE.MeshBasicMaterial({ color: 0xffffff }),
      );
      panelTop.position.set(0, 5, 0);
      panelTop.rotation.x = Math.PI / 2;
      const panelFront = new THREE.Mesh(
        new THREE.PlaneGeometry(8, 4),
        new THREE.MeshBasicMaterial({ color: 0xf2f2f8 }),
      );
      panelFront.position.set(0, 1, 6);
      panelFront.rotation.y = Math.PI;
      scene.add(panelTop, panelFront);
      const texture = pmrem.fromScene(scene, 0.04).texture;
      pmrem.dispose();
      return texture;
    },
  };
}
