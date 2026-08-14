#!/usr/bin/env python3
"""prompt.txt §0.1 spec-authoring — turn the Stage 0 artefacts into the ObjectSculptSpec.

    python3 spec/author_spec.py           # rewrites spec/object-sculpt-spec.json in place

`forge/stage2_spec/new_sculpt_spec.py` emits a GENERIC humanoid: 61 components with
fingers, eye cavities and lips, nine invented materials, and dimensions from a head-unit
template. None of that is this model. This script replaces the parts of that starter that
describe the object — the component tree, the materials, the passes, the acceptance
criteria — with prompt.txt §2's part table and Stage 0's measured numbers, and leaves the
schema scaffolding alone.

WHERE THE NUMBERS COME FROM (§0.6). Three classes, and the spec never mixes them:

  measured   read straight out of spec/landmarks.json, spec/facet-gate.json,
             spec/palette.json or spec/assessment.json. Confidence >= 0.7.
  derived    arithmetic on measured values, done HERE and written to
             spec/build-constants.json so the figure the spec quotes has a producer.
             Every derivation carries its own `source` string in that file.
  authored   a choice, not an observation: triangle budgets, roughness, the review
             thresholds. Also written to build-constants.json, under `authored`, so
             audit_records.py can tell them from measurements by which key they sit under.

Only the sole is measured as a part today (spec/measure_sole.py). Every other component
carries `dimensions.pending: true` and confidence 0.2: its box is the enclosing landmark
span, which is a bound, not a measurement. Each part measures itself on its own turn
(§0.3), and re-running this script after that measurement lands is what updates the spec.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "object-sculpt-spec.json"
CONSTANTS_PATH = HERE / "build-constants.json"

LM = json.loads((HERE / "landmarks.json").read_text())
FACET = json.loads((HERE / "facet-gate.json").read_text())
PALETTE = json.loads((HERE / "palette.json").read_text())

REFS = "src/assets/exhibits/ff7-cloud-strife-polygon-figure"

# --- measured -------------------------------------------------------------------------
NORM = LM["normalization"]["sole->chin"]
F = NORM["perView"]["front"]                      # front-view landmark heights, normalized
UNC = LM["measurementUncertainty"]                # 0.05447 — cross-view landmark agreement
RMS = NORM["measurementUncertaintyRms"]           # 0.01374 — the per-part shape tolerance
DIM = LM["dimensions"]
SOLE = LM["parts"]["sole"]
FRONT_PX = LM["views"]["front"]["landmarksPx"]

# The front view's own pixels-per-normalized-unit, so the two landmarks recorded only in
# pixels (upper-arm width, elbow row) join the same frame as everything else.
UNIT_PX = (FRONT_PX["sole"] - FRONT_PX["chin"]) / NORM["spanNormalized"]


def px_to_y(row: float) -> float:
    """An image row of front.webp as a normalized height above the sole."""
    return (FRONT_PX["sole"] - row) / UNIT_PX


# --- derived --------------------------------------------------------------------------
DERIVED: dict[str, dict] = {}


def derive(name: str, value: float, source: str) -> float:
    DERIVED[name] = {"value": value, "source": source}
    return value


SOLE_T = SOLE["thickness"]["adopted"]
SOLE_A = SOLE["lateralExtent"]["adopted"]
SOLE_B = SOLE["foreAftExtent"]["adopted"]
FOOT_GAP = DIM["footWidthEach"][1]

SOLE_X = derive(
    "soleCentreX",
    FOOT_GAP / 2 + SOLE_A / 2,
    "landmarks.dimensions.footWidthEach[1] (the gap between the two feet) / 2 + "
    "landmarks.parts.sole.lateralExtent.adopted / 2; mirrored to -X for the figure's right",
)
ELBOW_Y = derive(
    "elbowY",
    px_to_y(LM["poseAngles"]["figureLeftElbowRowPx"]["front"]),
    "landmarks.poseAngles.figureLeftElbowRowPx.front, carried into normalized height by "
    "the front view's own sole/chin pixel scale",
)
UPPER_ARM_W = derive(
    "upperArmWidth",
    LM["views"]["front"]["upperArmWidthPx"] / UNIT_PX,
    "landmarks.views.front.upperArmWidthPx / the front view's sole-chin pixel scale",
)
DELTOID_W = derive(
    "deltoidWidth",
    (DIM["shoulderWidth"] - DIM["chestWidth"]) / 2,
    "(landmarks.dimensions.shoulderWidth - chestWidth) / 2 — one deltoid is half of what "
    "the shoulder line adds to the chest slab",
)
CROWN_Y = LM["parts"]["head"]["crownHeight"]["adopted"]
HEAD_H = derive(
    "headHeight",
    CROWN_Y - F["chin"],
    "landmarks.parts.head.crownHeight.adopted - normalization['sole->chin'].perView.front."
    "chin. crownHeight is the cap-MASS boundary (front/back agree to 0.00415), not the "
    "spike tip (the old 1.0): Stage 1's bare skull, not the hair. See crownHeight.caveat.",
)
KNEE_H = derive(
    "kneeHeight",
    RMS,
    "FLOORED at measurementUncertaintyRms: the pant-leg gather's own height is not "
    "measured, and the crease it contains is a single row",
)

# Y levels along the socket chain (§4's ledger), front view.
Y = {
    "ground": 0.0,
    "soleTop": SOLE_T,
    "ankleTop": F["pantHem"],
    "calfTop": F["pantLegCrease"],
    "kneeTop": F["pantLegCrease"] + KNEE_H,
    "hip": F["crotchNotchApex"],
    "pelvisTop": F["beltBottom"],
    "waistTop": F["beltTop"],
    "chestTop": F["shoulderLine"],
    "deltoidWaist": F["deltoidWaistline"],
    "backArmTop": F["upperArmNarrowest"],
    "elbow": ELBOW_Y,
    "fist": LM["parts"]["arm"]["glove"]["bottomHeight"],
    "neckTop": F["chin"],
    "skullTop": CROWN_Y,
}

# The pants conflict, recorded rather than smoothed over: the front view puts the pant-leg
# crease at row 604 and the crotch notch apex at row 605 — one pixel apart — so the thigh
# segment §4[5] describes has no height to occupy. The back view gives it 0.018, still
# inside RMS. Reported as a risk; the thigh's own turn re-measures before it is authored.
THIGH_H = derive(
    "thighHeight",
    abs(Y["hip"] - Y["kneeTop"]),
    "|crotchNotchApex - (pantLegCrease + kneeHeight)| in the front view; the two landmarks "
    "sit one pixel apart, so this is a conflict marker, not a segment height",
)

# --- authored -------------------------------------------------------------------------
AUTHORED = {
    "mannequinColor": {
        "value": "#B0B0B0",
        "why": "prompt §4's M-00 stand-in, one shared instance for the whole of Stage 1",
    },
    "roughness": {"value": 0.85, "why": "prompt §2 M-01 matte vinyl; not tuned per part"},
    "roughnessVariation": {
        "value": 0.04,
        "why": "per-facet value spread only; the vinyl carries no roughness map",
    },
    "metalness": {"value": 0.0, "why": "prompt §2: no metal anywhere in the figure"},
    "microAmplitude": {
        "value": 0.001,
        "why": "the schema demands a positive micro-band amplitude; the vinyl carries no "
        "micro relief at all, so this is the smallest value that records 'none'",
    },
    "triangleBudget": {
        "value": {
            "slab": 64,        # S-01 S-02 S-03 S-11: prisms with chamfered ends
            "loft": 96,        # S-04 S-05 S-08 S-09 S-10 S-12 S-13 S-14
            "oneOff": 160,     # S-06 S-07 S-15 S-17 S-28
            "wedge": 48,       # S-16 S-18..S-26
            "plane": 2,        # S-27 faceDecal
        },
        "why": "authored ceilings, generous enough that a part fails the facet gate on "
        "roundness before it fails on count",
    },
    "stage1bBlockoutMargin": {
        "value": UNC,
        "why": "prompt §6: the assembled figure must beat its own blockout by more than "
        "the measured cross-view uncertainty, so the margin IS that measurement",
    },
    "lighting": {
        "value": {"key": "#FFFFFF", "sky": "#FFFFFF", "ground": "#D8D8D8",
                  "ambient": "#C8C8C8", "background": "#FFFFFF",
                  "keyDirection": [-0.35, 0.75, 0.56]},
        "why": "flat product-shot lighting, read off the four orthographic references; "
        "neutral by choice because the references are white-balanced product shots",
    },
    "soleChamferCrop": {
        "value": {"x": [5, 165], "y": [700, 821], "zoom": 8},
        "why": "the front.webp window the sole's end chamfer was read in, at 8x NEAREST, "
        "where the corner cut reads as its own facet",
    },
    "targetFidelity": {
        "value": 0.75,
        "why": "authored review bar; the reference is a photographed toy, not a render, so "
        "a perfect match is not available",
    },
}

BUDGET = AUTHORED["triangleBudget"]["value"]

# --- part table (prompt.txt §2, §4) ----------------------------------------------------
# id, group, stage, shape code, factory, generator, colour code, origin socket, emitted
# sockets, box (w, h, d) with a pending flag, one-line role.
G = "group"
PENDING = "pending"


def box(w: float, h: float, d: float, *, measured: bool = False) -> dict:
    return {
        "width": round(w, 6),
        "height": round(h, 6),
        "depth": round(d, 6),
        "units": "relative",
        "confidence": 0.85 if measured else 0.2,
        "pending": not measured,
    }


TUBE_L, TUBE_R = DIM["straightPantTubeWidth"]
TORSO_D = max(DIM["torsoDepth"].values())

# Spec ids carry a `Group` suffix; the object-tree NAME is the bare one prompt §2 fixes.
# They have to differ: §2's head group contains a part also called head, and two components
# cannot share an id. partInspector reads the name, never this id.
GROUPS = [
    ("headGroup", "head"),
    ("armLeftGroup", "armLeft"),
    ("armRightGroup", "armRight"),
    ("torsoGroup", "torso"),
    ("legLeftGroup", "legLeft"),
    ("legRightGroup", "legRight"),
    ("hairGroup", "hair"),
    ("faceGroup", "face"),
]
GROUP_ID = {name: gid for gid, name in GROUPS}


def leg(side: str) -> list[tuple]:
    s = 1.0 if side == "L" else -1.0
    tube = TUBE_L if side == "L" else TUBE_R
    grp = "legLeft" if side == "L" else "legRight"
    return [
        (f"sole{side}", grp, 1, "S-01", "createSole", "one-off", "C-05b", "soleTop", [],
         box(SOLE_A, SOLE_T, SOLE_B, measured=True), (s * SOLE_X, Y["soleTop"], 0.0),
         "Flat trapezoid slab, wide at the heel and narrow at the toe, splay baked in."),
        (f"ankle{side}", grp, 1, "S-02", "createAnkle", "chamferedBox", "C-05b", "ankleTop",
         ["soleTop"], box(tube, Y["ankleTop"] - Y["soleTop"], tube),
         (s * SOLE_X, Y["ankleTop"], 0.0),
         "Boot cuff: a prism whose section is LARGER than the pant tube it swallows."),
        (f"calf{side}", grp, 1, "S-03", "createCalf", "chamferedBox", "C-04", "calfTop",
         ["ankleTop"], box(tube, Y["calfTop"] - Y["ankleTop"], tube),
         (s * SOLE_X, Y["calfTop"], 0.0),
         "Straight pant tube, near-constant width, one vertical front crease."),
        (f"knee{side}", grp, 1, "S-04", "createKnee", "loftPrism", "C-04", "kneeTop",
         ["calfTop"], box(tube, KNEE_H, tube), (s * SOLE_X, Y["kneeTop"], 0.0),
         "The pant-leg gather: the one corner that turns the taper above into the tube below."),
        (f"thigh{side}", grp, 1, "S-05", "createThigh", "loftPrism", "C-04", "hip",
         ["kneeTop"], box(tube, THIGH_H, tube), (s * SOLE_X, Y["hip"], 0.0),
         "Bloomer taper from the crotch down; NOT the widest point, the pelvis is."),
    ]


def arm(side: str) -> list[tuple]:
    s = 1.0 if side == "L" else -1.0
    grp = "armLeft" if side == "L" else "armRight"
    x = s * (DIM["shoulderWidth"] / 2 - DELTOID_W / 2)
    shape_front = "S-12" if side == "L" else "S-13"
    rows = [
        (f"upperDeltoid{side}", grp, 1, "S-10", "createUpperDeltoid", "loftPrism", "C-01",
         "shoulder", ["deltoidWaist"],
         box(DELTOID_W, Y["chestTop"] - Y["deltoidWaist"], DELTOID_W), (x, Y["chestTop"], 0.0),
         "Loft quad -> hexagon; its bottom hexagon is lowerDeltoid's top."),
        (f"lowerDeltoid{side}", grp, 1, "S-09", "createLowerDeltoid", "loftPrism", "C-01",
         "deltoidWaist", ["backArmTop"],
         box(DELTOID_W, Y["deltoidWaist"] - Y["backArmTop"], DELTOID_W),
         (x, Y["deltoidWaist"], 0.0),
         "Loft hexagon -> quad, so it mates with the upper arm's rectangular section."),
        (f"backArm{side}", grp, 1, "S-11", "createBackArm", "chamferedBox", "C-01",
         "backArmTop", ["elbow"],
         box(UPPER_ARM_W, Y["backArmTop"] - Y["elbow"], UPPER_ARM_W),
         (x, Y["backArmTop"], 0.0),
         "Slender upper arm, thinner than both the deltoid above and the forearm below."),
        (f"frontArm{side}", grp, 1, shape_front, "createFrontArm", "loftPrism", "C-01",
         "elbow", ["fist"],
         box(UPPER_ARM_W, Y["elbow"] - Y["fist"], UPPER_ARM_W), (x, Y["elbow"], 0.0),
         "Forearm + wrist + glove as ONE part; the elbow break puts the fist ahead of the hip."),
    ]
    if side == "L":
        rows.append(
            ("pauldronL", "armLeft", 3, "S-28", "createPauldron", "one-off", "C-07",
             "shoulder", [], box(DELTOID_W, Y["chestTop"] - Y["deltoidWaist"], DELTOID_W),
             (x, Y["chestTop"], 0.0),
             "Black shoulder cap over the LEFT upperDeltoid; its lower edge lands on the "
             "hexagonal waistline. Stage 3 by the user's recorded exception (§0.7).")
        )
    return rows


SPIKES = [
    "crownSpikeFront", "crownSpikeRear", "fringeRightOuter", "fringeRightMid",
    "fringeRightInner", "sideburnRight", "fringeLeft", "sideburnLeftUpper",
    "sideburnLeftLower",
]

PARTS: list[tuple] = [
    # torso
    ("pelvis", "torso", 1, "S-06", "createPelvis", "one-off", "C-04", "pelvisTop",
     ["hipL", "hipR"],
     box(DIM["maxHipWidth"], Y["pelvisTop"] - Y["hip"], DIM["maxHipDepth"]),
     (0.0, Y["pelvisTop"], 0.0),
     "The largest volume in the model: pentagon in front, front/back-symmetric kite in profile."),
    ("waist", "torso", 1, "S-07", "createWaist", "one-off", "C-05", "waistTop", ["pelvisTop"],
     box(DIM["chestWidth"], Y["waistTop"] - Y["pelvisTop"], TORSO_D), (0.0, Y["waistTop"], 0.0),
     "Belt: a flat band standing proud of both the chest above and the pelvis below."),
    ("chest", "torso", 1, "S-08", "createChest", "loftPrism", "C-03", "chestTop",
     ["waistTop", "neckBase", "shoulderL", "shoulderR"],
     box(DIM["chestWidth"], Y["chestTop"] - Y["waistTop"], TORSO_D), (0.0, Y["chestTop"], 0.0),
     "Flat faceted slab, near-hexagonal in front, widest at the shoulder line."),
    # head
    ("neck", "head", 1, "S-14", "createNeck", "loftPrism", "C-01", "neckTop", ["neckBase"],
     box(DIM["neckWidth"], Y["neckTop"] - Y["chestTop"], DIM["neckWidth"]),
     (0.0, Y["neckTop"], 0.0),
     "Short faceted column, 8 radial segments, flat shaded."),
    ("head", "head", 1, "S-15", "createHead", "one-off", "C-01", "skullTop", ["neckTop"],
     box(DIM["hairCapWidth"], HEAD_H, DIM["hairCapWidth"]), (0.0, Y["skullTop"], 0.0),
     "Faceted skull and face, no hair, no ears, no eyes; carries the five faceGroups."),
    # hair (stage 2)
    ("hairCap", "hair", 2, "S-17", "createHairCap", "one-off", "C-02", "skullTop", [],
     box(DIM["hairCapWidth"], HEAD_H, DIM["hairCapWidth"]), (0.0, Y["skullTop"], 0.0),
     "Faceted dome conforming to head's scalp faceGroup; the ears stay outside it."),
    # face (stage 2)
    ("earL", "face", 2, "S-16", "createEar", "triWedge", "C-01", "ear", [],
     box(LM["hairThickness"]["left"]["medianNormalized"], RMS, RMS),
     (DIM["hairCapWidth"] / 2, Y["neckTop"] + HEAD_H / 2, 0.0),
     "Triangular prism growing laterally out of head's ear faceGroup."),
    ("earR", "face", 2, "S-16", "createEar", "triWedge", "C-01", "ear", [],
     box(LM["hairThickness"]["left"]["medianNormalized"], RMS, RMS),
     (-DIM["hairCapWidth"] / 2, Y["neckTop"] + HEAD_H / 2, 0.0),
     "Mirror of earL; the pair is one shape code."),
    ("faceDecal", "face", 2, "S-27", "createFaceDecal", "plane", "C-09", "face", [],
     box(DIM["hairCapWidth"] / 2, HEAD_H / 2, 0.0),
     (0.0, Y["neckTop"] + HEAD_H / 2, DIM["hairCapWidth"] / 2),
     "Eyes, brows and lash line as ONE CanvasTexture plane; a detail, not a part."),
]
PARTS += leg("L") + leg("R") + arm("L") + arm("R")
PARTS += [
    (sid, "hair", 2, f"S-{18 + i}", "createHairSpike", "triWedge", "C-02", "scalp", [],
     box(DIM["hairCapWidth"] / 4, HEAD_H / 2, DIM["hairCapWidth"] / 4),
     (0.0, Y["skullTop"], 0.0),
     "One hair spike; the nine are NOT mirror symmetric and their shape codes collapse "
     "only where they measure the same.")
    for i, sid in enumerate(SPIKES)
]

STAGE1 = [p[0] for p in PARTS if p[2] == 1]
STAGE2 = [p[0] for p in PARTS if p[2] == 2]
STAGE3 = [p[0] for p in PARTS if p[2] == 3]

BUDGET_BY_GENERATOR = {
    "one-off": BUDGET["oneOff"], "chamferedBox": BUDGET["slab"], "loftPrism": BUDGET["loft"],
    "triWedge": BUDGET["wedge"], "plane": BUDGET["plane"],
}

# --- materials ------------------------------------------------------------------------
# prompt §2: exactly TWO material codes in the finished model plus the Stage 1 stand-in.
# Every colour code is a localOverride on the vinyl, because that is what they are: one
# material, many albedo regions.
CODE_REGION = {
    "C-01": "skin, lit", "C-01s": "skin, mid and shadow", "C-02": "hair",
    "C-03": "shirt", "C-04": "pants", "C-05": "belt", "C-05b": "boot and sole",
    "C-07": "gloves and pauldron", "C-08": "left bracer",
}


def rgba(hex_color: str) -> str:
    v = hex_color.lstrip("#")
    r, g, b = (int(v[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, 1.0)"


def code_color(code: str) -> str:
    """A colour code's adopted albedo. C-09 is a texture, not a flat colour (prompt §2), so
    it borrows the skin it is printed on rather than inventing a swatch."""
    entry = PALETTE["codes"].get(code) or {}
    if "adopted" in entry:
        return entry["adopted"]
    if code == "C-09":
        return PALETTE["codes"]["C-01"]["adopted"]
    return AUTHORED["mannequinColor"]["value"]


def bands() -> list[dict]:
    return [
        {"id": "macro", "frequency": 1.0, "amplitude": 0.10,
         "role": "region albedo separation measured by spec/sample_palette.py"},
        {"id": "meso", "frequency": 4.0, "amplitude": 0.02,
         "role": "facet-to-facet value step under flat shading"},
        {"id": "micro", "frequency": 24.0,
         "amplitude": AUTHORED["microAmplitude"]["value"],
         "role": "none: the vinyl surface carries no micro relief"},
    ]


def material(mid: str, name: str, base: str, notes: str, overrides: list[dict]) -> dict:
    secondary = code_color("C-01s") if overrides else base
    return {
        "id": mid,
        "name": name,
        "type": "standard",
        "shaderModel": "MeshStandardMaterial",
        "baseColor": base,
        "color": base,
        "albedo": {
            "dominant": base,
            "secondary": [secondary],
            "samplingNotes": (
                "Every stop is a cluster centroid from spec/sample_palette.py, identified by "
                "position (mean y, mean x about the mirror axis), never by eye-dropper point."
            ),
        },
        "colorVariation": {
            "palette": [code_color(c) for c in CODE_REGION] if overrides else [base],
            "pattern": "flat regions with hard boundaries at the part seams",
            "amplitude": 0.0,
            "heightCorrelation": 0.0,
        },
        "textureResolution": 512,
        "textureProjection": {
            "mode": "generated-object-space",
            "repeat": [1.0, 1.0],
            "anisotropy": 1,
            "texelDensityIntent": (
                "Vertex colours and one face decal only; no tiling map exists to hold a "
                "texel density target."
            ),
        },
        "surfaceFrequencyBands": bands(),
        "roughness": {
            "base": AUTHORED["roughness"]["value"],
            "variation": AUTHORED["roughnessVariation"]["value"],
            "map": "independent-procedural-field",
            "localResponse": "per-facet only; the flat shading already separates the planes",
        },
        "metalness": {"base": AUTHORED["metalness"]["value"], "variation": 0.0},
        "normal": {"pattern": "none", "strength": 0.0, "scale": 1.0, "space": "tangent"},
        "bump": {"pattern": "none", "amplitude": 0.0, "scale": 1.0},
        "displacement": {"pattern": "none", "amplitude": 0.0, "scale": 1.0,
                         "silhouetteAffects": False},
        "ambientOcclusion": {
            "cavityStrength": 0.12,
            "contactShadowBias": 0.30,
            "map": "independent-contact-field",
            "notes": "Contacts only: the boot-cuff step, the belt's two steps, the deltoid "
                     "waistline and the hair-cap edge. The figure has no cavities.",
        },
        "wear": {"edgeWear": 0.0, "scratches": [], "chips": []},
        "dirt": {"amount": 0.0, "cavityBias": 0.0, "color": "#232427"},
        "localOverrides": overrides,
        "shaderNotes": [
            notes,
            "flatShading is true on every material; it is the object's identity, not a style.",
            "No normal, bump or displacement map: the subject is smooth vinyl with hard creases.",
        ],
        "notes": notes,
    }


def overrides() -> list[dict]:
    return [
        {
            "id": code,
            "region": region,
            "baseColor": code_color(code),
            "roughness": AUTHORED["roughness"]["value"],
            "evidenceRefs": ["full-object"],
        }
        for code, region in CODE_REGION.items()
    ]


MATERIALS = [
    material(
        "mannequin", "M-00 Stage 1 mannequin grey", AUTHORED["mannequinColor"]["value"],
        "Stage 1 stand-in. ONE instance shared by all 23 parts; a second colour constant "
        "or any texture inside a Stage 1 part file is a FAIL (prompt §4).",
        [],
    ),
    material(
        "matteVinyl", "M-01 matte vinyl", code_color("C-04"),
        "The whole finished figure is this one material. All the variation lives on the "
        "COLOUR axis, so Stage 3's job is sampling colour, not tuning material (prompt §2).",
        overrides(),
    ),
    material(
        "printedFace", "M-02 printed face", code_color("C-01"),
        "M-01 plus one map: the only textured surface in the model. Eyes, pupils, sclera, "
        "lash line and brows are PRINTED, never geometry (prompt §2c).",
        [{
            "id": "C-09",
            "region": "printed face decal",
            "baseColor": code_color("C-01"),
            "roughness": AUTHORED["roughness"]["value"],
            "evidenceRefs": ["full-object"],
        }],
    ),
]

MATERIAL_OF_STAGE = {1: "mannequin", 2: "matteVinyl", 3: "matteVinyl"}


# --- component tree -------------------------------------------------------------------
def socket_entry(sid: str, local: tuple[float, float, float]) -> dict:
    return {
        "id": sid,
        "localPosition": [round(v, 6) for v in local],
        "localRotation": [0.0, 0.0, 0.0],
    }


def component(
    cid: str, name: str, level: str, parent: str | None, material_id: str, *,
    dims: dict, position: tuple[float, float, float], sockets: list[dict],
    role: str = "body", note: str = "", features: list[dict] | None = None,
    parent_socket: str | None = None, child_socket: str | None = None,
    budget: int | None = None, colour: str = "C-01",
) -> dict:
    attachment = None
    if parent and parent_socket and child_socket:
        attachment = {
            "parentId": parent,
            "parentSocket": parent_socket,
            "childSocket": child_socket,
            "contactType": "socket",
            "localStart": [0.0, 0.0, 0.0],
            "localEnd": [0.0, -dims["height"], 0.0],
            "contactNormal": [0.0, 1.0, 0.0],
            "embedDepth": 0.0,
            "overlap": 0.0,
            "gapTolerance": 1e-06,
            "baseRadius": max(0.001, round(dims["width"] / 2, 6)),
            "endRadius": max(0.001, round(dims["width"] / 2, 6)),
            "notes": "Stage 1B assembly is pure translation: the pose is baked into the "
                     "part, so the local origin IS this socket (prompt §1.4).",
            "evidenceRefs": ["full-object"],
        }
    base = code_color(colour)
    return {
        "id": cid,
        "name": name,
        "level": level,
        "role": role,
        "importance": 1.0 if level == "macro" else 0.75,
        "confidence": dims["confidence"],
        "primitive": "box",
        "topologyClass": "assembled-solid",
        "topologyRationale": (
            "A discrete faceted solid socketed onto its neighbour. Nothing here is a shell "
            "or a continuous sculpt: the subject is an assembled vinyl toy."
        ),
        "geometryDescriptor": {
            "topologyIntent": "hard flat facets, visible edge creases, zero smoothing groups",
            "edgeTreatment": {"type": "chamfer", "bevelRadius": 0.0, "segments": 1},
            "deformationStack": [],
            "uvStrategy": "generated object-space coordinates",
            "normalStrategy": "flat normals; every authored plane reads as one facet",
        },
        "colorMaterialRecipe": {
            "dominantAlbedo": rgba(base),
            "secondaryAlbedo": rgba(code_color("C-01s")),
            "materialClass": "plastic",
            "materialClassConfidence": 0.9,
            "colorGradient": {
                # Both stops are the same colour on purpose: a part is ONE flat region.
                "type": "linear",
                "axis": "long-axis",
                "stops": [{"position": 0.0, "color": rgba(base)},
                          {"position": 1.0, "color": rgba(base)}],
            },
            "evidenceRefs": ["full-object"],
        },
        "parent": parent,
        "attachment": attachment,
        "dimensions": dims,
        "transform": {
            "position": [round(v, 6) for v in position],
            "rotation": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
        },
        "actionProfile": {
            "animationRole": "root" if parent is None else "detachable-part",
            "pivot": {"mode": "custom", "localPosition": [0.0, 0.0, 0.0],
                      "axis": [0.0, 1.0, 0.0], "confidence": dims["confidence"]},
            "transformChannels": {
                "translate": True, "rotate": False, "scale": False, "bend": False,
                "twist": False, "detach": parent is not None, "visibility": True,
                "materialState": True,
            },
            "sockets": sockets,
            "collider": {"type": "box", "offset": [0.0, 0.0, 0.0],
                         "scale": [dims["width"], dims["height"], dims["depth"]],
                         "isTrigger": False, "notes": "Axis-aligned box proxy."},
            "constraints": [],
            "destruction": {"breakable": False, "fractureGroup": cid, "seamRefs": [],
                            "detachableFragments": [], "breakImpulse": 0.0,
                            "debrisMaterial": material_id},
        },
        "material": material_id,
        "materialLayers": [material_id],
        "deformations": [],
        "joints": [],
        "seams": [],
        "localFeatures": features or [],
        "surfaceDetail": {
            "macroRoughness": 0.0, "microRoughness": 0.0, "bumpAmplitude": 0.0,
            "normalPattern": "none", "displacementPattern": "none",
            "occlusionPattern": "contact-only", "edgeWearPattern": "none",
            "notes": "Facet boundaries carry every visible detail; there is no surface relief.",
        },
        "evidenceRefs": ["full-object"],
        "details": [],
        "fidelityTier": "hero" if level == "macro" else "detail",
        "triangleBudget": budget or BUDGET["oneOff"],
        "notes": note,
    }


FEATURES = {
    "soleL": [
        {"id": "sole-toe-chamfer", "kind": "bevel",
         "description": "Blunt chamfer at the toe end, its own facet at 8x; "
                        f"{SOLE['planTrapezoid']['endChamfer']:.5f} deep.",
         "evidenceRefs": ["full-object"]},
        {"id": "sole-heel-chamfer", "kind": "bevel",
         "description": "The heel end carries the same chamfer, so the slab reads as a "
                        "trapezoid with two cut ends rather than a wedge.",
         "evidenceRefs": ["full-object"]},
        {"id": "sole-top-ledge", "kind": "contour",
         "description": "The top face emerges from under the boot cuff as a clean ledge "
                        "running all the way round.",
         "evidenceRefs": ["full-object"]},
    ],
    "ankleL": [{"id": "bootcuff-step", "kind": "contour",
                "description": "Hard step all round where the cuff swallows the pant tube.",
                "evidenceRefs": ["full-object"]},
               {"id": "bootcuff-vertical-chamfer", "kind": "bevel",
                "description": "Four chamfered vertical edges, each catching its own tone.",
                "evidenceRefs": ["full-object"]}],
    "calfL": [{"id": "pant-front-crease", "kind": "groove",
               "description": "One vertical crease down the front centre of the pant tube.",
               "evidenceRefs": ["full-object"]}],
    "kneeL": [{"id": "pantleg-corner", "kind": "contour",
               "description": "Exactly one hard corner: taper above, near-vertical below.",
               "evidenceRefs": ["full-object"]}],
    "pelvis": [{"id": "crotch-notch", "kind": "groove",
                "description": "Inverted-V notch cutting up between the legs.",
                "evidenceRefs": ["full-object"]},
               {"id": "hip-kite", "kind": "contour",
                "description": "Front/back-symmetric kite in profile, deepest at the widest height.",
                "evidenceRefs": ["full-object"]}],
    "waist": [{"id": "belt-proud-step", "kind": "contour",
               "description": "The belt stands proud of chest and pelvis, one hard step per edge.",
               "evidenceRefs": ["full-object"]}],
    "chest": [{"id": "chest-hexagon", "kind": "contour",
               "description": "Near-hexagonal front outline, widest at the shoulder line.",
               "evidenceRefs": ["full-object"]}],
    "upperDeltoidL": [{"id": "deltoid-hex-waistline", "kind": "seam",
                       "description": "Hexagonal waistline where the two deltoid segments meet.",
                       "evidenceRefs": ["full-object"]}],
    "backArmL": [{"id": "upperarm-thin", "kind": "contour",
                  "description": "Thinner in section than both the deltoid above and the "
                                 "forearm below; the contrast is an identity feature.",
                  "evidenceRefs": ["full-object"]}],
    "frontArmL": [{"id": "forearm-widens-downward", "kind": "contour",
                   "description": "The forearm thickens as it descends. Toy styling, not an error.",
                   "evidenceRefs": ["full-object"]},
                  {"id": "bracer-overhang", "kind": "contour",
                   "description": "The LEFT wrist block is the grey bracer, ~1.05x wider, its "
                                  "lower edge overhanging.",
                   "evidenceRefs": ["full-object"]},
                  {"id": "glove-flat-cut", "kind": "seam",
                   "description": "Chamfered cuboid glove, no fingers, one flat cut to the wrist.",
                   "evidenceRefs": ["full-object"]},
                  {"id": "elbow-break-forward", "kind": "contour",
                   "description": "The elbow breaks forward; the fist lands ahead of the hip line.",
                   "evidenceRefs": ["full-object"]}],
    "pauldronL": [{"id": "pauldron-left-only", "kind": "contour",
                   "description": "Black cap on the LEFT deltoid only. Handedness carrier.",
                   "evidenceRefs": ["full-object"]}],
    "hairCap": [{"id": "hairline-occiput-hard", "kind": "contour",
                 "description": "Hard horizontal line across the occiput; the only directly "
                                "measurable stretch of hairline.",
                 "evidenceRefs": ["full-object"]},
                {"id": "hair-spikes-not-mirrored", "kind": "contour",
                 "description": "Nine spikes, not mirrored: the head band scores mirrorIoU "
                                "0.657 against a 0.858 whole-figure floor.",
                 "evidenceRefs": ["full-object"]}],
    "earL": [{"id": "ears-outside-cap", "kind": "contour",
              "description": "The ears sit outside the hair cap; a skin wedge shows below it.",
              "evidenceRefs": ["full-object"]}],
    "head": [{"id": "jaw-chamfer-pointed-chin", "kind": "bevel",
              "description": "Near-planar face, widest at the cheekbones, chamfered jaw, "
                             "small pointed chin.",
              "evidenceRefs": ["full-object"]}],
    "faceDecal": [{"id": "face-print-eyes-brows-only", "kind": "decal",
                   "description": "Blue irises, dark pupils, white sclera, black upper lash "
                                  "line and brows, and nothing else. No printed nose or mouth.",
                   "evidenceRefs": ["full-object"]},
                  {"id": "flat-shaded-facets", "kind": "decal",
                   "description": "Every surface is flat-shaded matte vinyl; hard facet "
                                  "boundaries with no smooth gradient anywhere.",
                   "evidenceRefs": ["full-object"]}],
}


def build_components() -> list[dict]:
    comps = [component(
        "cloudStrifeFigure", "FF7 Cloud Strife polygon figure (root)", "macro", None,
        "mannequin",
        dims=box(DIM["shoulderWidth"], 1.0, DIM["maxHipDepth"]),
        position=(0.0, 0.0, 0.0), sockets=[], role="root",
        note="Assembly root. Authors no geometry itself (prompt §6).",
    )]
    for gid, gname in GROUPS:
        comps.append(component(
            gid, gname, "macro", "cloudStrifeFigure", "mannequin",
            dims=box(DIM["shoulderWidth"] / 2, 1.0 / len(GROUPS), DIM["maxHipDepth"]),
            position=(0.0, 0.0, 0.0),
            sockets=[socket_entry("figureOrigin", (0.0, 0.0, 0.0))], role="group",
            parent_socket="figureOrigin", child_socket="figureOrigin",
            note="Container node. partInspector descends through it because it holds named, "
                 "mesh-bearing children (prompt §1.6).",
        ))
    for (cid, grp, stage, shape, factory, generator, colour, origin, emits, dims,
         position, note) in PARTS:
        sockets = [socket_entry(origin, (0.0, 0.0, 0.0))]
        sockets += [socket_entry(sid, (0.0, -dims["height"], 0.0)) for sid in emits]
        comps.append(component(
            cid, cid, "meso" if cid != "faceDecal" else "micro", GROUP_ID[grp],
            MATERIAL_OF_STAGE[stage],
            dims=dims, position=position, sockets=sockets,
            features=FEATURES.get(cid, []),
            parent_socket=origin, child_socket=origin,
            budget=BUDGET_BY_GENERATOR[generator], colour=colour,
            note=f"stage {stage} · shape {shape} · {factory} · generator {generator} · "
                 f"colour {colour} · {note}",
        ))
    return comps


# --- passes ---------------------------------------------------------------------------
# prompt §0.7 rule 4 forbids inventing a SECOND stage numbering. The forge's pass ids are a
# fixed third-party vocabulary, so the map between them is written down ONCE, here, and the
# prompt's stage numbers stay authoritative.
STAGE_MAP = [
    ("blockout", "prompt Stage 1 — 23 monochrome structural parts, each gated on its own"),
    ("structural-pass", "prompt Stage 1B — rough assembly, socket placement only"),
    ("form-refinement", "prompt Stage 2 — surface geometry: face, hair, ears"),
    ("material-pass", "prompt Stage 3 — colour applied, material folded in (2 codes)"),
    ("surface-pass", "prompt Stage 5 — full integration and refinement"),
    ("interaction-pass", "prompt Stage 6 — detail iteration and part exposure"),
    ("optimization-pass", "hold the triangle budget without changing any silhouette"),
]

PASS_COMPONENTS = {
    "blockout": ["cloudStrifeFigure", *(g for g, _ in GROUPS), *STAGE1],
    "structural-pass": ["cloudStrifeFigure", *(g for g, _ in GROUPS), *STAGE1],
    "form-refinement": ["cloudStrifeFigure", "hairGroup", "faceGroup", "head", *STAGE2],
    "material-pass": ["cloudStrifeFigure", *STAGE1, *STAGE2, *STAGE3],
    "surface-pass": ["cloudStrifeFigure", *STAGE1, *STAGE2, *STAGE3],
    "interaction-pass": ["cloudStrifeFigure", *(g for g, _ in GROUPS)],
    "optimization-pass": ["cloudStrifeFigure", *STAGE1, *STAGE2, *STAGE3],
}

PASS_ACCEPTANCE = {
    "blockout": [
        f"Every part passes the facet gate: fraction of adjacent face pairs at or above "
        f"{FACET['angleDeg']} degrees is at least {FACET['threshold']}, pinned by the smooth "
        f"sphere and the lofted egg both failing (spec/facet-gate.json).",
        "flatShading is true and the triangle count is inside the part's own budget.",
        "Socket alignment: every mating name in the ledger agrees from both sides to under 1e-06.",
        "partInspector reports each part once, with the name and module from prompt §2.",
        "The 8 pure mirror pairs match point for point after negating x.",
    ],
    "structural-pass": [
        "Four-view silhouette IoU beats the bounding-prism blockout in EVERY view by more "
        f"than {UNC} (spec/landmarks.json measurementUncertainty).",
        "The clipped rows and columns recorded per view are masked out of both images first.",
        "The assembly file authors no geometry and performs no rotations.",
    ],
    "form-refinement": [
        "Skull plus hair cap plus spikes reproduce back.webp's outer silhouette.",
        "The ears sit outside the hair cap, matching the exposed skin wedge in back.webp.",
        "The face decal registers to the head's face faceGroup with no z-fighting.",
    ],
    "material-pass": [
        "Every colour code lands within the delta-E budget of its cluster centroid in "
        "spec/palette.json; the cool four-view set is the adopted source.",
        "Only two material codes exist in the finished model: matte vinyl and the printed face.",
        "pauldronL's arrival is re-checked against Stage 1B's four-view IoU (prompt §8.5b), "
        "which is what licenses its deferral past Stage 2.",
    ],
    "surface-pass": ["Every joint in the socket chain reads continuous at 6-8x NEAREST."],
    "interaction-pass": [
        "Each part is selectable and isolatable on its own, and the explode control appears.",
    ],
    "optimization-pass": ["No silhouette-changing decimation; every authored plane survives."],
}


def build_passes() -> list[dict]:
    return [
        {
            "id": pid,
            "goal": goal,
            "componentRefs": PASS_COMPONENTS[pid],
            "acceptance": PASS_ACCEPTANCE[pid],
        }
        for pid, goal in STAGE_MAP
    ]


FEATURE_TARGETS = [
    ("anatomy-proportion", "Segment proportions match the measured landmark chain",
     "critical", ["blockout", "structural-pass"], ["cloudStrifeFigure"]),
    ("pose-silhouette", "The baked pose reads: forward-broken elbows, abducted upper arms, "
     "splayed feet", "critical", ["blockout", "structural-pass"],
     ["frontArmL", "frontArmR", "soleL", "soleR"]),
    ("face-landmark-placement", "Eye line and decal registration against the reference",
     "important", ["form-refinement", "material-pass"], ["faceDecal", "head"]),
    ("outfit-and-palette", "Every colour code lands on the right region",
     "critical", ["material-pass"], ["chest", "pelvis", "waist", "ankleL", "frontArmL"]),
    ("handedness", "Black pauldron and grey bracer are both on the figure's LEFT",
     "critical", ["material-pass"], ["pauldronL", "frontArmL"]),
    ("faceted-identity", "Hard flat facets with visible creases; nothing smoothed",
     "critical", ["blockout", "form-refinement", "optimization-pass"],
     ["cloudStrifeFigure"]),
    ("pantleg-single-corner", "Exactly one corner between crotch and boot cuff",
     "critical", ["blockout", "structural-pass"], ["thighL", "kneeL", "calfL"]),
    ("boot-cuff-step", "The cuff's section is larger than the pant tube it swallows",
     "important", ["blockout"], ["ankleL", "calfL"]),
    ("upper-arm-thinner", "The upper arm is thinner than both its neighbours",
     "important", ["blockout"], ["backArmL", "lowerDeltoidL", "frontArmL"]),
    ("sole-forward-wedge", "The sole extends far forward and only slightly back",
     "important", ["blockout"], ["soleL", "soleR"]),
]


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text())
    comps = build_components()

    spec["targetId"] = "ff7-cloud-strife-polygon-figure"
    spec["sourceImage"] = f"{REFS}/front.webp"
    # `conditional`, not `pass`: the risks below are open, and the validator is right that a
    # clean verdict alongside a live risk list is a contradiction.
    spec["suitability"] = "conditional"
    spec["reviewHistory"] = []
    spec["sculptPipeline"] = {
        **spec.get("sculptPipeline", {}),
        "currentPass": "blockout",
        "completedPasses": [],
        "passGateMode": "locked-sequential",
        "passOrder": [pid for pid, _ in STAGE_MAP],
        "lastCompletedPass": None,
        "blockedReason": "",
        "stageMap": [{"passId": pid, "promptStage": goal} for pid, goal in STAGE_MAP],
        "nextRequiredEvidence": [
            "per-part render and orbit renders",
            "reference crop and render side by side at 6-8x NEAREST",
            "every gate's number, marked PASS or FAIL",
        ],
    }

    # The starter's assessment scores are the 0-10 scale the pre-spec tool writes; the spec
    # schema wants 0-3. Rescale rather than retype, so the ordering stays the assessment's.
    scores = spec["preSpecAssessment"]["complexity"]["scores"]
    for key, value in list(scores.items()):
        if isinstance(value, int) and value > 3:
            scores[key] = min(3, round(value * 3 / 10))
    for detail in spec["preSpecAssessment"]["detailInventory"]["details"]:
        detail["kind"] = {"geometry": "contour", "material": "decal"}.get(
            detail.get("kind"), detail.get("kind"))
    known = {f["id"] for comp in comps for f in comp["localFeatures"]}
    for detail in spec["preSpecAssessment"]["detailInventory"]["details"]:
        if detail["id"] in known:
            detail["mapsTo"] = {"ref": detail["id"], "kind": "component.localFeatures"}
    spec["preSpecAssessment"]["unknownsToResolveBeforeImplementation"] = []
    spec["preSpecAssessment"]["resolvedUnknowns"] = [
        "Forehead hairline is hidden by the fringe: derived from the side-view hair-cap "
        "thickness. Guess list item 1, default reading A.",
        "The crown is clipped in all four orthographic views, so total height 1.000 is "
        "extrapolated from left.webp's two straight spike edges.",
        "hipYokeVTip is not separable by colour (shirt and pants purple differ by 0.007 in "
        "cluster mean y); it is absent from landmarks.json and only a spatial boundary can "
        "find it.",
        "Occiput hair thickness is fringe depth, not cap-shell thickness; insetting "
        "back.webp by it would overshoot.",
        "Foot splay is solved from the plan trapezoid, not read off the bounding-box "
        "diagonal that poseAngles.footSplayDeg records.",
    ]

    spec["componentTree"] = comps
    spec["materials"] = MATERIALS
    spec["buildPasses"] = build_passes()
    spec["rig"] = {
        "skeleton": "none",
        "why": "prompt §1.4: the pose is baked into every part and there is no animation "
               "requirement, so a skeleton would be a rig nothing drives. "
               "spec/character-contracts.md carries the full argument.",
        "bones": [],
    }
    spec["repetitionSystems"] = [
        {
            "id": "mirror-pairs",
            "name": "Eight pure left/right mirror pairs",
            "realization": "shared-geometry",
            "buildsGeometry": True,
            "instances": 8,
            "rule": "One factory emits one geometry parameterised by sideSign; the R part is "
                    "the L part with x negated. Measured, not assumed: banded mirror IoU on "
                    "front.webp against a 0.858 whole-figure floor, read by extent difference "
                    "(1-3px on the pure pairs, 11px on the forearms).",
            "componentRefs": ["soleL", "ankleL", "calfL", "kneeL", "thighL",
                              "upperDeltoidL", "lowerDeltoidL", "backArmL"],
            "evidenceRefs": ["full-object"],
        },
        {
            "id": "hair-spikes",
            "name": "Nine hair spikes",
            "realization": "shared-generator",
            "buildsGeometry": True,
            "instances": 9,
            "rule": "triWedge builds all nine; shape codes S-18..S-26 collapse wherever two "
                    "spikes measure the same. NOT mirror symmetric.",
            "componentRefs": SPIKES,
            "evidenceRefs": ["full-object"],
        },
    ]
    spec["featureReviewTargets"] = [
        {"id": fid, "name": name, "tier": tier, "passIds": passes, "minimumScore": 0.7,
         "componentRefs": refs, "evidenceRefs": ["full-object"]}
        for fid, name, tier, passes, refs in FEATURE_TARGETS
    ]
    spec["qualityTargets"] = {
        "targetFidelity": AUTHORED["targetFidelity"]["value"],
        "mustMatch": [
            "hard flat facets and visible edge creases — the faceting IS the identity",
            "the baked pose: forward-broken elbows, abducted upper arms, splayed feet",
            "handedness: black pauldron and grey bracer both on the figure's LEFT",
            "the four-view silhouette, with the clipped rows and columns masked out",
        ],
        "niceToHave": ["the printed face's exact lash-line weight"],
        "fpsTarget": 60,
        "reviewViewpoints": ["front", "back", "left", "right", "three-quarter"],
    }
    spec["performanceBudget"] = {
        **spec.get("performanceBudget", {}),
        "qualityPriority": "reference-fidelity",
        "targetTriangles": sum(c["triangleBudget"] for c in comps),
        "maxDrawCalls": len(comps),
        "textureSize": 512,
        "optimizationPolicy": "Never decimate: every plane in this model is authored and "
                              "removing one changes a facet the gate measures.",
    }
    # prompt §2 fixes the finished model at TWO material codes plus the Stage 1 stand-in, so
    # the template's default floor of 4 describes a different object.
    spec["qualityContract"]["minimumSpecDepth"]["materialLayers"] = len(MATERIALS)
    spec["qualityContract"]["definitionOfDone"] = [
        "Every Stage 1 part passes its own gates before Stage 1B starts; no part is "
        "self-certified and no two parts are built in one turn (prompt §0.3).",
        f"Facet gate: adjacent-normal fraction at {FACET['angleDeg']} degrees is at least "
        f"{FACET['threshold']}, with both fake frames failing and all three controls passing.",
        f"Socket alignment under 1e-06 for every mating name in the ledger.",
        f"Stage 1B four-view IoU beats the blockout floor by more than {UNC} in every view.",
        "All geometry is finished before any colour, with pauldronL the single recorded "
        "exception and §8.5b's four-view re-check as its compensating gate.",
        "Every figure in this spec traces to an artefact under artifacts/exhibits/"
        "ff7-cloud-strife-polygon-figure/ — spec/audit_records.py is what checks it.",
    ]
    spec["lightingFromPhoto"] = [
        {"role": "key", "type": "directional", "direction": [-0.35, 0.75, 0.56],
         "color": "#FFFFFF", "intensity": 1.0,
         "evidence": "The four orthographic references are flat-lit product shots: the "
                     "brightest facets face up and slightly to the camera's left, and no "
                     "facet is crushed to black."},
        {"role": "fill", "type": "hemisphere", "skyColor": "#FFFFFF",
         "groundColor": "#D8D8D8", "intensity": 0.55,
         "note": "A hemisphere fill keeps the facet value steps readable, which is the "
                 "whole point of a flat-shaded subject."},
        {"role": "environment", "type": "ambient", "color": "#C8C8C8", "intensity": 0.25,
         "note": "No rim light exists in the references; low ambient stands in for it."},
        {"role": "rendering", "exposure": 1.0,
         "toneMapping": "LinearToneMapping — ACES filmic would desaturate the purple shirt "
                        "and pants, which are the two colours the palette gate turns on",
         "background": "#FFFFFF to match the product shots",
         "note": "Ambient occlusion and contact shadow stay on the contacts only: the "
                 "boot-cuff step, the belt's two edges, the deltoid waistline, the hair-cap "
                 "edge. No ground shadow; the references float on white."},
    ]
    spec["lookDevTargets"] = {
        "reviewBackground": "#FFFFFF",
        "keyDirection": [-0.35, 0.75, 0.56],
        "note": "Flat product-shot lighting. The subject carries no maps of any kind, so "
                "there is no reference-PBR extraction target to hit: prompt §2 fixes the "
                "finished model at two material codes and puts every variation on the "
                "colour axis.",
    }
    spec["risks"] = [
        "PANTS SEGMENTATION IS UNRESOLVED. front.webp puts the pant-leg crease at row 604 "
        "and the crotch-notch apex at row 605 — one pixel apart — so the thigh segment §4[5] "
        "describes has no height to occupy (back.webp gives it 0.018, still inside "
        "measurementUncertaintyRms). Either the crease is being found at the crotch or the "
        "four-segment split is wrong. thigh/knee/calf must be re-measured together before "
        "thigh is authored; the sole, ankle and calf are unaffected.",
        "self-check A (hip wider than the shoulder LINE) FAILS by 0.0965 while A1 (hip wider "
        "than the chest SLAB) passes by 0.0851. §4[6]'s 'wider than the shoulders' therefore "
        "means the chest slab. Recorded in landmarks.json promptDisagreements.",
        "The sole's plan outline (L/W, toe taper, end chamfer) is unobservable from four "
        "orthographic views: A, B and T fix all four silhouettes identically for every "
        "(L, W, theta). Only the three-quarter orbit render can falsify the adopted values, "
        "so the orthographic IoU must never be reported as confirming the plan shape.",
        "measurementUncertainty is a cross-view landmark tolerance, not a per-part shape "
        "tolerance: at 0.05447 it is about 43px of front.webp against a 4.7px reference fit "
        "residual, which would make the shape gates vacuous. Part-shape assertions use the "
        "RMS instead.",
        "Every component except the two soles carries dimensions.pending: its box is the "
        "enclosing landmark span, which bounds the part without measuring it.",
    ]
    spec["assumptions"] = [
        f"Sole plan aspect L/W = {SOLE['adopted']['aspectLtoW']} — adopted, not measured.",
        f"Sole toe taper {SOLE['adopted']['toeTaper']} — §4[1] says narrow at the toe but no "
        "view measures how much.",
        f"Sole end chamfer {SOLE['adopted']['endChamferOfThickness']} of thickness, read off "
        "front.webp x5..165 y700..821 at 8x where the corner cut reads as its own facet.",
        "The hair cap does not cover the ears (guess list §11.4, reading A): back.webp at "
        "5-6x shows a skin wedge exposed left and right below the cap edge.",
        "The knee segment's height is floored at the measurement RMS; its own height is not "
        "measured and the crease it contains is a single row.",
        "The sole's socket sits over the middle of its own footprint, so the slab reaches "
        "as far back as it does forward. §4[1] says it should extend a long way FORWARD "
        "and only slightly back — that is a statement about where the LEG stands on the "
        "foot, and the ledger puts that offset in ankle's own `soleTop` socket vector, not "
        "in the sole. It is measured on ankle's turn, from the boot cuff's fore-aft "
        "position against the sole's span in left.webp/right.webp. Until then the "
        "assembled foot will sit centred, and Stage 1B is where that would show.",
    ]

    SPEC_PATH.write_text(json.dumps(spec, indent=2) + "\n")
    CONSTANTS_PATH.write_text(json.dumps({
        "schema": "ff7-cloud-strife-build-constants/1",
        "generatedBy": "spec/author_spec.py",
        "why": "prompt §0.6 — a figure the spec quotes must have a producer. Measured values "
               "live in landmarks.json / facet-gate.json / palette.json; this file holds the "
               "two other classes so audit_records.py can source them and a reader can tell "
               "which is which.",
        "derived": DERIVED,
        "authored": AUTHORED,
        "socketChainY": {k: round(v, 6) for k, v in Y.items()},
        "unitPxFront": UNIT_PX,
        "triangleBudgetTotal": sum(c["triangleBudget"] for c in comps),
        # Every box, position, socket offset and budget the spec quotes, at the same
        # precision it quotes them. This is what makes the componentTree auditable: the
        # numbers in it are this script's output, not hand-typed, and audit_records.py
        # sources them from here.
        "componentGeometry": [
            {
                "id": c["id"],
                "dimensions": c["dimensions"],
                "position": c["transform"]["position"],
                "sockets": c["actionProfile"]["sockets"],
                "attachment": {k: v for k, v in (c["attachment"] or {}).items()
                               if isinstance(v, (int, float, list))},
                "triangleBudget": c["triangleBudget"],
            }
            for c in comps
        ],
    }, indent=2) + "\n")
    print(f"wrote {SPEC_PATH.name} and {CONSTANTS_PATH.name}")
    print(f"components={len(comps)} (1 root + {len(GROUPS)} groups + {len(PARTS)} parts)")
    print(f"stage1={len(STAGE1)} stage2={len(STAGE2)} stage3={len(STAGE3)} "
          f"materials={len(MATERIALS)} triangleBudget={sum(c['triangleBudget'] for c in comps)}")


if __name__ == "__main__":
    main()
