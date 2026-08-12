# Correction pass 2 — component hierarchy and joint logic

Supplied by the user after correction pass 1. Archived verbatim so the specification survives
the conversation it arrived in.

**This is the highest-priority specification for this exhibit.** It explicitly overrides
`09-correction-pass-1-hilt.md` wherever the two conflict — specifically the `centralGripSocket`
component, the four `driverSocket` components, and how far the white crystal shell extends
downward. The problem it addresses is not proportion: it is that the component hierarchy and
joint logic were wrong.

Its acceptance table is recorded in `../spec/confidence-report.md` under "Structural correction
pass — acceptance table", and the component contract it defines is asserted in code by
`../spec/check_centerline.py`.

---

You are correcting the existing Three.js Ultima Weapon model.

This is a strict structural correction pass. Do not redesign the sword and do not freely invent
new components.

The original artwork remains the final authority. The uploaded marked screenshots show defects in
the current generated model.

The following specification overrides all previous instructions that conflict with it.

## 1. Exact physical component contract

The final model must contain exactly the following physical geometry components. Empty
`THREE.Group` nodes may be used only for organization. They do not count as physical parts.

```
SwordRoot                         // organizational group only
├── BladeGroup                    // organizational group only
│   ├── outerCrystalShell
│   ├── purpleEnergyInsert
│   ├── darkCoreTriangle
│   └── rootDiamondGem
└── HiltGroup                     // organizational group only
    ├── crystalClampLeft
    ├── crystalClampRight
    ├── guardCore
    ├── leatherConnectorLeft
    ├── leatherConnectorRight
    ├── driverArray               // organizational group only
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

After applying this hierarchy: do not add any other physical mesh; do not remove any component
listed above; do not merge separately listed parts before review.

The following components must not exist: `centralGripSocket`; `driverSocketLeftUpper`;
`driverSocketLeftLower`; `driverSocketRightUpper`; `driverSocketRightLower`; any hidden
replacement socket mesh; any large plate placed behind the red diamond; any extra white crystal
extension below the metal clamps.

The four red drivers connect directly to their leather connector parts. They do not require
separate visible socket components.

## 2. The two triangular clamps are the blade socket

There is no `centralGripSocket`. `crystalClampLeft` and `crystalClampRight` together form the
complete structural socket between the blade and the hilt.

Both clamp parts must be triangular metal prisms. They must be mirrored across the sword vertical
centerline; equal in size; equal in depth; centered around the front/back plane; structurally
connected to the hilt; visible from both the front and back.

Do not model them as thin front-facing plates. Each clamp must have real thickness and must
extend equally toward the front and rear.

## 3. Exact red diamond and clamp contact

The red diamond crystal is the main vertical center of the entire sword. Its center must share
the same X coordinate as the outer crystal blade tip; the purple insert center; the dark core
center; the vertical grip; the bottom collar; the bottom pommel.

The lower-left edge of `rootDiamondGem` must touch the inner upper edge of `crystalClampLeft`.
The lower-right edge of `rootDiamondGem` must touch the inner upper edge of `crystalClampRight`.
These contacts must be edge-to-edge.

Requirements: no visible gap; no floating diamond; no overlap through the diamond; no rectangular
block underneath the diamond; no unrelated gold crown behind the diamond; no small red spike
extending below the diamond; no white surface inserted between the diamond and the clamps.

The two clamps must visually hold the lower half of the red diamond. The clamps begin exactly
where the red diamond ends.

## 4. The sword grip grows from the triangular clamps

The lower base areas of `crystalClampLeft` and `crystalClampRight` form the beginning of the hilt
structure. The vertical grip must begin directly below the joined clamp bases.

Do not place another socket between the clamps and the grip. Do not place a large horizontal
plate between them.

`guardCore` may exist only as a compact internal structural bridge connecting the two triangular
clamps; the left and right leather connectors; the vertical leather grip.

`guardCore` must not create a large visible crown, shield, rectangle, or additional front plate.
The triangular clamps remain the visible blade socket.

## 5. Stop the white crystal shell above the clamp base

The pale outer crystal shell must not continue growing below the triangular clamp region.

The lower white shell may taper inward toward the red diamond and clamp assembly, but it must
stop at the upper boundary of the clamps. It must not extend below the bottom edge of either
triangular clamp.

Remove all white or light-grey crystal geometry that appears below the triangular clamp bases;
beside the top of the vertical grip; behind the vertical grip; between the clamp bases and the
grip; as two hanging white triangles under the hilt center.

The required vertical sequence is:

```
outer white crystal shell
        ↓
purple crystal stack
        ↓
red diamond crystal
      ↙   ↘
left clamp   right clamp
      ↘   ↙
compact guard junction
        ↓
vertical leather grip
```

There must be no white crystal geometry after the triangular clamps begin the hilt.

## 6. Front and rear must use the same complete design

The current model has a designed front face but an unfinished or unrelated rear face. This is not
acceptable. The whole blade and hilt must be geometrically symmetric across the front/back plane.

Using the coordinate system X = left and right; Y = blade and grip direction; Z = front and rear:
all major hilt components must be centered around Z = 0. For every front surface at positive Z,
there must be a matching rear surface at negative Z.

This applies to every component in the contract above.

The rear must not be a flat closing polygon added after the front was completed. Build real
three-dimensional solids from the center plane.

The red diamond should be a faceted rhombus prism or low-poly bipyramid with equal front and rear
depth. The triangular clamps must be triangular prisms with equal front and rear depth. The front
and rear silhouette must match when rendered with the same orthographic camera.

## 7. T-hilt connectors must be complete cylinders

`leatherConnectorLeft` and `leatherConnectorRight` form the left and right arms of the T-shaped
hilt. They must use complete closed cylindrical geometry — a low-poly faceted cylinder with
approximately 6–8 radial segments.

They must not be rectangular beams; partial cylinders; flat plates; open channels; uneven polygon
blocks; thin diagonal strips.

Each connector must have a full circular or faceted-circular cross-section; a closed root cap; a
closed outer cap; consistent radius; symmetrical front and rear depth; dark grey leather material.

The left and right connectors must be mirrored. The connectors may angle downward and outward
according to the artwork, but they must remain complete cylinders.

## 8. Red drivers connect directly without socket meshes

There must be exactly four red cylindrical drivers. Each driver must use a slim faceted
cylindrical form. Do not create separate driver socket geometry.

The root end of each driver must connect directly to the correct leather connector. The root cap
must meet the connector surface cleanly.

The drivers must not pass through the leather connector; pass through the opposite side of the
connector; pass through the white crystal shell; cross the sword centerline; float away from the
connector; appear pasted over the front surface; continue through the complete T-hilt arm.

Allow only a very small hidden overlap at the joint to prevent a visible gap. Maximum allowed
hidden overlap: no more than 5% of the driver diameter; it must remain inside the outer surface of
the leather connector; it must not cross the connector's central axis.

The driver ends must stop at the connector joint. Use direct parent-child attachment or a
transform anchor. Do not generate a physical socket mesh.

## 9. Driver arrangement

From the front view: two drivers must appear on the left; two drivers must appear on the right;
all four roots remain close to the hilt; the arrangement is left/right mirrored; drivers radiate
outward; drivers do not overlap the red diamond; drivers do not cut through the pale crystal shell.

From the side view: each driver must show its real cylindrical depth; each driver must terminate
at the leather connector surface; no driver may extend through the connector; no driver may be
hidden inside a rectangular guard block.

The four drivers should share one reusable cylinder geometry with four independent transforms.

## 10. Side metal spinner ends must be connected and blunt

`spinnerEndLeft` must connect directly to the outer end of `leatherConnectorLeft`.
`spinnerEndRight` must connect directly to the outer end of `leatherConnectorRight`. There must be
no gap between the leather connector and its metal end piece. The connector end cap and spinner
attachment face must meet flush.

The side spinner pieces must be compact; faceted; muted gold, olive-gold, or aged brass; wider
near their connection; gradually reduced toward their outer end; blunt or truncated at the final
tip.

Do not create sharp needle-like points. Do not make the side ends look like hanging diamonds. Do
not leave the metal end pieces floating below the connectors. Do not attach them using another
visible ring or socket.

The left and right pieces must be mirrored in position; rotation; size; depth; material;
truncation shape.

## 11. Vertical grip

`leatherGrip` begins directly below the joined bases of the triangular clamps and the compact
guard junction. It must remain centered on the red diamond vertical axis. Use a complete
cylindrical or lightly faceted cylindrical shaft.

The grip must have a closed cross-section; keep a mostly consistent radius; not collapse into a
thin rectangular strip; not narrow suddenly under the T-hilt; remain symmetrical front-to-back;
use dark leather material; contain no repeated hard ring meshes.

Leather wrapping may be shown through subtle material variation; shallow helical ridges;
normal-map detail; restrained geometry bands built into the grip surface. Do not add new physical
ring parts.

## 12. Bottom grip collar and pommel

Keep exactly one `gripEndCollar` and one `pointedMetalPommel`. The collar must connect directly to
the end of the leather grip. The bottom pommel must connect directly below the collar. Do not add
extra rings.

The bottom pommel may remain pointed because it is the sword's bottom metal tail. This pointed
bottom pommel is different from the left and right side spinner ends, which must be blunt.

## 13. Outer white crystal material

`outerCrystalShell` must clearly read as a semi-transparent pale crystal. It must not appear as
opaque grey plastic or solid concrete.

Recommended Three.js starting material:

```js
new THREE.MeshPhysicalMaterial({
  color: 0xe7e8f3,
  metalness: 0.0,
  roughness: 0.2,
  transparent: true,
  opacity: 0.62,
  transmission: 0.3,
  ior: 1.45,
  thickness: 0.35,
  side: THREE.DoubleSide,
  depthWrite: false,
});
```

Treat these values as starting values and adjust them through render review.

Visual requirements: the purple insert must remain visible through parts of the white shell; the
shell must retain pale white highlights; side bevels must remain readable; front and rear faces
must both render; the shell must not become fully invisible; the shell must not become uniformly
opaque grey; transparency must not create sorting flicker; internal crystals must not disappear
behind it.

Use controlled transparency. Do not use glass-like perfect clarity. The result should look like
milky translucent crystal.

## 14. Do not change the approved blade-edge design

Preserve the existing requirement that the pale outer shell is sharpened; the tip contracts into a
clear point; both side edges taper into visible cutting bevels; the purple inner crystal remains
unsharpened. This correction pass must not undo those approved blade features.

## 15. Exact rejection conditions

Reject the result immediately when any of the following is present: `centralGripSocket` still
exists; any `driverSocket` mesh still exists; any new physical component has been added; any
required component has been removed; the triangular clamps are replaced by a central block; the
red diamond floats above the clamps; the diamond overlaps through the clamps; the diamond and
clamps have a visible gap; white crystal continues below the triangular clamp bases; white
triangular geometry appears beside the grip; front and rear geometry are not symmetric; the rear
hilt is flat, empty, or structurally unrelated; the T-hilt connector arms are rectangular;
connector arms are not complete closed cylinders; red drivers penetrate through the connectors;
red drivers use visible socket parts; side spinner ends float away from the connector arms; side
spinner ends have sharp needle tips; the outer white shell looks opaque grey; the red diamond,
grip, and pommel do not share one centerline.

## 16. Required validation renders

Render the corrected model using identical scale and neutral lighting: front orthographic; rear
orthographic; front/rear 50% overlay; left side; right side; three-quarter front; three-quarter
rear; close-up of red diamond and triangular clamp contact; close-up of the bottom of both clamps;
close-up of all four driver joints; close-up of both cylindrical leather connectors; close-up of
both blunt spinner ends; material test showing the purple crystal through the translucent white
shell.

Use a white background for geometry review and a checkerboard background for transparency review.

Do not continue to final material polish until all geometry rejection conditions pass.

---

## The relationships this pass is about

```
white translucent crystal shell
        ↓ stops here
purple inner crystal
        ↓
red diamond crystal
     ↙ flush contact ↘
left metal jaw    right metal jaw
     ↘            ↙
   directly forms the hilt junction
          ↓
      dark leather grip
```

```
red low-poly cylinder
        ↓ end-cap joint
dark grey complete-cylinder leather connector
        ↓ end-cap joint
blunt spinner-shaped metal end
```

and NOT:

```
red driver
   ↓ passes through
rectangular hilt part
   ↓ hangs off
sharp metal diamond
```
