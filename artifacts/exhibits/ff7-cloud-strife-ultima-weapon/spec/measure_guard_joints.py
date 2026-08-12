#!/usr/bin/env python3
"""Where the connector arms meet the shell, measured off the crop instead of assumed.

Correction C of 2026-08-08 says the arms are plugged into `outerCrystalShell`'s LOWER SLANTED
EDGE, and asks whether that edge and the arm are consistent with each other against the artwork.
Both halves are read here, in `measure_authority.py`'s own weapon-local frame.

**The joint is one boundary, not two.** Between the guard's dark mass and the arm there is a pale
WEDGE — on the right it runs x = 30…76 at Y = 40 and narrows to 33…35 at Y = 4 — and its outer
boundary is at once the shell's own slanted edge and the arm's inner silhouette edge. So both are
taken from the SAME row scan, and "the arm's inner edge is the shell's edge" is a measurement of
one line rather than of two that happen to agree. Walked outward from the axis rather than inward
from outside: the crop carries a white halo the alpha mask does not cut away, and an outside-in
scan reads that halo as a 131-unit half-width.

Two things this deliberately does NOT report:

  * **the arm's rake.** The crop's two arms fit rakes 20 degrees apart — the left is crossed by two
    rods over most of its length — so it is not a number this single view can give.
  * **the root cap's own footprint on the edge.** It would need the ramp where the arm's section
    grows from its raked tip to full, and above Y = 22 the driver rods cross the same flank in the
    same colour families. Every cut of that run puts the tip somewhere between Y = 5 and Y = 44.
    Recorded as unreadable at 8x rather than fitted anyway; see the zooms this writes.

What is left needs neither: the arm's FULL HORIZONTAL SECTION and the slanted edge's own line are
both read straight off the rows, and the build's two are recomputed from the factory in the same
horizontal cut, so the comparison is like for like.

    python3 src/exhibits/ff7-cloud-strife-ultima-weapon/spec/measure_guard_joints.py

Writes `spec/guard-joints.json`, four 8x NEAREST zooms and two artwork|render side-by-sides into
`spec/zoom-guard/`. Reads the artwork, the factory source and the front-orthographic capture.
"""

from __future__ import annotations

import json
import re
import math
from pathlib import Path

# The frame is built once, in measure_core_apex, and asserted there against measurements.json.
# Re-deriving it a third time is how two scripts end up measuring in two different coordinate
# systems, so it is imported.
from measure_core_apex import AP, CP, INV, IH, IW, PX_PER_UNIT, classify, zoom

HERE = Path(__file__).resolve().parent
V = HERE.parent
ROOT = V.parent.parent.parent

# --- where each feature is looked for -------------------------------------------------------
# The pale shell's lower flanks. The scan stops at the diamond's waist because above it the blade
# is the flat 81-83 band and below Y=6 the crop's own silhouette has ended (shell bbox minY 4.9).
SLANT_LO, SLANT_HI = 2.0, 44.0
# Where the slanted edge stops: the diamond's own waist, which is the height the whole hilt
# correction is anchored to. Read off the artwork's own gem blob (bbox Y = 9.1…98.8), not taken
# from the factory — this script answers to the crop and nothing else.
GEM_WAIST_Y_ART = 54.0
STEP = 0.25


def sil(lx: float, ly: float):
    """(family, V) at a weapon-local point, or None outside the silhouette."""
    px, py = INV(lx, ly)
    ix, iy = int(round(px)), int(round(py))
    if not (0 <= ix < IW and 0 <= iy < IH) or AP[ix, iy][3] <= 96:
        return None
    return classify(*CP[ix, iy])


def runs(sign: int, y: float) -> list[tuple[str | None, float, float]]:
    """The families crossed walking outward from the axis at height `y`, as (family, from, to)."""
    out: list[tuple[str | None, float, float]] = []
    x, prev, start = 0.0, sil(0.0, y), 0.0
    while x <= 160.0:
        f = sil(sign * x, y)
        if f != prev:
            out.append((prev, start, x))
            prev, start = f, x
        x += STEP
    out.append((prev, start, x))
    return out


# The pale WEDGE between the guard's dark mass and the connector arm. Its inner boundary sits at
# x ≈ 28–34 at every height in the band, so a run starting there is the wedge and a run starting
# at 60+ is the crop's own white halo, which the alpha mask does not cut away and which is what
# made a naive outside-in scan read a half-width of 131.
WEDGE_FROM, WEDGE_TO = 20.0, 46.0
DARK = {"steel", "grip", "gold"}


def slant_and_arm(sign: int, lo: float, hi: float):
    """Per row: where the pale wedge ends, and where the dark run outboard of it ends.

    The first is the shell's own lower slanted edge. The second is the connector arm's outer
    flank — the two are read from the SAME row scan on purpose, so "the arm's inner edge is the
    shell's edge" is a measurement of one boundary rather than of two that happen to agree.
    """
    rows = []
    y = lo
    while y <= hi:
        rs = runs(sign, y)
        wedge = next((r for r in rs
                      if r[0] == "shell" and WEDGE_FROM <= r[1] <= WEDGE_TO and r[2] - r[1] >= 1),
                     None)
        if wedge:
            dark = next((r for r in rs if r[0] in DARK and r[1] >= wedge[2] - STEP), None)
            rows.append((y, wedge[2], dark[2] if dark else None))
        y += 0.5
    return rows


def robust_fit(pts: list[tuple[float, float]]) -> tuple[dict, list[float]]:
    """`fit` with one 2.5-sigma rejection pass, returning the rejected rows as well.

    Needed rather than tidy: over Y = 22…30 a driver rod's specular highlight merges with the
    wedge and the pale run continues straight through the arm, so those rows report the blade's
    OUTER edge instead of the wedge's. Rejected rather than hard-coded out, so the same thing
    happening at another height is caught instead of assumed away.
    """
    f = fit(pts)
    resid = [abs(w - (f["intercept"] + f["slope"] * y)) for y, w in pts]
    cut = 2.5 * (sum(r * r for r in resid) / len(resid)) ** 0.5
    keep = [p for p, r in zip(pts, resid) if r <= cut]
    dropped = [p[0] for p, r in zip(pts, resid) if r > cut]
    return (fit(keep) if len(keep) >= 8 else f), dropped


def fit(pts: list[tuple[float, float]]) -> dict:
    """Least squares halfWidth = a + b*Y over [(Y, halfWidth)], with its own RMS."""
    n = len(pts)
    my = sum(p[0] for p in pts) / n
    mw = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - my) ** 2 for p in pts)
    sxy = sum((p[0] - my) * (p[1] - mw) for p in pts)
    b = sxy / sxx
    a = mw - b * my
    rms = math.sqrt(sum((p[1] - (a + b * p[0])) ** 2 for p in pts) / n)
    return {"intercept": a, "slope": b, "rmsUnits": rms, "rows": n}


FAMILY_COLOUR = {"shell": (235, 235, 235), "insert": (90, 60, 230), "red": (220, 40, 40),
                 "gold": (225, 190, 60), "grip": (20, 20, 20), "steel": (120, 130, 140),
                 None: (255, 0, 255)}


def family_map(x0: float, x1: float, y0: float, y1: float, path: Path,
               mag: int = 8) -> tuple[str, tuple[int, int]]:
    """The crop repainted as `classify()` sees it, upright and gridded.

    The zoom beside it shows what the guard LOOKS like; this shows what every measurement in this
    exhibit is actually reading, and the two disagree in one way that matters. The classifier's
    `shell` family is `v >= 0.55, s <= 0.30`, which the crop's white halo satisfies as readily as
    the blade does, and the alpha mask does not cut the halo away — so a boundary that looks
    obvious in the photograph can be twenty units out in the data. Every claim in this file's
    docstring about where a run starts was read off this image first.
    """
    from PIL import Image, ImageDraw

    upu = mag * PX_PER_UNIT
    w, h = int(round((x1 - x0) * upu)), int(round((y1 - y0) * upu))
    img = Image.new("RGB", (w, h), FAMILY_COLOUR[None])
    ip = img.load()
    for oy in range(h):
        ly = y1 - (oy + 0.5) / upu
        for ox in range(w):
            ip[ox, oy] = FAMILY_COLOUR[sil(x0 + (ox + 0.5) / upu, ly)]
    d = ImageDraw.Draw(img)
    for y in range(int(math.ceil(y0 / 20)) * 20, int(y1) + 1, 20):
        oy = int(round((y1 - y) * upu))
        d.line([(0, oy), (w, oy)], fill=(255, 0, 255))
        d.text((3, oy + 2), str(y), fill=(255, 0, 255))
    for x in range(int(math.ceil(x0 / 20)) * 20, int(x1) + 1, 20):
        ox = int(round((x - x0) * upu))
        d.line([(ox, 0), (ox, h)], fill=(0, 190, 0))
        d.text((ox + 2, 2), str(x), fill=(0, 150, 0))
    img.save(path)
    return path.name, img.size


def render_frame(name: str = "front-orthographic"):
    """The front-orthographic capture and the map from weapon-local units into its pixels.

    The render's frame is read off the RENDER, not assumed: the front-orthographic capture is
    upright and orthographic, so its own silhouette's topmost and bottommost rows are the blade
    tip (Y = 760) and the pommel tip (Y = −210.7), and two landmarks plus the axis of symmetry fix
    the mapping. Framing margins are fixed per view in the look-dev rig and never fitted per
    render, so this stays valid across captures — which is the point of comparing at all.

    Exported because `measure_spinner_taper.py` reads per-row half-widths out of the SAME capture
    in the SAME units. A second copy of this eight-line mapping is how two scripts end up
    reporting the same feature at two different heights — the mistake the frame import at the top
    of this file exists to prevent, one file further along.
    """
    from PIL import Image

    render = Image.open(ROOT / f"artifacts/ultima-v2/full/{name}.png").convert("RGB")
    rp = render.load()
    rw, rh = render.size
    rows = [y for y in range(rh)
            if any(sum(rp[x, y]) < 720 for x in range(0, rw, 2))]
    top, bottom = min(rows), max(rows)
    scale = (760.0 - (-210.7)) / (bottom - top)  # normalized units per render pixel
    ry0 = top + 760.0 / scale  # image row of Y = 0

    def render_px(lx: float, ly: float) -> tuple[int, int]:
        return (int(round(rw / 2 + lx / scale)), int(round(ry0 - ly / scale)))

    return render, rp, rw, rh, render_px, scale


def side_by_side(x0: float, x1: float, y0: float, y1: float, path: Path,
                 mag: int = 8) -> tuple[str, tuple[int, int]]:
    """Artwork | render over the same weapon-local window, both NEAREST, both gridded."""
    from PIL import Image, ImageDraw

    _render, rp, rw, rh, render_px, _scale = render_frame()

    upu = mag * PX_PER_UNIT
    w, h = int(round((x1 - x0) * upu)), int(round((y1 - y0) * upu))
    sheet = Image.new("RGB", (w * 2 + 12, h), (255, 255, 255))
    for panel in (0, 1):
        tile = Image.new("RGB", (w, h), (255, 255, 255))
        tp = tile.load()
        for oy in range(h):
            ly = y1 - (oy + 0.5) / upu
            for ox in range(w):
                lx = x0 + (ox + 0.5) / upu
                if panel == 0:
                    px, py = INV(lx, ly)
                    ix, iy = int(round(px)), int(round(py))
                    if 0 <= ix < IW and 0 <= iy < IH and AP[ix, iy][3] > 96:
                        tp[ox, oy] = CP[ix, iy]
                else:
                    ix, iy = render_px(lx, ly)
                    if 0 <= ix < rw and 0 <= iy < rh:
                        tp[ox, oy] = rp[ix, iy]
        d = ImageDraw.Draw(tile)
        for y in range(int(math.ceil(y0 / 20)) * 20, int(y1) + 1, 20):
            oy = int(round((y1 - y) * upu))
            d.line([(0, oy), (w, oy)], fill=(255, 0, 255))
            d.text((3, oy + 2), str(y), fill=(255, 0, 255))
        for x in range(int(math.ceil(x0 / 20)) * 20, int(x1) + 1, 20):
            ox = int(round((x - x0) * upu))
            d.line([(ox, 0), (ox, h)], fill=(0, 190, 0))
            d.text((ox + 2, 2), str(x), fill=(0, 150, 0))
        sheet.paste(tile, (panel * (w + 12), 0))
    sheet.save(path)
    return path.name, sheet.size


def main() -> None:
    out: dict = {"unitsPerSourcePixel": round(1 / PX_PER_UNIT, 4)}

    px = 1 / PX_PER_UNIT
    print(f"one source pixel = {px:.2f} normalized units")

    for side, sign in (("right", 1), ("left", -1)):
        rows = slant_and_arm(sign, SLANT_LO, SLANT_HI)
        if len(rows) < 12:
            out.setdefault("unreadable", []).append(
                f"{side}: only {len(rows)} rows carry a readable pale wedge between the guard and "
                "the arm at 8x NEAREST; the joint cannot be measured on this side"
            )
            print(f"\n{side}: UNREADABLE at 8x — {len(rows)} usable rows "
                  f"(see zoom-guard/arm-root-{side}-8x-grid.png)")
            continue

        slant, dropped = robust_fit([(y, w) for y, w, _ in rows])
        y_lo = min(y for y, _, _ in rows)
        y_hi = GEM_WAIST_Y_ART
        edge_len = math.hypot(y_hi - y_lo, slant["slope"] * (y_hi - y_lo))

        # The arm's ROOT CAP, read as the band over which its horizontal section grows from
        # nothing to full. The arm is at full section at the bottom of the wedge and tapers to its
        # inner tip going up, because the cap is raked; where that ramp starts and ends IS the
        # cap's footprint on the slanted edge. Measured as a SPAN rather than through a fitted
        # rake on purpose: the crop's two arms fit rakes 20 degrees apart (the left one is crossed
        # by two rods over most of its length), so a rake is not a number this crop can give, and
        # the span does not need one.
        widths = {y: o - w for y, w, o in rows if o is not None}
        if len(widths) < 8:
            out.setdefault("unreadable", []).append(f"{side}: the arm's outer flank is not "
                                                    "separable from the rods at 8x")
            print(f"\n{side}: arm flank UNREADABLE at 8x")
            continue
        # Walked upward from the bottom while the section keeps SHRINKING, and stopped at the
        # first row where it grows again. Above the cap's inner tip the same scan starts reading
        # a driver rod crossing the blade's flank instead — on the right that happens at Y = 24,
        # where the pale run merges with a rod's specular highlight — and a plain threshold would
        # take those rows for more cap and put its tip 23 units too high.
        # The arm is at FULL section at the bottom of the wedge and tapers upward to its raked
        # cap's inner tip. The full section reads cleanly; the ramp does not, and that is recorded
        # rather than fitted anyway. **At 8x NEAREST the cap's ramp cannot be separated from the
        # driver rods** (`zoom-guard/arm-root-{side}-8x-grid.png`): the rods cross the blade's own
        # flank over Y = 22…44 and their dark shadowed sides fall into the same families as the
        # arm, so the row scan reads a second dark run outboard of the wedge and cannot tell which
        # limb it belongs to. Every tip estimate the ramp supports therefore lands somewhere
        # between Y = 5 and Y = 44 depending on how the run is cut, which is not a measurement.
        # So the arm's own SECTION is what this reports, and the model's is compared to it in the
        # same horizontal cut, needing no rake from either side.
        full = widths[min(widths)]
        out.setdefault("sides", {})[side] = {
            "slantHalfWidth": {"intercept": slant["intercept"], "slope": slant["slope"],
                               "rmsUnits": slant["rmsUnits"], "rows": slant["rows"],
                               "rowsRejected": dropped},
            "slantSpanY": [y_lo, y_hi],
            "slantEdgeLength": edge_len,
            "armHorizontalWidthAtFullSection": full,
            "rootCapRamp": "unreadable at 8x — the driver rods cross the same flank over "
                           "Y = 22…44 and share the arm's colour families",
        }
        print(f"\nSHELL lower slant, {side}: halfWidth = {slant['intercept']:.2f} "
              f"{slant['slope']:+.4f} Y   RMS {slant['rmsUnits']:.2f} u = "
              f"{slant['rmsUnits'] / px:.2f} px over {slant['rows']} rows "
              f"({len(dropped)} rejected)")
        print(f"      the edge runs Y = {y_lo:.1f} … {y_hi:.0f}, {edge_len:.1f} units long")
        print(f"ARM   {side}: full horizontal section {full:.1f} units ({full / px:.1f} px). "
              "Its root cap's ramp is UNREADABLE at 8x — the rods cross the same flank.")

    # --- what the build does with the same two quantities -----------------------------------
    # Read out of the factory rather than restated, so the comparison cannot drift from the model.
    src = (V / "createUltimaWeaponV2Model.ts").read_text()

    def _c(p):
        return float(re.search(p, src, re.M).group(1))

    def _block_src(text: str, name: str) -> str:
        return re.search(rf"const {name}[^=]*= \[(.*?)\n\];", text, re.S).group(1)
    # The VISIBLE slanted edge, which is the segment the crop can see: from the jaws' floor, which
    # is also where the taper now STOPS, up to the diamond's waist. There is no tenon below it any
    # more (integration #15), so the visible segment and the whole lower taper are the same line.
    #
    # Its lower end is read out of CLAMP_OUTLINE rather than out of SHELL_STATIONS, because the
    # factory writes that row as the two constants the outline derives and this file's numeric-row
    # regex deliberately does not match it — the same contract `audit_records.py` is held to.
    rows_src = re.findall(r"^\s*\[(-?[\d.]+), (-?[\d.]+), ", _block_src(src, "SHELL_STATIONS"),
                          re.M)
    table = {float(y): float(w) for y, w in rows_src}
    _outline = [(float(a), float(b)) for a, b in
                re.findall(r"\[(-?[\d.]+), (-?[\d.]+)\]", _block_src(src, "CLAMP_OUTLINE"))]
    table[_outline[2][1]] = _outline[2][0] - _outline[1][0]
    lo_y, hi_y = _outline[2][1], 55.0
    slope = (table[hi_y] - table[lo_y]) / (hi_y - lo_y)
    radius = _c(r"^const CONNECTOR_RADIUS = (-?[\d.]+)")
    rake = _c(r"^const CONNECTOR_ANGLE_DEG = (-?[\d.]+)")
    built = {
        "slantHalfWidth": {"intercept": table[lo_y] - slope * lo_y, "slope": slope},
        "slantSpanY": [lo_y, hi_y],
        "slantEdgeLength": math.hypot(hi_y - lo_y, table[hi_y] - table[lo_y]),
        "armHorizontalWidthAtFullSection": 2 * radius / abs(math.sin(math.radians(rake))),
    }
    built["footprintShareOfEdge"] = (
        built["armHorizontalWidthAtFullSection"] * abs(math.sin(math.radians(rake)))
        / built["slantEdgeLength"])
    out["built"] = built
    print(f"\nBUILT slant halfWidth = {built['slantHalfWidth']['intercept']:.2f} "
          f"{built['slantHalfWidth']['slope']:+.4f} Y over an edge "
          f"{built['slantEdgeLength']:.1f} units long")
    print(f"BUILT arm's full horizontal section {built['armHorizontalWidthAtFullSection']:.1f} "
          f"units; its cap takes {100 * built['footprintShareOfEdge']:.1f}% of that edge")
    if "sides" in out and "right" in out["sides"]:
        art = out["sides"]["right"]
        ds = 100 * abs(built["slantHalfWidth"]["slope"]
                       / art["slantHalfWidth"]["slope"] - 1)
        da = 100 * abs(built["armHorizontalWidthAtFullSection"]
                       / art["armHorizontalWidthAtFullSection"] - 1)
        print(f"C     the build's slanted edge has the crop's own slope to {ds:.1f}%; the arm "
              f"plugged into it is {da:.0f}% wider in the same cut than the crop's")

    (HERE / "guard-joints.json").write_text(json.dumps(out, indent=2))

    zooms = (
        (-130, 130, -30, 130, 8, "guard-slant-8x-grid.png", 20, 20),
        (0, 100, -30, 70, 8, "arm-root-right-8x-grid.png", 10, 10),
        (-100, 0, -30, 70, 8, "arm-root-left-8x-grid.png", 10, 10),
        (-45, 45, -30, 70, 8, "socket-under-gem-8x-grid.png", 10, 10),
    )
    print()
    for x0, x1, y0, y1, mag, name, gx, gy in zooms:
        nm, size = zoom(x0, x1, y0, y1, mag, HERE / "zoom-guard" / name, gx, gy)
        print(f"wrote zoom-guard/{nm} {size[0]}x{size[1]}")

    nm, size = family_map(-140, 140, -40, 140, HERE / "zoom-guard" / "family-map-8x-grid.png")
    print(f"wrote zoom-guard/{nm} {size[0]}x{size[1]}")

    # The arm's OUTER end, added 2026-08-12 with the directive that put `CONNECTOR_LENGTH` back at
    # 72. The two windows above are both framed on the arm's ROOT, which is exactly the end the
    # length does not move, so neither of them could show what the directive changed: where the
    # end cap stops and where the crop's gold spinner cap emerges from under the leather. This one
    # runs down to Y = -110 so the whole spinner is in frame on both sides.
    for window, name in (((-130, 130, -30, 130), "compare-guard-region-8x.png"),
                         ((-10, 110, -40, 80), "compare-arm-root-right-8x.png"),
                         ((40, 140, -110, 10), "compare-arm-end-right-8x.png")):
        out = side_by_side(*window, HERE / "zoom-guard" / name)
        print(f"wrote zoom-guard/{out[0]} {out[1][0]}x{out[1][1]}")
    print("wrote spec/guard-joints.json")


if __name__ == "__main__":
    main()
