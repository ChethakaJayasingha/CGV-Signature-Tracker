"""Signature recognition — compare a detected signature to reference samples.

The goal (the brief's "higher grades" component) is to verify that the mark in a
signature cell is consistent with a student's known signature, so that a
different person's signature — or a non-signature mark — can be flagged.

OWNER: Recognition & QA Engineer.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

TEMPLATE_SIZE = (128, 64)   # (width, height) of the normalised signature template


@dataclass
class MatchResult:
    score: float
    is_match: bool
    detail: str


def _to_gray(img: np.ndarray) -> np.ndarray:
    return img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def _to_binary(gray: np.ndarray) -> np.ndarray:
    """Ensure a binary (0/255) image with ink as white.

    Accepts either an already-inverted-binary crop (from the pipeline) or a
    grey reference image loaded from disk.
    """
    # Otsu-threshold; assume dark ink on light paper -> invert so ink becomes
    # white.
    _, binimg = cv2.threshold(gray, 0, 255,
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binimg
