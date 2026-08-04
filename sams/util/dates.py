"""Best-effort date extraction from a sheet image filename.

Handles both ISO names (2019-07-12.jpeg) and the brief's day-first formats
(12.07.2019, 05/07/2019, 28.6.2019, 31/05/2019). ISO is tried first because a
four-digit leading group unambiguously identifies a yyyy-mm-dd date.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# ISO: yyyy-mm-dd (year first, 4 digits).
_ISO_RE = re.compile(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})")
# Day-first: dd-mm-yyyy (year last, 2-4 digits).
_DMY_RE = re.compile(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})")


def date_from_filename(path: str | Path) -> date | None:
    # Use the bare filename (not .stem): a dotted date like "28.6.2019.png"
    # would otherwise have ".2019" stripped as if it were the extension.
    stem = Path(path).name

    m = _ISO_RE.search(stem)
    if m:
        year, month, day = (int(g) for g in m.groups())
        return _safe_date(year, month, day)

    m = _DMY_RE.search(stem)
    if m:
        day, month, year = (int(g) for g in m.groups())
        if year < 100:
            year += 2000
        return _safe_date(year, month, day)

    return None


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None
