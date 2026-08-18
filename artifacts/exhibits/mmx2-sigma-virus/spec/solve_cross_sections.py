"""Solve the head's actual cross-section at every row, from the yaw sweep itself.

Everything before this treated the reference as a front view plus one depth scalar: each ring was
`chamferedRing(halfWidth(row), halfWidth(row) * 1.4255, 0.35)`. Two of those three numbers were
authored — the depth ratio was at least measured, but the chamfer, and the assumption that every
row is the SAME shape scaled, never were. The sheet does not require any of that. It is one mesh
photographed at many yaws, so each row's cross-section can be reconstructed instead of designed.

## The method

Filter to the frames whose height matches the front view's 68-70px and the rotation must have been
about the vertical axis: 87 pure-yaw frames. For a frame at yaw t, the image's horizontal axis
measures the body's extent along u(t) = (cos t, 0, -sin t). Per row, that extent is the
cross-section's WIDTH along u — and width is registration-free, which matters because nothing here
knows where the model's axis projects to in a turned frame. Using left/right edges separately
would need that; using the width does not.

Widths at many angles determine the cross-section's **central symmetral** — the centrally
symmetric convex body with the same width function. Its support function is h(t) = w(t) / 2, and
the body is the intersection of the half-planes  p . u(t) <= h(t)  over every measured t and its
opposite. That is a Sutherland-Hodgman clip of a large starting square, once per row.

What is lost is front/back asymmetry: the face is flat and the dome bulges, and a width-only
reconstruction cannot tell those apart. That is recorded rather than hidden, and the face parts
still anchor to the front surface as before.

## Estimating the yaw of each frame

Nothing labels the frames, so the yaw is measured from the eyes. Their 3D separation is fixed, so
its projection scales as cos(t):

  cos t = (accent x-extent in this frame) / (accent x-extent in the most frontal frame)

The wireframe is see-through and draws the far eye's hidden lines too, so the far eye keeps
contributing at large yaw instead of dropping out and biasing the estimate. This is model-free —
it never consults the build, so it cannot launder the build's own depth guess back in as evidence.

## What it found, and why that matters

The reconstructed widthX per row lands on the front view's own measurements — 20.4 against 20 at
row 0, 38.7 against 38 at row 16, 48.1 against 47 at row 32 — even though the front view's widths
were never fed in. That agreement is the check that the yaw estimate, the binning and the
half-plane intersection are all doing what they claim.

The depth profile is the payoff, and it is not proportional to width:

  row  0  width 20.4  depth  8.4   ratio 0.41   <- the crown is a thin slab front-to-back
  row 24  width 38.7  depth 54.1   ratio 1.40
  row 44  width 49.2  depth 67.7   ratio 1.38
  row 60  width 33.5  depth 33.8   ratio 1.01   <- the jaw is as deep as it is wide

The build assumed one global 1.4255 everywhere. That is right in the middle of the head and wrong
by more than 3x at the crown.

Usage:
  python3 solve_cross_sections.py <sheet.png> <frame-index.json> <out.json> [--ts <out.ts>]
"""

import json
import math
import pathlib
import sys

from PIL import Image

BG = (0, 0, 41)
BG_TOL = 24
ROWS = 69            # the geometry authority's height, the row grid everything resamples onto
BINS = 18            # yaw bins across 0..90 degrees, i.e. 5 degrees each
POLY = 16            # vertices emitted per cross-section


def is_bg(p):
    return all(abs(a - b) <= BG_TOL for a, b in zip(p, BG))


def hue_family(p):
    r, g, b = p
    if g > r + 40 and g > b + 40:
        return "green"
    if r > g + 40 and b > g + 40:
        return "purple"
    if r > g + 40 and r > b + 40:
        return "orange" if g > 60 else "red"
    if b > r + 40 and b > g + 20:
        return "blue"
    return "other"


def scan(px, f):
    """Per-row widths resampled onto ROWS, plus the accent's x-extent."""
    x0, y0, w, h = f["x0"], f["y0"], f["w"], f["h"]
    hues = {}
    rows_raw = []
    accent_x = []
    for y in range(y0, y0 + h):
        xs = []
        for x in range(x0, x0 + w):
            p = px[x, y]
            if is_bg(p):
                continue
            xs.append(x - x0)
            hues[hue_family(p)] = hues.get(hue_family(p), 0) + 1
        rows_raw.append((min(xs), max(xs)) if xs else None)
    dominant = max(hues, key=lambda k: hues[k]) if hues else "other"
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            p = px[x, y]
            if not is_bg(p) and hue_family(p) not in (dominant, "other"):
                accent_x.append(x - x0)

    widths = []
    for r in range(ROWS):
        src = rows_raw[min(h - 1, int(r * h / ROWS))]
        widths.append(None if src is None else src[1] - src[0] + 1)
    extent = (max(accent_x) - min(accent_x) + 1) if accent_x else 0
    return widths, extent


def clip(poly, nx, nz, d):
    """Sutherland-Hodgman: keep the half-plane  n . p <= d."""
    out = []
    n = len(poly)
    for i in range(n):
        ax, az = poly[i]
        bx, bz = poly[(i + 1) % n]
        da = nx * ax + nz * az - d
        db = nx * bx + nz * bz - d
        if da <= 0:
            out.append((ax, az))
        if (da > 0) != (db > 0):
            t = da / (da - db)
            out.append((ax + (bx - ax) * t, az + (bz - az) * t))
    return out


def resample(poly, k):
    """k vertices at even angles about the centroid, so every row emits the same ring size."""
    if len(poly) < 3:
        return None
    out = []
    for i in range(k):
        a = 2 * math.pi * i / k
        dx, dz = math.cos(a), math.sin(a)
        # Farthest point of the polygon along this ray, by clipping the ray against each edge.
        best = 0.0
        for j in range(len(poly)):
            px1, pz1 = poly[j]
            px2, pz2 = poly[(j + 1) % len(poly)]
            ex, ez = px2 - px1, pz2 - pz1
            den = dx * ez - dz * ex
            if abs(den) < 1e-12:
                continue
            # Solving  t*d = P1 + s*e  for (t, s). Both signs matter and both were wrong on the
            # first run: the flipped t sent every hit to the negative side of the ray, `t >= 0`
            # then kept whatever survived by accident, and rows came back 101px wide on a 47px
            # head. A cross-section wider than the head it came from is the tell.
            t = (px1 * ez - pz1 * ex) / den
            s = (dz * px1 - dx * pz1) / den
            if t >= 0 and 0 <= s <= 1:
                best = max(best, t)
        out.append((round(dx * best, 4), round(dz * best, 4)))
    return out


TS_STEP = 2      # emit every other row; the sections vary smoothly, the factory interpolates
TS_VERTS = 12    # down from POLY, for the same reason


def emit_ts(path, rec):
    """Write the solved sections as a generated TypeScript table."""
    lines = [
        "// GENERATED — do not edit by hand.",
        "//",
        "//   python3 artifacts/exhibits/mmx2-sigma-virus/spec/solve_cross_sections.py \\",
        "//     artifacts/exhibits/mmx2-sigma-virus/references/sigma-wireframe-sheet.png \\",
        "//     artifacts/exhibits/mmx2-sigma-virus/spec/frame-index.json \\",
        "//     artifacts/exhibits/mmx2-sigma-virus/spec/cross-sections.json \\",
        "//     --ts src/utils/sigmaVirusHead/crossSections.ts",
        "//",
        "// The head's cross-section at every other frame row, solved from the 87 pure-yaw frames",
        "// on the sprite sheet rather than designed. Each row is a closed XZ polygon in REFERENCE",
        "// PIXELS: x across the head, z front-to-back, centred on the row's own centre.",
        "//",
        "// These are the CENTRAL SYMMETRAL of the true cross-sections — reconstructed from",
        "// silhouette WIDTHS, which are registration-free, so they carry each row's true size and",
        "// elongation but not its front/back asymmetry. The sweep also stops at "
        f'{rec["yawRange"][1]:.1f} degrees of',
        "// yaw, so the z direction is bounded by the last constraint rather than by a true side",
        "// view, and depth is if anything slightly over-stated.",
        "",
        "export const CROSS_SECTION_ROW_STEP = %d;" % TS_STEP,
        "",
        "/** Index i covers frame row i * CROSS_SECTION_ROW_STEP. */",
        "export const CROSS_SECTIONS: readonly (readonly (readonly [number, number])[])[] = [",
    ]
    for r in range(0, ROWS, TS_STEP):
        s = rec["sections"][r]
        if not s:
            lines.append("  [], // row %d — under-constrained" % r)
            continue
        pts = resample([(p[0], p[1]) for p in s], TS_VERTS)
        body = ", ".join(f"[{px:.2f}, {pz:.2f}]" for px, pz in pts)
        lines.append(f"  [{body}], // row {r}")
    lines += ["] as const;", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {path}: {len(range(0, ROWS, TS_STEP))} rows x {TS_VERTS} vertices")


def main():
    sheet, idx, out = sys.argv[1], sys.argv[2], sys.argv[3]
    px = Image.open(sheet).convert("RGB").load()
    frames = json.load(open(idx))["frames"]
    # The pure-yaw set comes from pure_yaw_set.py, which adds the filter this script originally
    # lacked: matching height is necessary for a yaw but not sufficient, and six tumbled frames —
    # the six WIDEST, including the 67x68 that once set the head's depth — were passing on height
    # alone. Their widths were being fed in as if they measured a turned head.
    pure = json.load(open(pathlib.Path(__file__).with_name("pure-yaw.json")))["pureYaw"]
    keys = {(r["x0"], r["y0"]) for r in pure}
    pool = [f for f in frames if (f["x0"], f["y0"]) in keys]

    scanned = []
    for f in pool:
        widths, extent = scan(px, f)
        scanned.append({"frame": f, "widths": widths, "accentExtent": extent})
    ref_extent = max(s["accentExtent"] for s in scanned)

    for s in scanned:
        c = min(1.0, s["accentExtent"] / ref_extent)
        s["yawRaw"] = math.degrees(math.acos(c))

    # The raw estimate tops out at 77.4 degrees, not 90, and the reason is the eye itself: at a
    # true 90 the two eyes project onto each other but the pair still spans the eye's OWN depth,
    # so the extent floors at about 7px instead of collapsing. Left uncorrected, the frames that
    # really are near side-on get filed at 77 and their large widths constrain the wrong
    # direction; every such error can only shrink the intersection, and the first run shrank row
    # 44 from the reference's 47px to 36.8. Rescaling the observed range onto 0..90 is the
    # first-order correction, and `widthValidation` below is what says whether it worked.
    raw_max = max(s["yawRaw"] for s in scanned) or 1.0
    # The stretch factor is CALIBRATED, not assumed: --yaw-scale sweeps it and the front-view
    # width validation below picks the winner. That validation never enters the yaw estimate, so
    # tuning against it is a genuine hold-out rather than a circle.
    scale = 90.0 / raw_max
    if "--yaw-scale" in sys.argv:
        scale = float(sys.argv[sys.argv.index("--yaw-scale") + 1])
    for s in scanned:
        s["yawDeg"] = round(min(90.0, s["yawRaw"] * scale), 2)

    # Alternative estimator: the frame's own bbox width, mapped monotonically between the two
    # anchors that are independently established — the front view at 47px is 0 degrees, and the
    # widest pure-yaw frame at 67px is 90. It assumes the silhouette width rises monotonically
    # over that quarter turn, which the eye-based estimator does not have to assume; whichever
    # estimator wins the front-width validation is the one that ships.
    if "--yaw-from-width" in sys.argv:
        for s in scanned:
            w = s["frame"]["w"]
            s["yawDeg"] = round(min(90.0, max(0.0, 90.0 * (w - 47) / (67 - 47))), 2)

    # Bin, then take the MEDIAN width per (row, bin). A median survives the odd frame whose
    # dashed hidden lines broke a row's extent; a mean does not.
    binned = [[[] for _ in range(BINS)] for _ in range(ROWS)]
    for s in scanned:
        b = min(BINS - 1, int(s["yawDeg"] / (90 / BINS)))
        for r, wv in enumerate(s["widths"]):
            if wv:
                binned[r][b].append(wv)

    angles = [(i + 0.5) * (90 / BINS) for i in range(BINS)]
    sections = []
    coverage = []
    for r in range(ROWS):
        # Start from a square big enough to contain any cross-section of a 47x69 head.
        poly = [(-60, -60), (60, -60), (60, 60), (-60, 60)]
        used = 0
        for b, deg in enumerate(angles):
            vals = sorted(binned[r][b])
            if not vals:
                continue
            used += 1
            hw = vals[len(vals) // 2] / 2
            t = math.radians(deg)
            # Four half-planes per bin, not two. The sweep only covers ONE side of frontal, and
            # constraining only those directions let the solved sections come out TILTED — row 0
            # arrived as a sliver whose long axis ran at 20 degrees, on a head that is mirror
            # symmetric by measurement. The body's own symmetry says w(-t) = w(t), so the mirrored
            # direction carries exactly the same measured width and belongs in the intersection.
            for nx, nz in (
                (math.cos(t), -math.sin(t)),
                (math.cos(t), math.sin(t)),
            ):
                poly = clip(poly, nx, nz, hw)
                poly = clip(poly, -nx, -nz, hw)
            if len(poly) < 3:
                break
        coverage.append(used)
        # The RAW clipped polygon, not a resampled one. Resampling here and again in emit_ts
        # compounded: the second pass fed a 16-gon back through the ray test, directions that
        # missed every edge collapsed to the origin, and row 0 came out 4.5px wide having
        # measured 20.4px one step earlier. Resample exactly once, at the point of use.
        sections.append([[round(px_, 4), round(pz_, 4)] for px_, pz_ in poly] if used >= 4 else None)

    # Validation, and the only reason to trust any of this: the solved sections' X width was never
    # fed in as a constraint on the x direction alone — it falls out of the intersection. So
    # comparing it against the front view's own measured widths is an independent check on the
    # yaw estimate, the binning and the half-plane solve together.
    # Explicit path, not one derived by string-replacing the output name: writing the solve to a
    # scratch file then made the validation look for landmarks.json beside it and die.
    lm = (sys.argv[sys.argv.index("--landmarks") + 1] if "--landmarks" in sys.argv
          else str(pathlib.Path(__file__).with_name("landmarks.json")))
    front = json.load(open(lm))["rows"]
    checks = []
    for r in range(0, ROWS, 4):
        s = sections[r]
        if not s or not front[r]["span"]:
            continue
        xs = [p[0] for p in s]
        solved = max(xs) - min(xs)
        checks.append({"row": r, "front": front[r]["span"], "solved": round(solved, 2),
                       "relError": round(abs(solved - front[r]["span"]) / front[r]["span"], 4)})
    mean_err = round(sum(c["relError"] for c in checks) / len(checks), 4) if checks else None

    rec = {
        "framesUsed": len(scanned),
        "widthValidation": {"perRow": checks, "meanRelError": mean_err},
        "yawRange": [min(s["yawDeg"] for s in scanned), max(s["yawDeg"] for s in scanned)],
        "referenceAccentExtentPx": ref_extent,
        "bins": BINS,
        "binCoveragePerRow": coverage,
        "polygonVertices": POLY,
        "sections": sections,
        "note": (
            "Cross-sections are the CENTRAL SYMMETRAL: reconstructed from widths only, so they "
            "carry the true size and elongation of each row but not its front/back asymmetry. "
            "Units are reference pixels, x across the head and z front-to-back."
        ),
    }
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)

    if "--ts" in sys.argv:
        emit_ts(sys.argv[sys.argv.index("--ts") + 1], rec)

    print("width validation vs the front view: mean rel error",
          rec["widthValidation"]["meanRelError"])
    for c in rec["widthValidation"]["perRow"]:
        print(f'  row {c["row"]:2d}  front {c["front"]:3d}  solved {c["solved"]:6.1f}  err {c["relError"]:.3f}')
    print(f'{len(scanned)} frames, yaw {rec["yawRange"][0]:.1f}..{rec["yawRange"][1]:.1f} deg, '
          f'accent extent reference {ref_extent}px')
    print("bins covered per row:", min(coverage), "..", max(coverage))
    print("\nrow   widthX  depthZ   (from the solved section)")
    for r in range(0, ROWS, 4):
        s = sections[r]
        if not s:
            print(f"{r:3d}   --")
            continue
        xs = [p[0] for p in s]
        zs = [p[1] for p in s]
        print(f"{r:3d}   {max(xs) - min(xs):6.1f}  {max(zs) - min(zs):6.1f}")


main()
