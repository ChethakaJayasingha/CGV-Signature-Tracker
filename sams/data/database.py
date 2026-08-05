"""SQLite connection management and schema bootstrap.

SQLite is chosen because it is local, file-based, and zero-config — exactly
matching the brief's requirement to "store the attendance in a local DB".
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS student (
    index_no TEXT PRIMARY KEY,
    title    TEXT,
    name     TEXT
);

CREATE TABLE IF NOT EXISTS sheet (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    date     TEXT UNIQUE,          -- ISO yyyy-mm-dd
    hall     TEXT
);

CREATE TABLE IF NOT EXISTS attendance (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    student_no TEXT REFERENCES student(index_no),
    sheet_id   INTEGER REFERENCES sheet(id),
    present    INTEGER,            -- 0 / 1
    ink_ratio  REAL,
    UNIQUE(student_no, sheet_id)   -- re-running a sheet updates, not duplicates
);
"""


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a connection with foreign keys enabled and row access by name."""
    path = str(db_path if db_path is not None else config.DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def bootstrap(conn: sqlite3.Connection) -> None:
    """Create all tables if they do not already exist."""
    conn.executescript(SCHEMA)
    conn.commit()
