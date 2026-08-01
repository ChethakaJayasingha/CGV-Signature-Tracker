"""Stage 2 — Greyscale conversion.

Colour is irrelevant for ink detection, and working in a single channel
simplifies every subsequent step. Standard BGR -> GRAY conversion.
"""
from __future__ import annotations

import cv2
import numpy as np

from .base import PipelineContext, ProcessingStage


class GreyscaleStage(ProcessingStage):
    name = "grey"
    snapshot_prefix = "02"

    def apply(self, image: np.ndarray, ctx: PipelineContext) -> np.ndarray:
        if image.ndim == 3:
            grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            grey = image
        self.snapshot(grey)
        return grey
