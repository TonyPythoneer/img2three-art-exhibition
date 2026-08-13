# Image analysis — the step that was skipped

`grimoire/intake/image_analysis.md` is the img2threejs pipeline's **step 1**, before any
script. It was not run. `state.json` marks `image-analysis` done with `landmarks.json` as
its evidence — but that is a script's output, not an observation, so the mark was hollow.

Every part after the sole was built from numbers alone, without ever looking at the region
being built. Five measurement errors reached the model that way (belt→arm span,
deltoid→neck width, calf→both-legs span, chest→strap-cut runs, face→back view's ear
wedges), and each would have been visible in one crop.

`back.webp`, `right.webp` and `more-angle.webp` had never been opened at all.

Written from the four orthographic views plus more-angle. **Observation is separated from
inference**, per the protocol's first discipline.

---

## Layer 1 — Identification

Work type: a **polygon-figure statuette** — a physical vinyl collectible of a low-poly
game character, photographed as a product. `primaryDomain: character`. Confidence 0.95.

⚠ The subject is the TOY, not the game model. Every facet in the references is a facet on
a moulded object, not a rendering artefact.

## Layer 2 — Overall form & silhouette

Bilateral, geometric, hard-edged. Bounding volume is not a single primitive: the figure
reads as **a wide angular mass on top of a narrow stack**.

**OBSERVED, and this is the finding that matters most:** the HAIR MASS is the largest
single volume in the figure. In `back.webp` it spans nearly the full width of the
shoulders and covers the entire cranium; in `right.webp` it projects both forward of the
brow and behind the occiput, so its depth is roughly 1.5× the skull's own.

INFERENCE: the figure's silhouette identity is top-heavy. Any Stage 1 blockout without the
cap will read as a different object, and a whole-figure silhouette score at Stage 1 is
therefore uninformative — **but that does NOT excuse the current blockout**, whose torso
and limbs are wrong independently of the hair (Layer 4).

## Layer 3 — Macro → meso → micro

macro: hair mass · head · torso · arm ×2 · leg ×2
meso: cap + spikes · skull + face · chest slab + belt + pelvis · deltoid + upper arm +
      forearm + wrist + glove · thigh-to-calf tube + boot cuff + sole slab
micro: brow/eye print · nose wedge · chest straps · back diagonal panel · pauldron ·
       bracer · boot step

**OBSERVED in `right.webp`, and not in any measurement so far:** the **NOSE is a distinct
triangular wedge** projecting from the face plane, in profile, above the chin. §2 c) rules
eyes/pupils/brows out of geometry as printed art — correctly — but the nose is NOT print.
It is relief, and `parts.head` has nothing for it.

## Layer 4 — Spatial relationships, and where the built model is wrong

Triplets, with the built model's contradiction against each:

- `<deltoid, protrudes-laterally-past, chest>` — **OBSERVED** in both `front.webp` and
  `back.webp`: the deltoids are chunky blocks standing clear of the torso on both sides,
  and they, not the chest slab, set the shoulder width. **BUILT: the deltoid is narrower
  than the pelvis.** The section was measured as "how much bare skin appears on one row",
  which is not the part's section.
- `<upperArm, hangs-from, deltoid>` and `<glove, terminates, arm at hip height>` —
  **OBSERVED**: the arm runs from the shoulder down to roughly the widest-hip height, a
  span comparable to the torso's own. **BUILT: the whole arm chain is a short stub.**
- `<hairCap, encloses, cranium>`, `<spike, radiates-from, cap>` ×9 — Stage 2.
- `<sole, extends-forward-of, cuff>` — OBSERVED and BUILT correctly.
- `<pelvis, widens-below, belt>` then `<pelvis, tapers-to, crotch>` — OBSERVED and BUILT.

## Layer 5–6 — Materials & colour

One matte finish across the whole object; no gloss anywhere; no metal. Regions: yellow
hair · pink skin · violet shirt/pants (two values) · olive belt/boots · near-black
pauldron + gloves · grey bracer · printed face. Already covered by `palette.json`; nothing
here changes Stage 1, which carries no colour.

## Layer 7 — Identity-defining features

The three the current model gets wrong, in order of how much they cost:

1. **The hair mass**, both its width and its fore-aft depth. Stage 2.
2. **The deltoid's lateral protrusion.** This is what makes the figure read as
   broad-shouldered, and it is absent.
3. **The arm's LENGTH.** The reference's arms reach the hip; the model's do not reach the
   belt.

## Layer 8 — Uncertainty

- The cranium behind the face is `hidden` in every view (the cap covers it).
- The nose wedge's projection is `uncertain` — `right.webp` shows it clearly in profile
  but no view measures its depth against the face plane.
- The deltoid's true section is `occluded` on the figure's LEFT by the pauldron; the RIGHT
  is the authority, which §4[9] already said.

---

## What this changes

The current Stage 1 is a FAIL and the cause is not any single part. It is that the
measurements were taken without looking, so five of them measured a different thing than
the part, and the whole-figure instrument that noticed (Tier 1, IoU 0.201) was explained
away rather than believed.

The fix order:

1. **Restore Tier 1 as a real gate.** The §5.1 exclusion committed in `93a7995` was wrong.
   Crop the reference to the built region and match the camera so the comparison is fair —
   do not remove the comparison.
2. **Re-measure every section from the SILHOUETTE of that part's own region**, not from a
   colour band's run on one row. The band answers "how much of this colour is on this row";
   the part's section is a different question, and confusing them is the single error
   behind all five.
3. **Re-derive the arm chain's lengths and the deltoid's section**, which are the two
   biggest visual defects that do not depend on Stage 2.
4. Add the nose wedge to `parts.head` or record it as a deliberate omission.
