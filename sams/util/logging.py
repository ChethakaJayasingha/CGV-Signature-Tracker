"""Tiny console-progress helper.

The brief requires that we "show the progress of the image processing"
while sams.py runs. This module gives every stage a consistent way to
announce itself on the terminal.
"""
from __future__ import annotations


class Console:
    """Minimal colour-free progress printer (works on any terminal)."""

    _step = 0

    @classmethod
    def reset(cls) -> None:
        cls._step = 0

    @classmethod
    def step(cls, message: str) -> None:
        cls._step += 1
        print(f"  [{cls._step:02d}] {message}")

    @staticmethod
    def info(message: str) -> None:
        print(f"       {message}")

    @staticmethod
    def header(message: str) -> None:
        print()
        print("=" * 60)
        print(message)
        print("=" * 60)

    @staticmethod
    def result(message: str) -> None:
        print(f"  >>> {message}")
