import * as THREE from "three";

/**
 * Cloud's Ultima Weapon (FFVII 1997) — independent Fable 5 reconstruction.
 *
 * Every number here traces to spec/measurements.json (pixel measurements of the
 * 146×292 reference) through spec/object-sculpt-spec.json, which stays the single
 * source of truth. Coordinate frame per the brief: +Y handle→tip, +X weapon right,
 * +Z visible front, origin at the guard/handle junction, 100 reference px = 1 unit.
 * The model is built axis-vertical; the reference-matched camera applies the
 * measured 17.67° roll (spec referenceCamera).
 */

export type DetailLevel = "blockout" | "structural" | "full";

export type SculptRuntime = {
  nodes: Map<string, THREE.Object3D>;
  sockets: Map<string, THREE.Object3D>;
  materials: Record<string, THREE.Material>;
  setExplode: (amount: number) => void;
  resetAssembly: () => void;
  setPartVisible: (partId: string, visible: boolean) => void;
  getPartMetadata: (partId: string) => Record<string, unknown> | null;
};

export type ModelOptions = { detail?: DetailLevel };

/* ---------------------------------------------------------------- measured data */

// Leaf stations [localY, leftEdge, rightEdge] — measurements.json leafWidthProfile,
// per-side (the reference carries a real ~0.5px/side asymmetry that a symmetric
// average smears into a 1-2px silhouette fringe). Base rows appended from 180-195.
const LEAF: [number, number, number][] = [
  [2.82, 0.0, 0.0],
  [2.571, -0.093, 0.078],
  [2.519, -0.108, 0.101],
  [2.466, -0.124, 0.115],
  [2.414, -0.139, 0.138],
  [2.361, -0.144, 0.151],
  [2.309, -0.169, 0.174],
  [2.256, -0.175, 0.197],
  [2.204, -0.18, 0.201],
  [2.152, -0.205, 0.205],
  [2.099, -0.211, 0.209],
  [2.047, -0.216, 0.212],
  [1.994, -0.222, 0.235],
  [1.942, -0.228, 0.23],
  [1.889, -0.243, 0.224],
  [1.837, -0.239, 0.237],
  [1.784, -0.245, 0.232],
  [1.732, -0.25, 0.245],
  [1.679, -0.246, 0.24],
  [1.627, -0.242, 0.243],
  [1.574, -0.248, 0.238],
  [1.522, -0.254, 0.251],
  [1.469, -0.259, 0.255],
  [1.417, -0.256, 0.249],
  [1.364, -0.261, 0.253],
  [1.312, -0.257, 0.257],
  [1.259, -0.263, 0.261],
  [1.207, -0.269, 0.265],
  [1.154, -0.274, 0.269],
  [1.102, -0.27, 0.263],
  [1.05, -0.276, 0.277],
  [0.997, -0.272, 0.281],
  [0.945, -0.278, 0.284],
  [0.892, -0.283, 0.279],
  [0.84, -0.28, 0.283],
  [0.787, -0.276, 0.286],
  [0.735, -0.291, 0.281],
  [0.682, -0.287, 0.294],
  [0.63, -0.293, 0.289],
  [0.577, -0.289, 0.292],
  [0.525, -0.294, 0.296],
  [0.33, -0.294, 0.296],
];

// Core half-width stations, apex y69 → legs; notch measured: top y187 (Y 0.609), legs end y223 (Y 0.231).
const CORE: [number, number][] = [
  [1.847, 0.004],
  [1.795, 0.02],
  [1.742, 0.043],
  [1.69, 0.048],
  [1.637, 0.067],
  [1.585, 0.072],
  [1.532, 0.091],
  [1.48, 0.104],
  [1.427, 0.109],
  [1.375, 0.114],
  [1.322, 0.119],
  [1.27, 0.121],
  [1.217, 0.129],
  [1.165, 0.138],
  [1.112, 0.138],
  [1.06, 0.14],
  [1.008, 0.14],
  [0.955, 0.142],
  [0.903, 0.143],
  [0.85, 0.147],
  [0.798, 0.152],
  [0.745, 0.152],
  [0.693, 0.15],
  [0.64, 0.162],
  [0.588, 0.162],
  [0.535, 0.16],
  [0.483, 0.166],
  [0.43, 0.164],
  [0.378, 0.171],
];
const CORE_APEX_Y = 1.847;
const CORE_LEG_BOTTOM = 0.231;
const CORE_LEG_OUTER = 0.165;
const CORE_LEG_INNER = 0.095;
const NOTCH_APEX_Y = 0.609;

const SHELL_DEPTH = 0.06; // assumption: no side view, confidence 0.5
const CORE_DEPTH = 0.036;

// Emitter rod fan — MIRROR-symmetric, all rods tipward (guard-local-measurements.json:
// left 154.8/134.8° mirror right 23.7/41.6° within 1.5°, every measured axis passes
// within 0.05u of the radiation point (0, −0.115)). Measured rods carry their EXACT
// endpoints (root-local); the two occluded rods are fan-step continuations.
const RADIATION_Y = -0.115;
type RodDef = {
  id: string;
  inner: [number, number];
  outer: [number, number];
  radius: number;
  confidence: number;
  evidenceType: string;
};
const RODS: RodDef[] = [
  {
    id: "rightEmitterLower",
    inner: [0.372, 0.036],
    outer: [0.58, 0.128],
    radius: 0.023,
    confidence: 0.85,
    evidenceType: "visible",
  },
  {
    id: "rightEmitterMiddle",
    inner: [0.331, 0.153],
    outer: [0.465, 0.272],
    radius: 0.025,
    confidence: 0.85,
    evidenceType: "visible",
  },
  {
    id: "rightEmitterUpper",
    inner: [0.194, 0.212],
    outer: [0.321, 0.427],
    radius: 0.028,
    confidence: 0.45,
    evidenceType: "inferred",
  },
  {
    id: "leftEmitterLower",
    inner: [-0.304, 0.084],
    outer: [-0.546, 0.198],
    radius: 0.033,
    confidence: 0.85,
    evidenceType: "visible",
  },
  {
    id: "leftEmitterMiddle",
    inner: [-0.268, 0.152],
    outer: [-0.457, 0.342],
    radius: 0.036,
    confidence: 0.85,
    evidenceType: "visible",
  },
  {
    id: "leftEmitterUpper",
    inner: [-0.163, 0.228],
    outer: [-0.27, 0.454],
    radius: 0.028,
    confidence: 0.5,
    evidenceType: "inferred",
  },
];
// Measured endpoints are the VISIBLE segment; the physical rod continues inward and
// roots behind the shoulder plates. Extend the buried root toward the radiation point.
const ROD_ROOT_EXTENSION = 0.22;

// Row-wise measurements live in image rows; an off-axis point's true local Y is the
// row's axis position MINUS x·tan(tilt) — the shear the tilted axis induces. Verified:
// wing corner (row 205, d 54.2px) → local (0.542, 0.247), not (0.542, 0.42).
const SHEAR_TAN = Math.tan(TILT_RAD());
function TILT_RAD(): number {
  return THREE.MathUtils.degToRad(17.67);
}
function shearOutline(points: [number, number][]): [number, number][] {
  return points.map(([x, y]) => [x, y - x * SHEAR_TAN] as [number, number]);
}

/**
 * Douglas-Peucker simplification. The reference is a PS1 asset whose edges are FEW
 * STRAIGHT facets; per-row measurement stations wiggle around them by ±0.5px. Collapsing
 * runs within tolerance recovers the low-poly identity without moving the silhouette.
 */
function simplifyPolyline(points: [number, number][], tolerance: number): [number, number][] {
  if (points.length <= 2) return points;
  const [x1, y1] = points[0]!;
  const [x2, y2] = points[points.length - 1]!;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const norm = Math.hypot(dx, dy) || 1;
  let maxDist = 0;
  let maxIndex = 0;
  for (let i = 1; i < points.length - 1; i += 1) {
    const [px, py] = points[i]!;
    const dist = Math.abs(dy * px - dx * py + x2 * y1 - y2 * x1) / norm;
    if (dist > maxDist) {
      maxDist = dist;
      maxIndex = i;
    }
  }
  if (maxDist <= tolerance) return [points[0]!, points[points.length - 1]!];
  const left = simplifyPolyline(points.slice(0, maxIndex + 1), tolerance);
  const right = simplifyPolyline(points.slice(maxIndex), tolerance);
  return [...left.slice(0, -1), ...right];
}

// Right base wing: shell flare measured at rows 196-215, shear-corrected
// (X to 0.542 at true local Y ≈ 0.25).
const WING: [number, number][] = [
  [0.29, 0.42],
  [0.45, 0.33],
  [0.54, 0.25],
  [0.5, 0.19],
  [0.33, 0.24],
  [0.28, 0.33],
];

// Violet core gradient. Raw measured medians (#1B1161…#743FD7) read near-black under scene
// lighting in three-quarter views — the PS1 render's perceived vividness carries CRT-era
// brightness the medians undersample. Same hue track, value lifted to the perceived tone.
const CORE_STOPS = ["#2E1D7C", "#5238B8", "#6D46D8", "#8756EE", "#9E6BFA"];

/* ---------------------------------------------------------------- materials */

const srgb = (hex: string) => new THREE.Color(hex).convertSRGBToLinear();

function buildMaterials() {
  const outerBladeShellMaterial = new THREE.MeshPhysicalMaterial({
    name: "outerBladeShellMaterial",
    color: srgb("#EDEEF6"),
    roughness: 0.32,
    metalness: 0.0,
    transmission: 0.35,
    ior: 1.25,
    thickness: 0.06,
    transparent: true,
    opacity: 0.62, // reference shell reads solid milky, not glassy — 0.45 left base corners as shards
    depthWrite: false,
    envMapIntensity: 0.5,
    side: THREE.DoubleSide,
    flatShading: true,
  });
  const purpleCoreMaterial = new THREE.MeshStandardMaterial({
    name: "purpleCoreMaterial",
    color: srgb("#FFFFFF"),
    vertexColors: true,
    roughness: 0.35,
    metalness: 0.0,
    emissive: srgb("#4C34B4"),
    emissiveIntensity: 0.55, // carries the violet through shadow sides in orbit views

    flatShading: true,
  });
  const magentaSpineMaterial = new THREE.MeshStandardMaterial({
    name: "magentaSpineMaterial",
    color: srgb("#FFFFFF"),
    vertexColors: true,
    roughness: 0.3,
    metalness: 0.0,
    emissive: srgb("#3A0E20"),
    emissiveIntensity: 0.15,
    flatShading: true,
  });
  const gunmetalGuardMaterial = new THREE.MeshStandardMaterial({
    name: "gunmetalGuardMaterial",
    color: srgb("#383844"),
    roughness: 0.5,
    metalness: 0.55,
    flatShading: true,
  });
  const crimsonEmitterMaterial = new THREE.MeshPhysicalMaterial({
    name: "crimsonEmitterMaterial",
    color: srgb("#FFFFFF"),
    vertexColors: true, // two-tone facet lacquer: crimson bodies, near-black top faces, darker end caps
    roughness: 0.38,
    metalness: 0.1,
    clearcoat: 0.35,
    clearcoatRoughness: 0.4,
    envMapIntensity: 1.0,
    emissive: srgb("#40060F"),
    emissiveIntensity: 0.2, // keeps shadowed rod flanks reading crimson like the flat-lit reference
    flatShading: true,
  });
  const agedGoldMaterial = new THREE.MeshStandardMaterial({
    name: "agedGoldMaterial",
    color: srgb("#8D8354"),
    roughness: 0.55,
    metalness: 0.65,
    flatShading: true,
  });
  const gripMaterial = new THREE.MeshStandardMaterial({
    name: "gripMaterial",
    color: srgb("#1C1918"),
    roughness: 0.72,
    metalness: 0.08,
    flatShading: true,
  });
  return {
    outerBladeShellMaterial,
    purpleCoreMaterial,
    magentaSpineMaterial,
    gunmetalGuardMaterial,
    crimsonEmitterMaterial,
    agedGoldMaterial,
    gripMaterial,
  };
}

/* ---------------------------------------------------------------- geometry helpers */

function shapeFromPoints(points: [number, number][]): THREE.Shape {
  const shape = new THREE.Shape();
  const [first, ...rest] = points;
  shape.moveTo(first![0], first![1]);
  for (const [x, y] of rest) shape.lineTo(x, y);
  shape.closePath();
  return shape;
}

function extrude(points: [number, number][], depth: number): THREE.ExtrudeGeometry {
  const geometry = new THREE.ExtrudeGeometry(shapeFromPoints(points), {
    depth,
    bevelEnabled: false,
    curveSegments: 1,
  });
  geometry.translate(0, 0, -depth / 2);
  return geometry;
}

/** One side's edge as a sheared, facet-simplified polyline (top→bottom). Shared by the
 *  outline and the edge-wall strips so the translucent shell tiles without seams. */
function sideEdgePolyline(stations: [number, number, number][], side: 1 | -1): [number, number][] {
  const solid = stations.filter(([, l, r]) => r - l > 0.001);
  const pts = solid.map(([y, l, r]) => [side === 1 ? r : l, y] as [number, number]);
  return simplifyPolyline(shearOutline(pts), 0.008);
}

/** Closed outline from per-side stations [y, left, right]: shear-corrected and
 *  simplified to straight PS1 facets (tolerance 0.008u ≈ 0.8 reference px). */
function outlineFromStations(stations: [number, number, number][]): [number, number][] {
  const head = stations[0]!;
  const tip = head[2] - head[1] <= 0.001 ? [[0, head[0]] as [number, number]] : [];
  const rightEdge = sideEdgePolyline(stations, 1);
  const leftEdge = [...sideEdgePolyline(stations, -1)].reverse();
  return [...tip, ...rightEdge, ...leftEdge];
}

/** Leaf outline: measured per-side stations, closed across the base. */
function leafOutline(): [number, number][] {
  return outlineFromStations(LEAF);
}

/** Core outline with the inverted-V notch between the two lower legs. */
function coreOutline(): [number, number][] {
  const right = CORE.map(([y, w]) => [w, y] as [number, number]);
  const points: [number, number][] = [[0, CORE_APEX_Y]];
  points.push(...right.slice(1));
  points.push([CORE_LEG_OUTER, 0.3], [CORE_LEG_OUTER, CORE_LEG_BOTTOM]);
  points.push([CORE_LEG_INNER, CORE_LEG_BOTTOM]);
  points.push([0, NOTCH_APEX_Y]); // notch apex — measured y187
  points.push([-CORE_LEG_INNER, CORE_LEG_BOTTOM]);
  points.push([-CORE_LEG_OUTER, CORE_LEG_BOTTOM], [-CORE_LEG_OUTER, 0.3]);
  points.push(
    ...right
      .slice(1)
      .reverse()
      .map(([w, y]) => [-w, y] as [number, number]),
  );
  // Simplify as an open path: station wiggle collapses to straight facets while the
  // notch/leg corners survive (their deviation far exceeds the tolerance).
  return simplifyPolyline(shearOutline(points), 0.008);
}

/** Clip a closed polygon to the half-plane y >= minY (simple convex-boundary clip). */
function clipPolyY(points: [number, number][], minY: number): [number, number][] {
  const out: [number, number][] = [];
  for (let i = 0; i < points.length; i += 1) {
    const [x0, y0] = points[i]!;
    const [x1, y1] = points[(i + 1) % points.length]!;
    const in0 = y0 >= minY;
    const in1 = y1 >= minY;
    if (in0) out.push([x0, y0]);
    if (in0 !== in1) {
      const t = (minY - y0) / (y1 - y0);
      out.push([x0 + (x1 - x0) * t, minY]);
    }
  }
  return out;
}

/** Spine: dark upper spike into a wider lower diamond (zone r2c1). */
function spineOutline(): [number, number][] {
  return [
    [0, 0.64],
    [0.022, 0.5],
    [0.038, 0.42],
    [0.065, 0.35],
    [0.052, 0.26],
    [0.03, 0.19],
    [0, 0.14],
    [-0.03, 0.19],
    [-0.052, 0.26],
    [-0.065, 0.35],
    [-0.038, 0.42],
    [-0.022, 0.5],
  ];
}

/** Banded vertex colours along Y (PS1 per-facet steps, not a smooth ramp). */
function applyBandedGradient(
  geometry: THREE.BufferGeometry,
  yTop: number,
  yBottom: number,
  stops: string[],
) {
  const position = geometry.getAttribute("position");
  const colors = new Float32Array(position.count * 3);
  const parsed = stops.map((hex) => srgb(hex));
  for (let i = 0; i < position.count; i += 1) {
    const t = THREE.MathUtils.clamp((yTop - position.getY(i)) / (yTop - yBottom), 0, 0.999);
    const color = parsed[Math.floor(t * parsed.length)]!;
    colors[i * 3] = color.r;
    colors[i * 3 + 1] = color.g;
    colors[i * 3 + 2] = color.b;
  }
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
}

/** Rod two-tone facets (detail rod-two-tone-facets): crimson body, near-black faces
 *  that end up pointing weapon-up after the rod's Z-rotation, darker end caps. */
function applyRodTwoTone(geometry: THREE.BufferGeometry, rotationZ: number) {
  const g = geometry.toNonIndexed();
  const position = g.getAttribute("position");
  const normal = g.getAttribute("normal");
  const colors = new Float32Array(position.count * 3);
  const body = srgb("#9E1B2C");
  const top = srgb("#2E0A10");
  const cap = srgb("#5E1019");
  const cos = Math.cos(rotationZ);
  const sin = Math.sin(rotationZ);
  for (let i = 0; i < position.count; i += 1) {
    const nx = normal.getX(i);
    const ny = normal.getY(i);
    let color = body;
    if (Math.abs(ny) > 0.9) {
      color = cap;
    } else if (nx * sin + ny * cos > 0.72) {
      color = top;
    }
    colors[i * 3] = color.r;
    colors[i * 3 + 1] = color.g;
    colors[i * 3 + 2] = color.b;
  }
  g.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  return g;
}

/** Hard two-tone split for the spine: dark burgundy above ySplit, bright magenta below. */
function applySpineTwoTone(geometry: THREE.BufferGeometry, ySplit: number) {
  const position = geometry.getAttribute("position");
  const colors = new Float32Array(position.count * 3);
  const dark = srgb("#571031");
  const darker = srgb("#2E0A18");
  const bright = srgb("#8E2B4C");
  for (let i = 0; i < position.count; i += 1) {
    const y = position.getY(i);
    const color = y > 0.52 ? darker : y > ySplit ? dark : bright;
    colors[i * 3] = color.r;
    colors[i * 3 + 1] = color.g;
    colors[i * 3 + 2] = color.b;
  }
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
}

/* ---------------------------------------------------------------- model */

type PartMeta = {
  partId: string;
  category: string;
  confidence: number;
  evidenceType: "visible" | "mirrored" | "inferred";
  explodeVector: [number, number, number];
};

export function createCloudUltimaWeaponFableModel(options: ModelOptions = {}): THREE.Group {
  const detail: DetailLevel = options.detail ?? "full";
  const materials = buildMaterials();

  const root = new THREE.Group();
  root.name = "cloud-ultima-weapon";
  const nodes = new Map<string, THREE.Object3D>();
  const sockets = new Map<string, THREE.Object3D>();

  // Facet-band variant of the shell material (detail shell-facet-bands): the edge walls
  // carry the darker lavender band the reference shows along the blade's long edges.
  const shellEdgeMaterial = (
    materials.outerBladeShellMaterial as THREE.MeshPhysicalMaterial
  ).clone();
  shellEdgeMaterial.name = "outerBladeShellMaterial/facetBands";
  shellEdgeMaterial.color = srgb("#C9CADF");
  shellEdgeMaterial.opacity = 0.72;

  const register = (object: THREE.Object3D, meta: PartMeta, parent: THREE.Object3D) => {
    object.name = meta.partId;
    object.userData.partId = meta.partId;
    object.userData.category = meta.category;
    object.userData.confidence = meta.confidence;
    object.userData.evidenceType = meta.evidenceType;
    object.userData.explodeVector = meta.explodeVector;
    parent.add(object);
    nodes.set(meta.partId, object);
    return object;
  };

  const mesh = (
    geometry: THREE.BufferGeometry,
    material: THREE.Material,
    meta: PartMeta,
    parent: THREE.Object3D,
    position?: [number, number, number],
  ) => {
    const m = new THREE.Mesh(geometry, material);
    if (position) m.position.set(...position);
    return register(m, meta, parent) as THREE.Mesh;
  };

  const group = (meta: PartMeta, parent: THREE.Object3D) =>
    register(new THREE.Group(), meta, parent) as THREE.Group;

  /* ---- assemblies ---- */
  const bladeAssembly = group(
    {
      partId: "bladeAssembly",
      category: "blade",
      confidence: 0.9,
      evidenceType: "visible",
      explodeVector: [0, 0.55, 0],
    },
    root,
  );
  const guardAssembly = group(
    {
      partId: "guardAssembly",
      category: "guard",
      confidence: 0.85,
      evidenceType: "visible",
      explodeVector: [0, 0, 0],
    },
    root,
  );
  const handleAssembly = group(
    {
      partId: "handleAssembly",
      category: "handle",
      confidence: 0.6,
      evidenceType: "visible",
      explodeVector: [0, -0.5, 0],
    },
    root,
  );

  /* ---- blade: outer shell ---- */
  const outerBladeShell = group(
    {
      partId: "outerBladeShell",
      category: "blade",
      confidence: 0.85,
      evidenceType: "visible",
      explodeVector: [0, 0.3, 0],
    },
    bladeAssembly,
  );
  if (detail === "blockout") {
    // One faceted leaf volume; split into front/back/edges/tip at structural.
    const volume = extrude(leafOutline(), SHELL_DEPTH);
    const shellMesh = new THREE.Mesh(volume, materials.outerBladeShellMaterial);
    shellMesh.renderOrder = 3;
    outerBladeShell.add(shellMesh);
  } else {
    // Frame-visible plates own y <= 2.571; the inferred tip volume owns the rest —
    // they tile at the shared station so the translucent shell never double-renders.
    //
    // MATERIAL-PASS FINDING: the reference's core colours (down to #1B1161 navy) are
    // mathematically unreachable under any >=0.2-opacity white film (0.45*white alone
    // floors brightness at 0.42). The PS1 asset's shell SURROUNDS the core rather than
    // covering it — so the plates carry a core-shaped hole and the core plugs it,
    // recessed 0.004u, which also realizes the measured contact-shadow line.
    const plateStations = LEAF.slice(1);
    const outline = outlineFromStations(plateStations);
    const shape = shapeFromPoints(outline);
    const coreHole = clipPolyY(coreOutline(), 0.34);
    const holePath = new THREE.Path();
    holePath.moveTo(coreHole[0]![0], coreHole[0]![1]);
    for (const [hx, hy] of coreHole.slice(1)) holePath.lineTo(hx, hy);
    holePath.closePath();
    shape.holes.push(holePath);
    const front = new THREE.ShapeGeometry(shape, 1);
    const back = front.clone();
    const frontMesh = mesh(
      front,
      materials.outerBladeShellMaterial,
      {
        partId: "outerShellFront",
        category: "blade",
        confidence: 0.85,
        evidenceType: "visible",
        explodeVector: [0, 0, 0.45],
      },
      outerBladeShell,
      [0, 0, SHELL_DEPTH / 2],
    );
    frontMesh.renderOrder = 4;
    const backMesh = mesh(
      back,
      materials.outerBladeShellMaterial,
      {
        partId: "outerShellBack",
        category: "blade",
        confidence: 0.6,
        evidenceType: "mirrored",
        explodeVector: [0, 0, -0.45],
      },
      outerBladeShell,
      [0, 0, -SHELL_DEPTH / 2],
    );
    // Unmirrored on purpose: the outline is asymmetric, and a mirrored back plate shows a
    // double-edge through the translucency wherever front/back silhouettes diverge.
    backMesh.renderOrder = 2;

    // Edge walls: quad strips along the SAME simplified edge polylines as the plates,
    // so the translucent shell tiles without seams. Tip extrude owns the tip walls.
    const buildEdgeStrip = (side: 1 | -1) => {
      const edge = sideEdgePolyline(plateStations, side);
      const positions: number[] = [];
      for (let i = 0; i < edge.length - 1; i += 1) {
        const [x0, y0] = edge[i]!;
        const [x1, y1] = edge[i + 1]!;
        const zf = SHELL_DEPTH / 2;
        positions.push(x0, y0, zf, x0, y0, -zf, x1, y1, -zf);
        positions.push(x0, y0, zf, x1, y1, -zf, x1, y1, zf);
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(positions), 3));
      geometry.computeVertexNormals();
      return geometry;
    };
    const leftEdge = mesh(
      buildEdgeStrip(-1),
      shellEdgeMaterial,
      {
        partId: "outerShellLeftEdge",
        category: "blade",
        confidence: 0.8,
        evidenceType: "visible",
        explodeVector: [-0.25, 0, 0],
      },
      outerBladeShell,
    );
    leftEdge.renderOrder = 3;
    const rightEdge = mesh(
      buildEdgeStrip(1),
      shellEdgeMaterial,
      {
        partId: "outerShellRightEdge",
        category: "blade",
        confidence: 0.8,
        evidenceType: "visible",
        explodeVector: [0.25, 0, 0],
      },
      outerBladeShell,
    );
    rightEdge.renderOrder = 3;

    // Tip: the frame-cropped continuation above Y=2.571. Same plate-pair + edge-wall
    // construction as the body (one named group of anonymous meshes = one part): the
    // extruded volume it replaced was unmirrored and blend-sorted differently from the
    // mirrored body back plate, so the shared station showed an offset seam through the
    // translucency.
    const tipStations = LEAF.filter(([y]) => y >= 2.571);
    const outerShellTip = group(
      {
        partId: "outerShellTip",
        category: "blade",
        confidence: 0.5,
        evidenceType: "inferred",
        explodeVector: [0, 0.5, 0],
      },
      outerBladeShell,
    );
    const tipShape = shapeFromPoints(outlineFromStations(tipStations));
    const tipFront = new THREE.Mesh(
      new THREE.ShapeGeometry(tipShape, 1),
      materials.outerBladeShellMaterial,
    );
    tipFront.position.z = SHELL_DEPTH / 2;
    tipFront.renderOrder = 4;
    const tipBack = new THREE.Mesh(
      new THREE.ShapeGeometry(tipShape, 1),
      materials.outerBladeShellMaterial,
    );
    tipBack.position.z = -SHELL_DEPTH / 2;
    tipBack.renderOrder = 2;
    const tipWallPositions: number[] = [];
    for (const side of [1, -1] as const) {
      const edge = sideEdgePolyline(tipStations, side);
      for (let i = 0; i < edge.length - 1; i += 1) {
        const [x0, y0] = edge[i]!;
        const [x1, y1] = edge[i + 1]!;
        const zf = SHELL_DEPTH / 2;
        tipWallPositions.push(x0, y0, zf, x0, y0, -zf, x1, y1, -zf);
        tipWallPositions.push(x0, y0, zf, x1, y1, -zf, x1, y1, zf);
      }
    }
    const tipWallGeometry = new THREE.BufferGeometry();
    tipWallGeometry.setAttribute(
      "position",
      new THREE.BufferAttribute(new Float32Array(tipWallPositions), 3),
    );
    tipWallGeometry.computeVertexNormals();
    const tipWalls = new THREE.Mesh(tipWallGeometry, shellEdgeMaterial);
    tipWalls.renderOrder = 3;
    outerShellTip.add(tipFront, tipBack, tipWalls);
  }

  /* ---- blade: purple core ---- */
  const purpleEnergyCore = group(
    {
      partId: "purpleEnergyCore",
      category: "blade",
      confidence: 0.9,
      evidenceType: "visible",
      explodeVector: [0, 0, 0.28],
    },
    bladeAssembly,
  );
  {
    if (detail === "blockout") {
      const coreGeometry = extrude(coreOutline(), CORE_DEPTH);
      applyBandedGradient(coreGeometry, CORE_APEX_Y, CORE_LEG_BOTTOM, CORE_STOPS);
      purpleEnergyCore.add(new THREE.Mesh(coreGeometry, materials.purpleCoreMaterial));
    } else {
      // Front and back HALF volumes tile at z=0 — no overlap, together the full core.
      // Depth widened to plug the shell plates' core hole with a 0.004u recess per side.
      const PLUG_DEPTH = SHELL_DEPTH - 0.008;
      const frontGeometry = extrude(coreOutline(), PLUG_DEPTH / 2);
      applyBandedGradient(frontGeometry, CORE_APEX_Y, CORE_LEG_BOTTOM, CORE_STOPS);
      const front = mesh(
        frontGeometry,
        materials.purpleCoreMaterial,
        {
          partId: "purpleCoreFront",
          category: "blade",
          confidence: 0.85,
          evidenceType: "visible",
          explodeVector: [0, 0, 0.18],
        },
        purpleEnergyCore,
      );
      front.position.z = PLUG_DEPTH / 4;
      const backGeometry = extrude(coreOutline(), PLUG_DEPTH / 2);
      applyBandedGradient(backGeometry, CORE_APEX_Y, CORE_LEG_BOTTOM, CORE_STOPS);
      const back = mesh(
        backGeometry,
        materials.purpleCoreMaterial,
        {
          partId: "purpleCoreBack",
          category: "blade",
          confidence: 0.6,
          evidenceType: "mirrored",
          explodeVector: [0, 0, -0.18],
        },
        purpleEnergyCore,
      );
      back.position.z = -PLUG_DEPTH / 4;
      // Right bevel band: part of the core SURFACE (inside its outline), riding proud of
      // the plug's front face — the lighter plane + bright rim of the two-plane split.
      const edgeBand = CORE.filter(([y]) => y >= 0.4 && y <= 1.55);
      const edgeOutline = shearOutline([
        ...edgeBand.map(([y, w]) => [w - 0.002, y] as [number, number]),
        ...[...edgeBand].reverse().map(([y, w]) => [w - 0.034, y] as [number, number]),
      ]);
      const edgeGeometry = extrude(edgeOutline, 0.006);
      applyBandedGradient(edgeGeometry, CORE_APEX_Y, CORE_LEG_BOTTOM, [
        "#3A2688",
        "#4F31A8",
        "#6A44D0",
        "#8A6CF8",
        "#8A6CF8",
      ]);
      const edgeMesh = mesh(
        edgeGeometry,
        materials.purpleCoreMaterial,
        {
          partId: "purpleCoreEdge",
          category: "blade",
          confidence: 0.8,
          evidenceType: "visible",
          explodeVector: [0.15, 0, 0.1],
        },
        purpleEnergyCore,
      );
      edgeMesh.position.z = 0.029;
      const tipGeometry = extrude(
        shearOutline([
          [0, CORE_APEX_Y + 0.02],
          [0.05, 1.62],
          [-0.05, 1.62],
        ]),
        CORE_DEPTH + 0.002,
      );
      applyBandedGradient(tipGeometry, CORE_APEX_Y, 1.6, ["#1B1161", "#1B1161"]);
      mesh(
        tipGeometry,
        materials.purpleCoreMaterial,
        {
          partId: "purpleCoreTip",
          category: "blade",
          confidence: 0.85,
          evidenceType: "visible",
          explodeVector: [0, 0.22, 0.1],
        },
        purpleEnergyCore,
      );
    }
  }

  /* ---- blade: magenta spine ---- */
  const magentaCentralSpine = group(
    {
      partId: "magentaCentralSpine",
      category: "blade",
      confidence: 0.8,
      evidenceType: "visible",
      explodeVector: [0, 0, 0.6],
    },
    bladeAssembly,
  );
  magentaCentralSpine.position.z = CORE_DEPTH / 2 + 0.022; // 0.006 clearance over the core front
  {
    const spineGeometry = extrude(spineOutline(), 0.016);
    applySpineTwoTone(spineGeometry, 0.44);
    if (detail === "blockout") {
      magentaCentralSpine.add(new THREE.Mesh(spineGeometry, materials.magentaSpineMaterial));
    } else {
      const spineFront = mesh(
        extrude(spineOutline(), 0.008),
        materials.magentaSpineMaterial,
        {
          partId: "spineFront",
          category: "blade",
          confidence: 0.8,
          evidenceType: "visible",
          explodeVector: [0, 0, 0.15],
        },
        magentaCentralSpine,
      );
      applySpineTwoTone(spineFront.geometry, 0.44);
      spineFront.position.z = 0.004;
      const spineBack = mesh(
        extrude(spineOutline(), 0.008),
        materials.magentaSpineMaterial,
        {
          partId: "spineBack",
          category: "blade",
          confidence: 0.55,
          evidenceType: "mirrored",
          explodeVector: [0, 0, 0.08],
        },
        magentaCentralSpine,
      );
      applySpineTwoTone(spineBack.geometry, 0.44);
      spineBack.position.z = -0.004;
      const socketGeometry = new THREE.BoxGeometry(0.09, 0.07, 0.02);
      applySpineTwoTone(socketGeometry, 10); // uniform bright
      const baseSocket = mesh(
        socketGeometry,
        materials.magentaSpineMaterial,
        {
          partId: "spineBaseSocket",
          category: "blade",
          confidence: 0.5,
          evidenceType: "inferred",
          explodeVector: [0, -0.05, 0.3],
        },
        magentaCentralSpine,
      );
      baseSocket.position.set(0, 0.17, -0.005);
    }
  }

  /* ---- blade: mount ---- */
  if (detail !== "blockout") {
    const bladeMount = group(
      {
        partId: "bladeMount",
        category: "blade",
        confidence: 0.6,
        evidenceType: "inferred",
        explodeVector: [0, 0.12, 0],
      },
      bladeAssembly,
    );
    // Thin and tucked between the shell plates: the reference shows no dark band at the
    // base, so the inferred collar must not read through the translucent shell.
    const collar = mesh(
      new THREE.BoxGeometry(0.36, 0.05, 0.02),
      materials.gunmetalGuardMaterial,
      {
        partId: "upperBladeCollar",
        category: "blade",
        confidence: 0.55,
        evidenceType: "inferred",
        explodeVector: [0, 0.18, 0],
      },
      bladeMount,
    );
    collar.position.set(0, 0.3, 0);
    mesh(
      extrude(WING, 0.05),
      materials.outerBladeShellMaterial,
      {
        partId: "rightBladeClamp",
        category: "blade",
        confidence: 0.75,
        evidenceType: "visible",
        explodeVector: [0.3, 0, 0.1],
      },
      bladeMount,
    ).renderOrder = 3;
    mesh(
      extrude(
        [
          [-0.26, 0.36],
          [-0.37, 0.33],
          [-0.36, 0.28],
          [-0.26, 0.29],
        ],
        0.05,
      ),
      materials.outerBladeShellMaterial,
      {
        partId: "leftBladeClamp",
        category: "blade",
        confidence: 0.4,
        evidenceType: "inferred",
        explodeVector: [-0.3, 0, 0.1],
      },
      bladeMount,
    ).renderOrder = 3;
  } else {
    // Blockout still needs the visible right base flare — it is silhouette-defining.
    const flare = new THREE.Mesh(extrude(WING, 0.05), materials.outerBladeShellMaterial);
    flare.renderOrder = 3;
    bladeAssembly.add(flare);
  }

  /* ---- guard ---- */
  mesh(
    extrude(
      [
        [0, 0.31],
        [0.13, 0.17],
        [0.11, 0.02],
        [0, -0.05],
        [-0.11, 0.02],
        [-0.13, 0.17],
      ],
      0.12,
    ),
    materials.agedGoldMaterial,
    {
      partId: "centralGuardHub",
      category: "guard",
      confidence: 0.8,
      evidenceType: "visible",
      explodeVector: [0, 0, -0.15],
    },
    guardAssembly,
  );
  mesh(
    extrude(
      [
        [-0.05, 0.22],
        [-0.24, 0.1],
        [-0.34, -0.02],
        [-0.3, -0.15],
        [-0.1, -0.1],
        [-0.04, 0.02],
      ],
      0.1,
    ),
    materials.gunmetalGuardMaterial,
    {
      partId: "leftGunmetalShoulder",
      category: "guard",
      confidence: 0.8,
      evidenceType: "visible",
      explodeVector: [-0.4, 0, 0],
    },
    guardAssembly,
  );
  mesh(
    extrude(
      [
        [0.05, 0.22],
        [0.24, 0.1],
        [0.34, -0.02],
        [0.3, -0.15],
        [0.1, -0.1],
        [0.04, 0.02],
      ],
      0.1,
    ),
    materials.gunmetalGuardMaterial,
    {
      partId: "rightGunmetalShoulder",
      category: "guard",
      confidence: 0.8,
      evidenceType: "visible",
      explodeVector: [0.4, 0, 0],
    },
    guardAssembly,
  );

  const emitterRods = group(
    {
      partId: "emitterRods",
      category: "guard",
      confidence: 0.8,
      evidenceType: "visible",
      explodeVector: [0, 0, 0],
    },
    guardAssembly,
  );
  emitterRods.position.set(0, RADIATION_Y, 0);
  for (const rod of RODS) {
    let vx = rod.outer[0] - rod.inner[0];
    let vy = rod.outer[1] - rod.inner[1];
    const visibleLength = Math.hypot(vx, vy);
    const ux = vx / visibleLength;
    const uy = vy / visibleLength;
    const root: [number, number] = [
      rod.inner[0] - ux * ROD_ROOT_EXTENSION,
      rod.inner[1] - uy * ROD_ROOT_EXTENSION,
    ];
    vx = rod.outer[0] - root[0];
    vy = rod.outer[1] - root[1];
    const length = Math.hypot(vx, vy);
    const angle = Math.atan2(vy, vx);
    const rotationZ = angle - Math.PI / 2;
    const geometry = applyRodTwoTone(
      new THREE.CylinderGeometry(rod.radius * 0.8, rod.radius, length, 6, 1),
      rotationZ,
    );
    const rodMesh = mesh(
      geometry,
      materials.crimsonEmitterMaterial,
      {
        partId: rod.id,
        category: "guard",
        confidence: rod.confidence,
        evidenceType: rod.evidenceType as PartMeta["evidenceType"],
        explodeVector: [ux * 0.45, uy * 0.45, 0],
      },
      emitterRods,
    );
    // endpoints are root-local; the group already sits at (0, RADIATION_Y, 0)
    rodMesh.position.set(
      (root[0] + rod.outer[0]) / 2,
      (root[1] + rod.outer[1]) / 2 - RADIATION_Y,
      0,
    );
    rodMesh.rotation.z = rotationZ;
  }

  if (detail !== "blockout") {
    const goldGuardParts = group(
      {
        partId: "goldGuardParts",
        category: "guard",
        confidence: 0.6,
        evidenceType: "visible",
        explodeVector: [0, -0.1, 0],
      },
      guardAssembly,
    );
    const collarFront = mesh(
      extrude(
        [
          [-0.1, 0.14],
          [0.1, 0.14],
          [0.13, 0.05],
          [0, -0.01],
          [-0.13, 0.05],
        ],
        0.03,
      ),
      materials.agedGoldMaterial,
      {
        partId: "goldCenterCollarFront",
        category: "guard",
        confidence: 0.6,
        evidenceType: "visible",
        explodeVector: [0, 0, 0.3],
      },
      goldGuardParts,
    );
    collarFront.position.z = 0.07;
    const collarBack = mesh(
      extrude(
        [
          [-0.1, 0.14],
          [0.1, 0.14],
          [0.13, 0.05],
          [0, -0.01],
          [-0.13, 0.05],
        ],
        0.03,
      ),
      materials.agedGoldMaterial,
      {
        partId: "goldCenterCollarBack",
        category: "guard",
        confidence: 0.45,
        evidenceType: "mirrored",
        explodeVector: [0, 0, -0.3],
      },
      goldGuardParts,
    );
    collarBack.position.z = -0.07;
    mesh(
      extrude(
        [
          [-0.06, -0.08],
          [-0.16, -0.14],
          [-0.14, -0.22],
          [-0.05, -0.16],
        ],
        0.06,
      ),
      materials.agedGoldMaterial,
      {
        partId: "goldLowerFinLeft",
        category: "guard",
        confidence: 0.55,
        evidenceType: "visible",
        explodeVector: [-0.18, -0.12, 0],
      },
      goldGuardParts,
    );
    mesh(
      extrude(
        [
          [0.06, -0.08],
          [0.16, -0.14],
          [0.14, -0.22],
          [0.05, -0.16],
        ],
        0.06,
      ),
      materials.agedGoldMaterial,
      {
        partId: "goldLowerFinRight",
        category: "guard",
        confidence: 0.55,
        evidenceType: "visible",
        explodeVector: [0.18, -0.12, 0],
      },
      goldGuardParts,
    );
  }

  const lowerGuardBlocks =
    detail === "blockout"
      ? guardAssembly
      : group(
          {
            partId: "lowerGuardBlocks",
            category: "guard",
            confidence: 0.75,
            evidenceType: "visible",
            explodeVector: [0, -0.2, 0],
          },
          guardAssembly,
        );
  // Measured local bboxes: left [-0.383,-0.27,-0.252,-0.059], right [0.226,-0.322,0.355,-0.104].
  mesh(
    extrude(
      [
        [-0.255, -0.059],
        [-0.35, -0.1],
        [-0.383, -0.2],
        [-0.33, -0.27],
        [-0.252, -0.17],
      ],
      0.1,
    ),
    materials.agedGoldMaterial,
    {
      partId: "oliveBlockLeft",
      category: "guard",
      confidence: 0.8,
      evidenceType: "visible",
      explodeVector: [-0.35, -0.25, 0],
    },
    lowerGuardBlocks,
  );
  mesh(
    extrude(
      [
        [0.24, -0.104],
        [0.34, -0.12],
        [0.355, -0.24],
        [0.29, -0.322],
        [0.226, -0.2],
      ],
      0.12,
    ),
    materials.agedGoldMaterial,
    {
      partId: "oliveBlockRight",
      category: "guard",
      confidence: 0.8,
      evidenceType: "visible",
      explodeVector: [0.35, -0.25, 0],
    },
    lowerGuardBlocks,
  );

  /* ---- handle ---- */
  if (detail !== "blockout") {
    const tang = mesh(
      new THREE.BoxGeometry(0.05, 0.5, 0.05),
      materials.gripMaterial,
      {
        partId: "internalTang",
        category: "handle",
        confidence: 0.4,
        evidenceType: "inferred",
        explodeVector: [0, -0.1, 0],
      },
      handleAssembly,
    );
    tang.position.set(0, 0.05, 0);
  }
  const neck = mesh(
    new THREE.CylinderGeometry(0.04, 0.04, 0.09, 8, 1),
    materials.gripMaterial,
    {
      partId: "handleNeck",
      category: "handle",
      confidence: 0.7,
      evidenceType: "visible",
      explodeVector: [0, -0.22, 0],
    },
    handleAssembly,
  );
  neck.position.set(0, -0.055, 0);
  const gripCore = mesh(
    new THREE.CylinderGeometry(0.043, 0.043, 0.42, 8, 1),
    materials.gripMaterial,
    {
      partId: "blackGripCore",
      category: "handle",
      confidence: 0.75,
      evidenceType: "visible",
      explodeVector: [0, -0.4, 0],
    },
    handleAssembly,
  );
  gripCore.position.set(0, -0.31, 0);
  if (detail !== "blockout") {
    const sleeve = mesh(
      new THREE.CylinderGeometry(0.05, 0.05, 0.24, 8, 1),
      materials.gripMaterial,
      {
        partId: "blackGripSleeve",
        category: "handle",
        confidence: 0.5,
        evidenceType: "inferred",
        explodeVector: [0, -0.55, 0],
      },
      handleAssembly,
    );
    sleeve.position.set(0, -0.32, 0);
    const pommelCollar = mesh(
      new THREE.CylinderGeometry(0.05, 0.05, 0.05, 8, 1),
      materials.gunmetalGuardMaterial,
      {
        partId: "pommelCollar",
        category: "handle",
        confidence: 0.4,
        evidenceType: "inferred",
        explodeVector: [0, -0.7, 0],
      },
      handleAssembly,
    );
    pommelCollar.position.set(0, -0.56, 0);
    const pommelTip = mesh(
      new THREE.ConeGeometry(0.045, 0.09, 8, 1),
      materials.agedGoldMaterial,
      {
        partId: "goldPommelTip",
        category: "handle",
        confidence: 0.4,
        evidenceType: "inferred",
        explodeVector: [0, -0.85, 0],
      },
      handleAssembly,
    );
    pommelTip.rotation.x = Math.PI;
    pommelTip.position.set(0, -0.63, 0);
  }

  /* ---- sockets ---- */
  const socketDefs: [string, [number, number, number]][] = [
    ["bladeSocket", [0, 0.33, 0]],
    ["guardSocket", [0, 0.15, 0]],
    ["handleSocket", [0, -0.05, 0]],
    ["pommelSocket", [0, -0.55, 0]],
    ["leftEmitterSocket", [-0.12, RADIATION_Y, 0]],
    ["rightEmitterSocket", [0.12, RADIATION_Y, 0]],
  ];
  for (const [id, position] of socketDefs) {
    const socket = new THREE.Object3D();
    socket.name = id;
    socket.position.set(...position);
    root.add(socket);
    sockets.set(id, socket);
  }

  /* ---- runtime ---- */
  nodes.set("cloud-ultima-weapon", root);
  root.userData.partId = "cloud-ultima-weapon";
  root.userData.category = "root";
  root.userData.confidence = 0.9;
  root.userData.evidenceType = "visible";

  const assembled = new Map<string, THREE.Vector3>();
  for (const [id, node] of nodes) assembled.set(id, node.position.clone());
  for (const [id, node] of nodes) {
    node.userData.assembledTransform = {
      position: assembled.get(id)!.toArray(),
      rotation: [node.rotation.x, node.rotation.y, node.rotation.z],
      scale: node.scale.toArray(),
    };
  }

  const setExplode = (amount: number) => {
    const a = THREE.MathUtils.clamp(amount, 0, 1);
    for (const [id, node] of nodes) {
      if (id === "cloud-ultima-weapon") continue;
      const v = node.userData.explodeVector as [number, number, number] | undefined;
      if (!v) continue;
      const base = assembled.get(id)!;
      node.position.set(base.x + v[0] * a, base.y + v[1] * a, base.z + v[2] * a);
    }
  };

  const runtime: SculptRuntime = {
    nodes,
    sockets,
    materials,
    setExplode,
    resetAssembly: () => setExplode(0),
    setPartVisible: (partId: string, visible: boolean) => {
      const node = nodes.get(partId);
      if (node) node.visible = visible;
    },
    getPartMetadata: (partId: string) => {
      const node = nodes.get(partId);
      if (!node) return null;
      const {
        partId: id,
        category,
        confidence,
        evidenceType,
        assembledTransform,
        explodeVector,
      } = node.userData;
      return { partId: id, category, confidence, evidenceType, assembledTransform, explodeVector };
    },
  };
  root.userData.sculptRuntime = runtime;

  let rotationEnabled = false;
  root.userData.setDisplayRotation = (enabled: boolean) => {
    rotationEnabled = enabled;
  };
  root.userData.tick = (delta: number) => {
    if (rotationEnabled) root.rotation.y += delta * 0.25;
  };

  return root;
}
