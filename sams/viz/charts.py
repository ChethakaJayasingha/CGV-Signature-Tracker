"""Attendance-summary charts for infovis.py.

Design (following data-viz best practice):
  * The data's job is "change of a binary state over time" -> a present/absent
    TIMELINE is the primary form.
  * A headline attendance PERCENTAGE (hero number) answers "how are they doing?"
    at a glance.
  * A small donut shows the present/absent split.
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

    gs = fig.add_gridspec(2, 2, width_ratios=[2.3, 1], height_ratios=[1, 1.3],
                          hspace=0.45, wspace=0.3)

    # --- Hero number: attendance percentage ------------------------------ #
    ax_hero = fig.add_subplot(gs[0, 0])
    ax_hero.axis("off")
    hero_color = PRESENT_COLOR if pct >= 50 else ABSENT_COLOR
    ax_hero.text(0.0, 0.6, f"{pct:.0f}%", fontsize=44, fontweight="bold",
                 color=hero_color, ha="left", va="center")
    ax_hero.text(0.0, 0.12, f"present on {present_count} of {total} sheets",
                 fontsize=11, color=INK, ha="left", va="center")

    # --- Donut: present vs absent split ---------------------------------- #
    ax_donut = fig.add_subplot(gs[0, 1])
    absent_count = total - present_count
    if total:
        wedges, _ = ax_donut.pie(
            [present_count, absent_count],
            colors=[PRESENT_COLOR, ABSENT_COLOR],
            startangle=90, counterclock=False,
            wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
        )
        # Redundant hatch so the split is readable without colour.
        if wedges:
            wedges[0].set_hatch("")     # present: solid
            if len(wedges) > 1:
                wedges[1].set_hatch("////")  # absent: hatched
    ax_donut.set_title("Present vs Absent", fontsize=10, color=INK)
    ax_donut.text(0, 0, f"{present_count}/{total}", ha="center", va="center",
                  fontsize=12, fontweight="bold", color=INK)

    # --- Timeline: present/absent per sheet date ------------------------- #
    ax_tl = fig.add_subplot(gs[1, :])
    if total:
        labels = [(_parse_date(r["date"]).strftime("%d %b")
                   if _parse_date(r["date"]) else (r["filename"] or f"#{i+1}"))
                  for i, r in enumerate(rows)]
        xs = list(range(total))
        ys = [1 if r["present"] else 0 for r in rows]

        # Connecting step line (recessive) to show the sequence.
        ax_tl.step(xs, ys, where="mid", color=GRID_COLOR, linewidth=2, zorder=1)

        for x, y, r in zip(xs, ys, rows):
            present = r["present"]
            ax_tl.scatter(
                x, y,
                s=180,
                color=PRESENT_COLOR if present else ABSENT_COLOR,
                marker="o" if present else "X",   # redundant shape
                edgecolors="white", linewidths=1.5, zorder=3,
            )
            ax_tl.annotate("Present" if present else "Absent", (x, y),
                           textcoords="offset points", xytext=(0, 12),
                           ha="center", fontsize=8,
                           color=PRESENT_COLOR if present else ABSENT_COLOR)

        ax_tl.set_yticks([0, 1])
        ax_tl.set_yticklabels(["Absent", "Present"])
        ax_tl.set_ylim(-0.5, 1.5)
        ax_tl.set_xticks(xs)
        ax_tl.set_xticklabels(labels)
        ax_tl.set_xlabel("Signing-sheet date")
    else:
        ax_tl.text(0.5, 0.5, "No attendance records for this student yet.",
                   ha="center", va="center", fontsize=11, color=ABSENT_COLOR)
        ax_tl.axis("off")

    ax_tl.set_title("Attendance timeline", fontsize=10, color=INK)
    for spine in ("top", "right"):
        ax_tl.spines[spine].set_visible(False)
    ax_tl.grid(axis="y", color=GRID_COLOR, linewidth=0.8, alpha=0.6)
    ax_tl.set_axisbelow(True)

    fig.savefig(out_path, dpi=130, bbox_inches="tight", facecolor="white")
    if show:
        plt.show()
    plt.close(fig)
    return out_path
