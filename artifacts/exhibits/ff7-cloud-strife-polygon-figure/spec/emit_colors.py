#!/usr/bin/env python3
"""prompt.txt §2's colour table — hand the part factories their colours, as generated TS.

    python3 spec/emit_colors.py    # rewrites src/utils/cloudStrifeFigure/colors.ts

Same discipline as emit_measurements.py, applied to the colour axis: a factory may not
type a hex literal, it imports a generated module, and the module is generated from
spec/palette.json (§0.6 — spec/sample_palette.py's output wins over the hand-written table
in prompt.txt where the two disagree, so this reads palette.json, not the prompt).

Re-run this whenever spec/sample_palette.py changes. The generated file is checked in for
the same reason measurements.ts is: the build must not depend on artifacts/.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OUT = REPO / "src/utils/cloudStrifeFigure/colors.ts"

PALETTE = json.loads((HERE / "palette.json").read_text())
CODES = PALETTE["codes"]


def main() -> None:
    lines = [
        "// GENERATED FILE — do not edit.",
        "//",
        "// Source: artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/palette.json",
        "// Writer: artifacts/exhibits/ff7-cloud-strife-polygon-figure/spec/emit_colors.py",
        "//",
        "// prompt.txt §2's colour table (C-xx), sampled by clustering, identified by",
        "// position — never by eye-dropper. Every value is the pixel-count weighted mean",
        "// over the four cool orthographic views (front/back/left/right); §2 explains why",
        "// the cool set is adopted over the warm more-angle reference.",
        "",
        "/** C-xx -> adopted hex. C-09 (printed face) is a texture, not a flat colour —",
        " * absent here on purpose; Stage 2's faceDecal owns it. */",
        "export const COLORS = {",
    ]
    for code, entry in CODES.items():
        adopted = entry.get("adopted")
        if adopted is None:
            continue
        content = entry.get("content", "")
        lines.append(f'  "{code}": "{adopted}", // {content}')
    lines += [
        "} as const;",
        "",
    ]
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT.relative_to(REPO)} ({len(lines)} lines, {len([c for c in CODES.values() if c.get('adopted')])} codes)")


if __name__ == "__main__":
    main()
