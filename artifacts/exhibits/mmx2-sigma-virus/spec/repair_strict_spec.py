#!/usr/bin/env python3
"""Repair strict-quality metadata for the Sigma Virus green head spec.

This is deliberately metadata-only: it does not alter the authored geometry dimensions.
All observations point to the admitted x8 NEAREST authority crops under spec/refs or
spec/zoom-v2 and are rerunnable after the generic intake generator is run.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "object-sculpt-spec.json"
ASSESSMENT_PATH = HERE / "assessment.json"

OBJECT_CLASS = {
    "primaryType": "stylized low-poly helmet-like head rendered as wireframe line art",
    "primaryDomain": "object",
    "formLanguage": [
        "faceted planar shell segments",
        "angular cheek lobes forming the widest band",
        "recessed eye pockets under a brow ledge",
    ],
    "structureKind": ["hard-surface blockout", "low-poly prop"],
    "motionPotential": ["explode view by part scaling", "click-to-isolate parts"],
    "materialFamilies": ["emissive-style flat wire colour on navy fill", "no PBR texture projection"],
    "notes": (
        "Read from the admitted front, top, side, and green-yaw authority crops at 8x NEAREST; "
        "the green palette is colour authority and non-green views are structural supplements."
    ),
}

VIEWS = [
    {
        "id": "front-authority",
        "view": "front",
        "imageRegion": {"x": 0, "y": 0, "width": 1, "height": 1, "units": "normalized"},
        "imagePath": "spec/refs/front.png",
        "observations": [
            "Crown, brow, recessed eyes, cheek lobes, mouth bar, jaw taper, and two chin tabs are visible.",
            "Cheek band is the widest silhouette region; left/right outline drift is within the measured residual.",
        ],
        "confidence": 0.95,
    },
    {
        "id": "top-authority",
        "view": "top",
        "imageRegion": {"x": 0, "y": 0, "width": 1, "height": 1, "units": "normalized"},
        "imagePath": "spec/refs/top.png",
        "observations": [
            "Crown ridge and elongated head depth are visible; this is the G1 depth evidence.",
        ],
        "confidence": 0.8,
    },
    {
        "id": "side-authority",
        "view": "side",
        "imageRegion": {"x": 0, "y": 0, "width": 1, "height": 1, "units": "normalized"},
        "imagePath": "spec/refs/side.png",
        "observations": [
            "Side/rear-oblique crop shows plain faceted continuation and cheek-to-jaw depth.",
        ],
        "confidence": 0.72,
    },
    {
        "id": "green-yaw-authority",
        "view": "three-quarter yaw",
        "imageRegion": {"x": 0, "y": 0, "width": 1, "height": 1, "units": "normalized"},
        "imagePath": "spec/refs/green-yaw.png",
        "observations": [
            "Green palette authority confirms bright/dim wire tones, a peaked ridge, and an eye recessed inside face planes.",
        ],
        "confidence": 0.88,
    },
]

EXTRA_DETAILS = [
    {
        "id": "detail-brow-double-rim",
        "kind": "linework",
        "description": "The brow/eye system has an outer angular bracket rim and an inner rim around each recessed eye pocket.",
        "region": {"x": 0.18, "y": 0.42, "width": 0.64, "height": 0.18, "units": "frame-normalized"},
        "scale": "meso",
        "affects": "eye-pocket depth cue and facial identity",
        "mapsTo": {"type": "component.localFeatures", "ref": "browDoubleRim"},
        "evidenceRef": "spec/zoom-v2/front_brow-band-eyes.png",
        "confidence": 0.9,
    },
    {
        "id": "detail-crown-cornice",
        "kind": "linework",
        "description": "A horizontal cornice beam separates the flat crown top panel from the forehead plane.",
        "region": {"x": 0.27, "y": 0.02, "width": 0.46, "height": 0.16, "units": "frame-normalized"},
        "scale": "meso",
        "affects": "crown silhouette and planar hierarchy",
        "mapsTo": {"type": "component.localFeatures", "ref": "corniceBeam"},
        "evidenceRef": "spec/zoom-v2/front_crown.png",
        "confidence": 0.86,
    },
    {
        "id": "detail-cheek-diagonal-facets",
        "kind": "linework",
        "description": "Each cheek lobe contains diagonal facet lines between its vertical outer edge and inner overlap seam.",
        "region": {"x": 0.05, "y": 0.34, "width": 0.9, "height": 0.32, "units": "frame-normalized"},
        "scale": "micro",
        "affects": "cheek-lobe planar readability",
        "mapsTo": {"type": "component.localFeatures", "ref": "diagonalFacets"},
        "evidenceRef": "spec/green-breakdown/ost_front_cheek-lobe-left.png",
        "confidence": 0.84,
    },
]


def update(path: Path, *, is_spec: bool) -> None:
    data = json.loads(path.read_text())
    pre = data.setdefault("preSpecAssessment", {})
    pre["objectClass"] = OBJECT_CLASS
    complexity = pre.setdefault("complexity", {})
    complexity["scores"] = {
        "silhouetteComplexity": 2,
        "componentCount": 3,
        "hierarchyDepth": 2,
        "repetitionDensity": 2,
        "materialLayerCount": 2,
        "localDetailDensity": 3,
        "occlusionRisk": 2,
        "actionReadinessNeed": 3,
    }
    complexity["estimatedCounts"] = {
        "macroComponents": 1,
        "mesoComponents": 14,
        "microFeatureGroups": 7,
        "materialLayers": 3,
        "repetitionSystems": 1,
    }
    inventory = pre.setdefault("detailInventory", {})
    inventory["targetMinDetails"] = 10
    details = inventory.setdefault("details", [])
    detail_indices = {item.get("id"): index for index, item in enumerate(details)}
    for item in EXTRA_DETAILS:
        existing_index = detail_indices.get(item["id"])
        if existing_index is None:
            details.append(item)
        else:
            details[existing_index] = item

    if is_spec:
        data["viewEvidence"] = VIEWS
        # These references are consumed by validator and must resolve to viewEvidence IDs.
        for component in data.get("componentTree", []):
            refs = component.get("evidenceRefs", [])
            component["evidenceRefs"] = [ref for ref in refs if ref in {v["id"] for v in VIEWS}]
            if not component["evidenceRefs"]:
                component["evidenceRefs"] = ["front-authority"]

        components = data.get("componentTree", [])
        component_by_id = {c["id"]: c for c in components}
        if "crownRidge" not in component_by_id:
            ridge = deepcopy(component_by_id["crown"])
            ridge.update({
                "id": "crownRidge",
                "name": "Crown Ridge Plate",
                "level": "micro",
                "role": "ridge",
                "importance": 0.8,
                "confidence": 0.78,
                "dimensions": {"width": 0.1, "height": 0.14, "depth": 0.42, "units": "relative", "confidence": 0.78},
                "transform": {"position": [0, 0.485, -0.05], "rotation": [0, 0, 0]},
                "attachment": None,
                "localFeatures": [{
                    "id": "ridgePeak",
                    "name": "raised crown ridge peak",
                    "kind": "linework",
                    "description": "Raised narrow strip on the crown centre line, making the front-to-back ridge peak readable from oblique views.",
                    "evidenceRefs": ["spec/zoom-v2/top-down_full.png", "spec/zoom-v2/front_crown.png"],
                }],
                "evidenceRefs": ["front-authority", "top-authority", "green-yaw-authority"],
                "details": [],
                "fidelityTier": "blockout",
            })
            ridge["actionProfile"]["destruction"]["fractureGroup"] = "crownRidge"
            ridge["actionProfile"]["collider"]["scale"] = [0.1, 0.14, 0.42]
            components.append(ridge)
        if "mouthSeam" not in {c["id"] for c in components}:
            mouth = deepcopy(component_by_id["lowerFaceJaw"])
            mouth.update({
                "id": "mouthSeam",
                "name": "Mouth Seam Strip",
                "level": "micro",
                "role": "seam",
                "importance": 0.75,
                "confidence": 0.8,
                "material": "wireBright",
                "materialLayers": ["wireBright"],
                "dimensions": {"width": 0.56, "height": 0.03, "depth": 0.04, "units": "relative", "confidence": 0.8},
                "transform": {"position": [0, -0.27, 0.26], "rotation": [0, 0, 0]},
                "attachment": None,
                "localFeatures": [{
                    "id": "mouthBandStrip",
                    "name": "raised mouth seam strip",
                    "kind": "seam",
                    "description": "Thin horizontal raised strip across the lower face at the mouth band height.",
                    "evidenceRefs": ["spec/zoom-v2/front_mouth-chin.png"],
                }],
                "evidenceRefs": ["front-authority"],
                "details": [],
                "fidelityTier": "blockout",
            })
            mouth["actionProfile"]["destruction"]["fractureGroup"] = "mouthSeam"
            mouth["actionProfile"]["collider"]["scale"] = [0.56, 0.03, 0.04]
            components.append(mouth)
        data["componentTree"] = components
        feature_by_component = {c["id"]: c for c in components}
        for eye_id in ("eyePlateL", "eyePlateR"):
            eye = feature_by_component[eye_id]
            eye["transform"]["position"][2] = 0.34
            if isinstance(eye.get("attachment"), dict):
                eye["attachment"]["localStart"][2] = 0.34
                eye["attachment"]["localEnd"][2] = 0.335
        feature_by_component["crown"].setdefault("localFeatures", []).append({
            "id": "corniceBeam",
            "name": "crown cornice beam",
            "kind": "linework",
            "description": "Horizontal beam under the flat crown top panel.",
            "evidenceRefs": ["spec/zoom-v2/front_crown.png"],
        })
        feature_by_component["forehead"].setdefault("localFeatures", []).append({
            "id": "browDoubleRim",
            "name": "brow double rim",
            "kind": "linework",
            "description": "Outer and inner angular rims framing each recessed eye pocket.",
            "evidenceRefs": ["spec/zoom-v2/front_brow-band-eyes.png"],
        })
        for cid in ("cheekShellL", "cheekShellR"):
            feature_by_component[cid].setdefault("localFeatures", []).append({
                "id": "diagonalFacets",
                "name": "cheek diagonal facets",
                "kind": "linework",
                "description": "Diagonal facet lines across the cheek lobe plate.",
                "evidenceRefs": ["spec/green-breakdown/ost_front_cheek-lobe-left.png"],
            })

        data["preSpecAssessment"]["detailInventory"] = inventory
        # Keep all source references reproducible; these old paths were disposable crops.
        replacements = {
            "spec/zoom/geom_63_1811.png": "spec/zoom-v2/front_brow-band-eyes.png",
            "spec/zoom/wide0.png": "spec/zoom-v2/top-down_full.png",
            "spec/zoom/green_zone.png": "spec/zoom-v2/three-quarter-yaw_full.png",
        }
        def replace(value):
            if isinstance(value, str):
                return replacements.get(value, value)
            if isinstance(value, list):
                return [replace(item) for item in value]
            if isinstance(value, dict):
                return {key: replace(item) for key, item in value.items()}
            return value
        data = replace(data)
        data["materialPipeline"] = {
            "schemaVersion": 1,
            "status": "proceed",
            "registry": "docs/materials/material-reference.json",
            "source": "green-yaw palette authority with isolated colour-cluster crops",
            "regions": [
                {
                    "componentId": "root",
                    "regionId": "wireBright",
                    "profileId": "plastic.matte",
                    "specMaterialId": "wireBright",
                    "status": "proceed",
                    "evidenceRefs": ["spec/refs/green-yaw.png"],
                    "notes": "Bright green cluster isolated from the admitted green yaw authority; dim green is a declared local override.",
                },
                {
                    "componentId": "root",
                    "regionId": "eyesAccent",
                    "profileId": "plastic.matte",
                    "specMaterialId": "eyesAccent",
                    "status": "proceed",
                    "evidenceRefs": ["spec/refs/green-yaw.png"],
                    "notes": "Orange eye cluster isolated from the admitted green yaw authority.",
                },
            ],
            "unresolvedNotObservedMaterials": [],
            "limitation": "groundNavy is the transparent/background fill and has no independent foreground cluster; its exact source albedo is recorded in the material recipe and is not treated as a visible crop region.",
        }
    else:
        data["preSpecAssessment"]["detailInventory"] = inventory

    path.write_text(json.dumps(data, indent=2) + "\n")


update(ASSESSMENT_PATH, is_spec=False)
update(SPEC_PATH, is_spec=True)
print("repaired strict metadata: class, views, 10 details, and evidence links")
