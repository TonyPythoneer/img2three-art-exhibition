# Image Analysis — Cloud's Ultima Weapon (FFVII 1997)

Reference: `../reference-ultima-weapon.png` — 146×292 PNG, PS1-era flat-shaded game asset
render on a uniform white background. Probe warns: low resolution; small detail unreliable.
Analysis run: independent Fable 5 reconstruction (second run of the same brief; no reuse of
the first run's spec or measurements).

Viewing aids: 4× lanczos upscale, three band crops (top/mid/bottom), guard zoom (146×70 → 5×).
All coordinates below are **original image pixels** (x right, y down, origin top-left).
Weapon local space per brief: +Y handle→tip, −Y pommel, +X weapon right, +Z visible front.

## Layer 1 — Identification & classification

- **Observed:** a double-edged, leaf-bladed one-handed/hand-and-a-half sword rendered in
  deliberate low-polygon flat shading: translucent pale blade, saturated violet internal
  volume, radiating rod cluster at the guard, faceted dark grip.
- **Work type:** fantasy sword (game asset). Broad class: bladed weapon, compound
  hard-surface object. `primaryDomain: object`. Confidence 0.97 (subject named by the brief;
  the image is consistent with the 1997 FFVII Ultima Weapon menu/battle render).
- **Inference (marked):** the render is a 3D model screenshot, not pixel art — facet
  shading bands and perspective foreshortening are visible.

## Layer 2 — Overall form & silhouette

- Bounding volume: one long shallow extruded-profile volume (the blade) ≈ 3.5–4× the length
  of a compact radial guard cluster, plus a thin cylinder (grip) continuing off-frame.
- Blade axis is tilted ≈ 18° from image vertical, tip toward upper-left. Tip is cropped by
  the top/left frame edge; grip is cropped by the bottom frame edge. Axis angle must be
  re-measured deterministically at blockout before any silhouette gate (visual estimate only).
- Silhouette: leaf/lanceolate blade. In image space the right edge appears to bow out more
  than the left near the base (x≈100–140, y≈160–230). **Observation vs inference:** the 2D
  asymmetry is observed; whether the 3D profile is asymmetric or the blade plane is rolled
  slightly toward the camera is NOT decidable from one view. Treat profile symmetry as a
  measurement question at blockout (fit both edges against the measured axis), not an axiom.
- Symmetry elsewhere: guard reads bilaterally symmetric about the blade axis at macro level;
  rod directions break naive left/right mirroring (Layer 4).
- Shape language: geometric, planar-faceted throughout. No organic curvature anywhere.

## Layer 3 — Macro → meso → micro decomposition

Macro (independent assemblies):
1. Blade assembly — outer translucent shell + internal violet core + frontal magenta spine.
2. Guard assembly — central hub, shoulder blocks, gold parts, olive blocks, emitter rods.
3. Handle assembly — neck, grip, (pommel: off-frame).

Meso:
- Outer shell: front face, back face (hidden), left long edge band, right long edge band,
  tip region (cropped), base taper into guard.
- Violet core: front plane, right bevel plane (distinct value band), upper taper,
  two lower legs forming an inverted-V notch (apex ≈ (72, 172)); legs end ≈ y 205–212.
- Magenta spine: narrow wedge inside the notch, y≈172–215: dark burgundy upper spike,
  brighter red-magenta lower diamond; sits in FRONT of the core (+Z) — it overlaps the
  core's notch edges.
- Guard: central olive-gold hub/chevron directly under the spine (≈ (70–85, 205–235));
  left and right gunmetal shoulder prisms angled outward-downward; a small olive-gold
  faceted block at each shoulder's outer-lower tip (left ≈ (28–52, 245–275), right ≈
  (100–130, 235–280)); emitter rods (Layer 4/7).
- Handle: dark faceted rod from hub toward lower-right, ≈8–10 px wide, two visible planes
  (lit grey-black front-left, near-black right); cropped at y=292.

Micro (feature groups):
- Facet shading bands on shell (2–3 value steps along the left edge and base).
- Core front/bevel two-plane split with a bright violet rim along the lower-right edge.
- Rod end caps read darker than rod bodies.
- Gold blocks show two-tone facets (khaki-gold lit planes, dark olive shadow planes).

## Layer 4 — Spatial relationships (scene-graph)

- `<outerShell, encloses, violetCore>` — core visible THROUGH the shell: contact type embed.
- `<violetCore, notch-straddles, magentaSpine>` — spine embedded in the notch, offset +Z.
- `<bladeAssembly, socketed-into, guardHub>` — shell base narrows and butts into hub.
- `<gunmetalShoulders, flush-with, guardHub>` — overlap contact, one per lateral side.
- `<oliveBlocks, capped-onto, shoulder outer tips>` — butt/overlap at the outward-lower end.
- `<emitterRods, radiate-from, guard center region>` — visible rods: 3 on the weapon's left
  (image left, pointing outward and pommel-ward), 2–3 on the weapon's right (pointing
  outward and tip-ward, partially occluded near the shoulder). Extended axes appear to
  converge BELOW the guard hub on the blade axis, not at the hub center — the radiation
  center sits pommel-ward of the hub. Exact convergence point is a blockout measurement.
- `<handle, continues, hub along −Y>` — butt joint under the hub, slightly right of the
  image's blade-axis line (consistent with the 18° tilt).
- No part floats: every visible block shares an edge or overlap with the hub cluster.

## Layer 5 — Materials & surface (PBR)

One claim per surface; albedo estimates from flat-shaded bands (no photographic lighting to
remove, but the render bakes its own directional shading — treat band values as shaded, not
pure albedo):

| Surface | Albedo (est.) | Metalness | Roughness | Translucency | Notes |
|---|---|---|---|---|---|
| Outer shell | near-white, cool lavender cast (#EDEDF6 lit → #C9C9DE edge bands) | 0 | 0.3–0.45 | semi-translucent, milky | core stays readable through it; no glass-like caustic/refraction cues |
| Violet core upper | dark navy-violet (#2B2373) | 0 | 0.35 | opaque | slight emissive read (saturation holds in shadow) |
| Violet core lower/rim | vivid violet (#6E52E8, rim #8A6CF8) | 0 | 0.35 | opaque | brightest at lower legs/rim |
| Magenta spine upper | deep burgundy (#571031) | 0 | 0.3 | opaque | |
| Magenta spine lower | red-magenta (#B52343) | 0 | 0.3 | opaque | weak gloss |
| Emitter rods | crimson (#8E1827), near-black top faces | 0.1 | 0.35 | opaque | lacquer-like two-tone facets, dark end caps |
| Gunmetal shoulders | dark blue-grey (#3B3B47) | 0.6 | 0.5 | opaque | restrained highlight |
| Gold/olive blocks | khaki-gold (#8D8354 lit, #4B4732 shadow) | 0.7 | 0.55 | opaque | aged, not jewellery gold |
| Grip | near-black (#16161B, lit face #2E2E35) | 0.1 | 0.7 | opaque | |

- **Avoid-trap noted:** the white background bleeds into the shell edge via anti-aliasing;
  edge pixels are not albedo evidence.

## Layer 6 — Color & finish

- Shell: hue ~250° barely saturated, very high value; finish satin; gradient = facet bands,
  not a smooth ramp.
- Core: ordered gradient stops along −Y (tip-ward dark → pommel-ward bright):
  0.0 #2B2373 → 0.55 #4A38B5 → 1.0 #6E52E8, plus rim accent #8A6CF8 on the lower-right
  bevel edge. Banded per-facet, not continuous.
- Spine: two stops, #571031 (upper spike) → #B52343 (lower diamond), hard boundary.
- Rods: body #8E1827 satin with clearcoat-like facet highlight; top faces near-black
  (shadow side), ends darker still.
- Metals: gunmetal cool dark grey; gold desaturated olive-leaning; both matte-satin.
- Overall finish style: PS1 flat-shaded facets — value steps at facet boundaries, zero
  microtexture, zero decals.

## Layer 7 — Identity-defining features

1. Milky translucent shell with the violet core visibly floating inside — THE signature.
2. Inverted-V notch of the core's lower legs around the magenta spine.
3. Core's two-plane (front + right bevel) violet gradient with bright rim.
4. Radiating crimson rod fan at the guard (reads as 6-rod array, not a crossguard bar).
5. Two-tone olive-gold faceted blocks capping the gunmetal shoulders.
6. Everything planar-faceted: silhouette polygonal, no smooth curves.
7. NO engravings, screws, runes, seams, or decals anywhere — absence is identity here.

Each of 1–5 must land in `detailInventory` and become a `featureReviewTarget`; 6–7 are
look-dev constraints (facet shading, restrained materials).

## Layer 8 — Uncertainty & single-image limits

- **Cropped:** blade tip (top/left frame edge); grip lower half + pommel (bottom edge).
  Tip shape and pommel are undetermined → build per brief (pointed tip; pommel collar +
  gold tip) and mark `inferred`, confidence ≤0.5.
- **Hidden:** entire back face (assume front/back mirror, `mirrored`); blade thickness
  (thin, exact depth undetermined); guard rear; hub's far side.
- **Occluded:** rod roots behind shoulders; possible additional right-side rod; how many
  rods truly exist — brief fixes 3+3 with hidden ones marked inferred, confidence ~0.45.
- **Uncertain:** 2D right-edge bow = profile asymmetry vs blade-plane roll (Layer 2);
  radiation center of rods (below hub, exact y unknown); whether shell tint is lavender or
  neutral white shifted by the render's ambient.
- **Perspective:** mild foreshortening; the camera is close to frontal three-quarter with
  slight right offset — solve at blockout for the reference-matched view.
- All of the above land in `unknownsToResolveBeforeImplementation`; none justify
  `request-input` yet (the brief already dictates the inference policy for every one).

## Suitability verdict (validation rubric)

**Verdict: conditional — proceed.**

- Pass criteria met: one obvious target; object fills the frame; strong silhouette; all
  major materials visible; hidden side reasonably inferable (bilateral + front/back
  mirroring); target is exactly the "approximated with procedural primitives" case.
- Conditional criteria triggered: single view only; blade tip and grip/pommel cropped by
  the frame; fine detail limited by 146×292 resolution.
- Reject criteria NOT triggered: the cropped regions (tip, pommel) are covered by an
  explicit inference policy in the brief (pointed low-poly tip; pommel collar + gold tip,
  marked inferred) — the identity-defining mid-blade/guard region is fully visible. The
  translucent shell is milky flat-shaded translucency, not glass caustics; a direct
  transmission/opacity path exists.
- Conditions attached: tip and pommel geometry carry confidence ≤0.5 and `inferred`
  evidence type; back face carries `mirrored`; hidden rods confidence ~0.45; no claim of
  dimensional accuracy beyond the reference's pixel measurement error (±2 px at 146×292).
