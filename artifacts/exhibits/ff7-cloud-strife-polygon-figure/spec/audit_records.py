#!/usr/bin/env python3
"""prompt.txt §3.5 / §0.6 — every figure in a record must come from an artefact.

    python3 audit_records.py                 # audit the default record set
    python3 audit_records.py <file> [...]    # audit specific files

Ported from artifacts/exhibits/ff7-cloud-strife-ultima-weapon/spec/audit_records.py.
That version is a hand-written cross-check of ONE model's specific quantities; what
carries over is its reason for existing, not its body:

    the records are long and they cite each other, which is exactly how a number
    drifts — someone corrects the model, updates one report, and the other three keep
    quoting the old value.

So this port is generic where the original was bespoke. It harvests every number that
a MEASUREMENT ARTEFACT produced (the `*.json` written by the Stage 0 scripts, plus the
TypeScript part factories once they exist) and then reads the RECORDS (the sculpt spec
and the prose under ART/) asking one question per figure: did anything actually produce
this? A figure nothing produced is either a typo or a value that has moved on, and both
are the same defect.

Exit 1 with file, line and text for every unsourced figure. Until this runs clean §0.6
is exhortation, not a gate.

Pure stdlib.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ART = Path(__file__).resolve().parent.parent
REPO = ART.parent.parent.parent
FACTORY_DIR = REPO / "src/utils/cloudStrifeFigure"

# Sources of truth: anything a script wrote, plus the code the model is actually built
# from. prompt.txt is NOT a source — §0.6 puts the prompt's own numbers under the same
# rule as everything else.
ARTEFACT_GLOBS = [(ART / "spec", "*.json"), (FACTORY_DIR, "*.ts")]

# Records: documents that QUOTE figures. The spec is the important one; the prose is
# audited too because that is where the ultima drift actually happened.
RECORD_PATHS = [ART / "spec" / "object-sculpt-spec.json"]
RECORD_GLOBS = [(ART, "*.md")]

# Blocks of the sculpt spec that a FORGE SCRIPT writes, not the author: gate results,
# review entries, render hashes. Their figures are produced by the tool that appended them,
# so they are sources in their own right rather than quotes to be traced. Auditing them
# would only ever fire on the reviewer's own evidence.
MACHINE_WRITTEN = ("tier1Results", "reviewHistory", "visualEvidence")

NUMBER = re.compile(r"-?\d+\.\d+|-?\d{3,}")
HEXCOL = re.compile(r"#[0-9A-Fa-f]{6}\b|0x[0-9A-Fa-f]{6}\b")
TOLERANCE = 5e-7  # a quoted figure must match an artefact's value, not merely be near it

# Three things look like figures and are not. Without these the audit drowns in its own
# false positives - the first run over the sculpt spec reported 354 unsourced figures, of
# which every single one in this class was a section number or a JSON escape.
JSON_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")   # "—" is an em dash, not the year 2014
SECTION_REF = re.compile(r"§\s?\d+(\.\d+)*")  # "§5.5" is prompt.txt section 5.5
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")        # "2026-08-13" is a date, not a measurement
VERSION_KEY = re.compile(r"\"\w*[Vv]ersion\"\s*:\s*\"?[\d.]+\"?")  # schemaVersion 2.1


def _walk(node, out: list[float]) -> None:
    if isinstance(node, bool):
        return
    if isinstance(node, (int, float)):
        out.append(float(node))
    elif isinstance(node, dict):
        for k, v in node.items():
            _walk(k, out)
            _walk(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk(v, out)
    elif isinstance(node, str):
        for m in NUMBER.findall(node):
            out.append(float(m))


def harvest() -> tuple[set[float], set[str], list[str]]:
    nums: list[float] = []
    hexes: set[str] = set()
    sources: list[str] = []
    for base, pattern in ARTEFACT_GLOBS:
        if not base.exists():
            continue
        for path in sorted(base.glob(pattern)):
            if path in RECORD_PATHS:
                continue
            sources.append(str(path.relative_to(REPO)))
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".json":
                try:
                    _walk(json.loads(text), nums)
                except json.JSONDecodeError:
                    nums += [float(m) for m in NUMBER.findall(text)]
            else:
                nums += [float(m) for m in NUMBER.findall(text)]
            hexes |= {m.upper().replace("0X", "#") for m in HEXCOL.findall(text)}
    for record in RECORD_PATHS:
        if record.suffix != ".json" or not record.exists():
            continue
        doc = json.loads(record.read_text(encoding="utf-8"))
        for key in MACHINE_WRITTEN:
            if key in doc:
                _walk(doc[key], nums)
    return set(nums), hexes, sources


def quoted(path: Path) -> list[tuple[int, str, str]]:
    """(line number, token, kind) for every figure a record quotes.

    Section references, ISO dates and JSON \\uXXXX escapes are masked out first: they carry
    digits without being measurements, and auditing them turns the gate into noise.
    """
    out = []
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = JSON_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), raw)
        masked = ISO_DATE.sub(lambda m: " " * len(m.group(0)), line)
        masked = SECTION_REF.sub(lambda m: " " * len(m.group(0)), masked)
        masked = VERSION_KEY.sub(lambda m: " " * len(m.group(0)), masked)
        for m in HEXCOL.finditer(masked):
            out.append((i, m.group(0), "hex"))
        for m in NUMBER.finditer(masked):
            # A hex colour contains digit runs; do not audit them twice.
            if any(a.start() <= m.start() < a.end() for a in HEXCOL.finditer(masked)):
                continue
            out.append((i, m.group(0), "num"))
    return out


def sourced(token: str, kind: str, nums: set[float], hexes: set[str]) -> bool:
    if kind == "hex":
        return token.upper().replace("0X", "#") in hexes
    value = float(token)
    if any(abs(value - n) <= TOLERANCE for n in nums):
        return True
    # A record legitimately quotes a rounded artefact value ("IoU 0.8608" from
    # 0.86083...). Accept a figure that matches an artefact value AT THE PRECISION IT
    # WAS QUOTED TO, and only at that precision — this is what separates rounding from
    # a number nothing produced.
    dp = len(token.split(".")[1]) if "." in token else 0
    return any(round(n, dp) == value for n in nums)


def main(argv: list[str]) -> int:
    nums, hexes, sources = harvest()
    records = [Path(a) for a in argv] if argv else list(RECORD_PATHS)
    if not argv:
        for base, pattern in RECORD_GLOBS:
            records += sorted(p for p in base.rglob(pattern) if "_stale" not in p.parts)
    records = [p for p in records if p.exists()]

    print(f"artefacts: {len(sources)} file(s), {len(nums)} distinct figures, {len(hexes)} colours")
    for s in sources:
        print(f"  source  {s}")
    if not records:
        print("records:   none yet (no sculpt spec, no prose) — nothing to audit")
        return 0

    fail = []
    for path in records:
        checked = 0
        for line, token, kind in quoted(path):
            checked += 1
            if not sourced(token, kind, nums, hexes):
                fail.append((path, line, token))
        print(f"  record  {path.relative_to(REPO)}  ({checked} figures)")
    for path, line, token in fail:
        print(f"UNSOURCED {path.relative_to(REPO)}:{line}  {token}", file=sys.stderr)
    print(f"{len(fail)} unsourced figure(s)")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
