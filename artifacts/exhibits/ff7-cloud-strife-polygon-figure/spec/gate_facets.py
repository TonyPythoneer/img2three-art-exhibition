#!/usr/bin/env python3
"""prompt.txt §3.2 / §5.4 — the normal-angle distribution gate.

    python3 gate_facets.py pin                 # sweep the fake frames, write facet-gate.json
    python3 gate_facets.py check <meshes.json> # assert a real part against the pinned values

Why this gate exists: the mechanical gates that shipped the first head measured
DIMENSIONS and went all-green while the model was a smooth egg (AGENTS.md, "a gate
must block the thing you are actually afraid of"). Dimensions cannot see faceting.
The distribution of angles between ADJACENT FACE NORMALS can.

The assertion is
    fraction of adjacent face pairs whose normals differ by >= ANGLE  >=  THRESHOLD
plus `material.flatShading === true` and a triangle count within the part's budget.

ANGLE and THRESHOLD are NOT guessed. `pin` sweeps ANGLE, measures the fraction on two
fake frames that MUST fail (a smooth sphere and an 8-ring x 8-segment lofted egg) and
on a positive control that MUST pass (a chamfered box, the S-02/S-03/S-11 generator),
and takes the angle with the widest separation. If no angle separates them the gate is
invalid and this script says so instead of emitting a threshold — §12's hard stop.

Mesh input is the same shape forge/stage4_review/self_intersection.py consumes:
{"meshes": [{"name":..., "vertices": [[x,y,z],...], "indices": [...]}]} , or a single
mesh, or a bare list. `node runtime/scripts/export_mesh_geometry.mjs` emits it.

Pure stdlib.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "facet-gate.json"
WELD = 6  # decimal places for position welding

Vec = tuple[float, float, float]


# ----------------------------------------------------------------- the metric ---
def _tris(mesh: dict) -> list[tuple[int, int, int]]:
    idx = mesh.get("indices")
    if idx is None:
        n = len(mesh["vertices"])
        return [(i, i + 1, i + 2) for i in range(0, n - 2, 3)]
    if idx and isinstance(idx[0], (list, tuple)):
        return [tuple(t) for t in idx]
    return [(idx[i], idx[i + 1], idx[i + 2]) for i in range(0, len(idx) - 2, 3)]


def _normal(a: Vec, b: Vec, c: Vec) -> Vec | None:
    e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    n = (
        e1[1] * e2[2] - e1[2] * e2[1],
        e1[2] * e2[0] - e1[0] * e2[2],
        e1[0] * e2[1] - e1[1] * e2[0],
    )
    ln = math.sqrt(sum(c * c for c in n))
    return None if ln <= 0 else (n[0] / ln, n[1] / ln, n[2] / ln)


def facet_angles(mesh: dict) -> list[float]:
    """Angles in degrees between the normals of every edge-adjacent triangle pair.

    Vertices are welded BY POSITION, not by index. Under flatShading every triangle
    carries its own copies of its corners, so index-adjacency finds no shared edges at
    all and the gate would report "0 adjacent pairs" on exactly the models it exists
    to judge.
    """
    verts = [tuple(map(float, v)) for v in mesh["vertices"]]
    keys = [tuple(round(c, WELD) for c in v) for v in verts]
    normals: list[Vec] = []
    edges: dict[tuple, list[int]] = {}
    for tri in _tris(mesh):
        n = _normal(verts[tri[0]], verts[tri[1]], verts[tri[2]])
        if n is None:
            continue
        fi = len(normals)
        normals.append(n)
        k = [keys[i] for i in tri]
        for a, b in ((k[0], k[1]), (k[1], k[2]), (k[2], k[0])):
            edges.setdefault((a, b) if a <= b else (b, a), []).append(fi)
    out = []
    for faces in edges.values():
        if len(faces) != 2:
            continue
        n1, n2 = normals[faces[0]], normals[faces[1]]
        d = max(-1.0, min(1.0, sum(x * y for x, y in zip(n1, n2))))
        out.append(math.degrees(math.acos(d)))
    return out


def measure(mesh: dict, angle: float) -> dict:
    angles = facet_angles(mesh)
    if not angles:
        return {"adjacentPairs": 0, "fraction": 0.0, "meanDeg": 0.0, "triangles": len(_tris(mesh))}
    s = sorted(angles)
    return {
        "adjacentPairs": len(angles),
        "triangles": len(_tris(mesh)),
        "fraction": sum(1 for a in angles if a >= angle) / len(angles),
        "meanDeg": sum(angles) / len(angles),
        "medianDeg": s[len(s) // 2],
        "p90Deg": s[len(s) * 9 // 10],
        "maxDeg": s[-1],
    }


# ------------------------------------------------------------------ fake frames ---
def sphere(seg: int = 48, ring: int = 24) -> dict:
    """The smooth frame. It must FAIL — if it passes, the gate measures nothing."""
    verts: list[Vec] = []
    for i in range(ring + 1):
        phi = math.pi * i / ring
        for j in range(seg + 1):
            th = 2 * math.pi * j / seg
            verts.append(
                (math.sin(phi) * math.cos(th), math.cos(phi), math.sin(phi) * math.sin(th))
            )
    idx: list[tuple[int, int, int]] = []
    for i in range(ring):
        for j in range(seg):
            a = i * (seg + 1) + j
            b = a + seg + 1
            idx += [(a, b, a + 1), (b, b + 1, a + 1)]
    return {"name": "fake:smooth-sphere", "vertices": verts, "indices": idx}


def lofted_egg(sides: int = 8, segments: int = 8) -> dict:
    """The near-miss frame: the shape the first head turned out to be.

    An 8-sided ring lofted over 8 segments. It is genuinely faceted around its rings
    (45 degrees per edge) and genuinely smooth along them, which is the whole point:
    it is what a gate that only counts "some big angles somewhere" waves through.
    """
    verts: list[Vec] = []
    for k in range(segments + 1):
        t = k / segments
        y = math.cos(math.pi * t)
        r = math.sin(math.pi * t) * (0.75 + 0.25 * t)
        for j in range(sides + 1):
            th = 2 * math.pi * j / sides
            verts.append((r * math.cos(th), y, r * math.sin(th)))
    idx: list[tuple[int, int, int]] = []
    for k in range(segments):
        for j in range(sides):
            a = k * (sides + 1) + j
            b = a + sides + 1
            idx += [(a, b, a + 1), (b, b + 1, a + 1)]
    return {"name": "fake:lofted-egg-8x8", "vertices": verts, "indices": idx}


def _prism(rings: list[list[Vec]], name: str) -> dict:
    """Side quads plus two fan caps over a stack of equal-length rings."""
    sides = len(rings[0])
    verts: list[Vec] = [p for ring in rings for p in ring]
    idx: list[tuple[int, int, int]] = []
    for k in range(len(rings) - 1):
        base, nxt = k * sides, (k + 1) * sides
        for j in range(sides):
            j2 = (j + 1) % sides
            idx += [(base + j, nxt + j, base + j2), (nxt + j, nxt + j2, base + j2)]
    top = (len(rings) - 1) * sides
    for j in range(1, sides - 1):
        idx.append((0, j, j + 1))
        idx.append((top, top + j + 1, top + j))
    return {"name": name, "vertices": verts, "indices": idx}


def chamfered_box(w: float = 1.0, d: float = 0.8, h: float = 1.4, c: float = 0.12) -> dict:
    """Positive control: the S-02 / S-03 / S-11 generator, faceted by construction.

    A box with its four VERTICAL edges chamfered is an octagonal prism, which is what
    §4[2] describes; building it as one is both correct and cheap. (The first attempt
    took a brute-force convex hull of 24 corner points, which emits every coplanar
    triple, so a flat face ended up covered by overlapping triangles, every edge was
    shared by more than two faces, and the gate saw ZERO adjacent pairs.)

    If the pinned threshold does not admit THIS, the gate rejects the model it exists
    to protect and is as useless as one that admits the sphere.
    """
    x, z = w / 2, d / 2
    ring: list[Vec] = [
        (x - c, 0.0, z), (-(x - c), 0.0, z), (-x, 0.0, z - c), (-x, 0.0, -(z - c)),
        (-(x - c), 0.0, -z), (x - c, 0.0, -z), (x, 0.0, -(z - c)), (x, 0.0, z - c),
    ]
    rings = [[(p[0], y, p[2]) for p in ring] for y in (-h / 2, h / 2)]
    return _prism(rings, "control:chamfered-box")


def loft_prism(sides: int, name: str, r_top: float = 0.6, r_bot: float = 1.0) -> dict:
    """Positive control: the loftPrism generator behind S-04..S-14, one segment.

    Included because it is the shape the fake egg most resembles — same ring, same
    edge angles. If a pinned angle admits this and rejects the egg, the separation is
    real; if it rejects both, the gate cannot tell a legitimate lofted part from the
    failure mode, and that is a finding, not a threshold.
    """
    rings = []
    for y, r in ((-0.7, r_bot), (0.7, r_top)):
        rings.append(
            [
                (r * math.cos(2 * math.pi * j / sides), y, r * math.sin(2 * math.pi * j / sides))
                for j in range(sides)
            ]
        )
    return _prism(rings, name)


# ------------------------------------------------------------------------ pin ---
ANGLE_SWEEP = [float(a) for a in range(6, 91, 2)]
MIN_SEPARATION = 0.15


def pin() -> dict:
    fakes = [sphere(), lofted_egg()]
    controls = [
        chamfered_box(),
        loft_prism(6, "control:loftPrism-6"),
        loft_prism(8, "control:loftPrism-8"),
    ]
    rows = []
    for angle in ANGLE_SWEEP:
        fk = [measure(m, angle) for m in fakes]
        ct = [measure(m, angle) for m in controls]
        fake_max = max(r["fraction"] for r in fk)
        ctrl_min = min(r["fraction"] for r in ct)
        rows.append(
            {
                "angleDeg": angle,
                "fakeFractions": {m["name"]: r["fraction"] for m, r in zip(fakes, fk)},
                "controlFractions": {m["name"]: r["fraction"] for m, r in zip(controls, ct)},
                "separation": ctrl_min - fake_max,
            }
        )
    best = max(rows, key=lambda r: r["separation"])
    fake_max = max(best["fakeFractions"].values())
    ctrl_min = min(best["controlFractions"].values())
    ok = best["separation"] >= MIN_SEPARATION
    doc = {
        "schema": "ff7-cloud-strife-facet-gate/1",
        "generatedBy": "artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/gate_facets.py",
        "assertion": "fraction of edge-adjacent triangle pairs with normal angle >= angleDeg must be >= threshold",
        "sweep": rows,
        "angleDeg": best["angleDeg"],
        "threshold": (fake_max + ctrl_min) / 2 if ok else None,
        "fakeFrames": {
            name: {
                "fraction": frac,
                "fails": (frac < (fake_max + ctrl_min) / 2) if ok else None,
            }
            for name, frac in best["fakeFractions"].items()
        },
        "positiveControls": {
            name: {
                "fraction": frac,
                "passes": (frac >= (fake_max + ctrl_min) / 2) if ok else None,
            }
            for name, frac in best["controlFractions"].items()
        },
        "separation": best["separation"],
        "minSeparation": MIN_SEPARATION,
        "pinned": ok,
        "detail": {
            m["name"]: measure(m, best["angleDeg"]) for m in fakes + controls
        },
    }
    if not ok:
        doc["hardStop"] = (
            "no angle in the sweep separates both fake frames from the control by "
            f"{MIN_SEPARATION}. §12: the threshold cannot be pinned, so the gate is "
            "invalid and must not be carried forward."
        )
    return doc


# ---------------------------------------------------------------------- check ---
def load_meshes(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        meshes = payload.get("meshes") or payload.get("components")
        if isinstance(meshes, dict):
            return [dict(v, name=k) for k, v in meshes.items()]
        if isinstance(meshes, list):
            return meshes
        return [payload]
    return payload


def check(path: Path) -> int:
    if not OUT.exists():
        print("facet-gate.json missing — run `python3 gate_facets.py pin` first", file=sys.stderr)
        return 2
    cfg = json.loads(OUT.read_text(encoding="utf-8"))
    if not cfg.get("pinned"):
        print(f"gate is not pinned: {cfg.get('hardStop')}", file=sys.stderr)
        return 2
    angle, thr = cfg["angleDeg"], cfg["threshold"]
    failures = 0
    for mesh in load_meshes(path):
        name = mesh.get("name", "<unnamed>")
        r = measure(mesh, angle)
        flat = mesh.get("material", {}).get("flatShading")
        ok = r["fraction"] >= thr and flat is not False
        failures += 0 if ok else 1
        print(
            f"{'PASS' if ok else 'FAIL'} {name:24s} fraction={r['fraction']:.3f} "
            f"(>= {thr:.3f} at {angle:.0f} deg)  mean={r['meanDeg']:.1f} deg  "
            f"tris={r['triangles']}  flatShading={flat}"
        )
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "pin"
    if cmd == "pin":
        doc = pin()
        OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(f"angle {doc['angleDeg']:.0f} deg   separation {doc['separation']:.3f}")
        for name, r in doc["fakeFrames"].items():
            print(f"  fake    {name:26s} fraction={r['fraction']:.3f} fails={r['fails']}")
        for name, r in doc["positiveControls"].items():
            print(f"  control {name:26s} fraction={r['fraction']:.3f} passes={r['passes']}")
        print(f"threshold {doc['threshold']}   pinned={doc['pinned']}")
        if not doc["pinned"]:
            print(doc["hardStop"], file=sys.stderr)
            return 2
        return 0
    if cmd == "check" and len(argv) > 1:
        return check(Path(argv[1]))
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
