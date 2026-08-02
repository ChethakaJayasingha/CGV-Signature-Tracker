"""Core data models shared across the system.

Using dataclasses keeps the models small, typed, and readable — and gives us
free __init__/__repr__/__eq__ (helpful in tests).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Student:
    """A student on the roster (parsed from info.xml)."""

    index: str          # e.g. "10000409"
    title: str          # e.g. "Ms" / "Mr"
    name: str           # e.g. "M S Dilshanika Perera"

    @property
    def full_name(self) -> str:
        return f"{self.title} {self.name}".strip()
