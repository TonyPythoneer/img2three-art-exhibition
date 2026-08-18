"""Depth gate: does the model's yaw sweep widen the way the reference's does?

This is the only gate here that scores DEPTH, and it is pose-free — which matters, because no
frame on the sheet has a known pose. Both sides are reduced to the same pose-free statistic:

  widthRatio = (widest silhouette across the yaw sweep) / (front-view silhouette width)

For the reference that comes from the 87 frames whose height matches the front view's 68-70px.
A height match means the rotation stayed about the vertical axis, so those frames ARE a yaw
sweep of the same mesh in front of a fixed camera — 42px at the narrowest, 67px at the widest,
against a 47px front view. The model is captured the same way: fixed front camera, head turned.

A head that is too shallow cannot widen enough when it turns, and a head that is too deep widens
too much. Neither shows up in the front silhouette gate at all, which is why 1.25x-width sat on
the guess list through a whole pass of all-green gates.

  PASS when the model's width ratio is within --tol (relative) of the reference's.

Usage:
  python3 gate_yaw_sweep.py <renders-dir> <sheet.png> <frame-index.json> --out gate-yaw.json
Exit 0 pass, 1 gate failure, 2 error.
"""

import argparse
import json
import pathlib
import sys

from PIL import Image

SHEET_BG = (0, 0, 41)
BG_TOL = 24
FRONT_W = 47


def near(p, q, tol):
    return all(abs(a - b) <= tol for a, b in zip(p[:3], q[:3]))


def bbox(px, w, h, bg):
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            if not near(px[x, y], bg, BG_TOL):
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("renders")
    ap.add_argument("sheet")
    ap.add_argument("index")
    ap.add_argument("--out", required=True)
    # 5%: the reference widths are integers out of 67, so the instrument itself carries about
    # 1.5%. A looser tolerance would let a visibly wrong depth through — 1.25x-width sat at
    # 11.4% relative error and passed a 15% gate.
    ap.add_argument("--tol", type=float, default=0.05)
    a = ap.parse_args()

    # Reference side: the pure-yaw population.
    # Read the vetted pure-yaw set rather than re-deriving it from height alone. Height alone
    # admitted six tumbled frames, and because they were the six WIDEST they set this gate's
    # reference ratio single-handedly: 67/47 = 1.4255 against the true 62/47 = 1.319.
    pure_path = pathlib.Path(a.index).with_name("pure-yaw.json")
    yaw = json.load(open(pure_path))["pureYaw"]
    if not yaw:
        raise SystemExit(f"{pure_path} is empty — run pure_yaw_set.py")
    ref_widths = sorted(f["w"] for f in yaw)
    ref_ratio = max(ref_widths) / FRONT_W

    # Model side: the captured sweep.
    shots = sorted(pathlib.Path(a.renders).glob("yaw-*.png"))
    if not shots:
        raise SystemExit(f"no yaw-*.png in {a.renders} — run capture_sigma.mjs --yaw-sweep")
    sweep = []
    for p in shots:
        im = Image.open(p).convert("RGB")
        px = im.load()
        b = bbox(px, im.width, im.height, px[0, 0])
        if not b:
            raise SystemExit(f"{p.name} is empty — the capture caught a blank canvas")
        sweep.append({"file": p.name, "w": b[0], "h": b[1]})

    front = sweep[0]
    model_ratio = max(s["w"] for s in sweep) / front["w"]
    err = abs(model_ratio - ref_ratio) / ref_ratio

    rec = {
        "reference": {
            "pureYawFrames": len(yaw),
            "widthRange": [min(ref_widths), max(ref_widths)],
            "frontWidth": FRONT_W,
            "widthRatio": round(ref_ratio, 4),
        },
        "model": {
            "steps": len(sweep),
            "frontWidth": front["w"],
            "widestWidth": max(s["w"] for s in sweep),
            "widthRatio": round(model_ratio, 4),
            "sweep": sweep,
        },
        "relError": round(err, 4),
        "tol": a.tol,
        "pass": err <= a.tol,
    }
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=1)
    print(
        json.dumps({k: rec[k] for k in ("reference", "relError", "tol", "pass")}, indent=1)
    )
    print("model:", json.dumps({k: rec["model"][k] for k in
                                ("steps", "frontWidth", "widestWidth", "widthRatio")}))
    sys.exit(0 if rec["pass"] else 1)


main()
