#!/usr/bin/env python3
"""prompt.txt §3.3 — the colour table, sampled by clustering, identified by position.

    python3 sample_palette.py        # writes palette.json, prints the report

Two rules from §2 that this file exists to obey:

  1. NO EYE-DROPPER. A hand-picked point lands on a facet boundary and returns a
     blended colour. Every value here is the centroid of a cluster of pixels, and the
     cluster is chosen by WHERE it sits on the figure (which band, which rows),
     never by what it looks like.

  2. THE REDUCTION RULE IS WRITTEN DOWN AND APPLIED. §2 records an ADOPTED value per
     code without saying how the per-view samples became it, and notes the adopted
     column is not their plain mean. This script adopts the PIXEL-COUNT WEIGHTED MEAN
     over the four orthographic views, and prints the plain mean and the median beside
     it so the choice is visible rather than implied.

Region boundaries come from landmarks.json (§0.6: every number traces to an artefact),
so the belt is "the olive between the shirt and the pants" here for exactly the same
reason it is there.

Pure stdlib + Pillow.
"""
from __future__ import annotations

import json
from pathlib import Path

import refmask as R

HERE = Path(__file__).resolve().parent
OUT = HERE / "palette.json"
LANDMARKS = HERE / "landmarks.json"

# The four flat-lit orthographic product shots. more-angle is a lit three-quarter
# marketing shot and is sampled for REFERENCE only: §2 adopts the cool set because the
# three cool views cross-validate each other and the neutral grey bracer reads the same
# in both sets, which makes the difference saturation rather than white balance.
COOL = R.ORTHO
WARM = "more-angle"


def _hex(rgb) -> str:
    return "#%02X%02X%02X" % tuple(int(round(c)) for c in rgb)


def region_masks(v: R.View, lm: dict) -> dict[str, bytearray]:
    """Spatial regions, cut by the landmark rows rather than by colour similarity.

    shirt-purple and pants-purple are the same colour family (their cluster mean y
    differ by 0.007 of figure height), and belt-olive, strap-olive and boot-olive are
    another. Only their ROWS separate them, and the rows come from landmarks.json.
    """
    bands = R.band_map(v)
    w, h = v.w, v.h
    px = lm["views"][v.name]["landmarksPx"]
    belt_top = px.get("beltTop")
    belt_bot = px.get("beltBottom")
    out: dict[str, bytearray] = {}

    def cut(band: str, y0: int | None, y1: int | None) -> bytearray:
        src = bands[band]
        m = bytearray(w * h)
        lo = 0 if y0 is None else max(0, y0)
        hi = h if y1 is None else min(h, y1 + 1)
        m[lo * w : hi * w] = src[lo * w : hi * w]
        return m

    out["hair"] = bands["hair"]
    out["skin"] = bands["skin"]
    out["black"] = bands["black"]
    out["grey"] = bands["grey"]
    if belt_top is not None and belt_bot is not None:
        out["shirt"] = cut("purple", None, belt_top - 1)
        out["pants"] = cut("purple", belt_bot + 1, None)
        out["belt"] = cut("olive", belt_top, belt_bot)
        out["strap"] = cut("olive", None, belt_top - 1)
    olive_groups = R.split_rows(v, "olive")
    if olive_groups:
        boot = max(olive_groups, key=lambda g: g["y1"])
        out["boot"] = cut("olive", boot["y0"], boot["y1"])
    return {k: m for k, m in out.items() if sum(m) > 0}


def cluster_region(v: R.View, mask: bytearray, quant: int = R.QUANT) -> list[dict]:
    """Same quantise-then-merge as refmask.cluster, restricted to one region."""
    w, h = v.w, v.h
    height = v.y1 - v.y0 + 1
    axis = (v.x0 + v.x1) / 2.0
    buckets: dict[tuple[int, int, int], list[float]] = {}
    for y in range(h):
        row = y * w
        for x in range(w):
            if not mask[row + x]:
                continue
            r, g, b = v.px[x, y]
            key = (r // quant, g // quant, b // quant)
            e = buckets.get(key)
            if e is None:
                e = buckets[key] = [0.0] * 6
            e[0] += 1
            e[1] += r
            e[2] += g
            e[3] += b
            e[4] += (y - v.y0) / height
            e[5] += (x - axis) / height
    merged: list[list[float]] = []
    for e in sorted(buckets.values(), key=lambda e: -e[0]):
        c = (e[1] / e[0], e[2] / e[0], e[3] / e[0])
        for m in merged:
            mc = (m[1] / m[0], m[2] / m[0], m[3] / m[0])
            if sum((a - b) ** 2 for a, b in zip(c, mc)) ** 0.5 < R.MERGE_DIST:
                for i in range(6):
                    m[i] += e[i]
                break
        else:
            merged.append(list(e))
    total = sum(m[0] for m in merged) or 1
    return [
        {
            "hex": _hex((m[1] / m[0], m[2] / m[0], m[3] / m[0])),
            "rgb": [m[1] / m[0], m[2] / m[0], m[3] / m[0]],
            "pixels": int(m[0]),
            "shareOfRegion": m[0] / total,
            "meanY": m[4] / m[0],
            "meanX": m[5] / m[0],
        }
        for m in sorted(merged, key=lambda e: -e[0])
    ]


# code -> (region, which cluster of that region)
#   "dominant" = the largest cluster; "shadow" = the largest cluster that is darker
#   than the dominant one. The lit/shadow split is a POSITION-free but still
#   mechanical choice, and it is the only place this file ranks by appearance.
CODES = {
    "C-01": ("skin", "dominant", "skin (lit)"),
    "C-01s": ("skin", "shadow", "skin (mid/shadow)"),
    "C-02": ("hair", "dominant", "hair yellow"),
    "C-03": ("shirt", "dominant", "shirt purple"),
    "C-04": ("pants", "dominant", "pants purple"),
    "C-05": ("belt", "dominant", "belt olive-brown"),
    "C-05b": ("boot", "dominant", "boot olive-brown"),
    "C-06": ("strap", "dominant", "strap brown (UNSCHEDULED part; sampled for reference)"),
    "C-07": ("black", "dominant", "near-black (gloves + pauldron)"),
    "C-08": ("grey", "dominant", "bracer grey"),
}


# prompt.txt §2's ADOPTED column, quoted ONLY so the report can diff against it.
# Evidence about the prompt, not about the figure — nothing downstream may read it.
PROMPT_ADOPTED = {
    "C-01": "#E0C2BA", "C-01s": "#CFB5AF", "C-02": "#D0B063", "C-03": "#4C4A7C",
    "C-04": "#454280", "C-05": "#564C44", "C-05b": "#443F33", "C-07": "#232427",
    "C-08": "#7F8283",
}


def _rgb(h: str) -> tuple[int, int, int]:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def pick(clusters: list[dict], which: str) -> dict | None:
    if not clusters:
        return None
    dom = clusters[0]
    if which == "dominant":
        return dom
    lum = lambda c: sum(c["rgb"]) / 3.0
    darker = [c for c in clusters[1:] if lum(c) < lum(dom)]
    return max(darker, key=lambda c: c["pixels"]) if darker else None


def reduce_samples(samples: list[dict]) -> dict:
    """THE REDUCTION RULE, stated and applied.

    ADOPTED = the pixel-count weighted mean over the orthographic views.

    Weighted, not plain: the four views see wildly different amounts of each surface
    (the bracer is 3.0% of front.webp and 0.8% of right.webp), and an unweighted mean
    lets the view that barely sees a surface pull its value as hard as the view that
    sees all of it. The plain mean and the median are reported alongside so the
    difference the rule makes is visible instead of implied.
    """
    tot = sum(s["pixels"] for s in samples) or 1
    weighted = [sum(s["rgb"][i] * s["pixels"] for s in samples) / tot for i in range(3)]
    plain = [sum(s["rgb"][i] for s in samples) / len(samples) for i in range(3)]
    med = []
    for i in range(3):
        vals = sorted(s["rgb"][i] for s in samples)
        n = len(vals)
        med.append(vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2)
    return {
        "rule": "pixel-count weighted mean over the orthographic views",
        "adopted": _hex(weighted),
        "adoptedRgb": weighted,
        "plainMean": _hex(plain),
        "median": _hex(med),
        "totalPixels": tot,
    }


def main() -> int:
    if not LANDMARKS.exists():
        print("landmarks.json missing — run measure_landmarks.py first")
        return 2
    lm = json.loads(LANDMARKS.read_text(encoding="utf-8"))
    views = {n: R.load(n) for n in R.VIEWS}
    per_view: dict[str, dict] = {}
    for name, v in views.items():
        masks = region_masks(v, lm)
        per_view[name] = {
            region: cluster_region(v, m)[:4] for region, m in masks.items()
        }

    doc: dict = {
        "schema": "ff7-cloud-strife-palette/1",
        "generatedBy": "artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/sample_palette.py",
        "method": (
            "quantise the region's pixels into 24-level buckets, merge bucket centroids "
            "within RGB distance 26, take the largest cluster's centroid; regions are cut "
            "by landmarks.json rows, never by a hand-picked pixel"
        ),
        "coolViews": list(COOL),
        "warmView": WARM,
        "perViewRegions": per_view,
        "codes": {},
    }

    for code, (region, which, label) in CODES.items():
        samples = []
        for name in COOL:
            c = pick(per_view[name].get(region, []), which)
            if c:
                samples.append({**c, "view": name})
        warm = pick(per_view[WARM].get(region, []), which)
        entry = {
            "content": label,
            "region": region,
            "cluster": which,
            "coolSamples": {s["view"]: s["hex"] for s in samples},
            "coolSampleShares": {s["view"]: round(s["shareOfRegion"], 4) for s in samples},
            "warmReference": warm["hex"] if warm else None,
        }
        if samples:
            entry.update(reduce_samples(samples))
            claim = PROMPT_ADOPTED.get(code)
            if claim:
                d = [a - b for a, b in zip(entry["adoptedRgb"], _rgb(claim))]
                entry["promptAdopted"] = claim
                entry["deltaFromPromptRgb"] = [round(x, 1) for x in d]
                entry["deltaFromPromptMax"] = round(max(abs(x) for x in d), 1)
        doc["codes"][code] = entry
    doc["codes"]["C-09"] = {
        "content": "printed face",
        "note": "a CanvasTexture, not a flat colour — §7.2 owns it, nothing to sample here",
    }

    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    print(f"{'code':7s} {'content':34s} {'ADOPTED':9s} {'prompt':9s} {'dMax':>5s} "
          f"{'plain':9s} {'median':9s} warm")
    for code, e in doc["codes"].items():
        if "adopted" not in e:
            print(f"{code:7s} {e['content'][:34]:34s} {'-':9s}")
            continue
        print(
            f"{code:7s} {e['content'][:34]:34s} {e['adopted']:9s} "
            f"{e.get('promptAdopted', '-'):9s} {e.get('deltaFromPromptMax', 0):5.1f} "
            f"{e['plainMean']:9s} {e['median']:9s} {e['warmReference'] or '-'}"
        )
    print("\nper-view cool samples")
    for code, e in doc["codes"].items():
        if e.get("coolSamples"):
            print(f"  {code:7s} " + "  ".join(f"{k}={x}" for k, x in e["coolSamples"].items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
