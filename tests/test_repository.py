"""Tests for the SQLite attendance repository (uses an in-memory DB)."""
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


def test_upsert_students_then_lookup(repo, students):
    repo.upsert_students(students)
    s = repo.student("10000409")
    assert s is not None and s.name == "M S Dilshanika Perera"


def test_resolve_partial_index(repo, students):
    repo.upsert_students(students)
    assert repo.resolve_index("409") == "10000409"
    assert repo.resolve_index("10009301") == "10009301"
    assert repo.resolve_index("999999") is None


def test_attendance_roundtrip_and_ordering(repo, students):
    repo.upsert_students(students)
    s1 = repo.upsert_sheet("b.png", date(2019, 7, 12))
    s2 = repo.upsert_sheet("a.png", date(2019, 5, 31))

    repo.upsert_attendance(s1, [Attendance("10000409", date(2019, 7, 12), True, 0.05)])
    repo.upsert_attendance(s2, [Attendance("10000409", date(2019, 5, 31), False, 0.001)])

    rows = repo.attendance_for("10000409")
    assert len(rows) == 2
    # ordered oldest-first
    assert rows[0]["date"] == "2019-05-31"
    assert rows[1]["date"] == "2019-07-12"
    assert bool(rows[1]["present"]) is True


def test_reprocessing_sheet_updates_not_duplicates(repo, students):
    repo.upsert_students(students)
    sid = repo.upsert_sheet("x.png", date(2019, 7, 12))
    repo.upsert_attendance(sid, [Attendance("10000409", date(2019, 7, 12), False, 0.0)])
    # same student + same sheet again with a new verdict
    repo.upsert_attendance(sid, [Attendance("10000409", date(2019, 7, 12), True, 0.09)])
    rows = repo.attendance_for("10000409")
    assert len(rows) == 1
    assert bool(rows[0]["present"]) is True


def test_sheet_keyed_by_date(repo):
    a = repo.upsert_sheet("first.png", date(2019, 7, 12))
    b = repo.upsert_sheet("second.png", date(2019, 7, 12))  # same date
    assert a == b   # updated, not a new sheet
