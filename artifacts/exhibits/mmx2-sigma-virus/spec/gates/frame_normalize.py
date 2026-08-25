#!/usr/bin/env python3
"""Frame-normalize gate renders to the admitted reference's framing.

diagnose_render.py compares masks in frame space (224-grid, no bbox
normalization), so a fair silhouette comparison requires both images to carry
the subject at the same place and scale in frame.

Construction (uniform scale, exact subject placement):
  1. Clear background to alpha=0 on every SOURCE image first (raw captures are
     opaque, and build_foreground_mask's sat/luma clause would otherwise read
     the whole frame as foreground); subject bbox = alpha > 24.
  2. scale = mean over axes of (ref subject span / ref frame span) / (render
     subject span / render frame span): match FRAME FRACTIONS.
  3. Resize by that ONE scale (derived from the front view only), paste onto a
     transparent out-size canvas so the scaled subject centre lands on the
     reference subject centre mapped into out coordinates.
  4. The same transform applies to ALL views, so orbit/self-consistency signals
     (e.g. a collapsed silhouette) survive untouched.

Rerunnable: python3 frame_normalize.py --ref refs/front.png --front <front.png>
            --out-dir <dir> [--views a.png b.png ...] [--size 480 690]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

SKILL = Path("/Users/tonyyang/.claude/skills/img2threejs")
sys.path.insert(0, str(SKILL / "forge/stage1_intake"))
from extract_pbr_evidence import build_foreground_mask  # noqa: E402

BG = (0, 0, 41)
TOL = 30  # generous: catches LANCZOS ringing around strokes; fills are far away


def bg_cleared(path: Path) -> Image.Image:
    """RGBA copy with near-background pixels pushed to alpha=0."""
    rgba = Image.open(path).convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    tol2 = TOL * TOL
    for yy in range(h):
        for xx in range(w):
            r, g, b, a = px[xx, yy]
            d2 = (r - BG[0]) ** 2 + (g - BG[1]) ** 2 + (b - BG[2]) ** 2
            if d2 <= tol2 and a != 0:
                px[xx, yy] = (r, g, b, 0)
    return rgba


def subject_bbox_alpha(image: Image.Image) -> tuple[int, int, int, int]:
    w, h = image.size
    xs: list[int] = []
    ys: list[int] = []
    for y in range(h):
        for x in range(w):
            if image.getpixel((x, y))[3] >= 200:
                xs.append(x)
                ys.append(y)
    if not xs:
        raise SystemExit(f"no foreground subject found")
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", type=Path, required=True)
    parser.add_argument("--front", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--views", type=Path, nargs="*", default=[])
    parser.add_argument("--size", type=int, nargs=2, default=[480, 690])
    args = parser.parse_args()

    out_w, out_h = args.size
    ref = bg_cleared(args.ref)
    rw, rh = ref.size
    rx0, ry0, rx1, ry1 = subject_bbox_alpha(ref)

    front = bg_cleared(args.front)
    fw, fh = front.size
    fx0, fy0, fx1, fy1 = subject_bbox_alpha(front)

    scale_x = ((rx1 - rx0) / rw) / ((fx1 - fx0) / fw)
    scale_y = ((ry1 - ry0) / rh) / ((fy1 - fy0) / fh)
    scale = (scale_x + scale_y) / 2

    scaled_w, scaled_h = round(fw * scale), round(fh * scale)
    csx = ((fx0 + fx1) / 2) * scale
    csy = ((fy0 + fy1) / 2) * scale

    # Reference subject centre mapped into output coordinates.
    tx = ((rx0 + rx1) / 2) * (out_w / rw)
    ty = ((ry0 + ry1) / 2) * (out_h / rh)
    dx, dy = round(tx - csx), round(ty - csy)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "ref": str(args.ref), "refSize": [rw, rh],
        "refSubjectPx": [rx0, ry0, rx1, ry1],
        "frontSubjectPx": [fx0, fy0, fx1, fy1],
        "uniformScale": round(scale, 6),
        "scaledSize": [scaled_w, scaled_h],
        "pasteOffset": [dx, dy],
        "outputs": [],
    }
    for source in [args.front, *args.views]:
        cleared = bg_cleared(source)
        scaled = cleared.resize((scaled_w, scaled_h), Image.LANCZOS)
        canvas = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
        canvas.alpha_composite(scaled, (dx, dy))
        dest = args.out_dir / f"{source.stem}-norm.png"
        canvas.save(dest)
        report["outputs"].append({"source": str(source), "output": str(dest)})
        print(dest)
    (args.out_dir / "frame-normalize.json").write_text(json.dumps(report, indent=2))
    print("scale:", report["uniformScale"], "offset:", [dx, dy])


if __name__ == "__main__":
    main()
