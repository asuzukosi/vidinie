from fastapi import APIRouter, File, UploadFile, Form, HTTPException
# from pipeline.stage1_parsing import parse_document
# from pipeline.stage2_content import create_video_outline
# from pipeline.stage3_script import generate_scripts_and_voiceovers
# from pipeline.stage4_video import generate_video
from core.pipeline_data import PipelineData, SourceType, PipelineStage, PipelineStatus, ParsedContent
from utils.logger import setup_logging, get_logger
from pydantic import BaseModel
from typing import List, Any
import os
from pathlib import Path
from api.core.db import pipelines_collection
from utils.config_loader import get_config
from core.processors.pdf_processor import PDFProcessor
from core.processors.html_processor import HTMLProcessor
from bson.objectid import ObjectId
from datetime import datetime
from typing import Optional
from pydantic import Field
import requests

# setup logging
setup_logging(log_dir='temp')
logger = get_logger('pipelines')

# get config
config = get_config()

router = APIRouter(tags=["pipelines"])

class StartPipelineRequest(BaseModel):
    url: str
    name: str
    description: str
    tags: List[str]
    projects: List[str]


class CreatePipelineDataResponse(BaseModel):
    # identification
    id: str
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

@router.post("/start_pipeline_with_file", name="start pipeline with file")
async def start_pipeline_with_file(
    name: str = Form(...),
    description: str = Form(...),
    tags: List[str] = Form(...),
    projects: List[str] = Form(...),
    file: UploadFile = File(...),
) -> CreatePipelineDataResponse:
    logger.info("received request to start pipeline with file")
    if file.filename == "" or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type must be a PDF file")
    # create pipeline data object
    logger.info("creating pipeline data object")
    pipeline_data = PipelineData()
    pipeline_data.name = name
    pipeline_data.description = description
    pipeline_data.tags = tags[0].split(",")
    pipeline_data.projects = projects[0].split(",")
    pipeline_data.source_type = SourceType.PDF
    pipeline_data.update_stage(PipelineStage.DOCUMENT_PROCESSING, PipelineStatus.IN_PROGRESS)
    logger.info("pipeline data object created")

    # create temp directory for metadata
    temp_dir = config.get('output.temp_directory', 'temp')
    images_dir = os.path.join(temp_dir, pipeline_data.id, 'images')
    Path(images_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"created temp directory for metadata: {images_dir}")
    # save file to temp directory
    with open(os.path.join(temp_dir, pipeline_data.id, file.filename), 'wb') as f:
        f.write(file.file.read())
    logger.info(f"saved file to temp directory: {os.path.join(temp_dir, pipeline_data.id, file.filename)}")
    pipeline_data.source_path = os.path.join(temp_dir, pipeline_data.id, file.filename)
    
    # process pdf file
    with PDFProcessor(pipeline_data.source_path, images_output_dir=images_dir) as processor:
        content: ParsedContent = processor.extract_structured_content()
        pipeline_data.parsed_content = content

        # logging content info
        logger.info(f"title: {content.title}")
        logger.info(f"total pages: {content.total_pages}")
        logger.info(f"sections: {len(content.sections)}")

         # extract and label images if requested
        logger.info("labeling images")
        processor.label_images(config.openai_api_key, config.get_prompts_directory())
        pipeline_data.images_metadata = processor.images_metadata
        logger.info(f"labeled {len(processor.images_metadata)} images")
    
    pipeline_data.update_stage(PipelineStage.DOCUMENT_PROCESSING, PipelineStatus.COMPLETED)

    # save pipeline data to database
    logger.info("saving pipeline data to database")
    db_pipeline = await pipelines_collection.insert_one(pipeline_data.model_dump(mode="json"))
    pipeline_data.path_id = pipeline_data.id
    pipeline_data.id = str(db_pipeline.inserted_id)
    logger.info(f"pipeline data saved to database with id: {pipeline_data.id}")
    return CreatePipelineDataResponse(**pipeline_data.model_dump(mode="json"))

@router.post("/start_pipeline_with_url", name="start pipeline with url")
async def start_pipeline_with_url(request: StartPipelineRequest) -> Any:
    # validate if url is valid
    logger.info("received request to start pipeline with url")
    if not request.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL must start with http or https")
    # validate if url is reachable
    response = None
    try:
        response = requests.get(request.url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download file")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=400, detail="Failed to download file")
    
    logger.info("creating pipeline data object")
    pipeline_data = PipelineData()
    pipeline_data.name = request.name
    pipeline_data.description = request.description
    pipeline_data.tags = request.tags
    pipeline_data.projects = request.projects
    pipeline_data.source_type = SourceType.HTML
    pipeline_data.update_stage(PipelineStage.DOCUMENT_PROCESSING, 
                               PipelineStatus.IN_PROGRESS)
    
    
    logger.info("pipeline data object created")
    # create temp directory for metadata
    temp_dir = config.get('output.temp_directory', 'temp')
    images_dir = os.path.join(temp_dir, pipeline_data.id, 'images')
    Path(images_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"created temp directory for metadata: {images_dir}")
    # save file to temp directory
    with open(os.path.join(temp_dir, pipeline_data.id, 'data.html'), 'wb') as f:
        f.write(response.content)
    logger.info(f"saved file to temp directory: {os.path.join(temp_dir, pipeline_data.id, 'data.html')}")
    pipeline_data.source_path = os.path.join(temp_dir, pipeline_data.id, 'data.html')
    
   # process html file
    with HTMLProcessor(html_path=request.url, images_output_dir=images_dir) as processor:
        content: ParsedContent = processor.extract_structured_content()
        pipeline_data.parsed_content = content

        # logging content info
        logger.info(f"title: {content.title}")
        logger.info(f"total pages: {content.total_pages}")
        logger.info(f"sections: {len(content.sections)}")

         # extract and label images if requested
        logger.info("labeling images")
        processor.label_images(config.openai_api_key, config.get_prompts_directory())
        pipeline_data.images_metadata = processor.images_metadata
        logger.info(f"labeled {len(processor.images_metadata)} images")
    
    pipeline_data.update_stage(PipelineStage.DOCUMENT_PROCESSING, PipelineStatus.COMPLETED)

    # save pipeline data to database
    logger.info("saving pipeline data to database")
    db_pipeline = await pipelines_collection.insert_one(pipeline_data.model_dump(mode="json"))
    pipeline_data.path_id = pipeline_data.id
    pipeline_data.id = str(db_pipeline.inserted_id)
    logger.info(f"pipeline data saved to database with id: {pipeline_data.id}")
    return CreatePipelineDataResponse(**pipeline_data.model_dump(mode="json"))

# @router.post("/parse_document")
# async def parse_document_route(request: ParseDocumentRequest) -> PipelineData:
#     pipeline_data = parse_document(request.pdf_path, request.extract_images)
#     return pipeline_data

# class CreateVideoOutlineRequest(BaseModel):
#     skip_stock: bool = False
#     target_segments: int = 7
#     segment_duration: int = 45

# @router.post("/create_video_outline/{pipeline_id}")
# async def create_video_outline_route(pipeline_id: str, 
#                                     request: CreateVideoOutlineRequest) -> PipelineData:
#     pipeline_data = create_video_outline(pipeline_id, request.skip_stock, request.target_segments, request.segment_duration)
#     return pipeline_data

# class GenerateScriptsAndVoiceoversRequest(BaseModel):
#     provider: Optional[str] = None

# @router.post("/generate_scripts_and_voiceovers/{pipeline_id}")
# async def generate_scripts_and_voiceovers_route(pipeline_id: str, 
#                                                 request: GenerateScriptsAndVoiceoversRequest) -> PipelineData:
#     pipeline_data = generate_scripts_and_voiceovers(pipeline_id, request.provider)
#     return pipeline_data

# class GenerateVideoRequest(BaseModel):
#     output_path: Optional[str] = None

# @router.post("/generate_video/{pipeline_id}")
# async def generate_video_route(pipeline_id: str, 
#                                 request: GenerateVideoRequest) -> PipelineData:
#     pipeline_data = generate_video(pipeline_id, request.output_path)
#     return pipeline_data

# class RunFullPipelineRequest(BaseModel):
#     pdf_path: str
#     extract_images: bool = True
#     skip_stock: bool = False
#     target_segments: int = 7
#     segment_duration: int = 45
#     provider: Optional[str] = None
#     output_path: Optional[str] = None

# @router.post("/run_full_pipeline")
# async def run_full_pipeline(request: RunFullPipelineRequest) -> PipelineData:
#     pipeline_data = parse_document(request.pdf_path, request.extract_images)
#     pipeline_data = create_video_outline(pipeline_data.id, request.skip_stock, request.target_segments, request.segment_duration)
#     pipeline_data = generate_scripts_and_voiceovers(pipeline_data.id, request.provider)
#     pipeline_data = generate_video(pipeline_data.id, request.output_path)
#     return pipeline_data

# @router.post("/create")
# async def create_pipeline(request: VideoGenerationRequest):
#     return {"message": "Pipeline created successfully"}

# @router.get("/get")
# async def get_pipeline(pipeline_id: str):
#     return {"message": "Pipeline retrieved successfully"}

# @router.put("/update")
# def update_pipeline(pipeline_id: str, request: VideoGenerationRequest):
#     return {"message": "Pipeline updated successfully"}

# @router.delete("/delete")
# def delete_pipeline(pipeline_id: str):
#     return {"message": "Pipeline deleted successfully"}

# @router.get("/list")
# def list_pipelines():
#     return {"message": "Pipelines listed successfully"}

# def get_all_active_pipelines():
#     pass

# def get_all_fonts():
#     pass

# def pause_pipeline(pipeline_id: str):
#     pass

# def resume_pipeline(pipeline_id: str):
#     pass

# def cancel_pipeline(pipeline_id: str):
#     pass

# def get_pipeline_status(pipeline_id: str):
#     pass

# def get_pipeline_progress(pipeline_id: str):
#     pass

# def redo_pipeline_phase(pipeline_id: str, phase: str):
#     pass

# def get_pipeline_logs(pipeline_id: str):
#     pass

# def get_pipeline_errors(pipeline_id: str):
#     pass

# def get_pipeline_warnings(pipeline_id: str):
#     pass

# def get_pipeline_info(pipeline_id: str):
#     pass