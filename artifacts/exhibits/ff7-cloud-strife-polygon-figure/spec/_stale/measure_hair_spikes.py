#!/usr/bin/env python3
"""Measure hair-spike tips off the Cloud Strife polygon-figure references.

Reuses measure_head.py's load_rgb / coordinate conventions verbatim:
  Y normalized so full image height = 1.0 (1.000 = top, 0.000 = bottom)
  X measured from image centre, same scale.

Run from repo root:

    python3 artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/measure_hair_spikes.py
"""
import json
import math
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
ASSETS = ROOT / "src/assets/exhibits/ff7-cloud-strife-polygon-figure"
OUT = pathlib.Path(__file__).with_name("hair-spikes.json")

MASK_R = 150
MASK_G = 120
MASK_B = 140
MASK_RB = 60

RADIUS_MIN_FRAC = 1.15
ANGLE_MIN_DEG = 12.0
PROM_MIN_FRAC = 0.10


def load_rgb(path):
    """webp -> (w, h, bytes) via ImageMagick. No PIL/numpy/cv2."""
    txt = subprocess.run(
        ["magick", str(path), "-depth", "8", "-type", "TrueColor", "ppm:-"],
        check=True, capture_output=True,
    ).stdout
    fields, idx = [], 0
    while len(fields) < 4:
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


def is_hair(r, g, b):
    return r > MASK_R and g > MASK_G and b < MASK_B and (r - b) > MASK_RB


def scan_mask(w, h, body):
    """Return mask[y][x] bool grid."""
    mask = bytearray(w * h)
    for y in range(h):
        base = y * w * 3
        for x in range(w):
            o = base + x * 3
            if is_hair(body[o], body[o + 1], body[o + 2]):
                mask[y * w + x] = 1
    return mask


def mask_stats(mask, w, h):
    """pixels, bbox, centroid of mask.  centroid uses pixel-centre coords."""
    x0, y0, x1, y1 = w, h, -1, -1
    sx, sy, n = 0, 0, 0
    for y in range(h):
        for x in range(w):
            if mask[y * w + x]:
                n += 1
                sx += x
                sy += y
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y
    if n == 0:
        return 0, (0, 0, 0, 0), (w / 2, h / 2)
    return n, (x0, y0, x1, y1), (sx / n, sy / n)


def contour_loop(mask, w, h):
    """Outer contour: mask pixels with >=1 four-neighbour outside the mask.
    Returns list of (x, y) sorted by angle around the centroid."""
    def inside(xx, yy):
        return 0 <= xx < w and 0 <= yy < h and mask[yy * w + xx]
    pts = []
    for y in range(h):
        for x in range(w):
            if not mask[y * w + x]:
                continue
            if not (inside(x - 1, y) and inside(x + 1, y)
                    and inside(x, y - 1) and inside(x, y + 1)):
                pts.append((x, y))
    return pts


def sort_by_angle(pts, cx, cy):
    """Sort contour points by angle around centroid; ties broken by radius."""
    return sorted(pts,
                  key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


def angle_diff_deg(a, b):
    """Smallest unsigned angle between two degrees."""
    d = abs(a - b) % 360.0
    return d if d <= 180.0 else 360.0 - d


def find_peaks(sorted_contour, cx, cy, r_min):
    """Local-maxima of radius on the sorted contour with radius >= r_min.
    Prominence (c) is evaluated in collect_tips; here we just return every
    peak above the radius floor."""
    n = len(sorted_contour)
    if n < 3:
        return []
    radii = [math.hypot(p[0] - cx, p[1] - cy) for p in sorted_contour]
    peaks = []
    for i in range(n):
        r = radii[i]
        if r < r_min:
            continue
        prev = radii[(i - 1) % n]
        nxt = radii[(i + 1) % n]
        if r >= prev and r >= nxt:
            peaks.append(i)
    return peaks


def radius_between(sorted_contour, i, j, direction, n):
    """Minimum radius encountered walking from index i to j along the contour
    in the given direction (+1 cw, -1 ccw), exclusive of endpoints."""
    cx, cy = sorted_contour[0][0], sorted_contour[0][1]
    r_min = float("inf")
    k = i
    while True:
        k = (k + direction) % n
        if k == j:
            break
        p = sorted_contour[k]
        r = math.hypot(p[0] - cx, p[1] - cy)
        if r < r_min:
            r_min = r
    return r_min


def collect_tips(sorted_contour, peaks, cx, cy, equiv_r, height):
    """Apply the three acceptance conditions (radius / angular-separation /
    prominence) to the peak indices.  Peaks are processed largest-radius
    first so that the farthest tip in each angular region wins."""
    prom_min = equiv_r * PROM_MIN_FRAC
    n = len(sorted_contour)

    def ang(i):
        return math.degrees(math.atan2(
            sorted_contour[i][1] - cy, sorted_contour[i][0] - cx)) % 360.0

    def rad(i):
        p = sorted_contour[i]
        return math.hypot(p[0] - cx, p[1] - cy)

    peaks_by_r = sorted(peaks, key=lambda i: rad(i), reverse=True)
    accepted = []

    for ci in peaks_by_r:
        rc = rad(ci)

        # (b) angular separation from already-accepted tips
        too_close = False
        for ai in accepted:
            if angle_diff_deg(ang(ci), ang(ai)) < ANGLE_MIN_DEG:
                too_close = True
                break
        if too_close:
            continue

        # (c) prominence vs. the contour saddles to the nearest accepted tips
        if not accepted:
            prom = rc  # first tip: no saddle, passes trivially
        else:
            # nearest accepted on each side
            left_min = float("inf")
            right_min = float("inf")
            has_left = has_right = False
            k = ci
            while True:
                k = (k - 1) % n
                if k == ci:
                    break
                if k in accepted:
                    left_min = radius_between(sorted_contour, ci, k, -1, n)
                    has_left = True
                    break
            k = ci
            while True:
                k = (k + 1) % n
                if k == ci:
                    break
                if k in accepted:
                    right_min = radius_between(sorted_contour, ci, k, +1, n)
                    has_right = True
                    break
            if has_left and has_right:
                saddle = min(left_min, right_min)
            elif has_left:
                saddle = left_min
            elif has_right:
                saddle = right_min
            else:
                saddle = 0
            prom = rc - saddle

        if prom < prom_min:
            continue

        accepted.append(ci)

    accepted.sort(key=lambda i: ang(i))
    return accepted


def width_at_half(sorted_contour, cx, cy, px, py, mask, w, h):
    """Mask width measured at the midpoint of the centroid->tip segment,
    along the perpendicular direction."""
    mx = (cx + px) / 2
    my = (cy + py) / 2
    dx = px - cx
    dy = py - cy
    length = math.hypot(dx, dy)
    if length == 0:
        return 0
    # perpendicular unit vector
    px_u = -dy / length
    py_u = dx / length

    def in_mask(xx, yy):
        ix, iy = int(round(xx)), int(round(yy))
        if ix < 0 or ix >= w or iy < 0 or iy >= h:
            return False
        return mask[iy * w + ix] == 1

    # step outward until mask exits on each side
    step = 0.5
    pos_dist = 0
    s = step
    while s < length * 2:
        if in_mask(mx + px_u * s, my + py_u * s):
            pos_dist = s
            s += step
        else:
            break
    neg_dist = 0
    s = step
    while s < length * 2:
        if in_mask(mx - px_u * s, my - py_u * s):
            neg_dist = s
            s += step
        else:
            break
    return pos_dist + neg_dist


def ny(h, py):
    return round((h - py) / h, 4)


def nx(h, w, px):
    return round((px - w / 2) / h, 4)


def longest_run_in_row(mask, w, y):
    """Return (x0, x1, length) of the longest continuous run of 1s in row y.
    If no mask pixels in the row, returns (-1, -1, 0)."""
    best_x0 = best_x1 = -1
    best_len = 0
    cur_x0 = -1
    row_off = y * w
    for x in range(w + 1):
        in_mask = x < w and mask[row_off + x]
        if in_mask:
            if cur_x0 == -1:
                cur_x0 = x
        else:
            if cur_x0 != -1:
                run_len = x - cur_x0
                if run_len > best_len:
                    best_len = run_len
                    best_x0 = cur_x0
                    best_x1 = x - 1
                cur_x0 = -1
    return best_x0, best_x1, best_len


def measure_cap_shell(mask, w, h, body):
    """Measure the hair-cap shell: longest-run-per-row profile, hem, rim.

    Conventions match measure_head.py / measure_hair_spikes.py:
      Y normalized so 1.0 = image top, 0.0 = image bottom (ny()).
      X measured from image centre, same scale (nx()).
    """
    min_y = max_y = -1
    for y in range(h):
        row_off = y * w
        for x in range(w):
            if mask[row_off + x]:
                if min_y == -1:
                    min_y = y
                max_y = y
                break

    if min_y == -1:
        return None

    # 1. widthProfile
    width_profile = []
    max_w_norm = 0.0
    max_w_at_y = 0.0
    step_px = max(1, int(round(h * 0.005)))
    y = min_y
    while y <= max_y:
        x0, x1, run_len = longest_run_in_row(mask, w, y)
        x0n = nx(h, w, x0) if x0 >= 0 else None
        x1n = nx(h, w, x1) if x1 >= 0 else None
        wn = (x1n - x0n) if (x0n is not None and x1n is not None) else 0.0
        yn = ny(h, y)
        entry = {"yNorm": yn, "x0Norm": x0n, "x1Norm": x1n, "widthNorm": round(wn, 4)}
        width_profile.append(entry)
        if wn > max_w_norm:
            max_w_norm = wn
            max_w_at_y = yn
        y += step_px

    # 3. hemByColumn: every 2 px, lowest mask pixel in that column
    hem_by_col = []
    for x in range(0, w, 2):
        lowest = -1
        for yy in range(h - 1, -1, -1):
            if mask[yy * w + x]:
                lowest = yy
                break
        if lowest >= 0:
            hem_by_col.append({
                "xNorm": nx(h, w, x),
                "yNorm": ny(h, lowest),
            })

    if not hem_by_col:
        return {
            "widthProfile": width_profile,
            "maxWidthNorm": round(max_w_norm, 4),
            "maxWidthAtYNorm": max_w_at_y,
            "hemByColumn": [],
            "hemYNormAtCenter": None,
            "hemYNormAtSide": None,
            "rimThicknessPx": None,
        }

    # 4. hemYNormAtCenter / hemYNormAtSide
    max_half_w = max_w_norm / 2.0
    center_ys = [c["yNorm"] for c in hem_by_col if abs(c["xNorm"]) <= 0.02]
    side_lo = 0.7 * max_half_w
    side_hi = 0.95 * max_half_w
    side_ys = [c["yNorm"] for c in hem_by_col
               if side_lo <= abs(c["xNorm"]) <= side_hi]

    def median(vals):
        if not vals:
            return None
        s = sorted(vals)
        n = len(s)
        mid = n // 2
        return s[mid] if n % 2 else round((s[mid - 1] + s[mid]) / 2, 4)

    hem_center = median(center_ys)
    hem_side = median(side_ys)

    # 5. rimThicknessPx: scan up from hem until brightness exceeds 0.88*ref
    rim_thicknesses = []
    for x in range(0, w, 2):
        lowest = -1
        for yy in range(h - 1, -1, -1):
            if mask[yy * w + x]:
                lowest = yy
                break
        if lowest < 0:
            continue
        ref_y = lowest - 15
        if ref_y < 0:
            continue
        o_ref = ref_y * w + x * 3
        ref_sum = body[o_ref] + body[o_ref + 1] + body[o_ref + 2]
        if ref_sum == 0:
            continue
        threshold = ref_sum * 0.88
        thickness = 0
        for yy in range(lowest, -1, -1):
            o = yy * w + x * 3
            pix_sum = body[o] + body[o + 1] + body[o + 2]
            if pix_sum < threshold:
                thickness = lowest - yy
                break
        if thickness > 0:
            rim_thicknesses.append(thickness)

    rim_med = median(rim_thicknesses)
    if rim_med is not None and rim_med == int(rim_med):
        rim_med = int(rim_med)

    return {
        "widthProfile": width_profile,
        "maxWidthNorm": round(max_w_norm, 4),
        "maxWidthAtYNorm": max_w_at_y,
        "hemByColumn": hem_by_col,
        "hemYNormAtCenter": hem_center,
        "hemYNormAtSide": hem_side,
        "rimThicknessPx": rim_med,
    }


CAP_R_MIN = 4
CAP_R_MAX = 24
CAP_R_STEP = 2
CAP_PLATEAU_DELTA = 0.005
CAP_RADI = list(range(CAP_R_MIN, CAP_R_MAX + 1, CAP_R_STEP))


def circle_offsets(R):
    """Circular structuring element (Euclidean): offsets (dx,dy) with dx^2+dy^2 <= R^2.
    Centered at origin so erosion/dilation are self-complementary (B == -B)."""
    offs = []
    R2 = R * R
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            if dx * dx + dy * dy <= R2:
                offs.append((dx, dy))
    return offs


def erode_mask(mask, w, h, offsets):
    """Erosion: a mask pixel survives iff every offset of the circle is in-bounds
    and still in the mask (the whole structuring element is inside)."""
    eroded = bytearray(w * h)
    for y in range(h):
        ro = y * w
        for x in range(w):
            if mask[ro + x] == 0:
                continue
            ok = True
            for dx, dy in offsets:
                xx = x + dx
                yy = y + dy
                if xx < 0 or xx >= w or yy < 0 or yy >= h:
                    ok = False
                    break
                if mask[yy * w + xx] == 0:
                    ok = False
                    break
            if ok:
                eroded[ro + x] = 1
    return eroded


def dilate_mask(mask, w, h, offsets):
    """Dilation with the same circular structuring element: union of translated B."""
    dilated = bytearray(w * h)
    for y in range(h):
        ro = y * w
        for x in range(w):
            if mask[ro + x] == 0:
                continue
            for dx, dy in offsets:
                xx = x + dx
                yy = y + dy
                if 0 <= xx < w and 0 <= yy < h:
                    dilated[yy * w + xx] = 1
    return dilated


def bounding_rows(mask, w, h):
    """First/last row that contains a mask pixel."""
    min_y = max_y = -1
    for y in range(h):
        ro = y * w
        for x in range(w):
            if mask[ro + x]:
                if min_y == -1:
                    min_y = y
                max_y = y
                break
    return min_y, max_y


def per_row_profile(mask, w, h):
    """Longest horizontal run per sampled row. Step matches measure_head.py (0.5%)."""
    min_y, max_y = bounding_rows(mask, w, h)
    if min_y == -1:
        return [], 0.0, 0.0, None, None
    profile = []
    max_w = 0.0
    max_at_y = 0.0
    step_px = max(1, int(round(h * 0.005)))
    y = min_y
    while y <= max_y:
        x0, x1, _ = longest_run_in_row(mask, w, y)
        x0n = nx(h, w, x0) if x0 >= 0 else None
        x1n = nx(h, w, x1) if x1 >= 0 else None
        wn = (x1n - x0n) if (x0n is not None and x1n is not None) else 0.0
        yn = ny(h, y)
        profile.append({
            "yNorm": yn,
            "x0Norm": x0n,
            "x1Norm": x1n,
            "widthNorm": round(wn, 4),
        })
        if wn > max_w:
            max_w = wn
            max_at_y = yn
        y += step_px
    return profile, round(max_w, 4), max_at_y, ny(h, min_y), ny(h, max_y)


def measure_cap_core(mask, w, h):
    """Clean cap core via morphological opening (erode then dilate) with a
    circle-Euclidean structuring element, swept over radius R. The spikes
    are narrow (<70px) so any R big enough to span them vanishes, leaving the
    coarse cap shell; the plateau marks where the core width has stabilised.
    """
    sweep = []
    profiles = {}
    for R in CAP_RADI:
        offsets = circle_offsets(R)
        eroded = erode_mask(mask, w, h, offsets)
        opened = dilate_mask(eroded, w, h, offsets)
        n = sum(opened)
        profile, max_w, max_at_y, top_yn, bot_yn = per_row_profile(opened, w, h)
        sweep.append({
            "radiusPx": R,
            "survivingPixels": n,
            "maxWidthNorm": max_w,
            "maxWidthAtYNorm": max_at_y,
            "bottomYNorm": bot_yn,
            "topYNorm": top_yn,
        })
        profiles[R] = profile

    # Plateau = first R whose |maxWidthNorm delta vs previous R| < threshold AND
    # stays < threshold for every subsequent R (a genuine flat region).
    plateau_i = None
    for i in range(1, len(sweep)):
        d0 = abs(sweep[i]["maxWidthNorm"] - sweep[i - 1]["maxWidthNorm"])
        if d0 >= CAP_PLATEAU_DELTA:
            continue
        stable = True
        for j in range(i + 1, len(sweep)):
            dj = abs(sweep[j]["maxWidthNorm"] - sweep[j - 1]["maxWidthNorm"])
            if dj >= CAP_PLATEAU_DELTA:
                stable = False
                break
        if stable:
            plateau_i = i
            break

    if plateau_i is None:
        return {
            "structuringElement": "circle-euclidean",
            "sweep": sweep,
            "plateauRadiusPx": None,
            "widthProfileAtPlateau": None,
            "note": "沒有平台期",
        }

    plateau_r = CAP_RADI[plateau_i]
    return {
        "structuringElement": "circle-euclidean",
        "sweep": sweep,
        "plateauRadiusPx": plateau_r,
        "widthProfileAtPlateau": profiles[plateau_r],
        "note": None,
    }


def analyze(path):
    w, h, body = load_rgb(path)
    mask = scan_mask(w, h, body)
    n, bbox, (cx, cy) = mask_stats(mask, w, h)
    equiv_r = math.sqrt(n / math.pi)

    pts = contour_loop(mask, w, h)
    sorted_c = sort_by_angle(pts, cx, cy)

    r_min = equiv_r * RADIUS_MIN_FRAC
    peaks = find_peaks(sorted_c, cx, cy, r_min)
    tips_idx = collect_tips(sorted_c, peaks, cx, cy, equiv_r, h)

    tips = []
    for i in tips_idx:
        px, py = sorted_c[i]
        r = math.hypot(px - cx, py - cy)
        a = math.degrees(math.atan2(py - cy, px - cx)) % 360.0
        tips.append({
            "tipPx": [round(px, 2), round(py, 2)],
            "tipNorm": [nx(h, w, px), ny(h, py)],
            "angleDeg": round(a, 2),
            "radiusPx": round(r, 2),
            "radiusNorm": round(r / h, 4),
            "widthAtHalfPx": round(width_at_half(
                sorted_c, cx, cy, px, py, mask, w, h), 2),
        })

    # two Y readings
    y1 = y2 = None
    if n > 0:
        y_bottom = bbox[3]
        y1 = ny(h, y_bottom)
        band = w * 0.10
        cap_bottom = -1
        for yy in range(h):
            for xx in range(w):
                if not mask[yy * w + xx]:
                    continue
                if abs(xx - cx) <= band and yy > cap_bottom:
                    cap_bottom = yy
        y2 = ny(h, cap_bottom) if cap_bottom >= 0 else None

    cap_shell = measure_cap_shell(mask, w, h, body)
    cap_core = measure_cap_core(mask, w, h)

    return {
        "image": path.name,
        "size": [w, h],
        "maskPixels": n,
        "centroidPx": [round(cx, 2), round(cy, 2)],
        "equivRadiusPx": round(equiv_r, 2),
        "hairMaskBottomYNorm": y1,
        "capHemYNorm": y2,
        "tips": tips,
        "capShell": cap_shell,
        "capCore": cap_core,
    }


def main():
    result = {
        "generatedBy": "spec/measure_hair_spikes.py",
        "method": (
            f"hair mask: R>{MASK_R} G>{MASK_G} B<{MASK_B} (R-B)>{MASK_RB}; "
            f"contour = mask pixels with >=1 four-neighbour outside mask; "
            f"peaks = radius local-maxima on angle-sorted contour; "
            f"accept if radius>equivRadius*{RADIUS_MIN_FRAC}, "
            f"angle-sep>={ANGLE_MIN_DEG} deg, "
            f"prominence>equivRadius*{PROM_MIN_FRAC}"
            f"; capCore = morphological opening with a circle-Euclidean "
            f"structuring element (erode then dilate, radius R px), "
            f"R sweep {CAP_R_MIN}..{CAP_R_MAX} step {CAP_R_STEP}; "
            f"plateau = first R whose maxWidthNorm delta < {CAP_PLATEAU_DELTA} "
            f"and stays < {CAP_PLATEAU_DELTA}"
        ),
        "views": {},
    }
    for name in ("front", "back", "left", "right", "more-angle"):
        v = analyze(ASSETS / f"{name}.webp")
        result["views"][name] = v
        print(
            f"{name:11s} mask={v['maskPixels']:7d}  equivR={v['equivRadiusPx']:.1f}"
            f"  bottom={v['hairMaskBottomYNorm']}  capHem={v['capHemYNorm']}"
            f"  tips={len(v['tips'])}"
        )
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("->", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
