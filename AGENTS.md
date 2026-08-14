# img2three exhibition site — agent instructions

This file is the **single source of truth**. `CLAUDE.md` is a symlink to it; there is no
second copy. Harness-specific detail lives in `docs/agents/`:
[claude](docs/agents/claude.md) | [codex](docs/agents/codex.md) | [opencode](docs/agents/opencode.md)

An exhibition site that rebuilds reference images into pure-code Three.js models with the
img2threejs skill. **One exhibit = one route = one `src/pages/<slug>/index.vue`.** Wiring and
pipeline order per exhibit live in `artifacts/exhibits/<assetDir>/spec/RELATIONSHIPS.md`.

## Work split: the agent does all of it, the user drives advancement

The former standing rule ("dispatch all non-visual work to opencode via `/orchestration`") is
**revoked**.

> **Without an explicit user order, never call `/orchestration`, never launch opencode, never
> spawn subagents to split the work.** No exceptions. "Dispatching would be faster" and "this is
> purely mechanical" are not reasons.

opencode usage is documented in [docs/agents/opencode.md](docs/agents/opencode.md) for when the
user calls for it by hand.

The split still exists — it just moved from agent↔agent to agent↔user:

|                             | What                                                                                                         | Who                                                                                                                                                           |
| --------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Reading**                 | Reading the references, inspecting joints under zoom, writing the guess list                                 | Main agent                                                                                                                                                    |
| **Producing**               | Writing `.ts`/`.py`/`.mjs`/`.json`, running forge scripts and gates, measurement scripts, build/test, wiring | Main agent                                                                                                                                                    |
| **Accepting and advancing** | Judging a render `continue`/`refine-spec`/`refine-code`, choosing the next part, entering the next stage     | **The agent**, on the gates' evidence, recorded in the spec. The user sets direction and intervenes when they want to — they are not a per-part approval step |

Cadence: **rule on the part, report it, start the next one.** When the gates finish, decide
`continue` / `refine-spec` / `refine-code` yourself on the evidence they produced, record it, and
hand over the render, the reference crop side by side at 6–8× NEAREST, and every gate number —
including the ones that failed. Then keep going.

Stop and ask only when the decision changes committed work AND the evidence genuinely does not
settle it AND either reading would waste the work. An ambiguous _reading_ is never that: pick a
default, proceed, and say so. Do not stall.

Never declare a part "passed" that the gates did not pass, and never loosen an assertion to make
one pass. Those are the limits; the approval step is not.

Deliverables are always **files plus a rerunnable command**, never a conclusion in chat.

## Modelling

- Inspect joints at 6–8× NEAREST, point by point. A crop at native resolution does not count as
  having looked. Cut crops at **joints**, not at material boundaries.
- You may not claim "unresolvable" without zooming first. If it is still unresolvable after
  zooming, write "unresolvable after N× zoom" and attach the image.
- Anything the references do not resolve goes on the **guess list** (part / two readings / which
  was chosen / on what evidence). Deliver it in the first reply, and again with the model.
- Never stall when the user is away: pick a default and proceed, saying "I read this as X, it could
  be Y, going with X — tell me to change it."
- Show, don't tell: reference zoom and render side by side.
- **Any change to the 3D model must show up in the 3D preview.** A commit that touches geometry,
  material, socket placement, or assembly code is not done until a fresh capture (or the live
  exhibit page) shows the difference. If a model-code change produces no visible difference in a
  fresh render, that is a signal to stop and check — either the change was a no-op, the capture is
  stale, or the change never reached the code path the preview actually renders. Documentation and
  gate numbers describing a change are not a substitute for the render; get the render first.
- When a reading conflicts with the spec, **follow the spec and say so explicitly**. Do not paper
  over it with "can't tell".
- Acceptance = mechanical gates (assertions, silhouette IoU, part coverage) **plus** a zoomed
  comparison against the original.
- Every number traces to an artefact under `artifacts/`. Never copy from your own summary or from
  another document (`spec/audit_records.py` enforces this).
- **A gate must block the thing you are actually afraid of.** A gate that only measures dimensions
  goes all-green while the model is round. To block "too round" you must measure the distribution
  of angles between adjacent face normals. Pin the threshold with a fake frame (e.g. a smooth
  sphere); never guess it.

### Character parts: decompose first, then sculpt

Humans and characters are always decomposed along action-figure assembly logic. Do not scan
straight to a finished shape:

1. **Decide which parts exist and where the boundaries cut** —
   `grimoire/character/structure_decomposition.md`, the nine-layer taxonomy.
2. **Build the skull and face first**, then the hair that sits on top of it —
   `grimoire/character/head_construction.md`.
3. **Lock the hair topology before touching material** —
   `grimoire/character/stylized_hair_threejs.md` plus `threejs_hair_parameter_contract.json`.
   Material cannot rescue wrong hair-card topology.

Each part is its own file, with its own sockets, passing its own gates. Integration happens only
once all of them pass, and **the integration file may not author any geometry**.

## New model: three prerequisites before calling img2threejs

P0–P2 must be finished before `state.py init`. Skipping any one of them means every later stage is
spent making up for it. Executable script templates are in
[docs/agents/claude.md](docs/agents/claude.md).

### P0 — Reference triage: find out which numbers are untrustworthy

- Extract the silhouette with **corner flood fill AND a whiteness test**:
  `figure = (unreachable by flood fill) AND (255 - min(r,g,b) > tol)`.
  Flood fill alone misclassifies white regions enclosed by the subject (the gap between the legs)
  as subject; a global threshold alone lets compression noise turn the whole frame into subject.
- **Check for clipping**: does the topmost / bottommost / leftmost / rightmost line of each image
  still contain solid pixels? If so the subject is cut off there, that dimension is untrustworthy,
  and that view may not be used to measure it.
- **Check cross-view scale**: the subject's pixel height usually differs between views. Pick an
  alignment anchor made of landmarks that are **complete in every view**, and turn any extreme you
  cannot measure into an extrapolated derived value.
- The real output of this step is a **measurement uncertainty**. Every later IoU / ΔE threshold is
  derived from that residual, not guessed.

### P1 — Decompose, group, and code: this step decides the total workload

- **Groups → parts.** The object-tree naming IS the part table: `partInspector` reads the tree, not
  a registry. A part is the deepest named node; a group is its nearest named ancestor;
  `userData.explodeWithParent` marks a detail. Sub-segments inside a factory stay unnamed —
  one factory = one part.
- **Three orthogonal codes**, all assigned before any geometry is authored:
  - **Shape code S** — geometry identity. The same code shares one geometry (mirroring allowed).
    **Assigned from measured dimensions, never from names**: if two parts measure the same, they
    collapse into one code.
  - **Colour code C** — albedo identity.
  - **Material code M** — surface identity (the roughness / metalness / flatShading family).
- **Symmetry is measured, not assumed.** Run a banded mirror IoU (mirror the silhouette about the
  best-fit axis, compare band by band). For a pure mirror pair, review one side only and cover the
  other with a "negate vertex x and compare point by point" assertion. Claiming by eye that two
  sides differ, without measuring, invents half the workload out of nothing.
- **Share a generator only when ≥2 shapes use it and no extra option is needed to make that
  happen.** A generator that grows options in order to be shared is harder to maintain than writing
  each shape separately.
- **Count the material codes first.** If there are only one or two, do not give them their own
  stage — fold them into the colour stage.

### P2 — Zoom scan

6–8× NEAREST, cut at joints, scanning four things: **angles, joints, colour, material**.
Anything unresolvable goes on the guess list with a default. Details under Modelling above.

## New model: the stages

| Stage  | Output                                                                                                          | Entry condition                    |
| ------ | --------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| **0**  | Reference triage, `landmarks.json`, gate tooling, and the **parts gallery mode on the exhibit page**            | P0–P2 complete                     |
| **1**  | Monochrome structural parts, each passing its own gates, visible in that gallery                                | Stage 0 complete                   |
| **1B** | Monochrome rough assembly: socket placement only, zero geometry in the integration file                         | Every part passed                  |
| **2**  | **Surface geometry that sits on the structure** — face, hair, ears, and decoration (pauldrons, buckles, straps) | 1B silhouette passed               |
| **3**  | Colour applied (the colour codes land), plus material when there are ≤2 material codes                          | **All geometry finished**          |
| **4**  | Material codes applied — **only when there are ≥3**; otherwise folded into 3 and skipped                        | Colour passed ΔE                   |
| **5**  | Full integration and refinement                                                                                 | The colour/material stage complete |
| **6**  | Detail iteration: how to improve the model or the part assembly                                                 | 5 complete                         |

Four hard rules:

1. **All geometry must be finished before any colour.** Decoration is geometry and it changes the
   silhouette. Painting first and adding geometry later means rerunning the silhouette gate and
   possibly re-sampling every colour.
   _The one legitimate exception:_ a decoration part may be deliberately deferred past stage 2 when
   the owner says so — but then **that stage's gate must include a full four-view silhouette
   re-check against the previous stage's IoU**, and the exception must be named in the prompt. An
   exception without the compensating gate is just the bug the rule exists to prevent.
2. **1B's rough assembly may not be deferred to stage 5.** A socket mismatch is the most expensive
   error there is; it must surface while the model is still monochrome and no colour or material
   work has been invested. Stage 5 is **refinement**, not the first assembly.
3. **Stage 1 must be visible on the page.** A stage you cannot see is a stage that is not done —
   and do not add a `.vue` to achieve it; build it as a mode inside the existing exhibit page.
   Check that the page actually surfaces it: `ExhibitStage` only renders the explode control
   `v-if="viewer?.setExplode"`, so a mount helper that does not return `setExplode` silently hides
   it.
4. **A per-model prompt uses these stage numbers.** Do not invent a second numbering and then map
   between them — the map itself becomes a defect surface. If a model needs a stage this table does
   not have, add the row here first.

## New model: collaboration cadence

- **Decide, then keep going. Do not ask for `continue`.** The verdict after a gate run —
  `continue` / `refine-spec` / `refine-code` — is the AGENT's to make and to record, on the
  evidence the gates produced. Report what the numbers say and what you decided, then do the next
  thing.

  This replaces the old "one part per turn, stop and wait" rule, which was written when the
  agent's judgement was the weak link. It is not any more; the weak link now is momentum. Asking
  the user to rule on every part means the planning was not finished, and a run that stops
  twenty-three times costs more than one that stops when something is genuinely undecidable.

  **Stop and ask ONLY when all three hold:** the decision changes work already committed, the
  evidence genuinely does not settle it, and proceeding under either reading would be wasted
  effort. A gate that fails for a reason you can name and fix is not that — fix it. A threshold
  that cannot be pinned with a fake frame IS that — a guessed threshold is worse than none.

  What does not change: never self-certify a part the gates did not pass, never loosen an
  assertion to make one pass, and always report the numbers, including the ones that failed.

- **Scale the correction budget to the part count.**
  `state.py init --max-per-pass 3 --max-total N`, where N ≈ factories × 3 plus headroom for
  integration and the later stages. **Leave per-pass at 3** — if the same part has been corrected
  three times and is still wrong, the reading is wrong, not the code. Go back and look at the
  reference.
- **Sample colour by clustering, never by hand-picked eye-dropper points.** Quantise the subject's
  pixels into clusters, then identify each cluster **by position** (mean y, mean x relative to the
  mirror axis). Point sampling lands on boundaries and returns blended colours.
- **Settle a warm-vs-cool dispute by looking at the neutrals first.** If a neutral grey reads the
  same in both sets, neither is white-balance skewed and the difference is **saturation, not colour
  temperature**. In that case adopt the set whose views cross-validate each other, not the one that
  looks better.

## Adding an exhibit means wiring five places

Miss one and the home page will not show it:

1. `src/pages/<slug>/index.vue` — the exhibit page itself; its first line calls
   `useExhibit("<slug>")`. The route comes from the file location; there is no map to register.
2. An entry in `src/utils/exhibits.ts`.
3. The slug in `src/utils/exhibitSlugs.ts` (`includedRoutes` in `vite.config.ts` reads it; it is an
   allowlist, not a filter, so an unlisted slug is never prerendered).
4. `heroEntries()` in `src/components/home/heroStage.ts`.
5. `content/exhibits/<assetDir>.yml` (velite-managed copy and `images[]`) plus the images and
   `prompt.txt` under `src/assets/exhibits/<assetDir>/`.

Directory rules (Nuxt's `app/` layout, rooted at `src/`):

- `src/pages/` **is the URL surface** — one `.vue`, one route. The plugin only scans `.vue`, but do
  not lean on that to stash things there: one extra `.vue` is one extra junk route.
- `src/composables/` holds reactive access (`useExhibit`); `src/utils/` holds pure functions and
  data (the exhibit registry, the part inspector, geometry factories). Geometry factories live
  there because the home hero and `ultima-v2-harness` also use them; putting them under a page
  directory would make a component import a page.
- **Page assets** (the images listed in `images[]`, `prompt.txt`) go in
  `src/assets/exhibits/<assetDir>/`, flat, with no subdirectories. Vite hashes them and applies
  `base` automatically.
- **Gate evidence** (`spec/`, `brief/`, `.img2threejs/`) goes in `artifacts/exhibits/<assetDir>/`
  and never enters the bundle. Keep only **measurement records and the scripts that produce them**:
  JSON, `.py`/`.sh`/`.mjs`, `.md`.
- **Do not keep renders, zoom comparison sheets, PBR maps, or detail-inventory crops.** All of them
  can be regenerated by the neighbouring `capture_*.sh` / `tools/capture_*.mjs`, and the numbers
  themselves live in JSON. Generate them when you need to compare, then throw them away. The only
  images `artifacts/` keeps are the **irreproducible sources**: the blueprints in `references/` and
  the art crops in `assets/`.
- Images and prompts always go through `src/utils/exhibitAssets.ts`; never open your own
  `import.meta.glob` in a component. Always glob `*/`, never `**/` — `**` eagerly bundles the whole
  gate-evidence tree into the client bundle.
