#!/usr/bin/env python3
"""Agent-vision overrides after analyze_texture/extract_pbr_evidence patched the spec.

The finish classifier has no 'milky translucent PS1 shell' class: it zeroed the shell's
transmission, set clearcoat 1.0 everywhere, and made the grip/gold fully metallic. Scripts
do enforcement, agent vision does judgment — referencePbr evidence blocks are KEPT
(confidence 0.78-0.86, all >= 0.7), scalars are corrected to what the reference shows,
and every override is recorded on the material.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE / "object-sculpt-spec.json"
doc = json.load(open(SPEC))

OVERRIDES = {
    "outerBladeShellMaterial": {
        "values": {"transmission": {"base": 0.5, "variation": 0.0}, "opacity": 0.45,
                   "clearcoat": {"base": 0.0, "variation": 0.0},
                   "clearcoatRoughness": {"base": 0.0, "variation": 0.0},
                   "ior": {"base": 1.25, "value": 1.25}, "envMapIntensity": 0.5,
                   "roughnessBase": 0.32},
        "reason": "classifier picked painted-metal and zeroed transmission/maxed clearcoat — the milky translucency IS the identity feature; restored deliberate translucent plan (transmission 0.5, opacity 0.45, roughness 0.32, no clearcoat, ior 1.25)",
    },
    "purpleCoreMaterial": {
        "values": {"clearcoat": {"base": 0.0, "variation": 0.0}, "roughnessBase": 0.35},
        "reason": "clearcoat 1.0 meaningless on an opaque flat-shaded emissive core (and ignored by MeshStandardMaterial); roughness to matte-satin 0.35",
    },
    "magentaSpineMaterial": {
        "values": {"clearcoat": {"base": 0.0, "variation": 0.0}, "roughnessBase": 0.3},
        "reason": "same classifier artifact as core; spine is a flat lacquered wedge",
    },
    "gunmetalGuardMaterial": {
        "values": {"metalness": {"base": 0.55, "variation": 0.0},
                   "clearcoat": {"base": 0.0, "variation": 0.0}, "roughnessBase": 0.5},
        "reason": "painted-metal recipe emitted metalness 0.0 — the gunmetal shoulders read as restrained metal (crop value response), not painted plastic",
    },
    "crimsonEmitterMaterial": {
        "values": {"metalness": {"base": 0.1, "variation": 0.0},
                   "clearcoat": {"base": 0.35, "variation": 0.0},
                   "clearcoatRoughness": {"base": 0.4, "variation": 0.0},
                   "envMapIntensity": 0.8, "roughnessBase": 0.38},
        "reason": "gem-metal recipe made the rods 75% metallic mirrors; reference shows dark lacquer: dielectric body + moderate clearcoat",
    },
    "agedGoldMaterial": {
        "values": {"metalness": {"base": 0.65, "variation": 0.0}, "anisotropy": {"base": 0.0},
                   "roughnessBase": 0.55},
        "reason": "brushed-steel recipe set metalness 1.0 + anisotropy 1.0 — no brushing exists in a flat-shaded PS1 asset; aged olive gold stays rough and only moderately metallic",
    },
    "gripMaterial": {
        "values": {"metalness": {"base": 0.08, "variation": 0.0}, "anisotropy": {"base": 0.0},
                   "roughnessBase": 0.72},
        "reason": "brushed-steel recipe made the near-black grip fully metallic; it is a matte grip, not chrome",
    },
}

for m in doc["materials"]:
    ov = OVERRIDES[m["id"]]
    for k, v in ov["values"].items():
        if k == "roughnessBase":
            m["roughness"]["base"] = v
        else:
            m[k] = v
    rmap = m["roughness"].get("map")
    if isinstance(rmap, dict):
        rmap["wired"] = False
        rmap["reason"] = ("extracted map encodes the silhouette's anti-aliasing staircase, not surface "
                          "micro-structure (flat-shaded source has none); kept as evidence, not wired. "
                          "Also: three.js multiplies roughnessMap x roughness scalar — wiring it would square the response.")
    m["finishClassifierOverride"] = ov["reason"]

pre = doc["preSpecAssessment"]
resolutions = {
    "Blade axis angle": "RESOLVED: measured 17.67deg from vertical, centroid regression R2=0.9994 (measurements.json bladeAxis).",
    "Leaf profile symmetry": "RESOLVED: symmetric — max |left-right| < 1.5px over y in [0,195]; the 2D right bow was the base flare (rightBladeClamp wing), not the leaf profile.",
    "Emitter rod layout": "RESOLVED: 4 measured axes intersect the blade axis at image y 252-258 -> radiation centre (0,-0.115); fan is C2 point-symmetric, angles +5.8/+23.3/+40.8 deg (right) and C2 mirrors (left); brief's 'mirrored' phrasing recorded as evidence conflict.",
    "Blade tip profile": "RESOLVED by documented inference: taper continuation to Y=2.82, confidence 0.5 (assumptions).",
    "Grip lower half + pommel": "RESOLVED by documented inference: pommel collar + gold tip below Y=-0.52, confidence 0.4 (assumptions).",
    "Back face": "RESOLVED by policy: mirrored, evidenceType=mirrored on all back components.",
    "Blade thickness": "RESOLVED by assumption: 0.06u total, confidence 0.5 (assumptions); side views will not be silhouette-gated against invented depth.",
    "Shell tint": "RESOLVED: measured medians #EDEEF6 lit / #D6D7E2 bands / #C9CADF edge — cool lavender cast confirmed (measurements.json palette).",
}
resolved = []
for u in pre["unknownsToResolveBeforeImplementation"]:
    key = next((k for k in resolutions if u.startswith(k)), None)
    assert key, f"no resolution recorded for unknown: {u[:60]}"
    resolved.append({"unknown": u, "resolution": resolutions[key]})
pre["resolvedUnknowns"] = resolved
pre["unknownsToResolveBeforeImplementation"] = []

json.dump(doc, open(SPEC, "w"), indent=2, ensure_ascii=False)

# keep assessment.json in sync
ap = HERE / "assessment.json"
a = json.load(open(ap))
a["preSpecAssessment"]["resolvedUnknowns"] = resolved
a["preSpecAssessment"]["unknownsToResolveBeforeImplementation"] = []
json.dump(a, open(ap, "w"), indent=2, ensure_ascii=False)
print("material overrides + resolved unknowns applied")
