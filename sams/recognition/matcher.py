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


def _tight_crop(binary: np.ndarray) -> np.ndarray | None:
    """Crop to the bounding box of the ink; None if there is no ink."""
    ys, xs = np.where(binary > 0)
    if len(ys) == 0:
        return None
    return binary[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def _template(binary: np.ndarray) -> np.ndarray | None:
    """Tight-crop then size-normalise a signature to a fixed template.

    The crop is scaled to fit inside the template while PRESERVING its aspect
    ratio, and centred on a blank canvas. Preserving aspect ratio is essential:
    stretching a tight crop to a fixed rectangle would turn any single stroke
    into a solid filled block and destroy the very shape we want to compare.
    """
    crop = _tight_crop(binary)
    if crop is None or crop.size == 0:
        return None

    tw, th = TEMPLATE_SIZE                 # target width, height
    ch, cw = crop.shape
    scale = min(tw / cw, th / ch)
    new_w, new_h = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))
    resized = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((th, tw), np.uint8)
    y0 = (th - new_h) // 2
    x0 = (tw - new_w) // 2
    canvas[y0:y0 + new_h, x0:x0 + new_w] = resized
    return (canvas > 127).astype(np.float32)
