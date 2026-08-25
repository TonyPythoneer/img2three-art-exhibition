import * as THREE from "three";

// Sigma Virus Head — forge-generated model, adapted to the exhibit page contract.
//
// Provenance: artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json
//   -> generate_threejs_factory.py -> spec/generated-factory.ts (canonical artifact).
// This file ports the generated geometry emitters VERBATIM (SDF polygonizer,
// extrude builder, primitive dimensions baked via Geometry.scale) and adapts
// only the delivery layer:
//   1. Lean flat materials from the palette constants instead of the generator's
//      1024px canvas-texture machinery — the subject is four flat colours
//      (spec lookDevTargets.referencePbrExtraction.acceptedLimitation).
//   2. Parts named by component id, direct children of the returned Group, so
//      mountSigmaVirusViewer explode/toggle/partInspector work unchanged.
//   3. Facet seams drawn as LineSegments edges per part (spec repetitionSystems
//      wireTwoToneStrokes): bright #10D830 front-facing shells, dim #10B010
//      far-facing shells, accent #E05000 eye outlines; userData.explodeWithParent.
//   4. No root mesh: the root pivot is the returned Group itself.
//   5. Extrude geometries re-centred on z (generator emits them spanning 0..depth;
//      spec transforms assume part-centred geometry) and keep their measured profile
//      size — the generator's Geometry.scale(dimensions) pass would double-apply the
//      size to extrudes whose points already encode it. SDF polygonization gets
//      explicit tight bounds so resolution 24 samples the pocket, not [-2,2]^3.

export type ProceduralModelRuntime = {
  nodes: Record<string, THREE.Object3D>;
  meshes: Record<string, THREE.Mesh>;
  sockets: Record<string, THREE.Object3D>;
  colliders: Record<string, unknown>;
  destructionGroups: Record<string, THREE.Object3D[]>;
};

const GROUND = "#000029";
const WIRE = "#10D830";
const WIRE_FAR = "#10B010";
const EYE = "#E05000";

type SdfVector = readonly [number, number, number];
type SdfTransform = {
  position?: SdfVector;
  translation?: SdfVector;
  rotation?: SdfVector;
  scale?: SdfVector;
};
type SdfPrimitive = {
  readonly id: string;
  readonly type: "sphere" | "capsule" | "box" | "cone" | "ellipsoid";
  readonly center?: SdfVector;
  readonly radius?: number | SdfVector;
  readonly height?: number;
  readonly size?: SdfVector;
  readonly dimensions?: SdfVector;
  readonly radii?: SdfVector;
  readonly transform?: SdfTransform;
};
type SdfOperation = {
  readonly id?: string;
  readonly output?: string;
  readonly type: "smooth-union" | "subtract" | "intersect";
  readonly left: string;
  readonly right: string;
  readonly radius?: number;
};
type SdfDescriptor = {
  readonly primitives: readonly SdfPrimitive[];
  readonly operations?: readonly SdfOperation[];
  readonly resolution: number;
  readonly bounds?: { readonly min: SdfVector; readonly max: SdfVector };
};
type SdfFunction = (point: THREE.Vector3) => number;

function sdfSphere(point: THREE.Vector3, radius: number): number {
  return point.length() - radius;
}

function sdfCapsule(point: THREE.Vector3, radius: number, height: number): number {
  const halfHeight = height * 0.5;
  const y = Math.max(-halfHeight, Math.min(halfHeight, point.y));
  return point.distanceTo(new THREE.Vector3(0, y, 0)) - radius;
}

function sdfBox(point: THREE.Vector3, size: SdfVector): number {
  const q = new THREE.Vector3(Math.abs(point.x), Math.abs(point.y), Math.abs(point.z)).sub(
    new THREE.Vector3(size[0] * 0.5, size[1] * 0.5, size[2] * 0.5),
  );
  return q.clone().max(new THREE.Vector3()).length() + Math.min(Math.max(q.x, q.y, q.z), 0);
}

function sdfCone(point: THREE.Vector3, radius: number, height: number): number {
  const halfHeight = height * 0.5;
  const taper = radius * (1 - (point.y + halfHeight) / height);
  return Math.max(
    Math.hypot(point.x, point.z) - Math.max(0, taper),
    Math.abs(point.y) - halfHeight,
  );
}

function sdfEllipsoid(point: THREE.Vector3, radii: SdfVector): number {
  const scaled = new THREE.Vector3(point.x / radii[0], point.y / radii[1], point.z / radii[2]);
  return (scaled.length() - 1) * Math.min(radii[0], radii[1], radii[2]);
}

function sdfRadii(primitive: SdfPrimitive): SdfVector {
  const radius = primitive.radius;
  if (primitive.radii) return primitive.radii;
  if (typeof radius === "number") return [radius, radius, radius];
  return radius ?? [0.5, 0.5, 0.5];
}

function smin(left: number, right: number, radius: number): number {
  const blend = Math.max(radius - Math.abs(left - right), 0) / radius;
  return Math.min(left, right) - blend * blend * radius * 0.25;
}

function sdfLocalPoint(
  point: THREE.Vector3,
  primitive: SdfPrimitive,
): { point: THREE.Vector3; scale: number } {
  const transform = primitive.transform;
  const translation = transform?.position ??
    transform?.translation ??
    primitive.center ?? [0, 0, 0];
  const rotation = transform?.rotation ?? [0, 0, 0];
  const scale = transform?.scale ?? [1, 1, 1];
  const local = point
    .clone()
    .sub(new THREE.Vector3(translation[0], translation[1], translation[2]));
  const inverseRotation = new THREE.Quaternion()
    .setFromEuler(new THREE.Euler(rotation[0], rotation[1], rotation[2]))
    .invert();
  local.applyQuaternion(inverseRotation);
  local.set(local.x / scale[0], local.y / scale[1], local.z / scale[2]);
  return { point: local, scale: Math.min(scale[0], scale[1], scale[2]) };
}

function sdfPrimitive(point: THREE.Vector3, primitive: SdfPrimitive): number {
  const local = sdfLocalPoint(point, primitive);
  let distance: number;
  switch (primitive.type) {
    case "sphere":
      distance = sdfSphere(
        local.point,
        typeof primitive.radius === "number" ? primitive.radius : 0.5,
      );
      break;
    case "capsule":
      distance = sdfCapsule(
        local.point,
        typeof primitive.radius === "number" ? primitive.radius : 0.25,
        primitive.height ?? 1,
      );
      break;
    case "box":
      distance = sdfBox(local.point, primitive.size ?? primitive.dimensions ?? [1, 1, 1]);
      break;
    case "cone":
      distance = sdfCone(
        local.point,
        typeof primitive.radius === "number" ? primitive.radius : 0.5,
        primitive.height ?? 1,
      );
      break;
    case "ellipsoid":
      distance = sdfEllipsoid(local.point, sdfRadii(primitive));
      break;
  }
  return distance * local.scale;
}

function sdfSample(descriptor: SdfDescriptor): SdfFunction {
  const nodes = new Map<string, SdfFunction>();
  for (const primitive of descriptor.primitives)
    nodes.set(primitive.id, (point) => sdfPrimitive(point, primitive));
  const firstPrimitive = descriptor.primitives[0];
  let result = firstPrimitive ? nodes.get(firstPrimitive.id) : undefined;
  for (let index = 0; index < (descriptor.operations?.length ?? 0); index += 1) {
    const operation = descriptor.operations?.[index];
    if (!operation) continue;
    const left = nodes.get(operation.left);
    const right = nodes.get(operation.right);
    if (!left || !right) continue;
    let combined: SdfFunction;
    switch (operation.type) {
      case "smooth-union":
        combined = (point) => smin(left(point), right(point), operation.radius ?? 0.1);
        break;
      case "subtract":
        combined = (point) => Math.max(left(point), -right(point));
        break;
      case "intersect":
        combined = (point) => Math.max(left(point), right(point));
        break;
    }
    nodes.set(operation.id ?? operation.output ?? `operation-${index}`, combined);
    result = combined;
  }
  return result ?? (() => Infinity);
}

function polygonizeSdf(descriptor: SdfDescriptor): THREE.BufferGeometry {
  // img2threejs 1.5.1 surface-nets implementation: one interpolated vertex per
  // sign-changing cell, quads around crossing edges, and field-gradient normals.
  // This replaces the pre-1.5.1 exposed-voxel shell, which introduced grid-sized
  // stair steps into the recessed face cavity.
  const resolution = Math.max(4, Math.min(64, Math.floor(descriptor.resolution)));
  const defaultBounds: { readonly min: SdfVector; readonly max: SdfVector } = {
    min: [-2, -2, -2],
    max: [2, 2, 2],
  };
  const bounds = descriptor.bounds ?? defaultBounds;
  const min = new THREE.Vector3(bounds.min[0], bounds.min[1], bounds.min[2]);
  const step = new THREE.Vector3(
    (bounds.max[0] - bounds.min[0]) / resolution,
    (bounds.max[1] - bounds.min[1]) / resolution,
    (bounds.max[2] - bounds.min[2]) / resolution,
  );
  const sample = sdfSample(descriptor);
  const scratch = new THREE.Vector3();
  const side = resolution + 1;
  const field = new Float32Array(side * side * side);
  const cornerAt = (x: number, y: number, z: number): number => (z * side + y) * side + x;
  for (let z = 0; z < side; z += 1) {
    for (let y = 0; y < side; y += 1) {
      for (let x = 0; x < side; x += 1) {
        scratch.set(min.x + x * step.x, min.y + y * step.y, min.z + z * step.z);
        field[cornerAt(x, y, z)] = sample(scratch);
      }
    }
  }
  const cubeEdges: readonly (readonly [number, number, number, number, number, number])[] = [
    [0, 0, 0, 1, 0, 0], [1, 0, 0, 1, 1, 0], [0, 1, 0, 1, 1, 0], [0, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 0, 1], [1, 0, 1, 1, 1, 1], [0, 1, 1, 1, 1, 1], [0, 0, 1, 0, 1, 1],
    [0, 0, 0, 0, 0, 1], [1, 0, 0, 1, 0, 1], [1, 1, 0, 1, 1, 1], [0, 1, 0, 0, 1, 1],
  ];
  const positions: number[] = [];
  const normals: number[] = [];
  const indices: number[] = [];
  const cellVertex = new Int32Array(resolution * resolution * resolution).fill(-1);
  const cellAt = (x: number, y: number, z: number): number => (z * resolution + y) * resolution + x;
  const fieldAt = (x: number, y: number, z: number): number =>
    field[cornerAt(x, y, z)] ?? Number.POSITIVE_INFINITY;
  const cellVertexAt = (x: number, y: number, z: number): number =>
    cellVertex[cellAt(x, y, z)] ?? -1;
  const epsilon = Math.min(step.x, step.y, step.z) * 0.25;
  const gradient = (point: THREE.Vector3): THREE.Vector3 => {
    const gx = sample(scratch.set(point.x + epsilon, point.y, point.z))
      - sample(scratch.set(point.x - epsilon, point.y, point.z));
    const gy = sample(scratch.set(point.x, point.y + epsilon, point.z))
      - sample(scratch.set(point.x, point.y - epsilon, point.z));
    const gz = sample(scratch.set(point.x, point.y, point.z + epsilon))
      - sample(scratch.set(point.x, point.y, point.z - epsilon));
    const normal = new THREE.Vector3(gx, gy, gz);
    return normal.lengthSq() < 1e-20 ? new THREE.Vector3(0, 1, 0) : normal.normalize();
  };
  for (let z = 0; z < resolution; z += 1) {
    for (let y = 0; y < resolution; y += 1) {
      for (let x = 0; x < resolution; x += 1) {
        let crossings = 0;
        let sumX = 0;
        let sumY = 0;
        let sumZ = 0;
        for (const [ax, ay, az, bx, by, bz] of cubeEdges) {
          const a = fieldAt(x + ax, y + ay, z + az);
          const b = fieldAt(x + bx, y + by, z + bz);
          if ((a <= 0) === (b <= 0)) continue;
          const t = a / (a - b);
          sumX += ax + (bx - ax) * t;
          sumY += ay + (by - ay) * t;
          sumZ += az + (bz - az) * t;
          crossings += 1;
        }
        if (crossings === 0) continue;
        const px = min.x + (x + sumX / crossings) * step.x;
        const py = min.y + (y + sumY / crossings) * step.y;
        const pz = min.z + (z + sumZ / crossings) * step.z;
        cellVertex[cellAt(x, y, z)] = positions.length / 3;
        positions.push(px, py, pz);
        const normal = gradient(new THREE.Vector3(px, py, pz));
        normals.push(normal.x, normal.y, normal.z);
      }
    }
  }
  const quad = (a: number, b: number, c: number, d: number, flip: boolean): void => {
    if (a < 0 || b < 0 || c < 0 || d < 0) return;
    if (flip) indices.push(a, c, b, a, d, c);
    else indices.push(a, b, c, a, c, d);
  };
  for (let z = 0; z < side; z += 1) {
    for (let y = 0; y < side; y += 1) {
      for (let x = 0; x < side; x += 1) {
        const here = fieldAt(x, y, z) <= 0;
        if (x + 1 < side && y > 0 && z > 0 && y < side - 1 && z < side - 1
          && here !== (fieldAt(x + 1, y, z) <= 0)) {
          quad(cellVertexAt(x, y - 1, z - 1), cellVertexAt(x, y, z - 1),
            cellVertexAt(x, y, z), cellVertexAt(x, y - 1, z), !here);
        }
        if (y + 1 < side && x > 0 && z > 0 && x < side - 1 && z < side - 1
          && here !== (fieldAt(x, y + 1, z) <= 0)) {
          quad(cellVertexAt(x - 1, y, z - 1), cellVertexAt(x - 1, y, z),
            cellVertexAt(x, y, z), cellVertexAt(x, y, z - 1), !here);
        }
        if (z + 1 < side && x > 0 && y > 0 && x < side - 1 && y < side - 1
          && here !== (fieldAt(x, y, z + 1) <= 0)) {
          quad(cellVertexAt(x - 1, y - 1, z), cellVertexAt(x, y - 1, z),
            cellVertexAt(x, y, z), cellVertexAt(x - 1, y, z), !here);
        }
      }
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

// bevelEnabled defaults to true on THREE.ExtrudeGeometry and rounds every corner;
// sharp profiles need bevelEnabled:false plus lineTo()-only segments. Holes cut
// the double-rim lens interiors (zoom-v2/front_brow-band-eyes.png).
function buildExtrudeGeometry(profile: {
  points: [number, number][];
  depth: number;
  holes?: [number, number][][];
}): THREE.ExtrudeGeometry {
  const shape = new THREE.Shape();
  const points = profile.points;
  const first = points[0];
  if (first) {
    shape.moveTo(first[0], first[1]);
    for (let i = 1; i < points.length; i += 1) {
      const point = points[i];
      if (point) shape.lineTo(point[0], point[1]);
    }
  }
  shape.closePath();
  for (const loop of profile.holes ?? []) {
    if (loop.length < 3) continue;
    const path = new THREE.Path();
    const holeFirst = loop[0];
    if (!holeFirst) continue;
    path.moveTo(holeFirst[0], holeFirst[1]);
    for (let i = 1; i < loop.length; i += 1) {
      const point = loop[i];
      if (point) path.lineTo(point[0], point[1]);
    }
    path.closePath();
    shape.holes.push(path);
  }
  const geometry = new THREE.ExtrudeGeometry(shape, {
    depth: profile.depth,
    bevelEnabled: false,
    steps: 1,
  });
  // Adaptation (5): centre the extrusion on z so spec transforms position part centres.
  geometry.translate(0, 0, -profile.depth / 2);
  return geometry;
}

// ---- materials (adaptation 1: flat palette, no canvas textures) ------------

const fillMaterial = (color: string = GROUND) =>
  new THREE.MeshBasicMaterial({
    color,
    toneMapped: false,
    polygonOffset: true,
    polygonOffsetFactor: 1,
    polygonOffsetUnits: 1,
    side: THREE.DoubleSide,
  });

const strokeMaterial = (color: string) => new THREE.LineBasicMaterial({ color, toneMapped: false });

type Placement = { position?: [number, number, number]; rotation?: [number, number, number] };

function part(
  name: string,
  geometry: THREE.BufferGeometry,
  placement: Placement,
  edgeColor: string = WIRE,
  fillColor: string = GROUND,
): THREE.Mesh {
  const mesh = new THREE.Mesh(geometry, fillMaterial(fillColor));
  mesh.name = name;
  mesh.material.userData.sigmaBaseColor = fillColor;
  if (placement.position) mesh.position.set(...placement.position);
  if (placement.rotation) mesh.rotation.set(...placement.rotation);
  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(geometry, 14),
    strokeMaterial(edgeColor),
  );
  edges.name = `${name}Edges`;
  edges.userData.explodeWithParent = true;
  mesh.add(edges);
  return mesh;
}

// ---- component geometries (literals from spec/generated-factory.ts) --------

/** Crown Shell — angular helmet prism: flat-top facet panels per zoom-v2/front_crown.png.
 *  Brief fix: scale Y 0.31→0.26 (0.26/0.31≈0.839) and Z 0.62→0.58 (0.935) to reduce dome
 *  height/depth to match OSTation green front without swapping primitive family. */
function createCrown(): THREE.Mesh {
  const geometry = buildExtrudeGeometry({
    points: [
      [-0.29, 0.1],
      [-0.2, 0.14],
      [-0.05, 0.155],
      [0.05, 0.155],
      [0.2, 0.14],
      [0.29, 0.1],
      [0.27, -0.12],
      [0.2, -0.15],
      [-0.2, -0.15],
      [-0.27, -0.12],
    ],
    depth: 0.62,
  });
  // Apply brief's Y 0.31→0.26 and Z 0.62→0.58 as post-build scale (X unchanged, width stays 0.58).
  geometry.scale(1, 0.26 / 0.31, 0.58 / 0.62);
  return part("crown", geometry, { position: [0, 0.36, -0.06] });
}

function createForehead(): THREE.Mesh {
  const geometry = new THREE.BoxGeometry(1, 1, 1, 1, 1, 1);
  geometry.scale(0.5, 0.26, 0.52);
  return part("forehead", geometry, { position: [0, 0.17, -0.02] });
}

function createTemple(side: "L" | "R"): THREE.Mesh {
  const geometry = new THREE.BoxGeometry(1, 1, 1, 1, 1, 1);
  geometry.scale(0.12, 0.26, 0.4);
  return part(`templeShell${side}`, geometry, {
    position: [side === "L" ? -0.215 : 0.215, 0.13, -0.05],
    rotation: [0, 0, side === "L" ? (8 * Math.PI) / 180 : (-8 * Math.PI) / 180],
  });
}

const CHEEK_PROFILE: { points: [number, number][]; depth: number } = {
  points: [
    [-0.07, -0.11],
    [0.07, -0.11],
    [0.07, 0.06],
    [0.02, 0.11],
    [-0.05, 0.1],
  ],
  depth: 0.3,
};

function createCheek(side: "L" | "R"): THREE.Mesh {
  // Adaptation: the profile points already carry the measured size (x span 0.14,
  // y span 0.22, depth 0.3 == the component's dimensions block), so the generator's
  // Geometry.scale(dimensions) pass would double-apply the size here. Extrude parts
  // keep their authored size; recorded in the spec's adaptationNotes.
  // Brief fix: move inward 0.265→0.25 (0.24 fails aspect 0.07; 0.265 passes but brief asks inward;
  // 0.25 is minimal inward that keeps aspect ≤0.05, tested below).
  const geometry = buildExtrudeGeometry(CHEEK_PROFILE);
  return part(`cheekShell${side}`, geometry, {
    position: [side === "L" ? -0.25 : 0.25, -0.04, -0.02],
    rotation: [0, side === "L" ? (-6 * Math.PI) / 180 : (6 * Math.PI) / 180, 0],
  });
}

const FACE_CAVITY_SDF: SdfDescriptor = {
  primitives: [
    { id: "faceBlock", type: "box", size: [0.38, 0.28, 0.24], center: [0, -0.07, 0.13] },
    { id: "pocketCut", type: "box", size: [0.33, 0.23, 0.17], center: [0, -0.07, 0.245] },
  ],
  operations: [{ id: "carvePocket", type: "subtract", left: "faceBlock", right: "pocketCut" }],
  resolution: 24,
  bounds: { min: [-0.28, -0.26, -0.03], max: [0.28, 0.12, 0.37] },
};

function createFaceCavity(): THREE.Mesh {
  return part("faceCavity", polygonizeSdf(FACE_CAVITY_SDF), { position: [0, 0, 0] }, WIRE_FAR);
}

const EYE_PROFILE: { points: [number, number][]; depth: number; holes?: [number, number][][] } = {
  points: [
    [-0.095, 0],
    [-0.06, 0.034],
    [0, 0.044],
    [0.065, 0.028],
    [0.095, 0],
    [0.06, -0.034],
    [0, -0.044],
    [-0.06, -0.034],
  ],
  depth: 0.02,
  holes: [
    [
      [-0.068, 0],
      [-0.043, 0.024],
      [0, 0.031],
      [0.047, 0.02],
      [0.068, 0],
      [0.043, -0.024],
      [0, -0.031],
      [-0.043, -0.024],
    ],
  ],
};

function createEye(side: "L" | "R"): THREE.Mesh {
  const geometry = buildExtrudeGeometry(EYE_PROFILE);
  const eye = part(
    `eyePlate${side}`,
    geometry,
    {
      position: [side === "L" ? -0.115 : 0.115, -0.02, 0.34],
      rotation: [0, 0, side === "L" ? (-12 * Math.PI) / 180 : (12 * Math.PI) / 180],
    },
    EYE,
    EYE,
  );
  eye.renderOrder = 2;
  return eye;
}

function createMidFaceBridge(): THREE.Mesh {
  const geometry = new THREE.BoxGeometry(1, 1, 1, 1, 1, 1);
  geometry.scale(0.05, 0.2, 0.08);
  return part("midFaceBridge", geometry, { position: [0, -0.12, 0.24] });
}

const JAW_PROFILE: { points: [number, number][]; depth: number } = {
  points: [
    [-0.2, 0.15],
    [0.2, 0.15],
    [0.18, -0.13],
    [0.04, -0.15],
    [0, -0.125],
    [-0.04, -0.15],
    [-0.18, -0.13],
  ],
  depth: 0.4,
};

function createLowerFaceJaw(): THREE.Mesh {
  return part("lowerFaceJaw", buildExtrudeGeometry(JAW_PROFILE), { position: [0, -0.355, 0.06] });
}

const TAB_PROFILE: { points: [number, number][]; depth: number } = {
  points: [
    [-0.05, -0.05],
    [0.05, -0.05],
    [0.05, 0.05],
    [-0.05, 0.05],
  ],
  depth: 0.12,
};

function createChinTab(side: "L" | "R"): THREE.Mesh {
  return part(`chinTab${side}`, buildExtrudeGeometry(TAB_PROFILE), {
    position: [side === "L" ? -0.17 : 0.17, -0.45, 0.05],
  });
}

/** Crown Ridge Plate — raised strip on the dome's front-to-back centre line (ridgeSeam). */
function createCrownRidge(): THREE.Mesh {
  const geometry = new THREE.BoxGeometry(1, 1, 1, 1, 1, 1);
  geometry.scale(0.05, 0.07, 0.42);
  return part("crownRidge", geometry, { position: [0, 0.485, -0.05] });
}

/** Mouth Seam Strip — raised seam across the jaw front (mouthBand). */
function createMouthSeam(): THREE.Mesh {
  const geometry = new THREE.BoxGeometry(1, 1, 1, 1, 1, 1);
  geometry.scale(0.28, 0.015, 0.02);
  return part("mouthSeam", geometry, { position: [0, -0.27, 0.26] });
}

/** Rear Shell — plain symmetric continuation (guess G4), dim strokes (far-facing). */
function createRearShell(): THREE.Mesh {
  const geometry = new THREE.SphereGeometry(0.5, 16, 10);
  geometry.scale(0.54, 0.88, 0.46);
  return part("rearShell", geometry, { position: [0, 0.02, -0.22] }, WIRE_FAR);
}

// ---- assembly --------------------------------------------------------------

export const SIGMA_PARTS = [
  "crown",
  "crownRidge",
  "forehead",
  "templeShellL",
  "templeShellR",
  "cheekShellL",
  "cheekShellR",
  "faceCavity",
  "eyePlateL",
  "eyePlateR",
  "midFaceBridge",
  "lowerFaceJaw",
  "mouthSeam",
  "chinTabL",
  "chinTabR",
  "rearShell",
] as const;

export function createSigmaVirusHead(opts: { scale?: number } = {}): THREE.Group {
  const root = new THREE.Group();
  root.name = "sigmaVirusHead";
  root.add(
    createCrown(),
    createCrownRidge(),
    createForehead(),
    createTemple("L"),
    createTemple("R"),
    createCheek("L"),
    createCheek("R"),
    createFaceCavity(),
    createEye("L"),
    createEye("R"),
    createMidFaceBridge(),
    createLowerFaceJaw(),
    createMouthSeam(),
    createChinTab("L"),
    createChinTab("R"),
    createRearShell(),
  );
  const bounds = new THREE.Box3().setFromObject(root);
  const centre = bounds.getCenter(new THREE.Vector3());
  for (const child of root.children) child.position.sub(centre);
  root.scale.setScalar(opts.scale ?? 1);
  // 1.5.1 front silhouette review measured an over-tall filled mask after
  // frame normalization; a 0.95 Y scale brings the measured aspect under the
  // 0.05 gate while leaving width/depth and all part sockets intact.
  root.scale.y *= 0.95;
  const nodes: Record<string, THREE.Object3D> = {};
  const meshes: Record<string, THREE.Mesh> = {};
  const sockets: Record<string, THREE.Object3D> = {};
  const colliders: Record<string, unknown> = {};
  const destructionGroups: Record<string, THREE.Object3D[]> = {};
  for (const child of root.children) {
    nodes[child.name] = child;
    if ((child as THREE.Mesh).isMesh) meshes[child.name] = child as THREE.Mesh;

    // Every named component is its own stable pivot in the assembled runtime. There
    // are no worn/held attachments in this head, so the component pivot is also the
    // only socket needed by the exhibit interaction contract. Keep collider and
    // destruction metadata in userData rather than adding helper geometry.
    sockets[`${child.name}/pivot`] = child;
    const bounds = new THREE.Box3().setFromObject(child);
    const colliderSize = bounds.getSize(new THREE.Vector3());
    const colliderCentre = bounds.getCenter(new THREE.Vector3());
    colliders[child.name] = {
      type: "box",
      offset: colliderCentre.toArray(),
      scale: colliderSize.toArray(),
      isTrigger: false,
    };
    destructionGroups[child.name] = [child];
    child.userData.actionProfile = {
      animationRole: "component",
      pivot: { mode: "component-center", localPosition: [0, 0, 0], axis: [0, 1, 0] },
      sockets: [`${child.name}/pivot`],
      collider: colliders[child.name],
      destruction: { breakable: false, fractureGroup: child.name },
    };
  }
  root.userData.sculptRuntime = {
    nodes,
    meshes,
    sockets,
    colliders,
    destructionGroups,
  } satisfies ProceduralModelRuntime;
  root.userData.provenance =
    "img2threejs forge rebuild 2026-08-22 · spec object-sculpt-spec.json (strict-quality PASS) · " +
    "generated-factory.ts emitters ported · G1 depth=1.3w · G2 recessed eyes (SDF subtract pocket) · " +
    "G3 independent chin tabs · G4 plain rear facets · palette green frame authority";
  return root;
}
