# FF7 Cloud Strife polygon figure — handoff

Read this, then `spec/PLAN-stage1-rebuild.md`, then `prompt.txt`. Where they disagree, the
prompt wins and this file is stale.

## Start here, next session

```bash
cd /Users/tonyyang/git/personal/img2three-art-exhibition
pnpm dev        # usually already running on :3000 — check before starting another
```

```
http://localhost:3000/img2three-art-exhibition/ff7-cloud-strife-polygon-figure
```

Opens on the assembled figure. No query string.

## Stage 3 (colour) — closed for Stage 1's 23 parts, out of AGENTS.md's normal order

**The owner explicitly ordered this** ("你先做上色的 stage") before Stage 2 (hair/face/ears)
existed. AGENTS.md's Hard Rule #1 ("all geometry finished before any colour") has a named
exception for exactly this — owner says so, decoration deferred, compensating gate owed —
and this is that exception, used rather than silently worked around:

- **Coloured**: all 23 Stage 1 parts, using prompt.txt §2's already-measured C-xx codes
  (`spec/palette.json`, sampled by clustering in an earlier session — nothing was
  re-sampled or guessed this session).
- **NOT coloured, because NOT BUILT**: hair (C-02), the two ears, faceDecal (C-09) — all
  Stage 2 — and pauldronL, the two chest straps, the diagonal back panel — decoration,
  prompt.txt schedules pauldronL at "S3" but it does not exist as geometry yet, so there is
  nothing to colour. C-06 (strap brown) and C-02/C-09 are absent from the generated
  `colors.ts` for the same reason: an unused colour constant is not evidence of anything.
- **Compensating obligation, owed and not yet paid**: prompt.txt's exception clause requires
  a full four-view silhouette re-check against the pre-exception baseline once the deferred
  geometry lands. That baseline is THIS session's `gate_silhouette.py` mean IoU **0.740**
  (front 0.792 · back 0.785 · left 0.717 · right 0.664) — record it before building hair,
  ears, faceDecal or the pauldron, and diff against it once any of them exist.

### What changed and how it was verified

- `spec/emit_colors.py` (new) reproduces prompt.txt §2's colour table from
  `spec/palette.json` as generated TypeScript — `src/utils/cloudStrifeFigure/colors.ts` —
  same discipline `emit_measurements.py` already applies to dimensions: a factory may not
  type a hex literal, it imports the generated module.
- `src/utils/cloudStrifeFigure/materials.ts` (new): one M-01 matte-vinyl
  `MeshStandardMaterial` singleton per colour code actually in use (`MAT_SKIN`,
  `MAT_SHIRT`, `MAT_PANTS`, `MAT_BELT`, `MAT_BOOT`, `MAT_BLACK`, `MAT_GREY`) — same "one
  shared instance" discipline `MANNEQUIN` used for M-00, now retired (M-00 "is the Stage 1
  stand-in and is gone by Stage 3", prompt.txt §2 — it is; `MANNEQUIN` is deleted from
  `parts.ts`, not just unused).
- 14 factory files updated to import a colour material instead of `MANNEQUIN`. `frontArm`
  is the one multi-colour part (§4[12]'s forearm/wrist/glove) and needed a real change:
  `armSegment.ts`'s shared `loft()` now takes either one material (13 other callers,
  unchanged behaviour) or one material PER BAND, using `BufferGeometry.addGroup` so it
  stays ONE mesh with the sub-segments unnamed (§1.6), not three named parts.
- **`gate_color.py` (new)** — a WIRING gate, not a photometric one: it compares each
  mesh's exported `material.color` (the authored hex, read off `THREE.Color`, never a
  rendered pixel) against `palette.json`'s adopted value for the C-xx code prompt.txt §2
  assigns that part. 23/23 pass. Proven non-vacuous with a fake-frame negative control (a
  synthetic capture with `chest` coloured `#FF0000` and `waist` missing its colour — both
  FAIL, exit 1). Deliberately NOT a rendered-pixel ΔE gate: sampling actual pixels under
  this scene's `referenceLighting` rig (borrowed from the Ultima Weapon prop) showed every
  material rendering at roughly HALF its authored brightness, uniformly regardless of hue
  (measured directly — chest pixel (38,36,63) vs authored (75,72,115), boot pixel
  (33,31,25) vs authored (64,61,47), ~0.51-0.52x both times). That is the lookdev
  lighting's tone response, not a colour-authoring bug, and a pixel-vs-hex gate would fail
  every part identically and prove nothing about wiring — a lighting/tone-mapping fidelity
  gate is a real but SEPARATE, later concern (Stage 5 territory).
- A real gap the colour work surfaced and fixed, not swept under the multi-material change:
  `mountCloudStrifeViewer.ts`'s mesh-export code assumed `object.material` was always one
  material. `frontArm`'s new 3-material array made it export `type: undefined,
  flatShading: undefined` for both `frontArmL`/`frontArmR`, and `gate_facets.py` correctly
  FAILED both (`no flatShading in the capture`) rather than silently passing — exactly the
  gate behaviour §5.4's own history documents. Fixed by normalising to an array and only
  reporting a field when every material on the mesh agrees on it; re-captured and
  `gate_facets.py` is back to 23/23.
- Full gate sweep re-run on the fresh coloured capture (`/tmp/color2`, not reused from
  before the fix): `gate_assembly.py` 26/26, `gate_naming.py` 24/24, `gate_facets.py`
  23/23, `gate_color.py` 23/23, `gate_silhouette.py` mean IoU 0.740 (unchanged from the
  Stage 1B baseline, as expected — colour does not move geometry).

Rerun: `python3 spec/emit_colors.py` after any `sample_palette.py` change, then
`node tools/capture_parts.mjs --assembled --out /tmp/x --views front,back,left,right` and
the five gates above against `/tmp/x/*.json` / `/tmp/x/*.png`.

## Where the work actually stands

**Stage 1 PASSES and Stage 1B is CLOSED.** 23 of 23 parts exist, the socket chain is
verified, every part gate is green, and the whole-figure Tier 1 silhouette instrument — the
one number that was FAILING (0.201) at the last handoff — now clears its own pinned
threshold with margin. Stage 1B's own contract ("monochrome rough assembly: socket
placement only, zero geometry in the integration file") turned out to already be satisfied
by `buildAssembled()` in `mountCloudStrifeViewer.ts` — it was written this session to make
Stage 1's socket chain visible, and it never authors a mesh, only positions Stage-1-built
parts by the socket ledger. Nothing else needed building for 1B; this handoff re-ran every
gate against a fresh capture to confirm that, rather than trust the number a docstring
carried over from before the fix.

| | |
|---|---|
| parts built | 23 / 23 |
| socket joints verified in the render | 21, at 0.000e+00 (`gate_assembly.py` 26/26) |
| part gates | arm 56/56 · sole 18/18 · ankle 20/20 · pant-leg 42/42 · pelvis 16/16 · waist 14/14 · chest 15/15 · neck 12/12 · head 11/11 · naming 24/24 · facet 23 of 23 |
| whole-figure Tier 1 (`gate_silhouette.py`, this project's own fair instrument) | **mean IoU 0.740** (front 0.792 · back 0.785 · left 0.717 · right 0.664) against a pinned 0.6 threshold — **PASS** |
| verdict | **Stage 1 PASS. Stage 1B PASS. Stage 3 PASS for the 23 built parts** (`gate_color.py` 23/23, new this session — see "Stage 3 (colour)" above). Stage 2 (face, hair, ears, decoration) is still not started — the colour work jumped ahead of it on an explicit owner order, with the exception's compensating obligation recorded above. |

Baseline this session started from: 0.201 FAIL (`ac33665`), then 0.720 (an earlier
in-session fix to the shoulder socket + camera framing, commit `2364fbe`, not yet reconciled
with the fixes below when that number was taken).

## What changed this session, and why each one is real (not tuned to pass)

Four root-cause fixes, each traced to a specific wrong number with a specific reason it was
wrong — not a threshold loosened to get a green checkmark.

1. **Arm `fist` (glove bottom) landmark was a hip-height proxy, not a measurement.**
   `author_spec.py`'s `Y["fist"]` used to read `F["widestHip"]` — the *hip's* widest point,
   which has nothing to do with the glove. It sat 0.054 below where the glove's own black
   silhouette actually ends (isolated band segment, front.webp rows 453–516). Fixed:
   `measure_arm.py` now walks down from the glove's widest row until the run narrows under
   15% of its max width, and `author_spec.py` reads that (`parts.arm.glove.bottomHeight`).
2. **Head `skullTop` was hardcoded to 1.0 — the hair spike TIP, not the skull.** The bare
   Stage 1 skull was built up to that height and rendered as a cone. The cranium is hidden
   behind the hair cap in every reference view, so it cannot be measured directly — but the
   boundary between "spike blade" and "cap mass" can: scan the hair band's width from the
   top down and find where it first reaches 60% of its own max. front.webp and back.webp
   agree on this to 0.004 (front 0.903, back 0.907). `measure_head.py` now records this as
   `parts.head.crownHeight`, explicitly labeled an approximation (not a bone measurement),
   and `author_spec.py`'s `Y["skullTop"]`/`HEAD_H` read it instead of a bare `1.0`.
   Two gates had the same stale `1.0` assumption baked in independently and needed the same
   fix: `gate_head.py` (`height = 1.0 - H["chinHeight"]`, plus a dead `pantLeg` reference
   that meant nothing) and `gate_silhouette.py` (the render-side chin-mask fraction assumed
   the render's visible top was always the 1.0 hairtip anchor — true before this fix, false
   after, since Stage 1's visible top is now the shorter crown). Both now read
   `socketChainY.skullTop` live instead of assuming 1.0.
3. **Pant leg §5.7(d)'s "near-constant width" check sampled the wrong row.** Its bottom
   reading was taken at `ankleTop` (= `pantHem`, row 691 on front.webp) — but the boot
   cuff's highest reach (`bootCuffTopHighest`) is row 683, *above* that. The check was
   measuring the sliver of fabric still visible once the boot cuff had already started
   occluding the leg, not the tube. It only "passed" because the tolerance was loose enough
   to hide a 43% narrowing. Fixed: sample one RMS above `bootCuffTopHighest` instead.
   Difference dropped from 0.0248 to 0.0013 — now a real pass, not a loose one.
4. **Arm depth (Z, fore-aft) at shoulder/deltoidWaist was averaged with an occluded read.**
   `measure_arm.py` averaged left.webp and right.webp for the arm's depth at every height.
   §4[9] already established the figure's RIGHT side as the unoccluded read for *width*
   (the black pauldron sits on the LEFT); the same occlusion applies to *depth*, and nobody
   had excluded it there. At deltoidWaist, left.webp's "skin" band returns 1–4px slivers
   around the pauldron's edge — not an arm reading — and averaging that against right.webp's
   clean 54px run pulled the measured depth from 0.0714 to 0.0369, roughly half. Fixed:
   shoulder/deltoidWaist depth now reads right.webp only. backArmTop/elbow/fist sit below
   the pauldron and left/right already agreed there, so they're untouched.

Two carried-over todos from the prior handoff turned out to already be closed, checked
directly rather than assumed: **#13** (triangle-budget assertion coverage) — audited all 9
`gate_*.py` files against all 23 Stage 1 parts, every one already has a `§5.4` check. Closed,
no code change needed.

## A visual discrepancy that was investigated and NOT confirmed as a defect

The assembled figure's right-profile render shows a flat, angular wedge in the
deltoid/upper-arm region that doesn't visually resemble the reference's smoother, chunkier
profile silhouette. Two hypotheses were tested and rejected:

- **Not the width/depth asymmetry above** — fixing that (item 4) barely moved the render;
  the wedge is dominated by `backArmTop`/`elbow`/`fist`, whose depth was never averaged with
  the occluded side.
- **Not a left/right camera flip** — tested empirically by scoring `right.webp` against the
  RENDER's `left.png` instead of its own `right.png`: 0.425, worse than the correct pairing's
  0.664. A real flip would have scored better swapped, not worse. Camera wiring is correct.

Left as an open guess-list item rather than force-fixed on an unconfirmed visual impression
(a wrong fix backed by no measurement is worse than an open item — see AGENTS.md's guess-list
discipline). If picked up again: get a proper apples-to-apples scale-matched overlay (crop
both images to their own figure bbox, resize to equal height, place side by side) before
trying anything — eyeballing two differently-scaled renders is what produced the false
flip-hypothesis lead here.

## Rerunnable commands

```bash
S=artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec

# measurement -> landmarks.json (each writes one parts.* block)
python3 $S/measure_landmarks.py        # the base: triage, landmarks, uncertainty
python3 $S/measure_sole.py ; python3 $S/measure_ankle.py ; python3 $S/measure_pant_leg.py
python3 $S/measure_pelvis.py ; python3 $S/measure_chest.py
python3 $S/measure_arm.py ; python3 $S/measure_head.py
python3 $S/measure_neck.py ; python3 $S/measure_waist.py
python3 $S/author_spec.py              # -> object-sculpt-spec.json + build-constants.json
python3 $S/emit_measurements.py        # -> src/utils/cloudStrifeFigure/measurements.ts

# colour -> palette.json (§2's table, sampled by clustering) -> colors.ts
python3 $S/sample_palette.py           # rewrites palette.json if it needs re-sampling
python3 $S/emit_colors.py              # -> src/utils/cloudStrifeFigure/colors.ts

# capture
node tools/capture_parts.mjs --part <name> --out /tmp/<name>
node tools/capture_parts.mjs --assembled --out /tmp/asm --views front,back,left,right
node tools/capture_parts.mjs --gallery --out /tmp/gallery

# gates
python3 $S/gate_assembly.py /tmp/asm/meshes.json
python3 $S/gate_naming.py   /tmp/asm/parts.json
python3 $S/gate_facets.py check /tmp/<name>/meshes.json
python3 $S/gate_arm.py <eight meshes.json — the order is in its docstring>
python3 $S/gate_head.py /tmp/head/meshes.json
python3 $S/gate_pant_leg.py <six> ; python3 $S/gate_pelvis.py <one>
python3 $S/gate_sole.py <two> ; python3 $S/gate_ankle.py <two>
python3 $S/gate_neck.py <one> ; python3 $S/gate_waist.py <one> ; python3 $S/gate_chest.py <one>

# Stage 3's wiring gate — does the right C-xx code sit on the right part
python3 $S/gate_color.py /tmp/asm/meshes.json

# the whole-figure Tier 1 instrument (Phase 0's replacement for the excluded generic gate)
python3 $S/gate_silhouette.py --ref-dir src/assets/exhibits/ff7-cloud-strife-polygon-figure \
  --render /tmp/asm/front.png /tmp/asm/back.png /tmp/asm/left.png /tmp/asm/right.png \
  --view front back left right --mask-above-chin --threshold 0.6

# the comparison sheet — for eyeballing, never a substitute for the gates above
python3 ~/.claude/skills/img2threejs/forge/stage4_review/make_comparison_sheet.py \
  --reference src/assets/exhibits/ff7-cloud-strife-polygon-figure/front.webp \
  --render /tmp/asm/front.png --out /tmp/sheet.png

python3 $S/zoom.py <view> <x0> <y0> <x1> <y1> <scale> /tmp/crop.png   # 6-8x, throwaway
```

⚠ A factory's ONLY number source is the generated
`src/utils/cloudStrifeFigure/measurements.ts`. Never type a number into a `create*.ts`.
Same rule for colour: the only hex source is generated `colors.ts`, via a
`src/utils/cloudStrifeFigure/materials.ts` singleton — never a literal hex in a `create*.ts`.

⚠ A stale capture FAILS the facet gate by design — it carries no `flatShading`. Recapture
after every change rather than reusing a directory.

## The generic img2threejs state machine — deliberately NOT advanced this session

`forge/state.py` / `forge/stage4_review/append_review.py` are the generic pipeline's own
bookkeeping, separate from this project's own gates. Two things block them, both by design,
not oversight:

- `forge/stage4_review/diagnose_render.py` (the generic Tier 1 tool) scores this model badly
  (IoU 0.324, aspect delta 0.575, scale delta 0.612) for the exact reason `gate_silhouette.py`
  exists: it does a naive scale/aspect comparison against a reference that has hair Stage 1
  doesn't have yet, by design. This is the same unfairness Phase 0 already diagnosed and
  fixed once (commit `93a7995`'s wrong exclusion, then `2364fbe`'s real fix) — running the
  generic tool again just reproduces the old, already-solved problem.
- `append_review.py`'s `--action continue` requires `--layer-scores-json` with five forced
  categories, including `materialSurface` and `lightingCamera`. Stage 1 has neither — it is
  a single flat grey material with no lighting design yet. Filling those in would mean
  inventing scores with no measurement behind them, which the project's own rule (AGENTS.md:
  "every number traces to an artefact") forbids.

If a future session wants the generic state machine green too, the honest path is a
`--map-stripped-render` + real per-layer review once Stage 3/4 (colour/material) exist, not
retrofitting fake scores onto Stage 1.

## Open guess-list items

In `landmarks.json` under each `parts.*` block, and in `prompt.txt` §11. The ones that can
still bite:

- the right-profile "wedge" described above — investigated, not confirmed, not force-fixed
- the sole's plan outline (L/W 2.4, toe taper 0.72, end chamfer 0.34 T) — unobservable from
  four orthographic views, falsifiable only by the three-quarter orbit
- where thigh / knee / calf meet — no landmark between the crotch and the boot cuff
- the crotch notch's rise — no view sees under the figure
- the cranium behind the face — hidden in every view; `crownHeight` (this session) is the
  best available proxy (the hair cap-mass boundary), explicitly not a bone measurement
- **the nose**: `right.webp` shows it in relief. §2 c) rules eyes, pupils and brows out as
  printed art, correctly — but the nose is not print, and `parts.head` has nothing for it.
  Belongs to Stage 2 (face/decoration), not a Stage 1 blocker.

## Todo carried over

- ~~**#13** §5.4's triangle-budget assertion wired into some gates, not all.~~ **CLOSED**
  this session — audited, already complete (all 9 gate files × 23 parts).
- **#16** the neck's height — **CLOSED** in `b1d5cf1`, prior to this session (re-measured
  from the exposed skin column instead of comparing two landmarks to themselves).
- ~~**#17** §5.7(d)'s lower reading measures the visible fabric, not the tube.~~ **CLOSED**
  this session — sampled above `bootCuffTopHighest` instead of at `pantHem`.
- **#18 NEW** the compensating silhouette re-check owed by Stage 3's out-of-order colour
  exception (see "Stage 3 (colour)" at the top). Not closeable yet — it only fires once
  Stage 2 or the pauldron adds geometry. Diff against `gate_silhouette.py` mean IoU 0.740
  when that happens; do not skip it because colour already looks done.
