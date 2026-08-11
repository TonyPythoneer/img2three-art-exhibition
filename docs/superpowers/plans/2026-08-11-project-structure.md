# Project Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Get every non-code file out of `src/exhibits/<slug>/` so that directory holds only `.ts` and `.vue`, without moving exhibits into `src/pages/` and without migrating to Nuxt.

**Architecture:** Three-way split by _what a file is for_, not by which exhibit owns it. Page assets (the images the exhibit page renders, plus `prompt.txt`) go to `src/assets/exhibits/<slug>/` where Vite hashes them and applies `base` for free. Pipeline gate evidence (`spec/`, `brief/`, `.img2threejs/`, PBR maps, detail-inventory crops) goes to `artifacts/exhibits/<slug>/`, outside the bundle entirely. Code stays put.

**Tech Stack:** Vite 8 + `vite-plus` + vue-router 5 (built-in file routing via `vue-router/vite`) + `vite-ssg` 28 + velite 0.4 + Tailwind 4 + three.js 0.185. Node >=24 <25, pnpm 11.9.0.

---

## Findings — read this before executing

This plan answers two questions the user asked. Both answers are "no", with evidence. If you are here to execute, the tasks start at [Global Constraints](#global-constraints); read this section anyway so you do not "helpfully" reintroduce a rejected idea.

### Q1: Can exhibits move into `src/pages/`? — Technically yes, but don't.

`vite.config.ts:17` configures `VueRouter({ routesFolder: "src/pages", dts: "typed-router.d.ts" })`. In vue-router 5 that plugin is the absorbed unplugin-vue-router (`node_modules/vue-router/dist/unplugin/vite.mjs`).

Verified against the shipped type definitions in `node_modules/vue-router/dist/options-P-0BPDru.d.mts`:

| Option         | Default                                | Consequence                                                                                                       |
| -------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `extensions`   | `['.vue']`                             | Only `.vue` files become routes. **A `.ts` file inside `src/pages/` is never scanned and never becomes a route.** |
| `filePatterns` | `['**/*']`, combined with `extensions` | Scan glob resolves to `**/*.vue`.                                                                                 |
| `exclude`      | `[]`                                   | Array of picomatch globs, relative to cwd, e.g. `['src/pages/ignored/**']`.                                       |
| `routesFolder` | `"src/pages"`                          | Accepts an array of `{ src, path, filePatterns, exclude, extensions }` objects.                                   |

Confirmed empirically by `typed-router.d.ts`: `src/pages/` currently holds exactly four `.vue` files and the generated route map has exactly four routes — `/`, `/[slug]`, `/ff7-menu`, `/ultima-v2-harness`. One `.vue` in, one route out, no exceptions.

So the mechanical answer is: moving `createUltimaWeaponV2Model.ts` into `src/pages/` would be harmless (never scanned), and moving `UltimaV2Stage.vue` into `src/pages/` would silently create a junk route at `/UltimaV2Stage`.

**Reject it anyway, for three reasons:**

1. `src/pages/` in this stack _is_ the URL surface. There is one route per file, and the exhibits do not have one route each — all exhibits share a single dynamic route, `src/pages/[slug].vue`. Exhibits are not pages. Putting a 137 KB geometry factory next to the route table makes the URL surface unreadable for zero routing benefit.
2. The mitigation (`exclude: ['src/pages/**/_*.vue']` or a `.page.vue` extension convention) is a rule in `vite.config.ts` governing files far away from it. This codebase has already been bitten by exactly that shape — see the comment at `src/exhibits/cloud-ultima-weapon-v2/UltimaV2Stage.vue:120-123` about a duplicated `LightingMode` union: "miss one and the button type-checks fine and does nothing".
3. It does not solve the stated problem. The user's actual complaint is that non-`.vue` resources sit in a pages-adjacent directory. Moving _more_ things into `src/pages/` makes that worse.

**The supported alternative, if per-exhibit routes are ever wanted.** `routesFolder` takes an array, and the plugin's own documentation (same `.d.mts`, lines 2545-2555) ships this exact example:

```js
routesFolder: [
  { src: "src/pages" },
  {
    src: "src/exhibits",
    filePatterns: "*/pages/**",
    path: (file) => {
      const prefix = "src/exhibits";
      return file.slice(file.lastIndexOf(prefix) + prefix.length + 1).replace("/pages", "");
    },
  },
];
```

This is real and documented. It is **not** part of this plan: it would create a second source of truth for routes alongside `exhibitSlugs` in `src/exhibits/slugs.ts`, which `vite.config.ts:7` imports to build the SSG allowlist. Do not add it without deciding which of the two owns the route list.

### Q2: Nuxt directory conventions — the repo already matches, where they apply.

Nuxt 4's layout (verified against nuxt.com/docs/4.x, `srcDir` defaults to `app/` in Nuxt 4, was root in Nuxt 3):

```
app/  assets/ components/ composables/ layouts/ middleware/ pages/ plugins/ utils/ app.vue
content/  layers/  modules/  public/  server/  shared/  nuxt.config.ts
```

Mapped one by one:

| Nuxt                                                                           | This repo                                                                | Verdict                                                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app/` (srcDir)                                                                | `src/`                                                                   | **Skip.** `app/` is a Nuxt-4-only default that exists to keep file watchers off root folders. Outside Nuxt it buys nothing; `src/` is the Vite convention. Renaming touches `vite.config.ts` alias, `tsconfig.json` paths, and every `~/` import for a cosmetic win. |
| `app/app.vue`                                                                  | `src/RootApp.vue`                                                        | Cosmetic rename. Not worth a commit on its own.                                                                                                                                                                                                                      |
| `app/assets/`                                                                  | `src/assets/`                                                            | ✅ already matches                                                                                                                                                                                                                                                   |
| `app/components/`                                                              | `src/components/`                                                        | ✅ already matches                                                                                                                                                                                                                                                   |
| `app/pages/`                                                                   | `src/pages/`                                                             | ✅ already matches                                                                                                                                                                                                                                                   |
| `content/`                                                                     | `content/exhibits/*.yml`                                                 | ✅ already matches (velite)                                                                                                                                                                                                                                          |
| `public/`                                                                      | `public/assets/`                                                         | ✅ already matches                                                                                                                                                                                                                                                   |
| `app/composables/`                                                             | none exist                                                               | Creating an empty directory to look like Nuxt is cargo cult. Add it when there is a second composable.                                                                                                                                                               |
| `app/layouts/`                                                                 | none — `RootApp.vue:30,34` hardcodes `FF7_ROUTES` / `SHOWCASE_ROUTES`    | **The one real gap.** See Task 4 (optional).                                                                                                                                                                                                                         |
| `app/utils/`                                                                   | `src/site.ts`, `src/exhibits/status.ts`, `src/exhibits/partInspector.ts` | Partially applicable, but these are domain-scoped and already colocated with what uses them. Moving them to a flat `utils/` would split things that change together.                                                                                                 |
| `app/middleware/`, `app/plugins/`, `server/`, `shared/`, `modules/`, `layers/` | none                                                                     | N/A for a static gallery with no navigation guards and no server.                                                                                                                                                                                                    |

**`src/exhibits/` has no Nuxt equivalent, and that is fine.** Nuxt has no domain-folder convention; the nearest thing is a Nuxt _layer_ (`layers/<name>/` with its own `components/` and `pages/`), which is a Nuxt-only feature. Outside Nuxt, a domain folder is the correct call and matches the "files that change together live together" rule.

Net: adopting Nuxt conventions is a no-op for this repo except for `layouts/`, which is Task 4.

### Q3: Migrate to real Nuxt? — No.

Feasibility is not the problem; it would work. `nuxt generate` prerenders to static HTML, GitHub Pages serves it, `app.baseURL` replaces `base: "/img2three-art-exhibition/"`, and the strict route allowlist survives as `nitro.prerender.crawlLinks: false` plus an explicit `routes: [...]` (verified against nuxt.com/docs/4.x/getting-started/prerendering).

The problem is cost against benefit:

**What it costs**

- `vite-plus` goes away: `vp dev`, `vp preview`, `vp check --fix`, and the `staged` pre-commit hook wired at `vite.config.ts:32-34`. `package.json:prepare` runs `vp config` to install it. All of that is replaced by whatever you pick instead.
- `vite-ssg` goes away, and with it `ssgOptions.includedRoutes` — the deliberate allowlist commented at `vite.config.ts:42` as "An allowlist, not a filter, so a new page is never prerendered by accident". Nuxt's equivalent works, but it is a different mechanism to re-tune and re-verify.
- velite: `@velite/plugin-vite` can be pushed into `vite.plugins` inside `nuxt.config.ts`, or replaced by `@nuxt/content`. Content is the native answer and is a rewrite — the yml schema in `velite.config.ts` plus the `veliteFields()` merge at `src/exhibits/index.ts:52-65`.
- The crash-loop workaround documented at `src/exhibits/index.ts:1-10` and `src/exhibits/slugs.ts:1-7` (keeping `.velite/*` out of the config's import graph) is specific to vite-plus's config watcher. In Nuxt the hazard changes shape and would need re-deriving from scratch.
- `typed-router.d.ts` is replaced by Nuxt's own typed routes.

**What it buys**

- `layouts/` — obtainable for ~20 lines without Nuxt (Task 4).
- Auto-imports — a convenience at scale; this repo has 4 routes.
- `<ClientOnly>` / `.client.vue` for three.js SSR safety — already solved by the dynamic `import()` inside each `mount()`, which `src/components/stage/ExhibitStage.vue:173-177` documents.
- Nuxt Content, Nuxt Image — not currently needed.

**Recommendation: do not migrate.** Nuxt's value concentrates in server routes, data fetching, middleware, and auto-imports at scale. This site uses none of them. The migration would rewrite a working content pipeline and a deliberately tuned SSG allowlist to gain a feature Task 4 delivers for a fraction of the cost.

### Premise corrections found during review

Four things in the brief this plan was written from were wrong or stale. They are corrected here; the tasks below reflect the corrected state.

1. **`src/pages/ultima-fable-harness.vue` does not exist.** `ls src/pages/` returns exactly `[slug].vue`, `ff7-menu.vue`, `index.vue`, `ultima-v2-harness.vue`, and `typed-router.d.ts` agrees. Its deletion is staged.
2. **The fable and codex-sol exhibits are already deleted.** `git status` shows 231 staged deletions covering `src/exhibits/cloud-ultima-weapon-fable/`, `src/exhibits/cloud-ultima-weapon-codex-sol/`, `artifacts/codex-sol/`, `artifacts/ultima-fable/`, `.img2threejs/cloud-ultima-weapon-{fable,codex-sol}/`, and both `tests/codex-sol-*.test.mjs`.
3. **There are two exhibits now, not four**: `cloud-ultima-weapon-v2` and `cloud-strife-polygon-figure`. The "four parallel move sessions" framing no longer applies; it is two.
4. **The surviving tests do not reference the deleted exhibits.** `tests/ultima-v2-solid.test.mjs:24` and `tests/v2-sidebar.test.mjs:49` both point at `src/exhibits/cloud-ultima-weapon-v2/` code files, which this plan does not move. No test changes are required.

Baseline confirmed green before planning: `pnpm typecheck` exits clean on the current working tree.

### Bug found while reviewing, fixed in Task 3

`src/components/home/HeroStage.vue:32` builds its lookup key from `slug`, not `assetDir`:

```js
return file ? (imageUrls[`../../exhibits/${slug}/${file}`] ?? "") : "";
```

The v2 exhibit has `slug: "ff7-cloud-ultima-weapon"` but `assetDir: "cloud-ultima-weapon-v2"` (`src/exhibits/index.ts:69-70`), so this key never resolves and the hero turntable's reference photo is silently blank. `ExhibitGrid.vue:65` gets this right; `HeroStage.vue` was missed. Task 3 fixes it while rewriting the same line.

---

## Global Constraints

- Node `>=24 <25`, pnpm `11.9.0`. Do not change `package.json` engines.
- `base: "/img2three-art-exhibition/"` in `vite.config.ts:14` is load-bearing — a GitHub _project_ page. Do not touch it.
- **`vite.config.ts`'s import graph must never reach `.velite/*`.** It imports `./src/exhibits/slugs.js` only. Adding an import that transitively pulls `.velite/index.js` forces a config reload that races velite's delete-then-write into a crash loop. Rationale is in the header comment of `src/exhibits/index.ts`.
- Page assets go under `src/assets/` so Vite hashes them and applies `base` automatically. **`public/` is rejected** — it would need `import.meta.env.BASE_URL` stitched on by hand at every use site, and filenames lose their content hash. The reason is recorded at `src/components/home/ExhibitGrid.vue:56-57`; do not undo it.
- `import.meta.glob` patterns stay **shallow** (`*/`, never `**/`). A `**` under an exhibit directory would eagerly bundle every detail-inventory zone crop and PBR map — hundreds of files of gate evidence — into the client bundle.
- Use the array-of-patterns form for `import.meta.glob`, not brace expansion. The array form is already proven in this codebase.
- Do not move any `.ts` or `.vue` file out of `src/exhibits/<slug>/`.
- Never run `git mv` from two workers at once on this repo; concurrent workers contend on `.git/index.lock`. Use plain `mv` and let a later `git add -A` record the renames.

---

## File Structure

**Created:**

- `src/assets/exhibits/cloud-ultima-weapon-v2/` — the two reference PNGs the exhibit page renders, plus `prompt.txt`
- `src/assets/exhibits/cloud-strife-polygon-figure/` — the five reference WebPs, plus `prompt.txt`
- `artifacts/exhibits/cloud-ultima-weapon-v2/` — `spec/`, `brief/`, `references/`, `assets/`
- `artifacts/exhibits/cloud-strife-polygon-figure/` — `spec/`, `.img2threejs/`, `RUNBOOK.md`

**Modified:**

- `content/exhibits/cloud-strife-polygon-figure.yml` — `images[].file` loses its `references/` prefix
- `src/pages/[slug].vue:76-90,107,116` — two globs and two lookup keys repoint to `../assets/exhibits/`
- `src/components/home/ExhibitGrid.vue:56-67` — glob and lookup key repoint; comment simplifies
- `src/components/home/HeroStage.vue:24-33` — glob repoints, **and the `slug` vs `assetDir` bug is fixed**
- `CLAUDE.md` — the "新增展品要接四個地方" section, which currently says assets live at the exhibit root
- `src/exhibits/cloud-strife-polygon-figure/spec/object-sculpt-spec.json` — `sourceImage` paths
- `artifacts/exhibits/cloud-strife-polygon-figure/RUNBOOK.md` — the `/img2threejs <path>` commands

**Unchanged, deliberately:**

- `vite.config.ts` — no routing or base changes in this plan
- `src/exhibits/slugs.ts`, `src/exhibits/index.ts` — `assetDir` keeps its meaning, now naming a folder under `src/assets/exhibits/`
- `tests/*.mjs` — they reference only code files, which do not move

**Ownership and concurrency.** Tasks 1 and 2 touch only their own exhibit's files plus that exhibit's own velite yml — disjoint, safe to run in parallel. Task 3 owns every shared file (the three glob sites, `CLAUDE.md`) and **must run alone, after both moves land**. Task 4 is independent of all of them and optional.

---

### Task 1: Move cloud-ultima-weapon-v2's non-code files

**Files:**

- Move: `src/exhibits/cloud-ultima-weapon-v2/{reference-authority-sheet.png,reference-artwork-crop.png,prompt.txt}` → `src/assets/exhibits/cloud-ultima-weapon-v2/`
- Move: `src/exhibits/cloud-ultima-weapon-v2/{spec,brief,references,assets}/` → `artifacts/exhibits/cloud-ultima-weapon-v2/`
- Verify: `content/exhibits/cloud-ultima-weapon-v2.yml` (expected to need **no** change)

**Interfaces:**

- Produces: two page assets reachable at `src/assets/exhibits/cloud-ultima-weapon-v2/reference-authority-sheet.png` and `.../reference-artwork-crop.png`, and a prompt at `.../prompt.txt`. Task 3's globs depend on these exact paths.

- [ ] **Step 1: Record the before-count so the after-count can be checked**

```bash
find src/exhibits/cloud-ultima-weapon-v2 -type f ! -name '*.ts' ! -name '*.vue' | wc -l
```

Expected: `161`

- [ ] **Step 2: Create both destinations**

```bash
mkdir -p src/assets/exhibits/cloud-ultima-weapon-v2
mkdir -p artifacts/exhibits/cloud-ultima-weapon-v2
```

- [ ] **Step 3: Move the three page assets**

```bash
cd src/exhibits/cloud-ultima-weapon-v2
mv reference-authority-sheet.png reference-artwork-crop.png prompt.txt \
   ../../assets/exhibits/cloud-ultima-weapon-v2/
cd -
```

- [ ] **Step 4: Move the four evidence directories**

```bash
cd src/exhibits/cloud-ultima-weapon-v2
mv spec brief references assets ../../../artifacts/exhibits/cloud-ultima-weapon-v2/
cd -
```

- [ ] **Step 5: Verify nothing is left but code, and the counts balance**

```bash
ls src/exhibits/cloud-ultima-weapon-v2/
find src/assets/exhibits/cloud-ultima-weapon-v2 artifacts/exhibits/cloud-ultima-weapon-v2 -type f | wc -l
```

Expected from `ls`, exactly these four and nothing else:

```
UltimaV2Stage.vue
createUltimaWeaponV2LookDev.ts
createUltimaWeaponV2Model.ts
mountV2Viewer.ts
```

Expected from the count: `161`. If it differs, stop and report — a file was dropped or double-counted.

- [ ] **Step 6: Confirm the velite yml needs no edit**

```bash
grep 'file:' content/exhibits/cloud-ultima-weapon-v2.yml
```

Expected — both already flat filenames, no `references/` prefix, so no change is needed:

```
  - file: reference-authority-sheet.png
  - file: reference-artwork-crop.png
```

If either line has a directory prefix, strip it to the bare filename and note the deviation.

- [ ] **Step 7: Commit**

```bash
git add -A src/exhibits/cloud-ultima-weapon-v2 src/assets/exhibits artifacts/exhibits
git commit -m "refactor(v2): split exhibit assets from gate evidence"
```

---

### Task 2: Move cloud-strife-polygon-figure's non-code files

**Files:**

- Move: `src/exhibits/cloud-strife-polygon-figure/references/*.webp` → `src/assets/exhibits/cloud-strife-polygon-figure/` (**flattened** — the `references/` level is dropped)
- Move: `src/exhibits/cloud-strife-polygon-figure/prompt.txt` → `src/assets/exhibits/cloud-strife-polygon-figure/`
- Move: `src/exhibits/cloud-strife-polygon-figure/{spec,.img2threejs}/`, `RUNBOOK.md` → `artifacts/exhibits/cloud-strife-polygon-figure/`
- Modify: `content/exhibits/cloud-strife-polygon-figure.yml`
- Modify: `artifacts/exhibits/cloud-strife-polygon-figure/RUNBOOK.md`
- Modify: `artifacts/exhibits/cloud-strife-polygon-figure/spec/object-sculpt-spec.json`

**Interfaces:**

- Produces: five page assets at `src/assets/exhibits/cloud-strife-polygon-figure/{front,back,left,right,more-angle}.webp` and a prompt at `.../prompt.txt`. Task 3's globs depend on these exact flattened paths.

Flattening is deliberate: it collapses Task 3's glob from two patterns to one and lets the special-case comment at `src/pages/[slug].vue:76-79` be deleted.

- [ ] **Step 1: Record the before-count**

```bash
find src/exhibits/cloud-strife-polygon-figure -type f ! -name '*.ts' ! -name '*.vue' | wc -l
```

Expected: `114`

- [ ] **Step 2: Create both destinations**

```bash
mkdir -p src/assets/exhibits/cloud-strife-polygon-figure
mkdir -p artifacts/exhibits/cloud-strife-polygon-figure
```

- [ ] **Step 3: Move the five reference images, flattening `references/` away**

```bash
cd src/exhibits/cloud-strife-polygon-figure
mv references/*.webp ../../assets/exhibits/cloud-strife-polygon-figure/
rmdir references
mv prompt.txt ../../assets/exhibits/cloud-strife-polygon-figure/
cd -
```

`rmdir` (not `rm -rf`) is intentional: it fails loudly if the directory still holds something the move missed.

- [ ] **Step 4: Move the evidence**

```bash
cd src/exhibits/cloud-strife-polygon-figure
mv spec .img2threejs RUNBOOK.md ../../../artifacts/exhibits/cloud-strife-polygon-figure/
cd -
```

- [ ] **Step 5: Verify nothing is left but code, and the counts balance**

```bash
ls -a src/exhibits/cloud-strife-polygon-figure/
find src/assets/exhibits/cloud-strife-polygon-figure artifacts/exhibits/cloud-strife-polygon-figure -type f | wc -l
```

Expected from `ls -a`: `.`, `..`, and `CloudStrifeStage.vue` — nothing else.
Expected from the count: `114`. If it differs, stop and report.

- [ ] **Step 6: Strip the `references/` prefix from the velite yml**

Edit `content/exhibits/cloud-strife-polygon-figure.yml`. Five `file:` lines change:

```yaml
images:
  - file: front.webp
    caption: >-
      The proportion authority. Every normalized landmark in the spec — sole
      plane at 0.000 up to the tallest hair spike at 1.000 — is measured here
  - file: back.webp
    caption: >-
      The hair cap's radial facet fan and the diagonal strap panel crossing the
      shoulder blades, neither of which the front view shows
  - file: left.webp
    caption: >-
      The figure's LEFT: black pauldron, grey forearm bracer, black fist. Also
      the only clean read on the kite-shaped hip profile
  - file: right.webp
    caption: >-
      The figure's RIGHT: bare deltoid, no bracer. The asymmetry is the single
      easiest thing to build backwards
  - file: more-angle.webp
    caption: >-
      Warm studio light. Disagrees with the four product shots on white balance,
      and is the only one that separates the brown straps from the olive belt
```

Leave `slug`, `title`, `subtitle`, `source` untouched.

- [ ] **Step 7: Repoint the pipeline paths inside RUNBOOK.md**

Every `/img2threejs` command in `artifacts/exhibits/cloud-strife-polygon-figure/RUNBOOK.md` names a reference path. Replace throughout:

```
src/exhibits/cloud-strife-polygon-figure/references/   →   src/assets/exhibits/cloud-strife-polygon-figure/
```

Also update the `EXHIBIT=` variable near the top of that file:

```bash
EXHIBIT=artifacts/exhibits/cloud-strife-polygon-figure
ASSETS=src/assets/exhibits/cloud-strife-polygon-figure
SKILL=~/.claude/skills/img2threejs
```

and the `.img2threejs/state.json` path in the "每次開工前" block, which is now under `artifacts/exhibits/cloud-strife-polygon-figure/.img2threejs/state.json`.

- [ ] **Step 8: Repoint `sourceImage` in the sculpt spec**

```bash
grep -n 'references/' artifacts/exhibits/cloud-strife-polygon-figure/spec/object-sculpt-spec.json | head
```

Replace each `.../references/<name>.webp` with `src/assets/exhibits/cloud-strife-polygon-figure/<name>.webp`. Do the same in `spec/assessment.json` and `spec/reference-admission.json` if they carry the old path.

- [ ] **Step 9: Confirm the img2threejs state gate still resolves its evidence**

```bash
cd ~/.claude/skills/img2threejs && python3 forge/next.py \
  --state ~/git/personal/img2three-art-exhibition/artifacts/exhibits/cloud-strife-polygon-figure/.img2threejs/state.json \
  ~/git/personal/img2three-art-exhibition/artifacts/exhibits/cloud-strife-polygon-figure/spec/object-sculpt-spec.json
```

Expected: `step=build-current-pass, pass=blockout`, the same as before the move.

If it exits `3` or reports `status=stopped` on a missing evidence path, **stop and report** — do not re-init the state, and do not hand-edit `state.json` to make the error go away. The fallback is to leave the five WebPs under `artifacts/.../references/` and copy them into `src/assets/` instead, accepting 588 KB of duplication; take that route only after reporting.

- [ ] **Step 10: Commit**

```bash
git add -A src/exhibits/cloud-strife-polygon-figure src/assets/exhibits artifacts/exhibits content/exhibits
git commit -m "refactor(strife): split exhibit assets from gate evidence"
```

---

### Task 3: Repoint every glob site and update CLAUDE.md

**Runs alone, after Tasks 1 and 2 have both landed.** Every file here is shared; two workers editing them concurrently will conflict.

**Files:**

- Modify: `src/pages/[slug].vue:76-90`, `:107`, `:116`
- Modify: `src/components/home/ExhibitGrid.vue:56-67`
- Modify: `src/components/home/HeroStage.vue:24-33`
- Modify: `CLAUDE.md`

**Interfaces:**

- Consumes: `src/assets/exhibits/<assetDir>/<file>` from Tasks 1 and 2, where `<file>` is a bare filename with no directory prefix.

- [ ] **Step 1: Confirm the build is currently broken, so the fix is provably the fix**

```bash
npx velite build && pnpm build 2>&1 | tail -20
```

Expected: the build completes but the exhibit covers no longer resolve, because the globs still point at `../exhibits/`. Confirm with:

```bash
grep -o 'card-thumb" src="[^"]*"' dist/index.html
```

Expected: no matches, or matches missing the two exhibits. This is the red state Step 5 turns green.

- [ ] **Step 2: Rewrite the two globs and two lookups in `src/pages/[slug].vue`**

Replace lines 76-90 with:

```js
// Shallow on purpose. A `**` here would eagerly bundle every detail-inventory zone
// crop and PBR map — those live under artifacts/, not src/, precisely so they can
// never reach the client bundle.
const imageUrls = import.meta.glob(
  ["../assets/exhibits/*/*.png", "../assets/exhibits/*/*.webp"],
  { eager: true, import: "default", query: "?url" },
) as Record<string, string>;

const promptTexts = import.meta.glob("../assets/exhibits/*/*.txt", {
  eager: true,
  import: "default",
  query: "?raw",
}) as Record<string, string>;
```

Then line 107:

```js
const imageUrl = (file: string) => imageUrls[`../assets/exhibits/${assetDir.value}/${file}`] ?? "";
```

Then line 116, inside the `prompt` computed:

```js
return promptTexts[`../assets/exhibits/${found.assetDir ?? found.slug}/${found.promptFile}`] ?? "";
```

Leave the `rootTexts` glob at line 94 alone — it points at repo-root `*.md` and is unaffected.

- [ ] **Step 3: Rewrite the glob and lookup in `src/components/home/ExhibitGrid.vue`**

Replace lines 56-67 with:

```js
// Eager and hashed by Vite, so `base` is applied for free. public/ would need
// import.meta.env.BASE_URL stitched on by hand at every use site.
const imageUrls = import.meta.glob(
  ["../../assets/exhibits/*/*.png", "../../assets/exhibits/*/*.webp"],
  { eager: true, import: "default", query: "?url" },
) as Record<string, string>;

const cover = (exhibit: Exhibit): string | undefined => {
  const first = exhibit.images[0];
  const dir = exhibit.assetDir ?? exhibit.slug;
  return first ? imageUrls[`../../assets/exhibits/${dir}/${first.file}`] : undefined;
};
```

- [ ] **Step 4: Rewrite `src/components/home/HeroStage.vue` — glob AND the assetDir bug**

Replace lines 24-33 with:

```js
const imageUrls = import.meta.glob(
  ["../../assets/exhibits/*/*.png", "../../assets/exhibits/*/*.webp"],
  { eager: true, import: "default", query: "?url" },
) as Record<string, string>;

// Keyed by assetDir, not slug: an exhibit's route slug and its asset folder differ
// (ff7-cloud-ultima-weapon lives in cloud-ultima-weapon-v2/). Keying by slug silently
// returned "" and left the turntable's reference photo blank.
const coverOf = (slug: string): string => {
  const exhibit = exhibits.find((e) => e.slug === slug);
  const file = exhibit?.images[0]?.file;
  const dir = exhibit?.assetDir ?? slug;
  return file ? (imageUrls[`../../assets/exhibits/${dir}/${file}`] ?? "") : "";
};
```

- [ ] **Step 5: Build and verify all three cover paths resolve**

```bash
npx velite build && pnpm typecheck && pnpm build 2>&1 | tail -12
```

Expected: typecheck silent, build finishes, and `dist/` contains `index.html` plus one directory per slug.

```bash
grep -o 'card-thumb" src="[^"]*"' dist/index.html
```

Expected: two matches, one per exhibit, both pointing at hashed filenames under `/img2three-art-exhibition/assets/`.

```bash
grep -c 'VII Polygon Soft Vinyl Figure' dist/ff7-cloud-strife-figure/index.html
```

Expected: `1` — proves the `prompt.txt` glob still resolves through its new path.

- [ ] **Step 6: Update the CLAUDE.md wiring rule**

`CLAUDE.md` currently tells the next contributor that assets live at the exhibit root and that the glob only scans direct children. Both statements are now false. Replace the "新增展品要接四個地方" section with:

```markdown
## 新增展品要接五個地方

少接一個首頁就看不到：

1. `src/exhibits/index.ts` 條目（route 由 `vite.config.ts` 的 `includedRoutes` 從
   `src/exhibits/slugs.ts` 生，所以那邊也要補 slug）
2. `src/pages/[slug].vue` 的 `STAGES` map
3. `src/components/home/heroStage.ts` 的 `heroEntries()`
4. `content/exhibits/<assetDir>.yml`（velite 管的文案與 `images[]`）
5. `src/assets/exhibits/<assetDir>/` 底下的圖與 `prompt.txt`

檔案分流規則：

- **頁面資源**（`images[]` 列的圖、`prompt.txt`）→ `src/assets/exhibits/<assetDir>/`，
  平放不要開子資料夾。Vite 會 hash 並自動套 `base`。
- **閘門證據**（`spec/`、`brief/`、`.img2threejs/`、PBR map、detail-inventory crop）
  → `artifacts/exhibits/<assetDir>/`。這些永遠不進 bundle。
- `src/exhibits/<slug>/` 只放 `.ts` 與 `.vue`。
- glob 一律用 `*/`，不要用 `**/`：`**` 會把整包閘門證據 eager 打包進 client bundle。
```

- [ ] **Step 7: Commit**

```bash
git add -A src/pages src/components CLAUDE.md
git commit -m "refactor(assets): repoint exhibit globs at src/assets, fix hero cover key"
```

---

### Task 4 (optional, independent): Replace the hardcoded route arrays with route meta

This is the single genuine Nuxt-convention win identified in the review. It is independent of Tasks 1-3 and can be skipped or deferred without affecting them. Skip it if there is no appetite for touching routing.

**Before you start — two verified facts about `definePage`.**

1. It is a **compiler macro**, processed by the vue-router vite plugin. Do not import it; writing `import { definePage } from "vue-router"` will fail, because the main barrel does not export it (only `vue-router/experimental` does, and that is the type-level surface). Just call it inside `<script setup>` and the plugin transforms it away. Confirmed by the plugin's own error strings in `node_modules/vue-router/dist/options-B2eSXqPk.cjs:271-292` ("Fix the syntax error in the `definePage()` macro of this file").
2. **It cannot reference `<script setup>` bindings.** Same source, line 276: "Avoid referencing `<script setup>` bindings inside `definePage()`; pass static values instead." This is why Step 3 below passes a literal `"ff7"` rather than deriving chrome from the `exhibit` computed — a computed would be rejected at build time.

`definePage` lives on vue-router's experimental surface. It is load-bearing for this task and this task alone; if it is ever removed, fall back to reading a `chrome` field off the `Exhibit` record in `RootApp.vue`. That is why Task 4 is optional and independent.

**Problem.** `src/RootApp.vue:30,34` decides page chrome from two hardcoded path arrays:

```js
const FF7_ROUTES = ["/ff7-cloud-ultima-weapon", "/ff7-cloud-strife-figure"];
const SHOWCASE_ROUTES = ["", "/ff7-cloud-ultima-weapon", "/ff7-cloud-strife-figure", "/ff7-menu"];
```

Every new exhibit must be added to both, in a file that has nothing else to do with exhibits. This is exactly what Nuxt's `layouts/` solves — and vue-router's `meta` solves it without a layout system.

**Files:**

- Modify: `src/RootApp.vue:28-41`
- Modify: `src/pages/[slug].vue` (add a `definePage` meta block)
- Modify: `src/pages/index.vue`, `src/pages/ff7-menu.vue` (add meta blocks)

**Interfaces:**

- Produces: `route.meta.chrome` typed as `"ff7" | "showcase" | "plain" | undefined`, read once in `RootApp.vue`.

- [ ] **Step 1: Declare the meta type**

Create `src/router-meta.d.ts`:

```ts
import "vue-router";

declare module "vue-router" {
  interface RouteMeta {
    /** Page chrome. `ff7` implies showcase framing plus the FF7 token overlay.
     *  Absent means the plain document shell with the site nav and footer. */
    chrome?: "ff7" | "showcase";
  }
}
```

- [ ] **Step 2: Tag the two static showcase pages**

In `src/pages/index.vue`, add at the top of `<script setup>`:

```ts
definePage({ meta: { chrome: "showcase" } });
```

In `src/pages/ff7-menu.vue`, same block but:

```ts
definePage({ meta: { chrome: "ff7" } });
```

- [ ] **Step 3: Tag the dynamic exhibit route from exhibit data, not from a path list**

`src/pages/[slug].vue` serves every exhibit, so its chrome depends on the slug rather than the file. Add to `<script setup>`, after `const exhibit = computed(...)`:

```ts
definePage({ meta: { chrome: "ff7" } });
```

Every exhibit currently wears FF7 chrome, so a constant is correct today. If an exhibit ever needs different chrome, add a `chrome` field to the `Exhibit` type in `src/exhibits/index.ts` and read it in `RootApp.vue` instead — do not reintroduce a path array.

- [ ] **Step 4: Read meta in RootApp.vue**

Replace `src/RootApp.vue:28-41` with:

```ts
// Chrome is declared by each page through route meta (see src/router-meta.d.ts), so a
// new exhibit never has to be added to a list in this file. `ff7` implies showcase
// framing: the FF7 routes bring their own nav and footer too.
const route = useRoute();
const ff7 = computed(() => route.meta.chrome === "ff7");
const showcase = computed(() => route.meta.chrome !== undefined);
```

Delete the now-unused `path` computed and both arrays.

- [ ] **Step 5: Verify every route still gets the chrome it had**

```bash
npx velite build && pnpm typecheck && pnpm build 2>&1 | tail -8
for p in index ff7-cloud-ultima-weapon/index ff7-cloud-strife-figure/index; do
  printf '%-40s ff7-page=%s\n' "$p" "$(grep -c 'ff7-page' dist/$p.html)"
done
```

Expected: `index` → `0`, both exhibit pages → `1`. Matches the pre-change behaviour: the landing page is showcase-but-not-FF7, the exhibit pages are FF7.

`/ff7-menu` and `/ultima-v2-harness` are not prerendered (`vite.config.ts:43` allowlists only `/` and the exhibit slugs), so verify those two in the dev server instead:

```bash
pnpm dev
# visit /img2three-art-exhibition/ff7-menu — expect FF7 chrome
# visit /img2three-art-exhibition/ultima-v2-harness — expect plain chrome, no nav
```

- [ ] **Step 6: Commit**

```bash
git add -A src/RootApp.vue src/pages src/router-meta.d.ts
git commit -m "refactor(chrome): declare page chrome in route meta"
```

---

## Explicitly rejected — do not implement

Recorded so a future session does not rediscover these as good ideas.

| Idea                                                              | Why not                                                                                                                                                               |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Move exhibit `.vue`/`.ts` into `src/pages/`                       | Every `.vue` under `routesFolder` becomes a route; exhibits share one dynamic route and are not pages. See Q1.                                                        |
| Rename `src/` → `app/`                                            | Nuxt-4-only default with a watcher-performance rationale that does not apply here. Touches the `~` alias, tsconfig paths, and every import for zero behavioural gain. |
| Create empty `composables/`, `middleware/`, `plugins/`, `server/` | Cargo cult. Add each when it has a second occupant.                                                                                                                   |
| Migrate to Nuxt                                                   | See Q3. Rewrites velite + the SSG allowlist and discards vite-plus, to gain layouts that Task 4 delivers for ~20 lines.                                               |
| Move page assets to `public/`                                     | Loses content hashing and automatic `base`; every use site would need `import.meta.env.BASE_URL`. Rationale already recorded at `ExhibitGrid.vue:56-57`.              |
| `import.meta.glob("../assets/exhibits/**/*")`                     | The `**` would bundle every PBR map and zone crop. Keep globs shallow.                                                                                                |

## Open questions — not resolved by this review

- **Whether `forge/next.py` tolerates the reference-image move.** Task 2 Step 9 checks it, but I did not run the gate before or after a move, so I cannot promise the state file survives repointing. The fallback (duplicate the five WebPs instead of moving them) is written into that step.
- **Whether `docHref` needs updating.** `src/pages/[slug].vue:109` builds GitHub blob URLs from `const REPO = ".../blob/main/src/exhibits"`. No exhibit currently populates the `docs` field, so nothing renders from it and nothing breaks. If `docs` is ever used, that constant must point at wherever the doc actually lives — likely `artifacts/exhibits/`. Latent, not urgent.
- **`src/exhibits/cloud-strife-polygon-figure/CloudStrifeStage.vue` is the only file left in that directory after Task 2.** Whether a one-file directory earns its place, versus folding the stage into `src/components/stage/`, is a judgement call I am leaving to the person who adds the real viewer.
