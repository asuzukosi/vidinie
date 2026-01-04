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
from core.data.enums import SourceType, VideoPipelineStatus, VideoPipelineStage
from core.data.content_models import (
    VideoPipelineParsedContent,
    VideoPipelineContextChunk,
    VideoPipelineContextProcessor
)
from core.data.image_models import VideoPipelineImageMetadata
from core.data.segment_models import VideoPipelineOutline
from core.data.script_models import VideoPipelineScript
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
    description: str = Field(default="")
    tags: List[str] = Field(default_factory=list)  # tags of the video pipeline
    projects: List[str] = Field(default_factory=list)  # projects of the video pipeline

    # timing information
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # source document
    source_path: Optional[str] = None
    source_type: Optional[SourceType] = None

    # document_processing & image_processing operations
    parsed_content: Optional[VideoPipelineParsedContent] = None  # structured content from document
    images_metadata: List[VideoPipelineImageMetadata] = Field(default_factory=list)  # extracted and labeled images

    # content_analysis operation
    chunks: List[VideoPipelineContextChunk] = Field(default_factory=list)  # processed content chunks
    video_outline: Optional[VideoPipelineOutline] = None  # video structure and segment plan

    # script_generation operation
    script_data: Optional[VideoPipelineScript] = None  # generated narration scripts
    full_audio_path: Optional[str] = None  # path to generated full audio file
    full_audio_duration: Optional[float] = None  # duration of generated full audio file

    # video_generation operation
    video_path: Optional[str] = None  # path to generated video file
    output_path: Optional[str] = None  # final output video path

    # configuration
    config: Optional[Dict[str, Any]] = None  # video pipeline configuration settings

    # status tracking
    current_stage: VideoPipelineStage = VideoPipelineStage.INITIALIZED  # current operation name
    status: VideoPipelineStatus = VideoPipelineStatus.PENDING
    
    # stage status tracking (used for workflow status management)
    stage_statuses: Dict[VideoPipelineStage, VideoPipelineStatus] = Field(
        default_factory=lambda: {
            VideoPipelineStage.INITIALIZED: VideoPipelineStatus.PENDING,
            VideoPipelineStage.DOCUMENT_PROCESSING: VideoPipelineStatus.PENDING,
            VideoPipelineStage.IMAGE_PROCESSING: VideoPipelineStatus.PENDING,
            VideoPipelineStage.CONTENT_ANALYSIS: VideoPipelineStatus.PENDING,
            VideoPipelineStage.SCRIPT_GENERATION: VideoPipelineStatus.PENDING,
            VideoPipelineStage.VIDEO_GENERATION: VideoPipelineStatus.PENDING,
        }
    )

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

        if self.script_data:
            with open(folder / "video_script.json", 'w', encoding='utf-8') as f:
                json.dump(self.script_data, f, indent=2, ensure_ascii=False)

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

        script_file = folder / "video_script.json"
        if script_file.exists():
            with open(script_file, 'r', encoding='utf-8') as f:
                data["script_data"] = json.load(f)

        audio_file = folder / "script_with_audio.json"
        if audio_file.exists():
            with open(audio_file, 'r', encoding='utf-8') as f:
                data["script_with_audio"] = json.load(f)

        logger.info(f"Loaded video pipeline data from folder: {folder}")
        return cls(**data)

    @classmethod
    def load_by_id(cls, video_pipeline_id: str, base_dir: str = "temp") -> 'VideoPipeline':
        """
        load video pipeline data by ID from base directory.
        args:
            video_pipeline_id: uuid of the video pipeline
            base_dir: base directory containing video pipeline folders
        returns:
            VideoPipeline instance
        raises:
            FileNotFoundError: if video pipeline folder doesn't exist
        """
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
        Args:
            stage: current operation name (e.g., 'document_processing', 'content_analysis', etc.)
            status: status (pending, in_progress, completed, failed)
        """
        # update stage status tracking
        self.stage_statuses[stage] = status
        
        # Update current stage and overall status
        self.current_stage = stage
        self.status = status
        
        # initialize stages that haven't been set yet as pending
        # only initialize stages that come before the current stage
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
            if s not in self.stage_statuses:
                if i < current_stage_index:
                    # previous stages that haven't been set should be COMPLETED if we're past them
                    self.stage_statuses[s] = VideoPipelineStatus.COMPLETED
                elif i == current_stage_index:
                    # current stage status is already set above
                    pass
                else:
                    # future stages should be pending
                    self.stage_statuses[s] = VideoPipelineStatus.PENDING
    
    def get_stage_status(self, stage: VideoPipelineStage) -> VideoPipelineStatus:
        """
        get the status of a specific stage.
        args:
            stage: the stage to get status for
        returns:
            the status of the stage, or pending if not set
        """
        return self.stage_statuses.get(stage, VideoPipelineStatus.PENDING)

