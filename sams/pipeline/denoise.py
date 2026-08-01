"""Stage 3 — Denoise.

Phone photos carry sensor noise and paper texture that can create false ink
pixels. A light blur / non-local-means smooths these while keeping pen strokes.

OWNER: Preprocessing Engineer — tune the kernel/strength on the sample sheets.
"""
from __future__ import annotations

import cv2
import numpy as np

from .base import PipelineContext, ProcessingStage


class DenoiseStage(ProcessingStage):
    name = "denoised"
    snapshot_prefix = "03"

    def apply(self, image: np.ndarray, ctx: PipelineContext) -> np.ndarray:
        # Gaussian blur is fast and sufficient as a baseline.
        # TODO(owner): compare against cv2.fastNlMeansDenoising for quality.
        denoised = cv2.GaussianBlur(image, (3, 3), 0)
        self.snapshot(denoised)
        return denoised
