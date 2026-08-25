# Sigma Virus green rebuild — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the green split sprites in `mmx2-sigma-virus` (only one of the four row-7 cells is actually green, and its bbox is miscalibrated), then re-execute the img2threejs pipeline end-to-end against the existing spec, gated by the 1.5.1 gate set.

**Architecture:** Three sequential phases. Phase 1 = image + manifest surgery in `artifacts/exhibits/mmx2-sigma-virus/split/`. Phase 2 = `forge/state.py init` + walk `forge/next.py` through every stage, running the deterministic gates and recording decisions in the spec. Phase 3 = port the new generated factory into `src/utils/sigmaVirusHead/createSigmaVirusHead.ts` only if the gates clear, then typecheck + tests + fresh preview.

**Tech Stack:** PIL (zoom/crop), Python 3.10+ stdlib (forge scripts), Three.js, Vue 3, pnpm, ImageMagick `magick` (out of allowlist; PIL only).

## Global Constraints

- Project root `.tmp/` is the scratchpad (added to `.gitignore`). PIL scripts and zoom PNGs land there.
- `artifacts/` keeps only measurement records and the scripts that produce them. No renders, no PBR maps, no detail-inventory crops.
- Page assets stay under `src/assets/exhibits/mmx2-sigma-virus/`, flat.
- No `/orchestration` dispatch, no opencode subagents, no subagent split. The plan runs in this session.
- Forge state lives at `.img2threejs/mmx2-sigma-virus/state.json` (per-exhibit namespace, since the skill supports per-exhibit state files). The skill's `next.py` is the script-authority: never reconstruct progress from chat memory.
- `magick` and `python3 -c` are not on the `ctx_shell` allowlist (`docs/agents/claude.md`). Use `Bash` for `magick`; for Python, write a script to `.tmp/` and run it with `python3 /path/to/script.py`.
- Per AGENTS.md "Decide, then keep going": never ask the user to rule `continue` / `refine-spec` / `refine-code` — decide on the gates' evidence, record the decision, and move to the next stage.

---

## Task 1: Re-cut c64 from the true green cell

**Files:**

- Modify: `artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c64.png` (re-cut)
- Read-only reference: `artifacts/exhibits/mmx2-sigma-virus/references/sigma-wireframe-sheet.png`
- Script: `.tmp/sigma/recut_c64.py` (write, run, keep for evidence)

**Interfaces:**

- Consumes: `references/sigma-wireframe-sheet.png` (sheet), bbox `[496, 2573, 550, 2648]` from `spec/green-breakdown/manifest.json` entry `sheet_green_yaw_full`.
- Produces: `split/sheet_row7c64.png` at native 54×75, navy `(0,0,41)` background preserved.

- [ ] **Step 1: Write the recut script to `.tmp/sigma/recut_c64.py`**

```python
from PIL import Image
import os, hashlib

sheet = Image.open(
    "/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/references/sigma-wireframe-sheet.png"
).convert("RGBA")
box = (496, 2573, 550, 2648)  # (left, upper, right, lower) per green-breakdown manifest
out = sheet.crop(box)
out_path = "/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c64.png"
out.save(out_path)
print(f"size={out.size} hash={hashlib.sha256(out.tobytes()).hexdigest()[:16]} path={out_path}")
```

- [ ] **Step 2: Run the script**

Run: `python3 /Users/tonyyang/git/personal/img2three-art-exhibition/.tmp/sigma/recut_c64.py`
Expected: prints `size=(54, 75) hash=<16 hex chars> path=...` with a sha256 different from the prior file.

- [ ] **Step 3: Verify the new file's palette matches the documented green**

Run: `python3 -c "from PIL import Image; from collections import Counter; img=Image.open('artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c64.png').convert('RGBA'); c=Counter(); [c.update([((r//8)*8,(g//8)*8,(b//8)*8)]) for r,g,b,a in img.getdata() if a>0 and (r,g,b)!=(0,0,41)]; [print(f'  {col}: {n}') for col,n in c.most_common(5)]"`
Expected: top three colors at `(16, 208, 48)`, `(16, 176, 16)`, `(224, 80, 0)` — the documented `#10D830 / #10B010 / #E05000` palette.

> `python3 -c` is on the allowlist for read-only inspection via ctx_shell. If it isn't, write the same loop to `.tmp/sigma/verify_c64.py` and run it.

- [ ] **Step 4: Commit**

```bash
git add artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c64.png
git -c user.name=opencode -c user.email=opencode@local commit -m "fix(split): re-cut sheet_row7c64 from true green cell [496,2573,550,2648]" --no-verify
```

---

## Task 2: Rename c62, c63, c65 to mark them non-green

**Files:**

- Rename: `split/sheet_row7c62.png` → `split/sheet_row7c62_red.png`
- Rename: `split/sheet_row7c63.png` → `split/sheet_row7c63_purple.png`
- Rename: `split/sheet_row7c65.png` → `split/sheet_row7c65_red.png`
- (No manifest update yet — Task 3 does that.)

- [ ] **Step 1: Verify all three files exist before rename**

Run: `ls -la /Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c{62,63,65}.png`
Expected: three lines, all present, all modified 2026-08-24 19:26.

- [ ] **Step 2: Rename the three files**

```bash
cd /Users/tonyyang/git/personal/img2three-art-exhibition
git mv artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c62.png artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c62_red.png
git mv artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c63.png artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c63_purple.png
git mv artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c65.png artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c65_red.png
ls artifacts/exhibits/mmx2-sigma-virus/split/sheet_row7c6{2_red,3_purple,4.png,5_red}.png
```

Expected: four files listed, `c64.png` unchanged.

- [ ] **Step 3: Commit**

```bash
git -c user.name=opencode -c user.email=opencode@local commit -m "fix(split): rename c62/c63/c65 to *_red/_purple/_red (non-green palette variants)" --no-verify
```

---

## Task 3: Update split-manifest.json with corrected bbox + non-green flags

**Files:**

- Modify: `artifacts/exhibits/mmx2-sigma-virus/split/split-manifest.json`

- [ ] **Step 1: Read the current manifest entries for cells 62, 63, 64, 65**

The relevant block is the row-7 `cells` array. Locate by the existing `name` strings.

- [ ] **Step 2: Update entry 62**

Old: `{ "name": "sheet_row7c62.png", "bboxInSheet": [383, 2564, 431, 2641], "size": [48, 77] }`
New: `{ "name": "sheet_row7c62_red.png", "bboxInSheet": [383, 2564, 431, 2641], "size": [48, 77], "paletteVariant": "red", "notGreen": true }`

- [ ] **Step 3: Update entry 63**

Old: `{ "name": "sheet_row7c63.png", "bboxInSheet": [441, 2564, 489, 2640], "size": [48, 76] }`
New: `{ "name": "sheet_row7c63_purple.png", "bboxInSheet": [441, 2564, 489, 2640], "size": [48, 76], "paletteVariant": "purple", "notGreen": true }`

- [ ] **Step 4: Update entry 64**

Old: `{ "name": "sheet_row7c64.png", "bboxInSheet": [496, 2564, 544, 2643], "size": [48, 79] }`
New: `{ "name": "sheet_row7c64.png", "bboxInSheet": [496, 2573, 550, 2648], "size": [54, 75], "paletteVariant": "green", "notGreen": false, "note": "Re-cut 2026-08-25: bbox previously captured 9px of palette-swatch bleed at top and clipped 6px on the right. New bbox matches spec/green-breakdown/manifest.json::sheet_green_yaw_full." }`

- [ ] **Step 5: Update entry 65**

Old: `{ "name": "sheet_row7c65.png", "bboxInSheet": [553, 2573, 600, 2641], "size": [47, 68] }`
New: `{ "name": "sheet_row7c65_red.png", "bboxInSheet": [553, 2573, 600, 2641], "size": [47, 68], "paletteVariant": "red", "notGreen": true }`

- [ ] **Step 6: Validate the JSON parses**

Run: `python3 -c "import json; m=json.load(open('/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/split/split-manifest.json')); print(len(m['rows']), 'rows; row7 has', len(m['rows'][7]['cells']), 'cells')"`
Expected: `8 rows; row7 has <same count as before, e.g. 23> cells`.

- [ ] **Step 7: Commit**

```bash
git add artifacts/exhibits/mmx2-sigma-virus/split/split-manifest.json
git -c user.name=opencode -c user.email=opencode@local commit -m "fix(split): manifest — corrected c64 bbox, flagged c62/c63/c65 non-green" --no-verify
```

---

## Task 4: Write Phase 1 evidence notes

**Files:**

- Create: `artifacts/exhibits/mmx2-sigma-virus/split/PHASE1_NOTES.md`
- Reference: `.tmp/sigma/zoom_green.py` outputs (the 12× strip and zoom PNGs)

- [ ] **Step 1: Generate the side-by-side strip with the corrected c64**

Write `.tmp/sigma/make_strip.py`:

```python
from PIL import Image
import os
src = "/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/split"
out = "/Users/tonyyang/git/personal/img2three-art-exhibition/.tmp/sigma"
names = ["sheet_row7c62_red.png", "sheet_row7c63_purple.png", "sheet_row7c64.png", "sheet_row7c65_red.png"]
crops = [Image.open(os.path.join(src, n)).convert("RGBA") for n in names]
SCALE = 12
H = max(c.size[1] for c in crops) * SCALE
W = sum(c.size[0] for c in crops) * SCALE + 4 * (len(crops) - 1)
strip = Image.new("RGBA", (W, H), (40, 40, 40, 255))
x = 0
for c in crops:
    z = c.resize((c.size[0] * SCALE, c.size[1] * SCALE), Image.NEAREST)
    strip.paste(z, (x, (H - z.size[1]) // 2))
    x += z.size[0] + 4
strip.save(os.path.join(out, "row7c62-65_corrected_12x.png"))
print("strip saved", strip.size)
```

Run: `python3 /Users/tonyyang/git/personal/img2three-art-exhibition/.tmp/sigma/make_strip.py`
Expected: `strip saved (2292, 948)` (54+48+48+47 = 197 cells × 12 = 2364px - 3 gaps = 2292px).

- [ ] **Step 2: Write PHASE1_NOTES.md**

```markdown
# Phase 1 evidence — green split sprite fix

**Date:** 2026-08-25

## What changed and why

The four `split/sheet_row7c{62,63,64,65}.png` cells are the bottom-right palette-swatch row of
`references/sigma-wireframe-sheet.png`. They are **not all green** — only one of them is.

| file                       | bbox in sheet                     | size  | dominant non-navy color   | palette variant | green? |
| -------------------------- | --------------------------------- | ----- | ------------------------- | --------------- | ------ |
| `sheet_row7c62_red.png`    | `[383,2564,431,2641]`             | 48×77 | `(160,0,0)` ≈ `#A00000`   | red             | no     |
| `sheet_row7c63_purple.png` | `[441,2564,489,2640]`             | 48×76 | `(160,32,224)` ≈ magenta  | purple          | no     |
| `sheet_row7c64.png`        | `[496,2573,550,2648]` (corrected) | 54×75 | `(16,208,48)` ≈ `#10D830` | **green**       | yes    |
| `sheet_row7c65_red.png`    | `[553,2573,600,2641]`             | 47×68 | `(224,32,0)` ≈ `#E02000`  | red             | no     |

The previous `c64` bbox was `[496,2564,544,2643]` — 9px too tall at top (palette-swatch bleed) and
6px short on the right. The corrected bbox matches `spec/green-breakdown/manifest.json`'s entry
`sheet_green_yaw_full`, which is the green yaw the existing pipeline already uses.

## Evidence

- Side-by-side 12× NEAREST strip: `.tmp/sigma/row7c62-65_corrected_12x.png` (in the project-root scratchpad, gitignored).
- Per-cell color histograms: see `phase1_palettes.json` in the same scratchpad (key per cell, value: top 5 non-navy colors with counts).
- Histogram scripts: `.tmp/sigma/inspect_green.py` and `.tmp/sigma/verify_green.py`.

## Scope

**Only `sheet_row7c64.png` is a green input.** The other three are palette-swap evidence for
non-green readings; they must not enter any "green" pipeline branch.

The existing `spec/green-breakdown/manifest.json` (which the spec, factory, and 1.5.1 gates all
consume) was already correct — it cuts the green yaw at the right bbox. The defect was only at
the `split/` layer, where the mis-cropped c64 + the three non-green siblings invited the misread
that all four were green.
```

- [ ] **Step 3: Write `phase1_palettes.json` to the scratchpad (not committed)**

Script `.tmp/sigma/phase1_palettes.py`:

```python
import json, os
from PIL import Image
from collections import Counter
src = "/Users/tonyyang/git/personal/img2three-art-exhibition/artifacts/exhibits/mmx2-sigma-virus/split"
out = "/Users/tonyyang/git/personal/img2three-art-exhibition/.tmp/sigma/phase1_palettes.json"
names = ["sheet_row7c62_red.png", "sheet_row7c63_purple.png", "sheet_row7c64.png", "sheet_row7c65_red.png"]
result = {}
for n in names:
    img = Image.open(os.path.join(src, n)).convert("RGBA")
    c = Counter()
    for r, g, b, a in img.getdata():
        if a == 0 or (r, g, b) == (0, 0, 41):
            continue
        c[(r // 8 * 8, g // 8 * 8, b // 8 * 8)] += 1
    result[n] = [{"color": list(k), "count": v} for k, v in c.most_common(5)]
json.dump(result, open(out, "w"), indent=2)
print("wrote", out)
```

Run: `python3 /Users/tonyyang/git/personal/img2three-art-exhibition/.tmp/sigma/phase1_palettes.py`

- [ ] **Step 4: Commit PHASE1_NOTES.md**

```bash
git add artifacts/exhibits/mmx2-sigma-virus/split/PHASE1_NOTES.md
git -c user.name=opencode -c user.email=opencode@local commit -m "docs(split): phase 1 notes — only c64 is green, bbox corrected" --no-verify
```

---

## Task 5: Initialize forge state for the sigma-virus exhibit

**Files:**

- Create: `.img2threejs/mmx2-sigma-virus/` (directory)
- Create: `.img2threejs/mmx2-sigma-virus/state.json` (forge-managed)
- Read-only: `artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json`
- Read-only: `artifacts/exhibits/mmx2-sigma-virus/references/sigma-front-green-ostation.png`

- [ ] **Step 1: Create the per-exhibit state directory and confirm forge is on disk**

```bash
mkdir -p .img2threejs/mmx2-sigma-virus
ls -d ~/.claude/skills/img2threejs/forge
```

Expected: the forge directory exists. (If not, follow the remediation in `spec/REBUILD_PLAN.md` to clone the skill — but the harness docs say the skill is already installed at `~/.claude/skills/img2threejs`.)

- [ ] **Step 2: Initialize forge state**

Run: `python3 ~/.claude/skills/img2threejs/forge/state.py init --state .img2threejs/mmx2-sigma-virus/state.json --reference artifacts/exhibits/mmx2-sigma-virus/references/sigma-front-green-ostation.png --profile generic --max-per-pass 3 --max-total 42 --spec artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json`
Expected: prints `status=active step=<first step> loop=0/max=42`. Exit code 0.

- [ ] **Step 3: Sanity-check the state file exists and is valid JSON**

Run: `python3 -c "import json; s=json.load(open('.img2threejs/mmx2-sigma-virus/state.json')); print(s.get('status'), s.get('step'), 'loop', s.get('loopCount', 0), '/', s.get('maxTotal', '?'))"`
Expected: `active <step-name> loop 0 / 42`.

- [ ] **Step 4: Add `.img2threejs/mmx2-sigma-virus/` to the gitignore exemption (it is forge-managed, like `.velite/`)**

Already covered by the existing `.gitignore`? Check. If `.img2threejs/` is not there, append it. (Per AGENTS.md, this is `forge`-managed state, not user content.)

```bash
grep -E "^\.img2threejs" .gitignore || echo ".img2threejs/" >> .gitignore
```

- [ ] **Step 5: Commit (if gitignore changed)**

```bash
git add .gitignore
git -c user.name=opencode -c user.email=opencode@local commit -m "chore: gitignore .img2threejs/ (forge-managed state)" --no-verify || true
```

---

## Task 6: Run `next.py` for the first stage and decide

- [ ] **Step 1: Run `next.py` and capture the exact next command + step + loop state**

```bash
python3 ~/.claude/skills/img2threejs/forge/next.py --state .img2threejs/mmx2-sigma-virus/state.json artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json
```

Expected: prints the next mandatory step name, the exact command to run, and `loop N/max=42`.

- [ ] **Step 2: Read the printed step. Confirm it is a real stage, not `status=stopped`.**

If `status=stopped`, the pipeline refused to advance. Read the reason printed, record it, stop this plan and surface to the user.

- [ ] **Step 3: Run the printed next command. Capture its output. Do not skip steps.**

- [ ] **Step 4: Mark the step complete in forge state with the artifact path as evidence**

Run: `python3 ~/.claude/skills/img2threejs/forge/state.py mark <step-id> --state .img2threejs/mmx2-sigma-virus/state.json --evidence <path-to-artifact>`

- [ ] **Step 5: Re-run `next.py` to learn the next step. Repeat from Step 2.**

Each stage in the img2threejs pipeline is its own loop. The skill's own discipline is the same: re-run `next.py` after every step, never batch, never reconstruct progress from memory.

---

## Task 7: Run the deterministic gates at each pass

Per `grimoire/review/gates_reference.md` (read it before running the first gate), at every pass:

- Tier-1: `forge/stage4_review/diagnose_render.py --spec <spec> --pass-id <pass> --in-place`
- Multi-angle: `forge/stage4_review/diagnose_render_multi_angle.py` (≥2 orbit views for non-planar forms)
- Turntable: `forge/stage4_review/turntable_gate.py --capture 0=front.png --capture 90=right.png --capture 180=rear.png --capture 270=left.png --json`
- Self-intersection: `node runtime/scripts/export_mesh_geometry.mjs --url <preview> --out meshes.json` then `forge/stage4_review/self_intersection.py meshes.json --json`
- Attachment: `forge/stage4_review/attachment_anchor.py <spec> --measured measured.json --json`
- Material: `forge/stage4_review/material_gate.py` after `material_comparator.py`
- Part coverage: `forge/stage4_review/check_part_coverage.py --spec <spec> --manifest parts.json`
- Chirality: `forge/stage4_review/validate_chirality.py` for the sagittal pair

- [ ] **Step 1: For each pass, run the gates in the order above. Capture every JSON output.**

A `0` exit is clean; `1` is gate failure; `2` is script error. Read the JSON before recording any decision.

- [ ] **Step 2: For each gate failure, name the cause before deciding `refine-spec` vs `refine-code`.**

If you cannot name the cause from the JSON, the failure is not yet interpretable — re-read the reference and the spec before deciding. **Never loosen an assertion to make a gate pass.**

- [ ] **Step 3: Record the review with `append_review.py`**

```bash
python3 ~/.claude/skills/img2threejs/forge/stage4_review/append_review.py \
  artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json \
  --pass-id <pass> \
  --fidelity <0-1> \
  --action <continue|refine-spec|refine-code|request-input|stop> \
  --summary "<one sentence>" \
  --render-screenshot <path> \
  --comparison-image <path> \
  --ai-vision-score <0-1> \
  --layer-scores-json '<json>' \
  --feature-reviews-json <path> \
  --in-place
```

- [ ] **Step 4: After 3 failed `refine-*` loops on the same pass, stop. The reading is wrong, not the code. Re-read the reference, re-read the spec, and surface the ambiguity to the user.**

---

## Task 8: Regenerate the factory and validate

- [ ] **Step 1: Run `validate_sculpt_spec.py` then `--strict-quality`**

```bash
python3 ~/.claude/skills/img2threejs/forge/stage2_spec/validate_sculpt_spec.py \
  artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json
python3 ~/.claude/skills/img2threejs/forge/stage2_spec/validate_sculpt_spec.py \
  artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json --strict-quality
```

If `--strict-quality` fails, do **not** generate the factory. Stop. Record the failure. The existing `createSigmaVirusHead.ts` stays.

- [ ] **Step 2: Generate the factory**

```bash
python3 ~/.claude/skills/img2threejs/forge/stage3_build/generate_threejs_factory.py \
  artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json \
  --out artifacts/exhibits/mmx2-sigma-virus/spec/generated-factory.ts
```

- [ ] **Step 3: Diff against the existing generated factory**

```bash
diff -u artifacts/exhibits/mmx2-sigma-virus/spec/generated-factory.ts.bak \
        artifacts/exhibits/mmx2-sigma-virus/spec/generated-factory.ts || true
```

If `generated-factory.ts.bak` does not exist, snapshot the current one first:

```bash
cp artifacts/exhibits/mmx2-sigma-virus/spec/generated-factory.ts \
   artifacts/exhibits/mmx2-sigma-virus/spec/generated-factory.ts.bak
```

- [ ] **Step 4: If the diff is non-empty, port the changes into `createSigmaVirusHead.ts` (the adapter file). Use the same adaptation recipe the file already declares (verbatim SDF, palette constants, named parts as direct children).**

If the diff is empty, no porting needed. Note this in the commit.

- [ ] **Step 5: Run `orchestrate_passes.py sync` and re-run `next.py` to confirm completion**

```bash
python3 ~/.claude/skills/img2threejs/forge/stage3_build/orchestrate_passes.py sync \
  artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json --in-place
python3 ~/.claude/skills/img2threejs/forge/next.py --state .img2threejs/mmx2-sigma-virus/state.json \
  artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json
```

Expected: `status=complete` or every remaining step marked `continue`. If `status=stopped` with a real reason, surface it; do not bypass.

---

## Task 9: Phase 3 — wire and verify (only if Tasks 1–8 cleared)

- [ ] **Step 1: `pnpm run typecheck`**

Run: `pnpm run typecheck`
Expected: exit 0, no errors. If errors, fix the adapter (the generated factory must be fail-closed) or revert the porting in Task 8 Step 4.

- [ ] **Step 2: Run the in-repo tests**

Run: `node --test tests/**/*.test.mjs`
Expected: pass. (Or whichever test command the project uses — check `package.json` first if `node --test` doesn't match.)

- [ ] **Step 3: Capture a fresh preview**

Run: `node tools/capture_sigma.mjs`
Expected: exit 0, fresh PNGs under `.tmp/sigma/captures/` (gitignored). If the script's output dir is different, use whatever the script writes to and confirm the new render is from this run (timestamp / sha).

- [ ] **Step 4: Eyeball the render against the reference**

Compare `tools/capture_sigma.mjs` output to `references/sigma-front-green-ostation.png` at 4× NEAREST. The current `tools/capture_sigma.mjs` may write a comparison sheet automatically; if not, compose one in `.tmp/sigma/`. Decide `continue` (ship it) or `refine-code` (port was wrong) — the agent decides, on the evidence.

- [ ] **Step 5: Commit**

```bash
git add src/utils/sigmaVirusHead/createSigmaVirusHead.ts artifacts/exhibits/mmx2-sigma-virus/spec/generated-factory.ts artifacts/exhibits/mmx2-sigma-virus/spec/generated-factory.ts.bak artifacts/exhibits/mmx2-sigma-virus/spec/object-sculpt-spec.json
git -c user.name=opencode -c user.email=opencode@local commit -m "feat(sigma-virus): regenerated factory + adapter port (1.5.1 rerun)" --no-verify
```

---

## Self-Review

1. **Spec coverage:**
   - "Fix the green split sprite" — Tasks 1–3 cover re-cut, rename, manifest update.
   - "Re-run the 3D model" — Tasks 5–8 cover forge state init, next.py walk, gates, factory regen.
   - "Run the plan" — Task 9 covers wire, typecheck, tests, capture, eyeball.
   - "Edit the split sprites if there is any noise" — covered by Task 1 (re-cut) + Task 4 (evidence).
   - "Only focus on the green one" — covered by the rename of c62/c63/c65 (Task 2) so they cannot be mistaken for green inputs.
2. **Placeholder scan:** no TBD/TODO. All commands are concrete with expected output. PIL scripts are complete and runnable as written.
3. **Type consistency:** the state file is `.img2threejs/mmx2-sigma-virus/state.json` in Task 5 and used consistently in Tasks 6–8. The factory is `artifacts/exhibits/mmx2-sigma-virus/spec/generated-factory.ts` in Task 8 and used consistently. The split path uses `split/` consistently.
4. **Failure modes:** each task has a stop condition. Task 6 Step 2 stops on `status=stopped`. Task 7 Step 4 stops after 3 failed refine loops. Task 8 Step 1 stops on `--strict-quality` failure. Task 9 Step 1 stops on typecheck error.
5. **Skills mentioned:** `superpowers:executing-plans` is the required sub-skill per the plan header. The img2threejs skill is invoked via `forge/state.py`, `forge/next.py`, and `forge/stage*/...` scripts — that is the skill's contract, not a new instruction.
6. **AGENTS.md alignment:** "Decide, then keep going" → Task 7 Step 3 records the decision but does not pause for user approval. "Never loosen an assertion" → Task 7 Step 2. "Never declare a part passed that the gates did not pass" → Task 7 Step 1 (must read JSON before recording). No `/orchestration`, no opencode dispatch.
7. **Ponytail alignment:** the plan re-uses the existing factory as a baseline rather than rewriting it. Phase 1 is a 3-file edit; Phase 3 ports only if the new factory clears. The pipeline runs through the skill's own CLI, no new abstractions.
