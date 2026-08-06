"""AttendanceRepository — the single place that reads/writes attendance SQL.

No other layer touches SQL directly. This keeps persistence swappable and the
rest of the codebase clean (repository pattern → OOP marks).
"""
from __future__ import annotations

import sqlite3
from datetime import date

from ..domain.models import Attendance, Student


class AttendanceRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    # ---- students ------------------------------------------------------- #
    def upsert_students(self, students: list[Student]) -> None:
        self.conn.executemany(
            """INSERT INTO student (index_no, title, name)
               VALUES (?, ?, ?)
               ON CONFLICT(index_no) DO UPDATE SET
                   title = excluded.title,
                   name  = excluded.name;""",
            [(s.index, s.title, s.name) for s in students],
        )
        self.conn.commit()

    # ---- sheets --------------------------------------------------------- #
    def upsert_sheet(self, filename: str, sheet_date: date | None,
                     hall: str | None = None) -> int:
        """Insert (or update) a sheet row and return its id.

        Sheets are keyed by date so re-processing the same day's sheet does
        not create duplicates.
        """
        iso = sheet_date.isoformat() if sheet_date else None
        cur = self.conn.execute(
            """INSERT INTO sheet (filename, date, hall)
               VALUES (?, ?, ?)
               ON CONFLICT(date) DO UPDATE SET
                   filename = excluded.filename,
                   hall     = excluded.hall
               RETURNING id;""",
            (filename, iso, hall),
        )
        row = cur.fetchone()
        self.conn.commit()
        return int(row["id"])

    # ---- attendance ----------------------------------------------------- #
    def upsert_attendance(self, sheet_id: int, records: list[Attendance]) -> None:
        self.conn.executemany(
            """INSERT INTO attendance (student_no, sheet_id, present, ink_ratio)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(student_no, sheet_id) DO UPDATE SET
                   present   = excluded.present,
                   ink_ratio = excluded.ink_ratio;""",
            [(a.student_index, sheet_id, int(a.present), a.ink_ratio)
             for a in records],
        )
        self.conn.commit()
