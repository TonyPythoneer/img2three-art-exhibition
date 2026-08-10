# Confidence report — FF7 Ultima Weapon v2

What the artwork proves, what it merely suggests, what it never shows.

**Three correction passes applied**, each superseding the last where they conflict: pass 2
deleted `centralGripSocket` and the four `driverSocket` meshes and made the clamps the blade
socket; pass 3 turned the three inner crystals into a front/rear-symmetric relief ladder and
contracted the shell into the clamps. **The supplied marked screenshots were never attached to
any of the three requests**, so all three were executed from their written specifications alone;
anything visible in those screenshots but not written down was not addressed.

Current measured results live in `CURRENT-MODEL.md` §8, read from `spec/silhouette-report.json`
and `artifacts/ultima-v2/gate/*.json`. They are not repeated here — this file had carried a
second copy for two correction passes and it was wrong in both.

## Confidence by component

Anything below 0.70 is **directed** — supplied by a written correction specification because the
crop cannot answer it — not measured. A supplied component contract legitimately outranks a
210×434 crop on a question the crop cannot resolve; it is recorded so nobody later mistakes it
for a measurement.

**This table is now asserted.** `spec/audit_records.py` reads every backticked component name and
the number beside it out of this table and compares it to `object-sculpt-spec.json`. Three rows
had drifted before that clause existed — the jaws read 0.55 here against 0.60 in the spec, the
spinner ends 0.70 against 0.65, the driver array 0.85 against 0.90 — and none of them could be
caught by the retired-figure net, which matches whole strings.

| Component | Confidence | Basis |
|---|---:|---|
| `outerCrystalShell` | 0.88 | Width profile measured at 30 stations; agrees with reference 03's independent front view to within 3 units from `Y=110` up. Everything below `Y=42` is directed — see conflict 4 — **except its base ROW, which is derived**: integration #15 makes it `CLAMP_OUTLINE`'s own outer lower vertex, so the shell's lowest edge is not a number of its own. **Its material is SOLID by user direction against a brief that asks for translucent — see conflict 7**; the shape rating is unaffected. |
| `purpleEnergyInsert{Front,Rear}` | 0.90 | Apex height, both taper slopes and the knee at `Y=380` all measured directly. Apex at 63% of blade length; reference 03 independently gives 63.5%. Its base is the authority line and its half-width there is its own measured taper evaluated at that height, not a second number. |
| `rootDiamondGem{Front,Rear}` | 0.80 | Bright-red pixels give `Y=12.9…97.3` and a 32.6 waist. Depth is inferred, and the 四角錐 section — five faces, apex over the centre, no girdle and no depth band — is directed outright by the user (2026-08-09). The crop cannot arbitrate: its half-maximum crossings read flatter than the pyramid AND flatter than the flat crest it replaces, on a stone 5–13 source pixels across carrying a one-pixel outline stroke. |
| `darkCoreTriangle{Front,Rear}` | 0.75 | **Apex measured, base directed.** It was filed at 0.45 on the reading that the crop occludes everything above `Y=98.8`; that figure is where `measure_authority`'s RED colour family stops, and the core is red-tinted only where it flanks the gem. Above the gem it is a near-black wedge on violet, and read as a darkening of the insert its own edges fit a straight line over 86 rows at an RMS of 0.26 source pixels, reaching zero width at `Y=186.9` (`spec/measure_core_apex.py`). Below the gem's apex the gem's rim-dark shading shares the same dark run, so the base half-width stays directed — though the same fit extrapolated to the waist reads 18.45 against the directed 21, inside one source pixel. |
| `crystalClamp{L,R}` | 0.60 | **Up from 0.55, and the reason is that the outline stopped being free.** The artwork still shows no clamp. But two of the jaw's three vertices ARE the measured stone's own — the waist `(17, 55)` and the culet `(0, 13)` — and the third's HEIGHT is the culet's, which is what makes the floor one horizontal line. Only the outer `34` is directed, and the user's sketch (`references/04-user-sketch-guard.png`) is the authority for the triangle. The retired four-point outline had a knee and a vertical inner face, neither of which anything could be derived from. |
| `leatherConnector{L,R}` | 0.65 | Root, rake and LENGTH are all *derived* — the root cap's lower rim IS the jaws' outer vertex, the rake IS the shell's lower taper as an angle, and since 2026-08-13 the length is the perpendicular projection of the crop's own arm-end point (81.925, −62.878) onto the ray those two leave free, 88.8001. It replaces a value directed at 72 and it solves neither of the crop's two pins: the point is 28.993 units off the ray at every length, which is the rake's shortfall and not the length's. The cylindrical section, the radius and the leather *reading* stay directed, and the radius is 32% wider than the crop's. See conflict 1, `CURRENT-MODEL.md` §11 item 2c, and §11 G4 for every candidate length with its own miss. |
| `spinnerEnd{L,R}` | 0.70 | **Nothing here is inferred from reference 03 any more.** Its direction is measured — de-rotated upright, each arm-end→cap-centroid vector and each cap's PCA axis read within ~12° of straight down and nothing reads the arms' −50° — and both RADII are the crop's own per-row half-widths, converted through the lathe's 0.866 front-view factor — the wide one re-read on 2026-08-08 off the fit at the leather boundary rather than off the widest sampled row, 21.4 → 24.3. Its seat is derived in closed form from the arm's inradius, and since 2026-08-13 the whole profile is derived from that seat: a straight frustum, widest at the top, because `measure_spinner_taper.py` reads both caps as straight-sided to within one source pixel and neither widens downward by as much as one. The six-sided lathe is directed, and since 2026-08-08 so is the cap's BOTTOM — `SPINNER_BOTTOM_Y` −90.8, which spends the crop's measured −109.65 to buy its measured LENGTH: 56.00 built against 56.2, sitting 19.5 units high at both ends because the crop's leather stops 19 units lower than this build's. See conflict 8. |
| `driverArray` | 0.85 | Four PCA axes measured; endpoints and the common radiation centre are direct measurements. Elevations are pair means. The circular cross-section is directed — the crop cannot resolve a 22-unit rod's section. |
| `driver{L,R}{Upper,Lower}` | 0.82 | The four instances, one shared unit geometry. Below the array's own rating because each rod's ROOT is derived from the connector rather than measured: the crop cannot see it, since the root is buried inside the arm. |
| `leatherGrip` | 0.85 | Shaft length and width measured; constant shaft width is directed, and correction A makes it the whole part — one column, no tang, no collar. The crop's guard is one undifferentiated dark mass with the grip's column running into it and no seam anywhere at 8× (`spec/zoom-guard/`), so it supports *a* continuous solid there but cannot say which part it belongs to; the build assigns that solid to the two jaws, whose lower edge is the gem's culet plane at `+13`; the crop's dark mass runs on down to `−8` and the user's sketch draws that region OPEN, so the sketch is followed and the departure is recorded in the guess list. The column's top is not derived from the culet any more — integration #16 makes it the jaws' floor, face to face. |
| `pointedMetalPommel` | 0.80 | Bbox measured; the profile is *directed* to a straight cone, apex at the measured tip. Its base ring is **derived**, not directed: `POMMEL_RADIUS` is `GRIP_HALF_WIDTH` and `POMMEL_SIDES` is the column's 8, so the two rings are identical vertex for vertex and the junction cannot open. The spinning-top lathe it replaced, and the gold collar above it, are both deleted: at 16x the crop shows uniform leather to -180.3 and gold from the next row. |
| All depth (`Z`) | **0.35** | One view. Nothing about the third axis is observed — including the whole relief ladder, whose ratios are directed and whose absolute depths are therefore unverifiable against the crop. |

## Unresolved conflicts

**1. The measured `steel` bbox is not a plate.** The carrier's classified region spans
`X 7.6…85.7`, `Y −71.2…42.6`. Solving `L·cosθ + W·sinθ = 78` and `L·sinθ + W·cosθ = 114`
simultaneously at the −50° rake gives `W = −78`: a negative width, i.e. **no rotated rectangle
of any positive size fits that bbox at that angle**. The classifier is merging the carrier with
the dark shadow side of the rods behind it. The carrier is therefore sized to the measured `X`
range and raked per reference 03, and this is recorded rather than fitted to a box that cannot
be one plate.

**2. The blade's base flare is one-sided.** The crop reads half-width 96 on the left against 81
on the right at `Y≈50–75`. Reference 03's near-orthographic front view is monotonic and peaks
at 83. Following the crop literally would have widened the blade by 15% on both sides.

**3. Grip length contradicts the master prompt.** The brief's starting contract is grip 205 +
pommel 35 against a 760 blade (ratio 0.316). The artwork measures 175 + 30 (0.269), and
reference 03 independently gives 0.274. Two sources against one; the artwork wins, and the
render's pommel-tip error of 0.78% confirms it.

**4. The shell's lower convergence is spent silhouette.** `shellWidthProfile` reads a
near-constant right-hand edge — 81.7 at y=25, 81.5 at y=50, 80.7 at y=75 — and collapses to a
37.7-wide sliver at y=0 where the hilt occludes it. So the crop constrains the shell down to
about y=25 and no further, and the neck itself is unconstrained. The one measured value actually
overridden is the ~82 half-width at `Y=42`, built at 72, which is what buys the full
1.00-driver-diameter clearance the third correction spec prefers. Cost: silhouette IoU
0.8937 → 0.8875 and the blockout gate 0.8522 → 0.8505, still over its 0.85 bar. This is the only
place in the build where a measurement was knowingly given up for a directed relationship.

**5. An acceptance row was reported as passing when it was not.** "White crystal continues below
the clamp bases" was first recorded as passing with the evidence "the clamps' lowest point is
Y = 4". It was not: the clamp outline had been narrowed from `(44,4)` to `(34,6)` after that
reasoning was written, leaving 2 units of pale crystal below the jaws — an actual rejection
condition. It was caught by reading the built `parts.json` instead of the report.
`spec/check_centerline.py` now asserts `shell.minY ≥ clamp.minY`, so the same class of error
cannot pass a review again. **This is why the acceptance tables that used to live at the bottom
of this file are gone**: a hand-written table of "did we satisfy the spec" is exactly what let
that through. The per-pass record is `spec/object-sculpt-spec.json`'s `reviewHistory`; the
rejection conditions themselves are asserted in `check_centerline.py`, `audit_records.py` and
`front_rear_overlay.py`.

**6. The specification contradicts itself about where the shell stops.** Correction pass 2 §5
says both "it must stop at the upper boundary of the clamps" and "it must not extend below the
bottom edge of either triangular clamp". Those are different lines: the clamps span `Y = 6…55`.
The first reading would cut the blade off at the gem's waist and leave the diamond and both jaws
hanging below it, contradicting the artwork. The build follows the second, which is also what
§15's rejection condition tests. The shell now stops at `Y = 13`, the height where the two jaws
meet.

**7. `outerCrystalShell` is SOLID and the brief asks for "pale translucent".** Directed by the
user on 2026-08-07. The user wins, and this is the record of what that costs and what it does
not.

*What the brief says.* `brief/01-english-master-prompt.md` describes the shell as "Pale
**translucent** gradient with faceted light/shadow zones". `brief/` is supplied verbatim and is
not edited.

*What the crop says.* Nothing that contradicts a solid shell, and the test is arithmetic rather
than opinion: a pale layer of opacity `a` drawn over something floors every channel under it at
`a × 216`. Measured by `spec/zoom_shell_translucency.py`, with the pictures in
`spec/zoom-relief/translucency-*-8x.png` at 8× NEAREST —

- the violet field reaches **(0, 0, 45)**, with 0 in both R and G. Even `a = 0.15` would floor
  those channels at 32, so nothing pale is composited over the insert;
- the boundary between the violet field and the pale shell is **2 px at the median, 4 px at p90**
  over 358 scanline crossings — one source pixel is 2.40 normalized units, so it is a hard step,
  not a layer seen through another;
- at the guard, the arm roots and the blade's outer edge there is no place where a dark part
  shows through the crystal or where the crystal darkens over one.

So "translucent" in the brief is a description of the material's *look* — milky, high-value,
gradient — and not of any compositing the artwork performs. That look survives: the shell is
still the palest, highest-value surface in the frame, still carries a Y gradient and still
carries facet bands.

*What it costs.* Only the numbers that the shell's own pixel values feed. Silhouette IoU
0.8895 → 0.8893 and front/rear IoU 0.9979 → 0.9964, both because `compare_render.mask_from` keys
on `min(rgb) < 244` and the solid shell is 5 levels brighter; per-part ΔE 55.5 → 55.42; tier-1
blockout IoU 0.8508 → 0.8524 and the other tier-1 passes 0.8538 → 0.8555, both improvements — and
both have moved on since — to 0.8553 and 0.8573 with the guard integrations and the `loft` end-cap
repair, then down to 0.8478 and 0.8497 when the 2026-08-11 amendment to #17 raised both arms onto
the jaws' corners, then down again to 0.8367 and 0.8374 when the arms were directed longer on
2026-08-12, to 0.8348 and 0.8364 on 2026-08-13 when the spinner caps became frusta widest at the
top, and to **0.8175 and 0.8171** later that day when the arms were directed longer again and the
caps shortened with them, which is where they are RED against the 0.85 floor. The
stone's share proud of the shell reads 100.0% where it read 93.6%, and that is an instrument
change, not a geometry change — see §8 of `CURRENT-MODEL.md`.

*What it does not cost.* No geometry moved: 19 parts, every centreline, mirror, lift, flush and
socket assertion unchanged. (The triangle count was 1092 that day and is 984 now — the stone
became a 四角錐 on 2026-08-09 and each half went 126 → 72.)

*What is still short.* The shell's facet SPAN. The artwork's pale census spans 48 luminance
levels p5–p95 and the build spans 19 (`artifacts/ultima-v2/gate/shell-value.json`) — better than
the translucent build's 13, and not
because of the palette. The artwork shows three value bands across the blade; the model's
8-point ridged section presents essentially one to a front camera, because every front-facing
face scores the same step of `applyFacetSteps`' three-way quantiser. Closing it means re-cutting
the section's ridge shoulder, which is geometry, and it is recorded here rather than attempted.

**8. The spinner cap is 35% longer than the crop's, and the rake is why.** Recorded here because
three directives in a row moved it and none of them names it.

*What the crop measures.* `spec/spinner-taper.json`: each gold cap runs from the row where the
leather stops down to a blunt bottom — 56.2 units on the two-cap mean — and over that length the
flank is straight to within one source pixel (linear RMS 0.57 px, bowing out from its own chord by
0.77 px, which is not a curve this crop can resolve) and never widens downward by as much as one
pixel. Fitted, `halfWidth = 21.049 − 0.2135 × drop`.

*What the build has to do with it.* The cap's TOP is not at an absolute height in the weapon; it
is wherever the leather stops, and the arm decides that. The crop's gold appears at Y = −53.45 and
the build's at −34.00 — 19.45 units, 8.31 source pixels, high — and no length of arm on the locked
ray closes that (§11 G4). What the build CAN choose is where the cap ends.

*So the conflict changed shape on 2026-08-08, and this is the entry for it.* The user directed the
caps shorter a second time. The arm was already at its projection, so the only lever left was the
bottom pin, and it was spent: `SPINNER_BOTTOM_Y` −109.7 → −90.8. The exposed cap is now **56.00**
units against the crop's 56.20, where it was 76.0 — and the cap's bottom, which used to be the one
figure on this assembly the build hit to 0.15 of a pixel, now reads −90.00 against −109.65, 8.39
pixels high. **The length is the crop's and the position is not.** Both misses are the same 19.5
units, which is the point: the caps were never long, they were high.

*The wide end went the other way, and it went on evidence rather than on the directive.* 21.4 came
from the widest SAMPLED row, and `spec/spinner-taper.json` marks the rows above it
`boundaryRampRows` — the crop's slanted leather boundary still clips them, so they read narrow and
hold the sampled maximum down. The mean fit over 53 clean rows reads 21.049 half-width at drop 0,
which is the row the shoulder actually is: radius 24.3. The narrow end stays at the crop's 8.1.

*What gives is the CONE ANGLE, and it changed sign.* The build's flank now runs 0.2547 of
half-width per unit of drop against the crop's fitted 0.2135 — 19% STEEPER, where before the
shortening it was 29% shallower. The bottom is what absorbs it: on the crop's own line the cap
would end at 9.05 half-width and this one ends at 7.01, a gap of 2.03 units, **0.87 of a source
pixel**. Under one pixel is not worth giving up a measured radius for, so 8.1 stands.

*Which of the two to preserve when the length changes is a real choice and it was made once,
here.* Keeping the crop's ANGLE instead of its radii would need either a 29.5 top radius or a
bottom radius of 2.9 at the build's length — giving up a measured end to keep a rate. Both ends
are measured directly and the rate is a fit through them, so the ends win; and because the cap's
length is now set by the arm at one end and by a DIRECTED pin at the other, the angle is a
consequence with nothing left to set it with.

*What it costs.* Over the two 2026-08-13 directives, 0.0192 of tier-1 blockout IoU and 0.0232 of
registered silhouette IoU, both itemised in the chain above. 2026-08-08 gave some back — +0.0034
blockout, +0.0048 silhouette — and the reason is in §8: the caps' axis is 22 units outboard of the
crop's, so gold below the leather barely overlaps the crop's gold at any height, and deleting the
bottom 19 units deleted more render-only pixels than reference ones. What all of it buys is the
shape the user asked for and the crop shows: widest at the top, narrowing all the way down, and
now the crop's own length.

*What is still unresolved.* Whether the cap's bottom is a flat disc of radius ~11.5 or the blunt
8.1 the build carries. The crop's last six rows fall from half-width 11.4 to 3.5, but both caps
hang ~12° off vertical, so a flat bottom face reads as a 4–5 unit ramp of its own and the crop
cannot separate the tilt from the taper. 8.1 sits between the two readings and is kept.

## Defects worth recording

Both are hand-off traps with no home in this exhibit's own code. The four that *do* have one —
the explode rest-pose snapshot, `material.color` squaring the albedo, a concave outline fanning
into a bowtie, and `analyze_texture.py` inverting two of five materials — now live as JSDoc on
the constant or helper each one is about, and in `spec/pbr-evidence/README.md`.

1. **The blade root buried the entire hilt.** A full-width root at `Y=−30` put a 148-unit slab
   over the guard, all four driver roots and both carriers. The measured shell base is `Y=+4.9`;
   there is no root component any more — the shell converges into the jaws instead.

2. **The capture tool silently produced blank PNGs.** Roughly one shot in three came back pure
   white even after the harness signalled ready and an in-page probe confirmed the canvas held
   an image — the compositor, not the renderer. `tools/capture_ultima.mjs` now reads the drawing
   buffer via `toDataURL` instead of screenshotting the composited page.
