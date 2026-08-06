"""AttendanceRepository — the single place that reads/writes attendance SQL.

No other layer touches SQL directly. This keeps persistence swappable and the
rest of the codebase clean (repository pattern → OOP marks).
"""
from __future__ import annotations

import sqlite3

from ..domain.models import Student


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
