from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "object-sculpt-spec.json"
INVENTORY_PATH = HERE / "detail-inventory" / "di.json"


def rgba(hex_color: str, alpha: float = 1.0) -> str:
    value = hex_color.lstrip("#")
    red, green, blue = (int(value[index : index + 2], 16) for index in (0, 2, 4))
    return f"rgba({red}, {green}, {blue}, {alpha})"


def material(
    material_id: str,
    name: str,
    base: str,
    secondary: list[str],
    roughness: float,
    metalness: float,
    *,
    shader: str = "MeshStandardMaterial",
    overrides: list[dict] | None = None,
    notes: str,
) -> dict:
    palette = [base, *secondary]
    return {
        "id": material_id,
        "name": name,
        "type": "physical" if shader == "MeshPhysicalMaterial" else "standard",
        "shaderModel": shader,
        "baseColor": base,
        "color": base,
        "albedo": {
            "dominant": base,
            "secondary": secondary,
            "samplingNotes": "Palette follows visible flat-shaded color zones; edge antialiasing is excluded.",
        },
        "colorVariation": {
            "palette": palette,
            "pattern": "faceted longitudinal bands",
            "amplitude": 0.12,
            "heightCorrelation": 0.0,
        },
        "textureResolution": 1024,
        "textureProjection": {
            "mode": "generated-object-space",
            "repeat": [1.0, 1.0],
            "anisotropy": 4,
            "texelDensityIntent": "Keep faceted color bands stable in object space without raster-edge detail.",
        },
        "surfaceFrequencyBands": [
            {"id": "macro", "frequency": 1.0, "amplitude": 0.12, "role": "observed regional albedo separation"},
            {"id": "meso", "frequency": 6.0, "amplitude": 0.03, "role": "face-to-face value change"},
            {"id": "micro", "frequency": 32.0, "amplitude": 0.01, "role": "minimal highlight breakup; reference interiors are flat"},
        ],
        "roughness": {
            "base": roughness,
            "variation": 0.05,
            "map": "independent-procedural-field",
            "localResponse": "small face variation only; no contour aliasing encoded",
        },
        "metalness": {"base": metalness, "variation": 0.02 if metalness else 0.0},
        "normal": {
            "pattern": "independent-low-amplitude-fine-field",
            "strength": 0.04,
            "scale": 32.0,
            "space": "tangent",
        },
        "bump": {"pattern": "none", "amplitude": 0.0, "scale": 1.0},
        "displacement": {"pattern": "none", "amplitude": 0.0, "scale": 1.0, "silhouetteAffects": False},
        "ambientOcclusion": {
            "cavityStrength": 0.18,
            "contactShadowBias": 0.35,
            "map": "independent-contact-field",
            "notes": "Restrict AO to overlaps at blade root, rod sockets, fittings, and grip socket.",
        },
        "wear": {"edgeWear": 0.0, "scratches": [], "chips": []},
        "dirt": {"amount": 0.0, "cavityBias": 0.0, "color": "#17151A"},
        "localOverrides": overrides or [],
        "shaderNotes": [
            notes,
            "Albedo, roughness, normal, and ambient occlusion are independent fields.",
            "Do not convert antialiasing steps from the 146x292 reference into height or normal relief.",
        ],
        "notes": notes,
    }


def feature(feature_id: str, kind: str, description: str) -> dict:
    return {
        "id": feature_id,
        "kind": kind,
        "description": description,
        "evidenceRefs": ["full-object"],
    }


def component(
    component_id: str,
    name: str,
    level: str,
    parent: str | None,
    material_id: str,
    primitive: str,
    topology_class: str,
    topology_rationale: str,
    dimensions: tuple[float, float, float],
    position: tuple[float, float, float],
    *,
    role: str = "body",
    confidence: float = 0.8,
    local_features: list[dict] | None = None,
    material_class: str = "plastic",
) -> dict:
    width, height, depth = dimensions
    attachment = None
    if parent:
        attachment = {
            "parentId": parent,
            "parentSocket": f"{parent}-socket",
            "contactType": "overlap",
            "localStart": [0.0, -height / 2, 0.0],
            "localEnd": [0.0, height / 2, 0.0],
            "contactNormal": [0.0, 1.0, 0.0],
            "embedDepth": 0.03,
            "overlap": 0.03,
            "gapTolerance": 0.01,
            "baseRadius": max(0.02, width / 2),
            "endRadius": max(0.02, width / 2),
        }
    return {
        "id": component_id,
        "name": name,
        "level": level,
        "role": role,
        "importance": 1.0 if level == "macro" else 0.8,
        "confidence": confidence,
        "primitive": primitive,
        "topologyClass": topology_class,
        "topologyRationale": topology_rationale,
        "geometryDescriptor": {
            "topologyIntent": "low-poly hard-surface prop with stable named pivot",
            "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.02, "segments": 1},
            "deformationStack": [],
            "uvStrategy": "generated object-space coordinates",
            "normalStrategy": "flat or weighted vertex normals matching visible facets",
        },
        "colorMaterialRecipe": {
            "dominantAlbedo": rgba(MATERIAL_COLORS[material_id][0]),
            "secondaryAlbedo": rgba(MATERIAL_COLORS[material_id][1]),
            "materialClass": material_class,
            "materialClassConfidence": confidence,
            "colorGradient": {
                "type": "linear",
                "axis": "long-axis",
                "stops": [
                    {"position": 0.0, "color": rgba(MATERIAL_COLORS[material_id][0])},
                    {"position": 1.0, "color": rgba(MATERIAL_COLORS[material_id][1])},
                ],
            },
            "evidenceRefs": ["full-object"],
        },
        "parent": parent,
        "attachment": attachment,
        "dimensions": {
            "width": width,
            "height": height,
            "depth": depth,
            "units": "relative",
            "confidence": confidence,
        },
        "transform": {"position": list(position), "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
        "actionProfile": {
            "animationRole": "root" if parent is None else "detachable-part",
            "pivot": {"mode": "center", "localPosition": [0.0, 0.0, 0.0], "axis": [0.0, 1.0, 0.0], "confidence": confidence},
            "transformChannels": {"translate": True, "rotate": True, "scale": True, "bend": False, "twist": False, "detach": parent is not None, "visibility": True, "materialState": True},
            "sockets": [{"id": f"{component_id}-socket", "localPosition": [0.0, 0.0, 0.0], "localRotation": [0.0, 0.0, 0.0]}],
            "collider": {"type": "box", "offset": [0.0, 0.0, 0.0], "scale": [width, height, depth], "isTrigger": False, "notes": "Conservative compound proxy."},
            "constraints": [],
            "destruction": {"breakable": parent is not None, "fractureGroup": component_id, "seamRefs": [], "detachableFragments": [component_id] if parent else [], "breakImpulse": 1.0 if parent else 0.0, "debrisMaterial": material_id},
        },
        "material": material_id,
        "materialLayers": [material_id],
        "deformations": [],
        "joints": [],
        "seams": [],
        "localFeatures": local_features or [],
        "surfaceDetail": {
            "macroRoughness": 0.12,
            "microRoughness": 0.03,
            "bumpAmplitude": 0.01,
            "normalPattern": "low-amplitude independent field",
            "displacementPattern": "none",
            "occlusionPattern": "contact-only",
            "edgeWearPattern": "none visible",
            "notes": "Faceted color and real profile geometry carry the visible detail.",
        },
        "evidenceRefs": ["full-object"],
        "details": [],
        "fidelityTier": "hero" if level == "macro" else "detail",
    }


MATERIAL_COLORS = {
    "outerShellMaterial": ("#E7EAF4", "#BEC8E0"),
    "purpleCoreMaterial": ("#241B82", "#7650D8"),
    "magentaSpineMaterial": ("#6B153C", "#AE2E76"),
    "guardMaterial": ("#111116", "#35313A"),
    "rodMaterial": ("#5A1024", "#9A2748"),
    "fittingMaterial": ("#62634A", "#8C8B62"),
    "gripMaterial": ("#0D0D12", "#34343D"),
}


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text())
    inventory = json.loads(INVENTORY_PATH.read_text())["detailInventory"]

    spec["targetId"] = "codexSolUltimaWeapon"
    spec["referenceCamera"] = {
        "solved": False,
        "fovDegrees": 30.0,
        "aspect": 0.5,
        "orientation": {"yaw": 8.0, "pitch": -3.0, "roll": -17.5},
        "positionHint": [0.45, 0.1, 8.0],
        "note": "Single shallow three-quarter view; roll and shallow yaw are visually estimated and must be overlay-reviewed.",
    }
    spec["suitability"] = "conditional"
    spec["scores"] = {
        "object_isolation": 3,
        "silhouette_readability": 3,
        "depth_inference": 1,
        "primitive_decomposition": 3,
        "material_procedurality": 2,
        "occlusion_risk": 2,
        "interaction_fit": 3,
    }
    spec["preSpecAssessment"]["detailInventory"] = inventory
    spec["preSpecAssessment"]["unknownsToResolveBeforeImplementation"] = []
    spec["resolvedUncertainties"] = {
        "rearFaces": "Use mirrored front profiles.",
        "thickness": "Use conservative shallow extrusions and verify from side views.",
        "shellTransmission": "Use low transmission with opacity high enough to preserve the core silhouette.",
        "fittingMetalness": "Use conservative partial metalness because no diagnostic highlight is visible.",
        "croppedHandle": "Continue the straight grip to a compact inferred pommel.",
    }
    spec["assumptions"] = [
        "Rear faces mirror the visible front profile.",
        "Blade and guard use shallow thickness because no side view exists.",
        "The cropped grip continues straight and ends in a compact dark pommel.",
        "Raster edge steps are antialiasing rather than physical relief.",
    ]
    spec["coordinateFrame"] = {
        "front": "+Z faces the reference camera",
        "up": "+Y follows the weapon shaft from grip to blade tip",
        "scaleReference": "visible object height is 8.0 world units",
    }
    spec["silhouette"] = {
        "boundingShape": "elongated layered blade with a wide radial guard and narrow cropped grip",
        "aspectRatios": ["visible height:maximum guard width = 4.0:1", "outer shell width:core width = 1.75:1"],
        "symmetry": "bilateral in object space; shallow yaw creates projected asymmetry",
        "dominantCurves": ["outer shell convex lateral taper", "pointed purple core", "three-angle radial rod fans"],
        "negativeSpaces": ["core notch around magenta spine", "gaps between rod instances", "gap between guard wings and grip"],
        "landmarks": ["shell apex", "core apex", "core lower notch", "rod radiation center", "guard lower fittings", "grip axis"],
    }
    spec["viewEvidence"] = [{
        "id": "full-object",
        "view": "primary shallow three-quarter",
        "imageRegion": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0, "units": "normalized"},
        "observations": [
            "Pale shell encloses a narrower purple core.",
            "Six crimson rods radiate from below the blade root.",
            "Dark guard wings terminate in olive fittings.",
            "Grip and extreme tip are constrained by the image crop and low resolution.",
        ],
        "confidence": 0.82,
    }]

    shell_features = [
        feature("apexContour", "contour", "Rounded offset shell apex."),
        feature("lateralRim", "bevel", "Narrow darker lateral shell rim."),
    ]
    core_features = [
        feature("tipFacet", "bevel", "Darker and brighter core tip facets."),
        feature("lowerProngNotch", "groove", "Open notch dividing the two lower core prongs."),
    ]
    spine_features = [feature("axialWedge", "ridge", "Magenta wedge rising through the core notch.")]
    guard_features = [
        feature("leftRodFan", "ridge", "Three left radial rods."),
        feature("rightRodFan", "ridge", "Three right radial rods."),
        feature("rodRootEmbed", "seam", "Rod roots overlap the hub by 0.03 world units."),
    ]

    spec["materials"] = [
        material("outerShellMaterial", "Pale translucent outer shell", "#E7EAF4", ["#BEC8E0", "#F7F8FC"], 0.38, 0.0, shader="MeshPhysicalMaterial", overrides=[{"id": "edgeBand", "region": "lateral shell rim", "baseColor": "#BEC8E0", "roughness": 0.46, "evidenceRefs": ["full-object"]}], notes="Use transmission 0.18, opacity 0.72, clearcoat 0.18, and depthWrite true for a readable layered silhouette."),
        material("purpleCoreMaterial", "Faceted purple core", "#241B82", ["#4A2AAE", "#7650D8"], 0.3, 0.0, shader="MeshPhysicalMaterial", overrides=[{"id": "longitudinalBand", "region": "right longitudinal facet", "baseColor": "#7650D8", "roughness": 0.25, "evidenceRefs": ["full-object"]}], notes="Opaque saturated core with low clearcoat and longitudinal vertex-color facets."),
        material("magentaSpineMaterial", "Magenta axial spine", "#6B153C", ["#AE2E76"], 0.4, 0.0, notes="Opaque red-violet wedge; no emission is evidenced."),
        material("guardMaterial", "Dark guard", "#111116", ["#35313A"], 0.62, 0.45, notes="Dark gunmetal approximation; preserve readable face normals without mirror-like highlights."),
        material("rodMaterial", "Crimson rods", "#5A1024", ["#9A2748"], 0.48, 0.2, notes="Three rods per side share dimensions but use alternating face values."),
        material("fittingMaterial", "Muted olive fittings", "#62634A", ["#8C8B62"], 0.68, 0.35, overrides=[{"id": "guardEndCaps", "region": "lower guard wing caps", "baseColor": "#8C8B62", "roughness": 0.72, "evidenceRefs": ["full-object"]}], notes="Metalness is conservative because the reference contains no diagnostic highlight."),
        material("gripMaterial", "Dark grip", "#0D0D12", ["#34343D"], 0.58, 0.15, overrides=[{"id": "lateralHighlight", "region": "front-lateral grip face", "baseColor": "#34343D", "roughness": 0.42, "evidenceRefs": ["full-object"]}], notes="Long dark grip with one narrow lighter face band."),
    ]

    spec["componentTree"] = [
        component("codexSolUltimaWeapon", "Codex Sol Ultima Weapon", "macro", None, "guardMaterial", "box", "assembled-solid", "Root pivot spans the complete rigid prop and carries no organic curvature.", (2.2, 8.0, 0.34), (0.0, 0.0, 0.0), confidence=0.95, material_class="metal"),
        component("bladeAssembly", "Blade assembly", "macro", "codexSolUltimaWeapon", "outerShellMaterial", "extrude", "conforming-shell", "Layered shallow blade envelope follows the inset core profile.", (1.35, 5.6, 0.22), (0.0, 1.35, 0.0), role="blade", confidence=0.88, material_class="glass"),
        component("guardAssembly", "Guard assembly", "macro", "codexSolUltimaWeapon", "guardMaterial", "box", "assembled-solid", "Discrete guard blocks and hub have countable hard faces.", (2.2, 1.25, 0.34), (0.0, -1.72, 0.0), role="guard", confidence=0.86, local_features=guard_features, material_class="metal"),
        component("handleAssembly", "Handle assembly", "macro", "codexSolUltimaWeapon", "gripMaterial", "box", "assembled-solid", "Straight rigid grip and pommel form a discrete assembly.", (0.32, 2.2, 0.3), (0.0, -3.05, 0.0), role="handle", confidence=0.62, material_class="plastic"),
        component("outerShell", "Outer blade shell", "meso", "bladeAssembly", "outerShellMaterial", "extrude", "conforming-shell", "Thin pale shell follows the blade profile around the purple core.", (1.35, 5.6, 0.18), (0.0, 0.0, 0.0), role="blade", confidence=0.9, local_features=shell_features, material_class="glass"),
        component("purpleCore", "Purple energy core", "meso", "bladeAssembly", "purpleCoreMaterial", "extrude", "assembled-solid", "Faceted tapered slab has hard planar faces and a real lower notch.", (0.78, 4.55, 0.2), (0.0, -0.25, 0.04), role="blade", confidence=0.9, local_features=core_features, material_class="plastic"),
        component("magentaSpine", "Magenta central spine", "meso", "bladeAssembly", "magentaSpineMaterial", "extrude", "assembled-solid", "Narrow rigid wedge bridges the hub and core notch.", (0.26, 1.4, 0.24), (0.0, -2.0, 0.08), role="connector", confidence=0.88, local_features=spine_features, material_class="plastic"),
        component("centralHub", "Central guard hub", "meso", "guardAssembly", "guardMaterial", "box", "assembled-solid", "Compact faceted connector surrounds the shaft and covers rod roots.", (0.68, 0.7, 0.36), (0.0, 0.1, 0.0), role="connector", confidence=0.82, material_class="metal"),
        component("leftGuardWing", "Left guard wing", "meso", "guardAssembly", "guardMaterial", "extrude", "assembled-solid", "Polygonal rigid plate projects laterally and downward.", (0.72, 0.86, 0.3), (-0.62, -0.15, 0.0), role="wing", confidence=0.8, material_class="metal"),
        component("rightGuardWing", "Right guard wing", "meso", "guardAssembly", "guardMaterial", "extrude", "assembled-solid", "Polygonal rigid plate mirrors the left wing in object space.", (0.72, 0.86, 0.3), (0.62, -0.15, 0.0), role="wing", confidence=0.78, material_class="metal"),
        component("leftFitting", "Left olive fitting", "meso", "leftGuardWing", "fittingMaterial", "extrude", "assembled-solid", "Discrete polygonal cap overlaps the lower wing edge.", (0.38, 0.52, 0.32), (-0.08, -0.58, 0.0), role="connector", confidence=0.82, material_class="metal"),
        component("rightFitting", "Right olive fitting", "meso", "rightGuardWing", "fittingMaterial", "extrude", "assembled-solid", "Discrete polygonal cap mirrors the left fitting.", (0.38, 0.52, 0.32), (0.08, -0.58, 0.0), role="connector", confidence=0.8, material_class="metal"),
        component("rodFan", "Six-rod radial fan", "meso", "guardAssembly", "rodMaterial", "instanced-cluster", "fiber-strand", "Six long thin repeated rods radiate from one hub-centered distribution.", (2.0, 0.7, 0.16), (0.0, 0.12, -0.04), role="connector", confidence=0.88, material_class="metal"),
        component("grip", "Main grip", "meso", "handleAssembly", "gripMaterial", "box", "assembled-solid", "Long rigid dark grip has countable planar faces.", (0.24, 2.0, 0.26), (0.0, 0.0, 0.0), role="handle", confidence=0.64, material_class="plastic"),
        component("gripAccent", "Grip lateral highlight carrier", "meso", "handleAssembly", "gripMaterial", "plane-card", "material-only", "Thin carrier represents the observed lighter lateral face band without adding unsupported relief.", (0.04, 1.8, 0.01), (0.12, 0.0, 0.14), role="body", confidence=0.62, material_class="plastic"),
        component("pommel", "Compact pommel", "meso", "handleAssembly", "gripMaterial", "box", "assembled-solid", "Small inferred terminal block closes the cropped grip conservatively.", (0.34, 0.28, 0.32), (0.0, -1.12, 0.0), role="connector", confidence=0.32, material_class="plastic"),
    ]

    spec["repetitionSystems"] = [{
        "id": "sixRodRadialFan",
        "componentRef": "rodFan",
        "realization": "instanced-geometry",
        "buildsGeometry": True,
        "geometry": {"primitive": "box", "dimensions": [0.12, 0.78, 0.12], "material": "rodMaterial"},
        "instances": [
            {"side": -1, "angleDegrees": 26, "lengthScale": 0.88},
            {"side": -1, "angleDegrees": 8, "lengthScale": 1.0},
            {"side": -1, "angleDegrees": -12, "lengthScale": 0.94},
            {"side": 1, "angleDegrees": -26, "lengthScale": 0.88},
            {"side": 1, "angleDegrees": -8, "lengthScale": 1.0},
            {"side": 1, "angleDegrees": 12, "lengthScale": 0.94},
        ],
        "distribution": "bilateral three-angle fan around a center 0.12 units below the blade root",
        "evidenceRefs": ["full-object"],
    }]

    spec["proceduralStrategy"] = [
        "Extrude independent shell, core, spine, and guard profiles from explicit object-space points.",
        "Represent the shell rim and core facet band with shallow profile layers and vertex colors, not downloaded textures.",
        "Build the rod fan from one deterministic box geometry cloned at six recorded angles.",
        "Keep every macro and meso part under its own pivot group for selection and explode transforms.",
        "Use conservative shallow depth for hidden thickness and mirrored back faces.",
        "Use independent PBR parameters and contact-only AO; do not derive normal relief from raster edges.",
    ]
    spec["lightingFromPhoto"] = [
        "Reference key light is broad, cool-white, camera-left/front with intensity 2.4.",
        "Fill light is neutral front-right with intensity 1.1 to preserve dark guard faces.",
        "A cool rim light behind the blade separates the pale shell edge.",
        "Ambient environment color is #E9ECF5 at intensity 0.65.",
        "ACESFilmic tone mapping, exposure 1.05, white background, and soft contact shadow below the cropped grip.",
    ]
    spec["lookDevTargets"]["materialPass"]["referencePbrExtraction"]["acceptedLimitation"] = (
        "The 146x292 flat-shaded source bakes lighting and antialiasing into all visible edges; extracted normal/height maps would encode raster steps. Use observed palettes and independent procedural roughness/AO instead."
    )
    spec["lookDevTargets"]["materialPass"]["referencePbrExtraction"]["requiredWhenSourceImagePresent"] = False
    spec["featureReviewTargets"] = [
        {"id": "blade-envelope-core", "name": "Pale shell and inset purple core silhouette", "tier": "critical", "passIds": ["blockout", "form-refinement"], "minimumScore": 0.8, "mustPass": True, "componentRefs": ["outerShell", "purpleCore", "magentaSpine"], "evidenceRefs": ["full-object"]},
        {"id": "guard-wing-proportions", "name": "Bilateral dark guard wings and olive end fittings", "tier": "critical", "passIds": ["blockout", "structural-pass", "form-refinement"], "minimumScore": 0.8, "mustPass": True, "componentRefs": ["guardAssembly", "leftGuardWing", "rightGuardWing", "leftFitting", "rightFitting"], "evidenceRefs": ["full-object"]},
        {"id": "rod-fan-origin", "name": "Six crimson rods sharing the low radiation center", "tier": "critical", "passIds": ["structural-pass", "form-refinement"], "minimumScore": 0.82, "mustPass": True, "componentRefs": ["rodFan", "centralHub"], "evidenceRefs": ["full-object"]},
        {"id": "material-separation", "name": "Seven observed material/color systems remain separable", "tier": "critical", "passIds": ["material-pass", "surface-pass", "lighting-pass"], "minimumScore": 0.78, "mustPass": True, "componentRefs": ["outerShell", "purpleCore", "magentaSpine", "guardAssembly", "rodFan", "leftFitting", "grip"], "evidenceRefs": ["full-object"]},
        {"id": "action-ready-hierarchy", "name": "Explodable and selectable named assemblies", "tier": "important", "passIds": ["structural-pass", "interaction-pass", "optimization-pass"], "minimumScore": 0.7, "mustPass": False, "componentRefs": ["bladeAssembly", "guardAssembly", "handleAssembly"], "evidenceRefs": ["full-object"]},
    ]
    spec["qualityTargets"]["reviewViewpoints"] = ["reference", "front", "side", "three-quarter", "exploded-three-quarter"]
    spec["actionReadiness"]["rootMotionNode"] = "codexSolUltimaWeapon"

    pass_components = {
        "blockout": ["codexSolUltimaWeapon", "bladeAssembly", "guardAssembly", "handleAssembly"],
        "structural-pass": [item["id"] for item in spec["componentTree"]],
        "form-refinement": ["outerShell", "purpleCore", "magentaSpine", "leftGuardWing", "rightGuardWing", "leftFitting", "rightFitting", "rodFan", "grip"],
        "material-pass": ["outerShell", "purpleCore", "magentaSpine", "guardAssembly", "rodFan", "leftFitting", "rightFitting", "grip"],
        "surface-pass": ["outerShell", "purpleCore", "magentaSpine", "guardAssembly", "rodFan", "grip"],
        "lighting-pass": ["codexSolUltimaWeapon"],
        "interaction-pass": ["bladeAssembly", "guardAssembly", "handleAssembly"],
        "optimization-pass": ["codexSolUltimaWeapon", "rodFan"],
    }
    for build_pass in spec["buildPasses"]:
        build_pass["componentRefs"] = pass_components[build_pass["id"]]

    spec["animationAnchors"] = [
        {"id": "weaponRoot", "componentRef": "codexSolUltimaWeapon", "localPosition": [0.0, 0.0, 0.0], "purpose": "whole-object transform"},
        {"id": "gripSocket", "componentRef": "handleAssembly", "localPosition": [0.0, -0.2, 0.0], "purpose": "future hand attachment"},
    ]
    spec["destructionAnchors"] = [
        {"id": "bladeGuardSeam", "componentRefs": ["bladeAssembly", "guardAssembly"], "localPosition": [0.0, -1.5, 0.0]},
        {"id": "guardHandleSeam", "componentRefs": ["guardAssembly", "handleAssembly"], "localPosition": [0.0, -2.0, 0.0]},
    ]

    assert len(spec["materials"]) == 7
    assert sum(item["level"] == "macro" for item in spec["componentTree"]) >= 3
    assert sum(item["level"] == "meso" for item in spec["componentTree"]) >= 8
    required_micro = spec["qualityContract"]["minimumSpecDepth"]["microFeatureGroups"]
    assert sum(len(item["localFeatures"]) for item in spec["componentTree"]) >= required_micro
    assert len(spec["preSpecAssessment"]["detailInventory"]["details"]) >= 10
    SPEC_PATH.write_text(json.dumps(spec, indent=2) + "\n")


if __name__ == "__main__":
    main()
