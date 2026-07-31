from __future__ import annotations

import cv2
import numpy as np

import config
from ..util.logging import Console
from .base import PipelineContext, ProcessingStage


class TableLineStage(ProcessingStage):
    name = "grid"
    snapshot_prefix = "06"

    def apply(self, image: np.ndarray, ctx: PipelineContext) -> np.ndarray:
        binary = ctx.binary if ctx.binary is not None else image
        h, w = binary.shape[:2]

        # Horizontal lines: wide, 1px-tall kernel.
        h_len = max(10, w // config.H_LINE_SCALE)
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_len, 1))
        h_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel, iterations=1)

        # Vertical lines: tall, 1px-wide kernel.
        v_len = max(10, h // config.V_LINE_SCALE)
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_len))
        v_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel, iterations=1)

        grid = cv2.add(h_lines, v_lines)
        grid = cv2.dilate(grid, np.ones((2, 2), np.uint8), iterations=1)

        ctx.grid_mask = grid
        ctx.h_lines = h_lines
        ctx.v_lines = v_lines
        Console.info(f"H-kernel={h_len}px  V-kernel={v_len}px")

        self.snapshot(h_lines, suffix="a_h_lines")
        self.snapshot(v_lines, suffix="b_v_lines")
        self.snapshot(grid, suffix="c_grid")
        return grid
