import * as THREE from "three";

export type CodexSolPart = {
  id: string;
  category: "shell" | "core" | "spine" | "guard" | "handle";
  object: THREE.Object3D;
  homePosition: THREE.Vector3;
  explodeVector: THREE.Vector3;
};

export type CodexSolSculptRuntime = {
  parts: CodexSolPart[];
  nodes: Record<string, THREE.Object3D>;
  meshes: THREE.Mesh[];
  destructionGroups: Record<string, string[]>;
  setExplode: (amount: number) => void;
  getPart: (id: string) => THREE.Object3D | undefined;
  stats: { parts: number; meshes: number; triangles: number };
};

type Category = CodexSolPart["category"];

const outline = (points: readonly (readonly [number, number])[]) => {
  const first = points[0];
  if (!first) throw new Error("An outline needs at least one point");
  const shape = new THREE.Shape();
  shape.moveTo(first[0], first[1]);
  for (const [x, y] of points.slice(1)) shape.lineTo(x, y);
  shape.closePath();
  return shape;
};

const extrude = (
  points: readonly (readonly [number, number])[],
  depth: number,
  bevelSize = 0.018,
) => {
  const geometry = new THREE.ExtrudeGeometry(outline(points), {
    depth,
    steps: 1,
    curveSegments: 1,
    bevelEnabled: bevelSize > 0,
    bevelSegments: 3,
    bevelSize,
    bevelThickness: Math.min(bevelSize, depth * 0.2),
  });
  geometry.translate(0, 0, -depth / 2);
  geometry.computeVertexNormals();
  return geometry;
};

const applyGradient = (
  geometry: THREE.BufferGeometry,
  low: THREE.ColorRepresentation,
  high: THREE.ColorRepresentation,
  xBias = 0,
) => {
  geometry.computeBoundingBox();
  const box = geometry.boundingBox!;
  const position = geometry.getAttribute("position");
  const colors = new Float32Array(position.count * 3);
  const lowColor = new THREE.Color(low);
  const highColor = new THREE.Color(high);
  const spanY = Math.max(1e-6, box.max.y - box.min.y);
  const spanX = Math.max(1e-6, box.max.x - box.min.x);
  const color = new THREE.Color();
  for (let index = 0; index < position.count; index += 1) {
    const y = (position.getY(index) - box.min.y) / spanY;
    const x = (position.getX(index) - box.min.x) / spanX;
    color.copy(lowColor).lerp(highColor, THREE.MathUtils.clamp(y * 0.58 + x * xBias, 0, 1));
    colors[index * 3] = color.r;
    colors[index * 3 + 1] = color.g;
    colors[index * 3 + 2] = color.b;
  }
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
};

const materials = () => ({
  shell: new THREE.MeshPhysicalMaterial({
    color: 0xe8ebf3,
    roughness: 0.38,
    metalness: 0,
    transmission: 0.16,
    thickness: 0.32,
    transparent: true,
    opacity: 0.68,
    clearcoat: 0.18,
    clearcoatRoughness: 0.32,
    side: THREE.DoubleSide,
    depthWrite: true,
  }),
  shellEdge: new THREE.MeshPhysicalMaterial({
    color: 0xcfd8ea,
    roughness: 0.46,
    metalness: 0,
    transmission: 0.08,
    transparent: true,
    opacity: 0.7,
    side: THREE.DoubleSide,
  }),
  core: new THREE.MeshPhysicalMaterial({
    color: 0xffffff,
    vertexColors: true,
    roughness: 0.3,
    metalness: 0,
    clearcoat: 0.26,
    clearcoatRoughness: 0.24,
  }),
  coreFacet: new THREE.MeshPhysicalMaterial({
    color: 0x7650d8,
    roughness: 0.25,
    clearcoat: 0.3,
    clearcoatRoughness: 0.2,
  }),
  spine: new THREE.MeshStandardMaterial({ color: 0x7f1747, roughness: 0.4, metalness: 0 }),
  guard: new THREE.MeshStandardMaterial({
    color: 0x18171d,
    roughness: 0.62,
    metalness: 0.45,
    flatShading: true,
  }),
  guardFace: new THREE.MeshStandardMaterial({
    color: 0x35313a,
    roughness: 0.58,
    metalness: 0.38,
    flatShading: true,
  }),
  rod: new THREE.MeshStandardMaterial({ color: 0x68142c, roughness: 0.48, metalness: 0.2 }),
  rodFace: new THREE.MeshStandardMaterial({ color: 0x9a2748, roughness: 0.44, metalness: 0.18 }),
  fitting: new THREE.MeshStandardMaterial({
    color: 0x747557,
    roughness: 0.68,
    metalness: 0.35,
    flatShading: true,
  }),
  grip: new THREE.MeshStandardMaterial({ color: 0x0d0d12, roughness: 0.58, metalness: 0.15 }),
  gripAccent: new THREE.MeshStandardMaterial({ color: 0x34343d, roughness: 0.42, metalness: 0.12 }),
});

const SHELL: readonly (readonly [number, number])[] = [
  [-0.78, -0.04],
  [-0.84, 0.64],
  [-0.72, 1.25],
  [-0.78, 2.8],
  [-0.66, 4.25],
  [-0.55, 5.45],
  [-0.16, 6.42],
  [0.05, 6.65],
  [0.32, 6.28],
  [0.54, 4.9],
  [0.72, 3.35],
  [0.67, 1.3],
  [0.8, 0.62],
  [0.82, -0.04],
];

const CORE: readonly (readonly [number, number])[] = [
  [-0.33, 0.36],
  [-0.41, 1.42],
  [-0.38, 3.45],
  [-0.18, 4.85],
  [-0.03, 5.48],
  [0.04, 5.58],
  [0.19, 4.86],
  [0.39, 3.43],
  [0.42, 1.42],
  [0.33, 0.36],
  [0.17, 0.42],
  [0.1, 1.06],
  [0, 0.72],
  [-0.1, 1.06],
  [-0.17, 0.42],
];

const SPINE: readonly (readonly [number, number])[] = [
  [-0.12, 0.02],
  [-0.1, 1.45],
  [0, 2.35],
  [0.13, 1.4],
  [0.14, 0.02],
];

const LEFT_WING: readonly (readonly [number, number])[] = [
  [-0.06, 0.3],
  [-0.76, 0.2],
  [-0.9, -0.12],
  [-0.66, -0.58],
  [-0.3, -0.46],
  [-0.16, -0.12],
];

const RIGHT_WING: readonly (readonly [number, number])[] = LEFT_WING.map(([x, y]) => [-x, y]);

const LEFT_FITTING: readonly (readonly [number, number])[] = [
  [-0.42, -0.35],
  [-0.73, -0.52],
  [-0.65, -0.95],
  [-0.35, -0.82],
  [-0.22, -0.48],
];

const RIGHT_FITTING: readonly (readonly [number, number])[] = LEFT_FITTING.map(([x, y]) => [-x, y]);

export function createCodexSolUltimaWeaponModel(): THREE.Group {
  const material = materials();
  const root = new THREE.Group();
  root.name = "codexSolUltimaWeapon";
  root.userData.provenance = "codex-sol-5.6-xhigh";
  root.scale.x = 1.15;

  const bladeAssembly = new THREE.Group();
  bladeAssembly.name = "bladeAssembly";
  bladeAssembly.position.set(-0.04, 0.12, 0);
  bladeAssembly.scale.x = 0.82;
  bladeAssembly.scale.y = 1.04;
  const guardAssembly = new THREE.Group();
  guardAssembly.name = "guardAssembly";
  guardAssembly.position.set(-0.08, 0.45, 0);
  const handleAssembly = new THREE.Group();
  handleAssembly.name = "handleAssembly";
  handleAssembly.position.set(-0.065, 0.18, 0);
  root.add(bladeAssembly, guardAssembly, handleAssembly);

  const nodes: Record<string, THREE.Object3D> = {
    codexSolUltimaWeapon: root,
    bladeAssembly,
    guardAssembly,
    handleAssembly,
  };
  const meshes: THREE.Mesh[] = [];
  const parts: CodexSolPart[] = [];

  const addPart = (
    id: string,
    category: Category,
    parent: THREE.Object3D,
    meshList: THREE.Mesh[],
    position: readonly [number, number, number],
    explodeVector: readonly [number, number, number],
  ) => {
    const group = new THREE.Group();
    group.name = id;
    group.position.set(...position);
    group.userData.partId = id;
    group.userData.category = category;
    for (const mesh of meshList) {
      mesh.name ||= `${id}Mesh`;
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData.explodeWithParent = true;
      mesh.userData.partId = id;
      group.add(mesh);
      meshes.push(mesh);
    }
    parent.add(group);
    nodes[id] = group;
    parts.push({
      id,
      category,
      object: group,
      homePosition: group.position.clone(),
      explodeVector: new THREE.Vector3(...explodeVector),
    });
    return group;
  };

  const shellGeometry = extrude(SHELL, 0.22, 0.025);
  const shell = new THREE.Mesh(shellGeometry, material.shell);
  const shellEdgeGeometry = extrude(
    [
      [-0.52, 0.22],
      [-0.66, 1.25],
      [-0.73, 2.8],
      [-0.66, 4.25],
      [-0.4, 5.45],
      [-0.08, 6.12],
      [-0.02, 5.92],
      [-0.3, 5.35],
      [-0.55, 4.18],
      [-0.62, 2.8],
      [-0.56, 1.3],
      [-0.43, 0.3],
    ],
    0.245,
    0.012,
  );
  const shellEdge = new THREE.Mesh(shellEdgeGeometry, material.shellEdge);
  shellEdge.name = "outerShellLateralRim";
  addPart(
    "outerShell",
    "shell",
    bladeAssembly,
    [shell, shellEdge],
    [0, 0.08, -0.02],
    [-0.5, 0.65, -0.24],
  );

  const coreGeometry = extrude(CORE, 0.24, 0.018);
  applyGradient(coreGeometry, 0x13036b, 0x5b32d3, 0.18);
  const core = new THREE.Mesh(coreGeometry, material.core);
  const coreFacet = new THREE.Mesh(
    extrude(
      [
        [0.06, 0.7],
        [0.11, 1.1],
        [0.18, 4.82],
        [0.04, 5.5],
        [0.28, 4.74],
        [0.34, 1.48],
        [0.25, 0.48],
      ],
      0.025,
      0,
    ),
    material.coreFacet,
  );
  coreFacet.position.z = 0.132;
  coreFacet.name = "purpleCoreLongitudinalFacet";
  addPart(
    "purpleCore",
    "core",
    bladeAssembly,
    [core, coreFacet],
    [0, 0.06, 0.03],
    [0.42, 0.38, 0.34],
  );

  const spine = new THREE.Mesh(extrude(SPINE, 0.27, 0.014), material.spine);
  addPart("magentaSpine", "spine", bladeAssembly, [spine], [0, 0.02, 0.08], [0, 0.2, 0.65]);

  const hub = new THREE.Mesh(new THREE.BoxGeometry(0.66, 0.62, 0.38, 1, 1, 1), material.guardFace);
  hub.rotation.z = -0.08;
  addPart("centralHub", "guard", guardAssembly, [hub], [0, 0.05, 0], [0, 0.28, 0.42]);

  const leftWing = new THREE.Mesh(extrude(LEFT_WING, 0.32, 0.025), material.guard);
  const rightWing = new THREE.Mesh(extrude(RIGHT_WING, 0.32, 0.025), material.guard);
  addPart("leftGuardWing", "guard", guardAssembly, [leftWing], [-0.05, 0, 0], [-0.9, -0.15, 0.2]);
  addPart("rightGuardWing", "guard", guardAssembly, [rightWing], [0.13, 0, 0], [0.9, -0.15, 0.2]);

  const leftFitting = new THREE.Mesh(extrude(LEFT_FITTING, 0.34, 0.02), material.fitting);
  const rightFitting = new THREE.Mesh(extrude(RIGHT_FITTING, 0.34, 0.02), material.fitting);
  addPart(
    "leftFitting",
    "guard",
    guardAssembly,
    [leftFitting],
    [-0.05, 0, 0.015],
    [-1.12, -0.5, 0.32],
  );
  addPart(
    "rightFitting",
    "guard",
    guardAssembly,
    [rightFitting],
    [0.13, 0, 0.015],
    [1.12, -0.5, 0.32],
  );

  const rodFan = new THREE.Group();
  rodFan.name = "rodFan";
  rodFan.position.y = -0.08;
  rodFan.userData.partId = "rodFan";
  const rodGeometry = new THREE.BoxGeometry(0.1, 1.32, 0.14, 1, 1, 1);
  for (const side of [-1, 1] as const) {
    const angles = side < 0 ? [0.72, 1.08, 1.48] : [1.27, 1.57, 1.78];
    angles.forEach((angle, index) => {
      const signedAngle = angle * side;
      const lengthScale = [0.88, 1, 0.94][index]!;
      const rod = new THREE.Mesh(rodGeometry, index === 1 ? material.rodFace : material.rod);
      rod.name = `${side < 0 ? "left" : "right"}Rod${index + 1}`;
      const sideScale = side < 0 ? 1.22 : 1.05;
      rod.scale.y = lengthScale * sideScale;
      rod.rotation.z = signedAngle;
      const distance = 0.69 * lengthScale * sideScale;
      rod.position.set(
        -Math.sin(signedAngle) * distance,
        Math.cos(signedAngle) * distance + 0.02 + (side > 0 ? 0.14 : -0.035),
        -0.05,
      );
      rod.userData.explodeWithParent = true;
      rod.userData.partId = "rodFan";
      rod.castShadow = true;
      rod.receiveShadow = true;
      rodFan.add(rod);
      meshes.push(rod);
    });
  }
  guardAssembly.add(rodFan);
  nodes.rodFan = rodFan;
  parts.push({
    id: "rodFan",
    category: "guard",
    object: rodFan,
    homePosition: rodFan.position.clone(),
    explodeVector: new THREE.Vector3(0, 0.52, -0.5),
  });

  const grip = new THREE.Mesh(new THREE.BoxGeometry(0.19, 2.25, 0.28, 1, 5, 1), material.grip);
  const accent = new THREE.Mesh(new THREE.BoxGeometry(0.035, 2.05, 0.012), material.gripAccent);
  accent.position.set(0.113, 0, 0.147);
  accent.name = "gripLateralHighlight";
  const gripGroup = addPart(
    "grip",
    "handle",
    handleAssembly,
    [grip, accent],
    [0, -1.2, 0],
    [0, -0.75, 0.2],
  );
  gripGroup.rotation.z = -0.015;

  const pommel = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.28, 0.33), material.gripAccent);
  pommel.rotation.z = 0.05;
  addPart("pommel", "handle", handleAssembly, [pommel], [0, -2.47, 0], [0, -1.05, 0.28]);

  const setExplode = (amount: number) => {
    const clamped = THREE.MathUtils.clamp(amount, 0, 1);
    for (const part of parts) {
      part.object.position.copy(part.homePosition).addScaledVector(part.explodeVector, clamped);
    }
  };

  let triangles = 0;
  for (const mesh of meshes) {
    const geometry = mesh.geometry;
    triangles += geometry.index
      ? geometry.index.count / 3
      : (geometry.getAttribute("position")?.count ?? 0) / 3;
  }

  const runtime: CodexSolSculptRuntime = {
    parts,
    nodes,
    meshes,
    destructionGroups: {
      blade: ["outerShell", "purpleCore", "magentaSpine"],
      guard: [
        "centralHub",
        "leftGuardWing",
        "rightGuardWing",
        "leftFitting",
        "rightFitting",
        "rodFan",
      ],
      handle: ["grip", "pommel"],
    },
    setExplode,
    getPart: (id) => nodes[id],
    stats: { parts: parts.length, meshes: meshes.length, triangles: Math.round(triangles) },
  };

  root.userData.sculptRuntime = runtime;
  return root;
}
