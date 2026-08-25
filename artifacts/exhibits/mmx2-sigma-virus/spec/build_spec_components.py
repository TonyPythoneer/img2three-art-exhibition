#!/usr/bin/env python3
"""Author the Sigma Virus Head component tree into object-sculpt-spec.json.

Task 4 Step 2 of docs/superpowers/plans/2026-08-21-sigma-virus-rebuild.md.
Part table = componentTree names; measured px -> units with 69 px = 1.0 height.
Rerunnable: python3 build_spec_components.py (idempotent; rewrites componentTree).
"""
import json

spec = json.load(open("object-sculpt-spec.json"))


def comp(cid, name, level, role, primitive, topo, topo_why, dims, pos,
         material, evidence, attachment=None, local_features=None,
         rotation=None, extra_geom=None, confidence=0.8, importance=1.0):
    return {
        "id": cid, "name": name, "level": level, "role": role,
        "importance": importance, "confidence": confidence,
        "primitive": primitive,
        "topologyClass": topo,
        "topologyRationale": topo_why,
        "geometryDescriptor": dict(
            {
                "topologyIntent": "low-poly faceted shells; facet seams drawn as edge lines in the factory contract",
                "edgeTreatment": {"type": "none", "bevelRadius": 0.0, "segments": 1},
                "deformationStack": [],
                "uvStrategy": "generated procedural coordinates",
                "normalStrategy": "vertex normals from generated geometry",
            },
            **(extra_geom or {}),
        ),
        "parent": "root" if cid != "root" else None,
        "attachment": attachment,
        "dimensions": {"width": dims[0], "height": dims[1], "depth": dims[2],
                       "units": "relative", "confidence": confidence},
        # NOTE: no "scale" key here on purpose -- generate_threejs_factory.scale_vector()
        # prefers transform.scale over dimensions, and a template-style [1,1,1] would
        # bake every component's geometry to unit size (found by inspecting the first
        # generated-factory.ts where every Geometry.scale read 1.0, 1.0, 1.0).
        "transform": {"position": pos, "rotation": rotation or [0, 0, 0]},
        "actionProfile": {
            "animationRole": role,
            "pivot": {"mode": "center", "localPosition": [0, 0, 0], "axis": [0, 1, 0], "confidence": 0.8},
            "transformChannels": {"translate": True, "rotate": True, "scale": True,
                                  "bend": False, "twist": False, "detach": False,
                                  "visibility": True, "materialState": True},
            "sockets": [],
            "collider": {"type": "box", "offset": [0, 0, 0],
                         "scale": [dims[0], dims[1], dims[2]], "isTrigger": False,
                         "notes": "simplified box proxy sized to component dimensions"},
            "constraints": [],
            "destruction": {"breakable": False, "fractureGroup": cid,
                            "seamRefs": [], "detachableFragments": [],
                            "breakImpulse": 0.0, "debrisMaterial": material},
        },
        "material": material,
        "materialLayers": [material],
        "deformations": [],
        "joints": [],
        "seams": [],
        "localFeatures": local_features or [],
        "surfaceDetail": {
            "macroRoughness": 0.95, "microRoughness": 0.9,
            "bumpAmplitude": 0.0, "normalPattern": "", "displacementPattern": "",
            "occlusionPattern": "cavity shading inside the face pocket",
            "edgeWearPattern": "", "notes": "flat wire-art fills; relief is geometry, not maps",
        },
        "evidenceRefs": evidence,
        "details": [],
        "fidelityTier": "blockout",
    }


def attach(socket, start, end, contact="overlap", embed=0.03, gap=0.02):
    return {"parentSocket": socket, "localStart": start, "localEnd": end,
            "contactType": contact, "embedDepth": embed, "gapTolerance": gap}


def feat(fid, name, desc, evidence):
    return {"id": fid, "name": name, "kind": "linework",
            "description": desc, "evidenceRefs": evidence}


E_FRONT = ["spec/refs/front.png", "spec/measurements.json"]
E_TOP = ["spec/refs/top.png"]
E_SIDE = ["spec/refs/side.png"]
E_YAW = ["spec/refs/green-yaw.png"]

root = comp("root", "Sigma Virus Head", "macro", "body", "box", "assembled-solid",
            "Root pivot container carrying identity scale; dimensions are baked into child components per the generator WS-E contract.",
            (0.681, 1.0, 0.885), [0, 0, 0], "groundNavy", E_FRONT, confidence=0.85)

crown = comp("crown", "Crown Shell", "meso", "shell", "ellipsoid", "continuous-sculpt",
             "One sculpted faceted dome volume; ellipsoid is an allowed continuous-sculpt primitive and faceting comes from edge-line seams plus the flat material family.",
             (0.58, 0.30, 0.62), [0, 0.36, -0.06], "groundNavy", E_FRONT + E_YAW + E_TOP,
             local_features=[feat("ridgeSeam", "front-to-back crown ridge seam",
                                  "Facet lines converge to a short front-to-back ridge peak on the dome; reads as a peaked seam from oblique angles.",
                                  ["spec/zoom/wide0.png", "spec/fresh-zoom-scan.md"])],
             confidence=0.85)

forehead = comp("forehead", "Forehead Shell", "meso", "shell", "box", "assembled-solid",
                "Forward slab of the cranial shell above the brow ledge; a planar block is its measured form.",
                (0.50, 0.26, 0.52), [0, 0.17, -0.02], "groundNavy", E_FRONT + E_YAW,
                attachment=attach("crown/base-seam", [0, 0.04, -0.02], [0, -0.06, -0.02]))

temple_l = comp("templeShellL", "Left Temple Shell", "meso", "shell", "box", "assembled-solid",
                "Angular side shell at mid height; rotated prism matching the left silhouette band.",
                (0.12, 0.26, 0.40), [-0.26, 0.13, -0.05], "groundNavy", E_FRONT + E_SIDE,
                attachment=attach("forehead/side-seam-L", [-0.20, 0.13, -0.05], [-0.30, 0.10, -0.05]),
                rotation=[0, 0, 8])
temple_r = comp("templeShellR", "Right Temple Shell", "meso", "shell", "box", "assembled-solid",
                "Mirrored right temple shell (shape code shared with templeShellL).",
                (0.12, 0.26, 0.40), [0.26, 0.13, -0.05], "groundNavy", E_FRONT + E_SIDE,
                attachment=attach("forehead/side-seam-R", [0.20, 0.13, -0.05], [0.30, 0.10, -0.05]),
                rotation=[0, 0, -8])

cheek_geom = {"profile2D": {"points": [[-0.11, -0.16], [0.11, -0.16], [0.11, 0.10],
                                        [0.03, 0.16], [-0.07, 0.14]], "depth": 0.30}}
cheek_l = comp("cheekShellL", "Left Cheek Lobe", "meso", "plate", "extrude", "assembled-solid",
               "Independent angular lobe plate overlapping the cranial shell; forms the widest silhouette band.",
               (0.22, 0.32, 0.30), [-0.27, -0.06, -0.02], "groundNavy", E_FRONT + E_YAW,
               attachment=attach("cranial-shell/lobe-socket-L", [-0.18, -0.06, -0.02], [-0.34, -0.08, -0.02], embed=0.04),
               local_features=[feat("overlapSeam", "cheek-lobe overlap seam",
                                    "The lobe is its own shell plate overlapping the cranial shell; seam visible where it crosses the temple shell.",
                                    ["spec/zoom/green_zone.png"])],
               rotation=[0, -10, 0], extra_geom=cheek_geom)
cheek_r = comp("cheekShellR", "Right Cheek Lobe", "meso", "plate", "extrude", "assembled-solid",
               "Mirrored right cheek lobe (shape code shared with cheekShellL).",
               (0.22, 0.32, 0.30), [0.27, -0.06, -0.02], "groundNavy", E_FRONT + E_YAW,
               attachment=attach("cranial-shell/lobe-socket-R", [0.18, -0.06, -0.02], [0.34, -0.08, -0.02], embed=0.04),
               local_features=[feat("overlapSeam", "cheek-lobe overlap seam (mirrored)",
                                    "Same plate-over-shell seam as the left side.",
                                    ["spec/zoom/green_zone.png"])],
               rotation=[0, 10, 0], extra_geom=cheek_geom)

cavity_sdf = {"sdf": {
    "primitives": [
        {"id": "faceBlock", "type": "box", "size": [0.42, 0.34, 0.30], "center": [0, -0.09, 0.16]},
        {"id": "pocketCut", "type": "box", "size": [0.36, 0.28, 0.20], "center": [0, -0.09, 0.28]},
    ],
    "operations": [
        {"id": "carvePocket", "type": "subtract", "left": "faceBlock", "right": "pocketCut"}
    ],
}}
cavity = comp("faceCavity", "Face Cavity", "meso", "recessed-face-panel", "implicit", "implicit",
              "A real recessed pocket: implicit SDF face block minus a forward pocket cut (gate US-004 requires topologyClass 'implicit' with a subtract operation for any cavity-named part; G2 eyes recessed).",
              (0.42, 0.34, 0.31), [0, -0.09, 0.16], "groundNavy", E_FRONT + E_YAW,
              attachment=attach("forehead/brow-undercut", [0, 0.03, 0.16], [0, 0.08, 0.10]),
              extra_geom=cavity_sdf, confidence=0.75)

eye_geom = {"profile2D": {"points": [[-0.075, 0.0], [-0.045, 0.028], [0.0, 0.036],
                                      [0.05, 0.022], [0.075, -0.004], [0.03, -0.03],
                                      [-0.02, -0.034]], "depth": 0.02}}
eye_l = comp("eyePlateL", "Left Eye Plate", "meso", "accent-outline", "extrude", "assembled-solid",
             "Slanted almond accent outline sitting on the cavity floor, angled down toward the centre.",
             (0.15, 0.08, 0.03), [-0.105, 0.01, 0.19], "eyesAccent", E_FRONT + E_YAW,
             attachment=attach("faceCavity/pocket-floor-L", [-0.105, 0.01, 0.19], [-0.105, 0.01, 0.185], embed=0.01),
             local_features=[feat("eyeOutline", "almond eye outline",
                                  "Slanted leaf outline in #E05000; outlines sit inside the silhouette in every yaw (G2 recessed).",
                                  ["spec/zoom/geom_63_1811.png"])],
             rotation=[0, 0, -12], extra_geom=eye_geom)
eye_r = comp("eyePlateR", "Right Eye Plate", "meso", "accent-outline", "extrude", "assembled-solid",
             "Mirrored right eye plate (shape code shared with eyePlateL).",
             (0.15, 0.08, 0.03), [0.105, 0.01, 0.19], "eyesAccent", E_FRONT + E_YAW,
             attachment=attach("faceCavity/pocket-floor-R", [0.105, 0.01, 0.19], [0.105, 0.01, 0.185], embed=0.01),
             local_features=[feat("eyeOutline", "almond eye outline (mirrored)",
                                  "Mirror of the left almond outline.",
                                  ["spec/zoom/geom_63_1811.png"])],
             rotation=[0, 0, 12], extra_geom=eye_geom)

bridge = comp("midFaceBridge", "Mid-Face Bridge", "meso", "ridge", "box", "assembled-solid",
              "Central vertical ridge below the eye bridge ending above the nose tip.",
              (0.05, 0.30, 0.08), [0, -0.11, 0.24], "groundNavy", E_FRONT,
              attachment=attach("faceCavity/pocket-centre", [0, -0.02, 0.24], [0, 0.06, 0.22]),
              local_features=[feat("noseRidge", "nose ridge line",
                                   "Single centre vertical line below the eye bridge ending in a small triangular tip around 70% height.",
                                   ["spec/zoom/geom_63_1811.png"])])

jaw_geom = {"profile2D": {"points": [[-0.18, 0.15], [0.18, 0.15], [0.105, -0.135],
                                      [0.03, -0.15], [0.0, -0.12], [-0.03, -0.15],
                                      [-0.105, -0.135]], "depth": 0.40}}
jaw = comp("lowerFaceJaw", "Lower Face Jaw", "meso", "jaw", "extrude", "assembled-solid",
           "Trapezoid chin plate tapering from the cheek band, with the centre notch cut into its bottom profile edge and a mouth seam across its top third.",
           (0.36, 0.32, 0.40), [0, -0.345, 0.06], "groundNavy", E_FRONT + E_SIDE,
           attachment=attach("faceCavity/jaw-seam", [0, -0.24, 0.06], [0, -0.19, 0.06]),
           local_features=[
               feat("chinNotch", "chin centre notch",
                    "Small centre notch in the bottom edge of the trapezoid chin plate.",
                    ["spec/zoom/geom_63_1811.png"]),
               feat("mouthBand", "mouth band seam",
                    "Horizontal seam ~75-80% height between nose tip and chin plate.",
                    ["spec/zoom/geom_63_1811.png"]),
           ],
           extra_geom=jaw_geom)

tab_geom = {"profile2D": {"points": [[-0.05, -0.05], [0.05, -0.05], [0.05, 0.05],
                                      [-0.05, 0.05]], "depth": 0.12}}
tab_l = comp("chinTabL", "Left Chin Tab", "meso", "tab", "extrude", "assembled-solid",
             "Independent small tab hanging under the jaw's left underside (G3: independent plates, not a jaw continuation).",
             (0.10, 0.10, 0.12), [-0.085, -0.46, 0.05], "groundNavy", E_FRONT,
             attachment=attach("lowerFaceJaw/chin-underside-L", [-0.04, -0.44, 0.05], [-0.09, -0.50, 0.05]),
             extra_geom=tab_geom)
tab_r = comp("chinTabR", "Right Chin Tab", "meso", "tab", "extrude", "assembled-solid",
             "Mirrored right chin tab (shape code shared with chinTabL).",
             (0.10, 0.10, 0.12), [0.085, -0.46, 0.05], "groundNavy", E_FRONT,
             attachment=attach("lowerFaceJaw/chin-underside-R", [0.04, -0.44, 0.05], [0.09, -0.50, 0.05]),
             extra_geom=tab_geom)

rear = comp("rearShell", "Rear Shell", "meso", "shell", "ellipsoid", "continuous-sculpt",
            "Symmetric plain-facet continuation of the cranial volume (G4); no invented rear panels.",
            (0.54, 0.88, 0.46), [0, 0.02, -0.22], "groundNavy", E_SIDE + E_YAW,
            attachment=attach("cranial-shell/rear-seam", [0, 0.0, -0.44], [0, 0.0, -0.36]),
            confidence=0.55)

spec["componentTree"] = [root, crown, forehead, temple_l, temple_r, cheek_l, cheek_r,
                         cavity, eye_l, eye_r, bridge, jaw, tab_l, tab_r, rear]

# ---------------- materials -------------------------------------------------
spec["materials"] = [
    {
        "id": "wireBright", "name": "Wire structural bright",
        "type": "standard", "shaderModel": "MeshStandardMaterial / PBR approximation",
        "baseColor": "#10D830", "color": "#10D830",
        "albedo": {"dominant": "#10D830", "secondary": ["#10B010"],
                   "samplingNotes": "Green palette authority frame (green-yaw); two-tone bright/dim strokes."},
        "colorVariation": {"palette": ["#10D830", "#10B010"], "pattern": "view-dependent two-tone",
                            "amplitude": 0.0, "heightCorrelation": 0.0},
        "textureResolution": 4, "textureProjection": {"mode": "uv", "repeat": [1.0, 1.0],
                                                       "anisotropy": 1, "texelDensityIntent": "flat colour, no texture maps"},
        "surfaceFrequencyBands": [
            {"id": "macro", "frequency": 1.0, "amplitude": 0.0, "role": "flat emissive stroke colour"},
            {"id": "meso", "frequency": 4.0, "amplitude": 0.0, "role": "stroke density follows facet seams"},
            {"id": "micro", "frequency": 16.0, "amplitude": 0.0, "role": "none: line art has no micro relief"},
        ],
        "roughness": {"base": 0.45, "variation": 0.0, "map": "constant",
                       "localResponse": "uniform; emissive carries readability"},
        "metalness": {"base": 0.0, "variation": 0.0},
        "normal": {"pattern": "none", "strength": 0.0, "scale": 1.0, "space": "tangent"},
        "bump": {"pattern": "none", "amplitude": 0.0, "scale": 1.0},
        "displacement": {"pattern": "none", "amplitude": 0.0, "scale": 1.0, "silhouetteAffects": False},
        "ambientOcclusion": {"cavityStrength": 0.0, "contactShadowBias": 0.0,
                              "notes": "line art on flat fills; no AO response"},
        "wear": {"edgeWear": 0.0, "scratches": [], "chips": []},
        "dirt": {"amount": 0.0, "cavityBias": 0.0, "color": "#000029"},
        "localOverrides": [{
            "id": "brightDimOverride",
            "name": "Far-facing wire dim tone",
            "region": "strokes facing away from camera (backfaces and rear shells)",
            "baseColor": "#10B010",
            "roughness": 0.45,
            "notes": "Realized in the factory as dim-coloured LineSegments on far-facing edges; two-tone is the reference's own depth cue.",
            "evidenceRefs": ["spec/refs/green-yaw.png"],
        }],
        "shaderNotes": [
            "Flat emissive-style line art: color carries the stroke hue; no albedo reuse as roughness/normal/AO.",
        ],
        "notes": "Wire bright #10D830 from the green authority frame.",
    },
    {
        "id": "eyesAccent", "name": "Eye accent outline",
        "type": "standard", "shaderModel": "MeshStandardMaterial / PBR approximation",
        "baseColor": "#E05000", "color": "#E05000",
        "albedo": {"dominant": "#E05000", "secondary": [],
                   "samplingNotes": "Eye outlines in the green authority frame."},
        "colorVariation": {"palette": ["#E05000"], "pattern": "flat", "amplitude": 0.0, "heightCorrelation": 0.0},
        "textureResolution": 4, "textureProjection": {"mode": "uv", "repeat": [1.0, 1.0],
                                                       "anisotropy": 1, "texelDensityIntent": "flat colour"},
        "surfaceFrequencyBands": [
            {"id": "macro", "frequency": 1.0, "amplitude": 0.0, "role": "flat accent colour"},
            {"id": "meso", "frequency": 4.0, "amplitude": 0.0, "role": "outline follows the almond leaf shape"},
            {"id": "micro", "frequency": 16.0, "amplitude": 0.0, "role": "none"},
        ],
        "roughness": {"base": 0.45, "variation": 0.0, "map": "constant", "localResponse": "uniform"},
        "metalness": {"base": 0.0, "variation": 0.0},
        "normal": {"pattern": "none", "strength": 0.0, "scale": 1.0, "space": "tangent"},
        "bump": {"pattern": "none", "amplitude": 0.0, "scale": 1.0},
        "displacement": {"pattern": "none", "amplitude": 0.0, "scale": 1.0, "silhouetteAffects": False},
        "ambientOcclusion": {"cavityStrength": 0.0, "contactShadowBias": 0.0, "notes": "none"},
        "wear": {"edgeWear": 0.0, "scratches": [], "chips": []},
        "dirt": {"amount": 0.0, "cavityBias": 0.0, "color": "#000029"},
        "localOverrides": [],
        "shaderNotes": ["Accent #E05000 with emissive lift for parity with the wire strokes."],
        "notes": "Eye outlines recessed inside the face pocket (G2).",
    },
    {
        "id": "groundNavy", "name": "Ground navy fill",
        "type": "standard", "shaderModel": "MeshStandardMaterial / PBR approximation",
        "baseColor": "#000029", "color": "#000029",
        "albedo": {"dominant": "#000029", "secondary": [],
                   "samplingNotes": "Fills between wire strokes equal the sheet background navy."},
        "colorVariation": {"palette": ["#000029"], "pattern": "flat", "amplitude": 0.0, "heightCorrelation": 0.0},
        "textureResolution": 4, "textureProjection": {"mode": "uv", "repeat": [1.0, 1.0],
                                                       "anisotropy": 1, "texelDensityIntent": "flat colour"},
        "surfaceFrequencyBands": [
            {"id": "macro", "frequency": 1.0, "amplitude": 0.0, "role": "flat navy fill"},
            {"id": "meso", "frequency": 4.0, "amplitude": 0.0, "role": "facet planes read through edge lines only"},
            {"id": "micro", "frequency": 16.0, "amplitude": 0.0, "role": "none"},
        ],
        "roughness": {"base": 0.95, "variation": 0.0, "map": "constant",
                       "localResponse": "matte fill so strokes stay the brightest element"},
        "metalness": {"base": 0.0, "variation": 0.0},
        "normal": {"pattern": "none", "strength": 0.0, "scale": 1.0, "space": "tangent"},
        "bump": {"pattern": "none", "amplitude": 0.0, "scale": 1.0},
        "displacement": {"pattern": "none", "amplitude": 0.0, "scale": 1.0, "silhouetteAffects": False},
        "ambientOcclusion": {"cavityStrength": 0.25, "contactShadowBias": 0.35,
                              "notes": "pocket interior darkens naturally via geometry occlusion"},
        "wear": {"edgeWear": 0.0, "scratches": [], "chips": []},
        "dirt": {"amount": 0.0, "cavityBias": 0.0, "color": "#000029"},
        "localOverrides": [],
        "shaderNotes": ["Fill stays near-background value so the wire silhouette dominates, matching the sheet."],
        "notes": "The subject is the wire, not shaded plastic.",
    },
]

# ---------------- repetition system ----------------------------------------
spec["repetitionSystems"] = [{
    "id": "wireTwoToneStrokes",
    "name": "Wire two-tone stroke field",
    "level": "meso",
    "parent": "root",
    "count": 0,
    "realization": "edge-linesegments-hand-refinement",
    "buildsGeometry": False,
    "description": "Structural facet seams repeat across every shell as LineSegments coloured bright #10D830 front-facing / dim #10B010 far-facing. Not an InstancedMesh: strokes follow component edge topology, so the factory contract draws them per named part (userData.explodeWithParent) instead of instancing one primitive.",
    "evidenceRefs": ["spec/refs/front.png", "spec/refs/green-yaw.png"],
}]

# ---------------- feature review targets -----------------------------------
def target(tid, name, tier, pass_ids, refs, comps, minimum):
    return {"id": tid, "name": name, "tier": tier, "passIds": pass_ids,
            "minimumScore": minimum, "mustPass": tier == "critical",
            "componentRefs": comps, "evidenceRefs": refs}

CRIT = ["blockout", "structural-pass", "form-refinement"]
IMP = ["form-refinement", "structural-pass"]
spec["featureReviewTargets"] = [
    target("silhouette-front-IoU", "Front silhouette IoU against the admitted front ref", "critical",
           CRIT, ["spec/refs/front.png", "spec/measurements.json"], ["root"], 0.8),
    target("eye-placement", "Eye placement: slanted almonds at ~47.5% height joined at the central bridge", "critical",
           IMP, ["spec/zoom/geom_63_1811.png"], ["eyePlateL", "eyePlateR", "midFaceBridge"], 0.8),
    target("cheek-lobe-width-band", "Cheek lobes form the widest band and extend past the cranial shell", "critical",
           IMP, ["spec/measurements.json", "spec/zoom/green_zone.png"], ["cheekShellL", "cheekShellR", "templeShellL", "templeShellR"], 0.8),
    target("crown-facet-ridge", "Crown facet ridge peak readable front and oblique", "critical",
           IMP, ["spec/zoom/wide0.png", "spec/refs/top.png"], ["crown"], 0.8),
    target("jaw-taper", "Jaw tapers from the cheek band to the trapezoid chin plate", "critical",
           IMP, ["spec/refs/front.png"], ["lowerFaceJaw", "chinTabL", "chinTabR"], 0.8),
    target("mouth-band", "Mouth band seam at ~77% height", "important",
           IMP, ["spec/zoom/geom_63_1811.png"], ["lowerFaceJaw"], 0.65),
    target("chin-notch", "Centre notch in the chin bottom edge", "important",
           IMP, ["spec/zoom/geom_63_1811.png"], ["lowerFaceJaw"], 0.65),
    target("wire-two-tone", "Bright/dim wire two-tone depth cue", "important",
           ["structural-pass", "material-pass", "lighting-pass"], ["spec/refs/green-yaw.png"],
           ["root"], 0.65),
]

# ---------------- assumptions / risks / lighting -----------------------------
spec["assumptions"] = [
    {"id": "G1", "guess": "head depth", "readingA": "~1.3x width", "readingB": "~1.0x width",
     "chosen": "A", "evidence": "top frame foreshortened lower bound 1.25 (spec/refs/top.png)"},
    {"id": "G2", "guess": "eye depth", "readingA": "recessed pockets", "readingB": "flat decals",
     "chosen": "A", "evidence": "outline inside face planes in all yaws; faceCavity SDF subtract realizes the pocket"},
    {"id": "G3", "guess": "chin tabs", "readingA": "independent plates", "readingB": "jaw continuation",
     "chosen": "A", "evidence": "recur at same normalized position across frames"},
    {"id": "G4", "guess": "rear shell", "readingA": "symmetric plain facets", "readingB": "decorated mechanism",
     "chosen": "A", "evidence": "obliques show plain facets only"},
    {"id": "G5", "guess": "camera labels", "readingA": "canonical probes (front/30/60/side/top)", "readingB": "sheet order implies angles",
     "chosen": "A", "evidence": "labels not supplied"},
    {"id": "A6", "guess": "left/right symmetry", "readingA": "mirrored shape codes", "readingB": "per-side measured asymmetry",
     "chosen": "A within measurement residual", "evidence": "front row centres drift <=1px across all 18 rows (spec/measurements.json); sheet-wide drift comes from yaw views"},
]
spec["risks"] = [
    "Thin-stroke silhouette IoU is fragile: both masks are wire outlines, so sub-pixel offsets move IoU more than with solid silhouettes.",
    "Navy-on-navy fills can vanish into the background mask; gate captures must keep strokes visible (emissive lift) without inflating the silhouette.",
    "Implicit SDF sampling grid quantises the pocket depth; verify pocket floor visibility in renders.",
]
spec["lightingFromPhoto"] = [{
    "id": "flat-emissive-sheet",
    "keyLight": "none: sprite art is unlit line work",
    "fillLight": "uniform ambient so flat fills read at their albedo value",
    "rimOrEnvironment": "none",
    "exposure": "neutral; strokes must stay the brightest element",
    "toneMapping": "NoToneMapping to preserve exact palette values",
    "background": "#000029",
    "contactShadow": "none: floating head, no ground plane in frame",
}]

ld = spec["lookDevTargets"]["materialPass"]["referencePbrExtraction"]
ld["requiredWhenSourceImagePresent"] = False
ld["acceptedLimitation"] = ("Wire-art subject: the palette is four flat colours (wire bright/dim, eyes accent, navy ground) "
                            "swapped across frames; there is no lit surface response to invert, so PBR map extraction is "
                            "meaningless here. Albedo palette + emissive strokes are the fidelity authority.")

json.dump(spec, open("object-sculpt-spec.json", "w"), indent=2)
print("components:", len(spec["componentTree"]), "| materials:", len(spec["materials"]))
