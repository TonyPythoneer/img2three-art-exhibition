#!/usr/bin/env python3
"""Measure the head silhouette off the trimmed references, into head-measurements.json.

Run from the repo root:

    python3 artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/measure_head.py

Scope, deliberately narrow: figure-vs-background and hair-vs-not-hair, per row.
Skin was tried as a third class and dropped -- blown-out hair highlights land in the
same RGB neighbourhood as lit vinyl skin, so a face width read this way is noise.
The face/chin/eye heights come from prompt.txt §1, which is the size authority; what
this script adds is the hair silhouette profile, which prompt.txt only describes in words.

Y is normalized so 1.000 = top of the figure (the references are trimmed to it) and
0.000 = the sole plane. X is measured from the image centre, in the same units.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
ASSETS = ROOT / "src/assets/exhibits/ff7-cloud-strife-polygon-figure"
OUT = pathlib.Path(__file__).with_name("head-measurements.json")
# prompt.txt §1: shoulder line. Everything above it is head, neck and hair only.
SHOULDER_Y = 0.673


def load_rgb(path):
    """webp -> (w, h, bytes) via ImageMagick, so there is no PIL dependency."""
    txt = subprocess.run(
        ["magick", str(path), "-depth", "8", "-type", "TrueColor", "ppm:-"],
        check=True, capture_output=True,
    ).stdout
    fields, idx = [], 0
    while len(fields) < 4:  # P6, width, height, maxval
        while txt[idx:idx + 1].isspace():
            idx += 1
        if txt[idx:idx + 1] == b"#":
            idx = txt.index(b"\n", idx)
            continue
        start = idx
        while not txt[idx:idx + 1].isspace():
            idx += 1
        fields.append(txt[start:idx])
    idx += 1
    w, h = int(fields[1]), int(fields[2])
    return w, h, txt[idx:idx + w * h * 3]


def is_background(r, g, b):
    # Near-neutral near-white. Neutrality matters: the trimmed WebPs carry an
    # antialiased halo a few values off pure white.
    return min(r, g, b) > 224 and max(r, g, b) - min(r, g, b) < 26


def is_hair(r, g, b):
    # Gold vinyl: blue channel well under green, and a wide red-blue gap.
    return r > 140 and b < g - 40 and r - b > 55


def scan(path):
    w, h, body = load_rgb(path)
    rows = []
    for y in range(h):
        base = y * w * 3
        figure = hair = None
        for x in range(w):
            o = base + x * 3
            r, g, b = body[o], body[o + 1], body[o + 2]
            if is_background(r, g, b):
                continue
            figure = (x, x) if figure is None else (figure[0], x)
            if is_hair(r, g, b):
                hair = (x, x) if hair is None else (hair[0], x)
        rows.append({"figure": figure, "hair": hair})
    return w, h, rows


def summarize(path, step_frac=0.005):
    w, h, rows = scan(path)
    hair_rows = [y for y, s in enumerate(rows) if s["hair"]]
    head_limit = int(h * (1.0 - SHOULDER_Y))

    def ny(py):
        return round((h - py) / h, 4)

    def nx(px):
        return round((px - w / 2) / h, 4)

    profile = [
        {
            "y": ny(y),
            "figureX0": nx(rows[y]["figure"][0]),
            "figureX1": nx(rows[y]["figure"][1]),
            "hairX0": nx(rows[y]["hair"][0]) if rows[y]["hair"] else None,
            "hairX1": nx(rows[y]["hair"][1]) if rows[y]["hair"] else None,
        }
        for y in range(0, min(len(rows), head_limit), max(1, int(h * step_frac)))
        if rows[y]["figure"]
    ]
    widest = max(
        ((s["hair"][1] - s["hair"][0] + 1, y) for y, s in enumerate(rows) if s["hair"]),
        default=(0, 0),
    )
    return {
        "image": path.name,
        "size": [w, h],
        "hairTopY": ny(min(hair_rows)) if hair_rows else None,
        "hairLowestY": ny(max(hair_rows)) if hair_rows else None,
        "hairSpanMaxWidth": round(widest[0] / h, 4),
        "hairSpanMaxWidthAtY": ny(widest[1]),
        "profileStepY": round(step_frac, 4),
        "profile": profile,
    }


def main():
    result = {
        "generatedBy": "spec/measure_head.py",
        "measures": "hair silhouette only; sizes of face/neck come from prompt.txt §1",
        "shoulderY": SHOULDER_Y,
        "views": {},
    }
    for name in ("front", "back", "left", "right"):
        result["views"][name] = summarize(ASSETS / f"{name}.webp")
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    for name, v in result["views"].items():
        print(
            f"{name:6s} hairTop {v['hairTopY']}  hairLowest {v['hairLowestY']}"
            f"  maxSpan {v['hairSpanMaxWidth']} @ {v['hairSpanMaxWidthAtY']}"
            f"  rows {len(v['profile'])}"
        )
    print("->", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
