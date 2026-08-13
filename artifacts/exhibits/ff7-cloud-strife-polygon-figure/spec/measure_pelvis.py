#!/usr/bin/env python3
"""Measure the pelvis (§4[6], shape code S-06) into landmarks.json's parts.pelvis.

    python3 measure_pelvis.py

THE TWO THINGS THAT WERE STUCK, AND HOW EACH IS UNSTUCK
-------------------------------------------------------
1. Self-check B (the profile KITE) came back INDETERMINATE in both profile views with the
   note "glove occludes the hip outline". That is true of the SILHOUETTE and only of the
   silhouette: the gloves are near-black and the pants are purple, so the occlusion
   disappears the moment the outline is taken on the PURPLE BAND instead. Everything here
   is measured on that band.

2. Self-check A ("the widest point must be WIDER THAN THE SHOULDERS", §4[6]) FAILS by
   0.0965 — hip 0.28325 against shoulder 0.37978, nearly twice the uncertainty, so it is a
   real disagreement and not an undecided one. It is NOT silently resolved here. §0.6 says
   where a script disagrees with the prompt the script wins and the discrepancy is
   reported, so this records both the failure and the neighbouring check that PASSES
   (A1: the hip is wider than the CHEST SLAB, by 0.0851) and leaves the shape to follow the
   measurement.

WHAT IT MEASURES
  pentagon (front + back)  width at pelvisTop, the widest width and its height, the crotch
                           notch apex, and the notch's own width
  kite (left + right)      depth at pelvisTop, the deepest depth and its height, and the
                           front/back symmetry of the deepest row about the torso axis
  hip sockets              where each leg's centre line sits in x at the crotch, which is
                           what hipL / hipR have to emit
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
    px = lm["views"][view]["landmarksPx"]
    return int(round(px["sole"] - height * unit(lm, view)))


def purple_runs(v: R.View, row: int) -> list[tuple[int, int]]:
    return ML.real_runs(v, row, R.band_map(v)["purple"])


def main() -> int:
    path = HERE / "landmarks.json"
    lm = json.loads(path.read_text())
    views = {k: R.load(k) for k in FRONTAL + PROFILE}
    mu = lm["measurementUncertainty"]
    per = lm["normalization"]["sole->chin"]["perView"]
    top_h = per["front"]["beltBottom"]        # pelvisTop, the ledger's own name for it
    crotch = sum(per[k]["crotchNotchApex"] for k in FRONTAL) / len(FRONTAL)

    out: dict = {"generatedBy": "spec/measure_pelvis.py", "band": "purple"}

    # ---- the PENTAGON, front and back ----
    pent: dict = {}
    for k in FRONTAL:
        v, u = views[k], unit(lm, k)
        r_top, r_bot = row_of(lm, k, top_h), row_of(lm, k, crotch)
        prof = []
        for row in range(r_top, r_bot + 1):
            rs = purple_runs(v, row)
            if rs:
                prof.append((row, rs[-1][1] - rs[0][0] + 1, len(rs)))
        if not prof:
            continue
        widest = max(prof, key=lambda p: p[1])
        # The crotch notch apex is ALREADY measured, per view, by measure_landmarks.py, and
        # re-deriving it here as "the topmost row with two runs" gets it wrong: at
        # pelvisTop the purple band is already multi-run, because shirt purple and pants
        # purple fall in the same band and the belt's shading splits them. Reuse the
        # landmark rather than inventing a second, worse instrument for it.
        split = row_of(lm, k, per[k]["crotchNotchApex"])
        # The notch's width, measured a little BELOW the apex. At the apex itself the two
        # runs are one pixel apart by definition — that is what "apex" means — so measuring
        # there returns 0 and says nothing. Sampled 8% of the pelvis's height down, where
        # the V has opened but the legs have not yet started to splay.
        notch = None
        if split is not None:
            probe = min(int(split + 0.08 * (r_bot - r_top)), r_bot)
            rs = purple_runs(v, probe)
            if len(rs) >= 2:
                notch = (rs[-1][0] - rs[0][1]) / u
        pent[k] = {
            "widthAtPelvisTop": prof[0][1] / u,
            "widestWidth": widest[1] / u,
            "widestHeight": (lm["views"][k]["landmarksPx"]["sole"] - widest[0]) / u,
            "crotchNotchHeight": None
            if split is None
            else (lm["views"][k]["landmarksPx"]["sole"] - split) / u,
            "notchWidth": notch,
        }
    out["pentagon"] = pent

    # ---- the KITE, both profiles, on the purple band so the glove cannot occlude it ----
    kite: dict = {}
    for k in PROFILE:
        v, u = views[k], unit(lm, k)
        r_top, r_bot = row_of(lm, k, top_h), row_of(lm, k, crotch)
        prof = []
        for row in range(r_top, r_bot + 1):
            rs = purple_runs(v, row)
            if rs:
                prof.append((row, rs[0][0], rs[-1][1]))
        if not prof:
            continue
        deepest = max(prof, key=lambda p: p[2] - p[1])
        # front/back symmetry: the deepest row's two edges against the MIDPOINT of the
        # pelvis's own top section, which is the closest thing to a torso axis a profile
        # view carries. §4[6] calls the kite "FRONT/BACK SYMMETRIC", so this is the number
        # that decides whether that is true.
        axis = (prof[0][1] + prof[0][2]) / 2
        front_reach = abs(deepest[1] - axis) / u
        back_reach = abs(deepest[2] - axis) / u
        # §1.2: left.webp has model +Z = -image x; right.webp the other way round.
        if k == "right":
            front_reach, back_reach = back_reach, front_reach
        kite[k] = {
            "depthAtPelvisTop": (prof[0][2] - prof[0][1] + 1) / u,
            "maxDepth": (deepest[2] - deepest[1] + 1) / u,
            "maxDepthHeight": (lm["views"][k]["landmarksPx"]["sole"] - deepest[0]) / u,
            "frontReach": front_reach,
            "backReach": back_reach,
            "frontBackAsymmetry": abs(front_reach - back_reach),
        }
    out["kite"] = kite
    asym = max((s["frontBackAsymmetry"] for s in kite.values()), default=0.0)
    out["kiteSymmetry_4_6"] = {
        "worstAsymmetry": asym,
        "measurementUncertainty": mu,
        "verdict": "PASS (front/back symmetric)" if asym < mu else "FAIL",
        "note": "self-check B was INDETERMINATE on the SILHOUETTE because the glove sits in "
        "front of the hip. On the purple band the glove is not there at all — it is "
        "near-black — so the outline is the trouser's own.",
    }

    # ---- the hip sockets: each leg's centre line in x, at the crotch ----
    hips: dict = {}
    for k in FRONTAL:
        v, u = views[k], unit(lm, k)
        row = row_of(lm, k, crotch) + 4
        rs = purple_runs(v, row)
        if len(rs) < 2:
            continue
        axis = (rs[0][0] + rs[-1][1]) / 2
        centres = sorted(((r[0] + r[1]) / 2 - axis) / u for r in rs)
        # front.webp: image +x IS model +X, so the figure's LEFT is the image-right run.
        # back.webp is mirrored, so the sign flips (§1.2).
        sign = 1.0 if k == "front" else -1.0
        hips[k] = {"legCentreOffsetX": abs(centres[-1]) , "signedFromImage": [c * sign for c in centres]}
    out["hipSocketX"] = {
        "perView": hips,
        "adopted": sum(h["legCentreOffsetX"] for h in hips.values()) / len(hips) if hips else None,
        "crossViewSpread": (
            max(h["legCentreOffsetX"] for h in hips.values())
            - min(h["legCentreOffsetX"] for h in hips.values())
        )
        if len(hips) > 1
        else 0.0,
    }

    # ---- adopted dimensions ----
    widest = sum(p["widestWidth"] for p in pent.values()) / len(pent)
    out["adopted"] = {
        "height": top_h - crotch,
        "topHeight": top_h,
        "crotchHeight": crotch,
        "widthAtTop": sum(p["widthAtPelvisTop"] for p in pent.values()) / len(pent),
        "widestWidth": widest,
        "widestHeight": sum(p["widestHeight"] for p in pent.values()) / len(pent),
        "depthAtTop": sum(s["depthAtPelvisTop"] for s in kite.values()) / len(kite),
        "maxDepth": sum(s["maxDepth"] for s in kite.values()) / len(kite),
        "maxDepthHeight": sum(s["maxDepthHeight"] for s in kite.values()) / len(kite),
        "notchWidth": sum(p["notchWidth"] for p in pent.values() if p["notchWidth"])
        / max(1, len([p for p in pent.values() if p["notchWidth"]])),
        "widthSpread": max(p["widestWidth"] for p in pent.values())
        - min(p["widestWidth"] for p in pent.values()),
        "depthSpread": max(s["maxDepth"] for s in kite.values())
        - min(s["maxDepth"] for s in kite.values()),
    }

    # ---- the §4[6] disagreement, reported not resolved ----
    checks = lm["selfChecks"]
    out["widestPoint_4_6"] = {
        "claim": "§4[6]: the widest point must be WIDER THAN THE SHOULDERS",
        "measuredHipWidth": widest,
        "shoulderWidth": lm["dimensions"]["shoulderWidth"],
        "chestSlabWidth": lm["dimensions"]["chestWidth"],
        "vsShoulderLine": checks["A_hipWiderThanShoulderLine"],
        "vsChestSlab": checks["A1_hipWiderThanChestSlab"],
        "verdict": "the claim is FALSE against the shoulder LINE and TRUE against the chest "
        "SLAB. The shoulder line's 0.37978 is the whole silhouette across both deltoids, "
        "which is what a shoulder width is; the hip's 0.28325 is nowhere near it, and the "
        "gap is 0.0965 against an uncertainty of 0.05447 — decided, not undecided.",
        "applied": "the measurement. §0.6: where a script disagrees with this document, THE "
        "SCRIPT WINS. The pelvis is built at its measured width and stays the widest thing "
        "in the LOWER body, which is what §4[6]'s other sentence — 'the largest volume in "
        "the model and the part that decides the silhouette' — is actually about.",
    }

    lm.setdefault("parts", {})["pelvis"] = out
    path.write_text(json.dumps(lm, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("adopted", "kiteSymmetry_4_6", "hipSocketX", "widestPoint_4_6")},
                     indent=2)[:2600])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
