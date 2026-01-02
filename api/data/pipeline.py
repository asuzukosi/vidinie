from pydantic import BaseModel, Field
from typing import Optional, List, Tuple
from datetime import datetime
from core.data.pipeline import SourceType
from enum import Enum

from core.data.pipeline import BackgroundType, PipelineStageStatistics, ParsedContentMetadata

class VideoResolution(str, Enum):
    """video resolution."""
    RESOLUTION_4K = "4K"
    RESOLUTION_1080P = "1080P"
    RESOLUTION_720P = "720P"
    RESOLUTION_480P = "480P"

class StartPipelineRequest(BaseModel):
    url: str
    name: str
    description: str
    tags: Optional[List[str]] = None
    projects: Optional[List[str]] = None

class SummaryPipelineDataResponse(BaseModel):
    # identification
    id: str
    path_id: Optional[str] = None # id used by mongodb for internal use
    name: str = Field(default="")
    description: str = Field(default="")
    tags: List[str] = Field(default_factory=list, nullable=True)  # tags of the pipeline
    projects: List[str] = Field(default_factory=list, nullable=True)  # projects of the pipeline
    
    # timing information
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    #stage information
    current_stage: str = Field(default="")
    status: str  = Field(default="")
    # source document
    source_path: Optional[str] = None
    source_type: Optional[SourceType] = None

class DeletePipelineResponse(BaseModel):
    pipeline_id: str
    message: str

class PipelineStageDetails(BaseModel):
    stage: str
    status: str
    next_stage: str
    previous_stage: str
    stage_statistics: PipelineStageStatistics

class UpdatePipelineImageMetadataRequest(BaseModel):
    index: int
    filename: Optional[str] = None
    text_context: Optional[str] = None
    label: Optional[bool] = False
    description: Optional[str] = None
    relevance_score: Optional[float] = None
    image_type: Optional[str] = None
    key_elements: Optional[List[str]] = None
    ai_relevance: Optional[str] = None

class DeletePipelineImageResponse(BaseModel):
    pipeline_id: str
    filename: str
    message: str
    path_id: Optional[str] = None

class ParsedContentDataMinimal(BaseModel):
    title: Optional[str] = None
    total_pages: Optional[int] = None
    num_sections: Optional[int] = None
    metadata: Optional[ParsedContentMetadata] = None

class DeletePipelineSectionResponse(BaseModel):
    pipeline_id: str
    index: int
    message: str
    title: Optional[str] = None

class CreateVideoOutlineRequest(BaseModel):
    skip_stock: bool = False
    target_segments: int = 7
    segment_duration: int = 45

class VideoGenerationRequest(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    resolution: Optional[VideoResolution] = VideoResolution.RESOLUTION_720P
    fps: Optional[int] = 30
    title_duration: Optional[float] = 3.0
    end_duration: Optional[float] = 3.0
    transition_duration: Optional[float] = 0.5
    background_type: Optional[BackgroundType] = BackgroundType.GRADIENT


class VideoSegmentBackground(BaseModel):
    colors: Optional[List[Tuple[int, int, int]]] = None
    type: Optional[BackgroundType] = BackgroundType.GRADIENT
    image_path: Optional[str] = None

class PipelineReviewRequest(BaseModel):
    rating: Optional[int] = None
    feedback: Optional[str] = None

class RunAllPipelineOperationsRequest(BaseModel):
    url: str
    name: str
    description: str
    tags: Optional[List[str]] = None
    projects: Optional[List[str]] = None
    target_segments: int = 7
    segment_duration: int = 45
    provider: str = "elevenlabs"
    title: Optional[str] = None
    subtitle: Optional[str] = None
    resolution: Optional[VideoResolution] = VideoResolution.RESOLUTION_720P
    fps: Optional[int] = 30
    title_duration: Optional[float] = 3.0
    end_duration: Optional[float] = 3.0
    transition_duration: Optional[float] = 0.5
    background_type: Optional[BackgroundType] = BackgroundType.GRADIENT