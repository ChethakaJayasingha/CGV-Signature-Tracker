"""Tests for the ink-density presence logic and helpers."""
import numpy as np

import config
from sams.util.imaging import ink_ratio
from sams.pipeline.presence import _remove_specks


def test_ink_ratio_all_black_is_zero():
    cell = np.zeros((50, 100), dtype=np.uint8)
    assert ink_ratio(cell) == 0.0


def test_ink_ratio_half_filled():
    cell = np.zeros((10, 10), dtype=np.uint8)
    cell[:, :5] = 255                       # half the pixels are ink
    assert ink_ratio(cell) == 0.5


def test_ink_ratio_empty_array():
    assert ink_ratio(np.zeros((0, 0), dtype=np.uint8)) == 0.0


def test_remove_specks_drops_tiny_components():
    cell = np.zeros((60, 60), dtype=np.uint8)
    # a single stray pixel (area 1) should be removed
    cell[5, 5] = 255
    cleaned = _remove_specks(cell)
    assert np.count_nonzero(cleaned) == 0


def test_remove_specks_keeps_large_blob():
    cell = np.zeros((60, 60), dtype=np.uint8)
    cell[20:40, 20:40] = 255                # 400-px blob, well above min area
    cleaned = _remove_specks(cell)
    assert np.count_nonzero(cleaned) == 400


def test_presence_threshold_boundary():
    # A cell just above threshold counts as present.
    size = 10_000
    ink_px = int((config.PRESENCE_THRESHOLD + 0.01) * size)
    cell = np.zeros(size, dtype=np.uint8)
    cell[:ink_px] = 255
    assert ink_ratio(cell) > config.PRESENCE_THRESHOLD
