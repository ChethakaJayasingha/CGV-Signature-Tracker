"""Parse the info.xml roster into Student objects."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .models import Student


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

        tree = ET.parse(xml_path)
        root = tree.getroot()

        students: list[Student] = []
        # Find every <student> element anywhere in the tree (robust to the
        # exact nesting of <batches>/<batch>/<15> etc.).
        for node in root.iter("student"):
            index = _text(node, "index")
            name = _text(node, "name")
            title = _text(node, "title", default="")
            if index and name:
                students.append(Student(index=index, title=title, name=name))

        if not students:
            raise ValueError(f"No <student> entries found in {xml_path}")
        return students


def _text(parent: ET.Element, tag: str, default: str | None = None) -> str | None:
    """Return stripped text of a child tag, or default if missing/empty."""
    el = parent.find(tag)
    if el is None or el.text is None:
        return default
    value = el.text.strip()
    return value or default
