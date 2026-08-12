#!/usr/bin/env python3
"""Re-capture the doctored geometries the FLUSH assertions are bracketed against.

Every figure in a document under this exhibit has to trace to an artifact, and a bracket is a
figure. So each variant below is a one-clause reversion of the shipped factory, captured into its
own folder under `artifacts/ultima-v2/diag/`, and `spec/check_centerline.py` is run against it.
Nothing here is used by the build; it exists so the numbers in §8, §9 and RELATIONSHIPS §5 can be
re-derived rather than believed.

    python3 artifacts/ultima-v2/diag/bracket_flush.py [name ...]

The factory is restored from a copy on the way out, including on failure.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FACTORY = ROOT / "src/utils/ultimaWeaponV2/createUltimaWeaponV2Model.ts"
DIAG = ROOT / "artifacts/ultima-v2/diag"
CHECK = ROOT / "artifacts/exhibits/cloud-ultima-weapon-v2/spec/check_centerline.py"

APEX_EDGE = "    const apex = skinSection(apexY, 0, (x) => seatUnder(x, apexY), SKIN_STEP, sign);"
APEX_POINT = (
    "    const apex = [new THREE.Vector3(0, n(apexY), "
    "sign * n(seatUnder(0, apexY) + SKIN_STEP))];"
)
SEAT_HEAD = "const GEM_SEAT_STATIONS: number[] = (() => {"
COVERS = "  return halfWidth > 0 && Math.abs(x) <= halfWidth;"
BAND_23 = "  [23.5, 44.55125, 11.625],\n"
BAND_34 = "  [34, 57.3675, 12.25],\n"
BAND_44 = "  [44.5, 70.18375, 12.875],\n"

# name -> (what it reverts, patch)
VARIANTS: dict[str, tuple[str, "object"]] = {
    "bracket-apex-point": (
        "both films close their apex at a POINT at the outer depth, as before 2026-08-09",
        lambda s: s.replace(APEX_EDGE, APEX_POINT),
    ),
    "bracket-gem-no-seat-stations": (
        "the stone's rings are GEM_STATIONS alone — no shell knees, no ledge at the films' base",
        lambda s: s.replace(
            SEAT_HEAD,
            SEAT_HEAD + "\n  return GEM_STATIONS.map(([y]) => y); // BRACKET",
        ),
    ),
    "bracket-zero-width-covers-axis": (
        "`|x| <= halfWidthAt(y)` again, so a film of ZERO width covers its own axis",
        lambda s: s.replace(COVERS, "  return Math.abs(x) <= halfWidth; // BRACKET"),
    ),
    "bracket-trapezoid-1band": (
        "the shell's lower trapezoid as ONE band, Y = 13 -> 55",
        lambda s: s.replace(BAND_23, "").replace(BAND_34, "").replace(BAND_44, ""),
    ),
    "bracket-trapezoid-2band": (
        "the shell's lower trapezoid halved, + Y = 34 only",
        lambda s: s.replace(BAND_23, "").replace(BAND_44, ""),
    ),
}


def main() -> None:
    wanted = sys.argv[1:] or list(VARIANTS)
    good = FACTORY.read_text()
    env = {**os.environ, "CAPTURE_PORT": os.environ.get("CAPTURE_PORT", "3191")}
    try:
        for name in wanted:
            why, patch = VARIANTS[name]
            doctored = patch(good)
            if doctored == good:
                raise SystemExit(f"{name}: the patch matched nothing — the factory has moved")
            FACTORY.write_text(doctored)
            out = DIAG / name
            out.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["node", "tools/capture_ultima.mjs", "--route", "ultima-v2-harness",
                 "--out", str(out.relative_to(ROOT)), "--detail", "full",
                 "--views", "artwork-match"],
                cwd=ROOT, env=env, check=True, capture_output=True,
            )
            report = subprocess.run(
                ["python3", str(CHECK), str(out / "parts.json")],
                cwd=ROOT, capture_output=True, text=True,
            )
            print(f"=== {name}: {why}")
            for line in report.stdout.splitlines():
                if "seat flush" in line or "into the shell" in line or line.startswith("FAIL"):
                    print("   ", line)
            print(f"    check_centerline exit {report.returncode} "
                  f"({'FAILS as required' if report.returncode else 'PASSES — the bracket is dead'})")
    finally:
        FACTORY.write_text(good)
        shutil.copystat(FACTORY, FACTORY)


if __name__ == "__main__":
    main()
