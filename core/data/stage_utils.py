"""
stage utility functions for video pipeline.
"""

from typing import Dict
from .enums import VideoPipelineStage


STAGE_MAP: Dict[VideoPipelineStage, VideoPipelineStage] = {
    VideoPipelineStage.INITIALIZED: VideoPipelineStage.DOCUMENT_PROCESSING,
    VideoPipelineStage.DOCUMENT_PROCESSING: VideoPipelineStage.IMAGE_PROCESSING,
    VideoPipelineStage.IMAGE_PROCESSING: VideoPipelineStage.CONTENT_ANALYSIS,
    VideoPipelineStage.CONTENT_ANALYSIS: VideoPipelineStage.SCRIPT_GENERATION,
    VideoPipelineStage.SCRIPT_GENERATION: VideoPipelineStage.VIDEO_GENERATION,
    VideoPipelineStage.VIDEO_GENERATION: VideoPipelineStage.COMPLETED,
    VideoPipelineStage.FAILED: VideoPipelineStage.FAILED,
}


def get_next_stage(current_stage: VideoPipelineStage) -> VideoPipelineStage:
    """
    get the next stage of the video pipeline.
    """
    return STAGE_MAP.get(current_stage, VideoPipelineStage.FAILED)


def get_previous_stage(current_stage: VideoPipelineStage) -> VideoPipelineStage:
    """
    get the previous stage of the video pipeline.
    """
    for key, value in STAGE_MAP.items():
        if value == current_stage:
            return key
    return VideoPipelineStage.FAILED

