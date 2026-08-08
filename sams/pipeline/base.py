"""Pipeline infrastructure: the ProcessingStage contract, the shared context,
and the Pipeline driver that runs stages in order.

This is the backbone every image-processing member builds against. A stage only
needs to implement `apply()`; snapshot-saving and progress-printing are handled
here so the report always gets consistent step images.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

import numpy as np

from ..domain.models import Student
from ..util.imaging import maybe_show, save_snapshot, to_bgr
from ..util.logging import Console


@dataclass
class SignatureCell:
    """One extracted signature cell and its verdict."""

    row: int                       # 0-based row index (top-to-bottom)
    crop: np.ndarray               # the binary signature crop
    bbox: tuple[int, int, int, int]  # x, y, w, h in the deskewed image
    ink_ratio: float = 0.0
    present: bool = False


@dataclass
class PipelineContext:
    """Carried through every stage; accumulates results.

    Stages read what they need and write their outputs here rather than
    returning many values.
    """

    source_path: str
    roster: list[Student] = field(default_factory=list)
    sheet_date: date | None = None
    hall: str | None = None

    # Working images filled in as the pipeline runs.
    deskewed: np.ndarray | None = None      # colour, flattened
    binary: np.ndarray | None = None        # inverted adaptive threshold
    grid_mask: np.ndarray | None = None     # combined H+V table lines
    h_lines: np.ndarray | None = None       # horizontal-line mask only
    v_lines: np.ndarray | None = None       # vertical-line mask only
    ink_only: np.ndarray | None = None      # binary with grid lines removed

    cells: list[SignatureCell] = field(default_factory=list)


class ProcessingStage(ABC):
    """Base class for every pipeline stage.

    Subclasses set `name` and implement `apply()`. Use `self.snapshot(...)`
    inside apply() to persist an image for the report.
    """

    name: str = "stage"
    snapshot_prefix: str = "00"

    @abstractmethod
    def apply(self, image: np.ndarray, ctx: PipelineContext) -> np.ndarray:
        """Transform the image and/or populate the context; return next image."""
        raise NotImplementedError

    def snapshot(self, image: np.ndarray, suffix: str = "") -> None:
        """Save a labelled snapshot to output/steps/ and optionally show it."""
        tag = f"{self.snapshot_prefix}_{self.name}"
        if suffix:
            tag += f"_{suffix}"
        save_snapshot(to_bgr(image), f"{tag}.png")
        maybe_show(to_bgr(image), self.name)


class Pipeline:
    """Runs an ordered list of stages, threading the context through."""

    def __init__(self, stages: list[ProcessingStage]) -> None:
        self.stages = stages

    def run(self, image: np.ndarray, ctx: PipelineContext) -> PipelineContext:
        Console.reset()
        current = image
        for stage in self.stages:
            Console.step(f"{stage.name} …")
            current = stage.apply(current, ctx)
        return ctx
