"""Best-effort date extraction from a sheet image filename.

Handles ISO names (2019-07-12.jpeg).
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# ISO: yyyy-mm-dd (year first, 4 digits).
_ISO_RE = re.compile(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})")


def date_from_filename(path: str | Path) -> date | None:
    # Use the bare filename (not .stem): a dotted date like "28.6.2019.png"
    # would otherwise have ".2019" stripped as if it were the extension.
    stem = Path(path).name

    m = _ISO_RE.search(stem)
    if m:
        year, month, day = (int(g) for g in m.groups())
        return _safe_date(year, month, day)

    return None


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None
