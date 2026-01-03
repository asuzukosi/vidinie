"""
statistics models for video pipeline.
"""

from typing import Optional
from pydantic import BaseModel
from .enums import VideoPipelineStatus


class VideoPipelineStageStatistics(BaseModel):
    """
    statistics of the video pipeline stage.
    """
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[float] = None
    status: Optional[VideoPipelineStatus] = None

