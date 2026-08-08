"""Central configuration for the CGV Signature Tracker.

Keeping thresholds and paths here (instead of scattered through the code)
satisfies the "configuration over hard-coding" principle and makes the
pipeline easy to tune on the five sample sheets.
"""
from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent

DATA_DIR = ROOT / "data"
SHEETS_DIR = DATA_DIR / "sheets"
INFO_XML = DATA_DIR / "info.xml"
REFERENCE_DIR = DATA_DIR / "reference_signatures"

OUTPUT_DIR = ROOT / "output"
STEPS_DIR = OUTPUT_DIR / "steps"      # per-stage snapshots (for the report)
CHARTS_DIR = OUTPUT_DIR / "charts"    # infovis.py output
REPORTS_DIR = OUTPUT_DIR / "reports"  # investigate.py text reports

DB_PATH = ROOT / "attendance.db"

# --------------------------------------------------------------------------- #
# Image processing
# --------------------------------------------------------------------------- #
# Resize very large phone photos down to this working width (keeps aspect ratio).
WORKING_WIDTH = 1600

# Adaptive threshold parameters (cv2.adaptiveThreshold).
ADAPTIVE_BLOCK_SIZE = 25   # odd number; neighbourhood size
ADAPTIVE_C = 10            # constant subtracted from the mean

# Morphology kernel scale for table-line detection.
# The horizontal kernel length = image_width // H_LINE_SCALE, etc.
H_LINE_SCALE = 30
V_LINE_SCALE = 30

# Expected sheet layout (the real signing sheets).
EXPECTED_STUDENT_ROWS = 6          # 6 students per sheet
SIGNATURE_COLUMN_INDEX = -1        # signature is the right-most column

# --------------------------------------------------------------------------- #
# Presence decision
# --------------------------------------------------------------------------- #
# A signature cell is "present" if the ratio of ink pixels to cell area
# exceeds this threshold. Tune against the five sample sheets.
PRESENCE_THRESHOLD = 0.020

# Ignore connected components smaller than this many pixels (stray specks).
MIN_INK_COMPONENT_AREA = 15

# --------------------------------------------------------------------------- #
# Recognition (investigate.py)
# --------------------------------------------------------------------------- #
# A detected signature matches a reference if the NCC shape-similarity exceeds
# this. Tuned on the five sample sheets: genuine same-student pairs score ~0.23
# and above, while different-student / non-signature marks score lower.
# Signature verification on small phone-photo crops is inherently fuzzy, so this
# is an indicative threshold, not a hard biometric guarantee.
MATCH_THRESHOLD = 0.22

# --------------------------------------------------------------------------- #
# Behaviour
# --------------------------------------------------------------------------- #
SHOW_WINDOWS = False   # if True, cv2.imshow each stage live; snapshots always saved
SAVE_SNAPSHOTS = True


def ensure_dirs() -> None:
    """Create all output directories if they do not exist."""
    for d in (OUTPUT_DIR, STEPS_DIR, CHARTS_DIR, REPORTS_DIR,
              SHEETS_DIR, REFERENCE_DIR):
        d.mkdir(parents=True, exist_ok=True)
