"""Parse the info.xml roster into Student objects.

The XML follows the structure in Figure 1 of the brief, adapted to the real
signing sheets (8-digit indices + a `title` field):

    <nsbm>
      <students>
        <batches>
          <batch id="2016.1">
            <subject code="CS402.3">Computer Graphics and Visualization</subject>
            <student>
              <index>10000409</index>
              <title>Ms</title>
              <name>M S Dilshanika Perera</name>
            </student>
            ...
          </batch>
        </batches>
      </students>
    </nsbm>

The parser is tolerant of the simpler brief-style layout too (no <title>,
numeric <15> batch tags), so it also accepts the exact Figure 1 example.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .models import Student


class RosterError(ValueError):
    """Raised when info.xml cannot be turned into a usable roster.

    Deliberately subclasses ValueError so callers that already catch
    ValueError keep working; the distinct type just makes roster problems
    easy to tell apart from other failures.
    """


class RosterParser:
    """Reads info.xml and returns an ordered list of Student objects.

    Order matters: the row order here is matched against the top-to-bottom
    order of signature cells detected on the sheet.
    """

    @staticmethod
    def parse(xml_path: str | Path) -> list[Student]:
        xml_path = Path(xml_path)
        if not xml_path.exists():
            raise FileNotFoundError(f"info.xml not found: {xml_path}")

        try:
            tree = ET.parse(xml_path)
        except ET.ParseError as exc:
            raise RosterError(
                f"{xml_path} is not well-formed XML: {exc}. Check for an "
                f"unclosed tag or a stray '&' and re-save the file."
            ) from exc
        root = tree.getroot()

        students: list[Student] = []
        seen: set[str] = set()
        duplicates: list[str] = []
        # Find every <student> element anywhere in the tree (robust to the
        # exact nesting of <batches>/<batch>/<15> etc.).
        for node in root.iter("student"):
            index = _text(node, "index")
            name = _text(node, "name")
            title = _text(node, "title", default="")
            if index and name:
                if index in seen:
                    duplicates.append(index)
                else:
                    seen.add(index)
                students.append(Student(index=index, title=title, name=name))

        if not students:
            raise RosterError(f"No <student> entries found in {xml_path}")
        if duplicates:
            # A repeated index would silently shift every later row, so the
            # roster→sheet row-order contract breaks. Fail loudly instead.
            raise RosterError(
                f"duplicate student index(es) in {xml_path}: "
                f"{', '.join(sorted(set(duplicates)))}. Each student must "
                f"appear exactly once — roster order maps to sheet row order."
            )
        return students

    @staticmethod
    def find_student(students: list[Student], index: str) -> Student | None:
        """Look up a student by index, tolerating short/long forms.

        The CLI is invoked like `infovis.py 001`; real indices are 8 digits.
        This matches on exact index or on a suffix (so "409" finds "10000409"),
        which keeps the brief's `001` example working alongside real data.
        """
        for s in students:
            if s.index == index or s.index.endswith(index):
                return s
        return None


def _text(parent: ET.Element, tag: str, default: str | None = None) -> str | None:
    """Return stripped text of a child tag, or default if missing/empty."""
    el = parent.find(tag)
    if el is None or el.text is None:
        return default
    value = el.text.strip()
    return value or default
