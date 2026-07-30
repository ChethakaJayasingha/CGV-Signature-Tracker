"""Tests for the signature matcher (shape-template NCC)."""
import numpy as np
import pytest

from sams.recognition.matcher import (
    MatchResult, SignatureMatcher, _template, _tight_crop, _to_binary,
)


def _stroke_image(kind: str) -> np.ndarray:
    """Make a small binary (0/255) test image with a known shape."""
    img = np.zeros((60, 200), np.uint8)
    if kind == "vertical":
        img[10:50, 95:105] = 255           # a tall vertical stroke
    elif kind == "vertical2":
        img[12:48, 92:102] = 255           # similar tall stroke (should match)
    elif kind == "horizontal":
        img[28:32, 20:180] = 255           # a wide flat line (different shape)
    return img


def test_tight_crop_removes_whitespace():
    img = _stroke_image("vertical")
    crop = _tight_crop(img)
    assert crop is not None
    # tight crop should be close to the stroke's own size, not the full image
    assert crop.shape[0] <= 42 and crop.shape[1] <= 12


def test_tight_crop_empty_returns_none():
    assert _tight_crop(np.zeros((10, 10), np.uint8)) is None


def test_template_shape():
    t = _template(_stroke_image("vertical"))
    assert t is not None
    assert t.shape == (64, 128)            # (height, width) of TEMPLATE_SIZE


def test_identical_signatures_match_perfectly():
    m = SignatureMatcher()
    img = _stroke_image("vertical")
    result = m.compare(img, img)
    assert result.score == pytest.approx(1.0, abs=1e-3)
    assert result.is_match


def test_similar_shapes_score_higher_than_different():
    m = SignatureMatcher()
    same = m.compare(_stroke_image("vertical"), _stroke_image("vertical2")).score
    diff = m.compare(_stroke_image("vertical"), _stroke_image("horizontal")).score
    assert same > diff


def test_empty_candidate_is_not_a_match():
    m = SignatureMatcher()
    result = m.compare(_stroke_image("vertical"), np.zeros((60, 200), np.uint8))
    assert not result.is_match
    assert result.score == 0.0


def test_no_references_reports_cleanly(tmp_path):
    m = SignatureMatcher()
    result = m.compare_to_references(_stroke_image("vertical"), tmp_path)
    assert isinstance(result, MatchResult)
    assert not result.is_match
    assert "no reference" in result.detail


def test_to_binary_handles_grey_reference():
    # A grey image (dark stroke on light paper) should binarise with ink=white.
    grey = np.full((60, 200), 240, np.uint8)   # light paper
    grey[20:40, 90:110] = 30                     # dark ink
    binimg = _to_binary(grey)
    assert binimg[30, 100] == 255                # ink became white
    assert binimg[0, 0] == 0                      # paper became black
