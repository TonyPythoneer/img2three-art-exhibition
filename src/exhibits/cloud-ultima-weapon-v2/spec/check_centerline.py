"""Assert the correction spec's §1: one strict vertical centreline through the whole sword.

Reads the built model's world-space part bounds (written by the harness into
`artifacts/ultima-v2/full/parts.json`) rather than the source, so this checks what was
actually built. Two families:

  * on-axis parts must be centred on X=0 — |minX + maxX| below tolerance;
  * mirrored pairs must be reflections of each other — |left.minX + right.maxX| below it too.

Run:  python3 spec/check_centerline.py [<parts.json>]
Exit code 1 if anything drifts, so it works as a gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT = HERE.parents[2].parent / "artifacts" / "ultima-v2" / "full" / "parts.json"

# World units; the model is 9.71 tall, so this is ~0.1 normalized units.
TOLERANCE = 0.001
# The factory's `U`: one normalized-1000 unit in world space. Distances the model authors in
# normalized units are printed back in them rather than in world units nobody types.
UNIT = 0.01

ON_AXIS = [
    "outerCrystalShell",
    "purpleEnergyInsertFront",
    "purpleEnergyInsertRear",
    "darkCoreTriangleFront",
    "darkCoreTriangleRear",
    "rootDiamondGemFront",
    "rootDiamondGemRear",
    "driverArray",
    "leatherGrip",
    "pointedMetalPommel",
]

MIRRORED = [
    ("crystalClampLeft", "crystalClampRight"),
    ("leatherConnectorLeft", "leatherConnectorRight"),
    ("spinnerEndLeft", "spinnerEndRight"),
    ("driverLeftUpper", "driverRightUpper"),
    ("driverLeftLower", "driverRightLower"),
]

# --- the relief ladder, as LIFT above the shell's own crest ---------------------------------
#
# This used to be a band on each layer's total Z extent as a multiple of T: insert 1.16-1.22 T,
# core 1.28-1.36 T, gem 1.55-1.70 T. Those bands described BOSSES -- solids centred on Z = 0 and
# bulging out through both faces -- and the blade no longer has any. The insert and the dark core
# are now SKINS: films laid on the shell's own front and rear surfaces, following it in X and in
# Y. A skin's bounding box is dominated by how much the surface under it varies across its own
# footprint, not by how thick the film is, so the old band could not tell a 1.4-thick film from a
# 5-thick one and re-fitting it would have been a relabel, not an assertion.
#
# What IS readable from bounding boxes, and IS the thing that matters, is
#
#     lift(layer) = layer.maxZ - shell.maxZ
#
# -- how far the layer's outermost surface stands beyond the shell's own deepest point. Both are
# measured at the blade's thickest station, which every blade layer's footprint covers (the shell
# reaches its 14 half-depth over Y = 70..110, and the insert, the core and the gem all span part
# of that), so it is a like-for-like comparison rather than a bbox artifact.
#
# Three things are then asserted, and between them they are strictly harder to satisfy than the
# bands they replace:
#
#   1. every lift is positive and the lifts strictly increase in this order. Nothing can sink
#      back inside the shell and the stack order cannot reverse -- which is exactly what the old
#      ladder existed for, and a material change still moves none of it, so "reveal the crystals
#      by dropping the shell's opacity" still fails here.
#   2. each SKIN's own step over the layer under it sits inside SKIN_STEP_BAND. This is the new
#      half: a skin cannot quietly grow back into a boss. The build this replaces would FAIL it
#      -- its insert stepped 0.100 T and its core a further 0.065 T, against a ceiling of 0.060.
#   3. the BODY's step over the last skin is at least GEM_STEP_FLOOR. The diamond has to stand
#      off the skins as a mounted stone, not sit flush as a coloured patch. The build this
#      replaces would fail this too, at 0.120 T against a floor of 0.25.
#
# `T` and `shell.maxZ` are read out of the build, so these are ratios against what was actually
# made rather than against numbers typed into the source.
LIFT_LADDER = [
    ("purpleEnergyInsert", "purpleEnergyInsertFront", "purpleEnergyInsertRear", "skin"),
    ("darkCoreTriangle", "darkCoreTriangleFront", "darkCoreTriangleRear", "skin"),
    ("rootDiamondGem", "rootDiamondGemFront", "rootDiamondGemRear", "body"),
]
# Multiples of T. A film thinner than the floor is a colour change with no body -- at ~1.02
# normalized units per pixel in the orthographic review captures, 0.035 T is one pixel of rim.
SKIN_STEP_BAND = (0.035, 0.060)
GEM_STEP_FLOOR = 0.25

# A split layer's two halves have to be a clean mirror pair about Z = 0. Splitting a part is the
# one edit that can defeat the old "centre Z is 0" test by passing it trivially -- one half alone
# is not centred, and dropping the test to make the build green would also drop the thing it
# guarded: relief extruded onto one face only. So the test gets STRICTER instead of looser.
#
# ALL THREE PAIRS ARE NOW "seated", AND THAT IS A SPEC CHANGE. This block used to read:
#
#   "cut"    the diamond: each half runs from the cut plane outward, so it must REACH Z = 0 and
#            not cross it. The two halves meet there with no gap and no overlap.
#   "seated" the two skins: each half sits entirely clear of the cut plane on its own side.
#
# The diamond was the cut pair, and "reaches Z = 0" is the same sentence as "is driven through the
# middle of the shell". `outerCrystalShell` is a SOLID with nothing inside it, so a stone that
# starts at the blade's mid-plane is a rejection condition and this assertion was requiring it:
# measured through the harness's stack probe, the old halves sat up to 14.000 units inside the
# crystal and 16.800 units inside the layer they are supposed to be MOUNTED ON, over 527 of 1008
# surface samples. The stone now grows out of `bladeStackTop` and stops there.
#
# Dropping "reaches the cut" would drop what it protected -- one boss carrying a thin backing
# plate -- so it is REPLACED, not deleted, by three assertions that together are strictly harder:
#
#   1. the mirror test at BOTH ends, which both kinds already had and which is what actually rules
#      out a boss-plus-plate;
#   2. a THICKNESS floor on each half, below -- a plate keeps its crown and loses its body, and
#      that is exactly what `maxZ - minZ` sees;
#   3. the pointwise stack probe, below -- each half's inner face has to stay OUTSIDE the dark
#      core's own surface, which is the fact "reaches the cut" was standing in for and getting
#      backwards.
SPLIT_PAIRS = [
    ("purpleEnergyInsertFront", "purpleEnergyInsertRear", "seated"),
    ("darkCoreTriangleFront", "darkCoreTriangleRear", "seated"),
    # INLAID since 2026-08-09, and the word is the whole of the difference: a seated layer's
    # underside follows the surface it lies on, an inlaid one's is a PLANE cut through it. The
    # mirror test, the thickness floor and "clear of the cut plane" apply to both and are what
    # this row still asserts; the flush family below drops the stone and `INLAID_PARTS` replaces
    # it.
    ("rootDiamondGemFront", "rootDiamondGemRear", "inlaid"),
]

# Multiples of T, and only the stone answers to it: a skin is a film and is supposed to be thin.
#
# 0.35 is derived rather than judged -- it is the stone's own designed rise from its seat,
# `(GEM_RELIEF_STEP + GEM_CROWN_RISE) / T` = (3.36 + 6.46) / 28 -- so a diamond that keeps its
# crown depth while its underside creeps up to meet it fails here. The build measures 0.4923 T,
# the extra being the culet's seat sitting lower on the blade than the waist's.
BODY_THICKNESS_FLOOR = {"rootDiamondGem": 0.35}

# --- the shell is a SOLID, and so is every layer's own host ----------------------------------
#
# `shellPenetration` is written by the harness (src/pages/ultima-v2-harness.vue), which samples
# every part's triangles on a barycentric lattice and rays each sample down onto the surfaces it
# is supposed to be lying on. Bounding boxes cannot ask this: every blade layer's box overlaps the
# shell's box BY CONSTRUCTION, precisely because the layers sit on the shell.
#
# Two readings per part. `shell` is against `outerCrystalShell` alone -- nothing may be inside the
# crystal. `stack` is against everything under that layer in the relief ladder, so the dark core
# answers to the insert as well and the diamond answers to both skins; that is the reading that
# says the stone GROWS OUT OF the core rather than merely clearing the crystal.
#
# The tolerance is bracketed, not chosen. Measured through the same probe:
#
#                            vs shell   vs stack        (normalized units, 1 unit ~ 1 render px)
#   the build this replaces   insert       4.894 / 4.894
#                             dark core    0.249 / 1.649
#                             diamond     14.000 / 16.800
#   this build                insert       0.424 / 0.424
#                             dark core    0.000 / 0.036
#                             diamond      0.203 / 0.252
#
# **The tolerance is 0.20 normalized units, down from 1.0, and the question it bounds is now
# TWO-SIDED.** See `FLUSH` below: `shellPenetration` only ever reported `max(host - |z|)` clamped
# at zero, so a layer floating clear of its host scored a perfect 0.000, and three did.
#
# The residual is not slop, it is linearization, and it has two terms that shrink together: a
# layer's seat is a straight ruling between its own rings, and the surface it is seated on is
# `loft`'s triangulation of the shell rather than the shell's analytic section. Both depart from
# that section in the middle of a band and agree with it on the rails, by more the longer the band
# and the faster the section moves along it. The shell's lower trapezoid is subdivided into four
# bands for that reason, and this figure is what makes that subdivision LOAD-BEARING rather than a
# preference. Measured through the probe on otherwise identical geometry, artifacts under
# `artifacts/ultima-v2/diag/bracket-trapezoid-*/`, producer `diag/bracket_flush.py`:
#
#     trapezoid as ONE band  (Y = 13 -> 55)   stone's seat  -0.2017 .. +0.6203   FAILS
#     halved                 (+ Y = 34)                     -0.1532 .. +0.2991   FAILS
#     quartered              (+ 23.5, 34, 44.5)             -0.0906 .. +0.1297   passes
#
# 0.20 is the geometric midpoint of the last two — 1.54x above what this build carries and 1.50x
# below the coarsest mesh it has to reject — so it is bracketed on BOTH sides rather than set
# above a residual and left there. Every defect §3 lists is 10x to 22x over it. One normalized
# unit is about one pixel in the orthographic review captures, so this is a fifth of a pixel.
SHELL_SOLID_TOLERANCE = 0.002  # world units = 0.20 normalized units
BLADE_LAYERS = [
    "purpleEnergyInsertFront",
    "purpleEnergyInsertRear",
    "darkCoreTriangleFront",
    "darkCoreTriangleRear",
    "rootDiamondGemFront",
    "rootDiamondGemRear",
]
# The two jaws ARE inside the crystal, on purpose: they back the shell's base edge from the
# centreline out to its own outer corner, so no pale wedge can show between them -- see the
# shell/clamp flush equality above. Pulling them out would re-open that joint. So the exception is
# named rather than hidden, and it is BOUNDED: a socket part may be inside the shell only at or
# below the diamond's waist, which is `CLAMP_OUTLINE`'s inner-upper vertex and the top of the
# socket. A jaw that grew up the blade fails.
#
# **The list has been THREE parts longer than this and it is down to two on 2026-08-07, with the
# guard integrations.** It is a NAMED list rather than a predicate precisely so that shrinking it
# is an edit someone has to make and defend:
#
#   · `leatherGrip` was admitted first for its TANG and then for the plain column that replaced
#     it, on the argument that the shell's base cone ran down INSIDE the guard so the leather
#     contained the crystal's root. #15 took the base cone back up to the jaws' floor and #16
#     landed the column's top face on that same plane, so the two share a plane and nothing else.
#   · `leatherConnectorLeft/Right` came in with correction C, which slid each arm inward until its
#     root cap was buried behind the shell's lower slanted edge. #17 pins the cap's centre to the
#     jaws' outer corner and rakes it at the shell's own taper instead, which puts the cap PLANE
#     through the crystal's lateral edge: the arm is against the flank, not inside it. Measured
#     rather than argued -- both arms read `into the shell 0.000 u`, so they now pass the same
#     0.20 bound every blade layer is held to, with no exception at all.
#
# Admitting a part to an exception it no longer needs is how an exception list stops describing
# anything. If the column is ever pushed back up between the jaws, or an arm slid back inside the
# crystal, this list is the first thing that has to change and it will fail loudly first.
SOCKET_PARTS = {
    "crystalClampLeft",
    "crystalClampRight",
}
SOCKET_CEILING_Y = 0.55  # world = GEM_WAIST_Y

# --- and the stone, which is SET INTO the crystal rather than laid on it ---------------------
#
# The third kind of relationship on this blade, directed 2026-08-09. A SKIN follows its host; the
# JAWS pass through the shell's base; the STONE is sunk into a socket. What forced it: the surface
# under the stone climbs 5.8 normalized units from the culet to its top vertex — 1.2 of the shell's
# own taper and one 2.8 STEP where both skins begin on the authority line — so a stone that follows
# it stands 2.8 further out over its upper half than over its lower half, which is what the side
# view showed and what no shape of stone can fix.
#
# So the exception is named and BOUNDED, the same way the jaws' is, and the bound is the socket's
# own depth. The stone's base plane is the LOWEST the surface gets under its footprint and its
# girdle is the HIGHEST plus one relief step, so the deepest the stone can be inside its host is
# exactly `highest - lowest`: 16.8 - 11.0 = 5.8. A stone that reads deeper than that is not in a
# socket, it is falling through the blade.
#
# 0.10 of headroom, and it is for the model's own sampling rather than for slack: the factory finds
# the two extremes on a 41 x 41 lattice over the rhombus, and a lattice can miss a piecewise-linear
# surface's true minimum by a little. Measured on this build: 5.800 into the stack, 3.000 into the
# shell (the difference is the two skins, which the stone passes through on its way in).
INLAID_PARTS = {
    "rootDiamondGemFront",
    "rootDiamondGemRear",
}
GEM_SOCKET_DEPTH = 0.058 + 0.001  # world = 5.8 normalized units of socket + 0.1 of lattice

# --- FLUSH: the layers do not merely stay out of their host, they LIE ON it ------------------
#
# "貼在 outerCrystalShell 表面上，必須是完整貼齊" is a two-sided requirement and every assertion
# above it was one-sided. `shellPenetration` reports `max(host - |z|)` and clamps at zero, so a
# film hovering half a unit above the crystal scores 0.000 and passes -- and a film that floats
# is not laid on anything, it is a second body with a slot of air under it.
#
# `stackConformity` (harness) splits each layer's triangles by which way they look and measures a
# SIGNED clearance, `|z| - hostSurfaceZ`, on the two families that answer to the host:
#
#   seat   the underside. Flush <=> clearance == 0, so this row is |min| and |max| together.
#   outer  the visible face. For a FILM, flush <=> clearance == the film's own nominal thickness
#          everywhere on its footprint -- which is what says it has not been thinned or inflated
#          somewhere in the middle. The stone answers to no such number: its outer face is a
#          crown, not an offset, so it is measured and printed but not bounded here.
#
# Fed the geometry this correction replaces, the seat row fails on all four counts and the old
# one-sided probe saw none of them:
#
#   the stone crossing the films' base step with no ledge in its underside     +3.4130
#   a film's apex closed at its OUTER depth, so the tip is a wedge of air      +1.4000
#   `|x| <= halfWidth` counting a film of ZERO width as covering the axis      +2.8000
#   the stone's seat ruled straight across the shell's own Y = 70 knee         -0.2515
#
# **The stone left this family on 2026-08-09** and is asserted by `INLAID_PARTS` instead. It is
# not an exemption: an inlaid stone answers a harder question than a seated one, because "the base
# is a PLANE" and "the plane is at or under the host everywhere" together say there is no air
# under it AND that it has not drifted out of its socket, which is both directions of the same
# 完整貼齊 this family asks of a film. What it stops answering is "the underside follows the host",
# which is the thing the directive removed.
FLUSH_LAYERS = {
    "purpleEnergyInsertFront": 0.05,
    "purpleEnergyInsertRear": 0.05,
    "darkCoreTriangleFront": 0.05,
    "darkCoreTriangleRear": 0.05,
}

# How far the stone's base plane may sit ABOVE the surface under it: air, and there should be
# none. Not zero, for the same reason `GEM_SOCKET_DEPTH` carries headroom — the factory picks the
# plane off a 41 x 41 lattice, so it can land a hair above the true minimum. 0.05 normalized units
# is a fiftieth of a source pixel, and the build reads 0.0255.
INLAID_AIR_TOLERANCE = 0.0005  # world = 0.05 normalized units

# Correction D asks where the stone's MASS sits, not where its box is, and the two answers differ
# by however much the rhombus is skewed -- a box stays centred between the two tips however far
# the waist has slid. The tolerance is one order coarser than TOLERANCE because the quantity is a
# triangle-area-weighted sum over a five-station lathe rather than a vertex coordinate: the stone
# is symmetric in OUTLINE about its waist but not in DEPTH, because `gemDepthAt` reads a different
# stack above the waist than below it, so the surface centroid sits a little under the waist by
# construction. Bracketed both ways rather than chosen: this build measures 0.0036 world and the
# smallest thing the row has to catch is a waist displaced by one source pixel, 2.34 normalized
# units, which moves the centroid by the same amount and scores 2.3x the tolerance.
GEM_WAIST_TOLERANCE = 0.01  # world units = 1.0 normalized unit

# --- a mirrored pair has to mirror its COLOUR too --------------------------------------------
#
# Every assertion above is about where the two halves are; this is the one about what they look
# like, and it had no home until the correction of 2026-08-08. `applyFacetSteps` quantises each
# triangle against a key carrying +0.66 in Z, so a face and its mirror image landed on opposite
# sides of the quantiser and the two films' shell-facing undersides came out at a linear-light
# ratio of 1.2003 on the same surface — the front half's at sRGB (78.67, 43.82, 164.43) against
# the rear half's (85.83, 48.18, 178.52), measured unlit so the pixel IS the vertex colour
# (`artifacts/ultima-v2/diag/*-flatInsert{Front,Rear}.png`). The rear half now gets the mirrored
# key, so mirror-image faces score the same step.
#
# One 8-bit code, and the residual it has to accommodate is real rather than slack. The two halves
# are exact mirrors as SURFACES but not as triangle lists — `loft` splits every quad from
# `lower[i]` to `upper[i+1]` and `mirrorRearRing` reverses the ring order, so the rear half cuts
# each mirrored quad along the other diagonal. On a non-planar quad the two cuts give slightly
# different normals, and a normal near a quantiser boundary can land on the other step. Measured on
# this build: 0.000000 for both skins, 0.000318 for the diamond, against a tolerance of 0.003922.
#
# Bracketed by rebuilding the same geometry with the key left un-mirrored, which is the defect:
# 0.0086 / 0.0077 on the dark core, 0.0828 / 0.0792 on the insert, 0.2401 / 0.1288 on the diamond
# (inward / outward). The smallest of those is 24× the residual and 2.0× the tolerance.
MIRROR_COLOUR_TOLERANCE = 1 / 255

# The exact physical component contract. Anything else built, or anything here missing, is a
# rejection condition -- including the component families earlier passes invented
# (centralGripSocket, the four driverSocket meshes, and the guardCore bridge, whose job the two
# jaws' own flat floor now does), which is why this is asserted rather than assumed.
EXPECTED_PARTS = {
    "outerCrystalShell",
    "purpleEnergyInsertFront",
    "purpleEnergyInsertRear",
    "darkCoreTriangleFront",
    "darkCoreTriangleRear",
    "rootDiamondGemFront",
    "rootDiamondGemRear",
    "crystalClampLeft",
    "crystalClampRight",
    "leatherConnectorLeft",
    "leatherConnectorRight",
    "driverLeftUpper",
    "driverLeftLower",
    "driverRightUpper",
    "driverRightLower",
    "spinnerEndLeft",
    "spinnerEndRight",
    "leatherGrip",
    "pointedMetalPommel",
}
ORGANISATIONAL = {"bladeGroup", "hiltGroup", "driverArray"}


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    manifest = json.loads(path.read_text())
    bounds = {p["name"]: p.get("bounds") for p in manifest["parts"]}
    centroids = {p["name"]: p.get("centroid") for p in manifest["parts"]}
    failures: list[str] = []

    built = {p["name"] for p in manifest["parts"]} - ORGANISATIONAL
    for extra in sorted(built - EXPECTED_PARTS):
        failures.append(f"{extra}: built but not in the component contract")
        print(f"OFF {extra:<24} not in the contract")
    for missing in sorted(EXPECTED_PARTS - built):
        failures.append(f"{missing}: in the contract but not built")
        print(f"OFF {missing:<24} missing from the build")
    print(f"ok  component contract       {len(built)} built / {len(EXPECTED_PARTS)} specified")

    # Correction B, 2026-08-08: the clamps' lower edge is one horizontal line AND the shell's own
    # lowest edge is flush with it. This used to be the one-sided `shell.minY >= clamp.minY` --
    # "no pale crystal below the clamp bases" -- which a jaw hanging 7 units below the crystal
    # satisfies just as well as a flush joint does, and that is exactly what the build carried:
    # the jaws' outer vertex sat at Y = 6 against a shell base at Y = 13.
    #
    # It is now an EQUALITY, and it is strictly stronger: it still forbids pale crystal below the
    # jaws (slack < 0 fails, as before) and it additionally forbids the jaws dangling below the
    # crystal (slack > 0 fails, which the old form allowed). Both directions are rejection
    # conditions of correction B, so both are asserted.
    #
    # The tolerance is TOLERANCE, the same 0.001 world units (0.1 normalized) every other
    # geometric equality in this file uses, and it is not slack: since integration #15 the two
    # numbers are the same constant read out of the same table -- `SHELL_BASE_Y` IS
    # `CLAMP_FLOOR_Y` IS `CLAMP_OUTLINE`'s outer lower vertex -- so the only thing between them is
    # the float32 round trip through the vertex buffer, which is ~1e-7 world units here. Anything
    # larger than 0.001 means someone typed a second number instead of reusing the first.
    #
    # It failed for one build, on purpose and knowingly: the pass that made the jaws a TRIANGLE
    # moved their floor from -13 to +13 and left the shell's base at -13, which this read as
    # "outerCrystalShell reaches 0.2600 below the clamp base". #15 is the other half of that edit.
    shell, clamp = bounds.get("outerCrystalShell"), bounds.get("crystalClampRight")
    if shell and clamp:
        slack = shell["minY"] - clamp["minY"]
        status = "ok " if abs(slack) <= TOLERANCE else "OFF"
        print(f"{status} shell flush on clamp base   shell minY − clamp minY = {slack:+.6f}")
        if slack < -TOLERANCE:
            failures.append(
                f"outerCrystalShell reaches {-slack:.4f} below the clamp base "
                "(white crystal below the clamps is a rejection condition)"
            )
        elif slack > TOLERANCE:
            failures.append(
                f"crystalClamp hangs {slack:.4f} below outerCrystalShell's own base — correction "
                "B requires the jaws' horizontal lower edge to be FLUSH with the shell's lowest "
                "edge, not merely below it"
            )

    # --- correction D: one horizontal line four features answer to -----------------------------
    # `CLAMP_OUTLINE`'s inner-upper vertex is the authority, and the shell's lower taper, both
    # blade skins and the diamond's own waist are pinned to it. Three of the four are checkable
    # from bounds; the diamond's is not, because a rhombus whose waist has drifted still has a box
    # centred between its tips, so it is checked on the mass instead (`centroid`, from the
    # harness). The clamp's apex is read off the built jaw rather than from the source, so a jaw
    # rebuilt to a different outline fails here instead of being taken on trust.
    jaw = bounds.get("crystalClampRight")
    if jaw:
        authority = jaw["maxY"]
        print(f"    authority line           clamp apex Y = {authority / UNIT:.2f}")
        pinned = [
            ("purpleEnergyInsertFront", "minY", "the insert skin's lower edge"),
            ("purpleEnergyInsertRear", "minY", "the insert skin's lower edge"),
            ("darkCoreTriangleFront", "minY", "the dark core skin's lower edge"),
            ("darkCoreTriangleRear", "minY", "the dark core skin's lower edge"),
        ]
        for name, key, what in pinned:
            box = bounds.get(name)
            if not box:
                continue
            off = box[key] - authority
            ok = abs(off) <= TOLERANCE
            print(
                f"{'ok ' if ok else 'OFF'} {name:<24} {what} at "
                f"{box[key] / UNIT:.2f}, off the authority line by {off / UNIT:+.3f}"
            )
            if not ok:
                failures.append(
                    f"{name}: {what} sits at Y = {box[key] / UNIT:.2f} against the clamp apex's "
                    f"{authority / UNIT:.2f} — correction D pins them to one line"
                )
        for name in ("rootDiamondGemFront", "rootDiamondGemRear"):
            c = centroids.get(name)
            if c is None:
                failures.append(
                    f"{name}: parts.json carries no centroid — re-capture the renders with the "
                    "current harness; without it nothing checks the stone's waist against the "
                    "authority line"
                )
                continue
            off = c[1] - authority
            ok = abs(off) <= GEM_WAIST_TOLERANCE
            print(
                f"{'ok ' if ok else 'OFF'} {name:<24} centroid Y {c[1] / UNIT:.3f}, off the "
                f"authority line by {off / UNIT:+.3f}"
            )
            if not ok:
                failures.append(
                    f"{name}: its centroid sits at Y = {c[1] / UNIT:.3f} against the clamp apex's "
                    f"{authority / UNIT:.2f} — correction D pins the stone's own waist to that line"
                )

    def depth(name: str) -> float | None:
        b = bounds.get(name)
        return None if not b else b["maxZ"] - b["minZ"]

    shell_box = bounds.get("outerCrystalShell")
    T = depth("outerCrystalShell")
    if not T or not shell_box:
        failures.append("outerCrystalShell: no bounds, cannot check the relief ladder")
    else:
        crest = shell_box["maxZ"]
        # The shell itself is the only blade layer still centred on the cut plane, and it has to
        # stay that way: an off-centre shell would move every lift below by the same amount and
        # the ladder would still look fine.
        if abs(shell_box["minZ"] + shell_box["maxZ"]) > TOLERANCE:
            centre = (shell_box["minZ"] + shell_box["maxZ"]) / 2
            failures.append(
                f"outerCrystalShell: centre Z is {centre:+.5f}, not 0 — every lift below is "
                "measured against its crest, so an off-centre shell hides a one-sided blade"
            )

        previous = 0.0
        for label, front, rear, kind in LIFT_LADDER:
            fb, rb = bounds.get(front), bounds.get(rear)
            if not fb or not rb:
                failures.append(f"{label}: not both halves present in the built model")
                continue
            lift = fb["maxZ"] - crest
            step = lift - previous
            if kind == "skin":
                lo, hi = SKIN_STEP_BAND
                ok = lo <= step / T <= hi
                want = f"a skin: {lo}–{hi} T over the layer under it"
            else:
                lo, hi = GEM_STEP_FLOOR, float("inf")
                ok = step / T >= GEM_STEP_FLOOR
                want = f"a body: at least {GEM_STEP_FLOOR} T over the layer under it"
            print(
                f"{'ok ' if ok and step > 0 else 'OFF'} {label:<24} lift {lift / T:+.4f} T   "
                f"step {step / T:+.4f} T   ({want})"
            )
            if step <= 0:
                failures.append(
                    f"{label}: steps {step / T:+.4f} T over the layer under it — the stack order "
                    "has reversed, or this layer has sunk back inside the one below"
                )
            elif not ok:
                failures.append(
                    f"{label}: steps {step / T:.4f} T over the layer under it, outside "
                    f"{lo}–{hi} T. {want}"
                )
            # Rear half's own lift, so a lopsided pair cannot pass on the front half alone.
            rear_lift = -rb["minZ"] - crest
            if abs(rear_lift - lift) > TOLERANCE:
                failures.append(
                    f"{label}: front lifts {lift:.5f} and rear lifts {rear_lift:.5f} — the relief "
                    "is deeper on one face than on the other"
                )
            previous = lift

        for front, rear, kind in SPLIT_PAIRS:
            fb, rb = bounds.get(front), bounds.get(rear)
            if not fb or not rb:
                failures.append(f"{front}/{rear}: not both present in the built model")
                continue
            label = front.replace("Front", "")
            # Both kinds: mirrored at BOTH ends. That is what rules out one boss carrying a thin
            # backing plate, and it does not care where on the axis the pair sits.
            checks = {
                "outer mirror": abs(fb["maxZ"] + rb["minZ"]),
                "inner mirror": abs(fb["minZ"] + rb["maxZ"]),
            }
            worst = max(checks.values())
            ok = worst <= TOLERANCE
            # Every pair is seated: each half sits entirely clear of the cut plane on its own
            # side, with the shell's own solid body between them. Reaching Z = 0 means the half
            # is driven through the crystal rather than laid on it.
            if fb["minZ"] <= TOLERANCE or rb["maxZ"] >= -TOLERANCE:
                ok = False
                failures.append(
                    f"{front}/{rear}: a half reaches the cut plane "
                    f"(front minZ {fb['minZ']:+.5f}, rear maxZ {rb['maxZ']:+.5f}) — a seated "
                    "layer sits on the surface under it, not through the shell's middle"
                )
            floor = BODY_THICKNESS_FLOOR.get(label)
            if floor is not None:
                for piece, box in ((front, fb), (rear, rb)):
                    thickness = (box["maxZ"] - box["minZ"]) / T
                    if thickness < floor:
                        ok = False
                        failures.append(
                            f"{piece}: {thickness:.4f} T thick against a floor of {floor} T — "
                            "the stone has flattened into a plate on the skins. This is half of "
                            "what the retired 'reaches the cut' assertion was protecting"
                        )
                    else:
                        print(f"ok  {piece:<24} body thickness {thickness:.4f} T (≥ {floor})")
            print(
                f"{'ok ' if ok else 'OFF'} {label:<24} {kind:<6} pair, worst error {worst:.5f}"
                f"   front {fb['minZ']:+.4f}…{fb['maxZ']:+.4f}  rear {rb['minZ']:+.4f}…{rb['maxZ']:+.4f}"
            )
            for what, err in checks.items():
                if err > TOLERANCE:
                    failures.append(f"{front}/{rear}: {what} is off by {err:.5f}")
            if fb["maxZ"] <= 0 or rb["minZ"] >= 0:
                failures.append(
                    f"{front}/{rear}: a half has no depth on its own side of the cut — "
                    "the pair is not a front piece and a rear piece"
                )

    # --- the shell is a solid, and every layer sits ON its host rather than IN it ------------
    penetration = manifest.get("shellPenetration")
    if not penetration:
        failures.append(
            "parts.json carries no shellPenetration block — re-capture the renders with the "
            "current harness; without it nothing checks that the crystal is solid"
        )
    else:
        u = UNIT  # everything below is printed in normalized units, which is how the model reads
        for name, reading in sorted(penetration["parts"].items()):
            shell_in = reading["shell"]
            stack_in = reading["stack"]
            if name in SOCKET_PARTS:
                top = shell_in["insideMaxY"]
                inside_ok = top is None or top <= SOCKET_CEILING_Y + TOLERANCE
                print(
                    f"{'ok ' if inside_ok else 'OFF'} {name:<24} socket, inside the crystal to "
                    f"{0.0 if top is None else top / u:+.2f} (ceiling {SOCKET_CEILING_Y / u:.2f})"
                )
                if not inside_ok:
                    failures.append(
                        f"{name}: inside the shell up to Y = {top / u:.2f}, above the socket's "
                        f"ceiling of {SOCKET_CEILING_Y / u:.2f} — the two jaws and the two arms "
                        "may pass through the shell's base and its lower flanks, and nowhere else"
                    )
                continue
            asked = [("shell", shell_in)]
            if name in BLADE_LAYERS:
                asked.append(("stack", stack_in))
            # An inlaid part is inside its host by construction; what it may not do is go deeper
            # than its own socket. Same shape of exception as the jaws', a different bound.
            bound = GEM_SOCKET_DEPTH if name in INLAID_PARTS else SHELL_SOLID_TOLERANCE
            for what, entry in asked:
                deep = entry["worst"]
                inside_ok = deep <= bound
                x, y, z = entry["worstAt"]
                print(
                    f"{'ok ' if inside_ok else 'OFF'} {name:<24} into the {what:<5} "
                    f"{deep / u:.3f} u at ({x / u:.1f}, {y / u:.1f}, {z / u:.1f})"
                )
                if not inside_ok:
                    failures.append(
                        f"{name}: reaches {deep / u:.3f} normalized units inside the {what} at "
                        f"(x {x / u:.1f}, y {y / u:.1f}, z {z / u:.1f}), against a tolerance of "
                        f"{bound / u:.2f}. "
                        + (
                            "An inlaid stone sits in a socket as deep as the surface under it "
                            "varies, and no deeper"
                            if name in INLAID_PARTS
                            else "The shell is a solid body and every layer lies ON the surface "
                            "under it"
                        )
                    )

    # --- and lying ON it is a two-sided question: the seat is FLUSH, not merely clear ---------
    conformity = manifest.get("stackConformity")
    if not conformity:
        failures.append(
            "parts.json carries no stackConformity block — re-capture the renders with the "
            "current harness; without it nothing checks that a layer is FLUSH on its host "
            "rather than merely out of it"
        )
    else:
        u = UNIT
        for name, nominal in FLUSH_LAYERS.items():
            entry = conformity["layers"].get(name)
            if not entry:
                failures.append(f"{name}: no conformity reading — the harness did not measure it")
                continue
            seat = entry["seat"]
            worst = max(abs(seat["min"]), abs(seat["max"]))
            flush = worst <= SHELL_SOLID_TOLERANCE
            lo, hi = seat["minAt"], seat["maxAt"]
            print(
                f"{'ok ' if flush else 'OFF'} {name:<24} seat flush "
                f"{seat['min'] / u:+.4f} … {seat['max'] / u:+.4f} u   "
                f"(mean {seat['mean'] / u:+.4f}, rms {seat['rms'] / u:.4f}, "
                f"{seat['samples']} samples)"
            )
            if not flush:
                where = lo if abs(seat["min"]) > abs(seat["max"]) else hi
                failures.append(
                    f"{name}: its underside is {worst / u:.4f} normalized units off the surface "
                    f"it is lying on at (x {where[0] / u:.1f}, y {where[1] / u:.1f}, "
                    f"z {where[2] / u:.1f}), against a tolerance of "
                    f"{SHELL_SOLID_TOLERANCE / u:.2f}. A layer that floats is not laid on "
                    "anything and a layer that sinks is inside its host — 完整貼齊 is both"
                )
            # A FILM's outer face is its seat plus its own nominal thickness, everywhere.
            outer = entry["outer"]
            want = nominal * T
            drift = max(abs(outer["min"] - want), abs(outer["max"] - want))
            even = drift <= SHELL_SOLID_TOLERANCE
            print(
                f"{'ok ' if even else 'OFF'} {name:<24} film thickness "
                f"{outer['min'] / u:.4f} … {outer['max'] / u:.4f} u against a nominal "
                f"{want / u:.4f}"
            )
            if not even:
                failures.append(
                    f"{name}: its outer face runs {drift / u:.4f} normalized units off the "
                    f"nominal {want / u:.3f} it is supposed to stand above its own seat — the "
                    "film has been thinned or inflated somewhere inside its own footprint"
                )

        # --- the stone is INLAID: its base is a PLANE, and the plane is under the host --------
        #
        # Two clauses, and together they are the inlaid form of 完整貼齊. `stackConformity`'s seat
        # family measures `|z| - hostSurfaceZ` on the underside, so for a base that is one plane
        # its SPREAD over that family is the host's own variation and its MAXIMUM is the air gap.
        #
        #   spread  == the socket's depth  <=>  the base is flat and the socket is cut to fit
        #   max     <= 0                   <=>  no air anywhere under the stone
        #
        # A base that went back to following the host would collapse the spread to nothing and
        # fail the first; a base lifted out of its socket would push the max positive and fail the
        # second. Neither is reachable by editing one number, which is the point.
        #
        # **Bracketed against a real build rather than a doctored one**: the SEATED stone this
        # replaces, measured two edits earlier, read `-0.0001 … +0.1146` — spread 0.1147 against
        # the socket's 5.90, which is 50x outside the flat clause, and air +0.1146 against 0.05,
        # 2.3x outside the dry one. So both clauses reject the geometry that was shipping the day
        # before, which is the only bracket that matters here. This build reads spread 5.8258 and
        # air +0.0255.
        for name in sorted(INLAID_PARTS):
            entry = conformity["layers"].get(name)
            if not entry:
                failures.append(f"{name}: no conformity reading — the harness did not measure it")
                continue
            seat = entry["seat"]
            spread = seat["max"] - seat["min"]
            air = seat["max"]
            flat = abs(spread - GEM_SOCKET_DEPTH) <= GEM_SOCKET_DEPTH * 0.05
            dry = air <= INLAID_AIR_TOLERANCE
            print(
                f"{'ok ' if flat and dry else 'OFF'} {name:<24} inlaid base "
                f"{seat['min'] / u:+.4f} … {seat['max'] / u:+.4f} u   "
                f"(socket {spread / u:.4f} against {GEM_SOCKET_DEPTH / u:.2f}, "
                f"{seat['samples']} samples)"
            )
            if not flat:
                failures.append(
                    f"{name}: its underside spans {spread / u:.4f} normalized units against the "
                    f"socket's own {GEM_SOCKET_DEPTH / u:.2f} — a flat base under a surface that "
                    "varies reads the variation exactly, so this is the base following its host "
                    "again, or the socket no longer cut to the surface it is cut into"
                )
            if not dry:
                failures.append(
                    f"{name}: its base plane stands {air / u:.4f} normalized units ABOVE the "
                    f"surface under it at (x {seat['maxAt'][0] / u:.1f}, "
                    f"y {seat['maxAt'][1] / u:.1f}), against {INLAID_AIR_TOLERANCE / u:.2f} — a "
                    "set stone with air under it is not set, it is resting on its own rim"
                )

    # --- the two halves of a pair carry the same colour on mirror-image faces -----------------
    mirror_colour = manifest.get("mirrorColour")
    if not mirror_colour:
        failures.append(
            "parts.json carries no mirrorColour block — re-capture the renders with the current "
            "harness; without it nothing checks that a mirrored pair shades as a mirrored pair"
        )
    else:
        for label, entry in sorted(mirror_colour.items()):
            for group in ("inward", "outward"):
                delta = entry[group]["delta"]
                colour_ok = delta <= MIRROR_COLOUR_TOLERANCE
                front_rgb = " ".join(f"{v:.4f}" for v in entry[group]["front"])
                print(
                    f"{'ok ' if colour_ok else 'OFF'} {label:<24} {group:<7} face colour "
                    f"Δ {delta:.6f}   ({front_rgb})"
                )
                if not colour_ok:
                    where = "facing the shell" if group == "inward" else "facing the camera"
                    failures.append(
                        f"{label}: the two halves differ by {delta:.6f} in the vertex colour of "
                        f"their {group} faces — the ones {where}. The shading key is not being "
                        "mirrored with the geometry, so the pair reads as two different parts"
                    )

    for name in ON_AXIS:
        box = bounds.get(name)
        if not box:
            failures.append(f"{name}: not present in the built model")
            continue
        offset = box["minX"] + box["maxX"]
        status = "ok " if abs(offset) <= TOLERANCE else "OFF"
        print(f"{status} {name:<24} centre X {offset / 2:+.5f}")
        if abs(offset) > TOLERANCE:
            failures.append(f"{name}: centre X is {offset / 2:+.5f}, not on the axis")

    for left, right in MIRRORED:
        lb, rb = bounds.get(left), bounds.get(right)
        if not lb or not rb:
            failures.append(f"{left}/{right}: not both present in the built model")
            continue
        outer = lb["minX"] + rb["maxX"]
        inner = lb["maxX"] + rb["minX"]
        worst = max(abs(outer), abs(inner))
        status = "ok " if worst <= TOLERANCE else "OFF"
        print(f"{status} {left} / {right:<22} mirror error {worst:.5f}")
        if worst > TOLERANCE:
            failures.append(f"{left}/{right}: mirror error {worst:.5f}")

    print()
    if failures:
        for line in failures:
            print(f"FAIL {line}")
        raise SystemExit(1)
    print(
        f"contract + centreline: {len(EXPECTED_PARTS)} parts, {len(ON_AXIS)} on-axis, "
        f"{len(MIRRORED)} mirrored pairs, {len(SPLIT_PAIRS)} Z-split pairs — all pass"
    )


if __name__ == "__main__":
    main()
