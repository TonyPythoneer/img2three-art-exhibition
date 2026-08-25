#!/usr/bin/env python3
"""Second validation-fix pass: colorMaterialRecipe per component + surface response.

Rerunnable: python3 fix_spec_validation2.py
"""
import json

spec = json.load(open("object-sculpt-spec.json"))

NAVY = "rgba(0, 0, 41, 1.0)"
BRIGHT = "rgba(16, 216, 48, 1.0)"
DIM = "rgba(16, 176, 16, 1.0)"
ACCENT = "rgba(224, 80, 0, 1.0)"

RECIPES = {
    "root":          (NAVY, BRIGHT),
    "crown":         (NAVY, BRIGHT),
    "forehead":      (NAVY, BRIGHT),
    "templeShellL":  (NAVY, BRIGHT),
    "templeShellR":  (NAVY, BRIGHT),
    "cheekShellL":   (NAVY, BRIGHT),
    "cheekShellR":   (NAVY, BRIGHT),
    "faceCavity":    (NAVY, DIM),
    "eyePlateL":     (ACCENT, NAVY),
    "eyePlateR":     (ACCENT, NAVY),
    "midFaceBridge": (NAVY, BRIGHT),
    "lowerFaceJaw":  (NAVY, BRIGHT),
    "chinTabL":      (NAVY, BRIGHT),
    "chinTabR":      (NAVY, BRIGHT),
    "rearShell":     (NAVY, DIM),
}
for c in spec["componentTree"]:
    dom, sec = RECIPES[c["id"]]
    c["colorMaterialRecipe"] = {
        "dominantAlbedo": dom,
        "secondaryAlbedo": sec,
        "materialClass": "unknown",
        "materialClassConfidence": 0.35,
        "notes": ("Unlit sprite-art subject: dominant value is the flat navy fill, secondary is the "
                  "emissive-style stroke/accent hue; no lit response exists to classify a finish from."),
    }

# surface response: the two-tone bright/dim stroke behaviour is the one real
# view-dependent response the reference shows; carry it as nominal roughness
# variation so the material pass has something to verify against.
wb = spec["materials"][0]["roughness"]
wb["variation"] = 0.04
wb["localResponse"] = ("front-facing strokes read brighter than far-facing dim strokes "
                        "(#10D830 vs #10B010); nominal roughness variation stands in for "
                        "that view-dependent two-tone, which the factory realizes as stroke colour")

json.dump(spec, open("object-sculpt-spec.json", "w"), indent=2)
print("pass 2 applied")
