#!/usr/bin/env python
"""collect_references.py — build the reference-signature library.

The signature-recognition component (investigate.py) needs known-genuine
signatures for each student. The most reliable source is the signing sheets
themselves: on the sheets where a student signed, that crop IS their genuine
signature.

This helper runs the image-processing pipeline on each sheet, extracts every
student's signature cell, and saves the ones that contain a genuine signature
(present cells) to:

    data/reference_signatures/<student_index>/<sheet_date>.png

Cells that are absent (below the presence threshold) are skipped, so blank
cells and "absent" marks are not stored as references.

Usage:
    python collect_references.py                 # all sheets in data/sheets/
    python collect_references.py --exclude 2019-06-21   # hold a sheet out

Holding a sheet out is useful for testing: collect references from the other
sheets, then run investigate.py to see whether the held-out sheet's signatures
still match (they should) and whether a non-signature mark does not.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

import config
from sams.domain.roster import RosterParser
from sams.pipeline import build_default_pipeline
from sams.pipeline.base import PipelineContext
from sams.util.dates import date_from_filename


def run(exclude: list[str], xml_path: str) -> int:
    config.ensure_dirs()
    roster = RosterParser.parse(xml_path)

    sheets = sorted(config.SHEETS_DIR.glob("*.jpeg")) + \
        sorted(config.SHEETS_DIR.glob("*.png")) + \
        sorted(config.SHEETS_DIR.glob("*.jpg"))
    sheets = [s for s in sheets if s.stem not in exclude]
    if not sheets:
        print("No sheets found in data/sheets/.", file=sys.stderr)
        return 1

    saved = 0
    skipped = 0
    print(f"Collecting reference signatures from {len(sheets)} sheet(s)")
    print("-" * 60)

    for sheet_path in sheets:
        date = date_from_filename(sheet_path)
        tag = date.isoformat() if date else sheet_path.stem

        ctx = PipelineContext(source_path=str(sheet_path), roster=roster)
        image = cv2.imread(str(sheet_path), cv2.IMREAD_COLOR)
        if image is None:
            print(f"  {sheet_path.name}: cannot read — skipped")
            continue
        build_default_pipeline().run(image, ctx)

        for i, student in enumerate(roster):
            if i >= len(ctx.cells):
                continue
            cell = ctx.cells[i]
            if not cell.present:
                skipped += 1
                continue  # do not store blank / absent cells as references
            out_dir = config.REFERENCE_DIR / student.index
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{tag}.png"
            cv2.imwrite(str(out_path), cell.crop)
            saved += 1

        print(f"  {sheet_path.name}: processed")

    print("-" * 60)
    print(f"Saved {saved} reference signatures; skipped {skipped} absent cells.")
    print(f"References stored under: {config.REFERENCE_DIR}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect genuine reference signatures from the sheets.")
    parser.add_argument("--exclude", nargs="*", default=[],
                        help="sheet stems to hold out, e.g. 2019-06-21")
    parser.add_argument("--xml", default=str(config.INFO_XML),
                        help="roster file (default: data/info.xml)")
    args = parser.parse_args()
    return run(args.exclude, args.xml)


if __name__ == "__main__":
    raise SystemExit(main())
