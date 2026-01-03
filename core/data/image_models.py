"""
image-related models for video pipeline.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from .enums import ImageSource


class VideoPipelineImageMetadata(BaseModel):
    """
    image metadata from the document for video pipeline.
    """
    filename: Optional[str] = None
    filepath: Optional[str] = None
    page_number: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    mode: Optional[str] = None
    size_bytes: Optional[int] = None
    text_context: Optional[str] = None
    xref: Optional[int] = None
    index_on_page: Optional[int] = None
    label: Optional[str] = None
    description: Optional[str] = None
    relevance_score: Optional[float] = None
    image_type: Optional[str] = None
    key_elements: Optional[List[str]] = None
    ai_relevance: Optional[str] = None


class VideoPipelineSegmentImage(BaseModel):
    """video pipeline segment image model."""
    source: ImageSource
    query: Optional[str] = None  # search keyword if stock, or prompt if ai_generated
    path: Optional[str] = None  # path to pdf image if pdf, or path to generated image if ai_generated


class VideoPipelineImageStats(BaseModel):
    """
    image stats from the document for video pipeline.
    """
    total_images: int = Field(default=0)
    average_size: int = Field(default=0)
    total_size: int = Field(default=0)
    formats: Dict[str, int] = Field(default_factory=dict)
    pages_with_images: int = Field(default=0)

