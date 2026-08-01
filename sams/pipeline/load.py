"""Stage 1 — Load & normalise the source image.

Reads the phone photo from disk, resizes it to a manageable working width,
and stashes the colour image on the context for later overlay drawing.
"""
from __future__ import annotations

import cv2
import numpy as np

import config
from ..util.imaging import resize_to_width
from ..util.logging import Console
from .base import PipelineContext, ProcessingStage


class LoadStage(ProcessingStage):
    name = "original"
    snapshot_prefix = "01"

    def apply(self, image: np.ndarray, ctx: PipelineContext) -> np.ndarray:
        if image is None:
            image = cv2.imread(ctx.source_path, cv2.IMREAD_COLOR)
        if image is None:
            raise FileNotFoundError(f"Could not read image: {ctx.source_path}")

        image = resize_to_width(image, config.WORKING_WIDTH)
        Console.info(f"loaded {ctx.source_path}  ({image.shape[1]}x{image.shape[0]})")
        self.snapshot(image)
        return image
