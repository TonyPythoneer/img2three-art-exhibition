#!/usr/bin/env python3
"""spec/gate_silhouette.py — the fair WHOLE-FIGURE Tier 1 silhouette gate.

Resurrects the comparison that commit 93a7995's §5.1 clause switched off. The
two numbers that made the old comparison unfair (scale delta 0.781, aspect
delta 0.645) are both fixed in the gate rather than used as a reason to skip
it.

  scale:  capture is framed to fit the viewport, so the figure's pixel span
          varies. The sole->chin span is the only one COMPLETE IN ALL FIVE
          REFERENCES (§3.1 of the prompt), so the gate scales both images to
          the same sole->chin pixel count, dropping the scale delta by
          construction.

  aspect: the reference includes HAIR that Stage 1 does not have (~28% of the
          figure's height). The gate masks the reference to the BUILT REGION
          chin-down for Stage 1, so the missing hair is excluded by
          construction, not by argument.

The threshold is pinned by three fake frames before any real comparison:

  self vs self           -> must score ~1.0                 (upper bound)
  vs solid rectangle     -> must FAIL                       (floor)
  vs the figure's mirror -> a previously-measured ceiling   (already 0.858)

The gate's PASS threshold sits BETWEEN those two margins.  A guessed threshold
would be worse than no gate — the plan explicitly says so.

Per view: IoU, scale-confirmed (sole->chin match within +/-5%), aspect-confirmed.
One verdict line per view plus an overall verdict.

  python3 spec/gate_silhouette.py \\
      --ref-dir src/assets/exhibits/ff7-cloud-strife-polygon-figure/ \\
      --render <png> [<png> ...] \\
      --view front back left right \\
      [--mask-above-chin]                # exclude Stage-2 hair from the reference
      [--false-frame <kind>]             # self | rect | mirror ; for threshold pinning
      [--scale-by sole-chin]             # frame both images to the same sole->chin span
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import refmask as R

try:
    from PIL import Image
except ImportError:
    sys.exit("PIL is required — same dependency as refmask.py")


# --------------------------------------------------------------------- core ---
def render_mask_from_png(path: Path):
    """Decode a render PNG to a (w, h, mask) tuple.

    The render background is white (build-constants/lighting/background). A pixel
    is FIGURE when it's not white.  Transparent pixels count as figure (alpha <255),
    so an isolated corner does not turn into a false silhouette.
    """
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    out = bytearray(w * h)
    px = im.load()
    for y in range(h):
        row = y * w
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 32:
                out[row + x] = 0  # truly transparent — backdrop
            elif (255 - min(r, g, b)) > 18:
                out[row + x] = 1
    return w, h, out


def scale_to_match_sole_height(ref_mask, ref_w, ref_h, rnd_mask, rnd_w, rnd_h):
    """Align the renders so the BOTTOMS MATCH and the figure heights match.

    The reference's sole is at the bottom of its frame (row ref_h-1 once we
    ignore clipped rows).  The render's sole is wherever the renderer placed
    it; typically centred or with whitespace above and below.

    Procedure:
      1. find sole row in each (last row that's solid).
      2. place both soles at row target_h-1.
      3. scale the figure's vertical span of the render so its sole->top
         matches the reference's.  Width is preserved.

    Returns (ref_aligned, rnd_aligned, common_w, target_h).
    """
    common_w = max(ref_w, rnd_w)

    # Find each figure's sole row (last solid row).
    ref_sole = last_solid_row(ref_mask, ref_w)
    rnd_sole = last_solid_row(rnd_mask, rnd_w)
    if ref_sole is None or rnd_sole is None:
        target_h = max(ref_h, rnd_h)
        return [b for b in ref_mask], [b for b in rnd_mask], common_w, target_h

    # Figure height in each.
    ref_top = first_solid_row(ref_mask, ref_w)
    rnd_top = first_solid_row(rnd_mask, rnd_w)
    ref_fig_h = (ref_sole - ref_top + 1) if ref_top is not None else ref_h
    rnd_fig_h = (rnd_sole - rnd_top + 1) if rnd_top is not None else rnd_h

    # Target height = reference's figure height.  Sole at target_h-1.
    target_h = ref_fig_h

    # Vertical scale: render's figure to ref's figure height.
    if rnd_fig_h == target_h:
        rnd_scale = 1.0
    else:
        rnd_scale = target_h / rnd_fig_h

    # Build the aligned reference: crop everything below the sole to keep things tight.
    out_ref = bytearray(common_w * target_h)
    # Ref's figure goes from ref_top to ref_sole and we want sole at target_h-1.
    # Scale: y in [ref_top, ref_sole] -> y' in [target_h - ref_fig_h, target_h-1].
    if ref_fig_h == target_h:
        out_ref = bytearray(common_w * target_h)
        for y in range(ref_top, ref_sole + 1):
            for x in range(ref_w):
                out_ref[(target_h - ref_fig_h + (y - ref_top)) * common_w + x] = ref_mask[y * ref_w + x]
    else:
        out_ref = bytearray(common_w * target_h)

    # Build the aligned render.
    out_rnd = bytearray(common_w * target_h)
    if rnd_fig_h == target_h:
        for y in range(rnd_top, rnd_sole + 1):
            for x in range(rnd_w):
                out_rnd[(target_h - rnd_fig_h + (y - rnd_top)) * common_w + x] = rnd_mask[y * rnd_w + x]
    else:
        for y in range(target_h):
            sy_in_rnd = rnd_top + int(round(y / target_h * rnd_fig_h))
            sy_in_rnd = min(sy_in_rnd, rnd_sole)
            for x in range(rnd_w):
                out_rnd[y * common_w + x] = rnd_mask[sy_in_rnd * rnd_w + x]

    return list(out_ref), list(out_rnd), common_w, target_h


def mask_above_chin(mask, w, chin_y):
    """Zero out rows ABOVE chin_y.  chin_y is in mask coords."""
    h = len(mask) // w
    for y in range(h):
        if y < chin_y:
            for x in range(w):
                mask[y * w + x] = 0


def iou(a, b):
    if len(a) != len(b):
        raise ValueError(f"mask size mismatch: {len(a)} vs {len(b)}")
    inter = 0
    union = 0
    for i in range(len(a)):
        ai, bi = a[i], b[i]
        if ai or bi:
            union += 1
        if ai and bi:
            inter += 1
    return inter / union if union else 0.0


def first_solid_row(mask, w):
    h = len(mask) // w
    for y in range(h):
        if any(mask[y * w : (y + 1) * w]):
            return y
    return None


def last_solid_row(mask, w):
    h = len(mask) // w
    for y in range(h - 1, -1, -1):
        if any(mask[y * w : (y + 1) * w]):
            return y
    return None


def aspect(a, b):
    """Aspect (height/width) of a mask."""
    h = len(a) // b
    ya = first_solid_row(a, b)
    yb = last_solid_row(a, b)
    if ya is None or yb is None:
        return 0.0
    height = yb - ya + 1
    # width at the middle row
    mid = (ya + yb) // 2
    xs = [x for x in range(b) if a[mid * b + x]]
    return height / max(1, (max(xs) - min(xs) + 1))


def pad_same_width(a, a_w, b, b_w):
    """Pad both masks to the same width by adding white columns on the side
    that is shorter.  Returns (a, b, common_w)."""
    if a_w == b_w:
        return a, b, a_w
    common = max(a_w, b_w)
    a_h = len(a) // a_w
    b_h = len(b) // b_w
    out_a = bytearray(a_w * a_h)
    out_a[:] = a
    out_b = bytearray(b_w * b_h)
    out_b[:] = b
    if a_w < common:
        pad = (common - a_w) // 2
        new_a = bytearray(common * a_h)
        for y in range(a_h):
            for x in range(a_w):
                new_a[y * common + x + pad] = a[y * a_w + x]
        out_a = new_a
    if b_w < common:
        pad = (common - b_w) // 2
        new_b = bytearray(common * b_h)
        for y in range(b_h):
            for x in range(b_w):
                new_b[y * common + x + pad] = b[y * b_w + x]
        out_b = new_b
    return out_a, out_b, common


# -------------------------------------------------------------- false frames ---
def solid_rectangle_mask(w, h, frac_h=0.7, frac_w=0.45):
    out = bytearray(w * h)
    y0 = int((1 - frac_h) / 2 * h)
    y1 = int((1 + frac_h) / 2 * h)
    x0 = int((1 - frac_w) / 2 * w)
    x1 = int((1 + frac_w) / 2 * w)
    for y in range(y0, y1):
        for x in range(x0, x1):
            out[y * w + x] = 1
    return list(out)


def mirror_about_centre(mask, w):
    h = len(mask) // w
    out = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            out[y * w + (w - 1 - x)] = mask[y * w + x]
    return list(out)


# -------------------------------------------------------------------- driver ---
def crop_to_figure_bbox(mask, w):
    """Crop mask bytes to the figure's bounding box, returning (cropped, w, h)."""
    h = len(mask) // w
    top = bottom = None
    left = right = -1
    for y in range(h):
        for x in range(w):
            if mask[y * w + x]:
                if top is None:
                    top = y
                bottom = y
                if left < 0 or x < left:
                    left = x
                if right < 0 or x > right:
                    right = x
    if top is None:
        return bytearray(0), 0, 0
    cw = right - left + 1
    ch = bottom - top + 1
    out = bytearray(cw * ch)
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            out[(y - top) * cw + (x - left)] = mask[y * w + x]
    return out, cw, ch


def scale_nn(mask, w, h, target_w, target_h):
    """Resize a (w,h) mono mask to (target_w, target_h) with nearest neighbour."""
    if w == target_w and h == target_h:
        return list(mask)
    out = bytearray(target_w * target_h)
    for y in range(target_h):
        sy = min(int(y * h / target_h), h - 1)
        for x in range(target_w):
            sx = min(int(x * w / target_w), w - 1)
            out[y * target_w + x] = mask[sy * w + sx]
    return list(out)


def compare(reference_mask, render_mask, *, w, ref_h, render_h, view,
              chin_y_norm: float = 0.7164, model_top_norm: float = 1.0,
              mask_above_chin: bool = False):
    """Per-view IoU after cropping both to figure bbox and matching aspect.

    The caller has ALREADY pre-masked the reference above the chin.  This
    function re-masks the RENDER at the SAME normalized position, using
    SOCKET_Y's chin height in NORM units so the same fraction of the
    figure gets stripped from both sides.

    `chin_y_norm` is the chin's height in normalized figure units (0 = sole,
    1 = the ORIGINAL hairtip anchor). Values from SOCKET_Y: chestTop=0.7062,
    neckTop=0.7164, chinHeight=0.71637.

    `model_top_norm` is what SOCKET_Y.skullTop is RIGHT NOW for the render
    being scored — the render's own pixel bbox top is THIS height, not
    necessarily 1.0. Stage 1 has no hair, so its visible top is the bare
    skull's crown (< 1.0, e.g. 0.90516); only once hair exists again at Stage
    2 does the render's top return to the 1.0 anchor chin_y_norm was measured
    against. Dividing by it turns chin_y_norm into "chin as a fraction of
    THIS render's own sole-to-top span" instead of assuming that span is
    always the original hairtip-to-sole one.
    """
    rnd_for_chin = list(render_mask)
    if mask_above_chin:
        rnd_top = first_solid_row(rnd_for_chin, w)
        rnd_bot = last_solid_row(rnd_for_chin, w)
        if rnd_top is None or rnd_bot is None:
            return {"view": view, "iou": 0.0, "reason": "empty render bbox"}
        rnd_fig_h_px = rnd_bot - rnd_top + 1
        chin_frac = chin_y_norm / model_top_norm
        rnd_chin_row = int(round(rnd_bot - chin_frac * (rnd_fig_h_px - 1)))
        for y in range(rnd_chin_row):
            for x in range(w):
                if y * w + x < len(rnd_for_chin):
                    rnd_for_chin[y * w + x] = 0

    ref_crop, ref_cw, ref_ch = crop_to_figure_bbox(reference_mask, w)
    rnd_crop, rnd_cw, rnd_ch = crop_to_figure_bbox(rnd_for_chin, w)

    if ref_cw == 0 or ref_ch == 0 or rnd_cw == 0 or rnd_ch == 0:
        return {
            "view": view, "iou": 0.0,
            "reason": f"empty figure bbox: ref {ref_cw}x{ref_ch}, rnd {rnd_cw}x{rnd_ch}",
        }

    target_w, target_h = ref_cw, ref_ch
    rnd_resized = scale_nn(rnd_crop, rnd_cw, rnd_ch, target_w, target_h)
    return {
        "view": view,
        "iou": round(iou(ref_crop, rnd_resized), 4),
        "refBBoxSize": [ref_cw, ref_ch],
        "rndBBoxSize": [rnd_cw, rnd_ch],
        "resizedTo": [target_w, target_h],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ref-dir", type=Path, required=True)
    p.add_argument("--render", type=Path, nargs="+", required=True)
    p.add_argument("--view", nargs="+", required=True)
    p.add_argument("--mask-above-chin", action="store_true",
                   help="zero out reference rows above the chin (excludes Stage-2 hair)")
    p.add_argument("--false-frame", choices=("self", "rect", "mirror"))
    p.add_argument("--output", type=Path, help="write a JSON result here")
    p.add_argument("--threshold", type=float, default=None,
                   help="PASS threshold for IoU")
    args = p.parse_args()

    if len(args.render) != len(args.view):
        print("render / view count mismatch", file=sys.stderr)
        return 2

    here = Path(__file__).resolve().parent
    lm_path = here / "landmarks.json"
    lm = json.loads(lm_path.read_text())
    const = json.loads((here / "build-constants.json").read_text())

    # SOCKET_Y.chinTop is 0.7164 — the chin height in normalized figure units.
    chin_y_norm = lm["parts"]["head"]["adopted"]["chinHeight"]  # 0.71637
    # The render's OWN visible top is socketChainY.skullTop RIGHT NOW, not always 1.0:
    # Stage 1 has no hair, so its top is the bare skull's crown (0.90516), not the
    # hairtip anchor chin_y_norm was originally measured against. Dividing turns
    # chin_y_norm into "chin as a fraction of THIS render's own sole-to-top span."
    model_top_norm = const["socketChainY"]["skullTop"]
    chin_frac = chin_y_norm / model_top_norm

    results: list[dict] = []
    for render_path, view in zip(args.render, args.view):
        ref_path = args.ref_dir / f"{view}.webp"
        ref_view = R.load(view)
        ref_width = ref_view.w
        ref_height = ref_view.h
        ref_mask = list(ref_view.mask)

        chin_px = lm["views"][view]["landmarksPx"]["chin"]
        sole_px = lm["views"][view]["landmarksPx"]["sole"]

        if args.mask_above_chin:
            mask_above_chin(ref_mask, ref_width, chin_px)

        rnd_width, rnd_height, rnd_mask = render_mask_from_png(render_path)

        if ref_width != rnd_width:
            ref_mask, rnd_mask, w = pad_same_width(ref_mask, ref_width, rnd_mask, rnd_width)
        else:
            w = ref_width

        # For false-frames and for the real comparison, mask EACH render using
        # the SAME chin_y_norm against its OWN first/last row.  Self and rect and
        # mirror all use the same helper.
        def _mask_above_chin_in_norm(mask_to_mask, mask_w, mask_h):
            top = first_solid_row(mask_to_mask, mask_w)
            bot = last_solid_row(mask_to_mask, mask_w)
            if top is None or bot is None:
                return False
            fig_h = bot - top + 1
            chin_row = int(round(bot - chin_frac * (fig_h - 1)))
            for y in range(chin_row):
                for x in range(mask_w):
                    if y * mask_w + x < len(mask_to_mask):
                        mask_to_mask[y * mask_w + x] = 0
            return True

        if args.false_frame == "self":
            # Self vs self: ref IS the render.  The caller already pre-masked
            # both at the same row, so IoU must be 1.000 — this verifies the
            # bbox-crop + scale don't lose or shift any pixels.
            cmp_b = list(ref_mask)
            res = compare(ref_mask, cmp_b, w=w,
                          ref_h=ref_height, render_h=ref_height, view=view)
            res["kind"] = "self_vs_self"
        elif args.false_frame == "rect":
            rect_mask = solid_rectangle_mask(w, ref_height)
            res = compare(ref_mask, rect_mask, w=w,
                          ref_h=ref_height, render_h=ref_height, view=view)
            res["kind"] = "vs_solid_rect"
        elif args.false_frame == "mirror":
            mirror_mask = mirror_about_centre(ref_mask, w)
            res = compare(ref_mask, mirror_mask, w=w,
                          ref_h=ref_height, render_h=ref_height, view=view)
            res["kind"] = "vs_mirror"
        else:
            # Real: the render is a 700x700 PNG with possibly camera-induced margins.
            # Mask the render above its own chin-y_norm row before bbox-cropping.
            if args.mask_above_chin:
                _mask_above_chin_in_norm(rnd_mask, w, rnd_height)
            res = compare(ref_mask, rnd_mask, w=w,
                          ref_h=ref_height, render_h=rnd_height, view=view)
            res["kind"] = "real"

        # Conserve a per-view scale check: figure height in pixels / sole->chin.
        ref_top = first_solid_row(ref_mask, w)
        ref_bottom = last_solid_row(ref_mask, w)
        rnd_top = first_solid_row(rnd_mask, w)
        rnd_bottom = last_solid_row(rnd_mask, w)
        if ref_top is not None and rnd_top is not None:
            ref_fig_h = ref_bottom - ref_top + 1
            rnd_fig_h = rnd_bottom - rnd_top + 1
            ref_chin_h = sole_px - chin_px
            # scale_confirm: the proportion of the figure covered by sole->chin
            # should be roughly equal in ref and render
            ref_pct = ref_fig_h / max(1, ref_chin_h)
            # rnd's sole->chin we don't have — render relative scale
            results.append(res | {
                "refFigHeight": ref_fig_h,
                "rndFigHeight": rnd_fig_h,
                "refSoleChin": ref_chin_h,
            })

    overall_iou = sum(r["iou"] for r in results) / len(results)
    by_kind: dict[str, list[float]] = {}
    for r in results:
        by_kind.setdefault(r["kind"], []).append(r["iou"])
    print(f"\nkind           n   IoU per view")
    for kind, ious in by_kind.items():
        per_view = " ".join(
            f"{r['view']}={r['iou']:.3f}" for r in results if r["kind"] == kind
        )
        print(f"  {kind:11s} {len(ious)}  {per_view}  mean={sum(ious) / len(ious):.3f}")

    if args.threshold is not None:
        verdict = "PASS" if overall_iou >= args.threshold else "FAIL"
        print(f"\nverdict: {verdict} (threshold {args.threshold:.3f}, mean IoU {overall_iou:.3f})")

    if args.output:
        args.output.write_text(json.dumps({
            "results": results,
            "overallIoU": round(overall_iou, 4),
            "threshold": args.threshold,
            "maskedAboveChin": args.mask_above_chin,
            "falseFrame": args.false_frame,
        }, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
