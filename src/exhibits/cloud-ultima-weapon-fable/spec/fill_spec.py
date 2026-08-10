#!/usr/bin/env python3
"""Author the full ObjectSculptSpec from measurements.json + the brief's 47-node contract.

Coordinate frame (brief): +Y handle->tip, -Y pommel, +X weapon right, +Z visible front,
origin at the guard/handle junction. Scale: 100 reference px = 1.0 world unit; distances
along the blade axis corrected by 1/cos(tilt). Model is built axis-vertical; the
reference-matched review camera applies the measured roll.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "object-sculpt-spec.json"
M = json.load(open(HERE / "measurements.json"))

TILT = M["bladeAxis"]["tiltDegFromVertical"]          # 17.67
COS_T = math.cos(math.radians(TILT))
AX_A = M["bladeAxis"]["xAtY0"]
AX_B = M["bladeAxis"]["slopeDxPerDy"]
ORIGIN_Y = 245.0  # image row of the guard/handle junction (hub bottom / grip top)


def axis_x(y):
    return AX_A + AX_B * y


def Y(y_img):
    """Image row -> local Y (units), measured along the blade axis."""
    return round((ORIGIN_Y - y_img) / COS_T / 100.0, 3)


def X(x_img, y_img):
    """Image (x,y) -> local X (units), perpendicular distance from the axis."""
    return round((x_img - axis_x(y_img)) * COS_T / 100.0, 3)


# ---- derived landmarks (all traceable to measurements.json) ----
Y_TIP = 2.82            # inferred beyond frame (taper continuation), conf 0.5
Y_FRAME_TOP = Y(0)      # 2.571 visible blade cut
Y_CORE_APEX = Y(M["core"]["topApexY"])       # 1.847
Y_NOTCH = Y(M["core"]["notchTopY"])          # 0.609
Y_CORE_BOT = Y(M["core"]["bottomY"])         # 0.231
Y_BLADE_BASE = 0.33
Y_RADIATION = Y(256)    # -0.115 rod-axis convergence (measured mean y=252..258)

# leaf half-width stations [localY, halfWidth] from the symmetric measured profile
LEAF = [[Y(s["y"]), round((abs(s["left"]) + s["right"]) / 2 / 100.0, 3)]
        for s in M["leafWidthProfile"] if s["y"] <= 195]
LEAF = [[Y_TIP, 0.0]] + [[round(y, 3), w] for y, w in LEAF if y >= Y_BLADE_BASE - 0.01]
CORE = [[Y(s["y"]), round((abs(s["left"]) + max(s["right"], 0)) / 2 / 100.0, 3)]
        for s in M["core"]["profile"] if s["y"] <= 209]

CORE_STOPS = M["core"]["gradientStopsTopToBottom"]  # dark(top) -> bright(bottom)

SHELL_D = 0.06   # total blade thickness (thin sliver evidence; no side view) conf 0.5
CORE_D = 0.036
ROD_FAN = [  # [id, side, localAngleDeg from +X CCW, confidence, evidenceType, note]
    ["rightEmitterUpper", "right", 40.8, 0.85, "visible", "measured image -58.46deg -> local +40.8deg"],
    ["rightEmitterMiddle", "right", 23.3, 0.85, "visible", "measured image -40.9deg -> local +23.3deg"],
    ["rightEmitterLower", "right", 5.8, 0.45, "inferred", "occluded by right shoulder; fan-step (17.5deg) continuation"],
    ["leftEmitterUpper", "left", 185.8, 0.6, "visible", "visible but unmeasured (components merged); C2 of rightLower"],
    ["leftEmitterMiddle", "left", 203.3, 0.7, "visible", "C2 of rightMiddle; matches observed down-left ~41deg image angle"],
    ["leftEmitterLower", "left", 220.8, 0.7, "visible", "C2 of rightUpper; matches observed down-left ~57deg image angle"],
]

def gd(intent, uv="generated procedural coordinates", normals="flat facet normals (PS1 look: computeVertexNormals then flatShading)"):
    return {
        "topologyIntent": intent,
        "edgeTreatment": {"type": "none", "bevelRadius": 0.0, "segments": 1},
        "deformationStack": [],
        "uvStrategy": uv,
        "normalStrategy": normals,
    }


def pivot(pos, axis=(0, 1, 0)):
    return {"mode": "custom", "localPosition": list(pos), "axis": list(axis), "confidence": 0.8}


def channels(detach=True):
    return {"translate": True, "rotate": True, "scale": True, "bend": False,
            "twist": False, "detach": detach, "visibility": True, "materialState": True}


def collider(kind, offset, scale):
    return {"type": kind, "offset": list(offset), "scale": list(scale), "isTrigger": False, "notes": ""}


def destruction(group):
    return {"breakable": False, "fractureGroup": group, "seamRefs": [], "detachableFragments": [],
            "breakImpulse": 0.0, "debrisMaterial": "base"}


def comp(id, name, level, parent, primitive, topo, why, material, pos, dims, *,
         role="body", conf=0.8, ev=("full-object",), evtype="visible", attach=None,
         sockets=None, explode=(0, 0, 0), features=None, rot=(0, 0, 0), importance=0.8,
         intent=None, notes=""):
    w, h, d = dims
    return {
        "id": id, "name": name, "level": level, "role": role,
        "importance": importance, "confidence": conf,
        "primitive": primitive, "topologyClass": topo, "topologyRationale": why,
        "geometryDescriptor": gd(intent or f"{primitive} for {name}"),
        "parent": parent,
        "attachment": attach,
        "dimensions": {"width": w, "height": h, "depth": d, "units": "world (100 ref px = 1u)", "confidence": conf},
        "transform": {"position": list(pos), "rotation": list(rot), "scale": [1, 1, 1]},
        "actionProfile": {
            "animationRole": role if role != "body" else "static-detail",
            "pivot": pivot(pos if parent else (0, 0, 0)),
            "transformChannels": channels(detach=parent is not None),
            "sockets": sockets or [],
            "collider": collider("box", (0, 0, 0), [max(w, 0.02), max(h, 0.02), max(d, 0.02)]),
            "constraints": [],
            "destruction": destruction(id.split("-")[0] if parent else "root"),
        },
        "material": material,
        "materialLayers": [material],
        "deformations": [], "joints": [], "seams": [],
        "localFeatures": features or [],
        "surfaceDetail": {
            "macroRoughness": 0.0, "microRoughness": 0.0, "bumpAmplitude": 0.0,
            "normalPattern": "flat facets", "displacementPattern": "", "occlusionPattern": "",
            "edgeWearPattern": "", "notes": notes or "PS1 flat-shaded facet language: no microtexture by design.",
        },
        "evidenceRefs": list(ev),
        "details": [],
        "fidelityTier": "blockout",
        "evidenceType": evtype,
        "explodeVector": list(explode),
    }


def att(socket, contact, start, end, embed=0.0, overlap=0.0, gap=0.004):
    a = {"parentSocket": socket, "contactType": contact,
         "localStart": list(start), "localEnd": list(end), "gapTolerance": gap}
    if embed:
        a["embedDepth"] = embed
    if overlap:
        a["overlap"] = overlap
    return a


C = []
# ---- root + assemblies ----
C.append(comp("root", "cloud-ultima-weapon", "macro", None, "group", "assembled-solid",
              "Container group: compound hard-surface weapon per brief hierarchy.", "none",
              (0, 0, 0), (1.2, 4.2, 0.3), role="root", conf=0.9, importance=1.0,
              sockets=[{"id": "guardSocket", "localPosition": [0, 0.15, 0]},
                       {"id": "bladeSocket", "localPosition": [0, Y_BLADE_BASE, 0]},
                       {"id": "handleSocket", "localPosition": [0, -0.05, 0]},
                       {"id": "pommelSocket", "localPosition": [0, -0.55, 0]},
                       {"id": "leftEmitterSocket", "localPosition": [-0.12, Y_RADIATION, 0]},
                       {"id": "rightEmitterSocket", "localPosition": [0.12, Y_RADIATION, 0]}],
              intent="pivot-only group; origin at guard/handle junction"))
C.append(comp("bladeAssembly", "bladeAssembly", "macro", "root", "group", "assembled-solid",
              "Blade macro assembly (shell + core + spine + mount).", "none",
              (0, 0, 0), (0.62, 2.6, SHELL_D), conf=0.9, importance=1.0,
              attach=att("bladeSocket", "socket", (0, Y_BLADE_BASE, 0), (0, Y_TIP, 0), embed=0.06),
              explode=(0, 0.55, 0)))
C.append(comp("guardAssembly", "guardAssembly", "macro", "root", "group", "assembled-solid",
              "Guard macro assembly (hub, shoulders, rods, gold, olive).", "none",
              (0, 0, 0), (1.2, 0.75, 0.22), conf=0.85, importance=1.0,
              attach=att("guardSocket", "overlap", (0, 0.3, 0), (0, -0.35, 0), overlap=0.05),
              explode=(0, 0, 0)))
C.append(comp("handleAssembly", "handleAssembly", "macro", "root", "group", "assembled-solid",
              "Handle macro assembly along -Y; grip lower half + pommel are frame-cropped inferences.",
              "none", (0, 0, 0), (0.12, 0.75, 0.12), conf=0.6, evtype="visible",
              attach=att("handleSocket", "socket", (0, -0.02, 0), (0, -0.72, 0), embed=0.05),
              explode=(0, -0.5, 0)))

# ---- blade: outer shell ----
leaf_note = f"leaf half-width stations (localY, halfW): {LEAF}"
C.append(comp("outerBladeShell", "outerBladeShell", "meso", "bladeAssembly", "extrude", "continuous-sculpt",
              "Single faceted leaf volume (knife-blade worked example): custom polygon profile, shallow extrude — never a box/capsule.",
              "outerBladeShellMaterial", (0, 0, 0), (0.59, Y_TIP - Y_BLADE_BASE, SHELL_D),
              conf=0.85, importance=1.0, ev=("full-object", "zone-r0c0", "zone-r1c0", "detail:shell-facet-bands"),
              attach=att("bladeSocket", "socket", (0, Y_BLADE_BASE, 0), (0, Y_TIP, 0), embed=0.06),
              explode=(0, 0.3, 0),
              features=[{"id": "leafProfileStations", "kind": "profile-data", "data": LEAF,
                         "note": "measured symmetric profile: max |L-R| < 1.5px over y in [0,195]"}],
              intent="extruded custom leaf polygon; symmetric per measurement (leafWidthProfile)",
              notes=leaf_note))
C.append(comp("outerShellFront", "outerShellFront", "micro", "outerBladeShell", "extrude", "conforming-shell",
              "Front face plate of the leaf extrude, independently addressable per brief.",
              "outerBladeShellMaterial", (0, 0, SHELL_D / 2 - 0.005), (0.59, 2.49, 0.01),
              conf=0.85, attach=att("bladeSocket", "flush-with", (0, Y_BLADE_BASE, 0.025), (0, Y_TIP, 0.025)),
              explode=(0, 0, 0.45)))
C.append(comp("outerShellBack", "outerShellBack", "micro", "outerBladeShell", "extrude", "conforming-shell",
              "Back face plate; hidden in reference — mirrored from front.", "outerBladeShellMaterial",
              (0, 0, -SHELL_D / 2 + 0.005), (0.59, 2.49, 0.01), conf=0.6, evtype="mirrored",
              attach=att("bladeSocket", "flush-with", (0, Y_BLADE_BASE, -0.025), (0, Y_TIP, -0.025)),
              explode=(0, 0, -0.45)))
C.append(comp("outerShellLeftEdge", "outerShellLeftEdge", "micro", "outerBladeShell", "extrude", "conforming-shell",
              "Left long edge band closing the extrude; carries the darkest facet band.",
              "outerBladeShellMaterial", (-0.27, 1.35, 0), (0.05, 2.4, SHELL_D), conf=0.8,
              ev=("zone-r1c0", "detail:shell-facet-bands"),
              attach=att("bladeSocket", "flush-with", (-0.27, Y_BLADE_BASE, 0), (-0.02, Y_TIP, 0)),
              explode=(-0.25, 0, 0)))
C.append(comp("outerShellRightEdge", "outerShellRightEdge", "micro", "outerBladeShell", "extrude", "conforming-shell",
              "Right long edge band closing the extrude.", "outerBladeShellMaterial",
              (0.27, 1.35, 0), (0.05, 2.4, SHELL_D), conf=0.8,
              attach=att("bladeSocket", "flush-with", (0.27, Y_BLADE_BASE, 0), (0.02, Y_TIP, 0)),
              explode=(0.25, 0, 0)))
C.append(comp("outerShellTip", "outerShellTip", "micro", "outerBladeShell", "extrude", "continuous-sculpt",
              "Pointed tip beyond the cropped frame: taper continuation (~0.37px/row/side) to zero at Y=2.82.",
              "outerBladeShellMaterial", (0, (Y_FRAME_TOP + Y_TIP) / 2, 0), (0.17, Y_TIP - Y_FRAME_TOP, SHELL_D),
              conf=0.5, evtype="inferred", ev=("zone-r0c0", "detail:tip-crop-inference"),
              attach=att("bladeSocket", "flush-with", (0, Y_FRAME_TOP, 0), (0, Y_TIP, 0)),
              explode=(0, 0.5, 0)))

# ---- blade: purple core ----
core_note = f"core half-width stations: {CORE}; gradient stops (top->bottom): {CORE_STOPS}"
C.append(comp("purpleEnergyCore", "purpleEnergyCore", "meso", "bladeAssembly", "extrude", "continuous-sculpt",
              "Independent faceted violet volume embedded inside the shell; apex on axis at Y=1.847, inverted-V notch from Y=0.609.",
              "purpleCoreMaterial", (0, 0, 0), (0.36, Y_CORE_APEX - Y_CORE_BOT, CORE_D),
              conf=0.9, importance=1.0, ev=("zone-r1c1", "detail:core-two-plane-split", "detail:core-notch-inverted-v"),
              attach=att("bladeSocket", "embed", (0, Y_CORE_BOT, 0), (0, Y_CORE_APEX, 0), embed=CORE_D),
              explode=(0, 0, 0.28),
              features=[{"id": "coreProfileStations", "kind": "profile-data", "data": CORE,
                         "note": "apex y69, notch top y187, legs end y223 (image px)"},
                        {"id": "coreGradient", "kind": "gradient", "data": CORE_STOPS}],
              intent="extruded violet polygon with notched lower profile", notes=core_note))
C.append(comp("purpleCoreFront", "purpleCoreFront", "micro", "purpleEnergyCore", "extrude", "conforming-shell",
              "Front plane of the core (darker band of the two-plane split).", "purpleCoreMaterial",
              (0, 0, CORE_D / 2 - 0.004), (0.36, 1.6, 0.008), conf=0.85,
              ev=("zone-r1c1", "detail:core-two-plane-split"),
              attach=att("bladeSocket", "flush-with", (0, Y_CORE_BOT, 0.014), (0, Y_CORE_APEX, 0.014)),
              explode=(0, 0, 0.18)))
C.append(comp("purpleCoreBack", "purpleCoreBack", "micro", "purpleEnergyCore", "extrude", "conforming-shell",
              "Back plane; hidden — mirrored from front.", "purpleCoreMaterial",
              (0, 0, -CORE_D / 2 + 0.004), (0.36, 1.6, 0.008), conf=0.6, evtype="mirrored",
              attach=att("bladeSocket", "flush-with", (0, Y_CORE_BOT, -0.014), (0, Y_CORE_APEX, -0.014)),
              explode=(0, 0, -0.18)))
C.append(comp("purpleCoreEdge", "purpleCoreEdge", "micro", "purpleEnergyCore", "extrude", "conforming-shell",
              "Right bevel plane: lighter value band + bright rim accent along the lower-right edge.",
              "purpleCoreMaterial", (0.17, 0.9, 0), (0.03, 1.5, CORE_D), conf=0.8,
              ev=("zone-r1c1", "detail:core-bright-rim"),
              features=[{"id": "rimAccent", "kind": "color-accent", "data": {"color": "#8A6CF8", "edge": "lower-right"}}],
              attach=att("bladeSocket", "flush-with", (0.17, Y_CORE_BOT, 0), (0.02, Y_CORE_APEX, 0)),
              explode=(0.15, 0, 0.1)))
C.append(comp("purpleCoreTip", "purpleCoreTip", "micro", "purpleEnergyCore", "extrude", "continuous-sculpt",
              "Upper taper of the core ending in an on-axis apex at Y=1.847 (x offset -0.7..0.2px).",
              "purpleCoreMaterial", (0, Y_CORE_APEX - 0.12, 0), (0.09, 0.25, CORE_D), conf=0.85,
              ev=("zone-r0c0", "zone-r1c1"),
              attach=att("bladeSocket", "flush-with", (0, Y_CORE_APEX - 0.25, 0), (0, Y_CORE_APEX, 0)),
              explode=(0, 0.22, 0.1)))

# ---- blade: magenta spine ----
C.append(comp("magentaCentralSpine", "magentaCentralSpine", "meso", "bladeAssembly", "extrude", "continuous-sculpt",
              "Thin angular spear in front of the core notch: near-black burgundy spike (Y 0.61->0.44) into brighter magenta diamond (Y 0.44->0.17); lower end occluded by hub.",
              "magentaSpineMaterial", (0.005, 0, CORE_D / 2 + 0.015), (0.14, 0.47, 0.02),
              conf=0.8, importance=0.95, ev=("zone-r2c1", "detail:spine-two-tone", "detail:spine-z-offset"),
              attach=att("bladeSocket", "overlap", (0, 0.17, 0.033), (0, Y_NOTCH, 0.033), overlap=0.02, gap=0.004),
              explode=(0, 0, 0.6),
              features=[{"id": "spineTwoTone", "kind": "gradient",
                         "data": [{"t": 0.0, "color": "#2E0A18"}, {"t": 0.45, "color": "#571031"}, {"t": 1.0, "color": "#8E2B4C"}],
                         "note": "t=0 spike top (dark), t=1 lower diamond (bright #842B4C measured); below Y=0.2 darkened by hub occlusion in reference"}]))
C.append(comp("spineFront", "spineFront", "micro", "magentaCentralSpine", "extrude", "conforming-shell",
              "Front face of the spine wedge.", "magentaSpineMaterial",
              (0, 0.39, 0.008), (0.14, 0.44, 0.008), conf=0.8,
              attach=att("bladeSocket", "flush-with", (0, 0.17, 0.04), (0, Y_NOTCH, 0.04)),
              explode=(0, 0, 0.15)))
C.append(comp("spineBack", "spineBack", "micro", "magentaCentralSpine", "extrude", "conforming-shell",
              "Back face of the spine wedge; hidden — mirrored.", "magentaSpineMaterial",
              (0, 0.39, -0.008), (0.14, 0.44, 0.008), conf=0.55, evtype="mirrored",
              attach=att("bladeSocket", "flush-with", (0, 0.17, 0.026), (0, Y_NOTCH, 0.026)),
              explode=(0, 0, 0.08)))
C.append(comp("spineBaseSocket", "spineBaseSocket", "micro", "magentaCentralSpine", "box", "assembled-solid",
              "Small berth where the spine's diamond seats into the hub (occluded joint).", "magentaSpineMaterial",
              (0, 0.17, 0.02), (0.09, 0.07, 0.02), conf=0.5, evtype="inferred",
              attach=att("guardSocket", "socket", (0, 0.2, 0.02), (0, 0.13, 0.02), embed=0.03),
              explode=(0, -0.05, 0.3)))

# ---- blade: mount ----
C.append(comp("bladeMount", "bladeMount", "meso", "bladeAssembly", "group", "assembled-solid",
              "Mount hardware at the blade base bridging shell and hub.", "none",
              (0, 0.31, 0), (1.05, 0.14, 0.1), conf=0.6,
              attach=att("bladeSocket", "overlap", (0, 0.36, 0), (0, 0.26, 0), overlap=0.04),
              explode=(0, 0.12, 0)))
C.append(comp("upperBladeCollar", "upperBladeCollar", "micro", "bladeMount", "box", "assembled-solid",
              "Collar band clamping the shell base above the hub.", "gunmetalGuardMaterial",
              (0, 0.33, 0), (0.5, 0.07, 0.09), conf=0.55, evtype="inferred",
              attach=att("bladeSocket", "overlap", (0, 0.36, 0), (0, 0.3, 0), overlap=0.03),
              explode=(0, 0.18, 0)))
C.append(comp("rightBladeClamp", "rightBladeClamp", "micro", "bladeMount", "extrude", "assembled-solid",
              "Visible right base wing: shell flare measured to +0.45..+0.54u at y=200-205 — modeled as an angular clamp wing.",
              "outerBladeShellMaterial", (0.4, 0.32, 0), (0.28, 0.12, 0.05), conf=0.75,
              ev=("zone-r2c2", "detail:shell-base-taper"),
              attach=att("bladeSocket", "overlap", (0.28, 0.34, 0), (0.53, 0.28, 0), overlap=0.03),
              explode=(0.3, 0, 0.1)))
C.append(comp("leftBladeClamp", "leftBladeClamp", "micro", "bladeMount", "extrude", "assembled-solid",
              "EVIDENCE CONFLICT: no left counterpart of the right wing is visible (background at mirrored region). Brief requires the node; modeled as a small clamp block, NOT a mirrored wing.",
              "outerBladeShellMaterial", (-0.31, 0.32, 0), (0.12, 0.1, 0.05), conf=0.4, evtype="inferred",
              ev=("zone-r2c1", "detail:shell-base-taper"),
              attach=att("bladeSocket", "overlap", (-0.26, 0.34, 0), (-0.37, 0.29, 0), overlap=0.03),
              explode=(-0.3, 0, 0.1)))

# ---- guard ----
C.append(comp("centralGuardHub", "centralGuardHub", "meso", "guardAssembly", "extrude", "assembled-solid",
              "Olive-gold faceted arrowhead/collar under the blade base (x70-85, y219-245) with dark inner facets.",
              "agedGoldMaterial", (0, 0.13, 0), (0.24, 0.28, 0.12), conf=0.8, importance=0.95,
              ev=("zone-r2c1", "detail:hub-arrowhead"),
              attach=att("guardSocket", "socket", (0, 0.27, 0), (0, -0.01, 0), embed=0.02),
              explode=(0, 0, -0.15)))
C.append(comp("leftGunmetalShoulder", "leftGunmetalShoulder", "meso", "guardAssembly", "extrude", "assembled-solid",
              "Left folded gunmetal plate (x55-75, y230-270), angled outward-downward, visible facet split.",
              "gunmetalGuardMaterial", (-0.24, -0.07, 0), (0.22, 0.4, 0.1), conf=0.8,
              ev=("zone-r2c1", "detail:shoulder-folded-plate"),
              attach=att("guardSocket", "flush-with", (-0.12, 0.08, 0), (-0.36, -0.24, 0), overlap=0.03),
              explode=(-0.4, 0, 0), rot=(0, 0, 0.42)))
C.append(comp("rightGunmetalShoulder", "rightGunmetalShoulder", "meso", "guardAssembly", "extrude", "assembled-solid",
              "Right folded gunmetal plate (x100-125, y225-265), mirror of left at macro level.",
              "gunmetalGuardMaterial", (0.24, -0.07, 0), (0.22, 0.4, 0.1), conf=0.8,
              ev=("zone-r2c2", "detail:shoulder-folded-plate"),
              attach=att("guardSocket", "flush-with", (0.12, 0.08, 0), (0.36, -0.24, 0), overlap=0.03),
              explode=(0.4, 0, 0), rot=(0, 0, -0.42)))
C.append(comp("emitterRods", "emitterRods", "meso", "guardAssembly", "group", "assembled-solid",
              "Radial rod fan. MEASURED: C2 point-symmetric pinwheel (right rods tipward, left rods pommel-ward), all axes through (0, -0.115); brief's naive mirror reading contradicted by evidence — recorded, not silently resolved.",
              "none", (0, Y_RADIATION, 0), (1.2, 0.7, 0.1), conf=0.8, importance=0.95,
              ev=("zone-r2c0", "zone-r2c2", "detail:rod-fan-angles"),
              attach=att("guardSocket", "socket", (0, 0, 0), (0, Y_RADIATION, 0), embed=0.05),
              explode=(0, 0, 0)))
for rid, side, ang, conf_, evt, note in ROD_FAN:
    a = math.radians(ang)
    dir_x, dir_y = math.cos(a), math.sin(a)
    r0, r1 = 0.13, 0.45
    cx, cy = dir_x * (r0 + r1) / 2, Y_RADIATION + dir_y * (r0 + r1) / 2
    sock = "leftEmitterSocket" if side == "left" else "rightEmitterSocket"
    C.append(comp(rid, rid, "micro", "emitterRods", "cylinder", "fiber-strand",
                  f"Thin faceted rod (6-sided, ~0.085u thick, len ~0.31u): {note}",
                  "crimsonEmitterMaterial", (round(cx, 3), round(cy, 3), 0), (0.085, r1 - r0, 0.085),
                  conf=conf_, evtype=evt, ev=("zone-r2c0" if side == "left" else "zone-r2c2", "detail:rod-fan-angles", "detail:rod-two-tone-facets"),
                  attach=att(sock, "socket",
                             (round(dir_x * r0, 3), round(Y_RADIATION + dir_y * r0, 3), 0),
                             (round(dir_x * r1, 3), round(Y_RADIATION + dir_y * r1, 3), 0), embed=0.04),
                  explode=(round(dir_x * 0.45, 3), round(dir_y * 0.45, 3), 0),
                  rot=(0, 0, round(a - math.pi / 2, 4)),
                  intent="low-segment faceted cylinder from localStart to localEnd"))
C.append(comp("goldGuardParts", "goldGuardParts", "meso", "guardAssembly", "group", "assembled-solid",
              "Gold collar + lower fins group.", "none", (0, 0.0, 0), (0.4, 0.5, 0.14), conf=0.6,
              attach=att("guardSocket", "flush-with", (0, 0.1, 0), (0, -0.3, 0), overlap=0.02),
              explode=(0, -0.1, 0)))
C.append(comp("goldCenterCollarFront", "goldCenterCollarFront", "micro", "goldGuardParts", "extrude", "assembled-solid",
              "Front gold collar plate on the hub.", "agedGoldMaterial",
              (0, 0.08, 0.07), (0.2, 0.14, 0.03), conf=0.6, ev=("zone-r2c1", "detail:hub-arrowhead"),
              attach=att("guardSocket", "flush-with", (0, 0.12, 0.06), (0, 0.02, 0.06), overlap=0.02),
              explode=(0, 0, 0.3)))
C.append(comp("goldCenterCollarBack", "goldCenterCollarBack", "micro", "goldGuardParts", "extrude", "assembled-solid",
              "Back gold collar plate; hidden — mirrored.", "agedGoldMaterial",
              (0, 0.08, -0.07), (0.2, 0.14, 0.03), conf=0.45, evtype="mirrored",
              attach=att("guardSocket", "flush-with", (0, 0.12, -0.06), (0, 0.02, -0.06), overlap=0.02),
              explode=(0, 0, -0.3)))
C.append(comp("goldLowerFinLeft", "goldLowerFinLeft", "micro", "goldGuardParts", "extrude", "assembled-solid",
              "Small gold wedge below-left of the hub flanking the handle.", "agedGoldMaterial",
              (-0.11, -0.16, 0), (0.1, 0.14, 0.06), conf=0.55, ev=("zone-r2c1",),
              attach=att("guardSocket", "flush-with", (-0.06, -0.08, 0), (-0.15, -0.22, 0), overlap=0.02),
              explode=(-0.18, -0.12, 0)))
C.append(comp("goldLowerFinRight", "goldLowerFinRight", "micro", "goldGuardParts", "extrude", "assembled-solid",
              "Small gold wedge below-right of the hub flanking the handle.", "agedGoldMaterial",
              (0.11, -0.16, 0), (0.1, 0.14, 0.06), conf=0.55, ev=("zone-r2c1",),
              attach=att("guardSocket", "flush-with", (0.06, -0.08, 0), (0.15, -0.22, 0), overlap=0.02),
              explode=(0.18, -0.12, 0)))
C.append(comp("lowerGuardBlocks", "lowerGuardBlocks", "meso", "guardAssembly", "group", "assembled-solid",
              "Olive stabilizer blocks capping the shoulder tips.", "none",
              (0, -0.25, 0), (1.05, 0.35, 0.12), conf=0.75,
              attach=att("guardSocket", "flush-with", (0, -0.1, 0), (0, -0.4, 0), overlap=0.02),
              explode=(0, -0.2, 0)))
C.append(comp("oliveBlockLeft", "oliveBlockLeft", "micro", "lowerGuardBlocks", "extrude", "assembled-solid",
              "Left khaki/olive two-tone pyramid at the left shoulder tip (x28-52, y245-278).",
              "agedGoldMaterial", (X(40, 261), Y(261), 0), (0.24, 0.33, 0.1), conf=0.8,
              ev=("zone-r2c1", "detail:olive-block-two-tone"),
              attach=att("guardSocket", "butt", (X(52, 248), Y(248), 0), (X(30, 274), Y(274), 0), overlap=0.025),
              explode=(-0.35, -0.25, 0)))
C.append(comp("oliveBlockRight", "oliveBlockRight", "micro", "lowerGuardBlocks", "extrude", "assembled-solid",
              "Right olive folded cone/wedge, larger than left (x105-133, y250-285).",
              "agedGoldMaterial", (X(118, 267), Y(267), 0), (0.3, 0.36, 0.12), conf=0.8,
              ev=("zone-r2c2", "detail:olive-block-two-tone"),
              attach=att("guardSocket", "butt", (X(105, 252), Y(252), 0), (X(130, 282), Y(282), 0), overlap=0.025),
              explode=(0.35, -0.25, 0)))

# ---- handle ----
C.append(comp("internalTang", "internalTang", "micro", "handleAssembly", "box", "assembled-solid",
              "Hidden tang running through the hub into the grip (mechanical inference).", "gripMaterial",
              (0, 0.05, 0), (0.05, 0.5, 0.05), conf=0.4, evtype="inferred",
              attach=att("handleSocket", "embed", (0, 0.28, 0), (0, -0.2, 0), embed=0.05),
              explode=(0, -0.1, 0)))
C.append(comp("handleNeck", "handleNeck", "micro", "handleAssembly", "cylinder", "assembled-solid",
              "Short 8-sided neck between hub bottom and grip.", "gripMaterial",
              (0, -0.05, 0), (0.08, 0.09, 0.08), conf=0.7, ev=("zone-r2c1",),
              attach=att("handleSocket", "butt", (0, -0.01, 0), (0, -0.1, 0), gap=0.003),
              explode=(0, -0.22, 0)))
C.append(comp("blackGripCore", "blackGripCore", "micro", "handleAssembly", "cylinder", "assembled-solid",
              "Long 8-sided black grip (thickness 8.6px -> r=0.043); visible to frame bottom Y=-0.49, continues inferred to -0.52.",
              "gripMaterial", (0, -0.3, 0), (0.086, 0.42, 0.086), conf=0.75,
              ev=("zone-r2c1", "zone-r2c2", "detail:handle-two-plane"),
              attach=att("handleSocket", "butt", (0, -0.1, 0), (0, -0.52, 0), gap=0.003),
              explode=(0, -0.4, 0)))
C.append(comp("blackGripSleeve", "blackGripSleeve", "micro", "handleAssembly", "cylinder", "assembled-solid",
              "Slightly wider sleeve over the grip mid-section (8-sided).", "gripMaterial",
              (0, -0.32, 0), (0.1, 0.24, 0.1), conf=0.5, evtype="inferred",
              attach=att("handleSocket", "overlap", (0, -0.2, 0), (0, -0.44, 0), overlap=0.02),
              explode=(0, -0.55, 0)))
C.append(comp("pommelCollar", "pommelCollar", "micro", "handleAssembly", "cylinder", "assembled-solid",
              "Small collar below the grip; fully frame-cropped — brief-mandated inference.", "gunmetalGuardMaterial",
              (0, -0.56, 0), (0.1, 0.05, 0.1), conf=0.4, evtype="inferred",
              attach=att("pommelSocket", "butt", (0, -0.53, 0), (0, -0.585, 0), gap=0.003),
              explode=(0, -0.7, 0)))
C.append(comp("goldPommelTip", "goldPommelTip", "micro", "handleAssembly", "cone", "assembled-solid",
              "Small faceted gold pommel tip; fully frame-cropped — brief-mandated inference.", "agedGoldMaterial",
              (0, -0.63, 0), (0.09, 0.09, 0.09), conf=0.4, evtype="inferred",
              attach=att("pommelSocket", "butt", (0, -0.585, 0), (0, -0.675, 0), gap=0.003),
              explode=(0, -0.85, 0)))

# ---- schema conformance post-pass ----
# container nodes: validator only accepts mesh primitives + real material ids;
# keep them as pivot-only carriers with a representative material.
GROUP_MAT = {"root": "outerBladeShellMaterial", "bladeAssembly": "outerBladeShellMaterial",
             "guardAssembly": "gunmetalGuardMaterial", "handleAssembly": "gripMaterial",
             "outerBladeShell": "outerBladeShellMaterial", "purpleEnergyCore": "purpleCoreMaterial",
             "magentaCentralSpine": "magentaSpineMaterial", "bladeMount": "gunmetalGuardMaterial",
             "emitterRods": "crimsonEmitterMaterial", "goldGuardParts": "agedGoldMaterial",
             "lowerGuardBlocks": "agedGoldMaterial"}
for c in C:
    if c["primitive"] == "group":
        c["primitive"] = "box"
        c["geometryDescriptor"]["topologyIntent"] = "pivot-only group (no mesh emitted): " + c["geometryDescriptor"]["topologyIntent"]
    if c["material"] == "none":
        c["material"] = GROUP_MAT[c["id"]]
        c["materialLayers"] = [c["material"]]

# evidenceRefs must resolve to viewEvidence ids; keep detail linkage in localFeatures/notes.
DETAIL2ZONE = {
    "detail:shell-facet-bands": "zone-r1c0",
    "detail:core-two-plane-split": "zone-r1c1",
    "detail:core-bright-rim": "zone-r1c1",
    "detail:core-notch-inverted-v": "zone-r1c1",
    "detail:shell-contact-shadow": "zone-r1c1",
    "detail:spine-two-tone": "zone-r2c1",
    "detail:spine-z-offset": "zone-r2c1",
    "detail:hub-arrowhead": "zone-r2c1",
    "detail:shoulder-folded-plate": "zone-r2c1",
    "detail:olive-block-two-tone": "zone-r2c1",
    "detail:handle-two-plane": "zone-r2c1",
    "detail:shell-base-taper": "zone-r2c1",
    "detail:rod-fan-angles": "zone-r2c0",
    "detail:rod-two-tone-facets": "zone-r2c2",
    "detail:tip-crop-inference": "zone-r0c0",
}


def fix_refs(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "evidenceRefs" and isinstance(v, list):
                seen = []
                for r in v:
                    r2 = DETAIL2ZONE.get(r, r)
                    if r2 not in seen:
                        seen.append(r2)
                node[k] = seen
            else:
                fix_refs(v)
    elif isinstance(node, list):
        for item in node:
            fix_refs(item)


assert len(C) == 47, f"expected 47 nodes, got {len(C)}"
ids = [c["id"] for c in C]
assert len(set(ids)) == 47
by_id = {c["id"]: c for c in C}
for c in C:
    if c["parent"] is not None:
        assert c["parent"] in by_id, f"missing parent {c['parent']} for {c['id']}"


def band(i, f, amp, role):
    return {"id": i, "frequency": f, "amplitude": amp, "role": role}


def material(id, name, shader, base, palette, rough, metal, extra=None, overrides=None, notes=""):
    m = {
        "id": id, "name": name, "type": "physical" if shader == "MeshPhysicalMaterial" else "standard",
        "shaderModel": shader, "baseColor": base, "color": base,
        "albedo": {"dominant": base, "secondary": palette[1:], "samplingNotes": "median colours from measure_reference.py region masks"},
        "colorVariation": {"palette": palette, "pattern": "per-facet flat bands", "amplitude": 0.08, "heightCorrelation": 0.0},
        "textureResolution": 1024,
        "textureProjection": {"mode": "uv", "repeat": [1.0, 1.0], "anisotropy": 4,
                              "texelDensityIntent": "flat-shaded facet bands; no tiling textures"},
        "surfaceFrequencyBands": [
            band("macro", 1.0, 0.1, "facet-plane value banding (identity-defining)"),
            band("meso", 6.0, 0.02, "subtle per-facet value dither so large planes do not read as vector fills"),
            band("micro", 30.0, 0.005, "near-zero by design: PS1 flat-shaded reference has no microtexture — documented exception"),
        ],
        "roughness": {"base": rough, "variation": 0.06, "map": "none-flat-scalar",
                      "localResponse": "per-facet scalar only; NOTE three.js multiplies roughnessMap x roughness — avoid double application"},
        "metalness": {"base": metal, "variation": 0.0},
        "normal": {"pattern": "none", "strength": 0.0, "scale": 1.0, "space": "tangent"},
        "bump": {"pattern": "none", "amplitude": 0.0, "scale": 1.0},
        "displacement": {"pattern": "none", "amplitude": 0.0, "scale": 1.0, "silhouetteAffects": False},
        "ambientOcclusion": {"cavityStrength": 0.15, "contactShadowBias": 0.25, "notes": "guard cluster crevices only"},
        "wear": {"edgeWear": 0.0, "scratches": [], "chips": []},
        "dirt": {"amount": 0.0, "cavityBias": 0.0, "color": "#2F2A22"},
        "localOverrides": overrides or [],
        "shaderNotes": ["flatShading: true everywhere — facet planes ARE the surface language.",
                        "sRGB colours; gradients via vertex colors or small CanvasTexture ramps, never photos."],
        "notes": notes,
    }
    if extra:
        m.update(extra)
    return m


MATS = [
    material("outerBladeShellMaterial", "Translucent milky shell", "MeshPhysicalMaterial",
             "#EDEEF6", ["#EDEEF6", "#D6D7E2", "#C9CADF"], 0.32, 0.0,
             extra={"transmission": 0.5, "opacity": 0.45, "transparent": True, "ior": 1.25,
                    "thickness": 0.06, "depthWrite": False,
                    "transparencyOrdering": "renderOrder: outerShellBack=2, outerShellFront=4; core/spine opaque draw first; depthWrite off on shell faces"},
             overrides=[{"id": "facetBands", "mask": "left-edge facet planes", "albedo": "#C9CADF",
                         "evidenceRefs": ["detail:shell-facet-bands"]},
                        {"id": "innerDepthShadow", "mask": "band along core silhouette", "albedo": "-8% value",
                         "evidenceRefs": ["detail:shell-contact-shadow"]}],
             notes="Milky translucency, NOT clear glass: moderate transmission, visible body colour, no refraction caustics."),
    material("purpleCoreMaterial", "Violet energy core", "MeshStandardMaterial",
             "#4D2C9E", [s["color"] for s in CORE_STOPS], 0.35, 0.0,
             extra={"emissive": "#2A1878", "emissiveIntensity": 0.35},
             overrides=[{"id": "axialGradient", "mask": "vertical stops top->bottom", "albedo": json.dumps(CORE_STOPS),
                         "evidenceRefs": ["detail:core-two-plane-split"]},
                        {"id": "bevelPlaneLift", "mask": "right bevel plane", "albedo": "+8% value",
                         "evidenceRefs": ["detail:core-two-plane-split"]},
                        {"id": "rimAccent", "mask": "lower-right bevel edge", "albedo": "#8A6CF8",
                         "evidenceRefs": ["detail:core-bright-rim"]}],
             notes="Measured stops #1B1161->#743FD7 (top dark navy -> bottom bright violet); banded per facet, not smooth."),
    material("magentaSpineMaterial", "Magenta central spine", "MeshStandardMaterial",
             "#842B4C", ["#2E0A18", "#571031", "#8E2B4C"], 0.3, 0.0,
             extra={"emissive": "#3A0E20", "emissiveIntensity": 0.15},
             overrides=[{"id": "twoTone", "mask": "upper spike dark -> lower diamond bright",
                         "albedo": "stops 0:#2E0A18 0.45:#571031 1:#8E2B4C",
                         "evidenceRefs": ["detail:spine-two-tone"]}],
             notes="Measured bright zone #842B4C; upper spike so dark it fell out of the red classifier (~#2E0A18)."),
    material("gunmetalGuardMaterial", "Gunmetal guard", "MeshStandardMaterial",
             "#383844", ["#383844", "#2A2A33", "#4A4A58"], 0.5, 0.55,
             overrides=[{"id": "foldFacets", "mask": "folded plate facet split", "albedo": "-12% value on shadow facet",
                         "evidenceRefs": ["detail:shoulder-folded-plate"]}],
             notes="Restrained dark blue-grey; measured blob #31272E skewed by merged shadows — crop-observed #3B3B47 band used."),
    material("crimsonEmitterMaterial", "Crimson emitter lacquer", "MeshPhysicalMaterial",
             "#8E1827", ["#8E1827", "#26080D", "#5E1019"], 0.38, 0.1,
             extra={"clearcoat": 0.35, "clearcoatRoughness": 0.4},
             overrides=[{"id": "topFacetDark", "mask": "top faces", "albedo": "#26080D",
                         "evidenceRefs": ["detail:rod-two-tone-facets"]},
                        {"id": "endCaps", "mask": "rod end caps", "albedo": "-20% value",
                         "evidenceRefs": ["detail:rod-two-tone-facets"]}],
             notes="Two-tone facet lacquer: crimson bodies, near-black top faces, darker ends."),
    material("agedGoldMaterial", "Aged olive gold", "MeshStandardMaterial",
             "#8D8354", ["#8D8354", "#605F44", "#4B4732"], 0.55, 0.65,
             overrides=[{"id": "shadowFacets", "mask": "unlit fold facets", "albedo": "#4B4732",
                         "evidenceRefs": ["detail:olive-block-two-tone"]}],
             notes="Muted olive-leaning gold (median #605F44); rough enough to avoid jewellery read."),
    material("gripMaterial", "Near-black grip", "MeshStandardMaterial",
             "#1C1918", ["#1C1918", "#2E2E35"], 0.72, 0.08,
             overrides=[{"id": "litPlane", "mask": "front-left facet", "albedo": "#2E2E35",
                         "evidenceRefs": ["detail:handle-two-plane"]}],
             notes="8-sided faceted grip; measured median #1C1918."),
]

doc = json.load(open(SPEC_PATH))
doc["componentTree"] = C
doc["materials"] = MATS
doc["repetitionSystems"] = [{
    "id": "emitterRodFan",
    "componentRefs": [r[0] for r in ROD_FAN],
    "count": 6,
    "distribution": "radial fan, C2 point-symmetric about the blade axis (NOT left/right mirror — measured)",
    "parameters": {
        "radiationCenter": [0, Y_RADIATION, 0],
        "anglesDegFromPlusX": {r[0]: r[2] for r in ROD_FAN},
        "radialStart": 0.13, "radialEnd": 0.45, "thickness": 0.085, "sides": 6,
        "measurement": "4 measured rod axes intersect the blade axis at image y 252-258 (mean ~256)",
    },
    "evidenceRefs": ["detail:rod-fan-angles", "zone-r2c0", "zone-r2c2"],
}]
doc["silhouette"] = {
    "boundingShape": "long tapered leaf blade (visible 2.24u, inferred tip to 2.82u) over a compact radial guard cluster (1.05u wide) and thin grip",
    "aspectRatios": ["visible blade length : max blade width = 2.24 : 0.59 (3.8:1)",
                     "guard cluster width : blade width = 1.05 : 0.59"],
    "symmetry": "blade bilateral about measured axis (|L-R| < 1.5px over y 0-195); rod fan C2 point-symmetric; base flare right-only",
    "dominantCurves": ["leaf edges: monotonic taper base->tip (0.295 -> 0.085 half-width at frame top)",
                       "inverted-V core notch (apex y187)", "radial rod fan through (0,-0.115)"],
    "negativeSpaces": ["notch between core legs", "gaps between rods", "waist between guard and grip"],
    "landmarks": [
        {"id": "axis", "imagePx": "x = 12.78 + 0.3185*y", "note": "tilt 17.67deg from vertical, fit R2 0.9994"},
        {"id": "coreApex", "imagePx": [69], "localY": Y_CORE_APEX},
        {"id": "notchTop", "imagePx": [187], "localY": Y_NOTCH},
        {"id": "bladeBase", "imagePx": [212], "localY": Y_BLADE_BASE},
        {"id": "radiationCenter", "imagePx": [256], "localY": Y_RADIATION},
        {"id": "frameBottom", "imagePx": [292], "localY": Y(292)},
    ],
}
doc["referenceCamera"] = {
    "solved": False,
    "fovDegrees": 25.0, "aspect": 0.5,
    "orientation": {"yaw": 0.0, "pitch": 0.0, "roll": -TILT},
    "positionHint": [0.0, 1.05, 6.5],
    "note": "Near-orthographic frontal view; model axis-vertical, camera rolled -17.67deg reproduces the reference framing. Confirm by overlay at blockout; set solved=true after IoU gate.",
}
doc["coordinateFrame"] = {
    "front": "+Z (visible face in reference)",
    "up": "+Y handle->tip along measured blade axis",
    "right": "+X weapon right",
    "origin": "guard/handle junction (image y=245 on axis)",
    "scaleReference": "100 reference px = 1.0 world unit; axis distances corrected by 1/cos(17.67deg)",
}
doc["assumptions"] = [
    "Tip extends to Y=2.82 by taper continuation (frame-cropped), confidence 0.5.",
    "Pommel region (collar + gold tip) below Y=-0.52 per brief, frame-cropped, confidence 0.4.",
    "Back faces mirror front faces (single view), evidenceType=mirrored.",
    "Blade total thickness 0.06u (no side view), confidence 0.5.",
    "Rod fan is C2 point-symmetric per measurement; brief's 'mirrored rods' phrasing recorded as an evidence conflict, not silently resolved.",
    "Left blade clamp exists as a small block (brief-mandated node) though no left wing is visible — right wing is NOT mirrored.",
]
doc["risks"] = [
    "Transparency ordering: core must stay readable through the shell from front/back/three-quarter; deliberate renderOrder + depthWrite plan in outerBladeShellMaterial.",
    "Tone mapping can desaturate the violet core; verify saturation at lighting pass.",
    "three.js roughnessMap multiplies the roughness scalar — keep flat scalars, no redundant maps.",
    "Thin blade fails degenerate side-view checks by nature; do not add fake thickness to pass a gate.",
    "47 small meshes: draw call budget matters more than triangles; consider merged static groups only at optimization pass.",
]
doc["scores"] = {
    "object_isolation": 3, "silhouette_readability": 3, "depth_inference": 2,
    "primitive_decomposition": 3, "material_procedurality": 3, "occlusion_risk": 1,
    "interaction_fit": 3,
}
doc["performanceBudget"] = {
    "qualityPriority": "reference-fidelity",
    "targetTriangles": 20000, "maxDrawCalls": 70, "textureSize": 512, "fpsTarget": 60,
    "optimizationPolicy": "Low-poly by identity; keep 47 selectable nodes, optimize only draw calls/material sharing at optimization pass.",
}
doc["lightingFromPhoto"] = [
    {"role": "key", "type": "directional", "direction": [0.35, 0.5, 0.85], "color": "#FFFFFF",
     "intensity": 1.1,
     "evidence": "core right bevel plane lighter than front plane; bright rim on lower-right bevel edge; shell left-edge bands darkest — key from front-upper-right"},
    {"role": "fill", "type": "hemisphere", "skyColor": "#E8E8F0", "groundColor": "#B8B8C4",
     "intensity": 0.5,
     "note": "flat-shaded source is near-uniform; hemisphere fill keeps facet value steps readable without crushing shadows"},
    {"role": "environment", "type": "ambient", "color": "#9A9AA8", "intensity": 0.25,
     "note": "no rim light in the reference (flat asset); low ambient instead of a fake rim"},
    {"role": "rendering", "exposure": 1.0,
     "toneMapping": "LinearToneMapping (no ACES filmic: it desaturates the violet core — recorded risk)",
     "background": "#FFFFFF like the reference",
     "contactShadow": "none in the reference (floating asset render); review renders keep contact shadow off, viewer page may add a soft AO disc"},
]
doc["featureReviewTargets"] = [
    {"id": "leaf-silhouette-axis", "name": "Leaf silhouette + axis/proportions", "tier": "critical",
     "passIds": ["blockout", "form-refinement"], "minimumScore": 0.8, "mustPass": True,
     "componentRefs": ["outerBladeShell", "outerShellTip"], "evidenceRefs": ["full-object"]},
    {"id": "core-placement-notch", "name": "Core placement + inverted-V notch + spine", "tier": "critical",
     "passIds": ["blockout", "structural-pass", "form-refinement"], "minimumScore": 0.8, "mustPass": True,
     "componentRefs": ["purpleEnergyCore", "magentaCentralSpine"],
     "evidenceRefs": ["detail:core-notch-inverted-v", "detail:spine-two-tone"]},
    {"id": "rod-fan-layout", "name": "Emitter rod fan layout (C2 pinwheel)", "tier": "critical",
     "passIds": ["structural-pass", "form-refinement"], "minimumScore": 0.8, "mustPass": True,
     "componentRefs": ["emitterRods"], "evidenceRefs": ["detail:rod-fan-angles"]},
    {"id": "guard-cluster-massing", "name": "Guard cluster massing (hub/shoulders/olive/fins)", "tier": "important",
     "passIds": ["blockout", "structural-pass"], "minimumScore": 0.7, "mustPass": False,
     "componentRefs": ["centralGuardHub", "leftGunmetalShoulder", "rightGunmetalShoulder", "oliveBlockLeft", "oliveBlockRight"],
     "evidenceRefs": ["detail:hub-arrowhead", "detail:shoulder-folded-plate", "detail:olive-block-two-tone"]},
    {"id": "core-through-shell", "name": "Core readable through translucent shell", "tier": "critical",
     "passIds": ["material-pass", "surface-pass", "lighting-pass"], "minimumScore": 0.8, "mustPass": True,
     "componentRefs": ["outerBladeShell", "purpleEnergyCore"], "evidenceRefs": ["detail:shell-contact-shadow"]},
    {"id": "facet-shading-language", "name": "PS1 facet shading language", "tier": "important",
     "passIds": ["material-pass", "lighting-pass"], "minimumScore": 0.7, "mustPass": False,
     "componentRefs": ["root"], "evidenceRefs": ["detail:shell-facet-bands", "detail:handle-two-plane"]},
    {"id": "material-zone-separation", "name": "Seven material zones stay distinct", "tier": "critical",
     "passIds": ["material-pass", "lighting-pass"], "minimumScore": 0.75, "mustPass": True,
     "componentRefs": ["root"], "evidenceRefs": ["full-object"]},
    {"id": "explode-runtime", "name": "Explode/isolate runtime + sockets", "tier": "critical",
     "passIds": ["interaction-pass"], "minimumScore": 0.8, "mustPass": True,
     "componentRefs": ["root"], "evidenceRefs": ["full-object"]},
]
zone_obs = {
    "r0c0": "shell left half + core apex wedge entering bottom-right; soft facet band on left edge",
    "r0c1": "shell right edge diagonal; background upper-right",
    "r0c2": "background only",
    "r1c0": "shell left edge band with 2-3 value steps; core left edge navy->violet",
    "r1c1": "core two-plane split, bright rim, notch onset at bottom; shell contact shadow along core right edge",
    "r1c2": "shell right edge; background",
    "r2c0": "three crimson rods pointing down-left (image); flat dark tone, square-cut ends",
    "r2c1": "guard core: olive hub, left gunmetal shoulder, left olive block, spine bright zone, grip start, rod roots",
    "r2c2": "two crimson rods up-right, right shoulder, large right olive block, shell base corner, grip continuing",
}
doc["viewEvidence"] = [doc["viewEvidence"][0] | {"observations": [
    "single frontal three-quarter view, blade tilted 17.67deg, tip and grip frame-cropped",
    "flat-shaded PS1 asset on white background; facet value steps are the only shading",
], "confidence": 0.9}] + [
    {"id": f"zone-{k}", "view": "primary",
     "imageRegion": {"x": (int(k[3]) * 48.67) / 146, "y": (int(k[1]) * 97.33) / 292,
                     "width": 48.67 / 146, "height": 97.33 / 292, "units": "normalized"},
     "observations": [v], "confidence": 0.85}
    for k, v in zone_obs.items()
]
for p in doc["buildPasses"]:
    if p["id"] == "blockout":
        p["componentRefs"] = ["root", "bladeAssembly", "outerBladeShell", "purpleEnergyCore",
                              "magentaCentralSpine", "guardAssembly", "handleAssembly"]
        p["acceptance"] += [
            "Outer silhouette matches reference (IoU gate at reference-matched view).",
            "Blade-to-handle length ratio and guard width match pixel measurements.",
            "Purple core placement matches (apex Y=1.847, notch Y=0.609).",
            "Weapon reads correctly as a small thumbnail.",
        ]
    elif p["id"] == "structural-pass":
        p["componentRefs"] = [c["id"] for c in C]
        p["acceptance"] += [
            "Every one of the 47 atomic components exists; no major part fused into an unrelated part.",
            "All attachments touch correctly; mirrored and inferred parts recorded with confidence + evidenceType.",
        ]
    elif p["id"] == "material-pass":
        p["acceptance"] += [
            "Purple core remains visible through the pale shell (front/back/three-quarter).",
            "Shell neither fully invisible nor clear household glass.",
            "Gold, gunmetal, crimson and black regions remain distinct; tone mapping preserves violet.",
        ]
    else:
        p["componentRefs"] = ["root"]

# colorMaterialRecipe (strict gate): structured evidence-linked colour per component
def rgba(hexstr, a=1.0):
    h = hexstr.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {a})"


def stops_rgba(stops):
    return [{"offset": s["t"], "color": rgba(s["color"])} for s in stops]


RECIPES = {
    "outerBladeShellMaterial": {"dominantAlbedo": rgba("#EDEEF6", 0.45), "secondaryAlbedo": rgba("#C9CADF", 0.45),
                                "materialClass": "glass", "materialClassConfidence": 0.7},
    "purpleCoreMaterial": {"dominantAlbedo": rgba("#4D2C9E"), "secondaryAlbedo": rgba("#1B1161"),
                           "materialClass": "plastic", "materialClassConfidence": 0.6,
                           "colorGradient": {"type": "linear", "axis": "y",
                                             "stops": stops_rgba(CORE_STOPS)}},
    "magentaSpineMaterial": {"dominantAlbedo": rgba("#842B4C"), "secondaryAlbedo": rgba("#2E0A18"),
                             "materialClass": "plastic", "materialClassConfidence": 0.6,
                             "colorGradient": {"type": "linear", "axis": "y", "stops": [
                                 {"offset": 0.0, "color": rgba("#2E0A18")},
                                 {"offset": 0.45, "color": rgba("#571031")},
                                 {"offset": 1.0, "color": rgba("#8E2B4C")}]}},
    "gunmetalGuardMaterial": {"dominantAlbedo": rgba("#383844"), "secondaryAlbedo": rgba("#2A2A33"),
                              "materialClass": "metal", "materialClassConfidence": 0.8},
    "crimsonEmitterMaterial": {"dominantAlbedo": rgba("#8E1827"), "secondaryAlbedo": rgba("#26080D"),
                               "materialClass": "plastic", "materialClassConfidence": 0.7},
    "agedGoldMaterial": {"dominantAlbedo": rgba("#8D8354"), "secondaryAlbedo": rgba("#4B4732"),
                         "materialClass": "metal", "materialClassConfidence": 0.8},
    "gripMaterial": {"dominantAlbedo": rgba("#1C1918"), "secondaryAlbedo": rgba("#2E2E35"),
                     "materialClass": "rubber", "materialClassConfidence": 0.6},
}
for c in C:
    c["colorMaterialRecipe"] = dict(RECIPES[c["material"]])
    a = c.get("attachment")
    if a and "embedDepth" not in a and "overlap" not in a:
        a["overlap"] = 0.02  # strict gate: every joint states embed or overlap

# detailInventory: validator wants kind in VALID_DETAIL_KINDS and mapsTo={"ref": <link key>}
DETAIL_BIND = {
    "shell-facet-bands": ("contour", "facetBands"),
    "core-two-plane-split": ("bevel", "bevelPlaneLift"),
    "core-bright-rim": ("emissive", "rimAccent"),
    "core-notch-inverted-v": ("contour", "coreProfileStations"),
    "spine-two-tone": ("linework", "spineTwoTone"),
    "spine-z-offset": ("seam", "magentaCentralSpine"),
    "rod-two-tone-facets": ("gloss", "topFacetDark"),
    "rod-fan-angles": ("contour", "emitterRods"),
    "shoulder-folded-plate": ("bevel", "foldFacets"),
    "olive-block-two-tone": ("bevel", "shadowFacets"),
    "hub-arrowhead": ("contour", "centralGuardHub"),
    "handle-two-plane": ("bevel", "litPlane"),
    "shell-contact-shadow": ("stain", "innerDepthShadow"),
    "shell-base-taper": ("contour", "rightBladeClamp"),
    "tip-crop-inference": ("contour", "outerShellTip"),
}
for d in doc["preSpecAssessment"]["detailInventory"]["details"]:
    kind, ref = DETAIL_BIND[d["id"]]
    d["kind"] = kind
    d["mapsTo"] = {"ref": ref, "note": d["mapsTo"] if isinstance(d["mapsTo"], str) else d["mapsTo"].get("note", "")}
    d["realization"] = "spec-bound"
# keep assessment.json in sync with the bound inventory
assessment_path = HERE / "assessment.json"
assessment = json.load(open(assessment_path))
assessment["preSpecAssessment"]["detailInventory"] = doc["preSpecAssessment"]["detailInventory"]
json.dump(assessment, open(assessment_path, "w"), indent=2, ensure_ascii=False)

fix_refs(doc["componentTree"])
fix_refs(doc["featureReviewTargets"])
fix_refs(doc["repetitionSystems"])
fix_refs(doc["materials"])
fix_refs(doc["qualityContract"])
json.dump(doc, open(SPEC_PATH, "w"), indent=2, ensure_ascii=False)
print(f"spec authored: 47 components, {len(MATS)} materials -> {SPEC_PATH}")
