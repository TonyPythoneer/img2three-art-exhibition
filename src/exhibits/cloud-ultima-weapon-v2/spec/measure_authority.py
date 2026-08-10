"""Authority measurement for the FF7 Ultima Weapon v2 reconstruction.

Reads the review package's sword crop + transparent cutout and emits machine-readable
landmarks in weapon-local coordinates (normalized so the blade tip sits at local Y=760,
matching the master prompt's normalized-1000 contract).

Pipeline:
  1. silhouette mask from the transparent asset's alpha
  2. shaft axis from the two farthest silhouette points (tip, pommel tip)
  3. colour classes grounded in the artwork's HSV census, then connected components
     so overlapping hue families (gem vs drivers vs dark core) split spatially
  4. rotate every pixel into weapon-local space (+Y = tip, +X = screen-right upright)
  5. report bbox / centroid / extremes / width profile per named part

Run:  python3 measure_authority.py <exhibit-dir> <out.json> [<label-map.png>]
      python3 measure_authority.py --render <render.png> <out.json> [<label-map.png>]

The `--render` form runs the identical pipeline over an RGBA render, so a review render can be
read back in the same normalized-1000 weapon-local units as the artwork. Comparing those two
tables is far more diagnostic than a silhouette IoU: IoU says "0.57", the tables say which
station is 12 units too wide.
"""

from __future__ import annotations

import colorsys
import json
import math
import sys
from pathlib import Path

from PIL import Image

# Colour classes, grounded in the crop's HSV census (see spec/image-analysis.md).
# Order matters: narrow saturated families are tested before the pale catch-all.
CLASS_COLORS = {
    "shell": (215, 217, 235),
    "insert": (90, 45, 200),
    "red": (200, 40, 70),
    "gold": (150, 140, 80),
    "steel": (70, 70, 82),
    "grip": (20, 20, 22),
}


def classify(r: int, g: int, b: int) -> str:
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h *= 360
    if 225 <= h <= 285 and s >= 0.40 and v >= 0.15:
        return "insert"
    if (h >= 300 or h <= 22) and s >= 0.35 and v >= 0.12:
        return "red"  # gem + drivers + dark core all live here; split by component
    if 35 <= h <= 80 and s >= 0.15 and v >= 0.25:
        return "gold"
    if v >= 0.55 and s <= 0.30:
        return "shell"
    if v <= 0.13:
        return "grip"
    return "steel"


def components(labels: list[list[str | None]], want: str, w: int, h: int) -> list[list[tuple[int, int]]]:
    """4-connected components of one class. ponytail: iterative flood fill, plain
    lists — the mask is 210x434, a scipy dependency would buy nothing here."""
    seen = [[False] * w for _ in range(h)]
    out: list[list[tuple[int, int]]] = []
    for sy in range(h):
        for sx in range(w):
            if seen[sy][sx] or labels[sy][sx] != want:
                continue
            stack = [(sx, sy)]
            seen[sy][sx] = True
            blob: list[tuple[int, int]] = []
            while stack:
                x, y = stack.pop()
                blob.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and labels[ny][nx] == want:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            out.append(blob)
    out.sort(key=len, reverse=True)
    return out


def farthest_pair(pts: list[tuple[float, float]]) -> tuple[tuple[float, float], tuple[float, float]]:
    """Brute-force diameter over the per-row silhouette extremes (a cheap hull superset).
    ponytail: O(n^2) on ~800 candidates; rotating calipers if this ever gets big."""
    best = (0.0, pts[0], pts[0])
    for i, a in enumerate(pts):
        for b in pts[i + 1 :]:
            d = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
            if d > best[0]:
                best = (d, a, b)
    return best[1], best[2]


def main() -> None:
    argv = sys.argv[1:]
    if argv and argv[0] == "--render":
        source = Path(argv[1])
        out_path = Path(argv[2])
        label_png = Path(argv[3]) if len(argv) > 3 else None
        rgba = Image.open(source).convert("RGBA")
        crop = Image.new("RGB", rgba.size, (255, 255, 255))
        crop.paste(rgba, mask=rgba.split()[3])
        cut = rgba
    else:
        exhibit = Path(argv[0])
        out_path = Path(argv[1])
        label_png = Path(argv[2]) if len(argv) > 2 else None
        source = exhibit / "assets/artwork-sword-crop.webp"
        crop = Image.open(source).convert("RGB")
        cut = Image.open(exhibit / "assets/artwork-sword-transparent.webp").convert("RGBA")
    w, h = crop.size
    cp = crop.load()
    ap = cut.load()
    assert cp is not None and ap is not None

    labels: list[list[str | None]] = [[None] * w for _ in range(h)]
    silhouette: list[tuple[int, int]] = []
    for y in range(h):
        for x in range(w):
            if ap[x, y][3] <= 96:
                continue
            silhouette.append((x, y))
            labels[y][x] = classify(*cp[x, y])

    # --- weapon-local frame ------------------------------------------------
    cand: list[tuple[float, float]] = []
    rows: dict[int, list[int]] = {}
    for x, y in silhouette:
        rows.setdefault(y, []).append(x)
    for y, xs in rows.items():
        cand.append((float(min(xs)), float(y)))
        cand.append((float(max(xs)), float(y)))
    tip_img, pommel_img = farthest_pair(cand)
    if tip_img[1] > pommel_img[1]:
        tip_img, pommel_img = pommel_img, tip_img

    dx, dy = pommel_img[0] - tip_img[0], pommel_img[1] - tip_img[1]
    tilt = math.degrees(math.atan2(dx, dy))
    n = math.hypot(dx, dy)
    uy = (-dx / n, -dy / n)  # local +Y in image space (tip-ward)
    ux = (-uy[1], uy[0])  # local +X = screen-right once the sword stands upright

    # --- parts from connected components ----------------------------------
    shell_cc = components(labels, "shell", w, h)
    insert_cc = components(labels, "insert", w, h)
    red_cc = components(labels, "red", w, h)
    gold_cc = components(labels, "gold", w, h)
    steel_cc = components(labels, "steel", w, h)
    grip_cc = components(labels, "grip", w, h)

    def centroid(blob: list[tuple[int, int]]) -> tuple[float, float]:
        return (sum(p[0] for p in blob) / len(blob), sum(p[1] for p in blob) / len(blob))

    # Provisional origin: the gold+steel centroid projected onto the shaft axis. The gold
    # caps hang below the blade socket, so this lands low; it is only a staging frame.
    guard_blob = [p for b in gold_cc[:6] for p in b] + [p for b in steel_cc[:6] for p in b]
    gcx, gcy = centroid(guard_blob)
    t = (gcx - tip_img[0]) * uy[0] + (gcy - tip_img[1]) * uy[1]
    origin = (tip_img[0] + uy[0] * t, tip_img[1] + uy[1] * t)

    def local(x: float, y: float) -> tuple[float, float]:
        vx, vy = x - origin[0], y - origin[1]
        return (vx * ux[0] + vy * ux[1], vx * uy[0] + vy * uy[1])

    # The master prompt's guard_center is the blade socket, i.e. where the shell's root
    # meets the grip's top. Re-pin the origin there: the staging frame sits ~45 units low,
    # which alone accounts for the grip reading 30% short against the normalized contract.
    shell_root_y = min(local(float(x), float(y))[1] for x, y in shell_cc[0])
    grip_top_y = max(local(float(x), float(y))[1] for x, y in grip_cc[0])
    socket_y = (shell_root_y + grip_top_y) / 2
    origin = (origin[0] + uy[0] * socket_y, origin[1] + uy[1] * socket_y)

    scale = 760.0 / local(*tip_img)[1]

    def norm(x: float, y: float) -> tuple[float, float]:
        lx, ly = local(x, y)
        return (round(lx * scale, 1), round(ly * scale, 1))

    def stats(blob: list[tuple[int, int]]) -> dict:
        pts = [norm(float(x), float(y)) for x, y in blob]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return {
            "pixels": len(pts),
            "bbox": {
                "minX": round(min(xs), 1),
                "maxX": round(max(xs), 1),
                "minY": round(min(ys), 1),
                "maxY": round(max(ys), 1),
            },
            "centroid": [round(sum(xs) / len(xs), 1), round(sum(ys) / len(ys), 1)],
            "apex": list(max(pts, key=lambda p: p[1])),
            "base": list(min(pts, key=lambda p: p[1])),
            "farthestFromGuard": list(max(pts, key=lambda p: math.hypot(*p))),
        }

    def axis(blob: list[tuple[int, int]]) -> dict:
        """Principal axis of a rod, as a normalized-space segment. A PCA fit beats
        nearest/farthest endpoints here: the rod roots are occluded by the guard, so
        the extreme points sit on whatever fragment happens to poke out."""
        pts = [norm(float(x), float(y)) for x, y in blob]
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        sxx = sum((p[0] - mx) ** 2 for p in pts)
        syy = sum((p[1] - my) ** 2 for p in pts)
        sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
        theta = 0.5 * math.atan2(2 * sxy, sxx - syy)
        dxa, dya = math.cos(theta), math.sin(theta)
        if (mx > 0) != (dxa > 0):  # point the axis outward from the guard
            dxa, dya = -dxa, -dya
        proj = [(p[0] - mx) * dxa + (p[1] - my) * dya for p in pts]
        near, far = min(proj), max(proj)
        halfw = max(abs((p[0] - mx) * -dya + (p[1] - my) * dxa) for p in pts)
        return {
            "rootPoint": [round(mx + dxa * near, 1), round(my + dya * near, 1)],
            "endPoint": [round(mx + dxa * far, 1), round(my + dya * far, 1)],
            "elevationDeg": round(math.degrees(math.atan2(dya, abs(dxa))), 1),
            "length": round(far - near, 1),
            "halfWidth": round(halfw, 1),
        }

    # Red family: gem sits near the axis just above the guard; drivers reach far laterally;
    # the dark core triangle is the desaturated blob overlapping the insert's lower half.
    red_parts: dict[str, list[dict]] = {"gem": [], "drivers": [], "core": []}
    for blob in red_cc:
        if len(blob) < 20:
            continue
        s = stats(blob)
        cx, cy = s["centroid"]
        if abs(cx) > 70:
            red_parts["drivers"].append({**s, "axis": axis(blob)})
        elif cy > 130:
            red_parts["core"].append(s)
        else:
            red_parts["gem"].append(s)
    red_parts["drivers"].sort(key=lambda d: (d["centroid"][0] > 0, -d["centroid"][1]))
    for i, d in enumerate(red_parts["drivers"]):
        side = "left" if d["centroid"][0] < 0 else "right"
        d["id"] = f"{side}_{'upper' if i % 2 == 0 else 'lower'}"

    # The dark core triangle and the gem share one connected red blob in this view, so
    # split that blob by value instead of by connectivity.
    core_px: list[tuple[int, int]] = []
    gem_px: list[tuple[int, int]] = []
    for blob in red_cc:
        s = stats(blob)
        if abs(s["centroid"][0]) > 60:
            continue
        for x, y in blob:
            r, g, b = cp[x, y]
            _, _, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            (core_px if v < 0.34 else gem_px).append((x, y))

    def profile(blob: list[tuple[int, int]], step: int = 25) -> list[dict]:
        buckets: dict[int, list[float]] = {}
        for x, y in blob:
            lx, ly = norm(float(x), float(y))
            buckets.setdefault(int(round(ly / step)) * step, []).append(lx)
        return [
            {"y": k, "minX": round(min(v), 1), "maxX": round(max(v), 1), "width": round(max(v) - min(v), 1)}
            for k, v in sorted(buckets.items())
        ]

    blade_silhouette = [p for p in silhouette if norm(float(p[0]), float(p[1]))[1] > -10]

    result = {
        "units": "normalized-1000; guard centre at origin, blade tip at local Y=760",
        "sourceImage": str(source),
        "imageSize": [w, h],
        "artworkTiltDeg": round(tilt, 2),
        "pixelsPerNormalizedUnit": round(1 / scale, 4),
        "landmarks": {"tip": list(norm(*tip_img)), "pommelTip": list(norm(*pommel_img))},
        "outerCrystalShell": stats(shell_cc[0]),
        "shellWidthProfile": profile(shell_cc[0]),
        "purpleEnergyInsert": stats(insert_cc[0]),
        "insertWidthProfile": profile(insert_cc[0], 25),
        "red": red_parts,
        "darkCoreTriangle": stats(core_px) if core_px else {"pixels": 0},
        "darkCoreProfile": profile(core_px, 20) if core_px else [],
        "rootDiamondGem": stats(gem_px) if gem_px else {"pixels": 0},
        "gemProfile": profile(gem_px, 20) if gem_px else [],
        "gold": [stats(b) for b in gold_cc if len(b) >= 20],
        "steel": [stats(b) for b in steel_cc if len(b) >= 20],
        "grip": [stats(b) for b in grip_cc if len(b) >= 20],
        "fullSilhouetteProfile": profile(blade_silhouette),
    }
    out_path.write_text(json.dumps(result, indent=2))

    if label_png:
        vis = Image.new("RGB", (w, h), (255, 255, 255))
        vp = vis.load()
        assert vp is not None
        for y in range(h):
            for x in range(w):
                lab = labels[y][x]
                if lab:
                    vp[x, y] = CLASS_COLORS[lab]
        vis.resize((w * 4, h * 4), Image.Resampling.NEAREST).save(label_png)

    print(json.dumps({k: v for k, v in result.items() if not k.endswith("Profile")}, indent=2))


if __name__ == "__main__":
    main()
