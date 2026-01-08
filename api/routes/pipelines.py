from fastapi import APIRouter, File, UploadFile, Form,\
                    HTTPException, Request, \
                    WebSocket, BackgroundTasks,\
                    Depends, WebSocketDisconnect
import re
from fastapi.responses import StreamingResponse, FileResponse
from core.data import (
    VideoPipeline,
    SourceType,
    VideoPipelineStage,
    VideoPipelineStatus,
    VideoPipelineSegment,
    VideoPipelineContentSection,
    VideoPipelineImageMetadata,
)
import asyncio
from api.data.users import User
from api.core.auth import JWTBearer
from core.utils.logger import setup_logging, get_logger
from api.operations.document_operations import (
    process_pdf_document,
    process_html_document,
)
from api.operations.content_operations import (
    process_content,
    add_section_to_content as add_section_to_pipeline,
    delete_section_from_content as delete_section_from_pipeline,
    add_segment_to_outline,
    delete_segment_from_outline,
)
from api.operations.script_operations import generate_scripts
from api.operations.video_operations import generate_video
from api.operations.image_operations import (
    add_image_to_pipeline,
    delete_image_from_pipeline,
)
from api.helpers.pipeline_helpers import (
    get_pipeline_by_id,
    update_pipeline_in_db,
    create_pipeline_in_db,
    get_pipelines_for_user,
    delete_pipeline_from_db,
)
from api.helpers.user_helpers import get_user_by_id
import os
from pathlib import Path
from api.data.pipelines import CreateVideoPipelineRequest, VideoPipelineSummary, \
                               DeleteVideoPipelineResponse, DeleteVideoPipelineImageResponse, \
                               DeleteVideoPipelineSectionResponse, \
                               CreateVideoPipelineOutlineRequest, CreateVideoPipelineScriptRequest, \
                               VideoPipelineReviewRequest, VideoResolution, GenerateVideoPipelineRequest
from core.utils.config_loader import config
from datetime import datetime
from typing import Optional, Tuple, List
import shutil
import requests
from api.utils.error_wrapper import error_wrapper
from api.core.signals import broadcast_message, listen_for_messages


# setup logging
setup_logging(log_dir='temp')
logger = get_logger('pipelines')


router = APIRouter(tags=["pipelines"])

# keep track of resolutions in a map for easy lookup
resolution_map = {
    VideoResolution.RESOLUTION_4K: (3840, 2160),
    VideoResolution.RESOLUTION_1080P: (1920, 1080),
    VideoResolution.RESOLUTION_720P: (1280, 720),
    VideoResolution.RESOLUTION_480P: (640, 480),
}


# special utility function to write content to file for pipeline
async def write_content_to_file_for_pipeline(video_pipeline: VideoPipeline, 
                                             filename: str, 
                                             file_content: bytes) -> None:
    # now save file to disk with the final id
    temp_dir = config.get('output.temp_directory', 'temp')
    pipeline_dir = os.path.join(temp_dir, video_pipeline.id, "source")
    Path(pipeline_dir).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(pipeline_dir, filename)
    with open(file_path, 'wb') as f:
        f.write(file_content)
    video_pipeline.source_path = file_path
    await update_pipeline_in_db(video_pipeline.id, video_pipeline)
    broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "pipeline_file_written", "pipeline_id": video_pipeline.id, "file_path": file_path})
    logger.info(f"pipeline data saved to database with id: {video_pipeline.id}, file saved to: {file_path}")

# special utility function to delete pipeline temp directory
async def delete_pipeline_temp_directory(video_pipeline: VideoPipeline) -> None:
    # delete temp directory for pipeline
    temp_dir = config.get('output.temp_directory', 'temp')
    pipeline_dir = os.path.join(temp_dir, video_pipeline.id)
    if os.path.exists(pipeline_dir):
        shutil.rmtree(pipeline_dir)
        logger.info(f"temp directory deleted successfully with id: {video_pipeline.id}")
    else:
        logger.info(f"no temp directory found for pipeline with id: {video_pipeline.id}")


# pipeline stages to run in the order they are executed
PIPELINE_STAGES = [
    VideoPipelineStage.DOCUMENT_PROCESSING,
    VideoPipelineStage.CONTENT_ANALYSIS,
    VideoPipelineStage.SCRIPT_GENERATION,
    VideoPipelineStage.VIDEO_GENERATION,
]
# special utility function to run all the stages sequentialy
async def run_next_stages(video_pipeline: VideoPipeline, stage: Optional[VideoPipelineStage] = None, **kwargs) -> VideoPipeline:
    # get all stages after the current stage
    logger.info(f"running next stages after: {stage}")
    # get all stages after the current stage
    if stage:
        # if a stage is specified, run all stages after it
        tasks_to_run = PIPELINE_STAGES[PIPELINE_STAGES.index(stage):]
    else:
        # if no stage is specified, run all stages
        tasks_to_run = PIPELINE_STAGES
    logger.info(f"tasks to run: {tasks_to_run}")
    
    # run each task in the order they are specified
    
    # check and run document processing task
    if VideoPipelineStage.DOCUMENT_PROCESSING in tasks_to_run:
        if video_pipeline.source_type == SourceType.PDF:
            logger.info(f"running document processing task for pipeline: {video_pipeline.id}")
            broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "document_processing", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.IN_PROGRESS})
            # extract all the arguments from kwargs
            extract_images = kwargs.get('extract_images', True)
            pdf_content = kwargs.get('pdf_content', None)
            pdf_path = kwargs.get('pdf_path', None)
            if not pdf_content and not pdf_path:
                raise ValueError("either pdf_content or pdf_path must be provided")
            if pdf_content:
                video_pipeline = process_pdf_document(video_pipeline, 
                                                    extract_images=extract_images, 
                                                    pdf_content=pdf_content)
            elif pdf_path:
                video_pipeline = process_pdf_document(video_pipeline, 
                                                    extract_images=extract_images, 
                                                    pdf_path=pdf_path)
            else:
                raise ValueError("either pdf_content or pdf_path must be provided")
            # update database
            await update_pipeline_in_db(video_pipeline.id, video_pipeline)
            # broadcast message
            broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "document_processed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.COMPLETED})
            logger.info(f"document processing task completed for pipeline: {video_pipeline.id}")
        elif video_pipeline.source_type == SourceType.HTML:
            logger.info(f"running document processing task for pipeline: {video_pipeline.id}")
            broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "document_processing", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.IN_PROGRESS})
            # extract all the arguments from kwargs
            extract_images = kwargs.get('extract_images', True)
            html_content = kwargs.get('html_content', None)
            html_path = kwargs.get('html_path', None)
            if not html_content and not html_path:
                raise ValueError("either html_content or html_path must be provided")
            if html_content:
                video_pipeline = process_html_document(video_pipeline, 
                                                    extract_images=extract_images, 
                                                    html_content=html_content)
            elif html_path:
                video_pipeline = process_html_document(video_pipeline, 
                                                    extract_images=extract_images, 
                                                    html_path=html_path)
            else:
                raise ValueError("either html_content or html_path must be provided")
                
            # update database
            await update_pipeline_in_db(video_pipeline.id, video_pipeline)
            # broadcast message
            broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "document_processed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.COMPLETED})
            logger.info(f"document processing task completed for pipeline: {video_pipeline.id}")
        else:
            raise ValueError(f"unsupported source type: {video_pipeline.source_type}")
    
    # check and run content analysis task
    if VideoPipelineStage.CONTENT_ANALYSIS in tasks_to_run:
        logger.info(f"running content analysis task for pipeline: {video_pipeline.id}")
        broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "content_analysis", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.IN_PROGRESS})
        # process content
        skip_stock = kwargs.get('skip_stock', False)
        target_segments = kwargs.get('target_segments', 7)
        segment_duration = kwargs.get('segment_duration', 45)
        # process content
        video_pipeline = process_content(video_pipeline, 
                                         skip_stock=skip_stock, 
                                         target_segments=target_segments, 
                                         segment_duration=segment_duration)
        # update database
        await update_pipeline_in_db(video_pipeline.id, video_pipeline)
        broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "content_processed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.COMPLETED})
        logger.info(f"content analysis task completed for pipeline: {video_pipeline.id}")
    
    # check and run script genratiion task
    if VideoPipelineStage.SCRIPT_GENERATION in tasks_to_run:
        logger.info(f"running script generation task for pipeline: {video_pipeline.id}")
        broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "script_generation", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.IN_PROGRESS})
        # extract all the arguments from kwargs
        provider = kwargs.get('provider', 'elevenlabs')
        voice_id = kwargs.get('voice_id', None)
        video_pipeline = generate_scripts(video_pipeline, provider=provider, voice_id=voice_id)
        # update database
        await update_pipeline_in_db(video_pipeline.id, video_pipeline)
        # broadcast message
        broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "scripts_generated", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.COMPLETED})
        logger.info(f"script generation task completed for pipeline: {video_pipeline.id}")
    
    # check and run video generation task
    if VideoPipelineStage.VIDEO_GENERATION in tasks_to_run:
        logger.info(f"running video generation task for pipeline: {video_pipeline.id}")
        broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "video_generation", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.IN_PROGRESS})
        video_pipeline = generate_video(video_pipeline)
        await update_pipeline_in_db(video_pipeline.id, video_pipeline)
        broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "video_generated", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.COMPLETED})
        logger.info(f"video generation task completed for pipeline: {video_pipeline.id}")

    # all tasks completed for pipeline
    logger.info(f"all tasks completed for pipeline: {video_pipeline.id}")
    broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "pipeline_completed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.COMPLETED})
    logger.info(f"pipeline completed for pipeline: {video_pipeline.id}")
    return video_pipeline

@router.post("/from-file", name="create video pipeline from file", dependencies=[Depends(JWTBearer())])
@error_wrapper("create video pipeline from file")
async def create_video_pipeline_from_file(
    name: str = Form(...),
    description: str = Form(...),
    tags: Optional[List[str]] = Form(...),
    projects: Optional[List[str]] = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(JWTBearer()),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> VideoPipelineSummary:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to start pipeline with file")
    if file.filename == "" or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail=f"invalid file type, only pdf files currently supported: {file.filename}")
    # read file content into memory
    file_content = await file.read()
    logger.info(f"read file content into memory: {len(file_content)} bytes")
    # create pipeline data object
    logger.info("creating pipeline data object")
    video_pipeline = VideoPipeline(
        user_id=user.id,
        name=name,
        description=description,
        tags=tags[0].split(",") if tags and tags[0] else [],
        projects=projects[0].split(",") if projects and projects[0] else [],
        source_type=SourceType.PDF,
        stage_statuses={VideoPipelineStage.DOCUMENT_PROCESSING: VideoPipelineStatus.IN_PROGRESS}
    )
    logger.info("pipeline data object created")
    video_pipeline = await create_pipeline_in_db(video_pipeline)
    broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "pipeline_created", "pipeline_id": video_pipeline.id})
    await write_content_to_file_for_pipeline(video_pipeline, file.filename, file_content)

    # run all the stages sequentially in the background
    background_tasks.add_task(run_next_stages, video_pipeline, stage=VideoPipelineStage.DOCUMENT_PROCESSING, pdf_content=file_content, pdf_path=file.filename)
    # return pipeline summary
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))

@router.post("/from-url", name="create video pipeline from url", dependencies=[Depends(JWTBearer())])
@error_wrapper("create video pipeline from url")
async def create_video_pipeline_from_url(request: CreateVideoPipelineRequest,
                                         user_id: str = Depends(JWTBearer()),
                                         background_tasks: BackgroundTasks = BackgroundTasks()) -> VideoPipelineSummary:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # validate if url is valid
    logger.info("received request to start pipeline with url")
    if not request.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL must start with http or https")
    # validate if url is reachable
    response = None
    try:
        response = requests.get(request.url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to download file from url: {request.url} with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download file from url: {request.url} with error: {str(e)}")
    logger.info("creating pipeline data object")
    video_pipeline = VideoPipeline(
        user_id=user.id,
        name=request.name,
        description=request.description,
        tags=request.tags or [],
        projects=request.projects or [],
        source_type=SourceType.HTML,
        stage_statuses={VideoPipelineStage.DOCUMENT_PROCESSING: VideoPipelineStatus.IN_PROGRESS}
    )
    # save pipeline data to database first
    logger.info("saving pipeline data to database")
    video_pipeline = await create_pipeline_in_db(video_pipeline)
    broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "pipeline_created", "pipeline_id": video_pipeline.id})
    await write_content_to_file_for_pipeline(video_pipeline, 'data.html', response.content)
    # run all the stages sequentially in the background
    background_tasks.add_task(run_next_stages, video_pipeline, stage=VideoPipelineStage.DOCUMENT_PROCESSING, html_content=response.text, html_path='data.html')
    # return pipeline summary
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))

@router.get("/", name="get all video pipelines")
@error_wrapper("get all video pipelines")
async def get_all_video_pipelines(user_id: str = Depends(JWTBearer())) -> List[VideoPipelineSummary]:
    # verify user exists using helper
    await get_user_by_id(user_id)
    logger.info("received request to get all pipelines")
    # get pipelines using helper
    pipelines = await get_pipelines_for_user(user_id)
    return pipelines

@router.get("/{video_pipeline_id}", name="get video pipeline details")
@error_wrapper("get video pipeline details")
async def get_video_pipeline_details(video_pipeline_id: str, user_id: str = Depends(JWTBearer())) -> VideoPipeline:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to get pipeline details")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    if not video_pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    if video_pipeline.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return VideoPipeline(**video_pipeline.model_dump(mode="json"), id=video_pipeline.id)

@router.delete("/{video_pipeline_id}", name="delete video pipeline", 
               dependencies=[Depends(JWTBearer())])
@error_wrapper("delete video pipeline")
async def delete_video_pipeline(video_pipeline_id: str, 
                                user_id: str = Depends(JWTBearer()),
                                background_tasks: BackgroundTasks = BackgroundTasks()) -> DeleteVideoPipelineResponse:
    # verify user exists using helper
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to delete pipeline")
    # get pipeline using helper
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    if video_pipeline.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    logger.info(f"deleting pipeline with id: {video_pipeline_id}")
    # delete pipeline from database using helper
    await delete_pipeline_from_db(video_pipeline_id)
    # delete temp directory in background
    background_tasks.add_task(delete_pipeline_temp_directory, video_pipeline)
    # broadcast deletion message
    broadcast_message(f"pipeline-tasks-{video_pipeline_id}", {"type": "pipeline_deleted", "pipeline_id": video_pipeline_id})
    return DeleteVideoPipelineResponse(video_pipeline_id=video_pipeline_id, message="Pipeline deleted successfully")

@router.post("/{video_pipeline_id}/images", name="add video pipeline image", 
               dependencies=[Depends(JWTBearer())])
@error_wrapper("add video pipeline image")
async def add_video_pipeline_image(video_pipeline_id: str, image: UploadFile,
                             text_context: Optional[str] = None,
                             label: Optional[bool] = False, 
                             user_id: str = Depends(JWTBearer())) -> VideoPipelineImageMetadata:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to add pipeline image")
    # get pipeline using helper
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    if video_pipeline.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        # use reusable function to add image
        broadcast_message(f"pipeline-tasks-{video_pipeline_id}", {"type": "image_adding", "pipeline_id": video_pipeline_id, "image_filename": image.filename})
        image_metadata = add_image_to_pipeline(video_pipeline, image, text_context=text_context, label=label or False)
        broadcast_message(f"pipeline-tasks-{video_pipeline_id}", {"type": "image_added", "pipeline_id": video_pipeline_id, "image_metadata": image_metadata.model_dump(mode="json")})
        return VideoPipelineImageMetadata(**image_metadata.model_dump(mode="json"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{video_pipeline_id}/images/{index}", name="delete video pipeline image", 
               dependencies=[Depends(JWTBearer())])
@error_wrapper("delete video pipeline image")
async def delete_video_pipeline_image(video_pipeline_id: str, 
                                      index: int,
                                      user_id: str = Depends(JWTBearer())) -> DeleteVideoPipelineImageResponse:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to delete pipeline image")
    # get pipeline using helper
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    if video_pipeline.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        # use reusable function to delete image
        image_metadata = delete_image_from_pipeline(video_pipeline, index)
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        return DeleteVideoPipelineImageResponse(
            video_pipeline_id=video_pipeline_id,
            message=f"Image {image_metadata.filename} deleted successfully",
            filename=image_metadata.filename
        )
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{video_pipeline_id}/sections", name="add video pipeline section", dependencies=[Depends(JWTBearer())])
@error_wrapper("add video pipeline section")
async def add_video_pipeline_section(video_pipeline_id: str, section: VideoPipelineContentSection,
                                     user_id: str = Depends(JWTBearer())) -> VideoPipelineContentSection:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to add pipeline section")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    try:
        # use reusable function to add section
        added_section = add_section_to_pipeline(video_pipeline, section)
        
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        return added_section
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{video_pipeline_id}/sections/{index}", name="delete video pipeline section", dependencies=[Depends(JWTBearer())])
@error_wrapper("delete video pipeline section")
async def delete_video_pipeline_section(video_pipeline_id: str, 
                                        index: int,
                                        user_id: str = Depends(JWTBearer())) -> DeleteVideoPipelineSectionResponse:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to delete pipeline section")
    # get pipeline using helper
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    if video_pipeline.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        # use reusable function to delete section
        section_data = delete_section_from_pipeline(video_pipeline, index)
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        return DeleteVideoPipelineSectionResponse(
            video_pipeline_id=video_pipeline_id,
            index=index,
            message=f"Section {section_data.title} deleted successfully",
            title=section_data.title
        )
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{video_pipeline_id}/process", name="process video pipeline content", dependencies=[Depends(JWTBearer())])
@error_wrapper("process video pipeline content")
async def process_video_pipeline_content(video_pipeline_id: str, request: CreateVideoPipelineOutlineRequest,
                                         user_id: str = Depends(JWTBearer()),
                                         background_tasks: BackgroundTasks = BackgroundTasks()) -> VideoPipeline:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    if video_pipeline.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    # process content
    skip_stock = request.skip_stock
    target_segments = request.target_segments
    segment_duration = request.segment_duration
    # run content analysis task in the background
    background_tasks.add_task(run_next_stages, 
                              video_pipeline, 
                              stage=VideoPipelineStage.CONTENT_ANALYSIS, 
                              skip_stock=skip_stock, 
                              target_segments=target_segments, 
                              segment_duration=segment_duration)
    # return pipeline summary
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))

@router.post("/{video_pipeline_id}/outline/segments", name="add video pipeline outline segment", dependencies=[Depends(JWTBearer())])
@error_wrapper("add video pipeline outline segment")
async def add_video_pipeline_outline_segment(video_pipeline_id: str,
                                            segment: VideoPipelineSegment,
                                            user_id: str = Depends(JWTBearer())) -> VideoPipelineSegment:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to add pipeline video outline segment")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    if video_pipeline.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        # use reusable function to add segment
        added_segment = add_segment_to_outline(video_pipeline, segment)
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        return added_segment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# @router.delete("/{video_pipeline_id}/outline/segments/{index}", name="delete video pipeline outline segment")
@error_wrapper("delete video pipeline outline segment")
async def delete_video_pipeline_outline_segment(video_pipeline_id: str, index: int,
                                                user_id: str = Depends(JWTBearer())) -> VideoPipelineSegment:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to delete pipeline video outline segment")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    if video_pipeline.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        # use reusable function to delete segment
        deleted_segment = delete_segment_from_outline(video_pipeline, index)
        
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        return deleted_segment
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{video_pipeline_id}/generate-scripts", name="generate video pipeline scripts")
@error_wrapper("generate video pipeline scripts")
async def generate_video_pipeline_scripts(video_pipeline_id: str, request: CreateVideoPipelineScriptRequest,
                                          user_id: str = Depends(JWTBearer()),
                                          background_tasks: BackgroundTasks = BackgroundTasks()) -> VideoPipeline:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to generate scripts and voiceovers")
    # get pipeline using helper
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    if video_pipeline.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    # use modular operation to generate scripts
    provider = request.provider
    voice_id = request.voice_id
    # run script generation task in the background
    background_tasks.add_task(run_next_stages, 
                              video_pipeline, stage=VideoPipelineStage.SCRIPT_GENERATION, 
                              provider=provider, voice_id=voice_id)
    # return pipeline summary
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))

@router.post("/{video_pipeline_id}/generate", name="generate video pipeline output", dependencies=[Depends(JWTBearer())])
@error_wrapper("generate video pipeline output")
async def generate_video_pipeline_output(video_pipeline_id: str, request: GenerateVideoPipelineRequest,
                                         user_id: str = Depends(JWTBearer()),
                                         background_tasks: BackgroundTasks = BackgroundTasks()) -> VideoPipeline:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to generate video")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    if video_pipeline.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    # use modular operation to generate video
    title = request.title
    subtitle = request.subtitle
    resolution = resolution_map[request.resolution]
    fps = request.fps
    title_duration = request.title_duration
    end_duration = request.end_duration
    transition_duration = request.transition_duration
    background_type = request.background_type
    # run video generation task in the background
    background_tasks.add_task(run_next_stages, 
                              video_pipeline, stage=VideoPipelineStage.VIDEO_GENERATION, 
                              title=title, subtitle=subtitle, resolution=resolution, 
                              fps=fps, title_duration=title_duration, end_duration=end_duration, 
                              transition_duration=transition_duration, background_type=background_type)
    # return pipeline summary
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))

@router.get("/{video_pipeline_id}/output/download", name="download video pipeline output", dependencies=[Depends(JWTBearer())])
@error_wrapper("download video pipeline output")
async def download_video_pipeline_output(video_pipeline_id: str,
                                          user_id: str = Depends(JWTBearer())) -> FileResponse:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to download video")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    if video_pipeline.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    video_path = video_pipeline.video_path
    if not video_path:
        raise HTTPException(status_code=500, detail="Video path not found")
    return FileResponse(
        path=video_path,
        media_type='video/mp4',
        filename=f"{video_pipeline.script_data.title}-{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
    )

def parse_range_header(range_header: str, file_size: int) -> Tuple[int, int]:
    """ parse the range header coming from the client request"""
    byte_range = re.search(r'bytes=(\d+)-(\d+)', range_header)
    if not byte_range:
        return 0, file_size - 1
    start = int(byte_range.group(1))
    end = int(byte_range.group(2)) if byte_range.group(2) else file_size - 1
    return start, end

@router.get("/{video_pipeline_id}/output/stream", name="stream video pipeline output", dependencies=[Depends(JWTBearer())])
@error_wrapper("stream video pipeline output")
async def stream_video_pipeline_output(video_pipeline_id: str, request: Request,
                                       user_id: str = Depends(JWTBearer())) -> StreamingResponse:
    logger.info("received request to stream video")
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    if video_pipeline.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    video_path = video_pipeline.video_path
    if not video_path:
        raise HTTPException(status_code=500, detail="Video path not found")
    file_size = os.path.getsize(video_path)
    range_header = request.headers.get('range')

    if not range_header:
        start = 0
        end = int(0.9 * file_size)
    else:
        start, end = parse_range_header(range_header, file_size)
    content_length = end - start + 1

    def iter_video_file():
        """
        generator to stream file in chunks
        """
        with open(video_path, 'rb') as f:
            f.seek(start)
            remaining = content_length
            while remaining > 0:
                chunk_size = min(8192, remaining)
                data = f.read(chunk_size)
                if not data:
                    break
                remaining -= len(data)
                yield data
    return StreamingResponse(
        iter_video_file(),
        status_code=206,
        media_type='video/mp4',
        headers={ 'Content-Range': f'bytes {start}-{end}/{file_size}',
            'Accept-Ranges': 'bytes',
            'Content-Length': str(content_length),
            'Content-Type': 'video/mp4'
        }
    )

@router.post("/{video_pipeline_id}/review", name="add video pipeline review", dependencies=[Depends(JWTBearer())])
@error_wrapper("add video pipeline review")
async def add_video_pipeline_review(video_pipeline_id: str, request: VideoPipelineReviewRequest,
                                    user_id: str = Depends(JWTBearer())) -> VideoPipeline:
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("received request to add pipeline review")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    if video_pipeline.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if request.rating is not None:
        video_pipeline.rating = request.rating
    if request.feedback is not None:
        video_pipeline.feedback = request.feedback
    
    # update database
    await update_pipeline_in_db(video_pipeline_id, video_pipeline)
    
    logger.info(f"pipeline review added successfully: {video_pipeline.rating}, {video_pipeline.feedback}")
    return video_pipeline

async def receive_pipeline_ws_messages(websocket: WebSocket, pipeline: VideoPipeline, user: User) -> None:
    logger.info(f"received request to receive pipeline ws messages for pipeline {pipeline.name} and user {user.email}")
    while True:
        try:
        # wait for updates to the pipeline data
            data = await websocket.receive_json()
            logger.info(f"received message from pipeline {pipeline.name} and user {user.email}: {data}")
        except Exception as e:
            logger.error(f"error receiving pipeline ws messages for pipeline {pipeline.name} and user {user.email}: {e}")
            break
    logger.info(f"stopped receiving pipeline ws messages for pipeline {pipeline.name} and user {user.email}")

async def send_pipeline_ws_messages(websocket: WebSocket, pipeline: VideoPipeline, user: User) -> None:
    logger.info(f"received request to send pipeline ws messages for pipeline {pipeline.name} and user {user.email}")
    channel = f"pipeline-tasks-{pipeline.id}"
    listener_name = f"pipeline-ws-listener-{pipeline.id}-{user.email}"
    async for message in listen_for_messages(channel, listener_name):
        logger.info(f"received message from pipeline {pipeline.name} and user {user.email}: {message}")
        await websocket.send_json(message)
        logger.info(f"sent message to pipeline {pipeline.name} for user {user.email}")
    logger.info(f"stopped sending pipeline ws messages for pipeline {pipeline.name} and user {user.email}")

@router.websocket("/{video_pipeline_id}/ws", name="video pipeline state socket", dependencies=[Depends(JWTBearer())])
async def video_pipeline_state_socket(video_pipeline_id: str,
                                      websocket: WebSocket,
                                      user_id: str = Depends(JWTBearer())):
    logger.info("received request to connect to pipeline state socket")
    user = await get_user_by_id(user_id)
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    await websocket.accept()
    try:
        await asyncio.gather(
            receive_pipeline_ws_messages(websocket, video_pipeline, user),
            send_pipeline_ws_messages(websocket, video_pipeline, user)
        )
    except WebSocketDisconnect:
        logger.info(f"connection to pipeline state socket for pipeline {video_pipeline.name} and user {user.email} disconnected by user")
        await websocket.close(code=1000, reason="Connection disconnected")
    except asyncio.CancelledError:
        logger.info(f"connection to pipeline state socket for pipeline {video_pipeline.name} and user {user.email} cancelled")
        await websocket.close(code=1000, reason="Connection cancelled")
    except Exception as e:
        logger.error(f"error connecting to pipeline state socket for pipeline {video_pipeline.name} and user {user.email}: {e}")
        await websocket.close(code=1011, reason="Internal server error")
