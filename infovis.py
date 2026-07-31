#!/usr/bin/env python
"""infovis.py — attendance visualization entry point.

Usage:
    python infovis.py <student_index>

Example (from the brief):
    python infovis.py 001
    python infovis.py 10000409

Reads the attendance stored by sams.py and renders a summary graph for the
given student (attendance %, present/absent donut, and a per-date timeline).
Saves to output/charts/<index>.png and shows it on screen.
"""
from __future__ import annotations

import argparse
import sys

import config
from sams.data.database import bootstrap, connect
from sams.data.repository import AttendanceRepository
from sams.viz.charts import render_summary


def run(index: str, show: bool = True) -> int:
    config.ensure_dirs()

    conn = connect()
    bootstrap(conn)
    repo = AttendanceRepository(conn)

    full_index = repo.resolve_index(index)
    if full_index is None:
        print(f"ERROR: no student matching '{index}' in the database. "
              f"Run sams.py on at least one sheet first.", file=sys.stderr)
        return 1

    student = repo.student(full_index)
    rows = repo.attendance_for(full_index)
    if not rows:
        print(f"No attendance records for {student.full_name} ({full_index}) yet.",
              file=sys.stderr)

    out_path = render_summary(student, rows, show=show)
    print(f"Chart saved to {out_path}")
    conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Visualize a student's attendance summary.")
    parser.add_argument("index", help="student index, e.g. 001 or 10000409")
    parser.add_argument("--no-show", action="store_true",
                        help="save the chart without opening a window")
    args = parser.parse_args()
    return run(args.index, show=not args.no_show)


if __name__ == "__main__":
    raise SystemExit(main())
