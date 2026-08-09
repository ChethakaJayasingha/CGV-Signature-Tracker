"""Stage 7 — Cell extraction (line-projection method).

The grid mask from stage 6 is clean, so instead of hunting arbitrary contours we
locate cells by PROJECTING the detected lines onto the axes:

  1. Sum the vertical-line mask down each column  -> peaks = column separators (x).
  2. Sum the horizontal-line mask across each row  -> peaks = row separators (y).
  3. The SIGNATURE column is the band between the last two column separators
     (the right-most column of the table).
  4. Slice that band by consecutive row-separator pairs; the student rows are the
     bottom EXPECTED_STUDENT_ROWS bands (the ones above them are the header block).

This is robust to the printed text in other columns because we only ever crop the
right-most (signature) band. Crops are taken from ctx.binary for the presence stage.

OWNER: Cell-Extraction Engineer.
"""
from __future__ import annotations

import cv2
import numpy as np

import config
from ..util.imaging import to_bgr
from ..util.logging import Console
from .base import PipelineContext, ProcessingStage, SignatureCell


def _peaks(projection: np.ndarray, min_frac: float, min_gap: int) -> list[int]:
    """Find peak positions in a 1-D projection.

    A position qualifies if its value exceeds ``min_frac`` of the projection's
    maximum. Consecutive qualifying positions are collapsed to their centre, and
    peaks closer than ``min_gap`` are merged (keeps one line per separator).
    """
    if projection.max() == 0:
        return []
    thresh = projection.max() * min_frac
    hot = np.where(projection >= thresh)[0]
    if len(hot) == 0:
        return []

    # Group runs of consecutive hot indices into single centres.
    groups: list[int] = []
    start = prev = hot[0]
    for idx in hot[1:]:
        if idx - prev > 1:
            groups.append((start + prev) // 2)
            start = idx
        prev = idx
    groups.append((start + prev) // 2)

    # Merge centres that are closer than min_gap.
    merged: list[int] = []
    for c in groups:
        if merged and c - merged[-1] < min_gap:
            merged[-1] = (merged[-1] + c) // 2
        else:
            merged.append(c)
    return merged


class CellExtractionStage(ProcessingStage):
    name = "cells"
    snapshot_prefix = "07"

    def apply(self, image: np.ndarray, ctx: PipelineContext) -> np.ndarray:
        binary = ctx.binary if ctx.binary is not None else image
        h_lines = ctx.h_lines if ctx.h_lines is not None else binary
        v_lines = ctx.v_lines if ctx.v_lines is not None else binary
        H, W = binary.shape[:2]

        # Build a LINE-FREE binary: remove the printed grid so that only
        # handwriting remains. Otherwise a cell's own border lines count as
        # "ink" and every cell looks signed. The grid is dilated slightly so the
        # full stroke width of each printed line is subtracted.
        grid = cv2.dilate(cv2.add(h_lines, v_lines),
                          np.ones((3, 3), np.uint8), iterations=1)
        ink_only = cv2.bitwise_and(binary, cv2.bitwise_not(grid))
        # Close tiny gaps the line-removal punched through real strokes.
        ink_only = cv2.morphologyEx(ink_only, cv2.MORPH_CLOSE,
                                    np.ones((2, 2), np.uint8), iterations=1)
        ctx.ink_only = ink_only

        # 1. Column separators from the vertical-line mask. A lower threshold is
        #    used because the signature column's borders are often faint (messy
        #    handwriting breaks the printed line).
        col_proj = v_lines.sum(axis=0).astype(np.float64)
        col_x = _peaks(col_proj, min_frac=0.20, min_gap=max(15, W // 40))

        # 2. Row separators from the horizontal-line mask.
        row_proj = h_lines.sum(axis=1).astype(np.float64)
        row_y = _peaks(row_proj, min_frac=0.35, min_gap=max(10, H // 60))

        # 3. The table's true right edge comes from the HORIZONTAL lines (which
        #    reliably span the full table width), NOT from the last vertical line
        #    (the signature border is often too faint to be a strong v-peak).
        #    Use a STRONG column of h-line pixels (many stacked row rules end at
        #    the real border) so a single stray long edge cannot pull it wider.
        hcol_proj = h_lines.sum(axis=0).astype(np.float64)
        strong_cols = np.where(hcol_proj >= hcol_proj.max() * 0.30)[0]
        table_right = int(strong_cols.max()) if len(strong_cols) else W - 1

        cells: list[SignatureCell] = []
        if len(col_x) >= 1 and len(row_y) >= 2:
            # Signature band = from the last vertical line that sits LEFT of the
            # table's right edge, across to that right edge.
            interior = [x for x in col_x if x < table_right - max(20, W // 60)]
            x_left = interior[-1] if interior else col_x[-1]
            x_right = table_right

            # 4. Row bands = consecutive row-separator pairs.
            bands = list(zip(row_y[:-1], row_y[1:]))
            heights = [b - a for (a, b) in bands]
            # The table rows are uniform, so filter by the MEDIAN band height:
            # reject slivers (double-detected lines) AND over-tall bands (a stray
            # line far below the table forms one giant phantom band).
            if heights:
                med = float(np.median(heights))
                lo, hi = 0.45 * med, 1.8 * med
                bands = [(a, b) for (a, b) in bands if lo <= (b - a) <= hi]
            # The student rows are the bottom N valid bands (the header block and
            # the date/lecturer block sit above them).
            student_bands = bands[-config.EXPECTED_STUDENT_ROWS:]

            for i, (y0, y1) in enumerate(student_bands):
                pad = 3
                x0, x1 = x_left + pad, x_right - pad
                y0p, y1p = y0 + pad, y1 - pad
                crop = ink_only[y0p:y1p, x0:x1]   # line-free crop
                cells.append(SignatureCell(
                    row=i, crop=crop, bbox=(x0, y0p, x1 - x0, y1p - y0p)))

        ctx.cells = cells
        Console.info(f"cols={len(col_x)} rows={len(row_y)} -> "
                     f"{len(cells)} signature cells "
                     f"(expected {config.EXPECTED_STUDENT_ROWS})")

        self._save_overlay(ctx, cells, col_x, row_y)
        return image

    def _save_overlay(self, ctx: PipelineContext, cells: list[SignatureCell],
                      col_x: list[int], row_y: list[int]) -> None:
        base = ctx.deskewed if ctx.deskewed is not None else to_bgr(ctx.binary)
        canvas = base.copy()
        H, W = canvas.shape[:2]
        # Faint separator lines we detected (blue) — useful for the report.
        for x in col_x:
            cv2.line(canvas, (x, 0), (x, H), (255, 150, 0), 1)
        for y in row_y:
            cv2.line(canvas, (0, y), (W, y), (255, 150, 0), 1)
        # The signature cells we will measure (orange).
        for cell in cells:
            x, y, w, h = cell.bbox
            cv2.rectangle(canvas, (x, y), (x + w, y + h), (0, 165, 255), 2)
            cv2.putText(canvas, f"row {cell.row + 1}", (x + 4, y + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1,
                        cv2.LINE_AA)
        self.snapshot(canvas, suffix="overlay")
