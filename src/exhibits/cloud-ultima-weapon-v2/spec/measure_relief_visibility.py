#!/usr/bin/env python3
"""How much of each blade relief you can actually SEE, front and rear, measured off renders.

The lift ladder in `check_centerline.py` proves a layer stands the right distance off the one
below it AT THE BLADE'S THICKEST POINT. It cannot prove the layer is *visible* anywhere else: it
reads bounding boxes, so a layer can clear everything at its deepest vertex and still have its
whole outline buried. So this measures the thing the eye judges, differentially, from renders of
one camera:

    base    every blade relief AND the shell hidden
    only    base + one relief layer           -> the layer's own footprint is (only != base)
    shell   only + the outer shell            -> where (shell == only) the shell was DEPTH-
                                                REJECTED, i.e. the layer stands in front of it
    gemCore the gem + the dark core           -> where (gemCore == gemOnly) the gem stands in
                                                front of the layer DIRECTLY under it

**The last one is a separate question and it is the one that caught this correction.** The build
before it measured 93.4% of the diamond proud of the shell while the diamond's entire rhombus
outline lay inside the dark core: the gem's girdle sat at 15.53 and the core's plateau at 18.62
over the whole of their overlap, Y = 56…97. Proud of the shell and buried by the layer in
between are not the same fact, and only one of them was ever asked.

**The comparisons are NOT all scored the same way, and the rule is one sentence: identity is
valid exactly when the WINNER is opaque.** A layer that wins the depth test against an opaque
surface keeps its pixel to the bit; a layer that is itself TRANSMISSIVE has its own pixels
resolved against the opaque backbuffer, so whatever it won the depth test against still changes
its colour, and identity reads that as occlusion. `rootDiamondGem` is the one transmissive layer
on this blade and it is scored by projection against BOTH surfaces; the two films are opaque and
are scored by identity against the shell.

Against the SHELL, identity is right for an OPAQUE layer. `outerCrystal` has depth testing on, so
wherever the film is nearer the shell's fragment is discarded and never blended — the film's own
pixel is untouched.

**It stopped being right for the gem on 2026-08-07, when the shell went SOLID by direction.** A
translucent shell was not in the opaque backbuffer the gem's transmission pass samples; a solid
one is, so it now dims the gem's own red by about 8% everywhere the gem plainly wins the depth
test. Measured on the first captured set of the solid build: of the gem's 1548-px front
footprint, identity passed **18 px (1.2%)** — and of the 1530 it failed, **1530 (100%) stayed on
the gem-vs-shell colour axis with a survival of 0.847 or better, and not one took the shell's
colour** (`artifacts/ultima-v2/diag/gem_vs_shell.py`, e.g. `(227, 195, 205) -> (194, 165, 185)`
against a shell reading `(214, 215, 228)`). That is a tint, not an occlusion, and the failure map
covers the whole rhombus rather than any depth crossing. So the gem is scored against the shell
by the same projection it is scored against the core by, and the third frame it needs —
`shellOnly`, the colour a pixel the shell won would read as — is captured for it.

Against the DARK CORE it was wrong from the start, and it was wrong by 50 points. `rootGem` is a
`MeshPhysicalMaterial` with `transmission: 0.22`, which three.js resolves in a separate pass that
samples the OPAQUE backbuffer. Putting the opaque dark core behind the gem therefore darkens the
gem's own pixels even where the gem plainly won the depth test. Measured on the first captured
set: 44.9% by identity, and of the 850 failing pixels **771 (90.7%) were a dimmed gem red, not
the core's colour** — e.g. `(157, 25, 62) -> (116, 16, 45)` against a core reading `(26, 6, 35)`,
a 0.74 scaling and nothing like an occlusion. The failure map settled it: the boundary between
passing and failing was a flat horizontal line at the rhombus's waist, `Y = 55`, which is the
CORE'S OWN LOWER EDGE — the footprint boundary — and not the depth crossing near the apex that a
real occlusion would have drawn.

So the seating test asks the same question with an instrument that survives a translucent winner:
**how much of the gem's own contrast against the core survived at this pixel**, projected onto
the gem-vs-core colour axis. 1.0 = the gem owns the pixel outright, 0.0 = the core does. This is
not a softer threshold — a pixel the core genuinely wins reads as the core's exact colour and
scores 0.0. The distribution is bimodal with an empty valley: 1390 of 1543 pixels score ≥ 0.6,
64 score ≤ 0.2, and only 13 land anywhere near the 0.5 cut. Fed a synthetic frame in which the
core wins everywhere the two footprints overlap — the defect this gate exists for — it scores
**0.0%**.

Front view scores the FRONT piece, rear view the REAR piece — the two are separate meshes and
the point of the split is that each one has to break its host on its own side.

    python3 spec/measure_relief_visibility.py [<render dir>]

Writes artifacts/ultima-v2/gate/relief-visibility.json. Exit 1 if a layer's proud fraction is
under its floor on either face.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
A = ROOT / "artifacts" / "ultima-v2"

# A layer that clears the shell over less than this much of its own footprint does not read as a
# raised crystal. The whole point of the split is that BOTH faces have to hold it.
#
# **The number has not moved, but the way the gem reaches it did on 2026-08-07, so it is
# re-bracketed against the new scoring.** Doctored `gemShell` frames through this same script,
# each one repainting a band of the stone's footprint with what `shellOnly` reads there — i.e.
# the shell genuinely in front of that band (`artifacts/ultima-v2/diag/bracket_gem_shell.py`):
#
#     the shell wins the whole overlap                      0.0%   rejected
#     the stone's outer 8 px buried                        33.7%   rejected
#     the outer 6 px                                       49.1%   rejected
#     the outer 5 px                                       57.8%   rejected
#     the outer 4 px                                       67.3%   rejected
#     the outer 3 px                                       77.4%   passes
#     what is built now                                   100.0%   passes
#
# So 0.70 cuts between a three- and a four-pixel buried outline and the build clears it by 30
# points. Catching a thinner rim than that is SEAT_FLOOR's job at 0.95, against the layer the
# stone actually sits on, and it still reads 100.0%.
FLOOR = 0.70

# The diamond against the layer directly under it is held far higher, and the two floors are
# different KINDS of number rather than the same number twice. 0.70 is a judgement about how much
# of a relief has to read; this one is arithmetic: the gem's girdle is DERIVED to clear the stack
# by one relief step at every station, so the only part of the rhombus allowed to lose is the last
# few units into the apex, where the crown ramps down to a point inside the skins.
#
# That allowance is computable, not eyeballed. Between the upper band station and the apex the
# crown falls linearly from GEM_HALF_DEPTH = 24.785 at Y = 86.5 to zero at Y = 97, and the core
# skin's surface there is 14 + 2 x SKIN_STEP = 16.8, so the two cross at Y = 89.9. The rhombus's
# area above that line is 17 x (97 - 89.9)^2 / 42 = 20.5 against a total of 1428 -> **1.4%**. The
# render agrees: the outline fails over exactly the top six rows, 765-770 of 765-847, and passes
# from 771 down. The crop agrees too -- its dark pixels reach Y = 98.8 where the red stops at
# 97.3, so the artwork covers the gem's apex with the dark layer as well.
#
# The floor is then bracketed by measurement rather than set to "what this build scores". Fed
# doctored frames through this same script:
#
#     the core wins the whole overlap                       49.6%   rejected
#     the core wins only the gem's outer 3 px, plateau
#       still proud -- the PREVIOUS BUILD's actual defect
#       and the one an area score is worst at seeing        88.7%   rejected
#     what is built now                                     99.1%   passes
#
# 0.95 sits in the gap between 88.7 and 99.1. It has not been moved: it was 0.95 when the test
# was written, when the test was wrong, and now.
SEAT_FLOOR = 0.95
# Below this share of its own colour surviving, the pixel belongs to the layer underneath.
SEAT_OWNS = 0.5

# Only a pixel the layer clearly owns counts, so an antialiased sliver of the layer's edge is not
# scored as if it were the layer.
OWN = 14
# and "the other surface was depth-rejected here" is an exact pixel match, give or take the same
# edge.
SAME = 5
# `OWN` cannot remove the outermost antialiased ring on its own: a gem pixel blended 50/50 with
# the background still differs from `base` by far more than 14, so it enters the footprint while
# its colour is half something else. Behind it in the `gemCore` frame that something else is the
# dark core, which drags the ring's survival down for a reason that is the renderer's edge
# filtering and not the geometry — measured at 59.9% on the d=1 ring against 94.9% one pixel in
# and 100% in the interior. So the seating test erodes the footprint by one pixel first. That is
# the rule `OWN` already states, applied where it actually bites.
SEAT_ERODE = 1

# layer -> (render tag, (front mesh, rear mesh))
LAYERS = {
    "purpleEnergyInsert": ("insert", ("purpleEnergyInsertFront", "purpleEnergyInsertRear")),
    "darkCoreTriangle": ("core", ("darkCoreTriangleFront", "darkCoreTriangleRear")),
    "rootDiamondGem": ("gem", ("rootDiamondGemFront", "rootDiamondGemRear")),
}
# layer -> (its own render tag, the render with both, the layer under it, that layer's own tag).
# All four are needed: the pair says who won, and the under-layer ALONE is the colour a pixel it
# won would read as, which is what the survival projection is measured against.
SEATED = {
    "rootDiamondGem": ("gem", "gemCore", "darkCoreTriangle", "core"),
}
# Layers whose own material is transmissive, so their pixels are resolved against the opaque
# backbuffer and an opaque winner behind them tints without occluding. These are scored against
# the SHELL by the same projection as the seating test, with `shellOnly` as the under-frame.
# Identity is kept for everything else: the two films are opaque and their 97.6 / 93.2 are
# measured by the test that is valid for them.
TRANSMISSIVE = {"rootDiamondGem"}
SHELL_ALONE = "shellOnly"
FACES = {"front-orthographic": "front", "back-orthographic": "rear"}


def load(d: Path, name: str) -> bytes:
    """Flat RGB bytes — three per pixel, in the same order for every render of a view."""
    return Image.open(d / name).convert("RGB").tobytes()


def load_sized(d: Path, name: str) -> tuple[bytes, int, int]:
    """The same bytes, plus the frame size — the seating test needs neighbours."""
    image = Image.open(d / name).convert("RGB")
    return image.tobytes(), image.width, image.height


def surviving_fraction(
    over: bytes, own: bytes, under: bytes, i: int
) -> float | None:
    """How much of `own`'s colour against `under` survived in `over`, at flat-RGB offset `i`.

    A projection onto the own-vs-under colour axis rather than a distance, so it stays meaningful
    when the winner is translucent: `under` scores 0.0, an untouched `own` scores 1.0, and a gem
    that won the depth test but lost 26% of its diffuse to transmission scores 0.74.

    None when the two surfaces are the same colour here — there is nothing to tell apart, so the
    pixel cannot testify either way and is counted as owned.
    """
    axis = [own[i + c] - under[i + c] for c in (0, 1, 2)]
    norm = sum(v * v for v in axis)
    if norm < 12 * 12:
        return None
    return sum((over[i + c] - under[i + c]) * axis[c] for c in (0, 1, 2)) / norm


def eroded_footprint(base: bytes, only: bytes, w: int, h: int, rounds: int) -> bytearray:
    """The layer's own footprint, less `rounds` rings of its antialiased edge.

    Shared by both projected comparisons on purpose. The erosion is not a softener: a pixel of
    the layer blended 50/50 with what is behind it differs from `base` by far more than `OWN`, so
    it enters the footprint while its colour is already half something else, and a PROJECTION
    scores that ring on the renderer's edge filtering rather than on the geometry. Identity does
    not need it — an antialiased pixel is identical in both frames when nothing occludes it.
    """
    inside = bytearray(w * h)
    for p in range(w * h):
        i = p * 3
        if max(abs(only[i + c] - base[i + c]) for c in (0, 1, 2)) >= OWN:
            inside[p] = 1
    for _ in range(rounds):
        nxt = bytearray(w * h)
        for p in range(w * h):
            if not inside[p]:
                continue
            x, y = p % w, p // w
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                continue
            if inside[p - 1] and inside[p + 1] and inside[p - w] and inside[p + w]:
                nxt[p] = 1
        inside = nxt
    return inside


def main() -> None:
    d = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else A / "vis"
    if not d.exists():
        raise SystemExit(
            f"{d} is missing — capture it first:\n"
            "  zsh src/exhibits/cloud-ultima-weapon-v2/spec/capture_visibility.sh"
        )
    # `d` is an argument, so it may point outside the repo — a scratch copy with one frame
    # doctored is how the seating floor gets checked against a defect it has to reject.
    rel = str(d.relative_to(ROOT)) if d.is_relative_to(ROOT) else str(d)
    report: dict = {"renderDir": rel, "floor": FLOOR, "layers": {}}
    failures: list[str] = []

    for layer, (tag, pieces) in LAYERS.items():
        entry: dict = {"pieces": {}}
        for view, face in FACES.items():
            base, W, H = load_sized(d, f"{view}-base.png")
            only = load(d, f"{view}-{tag}Only.png")
            over = load(d, f"{view}-{tag}Shell.png")
            projected = layer in TRANSMISSIVE
            alone = load(d, f"{view}-{SHELL_ALONE}.png") if projected else None
            scored = eroded_footprint(base, only, W, H, SEAT_ERODE if projected else 0)
            own = proud = 0
            for p in range(W * H):
                if not scored[p]:
                    continue
                i = p * 3
                own += 1
                if projected:
                    assert alone is not None
                    share = surviving_fraction(over, only, alone, i)
                    if share is None or share >= SEAT_OWNS:
                        proud += 1
                elif max(abs(only[i + c] - over[i + c]) for c in (0, 1, 2)) <= SAME:
                    proud += 1
            fraction = proud / own if own else 0.0
            piece = pieces[0] if face == "front" else pieces[1]
            entry["pieces"][face] = {
                "mesh": piece,
                "view": view,
                "scoredBy": "survival" if projected else "identity",
                "footprintPx": own,
                "proudPx": proud,
                "proudFraction": round(fraction, 4),
                # Rounded once, here. Every document and `audit_records.py` quote THIS field --
                # re-rounding the fraction downstream is how 93.4 and 93.3 end up in two records
                # of the same measurement.
                "proudPercent": round(fraction * 100, 1),
            }
            status = "ok " if fraction >= FLOOR else "OFF"
            print(
                f"{status} {piece:<24} {face:<5} {proud:6d} / {own:6d} px proud of the shell"
                f"  = {entry['pieces'][face]['proudPercent']:5.1f}%   (floor {FLOOR * 100:.0f}%)"
            )
            if fraction < FLOOR:
                failures.append(
                    f"{piece}: only {fraction * 100:.1f}% of its {face}-view footprint stands "
                    f"in front of the shell; the floor is {FLOOR * 100:.0f}%"
                )
        f, r = entry["pieces"]["front"], entry["pieces"]["rear"]
        # The two halves are mirror images, so their footprints and their proud fractions have to
        # agree. A gap here means the split is lopsided, which the front/rear silhouette IoU
        # would only catch once it had grown large.
        skew = abs(f["proudFraction"] - r["proudFraction"])
        entry["frontRearSkew"] = round(skew, 4)
        print(f"{'ok ' if skew <= 0.02 else 'OFF'} {layer:<24} front/rear skew {skew:.4f}")
        if skew > 0.02:
            failures.append(f"{layer}: front and rear differ by {skew:.4f} in proud fraction")
        report["layers"][layer] = entry

    # --- and the same trick one layer down: is the diamond proud of what it sits ON? ---------
    report["seating"] = {}
    for layer, (tag, over, under_name, under_tag) in SEATED.items():
        entry = {"under": under_name, "pieces": {}}
        pieces = LAYERS[layer][1]
        for view, face in FACES.items():
            base, W, H = load_sized(d, f"{view}-base.png")
            only = load(d, f"{view}-{tag}Only.png")
            both = load(d, f"{view}-{over}.png")
            alone = load(d, f"{view}-{under_tag}Only.png")

            # The layer's own footprint, then eroded by one pixel to drop the antialiased ring.
            scored = eroded_footprint(base, only, W, H, SEAT_ERODE)

            own = proud = 0
            for p in range(W * H):
                if not scored[p]:
                    continue
                own += 1
                share = surviving_fraction(both, only, alone, p * 3)
                if share is None or share >= SEAT_OWNS:
                    proud += 1
            fraction = proud / own if own else 0.0
            piece = pieces[0] if face == "front" else pieces[1]
            entry["pieces"][face] = {
                "mesh": piece,
                "view": view,
                "footprintPx": own,
                "proudPx": proud,
                "proudFraction": round(fraction, 4),
                "proudPercent": round(fraction * 100, 1),
            }
            status = "ok " if fraction >= SEAT_FLOOR else "OFF"
            print(
                f"{status} {piece:<24} {face:<5} {proud:6d} / {own:6d} px proud of {under_name}"
                f"  = {entry['pieces'][face]['proudPercent']:5.1f}%   "
                f"(floor {SEAT_FLOOR * 100:.0f}%)"
            )
            if fraction < SEAT_FLOOR:
                failures.append(
                    f"{piece}: only {fraction * 100:.1f}% of its {face}-view footprint stands in "
                    f"front of {under_name}; the floor is {SEAT_FLOOR * 100:.0f}%. The layer it "
                    "sits on is swallowing its outline — clearing the SHELL is not the same test"
                )
        report["seating"][layer] = entry

    out = A / "gate" / "relief-visibility.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nwrote {out.relative_to(ROOT)}")
    if failures:
        for line in failures:
            print(f"FAIL {line}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
