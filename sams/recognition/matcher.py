"""Signature recognition — compare a detected signature to reference samples.

The goal (the brief's "higher grades" component) is to verify that the mark in a
signature cell is consistent with a student's known signature, so that a
different person's signature — or a non-signature mark — can be flagged.

Signature crops from phone photos are small, sparse and binary, which makes
off-the-shelf feature matching (e.g. ORB) unreliable. This matcher therefore
uses a shape descriptor built for exactly this data:

  1. Tight-crop the cell to its ink bounding box (removes surrounding whitespace).
  2. Size-normalise to a fixed 128x64 template.
  3. Compare templates by Normalised Cross-Correlation (NCC) of the ink shape.

OWNER: Recognition & QA Engineer.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

import config

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


def _ncc(a_tmpl: np.ndarray, b_tmpl: np.ndarray) -> float:
    """Normalised cross-correlation of two ink templates (0..1)."""
    denom = np.sqrt((a_tmpl ** 2).sum() * (b_tmpl ** 2).sum()) + 1e-6
    return float((a_tmpl * b_tmpl).sum() / denom)


class SignatureMatcher:
    """Compares signature crops against a student's reference set."""

    def __init__(self, threshold: float | None = None) -> None:
        self.threshold = threshold if threshold is not None else config.MATCH_THRESHOLD

    def compare(self, reference: np.ndarray, candidate: np.ndarray) -> MatchResult:
        ref_bin = _to_binary(_to_gray(reference))
        cand_bin = _to_binary(_to_gray(candidate))

        ta, tb = _template(ref_bin), _template(cand_bin)
        if ta is None or tb is None:
            return MatchResult(0.0, False, "empty signature (no ink)")

        ncc = _ncc(ta, tb)
        return MatchResult(
            score=round(ncc, 3),
            is_match=ncc >= self.threshold,
            detail=f"NCC={ncc:.3f}",
        )
