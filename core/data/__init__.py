"""
Video pipeline data models.
Exports all models, enums, and utilities for backward compatibility.
"""

# enums
from .enums import (
    SourceType,
    VideoPipelineStatus,
    VideoPipelineStage,
    ImageSource,
    VideoSource,
    BackgroundType,
)

# content models
from .content_models import (
    ContentSection,
    ContentMetadata,
    ParsedContent,
)

# image models
from .image_models import (
    ImageMetadata,
    SegmentImage,
)

# segment models
from .segment_models import (
    VideoSegment,
    VideoOutline,
)


# statistics models
from .statistics_models import (
    VideoPipelineStageStatistics,
)

# stage utilities
from .stage_utils import (
    STAGE_MAP,
    get_next_stage,
    get_previous_stage,
)

# video pipeline model
from .video_pipeline import (
    VideoPipeline,
)

__all__ = [
    # enums
    "SourceType",
    "VideoPipelineStatus",
    "VideoPipelineStage",
    "ImageSource",
    "VideoSource",
    "BackgroundType",
    # content models
    "ContentSection",
    "ContentMetadata",
    "ParsedContent",
    # image model
    "ImageMetadata",
    "SegmentImage",
    # segment models
    "VideoSegment",
    "VideoOutline",
    # statistics model
    "VideoPipelineStageStatistics",
    # stage utilities
    "STAGE_MAP",
    "get_next_stage",
    "get_previous_stage",
    # video pipeline model
    "VideoPipeline",
]

