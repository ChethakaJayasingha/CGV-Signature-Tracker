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

import matplotlib
import matplotlib.pyplot as plt

# Status palette — colour-blind-distinguishable green / red, plus redundant
# shape and hatch so meaning survives greyscale / CVD.
PRESENT_COLOR = "#1a7f37"   # green
ABSENT_COLOR = "#cf222e"    # red
GRID_COLOR = "#d0d7de"
INK = "#1f2328"
