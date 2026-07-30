#!/usr/bin/env python
"""investigate.py — signature recognition entry point (bonus component).

Usage:
    python investigate.py <student_index>

Example (from the brief):
    python investigate.py 001
    python investigate.py 10000409

Extracts the given student's signature from each processed sheet and compares
it against that student's REFERENCE signatures in
data/reference_signatures/<index>/. Reports, per sheet, whether the signature
is consistent with the reference set (possible mismatch / forgery otherwise).

Reference signatures must be collected beforehand (crop them from known-good
sheets or scans). Without references, this reports that none are on file.

OWNER: Recognition & QA Engineer.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

import config
from sams.data.database import bootstrap, connect
from sams.data.repository import AttendanceRepository
from sams.domain.roster import RosterParser
from sams.pipeline import build_default_pipeline
from sams.pipeline.base import PipelineContext
from sams.recognition.matcher import SignatureMatcher


def _extract_signature(image_path: str, roster, row_index: int):
    """Re-run the pipeline on a sheet and return the crop for a given row."""
    ctx = PipelineContext(source_path=image_path, roster=roster)
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        return None
    build_default_pipeline().run(image, ctx)
    if row_index < len(ctx.cells):
        return ctx.cells[row_index].crop
    return None


def run(index: str, xml_path: str) -> int:
    config.ensure_dirs()

    # Resolve student + their roster row.
    roster = RosterParser.parse(xml_path)
    student = RosterParser.find_student(roster, index)
    if student is None:
        print(f"ERROR: no student matching '{index}' in {xml_path}", file=sys.stderr)
        return 1
    row_index = roster.index(student)

    ref_dir = config.REFERENCE_DIR / student.index
    matcher = SignatureMatcher()

    # Which sheets have we processed? Pull filenames from the DB.
    conn = connect()
    bootstrap(conn)
    repo = AttendanceRepository(conn)
    rows = repo.attendance_for(student.index)
    conn.close()

    print(f"Signature investigation — {student.full_name} ({student.index})")
    print(f"reference dir: {ref_dir}")
    print("-" * 60)

    if not rows:
        print("No processed sheets in the DB. Run sams.py on the sheets first.")
        return 0

    for r in rows:
        sheet_file = r["filename"]
        if not sheet_file or not Path(sheet_file).exists():
            print(f"  {r['date']}: sheet image '{sheet_file}' not found — skipped")
            continue
        crop = _extract_signature(sheet_file, roster, row_index)
        if crop is None or crop.size == 0:
            print(f"  {r['date']}: could not extract signature — skipped")
            continue
        result = matcher.compare_to_references(crop, ref_dir)
        verdict = "MATCH   " if result.is_match else "MISMATCH"
        print(f"  {r['date']}: {verdict}  score={result.score:.3f}  ({result.detail})")

    print("-" * 60)
    print("Note: MISMATCH may mean absent, a different pen/signature, or forgery.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Investigate/verify a student's signatures across sheets.")
    parser.add_argument("index", help="student index, e.g. 001 or 10000409")
    parser.add_argument("--xml", default=str(config.INFO_XML),
                        help="roster file (default: data/info.xml)")
    args = parser.parse_args()
    return run(args.index, args.xml)


if __name__ == "__main__":
    raise SystemExit(main())
