# Phase 1 evidence — green split sprite fix

**Date:** 2026-08-25

## What changed and why

The four `split/sheet_row7c{62,63,64,65}.png` cells are the bottom-right palette-swatch row of
`references/sigma-wireframe-sheet.png`. They are **not all green** — only one of them is.

| file | bbox in sheet | size | dominant non-navy color | palette variant | green? |
|---|---|---|---|---|---|
| `sheet_row7c62_red.png` | `[383,2564,431,2641]` | 48×77 | `(184,0,8)` ≈ `#B80008` | red | no |
| `sheet_row7c63_purple.png` | `[441,2572,489,2640]` | 48×68 | `(168,40,240)` ≈ `#A828F0` | purple | no |
| `sheet_row7c64.png` | `[496,2573,544,2642]` | 48×69 | `(16,216,48)` ≈ `#10D830` | **green** | yes |
| `sheet_row7c65_red.png` | `[553,2573,600,2641]` | 47×68 | `(224,56,24)` ≈ `#E03818` | red/orange | no |

The four cells are **not all green** — only `c64` is. They are also **not the same size**: each is
cut to its own sprite content (48×77 / 48×68 / 48×69 / 47×68), per the 2026-08-25 re-cut/trim
pass. The previous `c64` bbox `[496,2564,544,2643]` was 9px too tall at top (palette-swatch bleed)
and 6px short on the right; the corrected true-green-cell crop was then trimmed of 6px dead navy
right + 6px bottom to the 48×69 sprite. `c63` had 8px dead navy above its sprite and was trimmed
to 48×68. `c65` was re-cut from a 47×75 crop (7px trailing navy) to the 47×68 content cell.

The 54×75 crop `spec/green-breakdown/manifest.json::sheet_green_yaw_full` remains the pipeline
authority (its 6px padding is harmless to the filled-mask gates); the `split/` crops are the
tight sprite-level evidence.

## Evidence

- Side-by-side 12× NEAREST strip: `.tmp/sigma/row7c62-65_corrected_12x.png` (2376×924, in the
  project-root scratchpad, gitignored).
- Per-cell color histograms: `phase1_palettes.json` in the same scratchpad (key per cell, value:
  top 5 non-navy colors with counts).
- Histogram/recut scripts: `.tmp/sigma/inspect_state.py`, `.tmp/sigma/recut_c64.py`,
  `.tmp/sigma/recut_c65.py`, `.tmp/sigma/verify_c64.py`, `.tmp/sigma/phase1_palettes.py`.

## Scope

**Only `sheet_row7c64.png` is a green input.** The other three are palette-swap evidence for
non-green readings; they must not enter any "green" pipeline branch.

The existing `spec/green-breakdown/manifest.json` (which the spec, factory, and 1.5.1 gates all
consume) was already correct — it cuts the green yaw at the right bbox. The defect was only at
the `split/` layer, where the mis-cropped c64 + the three non-green siblings invited the misread
that all four were green.
