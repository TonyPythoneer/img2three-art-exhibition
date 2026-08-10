#!/usr/bin/env python3
"""Is the gem OCCLUDED by the solid shell, or TINTED through its own transmission pass?

Same question `measure_relief_visibility.py` already had to answer once for the gem against the
dark core, and the answer settled it there: `rootGem` is a MeshPhysicalMaterial with
transmission 0.22, which three.js resolves in a pass that samples the OPAQUE backbuffer. A
translucent shell was never in that buffer; a SOLID one is. So the question has to be re-asked,
and a pixel-identity test cannot answer it.

Three signatures separate the two:

  occlusion  the pixel takes the SHELL's colour. The gem's red is gone.
  tint       the pixel stays on the gem-vs-shell colour AXIS, scaled — a dimmer or paler red.
  boundary   the failure map's edge is the depth crossing near the apex (occlusion) or the
             footprint edge / the whole rhombus (tint).

Prints the census and writes a failure map.

    python3 artifacts/ultima-v2/diag/gem_vs_shell.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
VIS = ROOT / "artifacts/ultima-v2/vis"
OUT = Path(__file__).resolve().parent

OWN = 14
SAME = 5


def load(name: str):
    im = Image.open(VIS / name).convert("RGB")
    return im.tobytes(), im.width, im.height


for view in ("front-orthographic", "back-orthographic"):
    base, W, H = load(f"{view}-base.png")
    only, _, _ = load(f"{view}-gemOnly.png")
    over, _, _ = load(f"{view}-gemShell.png")
    # `shellHere` is what the pixel reads when the SHELL owns it and the gem is absent: the
    # coreShell frame minus the core's own footprint is messy, so use the insertShell frame's
    # shell where the gem is not drawn — simplest honest proxy is the coreShell frame, which
    # carries the shell over the same region with the gem hidden.
    shell, _, _ = load(f"{view}-coreShell.png")

    own = same = 0
    buckets = {"identical": 0, "on-axis-scaled": 0, "shell-coloured": 0, "other": 0}
    samples = []
    shares: list[float] = []
    ys = []
    diff = Image.new("RGB", (W, H), (255, 255, 255))
    dpx = diff.load()
    for p in range(W * H):
        i = p * 3
        b = base[i : i + 3]
        o = only[i : i + 3]
        v = over[i : i + 3]
        s = shell[i : i + 3]
        if max(abs(o[c] - b[c]) for c in range(3)) < OWN:
            continue
        own += 1
        x, y = p % W, p // W
        if max(abs(o[c] - v[c]) for c in range(3)) <= SAME:
            same += 1
            dpx[x, y] = (210, 210, 210)
            continue
        ys.append(y)
        # projection of (over - shell) onto (only - shell): 1.0 = the gem owns it outright,
        # 0.0 = the shell does.
        axis = [o[c] - s[c] for c in range(3)]
        norm = sum(a * a for a in axis)
        share = (
            sum((v[c] - s[c]) * axis[c] for c in range(3)) / norm if norm >= 12 * 12 else None
        )
        if share is not None and share >= 0.5:
            buckets["on-axis-scaled"] += 1
            dpx[x, y] = (40, 160, 60)
        elif max(abs(v[c] - s[c]) for c in range(3)) <= SAME:
            buckets["shell-coloured"] += 1
            dpx[x, y] = (220, 40, 40)
        else:
            buckets["other"] += 1
            dpx[x, y] = (40, 60, 200)
        if share is not None:
            shares.append(share)
        if len(samples) < 6 and len(ys) % 233 == 1:
            samples.append((o, v, s, None if share is None else round(share, 3)))

    print(f"\n{view}: gem footprint {own} px, identical to gemOnly {same} px ({same/own:.1%})")
    for k, n in buckets.items():
        if n:
            print(f"  {k:16s} {n:6d}  {n/own:6.1%}")
    print(f"  failing rows y {min(ys) if ys else '-'}..{max(ys) if ys else '-'} "
          f"of the footprint's own span")
    for o, v, s, share in samples:
        print(f"  gemOnly {o} -> gemShell {v}   shell alone {s}   survival {share}")
    if shares:
        shares.sort()
        n = len(shares)
        q = lambda t: shares[min(n - 1, int(t * n))]
        print(
            f"  survival over the {n} non-identical px: min {shares[0]:.3f} p5 {q(.05):.3f} "
            f"p50 {q(.5):.3f} p95 {q(.95):.3f} max {shares[-1]:.3f}; "
            f"below 0.5: {sum(1 for v in shares if v < 0.5)}"
        )
    diff.save(OUT / f"gem-vs-shell-{view}.png")
    print(f"  wrote {(OUT / f'gem-vs-shell-{view}.png').relative_to(ROOT)}")
