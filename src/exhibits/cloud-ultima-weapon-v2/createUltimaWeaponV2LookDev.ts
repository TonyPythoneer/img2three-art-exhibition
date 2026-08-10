import * as THREE from "three";

/**
 * Look-dev rig for the v2 rebuild.
 *
 * `referenceLighting` reproduces `spec/object-sculpt-spec.json.lightingFromPhoto`: a soft
 * upper-left key, a hemisphere fill, low ambient in place of a rim the reference never had,
 * and linear tone mapping. ACES is deliberately not used — it desaturates the violet insert
 * and the magenta gem, the two most identity-carrying colours in the frame.
 *
 * `neutralReview` strips the artwork match so geometry can be judged without the look
 * flattering it.
 */

export type LightingMode = "referenceLighting" | "neutralReview" | "blackBox";

/**
 * The accepted values, as data. `ultima-v2-harness.vue` reads a mode off the query string and
 * used to cast it straight to `LightingMode` with no check — an unknown value fell silently into
 * the neutral branch, so a typo captured a set of evidence renders labelled as something they
 * were not. `view` already had a whitelist; this is the same guard for `mode`.
 */
export const LIGHTING_MODES = [
  "referenceLighting",
  "neutralReview",
  "blackBox",
] as const satisfies readonly LightingMode[];

export const isLightingMode = (value: string): value is LightingMode =>
  (LIGHTING_MODES as readonly string[]).includes(value);

/**
 * Per-mode material changes, applied over the factory's own values and reversible exactly.
 *
 * Keyed by the name the factory's `buildMaterials()` returns, then by property. The viewer keeps
 * the undo closure `applyMaterialOverrides` hands back and calls it before switching, so leaving
 * a mode restores the factory values rather than accumulating whatever the last mode set. The
 * factory's own numbers stay the single source of truth: a mode may only deviate from them, and
 * only for as long as it is the active mode.
 */
export type MaterialOverrides = Readonly<Record<string, Readonly<Record<string, unknown>>>>;

export type LookDevRig = {
  lights: THREE.Group;
  createEnvironment: (renderer: THREE.WebGLRenderer) => THREE.Texture;
  environmentIntensity: number;
  background: THREE.Color;
  toneMapping: THREE.ToneMapping;
  toneMappingExposure: number;
  /** Whether the renderer needs its shadow map at all. Only the black box casts shadows. */
  shadows: boolean;
  materialOverrides?: MaterialOverrides;
};

/**
 * Apply overrides and return the exact undo.
 *
 * Reads the current value of every property it is about to write and closes over it, so the
 * restore is the previous value rather than a second table of "defaults" that could drift from
 * the factory. Unknown material names and unknown properties are skipped rather than thrown on:
 * a mode should not be able to break the viewer by naming a material that a future factory
 * revision no longer builds.
 */
export function applyMaterialOverrides(
  materials: Readonly<Record<string, THREE.Material>>,
  overrides: MaterialOverrides | undefined,
): () => void {
  const undo: (() => void)[] = [];
  for (const [name, props] of Object.entries(overrides ?? {})) {
    const material = materials[name];
    if (!material) continue;
    const bag = material as unknown as Record<string, unknown>;
    for (const [prop, value] of Object.entries(props)) {
      if (!(prop in bag)) continue;
      const before = bag[prop];
      undo.push(() => {
        bag[prop] = before;
        material.needsUpdate = true;
      });
      bag[prop] = value;
    }
    material.needsUpdate = true;
  }
  return () => {
    for (const restore of undo.reverse()) restore();
  };
}

const srgb = (hex: string) => new THREE.Color().setStyle(hex, THREE.SRGBColorSpace);

/** Measured key direction: the shell's upper-left face is brightest, its lower-right darkest. */
export const KEY_DIRECTION = new THREE.Vector3(-0.42, 0.62, 0.66).normalize();

export function createUltimaWeaponV2LookDevLights(
  mode: LightingMode,
  bounds?: THREE.Sphere,
): LookDevRig {
  // The black box is a presentation stage, not a review rig, and it is built from the model's own
  // bounds rather than from the constants below. Returning early keeps the two review modes on
  // byte-for-byte the same code path they had before it existed — they are the baseline the colour
  // gate, the silhouette gate and every recorded ΔE are measured against, so "unchanged" has to
  // mean unchanged, not "re-expressed as a three-way table and believed to be equivalent".
  if (mode === "blackBox") return blackBoxRig(bounds);

  const lights = new THREE.Group();
  lights.name = "lookDevRig";

  const reference = mode === "referenceLighting";

  // `referenceLighting` is deliberately close to flat. The model already carries the artwork's
  // facet value steps as baked vertex colour, and its `color` is left white so that vertex
  // colour IS the measured albedo — so a strong key would shade an already-shaded surface and
  // the near-white shell would land two stops below the reference's #E6E7F2. The rig's job
  // here is only to sum to roughly 1.0 across all orientations.
  const key = new THREE.DirectionalLight(0xffffff, reference ? 0.22 : 0.85);
  key.position.copy(KEY_DIRECTION).multiplyScalar(12);
  lights.add(key);

  const fill = new THREE.HemisphereLight(
    srgb(reference ? "#EDEDF6" : "#FFFFFF"),
    srgb(reference ? "#BFC0CC" : "#909090"),
    reference ? 0.62 : 0.5,
  );
  lights.add(fill);

  // No rim light: adding one would invent a specular event the 1997 asset never had.
  lights.add(
    new THREE.AmbientLight(srgb(reference ? "#DCDCE4" : "#B4B4B4"), reference ? 0.42 : 0.25),
  );

  return {
    lights,
    createEnvironment: (renderer) => {
      // A tiny neutral gradient environment. The crystal shell uses transmission, which needs
      // *something* to refract; a hard-coded studio HDRI would paint highlights the flat
      // reference does not have, so this stays deliberately featureless.
      const size = 32;
      const data = new Uint8Array(size * size * 4);
      for (let y = 0; y < size; y += 1) {
        const t = y / (size - 1);
        const v = Math.round(THREE.MathUtils.lerp(150, 236, t));
        for (let x = 0; x < size; x += 1) {
          const i = (y * size + x) * 4;
          data[i] = v;
          data[i + 1] = v;
          data[i + 2] = Math.min(255, v + 6);
          data[i + 3] = 255;
        }
      }
      const texture = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.mapping = THREE.EquirectangularReflectionMapping;
      texture.needsUpdate = true;
      const pmrem = new THREE.PMREMGenerator(renderer);
      const environment = pmrem.fromEquirectangular(texture).texture;
      texture.dispose();
      pmrem.dispose();
      return environment;
    },
    environmentIntensity: reference ? 0.22 : 0.4,
    background: srgb(reference ? "#FFFFFF" : "#1B1C22"),
    toneMapping: THREE.LinearToneMapping,
    toneMappingExposure: reference ? 1.0 : 1.05,
    shadows: false,
  };
}

/**
 * Stage proportions, as multiples of the model's own bounding radius — nothing here is a world
 * coordinate. The weapon's bounds move whenever the blade profile is re-cut, and a hard-coded
 * light height would quietly stop covering it.
 */
const STAGE = {
  /** How far below the bounding sphere the floor sits. Just clear of the pommel. */
  floorDrop: 1.02,
  /** Wide enough that its edge never enters a presentation framing. */
  floorSpan: 16,
  keyHeight: 2.6,
  /** Cone half-angle: covers the weapon plus a margin of floor for the pool to read on. */
  coneCoverage: 1.25,
} as const;

/**
 * The presentation stage: one overhead key, a matte floor to catch it, nothing else.
 *
 * Deliberately NOT a review rig. The two review modes light the weapon evenly so that geometry
 * and colour can be judged; this one leaves most of it dark on purpose, which is the whole point
 * of "revealed out of the dark by a single overhead light" rather than "the white version with a
 * black backdrop". None of its output is comparable to the artwork, and nothing here feeds a gate.
 */
function blackBoxRig(bounds?: THREE.Sphere): LookDevRig {
  const lights = new THREE.Group();
  lights.name = "lookDevRig";

  const radius = bounds?.radius ?? 1;
  const centre = bounds?.center ?? new THREE.Vector3();
  const floorY = centre.y - radius * STAGE.floorDrop;
  const height = radius * STAGE.keyHeight;

  // A cone wide enough to hold the weapon and a ring of floor around it. Solved from the geometry
  // rather than dialled in, so re-cutting the blade cannot leave the tip outside the light.
  const key = new THREE.SpotLight(0xffffff);
  key.angle = Math.atan((radius * STAGE.coneCoverage) / height);
  key.penumbra = 0.55;
  key.decay = 2;
  // Inverse-square falloff means intensity is in candela and scales with distance squared; expressing
  // it against `height` keeps the illuminance on the weapon constant as the model's size changes.
  // This is the slider's 1.0, so it has to be a comfortable stage on its own rather than a floor
  // to build from. 4.6 was that floor and it was too dark: the viewer's slider tops out at a
  // multiple of this value, so a low base put the whole usable range in the dark half.
  key.intensity = 20 * height * height;
  // Straight down, as specified — and that costs the shell most of its brightness, which is worth
  // knowing before anyone "fixes" the numbers around it. A vertical blade under a vertical light
  // is lit at grazing incidence, so it has almost no diffuse to collect and lives on reflection.
  //
  // Two levers were measured against that, everything else held. Tilting this one line by 13
  // degrees: shell 27 -> 80, floor 40 -> 39. Raising the intensity instead, at 1.5 / 4.6 / 20 / 60
  // times height squared: shell 17 / 27 / 52 / 79, floor 20 / 40 / 86 / 145.
  //
  // Both reach a shell around 80, but they spend different things to get there. The floor faces
  // the light squarely, so it takes every extra candela at full cosine while the blade takes
  // almost none — push the intensity far enough to light the shell and the stage stops being
  // black. Tilting spends nothing: it moves the light onto the blade's faces instead of pouring
  // more of it into the floor. The floor's albedo is set below to buy some of that back.
  //
  // The angle is the lever being declined here, and it is declined on the brief's instruction
  // rather than on the physics.
  key.position.set(centre.x, centre.y + height, centre.z);
  key.target.position.copy(centre);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.radius = 5;
  key.shadow.bias = -0.0006;
  key.shadow.camera.near = radius * 0.4;
  key.shadow.camera.far = height + radius * 3;
  lights.add(key, key.target);

  // Enough ambient to keep the crystal's facet edges and the metal's silhouette readable where the
  // cone does not reach. Any more and the black box stops being one.
  lights.add(new THREE.AmbientLight(srgb("#20222E"), 0.5));

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(radius * STAGE.floorSpan, radius * STAGE.floorSpan),
    // Darker than it looks like it should be, because it is the surface that gains fastest as the
    // key comes up: at the old 4.6x base an albedo of #1E1E28 read 40, and at this 20x base the
    // same albedo reads 86 — a grey room. Dropping it keeps the pool visible without the floor
    // becoming the brightest thing in frame.
    new THREE.MeshStandardMaterial({ color: srgb("#141419"), roughness: 0.88, metalness: 0 }),
  );
  floor.name = "stageFloor";
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(centre.x, floorY, centre.z);
  floor.receiveShadow = true;
  // On `lights`, never on the model: `parts.json` is built by walking the model, and the contract
  // assertions fail on anything built that the component contract does not declare. The floor is
  // set dressing, not a part of the weapon, and this is where balamb-garden-center puts its own
  // shadow catcher for the same reason.
  lights.add(floor);

  return {
    lights,
    createEnvironment: (renderer) => {
      // BRIGHT, on a black background — the two are independent, and conflating them is what makes
      // dark-room renders look like a photograph of nothing. `scene.background` is what the camera
      // sees where no geometry is; `scene.environment` is what the surfaces reflect. A studio does
      // exactly this: black walls, bright softbox. Without it the crystal has nothing to catch and
      // reads as a hole in the frame.
      //
      // Still brighter at the top so a reflection reads as a source overhead, but only gently.
      // A steep gradient left the HORIZONTAL band dark, and the horizontal band is precisely what
      // a vertical blade reflects — at 12 -> 228 with a 1.7 exponent the equator sat at 79 and the
      // shell measured 25. The weapon's own faces decide which part of this map matters, not the
      // part that looks best as a sky.
      const size = 32;
      const data = new Uint8Array(size * size * 4);
      for (let y = 0; y < size; y += 1) {
        const t = y / (size - 1);
        const v = Math.round(THREE.MathUtils.lerp(48, 246, t ** 0.9));
        for (let x = 0; x < size; x += 1) {
          const i = (y * size + x) * 4;
          data[i] = v;
          data[i + 1] = v;
          data[i + 2] = Math.min(255, Math.round(v * 1.12) + 4);
          data[i + 3] = 255;
        }
      }
      const texture = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.mapping = THREE.EquirectangularReflectionMapping;
      texture.needsUpdate = true;
      const pmrem = new THREE.PMREMGenerator(renderer);
      const environment = pmrem.fromEquirectangular(texture).texture;
      texture.dispose();
      pmrem.dispose();
      return environment;
    },
    // Carries most of the weapon's diffuse, and it has to. A blade standing vertically under a
    // light pointing straight down is lit at grazing incidence — its faces are nearly parallel to
    // every ray, so the key contributes almost no diffuse to them however bright it is. That is a
    // consequence of the overhead direction itself, not of a number being too low. The environment
    // is the only lever that reaches those faces without adding a second light and flattening the
    // stage, and being a vertical gradient it still reads as illumination from above.
    environmentIntensity: 2.4,
    background: srgb("#000000"),
    // ACES is still refused for the same reason as the review rigs: it desaturates the violet
    // insert and the magenta gem, which are the two identity-carrying colours in the frame, and a
    // dark stage makes that more visible rather than less.
    toneMapping: THREE.LinearToneMapping,
    toneMappingExposure: 1.0,
    shadows: true,
    // The shell's alpha blend is the wrong instrument here: it reaches 210 under the review rig by
    // mixing 0.65 of a WHITE background into 0.35 of a lit 128, and over black the same numbers
    // give 45 — darker than the grey plastic this material was rescued from.
    //
    // Transmission is not the answer either, and the first attempt at this stage proved it: at 0.92
    // the shell vanished completely. Refraction returns whatever is BEHIND the surface, and behind
    // it is the black room. That is the same failure as the review rig's, mirrored — there it
    // refracted a featureless grey and lost a quarter of the diffuse, here it refracts black and
    // loses nearly all of it.
    //
    // What makes glass visible in a dark room is REFLECTION, so the environment carries it and
    // transmission stays low enough to read as depth without spending the diffuse.
    //
    // The clearcoat is doing the WORK here, not costing it. Thinning it from 1.0 to 0.22 was tried
    // on the theory that its grazing-angle Fresnel was masking the diffuse underneath, and the
    // shell got darker, not brighter: 35 -> 25. At grazing incidence there is barely any diffuse
    // to mask — a vertical face under a vertical light receives almost none — so the coat's
    // reflection is most of what the shell has. It goes back to full.
    // **Every `envMapIntensity` below is currently a NO-OP and the numbers are kept only as the
    // record of what was tried.** three r0.185 `three.module.js:18690` overwrites the uniform with
    // `scene.environmentIntensity` for any standard/physical material that has no `envMap` of its
    // own, which is all of them — the scene environment is what they reflect. Measured on the
    // review rig, where the shell's value is easiest to read: at 1, 7.5 and 40 the re-framed render
    // is byte-identical (`artifacts/ultima-v2/diag/opaque-trial{,2}/`). So this stage's look is the
    // one `environmentIntensity: 2.4` above produces, and re-tuning it starts there.
    materialOverrides: {
      outerCrystal: {
        transparent: false,
        opacity: 1,
        // The review rig pays the shell's LEVEL with a white emissive multiplied by vertex colour,
        // because that rig delivers only 0.322 of albedo and the artwork's shell sits above its own
        // albedo. This stage does not want that term at all: its whole subject is a weapon revealed
        // out of the dark by one light, and a shell that carries its own brightness is not revealed
        // by anything. Zeroed here rather than lowered — the factory's value is the review rig's.
        emissiveIntensity: 0,
        transmission: 0.4,
        ior: 1.72,
        thickness: 0.34,
        attenuationColor: srgb("#B9C0F2"),
        attenuationDistance: 1.4,
        roughness: 0.05,
        envMapIntensity: 4,
        clearcoat: 1,
        clearcoatRoughness: 0.06,
        // The inner crystals now break the shell's surface by 90-93% of their own area, so they no
        // longer depend on the shell skipping the depth buffer to be seen.
        depthWrite: true,
      },
      guardGold: { envMapIntensity: 2.4 },
      pommelGold: { envMapIntensity: 2.4 },
      clampMetal: { envMapIntensity: 2.1 },
      guardSteel: { envMapIntensity: 1.9 },
      driver: { envMapIntensity: 1.5 },
      rootGem: { envMapIntensity: 1.6 },
    },
  };
}

export const REVIEW_VIEWS = [
  "artwork-match",
  "front-orthographic",
  "back-orthographic",
  "left-side-thickness",
  "right-side-thickness",
  "assembled-three-quarter",
  "rear-three-quarter",
  "exploded-three-quarter",
  "isolated-outer-shell",
  "isolated-purple-core",
  "isolated-guard-assembly",
  // Close-ups the correction pass requires. Each frames one node instead of the whole model.
  "closeup-crystal-clamp",
  "closeup-clamp-bases",
  "closeup-driver-joints",
  "closeup-connectors",
  "closeup-spinner-ends",
  "closeup-grip-pommel",
  "material-transmission",
] as const;

export type ReviewView = (typeof REVIEW_VIEWS)[number];

/** Measured artwork roll: the tip↔pommel silhouette diameter leans 18.13° from vertical. */
export const ARTWORK_ROLL_DEG = 18.13;
/**
 * Solved, not estimated. A roll sweep (16 / 18.13 / 20 / 22) peaks at the measured 18.13,
 * and a yaw sweep (−12 … 24 at that roll) is flat within 0.001 IoU from −6 to +6 and falls
 * away outside it: silhouette IoU 0.818 / 0.819 / 0.818 / 0.814 / 0.799 / 0.776. The artwork
 * is therefore very nearly a straight-on view with a roll — which independently agrees with
 * the earlier run's finding that the blade is symmetric in weapon-local coordinates.
 * Yaw is set mid-plateau; pitch stays a small estimate the silhouette cannot constrain.
 */
export const ARTWORK_YAW_DEG = 4.0;
export const ARTWORK_PITCH_DEG = -3.0;

const DIRECTIONS: Record<Exclude<ReviewView, "artwork-match">, [number, number, number]> = {
  "front-orthographic": [0, 0, 1],
  "back-orthographic": [0, 0, -1],
  "left-side-thickness": [-1, 0, 0.06],
  "right-side-thickness": [1, 0, 0.06],
  "assembled-three-quarter": [0.6, 0.14, 0.79],
  "rear-three-quarter": [-0.6, 0.14, -0.79],
  "exploded-three-quarter": [0.6, 0.14, 0.79],
  "isolated-outer-shell": [0.34, 0.06, 0.94],
  "isolated-purple-core": [0.34, 0.06, 0.94],
  "isolated-guard-assembly": [0.42, 0.2, 0.88],
  "closeup-crystal-clamp": [0.16, 0.05, 0.99],
  "closeup-clamp-bases": [0.16, -0.1, 0.98],
  "closeup-driver-joints": [0.2, 0.1, 0.97],
  "closeup-connectors": [0.3, 0.12, 0.95],
  "closeup-spinner-ends": [0.25, -0.05, 0.97],
  "closeup-grip-pommel": [0.3, 0.05, 0.95],
  "material-transmission": [0.12, 0.04, 0.99],
};

/**
 * What each review view does beyond framing: how far to explode, what to isolate (layers off
 * for everything else), and what to FRAME on (the camera tightens onto one node while the rest
 * of the model keeps rendering — which is what a close-up needs and an isolate does not).
 */
export function reviewRecipe(view: ReviewView): {
  explode?: number;
  isolate?: string;
  frame?: string;
  margin?: number;
} {
  switch (view) {
    case "exploded-three-quarter":
      return { explode: 1 };
    case "isolated-outer-shell":
      return { isolate: "outerCrystalShell" };
    // Two meshes since the insert became a pair of skins; isolating the front one frames the
    // pair, exactly as `closeup-crystal-clamp` does for the diamond.
    case "isolated-purple-core":
      return { isolate: "purpleEnergyInsertFront" };
    // The guard is no longer one part to isolate: `guardCore` is gone and its job belongs to the
    // grip's tang, the two jaws and the two arms between them. `hiltGroup` is the assembly.
    case "isolated-guard-assembly":
      return { isolate: "hiltGroup" };
    // The diamond is two meshes since the Z=0 split; framing the front one frames the pair,
    // because they are mirror images and the camera only needs the extent.
    case "closeup-crystal-clamp":
      return { frame: "rootDiamondGemFront", margin: 3.4 };
    // Framed on the jaw itself now that the bridge under it is gone; margin 3.0 keeps the same
    // amount of hilt in shot, which is what this close-up is for — the jaws closing on the tang.
    case "closeup-clamp-bases":
      return { frame: "crystalClampRight", margin: 3.0 };
    case "closeup-driver-joints":
      return { frame: "leatherConnectorRight", margin: 2.2 };
    case "closeup-connectors":
      return { frame: "driverArray", margin: 1.15 };
    case "closeup-spinner-ends":
      return { frame: "spinnerEndRight", margin: 5.5 };
    // Framed on the pommel now that the collar is gone; margin 5.0 keeps the same amount of
    // leather in shot, which is what this close-up is for — the leather-to-gold junction.
    case "closeup-grip-pommel":
      return { frame: "pointedMetalPommel", margin: 5.0 };
    case "material-transmission":
      return { frame: "rootDiamondGemFront", margin: 9.0 };
    default:
      return {};
  }
}

/**
 * A fixed review camera. Orthographic on purpose: the reference is a near-orthographic
 * render, and a perspective camera would add a taper the artwork does not have — which the
 * next review loop would then "correct" in geometry, permanently.
 *
 * `frameTarget` narrows the framing to an isolated node; without it an isolated part would sit
 * as a speck in a frame sized for the whole weapon.
 */
export type CameraOverrides = { yaw?: number; pitch?: number; roll?: number };

export function createReviewCamera(
  view: ReviewView,
  model: THREE.Object3D,
  aspect: number,
  frameTarget?: THREE.Object3D,
  overrides: CameraOverrides = {},
): THREE.Camera {
  const recipe = reviewRecipe(view);
  const framed = frameTarget ?? model;
  model.updateWorldMatrix(true, true);
  const bounds = new THREE.Box3().setFromObject(framed).getBoundingSphere(new THREE.Sphere());
  const radius = Math.max(bounds.radius, 1e-4);

  let direction: THREE.Vector3;
  if (view === "artwork-match") {
    const yaw = THREE.MathUtils.degToRad(overrides.yaw ?? ARTWORK_YAW_DEG);
    const pitch = THREE.MathUtils.degToRad(overrides.pitch ?? ARTWORK_PITCH_DEG);
    direction = new THREE.Vector3(
      Math.sin(yaw) * Math.cos(pitch),
      Math.sin(pitch),
      Math.cos(yaw) * Math.cos(pitch),
    );
  } else {
    direction = new THREE.Vector3(...DIRECTIONS[view]);
  }
  direction.normalize();

  // Front and rear must share distance and scale exactly, or a rear render cannot be compared
  // against the front one — so the margin is a per-view constant, never fitted per render.
  const margin = recipe.margin ?? (view === "artwork-match" ? 1.02 : 1.12);
  const halfHeight = radius * margin;
  const halfWidth = halfHeight * aspect;
  const camera = new THREE.OrthographicCamera(
    -halfWidth,
    halfWidth,
    halfHeight,
    -halfHeight,
    0.01,
    radius * 20,
  );
  camera.name = view;
  camera.position.copy(bounds.center).addScaledVector(direction, radius * 8);
  camera.lookAt(bounds.center);
  if (view === "artwork-match") {
    // The artwork's lean is a camera roll, never geometry — the component contract authors the
    // model upright and puts the tilt here.
    camera.rotateZ(THREE.MathUtils.degToRad(-(overrides.roll ?? ARTWORK_ROLL_DEG)));
  }
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);
  return camera;
}
