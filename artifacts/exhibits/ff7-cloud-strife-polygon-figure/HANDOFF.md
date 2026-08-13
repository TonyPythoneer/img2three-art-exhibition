# FF7 Cloud Strife polygon figure — handoff

Updated 2026-08-13, at the end of the turn that authored the sculpt spec and built the
first Stage 1 part. Read this, then `prompt.txt`. Nothing here overrides `prompt.txt`;
where they disagree, the prompt wins and this file is stale.

## Where the run actually is

```bash
cd ~/.claude/skills/img2threejs
ART=/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/ff7-cloud-strife-polygon-figure
python3 forge/state.py status --state $ART/.img2threejs/state.json
```

⚠ **Do NOT run `prompt.txt` §0.1's init block.** That block is for a from-scratch
rebuild. `.img2threejs/state.json` now carries real progress, and
`.img2threejs/state.json.bak` already exists from the previous attempt — the `mv`
recipe would destroy both at once. The state file, not this document and not chat
memory, is the checklist authority (§0.1).

| | steps |
|---|---|
| done | the whole pre-spec chain · spec-authoring · strict-validation · build-current-pass · render-capture · review-contract-read · tier1-diagnostics · multi-angle-review |
| skipped, with reason | projection-route · material-evidence · material-spec-wiring |
| next | **pass-gate-check**, and it currently REFUSES — see below |
| then | ai-review-recorded · pipeline-sync · part-coverage · action-ready |

Correction budget: `loop 0/3`, `total 0/60`. Nothing has been spent.

⚠ `orchestrate_passes.py check --pass-id blockout` returns FAIL: "Tier 1 diagnostics have
not passed for this render". That is the gate working, not a broken command. Tier 1's
silhouette IoU is 0.720 against its 0.85 threshold, for a reason that is about the camera
rather than the model (below). The blockout pass cannot advance until the user rules on
it — and it should not, since 2 of 23 parts exist.

⚠ The spec exists now, so `forge/next.py` takes the positional spec argument. Re-running
`spec/author_spec.py` CLEARS `reviewHistory`; re-record the review afterwards.

## Stage progress against `prompt.txt` §0.7

| stage | state |
|---|---|
| P0 triage / Stage 0 measurement + tooling | **complete** — `spec/landmarks.json`, `spec/facet-gate.json`, `spec/palette.json`, gallery mode on the exhibit page |
| Stage 1 — 23 monochrome parts | **2 of 23 built** (soleL, soleR — one factory, one shape code). The page shows 2/23 |
| Stage 1B / 2 / 3 / 5 / 6 | not started |

Next part in §4's build order is **ankle** (the boot cuff), and nothing about it is
measured yet. Two things are already owed to it:

- its `soleTop` socket carries the FORE-AFT OFFSET of the leg on the foot. The sole is
  centred on its own footprint, so §4[1]'s "extends a long way forward and only slightly
  back" is not expressed anywhere yet. Measure the boot cuff's fore-aft position against
  the sole's span in `left.webp` / `right.webp`.
- §4[2] says the cuff's section is LARGER than the pant tube it swallows. `straightPantTubeWidth`
  is measured; the cuff's own section is not.

## The four entry points

| file | what it is authority for |
|---|---|
| `prompt.txt` | everything: §2 part table, §4 build recipes, §5 gates, §11 guess list |
| `spec/character-contracts.md` | layer assignment per part, why the projection route is refused, why there is no skeleton, which `structure_decomposition.md` checklist items are N/A |
| `spec/landmarks.json` | every measured number, including `parts.sole` |
| `.img2threejs/state.json` | where the run is |
| `spec/object-sculpt-spec.json` | the record: 46 components, 3 materials, 7 passes. **Generated** by `spec/author_spec.py` — edit the script, never the JSON |
| `spec/build-constants.json` | the two number classes landmarks.json does not carry: `derived` (arithmetic on measurements, each with its source) and `authored` (choices: budgets, roughness, review bars) |

## Numbers that gate everything

All from `spec/landmarks.json` and `spec/facet-gate.json` — §0.6 forbids quoting from
prose, so re-read them rather than trusting this table if anything looks off.

| quantity | value | note |
|---|---|---|
| `measurementUncertainty` | 0.05447 | worst landmark `beltTop`; **RMS is only 0.01374** |
| adopted anchor | `sole->chin`, span 0.71637 | both landmarks complete in all five views |
| total height 1.000 | derived, not measured | crown clipped in all four orthographic views (row-0 figure pixels front 6 / back 4 / left 4 / right 6) |
| facet gate | angle **42°**, threshold **0.33571** | pinned with fake frames: smooth sphere 0.0 FAIL, lofted egg 0.10 FAIL; controls 0.571 / 0.600 / 0.571 PASS; separation 0.4714 |
| Stage 1 material | one shared `MANNEQUIN` instance, `0xb0b0b0` | already exported from `parts.ts` — do not `new` per part |

Stage 0's self-checks, carried forward unresolved:

- **A `hipWiderThanShoulderLine` FAILS** by 0.0965 (hip 0.28325 vs shoulder 0.37978).
  A1 `hipWiderThanChestSlab` PASSES by 0.0851. So §4[6]'s "wider than the shoulders"
  holds against the **chest slab**, not against the shoulder line. Recorded as a prompt
  disagreement in `landmarks.json.promptDisagreements`; §0.6 says the script wins.
- A2 (hip deeper than shoulders) and C (torso is a slab) are **INDETERMINATE** — they
  fail or pass by less than `measurementUncertainty`, which is not a verdict.
- B (hip kite) is INDETERMINATE in both profile views: the glove occludes the hip
  outline.

## sole — built, gated, waiting on the user

`spec/landmarks.json` → `parts.sole`, produced by `spec/measure_sole.py`.

| | value | cross-view spread |
|---|---|---|
| lateral extent A (model X) | 0.19814 | 0.00294 |
| fore-aft extent B (model Z) | 0.19674 | 0.01890 |
| thickness T (model Y) | 0.05556 | 0.02365 |
| splay, derived | 45.3812° | prior `poseAngles.footSplayDeg` 47.158 / 44.406 |
| plan trapezoid | heel 0.09717 / toe 0.06996 / length 0.23320 / end chamfer 0.01889 | |

`crossViewCheck` verdict **PASS** (worst 0.02365 < 0.05447).

Rerun the whole thing with:

```bash
node tools/capture_parts.mjs --part soleL --out /tmp/soleL      # renders + meshes.json
node tools/capture_parts.mjs --part soleR --out /tmp/soleR
python3 spec/gate_sole.py /tmp/soleL/meshes.json /tmp/soleR/meshes.json
python3 spec/gate_facets.py check /tmp/soleL/meshes.json
```

Four things worth not re-learning:

1. **The plan solve has to include the chamfer it emits.** The first version inverted the
   2×2 for a SHARP-cornered trapezoid and then cut 0.34 T off exactly the two corners the
   bounding box is attained at, so the built slab came out 17% short of A and B. Every
   orthographic gate would have read that as a modelling error. `plan_extents()` now
   builds the same eight-point outline the factory does, `solve_plan()` bisects against
   it, and `parts.sole.planCheck` carries both residuals (0.0 and 2.8e-17).
2. **A taper measured in the FIGURE frame is measuring the pose.** At 45° of splay the
   x-extent of a z-band is dominated by the slab's diagonal. `gate_sole.foot_local()`
   un-rotates first; only then does "wide at the heel, narrow at the toe" mean the
   trapezoid. (The figure-frame version gave the right verdict for the wrong reason —
   worse than a failure, because it looks like evidence.)

3. **Thickness cannot be read as "ground row → ledge row".** The product shot is very
   slightly elevated, so the ground-contact outline itself spreads over dozens of rows:
   in `left.webp` the silhouette width climbs to 160 px at row 806 and then tapers to
   6 px at row 845, and those last 37 rows are the plate's near corner opening up, not
   37 rows of plate edge. Measuring the band height that way spread the four views by
   several times the uncertainty; that instrument was retired and nothing writes its
   numbers any more, which is why they are not quoted here (`spec/audit_records.py`
   fails on a figure no artefact produces). The working instrument is the contiguous
   vertical run at the plate's **far tip**, where the plate is alone in the column and
   its own depth is ~0 — `parts.sole.raw.<view>.thickness` in `landmarks.json`.
4. **`poseAngles.footSplayDeg` is not a splay angle.** It is `atan2(lateral, foreAft)`,
   the bounding box's diagonal. Only a zero-width foot makes those equal; a real one is
   always pulled toward 45°, so the true splay is further from 45° than that number.
   The factory must read `parts.sole.splayDeg.derived`.

## Guess list

`prompt.txt` §11 holds five items; all five stay on default reading A. Two got new
evidence in Stage 0:

- **§11.4 does the hair cap cover the ears** → `back.webp` at 5–6× supports reading A:
  a pink skin wedge is exposed left and right below the cap edge, so the ears are
  outside the cap. Same crop confirms §7.3's occipital V fold and the central seam.
- **§11.5 occipital hair thickness** → not one value: left 33 px / right 54 px
  (normalized 0.03863 / 0.07137), and what it measures is **fringe depth, not cap shell
  thickness**. Insetting `back.webp` by it to get the skull would overshoot.

Three added in Stage 0:

1. **`bootCuffTop` is not a single landmark.** The feet splay, so in profile the near
   and far boot openings differ by ~38 px. `pantHem` is the cross-view anchor now; the
   old value survives as `bootCuffTopHighest`.
2. **`hipYokeVTip` is not measurable by colour.** Shirt purple and pants purple differ
   by 0.007 in cluster mean y — statistically inseparable. Only a spatial boundary can
   find it, so it is absent from `landmarks.json`.
3. **`measurementUncertainty` is too loose as a per-part shape tolerance.** 0.05447 is
   about 43 px of `front.webp`, while the reference's own two-segment fit residual is
   4.7 px. Taking §5.7 literally would make that gate vacuous. Use RMS (0.01374) or the
   reference's own residual for part-shape assertions, and keep 0.05447 only for
   cross-view landmark agreement.

Three added with the sole, all in `parts.sole.adopted`:

4. **Plan outline is unobservable from four orthographic views.** A, B, T are
   recoverable; L, W and θ are 2 equations in 3 unknowns, and at θ≈45° the 2×2 system is
   singular (det = −cos 2θ). Adopted **L/W = 2.4**.
5. **Toe taper 0.72** — §4[1] says "wide at the heel, narrow at the toe" but no view
   measures how much.
6. **End chamfer = 0.34 × thickness** — read off `front.webp` x5..165 y700..821 at 8×,
   where the corner cut reads as its own facet.

⚠ Items 4–6 are falsifiable **only by §5.2's three-quarter orbit render**. A, B and T
alone fix all four orthographic silhouettes, so every (L, W, θ) satisfying them scores
identically on the orthographic IoU. Do not report the orthographic gate as
confirmation of the plan shape.

## Tooling that exists

- `spec/measure_landmarks.py` → `landmarks.json` · `spec/measure_sole.py` → `parts.sole`
- `spec/gate_facets.py` → `facet-gate.json` (threshold pinned with fake frames), and
  `gate_facets.py check <meshes.json>` for a built part
- `spec/sample_palette.py` → `palette.json` · `spec/fill_assessment.py` → `assessment.json`
- `spec/refmask.py` (silhouette: flood fill **AND** whiteness, tol 18) ·
  `spec/probe_references.py` (triage + banded mirror IoU) · `spec/zoom.py` (throwaway crops)
- `spec/audit_records.py` — §3.5's §0.6 enforcement. It masks three things that carry
  digits without being measurements (JSON `\uXXXX` escapes, `§N.M` references, ISO dates)
  and treats the spec's own `tier1Results` / `reviewHistory` as sources, because a forge
  script wrote them
- **new** `spec/author_spec.py` → `object-sculpt-spec.json` + `build-constants.json`
- **new** `spec/emit_measurements.py` → `src/utils/cloudStrifeFigure/measurements.ts`.
  This is how §3.1's "a factory reads only from landmarks.json" and AGENTS.md's "gate
  evidence never enters the bundle" hold at once: the numbers are COPIED by a script, so
  no one types one
- **new** `spec/gate_sole.py` — the sole's 13 assertions (§5.4/§5.5/§5.10/§4[1])
- **new** `spec/tight_crop.py` — trims reference and render to their own subject bbox so
  §5.1's IoU measures the shape instead of the framing
- **new** `tools/capture_parts.mjs` — per-part renders + `meshes.json` + `parts.json`
- `src/utils/mountCloudStrifeViewer.ts` — `assembled` / `gallery` modes, single-part +
  fixed-view mode, `window.__renderReady` / `__partInfo` / `__partMeshes` headless
  contract, and `setExplode` forwarded unconditionally so §5.9 is testable
- `src/utils/cloudStrifeFigure/parts.ts` — `MANNEQUIN` material + `STAGE1_PARTS`

Three viewer details that cost a debugging round each, all now fixed in code:

- the **arcball gizmo draws into the WebGL frame**. On a fixed review camera it must be
  turned off, or every silhouette gate reads two faint full-width lines as subject.
- a part rendered alone still needs its §2 **group node**, or `partInspector` reports
  `module: null` and §5.6 cannot be checked in the harness the review runs in.
- the gallery's layout holder is named for the part's **module**, not `<part>Slot`, for
  the same reason.

## Open for the user, in the order they will bite

1. **Tier 1's silhouette IoU on an isolated part is a camera comparison, not a shape
   one.** soleL scores 0.720 against a 0.85 threshold while its aspect and scale deltas
   are both 0.0045 and its three measured extents reproduce exactly. The reference is an
   elevated product shot whose silhouette includes the sole's top face; an orthographic
   front elevation cannot show that face at all.
   `grimoire/review/self_correction.md` documents this failure mode by name
   ("photo-vs-procedural ... dominated by framing + background + scale + lighting, NOT
   fidelity") and says not to optimise toward it. The options are: accept it as a
   documented limitation for every Stage 1 part, or solve a review camera with the
   product shot's elevation once and use it for all 23. **This is a user call**, and
   `orchestrate_passes.py check` stays FAIL until it is made.
2. **The pants segmentation does not survive its own measurement.** front.webp puts the
   pant-leg crease at row 604 and the crotch-notch apex at row 605 — one pixel apart — so
   §4[5]'s thigh segment has no height to occupy (back.webp gives it 0.018, still inside
   the RMS). Either the crease is being found at the crotch or the four-segment split is
   wrong. It does not touch sole / ankle / calf, and it must be re-measured before thigh
   is authored. Recorded in the spec's `risks`.
3. **Where the leg stands on the foot is still unexpressed.** See the ankle note at the
   top: the offset belongs in ankle's `soleTop` socket vector.

Also open, but deliberately: `heroEntries()` in `src/components/home/heroStage.ts` has
no entry for this exhibit. It needs a `build()` returning a finished model, and none
exists until Stage 1B, so it is a §6.4 task. Do not stub it with a placeholder.

## The cadence rule, restated because it is the one most often broken

**One part per turn.** When §5's gates finish, stop and hand over: the part's render,
its orbit renders, the reference crop and render side by side at 6–8× NEAREST, and every
gate's number marked PASS or FAIL. Then wait for the user to say
`continue` / `refine-spec` / `refine-code`. Never two parts back to back, never
self-certify a part, never enter the next stage on your own. `--action` on
`append_review.py` is the agent's recorded reading, not permission to proceed.

No dispatch: no `/orchestration`, no opencode, no subagents, without an explicit user
order.

## Open dispatch — neck + waist, on opencode, supervised BY THE USER

The user ordered the dispatch (which is what AGENTS.md's "never dispatch without an
explicit user order" exception requires) and then took over supervision. **The
coordinator is not waiting on this one.** A silent dispatch is not a dead dispatch.

| | |
|---|---|
| run | `run_ef27de43353c` |
| task | `task_cf8bf94971bb` |
| dispatch | `ctx_caaad8919773` |
| worker terminal | `term_51f68514-6c80-4374-a0ae-1156eeb06e4d` |
| worktree | **current** (the main one) — not a child |
| agent | opencode, model `opencode/mimo-v2.5-free` from the repo's `opencode.json` |

⚠ `worker-start --model` is rejected for opencode ("does not support launch-time model
selection"). The model comes from `opencode.json` at the repo root, which is why that
file stopped being gitignored. **Editing it changes what a dispatched worker runs.**

```bash
orca orchestration worker-show --dispatch ctx_caaad8919773 --json
orca orchestration worker-read --dispatch ctx_caaad8919773 --limit 50 --json
orca orchestration check --wait --types worker_done,escalation,question --timeout-ms 900000 --json
# only after a settled worker_done or escalation — never on a timeout or an idle TUI:
orca orchestration worker-release --dispatch ctx_caaad8919773 --json
```

### Why these two parts, and why now

neck (§4[13], S-14) and waist (§4[7], S-07) are the only two remaining Stage 1 parts with
**no shared-section chain and no unresolved contradiction**. Everything else is blocked on
something:

| not dispatched | blocked on |
|---|---|
| thigh / knee / calf | §5.7 fits crotch→cuff as ONE polyline; that fit cannot be produced from inside a segment. One owner must measure the whole line first |
| the four arm factories | the §1.4-vs-§1.5 mirror contradiction below |
| pelvis | self-check A FAILS by 0.0965 — see "Open for the user" |
| chest | emits four sockets; it is the hub of the whole ledger |
| head | `faceGroups` five-way triangle partition + a skull inset whose hair thickness is known to overshoot. **The previous attempt came out all-green and egg-shaped.** |

It is also an experiment, not just a build: three gates landed this session that did not
exist when the ankle was dispatched — socket shape, flatShading, and mirror — and each is
proven to fail on the exact defect it names. This dispatch is where we find out whether
they hold against a worker that has already produced three defects in one part.

### What to check before believing the result

- `git status` — the brief forbids commits, so the work must be an unstaged working tree.
- `spec/facet-gate.json` unchanged: angle 42.0, threshold 0.3357142857142857.
- **No existing gate was loosened.** `git diff spec/gate_*.py spec/socket_gate.py` should
  show additions for the two new parts and nothing subtracted from sole/ankle. A worker
  that makes its own part pass by weakening a shared assertion is the worst outcome here.
- `landmarks.json` gained `parts.neck` and `parts.waist` and nothing else changed.
- `.img2threejs/state.json` and its `.bak` intact.
- No renders anywhere under `artifacts/`.

### The one thing planted in the brief

The brief tells the worker that the ledger puts `neckTop` (0.716369, the chin) and
`chestTop` (0.706208, the shoulder line) about **0.0102** of figure height apart — a very
short neck — and then requires it to measure the exposed column itself and say whether it
agrees. The number may well be right; the head sits low and most of the neck is hidden.

It is the one place in this dispatch where copying the quoted number passes and only
measuring finds out. **How the worker handles that line is worth more than how many parts
it ships.**
