"""Tests for the class-wide summary query and the CSV export.

Same in-memory SQLite approach as tests/test_repository.py — no file is
touched except the CSV, which is written into pytest's tmp_path.
"""
import csv
from datetime import date

import pytest

from sams.data.database import bootstrap, connect
from sams.data.repository import AttendanceRepository
from sams.domain.models import Attendance, Student


@pytest.fixture
def repo():
    conn = connect(":memory:")
    bootstrap(conn)
    return AttendanceRepository(conn)


@pytest.fixture
def students():
    return [
        Student("10000409", "Ms", "M S Dilshanika Perera"),
        Student("10009301", "Mr", "C W M A Shehan Abeyrathne"),
    ]


def _two_sheets(repo, index):
    """Mark `index` present on 2019-05-31 and absent on 2019-07-12."""
    s1 = repo.upsert_sheet("a.png", date(2019, 5, 31))
    s2 = repo.upsert_sheet("b.png", date(2019, 7, 12))
    repo.upsert_attendance(s1, [Attendance(index, date(2019, 5, 31), True, 0.07)])
    repo.upsert_attendance(s2, [Attendance(index, date(2019, 7, 12), False, 0.001)])


def test_summary_percentage(repo, students):
    repo.upsert_students(students)
    _two_sheets(repo, "10000409")
    rows = {r["index_no"]: r for r in repo.class_summary()}
    assert rows["10000409"]["sheets"] == 2
    assert rows["10000409"]["present"] == 1
    assert rows["10000409"]["percentage"] == 50.0


def test_summary_includes_student_with_no_sheets(repo, students):
    repo.upsert_students(students)
    _two_sheets(repo, "10000409")
    rows = {r["index_no"]: r for r in repo.class_summary()}
    # 10009301 has never been processed — it must still appear, at 0%,
    # otherwise the class view would quietly lose a student.
    assert rows["10009301"]["sheets"] == 0
    assert rows["10009301"]["present"] == 0
    assert rows["10009301"]["percentage"] == 0.0


def test_summary_keeps_roster_order(repo, students):
    repo.upsert_students(students)
    indices = [r["index_no"] for r in repo.class_summary()]
    assert indices == ["10000409", "10009301"]


def test_summary_survives_reprocessing(repo, students):
    repo.upsert_students(students)
    _two_sheets(repo, "10000409")
    _two_sheets(repo, "10000409")       # the same two sheets processed again
    row = next(r for r in repo.class_summary() if r["index_no"] == "10000409")
    assert row["sheets"] == 2           # not 4
    assert row["percentage"] == 50.0


def test_export_csv_round_trip(repo, students, tmp_path):
    repo.upsert_students(students)
    _two_sheets(repo, "10000409")
    out = repo.export_csv(tmp_path / "attendance_export.csv")

    assert out.exists()
    with out.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    assert [r["index_no"] for r in rows] == ["10000409", "10009301"]
    assert rows[0]["name"] == "M S Dilshanika Perera"
    assert rows[0]["percentage"] == "50.0"
    assert rows[1]["percentage"] == "0.0"


def test_export_csv_creates_missing_directory(repo, students, tmp_path):
    repo.upsert_students(students)
    out = repo.export_csv(tmp_path / "reports" / "attendance_export.csv")
    assert out.exists()
