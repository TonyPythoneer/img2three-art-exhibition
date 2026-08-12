"""The leather->pommel seam at 8x NEAREST, upright, plus the per-row widths behind it.

The question this answers is narrow: does the gold cone's widest row match the leather column's
own width at the junction (a FLUSH seam - the two parts share a silhouette edge), or is there a
visible STEP (the cone starts narrower than the shaft)? A flush seam means the two solids agree
on their FRONT-VIEW reach, which for `polygonSection`'s phase is each prism's INRADIUS, since the
phase offset puts a FACE CENTRE on the +X axis and not a vertex. A step means they agree on their
circumradius instead, or on nothing.

The frame is `measure_authority.py`'s and is rebuilt here from the same two assets and the same
rule (silhouette from the transparent cutout's alpha, axis from the farthest pair of per-row
extremes, origin re-pinned to the blade socket, tip at local Y = 760) - then PROVED identical by
reprinting the scale and tilt it recorded in measurements.json.

Written as its own script under its own output name so it shares no path with the gate scripts.
Run:  python3 src/exhibits/cloud-ultima-weapon-v2/spec/zoom_pommel_junction.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image

from measure_authority import classify, components, farthest_pair

HERE = Path(__file__).resolve().parent
EXHIBIT = HERE.parent
OUT = HERE / "zoom-spinner"
SCALE = 8

TIP_Y = 760.0
# Weapon-local window: the whole gold cone plus 30 units of leather above the seam.
BOX = (-24.0, -216.0, 24.0, -150.0)


def build_frame():
    """(origin_img, ux, uy, px_per_unit, crop, cut) in measure_authority.py's own terms."""
    crop = Image.open(EXHIBIT / "assets/artwork-sword-crop.webp").convert("RGB")
    cut = Image.open(EXHIBIT / "assets/artwork-sword-transparent.webp").convert("RGBA")
    w, h = crop.size
    cp, ap = crop.load(), cut.load()

    labels: list[list[str | None]] = [[None] * w for _ in range(h)]
    silhouette: list[tuple[int, int]] = []
    for y in range(h):
        for x in range(w):
            if ap[x, y][3] <= 96:
                continue
            silhouette.append((x, y))
            labels[y][x] = classify(*cp[x, y])

    rows: dict[int, list[int]] = {}
    for x, y in silhouette:
        rows.setdefault(y, []).append(x)
    cand = [c for y, xs in rows.items() for c in ((float(min(xs)), float(y)), (float(max(xs)), float(y)))]
    tip_img, pommel_img = farthest_pair(cand)
    if tip_img[1] > pommel_img[1]:
        tip_img, pommel_img = pommel_img, tip_img
    dx, dy = pommel_img[0] - tip_img[0], pommel_img[1] - tip_img[1]
    tilt = math.degrees(math.atan2(dx, dy))
    n = math.hypot(dx, dy)
    uy = (-dx / n, -dy / n)
    ux = (-uy[1], uy[0])

    gold_cc = components(labels, "gold", w, h)
    steel_cc = components(labels, "steel", w, h)
    shell_cc = components(labels, "shell", w, h)
    grip_cc = components(labels, "grip", w, h)
    guard = [p for b in gold_cc[:6] for p in b] + [p for b in steel_cc[:6] for p in b]
    gcx = sum(p[0] for p in guard) / len(guard)
    gcy = sum(p[1] for p in guard) / len(guard)
    t = (gcx - tip_img[0]) * uy[0] + (gcy - tip_img[1]) * uy[1]
    origin = (tip_img[0] + uy[0] * t, tip_img[1] + uy[1] * t)

    def local(x, y):
        vx, vy = x - origin[0], y - origin[1]
        return (vx * ux[0] + vy * ux[1], vx * uy[0] + vy * uy[1])

    shell_root_y = min(local(float(x), float(y))[1] for x, y in shell_cc[0])
    grip_top_y = max(local(float(x), float(y))[1] for x, y in grip_cc[0])
    socket_y = (shell_root_y + grip_top_y) / 2
    origin = (origin[0] + uy[0] * socket_y, origin[1] + uy[1] * socket_y)
    scale = TIP_Y / local(*tip_img)[1]  # local (image px) -> normalized units
    return origin, ux, uy, 1.0 / scale, tilt, crop, cut


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    origin, ux, uy, ppu, tilt, crop, cut = build_frame()
    recorded = json.loads((HERE / "measurements.json").read_text())
    print(
        f"frame: {ppu:.4f} px/unit (measurements.json {recorded['pixelsPerNormalizedUnit']}), "
        f"tilt {tilt:+.2f}deg (recorded {recorded['artworkTiltDeg']})"
    )

    cp, ap = crop.load(), cut.load()
    size = crop.size

    def to_image(lx, ly):
        return (
            origin[0] + ux[0] * lx * ppu + uy[0] * ly * ppu,
            origin[1] + ux[1] * lx * ppu + uy[1] * ly * ppu,
        )

    def at(lx, ly):
        ix, iy = to_image(lx, ly)
        x, y = int(round(ix)), int(round(iy))
        if not (0 <= x < size[0] and 0 <= y < size[1]):
            return None
        if ap[x, y][3] <= 96:
            return None
        return cp[x, y]

    # --- upright NEAREST resample, 1 output pixel = 1/SCALE normalized unit ---------------
    x0, y0, x1, y1 = BOX
    w = int(round((x1 - x0) * SCALE))
    h = int(round((y1 - y0) * SCALE))
    plain = Image.new("RGB", (w, h), (255, 255, 255))
    sp = plain.load()
    for j in range(h):
        ly = y1 - (j + 0.5) / SCALE
        for i in range(w):
            lx = x0 + (i + 0.5) / SCALE
            c = at(lx, ly)
            if c is not None:
                sp[i, j] = c
    gridded = plain.copy()
    gp = gridded.load()
    for j in range(h):
        ly = y1 - (j + 0.5) / SCALE
        for i in range(w):
            lx = x0 + (i + 0.5) / SCALE
            if abs(lx - round(lx / 5) * 5) < 0.5 / SCALE or abs(ly - round(ly / 5) * 5) < 0.5 / SCALE:
                r, g, b = gp[i, j]
                gp[i, j] = (255 - r, 255 - g, 255 - b)
    sheet = Image.new("RGB", (w * 2 + 8, h), (255, 255, 255))
    sheet.paste(plain, (0, 0))
    sheet.paste(gridded, (w + 8, 0))
    path = OUT / "pommel-junction-8x.png"
    sheet.save(path)
    print(f"wrote {path.relative_to(EXHIBIT)}  local {BOX}  (plain | 5-unit grid)")

    # --- per-row extents, sampled across at 1/4 unit --------------------------------------
    print("\n      Y   silhouette span            leather span              gold span")
    ly = -150.0
    while ly >= -214.0:
        cols: dict[str, list[float]] = {"any": [], "grip": [], "gold": []}
        lx = -30.0
        while lx <= 30.0:
            c = at(lx, ly)
            if c is not None:
                cols["any"].append(lx)
                k = classify(*c)
                if k in cols:
                    cols[k].append(lx)
            lx += 0.25
        def span(v):
            if not v:
                return "          --            "
            return f"{min(v):+7.2f}..{max(v):+7.2f} w={max(v)-min(v):5.2f}"
        if cols["any"]:
            print(f"{ly:7.1f}   {span(cols['any'])}  {span(cols['grip'])}  {span(cols['gold'])}")
        ly -= 1.0


if __name__ == "__main__":
    main()
