#!/usr/bin/env python3
"""Measure the purpleEnergyInsert's colour gradient off the authority artwork.

Layer 6 of `spec/image-analysis.md` records the insert as four stops and calls the gradient a
"linear vertical ramp". That census is right, but it says nothing about *where along the blade*
each stop sits, and the factory's `applyRamp` spaces its three stops evenly over Y = 42..480.
This script measures the placement, so the ramp can be fitted rather than guessed.

Method:
  1. reuse `measure_authority`'s weapon-local frame verbatim, so Y here is the same Y the
     factory's `INSERT_STATIONS` and `applyRamp` are authored in
  2. take the insert's connected component, erode 1px to drop the antialias rim against the
     shell (the shell is near-white and drags the edge pixels 40+ levels bright)
  3. per image scanline, take the channel medians -> a colour profile down the blade axis
  4. fit the three `applyRamp` stops so the ramp REPRODUCES that profile. applyRamp lerps in
     LINEAR light (THREE.Color holds linear once ColorManagement is on), so the fit runs on
     linear values and is scored on the sRGB the viewer actually sees.

Emits `insert-gradient.json` plus NEAREST zooms at 6-8x.

Run:  python3 artifacts/exhibits/cloud-ultima-weapon-v2/spec/pbr-evidence/insert-gradient/measure_insert_gradient.py
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SPEC = HERE.parent.parent
EXHIBIT = SPEC.parent
sys.path.insert(0, str(SPEC))
from measure_authority import classify, components, farthest_pair  # noqa: E402

Y_BOTTOM, Y_TOP = 42.0, 480.0  # must track INSERT_STATIONS / applyRamp in the factory


# --- three.js colour space (ColorManagement.js) -----------------------------
def s2l(c: float) -> float:
    c /= 255.0
    return c * 0.0773993808 if c < 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def l2s(c: float) -> float:
    c = max(0.0, min(1.0, c))
    return (c * 12.92 if c < 0.0031308 else 1.055 * (c ** 0.41666) - 0.055) * 255.0


def weapon_local_insert() -> tuple[Image.Image, list[tuple]]:
    """(crop, [(imgX, imgY, localX, localY, r, g, b)]) for the insert's main component."""
    crop = Image.open(EXHIBIT / "assets/artwork-sword-crop.png").convert("RGB")
    cut = Image.open(EXHIBIT / "assets/artwork-sword-transparent.png").convert("RGBA")
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
    cand = [(float(f(xs)), float(y)) for y, xs in rows.items() for f in (min, max)]
    tip, pommel = farthest_pair(cand)
    if tip[1] > pommel[1]:
        tip, pommel = pommel, tip
    dx, dy = pommel[0] - tip[0], pommel[1] - tip[1]
    n = math.hypot(dx, dy)
    uy = (-dx / n, -dy / n)
    ux = (-uy[1], uy[0])

    shell_cc = components(labels, "shell", w, h)
    insert_cc = components(labels, "insert", w, h)
    gold_cc = components(labels, "gold", w, h)
    steel_cc = components(labels, "steel", w, h)
    grip_cc = components(labels, "grip", w, h)

    guard = [p for b in gold_cc[:6] for p in b] + [p for b in steel_cc[:6] for p in b]
    gcx = sum(p[0] for p in guard) / len(guard)
    gcy = sum(p[1] for p in guard) / len(guard)
    t = (gcx - tip[0]) * uy[0] + (gcy - tip[1]) * uy[1]
    origin = [tip[0] + uy[0] * t, tip[1] + uy[1] * t]

    def local(x, y):
        vx, vy = x - origin[0], y - origin[1]
        return (vx * ux[0] + vy * ux[1], vx * uy[0] + vy * uy[1])

    socket = (min(local(float(x), float(y))[1] for x, y in shell_cc[0])
              + max(local(float(x), float(y))[1] for x, y in grip_cc[0])) / 2
    origin = [origin[0] + uy[0] * socket, origin[1] + uy[1] * socket]
    scale = 760.0 / local(*tip)[1]

    out = []
    for x, y in insert_cc[0]:
        lx, ly = local(float(x), float(y))
        out.append((x, y, lx * scale, ly * scale, *cp[x, y]))
    return crop, out


def erode(px: list[tuple], k: int) -> list[tuple]:
    cur = {(p[0], p[1]) for p in px}
    nb = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    for _ in range(k):
        cur = {(x, y) for (x, y) in cur if all((x + a, y + b) in cur for a, b in nb)}
    return [p for p in px if (p[0], p[1]) in cur]


def ramp_linear(stops: list[float], y: float) -> float:
    """Exactly what `applyRamp` stores in the colour attribute: linear light, one channel."""
    t = max(0.0, min(1.0, (y - Y_BOTTOM) / (Y_TOP - Y_BOTTOM)))
    span = t * (len(stops) - 1)
    lo = min(int(span), len(stops) - 2)
    f = span - lo
    return s2l(stops[lo]) * (1 - f) + s2l(stops[lo + 1]) * f


def ramp(stops: list[float], y: float) -> float:
    """The same value decoded back to sRGB 0..255, for scoring against the artwork."""
    return l2s(ramp_linear(stops, y))


def main() -> None:
    crop, px = weapon_local_insert()
    core = erode(px, 1)
    byrow: dict[int, list[tuple]] = {}
    for p in core:
        byrow.setdefault(p[1], []).append(p)
    profile = sorted(
        (statistics.median(p[3] for p in sel), len(sel),
         statistics.median(p[4] for p in sel), statistics.median(p[5] for p in sel),
         statistics.median(p[6] for p in sel))
        for sel in byrow.values() if len(sel) >= 4
    )
    N = sum(r[1] for r in profile)

    # --- which axis is the gradient on? -----------------------------------
    def r2(key, ch):
        vals = [(key(p), p[4 + ch]) for p in core]
        mx = sum(v[0] for v in vals) / len(vals)
        my = sum(v[1] for v in vals) / len(vals)
        sxx = sum((v[0] - mx) ** 2 for v in vals)
        sxy = sum((v[0] - mx) * (v[1] - my) for v in vals)
        m = sxy / sxx if sxx else 0.0
        c = my - m * mx
        tot = sum((v[1] - my) ** 2 for v in vals)
        res = sum((v[1] - (m * v[0] + c)) ** 2 for v in vals)
        return (1 - res / tot if tot else 0.0), m * 100

    axes = {}
    for name, key in (("localY", lambda p: p[3]), ("localX", lambda p: p[2])):
        axes[name] = {ch: {"r2": round(r2(key, i)[0], 3), "slopePer100": round(r2(key, i)[1], 2)}
                      for i, ch in enumerate("RGB")}

    # --- fit the three stops ----------------------------------------------
    def rms(stops, ch):
        return math.sqrt(sum(r[1] * (ramp(stops, r[0]) - r[2 + ch]) ** 2 for r in profile) / N)

    def fit(ch, init, pinned=None):
        best, bc, step = list(init), None, 32.0
        bc = rms(best, ch)
        free = [i for i in range(3) if pinned is None or i not in pinned]
        while step > 0.05:
            moved = False
            for i in free:
                for d in (-step, step):
                    cand = list(best)
                    cand[i] = max(0.0, min(255.0, cand[i] + d))
                    v = rms(cand, ch)
                    if v < bc - 1e-9:
                        best, bc, moved = cand, v, True
            if not moved:
                step /= 2
        return best, bc

    CURRENT = {"base": "#7F3CF2", "mid": "#2F238C", "apex": "#160D59"}
    cur = [[int(CURRENT[k][1 + 2 * c:3 + 2 * c], 16) for k in ("base", "mid", "apex")]
           for c in range(3)]
    # The apex stop is pinned to a directly-observed tip pixel value rather than left free: the
    # free optimum runs to (0,0,64), which fits the observable rows marginally better but is an
    # extrapolation 20 units past the last row wide enough to read. See guess list, item 1.
    APEX_PIN = (8, 4, 68)
    fitted = [fit(c, [cur[c][0], cur[c][1], APEX_PIN[c]], pinned={2})[0] for c in range(3)]

    def hexes(per_ch):
        return ["#%02X%02X%02X" % tuple(int(round(per_ch[c][i])) for c in range(3))
                for i in range(3)]

    # --- where does each CURRENT stop actually live in the artwork? --------
    placed = {"base": Y_BOTTOM, "mid": (Y_BOTTOM + Y_TOP) / 2, "apex": Y_TOP}
    placement = {}
    for i, (name, hx) in enumerate(CURRENT.items()):
        tgt = [int(hx[1 + 2 * c:3 + 2 * c], 16) for c in range(3)]
        m = min(profile, key=lambda r: sum((r[2 + c] - tgt[c]) ** 2 for c in range(3)))
        placement[name] = {
            "hex": hx, "occursAtLocalY": round(m[0], 1),
            "applyRampPlacesAtY": placed[name],
            "offBy": round(m[0] - placed[name], 1),
        }

    # --- the flat-emissive floor ------------------------------------------
    E = [s2l(int(CURRENT["base"][1 + 2 * c:3 + 2 * c], 16)) * 0.22 for c in range(3)]
    floor = [round(l2s(e), 1) for e in E]
    unreachable = {}
    for c, nm in enumerate("RGB"):
        below = [r for r in profile if r[2 + c] < floor[c]]
        unreachable[nm] = {
            "fromLocalY": round(min((r[0] for r in below), default=0), 1) if below else None,
            "shareOfProjectedArea": round(sum(r[1] for r in below) / N, 3) if below else 0.0,
        }
    # Weighted by each row's pixel count, i.e. by projected area — the quantity a render-vs-artwork
    # mean actually compares. No sRGB round-trip: the colour attribute stays linear all the way to
    # the shader, so the mean that the emissive has to match is the mean of the linear values.
    meanV = [sum(r[1] * ramp_linear(fitted[c], r[0]) for r in profile) / N for c in range(3)]

    out = {
        "sourceImage": "assets/artwork-sword-crop.png",
        "frame": "weapon-local normalized-1000, identical to spec/measure_authority.py",
        "insertPixels": len(px), "afterErode1": len(core), "profileRows": len(profile),
        "gradientAxis": axes,
        "profile": [{"localY": round(r[0], 1), "n": r[1],
                     "rgb": [round(r[2]), round(r[3]), round(r[4])],
                     "hex": "#%02X%02X%02X" % (round(r[2]), round(r[3]), round(r[4]))}
                    for r in profile],
        "currentStopPlacement": placement,
        "stops": {
            "current": {"hex": list(CURRENT.values()),
                        "rmsVsArtwork": {nm: round(rms(cur[c], c), 2) for c, nm in enumerate("RGB")}},
            "fitted": {"hex": hexes(fitted),
                       "rmsVsArtwork": {nm: round(rms(fitted[c], c), 2) for c, nm in enumerate("RGB")}},
        },
        "flatEmissive": {
            "wasEmissive": CURRENT["base"], "wasIntensity": 0.22,
            "floorLinear": [round(e, 5) for e in E], "floorSrgb": floor,
            "artworkDarkerThanFloor": unreachable,
            "meanVertexColourLinear": [round(v, 5) for v in meanV],
            "levelPreservingIntensity": round(E[2] / meanV[2], 3),
        },
    }
    (HERE / "insert-gradient.json").write_text(json.dumps(out, indent=2) + "\n")

    # --- NEAREST zooms -----------------------------------------------------
    xs = [p[0] for p in px]
    ys = [p[1] for p in px]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    M = 3

    def zoom(box, k, name, grid=None):
        a = crop.crop(box)
        b = a.resize((a.width * k, a.height * k), Image.NEAREST)
        if grid:
            d = ImageDraw.Draw(b)
            for i in range(0, a.width + 1, grid):
                d.line([(i * k, 0), (i * k, b.height)], fill=(255, 255, 0))
            for j in range(0, a.height + 1, grid):
                d.line([(0, j * k), (b.width, j * k)], fill=(255, 255, 0))
        b.save(HERE / name)

    def band(top: int, bottom: int) -> tuple[int, int, int, int]:
        """Box around only the insert pixels in [top, bottom]. The artwork is rolled 18.13deg, so
        the insert's full-height bbox is far wider than the part is at any one height — cropping
        to the bbox puts the apex in a corner behind 60 columns of shell."""
        sel = [p for p in px if top <= p[1] <= bottom]
        return (min(p[0] for p in sel) - M, top - M, max(p[0] for p in sel) + 1 + M, bottom + 1 + M)

    zoom((x0 - M, y0 - M, x1 + 1 + M, y1 + 1 + M), 6, "01-insert-full-6x.png")
    zoom(band(y0, y0 + 30), 8, "02-insert-apex-8x.png", grid=5)
    zoom(band(y1 - 30, y1), 8, "03-insert-base-8x.png", grid=5)
    mid = (y0 + y1) // 2
    zoom(band(mid - 15, mid + 15), 8, "04-insert-mid-8x.png", grid=5)

    # artwork | current ramp | fitted ramp, at 3x width and 4x height per source row
    W = 46
    strip = Image.new("RGB", (W * 3 + 24, (y1 - y0 + 1) * 4), (24, 24, 28))
    d = ImageDraw.Draw(strip)
    for iy in range(y0, y1 + 1):
        sel = byrow.get(iy, [])
        if len(sel) < 4:
            continue
        ly = statistics.median(p[3] for p in sel)
        art = tuple(int(statistics.median(p[c] for p in sel)) for c in (4, 5, 6))
        yy = (iy - y0) * 4
        d.rectangle([0, yy, W - 1, yy + 3], fill=art)
        d.rectangle([W + 12, yy, W * 2 + 11, yy + 3],
                    fill=tuple(int(round(ramp(cur[c], ly))) for c in range(3)))
        d.rectangle([W * 2 + 24, yy, W * 3 + 23, yy + 3],
                    fill=tuple(int(round(ramp(fitted[c], ly))) for c in range(3)))
    strip.resize((strip.width * 3, strip.height), Image.NEAREST).save(
        HERE / "05-ramp-artwork-vs-current-vs-fitted.png")

    print(f"insert {len(px)} px, {len(profile)} profile rows over localY "
          f"{profile[0][0]:.0f}..{profile[-1][0]:.0f}")
    print("gradient axis R2  localY", {c: axes["localY"][c]["r2"] for c in "RGB"},
          " localX", {c: axes["localX"][c]["r2"] for c in "RGB"})
    for name, v in placement.items():
        print(f"  current {name:5s} {v['hex']} is the artwork at localY {v['occursAtLocalY']:.0f}, "
              f"applyRamp places it at {v['applyRampPlacesAtY']:.0f}  (off {v['offBy']:+.0f})")
    print("  stops current", list(CURRENT.values()), out["stops"]["current"]["rmsVsArtwork"])
    print("  stops fitted ", hexes(fitted), out["stops"]["fitted"]["rmsVsArtwork"])
    print(f"  flat emissive floor sRGB {floor}; artwork darker than it over "
          f"{unreachable['R']['shareOfProjectedArea']:.0%} (R) of the insert")
    print(f"  level-preserving emissiveIntensity once emissive *= vColor: "
          f"{out['flatEmissive']['levelPreservingIntensity']}")
    print(f"wrote {HERE}/insert-gradient.json + 5 zooms")


if __name__ == "__main__":
    main()
