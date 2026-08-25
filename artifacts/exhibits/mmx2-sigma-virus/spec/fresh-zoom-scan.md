# Fresh-start zoom scan — 2026-08-21

Re-inspected key frames at 8× NEAREST (`zoom_frames.py` + `crop_authorities.py`, crops under
`zoom/`). This restart keeps the sheet as sole authority and discards the previous model code;
the numbers below re-confirm or sharpen `reference-analysis.md`.

## Frames inspected

| Crop | Sheet coords | Size | Reading |
| --- | --- | --- | --- |
| `zoom/geom_63_1811.png` | (63,1811) | 48×69 | Front view, red wire, blue eyes |
| `zoom/green_zone.png` | (480,2540)+130×104 | three frames | Green + orange-red three-quarter yaw pair, purple partial at left edge |
| `zoom/wide0.png` | (12,2247) | 66×40 | Crown-from-above depth evidence |
| `zoom/wide1.png` | (142,1505) | 60×47 | Side/rear-oblique shell |

## Confirmed readings (front authority)

1. **Crown**: faceted dome, not spherical — outline slightly tapers downward from a broad top;
   internal facet lines converge to a short front-to-back ridge peak.
2. **Eyes**: two slanted leaf/almond outlines in accent colour, angled down toward the centre,
   joined near a central bridge; they sit ~45–50% down the frame and are recessed inside face
   planes (outline sits inside the silhouette, never on it).
3. **Temple/cheek lobes**: angular protrusions at mid-height form the widest silhouette band;
   they extend past the cranial shell on both sides.
4. **Nose ridge**: single centre vertical line below the eye bridge ending in a small triangular
   tip around 70% height.
5. **Jaw**: narrows below the cheek lobes to a trapezoid chin plate with a small centre notch at
   the bottom edge.
6. **Mouth band**: horizontal seam ~75–80% height between nose tip and chin plate.

## Confirmed readings (three-quarter authorities)

7. Yaw views show ONE dominant eye per side plus the far-side lobe behind — consistent with deep
   set eyes under a brow ledge; the crown ridge runs front-to-back and is visible as a peaked
   seam from oblique angles.
8. The cheek lobe reads as its own shell plate overlapping the cranial shell, not a bulge of it.

## Confirmed readings (top authority, guess G1)

9. Outline elongated along one axis with quadrilateral crown facets either side of a centre seam;
   the purple centre feature is the nose/brow assembly seen from above (brow bar + forward nose).
   Foreshortened: depth ≥ 1.25 × width stays a lower bound; modelling uses depth ≈ 1.3 × width.

## Guess list (carried, with defaults)

| # | Part | Reading A | Reading B | Chosen | Evidence |
| --- | --- | --- | --- | --- | --- |
| G1 | Head depth | ~1.3× width | ~1.0× width | A | top frame foreshortened lower bound 1.25 |
| G2 | Eye depth | recessed pockets | flat decals | recessed | outline inside face planes in all yaws |
| G3 | Chin tabs | independent plates | jaw continuation | independent | recur at same normalized position across frames |
| G4 | Rear shell | symmetric continuation, no invented panels | decorated mechanism | A | obliques show plain facets only |
| G5 | Camera labels | canonical probes (front/±30°/±60°/side/top) | sheet order implies angles | canonical | labels not supplied |

## Palette (colour authority, green frame)

- wire bright `#10D830`, wire dim `#10B010`, eyes `#E05000`; background navy `#000029`.
- Red-family frames swap bright/dim wires for `#BD0008`/`#8C0008`-class reds with blue-violet
  eyes; palette swap only — four frames measure identical 48×69 / 808 stroke pixels.
