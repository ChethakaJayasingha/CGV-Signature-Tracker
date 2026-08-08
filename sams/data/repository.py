"""AttendanceRepository — the single place that reads/writes attendance SQL.

No other layer touches SQL directly. This keeps persistence swappable and the
rest of the codebase clean (repository pattern → OOP marks).
"""
from __future__ import annotations

import csv
import sqlite3
from datetime import date
from pathlib import Path

import config

from ..domain.models import Attendance, Student

# Column order of the admin CSV export (also its header row).
CSV_FIELDS = ["index_no", "title", "name", "sheets", "present", "percentage"]


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

    # ---- queries (used by infovis.py) ----------------------------------- #
    def attendance_for(self, student_no: str) -> list[dict]:
        """Return a student's attendance across all sheets, oldest first.

        Each dict: {date, present, ink_ratio, filename}.
        """
        cur = self.conn.execute(
            """SELECT s.date AS date, a.present AS present,
                      a.ink_ratio AS ink_ratio, s.filename AS filename
               FROM attendance a
               JOIN sheet s ON s.id = a.sheet_id
               WHERE a.student_no = ?
               ORDER BY s.date ASC;""",
            (student_no,),
        )
        return [dict(r) for r in cur.fetchall()]

    def student(self, student_no: str) -> Student | None:
        cur = self.conn.execute(
            "SELECT index_no, title, name FROM student WHERE index_no = ?;",
            (student_no,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return Student(index=row["index_no"], title=row["title"], name=row["name"])

    def resolve_index(self, partial: str) -> str | None:
        """Resolve a possibly-short index (e.g. '409') to a stored full index."""
        cur = self.conn.execute(
            """SELECT index_no FROM student
               WHERE index_no = ? OR index_no LIKE ?
               ORDER BY length(index_no) LIMIT 1;""",
            (partial, f"%{partial}"),
        )
        row = cur.fetchone()
        return row["index_no"] if row else None

    # ---- class-wide reporting ------------------------------------------- #
    def class_summary(self) -> list[dict]:
        """Attendance percentage per student across every processed sheet.

        LEFT JOIN from student, so a student who has not appeared on any
        processed sheet yet still shows up (at 0%) instead of silently
        vanishing from the class view. Ordered by index so the result keeps
        the roster's row order.

        Each dict: {index_no, title, name, sheets, present, percentage}.
        """
        cur = self.conn.execute(
            """SELECT s.index_no AS index_no, s.title AS title, s.name AS name,
                      COUNT(a.id) AS sheets,
                      COALESCE(SUM(a.present), 0) AS present
               FROM student s
               LEFT JOIN attendance a ON a.student_no = s.index_no
               GROUP BY s.index_no
               ORDER BY s.index_no ASC;"""
        )
        summary: list[dict] = []
        for row in cur.fetchall():
            sheets = int(row["sheets"])
            present = int(row["present"])
            summary.append({
                "index_no": row["index_no"],
                "title": row["title"],
                "name": row["name"],
                "sheets": sheets,
                "present": present,
                "percentage": round(present / sheets * 100.0, 1) if sheets else 0.0,
            })
        return summary

    def export_csv(self, out_path: str | Path | None = None) -> Path:
        """Write the class summary to a CSV admin staff can open in Excel.

        Reuses class_summary() rather than issuing a second query. Defaults to
        output/reports/attendance_export.csv. The newline="" is the csv
        module's required idiom — without it Excel shows a blank row between
        every record on Windows.
        """
        if out_path is None:
            out_path = config.REPORTS_DIR / "attendance_export.csv"
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(self.class_summary())
        return path
