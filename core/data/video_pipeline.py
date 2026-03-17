"""
video pipeline model.
holds all data from each operation in the pipeline and provides
serialization and deserialization capabilities.
supports multiple workflow configurations with flexible operation ordering.
"""

import json
import pickle
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from core.utils.logger import get_logger
from core.utils.config_loader import config
from core.data.enums import SourceType, VideoPipelineStatus, VideoPipelineStage
from core.data.content_models import (
    ParsedContent,
)
from core.data.image_models import ImageMetadata
from core.data.segment_models import VideoOutline
from core.data.statistics_models import VideoPipelineStageStatistics

logger = get_logger('pipeline_data')


class VideoPipeline(BaseModel):
    """
    comprehensive data model for video generation pipeline.
    holds all data from each operation in the pipeline and provides
    serialization and deserialization capabilities.
    supports multiple workflow configurations with flexible operation ordering.
    """

    # identification
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None # user id of the user who created the video pipeline
    name: str = Field(default="")
    instructions: str  # user instructions to guide AI operations (required)
    voice: str  # audio voice selection for narration (required)

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
    content: Optional[str] = None  # processed content
    video_outline: Optional[VideoOutline] = None  # video structure and segment plan

    # script_generation operation
    full_audio_path: Optional[str] = None  # path to generated full audio file
    full_audio_duration: Optional[float] = None  # duration of generated full audio file

    # video_generation operation
    video_path: Optional[str] = None  # path to generated video file
    output_path: Optional[str] = None  # final output video path

    # configuration
    config: Optional[Dict[str, Any]] = None  # video pipeline configuration settings

    # status tracking - flat structure for easier frontend access
    current_stage: VideoPipelineStage = VideoPipelineStage.INITIALIZED  # current operation name
    status: VideoPipelineStatus = VideoPipelineStatus.PENDING
    
    # individual stage statuses (flat structure)
    initialized_status: VideoPipelineStatus = VideoPipelineStatus.PENDING
    document_processing_status: VideoPipelineStatus = VideoPipelineStatus.PENDING
    image_processing_status: VideoPipelineStatus = VideoPipelineStatus.PENDING
    content_analysis_status: VideoPipelineStatus = VideoPipelineStatus.PENDING
    script_generation_status: VideoPipelineStatus = VideoPipelineStatus.PENDING
    video_generation_status: VideoPipelineStatus = VideoPipelineStatus.PENDING

    stage_statistics: Dict[VideoPipelineStage, VideoPipelineStageStatistics] = Field(
        default_factory=dict
    )

    # rating information
    rating: Optional[int] = None  # rating of the video pipeline

    # feedback information
    feedback: Optional[str] = None  # feedback from the user

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def save_to_folder(self, base_dir: str) -> str:
        """
        save video pipeline data to a folder as JSON files.
        creates a subfolder named with the video pipeline ID.
        args:
            base_dir: base directory where video pipeline data will be saved
        returns:
            path to the saved data folder
        """
        base_path = Path(base_dir)
        base_path.mkdir(parents=True, exist_ok=True)

        # create subfolder with video pipeline id
        folder = base_path / self.id
        folder.mkdir(parents=True, exist_ok=True)

        # save main data
        main_file = folder / "video_pipeline_data.json"
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
                json.dump(self.video_outline.model_dump(mode="json"), f, indent=2, ensure_ascii=False)


        logger.info(f"Saved video pipeline data to {folder}")
        return str(folder)

    def save_to_pickle(self, file_path: str) -> str:
        """
        save video pipeline data to a pickle file.
        args:
            file_path: path to pickle file
        returns:
            path to the saved pickle file
        """
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path_obj, 'wb') as f:
            pickle.dump(self, f)

        logger.info(f"Saved video pipeline data to pickle: {file_path}")
        return str(file_path_obj)

    @classmethod
    def load_from_folder(cls, folder_path: str) -> 'VideoPipeline':
        """
        load video pipeline data from a folder.
        Can accept either a base directory with video pipeline ID subfolder, or a direct path to the video pipeline folder.
        args:
            folder_path: path to folder containing video pipeline data (can be base_dir/video_pipeline_id or direct path)
        returns:
            VideoPipeline instance
        """
        folder = Path(folder_path)

        # if folder doesn't exist, try treating it as base_dir/video_pipeline_id
        if not folder.exists():
            # check if it's a base directory with UUID subfolder
            base_dir = folder.parent
            video_pipeline_id = folder.name
            folder = base_dir / video_pipeline_id

        # try to load main data file (new name)
        main_file = folder / "video_pipeline_data.json"
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)

        # try to load old pipeline_data.json for backward compatibility
        old_main_file = folder / "pipeline_data.json"
        if old_main_file.exists():
            with open(old_main_file, 'r', encoding='utf-8') as f:
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

        logger.info(f"Loaded video pipeline data from folder: {folder}")
        return cls(**data)

    @classmethod
    def load_by_id(cls, video_pipeline_id: str, base_dir: Optional[str] = None) -> 'VideoPipeline':
        """
        load video pipeline data by ID from base directory.
        args:
            video_pipeline_id: uuid of the video pipeline
            base_dir: base directory containing video pipeline folders (defaults to config.output_directory)
        returns:
            VideoPipeline instance
        raises:
            FileNotFoundError: if video pipeline folder doesn't exist
        """
        if base_dir is None:
            base_dir = str(config.output_directory)
        folder_path = Path(base_dir) / video_pipeline_id
        if not folder_path.exists():
            raise FileNotFoundError(f"Video pipeline folder not found: {folder_path}")
        return cls.load_from_folder(str(folder_path))

    @classmethod
    def load_from_pickle(cls, file_path: str) -> 'VideoPipeline':
        """
        load video pipeline data from a pickle file.
        args:
            file_path: path to pickle file
        returns:
            VideoPipeline instance
        """
        with open(file_path, 'rb') as f:
            data = pickle.load(f)

        logger.info(f"Loaded video pipeline data from pickle: {file_path}")
        return data

    def update_stage(self, stage: VideoPipelineStage, status: VideoPipelineStatus = VideoPipelineStatus.IN_PROGRESS):
        """
        update current operation and status, tracking stage statuses.
        """
        # update the specific stage status field
        if stage == VideoPipelineStage.INITIALIZED:
            self.initialized_status = status
        elif stage == VideoPipelineStage.DOCUMENT_PROCESSING:
            self.document_processing_status = status
        elif stage == VideoPipelineStage.IMAGE_PROCESSING:
            self.image_processing_status = status
        elif stage == VideoPipelineStage.CONTENT_ANALYSIS:
            self.content_analysis_status = status
        elif stage == VideoPipelineStage.SCRIPT_GENERATION:
            self.script_generation_status = status
        elif stage == VideoPipelineStage.VIDEO_GENERATION:
            self.video_generation_status = status
        
        # update current stage and overall status
        self.current_stage = stage
        self.status = status
        
        # auto-complete previous stages if we're moving forward
        all_stages = [
            VideoPipelineStage.INITIALIZED,
            VideoPipelineStage.DOCUMENT_PROCESSING,
            VideoPipelineStage.IMAGE_PROCESSING,
            VideoPipelineStage.CONTENT_ANALYSIS,
            VideoPipelineStage.SCRIPT_GENERATION,
            VideoPipelineStage.VIDEO_GENERATION,
        ]
        
        current_stage_index = all_stages.index(stage) if stage in all_stages else -1
        for i, s in enumerate(all_stages):
            if i < current_stage_index:
                # previous stages should be COMPLETED if we're past them
                if s == VideoPipelineStage.INITIALIZED and self.initialized_status == VideoPipelineStatus.PENDING:
                    self.initialized_status = VideoPipelineStatus.COMPLETED
                elif s == VideoPipelineStage.DOCUMENT_PROCESSING and self.document_processing_status == VideoPipelineStatus.PENDING:
                    self.document_processing_status = VideoPipelineStatus.COMPLETED
                elif s == VideoPipelineStage.IMAGE_PROCESSING and self.image_processing_status == VideoPipelineStatus.PENDING:
                    self.image_processing_status = VideoPipelineStatus.COMPLETED
                elif s == VideoPipelineStage.CONTENT_ANALYSIS and self.content_analysis_status == VideoPipelineStatus.PENDING:
                    self.content_analysis_status = VideoPipelineStatus.COMPLETED
                elif s == VideoPipelineStage.SCRIPT_GENERATION and self.script_generation_status == VideoPipelineStatus.PENDING:
                    self.script_generation_status = VideoPipelineStatus.COMPLETED
    
    def get_stage_status(self, stage: VideoPipelineStage) -> VideoPipelineStatus:
        """
        get the status of a specific stage.
        """
        if stage == VideoPipelineStage.INITIALIZED:
            return self.initialized_status
        elif stage == VideoPipelineStage.DOCUMENT_PROCESSING:
            return self.document_processing_status
        elif stage == VideoPipelineStage.IMAGE_PROCESSING:
            return self.image_processing_status
        elif stage == VideoPipelineStage.CONTENT_ANALYSIS:
            return self.content_analysis_status
        elif stage == VideoPipelineStage.SCRIPT_GENERATION:
            return self.script_generation_status
        elif stage == VideoPipelineStage.VIDEO_GENERATION:
            return self.video_generation_status
        return VideoPipelineStatus.PENDING

