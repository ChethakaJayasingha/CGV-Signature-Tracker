from __future__ import annotations

import argparse
import sys

import cv2

import config
from sams.data.database import bootstrap, connect
from sams.data.repository import AttendanceRepository
from sams.domain.models import Attendance
from sams.domain.roster import RosterParser
from sams.pipeline import build_default_pipeline
from sams.pipeline.base import PipelineContext
from sams.util.dates import date_from_filename
from sams.util.logging import Console


def run(image_path: str, xml_path: str) -> int:
    config.ensure_dirs()
    Console.header(f"SAMS — processing {image_path}")

    # 1. Roster 
    roster = RosterParser.parse(xml_path)
    Console.info(f"roster: {len(roster)} students from {xml_path}")

    # 2. DB 
    conn = connect()
    bootstrap(conn)
    repo = AttendanceRepository(conn)
    repo.upsert_students(roster)

    # 3. Pipeline
    sheet_date = date_from_filename(image_path)
    ctx = PipelineContext(source_path=image_path, roster=roster,
                          sheet_date=sheet_date)
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        print(f"ERROR: cannot read image '{image_path}'", file=sys.stderr)
        return 2

    pipeline = build_default_pipeline()
    pipeline.run(image, ctx)

    # 4. Attribute cells to students (both are top-to-bottom ordered)
    if len(ctx.cells) != len(roster):
        Console.info(f"WARNING: {len(ctx.cells)} cells vs {len(roster)} students "
                     f"— attributing by row order; verify cell extraction.")

    records: list[Attendance] = []
    print()
    print("  Result")
    print("  " + "-" * 54)
    for i, student in enumerate(roster):
        if i < len(ctx.cells):
            cell = ctx.cells[i]
            present, ratio = cell.present, cell.ink_ratio
        else:
            present, ratio = False, 0.0
        records.append(Attendance(student.index, sheet_date, present, ratio))
        mark = "PRESENT" if present else "ABSENT "
        print(f"  {student.index:>10}  {mark}  ({ratio:.3f})  {student.name}")
    print("  " + "-" * 54)

    # 5. Persist 
    sheet_id = repo.upsert_sheet(image_path, sheet_date, ctx.hall)
    repo.upsert_attendance(sheet_id, records)
    Console.result(f"stored {len(records)} attendance records "
                   f"(sheet id {sheet_id}) in {config.DB_PATH.name}")
    Console.info(f"step images saved to {config.STEPS_DIR}")

    conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Process a signing-sheet image and record attendance.")
    parser.add_argument("image", help="signing-sheet image, e.g. 10.07.2019.png")
    parser.add_argument("xml", help="roster file, e.g. info.xml")
    args = parser.parse_args()
    return run(args.image, args.xml)


if __name__ == "__main__":
    raise SystemExit(main())
