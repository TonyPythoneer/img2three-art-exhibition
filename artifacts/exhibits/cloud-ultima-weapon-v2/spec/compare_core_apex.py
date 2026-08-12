#!/usr/bin/env python3
"""Blueprint beside render, same weapon-local window, same magnification.

`measure_core_apex.py` says where the artwork's dark wedge stops. This puts that claim next to
what was built, so the number can be checked by eye instead of only by gate.

The renders are ORTHOGRAPHIC and upright, so mapping render pixels to weapon-local units needs
exactly two landmarks and no camera maths: the blade tip is `Y = 760` and the pommel tip is
`Y = -210.7`, they are the silhouette's topmost and bottommost rows, and the model is symmetric
about its own bbox centre in X. Uniform scale, so the same factor serves both axes.

    python3 spec/compare_core_apex.py <render.png> [<render.png> …] [-o out.png]

Each render becomes one panel beside the artwork's own panel, all resampled NEAREST to the same
window and the same output height. Writes spec/zoom-relief/core-apex-compare.png by default.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from measure_core_apex import CP, AP, INV, IW, IH, PX_PER_UNIT  # noqa: E402

# The window the argument is about: the blade root and the whole of the wedge above it.
X0, X1, Y0, Y1 = -70.0, 70.0, -20.0, 300.0
MAG = 8  # output pixels per SOURCE pixel of the 210x434 crop
TIP_Y, POMMEL_Y = 760.0, -210.7


def artwork_panel(upu: float) -> Image.Image:
    w, h = int(round((X1 - X0) * upu)), int(round((Y1 - Y0) * upu))
    img = Image.new("RGB", (w, h), (255, 255, 255))
    ip = img.load()
    for oy in range(h):
        ly = Y1 - (oy + 0.5) / upu
        for ox in range(w):
            px, py = INV(X0 + (ox + 0.5) / upu, ly)
            ix, iy = int(round(px)), int(round(py))
            if 0 <= ix < IW and 0 <= iy < IH and AP[ix, iy][3] > 96:
                ip[ox, oy] = CP[ix, iy]
    return img


def render_panel(path: Path, upu: float) -> Image.Image:
    src = Image.open(path).convert("RGB")
    sp = src.load()
    sw, sh = src.size
    rows = [y for y in range(sh) for x in range(sw) if min(sp[x, y]) < 244]
    cols = [x for y in range(sh) for x in range(sw) if min(sp[x, y]) < 244]
    top, bottom = min(rows), max(rows)
    cx = (min(cols) + max(cols)) / 2
    # px per normalized unit in the render, from the two landmarks that bracket the whole model
    ppu = (bottom - top) / (TIP_Y - POMMEL_Y)

    w, h = int(round((X1 - X0) * upu)), int(round((Y1 - Y0) * upu))
    img = Image.new("RGB", (w, h), (255, 255, 255))
    ip = img.load()
    for oy in range(h):
        ly = Y1 - (oy + 0.5) / upu
        sy = int(round(top + (TIP_Y - ly) * ppu))
        for ox in range(w):
            lx = X0 + (ox + 0.5) / upu
            sx = int(round(cx + lx * ppu))
            if 0 <= sx < sw and 0 <= sy < sh:
                ip[ox, oy] = sp[sx, sy]
    return img


def main() -> None:
    argv = sys.argv[1:]
    out = HERE / "zoom-relief" / "core-apex-compare.png"
    if "-o" in argv:
        i = argv.index("-o")
        out = Path(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    labels = ["artwork 8x NEAREST"] + [Path(a).parent.name + "/" + Path(a).name for a in argv]

    upu = MAG * PX_PER_UNIT
    panels = [artwork_panel(upu)] + [render_panel(Path(a), upu) for a in argv]

    pad, top_bar = 8, 18
    w = sum(p.width for p in panels) + pad * (len(panels) + 1)
    h = panels[0].height + top_bar + pad * 2
    sheet = Image.new("RGB", (w, h), (250, 250, 250))
    d = ImageDraw.Draw(sheet)
    x = pad
    for panel, label in zip(panels, labels):
        sheet.paste(panel, (x, top_bar + pad))
        d.text((x + 2, 4), label, fill=(30, 30, 30))
        # the two heights the argument turns on
        for y, colour in ((187.0, (255, 0, 255)), (118.0, (0, 160, 255))):
            oy = top_bar + pad + int(round((Y1 - y) * upu))
            d.line([(x, oy), (x + panel.width, oy)], fill=colour)
            d.text((x + panel.width - 26, oy + 1), str(int(y)), fill=colour)
        x += panel.width + pad
    sheet.save(out)
    print(f"wrote {out} {sheet.size[0]}x{sheet.size[1]}  "
          f"(magenta = CORE_APEX_Y 187, blue = the retired 118)")


if __name__ == "__main__":
    main()
