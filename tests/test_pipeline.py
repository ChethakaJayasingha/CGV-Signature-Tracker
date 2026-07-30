"""Smoke tests for the image-processing pipeline on a synthetic sheet.

We build a tiny fake "signing sheet" in memory (a grid with some cells filled)
so the pipeline can be exercised without shipping large image fixtures. These
verify the stages wire together and produce cells/verdicts; accuracy tuning on
the real sheets is validated separately in the report.
"""
import cv2
import numpy as np
import pytest

from sams.domain.models import Student
from sams.pipeline import build_default_pipeline
from sams.pipeline.base import PipelineContext
from sams.pipeline.greyscale import GreyscaleStage
from sams.pipeline.binarize import BinarizeStage


def _synthetic_sheet(rows=6, filled=(0, 2, 4)):
    """White page with a black table grid; `filled` rows get a scribble."""
    h, w = 700, 500
    img = np.full((h, w, 3), 255, np.uint8)
    top, left, right = 100, 60, 440
    row_h = 70
    # outer + column lines
    cv2.rectangle(img, (left, top), (right, top + rows * row_h), (0, 0, 0), 2)
    cv2.line(img, (300, top), (300, top + rows * row_h), (0, 0, 0), 2)  # sig col
    for r in range(rows + 1):
        y = top + r * row_h
        cv2.line(img, (left, y), (right, y), (0, 0, 0), 2)
    # scribbles in the signature column for "present" rows
    for r in filled:
        y = top + r * row_h + row_h // 2
        cv2.putText(img, "sign", (315, y), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
                    1.2, (0, 0, 0), 2)
    return img


def test_greyscale_then_binarize_shapes():
    img = _synthetic_sheet()
    ctx = PipelineContext(source_path="<mem>")
    grey = GreyscaleStage().apply(img, ctx)
    assert grey.ndim == 2
    binary = BinarizeStage().apply(grey, ctx)
    assert binary.ndim == 2
    assert ctx.binary is not None


def test_full_pipeline_runs_and_populates_context(tmp_path, monkeypatch):
    # Write the synthetic sheet to disk so LoadStage/DeskewStage can read it.
    img = _synthetic_sheet()
    path = tmp_path / "sheet.png"
    cv2.imwrite(str(path), img)

    roster = [Student(f"1000000{i}", "Mr", f"Student {i}") for i in range(6)]
    ctx = PipelineContext(source_path=str(path), roster=roster)

    build_default_pipeline().run(img.copy(), ctx)

    # The pipeline should have produced binary + grid + some cells.
    assert ctx.binary is not None
    assert ctx.grid_mask is not None
    assert isinstance(ctx.cells, list)
    # Every cell must have a verdict set by the presence stage.
    for cell in ctx.cells:
        assert isinstance(cell.present, (bool, np.bool_))
        assert cell.ink_ratio >= 0.0
