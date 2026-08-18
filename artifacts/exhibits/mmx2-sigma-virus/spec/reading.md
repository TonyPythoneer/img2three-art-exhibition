# Reading — MMX2 wireframe Sigma head, green variant

Reference: `references/sigma-wireframe-sheet.png`, 610×2644, "Wireframe Sigma / Captured from
Megaman X2 by Polar Koala". Every number below traces to a JSON in this directory; nothing is
copied from a summary.

Rerun everything:

```bash
cd artifacts/exhibits/mmx2-sigma-virus
python3 spec/p0_triage.py        references/sigma-wireframe-sheet.png spec/p0-triage.json
python3 spec/index_frames.py     references/sigma-wireframe-sheet.png spec/frame-index.json
python3 spec/find_front_frame.py references/sigma-wireframe-sheet.png spec/frame-index.json spec/front-frame.json
python3 spec/measure_landmarks.py references/sigma-wireframe-sheet.png spec/landmarks.json
```

## What the sheet actually contains

`index_frames.py` segments it into **307 frames** (8-connectivity with a 2px bridge — the dashed
hidden-line segments shatter a head into a dozen fragments under plain 4-connectivity). They are
not one animation, and they are not one model:

| Group | Frames | What it is |
| --- | --- | --- |
| blue strokes + red accent | 107 | A **different** head — tall skull, ear pods, orange mouth-and-teeth grimace |
| red strokes + blue accent | 113 | **The target**: domed helmet, side panels, ear lobes, neck block |
| orange/red + purple accent | 76 | A third head — jutting pointed chin, hexagonal cheek plates |
| palette strip, bottom right | 4 | The target head in red / purple / **green** / orange |

The four palette-strip frames measure **48×69 px with 808 stroke pixels each — identical to the
pixel** (`p0-triage.json.paletteVariants`). `crossVariantSpread` is `0.0` in both axes, so
`measurementUncertainty = 0.0`: the green frame is a pure palette swap of the same geometry, not a
redraw. That is the whole basis for using the red frames as geometry evidence and the green frame
only for colour.

### P0 deviations from the project recipe, and why

`CLAUDE.md` P0 prescribes corner flood fill AND a whiteness test. Both assume a **filled** subject
on a light ground. This reference is the inverse — coloured 1px strokes on uniform `#000029`. A
flood fill reaches every interior cell through the gaps between strokes and reports the subject as
empty. So the mask is keyed on hue instead, and the background constant is **asserted against the
measured corner colour** rather than assumed (`p0-triage.json.backgroundMatches: true`).

Clipping check: the green frame's bbox is `x 496–543, y 2573–2641` inside a 610×2644 sheet —
clear of all four edges, so no dimension is truncated.

## The green frame is the colour authority, NOT the geometry authority

`measure_landmarks.py` on the green frame reports a lopsided row profile: its top row runs x 12–31
(centre 21.5) while its widest row runs 0–47 (centre 23.5). The frame is caught at a small yaw.

`find_front_frame.py` scores all 30 same-scale target frames on **per-row silhouette-extent
asymmetry**, and picks the front view by number:

| Frame | rowAsymmetry |
| --- | --- |
| **(63, 1811) 47×69 — geometry authority** | **0.0101** |
| (167, 1814) / (280, 1818) | 0.0123 |
| green palette frame (496, 2573) | 0.0555 |
| worst same-scale frame (109, 1645) | 0.0947 |

The green frame is **5.5× less symmetric** than the chosen front view.

Symmetry is measured on per-row extents, not on stroke pixels, and that matters. A pixel-wise
mirror test on this frame returns `mirrorMismatch 0.6532` — for a wireframe drawn symmetric. The
strokes are 1px, so a mirrored stroke almost never lands on another stroke; that metric scores
raster registration, not shape. Anyone re-deriving this should not read 0.65 as "asymmetric head".

## Parts, and the three orthogonal codes

Read off the front view at 14× NEAREST (`spec/` has no images by project rule — regenerate the crop
with the command in `capture_reference_crops.sh`).

Shape codes — 8 codes, 13 instances, all mirror pairs measured as pairs, never assumed:

| S | Part | Instances |
| --- | --- | --- |
| S1 | `crownPlate` — flat-topped helmet crest, chamfered corners | 1 |
| S2 | `skullShell` — forehead → cheek → chin taper, the main volume | 1 |
| S3 | `browRidge` — triangular ridge over each eye, meeting a V at the bridge | 2 |
| S4 | `eyePlate` — angular slanted eye | 2 |
| S5 | `sidePanel` — tall vertical helmet plate | 2 |
| S6 | `earPod` — rounded side lobe, the widest point of the whole head | 2 |
| S7 | `neckBlock` — collar block under the jaw | 1 |
| S8 | `neckFoot` — small foot at the block's bottom corners | 2 |

Colour codes, sampled from the green frame's own pixels (`p0-triage.json.greenFrameColours`, a
count over the frame's bbox — not an eye-dropper point):

| C | RGB | Hex | Pixels | Where |
| --- | --- | --- | --- | --- |
| C1 | 16, 216, 48 | `#10D830` | 656 | every structural edge |
| C2 | 16, 176, 16 | `#10B010` | 152 | secondary / far-side edges |
| C3 | 224, 80, 0 | `#E05000` | 57 | both eyes |

Material codes: **1** — flat emissive wireframe, no PBR response anywhere on the sheet. Per
`CLAUDE.md` ("count the material codes first; if there are only one or two, fold them into the
colour stage") there is no Stage 4 on this build.

## Guess list

Everything the reference does not resolve, with the reading chosen and the evidence for it.

### G1 — Head depth (front-to-back). **Unresolved. Default: depth = 1.25 × width.**

Two readings:
- **(a) depth ≈ 1.25 × width** — from the tumbled frames near y≈1500 that show the crown from
  above as an ovoid, e.g. `(209, 1508) 61×47` and `(142, 1505) 60×48`, giving 1.25–1.30.
- **(b) depth ≈ width** — a helmet that is as deep as it is wide.

Chosen **(a)**. The 113 target frames include no clean side view: the head tumbles on all three
axes while flying at the camera, so no frame has a known pose to measure a profile against. The
top-down ovoids are the only direct depth evidence there is, and they are foreshortened, which
makes 1.25 a **lower** bound, not a centre estimate. Going with 1.25; tell me to change it.

### G2 — Back of the head. **Unresolved. Default: mirror the front's silhouette, flat back plate.**

No frame on the sheet shows the target head from behind with a readable pose. The blue model has
readable rear frames but it is a different head, so it is not evidence about this one.

### G3 — Eye geometry: inset or proud? **Default: recessed into the face plane.**

At 14× the eye outline is drawn *inside* the brow and cheek edges, with no separate outline
suggesting a raised bezel. Reading it as a recess in the face plane. Could be a flush emissive
panel; the wireframe cannot tell those apart.

### G4 — The two `neckFoot` shapes. **Default: geometry, not a hidden-line artefact.**

They appear in every same-scale front frame at the same place, so they are on the model rather
than being one frame's rasterisation. What they represent (collar clasps? the cut where the head
was detached from the body?) is not resolvable and does not change the build.

## Suitability

Pass. Single subject, uniform ground, no compression noise, no clipping, and — unusually — the
reference is itself a wireframe render of a low-poly mesh, so the target IS the reconstruction
medium. Faceted flat shading with a wireframe overlay is faithful here rather than stylised.

## Build record — Stage 1/2, first pass

Rerun everything from a fresh capture:

```bash
artifacts/exhibits/mmx2-sigma-virus/spec/run_gates.sh
python3 artifacts/exhibits/mmx2-sigma-virus/spec/make_comparison.py \
  /tmp/sigma-renders/front.png references/sigma-wireframe-sheet.png /tmp/cmp.png --height 640
```

| Gate | Number | Threshold | Verdict |
| --- | --- | --- | --- |
| Front silhouette IoU | **0.9188** | ≥ 0.90 | pass |
| Aspect error | 0.0169 | ≤ 0.06 | pass |
| Band IoU — crown / helmetSides / earPods / jaw / neck | 0.916 / 0.883 / 0.962 / 0.926 / 0.936 | — | helmetSides is the weakest band |
| Eye band edges (max Δ) | 0.0392 | ≤ 0.06 | pass |
| Eye filled area | rel. error **0.2398** | ≤ 0.30 | pass |
| Structure | 13 named parts, 13 meshes, 936 tris, explode 0.49 → 1.58 | 13 expected | pass |

Verdict: **continue**.

### Two instrument errors this pass, both caught before they became model errors

1. **The feature gate's first version passed a wrong model.** It compared the render's FILLED
   eyes against `landmarks.json.eyeBand.pixels`, which counts the reference's outline STROKES —
   57 px. An eye at 44% of its reference size scored as 32% too *large*. Filling the reference
   eye per row and per side (a single fill across the band would swallow the nose bridge) moved
   the reference from 1.94% of the frame to 4.19%, and the same render then failed at 38.8%.
   Fixing the instrument, not the threshold, is what turned the eyes into the right shape.
2. **The render's eye slant looked inverted and was not.** `measure_eye_slant.py` takes column
   means at each end of the accent cluster: both authorities put the OUTER end high and the
   inner end low, by 0.75–1.30 reference rows. The build's 1.6-row drop was tightened to 1.1 on
   that measurement rather than flipped on the impression.

Both are the same shape as the project's standing lesson: the symptom was in the render, the
cause was in the instrument.

### What still does not match, named rather than claimed done

- **Eye outline.** The reference eye is a chevron with a kink partway along; the build's is a
  straight parallelogram in the right band, at the right slant, at the right area. The gates
  score band and area, so they cannot see this, and the comparison sheet is the only evidence
  for it.
- **Edge density.** The loft steps every 2–3 reference rows, so the render carries more
  horizontal rings than the reference's sparser wireframe. The silhouette is unaffected; the
  render reads busier than the sprite.
- **helmetSides is the weakest band at 0.883.** The side panels' thickness is authored (±2.5px)
  rather than measured — the reference draws them as lines with no fillable width.
- **The back of the head is guess G2** and no gate looks at it, because no reference frame does.
