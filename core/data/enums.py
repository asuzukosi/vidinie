"""
Enum definitions for video pipeline.
"""

from enum import Enum


class SourceType(str, Enum):
    """
    source type of the video pipeline.
    """
    PDF = "pdf"
    HTML = "html"


class VideoPipelineStatus(str, Enum):
    """
    status of the video pipeline.
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoPipelineStage(str, Enum):
    """
    stage of the video pipeline.
    """
    INITIALIZED = "initialized"
    DOCUMENT_PROCESSING = "document_processing"
    IMAGE_PROCESSING = "image_processing"
    CONTENT_ANALYSIS = "content_analysis"
    SCRIPT_GENERATION = "script_generation"
    VIDEO_GENERATION = "video_generation"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageSource(str, Enum):
    """
    source of the image.
    """
    PDF = "pdf"
    STOCK = "stock"
    UNSPLASH = "unsplash"
    PEXELS = "pexels"
    AI_GENERATED = "ai_generated"
    USER_UPLOADED = "user_uploaded"


class BackgroundType(str, Enum):
    """
    type of the background.
    """
    GRADIENT = "gradient"
    SOLID = "solid"
    IMAGE = "image"

