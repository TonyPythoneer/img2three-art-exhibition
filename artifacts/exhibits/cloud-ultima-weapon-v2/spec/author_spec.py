"""Author the FF7 Ultima Weapon v2 ObjectSculptSpec from the measured artwork.

Every number here traces to `spec/measurements.json` (emitted by `measure_authority.py`), to
`artifacts/ultima-v2/full/parts.json` (the BUILT manifest), or to a numbered assumption in
`spec/image-analysis.md` Layer 8. Normalized-1000 units are divided by 100 so the world-space
object stands 9.7 units tall.

**Every component's `dimensions` and `transform.position` are read out of the built manifest,
not typed here.** They used to be typed, and eight of them had drifted: the drivers carried a
retired root radius, the insert carried a retired base half-width and base height, and the
pommel carried radius 11 after `POMMEL_RADIUS` became `GRIP_HALF_WIDTH` = 12. A spec that
describes a model nobody built is worse than no spec, and there is no way to keep two hand-typed
copies of one number in step. `audit_records.py` re-checks each box against the same manifest.

This makes the manifest an INPUT to this script, so a geometry change needs two turns of the
crank: capture, author, capture, gates. `RELATIONSHIPS.md` §3 says so.

Run:  python3 spec/author_spec.py            # rewrites spec/object-sculpt-spec.json in place
"""

from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "object-sculpt-spec.json"
MEASURE_PATH = HERE / "measurements.json"
INVENTORY_PATH = HERE / "detail-inventory.json"
MANIFEST_PATH = HERE.parents[3] / "artifacts/ultima-v2/full/parts.json"

U = 0.01  # normalized-1000 -> world units

# --- measured landmarks (normalized-1000), see spec/image-analysis.md -------
TIP_Y = 760.0
POMMEL_TIP_Y = -210.7
GRIP_BOTTOM_Y = -180.0  # measured leather edge; the pommel cone starts on this same plane
# The hilt's structural floor: the two jaws' own lower edge. Everything in the guard answers to
# it — the shell's lowest edge (#15), the grip column's flat top (#16) and both arms' roots (#17).
# createUltimaWeaponV2Model's CLAMP_OUTLINE is the authority; these mirror it.
CLAMP_FLOOR_Y = 13.0
CLAMP_OUTER_X = 34.0
CLAMP_HALF_DEPTH = 16.0
GRIP_TOP_Y = CLAMP_FLOOR_Y  # face to face on the jaws' floor: no tang, no burial, no insertion
SHELL_MAX_HALF_WIDTH = 82.0  # U3: reference-03 orthographic ratio, not the crop's projected 194
SHELL_SHOULDER_Y = 70.0
# Y_TRANSITION is the insert's base line; below it the shell is one straight trapezoid down to the
# jaws' floor. SHELL_BASE_HALF_WIDTH is not chosen — it IS the clamp outline's outer vertex, so
# the contact holds by construction. See createUltimaWeaponV2Model.
Y_TRANSITION = 42.0
SHELL_BASE_Y = CLAMP_FLOOR_Y
SHELL_BASE_HALF_WIDTH = CLAMP_OUTER_X
# The shell's own [Y, halfDepth] curve, mirroring `SHELL_STATIONS`. Only the DEPTH column is
# needed here: every blade-layer seat anchor sits on the centre line, where the ridged section
# carries the full half-depth, so `shell_half_depth(y)` IS the surface a film is laid on at x = 0.
SHELL_DEPTH_STATIONS = [
    (13.0, 11.0), (23.5, 11.625), (34.0, 12.25), (44.5, 12.875), (55.0, 13.5), (70.0, 14.0),
    (110.0, 14.0), (300.0, 13.0), (500.0, 11.0), (575.0, 10.0), (650.0, 8.0), (760.0, 0.0),
]
# The blade's relief ladder, as multiples of T = the shell's own total front-to-back thickness.
# All three inner layers are a front half and a rear half, so each entry is the PAIR's total Z
# extent and each half declares half of it.
#
# The two middle layers are SKINS — films laid on the shell's own front and rear surfaces, one
# SKIN_STEP thick, following that surface in X and in Y. Their extent is therefore the shell's own
# T plus twice their own lift, not a boss depth: 1.10 T and 1.20 T are what the build measures,
# and the assertion that matters is the LIFT above the shell's crest, which
# `spec/check_centerline.py` carries. The diamond is the one raised body on the blade.
T_DEPTH = 28.0
SKIN_STEP_T = 0.05  # per face, per skin
RELIEF_T = {
    "outerCrystalShell": 1.00,
    "purpleEnergyInsert": 1.10,
    "darkCoreTriangle": 1.20,
    "rootDiamondGem": 1.77,
}
INSERT_PARTS = ("purpleEnergyInsertFront", "purpleEnergyInsertRear")
CORE_PARTS = ("darkCoreTriangleFront", "darkCoreTriangleRear")
GEM_PARTS = ("rootDiamondGemFront", "rootDiamondGemRear")
# The film's base is the AUTHORITY line and its half-width there is its own measured taper
# (43 at Y=42, 28 at Y=380) evaluated at 55 — `INSERT_OUTLINE`'s first row, not a second number.
INSERT_APEX_Y = 480.0
INSERT_BASE_Y = 55.0
INSERT_BASE_HALF_WIDTH = 42.42
GEM_APEX_Y = 97.0
GEM_BASE_Y = 13.0
GEM_HALF_WIDTH = 17.0
GEM_WAIST_Y = (GEM_APEX_Y + GEM_BASE_Y) / 2  # 55 — CLAMP_OUTLINE's inner-upper vertex
CORE_BASE_Y = GEM_WAIST_Y
CORE_APEX_Y = 187.0
CORE_HALF_WIDTH = 21.0
DRIVER_RADIATION_CENTRE = (0.0, -62.0)
DRIVER_ELEVATION = {"upper": 43.3, "lower": 25.4}
DRIVER_RADIAL_END = 172.0
DRIVER_RADIUS = 11.0
DRIVER_SIDES = 8
DRIVER_JOINT_OVERLAP = 0.05
# The rake is the shell's lower taper as an angle, so the arm's root cap is coplanar with the
# flank it plugs into. createUltimaWeaponV2Model.CONNECTOR_ANGLE_DEG is the authority.
CONNECTOR_RAKE_DEG = -49.3987
# DERIVED as of 2026-08-13, replacing the directed 72.0: the crop pins the arm's outer end as a
# POINT — (81.925, -62.806), its X the mean of the two gold caps' bbox centres and pixel centroids
# in spec/measurements.json and its Y their topmost gold row carried down by the build's own
# 9.356-unit emergence offset — and with the root and rake both locked the built end can only sit
# on one ray, 28.947 units away from that point at every length. This is the perpendicular
# projection, i.e. the closest the arm can get. audit_records.py recomputes it and fails on drift.
# createUltimaWeaponV2Model.CONNECTOR_LENGTH is the authority.
CONNECTOR_LENGTH = 88.8001
CONNECTOR_RADIUS = 16.0
CONNECTOR_SIDES = 8
# Integration #17, as amended on 2026-08-11: it is the root cap's LOWER RIM that sits on the jaws'
# outer vertex, not the cap's centre. So the centre is one radius up the cap's own in-plane normal
# `(-sin a, cos a)` — DERIVED here exactly as the factory's literal is derived, and held to that
# literal by `audit_records.py`, which recomputes it from CLAMP_OUTLINE and the rake.
CONNECTOR_ROOT = (
    CLAMP_OUTER_X - CONNECTOR_RADIUS * math.sin(math.radians(CONNECTOR_RAKE_DEG)),
    CLAMP_FLOOR_Y + CONNECTOR_RADIUS * math.cos(math.radians(CONNECTOR_RAKE_DEG)),
)
SPINNER_SEAT_CLEARANCE = 1.5
# The spinner is a straight-sided frustum, widest at the top. Its shape is DERIVED from the seat in
# `createUltimaWeaponV2Model.spinnerProfile()` rather than tabulated at absolute heights, because a
# table cannot hold a shape whose top ring rides with the arm — see the comment on
# SPINNER_TOP_RADIUS there, and `audit_records.py`'s exposed-ramp clause, which re-derives the
# whole profile from the arm and fails if any of it widens downward where a camera can see it.
# Both ends are the crop's own: `spec/spinner-taper.json`.
SPINNER_TOP_RADIUS = 24.3
SPINNER_BOTTOM_RADIUS = 8.1
SPINNER_BOTTOM_Y = -90.8
SPINNER_SHOULDER_DROP = SPINNER_SEAT_CLEARANCE
GRIP_HALF_WIDTH = 12.0
GRIP_SIDES = 8
# The pommel is one straight cone from the leather's edge to the measured tip. There is no
# collar between them: at 16x the crop runs uniform leather to -180 and gold from the next row.
# Its base ring IS the column's bottom ring — same circumradius, same facet count, asserted
# vertex for vertex by `tests/ultima-v2-solid.test.mjs` — so it is not a number of its own.
POMMEL_RADIUS = GRIP_HALF_WIDTH
POMMEL_SIDES = GRIP_SIDES


def shell_half_depth(y: float) -> float:
    """The shell's own half-depth at height `y` — the surface a film's seat anchor sits on."""
    for (y0, d0), (y1, d1) in zip(SHELL_DEPTH_STATIONS, SHELL_DEPTH_STATIONS[1:]):
        if y0 <= y <= y1:
            return d0 + (y - y0) / (y1 - y0) * (d1 - d0)
    raise ValueError(f"Y={y} is outside the shell's own span")


def driver_root_radius(elevation_deg: float) -> float:
    """Where a rod's root cap sits, DERIVED exactly as `driverRootRadius()` does.

    Not a typed-in coordinate and not a table: the cap is a disc standing in Z, so the surface
    that buries the whole rim is the arm's INRADIUS offset inward by the rod's own radius, taken
    at the far crossing and pushed one anti-gap margin deeper. Change the connector's radius,
    rake or root and the rods follow here in the same edit. The two literals this replaces
    (75.3 / 77.8) were the arm's OUTER surface solution and had been retired in the factory for
    two passes while this file still declared them.
    """
    e, a = math.radians(elevation_deg), math.radians(CONNECTOR_RAKE_DEG)
    dx, dy = math.cos(a), math.sin(a)
    inradius = CONNECTOR_RADIUS * math.cos(math.pi / CONNECTOR_SIDES)
    cap_surface = math.sqrt(inradius**2 - DRIVER_RADIUS**2)
    k0 = (0 - CONNECTOR_ROOT[0]) * dy - (DRIVER_RADIATION_CENTRE[1] - CONNECTOR_ROOT[1]) * dx
    k1 = math.cos(e) * dy - math.sin(e) * dx
    return max((cap_surface - k0) / k1, (-cap_surface - k0) / k1) - DRIVER_JOINT_OVERLAP * 2 * DRIVER_RADIUS


def driver_root_point(sign: float, band: str) -> tuple[float, float]:
    """The world-space (normalized) point where one rod's root cap centre sits."""
    e = math.radians(DRIVER_ELEVATION[band])
    r = driver_root_radius(DRIVER_ELEVATION[band])
    return (sign * r * math.cos(e), DRIVER_RADIATION_CENTRE[1] + r * math.sin(e))


def spinner_seat() -> tuple[float, float, float]:
    """The buried top ring of a spinner, DERIVED exactly as `spinnerSeat()` does: (x, y, radius)."""
    a = math.radians(CONNECTOR_RAKE_DEG)
    down, out = abs(math.sin(a)), abs(math.cos(a))
    inradius = CONNECTOR_RADIUS * math.cos(math.pi / CONNECTOR_SIDES)
    radius = down * inradius - SPINNER_SEAT_CLEARANCE * (down + out)
    lift = (out * radius + SPINNER_SEAT_CLEARANCE) / down
    return (
        CONNECTOR_ROOT[0] + CONNECTOR_LENGTH * math.cos(a),
        CONNECTOR_ROOT[1] + CONNECTOR_LENGTH * math.sin(a) + lift,
        radius,
    )

# --- the BUILT manifest: the authority for every box and every position --------------------
if not MANIFEST_PATH.exists():
    raise SystemExit(
        f"{MANIFEST_PATH} is missing — capture the full detail level before authoring the spec. "
        "Every component's dimensions and position are read from it, never typed here."
    )
_MANIFEST = {p["name"]: p for p in json.loads(MANIFEST_PATH.read_text())["parts"]}


def built_box(cid: str) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """`(width, height, depth), (centreX, centreY, centreZ)` of a built part, in world units.

    Four decimals: the manifest itself carries float32 noise in its 15th digit, and a spec that
    quotes it to full precision invites a diff every capture.
    """
    if cid not in _MANIFEST:
        raise SystemExit(
            f"{cid} is not in {MANIFEST_PATH.name} — either the factory dropped it or the "
            "manifest is stale. Re-capture before authoring."
        )
    b = _MANIFEST[cid]["bounds"]
    size = tuple(round(b[f"max{ax}"] - b[f"min{ax}"], 4) for ax in "XYZ")
    centre = tuple(round((b[f"max{ax}"] + b[f"min{ax}"]) / 2, 4) for ax in "XYZ")
    return size, centre  # type: ignore[return-value]


def built_union(*cids: str) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """The box spanning several built parts — how the root node gets a box it never built."""
    lo = [min(_MANIFEST[c]["bounds"][f"min{ax}"] for c in cids) for ax in "XYZ"]
    hi = [max(_MANIFEST[c]["bounds"][f"max{ax}"] for c in cids) for ax in "XYZ"]
    size = tuple(round(hi[i] - lo[i], 4) for i in range(3))
    centre = tuple(round((hi[i] + lo[i]) / 2, 4) for i in range(3))
    return size, centre  # type: ignore[return-value]


MATERIAL_COLORS = {
    "outerCrystalMaterial": ("#E4E5F3", "#B8BBD6"),
    "purpleInsertMaterial": ("#2B168F", "#7C3CFF"),
    "darkCoreMaterial": ("#3A0B43", "#210A38"),
    "rootGemMaterial": ("#C0184D", "#5A0B34"),
    "guardSteelMaterial": ("#353640", "#202126"),
    "clampMetalMaterial": ("#9698A6", "#55565F"),
    "guardGoldMaterial": ("#8D8450", "#6F6A3D"),
    "driverMaterial": ("#7C102F", "#BB2A50"),
    "connectorLeatherMaterial": ("#3A3B42", "#787985"),
    "gripLeatherMaterial": ("#111216", "#292A30"),
    "pommelGoldMaterial": ("#958044", "#5E512D"),
}


def rgba(hex_color: str, alpha: float = 1.0) -> str:
    value = hex_color.lstrip("#")
    r, g, b = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def feature(fid: str, kind: str, description: str, evidence: str = "full-object") -> dict:
    return {"id": fid, "kind": kind, "description": description, "evidenceRefs": [evidence]}


def override(oid: str, region: str, color: str, roughness: float) -> dict:
    return {
        "id": oid,
        "region": region,
        "baseColor": color,
        "roughness": roughness,
        "evidenceRefs": ["full-object"],
    }


def material(
    mid: str,
    name: str,
    roughness: float,
    metalness: float,
    *,
    shader: str = "MeshStandardMaterial",
    overrides: list[dict] | None = None,
    notes: str,
) -> dict:
    base, secondary = MATERIAL_COLORS[mid]
    return {
        "id": mid,
        "name": name,
        "type": "physical" if shader == "MeshPhysicalMaterial" else "standard",
        "shaderModel": shader,
        "baseColor": base,
        "color": base,
        "albedo": {
            "dominant": base,
            "secondary": [secondary],
            "samplingNotes": (
                "Stops come from the HSV census in spec/image-analysis.md Layer 6; the 1-px "
                "antialiasing ring around every silhouette edge is excluded from sampling."
            ),
        },
        "colorVariation": {
            "palette": [base, secondary],
            "pattern": "flat faceted bands along the component's long axis",
            "amplitude": 0.10,
            "heightCorrelation": 0.0,
        },
        "textureResolution": 1024,
        "textureProjection": {
            "mode": "generated-object-space",
            "repeat": [1.0, 1.0],
            "anisotropy": 4,
            "texelDensityIntent": (
                "Vertex-interpolated bands only. The source is a 210x434 flat-shaded render "
                "with no texture maps, so no texel density target applies."
            ),
        },
        "surfaceFrequencyBands": [
            {"id": "macro", "frequency": 1.0, "amplitude": 0.10, "role": "measured region albedo separation"},
            {"id": "meso", "frequency": 5.0, "amplitude": 0.02, "role": "face-to-face value step"},
            {"id": "micro", "frequency": 32.0, "amplitude": 0.005, "role": "near-zero; reference interiors are flat"},
        ],
        "roughness": {
            "base": roughness,
            "variation": 0.04,
            "map": "independent-procedural-field",
            "localResponse": "per-face variation only; contour aliasing is never encoded as relief",
        },
        "metalness": {"base": metalness, "variation": 0.02 if metalness else 0.0},
        "normal": {
            "pattern": "none",
            "strength": 0.0,
            "scale": 1.0,
            "space": "tangent",
        },
        "bump": {"pattern": "none", "amplitude": 0.0, "scale": 1.0},
        "displacement": {"pattern": "none", "amplitude": 0.0, "scale": 1.0, "silhouetteAffects": False},
        "ambientOcclusion": {
            "cavityStrength": 0.16,
            "contactShadowBias": 0.32,
            "map": "independent-contact-field",
            "notes": "AO is limited to the jaws' own contacts, the buried driver roots, the grip column's top face and the pommel joint. There is no socket cavity anywhere on this model to occlude.",
        },
        "wear": {"edgeWear": 0.0, "scratches": [], "chips": []},
        "dirt": {"amount": 0.0, "cavityBias": 0.0, "color": "#17151A"},
        "localOverrides": overrides or [],
        "shaderNotes": [
            notes,
            "Albedo, roughness, and AO are independent fields; none is derived from another.",
            "No normal or displacement map: the 1997 source is vertex-lit with zero surface relief.",
        ],
        "notes": notes,
    }


def component(
    cid: str,
    name: str,
    level: str,
    parent: str | None,
    material_id: str,
    primitive: str,
    topology_class: str,
    topology_rationale: str,
    *,
    box: tuple[tuple[float, float, float], tuple[float, float, float]] | None = None,
    role: str = "body",
    confidence: float = 0.85,
    local_features: list[dict] | None = None,
    material_class: str = "metal",
    sockets: list[tuple[str, tuple[float, float, float]]] | None = None,
    parent_socket: str | None = None,
    child_socket: str | None = None,
    contact_type: str = "socket",
    contact_normal: tuple[float, float, float] = (0.0, 1.0, 0.0),
    embed_depth: float = 0.0,
    overlap: float = 0.0,
    gap_tolerance: float = 0.001,
    attachment_note: str = "",
    joints: list[dict] | None = None,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> dict:
    """One component of the tree.

    `box` is the BUILT bounding box, `((w, h, d), (cx, cy, cz))`, from `built_box(cid)`; the
    default reads it from the manifest under this component's own id.

    **Sockets are declared in WORLD space and stored local.** A socket's `localPosition` is
    relative to this component's own `transform.position`, which is its built bbox centre — so a
    socket's world point is `transform.position + localPosition`, and `audit_records.py` asserts
    that a child's `childSocket` and its parent's `parentSocket` resolve to the SAME world point.
    That is what turns the anchor graph from prose into a gate: a socket that has been moved by
    an edit, or one that never existed, both fail there instead of at the next review.

    `embedDepth` is how far the child's contact face sits INSIDE the parent's solid, along
    `contactNormal`. `overlap` is the extent of the shared contact PATCH, in the contact plane.
    They are different questions and this model answers them differently on nearly every joint:
    it has almost no insertions left, so most embed depths are 0 while every overlap is positive.
    """
    (width, height, depth), position = box if box is not None else built_box(cid)
    attachment = None
    if parent:
        if parent_socket is None or child_socket is None:
            raise SystemExit(
                f"{cid}: parent {parent!r} needs both parent_socket and child_socket — a "
                "half-declared attachment is exactly the dangling reference this file had 10 of"
            )
        # The contact segment through the child's own anchor: from the mating socket, through
        # the box centre, out the far side. Derived from the socket rather than assumed vertical
        # — the arms rake at -49.4 deg and the rods at 43.3/25.4, and a hard-coded (0, ±h/2, 0)
        # described none of them.
        start = next(local for sid, local in _socket_locals(sockets, position) if sid == child_socket)
        attachment = {
            "parentId": parent,
            "parentSocket": parent_socket,
            "childSocket": child_socket,
            "contactType": contact_type,
            "localStart": [round(v, 4) for v in start],
            "localEnd": [round(-v, 4) for v in start],
            "contactNormal": [round(v, 4) for v in contact_normal],
            "embedDepth": round(embed_depth, 4),
            "overlap": round(overlap, 4),
            "gapTolerance": gap_tolerance,
            "baseRadius": max(0.02, round(width / 2, 4)),
            "endRadius": max(0.02, round(width / 2, 4)),
            "notes": attachment_note,
            "evidenceRefs": ["full-object"],
        }
    base, secondary = MATERIAL_COLORS[material_id]
    return {
        "id": cid,
        "name": name,
        "level": level,
        "role": role,
        "importance": 1.0 if level == "macro" else 0.75,
        "confidence": confidence,
        "primitive": primitive,
        "topologyClass": topology_class,
        "topologyRationale": topology_rationale,
        "geometryDescriptor": {
            "topologyIntent": "PS1-era planar low-poly hard surface; a small number of intentional faces",
            "edgeTreatment": {"type": "none", "bevelRadius": 0.0, "segments": 1},
            "deformationStack": [],
            "uvStrategy": "generated object-space coordinates",
            "normalStrategy": "flat normals so every authored plane reads as one facet",
        },
        "colorMaterialRecipe": {
            "dominantAlbedo": rgba(base),
            "secondaryAlbedo": rgba(secondary),
            "materialClass": material_class,
            "materialClassConfidence": confidence,
            "colorGradient": {
                "type": "linear",
                "axis": "long-axis",
                "stops": [
                    {"position": 0.0, "color": rgba(base)},
                    {"position": 1.0, "color": rgba(secondary)},
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
        "transform": {
            "position": list(position),
            "rotation": list(rotation),
            "scale": [1.0, 1.0, 1.0],
        },
        "actionProfile": {
            "animationRole": "root" if parent is None else "detachable-part",
            "pivot": {
                "mode": "custom",
                "localPosition": [0.0, 0.0, 0.0],
                "axis": [0.0, 1.0, 0.0],
                "confidence": confidence,
            },
            "transformChannels": {
                "translate": True,
                "rotate": True,
                "scale": True,
                "bend": False,
                "twist": False,
                "detach": parent is not None,
                "visibility": True,
                "materialState": True,
            },
            "sockets": [
                {"id": sid, "localPosition": [round(v, 4) for v in local], "localRotation": [0.0, 0.0, 0.0]}
                for sid, local in _socket_locals(sockets, position)
            ],
            "collider": {
                "type": "box",
                "offset": [0.0, 0.0, 0.0],
                "scale": [width, height, depth],
                "isTrigger": False,
                "notes": "Axis-aligned box proxy; the object is a thin planar slab so a box is conservative.",
            },
            "constraints": [],
            "destruction": {
                "breakable": parent is not None,
                "fractureGroup": cid,
                "seamRefs": [],
                "detachableFragments": [cid] if parent else [],
                "breakImpulse": 1.0 if parent else 0.0,
                "debrisMaterial": material_id,
            },
        },
        "material": material_id,
        "materialLayers": [material_id],
        "deformations": [],
        # The joints a single-parent tree cannot carry: every contact this part makes with a
        # component that is NOT its parent. The tree says who carries whom; this says what
        # touches what, which on this model is a different graph — the shell's base edge is the
        # two jaws' floors, and neither is the other's parent.
        "joints": joints or [],
        "seams": [],
        "localFeatures": local_features or [],
        "surfaceDetail": {
            "macroRoughness": 0.10,
            "microRoughness": 0.0,
            "bumpAmplitude": 0.0,
            "normalPattern": "none",
            "displacementPattern": "none",
            "occlusionPattern": "contact-only",
            "edgeWearPattern": "none visible",
            "notes": "Authored planes and per-face value steps carry all visible detail.",
        },
        "evidenceRefs": ["full-object"],
        "details": [],
        "fidelityTier": "hero" if level == "macro" else "detail",
    }


def _socket_locals(
    sockets: list[tuple[str, tuple[float, float, float]]] | None,
    centre: tuple[float, float, float],
) -> list[tuple[str, tuple[float, float, float]]]:
    """World-space socket declarations turned into positions local to the component's box centre."""
    return [(sid, tuple(w[i] - centre[i] for i in range(3))) for sid, w in (sockets or [])]


def anchor(*normalized: float) -> tuple[float, float, float]:
    """A world-space anchor written in the normalized-1000 frame every other number uses."""
    x, y, z = (list(normalized) + [0.0, 0.0, 0.0])[:3]
    return (round(x * U, 6), round(y * U, 6), round(z * U, 6))


def joint(
    jid: str,
    kind: str,
    with_ref: str,
    description: str,
    *,
    socket_ref: str | None = None,
    peer_socket_ref: str | None = None,
    derived_from: str = "",
    asserted_by: str = "",
    measured: str = "",
) -> dict:
    """One contact with a component that is not this one's parent.

    `measured` always names the figure AND its producing artifact, because a joint record that
    says "flush" and nothing else is the kind of claim `audit_records.py` exists to stop.
    """
    return {
        "id": jid,
        "kind": kind,
        "withRef": with_ref,
        "socketRef": socket_ref,
        "peerSocketRef": peer_socket_ref,
        "derivedFrom": derived_from,
        "assertedBy": asserted_by,
        "measured": measured,
        "description": description,
        "evidenceRefs": ["full-object"],
    }


# --- detail inventory ------------------------------------------------------
DETAILS = [
    ("shell-centre-ridge", "r0c1/r1c1", "ridge",
     "The pale shell carries a longitudinal centre ridge; thickness falls from the ridge to zero at both side edges",
     "centreRidge", "component:outerCrystalShell.localFeatures"),
    ("shell-edge-bevel", "r1c0/r1c2", "bevel",
     "Both lateral margins thin into bevelled cutting edges — the shell is the only sharpened blade layer",
     "lateralBevel", "component:outerCrystalShell.localFeatures"),
    ("shell-shoulder-knee", "r2c0/r2c1", "contour",
     "Width knee: half-width peaks at 82 at Y=70, then falls near-linearly at -0.059/unit",
     "shoulderKnee", "component:outerCrystalShell.localFeatures"),
    ("shell-lower-convergence", "r2c1", "contour",
     f"Below the insert's base line (Y={Y_TRANSITION:.0f}, half-width 72) the shell converges to the "
     f"clamps' own outer lower vertex at (+/-{CLAMP_OUTER_X:.0f}, {CLAMP_FLOOR_Y:.0f}) and stops "
     "there; no pale geometry exists below the jaws",
     "lowerConvergence", "component:outerCrystalShell.localFeatures"),
    ("shell-driver-clearance", "r2c0/r2c2", "seam",
     "Background is visible between the shell silhouette and every driver: 25.1 units in front view = 1.14 driver diameters, against a floor of 0.75",
     "driverClearance", "component:outerCrystalShell.localFeatures"),
    ("shell-tip-break", "r0c0/r0c1", "contour",
     "Second knee at Y=575 (half-width 54) where the taper breaks to -0.29/unit into the point",
     "tipBreak", "component:outerCrystalShell.localFeatures"),
    ("shell-value-bands", "r1c0/r1c1", "gloss",
     "Three flat lavender value bands (#E6E7F2 / #CDCFD8 / #B5B6BF) with no smooth ramp between them",
     "facetBands", "material:outerCrystalMaterial.localOverrides"),
    ("insert-apex-triangle", "r1c1", "contour",
     "Above Y=380 the insert's sides break to -0.28/unit, forming the small triangular point at Y=480",
     "apexPoint", f"component:{INSERT_PARTS[0]}.localFeatures"),
    ("insert-blunt-edge", "r1c1", "bevel",
     "The insert's side faces stay square and faceted — it never receives the shell's knife-edge bevel",
     "bluntSideFace", f"component:{INSERT_PARTS[0]}.localFeatures"),
    ("insert-relief-step", "r1c1/r2c1", "ridge",
     f"First skin: a film {SKIN_STEP_T:.2f} T thick laid on the shell's own front and rear surfaces, following that surface in X and in Y, never touching Z=0",
     "reliefStep", f"component:{INSERT_PARTS[0]}.localFeatures"),
    ("insert-energy-ramp", "r1c1/r2c1", "emissive",
     "Vertical ramp runs dark at the apex (#160D59) to bright at the base (#7F3CF2) — inverted from surface shading, so it reads as emitted energy",
     "energyRamp", "material:purpleInsertMaterial.localOverrides"),
    ("core-thin-wedge", "r2c1", "ridge",
     "Narrow centred upward triangle over the insert's lower half; never widens into a central panel",
     "thinWedge", "component:darkCoreTriangleFront.localFeatures"),
    ("core-relief-step", "r2c1", "ridge",
     f"Second skin: the same film {SKIN_STEP_T:.2f} T thick, seated on the insert's outer face rather than on the shell, so the two stack and the order cannot invert",
     "reliefStep", "component:darkCoreTriangleFront.localFeatures"),
    ("gem-rhombus-waist", "r2c1", "ridge",
     "Elongated rhombus, 84 tall by 34 wide (2.5:1), waist at Y=55 level with the clamp jaws' contact line",
     "waistGirdle", "component:rootDiamondGemFront.localFeatures"),
    ("gem-relief-step", "r2c1", "ridge",
     "The one raised BODY on the blade: a girdled rhombus seated on the two skins, its rim standing 0.12 T outside them at every station and its crown a further 0.38 of its own half-width above that rim",
     "reliefStep", "component:rootDiamondGemFront.localFeatures"),
    ("gem-facet-split", "r2c1", "bevel",
     "The gem's front splits into a lighter and a darker facet along its vertical axis",
     "facetSplit", "material:rootGemMaterial.localOverrides"),
    ("collar-tent-crease", "r2c1", "ridge",
     "The guard closes with no bridge part in it: the two jaws carry a flat floor at Y=13 and the grip column's flat top lies against it, face to face",
     "clampedTang", "component:leatherGrip.localFeatures"),
    ("connector-rake", "r2c0/r2c2", "contour",
     "Both leather connector arms rake outward-downward from the jaws' outer corners, at the shell's own lower taper turned into an angle",
     "connectorRake", "component:leatherConnectorRight.localFeatures"),
    ("spinner-end-taper", "r2c0/r2c2", "contour",
     "Each arm ends in a faceted frustum hanging vertically, WIDEST AT THE TOP and narrowing all "
     "the way down: a derived seat ring buried inside the leather, a shoulder 1.5 below it at "
     f"radius {SPINNER_TOP_RADIUS}, then one straight line to a blunt truncation at "
     f"{SPINNER_BOTTOM_RADIUS} rather than a point",
     "bluntTruncation", "component:spinnerEndRight.localFeatures"),
    ("driver-bright-edge", "r2c0/r2c2", "gloss",
     "One thin bright edge strip (#BB2A50) runs the length of each wine-red rod",
     "edgeHighlight", "material:driverMaterial.localOverrides"),
    ("driver-radiation-centre", "r2c1", "seam",
     "All four driver axes converge at (0, -62) — below the guard centre, not at it",
     "radiationCentre", "component:driverArray.localFeatures"),
    ("driver-root-insertion", "r2c0/r2c2", "seam",
     "Each rod's root cap is buried inside its connector arm, deep enough that the whole cap rim "
     "clears the leather and never as deep as the arm's own axis — there is no socket mesh",
     "rootCapOnConnector", "component:driverRightUpper.localFeatures"),
    ("clamp-jaw-pair", "r2c1", "seam",
     "Two mirrored triangular jaws cradle the diamond's lower half and meet on the axis at the "
     "culet, sharing that one vertical edge and no face",
     "jawBaseJoin", "component:crystalClampRight.localFeatures"),
    ("grip-constant-width", "r2c1", "contour",
     "The shaft holds half-width 12 from the jaws' floor at Y=13 to its measured lower edge at -180 — no waist, no T",
     "constantWidth", "component:leatherGrip.localFeatures"),
    ("grip-no-collar", "r2c1", "seam",
     "No collar anywhere on the shaft: at 16x the leather runs uniform to -180 and the gold starts on the next row",
     "noCollar", "component:leatherGrip.localFeatures"),
    ("pommel-cone", "r2c1", "contour",
     "The pointed pommel is one straight cone from the leather's own lower edge to the tip at "
     "-210.7. Its base ring is the column's bottom ring — same circumradius 12, same 8 facets — "
     "so its front-view reach is the column's own 11.087 and the junction cannot open",
     "straightCone", "component:pointedMetalPommel.localFeatures"),
]


def build_detail_inventory() -> dict:
    return {
        "scanMethod": "grid-3x3 zone scan cross-checked against measure_authority.py regions",
        "targetMinDetails": 10,
        "note": (
            "Every entry maps to a component.localFeatures or material.localOverrides entry. "
            "Details are measured from spec/measurements.json unless the mapsTo note says inferred."
        ),
        "details": [
            {
                "id": did,
                "zone": zone,
                "kind": kind,
                "description": desc,
                "mapsTo": {"ref": ref, "note": note},
                "realization": "spec-bound",
            }
            for did, zone, kind, desc, ref, note in DETAILS
        ],
    }


PBR_REJECTION = (
    "Extraction ran and is kept as evidence, but its output is deliberately not applied. "
    "The source is a 1997 vertex-lit render with zero surface relief: the extracted height and "
    "normal maps encode only the 1-px antialiasing steps along contours, with flat interiors, so "
    "applying them would stamp raster stair-stepping onto the model as physical relief. "
    "analyze_texture.py's finish classifier compounded this by reading the pale crystal as "
    "'brushed-steel' (metalness 1.0) and the muted gold guard as 'painted-metal' (metalness 0.0) "
    "- both inverted from what the artwork shows. Scalars therefore stay at the "
    "observation-grounded values in spec/image-analysis.md Layer 5."
)


def attach_reference_pbr(spec: dict) -> None:
    """Record every extraction run against this reference, marked unusable with the reason.

    The evidence is real and worth keeping; the verdict is the agent's, not the script's."""
    evidence_root = HERE / "pbr-evidence"
    for mat in spec["materials"]:
        run = evidence_root / mat["id"] / "pbr-evidence.json"
        if not run.exists():
            continue
        data = json.loads(run.read_text())
        maps = {}
        for channel, entry in (data.get("maps") or {}).items():
            if not isinstance(entry, dict):
                continue
            path = entry.get("path", "")
            try:
                path = str(Path(path).relative_to(HERE.parent))
            except ValueError:
                pass
            maps[channel] = {**entry, "path": path, "applied": False}
        mat["referencePbr"] = {
            "version": "1.0",
            "sourceImage": f"spec/pbr-evidence/crops/crop-{mat['id']}.png",
            "extractor": "stage1_intake/extract_pbr_evidence.py + stage1_intake/analyze_texture.py",
            "method": "single-image pixel evidence; not inverse rendering and not photogrammetry",
            "usable": False,
            "verdict": "rejected",
            "extractorVerdict": data.get("verdict"),
            "confidence": data.get("confidence"),
            "estimatedFidelity": data.get("estimatedFidelity"),
            "targetThreshold": data.get("targetThreshold"),
            "hardLimit": "A single flat-shaded image cannot recover albedo/roughness/normal/AO.",
            "rejectionReason": PBR_REJECTION,
            "maps": maps,
            "extractorWarnings": data.get("warnings", []),
        }


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text())
    measurements = json.loads(MEASURE_PATH.read_text())

    # Re-authoring invalidates every prior review: they scored a component tree that no longer
    # exists. Clearing the history here (rather than letting it accumulate) is what keeps
    # `author_spec -> run_gates -> record_reviews` reproducible from any starting state.
    spec["reviewHistory"] = []
    spec["sculptPipeline"] = {
        **spec.get("sculptPipeline", {}),
        "currentPass": "blockout",
        "completedPasses": [],
    }

    spec["targetId"] = "ultimaWeaponV2"
    spec["suitability"] = "conditional"
    spec["scores"] = {
        "object_isolation": 3,
        "silhouette_readability": 3,
        "depth_inference": 1,
        "primitive_decomposition": 3,
        "material_procedurality": 3,
        "occlusion_risk": 2,
        "interaction_fit": 3,
    }
    spec["referenceCamera"] = {
        "solved": False,
        "fovDegrees": 18.0,
        "aspect": 210 / 434,
        "orientation": {"yaw": 4.0, "pitch": -3.0, "roll": -18.13},
        "positionHint": [0.0, 2.2, 26.0],
        "note": (
            "Orthographic. Roll is measured (18.13 deg, tip-to-pommel silhouette diameter) and "
            "a roll sweep peaks there. Yaw is solved by sweep: IoU is flat within 0.001 from "
            "-6 to +6 deg and falls away outside, so the artwork is nearly a straight-on view "
            "with a roll. Pitch stays a small estimate the silhouette cannot constrain."
        ),
    }

    # --- assessment --------------------------------------------------------
    pre = spec["preSpecAssessment"]
    pre["objectClass"] = {
        "primaryType": "layered crystal straight sword with a four-rod driver array (PS1-era flat-shaded game asset)",
        "primaryDomain": "object",
        "formLanguage": ["hard-surface", "planar-faceted", "transparent-like"],
        "structureKind": ["compound object", "layered shell", "repeated modules"],
        "motionPotential": ["static prop", "whole-object transform", "detachable"],
        "materialFamilies": [
            "glass-like (pale crystal shell, built SOLID by user direction of 2026-08-07 against a brief that asks for translucent - confidence-report.md conflict 7)",
            "energy crystal (violet insert, magenta gem)",
            "metal (charcoal steel, muted olive gold)",
            "leather (near-black grip)",
        ],
        "notes": (
            "Eight public part types: four blade layers and four hilt part types. The identity "
            "rests on exactly four slim drivers in mirrored pairs, a sharpened pale shell over an "
            "unsharpened violet insert, and the absence of any surface microdetail."
        ),
    }
    pre["complexity"] = {
        "tier": "complex",
        "scores": {
            "silhouetteComplexity": 2,
            "componentCount": 3,
            "hierarchyDepth": 3,
            "repetitionDensity": 1,
            "materialLayerCount": 3,
            "localDetailDensity": 1,
            "occlusionRisk": 3,
            "actionReadinessNeed": 2,
        },
        "estimatedCounts": {
            "macroComponents": 8,
            "mesoComponents": 12,
            "microFeatureGroups": 18,
            "materialLayers": 9,
            "repetitionSystems": 1,
        },
        "reasoning": [
            "Two macro assemblies (blade, hilt) resolving into eight independently reviewable public part types.",
            "One repetition system: four drivers, two per side, sharing one geometry and four transforms.",
            "Nine distinct material zones. The shell was the main technical risk while it was translucent - ordering an alpha-blended hull over opaque inserts - and it is SOLID since 2026-08-07 by user direction, which retires that risk and replaces it with an occlusion one: a layer that does not physically break the shell is now deleted rather than washed out.",
            "Occlusion risk is high: the blade root and all four driver roots are hidden behind the guard, and the dark core's lower half shares the crop's dark run with the gem it surrounds.",
            "Zero microtexture — the flat faceted language is itself identity-defining, so adding relief is a failure mode, not an improvement.",
        ],
    }
    # U1-U7 are enumerated in spec/image-analysis.md Layer 8. Each carries a recorded
    # decision below, so none of them blocks implementation; the list stays empty on purpose.
    pre["unknownsToResolveBeforeImplementation"] = []
    pre["detailInventory"] = build_detail_inventory()
    pre["anatomy"]["applies"] = False

    spec["assumptions"] = [
        "Rear geometry mirrors the measured front profile (U1).",
        "Blade depth is +/-14 and guard depth +/-20 normalized units, inside the master prompt's 22-32 / 35-50 ranges (U1).",
        "darkCoreTriangle's apex is measured off the authority crop, not inferred from reference 03: the wedge's own edges fit a straight line over 86 rows and reach zero width at Y=186.9 (U2, confidence 0.75). Only its base half-width stays directed.",
        "The blade's maximum half-width uses reference 03's orthographic ratio rather than the crop's projected 194 (U3).",
        "The four drivers are mirrored pairs sharing one geometry; the left/right elevation gap is treated as projection, not authored asymmetry (U6).",
        "Grip and pommel follow the measured artwork (175 + 30) rather than the master prompt's starting contract (205 + 35) (U5).",
        "The 1-px silhouette antialiasing in the 210x434 source is rasterization, never surface relief (U7).",
    ]
    spec["resolvedUncertainties"] = {
        "U1_depth": "One view only. Rear geometry mirrors the measured front profile; shell +/-14 and guard +/-20 normalized units, inside the contract's ranges. Verified from the side review view.",
        "U2_darkCoreExtent": "RESOLVED against the crop, which was never occluding it. Y=98.8 was where measure_authority's RED colour family stops, and the core is red-tinted only where it flanks the gem; above the gem it is a near-black wedge on violet and falls into the insert/grip families. Read as a darkening of the insert instead, its edges fit halfWidth = 26.152 - 0.1400*Y over 86 rows at an RMS of 0.60 units (0.26 source pixels), reaching zero at Y=186.9 -- so the apex is measured at 187 and the outline is a straight two-point triangle. The same fit extrapolated to the waist reads 18.45 against the directed base half-width of 21, so the base is corroborated rather than merely directed. Confidence 0.75. See spec/measure_core_apex.py and spec/core-apex.json.",
        "U3_bladeRootWidth": "Occluded by the collar and carriers. Symmetric max half-width 95, from reference 03's orthographic width:length ratio of 0.249, not the crop's projected 194.",
        "U4_driverRoots": "All four emerge from behind the carriers. Roots extrapolated back along the measured PCA axes to radius 55 from the common radiation centre (0, -62).",
        "U5_gripLength": "Measured 175+30 conflicts with the master prompt's 205+35 starting contract. The artwork wins; reference 03's independent ratio (0.274) agrees with the measurement (0.284), not the contract (0.316).",
        "U6_driverZFan": "The 5-7 degree left/right elevation gap is treated as camera yaw. Drivers are authored coplanar in XY as mirrored pairs, the conservative reading the component contract requires.",
        "U7_pbrChannels": "The source is vertex-lit with no maps. Every PBR scalar is era-inference; extraction runs for the record but is not treated as ground truth.",
        "shellTransmission": "Low transmission with opacity high enough that the insert never washes out the shell's silhouette.",
    }

    spec["coordinateFrame"] = {
        "front": "+Z faces the artwork camera",
        "up": "+Y runs from the guard socket to the blade tip",
        "scaleReference": "normalized-1000 divided by 100; the object stands 9.707 world units tall",
        "componentTransform": (
            "Every componentTree entry's transform.position is its BUILT bounding-box centre, read "
            "from artifacts/ultima-v2/full/parts.json, and dimensions are that box's own extents. "
            "They are not authored numbers and must not be edited by hand."
        ),
        "socketConvention": (
            "actionProfile.sockets[].localPosition is relative to that component's own "
            "transform.position, so a socket's world point is position + localPosition. Both ends "
            "of every attachment declare the joint's anchor, and spec/audit_records.py asserts "
            "that the parentSocket and the childSocket resolve to the SAME world point. Anchors "
            "that describe an OUTLINE coincidence lie in the outline plane Z = 0; anchors that "
            "describe a SEAT carry the depth of the surface they sit on."
        ),
    }
    spec["silhouette"] = {
        "boundingShape": "long slender crystal leaf blade over a compact guard with four radiating rods and a narrow grip",
        "aspectRatios": [
            f"tip-to-pommel height : maximum blade width = {(TIP_Y - POMMEL_TIP_Y) / (2 * SHELL_MAX_HALF_WIDTH):.2f}:1",
            f"blade length : grip+pommel length = {TIP_Y / -POMMEL_TIP_Y:.2f}:1",
            "shell maximum width : insert maximum width = 2.21:1",
        ],
        "symmetry": "bilateral about the YZ plane; the crop's projected asymmetry is camera yaw, not geometry",
        "dominantCurves": [
            "shell shoulder knee at Y=62 then one straight taper to Y=575",
            "insert knee at Y=380 into its triangular point",
            "four straight driver axes converging at (0, -62)",
        ],
        "negativeSpaces": [
            "the gap between each driver pair",
            "the gap between the carriers' gold caps and the grip",
            "the clearance between the insert's edges and the shell's bevels (>=54 units per side)",
        ],
        "landmarks": [
            "blade tip (0, 760)",
            "shell shoulder (+/-95, 62)",
            "insert apex (0, 480)",
            "gem apex (0, 97)",
            "guard socket (0, 0)",
            "cap centres (+/-85, -80)",
            "driver ends (+/-126, 54) and (+/-155, 14)",
            "grip end (0, -180)",
            "pommel tip (0, -211)",
        ],
    }
    spec["viewEvidence"] = [
        {
            "id": "full-object",
            "view": "artwork three-quarter, rolled 18.13 degrees",
            "imageRegion": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0, "units": "normalized"},
            "observations": [
                "A pale shell fully encloses a narrower violet insert on every side. The brief reads this shell as translucent; the crop shows no compositing to support that - the violet field reaches (0, 0, 45) and its boundary against the shell is 2 px at the median - and the user directed it SOLID on 2026-08-07 (spec/zoom_shell_translucency.py).",
                "Exactly four wine-red rods radiate outward and upward, two per side.",
                "A magenta rhombus gem straddles the gold collar at the blade root.",
                "The charcoal carriers rake down-outward and end in gold truncated cones.",
                "The grip is a narrow near-black shaft ending in a small gold cone.",
            ],
            "confidence": 0.86,
        },
        {
            "id": "reference-03-front",
            "view": "community rebuild, near-orthographic front (secondary evidence only)",
            "imageRegion": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0, "units": "normalized"},
            "observations": [
                "Confirms bilateral symmetry and the blade's true width:length ratio of 0.249.",
                "Confirms the dark core triangle exists as a separate layer above the gem.",
                "Confirms the grip+pommel : blade ratio at 0.274, matching the measured 0.284.",
            ],
            "confidence": 0.5,
        },
    ]

    # --- materials ---------------------------------------------------------
    spec["materials"] = [
        material(
            "outerCrystalMaterial", "Pale faceted crystal shell", 0.22, 0.0,
            shader="MeshPhysicalMaterial",
            overrides=[
                override("facetBands", "flat lavender value bands across the shell's planes", "#CDCFD8", 0.26),
                override("edgeBevelBand", "the thin bevel facets along both cutting edges", "#B8BBD6", 0.20),
            ],
            notes=(
                "Transmission 0.16, opacity 0.86, clearcoat 0.12, depthWrite true. Transmission stays "
                "low so the insert reads as inset rather than showing through the shell's whole face."
            ),
        ),
        material(
            "purpleInsertMaterial", "Violet energy insert", 0.35, 0.0,
            shader="MeshPhysicalMaterial",
            overrides=[
                override("energyRamp", "vertical ramp, dark apex to bright base", "#7C3CFF", 0.32),
            ],
            notes="Opaque with a weak emissive lift at the base; the ramp runs opposite to surface shading.",
        ),
        material(
            "darkCoreMaterial", "Dense dark core crystal", 0.45, 0.0,
            notes="Opaque, darker and denser than the insert; no emission is evidenced.",
        ),
        material(
            "rootGemMaterial", "Faceted magenta root gem", 0.15, 0.0,
            shader="MeshPhysicalMaterial",
            overrides=[
                override("facetSplit", "the gem's lighter and darker front facets", "#FF3866", 0.12),
            ],
            notes="Transmission 0.30 with sharp flat facets; it must read dimensional, not as a flat arrow.",
        ),
        material(
            "guardSteelMaterial", "Charcoal guard steel", 0.50, 0.80,
            notes="Dark steel; keep face normals readable without a mirror highlight the source never shows.",
        ),
        material(
            "clampMetalMaterial", "Machined clamp and socket metal", 0.42, 0.85,
            notes=(
                "Two stops lighter than the guard steel on purpose. The clamp jaws and driver "
                "sockets sit directly against dark grey leather, and at the guard steel's value "
                "the whole hilt collapsed into one black mass at exactly the place this pass is about."
            ),
        ),
        material(
            "guardGoldMaterial", "Muted olive-gold guard fittings", 0.40, 0.90,
            overrides=[
                override("capRimBand", "the gold caps' upper rim where they meet the carriers", "#6F6A3D", 0.46),
            ],
            notes="Desaturated olive gold; metalness is high but roughness keeps it matte, as measured.",
        ),
        material(
            "driverMaterial", "Wine-red driver rods", 0.35, 0.50,
            overrides=[
                override("edgeHighlight", "one thin bright strip along each rod's lit edge", "#BB2A50", 0.28),
            ],
            notes="All four instances share this material; the bright strip is the only specular event in the source.",
        ),
        material(
            "connectorLeatherMaterial", "Dark grey connector leather", 0.75, 0.0,
            overrides=[
                override("wrapSeam", "the single seam running the arm's length", "#787985", 0.70),
            ],
            notes=(
                "The arms under the drivers are leather-covered, not black metal cubes. Non-metallic "
                "like the grip and two stops lighter, so the two leathers read as different components."
            ),
        ),
        material(
            "gripLeatherMaterial", "Near-black leather grip", 0.80, 0.0,
            overrides=[
                override("wrapRidgeBand", "the raised wrap ridges", "#292A30", 0.72),
            ],
            notes="Non-metallic and rough; the darkest region in the whole reference at #0C0C0C.",
        ),
        material(
            "pommelGoldMaterial", "Muted gold spinner pommel", 0.35, 0.90,
            notes="Slightly brighter and smoother than the guard fittings, matching the measured #958044.",
        ),
    ]

    attach_reference_pbr(spec)

    # --- the assembly anchor graph -----------------------------------------
    # Every anchor below is a WORLD point in the normalized-1000 frame, and every one of them is
    # a point some part of the model is DERIVED from — not a convenience offset. They are written
    # once, here, and both ends of each joint read the same name, which is what stops a socket
    # from being moved on one side of a contact and not the other.
    #
    # `A_BASE` carries four parts at once and is the hilt's structural datum: the jaws' floor
    # (`CLAMP_FLOOR_Y`), the stone's culet, the shell's lowest edge (#15) and the grip column's
    # flat top (#16) are all on it.
    A_GUARD = anchor(0, 0, 0)
    A_BASE = anchor(0, CLAMP_FLOOR_Y, 0)
    A_FLOOR = {-1.0: anchor(-CLAMP_OUTER_X, CLAMP_FLOOR_Y, 0),
               1.0: anchor(CLAMP_OUTER_X, CLAMP_FLOOR_Y, 0)}
    A_WAIST = {-1.0: anchor(-GEM_HALF_WIDTH, GEM_WAIST_Y, 0),
               1.0: anchor(GEM_HALF_WIDTH, GEM_WAIST_Y, 0)}
    # A film's seat is the host's own surface ON THE CENTRE LINE at the film's base height, where
    # the ridged section carries its full half-depth. The core's seat is the insert's outer face,
    # which is the shell's surface plus one SKIN_STEP — the stack written as a chain, not as two
    # independent depths.
    A_INSERT_SEAT = {1.0: anchor(0, INSERT_BASE_Y, shell_half_depth(INSERT_BASE_Y)),
                     -1.0: anchor(0, INSERT_BASE_Y, -shell_half_depth(INSERT_BASE_Y))}
    A_CORE_SEAT = {1.0: anchor(0, CORE_BASE_Y, shell_half_depth(CORE_BASE_Y) + SKIN_STEP_T * T_DEPTH),
                   -1.0: anchor(0, CORE_BASE_Y, -(shell_half_depth(CORE_BASE_Y) + SKIN_STEP_T * T_DEPTH))}
    A_RADIATION = anchor(0, DRIVER_RADIATION_CENTRE[1], 0)
    A_DRIVER_ROOT = {(sign, band): anchor(*driver_root_point(sign, band), 0)
                     for sign in (-1.0, 1.0) for band in ("upper", "lower")}
    _seat_x, _seat_y, _seat_r = spinner_seat()
    A_SPINNER = {-1.0: anchor(-_seat_x, _seat_y, 0), 1.0: anchor(_seat_x, _seat_y, 0)}
    A_GRIP_BOTTOM = anchor(0, GRIP_BOTTOM_Y, 0)

    # Contact normals that are not vertical are DERIVED from the edge or axis they belong to.
    _edge = math.hypot(GEM_HALF_WIDTH, GEM_WAIST_Y - GEM_BASE_Y)          # the jaw's inner edge
    JAW_NORMAL = {s: (s * (GEM_WAIST_Y - GEM_BASE_Y) / _edge, -GEM_HALF_WIDTH / _edge, 0.0)
                  for s in (-1.0, 1.0)}
    _rake = math.radians(CONNECTOR_RAKE_DEG)
    ARM_AXIS = {s: (s * math.cos(_rake), math.sin(_rake), 0.0) for s in (-1.0, 1.0)}

    # The two assemblies overlap over this span: the jaws, the arms and the upper rods all rise
    # above the guard-centre plane and into the blade group's own vertical span. Read from the
    # manifest, so it is the built overlap and not a claim about one.
    GROUP_OVERLAP = round(built_box("hiltGroup")[0][1] / 2 + built_box("hiltGroup")[1][1]
                          - (built_box("bladeGroup")[1][1] - built_box("bladeGroup")[0][1] / 2), 4)
    GRIP_REACH = GRIP_HALF_WIDTH * math.cos(math.pi / GRIP_SIDES) * U     # the octagon's own reach

    # --- component tree ----------------------------------------------------
    comps: list[dict] = []
    comps.append(component(
        "ultimaWeaponV2Root", "Ultima Weapon v2 root", "macro", None, "guardSteelMaterial",
        "box", "assembled-solid",
        "The root spans a rigid multi-material prop with no continuous organic surface; it carries transforms only.",
        box=built_union("bladeGroup", "hiltGroup"), confidence=0.95,
        sockets=[("guard_center_anchor", A_GUARD)],
    ))
    comps.append(component(
        "bladeGroup", "Blade group", "macro", "ultimaWeaponV2Root", "outerCrystalMaterial",
        "extrude", "conforming-shell",
        "A layered blade envelope whose inner layers break through the outer shell's faces as a relief ladder.",
        role="blade", confidence=0.9, material_class="glass",
        parent_socket="guard_center_anchor", child_socket="blade_group_origin",
        contact_type="frame", contact_normal=(0.0, 1.0, 0.0),
        overlap=GROUP_OVERLAP, gap_tolerance=0.0,
        attachment_note=(
            "A transform frame, not a surface contact: the blade group carries no geometry of its "
            "own. The overlap is how far the HILT's parts rise into this group's vertical span."
        ),
        sockets=[
            ("blade_group_origin", A_GUARD),
            # The shell's base plane and the stone's culet are the same world point — the jaws'
            # floor — and they are two sockets rather than one because two different parts hang
            # off them and a shared name would hide which moved.
            ("blade_root_anchor", A_BASE),
            ("gem_mount_anchor", A_BASE),
        ],
    ))
    comps.append(component(
        "outerCrystalShell", "Outer crystal shell", "macro", "bladeGroup", "outerCrystalMaterial",
        "extrude", "conforming-shell",
        "A ridged blade shell: one longitudinal centre ridge with the cross-section contracting to zero thickness at both edges.",
        role="blade", confidence=0.88, material_class="glass",
        parent_socket="blade_root_anchor", child_socket="base_anchor",
        contact_type="butt", contact_normal=(0.0, 1.0, 0.0),
        overlap=2 * CLAMP_OUTER_X * U, gap_tolerance=0.001,
        attachment_note=(
            "Integration #15: the shell's lowest edge lies ON the jaws' floor plane and is exactly "
            "as long as the two jaws' floor edges laid end to end. Nothing is inserted — the "
            "overlap is that shared edge's own length, and the embed depth is zero."
        ),
        sockets=[
            # Every anchor sits on Z = 0 unless it names a SEAT. A seat carries the depth of the
            # surface it is on; an outline anchor lies in the outline's own plane.
            ("base_anchor", A_BASE),
            ("insert_seat_front", A_INSERT_SEAT[1.0]),
            ("insert_seat_rear", A_INSERT_SEAT[-1.0]),
            ("lower_contact_left", A_FLOOR[-1.0]),
            ("lower_contact_right", A_FLOOR[1.0]),
        ],
        joints=[
            joint(
                f"shellBaseOn{side}Jaw", "tile", f"crystalClamp{side}",
                "The shell's own lowest corner IS this jaw's outer floor vertex; the two jaws' "
                "floor edges tile end to end across the shell's whole base edge.",
                socket_ref=f"lower_contact_{side.lower()}", peer_socket_ref=f"floor_outer_{side.lower()}",
                derived_from="SHELL_STATIONS' base row = CLAMP_OUTLINE[2] (integration #15)",
                asserted_by="check_centerline.py (shell.minY = clamp.minY), audit_records.py (#15)",
                measured="shell.minY - clamp.minY = +0.000000 world; 68.000 vs 34.000 + 34.000 "
                         "(artifacts/ultima-v2/full/parts.json)",
            ) for side in ("Left", "Right")
        ] + [
            joint(
                f"shellFlankUnder{side}Arm", "flank-contact", f"leatherConnector{side}",
                "The arm's root cap is raked to the shell's own lower taper, so the cap's WHOLE "
                "diameter lies ON this flank instead of behind it.",
                socket_ref=f"lower_contact_{side.lower()}", peer_socket_ref="root_rim_anchor",
                derived_from="CONNECTOR_ANGLE_DEG = -atan((83 - 34) / (55 - 13)) (integration #17)",
                asserted_by="audit_records.py — root cap vs the shell's front-view edge",
                measured="worst front-view residual 0.000005 over 65 samples "
                         "(printed by audit_records.py from createUltimaWeaponV2Model.ts)",
            ) for side in ("Left", "Right")
        ],
        local_features=[
            feature("centreRidge", "ridge", "Longitudinal centre ridge; thickness falls from the ridge to zero at both side edges."),
            feature("lateralBevel", "bevel", "Both side margins thin into bevelled cutting edges — the only sharpened blade layer."),
            feature("shoulderKnee", "contour", f"Half-width peaks at {SHELL_MAX_HALF_WIDTH:.0f} at Y={SHELL_SHOULDER_Y:.0f}, then falls at -0.059/unit to 54 at Y=575."),
            feature("tipBreak", "contour", "Taper breaks to -0.29/unit at Y=575 and contracts into a crisp point at Y=760."),
            feature("lowerConvergence", "contour", f"Below Y={Y_TRANSITION:.0f} (half-width 72) the shell converges to the clamps' outer edges at (+/-{SHELL_BASE_HALF_WIDTH:.0f}, {SHELL_BASE_Y:.0f}) and stops. No pale geometry below the jaws."),
            feature("driverClearance", "seam", "Background stays visible between the shell and every driver: 1.14 driver diameters in front view, against a floor of 0.75."),
            feature("facetBands", "gloss", "Three flat lavender value bands with hard steps between them."),
        ],
    ))
    # The insert is TWO meshes as well, and unlike the diamond they are NOT cut on Z=0: each is a
    # film laid on one of the shell's own faces, so the pair straddles the shell's body rather
    # than meeting in its middle. The spec says what was built.
    for cid, side, sign in ((INSERT_PARTS[0], "front", 1.0), (INSERT_PARTS[1], "rear", -1.0)):
        comps.append(component(
            cid, f"Violet energy insert, {side} skin", "meso", "outerCrystalShell", "purpleInsertMaterial",
            "extrude", "conforming-shell",
            f"The {side} film of the violet energy channel: a skin {SKIN_STEP_T:.2f} T thick laid ON the shell's {side} surface and following it in X and in Y, not a boss standing through the blade.",
            role="core", confidence=0.9, material_class="plastic",
            parent_socket=f"insert_seat_{side}", child_socket="seat_anchor",
            contact_type="seated", contact_normal=(0.0, 0.0, sign),
            overlap=built_box(cid)[0][0], gap_tolerance=0.002,
            attachment_note=(
                "Seated, not inserted: the film's whole underside is the shell's own surface "
                "evaluated pointwise, so the overlap is its entire footprint and the embed depth "
                "is zero. Signed seat clearance -0.0608 ... +0.0617 normalized units, against a "
                "0.20 bound (artifacts/ultima-v2/full/parts.json, stackConformity)."
            ),
            sockets=[
                ("seat_anchor", A_INSERT_SEAT[sign]),
                # What the dark core is laid on: this film's own outer face, one SKIN_STEP out.
                (f"core_seat_{side}", A_CORE_SEAT[sign]),
            ],
            local_features=[
                feature("apexPoint", "contour", "Sides break to -0.28/unit above Y=380, forming the small triangular point at Y=480."),
                feature("bluntSideFace", "bevel", "Side faces stay square and faceted; no knife-edge bevel is applied."),
                feature("reliefStep", "ridge", f"First skin: {SKIN_STEP_T:.2f} T of film, so the PAIR spans {RELIEF_T['purpleEnergyInsert']:.2f} T — the shell's own thickness plus two films, not a boss depth."),
                feature("conformingUnderside", "seam", "The underside sits ON the shell's front surface, carrying the shell's own ridge shoulder as a ring point, so the film never dips back inside its host."),
                feature("energyRamp", "emissive", "Dark apex to bright base — inverted from surface shading, so it reads as emitted energy."),
            ],
        ))
    # The dark core is the second film, and its parent is the FILM UNDER IT rather than the shell:
    # its underside is the insert's outer face, so the two stack and the order cannot invert by
    # editing one number. The tree says so now; it used to hang off the shell's `core_anchor`,
    # which described a layer seated on a surface it does not touch.
    for cid, side, sign in ((CORE_PARTS[0], "front", 1.0), (CORE_PARTS[1], "rear", -1.0)):
        insert_cid = INSERT_PARTS[0] if sign > 0 else INSERT_PARTS[1]
        gem_cid = GEM_PARTS[0] if sign > 0 else GEM_PARTS[1]
        comps.append(component(
            cid, f"Dark core triangle, {side} skin", "meso", insert_cid, "darkCoreMaterial",
            "extrude", "conforming-shell",
            f"The {side} film of the dark core: the same skin thickness again, seated on the insert's {side} face, so the two stack and the order cannot invert.",
            role="core", confidence=0.75, material_class="plastic",
            parent_socket=f"core_seat_{side}", child_socket="seat_anchor",
            contact_type="seated", contact_normal=(0.0, 0.0, sign),
            overlap=built_box(cid)[0][0], gap_tolerance=0.002,
            attachment_note=(
                "Seated on the insert's outer face, one SKIN_STEP out. Signed seat clearance "
                "-0.0362 ... +0.0404 normalized units against a 0.20 bound "
                "(artifacts/ultima-v2/full/parts.json, stackConformity)."
            ),
            sockets=[("seat_anchor", A_CORE_SEAT[sign])],
            joints=[
                joint(
                    "gemStandsOnCore", "seated-under", gem_cid,
                    "Over Y = 55...97 this film is the surface the stone is seated on, and the "
                    "stone's whole rhombus outline has to clear it — a different question from "
                    "clearing the shell, and the one that was never asked until 2026-08-08.",
                    socket_ref="seat_anchor", peer_socket_ref="culet_anchor",
                    derived_from="bladeStackTop(x, y) -> GEM_GIRDLE_DEPTH",
                    asserted_by="measure_relief_visibility.py — gem proud of the DARK CORE >= 95%",
                    measured="100.0% front / 100.0% rear "
                             "(artifacts/ultima-v2/gate/relief-visibility.json)",
                ),
            ],
            local_features=[
                feature("thinWedge", "ridge", f"Narrow centred upward triangle, two points only: [{CORE_BASE_Y:.0f}, {CORE_HALF_WIDTH:.0f}] to [{CORE_APEX_Y:.0f}, 0]. It never widens into a central panel and it carries no knee."),
                feature("reliefStep", "ridge", f"Second skin: a further {SKIN_STEP_T:.2f} T of film over the insert, so the PAIR spans {RELIEF_T['darkCoreTriangle']:.2f} T."),
                feature("conformingUnderside", "seam", f"The underside sits ON the insert's {side} face; the pair never reaches Z=0, which is what makes it a skin rather than a boss."),
                feature("girdledRim", "bevel", "The rim carries a girdle derived from the surface under it, so the outline clears that surface and not just the plateau."),
            ],
        ))
    # The diamond is the one BODY on the blade and the only inner layer still cut on Z=0: it is a
    # stone set through the jaws, seated on top of the two skins, not a film laid over them.
    for cid, side, sign in ((GEM_PARTS[0], "front", 1.0), (GEM_PARTS[1], "rear", -1.0)):
        core_cid = CORE_PARTS[0] if sign > 0 else CORE_PARTS[1]
        comps.append(component(
            cid, f"Root diamond gem, {side} half", "meso", "bladeGroup", "rootGemMaterial",
            "lathe", "assembled-solid",
            f"The {side} half of a four-sided column carrying a four-sided pyramidal cap, seated on the stack and closed underneath by the surface it is mounted on; low-poly flat facets, elongated 2.5:1 along Y.",
            role="ornament", confidence=0.8, material_class="glass",
            parent_socket="gem_mount_anchor", child_socket="culet_anchor",
            contact_type="seated", contact_normal=(0.0, 0.0, sign),
            overlap=built_box(cid)[0][0], gap_tolerance=0.002,
            attachment_note=(
                "The stone's culet is the jaws' own meeting point on the axis. Its underside is "
                "`bladeStackTop` evaluated pointwise INCLUDING that surface's step at Y = 55, so "
                "the seat has a ledge where the films' base is. Signed seat clearance "
                "-0.0906 ... +0.1297 normalized units against a 0.20 bound "
                "(artifacts/ultima-v2/full/parts.json, stackConformity)."
            ),
            sockets=[
                ("culet_anchor", A_BASE),
                ("waist_left", A_WAIST[-1.0]),
                ("waist_right", A_WAIST[1.0]),
            ],
            joints=[
                joint(
                    "gemSeatedOnCore", "seated", core_cid,
                    "The stone grows out of the dark core's outer face where the two overlap, and "
                    "out of the bare crystal below the films' base line.",
                    socket_ref="culet_anchor", peer_socket_ref="seat_anchor",
                    derived_from="GEM_GIRDLE_DEPTH = bladeStackTop(17, 55) + GEM_RELIEF_STEP",
                    asserted_by="check_centerline.py — the stone's step over the last skin >= 0.25 T",
                    measured="lift 0.3852 T above the shell's crest "
                             "(artifacts/ultima-v2/full/parts.json)",
                ),
            ] + [
                joint(
                    f"gemLowerEdgeIs{jaw}JawEdge", "coplanar-edge", f"crystalClamp{jaw}",
                    "The jaw's inner upper edge IS this stone's own lower edge over its whole "
                    "length, waist to culet: edge to edge, no gap and no overlap.",
                    socket_ref=f"waist_{jaw.lower()}", peer_socket_ref=f"gem_edge_{jaw.lower()}",
                    derived_from="CLAMP_OUTLINE[0] = (GEM_HALF_WIDTH, GEM_WAIST_Y), [1] = (0, GEM_BASE_Y)",
                    asserted_by="audit_records.py — the jaw's inner edge against the gem's at 65 heights",
                    measured="max |gem - jaw| = 0.000000000 "
                             "(recomputed by audit_records.py from createUltimaWeaponV2Model.ts)",
                ) for jaw in ("Left", "Right")
            ],
            local_features=[
                feature("waistGirdle", "ridge", f"The rhombus waist sits at Y={GEM_WAIST_Y:.0f}, level with the clamp jaws' contact line."),
                feature("reliefStep", "ridge", f"The blade's one raised body: {RELIEF_T['rootDiamondGem']:.2f} T for the pair. Its rim is DERIVED to stand 0.12 T outside the two skins at every station, and its point a further 0.38 of its own half-width above that rim, so the whole rhombus outline reads from the front AND the rear."),
                feature("crestFacets", "bevel", "Four cap facets running the WHOLE half-width to a point on the axis — a 尖頂 on a 柱身, not a plateau with a chamfer drawn on it."),
                feature("seatedUnderside", "seam", f"A surface, not a plane: the {side} half closes underneath on `bladeStackTop` evaluated at each ring point, so no part of the stone runs through the crystal's middle."),
                feature("facetSplit", "bevel", "The front splits into a lighter and a darker facet along the vertical axis."),
            ],
        ))
    comps.append(component(
        "hiltGroup", "Hilt group", "macro", "ultimaWeaponV2Root", "guardSteelMaterial",
        "box", "assembled-solid",
        "A mechanical assembly of separate rigid fittings; nothing here is a continuous surface.",
        role="handle", confidence=0.9,
        parent_socket="guard_center_anchor", child_socket="hilt_group_origin",
        contact_type="frame", contact_normal=(0.0, 1.0, 0.0),
        overlap=GROUP_OVERLAP, gap_tolerance=0.0,
        attachment_note=(
            "A transform frame. The overlap is how far this assembly's own parts — the jaws, both "
            "arms and the upper rods — rise into the blade group's vertical span, read from the "
            "built manifest."
        ),
        # These used to hang off guardCore. With that bridge deleted the anchors belong to the
        # assembly itself, and all three of the ones on the guard's floor are the SAME world
        # point: the jaws meet the stone's culet there, the grip column's flat top lies on it,
        # and the shell's lowest edge is on the same plane.
        sockets=[
            ("hilt_group_origin", A_GUARD),
            ("jaw_mount_anchor", A_BASE),
            ("grip_anchor", A_BASE),
            ("driver_array_anchor", A_RADIATION),
        ],
    ))
    # The two jaws ARE the blade socket. There is no container group, no central socket component
    # and no bridge beneath them: the load path runs shell -> purple stack -> diamond -> these two
    # prisms -> their own flat floor -> the grip column's top face, with nothing inserted anywhere
    # along it.
    for side, sign in (("Left", -1.0), ("Right", 1.0)):
        low = side.lower()
        comps.append(component(
            f"crystalClamp{side}", f"Crystal clamp {side.lower()}", "macro", "hiltGroup", "clampMetalMaterial",
            "extrude", "assembled-solid",
            "A triangular metal prism of real thickness, extending equally front and rear. Not a thin front-facing plate.",
            # 0.60, up from the 0.55 the records carried while this file said 0.60. The artwork
            # still shows no clamp, but the outline is no longer free: TWO of its three vertices
            # are the measured stone's own vertices and the third's HEIGHT is the culet's. Only
            # the outer 34 is directed, and the user's sketch is authority for the triangle.
            role="guard", confidence=0.6,
            parent_socket="jaw_mount_anchor", child_socket="culet_anchor",
            contact_type="coplanar-edge", contact_normal=JAW_NORMAL[sign],
            overlap=round(_edge * U, 4), gap_tolerance=0.0,
            attachment_note=(
                "The jaw mounts on the stone's culet and its inner upper edge runs from there to "
                "the stone's waist vertex. The overlap is that shared edge's own length and the "
                "contact normal is the edge's own normal, both derived from CLAMP_OUTLINE."
            ),
            sockets=[
                ("culet_anchor", A_BASE),
                # ONE point, three jobs, so ONE socket: the shell's lowest corner (#15), this
                # jaw's outer floor vertex, and the connector arm's root (#17).
                (f"floor_outer_{low}", A_FLOOR[sign]),
                (f"gem_edge_{low}", A_WAIST[sign]),
            ],
            joints=[
                joint(
                    "jawFloorCarriesShell", "tile", "outerCrystalShell",
                    "This jaw's floor edge is half of the shell's own lowest edge; the two jaws' "
                    "floors laid end to end ARE that edge.",
                    socket_ref=f"floor_outer_{low}", peer_socket_ref=f"lower_contact_{low}",
                    derived_from="CLAMP_FLOOR_SPAN -> SHELL_STATIONS' base row (integration #15)",
                    asserted_by="check_centerline.py (equality), audit_records.py (#15)",
                    measured="shell.minY - clamp.minY = +0.000000 world "
                             "(artifacts/ultima-v2/full/parts.json)",
                ),
                joint(
                    "jawFloorCarriesGrip", "butt", "leatherGrip",
                    "The grip column's flat top lies FACE TO FACE on this floor, not between the "
                    "jaws: its top face reaches 11.087 in x and in z, inside a floor footprint of "
                    "+/-34 by +/-16, so no camera reaches the joint.",
                    socket_ref="culet_anchor", peer_socket_ref="top_anchor",
                    derived_from="GRIP_TOP_Y = CLAMP_FLOOR_Y (integration #16)",
                    asserted_by="audit_records.py — the plane clause and the footprint clause",
                    measured="13.000 vs 13.000; 11.087 in x and z inside +/-34.000 x +/-16.000 "
                             "(recomputed by audit_records.py from the built manifest)",
                ),
                joint(
                    f"jawEdgeIsGemEdge{side}", "coplanar-edge", GEM_PARTS[0],
                    "The inner upper edge IS the stone's own lower edge, waist to culet.",
                    socket_ref=f"gem_edge_{low}", peer_socket_ref=f"waist_{low}",
                    derived_from="CLAMP_OUTLINE[0] and [1], both read off the gem",
                    asserted_by="audit_records.py — 65 heights",
                    measured="max |gem - jaw| = 0.000000000",
                ),
                joint(
                    f"jawRoots{side}Arm", "butt", f"leatherConnector{side}",
                    "The arm's root cap's LOWER RIM is this jaw's outer floor vertex, and the "
                    "cap's whole diameter runs from there up the shell's lower taper.",
                    socket_ref=f"floor_outer_{low}", peer_socket_ref="root_rim_anchor",
                    derived_from="CONNECTOR_ROOT - CONNECTOR_RADIUS*(-sin a, cos a) = "
                                 "CLAMP_OUTLINE[2] (integration #17)",
                    asserted_by="audit_records.py — the arm's rim and rake, both recomputed",
                    measured="(34.000000, 13.000000) against the jaws' outer vertex "
                             "(34.000, 13.000); rake -49.3987 deg against the shell taper's "
                             "-49.3987 deg",
                ),
            ],
            local_features=[
                feature("jawInnerEdge", "contour", f"The inner upper edge IS the gem's own lower edge, ({GEM_HALF_WIDTH:.0f},{GEM_WAIST_Y:.0f}) to (0,{GEM_BASE_Y:.0f}): edge-to-edge contact with no gap and no overlap."),
                feature("jawBaseJoin", "seam", f"Both jaws meet at (0,{CLAMP_FLOOR_Y:.0f}) and their two floor edges tile end to end across -{CLAMP_OUTER_X:.0f}...{CLAMP_OUTER_X:.0f}. The shell's lowest edge is that same span, the grip column's flat top lies under it, and each arm's root is its outer corner."),
                feature("equalDepth", "contour", f"Half-depth {CLAMP_HALF_DEPTH:.0f}, centred on Z=0, deeper than the shell so the prism reads from both faces."),
            ],
        ))

    driver_specs = [
        ("driverLeftUpper", -1.0, "upper", 0),
        ("driverLeftLower", -1.0, "lower", 1),
        ("driverRightUpper", 1.0, "upper", 2),
        ("driverRightLower", 1.0, "lower", 3),
    ]

    for side, sign in (("Left", -1.0), ("Right", 1.0)):
        low = side.lower()
        comps.append(component(
            f"leatherConnector{side}", f"Leather connector {side.lower()}", "meso", f"crystalClamp{side}",
            "connectorLeatherMaterial", "cylinder", "assembled-solid",
            "A complete closed cylinder of constant radius, capped at both ends: the horizontal limb of the T. Not a beam, plate or open channel.",
            role="guard", confidence=0.65, material_class="fabric",
            parent_socket=f"floor_outer_{low}", child_socket="root_rim_anchor",
            contact_type="butt", contact_normal=ARM_AXIS[sign],
            overlap=2 * CONNECTOR_RADIUS * U, gap_tolerance=0.001,
            attachment_note=(
                "Integration #17, as amended on 2026-08-11. The jaw's outer vertex is the root "
                "cap's LOWER RIM, not its centre, and there is no inset: the cap's full diameter "
                "is the overlap and all of it runs from that corner UP the crystal's flank. "
                "Nothing of the arm hangs below the guard's floor any more; the open wedge the "
                "user's sketch draws is the space the raked arm leaves beside the grip column, "
                "not half a cap in mid-air."
            ),
            rotation=(0.0, 0.0, round(math.radians(CONNECTOR_RAKE_DEG if sign > 0
                                                   else 180 - CONNECTOR_RAKE_DEG), 4)),
            sockets=[
                # The cap's LOWER RIM, which is the jaw's outer vertex. The cap's CENTRE is the
                # component's own origin and is not a socket: nothing joins to it.
                ("root_rim_anchor", A_FLOOR[sign]),
                (f"spinner_anchor_{low}", A_SPINNER[sign]),
                # Where each rod's root cap is buried. These are the DERIVED points
                # `driverRootRadius()` solves for, and the rods' own anchors are the same points.
                (f"driver_seat_{low}_upper", A_DRIVER_ROOT[(sign, "upper")]),
                (f"driver_seat_{low}_lower", A_DRIVER_ROOT[(sign, "lower")]),
            ],
            joints=[
                joint(
                    f"arm{side}OnShellFlank", "flank-contact", "outerCrystalShell",
                    "The cap is perpendicular to an axis raked at the shell's own lower taper, so "
                    "its WHOLE diameter lies on that flank, from this corner outward.",
                    socket_ref="root_rim_anchor", peer_socket_ref=f"lower_contact_{low}",
                    derived_from="CONNECTOR_ANGLE_DEG = -atan((83 - 34) / (55 - 13))",
                    asserted_by="audit_records.py — the whole cap against the shell's edge",
                    measured="worst front-view residual 0.000005 over 65 samples",
                ),
            ] + [
                joint(
                    f"arm{side}Buries{band.capitalize()}Rod", "buried", f"driver{side}{band.capitalize()}",
                    "The rod's root cap is buried inside this arm — deep enough that the whole cap "
                    "rim clears the wall, never so deep that it reaches the arm's own axis.",
                    socket_ref=f"driver_seat_{low}_{band}", peer_socket_ref="root_cap_anchor",
                    derived_from="driverRootRadius(): the arm's INRADIUS pulled in by the rod's radius",
                    asserted_by="audit_records.py — recomputed, and the axis floor checked",
                    measured=(f"root at ({driver_root_point(1.0, band)[0]:.1f}, "
                              f"{driver_root_point(1.0, band)[1]:.1f}) "
                              "(recomputed by audit_records.py from createUltimaWeaponV2Model.ts)"),
                ) for band in ("upper", "lower")
            ] + [
                joint(
                    f"arm{side}SeatsSpinner", "buried", f"spinnerEnd{side}",
                    "The spinner's flat top ring is sunk inside this arm rather than capping it: "
                    "turning the piece vertical leaves the two end faces 40 degrees apart.",
                    socket_ref=f"spinner_anchor_{low}", peer_socket_ref="seat_anchor",
                    derived_from="spinnerSeat(): radius = sin|a|*inradius - clearance*(sin|a| + cos|a|)",
                    measured=(f"seat radius {_seat_r:.2f} at ({_seat_x:.2f}, {_seat_y:.2f}), "
                              f"clearing the leather by {SPINNER_SEAT_CLEARANCE:.1f} on every side"),
                ),
            ],
            local_features=[
                feature("closedCylinder", "contour", f"Constant radius {CONNECTOR_RADIUS:.0f}, {CONNECTOR_SIDES:.0f} radial segments, closed root and outer caps."),
                feature("connectorRake", "contour", f"Root cap's LOWER RIM on the jaw's outer corner ({CLAMP_OUTER_X:.0f}, {CLAMP_FLOOR_Y:.0f}), its centre one radius up the cap's own normal at ({CONNECTOR_ROOT[0]:.3f}, {CONNECTOR_ROOT[1]:.3f}), raked {CONNECTOR_RAKE_DEG:.4f} degrees, which is the shell's own lower taper as an angle — so the cap's WHOLE diameter lies ON the crystal's lower slanted flank rather than behind it, and none of it hangs below the guard's floor."),
                feature("driverSeat", "seam", "The rods' root caps are buried in this surface; there is no socket component between them."),
            ] if side == "Right" else [],
        ))
        comps.append(component(
            f"spinnerEnd{side}", f"Spinner end {side.lower()}", "meso", f"leatherConnector{side}",
            "guardGoldMaterial", "lathe", "assembled-solid",
            "A compact faceted spinning top hanging VERTICALLY, on the pommel's axis rather than the connector's, truncated BLUNT. Never a needle point, never a hanging paddle.",
            # 0.70, up from 0.65: nothing about this piece is inferred from reference 03 any more.
            # Its DIRECTION is measured (de-rotated upright, both caps read within ~12 deg of
            # straight down), its per-row half-widths are the crop's own, and its seat is derived
            # in closed form from the arm. Only the six-sided lathe is directed.
            role="guard", confidence=0.7,
            parent_socket=f"spinner_anchor_{low}", child_socket="seat_anchor",
            contact_type="buried", contact_normal=(0.0, -1.0, 0.0),
            embed_depth=SPINNER_SEAT_CLEARANCE * U, overlap=round(2 * _seat_r * U, 4),
            gap_tolerance=round(SPINNER_SEAT_CLEARANCE * U, 4),
            attachment_note=(
                "The only joint on the model closed by BURIAL rather than by two faces meeting: "
                "the top ring is horizontal and the arm's end cap is raked, so they cannot mate. "
                "The embed depth is the clearance the ring keeps inside the leather on every side."
            ),
            rotation=(0.0, 0.0, 0.0),
            sockets=[("seat_anchor", A_SPINNER[sign])],
            local_features=[
                feature("buriedSeat", "seam", f"The top ring is sunk INSIDE the connector rather than capping it. Turning the piece vertical leaves its horizontal top ring 40 degrees off the arm's raked end cap, so the two can no longer meet flush; the ring is instead seated on the arm's own axis at a radius solved from the prism's inradius, clearing the leather by {SPINNER_SEAT_CLEARANCE:.1f} units on every side and from every camera."),
                feature("bluntTruncation", "contour", f"Radius {_seat_r:.2f} at the buried seat, {SPINNER_TOP_RADIUS:.1f} at the shoulder {SPINNER_SHOULDER_DROP:.1f} below it, then ONE STRAIGHT LINE down to a blunt truncation at {SPINNER_BOTTOM_RADIUS:.1f} on Y={SPINNER_BOTTOM_Y:.1f} — never a point, and never wider lower down. Both caps in the crop are straight-sided to within one source pixel and neither widens downward by as much as one; spec/spinner-taper.json."),
            ] if side == "Right" else [],
        ))

    comps.append(component(
        "driverArray", "Driver array", "macro", "hiltGroup", "driverMaterial",
        "box", "assembled-solid",
        "A transform host for four instances of one rigid rod; it owns no surface of its own.",
        # 0.85, down from 0.90 and now agreeing with the confidence report: the arrangement is
        # measured (four PCA axes, a common radiation centre, endpoint radius) but the rods' own
        # circular section is directed, and this node stands for the array as a whole.
        role="mechanism", confidence=0.85,
        parent_socket="driver_array_anchor", child_socket="radiation_centre_anchor",
        contact_type="frame", contact_normal=(0.0, 1.0, 0.0),
        overlap=0.0, gap_tolerance=0.0,
        attachment_note=(
            "A transform frame on the radiation centre. The rods it holds make their real joint "
            "with the CONNECTOR ARMS, not with this node — see each rod's `joints`."
        ),
        sockets=[("radiation_centre_anchor", A_RADIATION)] + [
            (f"driver_root_{'left' if s < 0 else 'right'}_{b}", A_DRIVER_ROOT[(s, b)])
            for s in (-1.0, 1.0) for b in ("upper", "lower")
        ],
        local_features=[
            feature("radiationCentre", "seam", f"All four axes converge at (0, {DRIVER_RADIATION_CENTRE[1]:.0f}), below the guard centre rather than at it."),
        ],
    ))
    for cid, sign, band, index in driver_specs:
        side = "left" if sign < 0 else "right"
        elev = math.radians(DRIVER_ELEVATION[band])
        comps.append(component(
            cid, f"Driver {index}", "meso", "driverArray", "driverMaterial",
            "cylinder", "assembled-solid",
            "A faceted cylinder with a real circular section, not a rectangular prism: eight radial segments, one shared unit geometry placed by four transforms whose X scale carries the length.",
            role="mechanism", confidence=0.82,
            parent_socket=f"driver_root_{side}_{band}", child_socket="root_cap_anchor",
            contact_type="buried", contact_normal=(sign * math.cos(elev), math.sin(elev), 0.0),
            embed_depth=DRIVER_JOINT_OVERLAP * 2 * DRIVER_RADIUS * U,
            overlap=2 * DRIVER_RADIUS * U, gap_tolerance=0.001,
            attachment_note=(
                "The rod hangs off the array for transform purposes and is BURIED in its "
                "connector arm for structural ones. The embed depth is the anti-gap margin ON TOP "
                "of the burial `driverRootRadius()` derives; the overlap is the cap's own diameter."
            ),
            rotation=(0.0, 0.0, round(elev if sign > 0 else math.pi - elev, 4)),
            sockets=[("root_cap_anchor", A_DRIVER_ROOT[(sign, band)])],
            joints=[
                joint(
                    f"rod{index}InArm", "buried", f"leatherConnector{'Left' if sign < 0 else 'Right'}",
                    "The structural host: the root cap sits inside the arm's leather, on the "
                    "surface that is the arm's inradius pulled in by this rod's own radius.",
                    socket_ref="root_cap_anchor", peer_socket_ref=f"driver_seat_{side}_{band}",
                    derived_from="driverRootRadius(DRIVER_ELEVATION_DEG['%s'])" % band,
                    asserted_by="audit_records.py — recomputed root, plus the connector-axis floor",
                    measured=(f"root at ({driver_root_point(1.0, band)[0]:.1f}, "
                              f"{driver_root_point(1.0, band)[1]:.1f}), length "
                              f"{DRIVER_RADIAL_END - driver_root_radius(DRIVER_ELEVATION[band]):.1f}"),
                ),
            ],
            local_features=[
                feature("rootCapOnConnector", "seam", "The root cap is buried inside the connector, deep enough that the whole cap rim clears the arm's wall and not merely its centre line, and never as deep as the connector's central axis."),
                feature("cappedEnd", "contour", "The outer end closes to 0.86 radius rather than ending open."),
            ] if index == 2 else [],
        ))

    comps.append(component(
        "leatherGrip", "Leather grip", "macro", "hiltGroup", "gripLeatherMaterial",
        "cylinder", "assembled-solid",
        "An eight-sided shaft of ONE constant width from top to bottom; the wrap is banding on the same shaft, not added ring geometry. One mesh, not a shaft plus a fitting.",
        role="handle", confidence=0.85, material_class="fabric",
        parent_socket="grip_anchor", child_socket="top_anchor",
        contact_type="butt", contact_normal=(0.0, -1.0, 0.0),
        overlap=round(2 * GRIP_REACH, 4), gap_tolerance=0.0,
        attachment_note=(
            "Integration #16: face to face on the jaws' floor, GRIP_TOP_Y being CLAMP_FLOOR_Y "
            "itself. Embed depth zero — a burial is as wrong as a gap here — and the overlap is "
            "the column's own top face, which the floor's +/-34 x +/-16 footprint covers entirely."
        ),
        sockets=[("top_anchor", A_BASE), ("pommel_anchor", A_GRIP_BOTTOM)],
        joints=[
            joint(
                f"gripTopOn{side}Jaw", "butt", f"crystalClamp{side}",
                "The column's flat top lies on this jaw's floor, parallel and touching; it is not "
                "inserted between the jaws and they do not close on its flanks.",
                socket_ref="top_anchor", peer_socket_ref="culet_anchor",
                derived_from="GRIP_TOP_Y = CLAMP_FLOOR_Y (integration #16)",
                asserted_by="audit_records.py — plane equality plus the footprint clause",
                measured="13.000 vs 13.000; 11.087 in x and z inside +/-34.000 x +/-16.000",
            ) for side in ("Left", "Right")
        ],
        local_features=[
            feature("clampedTang", "seam", f"The column's flat top lies FACE TO FACE on the two jaws' floor at Y={GRIP_TOP_Y:.0f}, parallel and touching; it is not inserted between them and they do not close on its flanks. Its top face reaches {GRIP_REACH / U:.3f} in x and in z, inside a floor footprint of +/-{CLAMP_OUTER_X:.0f} by +/-{CLAMP_HALF_DEPTH:.0f}, so no camera reaches it."),
            feature("tangReach", "contour", f"No tang and no widening: half-width {GRIP_HALF_WIDTH:.0f} at the top face, the same as everywhere else on the shaft."),
            feature("constantWidth", "contour", f"Half-width {GRIP_HALF_WIDTH:.0f} from the jaws' floor at Y={GRIP_TOP_Y:.0f} to its measured lower edge at {GRIP_BOTTOM_Y:.0f}: no waist, no T."),
            feature("wrapBanding", "gloss", "Nine wrap bands as vertex-colour value steps; zero protruding ring meshes."),
            feature("noCollar", "seam", "No collar, ring or band anywhere on the shaft; the leather's own end cap meets the pommel's base ring in the same plane."),
        ],
    ))
    comps.append(component(
        "pointedMetalPommel", "Pointed metal pommel", "macro", "leatherGrip", "pommelGoldMaterial",
        "cone", "assembled-solid",
        "One straight cone: base ring on the leather's lower edge, apex at the measured tip. No collar above it and never merged into the leather.",
        role="pommel", confidence=0.8,
        parent_socket="pommel_anchor", child_socket="top_anchor",
        contact_type="butt", contact_normal=(0.0, -1.0, 0.0),
        overlap=round(2 * GRIP_REACH, 4), gap_tolerance=0.0,
        attachment_note=(
            "The cone's base ring IS the column's bottom ring — same plane, same circumradius, "
            "same facet count, compared vertex for vertex by tests/ultima-v2-solid.test.mjs — so "
            "the overlap is that whole shared ring and the gap tolerance is zero, not small."
        ),
        sockets=[("top_anchor", A_GRIP_BOTTOM)],
        local_features=[
            feature("straightCone", "contour", f"A single straight taper from circumradius {POMMEL_RADIUS:.0f} at Y={GRIP_BOTTOM_Y:.0f} to a point at Y={POMMEL_TIP_Y}: no belly and no waist."),
            feature("sharedBaseRing", "seam", f"POMMEL_RADIUS is GRIP_HALF_WIDTH and POMMEL_SIDES is the column's {POMMEL_SIDES:.0f}, so the base ring is not a second number: the two rings are identical vertex for vertex and the joint cannot open."),
        ],
    ))
    spec["componentTree"] = comps

    # --- repetition system -------------------------------------------------
    spec["repetitionSystems"] = [
        {
            "id": "driverArray",
            "componentRefs": [cid for cid, *_ in driver_specs],
            "count": 4,
            "distribution": (
                "Radial, MIRROR-symmetric about the blade axis, two per side. Elevations are the "
                "measured left/right pair means; the 5-7 degree per-side gap in the crop is camera "
                "yaw, not authored asymmetry (U6)."
            ),
            "parameters": {
                "radiationCenter": [0.0, DRIVER_RADIATION_CENTRE[1] * U, 0.0],
                "anglesDegFromPlusX": {
                    "driverRightUpper": DRIVER_ELEVATION["upper"],
                    "driverRightLower": DRIVER_ELEVATION["lower"],
                    "driverLeftUpper": 180.0 - DRIVER_ELEVATION["upper"],
                    "driverLeftLower": 180.0 - DRIVER_ELEVATION["lower"],
                },
                # Derived by `driver_root_radius()`, the same closed form `driverRootRadius()`
                # uses. It used to be a two-entry literal table (75.3 / 77.8) that had been the
                # arm's OUTER-surface solution and stayed here for two passes after the factory
                # moved to the inradius; the spec described rods 9 units too long.
                "radialStartByBand": {b: round(driver_root_radius(DRIVER_ELEVATION[b]) * U, 4)
                                      for b in ("upper", "lower")},
                "radialEnd": DRIVER_RADIAL_END * U,
                "crossSection": "faceted cylinder, 8 radial segments — not a rectangular prism",
                "radius": DRIVER_RADIUS * U,
                "sides": 8,
                "attachment": (
                    "Root cap lands on the leather connector's outer surface; no socket component "
                    "exists. The two bands need different lengths because their axes meet the same "
                    "cylinder at different distances, so the shared geometry is a unit cylinder and "
                    "the length lives in each transform's X scale."
                ),
                "measurement": (
                    "PCA axes of the four red connected components: right_upper 40.7 deg, "
                    "left_upper 45.9 deg, right_lower 21.6 deg, left_lower 29.1 deg. Both axis "
                    "families cross X=0 at Y=-62 within 6 units of each other."
                ),
            },
            "sharedGeometry": True,
            "evidenceRefs": ["full-object"],
        }
    ]

    # --- feature review targets --------------------------------------------
    spec["featureReviewTargets"] = [
        {
            # NOT "fully inset" any more: the correction pass that produced this build overrides
            # every earlier instruction that buried the inner crystals inside the pale shell.
            "id": "blade-layer-stack", "name": "Two conforming skins under one raised stone: lifts 0.05 / 0.10 / 0.385 T above the shell's crest, mirrored front and rear",
            "tier": "critical", "passIds": ["blockout", "structural-pass"], "minimumScore": 0.8, "mustPass": True,
            "componentRefs": ["outerCrystalShell", *INSERT_PARTS, *CORE_PARTS, *GEM_PARTS],
            "evidenceRefs": ["full-object"],
        },
        {
            "id": "driver-quad-array", "name": "Exactly four drivers in two mirrored pairs",
            "tier": "critical", "passIds": ["blockout", "structural-pass"], "minimumScore": 0.85, "mustPass": True,
            "componentRefs": ["driverArray"] + [cid for cid, *_ in driver_specs],
            "evidenceRefs": ["full-object"],
        },
        {
            "id": "driver-socket-insertion",
            "name": "Cylindrical rods whose root caps land on the connector surface, with no socket meshes",
            "tier": "critical", "passIds": ["structural-pass", "form-refinement"], "minimumScore": 0.8,
            "mustPass": True,
            "componentRefs": ["driverArray", "leatherConnectorLeft", "leatherConnectorRight"]
            + [cid for cid, *_ in driver_specs],
            "evidenceRefs": ["full-object"],
        },
        {
            "id": "crystal-clamp-mount",
            "name": "Two mirrored jaws cradle the diamond and land on the socket's shoulders",
            "tier": "critical", "passIds": ["structural-pass", "form-refinement"], "minimumScore": 0.78,
            "mustPass": True,
            "componentRefs": ["crystalClampLeft", "crystalClampRight", *GEM_PARTS],
            "evidenceRefs": ["full-object"],
        },
        {
            "id": "hilt-proportion-system", "name": "Blade : grip : pommel proportion system",
            "tier": "critical", "passIds": ["blockout"], "minimumScore": 0.8, "mustPass": True,
            "componentRefs": ["outerCrystalShell", "leatherGrip", "pointedMetalPommel"],
            "evidenceRefs": ["full-object", "reference-03-front"],
        },
        {
            "id": "shell-sharpened-profile", "name": "Only the shell is sharpened; the insert stays blunt",
            "tier": "critical", "passIds": ["form-refinement"], "minimumScore": 0.8, "mustPass": True,
            "componentRefs": ["outerCrystalShell", *INSERT_PARTS],
            "evidenceRefs": ["full-object"],
        },
        {
            "id": "guard-compactness", "name": "Compact raked guard subordinate to blade and drivers",
            "tier": "important", "passIds": ["structural-pass", "form-refinement"], "minimumScore": 0.75,
            "componentRefs": ["leatherGrip", "leatherConnectorLeft", "leatherConnectorRight", "spinnerEndLeft", "spinnerEndRight"],
            "evidenceRefs": ["full-object"],
        },
        {
            "id": "connector-leather-reading",
            "name": "The arms under the drivers read as dark grey leather, not black metal",
            "tier": "important", "passIds": ["surface-pass"], "minimumScore": 0.72,
            "componentRefs": ["leatherConnectorLeft", "leatherConnectorRight"],
            "evidenceRefs": ["full-object"],
        },
        {
            "id": "grip-pommel-stack",
            "name": "Constant-width grip, no collar, independent conical pommel",
            "tier": "important", "passIds": ["form-refinement", "interaction-pass"], "minimumScore": 0.75,
            "componentRefs": ["leatherGrip", "pointedMetalPommel"],
            "evidenceRefs": ["full-object"],
        },
        {
            "id": "gem-dimensionality", "name": "Root gem reads as a dimensional crystal, not a flat arrow",
            "tier": "important", "passIds": ["form-refinement", "material-pass"], "minimumScore": 0.75,
            "componentRefs": [*GEM_PARTS], "evidenceRefs": ["full-object"],
        },
        {
            "id": "layer-material-separation", "name": "Nine measured material zones stay separable",
            "tier": "critical", "passIds": ["material-pass", "surface-pass"], "minimumScore": 0.78, "mustPass": True,
            "componentRefs": ["outerCrystalShell", *INSERT_PARTS, *GEM_PARTS, "crystalClampRight", "driverArray", "leatherConnectorRight", "leatherGrip"],
            "evidenceRefs": ["full-object"],
        },
        {
            "id": "lowpoly-facet-language", "name": "PS1 planar facet language preserved",
            "tier": "important", "passIds": ["material-pass", "surface-pass", "optimization-pass"], "minimumScore": 0.7,
            "componentRefs": ["ultimaWeaponV2Root"], "evidenceRefs": ["full-object"],
        },
        {
            "id": "transparency-sort-order", "name": "Crystal layers sort deterministically from every review view",
            "tier": "important", "passIds": ["material-pass", "lighting-pass"], "minimumScore": 0.7,
            "componentRefs": ["outerCrystalShell", *INSERT_PARTS, *GEM_PARTS],
            "evidenceRefs": ["full-object"],
        },
        {
            "id": "runtime-part-exposure", "name": "All eight public part types stay independently selectable",
            "tier": "important", "passIds": ["interaction-pass", "optimization-pass"], "minimumScore": 0.7,
            "componentRefs": ["ultimaWeaponV2Root", "driverArray"], "evidenceRefs": ["full-object"],
        },
    ]

    # --- passes ------------------------------------------------------------
    pass_refs = {
        # The drivers are in the blockout: they carry about a tenth of the macro silhouette,
        # and holding them back capped the blockout gate at IoU 0.65 against a 0.85 threshold.
        "blockout": ["ultimaWeaponV2Root", "bladeGroup", "outerCrystalShell", "hiltGroup", "leatherConnectorLeft", "leatherConnectorRight", "spinnerEndLeft", "spinnerEndRight", "driverArray", "leatherGrip", "pointedMetalPommel"],
        "structural-pass": [*INSERT_PARTS, *CORE_PARTS, *GEM_PARTS, "crystalClampLeft", "crystalClampRight"]
        + [cid for cid, *_ in driver_specs],
        "form-refinement": ["outerCrystalShell", *INSERT_PARTS, *GEM_PARTS, "crystalClampLeft", "crystalClampRight", "spinnerEndLeft", "spinnerEndRight", "leatherGrip", "pointedMetalPommel"],
        "material-pass": [c["id"] for c in comps],
        "surface-pass": [c["id"] for c in comps],
        "lighting-pass": ["ultimaWeaponV2Root"],
        "interaction-pass": ["ultimaWeaponV2Root", "driverArray"],
        "optimization-pass": [c["id"] for c in comps],
    }
    pass_goals = {
        "blockout": (
            f"Match the measured silhouette: tip at Y={TIP_Y:.0f}, shoulder half-width "
            f"{SHELL_MAX_HALF_WIDTH:.0f} at Y={SHELL_SHOULDER_Y:.0f}, converging trapezoid down to "
            f"the jaws' own outer vertex at (+/-{CLAMP_OUTER_X:.0f}, {CLAMP_FLOOR_Y:.0f}), grip end "
            f"at Y={GRIP_BOTTOM_Y:.0f}, pommel tip at Y={POMMEL_TIP_Y:.1f}."
        ),
        "structural-pass": (
            "Place every public part type and every declared anchor: the four rods seated directly "
            "in the two connector arms, both clamp jaws, and no socket mesh anywhere — "
            "`centralGripSocket`, `driverSocket*`, `gripEndCollar` and `guardCore` are all forbidden."
        ),
        "form-refinement": "Cut the shell's ridge, edge bevels and converging neck; keep the insert blunt; facet the gem, the jaws and the spinner ends.",
        "material-pass": "Apply the nine measured material zones and their gradients without inventing surface relief.",
        "surface-pass": "Verify per-face value steps read as flat facets from every review view.",
        "lighting-pass": "Soft upper-left key on a white background; no bloom that would hide the silhouette.",
        "interaction-pass": "Expose the eight part types plus the four driver instances as named, selectable nodes.",
        "optimization-pass": "Hold the triangle budget while keeping every authored plane; no silhouette-changing decimation.",
    }
    for build_pass in spec["buildPasses"]:
        pid = build_pass["id"]
        build_pass["componentRefs"] = pass_refs.get(pid, ["ultimaWeaponV2Root"])
        build_pass["goal"] = pass_goals.get(pid, build_pass["goal"])

    spec["qualityTargets"]["targetFidelity"] = 0.78
    spec["qualityTargets"]["reviewViewpoints"] = ["artwork-match", "front", "side", "three-quarter", "rear"]
    spec["qualityContract"]["minimumSpecDepth"]["materialLayers"] = 9
    spec["qualityContract"]["definitionOfDone"] = [
        "Silhouette IoU against the authority crop >= 0.90 from the artwork-match camera.",
        "Tip, guard centre, gem centre, grip end, and all four driver endpoints within 2.5% of image height.",
        "Blade-to-hilt length ratio error <= 3%.",
        "Exactly four drivers and exactly four blade parts.",
        "The shell reads as sharpened and the insert as blunt from the form-refinement pass onward.",
        # The correction pass's own acceptance criteria, each one mechanically checked rather
        # than eyeballed: the first three by check_centerline.py against the built parts.json,
        # the fourth by audit_records.py against the factory's own stations.
        "Relief ladder, as LIFT above the shell's own crest: each skin steps 0.035-0.060 T over the layer under it and the diamond steps at least 0.25 T over the last skin, where T is the shell's own total depth.",
        "Every blade layer's Z bounds centre on 0 within 0.001 world units — no front-only extrusion.",
        "The shell's base half-width equals the clamps' outer edge at that height, and no pale geometry exists below the jaws.",
        "Front-view gap between the shell and every driver >= 0.75 driver diameters, target 1.00.",
    ]

    spec["lightingFromPhoto"] = [
        {
            "role": "key",
            "type": "directional",
            "direction": [-0.42, 0.62, 0.66],
            "color": "#FFFFFF",
            "intensity": 1.05,
            "evidence": (
                "The shell's upper-left face is the brightest region (#E6E7F2) and its lower-right edge "
                "the darkest (#B5B6BF); the gold caps light on their upper-outer planes. Key sits "
                "front-upper-left."
            ),
        },
        {
            "role": "fill",
            "type": "hemisphere",
            "skyColor": "#EDEDF6",
            "groundColor": "#BFC0CC",
            "intensity": 0.55,
            "note": (
                "The source is vertex-lit and near-uniform inside each facet; a hemisphere fill keeps "
                "the facet value steps readable instead of crushing one side to black."
            ),
        },
        {
            "role": "environment",
            "type": "ambient",
            "color": "#9EA0AE",
            "intensity": 0.22,
            "note": (
                "No rim light exists in the reference. Low ambient replaces it; adding a rim would "
                "invent a specular event the 1997 asset never had."
            ),
        },
        {
            "role": "rendering",
            "exposure": 1.0,
            "toneMapping": "LinearToneMapping — ACES filmic desaturates the violet insert and the magenta gem",
            "background": "#FFFFFF for the artwork-match view; transparent for the exploded and overlay renders",
            "note": (
                "Contact shadow and ambient occlusion are limited to the jaws' own contacts, the "
                "buried driver roots, the grip column's top face and the pommel joint. No ground "
                "shadow: the reference floats on white."
            ),
        },
    ]
    spec["lookDevTargets"] = {
        "reviewBackground": "#FFFFFF",
        "keyDirection": [-0.42, 0.62, 0.66],
        "note": "Soft upper-left key that reveals crystal facets without bloom that would hide the silhouette.",
    }

    spec["risks"] = [
        "Transparency sorting between the shell, insert, and gem can invert at grazing angles; fixed render order plus physical Z spacing is required.",
        "The dark core triangle's base half-width is still directed rather than measured: below the gem's apex the gem's own rim-dark shading shares the crop's dark run, so no threshold can separate the two. The apex above it is measured.",
        "The side view is a thin slab by design and will trip a degenerate-view gate; adding depth to pass that gate would invent geometry the reference does not support.",
    ]

    SPEC_PATH.write_text(json.dumps(spec, indent=2) + "\n")
    INVENTORY_PATH.write_text(json.dumps({"detailInventory": build_detail_inventory()}, indent=2) + "\n")
    print(f"wrote {SPEC_PATH}")
    print(f"components={len(comps)} materials={len(spec['materials'])} details={len(DETAILS)}")
    print(f"measured tilt={measurements['artworkTiltDeg']} deg")


if __name__ == "__main__":
    main()
