#!/usr/bin/env python3
"""spec/section.py — the unified section-measuring helper.

The single rule, in one line:

  "Can this band hold something that is not the part, on this row?
   If yes take the run; if no take the span."

Three primitives each measure_*.py needs:

  - band_span  — band IS the part on this row (chest on chest rows, belt on belt
                 rows, pelvis on pelvis rows).  Covers fragmentation when an
                 overlay splits the part: the wrist straps, the belt buckle edges.

  - outer_run  — band has multiple things on this row, so select the run by
                 POSITION on the figure's side.  Used for the arm chain — the
                 skin band has the face at this row too, and the figure's RIGHT
                 deltoid is the IMAGE-RIGHT run in front.webp.

  - axis_run   — band has multiple things on this row, and the part is the one
                 that crosses the figure's centre axis.  Used for the neck, where
                 head, beard and forearms are all skin and the neck is whichever
                 run contains the vertical axis.

The four orthographic views are decoded positionally by front.webp's convention
(§1.2): figure's LEFT is IMAGE-RIGHT in front, IMAGE-LEFT in back; profile views
do not flip.

Everything is in pure stdlib + Pillow.  measure_landmarks.py and refmask.py are
the only sibling imports.
"""
from __future__ import annotations

from typing import Literal

import measure_landmarks as ML
import refmask as R


# --------------------------------------------------------------------- bands ---
BAND_KEYS = ("skin", "hair", "purple", "olive", "black", "grey")


def band_signature(v: R.View, row: int) -> dict:
    """Inventory of every band's runs on this row, for the caller to assert against.

    A `band_span` that comes back into a row with an unexpected neighbour should
    surprise the gate.  The caller can compare `signature["bands_present"]` to
    the bands it expected and fail loudly if a part-measurement silently used the
    row's full silhouette when only its own band was the part.
    """
    out: dict = {"row": row, "bands_present": [], "runs_per_band": {}}
    bands = R.band_map(v)
    for b in BAND_KEYS:
        runs = ML.real_runs(v, row, bands[b])
        if runs:
            out["bands_present"].append(b)
            out["runs_per_band"][b] = runs
    return out


# ------------------------------------------------------------------- the rule ---
def _span(runs: list[tuple[int, int]]) -> float:
    """First run start to last run end.  The PART'S extent when its band IS the part."""
    return float(runs[-1][1] - runs[0][0] + 1) if runs else 0.0


def _run_width(run: tuple[int, int]) -> float:
    return float(run[1] - run[0] + 1)


# ------------------------------------------------------------ the three modes ---
def band_span(
    v: R.View,
    row: int,
    band: str,
    *,
    silhouette_substitute: bool = False,
    min_run_frac: float = 0.20,
) -> tuple[float, list[tuple[int, int]]]:
    """The band's full SPAN on the row.

    Use when the band IS the part on this row — the belt on belt rows (only olive),
    the chest on chest rows (the straps are GAPS to span across), the pelvis on
    pelvis rows (only purple at that height).  Belt rows pass because the only
    other olive thing is the boots 0.36 figure-heights below.

    silhouette_substitute=True expands each band run to the silhouette run that
    COVERS it, so the section takes the visible chunk of the part rather than
    the visible chunk of the colour.  Use this when the band leaves an anti-aliased
    edge but the part's true silhouette is what you want — relevant where the
    band gives you the part minus one column of pixels at each side.
    """
    runs = ML.real_runs(v, row, R.band_map(v)[band], frac=min_run_frac)
    if not runs:
        return 0.0, runs
    if silhouette_substitute:
        sil_runs = v.row_runs(row)
        # For each band run, find the silhouette run that contains its centre.
        expanded: list[tuple[int, int]] = []
        for br in runs:
            centre = (br[0] + br[1]) // 2
            for sr in sil_runs:
                if sr[0] <= centre <= sr[1]:
                    expanded.append(sr)
                    break
            else:
                expanded.append(br)
        runs = expanded
    return _span(runs), runs


def outer_run(
    v: R.View,
    row: int,
    band: str,
    *,
    side: Literal["L", "R"],
) -> tuple[float, tuple[int, int] | None]:
    """The band run for THIS ARM at this row, picked by figure's side.

    `side` is the figure's own side, not the image's.  Caller decodes it from
    the view name: front.webp puts figure-left on IMAGE-RIGHT, back.webp flips.
    §1.3 of the prompt has the table.

    A two-pixel speck of skin out by the glove is never an arm, so we drop
    anything narrower than a fifth of the widest (per measure_arm.arm_runs).
    """
    runs = ML.real_runs(v, row, R.band_map(v)[band])
    if not runs:
        return 0.0, None
    widest = max(r[1] - r[0] + 1 for r in runs)
    real = [r for r in runs if (r[1] - r[0] + 1) >= widest / 5]
    if not real:
        return 0.0, None

    image_right_is_figure_left = v.name in ("front", "right")
    want_rightmost = (side == "L" and image_right_is_figure_left) or (
        side == "R" and not image_right_is_figure_left
    )
    pick = real[-1] if want_rightmost else real[0]
    return _run_width(pick), pick


def axis_run(
    v: R.View,
    row: int,
    band: str,
) -> tuple[float, tuple[int, int] | None]:
    """The band run that crosses the figure's centre axis at this row.

    Use for the neck: skin makes the face, the deltoids, the wrists, AND the neck
    on a single row at the chin, and the neck is the run containing the
    figure's vertical axis.
    """
    runs = ML.real_runs(v, row, R.band_map(v)[band])
    if not runs:
        return 0.0, None
    # The figure's centre axis is the mean of the figure's leftmost and rightmost
    # column, the same axis landmarks.json uses for the cluster position signature.
    extent = v.row_extent(row)
    if extent is None:
        return 0.0, None
    axis = (extent[0] + extent[1]) / 2.0
    # Pick the run whose centre is closest to the axis.
    best = min(runs, key=lambda r: abs((r[0] + r[1]) / 2.0 - axis))
    return _run_width(best), best


# ------------------------------------------------------ normalized convenience ---
def at_height(
    v: R.View,
    height_normalized: float,
    *,
    unit_px_per_unit: float,
    sole_row_px: int,
) -> int:
    """Row corresponding to a normalized height, in pixels.

    Centralised so a height helper never gets its direction wrong.  Y up: ground
    at the bottom row, sole on the highest polar row, chin above the sole.
    height=0 → sole row; height=1 → top of the figure.
    """
    return int(round(sole_row_px - height_normalized * unit_px_per_unit))


def width_in_units(
    v: R.View,
    width_px: float,
    *,
    unit_px_per_unit: float,
) -> float:
    """Convert a pixel width to normalized units, by the SAME per-view unit."""
    return width_px / unit_px_per_unit
