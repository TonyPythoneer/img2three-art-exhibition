# Claude Code

Project rules live in [AGENTS.md](../../AGENTS.md) (`CLAUDE.md` is a symlink to it). This file holds
only what is specific to this harness.

## Skill

- Do not auto-activate `superpowers` skills; use one only when the user names it.
- `img2threejs` is at `~/.claude/skills/img2threejs`, currently detached HEAD @ `d667338`
  (tag `v1.5-beta`). **`SKILL.md`'s `version:` field says `1.4.4` because upstream never bumped it —
  trust the commit, not the field.**

## The two limits of lean-ctx

`ctx_*` replaces native Read/Grep/Glob/Shell (native Grep/Glob are blocked by a hook). Two places
force you back to the native tools:

- **`ctx_read` cannot leave the project root.** Reading the grimoire under
  `~/.claude/skills/img2threejs/**` needs native `Read`.
- **`ctx_shell` runs an allowlist.** `magick` is not on it, and `python3 -c` is blocked. Cutting
  zoom crops and running inline Python both need native `Bash`.

## Zooming in on a reference

```bash
magick <ref> -crop WxH+X+Y +repage -filter point -resize 1100% <out>.png
```

`-filter point` is NEAREST; never use the default smooth resampling. Cut crops at **joints**.
ImageMagick silently converts low-colour PNGs to a palette, which makes the forge scripts fail —
add `-type TrueColor` when cutting.

`magick` is not on the `ctx_shell` allowlist, but **PIL is**: writing one `.py` in the scratchpad
that cuts a whole batch is faster than one `magick` call per crop and sidesteps the allowlist
entirely. `Image.NEAREST` is the equivalent of `-filter point`.

## The three prerequisite measurement scripts (AGENTS.md's P0 / P1)

Always write them to a file before running (`ctx_shell` blocks `python3 -c`). Finished ones go in
`artifacts/exhibits/<assetDir>/spec/`; drafts stay in the scratchpad.

**1. Silhouette and clipping triage** (P0)

```python
# figure = unreachable from the border AND not near-white
solid[i] = (255 - min(r, g, b)) > TOL           # TOL=18 is enough for these webp files
reach    = flood_fill_from_border(not solid)     # seed from all four edges
figure[i] = (not reach[i]) and solid[i]
```

Clipping test: `sum(figure)` along the topmost / bottommost / leftmost / rightmost line. A genuine
point is 1–2 px wide; a solid run there means the subject is cut off and that direction's
measurements are untrustworthy.

Flood fill alone counts white regions enclosed by the subject (the gap between the legs) as
subject; a threshold alone counts compression noise as subject. You need both conditions.

**2. Banded mirror IoU** (P1, for deciding symmetry)

Sweep the silhouette for its best mirror axis (half-pixel steps, maximise IoU), then cut horizontal
bands by height fraction and report `mirrorIoU` plus the left/right difference in maximum lateral
extent per band.

**The whole-figure IoU is the noise floor** (photographic perspective and staging cause it).
Subtract it when reading the bands — with a floor of 0.85, a band at 0.88 is not "asymmetric".

**3. Palette clustering** (P1, for assigning colour codes)

Do not eye-dropper by hand; points land on boundaries and return blended colours. Quantise the
subject's pixels into 24-level buckets and report each cluster's centroid hex, pixel share, mean y,
and mean x relative to the mirror axis, then identify each cluster **by position**.

Asymmetric accessories (a bracer, a pauldron) fall out of the sign of that mean x on their own,
which doubles as a cross-check on handedness.
