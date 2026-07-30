"""Shared pytest fixtures and path setup.

Ensures the project root is importable so `import config` / `import sams`
work when tests are run from anywhere.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
