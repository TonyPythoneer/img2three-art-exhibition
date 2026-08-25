#!/usr/bin/env python3
"""P0 reference triage for the Sigma wireframe sheet (AGENTS.md P0, sheet-adapted).

The sheet is a dark navy (#000029) capture with wireframe sprites of all hues, so
the AGENTS.md whitenness test inverts to a darkness test:
    fg[i]   = max channel deviates from the measured background
    reach   = flood fill from the component bounds OUTWARD through not-fg
    figure  = fg AND not reachable               (enclosed holes are not figure)

Per figure: silhouette envelope (per-row / per-col extents), clipping flags
(entire silhouette flush with the bounds = the sprite was cut), scale, palette
family, stroke/figure pixel counts, and row-centre asymmetry.

Output: spec/p0-triage.json
"""
from __future__ import annotations

import collections
import json
import pathlib

import sys
import collections as _c


def hue_family(pixel: tuple[int, int, int]) -> str:
    r, g, b = pixel
    # Resolve against the sheet's measured palette families first.
    if abs(r - 16) < 12 and abs(g - 216) < 12 and abs(b - 48) < 12:
        return "green-bright"
    if abs(r - 16) < 12 and abs(g - 176) < 12 and abs(b - 16) < 12:
        return "green-dim"
    if abs(r - 224) < 12 and abs(g - 80) < 12 and abs(b) < 12:
        return "eye"
    if g > r + 40 and g > b + 40:
        return "green"
    if b > r + 40 and b > g + 20:
        return "blue"
    if r > g + 40 and b > g + 40:
        return "purple"
    if r > g + 40 and r > b + 40:
        return "orange" if g > 60 else "red"
    return "other"


def main() -> None:
    import pathlib

    from PIL import Image

    exhibit = pathlib.Path(__file__).resolve().parents[1]
    im = Image.open(exhibit / "references" / "sigma-wireframe-sheet.png").convert("RGB")
    w, h = im.size
    px = im.load()

    colour = collections.Counter(px[x, y] for y in range(h) for x in range(w))
    bg = colour.most_common(1)[0][0]

    def is_fg(p):
        return not all(abs(a - b) <= 8 for a, b in zip(p, bg))

    fg = [[is_fg(px[x, y]) for x in range(w)] for y in range(h)]

    # Connected components, 2-px bridge so antialiased wire crossings stay one sprite.
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if seen[y][x] or not fg[y][x]:
                continue
            stack = [(x, y)]
            seen[y][x] = True
            pts = []
            while stack:
                cx, cy = stack.pop()
                pts.append((cx, cy))
                for dy in (-2, -1, 0, 1, 2):
                    for dx in (-2, -1, 0, 1, 2):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and fg[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
            if len(pts) >= 20:
                comps.append(pts)

    records = []
    for i, pts in enumerate(comps):
        x0 = min(x for x, _ in pts)
        y0 = min(y for _, y in pts)
        x1 = max(x for x, _ in pts)
        y1 = max(y for _, y in pts)
        fw, fh = x1 - x0 + 1, y1 - y0 + 1

        # Flood fill from the four borders of the figure bounds through not-fg.
        reach = [[False] * fw for _ in range(fh)]
        stack = []
        for x in range(fw):
            for y in (0, fh - 1):
                if not reach[y][x] and not fg[y0 + y][x0 + x]:
                    stack.append((x, y))
            reach[y][x] = True
        for y in range(fh):
            for x in (0, fw - 1):
                if not reach[y][x] and not fg[y0 + y][x0 + x]:
                    stack.append((x, y))
            reach[y][x] = True
        while stack:
            cx, cy = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < fw and 0 <= ny < fh and not reach[ny][nx] and not fg[y0 + ny][x0 + nx]:
                        reach[ny][nx] = True
                        stack.append((nx, ny))

        figure = [
            (x, y)
            for y in range(fh)
            for x in range(fw)
            if fg[y0 + y][x0 + x] and not reach[y][x]
        ]
        rows = collections.defaultdict(list)
        cols = collections.defaultdict(list)
        for x, y in figure:
            rows[y].append(x)
            cols[x].append(y)

        row_envelope = [[r, min(rows[r]), max(rows[r])] for r in sorted(rows)]
        col_envelope = [[c, min(cols[c]), max(cols[c])] for c in sorted(cols)]

        touches = {
            "top": any(x for x, y in figure if y == 0),
            "bottom": any(x for x, y in figure if y == fh - 1),
            "left": any(y for x, y in figure if x == 0),
            "right": any(y for x, y in figure if x == fw - 1),
        }

        fam = collections.Counter(
            hue_family(px[x0 + x, y0 + y]) for x, y in figure
        )
        rows_occ = sorted(rows)
        asym = 0.0
        if rows_occ:
            asym = (
                min(
                    abs(((min(rows[r]) + max(rows[r])) / 2) - (fw - 1) / 2)
                    for r in rows_occ
                )
                / max(1, fw)
            )

        records.append(
            {
                "id": i,
                "bbox": [x0, y0, x1, y1],
                "w": fw,
                "h": fh,
                "aspect": round(fw / fh, 4) if fh else None,
                "fgPx": sum(1 for p in pts if fg[p[1]][p[0]]),
                "figurePx": len(figure),
                "strokePx": len({(x, y) for x, y in figure}),
                "rowEnvelope": row_envelope,
                "colEnvelope": col_envelope,
                "rowWidths": [max(rows[r]) - min(rows[r]) + 1 for r in rows_occ],
                "colHeights": [max(cols[c]) - min(cols[c]) + 1 for c in sorted(cols)],
                "clipped": touches,
                "touchesCount": sum(touches.values()),
                "families": dict(fam.most_common()),
                "rowCentreAsymmetry": round(asym, 5),
            }
        )

    out = {
        "source": "references/sigma-wireframe-sheet.png",
        "bg": list(bg),
        "componentCount": len(comps),
        "records": records,
    }
    o = exhibit / "spec" / "p0-triage.json"
    o.write_text(json.dumps(out, indent=2))

    big = [r for r in records if r["h"] >= 62]
    frag = [r for r in records if r["h"] < 62]
    clipped = [r for r in records if r["touchCount" if "touchCount" in r else "touchesCount"]]
    print(
        f"components>={20}px: {len(records)}  full-scale(h>=62): {len(big)}  "
        f"small: {len(frag)}  clipped: {len(clipped)}"
    )
    for r in records:
        if r["touchesCount"] or r["w"] * r["h"] > 90 * 85:
            print(
                f"  id={r['id']} bbox={r['bbox']} {r['w']}x{r['h']} fig={r['figurePx']} "
                f"touch={[k for k, v in r['clipped'].items() if v]} fam={r['families']}"
            )


if __name__ == "__main__":
    main()
