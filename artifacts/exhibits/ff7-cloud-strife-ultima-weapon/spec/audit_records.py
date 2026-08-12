#!/usr/bin/env python3
"""Cross-check every figure quoted in this exhibit's records against the built artifacts.

The records are long and they cite each other, which is exactly how a number drifts: someone
corrects the model, updates one report, and the other three keep quoting the old value. Three
figures had already forked this way (the per-part delta-E existed as 58.9, 62.3 and 58.61
simultaneously) before this script was written.

So: every figure comes from an artifact or from the factory source, never from another document.

    python3 artifacts/exhibits/ff7-cloud-strife-ultima-weapon/spec/audit_records.py

Exit 1 with the offending file, line and text if any document quotes a retired figure.
"""
import json, math, re, sys
from pathlib import Path

# V is this exhibit's evidence dir under artifacts/; the code it audits lives under src/.
# The two were one directory until the 2026-08-12 split, which is why every V-relative path
# below points at spec output and every ROOT-relative one points at source.
V = Path(__file__).resolve().parent.parent
ROOT = V.parent.parent.parent
A = ROOT / "artifacts/ultima-v2"
FACTORY = ROOT / "src/utils/ultimaWeaponV2/createUltimaWeaponV2Model.ts"
fail: list[str] = []


SRC = FACTORY.read_text()


def const(pattern: str) -> float:
    """Read a scalar out of the factory, so the audit cannot drift from the code it checks."""
    m = re.search(pattern, SRC, re.M)
    if not m:
        raise SystemExit(f"{pattern!r} not found in {FACTORY.name} — the audit needs updating")
    return float(m.group(1))


# --- what actually built -----------------------------------------------------------------
parts = json.loads((A / "full" / "parts.json").read_text())
names = {p["name"] for p in parts["parts"]}
meshes = sum(1 for p in parts["parts"] if p["kind"] == "part")
tris = sum(p["triangles"] for p in parts["parts"] if p["kind"] == "part")
iou = f"{json.loads((V / 'spec' / 'silhouette-report.json').read_text())['iou']:.4f}"
# Only the material and surface passes are colour-gated; the blockout is untextured grey, so its
# own delta-E (69.35) is not a figure any document should be quoting.
de = max(
    json.loads((A / "gate" / f"tier1-{p}.json").read_text())["checks"]["colorDelta"]["maxDeltaE"]
    for p in ("material-pass", "surface-pass")
)
blockout_iou = json.loads((A / "gate" / "tier1-blockout.json").read_text())["checks"]["silhouetteIoU"]
front_rear_iou = f"{json.loads((A / 'front-rear-overlay.json').read_text())['iou']:.4f}"
# How much of each split relief actually stands in front of the shell, front face and rear face.
# The relief ladder proves depth; this is the only figure that proves the depth is visible.
visibility = json.loads((A / "gate" / "relief-visibility.json").read_text())
proud = {
    layer: [entry["pieces"][face]["proudPercent"] for face in ("front", "rear")]
    for layer, entry in visibility["layers"].items()
}
seated = {
    layer: [entry["pieces"][face]["proudPercent"] for face in ("front", "rear")]
    for layer, entry in visibility.get("seating", {}).items()
}

# --- the blade's relief ladder, as LIFT above the shell's own crest ------------------------
# Each inner layer's outermost surface against the shell's deepest point, in multiples of the
# shell's own built thickness. This is the quantity `check_centerline.py` asserts, recomputed
# here from the same artifact so no document can quote a ladder the build no longer has.
_pb = {p["name"]: p.get("bounds") for p in parts["parts"]}
_shell = _pb["outerCrystalShell"]
_T = _shell["maxZ"] - _shell["minZ"]
_ladder = ("purpleEnergyInsertFront", "darkCoreTriangleFront", "rootDiamondGemFront")
if any(n not in _pb for n in _ladder):
    # Stale artifacts, not a drifted document: say which, rather than raising a KeyError three
    # screens away from the cause.
    raise SystemExit(
        "parts.json is missing "
        f"{sorted(n for n in _ladder if n not in _pb)} — re-capture the renders before auditing"
    )
lifts = " / ".join(f"{(_pb[n]['maxZ'] - _shell['maxZ']) / _T:.4f}" for n in _ladder)

# --- the driver roots, recomputed exactly as driverRootRadius() does ------------------------
# Each rod's root cap is buried inside the connector, on the FAR crossing of the surface that is
# the arm's inradius offset inward by the rod's radius — the cap is a disc standing in Z, so
# solving against the outer surface leaves its rim proud of the leather. Not a typed-in
# coordinate: change the connector and these move.
CX = const(r"^const CONNECTOR_ROOT.*= \[(-?[\d.]+)")
CY = const(r"^const CONNECTOR_ROOT.*= \[-?[\d.]+, (-?[\d.]+)")
angle = const(r"^const CONNECTOR_ANGLE_DEG = (-?[\d.]+)")
radius = const(r"^const CONNECTOR_RADIUS = (-?[\d.]+)")
sides = const(r"^const CONNECTOR_SIDES = (-?[\d.]+)")
centre_y = const(r"^const DRIVER_CENTRE.*= \[-?[\d.]+, (-?[\d.]+)")
rod_r = const(r"^const DRIVER_RADIUS = (-?[\d.]+)")
overlap = const(r"^const DRIVER_JOINT_OVERLAP = (-?[\d.]+)")
cap_surface = math.sqrt((radius * math.cos(math.pi / sides)) ** 2 - rod_r ** 2)
roots = {}
for band, elev in (("upper", const(r"DRIVER_ELEVATION_DEG = \{ upper: (-?[\d.]+)")),
                   ("lower", const(r"DRIVER_ELEVATION_DEG = \{.*lower: (-?[\d.]+)"))):
    e, a = math.radians(elev), math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    k0 = (0 - CX) * dy - (centre_y - CY) * dx
    k1 = math.cos(e) * dy - math.sin(e) * dx
    r = max((cap_surface - k0) / k1, (-cap_surface - k0) / k1) - overlap * 2 * rod_r
    roots[band] = (r * math.cos(e), centre_y + r * math.sin(e))
    # The rod must stay clear of the connector's own axis even fully buried.
    axis_floor = min((0 - k0) / k1, (-0 - k0) / k1)
    if r <= axis_floor:
        fail.append(f"{band} driver root r={r:.1f} reaches the connector axis at {axis_floor:.1f}")

print(f"BUILT   nodes={len(names)} meshes={meshes} tris={tris} IoU={iou} "
      f"blockoutIoU={blockout_iou} maxDeltaE={de} frontRearIoU={front_rear_iou}")
for layer, (f, r) in proud.items():
    print(f"BUILT   {layer} stands proud of the shell over {f}% front / {r}% rear")
for layer, (f, r) in seated.items():
    under = visibility["seating"][layer]["under"]
    print(f"BUILT   {layer} stands proud of {under} over {f}% front / {r}% rear")
print(f"BUILT   blade lift ladder (insert / core / gem, T-multiples above the shell) {lifts}")
for band, (x, y) in roots.items():
    print(f"DERIVED {band} driver root at ({x:.1f}, {y:.1f})")

# --- front-view clearance between the pale shell and each red driver -----------------------
# The correction spec forbids the shell touching or nearly touching a driver, and this is the
# one acceptance criterion with no other mechanical home: part bounds are axis-aligned boxes and
# would report an overlap across the whole guard where there is in fact clear space.
#
# So the shell's own station table is read back out of the factory and the rod's inner silhouette
# edge is walked against it. Widen the neck or move a rod inward and this fails.
def _block(name: str) -> str:
    """The body of a `const NAME … = [ … ];` table in the factory."""
    m = re.search(rf"const {name}[^=]*= \[(.*?)\n\];", SRC, re.S)
    if not m:
        raise SystemExit(f"{name} not found in {FACTORY.name} — the audit needs updating")
    return m.group(1)


clamp = [(float(a), float(b)) for a, b in re.findall(r"\[(-?[\d.]+), (-?[\d.]+)\]", _block("CLAMP_OUTLINE"))]
if len(clamp) != 3:
    raise SystemExit(
        f"CLAMP_OUTLINE has {len(clamp)} vertices — the jaw is a TRIANGLE (apex, culet, outer "
        "corner) and every check below indexes those three by name"
    )
(cix, ciy), (clx, cly), (cox, coy) = clamp
# The hilt's structural floor is the jaws' own lower edge, and every other part answers to it:
# the shell's base plane (#15), the grip column's top face (#16) and both arms' roots (#17). It
# is read out of the outline here, exactly as the factory reads it out of the same table, and
# `GUARD_UNDERSIDE_Y` is deliberately NOT read — that constant is the crop's dark-mass underside
# at -13 and it stopped being a structural plane when the jaws' floor went to 13.
floor_y = coy
floor_span = cox - clx
# The base STATION is written `[CLAMP_FLOOR_Y, CLAMP_FLOOR_SPAN, 11]`, which this file's numeric
# row regex deliberately does not match — the base is prepended from the outline instead, so a
# base typed as literals somewhere else would show up as a duplicated first row rather than being
# silently accepted.
profile = [(floor_y, floor_span)]
profile += [(float(y), float(w))
            for y, w in re.findall(r"^\s*\[(-?[\d.]+), (-?[\d.]+), ", _block("SHELL_STATIONS"), re.M)]
if profile[1][0] <= profile[0][0]:
    fail.append(
        f"SHELL_STATIONS' first NUMERIC row is at Y={profile[1][0]:.2f}, at or below the base row "
        f"the outline derives at Y={floor_y:.2f} — the base has been typed as a second pair of "
        "literals instead of being derived from CLAMP_OUTLINE"
    )
radial_end = const(r"^const DRIVER_RADIAL_END = (-?[\d.]+)")


def shell_half_width(y: float) -> float:
    """The pale shell's front-view half-width at height y; 0 where the shell does not reach."""
    if not profile[0][0] <= y <= profile[-1][0]:
        return 0.0
    for (y0, w0), (y1, w1) in zip(profile, profile[1:]):
        if y0 <= y <= y1:
            return w0 if y1 == y0 else w0 + (w1 - w0) * (y - y0) / (y1 - y0)
    return 0.0


for band, (rx, ry) in roots.items():
    e = math.radians(const(rf"DRIVER_ELEVATION_DEG = \{{.*{band}: (-?[\d.]+)"))
    r0 = math.hypot(rx, ry - centre_y)
    worst = min(
        # the rod's inner silhouette edge: axis offset by one radius, perpendicular and inward
        (t * math.cos(e) - rod_r * math.sin(e))
        - shell_half_width(centre_y + t * math.sin(e) + rod_r * math.cos(e))
        for i in range(201)
        for t in [r0 + (radial_end - r0) * i / 200]
    )
    print(f"DERIVED {band} driver clears the shell by {worst:.1f} "
          f"= {worst / (2 * rod_r):.2f} driver diameters")
    if worst < 0.75 * 2 * rod_r:
        fail.append(f"{band} driver clears the shell by only {worst / (2 * rod_r):.2f} driver "
                    f"diameters; the correction spec's floor is 0.75 and its target is 1.00")

# --- the guard's DAYLIGHT SWEEP, which replaced the grip tang's two assertions ---------------
# Retired 2026-08-08 with the tang itself (correction A). Those assertions asked "does the tang
# reach the widest gap between the jaws' splaying lower edges and the arms, and does its top sit
# past the jaws' junction" — two proxies for one question, and both are meaningless once the jaws
# have a flat floor and the leather is a plain column. The question they were proxies for is the
# only thing that ever mattered and it is now asked directly:
#
#     is there any height in the socket at which you can see through the guard?
#
# Swept, not reasoned. At each height the right half-plane is covered by three intervals — the
# grip column [0, its own reach], the jaw [inner edge, outer edge], and the shell [0, half-width]
# — and the sweep walks outward from the axis looking for the first x that none of them contains,
# out to whichever of the jaw or the shell reaches furthest. A gap anywhere in the band is
# daylight and fails. This is strictly harder than what it replaced: the tang test only ever
# examined the ONE widest gap and only between two of the parts, and it could not have noticed a
# second gap opening somewhere else, which is exactly what raising the jaws' floor would do.
#
# **The band is the JAWS' OWN FLOOR to the authority line, not the crop's dark-mass underside.**
# It used to start at GUARD_UNDERSIDE_Y = -13 because that was where the shell's tenon ended. The
# jaws' floor is at +13 now (#15/#16), and sweeping a band whose lower 26 units are below every
# part in the socket is not a stricter test, it is a broken one: it scores open air. Below the
# floor the hilt is the grip column and two raked arms that deliberately do NOT meet — see the
# guess list — so there is no "socket" down there to see through.
#
# Two seams carry it and both are recomputed from the factory rather than trusted:
#   · grip column ↔ jaw FLOOR, which is now a face-to-face contact on one plane (#16) rather than
#     a 5% bite into the column's flanks — see the coverage check below the sweep;
#   · jaw outer edge / shell edge ↔ the arm's inner silhouette, which is where the guard hands
#     over to the connector, over the arm's OWN height range and no further.
inradius = radius * math.cos(math.pi / sides)
arm_a = math.radians(angle)
grip_half = const(r"^const GRIP_HALF_WIDTH = (-?[\d.]+)")
grip_bottom = const(r"^const GRIP_BOTTOM_Y = (-?[\d.]+)")
gem_base = const(r"^const GEM_BASE_Y = (-?[\d.]+)")
gem_waist_y = (const(r"^const GEM_APEX_Y = (-?[\d.]+)") + gem_base) / 2
gem_half_w = const(r"^const GEM_HALF_WIDTH = (-?[\d.]+)")
clamp_half_depth = const(r"^const CLAMP_HALF_DEPTH = (-?[\d.]+)")
octagon_reach = math.cos(math.pi / 8)
grip_reach = grip_half * octagon_reach
grip_top = floor_y
insert_base_y = float(re.findall(r"\[(-?[\d.]+), ", _block("INSERT_OUTLINE"))[0])


def jaw_outer_edge_x(y: float) -> float:
    return cix + (cox - cix) * (ciy - y) / (ciy - coy)


def jaw_inner_edge_x(y: float) -> float:
    """The jaw's inner edge: the stone's own lower-right edge, apex down to the culet."""
    if y < cly or y > ciy:
        return math.inf
    return clx + (cix - clx) * (y - cly) / (ciy - cly)


# `_connector_inset()` used to live here: a re-run of correction C's bisection, sliding the arm
# inward along its own axis until its raked root cap was 5% of a diameter inboard of the shell's
# edge. It is DELETED with the inset itself — integration #17 anchors the arm's root cap centre ON
# the jaw's outer vertex and rakes it at the shell's own taper, so the cap's upper half IS the
# crystal's lower slanted edge and there is no depth left to search for. Kept nothing "in case":
# a dead bisection is a second definition of a joint the construction already fixes.
#
# The arm's TOP: the highest point on the whole limb is the root cap's outer rim, because the axis
# rakes downward from the root. Nothing above this height is arm, so the handover seam is only
# meaningful below it — extrapolating the cap's line past its own rim is how a check that reads
# "the guard stops short of the arm" gets asked about a height at which there is no arm.
arm_top_y = CY + radius * math.cos(arm_a)


def arm_inner_edge_x(y: float) -> float:
    """The arm's innermost silhouette x at height y, or +inf where the arm does not reach."""
    if y > arm_top_y:
        return math.inf
    cap = CX - (y - CY) * math.sin(arm_a) / math.cos(arm_a)
    wall = CX + (inradius + (y - CY) * math.cos(arm_a)) / math.sin(arm_a)
    return max(cap, wall)


# **The `gap` clause is RETIRED, on 2026-08-07, and it is retired because it stopped being able
# to fail — not because it started being inconvenient.** It walked outward from the axis at 801
# heights looking for the first x that no part covers, over `max(shell, jaw outer)`. Integration
# #15 gives the shell a base edge of half-width `CLAMP_FLOOR_SPAN` = 34 on the jaws' own floor,
# so across the WHOLE band the shell is a solid interval `[0, w(y)]` with `w(y) ≥ 34 ≥` the jaw's
# outer edge at every height. The union therefore starts at 0 and reaches the limit for ANY jaw
# outline whatsoever, and the clause returns +0.000 for the correct build, for the retired
# four-point jaw, for a jaw deleted outright. A clause that cannot reject anything is not
# coverage, it is the appearance of coverage, and this file exists because of what that costs.
#
# What it was protecting is now carried by three assertions that each name one joint, each biting
# on one of the three integrations, and each bracketed below against the geometry it replaced:
#
#   #15  the shell's lowest edge IS the two jaws' floor edges laid end to end;
#   #16  the grip column's top face lies ON that floor and inside its footprint, in x AND in z;
#   #17  each arm's root cap is pinned to the jaws' outer vertex and lies ON the shell's flank,
#        so the guard hands over to the arm with no slit at any height the arm reaches.
#
# and by one MEASUREMENT that is recorded rather than thresholded, for the same reason
# `measure_shell_value.py` records rather than thresholds: below the jaws' floor the hilt is the
# grip column and two raked arms which deliberately do NOT close on each other. The sketch draws
# that gap open and the crop reads dark mass there down to Y = -8. The build follows the sketch;
# the figure is printed so that any document quoting it is held to it, and so that re-filling the
# underside cannot happen quietly.
def guard_reach(y: float, inner_edge, outer_edge) -> float:
    """How far out the guard's own solid mass reaches at height y, in the front view."""
    jaw_in, jaw_out = inner_edge(y), outer_edge(y)
    return max(shell_half_width(y), jaw_out if math.isfinite(jaw_in) else 0.0)


def handover(inner_edge, outer_edge, root, rake, lo: float, hi: float):
    """The worst slit between the guard's reach and the arm's inner silhouette, over the arm."""
    worst, worst_y = math.inf, lo
    for i in range(801):
        y = lo + (hi - lo) * i / 800
        arm_x = arm_inner_edge_x(y) if (root, rake) == ((CX, CY), arm_a) else _arm_inner(
            y, root, rake)
        if not math.isfinite(arm_x):
            continue
        margin = guard_reach(y, inner_edge, outer_edge) - arm_x
        if margin < worst:
            worst, worst_y = margin, y
    return worst, worst_y


def _arm_inner(y: float, root, rake: float) -> float:
    """`arm_inner_edge_x` for a DOCTORED arm — the brackets below need it off the live one."""
    rx, ry = root
    if y > ry + radius * math.cos(rake):
        return math.inf
    cap = rx - (y - ry) * math.sin(rake) / math.cos(rake)
    wall = rx + (inradius + (y - ry) * math.cos(rake)) / math.sin(rake)
    return max(cap, wall)


# **The notch, in closed form.** Until 2026-08-11 this clause read `hand >= -0.001`: the cap's
# centre was on the jaw's corner, so every height in the band met the cap LINE, which is the
# flank, and the margin was 0 everywhere. The corner is the cap's lower RIM now, and that rim is
# the octagon's CIRCUMSCRIBED one while the arm's front-view silhouette is carried by its FACES,
# one apothem in — the same inradius-not-radius distinction `driverRootRadius()` and
# `spinnerSeat()` are both built on. So the leather's own lower face starts
# `radius*(1 - cos(pi/sides))` further along the cap, and a notch opens at the corner whose width
# is that divided by |sin a|.
#
# It is asserted as an EQUALITY, not as a slackened floor. The notch is a function of the radius,
# the facet count and the rake and of nothing else, so `hand` has exactly one admissible value;
# an arm anywhere else scores something else and fails, in either direction. That is strictly
# harder than the `>= -0.001` it replaces, which any arm sunk deeper into the guard would have
# passed. Both brackets below are run against it.
_notch = radius * (1 - math.cos(math.pi / sides)) / abs(math.sin(arm_a))
hand, hand_y = handover(jaw_inner_edge_x, jaw_outer_edge_x, (CX, CY), arm_a, floor_y, arm_top_y)
print(f"DERIVED guard hands over to the arm with {hand:+.4f} at Y={hand_y:.1f}, against the "
      f"octagon's own apothem notch {-_notch:+.4f} = R(1-cos(pi/{sides:.0f}))/|sin a| "
      f"(arm root ({CX:.3f}, {CY:.3f}), rake {angle:.4f} deg, top of arm Y={arm_top_y:.3f})")
if abs(hand + _notch) > 1e-6:
    fail.append(f"the guard hands over to the arm with {hand:+.4f} where the octagon's apothem "
                f"derives exactly {-_notch:+.6f}: the arm's root cap is no longer hanging off the "
                "jaw's corner along the crystal's lower slanted edge")

# --- integration #15, at the source: the shell's lowest edge and the two jaws' floors ---------
_base_row = profile[0]
if abs(_base_row[0] - coy) > 1e-9 or abs(_base_row[1] - cox) > 1e-9:
    fail.append(f"the shell's base row is ({_base_row[0]:.3f}, {_base_row[1]:.3f}) against the "
                f"clamp outline's outer vertex ({coy:.3f}, {cox:.3f})")
print(f"DERIVED #15 shell lowest edge 2 x {_base_row[1]:.3f} = {2 * _base_row[1]:.3f} on Y="
      f"{_base_row[0]:.3f}; the two jaw floors are {floor_span:.3f} + {floor_span:.3f} = "
      f"{2 * floor_span:.3f} on the same plane")
if abs(2 * _base_row[1] - 2 * floor_span) > 1e-9:
    fail.append(f"the shell's lowest edge is {2 * _base_row[1]:.3f} against the two jaws' floor "
                f"edges summing to {2 * floor_span:.3f} — integration #15 is an EQUALITY")

# --- integration #16: the grip column's top face is ON the jaws' floor, and under both jaws ----
# Two clauses, because "parallel and touching" and "hidden" are different failures. The plane
# clause catches a column that pokes up between the jaws again; the footprint clause catches one
# wide or deep enough for its own top face to show past them.
_grip_depth_reach = grip_half * math.cos(math.pi / 8)  # an 8-gon reaches its inradius in z too
print(f"DERIVED #16 grip top plane Y={grip_top:.3f} against the jaws' floor Y={floor_y:.3f}; "
      f"top face reaches {grip_reach:.3f} in x and {_grip_depth_reach:.3f} in z, inside a floor "
      f"footprint of +/-{floor_span:.3f} x +/-{clamp_half_depth:.3f}")
if abs(grip_top - floor_y) > 1e-9:
    fail.append(f"the grip column's top is at Y={grip_top:.3f} against the jaws' floor at "
                f"Y={floor_y:.3f}: integration #16 is face-to-face contact on ONE plane, so a "
                "burial is as wrong as a gap")
for what, built, limit in (("x", grip_reach, floor_span),
                           ("z", _grip_depth_reach, clamp_half_depth)):
    if built >= limit:
        fail.append(f"the grip column's top face reaches {built:.3f} in {what} against the jaws' "
                    f"floor footprint of {limit:.3f}: part of the face is not covered")

# --- the arm's LENGTH against the crop's own spinner axis, recorded rather than thresholded ----
# `CONNECTOR_LENGTH` was a bare directed literal with no provenance until 2026-08-11, when moving
# the arm's root perpendicular to its own axis carried its OUTER end with it — which the crop
# pins. The spinner hangs off that end, `measure_authority.py` segments both gold caps out of the
# artwork, and each blob gives two independent estimates of the spinner's axis: its bbox centre
# and its pixel centroid. `L` = 54.97 puts `spinnerSeat()`'s x on their mean.
#
# **On 2026-08-12 the length went back to 72 by user direction, so this record now measures a
# DEVIATION rather than a solve — and that is exactly why it is kept.** L = 55 solved this X pin
# to 0.007 of a source pixel and paid for it at the other end of the same arm, lifting the spinner
# assembly to an end-cap centre of (81.942, −18.346), which the user rejected on sight. The
# measurement did not stop being true when the directive overruled it, so it is printed every run
# with the residual it now carries — 11.080 units, 4.73 source pixels — instead of being deleted
# to make the build look solved. See CURRENT-MODEL §11 G4.
#
# Recorded and not gated, for the reason `measure_shell_value.py` records: the two caps disagree
# with each other by 12% — the crop's own left/right asymmetry, which a symmetric model cannot
# carry — so a threshold here would be scoring that asymmetry rather than the model. That was
# true while the length solved it and it is still true now that the length is directed: a gate
# here would be converting a user directive into a red light with no action behind it.
_length = const(r"^const CONNECTOR_LENGTH = (-?[\d.]+)")
_built_axis = CX + _length * math.cos(arm_a)
_gold = [g for g in json.loads((V / "spec" / "measurements.json").read_text())["gold"]
         if abs(g["centroid"][0]) > 50]
if len(_gold) != 2:
    fail.append(f"measurements.json's gold blobs no longer resolve to the two spinner caps "
                f"({len(_gold)} outboard of |x| = 50) — this record has gone stale")
else:
    _axes = sorted([abs(g["bbox"]["minX"] + g["bbox"]["maxX"]) / 2 for g in _gold]
                   + [abs(g["centroid"][0]) for g in _gold])
    _want_axis = sum(_axes) / len(_axes)
    _cap_normal = (-math.sin(arm_a), math.cos(arm_a))
    _end_y = CY + _length * math.sin(arm_a)
    _rim_y = _end_y - radius * _cap_normal[1]
    print(f"BUILT   spinner axis x={_built_axis:.3f} at CONNECTOR_LENGTH={_length:.0f}, against "
          f"the crop's two gold caps ({', '.join(f'{v:.2f}' for v in _axes)}, mean "
          f"{_want_axis:.3f}) — {abs(_built_axis - _want_axis):.3f} units off, "
          f"{abs(_built_axis - _want_axis) / 2.3414:.3f} of a source pixel. DIRECTED since "
          f"2026-08-12; the X-solving length is 54.97")
    # The other pin the same length has to reach, and the one the directive is FOR: the crop's
    # gold caps emerge from under the leather at Y = -53.45, and the arm's end-cap lower rim is
    # where this build stops covering them. Printed beside the X residual so a reader can see
    # both ends of the trade in one place rather than in two documents.
    print(f"BUILT   arm end-cap centre ({_built_axis:.3f}, {_end_y:.3f}), its lower rim at "
          f"Y={_rim_y:.3f} against the crop's gold-cap tops at Y=-53.450 — "
          f"{abs(_rim_y - (-53.45)):.3f} units short (it was 24.688 at L=55)")

# --- the spinner tapers ONE WAY, and the check is against the ARM rather than against the table --
# **This is the clause the five-row profile table could not have had.** That table put every ring
# at an absolute height while its top ring came from `spinnerSeat()`, so the lathe interpolated
# between a ring that moved with the arm and a first row that never moved: at L = 55 the arm's own
# end cap hid nearly all of that ramp, and the 2026-08-12 return to L = 72 lifted the seat 10.4
# units and pulled the arm's cover up with it, exposing 13.0 units of flank that got WIDER going
# down. Every number in the factory was unchanged. Every gate was green about the spinner. The
# defect was in the interpolation, which no table can assert about.
#
# So this re-derives the whole profile the way the factory does and asks the two questions that
# survive an arm moving underneath them:
#
#   1. below the shoulder, does the radius ever increase going DOWN? By construction it cannot —
#      it is one interpolated line — but the clause is here so that re-tabulating the rows by hand
#      fails instead of quietly restoring the defect.
#   2. how much of the shoulder is OUTSIDE the arm? That is the only widening a camera can see,
#      and it is a function of the arm's rake, radius and length as much as of the spinner. The
#      flank at half-width w leaves the arm's end-cap plane at Y = capCentre + w*cot|a|; walking
#      the shoulder segment to that crossing gives the exposed height directly.
#
# The floor is 2.0 units — two render pixels on the 0.9915-units-per-pixel capture the gates read,
# i.e. the smallest widening a viewer could resolve. The build scores 1.1. The five-row table this
# replaces scores 29.7 on the same formula, so the doctored bracket below is not a hypothetical.
_spin_top_r = const(r"^const SPINNER_TOP_RADIUS = (-?[\d.]+)")
_spin_bot_r = const(r"^const SPINNER_BOTTOM_RADIUS = (-?[\d.]+)")
_spin_bot_y = const(r"^const SPINNER_BOTTOM_Y = (-?[\d.]+)")
_spin_bands = int(const(r"^const SPINNER_BANDS = (-?[\d.]+)"))
_spin_clear = const(r"^const SPINNER_SEAT_CLEARANCE = (-?[\d.]+)")
if not re.search(r"^const SPINNER_SHOULDER_DROP = SPINNER_SEAT_CLEARANCE;", SRC, re.M):
    fail.append("SPINNER_SHOULDER_DROP is no longer SPINNER_SEAT_CLEARANCE — the shoulder's height "
                "is what decides how much of the only widening section a camera can see, and it "
                "is derived from the clearance rather than chosen")
_spin_drop = _spin_clear
_lathe_k = math.cos(math.pi / 6)      # the six-sided lathe's front-view factor


def spinner_profile(root=(None, None), rake=None, length=None, table=None):
    """`spinnerProfile()`, re-derived. `table` doctors it back into an absolute-height list."""
    rx = CX if root[0] is None else root[0]
    ry = CY if root[1] is None else root[1]
    a = arm_a if rake is None else rake
    L = _length if length is None else length
    down, out = abs(math.sin(a)), abs(math.cos(a))
    r = down * inradius - _spin_clear * (down + out)
    seat = (r, ry + L * math.sin(a) + (out * r + _spin_clear) / down)
    if table is not None:
        return [seat, *table], seat, rx + L * math.cos(a), ry + L * math.sin(a)
    top_y = seat[1] - _spin_drop
    rings = [seat]
    for i in range(_spin_bands + 1):
        t = i / _spin_bands
        rings.append((_spin_top_r + (_spin_bot_r - _spin_top_r) * t,
                      top_y + (_spin_bot_y - top_y) * t))
    return rings, seat, rx + L * math.cos(a), ry + L * math.sin(a)


def exposed_widening(rings, cap_centre_y: float, rake: float) -> float:
    """The height over which the outline still WIDENS downward once it is clear of the arm.

    The arm's end-cap plane, in the front view, is the line through the cap's centre whose outboard
    flank rises by cot|a| per unit out. A profile point at radius r shows a front-view half-width
    of `0.866 r`, and it is outside the arm below `capCentre + 0.866 r * cot|a|`. Walking each
    widening segment to that crossing and summing what is left is the exposed ramp.
    """
    cot = abs(math.cos(rake)) / abs(math.sin(rake))
    total = 0.0
    for (r0, y0), (r1, y1) in zip(rings, rings[1:]):
        if r1 <= r0 or y1 >= y0:
            continue                                     # not a widening segment
        drop = y0 - y1
        # `f(s) = y(s) - plane(w(s))` is POSITIVE where the flank is still covered — the arm's
        # solid is above its own end-cap plane — and it falls monotonically along a widening
        # segment, because y drops while the plane rises. So the crossing is one linear solve.
        f0 = y0 - (cap_centre_y + _lathe_k * r0 * cot)
        f1 = y1 - (cap_centre_y + _lathe_k * r1 * cot)
        if f0 <= 0:
            s = 0.0                                      # already outside at the top of the ramp
        elif f1 >= 0:
            continue                                     # the whole segment stays inside the arm
        else:
            s = f0 / (f0 - f1)
        total += (1 - s) * drop
    return total


# --- the arm's LENGTH, DERIVED as of 2026-08-13, and the pin it can no longer be accused of -----
# **`CONNECTOR_LENGTH` stops being a directed literal here.** It was 72 by user direction, against
# a crop reading that solved to 54.97, and the record said so every run. On 2026-08-13 the user
# directed the arm LONGER and the spinner SHORTER, against the artwork — and once you ask the crop
# where the arm's outer END is rather than where its X is, the length has a closed form.
#
# The crop pins that end as a POINT: X = 81.925, four ways off the two gold blobs, and Y = the
# height where its gold first appears, −53.45, carried down by the emergence offset below. The
# root and the rake are both LOCKED, so the built end can only sit on the ray
# `CONNECTOR_ROOT + L·(cos a, sin a)`, and that point is not on it. The length that puts the built
# end CLOSEST to it is the perpendicular projection, and that is what ships:
#
#     L = (cropArmEnd − CONNECTOR_ROOT) · (cos a, sin a)
#
# What it does NOT do is solve either pin. The perpendicular shortfall is 28.95 units and belongs
# to the rake, not to any length; the axis lands 21.97 units wide of 81.925 (9.4 source pixels,
# worse than the 4.73 at L = 72) and the cap top lands 18.84 units high of −53.45. Both are worse
# on their own pin than some other length would be, and the projection is still the best available
# because it is the only choice no other length beats on DISTANCE. §11 G4 carries the whole table.
#
# The emergence offset is the geometry that makes the Y pin comparable at all: the crop's cap top
# is its topmost GOLD pixel, and the build's topmost gold pixel is not its end-cap centre — it is
# where the shoulder's flank crosses the arm's end-cap plane, `emerge` above that centre. Same
# solve as `exposed_widening`, and it is independent of L, which is why the projection stays
# linear.
_cot = abs(math.cos(arm_a)) / abs(math.sin(arm_a))
_spin_seat_r = abs(math.sin(arm_a)) * inradius - _spin_clear * (abs(math.sin(arm_a))
                                                                + abs(math.cos(arm_a)))
_lift = (abs(math.cos(arm_a)) * _spin_seat_r + _spin_clear) / abs(math.sin(arm_a))
_f0 = _lift - _lathe_k * _spin_seat_r * _cot
_f1 = _lift - _spin_drop - _lathe_k * _spin_top_r * _cot
_s = 0.0 if _f0 <= 0 else (1.0 if _f1 >= 0 else _f0 / (_f0 - _f1))
_emerge = _lathe_k * (_spin_seat_r + _s * (_spin_top_r - _spin_seat_r)) * _cot
CROP_CAP_TOP, CROP_CAP_BOTTOM, CROP_CAP_AXIS = -53.45, -109.65, 81.925
_crop_end = (CROP_CAP_AXIS, CROP_CAP_TOP - _emerge)
_v = (_crop_end[0] - CX, _crop_end[1] - CY)
_want_length = _v[0] * math.cos(arm_a) + _v[1] * math.sin(arm_a)
_perp = abs(-_v[0] * math.sin(arm_a) + _v[1] * math.cos(arm_a))
print(f"DERIVED CONNECTOR_LENGTH {_length:.4f} against the projection of the crop's own arm end "
      f"({_crop_end[0]:.3f}, {_crop_end[1]:.3f}) onto the locked ray = {_want_length:.4f}; "
      f"gold appears {_emerge:.3f} above the end-cap centre; the rake leaves "
      f"{_perp:.3f} units of perpendicular miss at EVERY length")
if abs(_length - _want_length) > 5e-4:
    fail.append(f"CONNECTOR_LENGTH is {_length:.4f} but the crop's own arm end projects to "
                f"{_want_length:.4f} on the locked ray — the length is DERIVED as of 2026-08-13 "
                "and is not a free literal any more")
# Both retired lengths, on the same solve. 72 was the directed value this replaces and 54.97 the
# X solve before it; each is the answer to ONE pin and each is further from the crop's arm end
# than the projection is.
for _what, _l in (("the directed 72", 72.0), ("the X solve 54.97", 54.97),
                  ("the cap-top solve", (CROP_CAP_TOP - _emerge - CY) / math.sin(arm_a))):
    _end = (CX + _l * math.cos(arm_a), CY + _l * math.sin(arm_a))
    _miss = math.hypot(_end[0] - _crop_end[0], _end[1] - _crop_end[1])
    if _miss <= _perp + 1e-9:
        fail.append(f"{_what} is no further from the crop's arm end than the projection — the "
                    "projection clause has stopped being a minimum")
    else:
        print(f"BRACKET {_what} (L={_l:.2f}) misses the crop's arm end by {_miss:.3f} against the "
              f"projection's {_perp:.3f} — correctly rejected")

_rings, _seat, _axis_x, _cap_y = spinner_profile()
_widen = exposed_widening(_rings, _cap_y, arm_a)
_below = [(r, y) for r, y in _rings[1:]]
_rise = max((_below[i + 1][0] - _below[i][0] for i in range(len(_below) - 1)), default=0.0)
print(f"DERIVED spinner profile {len(_rings)} rings, seat r={_seat[0]:.3f} at Y={_seat[1]:.3f}, "
      f"shoulder r={_spin_top_r:.1f} at Y={_seat[1] - _spin_drop:.3f}, blunt bottom r="
      f"{_spin_bot_r:.1f} at Y={_spin_bot_y:.1f}; widest ring is ring 2 of {len(_rings)}; "
      f"largest widening below the shoulder {_rise:+.4f}; exposed ramp {_widen:.3f} units "
      f"against a 2.0 floor")
if _rise > 1e-9:
    fail.append(f"the spinner widens by {_rise:+.4f} somewhere BELOW its shoulder — it is a "
                "spinning top again, not a frustum. The whole piece below the shoulder is one "
                "straight line between two measured ends and cannot widen unless it was "
                "re-tabulated by hand")
if _widen > 2.0:
    fail.append(f"the spinner's outline still widens downward over {_widen:.3f} units after it "
                f"clears the arm's end-cap plane, against a 2.0-unit floor. The shoulder is the "
                "only widening section and it has to stay buried; if the ARM moved, this is what "
                "it broke")
# Both brackets are the five-row table itself, on two different arms — the one it shipped on until
# 2026-08-13 and the one it was authored against before the 2026-08-11 amendment, when the jaw's
# outer corner was the arm's cap CENTRE and the seat sat at Y = -31.884. It fails on both, and
# that is the finding rather than a formality: the ramp was never hidden. Moving the arm made it
# 10.185 units worse — 19.492 to 29.677 — which is when it got noticed, but the table was already
# carrying 19.5 units of exposed ramp through every acceptance review it ever passed.
_TABLE = [(21.4, -53.5), (20.8, -63.5), (16.6, -78.5), (12.9, -93.5), (8.1, -109.7)]
for _what, _root, _floor in (
    ("the 5-row table on today's arm", (CX, CY), 2.0),
    ("the 5-row table on the pre-2026-08-11 arm (cap centre on the jaw's corner)", (cox, coy), 2.0),
):
    _r2, _s2, _x2, _c2 = spinner_profile(root=_root, table=_TABLE)
    _w2 = exposed_widening(_r2, _c2, arm_a)
    if _w2 <= _floor:
        fail.append(f"the exposed-ramp clause passes {_what}, which is the defect it exists to "
                    f"catch ({_w2:.3f} against {_floor})")
    else:
        print(f"BRACKET {_what} scores {_w2:.3f} units of exposed ramp (seat Y={_s2[1]:.3f}) — "
              "correctly rejected")

# --- integration #17, at the source: the arm's root cap's LOWER RIM is the jaws' outer vertex ---
# **Amended 2026-08-11, and the amendment is which END of the cap the corner is.** The clause used
# to read "CONNECTOR_ROOT == the outer vertex", i.e. the cap's CENTRE on the corner — which put
# the cap's lower rim at (21.852, 2.587), 10.413 units below the guard's own floor and hanging in
# open air under the jaws. The directive is that the arm hangs OFF that corner and runs up the
# flank, so the corner is the cap's lower RIM and the centre is one radius further along the cap's
# own in-plane normal.
#
# That normal is not a free choice either: a cap perpendicular to the axis has its diameter along
# (-sin a, cos a), so making the rake the shell's lower taper puts the cap's WHOLE diameter ON the
# crystal's flank. Re-derived here from SHELL_STATIONS, CLAMP_OUTLINE and CONNECTOR_RADIUS, never
# read from the factory's own comment: move a clamp vertex, the taper or the radius and the
# literal in the factory has to move with it or this fails.
_taper_slope = (shell_half_width(gem_waist_y) - cox) / (gem_waist_y - coy)
_want_rake = -math.degrees(math.atan(_taper_slope))
_cap_n = (-math.sin(arm_a), math.cos(arm_a))          # the cap's own in-plane unit normal
_rim_lo = (CX - radius * _cap_n[0], CY - radius * _cap_n[1])
_rim_hi = (CX + radius * _cap_n[0], CY + radius * _cap_n[1])
_want_root = (cox + radius * _cap_n[0], coy + radius * _cap_n[1])
print(f"DERIVED #17 arm root ({CX:.6f}, {CY:.6f}) against the corner + R*(-sin a, cos a) = "
      f"({_want_root[0]:.6f}, {_want_root[1]:.6f}); cap runs ({_rim_lo[0]:.3f}, {_rim_lo[1]:.3f}) "
      f"-> ({_rim_hi[0]:.3f}, {_rim_hi[1]:.3f}); rake {angle:.4f} deg against the shell taper's "
      f"{_want_rake:.4f} deg (slope {_taper_slope:.6f})")
_rim_err = max(abs(_rim_lo[0] - cox), abs(_rim_lo[1] - coy))
if _rim_err > 1e-6:
    fail.append(f"the arm's root cap's LOWER RIM is ({_rim_lo[0]:.6f}, {_rim_lo[1]:.6f}) but the "
                f"clamp outline's outer vertex is ({cox:.3f}, {coy:.3f}) — {_rim_err:.6f} apart. "
                "CONNECTOR_ROOT has to be that vertex plus one CONNECTOR_RADIUS along "
                "(-sin a, cos a), or the arm has stopped hanging off the jaw's corner")
if abs(angle - _want_rake) > 0.001:
    fail.append(f"CONNECTOR_ANGLE_DEG is {angle:.4f} but the shell's lower taper derives "
                f"{_want_rake:.4f} — the arm's root cap is no longer coplanar with the flank it "
                "is plugged into")


def _flank_at(y: float) -> float:
    """The shell's flank at a cap sample, with the base row's own vertex snapped ON.

    The cap's lower rim IS the base row's vertex, and `CY - radius*cos a` reconstructs Y = 13 to
    within 4e-8 — sometimes a hair BELOW it, where `shell_half_width` correctly answers "there is
    no shell here" and the residual jumps to the full 34. The snap is 1e-6 wide and the rim's own
    position is asserted to 1e-6 above, so it can only ever absorb float noise: a rim that has
    really moved fails the clause before this one, and a sample further out than 1e-6 still falls
    off the shell and blows the residual up, which is the behaviour that has to survive.
    """
    lo, hi = profile[0][0], profile[-1][0]
    if y < lo - 1e-6 or y > hi + 1e-6:
        return 0.0
    return shell_half_width(min(max(y, lo), hi))


_cap_residual = max(
    abs((CX + math.sin(-arm_a) * s) - _flank_at(CY + math.cos(arm_a) * s))
    for i in range(65) for s in [-radius + 2 * radius * i / 64]
)
print(f"DERIVED #17 the WHOLE root cap against the shell's flank: worst front-view residual "
      f"{_cap_residual:.6f} over 65 samples, rim to rim")
if _cap_residual > 0.01:
    fail.append(f"the arm's root cap stands {_cap_residual:.3f} off the shell's lower slanted "
                "edge; correction C's 'one line, not two' is the construction now, not a target")

# --- the guard's UNDERSIDE, recorded rather than thresholded -----------------------------------
_under_lo = const(r"^const GUARD_UNDERSIDE_Y = (-?[\d.]+)")
_open_run, _open_y = -math.inf, _under_lo
for i in range(801):
    _y = _under_lo + (floor_y - _under_lo) * i / 800
    _covered = grip_reach if grip_bottom <= _y <= grip_top else 0.0
    _run = arm_inner_edge_x(_y) - _covered
    if math.isfinite(_run) and _run > _open_run:
        _open_run, _open_y = _run, _y
print(f"BUILT   guard underside opening {_open_run:.3f} units wide at Y={_open_y:.1f}, between "
      f"the grip column and each arm, over Y={_under_lo:.0f}...{floor_y:.0f}")

# --- brackets: every clause above, run against the geometry it replaced ------------------------
# Five: the three retired readings, the retired rake, and the retired ROOT — the cap centre sitting
# ON the jaw's corner, which is what this file asserted until 2026-08-11 and what the amended #17
# has to reject. Each reverts exactly one clause, so a bracket that passes says which assertion
# has gone blind.
_b_root = (28.0, 8.0)      # correction C's measured axis anchor, before #17
_b_centre = (cox, coy)     # the cap CENTRE on the corner — #17 as it stood until 2026-08-11
_b_rake = -50.0            # the directed rake, before it was derived from the taper
_b_burial = 3.0            # GRIP_BURIAL, before #16
_b_tenon = grip_half * math.cos(math.pi / 8) - 0.05 * 2 * grip_half  # the retired shell tenon


def _rim_miss(root) -> float:
    """How far a doctored cap CENTRE puts the cap's lower rim from the jaw's outer vertex."""
    return math.hypot(root[0] - radius * _cap_n[0] - cox, root[1] - radius * _cap_n[1] - coy)


def _notch_miss(root, rake: float) -> float:
    """How far a doctored arm's handover departs from the octagon's own apothem notch."""
    return abs(handover(jaw_inner_edge_x, jaw_outer_edge_x, root, rake,
                        floor_y, root[1] + radius * math.cos(rake))[0] + _notch)


_b_rake_n = (-math.sin(math.radians(_b_rake)), math.cos(math.radians(_b_rake)))
_b_rake_root = (cox + radius * _b_rake_n[0], coy + radius * _b_rake_n[1])
_brackets = [
    ("#15 base row at the retired tenon",
     abs(_b_tenon - cox), 0.01),
    ("#16 grip top at the retired burial",
     abs((floor_y + _b_burial) - floor_y), 1e-9),
    ("#17 arm at correction C's measured root",
     _rim_miss(_b_root), 1e-6),
    ("#17 arm with its cap CENTRE back on the jaw's corner",
     _rim_miss(_b_centre), 1e-6),
    ("#17 handover with the cap CENTRE back on the jaw's corner",
     _notch_miss(_b_centre, arm_a), 1e-6),
    ("#17 handover at the directed -50 rake",
     _notch_miss(_b_rake_root, math.radians(_b_rake)), 1e-6),
]
for _label, _score, _floor in _brackets:
    print(f"BRACKET {_label} scores {_score:+.4f} against a tolerance of {_floor:g}")
    if _score <= _floor:
        fail.append(f"the bracket '{_label}' PASSES the assertion written to reject it — that "
                    "clause is no longer measuring anything")

# --- correction D, at the source: one line, four features ------------------------------------
# The built model is checked by `check_centerline.py` from the manifest; this checks the numbers
# the factory was written with, so a literal typed a unit off fails before anything is rendered.
authority = ciy
# The VISIBLE lower trapezoid is ONE straight line all the way to its own base, and every station
# on it has to lie on the line through its two ends.
#
# The second half of this used to be "and that line reaches zero half-width at the guard's
# underside", which is what made the shell's root a STUB of the trapezoid it could be dropped into
# the guard on. Integration #15 retires it: the trapezoid does not vanish any more, it lands on
# the jaws' floor at their own outer vertex, and the clause that says so is `#15` above. Leaving
# the vanish check in place would demand a shape the build no longer has and pass only by luck.
_taper = [row for row in profile if row[0] <= gem_waist_y]
if len(_taper) >= 3:
    (y1, w1) = _taper[-1]
    (y0, w0) = _taper[0]
    for y, w in _taper[1:-1]:
        want = w0 + (w1 - w0) * (y - y0) / (y1 - y0)
        if abs(w - want) > 0.02:
            fail.append(f"SHELL_STATIONS' row at Y={y:.0f} is {w:.3f} wide where the trapezoid's "
                        f"own line gives {want:.3f} — the lower taper has a step in it")
    print(f"DERIVED the lower taper runs ({y0:.0f}, {w0:.3f}) to ({y1:.0f}, {w1:.3f}), slope "
          f"{(w1 - w0) / (y1 - y0):.4f} per unit of height, against the crop's least-squares "
          "1.131 (RMS residual 1.71, one source pixel 2.34)")

# Where the shell's lower contraction STARTS is the top of that straight line — the last station
# on it — so the two checks together are the whole of correction D's first clause: every station
# below Y=55 lies on one line, and Y=55 is a station.
taper_start = _taper[-1][0] if _taper else float("nan")
for label, value in (("SHELL_STATIONS' taper start", taper_start),
                     ("INSERT_OUTLINE's base", insert_base_y),
                     ("CORE_OUTLINE's base (GEM_WAIST_Y)", gem_waist_y)):
    if not abs(value - authority) <= 0.01:
        fail.append(f"{label} is at Y={value:.2f} against CLAMP_OUTLINE's authority vertex at "
                    f"Y={authority:.2f} — correction D pins them to one line")
print(f"DERIVED authority line Y={authority:.1f}: shell taper starts {taper_start:.1f}, "
      f"insert base {insert_base_y:.1f}, core base {gem_waist_y:.1f}")

# --- the clamp outline's own literals, recomputed from the parts they answer to --------------
# CLAMP_OUTLINE has to be numeric literals (the tables above parse it), so nothing in TypeScript
# can hold it to the gem it is cut from. This does. Three vertices, and every one of them is a
# vertex of the GEM — the outline stopped answering to the grip column when the column stopped
# being inserted between the jaws (#16), so the retired knee and the retired vertical inner face
# at CLAMP_INNER_X are gone from both the table and from here.
for what, built, want in (("inner-upper X", cix, gem_half_w),
                          ("inner-upper Y", ciy, gem_waist_y),
                          ("inner-lower X (the culet, ON the axis)", clx, 0.0),
                          ("inner-lower Y (the culet)", cly, gem_base)):
    if abs(built - want) > 0.01:
        fail.append(f"CLAMP_OUTLINE's {what} is {built:.3f}, but the gem derives {want:.3f} — the "
                    "jaw no longer follows the stone it clamps")
if abs(cly - coy) > 1e-9:
    fail.append(f"CLAMP_OUTLINE's lower edge runs {cly:.2f}→{coy:.2f}: correction B requires it "
                "to be one HORIZONTAL line")
# The jaw's inner edge 1→2 IS the stone's own lower edge, so the two are flush over its whole
# length rather than merely sharing two endpoints. Both are straight, so the endpoints settle it
# only because the gem's own half-width is linear in Y between them — checked, not assumed.
_flush = max(abs(jaw_inner_edge_x(cly + (ciy - cly) * i / 64)
                 - gem_half_w * (cly + (ciy - cly) * i / 64 - gem_base)
                 / (gem_waist_y - gem_base))
             for i in range(65))
print(f"DERIVED the jaw's inner edge against the gem's lower edge: max |gem − jaw| = {_flush:.9f}")
if _flush > 1e-6:
    fail.append(f"the jaw's inner edge stands {_flush:.4f} off the stone's own lower edge")

grip = next(p["bounds"] for p in parts["parts"] if p["name"] == "leatherGrip")
for what, built, want in (("half-width", grip["maxX"] / 0.01, grip_reach),
                          ("top", grip["maxY"] / 0.01, grip_top)):
    if abs(built - want) > 0.01:
        fail.append(f"leatherGrip {what} built at {built:.3f} against a derived {want:.3f} — the "
                    "column is not the plain constant-width column correction A asks for, or its "
                    "top face is no longer flat on the jaws' floor (integration #16)")

# --- figures the documents must agree on ---------------------------------------------------
# Each entry: label, the one live value, and every value it has retired.
FAMILIES = [
    # 0.8895 retired 2026-08-07 with the shell going solid: `mask_from` keys on `min(rgb) < 244`
    # and the solid shell is 5 levels brighter, so the blade's needle tip sits closer to that
    # line. Same geometry, same mask bbox (432x1031), 0.0002 of IoU.
    # 0.8893 retired 2026-08-07 with integrations #15/#16/#17. The guard is the only thing that
    # moved and it moved a long way: the shell's lowest edge came up 26 units to the jaws' floor
    # and widened to 68 there, and both arms moved out to the jaws' outer corners. IoU went UP.
    # 0.8993 retired 2026-08-11 with the amendment to #17. Both arms came up one radius along
    # their own normals and their length was re-solved for the crop's spinner axis; the arms are
    # the only thing that moved and the silhouette pays 0.0015 for it. Swept over CONNECTOR_LENGTH
    # 40…72 this is the best value available at the new root — see CURRENT-MODEL §11 G4.
    # 0.8978 retired 2026-08-12 with CONNECTOR_LENGTH going back to 72 by user direction. The arms
    # are again the only thing that moved, and this is the figure the sweep already predicted for
    # L = 72 at the amended root. The directive is about where the spinner balls SIT; this number
    # is what it costs, and it is recorded rather than argued with.
    # 0.8793 retired 2026-08-13 with the spinner's profile becoming a derived frustum. The caps
    # keep their bbox exactly — same widest radius, same seat, same bottom — but the widest ring
    # moved from Y = -53.5 up to the shoulder, so the cap is wider over -23…-53 and narrower below
    # it than the crop's own rows. The crop's rows are where they are because ITS leather stops at
    # -53.45 and this build's stops at -41.67; see the comment on SPINNER_TOP_RADIUS.
    ("silhouette IoU", iou,
     ["0.8943", "0.8937", "0.8892", "0.815", "0.8875", "0.8868", "0.8891", "0.8894", "0.8895",
      "0.8893", "0.8993", "0.8978", "0.8793", "0.8776"]),
    # 4 decimal places like every other IoU: at 3 the live value rounded to a string that never
    # appears in any document, so the family could never be satisfied.
    # 0.8553 retired 2026-08-11 with the same amendment, and this is the figure it cost the most:
    # the gate's floor is 0.85 and this went RED, 0.8478. Swept, not assumed — see §11 G4 and the
    # limitation note in CURRENT-MODEL §8.
    # 0.8478 retired 2026-08-12 with CONNECTOR_LENGTH directed back to 72: 0.8367, the value the
    # same sweep already recorded at that length. The floor is NOT moved to meet it — the chain
    # 0.8553 (pass) → 0.8478 → 0.8367 is written down in §8 as a documented limitation, because a
    # threshold that follows the build is not a threshold.
    # 0.8367 retired 2026-08-13 with the spinner's frustum: 0.8348, one more step down the same
    # chain and for the same kind of reason — a user directive about SHAPE, paid for in silhouette.
    # The floor stays at 0.85 and the chain 0.8553 → 0.8478 → 0.8367 → 0.8348 is written down in
    # §8 rather than met by moving the threshold.
    # 0.8209 retired 2026-08-09 with the stone's crown going to a POINT, which took `loft` off its
    # fixed diagonal and retriangulated every mesh on the model: 0.8208. One ten-thousandth, and it
    # is here because a figure that appears in four paragraphs is exactly the kind that goes stale.
    ("blockout tier-1 IoU", f"{blockout_iou:.4f}",
     ["0.848", "0.8522", "0.8523", "0.8505", "0.8499", "0.8492", "0.8506", "0.8515", "0.8514",
      "0.8503", "0.8508", "0.8524", "0.8553", "0.8478", "0.8367", "0.8348", "0.8209", "0.8208"]),
    # 55.49 retired 2026-08-09: subdividing the shell's lower trapezoid adds facet bands to the
    # pale wedge either side of the guard, which is an AREA-proportion change like every other
    # entry in this list. No material and no surface moved.
    # "55.5" was never in this list and should have been: it is what every record quoted while the
    # live value was 55.49, and the families match by substring, so a rounded figure has to be
    # retired explicitly or it drifts silently. 55.42 comes off the list because it is live again
    # — the solid shell moved the render's five dominant clusters by 0.07 of delta-E, which is the
    # whole of this change's effect on the one red gate.
    # 55.42 retired 2026-08-07 with the guard integrations, and "56.28" comes OFF the retired list
    # because it is live again — the same figure this metric read two passes ago, reached from a
    # different geometry. That is what the substring net is for: a value has to be retired while
    # it is dead and un-retired when it comes back, or the family can never be satisfied.
    # 56.28 retired 2026-08-11: the arms and the four rods moved, which changes the area
    # proportions of the render's dominant clusters — the same kind of change as every other entry
    # here. No material moved.
    # 56.83 retired 2026-08-12 for the same reason one more time: the arms grew 17 units, which
    # moves the area proportions the five dominant clusters are fitted to. No material moved.
    # 57.35 retired 2026-08-13, same mechanism one more time: the spinner caps carry the same
    # gold over a different area, and this metric fits five dominant clusters by area proportion.
    # No material moved.
    ("per-part delta-E", f"{de}",
     ["62.3", "58.9", "58.62", "58.61", "61.94", "56.49", "56.87", "55.76",
      "56.23", "55.7", "55.52", "55.49", "55.5", "55.42", "56.28", "56.83", "57.35", "57.1"]),
    ("node count", str(len(names)), ["27 named", "27 specified", "47 named",
                                     "21 named", "21 specified"]),
    ("mesh count", str(meshes), ["22 meshes", "22 mesh", "18 meshes", "18 physical"]),
    # 1040 retired 2026-08-07: #15 replaced the shell's two lowest stations with one, and the
    # jaws' floor, the grip's top and both arms' root caps all re-triangulated around it.
    ("triangle count", str(tris),
     ["1004 triangles", "968 triangles", "720 triangles", "748 triangles", "740 triangles",
      "788 triangles", "952 triangles", "932 triangles", "896 triangles", "810 triangles",
      "826 triangles", "840 triangles", "1040 triangles", "1080 triangles", "1092 triangles",
      "1064 triangles", "984 triangles"]),
    # 0.9987/0.9989 were measured before the shell's blending was rebuilt (transmission to 0,
    # DoubleSide to FrontSide, opacity 0.35). This metric masks on `min(rgb) < 244`, so a change
    # to how the translucent shell composites over white moves it; splitting the blade reliefs
    # did not. Measured both ways on matched hide-sets: 0.9977 before AND after the split.
    # 0.9979 retired 2026-08-07 for the same reason as the silhouette IoU above: this metric masks
    # on `min(rgb) < 244` too, and the solid shell sits closer to that line.
    # 0.9963 retired 2026-08-12 with CONNECTOR_LENGTH back at 72: this metric is an AREA ratio and
    # the arms are 17 units longer, so the same antialiased rim is a smaller fraction of a larger
    # silhouette. The model is still exactly symmetric front to rear — `check_centerline.py`'s
    # mirror rows read 0.00000 — which is what this row is actually for.
    # 0.9962 retired 2026-08-13 with the spinner's frustum, and "0.9964" comes OFF the retired list
    # in the same edit because it is LIVE again — the same figure this metric read two passes ago,
    # reached from different geometry. That is what the substring net is for and it is the second
    # time this row has needed it. The model is still exactly symmetric front to rear;
    # `check_centerline.py`'s mirror rows read 0.00000.
    ("front/rear silhouette IoU", front_rear_iou,
     ["0.9987", "0.9989", "0.9977", "0.9978", "0.9979", "0.9962", "0.9964"]),
    # The split's own acceptance figure. 66.5%/66.6% is the dark core before the split, when its
    # depth collapsed to 0.62 of full above Y=84 and it sank inside both the shell and the insert;
    # 89.8/89.7 is the boss it was before the skins, which cleared the shell over most but not all
    # of its footprint because a boss's clearance varies across its own face and a skin's does not.
    # 92.5% is the same skin with its apex cut off at Y=118 — a shorter triangle, so more
    # antialiased perimeter per unit of area, so a slightly worse score for identical geometry.
    ("dark core proud fraction", f"{proud['darkCoreTriangle'][0]}%",
     ["66.5%", "66.6%", "89.8%", "89.7%", "92.5%"]),
    # "9.4%" is deliberately NOT retired here: these families match by substring, and it is a
    # substring of 89.4%, 49.4% and every other x9.4%.
    #
    # 93.8% is the same geometry with the stone still built as a cut pair: its two tips collapsed
    # to points ON Z = 0, buried under every layer on the blade, and seating them on the stack is
    # what took the figure to 95.8%.
    # 95.8% is the same stone measured while the insert skin still ran down to Y = 42: it propped
    # the gem's own seat up by one SKIN_STEP over Y = 42…55, and correction D's authority line took
    # that prop away. 54.3% is the DEGENERATE-tenon defect the shell's base station now prevents —
    # a rear-only figure, never a build that shipped.
    # 93.6% retired 2026-08-07: the shell went solid, so it entered the opaque backbuffer the
    # gem's transmission pass samples and started tinting the stone's own pixels without occluding
    # them. Identity scored that 1.2% — the same instrument failure the gem-against-the-core test
    # had, with the same fix — and the stone is now scored against the shell by survival on a
    # once-eroded footprint. 1.2%/0.6% is that broken reading and is retired with the rest.
    ("diamond proud fraction", f"{proud['rootDiamondGem'][0]}%",
     ["82.4%", "93.4%", "93.8%", "95.8%", "54.3%", "93.6%", "1.2%", "0.6%"]),
    # The diamond against the layer it SITS ON, which is a different surface from the shell.
    # 44.9%/44.8% is what the same geometry read while the test compared pixels for identity: the
    # gem is 22% transmissive, so the opaque core behind it tinted its pixels without occluding
    # them. Retired as a figure, kept as an argument in that script's docstring. 99.1% is the cut
    # pair, whose buried tips were the last 0.9%.
    ("diamond seated on the core",
     f"{seated['rootDiamondGem'][0]}%" if seated else "n/a", ["44.9%", "44.8%", "99.1%"]),
    # The relief ladder, as the three lifts above the shell's own crest that `check_centerline.py`
    # now asserts. Recomputed here from the same parts.json rather than quoted from that script's
    # output, so a document cannot cite a band the build stopped satisfying. The retired strings
    # are the BOSS ladder this correction replaced — total Z extents as multiples of T, which is a
    # different quantity, not a different value of the same one.
    ("blade lift ladder", lifts,
     ["1.16–1.22", "1.28–1.36", "1.55–1.70", "1.200 / 1.330 / 1.570",
      "1.16-1.22", "1.28-1.36", "1.55-1.70"]),
    # (59.7, / (76.5, are the outer-surface solution, retired when the cap turned out to sit rim-
    # proud of the leather and the burial depth became geometry rather than the 5% overlap budget.
    # (54.8, / (70.2, are the same formula evaluated on the arm before integration #17 moved its
    # root to the jaws' outer corner. The rods are DERIVED from the arm, so moving the arm moves
    # them; that is the point of deriving them, and it is also why they have to be retired here.
    # (60.8, / (78.1, are the same formula evaluated on the arm before the 2026-08-11 amendment to
    # #17 moved the cap's centre one radius up its own normal. Same reason again: the rods are
    # DERIVED from the arm.
    ("upper driver root", f"({roots['upper'][0]:.1f},", ["(60.5,", "(59.7,", "(54.8,", "(60.8,"]),
    ("lower driver root", f"({roots['lower'][0]:.1f},", ["(77.4,", "(76.5,", "(70.2,", "(78.1,"]),
    # The arm's OUTER end, which is the spinner's axis and the one figure `CONNECTOR_LENGTH` moves
    # on its own — the roots above it are derived from the arm's ROOT and did not move at all when
    # the length changed. 81.942 is the X-solving length's answer, retired 2026-08-12 when the
    # length was directed back to 72; -18.346 was the end-cap centre it went with and -8.564 the
    # spinner seat that hung off it. The measurement 81.925 those numbers were solved against is
    # NOT retired — it is the crop's own reading and it is still true; what is retired is the
    # claim that the build sits on it.
    # 93.005 / -31.254 / -21.471 retired 2026-08-13 with the length becoming derived. The pattern
    # is now three deep and worth stating once: every value in this row is the SAME formula at a
    # different length, so they retire as a set each time the length moves, and the crop's own
    # 81.925 is never in the list — it is the measurement, not the build.
    # 103.903 / -34.185 retired 2026-08-08, and this time the length moved without being touched:
    # widening SPINNER_TOP_RADIUS moved where the shoulder's flank clears the arm's end-cap plane,
    # which is the offset the derived length is a function of. Same set, same rule.
    ("the arm's outer end and the spinner seat", f"{_built_axis:.3f}",
     ["81.942", "18.346", "8.564", "93.005", "31.254", "21.471", "103.903", "34.185"]),
    # The built length itself, in the assignment form that asserts it. Prose about the MEASUREMENT
    # — "L = 55", "54.97" — is deliberately not retired: §11 G4 has to be able to say what the
    # crop's X pin solves to, and deleting that would be erasing the evidence the directive
    # overruled rather than recording it.
    # Both spellings, because a document writes the constant in backticks and the factory does
    # not, and a net that only catches one of them catches neither in practice.
    # `CONNECTOR_LENGTH = 72` joins the list on 2026-08-13 in both spellings, for the same reason
    # 55 is here: a document that still writes the assignment is describing a build that no longer
    # exists. Prose about what 72 WAS — the directed value, what it missed — stays legal, because
    # §8 and §11 G4 have to be able to narrate the chain.
    # 88.7455 joins on 2026-08-08 in the assignment spellings AND as `L = 88.7455`, which is how
    # the results table and §11 G4 write the build's own row. Prose about the 2026-08-13 change
    # that produced it stays legal, same as 55 and 72: it says `the derived 88.7455`, not `L =`.
    ("the connector's built length", f"{_length:.4f}",
     ["CONNECTOR_LENGTH = 55", "CONNECTOR_LENGTH` = 55", "CONNECTOR_LENGTH = 55.0",
      "CONNECTOR_LENGTH = 72", "CONNECTOR_LENGTH` = 72", "CONNECTOR_LENGTH = 72.0",
      "CONNECTOR_LENGTH = 88.7455", "CONNECTOR_LENGTH` = 88.7455", "L = 88.7455"]),
    # The guard's underside opening, which has no threshold and is therefore exactly the kind of
    # figure that drifts unwatched — it was quoted in three documents and nothing held them to it.
    # 25.730 was the opening while the arms' root caps still straddled the jaws' corners; raising
    # them one radius up their own normals lifted each arm's inner silhouette with it and the gap
    # beside the grip column grew. It is still recorded rather than thresholded: the sketch draws
    # this region open and the model follows the sketch.
    ("guard underside opening", f"{_open_run:.3f}", ["25.730"]),
    # --- the seven-pass correction of 2026-08-10 retires these ----------------------------------
    # The tier-1 IoU of every pass except the blockout. It had its own family only from this pass:
    # it was quoted once, in §8's results table, and it went stale there for two passes because
    # nothing was watching a figure that appears exactly once.
    ("tier-1 IoU, other passes",
     f"{max(json.loads((A / 'gate' / f'tier1-{p}.json').read_text())['checks']['silhouetteIoU'] for p in ('material-pass', 'surface-pass', 'structural-pass', 'form-refinement')):.4f}",
     # 0.8206 is deliberately NOT retired here even though it is this family's previous live
     # value: it is the BLOCKOUT's live value today, and the two families read the same documents.
     # Retiring it makes every paragraph that correctly quotes today's blockout figure fail this
     # family instead. The blockout's own family already retires 0.8208, which is the pair's real
     # protection; a second net over the same string only fires on the truth.
     ["0.8555", "0.8538", "0.8547", "0.8573", "0.8497", "0.8374", "0.8364", "0.8207"]),
    # The stone's own thickness as a multiple of T. 0.4892 was the PLATEAU section and 0.4923 the
    # two shapes after it, both of them SEATED, so their floor was the surface under the stone.
    # The inlaid stone's floor is its socket, which is deeper: same quantity, different solid,
    # three times over now.
    ("the stone's thickness",
     f"{(_pb['rootDiamondGemFront']['maxZ'] - _pb['rootDiamondGemFront']['minZ']) / _T:.4f} T",
     ["0.4892 T", "0.4923 T"]),
    # Worst pointwise penetration of any BLADE layer, in normalized units. The jaws are excluded —
    # they are inside the crystal by named exception at 12.165, which is live and must stay
    # quotable. 0.091 was the plateau stone. 0.083 was the 錐冠's, and it retired on 2026-08-09 with
    # `loft`'s fixed diagonal rather than with any layer moving: the worst became the insert's
    # 0.020, and the stone read 0.000.
    # **The STONE left this family the same day**, with the inlaid directive: it is now inside its
    # host by the depth of its own socket, on purpose, and `check_centerline.py` bounds it there
    # the way it bounds the jaws. A family whose live value is an exception's own figure cannot
    # catch anything, so the exception is excluded here and asserted there.
    ("blade layer inside the shell",
     f"{max(v['shell']['worst'] for k, v in parts['shellPenetration']['parts'].items() if 'Clamp' not in k and 'Gem' not in k) * 100:.3f}",
     ["0.091", "0.083"]),
    # The stone's signed seat clearance. Both ends moved when the section changed, and the pair is
    # retired together because a paragraph quoting one of them is quoting the old geometry.
    # Written UNSIGNED on purpose: the records use a Unicode minus and this file would otherwise
    # be comparing "-0.0826" against "−0.0826" and never matching.
    # **Since 2026-08-09 this is the SOCKET's depth, not a clearance.** The stone's base is a plane
    # cut through the surface rather than a skin laid on it, so what the seat family measures is
    # how far the surface varies under the stone. Same expression, and it is left in place because
    # the numbers it retires are exactly the ones a document would still be quoting.
    ("the stone's seat clearance",
     f"{abs(min(parts['stackConformity']['layers'][g]['seat']['min'] for g in ('rootDiamondGemFront', 'rootDiamondGemRear'))) * 100:.4f}",
     ["0.0906", "0.1297", "0.0826"]),
    # The mirrored pair's outward-face colour delta. 0.000157 was the plateau's facet count.
    # 0.000311 was the 錐冠's, and it was never the stone's fault: `loft` cut the two halves on
    # opposite diagonals, so the pair was an exact mirror as a surface and not as a triangle list.
    # The shorter-diagonal split took it to zero, which is what let the crown be a POINT at all.
    ("mirrored pair colour delta",
     f"{parts['mirrorColour']['rootDiamondGem']['outward']['delta']:.6f}",
     ["0.000157", "0.000311"]),
    # The socket's own depths. Only the JAWS are in that list now: integrations #15/#16/#17 took
    # the grip column (11.179) and both arms (1.29) out of it entirely, and the arms measure
    # 0.000 today. 12.165 stays LIVE — it is still each jaw's own depth into the crystal.
    ("socket depths retired with #15/#16/#17", "retired", ["11.179", "1.29 units"]),
    # The pommel's radius. `POMMEL_RADIUS` is `GRIP_HALF_WIDTH` now, so the cone's base ring IS the
    # column's bottom ring and 11 is not a radius on this model any more — it is the ring's
    # front-view REACH, 11.087, which is a different quantity and written differently.
    # The live value is the ring's front-view REACH rather than "12", because 12 is a substring of
    # half the numbers in the folder and a family whose live value matches everything can never
    # fire. A record that has been corrected names 11.087; one that has not still says "radius 11".
    ("the pommel's base ring",
     f"{const(r'^const GRIP_HALF_WIDTH = (-?[\d.]+)') * math.cos(math.pi / const(r'^const POMMEL_SIDES = (-?[\d.]+)')):.3f}",
     ["maximum radius 11", "max radius 11", "inside radius 11"]),
    # The guard's own figures, retired with the three integrations. The daylight sweep's `gap`
    # clause and the jaw-bites-the-column seam are gone outright (see the block that replaced
    # them); the arm inset is gone with correction C's bisection; 31.735 was the shell's half-width
    # at the jaws' floor when its base still ran on down to -13, and 29.14 was the spec's mirror of
    # it. 1.200 was the 5% bite. 11.087 stays LIVE — it is still the grip column's front-view
    # reach, now as the number the jaws' floor has to cover rather than the number they bite into.
    # This family's "live value" is the WORD `retired`, not a number: these names and figures do
    # not have successors, they simply stopped existing, and a record is still allowed to explain
    # what went and why. What it may not do is describe one as though it were still there. So the
    # rule a paragraph has to satisfy is that it says so.
    ("guard constants retired with #15/#16/#17", "retired",
     ["arm inset", "CLAMP_INNER_X", "CLAMP_GRIP_OVERLAP", "GRIP_BURIAL", "CONNECTOR_INSET",
      "CONNECTOR_SHELL_OVERLAP", "31.735", "29.14", "1.200 by construction", "-12.78", "−12.78"]),
]

# `index.ts` used to be scanned too, because the exhibit card carried a `decisions[]` array of
# build-log prose that quoted both retired driver roots for a whole correction pass while every
# .md in the folder was clean. That array has since been removed from the registry entirely, so
# there is no longer any figure-bearing prose there to audit — only the doc links, checked below.
# If narrative prose ever returns to the exhibit record, it has to come back into this net.
SCANNED: list[tuple[str, str]] = [
    (str(doc.relative_to(V)), doc.read_text())
    for doc in sorted(V.rglob("*.md")) + sorted(V.glob("spec/*.sh"))
    if not str(doc.relative_to(V)).startswith("brief/")  # brief/ is supplied verbatim
]

for rel, text in SCANNED:
    line_no = 1
    # Scan by paragraph, not by line: a sentence narrating a change routinely wraps.
    for para in text.split("\n\n"):
        # "X → Y" and "from X to Y" narrate a change and may carry a retired figure alone.
        #
        # A table row used to get the same blanket pass just for starting with "|", and that hole
        # is how `confidence-report.md`'s Final-numbers table kept quoting a dead IoU through two
        # correction passes. A table now has to actually look like a before/after table — a
        # header cell saying so — instead of merely being a table.
        narrates = ("→" in para or re.search(r"from [\d.]+ to [\d.]+", para)
                    or re.search(r"\|\s*(before|after|was|now|earlier|previous)\b", para, re.I))
        for label, live, retired in FAMILIES:
            for bad in retired:
                if bad in para and live not in para and not narrates:
                    hit = next(l for l in para.splitlines() if bad in l)
                    fail.append(f"{rel}:~{line_no} {label}: {bad!r} quoted with no {live!r} "
                                f"nearby\n    {hit.strip()[:110]}")
        line_no += para.count("\n") + 2

# --- structural invariants -----------------------------------------------------------------
# The deleted components are named throughout the rejection lists, so prose is the wrong place
# to look for them. The artifact is the authority: they must not be BUILT.
for gone in ("centralGripSocket", "driverSocket"):
    if any(gone in nm for nm in names):
        fail.append(f"{gone} was rebuilt — correction pass 2 forbids it as a component")

# Every doc link on the exhibit card must resolve, or the page renders a dead entry.
# Keyed on assetDir, not slug: the route was renamed to ff7-cloud-strife-ultima-weapon while the
# asset and evidence folders kept the v2 name.
index = (ROOT / "src/utils/exhibits.ts").read_text()
block = index[index.index('assetDir: "ff7-cloud-strife-ultima-weapon"'):]
for f in re.findall(r'file: "([^"]+)"', block[: block.index("\n  },")]):
    if not (V / f).exists():
        fail.append(f"exhibits.ts links {f} — missing on disk")

# Nothing may build that the spec does not declare.
SPEC_JSON = V / "spec" / "object-sculpt-spec.json"
spec_ids = set(re.findall(r'"id": "([a-zA-Z0-9_]+)"', SPEC_JSON.read_text()))
undeclared = {n for n in names if n not in spec_ids and n != "ultimaWeaponV2"}
if undeclared:
    fail.append(f"built parts absent from the spec: {sorted(undeclared)}")


# --- the ASSEMBLY ANCHOR GRAPH -------------------------------------------------------------
# `parent` says who carries whom. `attachment.parentSocket` / `childSocket` say WHERE, and until
# 2026-08-10 nothing checked that those two names resolved to anything: **10 of the 22 attached
# components named a socket their own parent does not own**, and five of those named a socket id
# that existed nowhere in the file at all (`gem_mount_anchor` on four components, `hiltGroup_socket`
# on one). The other five named a socket that lives on some other component — the four rods
# reaching for `connector_anchor_*` on their grandparent, and the pommel reaching for the grip's
# `pommel_anchor` across a sibling edge. Every one of them was a plain string with nothing on the
# other end, and the spec read as though the model were anchored when it was not.
#
# Four clauses, and they close the loop in both directions:
#
#  1. every `parentSocket` is declared on the named parent, and every `childSocket` on the child;
#  2. the two land on the SAME WORLD POINT — `transform.position + localPosition`, both ends —
#     so a socket that gets moved on one side of a contact and not the other fails here rather
#     than at the next review. This is the clause with teeth: clause 1 only asks whether a name
#     resolves, and a name can resolve to the wrong place;
#  3. no ORPHAN sockets: every declared socket is referenced by an attachment or by a `joints`
#     entry. Without this the graph rots the other way — sockets accumulate that nothing uses,
#     and the next reader cannot tell which of them are load-bearing;
#  4. every `joints[]` entry names a component that exists and sockets that exist on both ends.
#
# Plus the boxes: each component's declared `dimensions` and `transform.position` must equal the
# BUILT bounding box. `author_spec.py` reads them out of the same manifest, so any difference
# means the spec was authored against a different capture than the one being audited.
ANCHOR_TOL = 3e-4  # world units; local positions are stored to 4 dp, so this is 3 rounding steps
BOX_TOL = 1e-3


def audit_anchor_graph(spec: dict) -> list[str]:
    out: list[str] = []
    comps = spec.get("componentTree") or []
    by_id = {c["id"]: c for c in comps}
    socket_local = {
        c["id"]: {s["id"]: s["localPosition"]
                  for s in ((c.get("actionProfile") or {}).get("sockets") or [])}
        for c in comps
    }
    used: set[tuple[str, str]] = set()

    def world(cid: str, sid: str) -> list[float] | None:
        local = socket_local.get(cid, {}).get(sid)
        if local is None:
            return None
        pos = by_id[cid]["transform"]["position"]
        return [pos[i] + local[i] for i in range(3)]

    for c in comps:
        cid, parent = c["id"], c.get("parent")
        att = c.get("attachment")
        if parent is None:
            if att is not None:
                out.append(f"{cid} is a root but carries an attachment")
            continue
        if not isinstance(att, dict):
            out.append(f"{cid} declares parent {parent!r} with no attachment contract")
            continue
        if parent not in by_id:
            out.append(f"{cid} names parent {parent!r}, which is not a component")
            continue
        if att.get("parentId") != parent:
            out.append(f"{cid} attachment.parentId {att.get('parentId')!r} != parent {parent!r}")
        ps, cs = att.get("parentSocket"), att.get("childSocket")
        pw, cw = world(parent, ps or ""), world(cid, cs or "")
        if pw is None:
            out.append(f"{cid} attachment.parentSocket {ps!r} is not declared on {parent} "
                       f"(it owns {sorted(socket_local.get(parent, {}))})")
        if cw is None:
            out.append(f"{cid} attachment.childSocket {cs!r} is not declared on {cid} "
                       f"(it owns {sorted(socket_local.get(cid, {}))})")
        if pw is not None and cw is not None:
            drift = max(abs(pw[i] - cw[i]) for i in range(3))
            if drift > ANCHOR_TOL:
                out.append(f"{cid}: socket {parent}.{ps} lands at {[round(v, 4) for v in pw]} but "
                           f"{cid}.{cs} lands at {[round(v, 4) for v in cw]} — {drift:.5f} world apart")
            used.add((parent, ps))
            used.add((cid, cs))

    for c in comps:
        cid = c["id"]
        for j in c.get("joints") or []:
            peer = j.get("withRef")
            if peer not in by_id:
                out.append(f"{cid} joint {j.get('id')!r} names {peer!r}, which is not a component")
                continue
            for owner, key in ((cid, "socketRef"), (peer, "peerSocketRef")):
                sid = j.get(key)
                if sid is None:
                    continue
                if sid not in socket_local.get(owner, {}):
                    out.append(f"{cid} joint {j.get('id')!r} {key} {sid!r} is not declared on {owner}")
                else:
                    used.add((owner, sid))

    for cid, owned in socket_local.items():
        for sid in owned:
            if (cid, sid) not in used:
                out.append(f"{cid}.{sid} is an orphan socket — no attachment and no joint uses it")

    for c in comps:
        cid = c["id"]
        if cid == "ultimaWeaponV2Root":
            lo = [min(p["bounds"][f"min{a}"] for p in parts["parts"]) for a in "XYZ"]
            hi = [max(p["bounds"][f"max{a}"] for p in parts["parts"]) for a in "XYZ"]
        elif cid in _pb:
            lo = [_pb[cid][f"min{a}"] for a in "XYZ"]
            hi = [_pb[cid][f"max{a}"] for a in "XYZ"]
        else:
            out.append(f"{cid} is declared in the spec but absent from parts.json")
            continue
        want_size = [hi[i] - lo[i] for i in range(3)]
        want_pos = [(hi[i] + lo[i]) / 2 for i in range(3)]
        got_size = [c["dimensions"][k] for k in ("width", "height", "depth")]
        got_pos = c["transform"]["position"]
        if max(abs(got_size[i] - want_size[i]) for i in range(3)) > BOX_TOL:
            out.append(f"{cid} dimensions {got_size} against the built box "
                       f"{[round(v, 4) for v in want_size]}")
        if max(abs(got_pos[i] - want_pos[i]) for i in range(3)) > BOX_TOL:
            out.append(f"{cid} transform.position {got_pos} against the built centre "
                       f"{[round(v, 4) for v in want_pos]}")
    return out


# --- the confidence table in the records against the confidences in the spec ----------------
# `confidence-report.md`'s table is the one place a component attribute is written down twice,
# and all three of the rows that could drift had: the jaws read 0.55 there against 0.60 in the
# spec, the spinner ends 0.70 against 0.65, the driver array 0.85 against 0.90. Nothing was
# looking, because the retired-figure net matches whole strings and "0.55" is a substring of
# half the numbers in the folder. This reads the table instead.
CONFIDENCE_ALIASES = {
    "{L,R}": ["Left", "Right"],
    "{Front,Rear}": ["Front", "Rear"],
    "{L,R}{Upper,Lower}": ["LeftUpper", "LeftLower", "RightUpper", "RightLower"],
}


def audit_confidence_table(spec: dict) -> list[str]:
    out: list[str] = []
    declared = {c["id"]: c["confidence"] for c in spec.get("componentTree") or []}
    text = (V / "spec" / "confidence-report.md").read_text()
    rows = re.findall(r"^\|\s*`([A-Za-z{},]+)`\s*\|\s*\**([\d.]+)\**\s*\|", text, re.M)
    checked = 0
    for name, value in rows:
        suffixes = [""]
        for token, expansions in CONFIDENCE_ALIASES.items():
            if name.endswith(token):
                name, suffixes = name[: -len(token)], expansions
        for suffix in suffixes:
            cid = name + suffix
            if cid not in declared:
                out.append(f"confidence-report.md names `{cid}`, which is not a component")
                continue
            checked += 1
            if abs(declared[cid] - float(value)) > 1e-9:
                out.append(f"confidence-report.md gives {cid} confidence {value} against the "
                           f"spec's {declared[cid]}")
    if checked < 12:
        out.append(f"only {checked} confidence rows matched the table's format — the parser has "
                   "gone stale and is no longer reading the report")
    return out


_spec_doc = json.loads(SPEC_JSON.read_text())
fail.extend(audit_confidence_table(_spec_doc))
_anchor_problems = audit_anchor_graph(_spec_doc)
fail.extend(_anchor_problems)
_attached = sum(1 for c in _spec_doc["componentTree"] if c.get("parent"))
_socket_count = sum(len((c.get("actionProfile") or {}).get("sockets") or [])
                    for c in _spec_doc["componentTree"])
_joint_count = sum(len(c.get("joints") or []) for c in _spec_doc["componentTree"])
print(f"GRAPH   {_attached} attachments, {_socket_count} sockets, {_joint_count} cross-branch "
      f"joints; {len(_anchor_problems)} unresolved")

# Bracketed against DOCTORED specs, one broken clause each — otherwise the block above is a
# check nobody has seen fail. Each mutation is the exact defect the clause exists to catch, and
# the first two are re-creations of what was actually in this file before 2026-08-10.
_BRACKETS: list[tuple[str, object]] = [
    # `hiltGroup_socket` is the literal string `driverArray` used to carry: the auto-generated
    # `f"{parent}_socket"` default, for a parent that declares its own sockets and therefore never
    # had one. `gem_mount_anchor` is a real socket today, so it cannot stand in for this clause.
    ("a parentSocket naming a socket that exists nowhere (the retired `hiltGroup_socket` bug)",
     lambda s: s["componentTree"][15]["attachment"].__setitem__("parentSocket", "hiltGroup_socket")),
    ("a parentSocket naming a socket owned by another component (the retired pommel bug)",
     lambda s: s["componentTree"][-1]["attachment"].__setitem__("parentSocket", "grip_anchor")),
    ("a socket moved on one side of a joint only",
     lambda s: s["componentTree"][-1]["actionProfile"]["sockets"][0]["localPosition"].__setitem__(1, 9.0)),
    ("a socket nothing references",
     lambda s: s["componentTree"][0]["actionProfile"]["sockets"].append(
         {"id": "spare_anchor", "localPosition": [0, 0, 0], "localRotation": [0, 0, 0]})),
    ("a joint pointing at a component that does not exist",
     lambda s: s["componentTree"][2]["joints"][0].__setitem__("withRef", "guardCore")),
    ("a component box that no longer matches the build",
     lambda s: s["componentTree"][2]["dimensions"].__setitem__("height", 9.9)),
]
for _label, _break in _BRACKETS:
    _doctored = json.loads(SPEC_JSON.read_text())
    _break(_doctored)
    _caught = audit_anchor_graph(_doctored)
    if not _caught:
        fail.append(f"the anchor-graph audit does NOT catch {_label} — the clause is dead")
    else:
        print(f"BRACKET anchor graph rejects {_label}: {_caught[0][:96]}")

print()
if fail:
    print("\n".join("FAIL " + f for f in fail))
    sys.exit(1)
print(f"PASS  {len(list(V.rglob('*.md')))} documents, every figure traced to an artifact")
