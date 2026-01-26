"""
segment and outline models for video pipeline.
"""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from .enums import BackgroundType
from .image_models import SegmentImage, SegmentVideoClip


class VideoSegment(BaseModel):
    """video pipeline segment model."""
    title: str
    purpose: str
    content: str
    key_points: List[str]
    visual_keywords: List[str]
    script: Optional[str] = None
    word_count: Optional[int] = None
    duration: int
    images: Optional[List[SegmentImage]] = None  # images to show with segment
    video_clips: Optional[List[SegmentVideoClip]] = None  # video clips to show with segment
    transition_to: Optional[str] = None
    transition_type: Optional[str] = None
    audio_file: Optional[str] = None
    audio_duration: Optional[float] = None
    # video generation settings
    background_colors: Optional[List[Tuple[int, int, int]]] = Field(default_factory=lambda: [(0, 0, 0), (0, 0, 0)])
    background_type: Optional[BackgroundType] = Field(default=BackgroundType.GRADIENT)
    background_image_path: Optional[str] = None


class VideoOutline(BaseModel):
    """video pipeline outline model."""
    title: str
    total_segments: int
    estimated_duration: int
    segments: List[VideoSegment]
    full_script: Optional[str] = Field(default="")

