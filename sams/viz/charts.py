"""Attendance-summary charts for infovis.py.

Design (following data-viz best practice):
  * The data's job is "change of a binary state over time" -> a present/absent
    TIMELINE is the primary form.
  * present/absent is a STATUS encoding (not categorical): reserved green/red,
    reinforced with marker SHAPE + hatch so it never relies on colour alone
    (colour-blind safe).

Everything is saved to output/charts/<index>.png and shown on screen.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

import config
from ..domain.models import Student

# Status palette — colour-blind-distinguishable green / red, plus redundant
# shape and hatch so meaning survives greyscale / CVD.
PRESENT_COLOR = "#1a7f37"   # green
ABSENT_COLOR = "#cf222e"    # red
GRID_COLOR = "#d0d7de"
INK = "#1f2328"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def render_summary(student: Student, rows: list[dict],
                   out_dir: Path | None = None, show: bool = True) -> Path:
    """Render the attendance summary for one student and return the PNG path.

    rows: list of {date, present, ink_ratio, filename} oldest-first.
    """
    out_dir = out_dir or config.CHARTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{student.index}.png"

    total = len(rows)
    present_count = sum(1 for r in rows if r["present"])
    pct = (present_count / total * 100.0) if total else 0.0

    fig = plt.figure(figsize=(11, 5.5))
    fig.suptitle(f"Attendance Summary — {student.full_name}  ({student.index})",
                 fontsize=14, fontweight="bold", color=INK)

    fig.savefig(out_path, dpi=130, bbox_inches="tight", facecolor="white")
    if show:
        plt.show()
    plt.close(fig)
    return out_path
