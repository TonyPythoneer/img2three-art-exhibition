#!/usr/bin/env python3
"""What value the pale shell actually renders at, against what the artwork measures.

`outerCrystalShell` is the largest thing in the frame and its level has been wrong twice, both
times for a reason in the RENDER PATH rather than in the palette: `transmission` handing a
quarter of the diffuse to a rig that returns nothing, then `transparent`/`opacity` and
`DoubleSide` fighting over the same pixel. Both were found by measuring, and both were argued
about first — so the measurement gets a producer of its own instead of living in a comment.

**The mask is the same test on both pictures, and it is a colour census, not a footprint.**
Near-neutral (max-min <= 20), clearly not the background (max < 250) and clearly not the dark
steel or leather (min >= 170). Nothing else in either frame is pale AND neutral: the clamp metal
means 150 and falls under the floor, the gold and the two crystals fail the chroma test, and the
white background fails the ceiling. Applied to the 210x434 artwork crop it returns
(216, 217, 227) over 10910 px, which is the figure this build has quoted since the shell's
blending was rebuilt; applied to the re-framed render of that build it returns (210, 210, 213),
which is the other half of the same record. So the instrument reproduces both recorded numbers
before it is used to judge a new one.

**The span is reported as percentiles of luminance, not as min/max.** Both frames are
antialiased against a white background and both carry a few near-clipped highlight pixels, so the
extremes measure the edge filter. p5..p95 is the facet-step band: the artwork's is 193..241 and
the SHAPE of that band is what `applyFacetSteps` exists to reproduce.

    python3 src/exhibits/ff7-cloud-strife-ultima-weapon/spec/measure_shell_value.py [<re-framed render>]

Reads `artifacts/ultima-v2/gate/full.png` by default -- the render `run_gates.sh` re-frames to
the crop's own 210x434 framing, so the two pictures are the same size and the same subject.
Writes `artifacts/ultima-v2/gate/shell-value.json`. Not a gate: it records, `audit_records.py`
then holds every document to what it recorded.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
V = HERE.parent
ROOT = HERE.parents[3]
A = ROOT / "artifacts" / "ultima-v2"
CROP = V / "assets" / "artwork-sword-crop.png"

CHROMA = 20   # max - min, above which a pixel belongs to a crystal, the gold or the leather
FLOOR = 170   # min channel, below which it is steel, leather or a shadowed metal
CEILING = 250  # max channel, above which it is the white background or its antialiasing


def census(image: Image.Image) -> dict:
    px = image.convert("RGB").load()
    w, h = image.size
    vals = [
        px[x, y]
        for y in range(h)
        for x in range(w)
        if max(px[x, y]) - min(px[x, y]) <= CHROMA
        and min(px[x, y]) >= FLOOR
        and max(px[x, y]) < CEILING
    ]
    if not vals:
        return {"pixels": 0}
    n = len(vals)
    lum = sorted(round(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) for c in vals)
    q = lambda t: lum[min(n - 1, int(t * n))]
    return {
        "pixels": n,
        "meanRGB": [round(sum(c[i] for c in vals) / n) for i in range(3)],
        "lumP5": q(0.05),
        "lumP50": q(0.50),
        "lumP95": q(0.95),
        "lumSpan": q(0.95) - q(0.05),
        "lumLevels": len(set(lum)),
    }


def main() -> None:
    render_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else A / "gate" / "full.png"
    artwork = Image.open(CROP)
    if not render_path.exists():
        raise SystemExit(
            f"{render_path} is missing -- capture the renders and run spec/run_gates.sh first"
        )
    render = Image.open(render_path)
    if render.size != artwork.size:
        raise SystemExit(
            f"{render_path} is {render.size}, not the crop's {artwork.size}: this compares the "
            "RE-FRAMED render (artifacts/ultima-v2/gate/full.png), not the raw capture"
        )

    art = census(artwork)
    ren = census(render)
    report = {
        "mask": {"chroma": CHROMA, "floor": FLOOR, "ceiling": CEILING},
        "artwork": art,
        "render": ren,
        "renderPath": str(render_path.relative_to(ROOT))
        if render_path.is_relative_to(ROOT)
        else str(render_path),
        "meanDelta": [ren["meanRGB"][i] - art["meanRGB"][i] for i in range(3)],
        "spanRatio": round(ren["lumSpan"] / art["lumSpan"], 3) if art["lumSpan"] else None,
    }
    for label, s in (("artwork", art), ("render ", ren)):
        print(
            f"{label}  n={s['pixels']:6d}  mean={tuple(s['meanRGB'])}  "
            f"lum p5={s['lumP5']} p50={s['lumP50']} p95={s['lumP95']}  "
            f"span={s['lumSpan']}  levels={s['lumLevels']}"
        )
    print(f"delta   mean {report['meanDelta']}   facet span ratio {report['spanRatio']}")

    out = A / "gate" / "shell-value.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
