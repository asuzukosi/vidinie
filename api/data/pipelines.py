from pydantic import BaseModel, Field
from typing import Optional, List, Tuple, Dict
from datetime import datetime
from core.data import SourceType, BackgroundType, VideoPipelineContentMetadata
from enum import Enum

class VideoResolution(str, Enum):
    """video resolution."""
    RESOLUTION_4K = "4K"
    RESOLUTION_1080P = "1080P"
    RESOLUTION_720P = "720P"
    RESOLUTION_480P = "480P"

class CreateVideoPipelineRequest(BaseModel):
    url: str
    name: str
    description: str
    tags: Optional[List[str]] = None
    projects: Optional[List[str]] = None

class VideoPipelineSummary(BaseModel):
    # identification
    id: str
    name: str = Field(default="")
    description: str = Field(default="")
    tags: List[str] = Field(default_factory=list, nullable=True)  # tags of the video pipeline
    projects: List[str] = Field(default_factory=list, nullable=True)  # projects of the video pipeline

    # timing information
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    #stage information
    current_stage: str = Field(default="")
    status: str  = Field(default="")
    # source document
    source_path: Optional[str] = None
    source_type: Optional[SourceType] = None

class DeleteVideoPipelineResponse(BaseModel):
    video_pipeline_id: str
    message: str

class VideoPipelineStageDetails(BaseModel):
    stage: str
    status: str
    next_stage: str
    previous_stage: str
    stage_statuses: Optional[Dict[str, str]] = None

class UpdateVideoPipelineImageRequest(BaseModel):
    index: int
    filename: Optional[str] = None
    text_context: Optional[str] = None
    label: Optional[bool] = False
    description: Optional[str] = None
    relevance_score: Optional[float] = None
    image_type: Optional[str] = None
    key_elements: Optional[List[str]] = None
    ai_relevance: Optional[str] = None

class DeleteVideoPipelineImageResponse(BaseModel):
    video_pipeline_id: str
    filename: str
    message: str

class VideoPipelineContentMinimal(BaseModel):
    title: Optional[str] = None
    total_pages: Optional[int] = None
    num_sections: Optional[int] = None
    metadata: Optional[VideoPipelineContentMetadata] = None

class DeleteVideoPipelineSectionResponse(BaseModel):
    video_pipeline_id: str
    index: int
    message: str
    title: Optional[str] = None

class CreateVideoPipelineOutlineRequest(BaseModel):
    skip_stock: bool = False
    target_segments: int = 5
    segment_duration: int = 40

class CreateVideoPipelineScriptRequest(BaseModel):
    provider: str = "elevenlabs"
    voice_id: Optional[str] = None

class GenerateVideoPipelineRequest(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    resolution: Optional[VideoResolution] = VideoResolution.RESOLUTION_720P
    fps: Optional[int] = 30
    title_duration: Optional[float] = 3.0
    end_duration: Optional[float] = 3.0
    transition_duration: Optional[float] = 0.5
    background_type: Optional[BackgroundType] = BackgroundType.GRADIENT


class VideoPipelineSegmentBackground(BaseModel):
    colors: Optional[List[Tuple[int, int, int]]] = None
    type: Optional[BackgroundType] = BackgroundType.GRADIENT
    image_path: Optional[str] = None

class VideoPipelineReviewRequest(BaseModel):
    rating: Optional[int] = None
    feedback: Optional[str] = None

class RunVideoPipelineOperationsRequest(BaseModel):
    url: str
    name: str
    description: str
    tags: Optional[List[str]] = None
    projects: Optional[List[str]] = None
    target_segments: int = 5
    segment_duration: int = 40
    provider: str = "elevenlabs"
    title: Optional[str] = None
    subtitle: Optional[str] = None
    resolution: Optional[VideoResolution] = VideoResolution.RESOLUTION_720P
    fps: Optional[int] = 30
    title_duration: Optional[float] = 3.0
    end_duration: Optional[float] = 3.0
    transition_duration: Optional[float] = 0.5
    background_type: Optional[BackgroundType] = BackgroundType.GRADIENT