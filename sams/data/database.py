"""SQLite connection management and schema bootstrap.

SQLite is chosen because it is local, file-based, and zero-config — exactly
matching the brief's requirement to "store the attendance in a local DB".
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import config


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a connection with foreign keys enabled and row access by name."""
    path = str(db_path if db_path is not None else config.DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
