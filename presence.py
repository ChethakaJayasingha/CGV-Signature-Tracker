"""Stage 8 — Presence decision.

For each extracted signature cell, decide present vs absent from ink density:

    ink_ratio = (ink pixels) / (cell area)
    present   = ink_ratio > PRESENCE_THRESHOLD

Small connected components (stray dots, grid remnants) are removed first so a
speck cannot be mistaken for a signature. Produces a final colour overlay
(green = present, red = absent) for the report.

OWNER: Detection & Data Engineer — tune PRESENCE_THRESHOLD / cleanup on sheets.
"""
from __future__ import annotations

import cv2
import numpy as np

import config
from ..util.imaging import ink_ratio, to_bgr
from ..util.logging import Console
from .base import PipelineContext, ProcessingStage


def _remove_specks(binary_cell: np.ndarray) -> np.ndarray:
    """Zero-out connected components smaller than the configured min area."""
    if binary_cell.size == 0:
        return binary_cell
    num, labels, stats, _ = cv2.connectedComponentsWithStats(binary_cell, 8)
    cleaned = np.zeros_like(binary_cell)
    for i in range(1, num):  # 0 is background
        if stats[i, cv2.CC_STAT_AREA] >= config.MIN_INK_COMPONENT_AREA:
            cleaned[labels == i] = 255
    return cleaned


class PresenceDecisionStage(ProcessingStage):
    name = "result"
    snapshot_prefix = "08"

    def apply(self, image: np.ndarray, ctx: PipelineContext) -> np.ndarray:
        for cell in ctx.cells:
            cleaned = _remove_specks(cell.crop)
            cell.ink_ratio = ink_ratio(cleaned)
            cell.present = cell.ink_ratio > config.PRESENCE_THRESHOLD

        present = sum(1 for c in ctx.cells if c.present)
        Console.result(f"{present}/{len(ctx.cells)} signatures detected as PRESENT")

        self._save_overlay(ctx)
        return image

    def _save_overlay(self, ctx: PipelineContext) -> None:
        base = ctx.deskewed if ctx.deskewed is not None else to_bgr(ctx.binary)
        canvas = base.copy()
        for cell in ctx.cells:
            x, y, w, h = cell.bbox
            colour = (0, 200, 0) if cell.present else (0, 0, 255)
            label = "PRESENT" if cell.present else "ABSENT"
            cv2.rectangle(canvas, (x, y), (x + w, y + h), colour, 2)
            # Draw the label just INSIDE the top-left of the box (not above it),
            # so it never lands inside the cell above.
            cv2.putText(canvas, f"{label} {cell.ink_ratio:.3f}",
                        (x + 4, y + 18), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, colour, 1, cv2.LINE_AA)
        self.snapshot(canvas, suffix="overlay")
