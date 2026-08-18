# HANDOFF — MMX2 Sigma Virus head (green), `/mmx2-sigma-virus`

Branch `feat/megaman-x2-sigama-virus`, six commits, pushed. Read this file, then
[`spec/reading.md`](spec/reading.md) — reading.md carries the evidence and the derivations, this
file carries what is **left**.

Nothing here is blocked on a decision. Everything below is work someone could pick up cold.

## Where it stands

```bash
artifacts/exhibits/mmx2-sigma-virus/spec/run_gates.sh    # fresh capture + every gate, ~40s
```

| Gate | Number | Threshold | |
| --- | --- | --- | --- |
| Front silhouette IoU | 0.9347 | ≥ 0.90 | pass |
| Aspect error | 0.0423 | ≤ 0.06 | pass |
| Band IoU — crown / helmetSides / earPods / cheekTaper / jawBlock | 0.897 / 0.941 / 0.981 / 0.906 / 0.933 | — | pass |
| Eye band edges, max Δ | 0.037 | ≤ 0.06 | pass |
| Eye filled area | 0.0616 | ≤ 0.30 | pass |
| Depth, yaw-sweep width ratio | 1.2936 vs 1.3191 → 0.0194 | ≤ 0.05 | pass |
| Structure | 13 named parts, 13 meshes, 664 tris, explode 0.49 → 1.58 | 13 | pass |
| Wireframe density | reference 11.93, assembly 41.6, skullShell alone 17.7 | ≤ 25% | **documented limitation** |

`vue-tsc` clean, `npm run build` prerenders three pages, `node --test tests/*.test.mjs` 9/9.

## The one thing that is not done, and cannot be with the current structure

### H1 — Wireframe density: the assembly draws ~3.5× the reference's line

The reference is a single-shell wireframe carrying 11.93 head-heights of line. The build carries
41.6. Side by side, the render reads busier than the sprite; this is the largest remaining visual
difference and the only gate that does not pass.

**It is not over-tessellation.** Capture the same model with every part but `skullShell` hidden
and it reads 17.7 — the same order as the reference. The excess is the **13-part decomposition the
project's assembly gate requires**: thirteen closed solids each draw their own top, bottom and
rear rims, where the reference's single shell has no such surfaces at all.

What was already tried:

- `RING_STEP` 2 → 7 and `EdgesGeometry` 1° → 30°: 59.8 → 44.3, cost 0.006 of front IoU. Pushing
  to step 16 only reached 2.6× while dropping IoU to 0.9006 — that is where the trade stops.
- `cullBuriedEdges.ts` — drop every edge whose endpoints and midpoint sit inside the skull's
  measured envelope. Bought 11%. Little is buried, because the small parts protrude by design.

What would actually close it, in rough order of cost:

1. **Hidden-line removal between parts.** Not the envelope test that exists, but real
   part-vs-part occlusion: for each edge, whether any OTHER part's surface lies in front of it
   from the current camera. That is view-dependent, so it means a per-frame pass, not a build-time
   one.
2. **Author the shell as one mesh and derive the parts from face groups** rather than from
   separate solids. `check_part_coverage`-style structure gates want named parts, not separate
   geometries — a single `BufferGeometry` with named groups might satisfy both. Worth checking
   what `partInspector.ts` actually requires before committing to it.
3. Accept it and re-base the gate on a part-decomposed reference. There isn't one, so this is
   really "delete the gate", and the gate is telling the truth.

## Reference limits — real, and not closable from this sheet

### H2 — The cross-section solve loses front/back asymmetry

`solve_cross_sections.py` reconstructs each row's **central symmetral** from silhouette widths.
Widths are registration-free, which is why the solve works at all without knowing where the
model's axis projects to in a turned frame — and it is exactly why the result is centrally
symmetric. The real head is not: the face is a plane and the dome bulges behind it.

The build compensates by anchoring the face parts (`browRidge`, `eyePlate`) to the shell's front
surface via `FACE_Z`, which puts ~0.1 of the depth in front of the eyes and ~1.9 behind. That
matches what the ~60° frames show, but it is a placement rule, not a measured profile.

To do it properly you need the **left and right silhouette edges separately**, which needs each
frame's axis projection — i.e. solving, per frame, both the yaw and the horizontal offset of the
model's axis. A bundle adjustment over the 81 pure-yaw frames, with the head's own mirror symmetry
as the constraint that makes it identifiable. That is the single biggest remaining fidelity lever.

### H3 — The solve undershoots, and is corrected by one scalar

A support-function reconstruction can only shrink: every extra measured direction is another
half-plane and none push outwards. The widest solved section has a caliper of 55.3px against the
vetted set's widest frame at 62, so `section.ts` multiplies depths by **1.1212**.

One global scalar standing in for a per-row bias. It is pinned to an independent measurement and
`gate_yaw_sweep.py` holds it, but a per-row undershoot estimate — from how many bins actually
constrained each row — would be better. `cross-sections.json.binCoveragePerRow` already carries
the input.

### H4 — Yaw is estimated, not solved

Per frame, `cos t = accent x-extent / the most frontal frame's extent`, then the observed range is
stretched onto 0..90 because the extent floors at ~7px rather than collapsing (the eye has its own
depth). The stretch factor is calibrated against the front-view widths — a genuine hold-out, mean
relative error **0.0197** — but it is still a one-parameter correction to a first-order model.

Alternatives tried and rejected: yaw from the frame's own bbox width (mean error 0.0835, and it
fails badly at rows 0 and 68). Analysis-by-synthesis — assign yaw from the current model's own
width curve, re-solve, iterate — was not tried and is the obvious next step.

### H5 — G2, the back of the head, is closed as unresolvable

`find_back_frame.py` scans all 263 full-scale frames for one whose accent has been occluded and
finds **zero**; the minimum is 27 accent pixels. The animation never turns the head far enough to
show its back. The most-turned frames do show the rear dome as a faceted shell with hexagonal
panelling — that is a reading, not a measurement, and nothing reproduces it.

If someone finds a second rip of this model, or the mesh itself in a ROM dump, this reopens.

### H6 — The eye is a leaf, and G3 is still a guess

`EYE_POLYGON` is six vertices fitted to 14 measured columns, within 0.6 reference pixels. What is
still guessed is whether the eye is **recessed or flush** (G3): the build recesses it to 0.9 of
the face plane, because moving it to within 0.4px of the plane pushed its projected area past the
gate at 30.6%. A wireframe cannot distinguish a recess from a flush emissive panel.

## Smaller things, in the order I would do them

### H7 — `cheekTaper` is the weakest band at 0.906

Rows 43–44 want the full 0–46 width the ear pods supply; rows 45–51 want the taper the skull
supplies. The handover between `BANDS.earPod` and the skull's `SKULL_MAX_HALF` cap lands one ring
short of the reference's corner. Sweeping the two band ends against each other trades 0.0016 of
this band for 0.0026 of the whole figure, so it sits where the whole-figure number is best. A
non-uniform ring at the handover row would get both; `bandRings` currently only takes a fixed
`step`.

### H8 — `crown` slipped from 0.916 to 0.897 when depth became per-row

The solve puts the crest at 7px deep against the ~33px the old global ratio gave it. Under
perspective a much shallower crest projects slightly differently, and the crown band paid ~2
points for it. The depth number is better evidenced than the band is; worth confirming with an
orthographic capture, which would remove perspective from the comparison entirely.

### H9 — The silhouette gate measures the WIREFRAME's extent, not the solid's

`COLORS.ground` is used for both the scene background and the part fills, so the fills are exactly
background-coloured and the gate's bounding box is defined by the drawn lines. Raising
`EDGE_ANGLE` therefore moves the measured aspect (0.0138 → 0.0337 across one such change) without
the model's shape changing at all. Giving the fill a navy distinguishable from the ground by more
than `BG_TOL` (24) would decouple them — at the cost of the render no longer reading as pure
wireframe on the sheet's own ground.

### H10 — `measure_profile_width.py` and `measure_depth_bound.py` are superseded

Both predate `pure_yaw_set.py` and both use the height-only filter, so their conclusions
(depth 1.4255, lower bound 37.9px) are computed over a set containing the six tumbled frames.
They are kept because `reading.md` cites them as the record of how the number moved, but nothing
in the build reads them. Either re-run them against `pure-yaw.json` or mark them superseded in
their own docstrings — right now only reading.md says so.

### H11 — `gate-parts.json` was invalid JSON for five commits

`run_gates.sh` redirected all of `verify_sigma_parts.mjs`'s stdout into it, trailing human-readable
PASS line and all. Fixed by giving the tool an explicit `--out`. Nothing read the file back, which
is why nothing complained — worth a glance at the other `gate-*.json` for the same shape of
problem.

### H12 — The exhibit has no lighting-mode control, deliberately

One material code, so a rig switcher would be three buttons rendering the same thing. If a future
pass adds material variation, `mountSigmaVirusViewer.ts` will need the `setMode` the other exhibit
has.

## Map of the code

| File | What it owns |
| --- | --- |
| `src/utils/sigmaVirusHead/measurements.ts` | Every measured constant, unit conversion, the 69-row silhouette table, the eye outline and polygon. Docstrings carry the provenance. |
| `crossSections.ts` | **GENERATED** — 35 rows × 12 vertices of solved cross-section. Regenerate, never hand-edit; the command is in its header. |
| `section.ts` | Interpolates the generated sections, applies the X renormalisation and the 1.1212 undershoot correction. |
| `loft.ts` | `chamferedRing` + a non-indexed faceted loft. Non-indexed on purpose: `computeVertexNormals` on an indexed mesh smooths the facets away. |
| `cullBuriedEdges.ts` | Envelope test that drops edges buried inside the skull. |
| `createSigmaVirusHead.ts` | The 13 part factories and the assembly. Authors no geometry at the root. |
| `mountSigmaVirusViewer.ts` | The viewer. Exposes `window.__sigmaViewer` for the capture harness and `__renderReady` on the third frame. |
| `tools/capture_sigma.mjs` | Headless capture off the real route. `--yaw-sweep`, `--only-part`, `--views`. |
| `tools/verify_sigma_parts.mjs` | The structure gate. |

Evidence and instruments live in `spec/`. Every `gate_*.py` exits 0/1/2 and writes its own JSON;
every `measure_*.py` / `find_*.py` / `solve_*.py` writes a JSON and prints a human summary.

## Six instrument errors this build already made

Listed so the next person does not repeat them, and because every one of them looked like a model
error first. Details in `reading.md`.

1. Comparing the render's **filled** eyes against the reference's 57 **outline** pixels: an eye at
   44% of its size scored as 32% too large.
2. The eye slant looked inverted and was not — column means settle it, single pixels do not.
3. Letting frame height float in `compare_hue_groups.py` scored pitch instead of shape, and turned
   two poses of one mesh into "three different heads".
4. A per-row z-centre that aligned every ring's front on one plane: perspective magnified the
   shallow crown, aspect failed at 0.1147.
5. The density gate counting lit fills as line: 13.7× where the honest number is 4×.
6. Tracing the eye's 14 measured columns literally: a sawtooth, because those columns are a 1px
   rasterisation of straight edges.

And the big one, which was not an instrument error but a **filter** error: "height matches the
front view" is necessary for a pure yaw and not sufficient. Six tumbled frames passed it, they
were the six widest, and they set the head's depth by themselves for two commits.
