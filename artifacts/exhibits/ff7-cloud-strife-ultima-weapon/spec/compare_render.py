"""Silhouette IoU + landmark error between the authority artwork and an artwork-match render.

The two images are framed differently (the crop is a tight bbox, the render frames a bounding
sphere), so a raw pixel-wise IoU would measure framing, not shape. Both masks are therefore
normalized to their own tight bounding box and resampled onto a common grid before overlap is
counted — the standard silhouette-IoU-after-alignment the review targets are written against.

Run:  python3 spec/compare_render.py <render.png> [<overlay-out.png>]
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
EXHIBIT = HERE.parent
GRID = 512  # normalized comparison resolution


def mask_from(image: Image.Image) -> list[list[bool]]:
    """Foreground test that works for every input this pipeline produces.

    Both tests are applied, never one or the other: the artwork cutout carries real alpha but
    a white body, while a canvas `toDataURL` render carries alpha=255 everywhere because the
    white review background is drawn as scene geometry. Keying on alpha alone marks the whole
    frame as foreground there and the IoU silently collapses to 0.29.
    """
    w, h = image.size
    rgba = image.convert("RGBA")
    px = rgba.load()
    assert px is not None
    return [[px[x, y][3] > 96 and min(px[x, y][:3]) < 244 for x in range(w)] for y in range(h)]


def normalized(mask: list[list[bool]]) -> list[list[bool]]:
    """Resample a mask onto a GRID x GRID square at **uniform** scale.

    Scaling X and Y independently would let a render with a different bounding-box aspect be
    stretched into agreement, which is exactly the error an aspect-sensitive silhouette check
    exists to catch. The mask is scaled by its longest side and centred instead, so aspect
    error stays visible in the IoU.
    """
    h = len(mask)
    w = len(mask[0])
    xs = [x for y in range(h) for x in range(w) if mask[y][x]]
    ys = [y for y in range(h) for x in range(w) if mask[y][x]]
    if not xs:
        raise SystemExit("empty mask")
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    bw = max(x1 - x0 + 1, 1)
    bh = max(y1 - y0 + 1, 1)
    span = max(bw, bh)
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    out = [[False] * GRID for _ in range(GRID)]
    for gy in range(GRID):
        sy = int(round(cy + (gy - GRID / 2 + 0.5) * span / GRID))
        if not 0 <= sy < h:
            continue
        row = mask[sy]
        for gx in range(GRID):
            sx = int(round(cx + (gx - GRID / 2 + 0.5) * span / GRID))
            if 0 <= sx < w:
                out[gy][gx] = row[sx]
    return out


def landmarks(mask: list[list[bool]]) -> dict[str, tuple[float, float]]:
    """Extremes of the normalized silhouette, as fractions of the grid."""
    pts = [(x, y) for y in range(GRID) for x in range(GRID) if mask[y][x]]
    top = min(pts, key=lambda p: (p[1], p[0]))
    bottom = max(pts, key=lambda p: (p[1], -p[0]))
    left = min(pts, key=lambda p: (p[0], p[1]))
    right = max(pts, key=lambda p: (p[0], -p[1]))
    return {
        "tip": (top[0] / GRID, top[1] / GRID),
        "pommelTip": (bottom[0] / GRID, bottom[1] / GRID),
        "leftExtreme": (left[0] / GRID, left[1] / GRID),
        "rightExtreme": (right[0] / GRID, right[1] / GRID),
    }


def shift(mask: list[list[bool]], dx: int, dy: int) -> list[list[bool]]:
    out = [[False] * GRID for _ in range(GRID)]
    for y in range(GRID):
        sy = y - dy
        if not 0 <= sy < GRID:
            continue
        row = mask[sy]
        target = out[y]
        for x in range(GRID):
            sx = x - dx
            if 0 <= sx < GRID and row[sx]:
                target[x] = True
    return out


def compare(reference: list[list[bool]], render_path: Path, overlay_path: Path | None) -> dict:
    raw = normalized(mask_from(Image.open(render_path)))

    # Bounding-box centring is not a registration: the reference's own bbox is set by its
    # driver tips, so any difference in the hilt drags the whole blade sideways and the IoU
    # then measures that offset rather than the shape. A coarse-to-fine translation search
    # removes it; the chosen offset is reported so it cannot hide a real placement error.
    best = (-1.0, 0, 0, raw)
    for step in (8, 2):
        base_dx, base_dy = best[1], best[2]
        for dy in range(base_dy - step * 4, base_dy + step * 4 + 1, step):
            for dx in range(base_dx - step * 4, base_dx + step * 4 + 1, step):
                candidate = shift(raw, dx, dy)
                i = sum(
                    1 for y in range(GRID) for x in range(GRID) if reference[y][x] and candidate[y][x]
                )
                u = sum(
                    1 for y in range(GRID) for x in range(GRID) if reference[y][x] or candidate[y][x]
                )
                score = i / u if u else 0.0
                if score > best[0]:
                    best = (score, dx, dy, candidate)
    _, off_x, off_y, render = best

    inter = sum(1 for y in range(GRID) for x in range(GRID) if reference[y][x] and render[y][x])
    union = sum(1 for y in range(GRID) for x in range(GRID) if reference[y][x] or render[y][x])
    ref_only = sum(1 for y in range(GRID) for x in range(GRID) if reference[y][x] and not render[y][x])
    render_only = sum(1 for y in range(GRID) for x in range(GRID) if render[y][x] and not reference[y][x])

    ref_marks = landmarks(reference)
    ren_marks = landmarks(render)
    errors = {
        name: round(
            math.hypot(ref_marks[name][0] - ren_marks[name][0], ref_marks[name][1] - ren_marks[name][1]),
            4,
        )
        for name in ref_marks
    }

    # Row-wise width error: catches a blade that is the right length but the wrong taper, which
    # a global IoU can hide behind a large matching area.
    width_rows = []
    for band in range(0, GRID, GRID // 16):
        rows = range(band, min(band + GRID // 16, GRID))
        rw = sum(sum(1 for x in range(GRID) if reference[y][x]) for y in rows) / len(list(rows))
        gw = sum(sum(1 for x in range(GRID) if render[y][x]) for y in rows) / len(list(rows))
        width_rows.append({"band": band / GRID, "reference": round(rw / GRID, 4), "render": round(gw / GRID, 4)})

    report = {
        "render": str(render_path),
        "iou": round(inter / union, 4) if union else 0.0,
        "registrationOffsetFractionOfSpan": [round(off_x / GRID, 4), round(off_y / GRID, 4)],
        "referenceOnlyFraction": round(ref_only / union, 4) if union else 0.0,
        "renderOnlyFraction": round(render_only / union, 4) if union else 0.0,
        "landmarkErrorFractionOfHeight": errors,
        "widthProfileByBand": width_rows,
    }

    if overlay_path:
        overlay = Image.new("RGB", (GRID, GRID), (255, 255, 255))
        op = overlay.load()
        assert op is not None
        for y in range(GRID):
            for x in range(GRID):
                r, g = reference[y][x], render[y][x]
                if r and g:
                    op[x, y] = (60, 60, 70)  # agreement
                elif r:
                    op[x, y] = (214, 66, 90)  # artwork only
                elif g:
                    op[x, y] = (58, 150, 214)  # render only
        overlay.save(overlay_path)
        report["overlay"] = str(overlay_path)
        # Side-by-side of the two normalized masks. The overlay says "they disagree here";
        # these say which of the two is the odd shape.
        pair = Image.new("RGB", (GRID * 2 + 8, GRID), (255, 255, 255))
        pp = pair.load()
        assert pp is not None
        for y in range(GRID):
            for x in range(GRID):
                if reference[y][x]:
                    pp[x, y] = (214, 66, 90)
                if render[y][x]:
                    pp[x + GRID + 8, y] = (58, 150, 214)
        pair.save(overlay_path.with_name(overlay_path.stem + "-pair.png"))
    return report


def write_gate_render(render_path: Path, out_path: Path) -> None:
    """Re-frame a review render to the authority crop's own framing.

    forge/stage4_review/diagnose_render.py compares raw pixels, so handing it a 584x1168
    render against a 210x434 crop measures framing and reports IoU 0.42 for a model that
    actually registers at 0.89. This crops the render to its silhouette and resizes it to the
    reference's dimensions so the deterministic gate scores the shape it is meant to score.
    """
    def bbox(mask: list[list[bool]]) -> tuple[int, int, int, int]:
        h, w = len(mask), len(mask[0])
        xs = [x for y in range(h) for x in range(w) if mask[y][x]]
        ys = [y for y in range(h) for x in range(w) if mask[y][x]]
        return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)

    reference = Image.open(EXHIBIT / "assets/artwork-sword-transparent.webp")
    rx0, ry0, rx1, ry1 = bbox(mask_from(reference))
    image = Image.open(render_path).convert("RGB")
    box = bbox(mask_from(image))
    # Land the render's silhouette on the reference's silhouette box, inside a canvas of the
    # reference's own size, so the gate's un-registered pixel overlap is not measuring padding.
    canvas = Image.new("RGB", reference.size, (255, 255, 255))
    # Box filter, not Lanczos: Lanczos rings around the hard PS1-era edges and the halo shifts
    # the gate's foreground threshold by about a pixel all the way round the silhouette.
    canvas.paste(image.crop(box).resize((rx1 - rx0, ry1 - ry0), Image.Resampling.BOX), (rx0, ry0))
    canvas.save(out_path)


def main() -> None:
    if sys.argv[1] == "--gate-render":
        write_gate_render(Path(sys.argv[2]), Path(sys.argv[3]))
        print(f"gate render -> {sys.argv[3]}")
        return
    reference = normalized(mask_from(Image.open(EXHIBIT / "assets/artwork-sword-transparent.webp")))
    target = Path(sys.argv[1])
    if target.is_dir():
        rows = sorted(
            (compare(reference, p, None) for p in sorted(target.glob("*.png"))),
            key=lambda r: -r["iou"],
        )
        for row in rows:
            e = row["landmarkErrorFractionOfHeight"]
            print(
                f"IoU {row['iou']:.4f}  refOnly {row['referenceOnlyFraction']:.3f} "
                f"renderOnly {row['renderOnlyFraction']:.3f}  "
                f"tip {e['tip']:.3f} pommel {e['pommelTip']:.3f} "
                f"L {e['leftExtreme']:.3f} R {e['rightExtreme']:.3f}  "
                f"{Path(row['render']).name}"
            )
        return
    overlay = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    print(json.dumps(compare(reference, target, overlay), indent=2))


if __name__ == "__main__":
    main()
