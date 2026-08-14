# Plan — rebuild Stage 1 on a working instrument

Diagnosis is in `spec/image-analysis.md`; it is not repeated here. One line of it drives
this whole plan:

> the measurements were taken without looking, so five of them measured a different thing
> than the part, and the whole-figure instrument that noticed was explained away.

So the order below fixes the **instrument** first, the **method** second, and the
**geometry** last. Rebuilding geometry first would mean judging the rebuild with the same
blind gates that passed the broken version 200-plus assertions to nil.

## What is NOT being redone

Churning working parts is how a rebuild loses more than it fixes. These stay:

| kept | why it is trusted |
|---|---|
| `sole` | cross-checked against a second instrument (front/back vs left/right agree to 0.0029) and reads correctly in the profile render |
| `ankle` | section vs `straightPantTubeWidth`, an independent script, agrees |
| `pantLeg` ×3 | `sharedSection.widthX` 0.05643 vs `dimensions.straightPantTubeWidth` 0.06097 — different script, different row, agrees |
| `pelvis` | kite symmetry 0.0375 measured on the purple band after the glove occlusion was removed |
| the socket ledger | 21 joints verified in the render at 0.000e+00; the chain is sound even where the sections are not |
| `socket_gate.py`, `gate_facets.py` | both proven to FAIL on the defect they name |

`chest`, `waist`, the four arm factories and `head` are in scope.

---

## Phase 0 — make the whole-figure check honest, and record today's score

**Nothing else can be judged until a number exists that moves when the model improves.**

1. **Revert the §5.1 exclusion** committed in `93a7995`. Tier 1 against the whole figure
   was right to fail; excluding it was wrong.
2. **`spec/gate_silhouette.py`** — a fair four-view comparison:
   - render with an **orthographic camera scaled by the sole→chin anchor**, the one span
     complete in all five references, instead of framing the model to fit. Scale delta
     0.781 was the auto-framing, not the model.
   - mask the reference to the **built region** — chin down for Stage 1 — so the missing
     hair is excluded by construction rather than by argument.
   - report per-view IoU plus the four extents, so a failure says *where*.
3. **Pin the threshold with fake frames**, never guess it:
   - reference against itself → must score ~1.0
   - reference against a same-height solid rectangle → must FAIL (the floor)
   - reference against its own mirror → the bilateral-noise ceiling, already known to be
     0.858 whole-figure
   Threshold sits between the rectangle and the mirror, and both margins get recorded.
4. **Record today's score as the baseline.** Every later phase must move it. A phase that
   does not is a wrong reading, not a wrong number — §0.3's three-corrections rule.

**Done when:** `gate_silhouette.py` runs, its threshold is pinned by frames that separate,
and the current figure's four IoUs are in `landmarks.json`.

## Phase 1 — fix the measuring method once, not five more times

The five errors are one error: **a colour band's run on one row was used as the part's
section.** The band answers "how much of this colour is on this row". A part's section is a
different question.

1. **`spec/section.py`**, one shared helper, replacing the per-script ad-hoc reads:
   - the band **identifies which run belongs to the part**; the part's extent is then that
     run's full silhouette extent, not the band's.
   - **occlusion fallback**: when the part is covered on one side (the pauldron over the
     figure's left deltoid), measure the other side and say so in the record. §4[9] already
     names the right shoulder as the authority.
   - **fragmentation**: when an overlay splits the part (the chest straps), span the
     fragments; when a neighbour shares the row (the forearms at belt height), do not.
     The rule is one line and belongs in the helper: *can this band hold something that is
     not the part, on this row?*
2. **Every `measure_*.py` re-run through it**, including the parts being kept — a kept part
   whose number changes was never trusted, only lucky.
3. **Every section cross-checked** against `dimensions.*` where a second script already
   measured the same quantity. A disagreement above the RMS is a stop.

**Done when:** every `parts.*` section carries a cross-check field, and no part's own
measurement disagrees with an independent one by more than `measurementUncertaintyRms`
(0.01374) — the RMS, not the 0.05447 cross-view figure, which is too loose to catch this.

## Phase 2 — the two defects that do not depend on Stage 2

Both are visible in the comparison sheet without any hair.

1. **The deltoid's section.** Measured 0.09595 as bare skin on one row; the part reads
   narrower than the pelvis while the reference's deltoids set the shoulder width. Re-measure
   as the deltoid run's own extent on the figure's RIGHT, in `front.webp` and `back.webp`,
   and cross-check against `shoulderWidth` (0.37978) minus the chest slab — two independent
   routes to one number.
2. **The arm chain's lengths.** `fist` at 0.33151 is already known to sit BELOW the glove —
   the black band is empty there. So the ledger's `elbow` and `fist` are both suspect.
   Re-derive from the arm's own silhouette: shoulder → the row where the deltoid run
   detaches from the torso → the elbow break → the glove's bottom.

**Done when:** the arm reaches hip height and the shoulder span is set by the deltoids, and
`gate_silhouette.py` has moved from the Phase 0 baseline.

## Phase 3 — the head, which is wrong in its own way

Separate phase because its defect is in the **ledger**, not in a section.

1. `SOCKET_Y.skullTop` is 1.0 — the **extrapolated hair tip**, not bone. The bare skull is
   built 0.2836 tall from it and renders as a cone. Derive a real crown height, or make the
   head's origin the crown and record `skullTop` as the hair's anchor rather than the
   skull's.
2. **The nose.** `right.webp` shows a triangular wedge in relief. §2 c) rules eyes, pupils
   and brows out as printed art — correctly, they are print — but the nose is not print.
   Either add it to `parts.head` or record the omission in the guess list with a reason.
   Silence is the one option that is not available.

**Done when:** the head's profile silhouette matches `right.webp`'s skull region, and the
nose is either built or written down as deliberately absent.

## Phase 4 — re-gate everything, then Stage 1B

1. All eleven part gates re-run on fresh captures — a stale capture must fail, and
   `gate_facets.py` already proves it does.
2. `gate_silhouette.py` four views, against the Phase 0 baseline.
3. Only then Stage 1B, whose integration file authors no geometry.

**CLOSED.** `mountCloudStrifeViewer.ts`'s `buildAssembled()` — written earlier this phase to
make the socket chain visible for Phase 0–3's own debugging — turned out to already BE
Stage 1B's integration file: it authors zero geometry, places every Stage-1-built part by
the §4 socket ledger, and the whole-figure `gate_silhouette.py` PASS above was measured
against exactly its output. Re-confirmed on a fresh capture rather than trusted on the
number already in hand: `gate_assembly.py` 26/26, `gate_naming.py` 24/24, `gate_facets.py`
23/23, `gate_silhouette.py` mean IoU 0.740. See `HANDOFF.md` for the full table. Stage 2 is
next and was not started — it is new scope (face/hair/ears/decoration), not this plan's.

---

## The rule this plan is really enforcing

`gate_assembly.py` refuses to pass when every joint is skipped, because a gate that checks
nothing is worse than no gate. **The same test applied to the whole of Stage 1 is what was
missing**: eleven gates, 200-plus assertions, all green, on a model nobody had compared to
the reference. Phase 0 exists so that cannot happen twice.
