"""
pipeline data model
holds all data related to a video generation operation.
workflow operations:
    the pipeline supports multiple workflow configurations. the standard workflow includes:
    1. document_processing  - parse and extract document structure
    2. image_processing     - extract and label images with AI
    3. content_analysis     - analyze content and create video outline
    4. script_generation    - generate narration scripts and voiceovers
    5. video_generation     - compose final video from all assets
    alternative workflows may skip operations, reorder them, or introduce custom operations
    depending on the input type and desired output. the system is designed to support
    multiple workflow paths for different use cases.
"""

import os
import json
import pickle
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from utils.logger import get_logger
from enum import Enum
logger = get_logger('pipeline_data')


class SourceType(str, Enum):
    """
    source type of the pipeline data.
    """
    PDF = "pdf"
    HTML = "html"

class PipelineStatus(str, Enum):
    """
    status of the pipeline.
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineStage(str, Enum):
    """
    stage of the pipeline.
    """
    INITIALIZED = "initialized"
    DOCUMENT_PROCESSING = "document_processing"
    IMAGE_PROCESSING = "image_processing"
    CONTENT_ANALYSIS = "content_analysis"
    SCRIPT_GENERATION = "script_generation"
    VIDEO_GENERATION = "video_generation"
    COMPLETED = "completed"
    FAILED = "failed"

class ParsedContentSection(BaseModel):
    """
    parsed content section from the document.
    """
    title: Optional[str] = None
    content: Optional[str] = None
    level: Optional[int] = None

class ParsedContentMetadata(BaseModel):
    """
    parsed content metadata from the document.
    """
    title: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None

class ParsedContent(BaseModel):
    """
    parsed content from the document.
    """
    title: Optional[str] = None
    total_pages: Optional[int] = None
    sections: List[ParsedContentSection] = Field(default_factory=list)
    metadata: Optional[ParsedContentMetadata] = None

class ImageMetadata(BaseModel):
    """
    image metadata from the document.
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

STAGE_MAP: Dict[PipelineStage, PipelineStage] = {
    PipelineStage.INITIALIZED: PipelineStage.DOCUMENT_PROCESSING,
    PipelineStage.DOCUMENT_PROCESSING: PipelineStage.IMAGE_PROCESSING,
    PipelineStage.IMAGE_PROCESSING: PipelineStage.CONTENT_ANALYSIS,
    PipelineStage.CONTENT_ANALYSIS: PipelineStage.SCRIPT_GENERATION,
    PipelineStage.SCRIPT_GENERATION: PipelineStage.VIDEO_GENERATION,
    PipelineStage.VIDEO_GENERATION: PipelineStage.COMPLETED,
    PipelineStage.FAILED: PipelineStage.FAILED,
}

def get_next_stage(current_stage: PipelineStage) -> PipelineStage:
    """
    get the next stage of the pipeline.
    """
    return STAGE_MAP.get(current_stage, PipelineStage.FAILED)

def get_previous_stage(current_stage: PipelineStage) -> PipelineStage:
    """
    get the previous stage of the pipeline.
    """
    for key, value in STAGE_MAP.items():
        if value == current_stage:
            return key
    return PipelineStage.FAILED


class PipelineStageStatistics(BaseModel):
    """
    statistics of the pipeline stage.
    """
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[float] = None
    status: Optional[PipelineStatus] = None

class PipelineData(BaseModel):
    """
    comprehensive data model for document processing pipeline.
    holds all data from each operation in the pipeline and provides
    serialization and deserialization capabilities.
    supports multiple workflow configurations with flexible operation ordering.
    """

    # identification
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    path_id: Optional[str] = None # id used by mongodb for internal use
    name: str = Field(default="")
    description: str = Field(default="")
    tags: List[str] = Field(default_factory=list)  # tags of the pipeline
    projects: List[str] = Field(default_factory=list)  # projects of the pipeline
    
    # timing information
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # source document
    source_path: Optional[str] = None
    source_type: Optional[SourceType] = None
    
    # document_processing & image_processing operations
    parsed_content: Optional[ParsedContent] = None  # structured content from document
    images_metadata: List[ImageMetadata] = Field(default_factory=list)  # extracted and labeled images
    
    # content_analysis operation
    chunks: List[Dict[str, Any]] = Field(default_factory=list)  # processed content chunks
    video_outline: Optional[Dict[str, Any]] = None  # video structure and segment plan
    
    # script_generation operation
    script_data: Optional[Dict[str, Any]] = None  # generated narration scripts
    script_with_audio: Optional[Dict[str, Any]] = None  # scripts with voiceover audio paths
    
    # video_generation operation
    video_path: Optional[str] = None  # path to generated video file
    output_path: Optional[str] = None  # final output video path
    
    # configuration
    config: Optional[Dict[str, Any]] = None  # pipeline configuration settings
    
    # context processor information
    context_processor_info: Optional[Dict[str, Any]] = None  # stores context processor config and results
    
    # status tracking
    current_stage: PipelineStage = PipelineStage.INITIALIZED  # current operation name
    status: PipelineStatus = PipelineStatus.PENDING
    
    # timing information
    stage_statistics: Dict[PipelineStage, PipelineStageStatistics] = Field(default_factory=dict)  # {stage: {start_time, end_time, duration, status}}

    # rating information
    rating: Optional[int] = None  # rating of the pipeline
    
    # feedback information
    feedback: Optional[str] = None  # feedback from the user
    

    class Config:
        """pydantic configuration."""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def save_to_folder(self, base_dir: str) -> str:
        """
        save pipeline data to a folder as JSON files.
        creates a subfolder named with the pipeline ID.
        args:
            base_dir: base directory where pipeline data will be saved
        returns:
            path to the saved data folder
        """
        base_path = Path(base_dir)
        base_path.mkdir(parents=True, exist_ok=True)
        
        # create subfolder with pipeline ID
        folder = base_path / self.id
        folder.mkdir(parents=True, exist_ok=True)
        
        # save main data
        main_file = folder / "pipeline_data.json"
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
        
        # save individual components for easy access
        if self.parsed_content:
            with open(folder / "parsed_content.json", 'w', encoding='utf-8') as f:
                json.dump(self.parsed_content.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
        
        if self.images_metadata:
            images_dir = folder / "images"
            images_dir.mkdir(exist_ok=True)
            with open(images_dir / "images_metadata_labeled.json", 'w', encoding='utf-8') as f:
                data = [img.model_dump(mode="json") for img in self.images_metadata]
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        if self.video_outline:
            with open(folder / "video_outline.json", 'w', encoding='utf-8') as f:
                json.dump(self.video_outline, f, indent=2, ensure_ascii=False)
        
        if self.script_data:
            with open(folder / "video_script.json", 'w', encoding='utf-8') as f:
                json.dump(self.script_data, f, indent=2, ensure_ascii=False)
        
        if self.script_with_audio:
            with open(folder / "script_with_audio.json", 'w', encoding='utf-8') as f:
                json.dump(self.script_with_audio, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved pipeline data to {folder}")
        return str(folder)
    
    def save_to_pickle(self, file_path: str) -> str:
        """
        save pipeline data to a pickle file.
        
        args:
            file_path: path to pickle file
        
        returns:
            path to the saved pickle file
        """
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path_obj, 'wb') as f:
            pickle.dump(self, f)
        
        logger.info(f"Saved pipeline data to pickle: {file_path}")
        return str(file_path_obj)
    
    @classmethod
    def load_from_folder(cls, folder_path: str) -> 'PipelineData':
        """
        load pipeline data from a folder.
        can accept either a base directory with pipeline ID subfolder, or a direct path to the pipeline folder.
        args:
            folder_path: path to folder containing pipeline data (can be base_dir/pipeline_id or direct path)
        
        returns:
            pipelinedata instance
        """
        folder = Path(folder_path)
        
        # if folder doesn't exist, try treating it as base_dir/pipeline_id
        if not folder.exists():
            # check if it's a base directory with UUID subfolder
            base_dir = folder.parent
            pipeline_id = folder.name
            folder = base_dir / pipeline_id
        
        # try to load main data file
        main_file = folder / "pipeline_data.json"
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)
        
        # fallback: reconstruct from individual components
        data = {
            "id": folder.name,
            "created_at": datetime.now().isoformat()
        }
        
        parsed_file = folder / "parsed_content.json"
        if parsed_file.exists():
            with open(parsed_file, 'r', encoding='utf-8') as f:
                data["parsed_content"] = json.load(f)
        
        images_file = folder / "images" / "images_metadata_labeled.json"
        if images_file.exists():
            with open(images_file, 'r', encoding='utf-8') as f:
                data["images_metadata"] = json.load(f)
        
        outline_file = folder / "video_outline.json"
        if outline_file.exists():
            with open(outline_file, 'r', encoding='utf-8') as f:
                data["video_outline"] = json.load(f)
        
        script_file = folder / "video_script.json"
        if script_file.exists():
            with open(script_file, 'r', encoding='utf-8') as f:
                data["script_data"] = json.load(f)
        
        audio_file = folder / "script_with_audio.json"
        if audio_file.exists():
            with open(audio_file, 'r', encoding='utf-8') as f:
                data["script_with_audio"] = json.load(f)
        
        logger.info(f"Loaded pipeline data from folder: {folder}")
        return cls(**data)
    
    @classmethod
    def load_by_id(cls, pipeline_id: str, base_dir: str = "temp") -> 'PipelineData':
        """
        load pipeline data by ID from base directory.
        args:
            pipeline_id: uuid of the pipeline
            base_dir: base directory containing pipeline folders
        
        returns:
            pipelinedata instance
        
        raises:
            filenotfounderror: if pipeline folder doesn't exist
        """
        folder_path = Path(base_dir) / pipeline_id
        if not folder_path.exists():
            raise FileNotFoundError(f"Pipeline folder not found: {folder_path}")
        return cls.load_from_folder(str(folder_path))
    
    @classmethod
    def load_from_pickle(cls, file_path: str) -> 'PipelineData':
        """
        load pipeline data from a pickle file.
        args:
            file_path: path to pickle file
        
        returns:
            pipelinedata instance
        """
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        logger.info(f"Loaded pipeline data from pickle: {file_path}")
        return data
    
    def update_stage(self, stage: PipelineStage, status: PipelineStatus = PipelineStatus.IN_PROGRESS):
        """
        update current operation and status, tracking timing.
        
        note: method name 'update_stage' is kept for backward compatibility,
        but the 'stage' parameter represents the current operation name
        (e.g., 'document_processing', 'image_processing', 'content_analysis', etc.)
        
        args:
            stage: current operation name
            status: status (pending, in_progress, completed, failed)
        """
        now = datetime.now().isoformat()
        
        # if starting a new operation
        if status == "in_progress" and stage != self.current_stage:
            if stage not in self.stage_statistics:
                self.stage_statistics[stage] = PipelineStageStatistics()
            self.stage_statistics[stage].start_time = now
        
        # if completing or failing an operation
        if status in ["completed", "failed"]:
            if stage in self.stage_statistics and self.stage_statistics[stage].start_time:
                start_time = datetime.fromisoformat(self.stage_statistics[stage].start_time)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                self.stage_statistics[stage].end_time = now
                self.stage_statistics[stage].duration = duration
                self.stage_statistics[stage].status = status
        
        self.current_stage = stage
        self.status = status
    
    def get_summary(self) -> Dict[str, Any]:
        """
        get a summary of the pipeline data including operation status and timing.
        returns:
            dictionary with summary information including completed operations and timings
        """
        total_duration = sum(
            timing.get('duration', 0) 
            for timing in self.stage_timings.values() 
            if 'duration' in timing
        )
        
        return {
            "id": self.id,
            "created_at": self.created_at,
            "source_path": self.source_path,
            "source_type": self.source_type,
            "current_stage": self.current_stage,  # current operation name
            "status": self.status,
            "output_path": self.output_path,
            "has_parsed_content": self.parsed_content is not None,
            "has_images": len(self.images_metadata) > 0,
            "has_outline": self.video_outline is not None,
            "has_scripts": self.script_data is not None,
            "has_audio": self.script_with_audio is not None,
            "has_video": self.video_path is not None and os.path.exists(self.video_path) if self.video_path else False,
            "stage_timings": self.stage_timings,  # operation timings
            "total_duration": total_duration,
            "context_processor_info": self.context_processor_info
        }

