"""Tests for date extraction from sheet filenames."""
from datetime import date

import pytest

from sams.util.dates import date_from_filename


@pytest.mark.parametrize("name,expected", [
    ("2019-05-31.jpeg", date(2019, 5, 31)),   # ISO
    ("2019-07-12.jpeg", date(2019, 7, 12)),   # ISO
    ("12.07.2019.png", date(2019, 7, 12)),    # brief example (day-first, dots)
    ("28.6.2019.png", date(2019, 6, 28)),     # single-digit month, dotted
    ("31.05.2019.jpeg", date(2019, 5, 31)),   # day-first, dots
    ("data/sheets/2019-06-21.jpeg", date(2019, 6, 21)),  # with directory
])
def test_date_from_filename(name, expected):
    assert date_from_filename(name) == expected


def test_no_date_returns_none():
    assert date_from_filename("sheet_unknown.png") is None


def test_iso_not_misread_as_day_first():
    # Regression: 2019-05-31 must NOT be read as day=19, month=05, year=31.
    assert date_from_filename("2019-05-31.jpeg") == date(2019, 5, 31)
