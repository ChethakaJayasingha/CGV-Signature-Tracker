"""Tests for the roster parser's error reporting.

The happy paths live in tests/test_roster.py; this file only covers the
failure messages, so a broken info.xml is diagnosable without a stack trace.
"""
from pathlib import Path

import pytest

from sams.domain.roster import RosterError, RosterParser

DUPLICATE_XML = """<?xml version="1.0"?>
<nsbm><students><batches><batch id="2016.1">
  <student><index>10009301</index><title>Mr</title><name>C W M A Shehan Abeyrathne</name></student>
  <student><index>10009301</index><title>Mr</title><name>Duplicated By Mistake</name></student>
</batch></batches></students></nsbm>
"""

# <batch> and <nsbm> are never closed.
MALFORMED_XML = """<?xml version="1.0"?>
<nsbm><students><batch>
  <student><index>001</index><name>John Snow</name></student>
"""


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "info.xml"
    p.write_text(content, encoding="utf-8")
    return p


def test_duplicate_index_names_the_offender(tmp_path):
    with pytest.raises(RosterError) as exc:
        RosterParser.parse(_write(tmp_path, DUPLICATE_XML))
    assert "10009301" in str(exc.value)
    assert "duplicate" in str(exc.value).lower()


def test_malformed_xml_is_explained(tmp_path):
    with pytest.raises(RosterError) as exc:
        RosterParser.parse(_write(tmp_path, MALFORMED_XML))
    assert "well-formed" in str(exc.value)


def test_roster_errors_remain_value_errors(tmp_path):
    # tests/test_roster.py catches plain ValueError, so RosterError must stay
    # a subclass of it or that suite breaks.
    assert issubclass(RosterError, ValueError)
    with pytest.raises(ValueError):
        RosterParser.parse(_write(tmp_path, DUPLICATE_XML))
