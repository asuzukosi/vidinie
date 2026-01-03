"""
Script-related models for video pipeline.
"""

from typing import List
from pydantic import BaseModel, Field
from .segment_models import VideoPipelineSegment


class VideoPipelineScript(BaseModel):
    """video pipeline script model."""
    title: str = Field(default="")
    total_segments: int = Field(default=0)
    segments: List[VideoPipelineSegment] = Field(default_factory=list)
    full_script: str = Field(default="")

