# Image analysis — FF7 Ultima Weapon (v2 rebuild)

Reference: `assets/artwork-sword-crop.webp` (210×434 RGB), isolated from
`references/01-authority-artwork.webp`. Secondary: `references/03-community-colored-model.webp`
(near-orthographic front view, used only where the authority crop is occluded);
`references/02-community-draft.webp` (separation hints only).

All coordinates are **normalized-1000 weapon-local**: `+Y` guard→tip, `-Y` guard→pommel,
`+Z` artwork-facing, origin at the blade socket (midpoint between the shell's root and the
grip's top). Emitted by `spec/measure_authority.py` → `spec/measurements.json`.

---

## Layer 1 — Identification & classification

- **Work type**: a two-handed straight sword — specifically a layered crystal blade with a
  radiating driver array. `primaryType` = weapon/sword, `primaryDomain` = `object`.
- **Broad classification**: bladed prop, hard-surface, bilateral.
- **Provenance**: a PS1-era (1997) flat-shaded game asset rendered against white. Gouraud
  gradients, no texture maps, no bevel loops, hard silhouette edges with 1-px antialiasing.
- **Confidence**: 0.95 on class, 0.9 on era.

## Layer 2 — Overall form & silhouette

- Bounding volume: a thin slab. Overall height 970.7 units (tip `Y=760` → pommel tip
  `Y=−210.7`); maximum lateral extent 309 units (driver endpoints `X=−153.0 … +156.0`);
  depth is unobservable from one view.
- **Artwork tilt**: `18.13°` clockwise from image-vertical, measured from the tip↔pommel-tip
  silhouette diameter. This is a **camera transform, not geometry** — the model is authored
  upright per the component contract.
- Symmetry: bilateral about the `YZ` plane. The crop is *not* mirror-symmetric in image space
  (blade midline is centred at `X≈−1` for `Y>100` but the base flare reaches `−113` on the
  left against `+82` on the right); that residual is a yaw/perspective artifact plus guard
  occlusion, not authored asymmetry — reference 03's near-front view is symmetric.
- Primitive read: extruded profile (blade shell), inset extruded profile (energy insert),
  triangular prism (dark core), low-poly bipyramid (gem), faceted wedges + truncated cones
  (guard), four instanced bars (drivers), tapered prism (grip), cone (pommel).

## Layer 3 — Structure, as counted off the crop

**4 blade parts** and **4 hilt part types**, with the driver array holding exactly **4**
instances — counted from the crop's connected components (Layer 7), and the count the supplied
component contract independently fixes.

The component *names* this layer originally proposed are gone: they were authored before the
build and five of them (`bladeSocketCollar`, `carrier L/R`, `endCap L/R`, `leatherTGrip`,
`metalSpinnerPommel`) were never made. The contract that was built is in `CURRENT-MODEL.md` §3
and is asserted by `check_centerline.py`.

## Layer 4 — Spatial relationships

The one thing the crop actually shows about depth is the overlap order, camera → back:

```
gem → dark core → purple insert → outer shell → the gold at the guard
```

**In the build this is produced by real front-to-back relief, not by draw order** — each inner
crystal stands proud of the one under it, equally front and rear (`CURRENT-MODEL.md` §5). The
crop cannot distinguish the two readings; the correction specification chose relief.

## Layer 5 — Materials & surface

What is observable: flat value bands with linear ramps, no specular hot-spots other than one thin
bright edge per driver, and no surface relief anywhere. Nine material families, separable by
hue/value — the measured census is Layer 6.

What is **not** observable: any PBR scalar. This layer once carried a metalness/roughness table
inferred from the source era's lighting model; the roughness guesses were roughly right and the
metalness guesses (~0.8 for steel, ~0.9 for gold) were the opposite of what the build needs — in
a near-ambient rig over a featureless environment they render near-black. See `CURRENT-MODEL.md`
§6 rule 2 and `spec/pbr-evidence/README.md`, where an automated extraction made the same class of
error in the other direction and had its scalars rejected.

## Layer 6 — Colour & finish (measured HSV census)

| Region | Sampled stops | Share of in-mask pixels |
|---|---|---|
| shell | `#E6E7F2` (highlight) → `#CDCFD8` (body) → `#B5B6BF` (shadow) | 52.6% |
| insert | `#160D59` (apex) → `#2F238C` → `#5729A5` → `#7F3CF2` (base glow) | 22.5% |
| gem | `#722832` → `#C0184D`-family bright face | 1.2% |
| dark core | `#3F0F16` → `#591620` | 1.0% |
| drivers | `#59161F` (shadow) → `#721C28` (body) → bright edge | 1.6% |
| gold | `#726E56` → `#8C8769` | 2.9% |
| charcoal steel | `#212026` → `#37363F` → `#3C3C3F` | 4.4% |
| grip | `#0C0C0C` → `#262424` | 1.3% |

Finish: matte-to-satin throughout. Every gradient is a **linear vertical ramp**, consistent
with per-vertex colour interpolation rather than a texture. The insert's ramp runs dark at the
apex to bright at the base — the reverse of a lit-from-above surface, so it reads as emissive
energy, not shading.

## Layer 7 — Identity-defining features (measured)

1. **Exactly four drivers, two per side, in mirrored pairs.** Four connected red components
   outside `|X|>60`. PCA axes:

   | id | root | end | elevation | length | half-width |
   |---|---|---|---:|---:|---:|
   | `left_upper` | `(−69.8, 4.6)` | `(−125.2, 61.9)` | 45.9° | 79.7 | 10.4 |
   | `left_lower` | `(−78.8, −15.9)` | `(−153.0, 25.4)` | 29.1° | 84.9 | 10.9 |
   | `right_upper` | `(66.8, −6.4)` | `(127.4, 45.7)` | 40.7° | 79.9 | 11.3 |
   | `right_lower` | `(76.4, −28.6)` | `(156.0, 3.0)` | 21.6° | 85.7 | 11.0 |

   The 5–7° left/right elevation gap is a projection artifact of the yaw; authored elevation
   is the pair mean: **upper 43.3°, lower 25.4°**, length 80 / 85, half-width 11.

2. **The outer shell is the sharpened layer.** Its width profile has one shoulder and one long
   straight taper: half-width 95 at `Y=62`, falling near-linearly (slope −0.059/unit) to 54 at
   `Y=575`, then breaking to −0.29/unit into the point at `Y=760`. Two silhouette segments,
   one knee — a PS1 profile, not a curve.

3. **The insert never reaches the tip and never touches the shell's edges.** Insert apex
   `Y=480.1` (63% of blade length); maximum width 86.6 at `Y=50` against the shell's 194 —
   the shell clears it by ≥54 units per side at every height.

4. **The insert has its own knee, in the opposite sense.** Slow taper (−0.046/unit) from the
   base to `Y≈380` (half-width 28), then −0.28/unit to the apex — the "small triangular point
   over a long trapezoid" silhouette.

5. **The root gem is an elongated rhombus, not a flat arrow.** Bright-red pixels span
   `Y=12.9…97.3` with maximum width 32.6 at `Y≈55`: a 2.5:1 diamond whose waist sits at the top
   of the guard's own dark mass. **That waist is the single most load-bearing measurement in the
   hilt**, because five other features are pinned to it rather than measured independently: the
   shell's lower taper starts there, both films' lower edge is there, and it is each jaw's apex
   vertex — `CLAMP_OUTLINE[0]` *is* `(GEM_HALF_WIDTH, GEM_WAIST_Y)`. `CURRENT-MODEL.md` §4 draws
   the line; `audit_records.py` and `check_centerline.py` both hold the four features to it.

6. **The guard is compact and steeply angled.** Carriers run from `(±20, +40)` out and down to
   `(±88, −60)` — roughly −53° from horizontal — each ending in a gold truncated cone spanning
   `Y=−45…−117`, `|X|=56…106`.

7. **The gold collar is a shallow tent, not a crossguard bar.** `X=−32.9…24.8`,
   `Y=−7.8…23.9`: a small up-pointing wedge around the blade root, split by a vertical ridge.

8. **The grip is narrow and the sword reads as a T only in combination.** Grip
   `X=−13.5…6.5` (width 20), `Y=−180.3…−4.9`. No separate crossbar exists.

9. **The pommel is a small downward cone.** Gold, `Y=−209.3…−179.6`, half-width ≈10 —
   30 units of extension, narrower than the grip.

## Layer 8 — Uncertainty & single-image limits

What the single view cannot settle. The **Handling** column is deliberately a pointer, not a
value: it once carried the intake-time authored numbers (core apex `Y=150`, shell half-width 95
at `Y=62`, driver roots on a `Y=0` circle at `|X|=52`) and every one of them was retired by a
later pass while this table went on quoting them.

| # | Item | Class | Handled where |
|---|---|---|---|
| U1 | All depth (`Z`). One view only. | hidden | `CURRENT-MODEL.md` §5 — the relief ladder, all of it directed, confidence 0.35 |
| U2 | `darkCoreTriangle` extent. **Was** filed as occluded on the strength of a `Y=98.8` apex; that is where the RED colour family stops, not where the core does — above the gem the wedge is near-black on violet and lands in the insert/grip families. Read as a darkening of the insert it is measurable to its tip. | **resolved** | `CORE_*` in the factory, apex measured at `Y=187`, confidence 0.75. Only the base half-width stays directed: below the gem's apex the gem's own rim-dark shading shares the same dark run. `spec/measure_core_apex.py`, `spec/zoom-relief/core-apex-{8,16}x-grid.png` |
| U3 | Blade root width. The shell's base is hidden by the guard's dark mass; the left flare reaches `−113` while the right is occluded at `+82`. | occluded | `SHELL_STATIONS`. The taper between `Y = 55` and `Y = 13` is directed (`confidence-report.md` conflict 4) but **its two endpoints are not, and neither is its lowest ROW**: integration #15 makes the base row `CLAMP_OUTLINE`'s own outer lower vertex, so the shell's lowest edge is the two jaws' floor edges laid end to end rather than a number of its own |
| U4 | Driver roots. All four emerge from behind the arms and are invisible in the crop. | occluded | `driverRootRadius()` — derived in closed form from the connector's inradius, not authored. `audit_records.py` recomputes it every run, and since 2026-08-10 `author_spec.py` does too rather than carrying a hand-typed copy, which had gone stale by 9 units |
| U5 | Grip length vs the master prompt's contract. Measured 175 (+30 pommel) against the contract's 205 (+35). | conflict | **Artwork wins.** Reference 03's independent ratio (0.274) matches the measurement (0.284), not the contract (0.316) |
| U6 | Drivers' `Z` fan. The left/right elevation asymmetry could also be a forward/back fan. | uncertain | Authored coplanar in `XY` (the conservative reading), mirrored pairs as the contract requires. This is one of the two residuals in the remaining silhouette IoU — a symmetric model at yaw ≈ 0 cannot reproduce a per-side elevation difference, and the single view cannot say whether there is one |
| U7 | Real PBR channels. The source is vertex-lit with no maps. | undetermined | No extracted scalar is used; see `spec/pbr-evidence/README.md` |
| U8 | The guard's UNDERSIDE, between the grip column and each arm. The crop's dark mass runs unbroken across the full width down to `Y = −8`; the user's sketch draws that region open on both sides. | conflict | **Sketch wins**, because the crop is a projected 3/4 view in which a dark pixel cannot be assigned to a part. Built open, and the opening is measured rather than waved at — `audit_records.py` prints **46.803 units at `Y = −13`** every run, recorded and not thresholded, so re-filling it cannot happen quietly. It was 25.730 until the arms came up to hang off the jaws' corners on 2026-08-11. `CURRENT-MODEL.md` §11 G1 |
| U9 | The stone's cap flatness. The crop's half-maximum crossings put the bright top at a median 0.733 of the half-width, against a built cap that closes on a POINT. | unreliable | The stone is 5–13 source pixels across and carries a one-pixel dark outline stroke, which drags the crossing to about that value by itself. Recorded, not followed — it read the same way against the flat crest at 0.45 that the point replaced, which was itself bracketed against the mirrored-pair colour tolerance rather than measured. `CURRENT-MODEL.md` §11 item 7 |
