# CURRENT-MODEL — FF7 Ultima Weapon V2

Start here. `RELATIONSHIPS.md` is which file feeds which and in what order;
`confidence-report.md` is what is measured against what is directed, and where the sources
conflict. Numbers here are read from `artifacts/ultima-v2/full/parts.json` and the gate JSON,
never from another document — `spec/audit_records.py` enforces that.

---

## 1. What this is

The exhibit at `/cloud-ultima-weapon-v2`. All geometry comes from one hand-authored factory,
`createUltimaWeaponV2Model.ts` — no external meshes, no textures, no image maps. Its reference is
a **210×434 artwork crop** supplied as a review package with its own written component contract,
_not_ the 146×292 game render the other three Ultima Weapon exhibits are built from. The two
sources disagree about part count and proportion; this build answers only to the crop and its
contract, so do not "fix" one exhibit's numbers with the other's.

---

## 2. Coordinate system and units

Normalized-1000, weapon-local: `+Y` guard→tip, `−Y` guard→pommel, `+Z` artwork-facing, origin at
the blade socket. `U = 0.01` — the factory divides every constant by 100, so `Y = 760` (the blade
tip) is world `+7.60` and `Y = −211` (the pommel tip) is world `−2.11`. Total height 9.71 world
units, widest extent `±1.5973` at the lower driver rods.

The model is authored **upright and symmetric**. The artwork's 18.13° lean is a **camera roll**
applied in `createUltimaWeaponV2LookDev.ts`, never in geometry.

---

## 3. The exact component contract

22 named nodes: 3 organisational groups carrying no geometry, and 19 physical meshes. The root
`THREE.Group` is `ultimaWeaponV2` and is not in `runtime.nodes`.

```
ultimaWeaponV2
├── bladeGroup      outerCrystalShell · purpleEnergyInsertFront/Rear
│                   darkCoreTriangleFront/Rear · rootDiamondGemFront/Rear
└── hiltGroup       crystalClampLeft/Right · leatherConnectorLeft/Right
                    spinnerEndLeft/Right · leatherGrip · pointedMetalPommel
    └── driverArray driverLeftUpper/Lower · driverRightUpper/Lower
```

**That is the built `THREE.Object3D` tree and it is deliberately flat**: every blade layer parents
straight to `bladeGroup` and every hilt part straight to `hiltGroup`, whatever it actually rests
on. The spec's `componentTree` is a different tree — the ASSEMBLY tree, where a part's parent is
the part it is mounted on, so the dark core hangs off the insert it is seated on and the pommel
off the grip whose bottom ring it shares. §4 carries it. Neither is wrong: a transform hierarchy
and a load path are different questions, and only one of them has to satisfy a renderer.

**`centralGripSocket` MUST NOT exist. No `driverSocket*` mesh MUST exist.** Both were components
of an earlier pass and both were structurally wrong: the two triangular clamps _are_ the blade
socket, and each rod's root cap seats directly inside its connector's cylinder.

**`guardCore` MUST NOT exist.** It was a steel bridge under the jaws, directed at confidence 0.50,
and the crop does not show a bridge: at 8× NEAREST the guard is one undifferentiated dark mass and
the grip's own column runs up into it with no seam anywhere (`spec/zoom-guard/`). Its job — closing
the wedge between the jaws' lower edges and the hilt — passed first to the grip's **tang** and then
to the jaws themselves: their lower edge is one horizontal floor at `CLAMP_FLOOR_Y` = 13, and the
shell's lowest edge and the grip column's top face both land on that same plane, so there is no
wedge left to fill.

**`leatherGrip` MUST NOT carry a tang, and MUST NOT be inserted.** Correction A made it one plain
octagonal column of constant width from the pommel to its top; integration #16 then landed that
top FACE TO FACE on the two jaws' floor instead of running it up between them. The widened T-head
that replaced `guardCore` existed only to fill the V the jaws left below their junction, and the
jaws have a flat floor now with the crystal's own base edge on it, so there is nothing under them
to fill. What holds the column is coverage, not a bite: its top face reaches 11.087 in x and in z
inside a floor footprint of ±34 by ±16 (§9).

**`gripEndCollar` MUST NOT exist.** It was directed at confidence 0.60 and the crop refutes it: at
16× NEAREST the leather runs uniform near-black from Y = −160 down to its measured edge at −180.3
and the warm gold starts on the very next row. No ring, no band, no second material. The leather
now runs to that measured edge and the pommel's base ring shares the same plane, so removing it
opened no gap — the grip's own end cap closes the junction.

**All three inner layers are each TWO meshes**, `…Front` and `…Rear` — one component of the
contract, two pieces, and the two halves asserted to be exact mirrors. **All three are SEATED:
every one of the six meshes lies on the surface under it, and none of them reaches `Z = 0`.**

- **`purpleEnergyInsert{Front,Rear}` and `darkCoreTriangle{Front,Rear}` are SKINS.** Each is a
  film laid _on_ one of the shell's own faces, `SKIN_STEP` = 0.05 T thick, following that surface
  in X and in Y on **both** of its own faces. The dark core's underside is the insert's outer
  face, so the two stack.
- **`rootDiamondGem{Front,Rear}` is a STONE**: a **四角錐** grown out of the dark core's outer face
  — four triangular flanks over a seated rhombus base, one apex, measured at **0.500 across and
  0.500 up its own front-view box** (`spec/measure_gem_facets.mjs`). Its height above the seat is
  a relief step plus 0.38 of its own half-width. It is the one raised body on the blade, and the
  lift ladder is what says so — what it is _not_ any more is a half-body driven through the
  crystal from the mid-plane outward, and since 2026-08-09 it is not a girdled prism either.

The correction of 2026-08-07 made the two lower layers skins: they had been bosses standing
1.20 T and 1.33 T through the blade, and the diamond's rim at 15.53 was buried inside the dark
core's plateau at 18.62 over the whole of their overlap, `Y = 56…97`.

**The correction of 2026-08-08 finished the job on the undersides.** Every layer's _outer_ surface
was solved and none of their _inner_ ones was: both films closed underneath with a **flat** face at
their own rim depth, which runs below the host's crest everywhere inboard of the rim; the diamond
was a **cut** pair, each half running from `Z = 0` outward; and `loft` closed each end with a fan
through the ring's centroid, which for a crescent-shaped ring is a point off the band.

**The correction of 2026-08-09 is the two-sided form of the same question, and it found four
more.** "Out of the crystal" and "lying on the crystal" are not the same sentence, and every
instrument on this model only ever asked the first: the harness's probe reports `max(host − |z|)`
**clamped at zero**, so a layer floating clear of the surface it is supposed to be laid on scored a
perfect 0.000 and passed. `measureStackConformity` splits each layer's triangles by which way they
look and reports a SIGNED clearance on the underside — `|z| − hostSurfaceZ`, positive a gap,
negative a penetration. Normalized units
(`artifacts/ultima-v2/diag/conform-before/parts.json` against `full/parts.json`; producer
`spec/capture_visibility.sh`, printed by `artifacts/ultima-v2/diag/report_conformity.py`):

| underside, before → now |             worst gap |     worst penetration |
| ----------------------- | --------------------: | --------------------: |
| insert skin             | +1.4000 → **+0.0182** | −0.0607 → **−0.0200** |
| dark core skin          | +1.4000 → **+0.0305** | −0.0361 → **−0.0001** |
| diamond                 | +3.4130 → **+0.1146** | −0.2515 → **−0.0001** |

The "now" column is smaller than it was on the day that correction landed — +0.0617 / −0.0608,
+0.0404 / −0.0362 and +0.1148 / −0.0826 — and none of that came from moving a layer. It came from
`loft`, on 2026-08-09: it split every quad on a fixed diagonal, and a fixed diagonal on a warped
quad bulges to one side. Splitting on the SHORTER one instead took the worst penetration of any
blade layer into the shell from 0.083 to 0.020 in the same units. §9 carries the rule.

Four causes, and the old probe scored every one of them under 0.3:

1. **The stone crossed a STEP in its host with no ledge in its own underside.** Both films end at
   the authority line `Y = 55`, so the surface under the stone jumps 2.8 units there, while the
   stone spanned `Y = 13…97` on rings at 13, 23.5, 55, 86.5, 97 only — it stood **+3.4130 clear of
   the crystal at (−7.5, 39.3)**. The ring list is derived now (`GEM_SEAT_STATIONS`) and a step
   gets two rings.
2. **Both films closed their apex at their OUTER depth**, leaving the insert's last 100 units of
   height and the core's last 77 as a wedge of air one full film thickness deep. A film of constant
   thickness whose footprint closes to a point ends in a zero-width, full-thickness EDGE.
3. **A layer of zero width was counted as covering its own axis.** `bladeStackTop`'s containment
   test was `|x| <= halfWidthAt(y)` against an interpolation that returns 0 outside the layer's
   span, and `0 <= 0` is true, so both films' steps were added on the centre line at every height
   where neither film exists: **+2.8 on the axis at `Y = 23.5`**.
4. **The shell's own MESH is not the shell's analytic section**, and the layers are seated on the
   section. `loft`'s triangulated quads agree with the ruled surface on the rails and depart in the
   middle, by more the longer the band; `Y = 13→55` was this shell's longest and fastest — 42 units
   over which the half-width more than doubles — and the stone sits on the whole of it. Subdividing
   it into four bands took the residual from `−0.2017 … +0.6203` to `−0.0826 … +0.1148`, and the
   diagonal fix above then took it to the `−0.0001 … +0.1146` in the table; §8 carries the ladder.

Undersides now conform on both sides of zero, and `spec/check_centerline.py` asserts it.

**That assertion is also what makes the stack ORDER pointwise rather than a bounding-box claim.**
Flush-on-the-surface-under-it plus a positive thickness above that surface is "outermost is the
stone, then the dark core, then the violet film, all of them lying on the crystal" evaluated at
every point rather than at one. `measure_relief_visibility.py` is the render-side half of the same
question and reads 97.6 / 93.2 / 100.0% proud of the shell and 100.0% of the stone proud of the
core, front and rear identically.

`outerCrystalShell` is therefore a solid with nothing in it. **The one exception is the socket, and
it is down to TWO parts**: `crystalClamp{Left,Right}`, which back the shell's base edge from the
axis out to its own outer corner and reach Y = 55 of the crystal, exactly the ceiling. The guard
integrations emptied the other three out of the list rather than re-arguing them — `leatherGrip`
shares a PLANE with the crystal (#15, #16) and both `leatherConnector`s read **0.000 units into the
shell** (#17 puts each root cap's plane through the crystal's own lateral edge), so the arm is
against the flank rather than inside it and passes the same 0.20 bound with no exception at all.

`spec/check_centerline.py` asserts the contract two-way (an extra part and a missing part both
fail), plus the centreline, the mirrored pairs, `shell.minY ≥ clamp.minY`, the blade's lift
ladder, the pointwise penetration above, **the two-sided seat-flush and film-thickness rows**, the
mirrored pairs' **colour**, and — for each split pair — the mirror at both ends and that it stays
clear of `Z = 0`. It prints its results and exits non-zero on drift; read its output, not a table
here.

**`rootDiamondGem` is NOT becoming a conforming skin, and that is a decision rather than an
omission.** The requirement is that all three layers lie flush on the surface under them, and
"flush" is a property of a layer's UNDERSIDE. Its outer form is a separate question and the
artwork answers it: the violet field is rim-bright and centre-dark by 20–25 luminance levels, the
red stone is centre-bright over rim-dark by +32 at `Y = 80` and +46 at `Y = 90`, with a specular
apex (§5). One raised body on this blade and it is the stone. Making it conform would also fail
two assertions written to forbid exactly that — the stone's 0.35 T thickness floor and its 0.25 T
step over the last skin — and would put it back inside the skin band a skin cannot leave. So its
underside is now the surface it meets, evaluated pointwise **including that surface's steps**, and
its crown is untouched: `gemCrownDepthAt` reads `GEM_STATIONS` rather than re-deriving the depth
at an added ring, so a station added for the seat cannot move the outside.

**One assertion was inverted rather than added, and that is a spec change.** It used to require the
diamond to REACH `Z = 0` as a "cut" pair, so the penetration was the passing condition. Deleting
that would have dropped what it protected — one boss carrying a thin backing plate — so it is
replaced by three things that together are strictly harder: the mirror test at both ends (which it
already had), a **thickness floor** of 0.35 T on each half, derived as the stone's own designed
rise from its seat `(GEM_RELIEF_STEP + GEM_CROWN_RISE) / T` — measured at 0.4923 T while the stone
was seated and at **0.5579 T** now that it is set into a socket — and the
pointwise stack probe, which is the fact "reaches the cut" was standing in for and getting
backwards. Fed the pre-correction geometry, the new block fails on all three counts.

`detail: "blockout"` hides both insert skins, both core skins, both gem halves and both clamps and
drops `sides` from 6 to 4;
`"structural"` and `"full"` are identical in this build. The runtime API is the exported
`SculptRuntime` type; the viewer's isolation groups are `ISOLATION` in `mountV2Viewer.ts`.

**One ordering trap:** explode rest positions are snapshotted _after_ the whole tree is built,
never at registration — callers set a part's position after `register()`, and snapshotting early
made the first `setExplode(0)` slam every driver, gem and cap back to the origin. Do not move
that loop.

---

## 4. The assembly graph: what carries what, and where

Every hilt decision serves one continuous chain, and a change that breaks any link in it is a
rejection condition:

```
blade tip → shell → converging trapezoid → the shell's own base EDGE, 68 wide on Y = +13
                 ↘ purple skin → dark core skin → red diamond ↗
                                                   ↓
                            crystalClampLeft + crystalClampRight (they ARE the socket)
                                                   ↓
                     leatherGrip's column, its flat top FACE TO FACE on their floor
                                                   ↓
                            leatherGrip's shaft → pointedMetalPommel

              leatherConnector{Left,Right} root on each jaw's OUTER floor vertex (±34, 13)
              and hand the guard out to the drivers and the spinner ends
```

Nothing is inserted anywhere along it. The two jaws carry the blade on their own; there is no
central socket component and no bridge under them, and since integration #16 the grip is not
inserted either — its column's flat top is BUTTED against the jaws' floor, face to face on one
plane, which is what the user's sketch draws. That floor is the hilt's structural datum and three
things land on it at once: the jaws' own lower edges, the crystal's lowest edge (#15, and their
lengths are equal by construction) and the column's top face (#16). The two arms start at its outer
corners (#17). Below it the column and the arms do not meet, and that is drawn open in the
sketch rather than closed — see the guess list in §11.

### The guard in section, which is where nearly every joint lives

Two horizontal lines carry the whole assembly, and every part in the guard is derived from one of
them. Normalized-1000 units, front view, upright:

```
              ╲   outerCrystalShell   ╱          the lower trapezoid, slope
               ╲   lower trapezoid   ╱           (83 − 34) / (55 − 13) = 1.1667
                ╲                   ╱
   Y = +55 ──────◆═════════════════◆──────  THE AUTHORITY LINE
            (−17, 55)          (+17, 55)    · the shell's taper starts here
                 ╲   rootDiamondGem  ╱      · both films' lower edge
                  ╲    (the stone)  ╱       · the stone's WAIST
      crystalClamp ╲               ╱ crystalClamp    · each jaw's APEX vertex
          Left      ╲     ▼       ╱     Right
                     ╲   ╱ ╲    ╱       ← each jaw's inner edge IS the stone's
                      ╲ ╱   ╲  ╱          own lower edge: |gem − jaw| = 0.000000000
   Y = +13 ──●─────────●───────●─────────●──  THE JAWS' FLOOR — the structural datum
         (−34, 13)  (0, 13) culet   (+34, 13)
             │          │                │
             │          │                └─ leatherConnectorRight's ROOT CAP LOWER RIM (#17),
             │          │                   cap raked −49.3987° so its whole diameter lies
             │          │                   ON the trapezoid, running (34,13) → (58.296,
             │          │                   33.825); the cap's CENTRE is at (46.148, 23.413)
             │          │
             │          └─ leatherGrip's flat TOP FACE (#16): reach 11.087 in x AND in z,
             │             entirely inside a floor footprint of ±34 by ±16
             └─ leatherConnectorLeft's root cap lower rim, mirrored

      and the two floor edges, 34 + 34, laid end to end across −34…+34, ARE the shell's
      own lowest edge, 68 wide on the same plane (#15): 68.000 vs 34.000 + 34.000
```

Below `Y = +13` the column and the arms **do not meet**. That gap is measured rather than waved
at — 46.803 units at `Y = −13` — and it is drawn open in the user's sketch; see G1 in §11. It was
25.730 while each cap straddled its corner; raising the arms one radius up their own normals on
2026-08-11 lifted each arm's inner silhouette with them and the gap beside the column grew.

### The anchor graph

`componentTree` is the ASSEMBLY tree: `parent` is the part a component is mounted ON, and
`attachment.parentSocket` / `childSocket` are the named anchors the two meet at. **It is not the
built `THREE.Object3D` tree**, which is flatter — the factory parents every blade layer straight
to `bladeGroup` and every hilt part straight to `hiltGroup`, because a transform hierarchy and a
load path are different questions and only one of them has to match a renderer.

A socket's `localPosition` is relative to its owner's `transform.position`, which is that
component's own BUILT bounding-box centre. So a socket's world point is `position + localPosition`,
and **both ends of every attachment name an anchor at the same world point** —
`spec/audit_records.py` asserts it, and that assertion is the one with teeth, because a socket
name can resolve and still be in the wrong place.

```
ultimaWeaponV2Root                                   socket used              contact
│   guard_center_anchor (0, 0)
├── bladeGroup ······································ blade_group_origin ····· frame
│   ├── outerCrystalShell ·························· blade_root_anchor (0,13)  butt
│   │   ├── purpleEnergyInsertFront ················ insert_seat_front  (0, 55, +13.5)   seated
│   │   │   └── darkCoreTriangleFront ·············· core_seat_front    (0, 55, +14.9)   seated
│   │   └── purpleEnergyInsertRear ················· insert_seat_rear   (0, 55, −13.5)   seated
│   │       └── darkCoreTriangleRear ··············· core_seat_rear     (0, 55, −14.9)   seated
│   ├── rootDiamondGemFront ························ gem_mount_anchor   (0, 13)          seated
│   └── rootDiamondGemRear ························· gem_mount_anchor   (0, 13)          seated
└── hiltGroup ······································ hilt_group_origin ······· frame
    ├── crystalClampLeft ···························· jaw_mount_anchor  (0, 13)   coplanar-edge
    │   └── leatherConnectorLeft ···················· floor_outer_left  (−34, 13)        butt
    │       └── spinnerEndLeft ······················ spinner_anchor_left (−103.90, −34.19) buried
    ├── crystalClampRight ··························· jaw_mount_anchor  (0, 13)   coplanar-edge
    │   └── leatherConnectorRight ··················· floor_outer_right (+34, 13)        butt
    │       └── spinnerEndRight ····················· spinner_anchor_right (+103.90, −34.19) buried
    ├── driverArray ································· driver_array_anchor (0, −62)      frame
    │   ├── driverLeftUpper ························· driver_root_left_upper  (−72.4, 6.2)   buried
    │   ├── driverLeftLower ························· driver_root_left_lower  (−93.1, −17.8) buried
    │   ├── driverRightUpper ························ driver_root_right_upper (+72.4, 6.2)   buried
    │   └── driverRightLower ························ driver_root_right_lower (+93.1, −17.8) buried
    └── leatherGrip ································· grip_anchor       (0, 13)           butt
        └── pointedMetalPommel ······················ pommel_anchor     (0, −180)         butt
```

**Two of those world points move whenever the guard's arms do, and both are recomputed rather
than typed.** `spinner_anchor_{left,right}` is `spinnerSeat()`, at (±103.938, −34.227) since
2026-08-08 — widening `SPINNER_TOP_RADIUS` moved the gold-emergence offset the DERIVED
`CONNECTOR_LENGTH` is a function of, and carried the length with it. Every earlier value of this
point is one arm length older; the ledger is the audit's retired-value list, not this paragraph.
The four `driver_root_*` points did NOT move with any of it: `driverRootRadius()` derives them from
the arm's ROOT, its rake and its radius, none of which these changes touched, so they still read
(±72.4, 6.2) and (±93.1, −17.8), and the two clearance figures behind them are still 1.14 and
4.02 driver diameters.
`audit_records.py`'s anchor-graph block holds both ends of every attachment to the same world
point within 3e-4, so a stale figure here is a failing gate rather than a stale sentence.

**Six contact kinds, and the model is deliberately lopsided across them.** `frame` is a transform
node with no surface. `butt` is two flat faces on one plane, embed depth zero. `seated` is a
layer's whole underside lying on the surface below it, evaluated pointwise. `coplanar-edge` is two
outlines sharing an edge exactly. `buried` is the only kind that penetrates — and there are just
three of them, all in the guard: each rod's root cap inside its arm, and each spinner's top ring
inside its arm. **Everything else on this weapon is a butt or a seat**, which is the shape of five
correction passes: every insertion that used to exist turned out to be a part standing in for a
derivation, and each one was replaced by the derivation.

### The joints a single-parent tree cannot hold

Nine contacts are between components that are not each other's parent, and the tree has no place
to put them, so each one is a `joints[]` entry on both components — with the function that owns
the derivation and the artifact the figure comes from. `audit_records.py` checks that every
`withRef` and every socket named in one of them resolves.

| Contact                                                       | Anchors                                         | Measured                                                                                                                   |
| ------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `outerCrystalShell` base edge ↔ both jaws' floors             | `lower_contact_{l,r}` ↔ `floor_outer_{l,r}`     | `shell.minY − clamp.minY` = **+0.000000** world; 68.000 vs 34.000 + 34.000                                                 |
| `crystalClamp{L,R}` inner edge ↔ `rootDiamondGem` lower edge  | `gem_edge_{l,r}` ↔ `waist_{l,r}`                | max &#124;gem − jaw&#124; = **0.000000000** over 65 heights                                                                |
| `crystalClamp{L,R}` floor ↔ `leatherGrip` top face            | `culet_anchor` ↔ `top_anchor`                   | 13.000 vs 13.000; reach 11.087 in x and z inside ±34 × ±16                                                                 |
| `leatherConnector{L,R}` root cap ↔ the shell's slanted flank  | `root_rim_anchor` ↔ `lower_contact_{l,r}`       | front-view residual **0.000005** over 65 samples, rim to rim                                                               |
| `driver{L,R}{Upper,Lower}` root cap ↔ `leatherConnector{L,R}` | `root_cap_anchor` ↔ `driver_seat_{side}_{band}` | roots at (72.4, 6.2) and (93.1, −17.8), recomputed every gate run — was (60.8, −4.7) / (78.1, −24.9) before the arms moved |
| `rootDiamondGem{F,R}` underside ↔ `darkCoreTriangle{F,R}`     | `culet_anchor` ↔ `seat_anchor`                  | gem proud of the core **100.0 / 100.0%**                                                                                   |

### How each joint is actually made

Every joint below is **derived from the part it meets**, never typed in. That is the property to
preserve: change a clamp outline or a connector radius and everything hanging off it follows, so
the model cannot drift into a state where two parts merely _used_ to fit. Each row names the
function that owns the derivation — that function's JSDoc carries the full reasoning.

| Joint                   | How it is made                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Owner                                    |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| shell → clamps          | **Integration #15.** The shell's base ROW _is_ the outline's outer lower vertex — `[CLAMP_FLOOR_Y, CLAMP_FLOOR_SPAN, 11]`, read out of `CLAMP_OUTLINE` rather than typed — so the shell's lowest edge is 2 × 34 = 68 on Y = 13 and the two jaws' floor edges are 34 each on the same plane. Their sum IS that edge: one substitution, not a coincidence.                                                                                                                                                                                                                                                                                                                                                                           | `SHELL_STATIONS`' first row              |
| connector → shell       | **Integration #17, amended 2026-08-11.** Each arm's root cap has its LOWER RIM on the jaws' outer vertex — not its centre, which was the reading until then and left the rim at (21.852, 2.587), 10.413 units below the guard's floor in open air. The rake is the shell's lower taper as an angle, `−atan((83 − 34) / (55 − 13))` = −49.3987°, so a cap perpendicular to that axis has its diameter along the taper and the cap's WHOLE diameter lies on the crystal's lower slanted flank, (34, 13) → (58.296, 33.825): front-view residual 0.000005 over 65 samples, rim to rim. `CONNECTOR_ROOT` is therefore derived — the corner plus one `CONNECTOR_RADIUS` along `(−sin a, cos a)` — and `audit_records.py` recomputes it. | `CONNECTOR_ROOT` / `CONNECTOR_ANGLE_DEG` |
| grip column → jaws      | **Integration #16.** Face to face on one plane: `GRIP_TOP_Y` _is_ `CLAMP_FLOOR_Y`. The column is not inserted between the jaws and they do not close on its flanks — the jaws are triangles on the stone's own lower edges, meeting on the axis at the culet, so there is no slot. What hides the top face is coverage: 11.087 in x and in z inside a floor footprint of ±34 by ±16.                                                                                                                                                                                                                                                                                                                                               | `GRIP_TOP_Y`                             |
| skins → shell           | The insert and core skins are **conformal**: each station's depth is `shellFrontDepth(x, y) + SKIN_STEP`, so the film follows the shell's own ridged surface instead of sitting at a fixed depth. Stations are the union of the skin's own corners, every `SHELL_STATIONS` height inside its span, and the height where the shell's ridge shoulder crosses the skin's outer edge.                                                                                                                                                                                                                                                                                                                                                  | `skinStations` / `skinSection`           |
| core skin → insert skin | The core's underside is the insert's outer face, so they stack rather than intersect. One `SKIN_STEP` apart.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | `bladeStackTop`                          |
| gem → skins             | The gem's girdle is derived to clear `bladeStackTop` — the top of whichever skin is under it at that station — by one relief step. Solving against the shell instead is exactly the defect §3 describes.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | `GEM_GIRDLE_RATIO`                       |
| gem → jaws              | The clamps' inner edge **is** the gem's own lower edge over its whole length, waist `(17, 55)` to culet `(0, 13)`: max                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | gem − jaw                                | = 0.000000000, recomputed at 65 heights by `audit_records.py`. There is no knee and no vertical face any more — the jaw is a triangle and the third point is its outer corner. | `CLAMP_OUTLINE` |
| gem → grip column       | Nothing to derive: the gem's culet and the jaws' floor are the same point on the axis, and the column's top face is that plane. The stone is not balanced on the leather and not buried in it — the two jaws carry it and the column carries them.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | `GRIP_TOP_Y`                             |
| driver → connector      | The root cap is buried against the surface that is the arm's **inradius** pulled in by the rod's own radius — not the arm's outer surface. Solving against the outer surface buries the centre line only and leaves the cap's rim floating 5.6–5.8 units proud.                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | `driverRootRadius()`                     |
| spinner → connector     | Turning the piece vertical leaves its horizontal top ring 40° off the arm's raked end cap, so the two can no longer meet flush. The ring is seated on the arm's own axis at a radius solved in closed form from the same inradius, clearing the leather by 1.5 units on every side and from every camera.                                                                                                                                                                                                                                                                                                                                                                                                                          | `spinnerSeat()`                          |
| grip shaft → pommel     | The pommel's base ring shares the leather's measured lower edge exactly — built gap `0.000000`. The grip's own end cap closes the junction; there is no collar.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | `GRIP_BOTTOM_Y`                          |

**Three of those joints are the same lesson, learned three times.** A flat cap meeting a curved
wall is not seated by sinking its centre line: the cap is a disc that stands in Z, so its rim
reaches out to where the wall has already curved away. The surface to solve against is the
prism's **inradius** — its thinnest wall, since a rim can land on a face centre rather than on a
vertex — offset inward by the cap's own radius. The driver roots, the spinner seats and the tang
all use it. Anything new that lands a flat face on a round arm should too.

**And the blade learned it a fourth time, on the other side of each layer.** A film laid on a
curved host is not seated by giving it a flat back at the host's rim depth: the back is a plane
and the host is a ridge, so everywhere inboard of the rim the plane is _under_ the surface it is
supposed to be lying on. Every underside on the blade is now the same polyline as the face above
it, translated — the insert's and the core's by `skinSection`, the stone's by `gemHalfSection`
closing on `bladeStackTop`. The rule is one sentence: **on this blade nothing is bounded by a
plane; every face is bounded by the surface it meets.**

There is only one kind of contact left in the blade, and that is the point: every split pair is
**seated** — it lies on the surface under it and never touches `Z = 0`. `check_centerline.py`
asserts that for all three, and asserts the two _kinds of layer_ by their step over what is below
instead: a skin's inside 0.035–0.060 T, the stone's at least 0.25 T. So a skin still cannot
quietly become a body, and it is now measured by thickness rather than by where the piece starts.

---

## 5. Geometry: provenance, not values

The values are in `createUltimaWeaponV2Model.ts`, one `const` block, each with its reasoning as
JSDoc beside it. What follows is what the code does not carry in one place: where each number
came from. **Measured** = read off the 210×434 crop by `spec/measure_authority.py`. **Directed**
= supplied by a written correction specification, which the crop cannot answer. **Inferred** =
taken from reference 03, a community front view. **Derived** = computed from another component,
so it moves when that one does. **Every `Z` / depth value is directed; confidence 0.35.**

Two tables are reproduced in full because they are the ones a future edit is most likely to get
wrong: the shell's stations, which carry the build's one deliberate departure from the crop, and
the relief chain, which spans four components at once.

### `outerCrystalShell` — `SHELL_STATIONS`, 13 stations, 8-point ridged section

`[Y, halfWidth, halfDepth]`:

|    Y |               halfWidth | halfDepth | Provenance                                                                                                                                                                                                                                                                                                                                                                          |
| ---: | ----------------------: | --------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|   13 | `CLAMP_FLOOR_SPAN` = 34 |        11 | **derived** — the base row IS `CLAMP_OUTLINE`'s outer lower vertex (integration #15), so the shell's lowest edge and the two jaws' floor edges are one pair of numbers read once. It replaces two rows: a 9.89-wide tenon at Y = −13 and the 31.735 the taper happened to reach at 13. The 11 is the DEPTH knee, and §8 says what dropping it cost                                  |
| 23.5 |                44.55125 |    11.625 | **derived, and carries NO shape** — the 13 → 55 line evaluated here, so the analytic surface is unchanged and `audit_records.py`'s "one straight taper" check passes on it. It is a MESH station: `loft`'s triangulation of a long band departs from the ruled surface the layers are seated on, and this is one of three subdivisions that take that departure from ±0.62 to ±0.13 |
|   34 |                 57.3675 |     12.25 | same, the trapezoid's midpoint                                                                                                                                                                                                                                                                                                                                                      |
| 44.5 |                70.18375 |    12.875 | same                                                                                                                                                                                                                                                                                                                                                                                |
|   55 |                      83 |      13.5 | = `GEM_WAIST_Y`, the diamond's widest line — where the trapezoid starts. Directed: the crop's own knee is at Y≈46. halfWidth is the crop's measured 81–83 band at its top; halfDepth is the old table's interpolated value at this height, so the depth curve stays continuous                                                                                                      |
|   70 |                      83 |        14 | assumption U3 — reference 03's orthographic ratio, _not_ the crop's one-sided 96                                                                                                                                                                                                                                                                                                    |
|  110 |                      81 |        14 | measured                                                                                                                                                                                                                                                                                                                                                                            |
|  300 |                      73 |        13 | measured                                                                                                                                                                                                                                                                                                                                                                            |
|  500 |                      63 |        11 | measured                                                                                                                                                                                                                                                                                                                                                                            |
|  575 |                      54 |        10 | measured — the taper's knee                                                                                                                                                                                                                                                                                                                                                         |
|  650 |                      34 |         8 | measured                                                                                                                                                                                                                                                                                                                                                                            |
|  760 |                       0 |         0 | measured — tip                                                                                                                                                                                                                                                                                                                                                                      |

Section (`ridgedSection`), per ring, with `a = 0.58·hw` and `shoulder = 0.72·hd`:
`(−hw, 0) (−a, shoulder) (0, hd) (a, shoulder) (hw, 0) (a, −shoulder) (0, −hd) (−a, −shoulder)`.
The **zero depth at `±hw`** is what makes the shell read as sharpened. No other component uses this
section.

**Below `Y = 42` the shell is a converging neck, and the 72 at `Y = 42` is this build's one
deliberate departure from a measurement** — the crop reads ~82 there. Why, and what it bought,
is `confidence-report.md` conflict 4. Widening it back fails `audit_records.py`, which recomputes
the driver clearance from these very stations.

### The blade's relief ladder — two skins under one stone

`T` = the shell's total front-to-back thickness through the lower-middle blade = 28. **Nothing on
the blade carries an absolute Z any more.** Each layer is written as _the surface under it,
evaluated at the point being asked about, plus its own step_ — a pointwise chain, not four
independent depths, so the order cannot be reversed by editing one number:

| Layer                            | What it is |                                               Its step | Where that step is measured                                |
| -------------------------------- | ---------- | -----------------------------------------------------: | ---------------------------------------------------------- |
| `outerCrystalShell`              | the host   |                                                      — | —                                                          |
| `purpleEnergyInsert{Front,Rear}` | skin       |                                   `SKIN_STEP` = 0.05 T | above `shellFrontDepth(x, y)`, everywhere on its footprint |
| `darkCoreTriangle{Front,Rear}`   | skin       |                                   `SKIN_STEP` = 0.05 T | above the insert skin's outer face                         |
| `rootDiamondGem{Front,Rear}`     | stone      | rim +0.12 T, then the point +0.38 × its own half-width | above `bladeStackTop(x, y)`, the two skins included        |

**The same chain runs on the UNDERSIDE of each layer, and until 2026-08-08 it did not.** Every one
of the six meshes closes underneath on the surface it is lying on, evaluated pointwise at the same
`x` breaks as its own outer face: `shellFrontDepth` for the insert, that plus one `SKIN_STEP` for
the core, `bladeStackTop` for the stone. Not a plane at the layer's rim depth, and for the stone
not `Z = 0`. So the layer's thickness is the step and nothing else, and there is no geometry
between a layer and its host.

**And it runs in Y as well as in X, which is what 2026-08-09 added.** Evaluating the surface under
a layer at the layer's own ring heights and ruling straight between them is only right where that
surface is smooth. It is not smooth in two places, and each needed a ring of its own:

- **it KNEES** at every `SHELL_STATIONS` height inside the layer's span. The two films already
  carried those (`skinStations`); the stone did not, and ruled straight across the shell's `Y = 70`
  knee for 0.2515 units of its own underside.
- **it STEPS**, by two `SKIN_STEP`s, at the films' lower edge — the authority line `Y = 55`. A step
  is two rings one `SEAT_STEP_SPAN` apart, the lower one reading the bare crystal and the upper one
  the full stack, and the band between them is the LEDGE. Given the same height instead, the two
  rings make a wall with no extent in Y and nothing downstream can tell which side of the step a
  face belongs to.

Both are derived rather than listed: `GEM_SEAT_STATIONS` unions the stone's own stations, the shell
stations inside its span, the heights where the shell's ridge shoulder or either film's rim crosses
the rhombus (none do, and it is bisected for rather than asserted), and the films' base as a step.

Every layer protrudes equally front and rear: the shell by being centred on `Z = 0`, the other
three by being two meshes that mirror across it.

**What the artwork actually supports.** Depth is one thing the crop cannot answer — it is a single
flat view, which is why §5's header says every `Z` is directed at confidence 0.35. What it _can_
answer is whether a layer shades like a raised body, and it answers differently for the two
kinds. Measured in `measure_authority`'s own weapon-local frame and reproduced at 16× NEAREST in
`spec/zoom-relief/`:

- the violet field runs **rim-bright, centre-dark by 20–25 luminance levels** from Y = 160 upward
  (centre 58.0 against rim 81.8 at Y = 160; 46.4 against 66.5 at Y = 300) — the inverse of what a
  plateau raised toward the viewer would shade like — and its boundary against the pale shell is
  **0–3 units wide at every height sampled**, one source pixel or less, with no bevel ramp inside
  it;
- the red gem runs **centre-bright over rim-dark**, and the contrast grows upward: +7.8 at Y = 50,
  +10.2 at 55, **+32.2 at 80, +46.4 at 90**, with a specular apex.

One raised body on this blade, and it is the stone. That is the reading, and it is what the
correction asks for independently.

**Depth is not visibility, and neither ladder can tell the difference.** `check_centerline.py`
reads bounding boxes: it proves the layers stand the right distance apart at the blade's thickest
point and nowhere else. Two defects have hidden in that gap, both found only by rendering:

1. `darkCoreTriangle`'s middle station once carried `0.62 ×` full depth = 11.54, behind the
   shell's own 14, so from Y ≈ 84 upward it stopped rendering as dark core at all.
2. the diamond's girdle sat at 15.53 while the dark core's plateau sat at **18.62** — the gem's
   entire rhombus outline was inside the layer directly under it, over the whole of their overlap
   (`Y = 56…97`), while the gate asked only whether it cleared _the shell_, which it did then at
   93.4% and does now at 100.0%. Proud of the shell and buried by the layer in between are not the
   same fact, and only one of them was being asked.

`spec/measure_relief_visibility.py` now asks both; §8 carries its numbers.

**And a third defect hid in the instrument rather than in the model.** The first version of that
second question compared pixels for exact identity, which assumes the winning surface is opaque.
`rootGem` carries `transmission: 0.22`, and three.js resolves transmission from the OPAQUE
backbuffer — so putting the dark core behind the gem dims the gem's own pixels even where the gem
plainly won the depth test. The test read 44.9% where the same geometry measures **100.0%** once
the instrument is right, and the geometry was never the problem: 90.7% of the failing pixels were
a dimmed gem red rather than the core's colour, and the pass/fail boundary was a flat line at the
rhombus's waist, `Y = 55`, which is the core's own FOOTPRINT edge and not a depth crossing. The
measurement now projects onto the gem-vs-core colour axis, so a translucent winner still counts as
a winner and an occluded pixel still scores zero — fed a frame in which the core wins the whole
overlap it scores 0.0%. The floor stayed at 0.95 throughout. That script's docstring carries the
evidence.

### Every other component

| Component                        | Provenance                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `purpleEnergyInsert{Front,Rear}` | Widths and both taper knees measured. It is a **skin**: its depth is not authored at all — it is `shellFrontDepth` plus `SKIN_STEP`, so it moves with the shell. `SKIN_STEP` is directed. The station list is **derived**: the layer's own knees, every `SHELL_STATIONS` height inside its span, and the height where the shell's ridge shoulder crosses the film's rim. All three are load-bearing — drop the shell stations and the film sinks 2.60 inside its host at Y ≈ 70; drop the shoulder crossing and it sinks 0.59 at Y ≈ 47.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `darkCoreTriangle{Front,Rear}`   | **Apex measured, base directed, confidence 0.75.** Two points: `[55, 21]` to `[187, 0]`. It was filed as "inferred from reference 03 at 0.45, because the crop shows only a dark rim reaching `Y = 98.8`" — and that 98.8 is where `measure_authority`'s RED colour family stops, not where the core does. The core is red-tinted only where it flanks the gem; above the gem it is near-black on violet and falls into the insert and grip families instead, so the red-family blob could never see it. Read as a _darkening of the insert_ by `spec/measure_core_apex.py`, the wedge's own edges fit `halfWidth = 26.152 − 0.1400 · Y` over 86 rows at an RMS of **0.60 units = 0.26 source pixels**, reaching zero width at `Y = 186.9`; a single-row half-maximum crossing agrees at 183, and sweeping the threshold over 0.35…0.65 of the wedge's own contrast moves the fit only between 178 and 195. The base half-width stays directed at 21 because below the gem's apex the gem's rim-dark shading shares the same dark run — but the same fit extrapolated down to the waist reads 18.45, inside 1.1 source pixels of it, so the directed base is now corroborated rather than merely asserted. The knee the outline used to carry at `(100, 3.86)` is deleted: it was never measured, it was the shape a triangle takes when its tip is cut off at 118, and the artwork measures **13.1** there. The second **skin**, seated on the insert's outer face rather than on the shell, so the two stack by construction.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `rootDiamondGem{Front,Rear}`     | Outline measured (bright-red pixels `Y = 12.9…97.3`, waist 32.6). The one raised **stone**, and it is a **四角錐** — DIRECTED by the user on 2026-08-09, five faces: four triangular flanks and a seated base, with the rim on `bladeStackTop` and ONE apex over the rhombus's centre. `GEM_STATIONS` is three rows and that is what makes it a pyramid rather than a roof — the middle row is the apex, the outer two are the culet and the top vertex at the depth of the surface they land on, so the axis profile is two straight segments meeting at a point. Its height is **derived in two steps**: `GEM_HALF_DEPTH` = `bladeStackTop(17, 55)` + 0.12 T + 0.38 × the stone's own half-width. The rise is a fraction of the half-width and not a depth on purpose — give it a fixed depth and narrowing the rhombus turns it into a spike. **Two things went with that directive and both were load-bearing**: a GIRDLE, a wall at `±halfWidth` one relief step tall that held the whole outline proud, and a BAND that held the crown at full depth across the middle 75% of the height — which is why the peak used to be a plateau three quarters as long as the stone. Measured on the result (`spec/measure_gem_facets.mjs`): apex at **0.500 across, 0.500 up**, four flanks per half, each flat to **0.11–0.19 units of bow and 1.7° of kink**. **The one face a 四角錐 does not have and this one cannot lose is the waist LEDGE**: both skins begin at `Y = 55`, so the surface under the stone steps 2.8 units there and the rim steps with it — 12 triangles, and the variant without it is rejected at +2.8001. The crop cannot settle any of this: its own half-maximum crossings read a bright top at a median 0.733 of the half-width on a stone 5–13 source pixels across carrying a one-pixel dark outline stroke that drags the crossing there by itself. Its **underside** is `bladeStackTop`, evaluated at each ring point, and its culet and apex are points ON that surface rather than on `Z = 0` — so the stone grows out of the dark core instead of running through the blade. That is the 2026-08-08 correction; see §3.                                                                                                                                                                                                                                                                                        |
| `crystalClamp{L,R}`              | **Three** points, a TRIANGLE, and the user's own sketch (`references/04-user-sketch-guard.png`) is the authority for that shape. Apex `(17, 55)` = the measured gem's waist vertex (the AUTHORITY line, §9). Inner lower `(0, 13)` = the gem's culet, so edge 1→2 IS the stone's own lower edge — max                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | gem − jaw | = 0.000000000. Outer lower `(34, 13)`: the 34 stays directed, the 13 is the culet's, which is what makes the floor one horizontal line from the axis outward. That floor is the hilt's structural plane and three other parts are derived from it (#15, #16, #17). The retired knee and the vertical inner face went with the slot the grip column used to be inserted into.                                                                            |
| `leatherConnector{L,R}`          | Root and rake **derived**; section, radius and — since 2026-08-12 — length directed. Integration #17, amended 2026-08-11: the root cap's LOWER RIM is `CLAMP_OUTLINE`'s outer vertex `(34, 13)`, because the user's sketch draws each arm's two long edges converging on that corner (`spec/zoom-guard/sketch-arm-root-left-8x.png`), and the rake is the shell's lower taper as an angle, −49.3987°, because a cap perpendicular to THAT axis has its diameter along the taper. `CONNECTOR_ROOT` — the cap's CENTRE — is that corner plus one `CONNECTOR_RADIUS` along `(−sin a, cos a)`, i.e. `(46.148, 23.413)`. Both together put the cap's WHOLE diameter on the crystal's flank with a front-view residual of 0.000005 — correction C's sentence, "the arm's inner silhouette edge and the shell's slanted edge are ONE line", as construction rather than as the target of a bisection. Until the amendment the corner was the cap's CENTRE, which hung the cap's lower half 10.413 units below the guard's floor in open air. The arm's own section is 31% wider than the crop's; see §11 open item 2c. Its LENGTH is **directed at 72** and the measurement it is directed against is on the record: the crop's own spinner axis is                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | x         | = 81.925 (the mean of the two gold caps' bbox centres and pixel centroids in `measurements.json`), which a length of 54.97 solves to 0.007 of a source pixel, while 72 lands the arm's outer end-cap centre at 93.005 — 11.080 units, 4.73 source pixels, wide of it. The X solve shipped for one pass and put the spinner balls visibly too high on the guard, so the user directed the length back. See §11 G4 for both pins and what each one costs. |
| `spinnerEnd{L,R}`                | Hangs **vertically**, the same orientation as `pointedMetalPommel`, lathed about `Y` with zero rotation. Direction measured: de-rotated upright, each arm-end→cap-centroid vector and each cap's PCA axis read within ~12° of straight down, none near the arms' −50°. **Shape: a straight-sided frustum, widest at the top — and the whole profile is DERIVED from the seat rather than tabulated at absolute heights, which is the 2026-08-13 correction.** `measure_spinner_taper.py` reads both caps per weapon-local row: each flank is straight to within one source pixel (linear RMS 0.57 px, bowing out from its own chord by 0.77 px) and neither cap widens downward by as much as one source pixel. The WIDE end is the crop's — radius 24.3, its own fitted 21.049 front-view half-width at the leather boundary ÷ 0.866, widened from 21.4 on 2026-08-08; the narrow end is the crop's blunt 8.1; the cap's BOTTOM is **DIRECTED** at Y = −90.8 the same day, spending the one measured pin this assembly used to hit (−109.65) to buy the crop's own cap length. Between them the radius is one straight line. Seat **derived** by `spinnerSeat()` — the largest horizontal ring that fits inside the arm's inradius _and_ short of its end cap, seated on the arm's own axis, so the flat top face is buried and invisible from every camera rather than mated flush against a face it can no longer meet — and the widest ring hangs `SPINNER_SEAT_CLEARANCE` below it, which is the shortest shoulder that is not a degenerate flat plate. What that replaces is a five-row table at absolute heights whose top ring came from the seat: the lathe interpolated between a ring that moved with the arm and a first row that did not, and the ramp it opened got wider every time the arm moved (19.492 units of exposed flank before the 2026-08-11 amendment, 29.677 after the 2026-08-12 length directive) without a single number in the factory changing. `audit_records.py` re-derives the profile from the arm and fails if more than 2.0 units of it still widen downward outside the arm's end-cap plane; the build scores **1.145**, and both historical arms are run as brackets. X is still the connector's outer end-cap centre, so the arm's length is what puts it there: at the derived 88.8001 the seat sits at (103.938, −34.227) against the crop's two gold caps, whose four estimates of this axis average | x         | = 81.925. That 22.013-unit deviation is the price of the 2026-08-12 directive and the 2026-08-13 projection together, and is printed by `audit_records.py` every run; §11 G4.                                                                                                                                                                                                                                                                           |
| `driver{L,R}{Upper,Lower}`       | Radiation centre `(0, −62)`, both elevations (pair means of four PCA axes) and the endpoint radius measured; circular section directed. Root radius **derived** by `driverRootRadius()` — the far crossing of the surface that buries the whole cap, which is the arm's inradius pulled in by the rod's own radius, not the arm's outer surface. That is why no cap rim floats proud of the leather and no rod reaches its arm's axis. `audit_records.py` recomputes it and prints it on every gate run.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `leatherGrip`                    | Shaft length and width measured (20 wide, against the brief's 24–32 starting contract — the artwork wins), lower edge measured at `−180.3`. Constant shaft width is directed, and correction A makes it the whole part: one octagonal COLUMN from the pommel to its top, no tang, no collar, no step. The top at `+13` is **derived** and is not an offset from anything — integration #16 makes it `CLAMP_FLOOR_Y`, face to face on the jaws' floor. `audit_records.py` recomputes the reach and the top against the built bounds and separately checks that the top face is inside the jaws' floor footprint in x AND in z, so a tang growing back and a column pushed back up between the jaws both fail.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `pointedMetalPommel`             | Bbox measured (tip at `−210.7`), profile **directed** to a straight cone. Its base ring is **derived and no longer a number of its own**: `POMMEL_RADIUS` _is_ `GRIP_HALF_WIDTH` and `POMMEL_SIDES` _is_ the column's 8, so the cone's base ring and the leather's bottom ring are the same ring — same plane, same circumradius 12, same facet count, front-view reach 11.087 on both — and `tests/ultima-v2-solid.test.mjs` compares them vertex for vertex. It used to carry radius 11 against the grip's 12, which put a 1-unit ledge at the junction and made the circumradius-vs-inradius question live; identical rings make it moot. Against the crop the cone still runs ~2 units narrow through `Y ≈ −190` — under one source pixel, and the price of a cone that also starts at the leather's measured edge.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |

A `+2.5°` driver elevation bias was tried against the overlay and made the silhouette IoU worse
(0.8859 → 0.8849), so the measured means stand.

---

## 6. Materials

Eleven materials, no texture maps of any kind — the source has zero surface relief and every
gradient in the artwork is reproduced as per-vertex colour interpolation. Parameters and the
measured `PALETTE` are in `buildMaterials()` and the `PALETTE` block of the factory.

Six things are not obvious from reading those, and every one of them has cost a pass:

1. **`material.color` must stay white (`VERTEX_ALBEDO`) on every material.** Three.js
   _multiplies_ it by the vertex colour. Carrying the measured albedo in both squares it:
   `#CDCFD8` rendered as `0.64` instead of `0.80` and the whole weapon came out flat mid-grey
   against a near-white reference. Vertex colour **is** the measured albedo here.
2. **Metalness stays at or below `METAL.bright = 0.35`.** The rig is near-ambient over a
   deliberately featureless environment, so a metalness-0.85 surface has nothing to reflect and
   renders near-black. An earlier pass lightened the clamp albedo two stops and the jaws stayed
   black — the albedo was never the problem _there_. It is measurably part of the problem
   everywhere else: measured inside each part's own projected footprint, an opaque `METAL.mid`
   surface renders at 0.215 of its vertex colour in linear light while a metalness-0 surface
   beside it renders at 0.447, so a metal part authored with the crop's raw colour comes out at
   half value. `PALETTE.gold`/`goldShadow` are therefore pre-divided by that transfer, and their
   JSDoc says so. Reflection is bought per material with `envMapIntensity`, never by raising the
   scene environment, which is global and would move every part's ΔE at once.
3. **`outerCrystal` is SOLID** — `transparent: false`, `opacity: 1`, `transmission: 0`,
   `depthWrite: true`, no `renderOrder`. Directed by the user on 2026-08-07 and a departure from
   the brief, which asks for "pale translucent"; `confidence-report.md` conflict 7 carries the
   departure and the crop evidence behind it. Nothing is depth-culled by it: the three inner
   layers stand 97.6 / 93.2 / 100.0% proud of it in the render, front and rear.
4. **The alpha blend was paying for LEVEL, not for translucency, and removing it exposes that
   the rig under-lights this material by 3.6×.** With `opacity: 0.35` the surface lit to 128 and
   the other 0.65 came from the WHITE BACKGROUND, which is what put it on 210. Solid, the same
   material renders at a median of **122**. Measured in linear light, the rig delivers **0.322 of
   albedo** while the artwork's shell sits at 0.701 against a measured albedo of 0.610 — it reads
   _brighter than its own albedo_, so no palette can reach it: the stops' whole remaining headroom
   to white is 1.11×.
   - **`envMapIntensity` cannot pay it, and the records were wrong to say it could.** three
     r0.185 `three.module.js:18690` overwrites the uniform with `scene.environmentIntensity` for
     any standard/physical material whose own `envMap` is null, which is every material here.
     Measured: at 1, 7.5 and 40 the re-framed render is byte-identical. `guardGold`'s and the
     black box's `envMapIntensity` values are dead code kept as a record.
   - **A white `emissive` multiplied by `vColor` pays it**, the same shader patch `purpleInsert`
     already uses. Proportional to the vertex colour is the load-bearing property: the facet steps
     and the Y ramp live entirely in vertex colour, so this raises the level and leaves the shape
     alone. Solved rather than dialled — `0.322 + E = 0.701 / 0.6052`, so `E = 0.836`.
   - The shell then measures **(215, 216, 228)** against the artwork's (216, 217, 227), and its
     profile along the blade tracks the artwork's to an RMS of 0.011 linear. Producer:
     `spec/measure_shell_value.py` → `artifacts/ultima-v2/gate/shell-value.json`.
   - **The three `PALETTE.shell*` stops were re-derived onto the right axis.** They had been
     Layer 6's census bands — `#E6E7F2 / #CDCFD8 / #B5B6BF` — fed into `applyRamp` as a vertical
     gradient, but a census is a histogram with no axis and those bands run ACROSS the blade, not
     up it. Along Y the artwork is flat at 0.684 linear to Y ≈ 400, dips 0.03 through 400–500 and
     climbs to 0.842 at the tip; the stops are that profile, at Y = 200 / 480 / 760. The census's
     bands are still in the build — they are what `applyFacetSteps` makes, on the axis they were
     measured on.
   - **What survived from the translucent build is the diagnosis, not the fix.** `transmission`
     stays at 0: refraction returns the environment, and this environment is a featureless grey
     gradient at 0.22 intensity, so every point of it was a straight subtraction (handing the job
     to transmission alone measured 125, spanning 112 → 161). `FrontSide` stays: `DoubleSide` over
     `depthWrite: false` drew the far wall and the near wall into the same pixel and averaged
     every facet into one middle grey.
5. **`applyFacetSteps` takes the MIRRORED key for the rear half of a Z-split pair.** The key
   carries +0.66 in Z, so a face and its mirror image across the cut plane land on opposite sides
   of the quantiser — `(0, 0, +1)` scores step 1 and `(0, 0, −1)` scores step 0, which at the
   insert's strength of 0.55 is a multiplier of 1.088 against 0.901. Two meshes asserted to be
   exact mirrors therefore shaded a factor of 1.20 apart on the same surface, and nothing asked:
   the assertions were all about _where_ the two halves are, none about what they look like.
   Measured, not reasoned — captured unlit so the pixel IS the vertex colour, the two films'
   shell-facing undersides read (78.67, 43.82, 164.43) on the front half against
   (85.83, 48.18, 178.52) on the rear, a linear-light ratio of 1.2003 against the 1.2076 the
   arithmetic predicts. It is now 1.0000, asserted from the geometry every gate run.
   **The rig's own key is the same measured vector**, so a lit render cannot separate the two
   causes and never could: `spec/capture_skin_faces.sh` takes each frame twice, lit and unlit, and
   that pair is what splits a colour symptom into the part the model baked and the part the rig
   added. What the rig adds is 1.0629 and stays — see open item 5.
6. **`clampMetal` carries `polygonOffset(−1, −1)`, and it is the consequence of a geometric
   requirement rather than an appearance choice.** Integrations #15 and #16 put three downward
   faces on ONE plane at `CLAMP_FLOOR_Y`: the two jaws' floors (±16 deep), the shell's base cap
   (±11) and the grip column's top (±11.087). That coplanarity **is the specification** —
   `check_centerline.py` asserts `shell.minY = clamp.minY` and would reject any of the three being
   nudged off it — and three exactly coplanar faces are a depth-buffer tie, which resolves per
   triangle and showed as a pale band of crystal cutting across the guard's underside in
   `closeup-clamp-bases.png`. Biasing the JAWS toward the camera settles the tie the way the
   object does: the jaws' floor IS the guard's underside and it covers both other faces outright
   (±34 × ±16 against ±34 × ±11 and ±11.087 × ±11.087), so nothing that ought to be seen is
   hidden. It is deliberately **not** `renderOrder` — draw order cannot settle a tie between two
   opaque faces, only a depth bias can, which is why `renderOrder` came off the shell when that
   went solid — and it is **not** slack in the flush assertion: the geometry is untouched and the
   assertion still reads +0.000000.

Shading is baked into vertex colour by `applyFacetSteps`, which quantises the face normal
against the key into **three flat steps**. That is the whole shading model for a flat-shaded
source; the lights only tint it, which is why the facet bands survive any lighting setting.

---

## 7. Lighting and cameras

In `createUltimaWeaponV2LookDev.ts`, which carries every value and every reason. Two facts
matter outside that file: the artwork's **18.13° lean is a camera roll, never geometry**, and the
review cameras are **orthographic on purpose** — a perspective camera cannot be compared with an
orthographic crop pixel-for-pixel. `REVIEW_VIEWS` and the per-view framing margins live there
too; the margins are fixed per view and are never fitted per render, so a silhouette change shows
up as a silhouette change rather than being absorbed by the framing.

---

## 8. Current measured results

From `spec/silhouette-report.json`, `artifacts/ultima-v2/gate/*.json` and `parts.json`.

| Metric                                                                                | Budget                                            |                                                                                                                               Current | Verdict                                        |
| ------------------------------------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------: | ---------------------------------------------- |
| Silhouette IoU vs artwork, artwork-match camera                                       | ≥ 0.90                                            |                                                                                                                            **0.8608** | misses by 0.039                                |
| Tip / pommel-tip / left / right landmark error                                        | ≤ 2.5% of image height                            |                                                                                                            1.00 / 0.59 / 1.00 / 1.00% | pass                                           |
| Front/rear silhouette IoU                                                             | symmetric                                         |                                                                                                                            **0.9964** | pass                                           |
| Lift above the shell's crest: insert / core / gem                                     | skins step 0.035–0.060 T each, the stone ≥ 0.25 T |                                                                                                        **0.0500 / 0.1000 / 0.4507 T** | pass                                           |
| Shell centre Z (every lift is measured from its crest)                                | 0 ± 0.001                                         |                                                                                                                               0.00000 | pass                                           |
| Split pairs: mirrored at both ends, all three clear of the cut                        | ≤ 0.001                                           |                                                                                                                         0.00000 worst | pass                                           |
| The stone's own thickness, each half                                                  | ≥ 0.35 T                                          |                                                                                                                          **0.5579 T** | pass                                           |
| Blade layers inside the SHELL, the four SEATED ones                                   | ≤ 0.20 normalized units                           |                                                                                                      **0.020** (insert), 0.000 (core) | pass                                           |
| Blade layers inside the LAYER UNDER THEM, the four SEATED ones                        | ≤ 0.20 normalized units                           |                                                                                                      **0.020** (insert), 0.000 (core) | pass                                           |
| **The stone INSIDE its host, which it is by design**                                  | ≤ the socket's own depth, 5.90                    |                                                                                    **3.000** into the shell, **5.800** into the stack | pass, by exception                             |
| **The stone's base is a PLANE, and the plane is under the host**                      | spread = the socket's depth; no air above it      |                                                          **−5.8002 … +0.0255** — spread 5.8258 against 5.90, air +0.0255 against 0.05 | pass                                           |
| **Each SEATED underside FLUSH on the surface it lies on, signed**                     | ≤ 0.20 normalized units either way                |                                                                                  −0.0200 … +0.0182 (insert), −0.0001 … +0.0305 (core) | pass                                           |
| **Each film's outer face above its own seat**                                         | its nominal 1.400 ± 0.20                          |                                                                                                                   **1.3800 … 1.4305** | pass                                           |
| The socket inside the shell — and it is down to the two JAWS                          | at or below the diamond's waist                   | each jaw is **12.165** units into the crystal and reaches **Y = 55.00** against a ceiling of 55.00; both arms read **0.000** units in | pass, by exception                             |
| A mirrored pair's vertex colour, inward faces / outward faces                         | ≤ 1/255                                           |                                                                                            **0.000000 / 0.000000** on all three pairs | pass                                           |
| Insert skin / core skin / stone proud of the SHELL, front / rear                      | ≥ 70%                                             |                                                                                     **97.6 / 93.2 / 100.0%**, identical on both faces | pass                                           |
| Diamond proud of the DARK CORE, i.e. of the layer it sits on                          | ≥ 95%                                             |                                                                                                                    **100.0 / 100.0%** | pass                                           |
| Shell-to-driver front-view gap                                                        | ≥ 0.75 D, target 1.00 D                           |                                                                                                                     **1.14 D** (25.1) | pass                                           |
| Shell's lowest edge against the clamps' lower edge                                    | equal, ± 0.001 world                              |                                                                                                                         **+0.000000** | pass                                           |
| Correction D's authority line: insert / core lower edges, stone's centroid            | on the clamp apex, ± 0.1 / ± 1.0 normalized       |                                                                                                          **+0.000 / +0.000 / −0.362** | pass                                           |
| #15 shell's lowest edge vs the two jaws' floor edges added together                   | equal                                             |                                                                                                         **68.000 vs 34.000 + 34.000** | pass                                           |
| #16 grip top plane vs the jaws' floor; top face inside their footprint                | equal; strictly inside                            |                                                                              **13.000 vs 13.000; 11.087 in x and z inside ±34 × ±16** | pass                                           |
| #17 arm root cap's LOWER RIM vs the jaws' outer vertex; rake vs the shell's taper     | equal, ± 1e-6                                     |                                                                                    **(34.000000, 13.000000); −49.3987° vs −49.3987°** | pass                                           |
| #17 the WHOLE root cap against the shell's flank, front view, rim to rim              | ≤ 0.01                                            |                                                                                                          **0.000005** over 65 samples | pass                                           |
| Guard hand-over to the arm, swept over the arm's own height                           | equal to the octagon's apothem notch, ± 1e-6      |                                                                                                     **−1.6041 vs −1.6041**, at Y = 13 | pass                                           |
| Guard underside opening between the column and each arm                               | recorded, not thresholded                         |                                                                                                                 **46.803** at Y = −13 | —                                              |
| Triangles at `detail: "full"`                                                         | —                                                 |                                                                                                                               **868** | —                                              |
| The stone's apex, as a fraction of its own front-view box                             | over the rhombus's centre                         |                                                                                               **0.500 across, 0.500 up**, both halves | pass                                           |
| Each of the stone's four crown flanks per half, against its own best-fit plane        | flat enough that `applyFacetSteps` cannot band it |                                                                      **bow 0.0000 u, kink 0.00°** — one triangle each, exactly planar | pass                                           |
| The stone's faces per half                                                            | 4 crown + socket wall + base                      |                                                                                               **4 crown / 8 wall / 2 base triangles** | —                                              |
| Named nodes / meshes                                                                  | —                                                 |                                                                                                                           **22 / 19** | —                                              |
| **Assembly anchor graph: attachments / sockets / cross-branch joints, all resolving** | zero unresolved                                   |                                                                                                        **22 / 53 / 34, 0 unresolved** | pass                                           |
| **Every component's declared box against its built bounding box**                     | ≤ 0.001 world                                     |                                                                                                                          all 23 equal | pass                                           |
| `check_part_coverage`                                                                 | —                                                 |                                                                      printed by the gate; `author_spec.py` declares both insert skins | —                                              |
| Forge tier-1 blockout IoU                                                             | ≥ 0.85                                            |                                                                                                                            **0.8206** | **RED**, by 0.0294 — documented limitation, §8 |
| Forge tier-1 IoU, other passes                                                        | ≥ 0.85                                            |                                                                                                                            **0.8204** | **RED**, by 0.0296 — same cause                |

**Seven of those rows are the hilt's own gates** — the flush base plane, the authority line, the
three integration equalities, the root-cap residual and the hand-over seam (§9). The
penetration rows, the thickness row and the mirror-colour row are the blade correction's; the two
FLUSH rows are 2026-08-09's.

**The penetration rows tightened from 1.0 to 0.20 normalized units, and 0.20 is bracketed on both
sides rather than parked above a residual.** The residual is two linearizations that shrink
together — a layer's underside is ruled straight between its own rings, and the surface it is
ruled against is `loft`'s triangulation of the shell rather than the shell's analytic section.
Both agree on the rails and depart in the middle of a band. Measured through the probe on
otherwise identical geometry (`artifacts/ultima-v2/diag/bracket-trapezoid-*/parts.json`, producer
`diag/bracket_flush.py`), the stone's own seat clearance against how finely the lower trapezoid is
cut:

| the trapezoid, `Y = 13 → 55`   |      the stone's seat | the gate |
| ------------------------------ | --------------------: | -------- |
| one band                       |     −0.2017 … +0.6203 | fails    |
| halved, `+34`                  |     −0.1532 … +0.2991 | fails    |
| quartered, `+23.5, +34, +44.5` | **−0.0001 … +0.1146** | passes   |

**The first two rows are the 2026-08-09 bracket run**, measured on that pass's plateau stone; the
third is today's 四角尖柱. It is the shell's mesh the rows vary and not the stone, and the seat is
the stone's UNDERSIDE, which the shape of its crown does not touch — the third row read
−0.0826 … +0.1148 on the plateau and on the 錐冠 alike, and reached −0.0001 only when `loft`
stopped cutting warped quads on a fixed diagonal. **The whole table retired the same day**: the
stone stopped being seated at all, and what the seat family measures on an INLAID base is the
socket's own depth, **5.8002**. Kept as the record of what the subdivision bought while the stone
still lay on it — the two films still do, and they are what the ladder protects now.

0.20 is the geometric midpoint of the last two — 1.74× above what this build carries and 1.50×
below the coarsest mesh it rejects — so the subdivision is load-bearing and not a preference. Every
defect §3 lists is 10× to 22× over it.

**The stone's share proud of the SHELL is now 100.0%, and the number moved because the INSTRUMENT
changed, not because the stone did.** Its geometry is untouched since correction D; what changed is
that the solid shell entered the opaque backbuffer three.js resolves `rootGem`'s 22% transmission
against, dimming the stone's own red by about 8% even where it plainly wins the depth test. Pixel
identity scored that as occlusion and read **1.2%** — yet all 1530 failing pixels stayed on the
gem-vs-shell colour axis at a survival of 0.847 or better and not one took the shell's colour
(`artifacts/ultima-v2/diag/gem_vs_shell.py`). Same instrument failure and same fix as the
gem-against-the-core test of 2026-08-08: scored by survival on a once-eroded footprint, bracketed
by doctored frames through the same script — the shell winning the whole overlap scores 0.0%, its
outer 4 px 67.3%, its outer 3 px 77.4% — so the 0.70 floor cuts between a three- and a four-pixel
buried outline and the build clears it by 30 points. The two opaque films are untouched by any of
this and are still scored by identity, at 97.6 and 93.2%.

The figures this replaces belong to the translucent build and to correction D's own price:
95.8% → 93.6%, because the insert skin used to run down to `Y = 42.6` and propped the gem's seat
up by one `SKIN_STEP` over `Y = 42…55` until the film's lower edge was pinned to the authority
line.

**One figure in this table was a rear-render defect and never a build.** With the shell's base ring
collapsed to a POINT, the loft's last band is eight slivers off a degenerate ring and the crystal's
two faces stop being triangulated as mirrors: the stone measured 93.6% proud on the front and
**54.3%** on the rear, where the same stone reads 100.0% on both today. Every geometric assertion
passed throughout — pointwise 0.202 on both halves, both mirror tests 0.00000, identical bounding
boxes — and only the rear render could see it. That is the fourth time on this model that a symptom
appeared in colour and the cause sat somewhere no bounding box reaches.

**The triangle count is 984, and the stone gave back 108 of them in one pass.** The 2026-08-09
flush pass had added 200 — three shell stations subdividing the lower trapezoid (+48), the stone's
ring list gaining those stations and the ledge pair at the films' base (+120), each film's apex
closing with a zero-width edge instead of a point (+32) — and none of them moves a silhouette,
because every added ring is an existing line evaluated at a new height and a zero-width ring is a
point in the front view. Another 52 are the `loft` end-cap repair: four drivers, two connectors,
the grip, the pommel and both spinner ends had been shipping without caps.

Then the stone became a 四角錐 and each half went **126 → 112 → 72**. The crest collapsing to a
point took one ring point; the girdle took two more and the two band stations took two whole
rings. That is the shape of the trade this pass makes: a solid with five faces needs fewer
triangles than one with nine, and the faces it stops having are the ones that held the outline
proud. Checked rather than eyeballed:
`tests/ultima-v2-solid.test.mjs` asserts zero boundary edges and positive signed volume on every
part at all three detail levels.

IoU is measured after uniform-scale normalization and a translation search (±8% of span), so it
is a shape score, not an alignment artifact. `widthProfileByBand` localises the residual: bands
0.6875 and 0.75 — the lower blade, exactly where the neck converges — read 0.2271/0.2333 in the
crop against 0.2115/0.1987 in the render, while every other band agrees to within 0.005. The IoU
fell 0.8937 → 0.8875 in the relief pass for that reason and no other; see `confidence-report.md`
conflict 4.

**"Per-part colour ΔE" is not per-part, and knowing that is what stops the number being chased.**
`per_part_color_delta` never samples a component's own region. It k-means the WHOLE render's
foreground into five Lab clusters and scores each component's declared albedo against its nearest
cluster centre. So the figure is "how far is this component's colour from the render's five
dominant colours", and it moves whenever the _area proportions_ of the weapon change, even when
no material and no surface does. Recorded, not fixed.

**The ΔE gate is red**, at a maximum of **57.55 against a 20.0 threshold**, failing
`material-pass` and `surface-pass` (`artifacts/ultima-v2/gate/tier1-material-pass.json`,
`tier1-surface-pass.json`). It is the diamond's saturated red, which is far too small an area to
form a cluster of its own at any depth. It came down from 61.94 when the shell's blending was
fixed — see §6 — and the shell now measures a mean of (215, 216, 228) against the artwork's
(216, 217, 227), read by `spec/measure_shell_value.py` over the whole re-framed render. Since
then it has only tracked area proportions — the same gold and the same leather over different
areas, with no material moved at any step. Ten geometry passes carried it 56.49 → 57.49, and the
per-step ledger is the retired-value list in `audit_records.py` rather than a chain of arrows here.
**The solid-shell step is the one worth naming**: the shell is the largest surface in the frame,
its blending changed and its palette was re-derived, and the gate moved by 0.08. That is the
clearest evidence yet that this metric is not reading per-part colour — it k-means the whole render
into five clusters and the pale cluster's centre barely moves when the pale surface's mean moves 5
levels. None of these is a material regression, and none is worth chasing.

**The tier-1 blockout IoU is RED at 0.8206** against a 0.85 floor, and the other four passes are
red at 0.8204 with it. **This is the price of eight user directives in a row, and it is a
documented limitation rather than a defect with a fix in hand.** The whole chain, each step
measured on the gate and none of it argued:

| when              | what the user directed                                                                                                                                         |                                              blockout tier-1 IoU |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------: |
| before 2026-08-11 | —                                                                                                                                                              |                                     **0.8553**, a pass by 0.0053 |
| 2026-08-11        | both arms up one radius along their own normals, so each root cap's lower RIM sits on the jaw's outer corner instead of straddling it                          |                                        **0.8478**, red by 0.0022 |
| 2026-08-12        | `CONNECTOR_LENGTH` back to 72 — the arms are 17 units longer, so the spinner balls hang where the user wants them rather than where the crop's X pin puts them |                                        **0.8367**, red by 0.0133 |
| 2026-08-13        | the spinner caps are frusta, widest at the TOP, instead of spinning tops widest half way down                                                                  |                                        **0.8348**, red by 0.0152 |
| 2026-08-13        | the arms LONGER and the caps SHORTER against the artwork, which turned `CONNECTOR_LENGTH` into the derived 88.7455                                             |                                        **0.8175**, red by 0.0325 |
| 2026-08-08        | the caps SHORTER again and WIDER at the wide end, against the artwork — `SPINNER_BOTTOM_Y` −109.7 → −90.8, `SPINNER_TOP_RADIUS` 21.4 → 24.3                    |                                        **0.8209**, red by 0.0291 |
| 2026-08-09        | the stone's crown to a POINT, which took `loft` off its fixed diagonal and retriangulated every part                                                           |                                        **0.8208**, red by 0.0292 |
| 2026-08-09        | the stone to a 四角錐 outright — five faces, apex over the centre — which cost it the girdle and the depth band                                                | **0.8208**, unmoved: the stone is behind the shell in this frame |
| 2026-08-09        | the stone SET INTO the crystal on a flat base, so its girdle line is level instead of following a surface that steps                                           |                                        **0.8206**, red by 0.0294 |

The first step moved the arm-and-spinner assembly up and out of the artwork's own dark mass. The
second pushed it further out along the same rake. The third costs 0.0019 for the shape.

**The fourth costs 0.0173, the most of any of them, and it is the one where the trade is
explicit.** Three pins, one length, and the length can only slide along a locked ray (§11 G4). It
now sits at the projection — the closest the arm's end can get to where the crop actually puts it
— and that buys the two VERTICAL pins at the cost of the horizontal one.

**The fifth is the only step in the chain that gave IoU back, +0.0034, and the reason is worth
having in writing: the caps' overlap with the crop's was never vertical.** Their axis is 22 units
outboard of the crop's, so gold below the leather barely overlaps the crop's gold at any height —
shortening the cap deleted render-only pixels (0.0585 → 0.0529 of the union) faster than it gave
up reference ones (0.0854 → 0.0862), and widening the shoulder put area back where the crop does
have gold. The whole-model silhouette moved the same way, 0.8561 → 0.8609.

| pin, both caps averaged |    crop |                 at L = 72 |           at L = 88.8001 |
| ----------------------- | ------: | ------------------------: | -----------------------: |
| gold's topmost row      |  −53.45 | −21.00, **13.86 px high** | −34.00, **8.31 px high** |
| gold's lowest row       | −109.65 |          −110.00, 0.15 px | −90.00, **8.39 px high** |
| exposed cap length      |   56.20 |                     89.00 |                **56.00** |
| spinner axis \|x\|      |  81.925 |   93.00, **4.73 px wide** | 103.94, **9.40 px wide** |

Gold's lowest row used to be the one pin this build hit; 2026-08-08 spent it to buy the LENGTH —
§11 G4 carries why one length cannot hold both ends.

The silhouette gate reads the horizontal one hardest, because the caps sit at the widest point of
the whole weapon and 22 units of splay is 22 units of non-overlap on each side. `spec/zoom-spinner/
compare-arms-4x.png` is the artwork beside the render over the same window, at 4× NEAREST, and it
shows both halves of the trade in one frame. **Neither the floor nor the IoU's computation was
touched at any point** — `compare_render.py` and `diagnose_render.py` are the same scripts scoring
the same re-framed 210×434 crop, and the number is simply worse.

Three levers were swept before the second directive and none reaches the floor — all superseded by
today's 0.8206, kept as the record of what was swept rather than as a claim about this build:
`CONNECTOR_LENGTH` over 40…72 peaks at 0.8478 (`L` = 55, falling monotonically either side to
0.8419 at 40 and **0.8367** at 72); the crop's own measured arm section 12.148 reads 0.8464, so the
arm's 31% excess section is not what this gate reads; undoing the amendment reads 0.8553. The
sweep's own row for `L` = 72 predicted today's value to four decimals, so nothing here appeared
from somewhere unexamined. Only putting the arms back recovers the gate and the directives outrank
it; **`L` = 55 remains the value the crop's X pin solves for**, kept in §11 G4 rather than deleted.

The residual loss, from before the amendment, is still located rather than guessed: `silhouette_diff` by 20-row band puts the bulk of the
missing pixels in the guard region, where `detail: "blockout"` hides both clamps and nothing else
can fill the space they occupy at `full`. The trapezoid the lower shell carries narrows that
region further, and that is what put this gate on the floor to begin with. The two ways to buy
margin back there were both rejected: widening the trapezoid's base past the jaws would
show pale crystal outside them, and re-cutting the blade's upper taper (the render runs
2.5–3.7 units wide of the crop from Y≈590 to 690, worth roughly +0.005) reshapes the whole blade
to fix a hilt-region gate. Accepted as the trapezoid's price.

**Integration #15 took that region to 0.8553**, the best this gate has read — today's 0.8206 is
eight user directives later — because the shell's lowest
edge is 68 wide on the jaws' floor instead of a 19.8-wide tenon 26 units lower, so `blockout` sees
the crystal even where it hides the jaws. It paid back the 0.0006 deleting the grip's tang cost and
the 0.0009 deleting `guardCore` earned, both of which were the same ledger — `blockout` hides the
clamps, so anything filling guard pixels shows up here and nowhere else. Against it, the straight
cone spends 0.0007 entirely at the pommel: no cone with the measured apex at −210.7 and the
column's own base ring (front-view reach 11.087, compared vertex for vertex by
`tests/ultima-v2-solid.test.mjs`) can cover a crop silhouette inflated by the pommel's cream
rim-glow. Both accepted; §11 item 4.

---

## 9. Hard constraints that must not be broken

Most of these are asserted, not trusted. The table says where; a future edit that breaks one
fails a gate rather than a review.

| Must not                                                                                                                                          | Caught by                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Re-introduce `centralGripSocket`, any `driverSocket*`, `gripEndCollar` or `guardCore`; add or drop any of the 19 parts; merge or split one        | `check_centerline.py` (two-way), `audit_records.py`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Give `leatherGrip` a tang again, or push its column back up between the jaws**                                                                  | `audit_records.py` — integration #16's two clauses. The plane clause holds `GRIP_TOP_Y` to `CLAMP_FLOOR_Y` exactly (bracketed at +3.0000 against the retired `GRIP_BURIAL`), and the footprint clause holds the top face's reach inside the jaws' floor in x AND in z — a widened T-head fails the second even if someone keeps the first. The built `maxX`/`maxY` are checked against the manifest besides, so a tang fails three ways. **This replaced the guard's DAYLIGHT SWEEP**, which is retired rather than relaxed: #15 makes the shell a solid interval from the axis out at every height in the band, so the sweep returns +0.000 for ANY jaw outline, including the one it was written to reject. A clause that cannot fail is not coverage |
| **Let the clamps' lower edge stop being one horizontal line, or stop being flush with the shell's lowest edge**                                   | `audit_records.py` for the horizontality, `check_centerline.py` for the flushness — and the second is an EQUALITY, so a jaw hanging below the crystal fails just as a crystal hanging below the jaw does. The one-sided form this replaced allowed the first                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **Move `CLAMP_OUTLINE`'s inner-upper vertex off `(GEM_HALF_WIDTH, GEM_WAIST_Y)`, or let any of the four features pinned to it drift**             | `check_centerline.py` on the built model — the shell's taper start, both skins' lower edges and the stone's own CENTROID against the built jaw's apex — and `audit_records.py` on the source literals. The stone is checked on its centroid because a box stays centred between the two tips however far the waist has slid                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **Let a connector arm stop short of the shell's lower slanted edge, or slide along it**                                                           | `audit_records.py` — the arm's root and rake are recomputed from `CLAMP_OUTLINE`, `SHELL_STATIONS` and `CONNECTOR_RADIUS`, the WHOLE root cap is sampled against the shell's own front-view edge rim to rim (residual 0.000005), and the handover seam is swept over the arm's own height range and held to the octagon's apothem notch as an EQUALITY rather than to a floor. Four brackets: +16.0000 with the cap centre back on the jaw's corner (the reading retired on 2026-08-11) and +1.6041 for the same arm at the handover clause, +23.8097 against correction C's measured root, +0.0142 against the retired −50° rake                                                                                                                       |
| Move a central part off `X = 0`, or break a mirrored pair (0.001 world)                                                                           | `check_centerline.py`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Let pale crystal continue below the clamp assembly                                                                                                | `check_centerline.py` — `shell.minY = clamp.minY`, now an equality                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Reveal an inner crystal by dropping the shell's opacity instead of by geometry; reverse the stack order; let a layer sink back into the one below | `check_centerline.py` — the lift ladder. Every lift is positive and strictly increasing, and no material change moves any of it                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Let either skin grow back into a boss**                                                                                                         | `check_centerline.py` — each skin's step over the layer under it must stay inside 0.035–0.060 T. The build this replaced stepped 0.100 T and 0.065 T and fails here                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Let the diamond flatten into a coloured patch on the skins**                                                                                    | `check_centerline.py` — the stone's step over the last skin must be ≥ 0.25 T. The build this replaced stepped 0.120 T and fails here                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Extrude relief onto one face only, or let a split pair drift apart                                                                                | `check_centerline.py` — every pair is mirrored at BOTH ends, and each layer's rear lift must equal its front lift                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Let any split pair reach the cut plane                                                                                                            | `check_centerline.py` — the split-pair block. All three are seated now; the diamond used to be REQUIRED to reach it and that requirement is what drove it through the crystal                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **Put anything inside `outerCrystalShell`**                                                                                                       | `check_centerline.py` — the harness's pointwise probe, ≤ **0.20** normalized units for every blade layer against the shell AND against the layer under it. Bracketed both ways: the residual is 0.020 and the geometry this replaced reads 4.894 / 1.649 / 16.800                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **Let a layer FLOAT above the surface it is laid on**                                                                                             | `check_centerline.py` — `stackConformity`'s SIGNED seat clearance, ≤ 0.20 normalized units in EITHER direction, on the underside faces only. The row above is one-sided and clamps at zero, so a layer with a slot of air under it scores 0.000 on it: three did, and all three passed. Bracketed with doctored factories, each reverting one clause on otherwise final geometry (`diag/bracket_flush.py`) — the stone with no ledge at the films' base +2.8001 (the one-sided probe reads 0.000 there and PASSES), a zero-width film counted as covering the axis +2.8001 (one-sided 0.085, PASSES), a film's apex closed at its outer depth +1.4000 (one-sided 0.061, PASSES)                                                                         |
| **Coarsen the shell's lower trapezoid**                                                                                                           | same — the stone is seated on it over `Y = 13…55`, and a mesh that no longer tracks its own analytic section shows up as the stone's seat leaving it. Halving the subdivision scores +0.2991 and fails; removing it scores +0.6203 and fails                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **Thin or inflate a film somewhere inside its own footprint**                                                                                     | same — each skin's outer face has to stand its own nominal `SKIN_STEP` above its own seat, everywhere, ± 0.20. It is the outer half of the sentence the row above makes about the underside                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Let the socket's overlap with the shell creep up the blade                                                                                        | same — the two jaws, the grip column and the two connector arms are inside the crystal by exception, and the exception stops at the diamond's waist                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Let the diamond flatten into a plate on the skins**                                                                                             | `check_centerline.py` — each half at least 0.35 T thick, derived as `(GEM_RELIEF_STEP + GEM_CROWN_RISE) / T`. Half of what the retired "reaches the cut" assertion was protecting; the other half is the mirror test                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **Shade the two halves of a mirrored pair differently**                                                                                           | `check_centerline.py` — inward and outward face colours within 1/255. `applyFacetSteps`' key carries +Z, so an unmirrored key puts a face and its mirror image on opposite sides of the quantiser; `keyZ` mirrors it for the rear half of every Z-split pair. Bracketed at 0.0086–0.2401 unmirrored against a residual of **0.000000** on all six — it was 0.000311 on the stone's outward facets until `loft` stopped cutting the two halves on opposite diagonals                                                                                                                                                                                                                                                                                     |
| Let a relief pass the ladder while sinking inside the shell where the ladder cannot see                                                           | `measure_relief_visibility.py` — ≥ 70% of each face proud, front and rear within 0.02                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Let the stone pass every depth assertion while the layer directly under it swallows its outline                                                   | `measure_relief_visibility.py` — ≥ 95% of the gem proud of the DARK CORE. A different question from clearing the shell, and asking only the first is how the gem shipped with its whole rhombus buried. The floor is bracketed by doctored frames run through the same script: the core winning the whole overlap scores 49.6%, the core winning only the gem's outer 3 px — the previous build's actual defect — scores 88.7%, and the build scores 100.0%                                                                                                                                                                                                                                                                                             |
| Let the shell grow back into a driver                                                                                                             | `audit_records.py` — front-view clearance ≥ 0.75 diameters                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Build a rear face as a flat closing polygon                                                                                                       | `front_rear_overlay.py`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **Leave a component anchored to a socket that does not exist, or that exists somewhere else**                                                     | `audit_records.py` — the anchor-graph block. 10 of the 22 attachments were in this state until 2026-08-10 and nothing was looking: five named a socket id that existed nowhere in the file, five named one owned by another component. Four clauses now, closing the loop both ways — the names resolve, the two ends land on the same WORLD point, no socket is an orphan, and every cross-branch `joints` entry resolves. Bracketed with six doctored specs, one broken clause each                                                                                                                                                                                                                                                                   |
| **Let a component's declared box drift off the built one**                                                                                        | same — `dimensions` and `transform.position` are read out of `parts.json` by `author_spec.py` and re-checked against it here. Eight had drifted: the drivers carried a retired root radius, the insert a retired base, the pommel radius 11                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **Ship a mesh with a missing or inverted end cap**                                                                                                | `tests/ultima-v2-solid.test.mjs` — zero boundary edges and positive signed volume, every part, all three detail levels. `loft` capped ends by flattening each ring to (x, z), which is degenerate for every `radialSectionX` ring, so four drivers and two connectors shipped as open tubes and the grip, the pommel and both spinners with both caps inverted. Backface culling makes both silent and no render gate saw any of it                                                                                                                                                                                                                                                                                                                     |
| Quote a retired figure in any document under this exhibit                                                                                         | `audit_records.py`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **Let `confidence-report.md`'s confidence table disagree with the spec**                                                                          | `audit_records.py` — it reads every backticked component name and the number beside it. Three rows had drifted, and the retired-figure net could never have caught them: it matches whole strings, and "0.55" is a substring of half the numbers in the folder                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |

The rest have no gate, and each lives as JSDoc on the constant it guards in
`createUltimaWeaponV2Model.ts`: the connector arms staying closed
cylinders, a rod never crossing its connector's axis, the spinner ends staying blunt, vertical and
seated inside their arms rather than butted flush against them,
the grip's SHAFT staying constant-width and collarless from the guard's underside down to its
measured edge — the leather is no longer allowed to widen anywhere — the pommel staying one
straight cone whose base ring is `GRIP_HALF_WIDTH` and `POMMEL_SIDES` rather than a second pair of
numbers (that one DOES have a gate, in `tests/ultima-v2-solid.test.mjs`, which compares the two
built rings vertex for vertex), `material.color` staying white on a vertex-coloured material,
metalness staying at or below `METAL.bright`, no texture maps, the 18.13° lean staying a camera
roll, the review cameras staying orthographic, the `part.rest.copy(...)` loop staying at the
end of the build, and — new with the 2026-08-08 correction — **no face on the blade being bounded
by a plane**: every underside is the surface it meets, evaluated at the same `x` breaks as the face
above it, and every end cap is triangulated in its own plane rather than fanned through a centroid
that a crescent ring does not contain.

**2026-08-09 adds the Y half of that sentence, and it has a gate as well as JSDoc:** a layer's
ring HEIGHTS are derived from the surface under it, never listed — every knee of that surface
inside the layer's span, every crossing of one of its profile breaks with the layer's own rim, and
a PAIR of rings wherever it steps. `skinStations` and `GEM_SEAT_STATIONS` are the two
implementations and they share `signChangeStations`; a station typed in by hand is the smell.

**One constraint has no home in code, so it lives here:** do not change the blade above the
measured base — the `Y ≥ 110` stations, the insert's outline, the four-layer hierarchy — to chase
a hilt problem. Those numbers are measured and have survived three correction passes.

---

## 10. How to verify a change

The command sequence and the reason its order is not optional are in `RELATIONSHIPS.md` §3 and
§7. They are not repeated here; two copies of a command list is how one of them goes stale.

---

## 11. Open items

### The guess list for the hilt integrations

Five readings the evidence does not settle. Each names the part, the two readings, which one is
built and on what authority — so the next pass argues with a decision rather than rediscovering
that one was made.

**G1. The guard's UNDERSIDE is open between the grip column and each arm, and the crop says it is
solid.** Read: the user's sketch draws white paper in that region on both sides — below the jaws'
floor, outboard of the column, inboard of the arm — and the arms rake away from the corner rather
than closing on the shaft. The other reading is `measure_authority`'s: the crop's dark mass runs
unbroken across the full width down to `Y = −8`, first opening beside the grip at `−12`. **Built to
the sketch**, because the sketch is the higher authority for the hilt and the crop is a projected
3/4 view in which a dark pixel cannot be assigned to a part. The opening is measured rather than
waved at — `audit_records.py` prints it every run at **46.803 units at Y = −13**, recorded and not
thresholded, so re-filling it cannot happen quietly. It read 25.730 until 2026-08-11, when the arms
came up one radius along their own normals to hang off the jaws' corners instead of straddling
them; the arms' inner silhouettes came up with them and the opening widened by 21.1. If the crop
wins later, the part that fills it is a new one and this figure is where its size comes from.

**G2. The sketch's PROPORTIONS are not used, only its topology.** Its jaw is 164 px wide against
118 px tall — an aspect of 1.39 where `CLAMP_OUTLINE` is 34 / 42 = 0.81 — and its blade is drawn
with parallel sides rather than as a trapezoid. So the sketch is read for which part meets which
and where, and every dimension still comes from the crop. The one dimensional thing taken from it
is a RATIO that survives the distortion: one jaw's floor edge and the shell's lowest edge are the
same length in it, 155 px against 143 px, 8% apart — which is integration #15.

**G3. The lower taper's slope is arithmetic between two crop fits that disagree with each other.**
`measure_authority` fits 1.131 per unit over the pale rows (RMS 1.71 units, 0.73 px);
`measure_guard_joints` fits 1.2616 on the same edge scanned differently (RMS 3.0 px). The build's
1.1667 is neither — it is `(83 − 34) / (55 − 13)`, the diamond's waist over the jaws' outer vertex,
both of which are measured. It lands 3.2% off the tighter fit and 7.5% off the looser one, i.e.
inside the two fits' own 11% disagreement. Recorded rather than chased: moving it means moving one
of the two vertices, and both are pinned by other assertions.

**G4. The crop pins the arm's outer end as a POINT that is not on the ray the arm's length slides
along, so the length is DERIVED as the closest approach and the shortfall belongs to the rake.**
Rewritten 2026-08-13; it used to say "pins it TWICE, one length cannot reach both, and the choice
is DIRECTED". Both halves of that are now sharper.

_The point._ `measurements.json`'s two gold caps give four estimates of the spinner's axis — each
blob's bbox centre and its pixel centroid, |X| = 76.50, 77.75, 86.00, 87.45, mean **81.925** — and
their tops, the topmost GOLD pixel of each blob, sit at Y = −61.5 and −45.4, mean **−53.45**. That
second number is not the arm's end-cap centre and never was: the build's own topmost gold pixel
sits **9.428 units ABOVE** its end-cap centre, where the spinner's shoulder crosses the arm's
end-cap plane, and carrying the crop's reading down by that same construction puts the crop's arm
end at **(81.925, −62.878)**. That offset is a function of `SPINNER_TOP_RADIUS`, so the
2026-08-08 widening moved it — 9.356 → 9.428 — and moved the derived length with it.

_The ray._ `CONNECTOR_ROOT` and `CONNECTOR_ANGLE_DEG` are both locked — the root by the user's
sketch (integration #17), the rake by the shell's own lower taper — so the built end can only sit
at `CONNECTOR_ROOT + L·(cos a, sin a)`. That point is **28.993 units off that ray**, and no length
recovers any of it. **The unreachable part is the rake, not the length**: the crop's own arm end
bears −67.5° from the locked root while the locked rake is −49.3987°, and `measure_guard_joints.py`
already records that the crop's two arms fit rakes 20° apart, so the crop cannot supply a rake to
correct it with.

_The choice._ The length that gets closest is the perpendicular projection, and that is what
ships. Every candidate on the ray, with what it solves and what it misses:

|         `L` | what it solves exactly        | axis \|x\| | gold's top row | miss to (81.925, −62.878) |
| ----------: | ----------------------------- | ---------: | -------------: | ------------------------: |
|       54.97 | the X pin                     |      81.92 |          −8.90 |                    44.554 |
|          72 | nothing — directed 2026-08-12 |      93.01 |         −21.83 |                    33.509 |
| **88.8001** | **the distance itself**       | **103.94** |     **−34.58** |                **28.993** |
|      113.65 | the cap-top pin               |     120.11 |         −53.45 |                    38.187 |

All four rows are re-derived and bracketed by `audit_records.py` on every run, and the three that
are not the build must all score worse than 28.993 or the clause fails.

_What it costs._ The projection buys the two vertical pins and pays on the horizontal one: gold's
topmost row 13.86 → 8.31 source pixels high, the axis 4.73 → **9.40** wide, blockout 0.8348 →
0.8175 (§8). **2026-08-08 then spent the last pin.** Wider was free — the crop's fitted row at the
leather boundary is 21.049 half-width against the sampled 19.0 the shipped 21.4 came from, so
`SPINNER_TOP_RADIUS` = 24.3 is evidence and not the directive. Shorter was not free: the cap's top
is the arm's to set and the arm was already at its projection, so `SPINNER_BOTTOM_Y` −109.7 → −90.8
buys the crop's own LENGTH (56.00 against 56.20) and gives up its POSITION — 19.45 units high at
the top, 19.65 at the bottom. **The caps were never too long. They are too high**, and both
readings are the same 19.5 units. The user's two levers were never two degrees of freedom: the
spinner's length moves only the cap's BOTTOM, so one length still cannot reach a point off its own
ray with the rake locked.

Both pins are visible in one picture rather than argued from a table:
`spec/zoom-guard/compare-arm-end-right-8x.png`, artwork | render at 8× NEAREST over the same
weapon-local window `x = 40…140, y = −110…10`, produced by `measure_guard_joints.py`. The crop's
gold cap emerges from under the leather around Y = −53 with its axis near |x| = 82; the build's
emerges around Y = −34 with its axis at 103.938. The two windows beside it are both framed on the
arm's ROOT, which is the end this change does not move.

**What is NOT fixed by this and must not be mistaken for it:** the arm's ROOT is still one radius
up its own normal from where it sat before 2026-08-11, so the spinner still hangs 10.4 units
higher and 12.1 units further out than the pre-amendment build. Restoring the length restores the
length only. Putting the spinner back on its old seat means moving `CONNECTOR_ROOT` back onto the
jaw's corner, which is the thing integration #17 exists to prevent — it hung the arm's root cap
half in open air below the guard's floor.

**G5. The arm's silhouette starts one apothem up the flank from the jaw's corner, and a notch
1.604 × 0.793 opens there.** The directive pins the root cap's CIRCUMSCRIBED rim to `(34, 13)`;
the front-view silhouette of an 8-gon is carried by its FACES, `16 × (1 − cos(π/8))` = 1.218
inboard of that rim, so the leather's own lower face begins at `(34.925, 13.793)` and the guard's
floor ends 1.604 short of the arm at `Y = 13`. The other reading is to shift by the APOTHEM
(14.782) instead, which would land the visible face exactly on the corner and close the notch, at
the cost of moving the cap's nominal rim to `(35.2, 13.9)` — off the corner the directive names.
**Built to the directive.** The notch is not tolerated, it is asserted: `audit_records.py` holds
the handover to `R(1 − cos(π/8)) / |sin a|` as an equality in both directions, so an arm anywhere
else fails. It is 0.7 × 0.3 of a source pixel at the crop's own scale.

### The rest

**1. The remaining 0.001 of silhouette IoU.** Roughly half is the shell's deliberate lower
convergence (`confidence-report.md` conflict 4) and is not a defect. The rest is the hilt: the
carrier plate shape, unsolvable from a bbox that fits no rotated rectangle, and the per-side
driver elevation asymmetry, which a symmetric model at yaw ≈ 0 cannot reproduce. Resolving
either needs evidence the single view does not contain.

**2. The colour ΔE gate is red** at 57.55 against a 20.0 threshold — see §8, including why the
metric is a whole-render statistic rather than a per-part one.

**2b. The guard block is too dark, and the crop says it is GOLD.** Measured inside a box clear of
both the grip and the jaws (`|x| = 13…22`, `Y = −10…3`), the crop reads (73, 64, 37) on the right
and (102, 100, 77) on the left — warm olive — while the render read (23, 24, 30) with `guardCore`'s
steel there and darker still with the tang's leather. Read as families at 8× rather than as a
single box (`spec/zoom-guard/family-map-8x-grid.png`), the crop's guard centre is a `gold` blob
spanning `|x| ≤ 33`, `Y = −8…24`: the whole block the jaws now occupy is brass in the artwork and
steel in the build. Correction A puts the jaws' own metal back where the tang's leather was, which
moves the render in the right direction and nowhere near far enough. It is a MATERIAL question, not
a geometry one, so it stays here rather than being fixed by moving a part; the crop's left/right
disagreement of 30 levels says how much confidence the reading carries.

**2c. The connector arms are 31% thicker than the crop's, and the edge they plug into is right.**
Correction C's consistency question, measured in `spec/guard-joints.json` and reproduced at 8×
NEAREST in `spec/zoom-guard/`. The two quantities are compared in the same HORIZONTAL cut, which
needs no rake from either side — a good thing, because the crop's two arms fit rakes 20° apart and
it cannot give one:

- the shell's lower slanted edge, right side: the crop fits `halfWidth = 30.62 + 1.2616 · Y` over
  78 rows at an RMS of 3.0 source pixels, against the build's `18.83 + 1.1667 · Y`. **The slope
  agrees to 7.5%**, against 3.2% before integration #15 tied that line to the jaws' outer vertex.
  Worth being exact about what "agrees" is being measured against, because the crop gives TWO
  slopes for the same edge and they are 11% apart: `measure_authority`'s least-squares over the
  pale rows Y = 4…46 reads **1.131 with an RMS of 1.71 units** (0.73 of a source pixel), and
  `measure_guard_joints`' scan reads 1.2616 with an RMS of 3.0 pixels — four times the residual.
  The build's 1.1667 sits between them, 3.2% off the tighter fit and 7.5% off the looser one, and
  it is not fitted to either: it is `(83 − 34) / (55 − 13)`, the diamond's waist over the jaws'
  outer vertex. Both endpoints are measured; the line between them is arithmetic. The intercepts
  differ by 12 units, which is `confidence-report.md` conflict 4's known departure and not new.
- the arm's full section across a row: **32.0 units in the crop against 42.1 in the build**, 32%
  wide. That is `CONNECTOR_RADIUS` being directed at 16, and it is left alone deliberately —
  changing it moves `driverRootRadius()`, `spinnerSeat()`, the driver-clearance gate and the
  silhouette at once, none of which correction C or integration #17 asked for.

The cap's own footprint on the edge takes 49.6% of it in the build; the crop cannot be asked the
same question, because above Y = 22 the driver rods cross the same flank in the same colour
families and the ramp is **unreadable at 8×**. Recorded, not chased.

**3. The dark core is partly hidden BY THE DIAMOND**, which is a different problem from being
hidden by the shell. The core is a film, and the diamond stands 0.2852 T above it by assertion, so
the stone covers the core wherever the two overlap — `Y = 55…97`. The correction spec asks for 85%
of the core to stay readable _and_ for the diamond to be the most raised layer with its whole
outline visible; those cannot both hold below the gem's apex, and the build follows the second,
mechanically.

**This is much smaller than it was**, and the lever turned out not to be the one recorded here.
`CORE_HALF_WIDTH` was named as the way out, and it was the wrong end of the part: widening the base
is what once made the junction read as one black chevron instead of a gem in two jaws. The apex was
the free axis, and it was pinned at 118 only because a mis-scoped colour classifier put the crop's
dark pixels at `Y = 98.8` — see §5. Measured properly the wedge reaches 187, and raising it there
took the core's own footprint from 1189 to 2772 square units at the same base width, so the
majority of the core now sits **above** the diamond where nothing occludes it. Its measured share
proud of the shell went 92.5% → 93.2% at the same time, because a taller triangle has less
antialiased perimeter per unit of area, not more.

**3b. CLOSED, 2026-08-08.** The diamond's tips used to collapse onto `Z = 0`, under every layer on
the blade; seated on `bladeStackTop` they read 99.1% → **100.0%** proud of the dark core.
`SEAT_FLOOR` stays at 0.95 — the headroom is worth keeping, but nothing is spending it.

**4. The pommel's straight cone is ~2 units narrow at `Y ≈ −190`** against the crop, and spends
0.0007 of the blockout gate's margin — see §8. A cone that matched that width would need radius
14.7 where it meets the leather, wider than the grip. That is now doubly binding rather than
merely undesirable: the cone's base ring **is** the column's bottom ring, so widening the cone
means widening the grip, and `tests/ultima-v2-solid.test.mjs` compares the two rings vertex for
vertex. The narrow band is accepted; the shared ring is not negotiable.

**5. The two films' shell-facing faces are still 1.063 apart in linear light, and that residual is
the look-dev rig.** The model's own share is gone — both halves now bake bit-identical vertex
colour, asserted every gate run — but `createUltimaWeaponV2LookDev.ts` lights the scene with a
directional key along the SAME measured vector `(-0.42, 0.62, 0.66)`, and a +Z-facing surface
receives more of it than a −Z-facing one. That is one lamp lighting one object, so it cannot be
mirrored per half without lighting the two sides of one blade with two different rigs. Measured
front (66.79, 36.63, 143.19) against rear (69.10, 38.33, 147.24), down from 1.275 before the
correction: `artifacts/ultima-v2/diag/skin-faces.json`, producer `spec/capture_skin_faces.sh`.

**6. CLOSED 2026-08-09 — `loft` now splits every quad on its SHORTER diagonal, and the residual it
was made of went with it.** It used to cut from `lower[i]` to `upper[i+1]` unconditionally, and
mirroring a ring reverses its index order, so the two halves of a symmetric section were
triangulated along opposite diagonals. On the shell's `Y = 13 → 55` band, measured before the
trapezoid was subdivided (`artifacts/ultima-v2/diag/bracket-trapezoid-1band/parts.json`), the same
seat read **0.2017 inside** the crystal at `(+4.3, 23.5)` and **0.6203 clear of it** at
`(−8.5, 34.0)` — one number on each flank of a blade whose geometry is exactly symmetric.

This item said the fix would "re-triangulate all nineteen meshes, move every `applyFacetSteps`
quantisation and therefore every ΔE, to buy a tenth of a render pixel on a surface nothing can
see", and declined it. What forced it was the stone's crown going to a POINT: at that facet angle
the pair's colour delta failed `MIRROR_COLOUR_TOLERANCE` outright, so the split rule was the only
thing left to change. The price came in as predicted and is small — tier-1 IoU 0.8209 → 0.8208,
max per-part ΔE 57.49 → 57.52 — and the purchase is larger than this item guessed: worst
penetration of any blade layer into the shell 0.083 → **0.020**, the stone's own seat clearance
−0.0826 → **−0.0001**, and all six mirrored faces at exactly **0.000000** instead of five. Front
and rear now measure identically on every probe, which they never did before.

**7. The stone's whole SECTION is directed, and the crop cannot settle any of it.** It was a
girdled prism with a flat crest at 45% of the half-width and a depth band across the middle 75%
of its height; on 2026-08-09 the user directed a 四角錐 — five faces, one apex over the centre —
and all three of those went. Only the crest ratio was ever bracketed against anything
(`MIRROR_COLOUR_TOLERANCE`, item 6); the girdle and the band were arguments about whether the
outline reads, made in prose. The crop's own reading is recorded and followed by none of them:
the half-maximum crossings on iso-Y cuts of the artwork's diamond put the bright top at a median
0.733 of the half-width, p25–p75 = 0.65–0.85, on a stone 5–13 source pixels across carrying a
one-pixel dark outline stroke that drags the crossing to about that value on its own.

**What replaced the prose is a measurement.** The girdle's job — keep the rhombus outline
reading — is now held by nothing at all, and `measure_relief_visibility.py` says it did not need
holding: the stone reads **100.0% proud of the shell and 100.0% proud of the dark core**, both
faces, unchanged from the girdled build. The reason the girdle looked load-bearing is that the
shape it was introduced against ran its rim at `Z = 0`, buried 12.17 units inside the shell; this
one runs its rim ON the stack, so it still wins the depth test everywhere strictly inside its
footprint and the gate erodes the one-pixel rim before scoring. What is genuinely lost is the
STEP — the outline is flush rather than raised — and no instrument on this model scores that.
Resolving it would need a source with more than 13 pixels of stone.

**8. `author_spec.py` now READS `artifacts/ultima-v2/full/parts.json`**, which makes the built
manifest an input to the spec as well as an output of the model. Every component's `dimensions`
and `transform.position` come from it — that is what stopped eight of them drifting — but it means
a geometry change needs two turns of the crank: capture, author, capture, gates. `RELATIONSHIPS.md`
§3 carries the order. The alternative was keeping two hand-typed copies of every box in step,
which is what had already failed.

Everything else that was once listed here — the directed-vs-measured table, the carrier bbox,
the one-sided base flare, the specification's self-contradiction about where the shell stops —
now lives once, in `confidence-report.md`.
