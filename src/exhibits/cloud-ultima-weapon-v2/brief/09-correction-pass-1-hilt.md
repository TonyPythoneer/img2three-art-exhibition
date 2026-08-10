# Correction pass 1 — hilt geometry

Supplied by the user after the first full build. Archived verbatim so the specification
survives the conversation it arrived in.

**Superseded in part by `10-correction-pass-2-structure.md`**, which explicitly overrides
everything here about `centralGripSocket`, the four `driverSocket` components, and how far the
white crystal shell extends downward. Where the two conflict, pass 2 wins.

Its acceptance table is recorded in `../spec/confidence-report.md` under
"Correction pass — acceptance table".

---

Work from the current model and produce the smallest geometry changes that satisfy this
correction specification. Do not replace approved components merely because rebuilding them is
easier.

You are correcting an existing Three.js model of the Final Fantasy VII Ultima Weapon.

This is a targeted geometry correction pass, not a redesign.

Use the original artwork as the final authority. Use the uploaded marked screenshots only as
defect evidence showing what is currently wrong.

Do not rebuild or simplify the entire sword. Preserve all already-approved blade proportions,
including:

- the sharpened pale outer crystal shell;
- the unsharpened inner purple crystal;
- the overall blade silhouette;
- the four-layer blade hierarchy.

Concentrate this correction pass on:

1. the central blade-to-hilt transition;
2. the red diamond crystal mount;
3. the T-shaped guard;
4. the four red drivers;
5. the leather connectors;
6. the vertical grip and pommel;
7. consistent front, side, and rear construction.

## 1. Establish one strict vertical centerline

Treat the vertical centerline through the red diamond crystal as the primary structural axis of
the entire sword.

The following points must share the same X coordinate: pale outer crystal tip; pale outer
crystal lower neck; purple crystal center; dark-purple triangle center; red diamond crystal
center; central metal cradle; vertical grip center; grip-end collar; pointed metal pommel.

Do not allow any of these parts to drift left or right. The red diamond crystal is the visual
and structural center of the blade-to-hilt transition.

## 2. Correct the lower pale crystal shell

The pale outer crystal shell must not terminate as a wide, flat, rectangular slab above the
guard. Its lower section must form a symmetrical downward taper: begin from the full lower
blade width; contract inward through two mirrored sloping sides; form a shallow trapezoidal or
faceted neck; converge toward the red diamond crystal centerline; visually transfer the blade
load into the hilt.

The left and right lower edges must be mirrored. The lower crystal neck must connect
structurally to the guard assembly. It must not float behind the red diamond crystal. Preserve
the approved sharpened side edges of the outer crystal shell.

## 3. Align the internal crystal layers

The pale-purple insert, dark-purple triangular core, and red diamond crystal must form one
coherent vertical stack: the bottom center of the pale-purple insert must align with the red
diamond centerline; the dark-purple triangle must be centered directly behind or above the red
diamond; the dark-purple triangle must not lean or widen asymmetrically; the red diamond must
not be offset from the purple crystal stack; the inner purple crystal remains faceted but
unsharpened.

The purple components are internal crystals, not additional cutting blades.

## 4. Rebuild the red diamond crystal mount

The red diamond must be a separate faceted crystal node, not a flat arrow polygon.

Place two small mirrored triangular metal jaws beside its lower-left and lower-right faces.
These two metal jaws must closely cradle the lower half of the diamond; be symmetrical around
the sword centerline; have their upper tips positioned beside the diamond; slope downward and
outward; connect at their lower ends to the left and right shoulders of the central grip/guard
structure.

The metal jaws must read as a real mechanical crystal clamp. Do not place one wide rectangular
block under the diamond. Do not leave the diamond floating. Do not allow the jaws to intersect
through the diamond.

## 5. Reconstruct the T-shaped guard

The T-shaped guard must be a coherent assembly with one central vertical grip socket; one left
connector arm; one right connector arm; compact metal spinner-shaped end pieces; independent
driver sockets.

The left and right connector arms must be mirrored. The horizontal guard must connect cleanly
into the vertical grip without an unexplained narrow waist. The connection immediately below the
T-shaped guard must maintain the grip's main width. Do not taper it into a thin neck.

## 6. Correct the four red drivers

There must be exactly four red drivers: left upper; left lower; right upper; right lower.

Replace the current rectangular bars with slim low-poly cylindrical rods. Use a faceted
cylinder, approximately 6–8 radial segments, to preserve the original low-poly style.

Each driver must have a circular or faceted-circular cross-section; a consistent narrow radius;
a visible root section; a clean capped outer end; dark wine-red sides; a restrained magenta
highlight.

The drivers must not lie flat on top of the T-shaped horizontal guard. They must not appear
pasted onto its front surface. Each driver root must be inserted into its own mounting socket
positioned above or behind the corresponding leather connector.

From the front view the four drivers radiate outward, the arrangement is mirrored, two drivers
appear on each side, and the roots remain compact near the guard. From the side view the drivers
must have real Z-depth; their roots must visibly enter the mounting sockets; they must not
collapse into one flat plane; they must not pass through the pale crystal shell; they must not
float separately from the guard.

Use one reusable driver geometry with four independent transforms.

## 7. Correct the connector material under the drivers

The connector arms directly underneath the red drivers must be dark grey leather-covered
components. They are not plain black metal cubes.

Use dark grey leather; low roughness variation; restrained seam or wrap detail; a compact
faceted shape; no oversized box geometry. Each leather connector supports the corresponding
driver sockets and leads toward the metal end piece. Do not add excessive wrapping rings.

## 8. Add spinner-shaped metal pieces to both T-guard ends

The left and right ends of the T-shaped guard must each terminate in one compact spinner-shaped
metal piece, resembling a small faceted spinning top, plumb bob, or opposing cone assembly.

Exactly one on the left; exactly one on the right; mirrored size and position; muted olive-gold
or aged brass material; visibly separate from the leather connector; compact rather than hanging
as a large paddle; connected directly to the end of the corresponding T-guard arm.

Do not leave these pieces floating below the guard. Do not make them large rectangular plates.

## 9. Correct the vertical grip

The vertical grip must be a straight, narrow, dark leather-wrapped shaft: maintain nearly
constant width from the guard connection downward; do not narrow immediately below the T-guard;
remove the repeated protruding rings currently placed along the grip; use subtle leather wrapping
or surface ridges instead of multiple hard collars; keep the grip centered on the red diamond
axis.

There must be exactly one clear finishing collar near the bottom of the leather grip. Do not
distribute several identical ring bands along the shaft.

## 10. Separate the bottom metal pommel

The bottom pointed metal piece must be a separate component from the leather grip. Required
order: leather grip; one finishing metal collar; one independent pointed metal pommel or rivet.

The pommel must remain centered; be narrower than the grip; have a compact faceted cone or
spinning-top form; use a muted metal material; be visibly separated from the leather by the
collar. Do not merge the pointed metal tail into the leather geometry. Do not add extra rings
above it.

## 11. Make the rear design structurally consistent

The back of the hilt must be derived from the same real assembly as the front. Do not create an
unrelated simplified rear face.

The rear view must preserve the same central axis; the same crystal clamp thickness; the same
left/right connector structure; the same four driver sockets; the same grip socket; the same
component depth relationships.

Front and back surfaces may use simpler artwork-faithful facets, but they must belong to the same
connected 3D structure. No floating rear rods, missing mounts, open gaps, or unexplained diagonal
plates are allowed.

## 12. Component ownership

Keep these as separately reviewable nodes:

```
SwordRoot
├── BladeGroup
│   ├── outerCrystalShell
│   ├── purpleEnergyInsert
│   ├── darkCoreTriangle
│   └── rootDiamondGem
└── HiltGroup
    ├── crystalClamp
    │   ├── crystalClampLeft
    │   └── crystalClampRight
    ├── guardCore
    ├── leatherConnectorLeft
    ├── leatherConnectorRight
    ├── driverArray
    │   ├── driverLeftUpper
    │   ├── driverLeftLower
    │   ├── driverRightUpper
    │   └── driverRightLower
    ├── spinnerEndLeft
    ├── spinnerEndRight
    ├── leatherGrip
    ├── gripEndCollar
    └── pointedMetalPommel
```

Do not merge all hilt geometry into one mesh before review.

## 13. Required validation renders

After correction, render all of the following with the same neutral lighting: front orthographic
view; rear orthographic view; left side view; right side view; three-quarter front view;
three-quarter rear view; close-up of the diamond crystal and clamp; close-up of the driver
sockets; close-up of the grip collar and independent pommel.

The front and rear renders must use identical camera distance and scale.

## 14. Acceptance criteria

Reject the result unless all conditions pass: the red diamond center is on the sword centerline;
the pale and dark purple crystal layers align with that same centerline; the pale outer shell
contracts symmetrically into the guard; two metal triangular jaws cradle the lower diamond; both
jaws connect to the left and right sides of the central grip structure; exactly four red drivers
exist; the drivers use faceted cylindrical geometry, not rectangular prisms; driver roots enter
dedicated sockets and do not lie flat on the T-guard; the side view shows real driver depth and
insertion; the connector arms below the drivers read as dark grey leather; both T-guard ends
terminate in compact spinner-shaped metal pieces; the vertical grip does not narrow directly
below the guard; repeated grip rings are removed; exactly one finishing collar exists near the
grip bottom; the pointed metal pommel is an independent component; the rear assembly follows the
same structural logic as the front; no visible floating, disconnected, or intersecting hilt
components remain.

Do not proceed to material polishing until these geometry checks pass.
