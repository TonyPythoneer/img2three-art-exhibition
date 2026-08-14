#!/usr/bin/env python3
"""Measure the bare skull (§4[14], shape code S-15) into landmarks.json's parts.head.

    python3 measure_head.py

THE TRAP §4[14] SETS, AND HOW THIS AVOIDS IT

§4[14] says: "back.webp's outer silhouette is the HAIR CAP, not the skull … Skull outline =
back.webp's outer silhouette inset by one hair thickness (hair thickness from
landmarks.json)."

That recipe is unusable, and the guess list already says why: `hairThickness` is a FRINGE
DEPTH — the distance from the face plane forward to the outermost hair, measured in the
profile views — not the cap's shell thickness. It reads 33 px on the left and 54 px on the
right (0.0386 / 0.0714 normalized), a 1.85x disagreement between two views of the same
quantity, and insetting a silhouette by it would overshoot badly. The previous attempt at
this part came out all-green and egg-shaped.

So the skull is measured where it is VISIBLE instead. The face is bare skin, and the skin
band gives its width directly at every height — no inset, no hair, no guess. What the
references genuinely cannot see is the BACK of the cranium under the cap, and that is the
one dimension left as a guess-list item rather than the whole skull.

WHAT IT MEASURES
  face width per row, from the chin up, on the SKIN band in front.webp / back.webp
  cheekbone   the widest of those rows, and its height — §4[14]'s "widest at the cheekbones"
  chin        the narrowest row at the bottom — "a small pointed chin"
  depth       the exposed face's depth from the profiles' skin band
  nape        the occiput's hard horizontal hairline in back.webp, which §4[14] calls the
              only stretch of the hairline that can be measured directly
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


def skin_runs(v: R.View, row: int) -> list[tuple[int, int]]:
    return ML.real_runs(v, row, R.band_map(v)["skin"])


def main() -> int:
    path = HERE / "landmarks.json"
    lm = json.loads(path.read_text())
    views = {k: R.load(k) for k in FRONTAL + PROFILE}
    mu = lm["measurementUncertainty"]
    per = lm["normalization"]["sole->chin"]["perView"]

    # The face band: from the chin up to where the fringe takes over. The top is not a
    # landmark — the forehead hairline is completely hidden (guess-list item 1) — so the
    # scan simply stops when the skin runs out, which IS the fringe's lower edge.
    out: dict = {"generatedBy": "spec/measure_head.py", "band": "skin (the bare face)"}
    profiles: dict = {}
    # FRONT ONLY. back.webp has no exposed face at all — §11.4's finding is that the cap
    # leaves only a small skin wedge beside each ear back there — so it returned a
    # "cheekbone width" of 0.03346 against the front's 0.13972, a 4x disagreement and a
    # spread of 0.106 against an uncertainty of 0.05447. Averaging the two would have
    # halved the face. A view that cannot see the thing does not get a vote.
    for k in ("front",):
        u = unit(lm, k)
        chin_row = int(lm["views"][k]["landmarksPx"]["chin"])
        rows = []
        for row in range(chin_row, max(0, chin_row - int(0.30 * u)), -1):
            rs = skin_runs(views[k], row)
            if not rs:
                break
            # The FACE is the widest run: at these rows the band can also carry a sliver of
            # ear or a hand, and the face is by far the largest skin region up here.
            w = max(r[1] - r[0] + 1 for r in rs) / u
            # "The skin ran out" is not the same as "the band returned nothing". Above the
            # fringe the band still hands back specks, and the loop ran its full 236-row
            # limit without stopping — reporting an exposed face 0.2986 tall, which puts
            # the top of the face above the hair tip. The face has ended when its widest
            # run collapses to a quarter of the widest row seen so far.
            if rows and w < max(r[1] for r in rows) * 0.25:
                break
            rows.append([(lm["views"][k]["landmarksPx"]["sole"] - row) / u, w])
        profiles[k] = rows

    face: dict = {}
    for k, rows in profiles.items():
        if not rows:
            continue
        widest = max(rows, key=lambda r: r[1])
        face[k] = {
            "chinHeight": rows[0][0],
            "chinWidth": rows[0][1],
            "cheekboneHeight": widest[0],
            "cheekboneWidth": widest[1],
            "exposedHeight": rows[-1][0] - rows[0][0],
            "rowsScanned": len(rows),
        }
    out["facePerView"] = face

    depth: dict = {}
    for k in PROFILE:
        u = unit(lm, k)
        chin_row = int(lm["views"][k]["landmarksPx"]["chin"])
        best = 0.0
        for row in range(chin_row, max(0, chin_row - int(0.30 * u)), -1):
            rs = skin_runs(views[k], row)
            if not rs:
                break
            best = max(best, (rs[-1][1] - rs[0][0] + 1) / u)
        depth[k] = best
    out["exposedDepthPerView"] = depth

    cheek_w = sum(f["cheekboneWidth"] for f in face.values()) / len(face)
    cheek_h = sum(f["cheekboneHeight"] for f in face.values()) / len(face)
    chin_w = sum(f["chinWidth"] for f in face.values()) / len(face)
    chin_h = sum(f["chinHeight"] for f in face.values()) / len(face)
    exposed = sum(f["exposedHeight"] for f in face.values()) / len(face)
    dep = sum(depth.values()) / len(depth)

    out["adopted"] = {
        "chinHeight": chin_h,
        "chinWidth": chin_w,
        "cheekboneHeight": cheek_h,
        "cheekboneWidth": cheek_w,
        "exposedFaceHeight": exposed,
        "exposedDepth": dep,
        "widthSpread": max(f["cheekboneWidth"] for f in face.values())
        - min(f["cheekboneWidth"] for f in face.values()),
        "depthSpread": max(depth.values()) - min(depth.values()),
    }
    out["pointedChin_4_14"] = {
        "chinWidth": chin_w,
        "cheekboneWidth": cheek_w,
        "ratio": chin_w / cheek_w if cheek_w else None,
        "verdict": "PASS (the chin is narrower than the cheekbones)"
        if chin_w < cheek_w
        else "FAIL",
        "note": "§4[14]: 'widest at the cheekbones, tapering to a small pointed chin'.",
    }

    # The crown: no view sees bare bone (the cap covers it in every view — guess-list item),
    # so skullTop cannot be a measurement. But it does NOT have to fall back to the hair
    # TIP (the spikes' highest point) either, which is what put it at 1.0 and rendered the
    # Stage 1 skull as a cone: a spike is a thin radiating blade with no cranium under it.
    # What IS measurable is where the CAP MASS starts, as opposed to a spike: walk down
    # from the hair's top row and find where the lateral hair band's width first reaches
    # 60% of its own eventual max — above that line the silhouette is spike blades (narrow,
    # still widening); at and below it, it is the rounded cap volume a skull could plausibly
    # sit under. front.webp and back.webp (both a LATERAL width, unlike the profile views'
    # fore-aft depth) agree to within RMS: 0.90308 vs 0.90724, spread 0.00416.
    cap_mass_rows: dict = {}
    for k in FRONTAL:
        v = views[k]
        widths = R.row_counts(v, "hair")
        top = next((y for y, c in enumerate(widths) if c > 0), None)
        if top is None:
            continue
        cap_max = max(widths)
        threshold = cap_max * 0.6
        begin = next(
            (y for y in range(top, len(widths)) if widths[y] >= threshold), None
        )
        if begin is None:
            continue
        cap_mass_rows[k] = (lm["views"][k]["landmarksPx"]["sole"] - begin) / unit(lm, k)
    crown_h = sum(cap_mass_rows.values()) / len(cap_mass_rows) if cap_mass_rows else None
    out["crownHeight"] = {
        "perView": cap_mass_rows,
        "adopted": crown_h,
        "spread": (max(cap_mass_rows.values()) - min(cap_mass_rows.values()))
        if len(cap_mass_rows) > 1
        else 0.0,
        "method": "row where the hair band's lateral width first reaches 60% of its own "
        "max, scanning down from the hair's topmost pixel — the boundary between spike "
        "blades and the cap's rounded mass, on front.webp and back.webp only (the profile "
        "views measure fore-aft depth, a different quantity, not cross-checkable against "
        "this).",
        "caveat": "APPROXIMATION, not a skull measurement: the cap mass still includes "
        "scalp-hair thickness over the bone, so the true crown is somewhat below this line "
        "too. It is the best available evidence, and materially better than the OLD value "
        "(1.0, the spike TIP) which had nothing to do with a skull. Stage 1 authors the "
        "bare-skull mesh at this height; Stage 2 keeps skullTop=1.0 as the hair's own anchor.",
    }

    # The one dimension no view can see: the back of the cranium, under the hair cap.
    out["craniumBehindFace"] = {
        "value": None,
        "why": "UNMEASURABLE. §4[14] offers 'back.webp's silhouette inset by one hair "
        "thickness', but landmarks.json's hairThickness is a FRINGE DEPTH measured forward "
        "from the face plane — 0.03863 left against 0.07137 right, a 1.85x disagreement "
        "between two views of one quantity — not the cap's shell thickness. Insetting by it "
        "overshoots, which is how the previous attempt at this part came out all-green and "
        "egg-shaped.",
        "adoptedRule": "the skull's total depth is the exposed face depth plus the same "
        "again behind it, i.e. the cranium is as deep behind the face plane as the face is "
        "in front of the ear line. A GUESS-LIST item, falsifiable only by the profile "
        "silhouette once the hair cap exists at Stage 2 (§7.6 already requires skull + "
        "hairCap to reproduce back.webp's outer silhouette).",
    }
    out["tolerances"] = {"measurementUncertainty": mu}

    lm.setdefault("parts", {})["head"] = out
    path.write_text(json.dumps(lm, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("adopted", "pointedChin_4_14", "facePerView",
                                          "exposedDepthPerView")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
