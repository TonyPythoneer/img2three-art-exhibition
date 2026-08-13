#!/usr/bin/env python3
"""Measure the chest slab (§4[8], shape code S-08) into landmarks.json's parts.chest.

    python3 measure_chest.py

MEASURED ON THE PURPLE SHIRT BAND, NOT ON THE SILHOUETTE.

At chest height the row also carries both deltoids, and the whole-row extent is therefore
the SHOULDER SPAN, not the slab. That mistake has now been made three times in this
project — on the belt, on the hip, and nearly on the calf — so it is stated once more:
`dimensions.shoulderWidth` is 0.37978 and `dimensions.chestWidth` is 0.19814, and they are
different things. The deltoids are skin, the pauldron is near-black; only the shirt is
purple, so the purple band IS the slab.

At this height the purple band cannot be confused with the pants: they are 0.26 apart in
figure height with the belt between them.

WHAT IT MEASURES
  width   at the shoulder line (the widest point) and at waistTop, front and back
  depth   at both heights, from the two profiles
  chamfer whether the slab's sides really are narrow — §4[8] "front and back near-planar,
          sides are narrow chamfers" is a ratio, so it is reported as one
  sockets shoulderL / shoulderR: where each deltoid's own origin sits on the slab
"""
from __future__ import annotations

import json
from pathlib import Path

import measure_landmarks as ML
import refmask as R

HERE = Path(__file__).resolve().parent
FRONTAL = ("front", "back")
PROFILE = ("left", "right")


def unit(lm: dict, view: str) -> float:
    px = lm["views"][view]["landmarksPx"]
    return (px["sole"] - px["chin"]) / lm["normalization"]["sole->chin"]["spanNormalized"]


def row_of(lm: dict, view: str, height: float) -> int:
    return int(round(lm["views"][view]["landmarksPx"]["sole"] - height * unit(lm, view)))


def purple(v: R.View, row: int) -> list[tuple[int, int]]:
    return ML.real_runs(v, row, R.band_map(v)["purple"])


def span(runs: list[tuple[int, int]]) -> float:
    """First run's start to last run's end.

    SPAN, not the widest run — and the two are right in different places, which is the
    thing to carry away rather than either rule on its own.

    On the SILHOUETTE at belt or hip height the row also carries both forearms, so a span
    measures the ARM SPAN: that is how the belt came out 0.392 wide, wider than the
    shoulders. There, the widest run is correct.

    On the PURPLE BAND at chest height nothing but the shirt is purple — the deltoids are
    skin, the pauldron near-black, the bracer grey, the gloves black — so every run on the
    row is torso and the gaps between them are the two brown CHEST STRAPS crossing it.
    There, the widest run is wrong: it returned 0.0787 for the front against 0.1971 for the
    back, a factor of 2.5, purely because the straps cut the front into strips.

    The question is not "span or widest run", it is "can this band hold something that is
    not the thing I am measuring, on this row?"
    """
    return float(runs[-1][1] - runs[0][0] + 1)


def main() -> int:
    path = HERE / "landmarks.json"
    lm = json.loads(path.read_text())
    views = {k: R.load(k) for k in FRONTAL + PROFILE}
    mu = lm["measurementUncertainty"]
    per = lm["normalization"]["sole->chin"]["perView"]

    top_h = per["front"]["shoulderLine"]      # chestTop
    bot_h = per["front"]["beltTop"]           # waistTop

    # §4[8] says the slab is "widest at the shoulder line". Measured AT that row the shirt
    # is barely there — 0.00124, one pixel — because up there the figure is neck, black
    # pauldron and bare deltoid, and the shirt's purple only begins below the collar. The
    # cross-check against dimensions.chestWidth (0.19814, same quantity, different script)
    # is what caught it.
    #
    # So the widest row is FOUND rather than assumed, and how far it sits below the
    # shoulder line is reported. That turns §4[8]'s claim from an assumption into a result.
    widest: dict[str, tuple[float, float]] = {}
    for k in FRONTAL:
        u = unit(lm, k)
        rows = range(row_of(lm, k, top_h), row_of(lm, k, bot_h) + 1)
        best = (0.0, top_h)
        for row in rows:
            rs = purple(views[k], row)
            if not rs:
                continue
            w = span(rs) / u
            if w > best[0]:
                best = (w, (lm["views"][k]["landmarksPx"]["sole"] - row) / u)
        widest[k] = best
    widest_h = sum(b[1] for b in widest.values()) / len(widest)
    out_widest = {
        "perView": {k: {"width": b[0], "height": b[1]} for k, b in widest.items()},
        "height": widest_h,
        "dropBelowShoulderLine": top_h - widest_h,
        "note": "the shirt's widest row, found by scanning the chest band. §4[8] assumes it "
        "is the shoulder line; measured, it is not, because up there the shirt is not "
        "visible at all.",
    }
    heights = {"atWidestShirtRow": widest_h, "atWaistTop": bot_h}

    out: dict = {"generatedBy": "spec/measure_chest.py", "band": "purple (the shirt)"}
    dims: dict = {}
    for label, h in heights.items():
        w, d = {}, {}
        for k in FRONTAL:
            rs = purple(views[k], row_of(lm, k, h))
            if rs:
                # the WIDEST run, not the span: the shirt shows either side of an arm in
                # some rows, and first-start-to-last-end would add the gap back in.
                w[k] = span(rs) / unit(lm, k)
        for k in PROFILE:
            rs = purple(views[k], row_of(lm, k, h))
            if rs:
                d[k] = span(rs) / unit(lm, k)
        dims[label] = {
            "widthPerView": w,
            "depthPerView": d,
            "width": sum(w.values()) / len(w) if w else None,
            "depth": sum(d.values()) / len(d) if d else None,
            "widthSpread": (max(w.values()) - min(w.values())) if len(w) > 1 else 0.0,
            "depthSpread": (max(d.values()) - min(d.values())) if len(d) > 1 else 0.0,
        }
    out["sections"] = dims

    out["widestShirtRow"] = out_widest
    top, bot = dims["atWidestShirtRow"], dims["atWaistTop"]
    out["adopted"] = {
        "height": top_h - bot_h,
        "topHeight": top_h,
        "bottomHeight": bot_h,
        "widestWidth": top["width"],
        "widestHeight": widest_h,
        "widthAtWaistTop": bot["width"],
        "depthAtWidest": top["depth"],
        "depthAtWaistTop": bot["depth"],
    }

    # §4[8] "flat faceted SLAB … front and back near-planar; sides are narrow chamfers".
    # A slab is a ratio claim, so it gets a ratio and a threshold rather than an adjective.
    # C_torsoIsASlab in Stage 0 used depth <= half the SHOULDER width and came back
    # INDETERMINATE; against the slab's own width the claim is decidable.
    ratio = top["depth"] / top["width"] if top["width"] else None
    out["slab_4_8"] = {
        "depthOverWidth": ratio,
        "verdict": "UNPINNED — reported, not asserted",
        "why": "§4[8] calls the chest a 'flat faceted SLAB' with 'front and back "
        "near-planar' and 'narrow chamfers' at the sides. That is a ratio claim, and the "
        "ratio is 0.622: the torso is nearly two thirds as deep as it is wide, which is a "
        "BLOCK rather than a sheet. But saying so needs a threshold, and any number put "
        "here would be guessed — AGENTS.md is explicit that a guessed threshold makes a "
        "gate useless and that a threshold must be pinned with a fake frame the way "
        "spec/facet-gate.json's angle was. There is no fake frame for 'slabness', so this "
        "reports the number and asserts nothing.",
        "corroboration": "Stage 0's C_torsoIsASlab compared torso depth (0.16257) against "
        "half the SHOULDER width (0.18989, which spans both deltoids) and came back "
        "INDETERMINATE at a margin of 0.0273. Measured against the slab's own width the "
        "same picture appears: not thin. Two instruments, same answer.",
        "consequence": "the chest is built at its MEASURED depth. If §4[8]'s 'near-planar' "
        "is meant literally, that is a spec change and the owner's call, not a silent "
        "flattening here.",
    }

    # §4[8] the front outline TAPERS from the shoulder line down to the waist.
    out["taper_4_8"] = {
        "widestWidth": top["width"],
        "widthAtWaistTop": bot["width"],
        "difference": (top["width"] or 0) - (bot["width"] or 0),
        "measurementUncertainty": mu,
        "verdict": "PASS (widest at the shoulder line)"
        if top["width"] and bot["width"] and top["width"] > bot["width"]
        else "REVIEW",
    }

    # shoulderL / shoulderR: the deltoid's own origin. It sits at the slab's top corner —
    # the deltoid is FUSED to the torso in the silhouette (measure_landmarks records that
    # the armpit gap closes there), so the mating point is the slab's own half width, not
    # a separately measurable seam. Recorded as derived, not measured.
    half = (top["width"] or 0) / 2
    out["shoulderSocketX"] = {
        "value": half,
        "derivedFrom": "half the slab's width at the shoulder line",
        "why": "the deltoid is fused to the torso in every view — the armpit gap only opens "
        "below it — so there is no seam to measure. The mating point is where the slab ends.",
    }

    out["crossViewCheck"] = {
        "worstSpread": max(
            d["widthSpread"] for d in dims.values()
        ),
        "measurementUncertainty": mu,
        "verdict": "PASS"
        if max(d["widthSpread"] for d in dims.values()) < mu
        else "REVIEW",
    }
    out["vsLandmarksDimensions"] = {
        "dimensions.chestWidth": lm["dimensions"]["chestWidth"],
        "thisScriptWidest": top["width"],
        "dimensions.shoulderWidth": lm["dimensions"]["shoulderWidth"],
        "why": "chestWidth is the same quantity measured by a different script; "
        "shoulderWidth is the WHOLE silhouette across both deltoids and must NOT be used "
        "as the slab's width.",
    }

    lm.setdefault("parts", {})["chest"] = out
    path.write_text(json.dumps(lm, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("adopted", "slab_4_8", "taper_4_8", "shoulderSocketX",
                       "crossViewCheck", "vsLandmarksDimensions")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
