"""Tests for the info.xml roster parser."""
from pathlib import Path

import pytest

from sams.domain.roster import RosterParser

SAMPLE_XML = """<?xml version="1.0"?>
<nsbm><students><batches><batch id="2016.1">
  <student><index>10000409</index><title>Ms</title><name>M S Dilshanika Perera</name></student>
  <student><index>10009301</index><title>Mr</title><name>C W M A Shehan Abeyrathne</name></student>
</batch></batches></students></nsbm>
"""

# The brief's Figure 1 shows a <15> batch tag, but XML element names cannot
# start with a digit (that markup is not well-formed). The real roster therefore
# carries the batch number as an attribute, which the parser handles by finding
# <student> anywhere in the tree. This fixture omits <title> like the brief example.
BRIEF_STYLE_XML = """<?xml version="1.0"?>
<nsbm><students><batches><batch id="15">
  <student><index>001</index><name>John Snow</name></student>
  <student><index>007</index><name>James Bond</name></student>
</batch></batches></students></nsbm>
"""


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "info.xml"
    p.write_text(content, encoding="utf-8")
    return p


def test_parses_real_sheet_roster(tmp_path):
    students = RosterParser.parse(_write(tmp_path, SAMPLE_XML))
    assert len(students) == 2
    assert students[0].index == "10000409"
    assert students[0].title == "Ms"
    assert students[0].full_name == "Ms M S Dilshanika Perera"


def test_parses_brief_style_without_title(tmp_path):
    students = RosterParser.parse(_write(tmp_path, BRIEF_STYLE_XML))
    assert len(students) == 2
    assert students[0].index == "001"
    assert students[0].title == ""          # no <title> in brief example
    assert students[1].name == "James Bond"


def test_preserves_row_order(tmp_path):
    students = RosterParser.parse(_write(tmp_path, SAMPLE_XML))
    indices = [s.index for s in students]
    assert indices == sorted(indices)       # this sample happens to be sorted


def test_find_student_by_suffix(tmp_path):
    students = RosterParser.parse(_write(tmp_path, SAMPLE_XML))
    found = RosterParser.find_student(students, "409")
    assert found is not None and found.index == "10000409"


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        RosterParser.parse(tmp_path / "nope.xml")


def test_empty_roster_raises(tmp_path):
    empty = _write(tmp_path, '<?xml version="1.0"?><nsbm></nsbm>')
    with pytest.raises(ValueError):
        RosterParser.parse(empty)
