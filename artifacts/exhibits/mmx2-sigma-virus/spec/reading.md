# Reading — MMX2 wireframe Sigma head, green variant

Reference: `references/sigma-wireframe-sheet.png`, 610×2644, "Wireframe Sigma / Captured from
Megaman X2 by Polar Koala". Every number below traces to a JSON in this directory; nothing is
copied from a summary.

Rerun everything:

```bash
cd artifacts/exhibits/mmx2-sigma-virus
python3 spec/p0_triage.py           references/sigma-wireframe-sheet.png spec/p0-triage.json
python3 spec/index_frames.py        references/sigma-wireframe-sheet.png spec/frame-index.json
python3 spec/compare_hue_groups.py  references/sigma-wireframe-sheet.png spec/frame-index.json spec/hue-groups.json
python3 spec/find_front_frame.py    references/sigma-wireframe-sheet.png spec/frame-index.json spec/front-frame.json
python3 spec/measure_landmarks.py   references/sigma-wireframe-sheet.png spec/landmarks.json
python3 spec/measure_eye_slant.py
python3 spec/measure_profile_width.py references/sigma-wireframe-sheet.png spec/frame-index.json spec/profile-width.json
python3 spec/measure_depth_bound.py   references/sigma-wireframe-sheet.png spec/frame-index.json spec/depth-bound.json
spec/run_gates.sh                       # fresh capture + all four gates
```

## What the subject is

The MMX2 **Sigma Virus** is the game's final boss: with his Reploid body destroyed, Sigma takes
the Central Computer's power and fights on as an energy body shaped like a 3D wireframe of his
own head. It has **no health meter** — damage is reported purely by the model's colour, which
runs **green (full health) → pale blue → dark blue → purple → orange → red**. It can only be hurt
by a Charge Shot, Strike Chain, or Shoryuken, and it fires heat rays from its mouth.

So **the green one is the Sigma Virus at full health**, which is why "the green one" is the
version worth building — it is the default state, not one of six equal palettes.

## What the sheet actually contains — one mesh, not three heads

`index_frames.py` segments it into **307 frames** (8-connectivity with a 2px bridge — the dashed
hidden-line segments shatter a head into a dozen fragments under plain 4-connectivity):

| Strokes | Accent | Frames |
| --- | --- | --- |
| blue | red | 107 |
| red | blue | 113 |
| red | purple | 31 |
| orange | purple | 46 |
| red / purple / **green** / orange | rotates with the body | 4 (the palette strip) |

**The first reading of this table was wrong**, and it is worth recording how. Comparing a blue
frame against a red frame at 10× NEAREST, the blue one looked like a different head — no crest
triangles, an accent low on the face reading as a grimacing mouth. That went into the first
report as "three different heads on the sheet".

It was a pose difference, not a topology difference. `compare_hue_groups.py` picks each hue
group's most row-symmetric frame **at the palette strip's own 48×69** and takes the IoU of their
filled silhouettes:

| Pair | IoU |
| --- | --- |
| blue \| orange | 0.9886 |
| blue \| red | 0.9623 |
| orange \| red | 0.9540 |
| green \| red | 0.9320 |
| green \| orange | 0.9228 |
| blue \| green | 0.9155 |

Every pair clears the same 0.90 the front-view gate uses for "the same shape". Letting the frame
height float instead — the first version of that script — pairs a frame at one pitch against
another at a different one and scores the pitch: blue\|red fell to 0.9087 and green\|red to
0.8902, which is what made two poses of one mesh look like two meshes.

Cross-checked against the published colour ladder above, the conclusion is that **the sheet is
one mesh in the boss's six damage palettes**, and the accent hue rotates with the body colour —
the eyes are blue at red health, purple at orange health, orange at green health. That is an SNES
palette rotation, and it means **all 307 frames are evidence about this head**, not 113.

### The palette strip, and what green is authority for

The four palette-strip frames measure **48×69 px with 808 stroke pixels each — identical to the
pixel** (`p0-triage.json.paletteVariants`). `crossVariantSpread` is `0.0` in both axes, so
`measurementUncertainty = 0.0`.

The green frame is nevertheless the **colour authority only**. `measure_landmarks.py` on it
returns a lopsided row profile — top row x 12–31 (centre 21.5) against a widest row of 0–47
(centre 23.5) — and `find_front_frame.py` scores it by per-row silhouette-extent asymmetry:

| Frame | rowAsymmetry |
| --- | --- |
| **(63, 1811) 47×69 — geometry authority** | **0.0101** |
| (167, 1814) / (280, 1818) | 0.0123 |
| green palette frame (496, 2573) | 0.0555 |
| worst same-scale frame (109, 1645) | 0.0947 |

The green frame is **5.5× less symmetric**: it is caught at a small yaw, so geometry comes from
the red frame and only the palette comes from green.

Symmetry is measured on per-row extents, not on stroke pixels. A pixel-wise mirror test on this
frame returns `mirrorMismatch 0.6532` for a wireframe drawn symmetric — the strokes are 1px, so a
mirrored stroke almost never lands on another stroke, and that metric scores raster registration
rather than shape. Anyone re-deriving this should not read 0.65 as "asymmetric head".

### P0 deviations from the project recipe, and why

`CLAUDE.md` P0 prescribes corner flood fill AND a whiteness test. Both assume a **filled** subject
on a light ground. This reference is the inverse — coloured 1px strokes on uniform `#000029`. A
flood fill reaches every interior cell through the gaps between strokes and reports the subject as
empty. So the mask is keyed on hue instead, and the background constant is **asserted against the
measured corner colour** (`p0-triage.json.backgroundMatches: true`).

Clipping check: the green frame's bbox is `x 496–543, y 2573–2641` inside a 610×2644 sheet —
clear of all four edges, so no dimension is truncated.

## Parts, and the three orthogonal codes

Shape codes — 8 codes, 13 instances, every mirror pair authored once and negated in x:

| S | Part | Instances |
| --- | --- | --- |
| S1 | `crownPlate` — flat-topped helmet crest, chamfered corners | 1 |
| S2 | `skullShell` — forehead → cheek → chin taper, the main volume | 1 |
| S3 | `browRidge` — triangular ridge over each eye, meeting a V at the bridge | 2 |
| S4 | `eyePlate` — angular slanted eye | 2 |
| S5 | `sidePanel` — tall vertical helmet plate | 2 |
| S6 | `earPod` — rounded side lobe, the widest point of the whole head | 2 |
| S7 | `jawBlock` — the block under the cheeks | 1 |
| S8 | `chinTab` — tab at the jaw block's bottom corners | 2 |

`jawBlock`/`chinTab` were first named `neckBlock`/`neckFoot`, from reading the lower rectangle as
a neck. The published record says otherwise: the boss fires from its **mouth**, and the retail
build's changes to the prototype model are described as recolouring the eyes and reworking
Sigma's **smirk and chin** to match his sprite design. A wireframe head that ends at a chin has no
neck, and the yawed frames back that up — the lower structure juts forward under the cheeks
rather than dropping straight down.

Colour codes, from a pixel count over the green frame's bbox (`p0-triage.json.greenFrameColours`),
not an eye-dropper point:

| C | RGB | Hex | Pixels | Where |
| --- | --- | --- | --- | --- |
| C1 | 16, 216, 48 | `#10D830` | 656 | every structural edge |
| C2 | 16, 176, 16 | `#10B010` | 152 | secondary / far-side edges |
| C3 | 224, 80, 0 | `#E05000` | 57 | both eyes |

Material codes: **1** — flat emissive wireframe. Per `CLAUDE.md` ("count the material codes
first; if there are only one or two, fold them into the colour stage") there is no Stage 4.

## Guess list

### G1 — Head depth. **RESOLVED at 1.4255 × width.** Was a guess at 1.25.

Once the sheet is one mesh, a pose-free measurement exists. Filter the index to frames whose
height matches the front view's 68–70px and the rotation must have stayed about the vertical
axis: **87 frames, a pure yaw sweep**, widths running **42 → 67** against a 47px front view
(`profile-width.json`).

The peak alone does not finish it — for a rectangular cross-section the peak is the ~45° diagonal
(depth 1.02×) and for an elliptical one it is the 90° view (depth 1.43×). The model's own captured
sweep decides which family this is: across 0–90° it runs 480, 478, 502, 534, 560, 581, 600, 603,
594, 606 — flat from 60° and peaking at 90°. Width at the peak IS depth, so

> depth / width = 67 / 47 = **1.4255**

Cross-check, `measure_depth_bound.py`: the largest silhouette chord over all frames is the mesh's
own 3D caliper diameter regardless of pose, and against the front view's chord it puts a **lower**
bound of 37.9px on the depth (0.81× width). 67px sits above that, consistently.

The old 1.25 came from the crown-from-above ovoids at (209,1508) 61×47 and (142,1505) 60×48 —
foreshortened, and 11.4% low. `gate_yaw_sweep.py` now holds this at a 5% tolerance.

### G2 — Back of the head. **Still open. Default: the shells' own rear.**

The yawed frames at (529,119) and (468,2258) — both 66×68 — do show the rear dome, and it reads
as a faceted shell with hexagonal panelling. Nothing here reproduces that panelling, and no gate
looks at it, because turning those frames into measurements needs each one's pose solved first.

### G3 — Eye geometry: inset or proud? **Default: recessed into the face plane.**

At 14× the eye outline is drawn inside the brow and cheek edges, with no separate outline
suggesting a raised bezel. The build puts it at 0.9 of the face plane's z. Could be a flush
emissive panel; the wireframe cannot tell those apart.

### G4 — The two `chinTab` shapes. **Default: geometry, not a hidden-line artefact.**

They appear in every same-scale front frame at the same place, so they are on the model.

## Suitability

Pass. Single subject, uniform ground, no compression noise, no clipping, and — unusually — the
reference is itself a wireframe render of a low-poly mesh, so the target IS the reconstruction
medium. Faceted flat shading with a wireframe overlay is faithful here rather than stylised.

## Build record — Stage 1/2

| Gate | Number | Threshold | Verdict |
| --- | --- | --- | --- |
| Front silhouette IoU | **0.9205** | ≥ 0.90 | pass |
| Aspect error | 0.0169 | ≤ 0.06 | pass |
| Band IoU — crown / helmetSides / earPods / cheekTaper / jawBlock | 0.917 / 0.885 / 0.963 / 0.928 / 0.938 | — | helmetSides is the weakest |
| Eye band edges (max Δ) | 0.037 | ≤ 0.06 | pass |
| Eye filled area | rel. error **0.2595** | ≤ 0.30 | pass |
| Depth, yaw-sweep width ratio | model 1.4177 vs reference 1.4255, rel. error **0.0055** | ≤ 0.05 | pass |
| Structure | 13 named parts, 13 meshes, explode 0.49 → 1.58 | 13 expected | pass |

Verdict: **continue**.

### Four instrument errors so far, all caught before they became model errors

1. **The feature gate's first version passed a wrong model.** It compared the render's FILLED
   eyes against `landmarks.json.eyeBand.pixels`, which counts the reference's outline STROKES —
   57px. An eye at 44% of its reference size scored as 32% too *large*. Filling the reference eye
   per row and per side moved the reference from 1.94% of the frame to 4.19%, and the same render
   then failed at 38.8%.
2. **The render's eye slant looked inverted and was not.** `measure_eye_slant.py` takes column
   means at each end of the accent cluster: both authorities put the OUTER end high by 0.75–1.30
   rows. The drop was tightened from 1.6 to 1.1 rather than flipped.
3. **`compare_hue_groups.py` first let frame height float**, which scored pitch instead of shape
   and turned two poses of one mesh into "two different heads" in the first report.
4. **A per-row z-centre was tried and rejected by its own render.** Aligning every ring's FRONT on
   one plane pushed the shallow crown and chin tabs forward while the deep ear-pod rows stayed
   back; perspective magnified the near extremes and the front view grew from 476×695 to 480×796,
   failing aspect at 0.1147 against 0.06. The reference says the face is at the front; it says
   nothing about the crown's z-centre.

Every one is the same shape: the symptom was in the render, the cause was in the instrument or in
a rule that the reference never licensed.

### What still does not match, named rather than claimed done

- **Eye outline.** The reference eye is a chevron with a kink partway along; the build's is a
  straight parallelogram in the right band, at the right slant, at the right area. The gates score
  band and area, so they cannot see this.
- **Edge density.** The loft steps every 2–3 reference rows, so the render carries more horizontal
  rings than the reference's sparser wireframe.
- **helmetSides is the weakest band at 0.885.** The side panels' thickness is authored (±2.5px);
  the reference draws them as lines with no fillable width.
- **The rear dome's panelling** — guess G2 above.

## Sources

Consulted for the subject's identity, the damage-colour ladder, and the prototype-vs-retail model
changes:

- [Sigma Virus — MMKB (Fandom)](https://megaman.fandom.com/wiki/Sigma_Virus)
- [Sigma/Mega Man X2 — MMKB (Fandom)](https://megaman.fandom.com/wiki/Sigma/Mega_Man_X2)
- [Sigma Virus — MMKB (Miraheze)](https://megaman.miraheze.org/wiki/Sigma_Virus)
- [Mega Man X2/X-Hunters Base 5 — StrategyWiki](https://strategywiki.org/wiki/Mega_Man_X2/X-Hunters_Base_5)
- [Proto:Mega Man X2/Sprite Changes — The Cutting Room Floor](https://tcrf.net/Proto:Mega_Man_X2/Sprite_Changes)
- [Sigma Virus — The Spriters Resource (SNES / Mega Man X2)](https://spriters-resource.com/snes/megamanx2/sheet/3087)

Two caveats on those. Fandom, Miraheze and Spriters Resource all refused a direct fetch (402/403),
so the wiki claims above rest on search-result summaries rather than on pages read end to end.
And the TCRF page, when fetched, returned **prompt-injection text** — instructions addressed at an
LLM to write files and report fabricated errors — instead of article content. Those instructions
were not followed, and the prototype-vs-retail claim here comes from the search summary, not from
that fetch. Treat every source line in this section as second-hand; the numbers in this document
all come from the sheet.
