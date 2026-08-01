"""Stage 4 — Deskew / perspective correction.

The sheets are photographed at an angle, so the printed grid is not axis-aligned.
This stage finds the largest 4-corner (paper/table) contour and warps it to a
flat, front-on rectangle. If no clean quadrilateral is found it falls back to a
rotation based on the minimum-area rectangle of the page content.

Because later stages need a colour image to draw overlays, the deskew transform
is computed on the grey image but ALSO applied to the original colour image,
which is stored on ctx.deskewed.

OWNER: Geometry Engineer — improve corner detection robustness on all 5 sheets.
"""
from __future__ import annotations

import cv2
import numpy as np

from ..util.imaging import resize_to_width
from ..util.logging import Console
from .base import PipelineContext, ProcessingStage
import config


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """Order 4 points as top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]      # top-left  (smallest x+y)
    rect[2] = pts[np.argmax(s)]      # bottom-right (largest x+y)
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]   # top-right (smallest y-x)
    rect[3] = pts[np.argmax(diff)]   # bottom-left
    return rect


def _find_document_quad(grey: np.ndarray) -> np.ndarray | None:
    """Return 4 ordered corners of the largest quadrilateral, or None."""
    edged = cv2.Canny(grey, 50, 150)
    edged = cv2.dilate(edged, np.ones((3, 3), np.uint8), iterations=1)
    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    img_area = grey.shape[0] * grey.shape[1]
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4 and cv2.contourArea(approx) > 0.30 * img_area:
            return _order_corners(approx.reshape(4, 2).astype("float32"))
    return None


def _estimate_skew_angle(grey: np.ndarray) -> float:
    """Estimate table skew (degrees) from near-horizontal printed lines.

    Uses probabilistic Hough to find long straight segments, keeps those within
    ~20 deg of horizontal, and returns the median angle. Positive = the sheet is
    rotated clockwise and must be rotated back by that amount.
    """
    edges = cv2.Canny(grey, 50, 150)
    min_len = grey.shape[1] // 4       # only long lines (table rules)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=120,
                            minLineLength=min_len, maxLineGap=20)
    if lines is None:
        return 0.0
    angles: list[float] = []
    for x1, y1, x2, y2 in lines[:, 0]:
        ang = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if abs(ang) <= 20:             # near-horizontal only
            angles.append(ang)
    if not angles:
        return 0.0
    return float(np.median(angles))


def _rotate(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate an image about its centre by ``angle`` degrees (white border)."""
    h, w = image.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    border = 255 if image.ndim == 2 else (255, 255, 255)
    return cv2.warpAffine(image, m, (w, h), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=border)


class DeskewStage(ProcessingStage):
    name = "deskewed"
    snapshot_prefix = "04"

    def apply(self, image: np.ndarray, ctx: PipelineContext) -> np.ndarray:
        grey = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Reload the colour image so we can keep a colour deskewed copy for overlays.
        colour = cv2.imread(ctx.source_path, cv2.IMREAD_COLOR)
        if colour is not None:
            colour = resize_to_width(colour, config.WORKING_WIDTH)
        else:
            colour = cv2.cvtColor(grey, cv2.COLOR_GRAY2BGR)

        quad = _find_document_quad(grey)
        if quad is not None:
            (tl, tr, br, bl) = quad
            width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
            height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
            width, height = max(width, 1), max(height, 1)
            dst = np.array([[0, 0], [width - 1, 0],
                            [width - 1, height - 1], [0, height - 1]],
                           dtype="float32")
            m = cv2.getPerspectiveTransform(quad, dst)
            grey_out = cv2.warpPerspective(grey, m, (width, height))
            colour_out = cv2.warpPerspective(colour, m, (width, height))
            Console.info("perspective-corrected via document contour")
        else:
            # Fallback: no clean 4-corner quad (common when the table doesn't
            # fill the frame). Estimate the skew ANGLE from the table's near-
            # horizontal printed lines via the Hough transform, then rotate to
            # level them. This straightens tilted sheets so the line-projection
            # in later stages separates rows/columns cleanly.
            angle = _estimate_skew_angle(grey)
            if abs(angle) > 0.3:
                grey_out = _rotate(grey, angle)
                colour_out = _rotate(colour, angle)
                Console.info(f"no quad — rotated by {angle:+.2f} deg to deskew")
            else:
                grey_out, colour_out = grey, colour
                Console.info("no quad and near-level — using image as-is")

        ctx.deskewed = colour_out
        self.snapshot(grey_out)
        return grey_out
