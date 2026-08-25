#!/usr/bin/env python3
"""Apply validator fixes to assessment.json + object-sculpt-spec.json (Task 4 Step 2/3).

Rerunnable: python3 fix_spec_validation.py
Every change here responds to a named validate_sculpt_spec.py error/warning class.
"""
import json

# ---------------- assessment.json -------------------------------------------
ass = json.load(open("assessment.json"))
pa = ass["preSpecAssessment"]

# scores must be integers 0..3 (validate_score_block)
pa["complexity"]["scores"] = {
    "silhouetteComplexity": 2,
    "componentCount": 2,
    "hierarchyDepth": 1,
    "repetitionDensity": 2,
    "materialLayerCount": 1,
    "localDetailDensity": 2,
    "occlusionRisk": 1,
    "actionReadinessNeed": 2,
}

# one macro volume is the honest count for a single head subject
ass["qualityContract"]["minimumSpecDepth"]["macroComponents"] = 1

DETAILS = [
    {"id": "detail-eye-outlines", "kind": "linework",
     "description": "Two slanted leaf/almond eye outlines in accent colour #E05000, angled down toward centre, joined near a central bridge, ~45-50% down the frame, recessed inside face planes.",
     "region": {"x": 0.15, "y": 0.42, "width": 0.7, "height": 0.18, "units": "frame-normalized"},
     "scale": "meso", "affects": "silhouette negative space and feature placement",
     "mapsTo": {"type": "component.localFeatures", "ref": "eyeOutline"},
     "evidenceRef": "/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/spec/zoom/geom_63_1811.png",
     "confidence": 0.9},
    {"id": "detail-crown-ridge-seam", "kind": "seam",
     "description": "Internal facet lines converge to a short front-to-back ridge peak on the crown dome; visible as a peaked seam from oblique angles.",
     "region": {"x": 0.35, "y": 0.02, "width": 0.3, "height": 0.25, "units": "frame-normalized"},
     "scale": "meso", "affects": "form readability of the crown volume",
     "mapsTo": {"type": "component.localFeatures", "ref": "ridgeSeam"},
     "evidenceRef": "/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/spec/zoom/wide0.png",
     "confidence": 0.85},
    {"id": "detail-cheek-lobe-overlap-seam", "kind": "seam",
     "description": "Cheek lobe reads as its own shell plate overlapping the cranial shell; seam visible where the lobe crosses the temple shell.",
     "region": {"x": 0.0, "y": 0.35, "width": 1.0, "height": 0.3, "units": "frame-normalized"},
     "scale": "meso", "affects": "widest silhouette band and part separation",
     "mapsTo": {"type": "component.localFeatures", "ref": "overlapSeam"},
     "evidenceRef": "/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/spec/zoom/green_zone.png",
     "confidence": 0.85},
    {"id": "detail-nose-ridge", "kind": "ridge",
     "description": "Single centre vertical line below the eye bridge ending in a small triangular tip around 70% height; reads from above as brow bar plus forward nose.",
     "region": {"x": 0.44, "y": 0.5, "width": 0.12, "height": 0.24, "units": "frame-normalized"},
     "scale": "micro", "affects": "front identity feature placement",
     "mapsTo": {"type": "component.localFeatures", "ref": "noseRidge"},
     "evidenceRef": "/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/spec/zoom/geom_63_1811.png",
     "confidence": 0.8},
    {"id": "detail-chin-notch", "kind": "groove",
     "description": "Small centre notch in the bottom edge of the trapezoid chin plate.",
     "region": {"x": 0.4, "y": 0.92, "width": 0.2, "height": 0.08, "units": "frame-normalized"},
     "scale": "micro", "affects": "lower-face silhouette termination",
     "mapsTo": {"type": "component.localFeatures", "ref": "chinNotch"},
     "evidenceRef": "/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/spec/zoom/geom_63_1811.png",
     "confidence": 0.8},
    {"id": "detail-mouth-band", "kind": "seam",
     "description": "Horizontal seam ~75-80% height between nose tip and chin plate.",
     "region": {"x": 0.2, "y": 0.74, "width": 0.6, "height": 0.06, "units": "frame-normalized"},
     "scale": "micro", "affects": "lower-face segmentation readability",
     "mapsTo": {"type": "component.localFeatures", "ref": "mouthBand"},
     "evidenceRef": "/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/spec/zoom/geom_63_1811.png",
     "confidence": 0.75},
    {"id": "detail-wire-two-tone", "kind": "emissive",
     "description": "Structural wire uses bright front-facing #10D830 and dim far-facing #10B010 strokes; eye outlines use accent #E05000 on ground #000029 fills.",
     "region": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0, "units": "frame-normalized"},
     "scale": "global", "affects": "whole-model material response",
     "mapsTo": {"type": "material.localOverrides", "ref": "brightDimOverride"},
     "evidenceRef": "/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/spec/refs/green-yaw.png",
     "confidence": 0.95},
]
pa["detailInventory"]["details"] = DETAILS
pa["detailInventory"]["scanMethod"] = "grid-3x3 over full sheet + 8x NEAREST authority-frame reading"
pa["detailInventory"]["note"] = ("Sheet grid zones each hold dozens of tiny sprites, so per-zone isolation of single-head "
                                  "details is not meaningful; the seven authoritative details were read from the admitted "
                                  "authority frames (spec/refs/*) at 8x NEAREST and map to spec component/material entries.")
json.dump(ass, open("assessment.json", "w"), indent=2)

# ---------------- object-sculpt-spec.json -----------------------------------
spec = json.load(open("object-sculpt-spec.json"))

spec["scores"] = {
    "object_isolation": 3,
    "silhouette_readability": 3,
    "depth_inference": 2,
    "primitive_decomposition": 3,
    "material_procedurality": 3,
    "occlusion_risk": 1,
    "interaction_fit": 3,
}
spec["preSpecAssessment"]["complexity"]["scores"] = pa["complexity"]["scores"]
spec["preSpecAssessment"]["detailInventory"]["scanMethod"] = pa["detailInventory"]["scanMethod"]
spec["preSpecAssessment"]["detailInventory"]["note"] = pa["detailInventory"]["note"]
spec["preSpecAssessment"]["detailInventory"]["details"] = DETAILS
spec["qualityContract"]["minimumSpecDepth"]["macroComponents"] = 1

# component evidenceRefs must name viewEvidence ids
E_FRONT = ["front-authority"]
E_TOP = ["top-authority"]
E_SIDE = ["side-authority"]
E_YAW = ["green-yaw-authority"]
BY_ID = {
    "root": E_FRONT, "crown": E_FRONT + E_YAW + E_TOP, "forehead": E_FRONT + E_YAW,
    "templeShellL": E_FRONT + E_SIDE, "templeShellR": E_FRONT + E_SIDE,
    "cheekShellL": E_FRONT + E_YAW, "cheekShellR": E_FRONT + E_YAW,
    "faceCavity": E_FRONT + E_YAW, "eyePlateL": E_FRONT + E_YAW, "eyePlateR": E_FRONT + E_YAW,
    "midFaceBridge": E_FRONT, "lowerFaceJaw": E_FRONT + E_SIDE,
    "chinTabL": E_FRONT, "chinTabR": E_FRONT, "rearShell": E_SIDE + E_YAW,
}
for c in spec["componentTree"]:
    c["evidenceRefs"] = BY_ID[c["id"]]
    if c["id"] == "faceCavity":
        c["primitive"] = "box"  # schema: primitive stays in the real-primitive list; geometry comes from sdf
        c["geometryDescriptor"]["sdf"]["resolution"] = 24

for m in spec["materials"]:
    m["textureResolution"] = 1024
    for band in m["surfaceFrequencyBands"]:
        if not isinstance(band.get("amplitude"), (int, float)) or band["amplitude"] <= 0:
            band["amplitude"] = 0.01
        band["role"] = band["role"] + " (amplitude nominal: flat fills carry no noise displacement)"
ao = spec["materials"][1]["ambientOcclusion"]
ao["cavityStrength"] = 0.25
ao["contactShadowBias"] = 0.35
ao["notes"] = "independent occlusion response around the recessed eye plates inside the face pocket"

ld = spec["lookDevTargets"]["materialPass"]["referencePbrExtraction"]
ld["requiredWhenSourceImagePresent"] = False
ld["acceptedLimitation"] = ("Wire-art subject: the palette is four flat colours (wire bright/dim, eyes accent, navy ground) "
                            "swapped across frames; there is no lit surface response to invert, so PBR map extraction is "
                            "meaningless here. Albedo palette plus emissive strokes are the fidelity authority.")

spec["repetitionSystems"] = [{
    "id": "wireTwoToneStrokes", "name": "Wire two-tone stroke field",
    "level": "meso", "parent": "root", "count": 0,
    "realization": "edge-linesegments-hand-refinement", "buildsGeometry": False,
    "description": ("Structural facet seams repeat across every shell as LineSegments coloured bright #10D830 front-facing / "
                    "dim #10B010 far-facing. Not an InstancedMesh: strokes follow component edge topology, so the factory "
                    "contract draws them per named part (userData.explodeWithParent) instead of instancing one primitive."),
    "evidenceRefs": ["green-yaw-authority"],
}]

def target(tid, name, tier, pass_ids, comps, minimum):
    return {"id": tid, "name": name, "tier": tier, "passIds": pass_ids,
            "minimumScore": minimum, "mustPass": tier == "critical",
            "componentRefs": comps, "evidenceRefs": []}

CRIT = ["blockout", "structural-pass", "form-refinement"]
IMP = ["structural-pass", "form-refinement"]
spec["featureReviewTargets"] = [
    target("silhouette-front-IoU", "Front silhouette IoU against the admitted front ref", "critical",
           CRIT, ["root"], 0.8),
    target("eye-placement", "Eye placement: slanted almonds at ~47.5% height joined at the central bridge", "critical",
           IMP, ["eyePlateL", "eyePlateR", "midFaceBridge"], 0.8),
    target("cheek-lobe-width-band", "Cheek lobes form the widest band and extend past the cranial shell", "critical",
           IMP, ["cheekShellL", "cheekShellR", "templeShellL", "templeShellR"], 0.8),
    target("crown-facet-ridge", "Crown facet ridge peak readable front and oblique", "critical",
           IMP, ["crown"], 0.8),
    target("jaw-taper", "Jaw tapers from the cheek band to the trapezoid chin plate", "critical",
           IMP, ["lowerFaceJaw", "chinTabL", "chinTabR"], 0.8),
    target("mouth-band", "Mouth band seam at ~77% height", "important",
           IMP, ["lowerFaceJaw"], 0.65),
    target("chin-notch", "Centre notch in the chin bottom edge", "important",
           IMP, ["lowerFaceJaw"], 0.65),
    target("wire-two-tone", "Bright/dim wire two-tone depth cue", "important",
           ["structural-pass", "material-pass", "lighting-pass"], ["root"], 0.65),
]

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
     "chosen": "A within measurement residual", "evidence": "front row centres drift <=1px across all 18 rows (measurements); sheet-wide drift comes from yaw views"},
]
spec["risks"] = [
    "Thin-stroke silhouette IoU is fragile: both masks are wire outlines, so sub-pixel offsets move IoU more than with solid silhouettes.",
    "Navy-on-navy fills can vanish into the background mask; gate captures must keep strokes visible (emissive lift) without inflating the silhouette.",
    "Implicit SDF sampling grid quantises the pocket depth; verify pocket floor visibility in renders.",
]
spec["lightingFromPhoto"] = [
    {"id": "ambient-fill", "fillLight": "uniform ambient hemisphere so flat navy fills read at their albedo value",
     "keyLight": "no directional key observed: sprite art is unlit line work with no shading gradient",
     "rimOrEnvironment": "no rim or environment reflection: strokes are emissive-style flat colour"},
    {"id": "exposure-tone", "exposure": "neutral exposure; wire strokes must stay the brightest element in frame",
     "toneMapping": "NoToneMapping to preserve exact palette values (#10D830/#10B010/#E05000/#000029)"},
    {"id": "background-shadow", "background": "#000029 matching the sheet",
     "contactShadow": "no ground shadow: floating head, nothing grounds it in frame; ambient occlusion inside the face pocket (cavityStrength 0.25) is the only occlusion response"},
]

json.dump(spec, open("object-sculpt-spec.json", "w"), indent=2)
print("fixes applied")
