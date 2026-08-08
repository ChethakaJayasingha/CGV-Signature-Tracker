"""Image-processing pipeline: an ordered chain of observable stages.

Each stage is a class implementing ProcessingStage. The Pipeline runs them in
order, threading a PipelineContext through, and every stage saves a snapshot so
the report can show the full step-by-step process.
"""
from .base import Pipeline, PipelineContext, ProcessingStage
from .load import LoadStage
from .greyscale import GreyscaleStage
from .denoise import DenoiseStage
from .deskew import DeskewStage
from .binarize import BinarizeStage
from .table_lines import TableLineStage
from .cells import CellExtractionStage
from .presence import PresenceDecisionStage


def build_default_pipeline() -> Pipeline:
    """Construct the standard 8-stage pipeline used by sams.py."""
    return Pipeline([
        LoadStage(),
        GreyscaleStage(),
        DenoiseStage(),
        DeskewStage(),
        BinarizeStage(),
        TableLineStage(),
        CellExtractionStage(),
        PresenceDecisionStage(),
    ])


__all__ = [
    "Pipeline", "PipelineContext", "ProcessingStage",
    "LoadStage", "GreyscaleStage", "DenoiseStage", "DeskewStage",
    "BinarizeStage", "TableLineStage", "CellExtractionStage",
    "PresenceDecisionStage", "build_default_pipeline",
]
