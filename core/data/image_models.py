"""
image-related models for video pipeline.
"""

from typing import List, Optional
from pydantic import BaseModel
from .enums import ImageSource, VideoSource


class ImageMetadata(BaseModel):
    """
    image metadata from the document for video pipeline.
    """
    filename: Optional[str] = None
    filepath: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    image_type: Optional[str] = None
    key_elements: Optional[List[str]] = None
    relevance: Optional[str] = None


class SegmentImage(BaseModel):
    """segment image"""
    source: ImageSource
    query: Optional[str] = None  # search keyword if stock, or prompt if ai_generated
    path: Optional[str] = None  # path to pdf image if pdf, or path to generated image if ai_generated
    timing: Optional[str] = None  # start, middle, end, throughout

class SegmentClip(BaseModel):
    """segment clip"""
    source: VideoSource
    query: Optional[str] = None  # search keyword if stock, or prompt if ai_generated
    path: Optional[str] = None  # url to video clip
    timing: Optional[str] = None  # start, middle, end, throughout

