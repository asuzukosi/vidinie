from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request, WebSocket, BackgroundTasks, Depends, WebSocketDisconnect
import re
from fastapi.responses import StreamingResponse, FileResponse
from core.data import (
    VideoPipeline,
    SourceType,
    VideoPipelineStage,
    VideoPipelineStatus,
    VideoSegment,
    ContentSection,
    ImageMetadata,
)
import asyncio
from api.core.auth import BetterAuthBearer
from core.utils.logger import setup_logging, get_logger
from api.operations.content_operations import (
    add_section_to_content as add_section_to_pipeline,
    delete_section_from_content as delete_section_from_pipeline,
    add_segment_to_outline,
    delete_segment_from_outline,
)
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
    verify_pipeline_ownership,
)
import os
from pathlib import Path
from api.data.pipelines import CreateVideoPipelineRequest, VideoPipelineSummary, \
                               DeleteVideoPipelineResponse, DeleteVideoPipelineImageResponse, \
                               DeleteVideoPipelineSectionResponse, \
                               CreateVideoOutlineRequest, CreateVideoPipelineScriptRequest, \
                               VideoPipelineReviewRequest, GenerateVideoPipelineRequest
from core.utils.config_loader import config
from core.clients.audio_engine import AudioVoiceString
from datetime import datetime
from typing import Optional, Tuple, List
import shutil
import requests
from api.utils.error_wrapper import error_wrapper
from api.core.signals import broadcast_message, listen_for_messages, PipelineBroadcastMessageType, PipelineBroadcastStatus
from api.core.celery import execute_pipeline_task

# setup logging
setup_logging(log_dir=str(config.logs_directory))
logger = get_logger('pipelines')
router = APIRouter(tags=["pipelines"])


async def copy_base_to_target(target_path: str) -> bool:
    """copy the base project to the target path."""
    copy_target_path = os.path.join(target_path)
    if os.path.exists(copy_target_path):
        logger.info(f"removing existing composition at {copy_target_path}")
        shutil.rmtree(copy_target_path)
    logger.info(f"copying base project to {copy_target_path}")
    return shutil.copytree(str(config.base_project_path), copy_target_path)

# special utility function to write content to file for pipeline
async def write_content_to_file_for_pipeline(video_pipeline: VideoPipeline, 
                                             filename: str, 
                                             file_content: bytes) -> None:
    # now save file to disk with the final id
    output_dir = str(config.output_directory)
    pipeline_dir = os.path.join(output_dir, video_pipeline.id)
    # create pipeline directory
    Path(pipeline_dir).mkdir(parents=True, exist_ok=True)
    # copy base project to pipeline directory
    await copy_base_to_target(pipeline_dir)
    pipeline_source_path = os.path.join(pipeline_dir, 'public', 'sources')
    # create folder for source files
    Path(pipeline_source_path).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(pipeline_source_path, filename)
    with open(file_path, 'wb') as f:
        f.write(file_content)
    video_pipeline.source_path = file_path
    await update_pipeline_in_db(video_pipeline.id, video_pipeline)
    await broadcast_message({
        "type": PipelineBroadcastMessageType.PIPELINE,
        "pipeline_id": video_pipeline.id,
        "user_id": video_pipeline.user_id or "",
        "status": PipelineBroadcastStatus.IN_PROGRESS,
        "file_path": file_path
    })
    logger.info(f"pipeline data saved to database with id: {video_pipeline.id}, file saved to: {file_path}")

# special utility function to delete pipeline temp directory
async def delete_pipeline_temp_directory(video_pipeline: VideoPipeline) -> None:
    # delete temp directory for pipeline
    output_dir = str(config.output_directory)
    pipeline_dir = os.path.join(output_dir, video_pipeline.id)
    if os.path.exists(pipeline_dir):
        shutil.rmtree(pipeline_dir)
        logger.info(f"temp directory deleted successfully with id: {video_pipeline.id}")
    else:
        logger.info(f"no temp directory found for pipeline with id: {video_pipeline.id}")

async def any_stage_is_processing(video_pipeline: VideoPipeline) -> bool:
    # check if any stage is processing
    return video_pipeline.status == VideoPipelineStatus.IN_PROGRESS

# pipeline stages to run in the order they are executed



@router.post("/from-file", name="create video pipeline from file", dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("create video pipeline from file")
async def create_video_pipeline_from_file(
    name: str = Form(...),
    instructions: str = Form(...),
    voice: str = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(BetterAuthBearer()),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> VideoPipelineSummary:
    # validate voice string
    try:
        AudioVoiceString(voice)
    except (ValueError, KeyError):
        valid_voices = [v.value for v in AudioVoiceString]
        raise HTTPException(status_code=400, detail=f"Invalid voice value: {voice}. Must be one of {valid_voices}")
    logger.info("received request to start pipeline with file")
    if file.filename == "" or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail=f"invalid file type, only pdf files currently supported: {file.filename}")
    # read file content into memory
    file_content = await file.read()
    logger.info(f"read file content into memory: {len(file_content)} bytes")
    # create pipeline data object
    logger.info("creating pipeline data object")
    video_pipeline = VideoPipeline(
        user_id=user_id,
        name=name,
        instructions=instructions,
        voice=voice,
        source_type=SourceType.PDF,
        document_processing_status=VideoPipelineStatus.IN_PROGRESS
    )
    logger.info("pipeline data object created")
    video_pipeline = await create_pipeline_in_db(video_pipeline)
    await broadcast_message({
        "type": PipelineBroadcastMessageType.PIPELINE.value,
        "pipeline_id": video_pipeline.id,
        "user_id": video_pipeline.user_id or "",
        "status": PipelineBroadcastStatus.PENDING.value
    })
    background_tasks.add_task(write_content_to_file_for_pipeline, video_pipeline, file.filename, file_content)
    execute_pipeline_task.delay(video_pipeline.id, start_from_stage=VideoPipelineStage.DOCUMENT_PROCESSING, pdf_content=file_content)
    # return pipeline summary
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))

@router.post("/from-url", name="create video pipeline from url", dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("create video pipeline from url")
async def create_video_pipeline_from_url(request: CreateVideoPipelineRequest,
                                         user_id: str = Depends(BetterAuthBearer()),
                                         background_tasks: BackgroundTasks = BackgroundTasks()) -> VideoPipelineSummary:
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
    # validate voice string
    try:
        AudioVoiceString(request.voice)
    except (ValueError, KeyError):
        valid_voices = [v.value for v in AudioVoiceString]
        raise HTTPException(status_code=400, detail=f"Invalid voice value: {request.voice}. Must be one of {valid_voices}")
    logger.info("creating pipeline data object")
    video_pipeline = VideoPipeline(
        user_id=user_id,
        name=request.name,
        instructions=request.instructions,
        voice=request.voice,
        source_type=SourceType.HTML,
        document_processing_status=VideoPipelineStatus.IN_PROGRESS
    )
    # save pipeline data to database first
    logger.info("saving pipeline data to database")
    video_pipeline = await create_pipeline_in_db(video_pipeline)
    await broadcast_message({
        "type": PipelineBroadcastMessageType.PIPELINE.value,
        "pipeline_id": video_pipeline.id,
        "user_id": video_pipeline.user_id or "",
        "status": PipelineBroadcastStatus.PENDING.value
    })
    background_tasks.add_task(write_content_to_file_for_pipeline, video_pipeline, 'data.html', response.content)
    # run all the stages sequentially in the background
    execute_pipeline_task.delay(video_pipeline.id, start_from_stage=VideoPipelineStage.DOCUMENT_PROCESSING, html_content=response.text, original_url=request.url)
    # return pipeline summary
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))

@router.get("/", name="get all video pipelines")
@error_wrapper("get all video pipelines")
async def get_all_video_pipelines(user_id: str = Depends(BetterAuthBearer())) -> List[VideoPipelineSummary]:
    logger.info("received request to get all pipelines")
    # get pipelines using helper
    pipelines = await get_pipelines_for_user(user_id)
    return pipelines

@router.get("/{video_pipeline_id}", name="get video pipeline details")
@error_wrapper("get video pipeline details")
async def get_video_pipeline_details(video_pipeline_id: str, user_id: str = Depends(BetterAuthBearer())) -> VideoPipeline:
    logger.info("received request to get pipeline details")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    await verify_pipeline_ownership(video_pipeline, user_id)
    return video_pipeline

@router.delete("/{video_pipeline_id}", name="delete video pipeline", 
               dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("delete video pipeline")
async def delete_video_pipeline(video_pipeline_id: str, 
                                user_id: str = Depends(BetterAuthBearer()),
                                background_tasks: BackgroundTasks = BackgroundTasks()) -> DeleteVideoPipelineResponse:
    logger.info("received request to delete pipeline")
    # get pipeline using helper
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    await verify_pipeline_ownership(video_pipeline, user_id)
    logger.info(f"deleting pipeline with id: {video_pipeline_id}")
    # delete pipeline from database using helper
    await delete_pipeline_from_db(video_pipeline_id)
    # delete temp directory in background
    background_tasks.add_task(delete_pipeline_temp_directory, video_pipeline)
    # broadcast deletion message
    await broadcast_message({
        "type": PipelineBroadcastMessageType.PIPELINE,
        "pipeline_id": video_pipeline_id,
        "user_id": video_pipeline.user_id or "",
        "status": PipelineBroadcastStatus.DELETED
    })
    return DeleteVideoPipelineResponse(video_pipeline_id=video_pipeline_id, message="Pipeline deleted successfully")

@router.post("/{video_pipeline_id}/images", name="add video pipeline image", 
               dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("add video pipeline image")
async def add_video_pipeline_image(video_pipeline_id: str, image: UploadFile,
                             label: Optional[bool] = False, 
                             user_id: str = Depends(BetterAuthBearer())) -> ImageMetadata:
    logger.info("received request to add pipeline image")
    # get pipeline using helper
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    await verify_pipeline_ownership(video_pipeline, user_id)
    try:
        # use reusable function to add image
        await broadcast_message({
            "type": PipelineBroadcastMessageType.IMAGE,
            "pipeline_id": video_pipeline_id,
            "user_id": video_pipeline.user_id or "",
            "status": PipelineBroadcastStatus.IN_PROGRESS,
            "image_filename": image.filename or ""
        })
        image_metadata = add_image_to_pipeline(video_pipeline, image, label=label or False)
        await broadcast_message({
            "type": PipelineBroadcastMessageType.IMAGE,
            "pipeline_id": video_pipeline_id,
            "user_id": video_pipeline.user_id or "",
            "status": PipelineBroadcastStatus.COMPLETED,
            "image_metadata": image_metadata.model_dump(mode="json")
        })
        return ImageMetadata(**image_metadata.model_dump(mode="json"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{video_pipeline_id}/images/{index}", name="delete video pipeline image", 
               dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("delete video pipeline image")
async def delete_video_pipeline_image(video_pipeline_id: str, 
                                      index: int,
                                      user_id: str = Depends(BetterAuthBearer())) -> DeleteVideoPipelineImageResponse:
    logger.info("received request to delete pipeline image")
    # get pipeline using helper
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    await verify_pipeline_ownership(video_pipeline, user_id)
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

@router.post("/{video_pipeline_id}/sections", name="add video pipeline section", dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("add video pipeline section")
async def add_video_pipeline_section(video_pipeline_id: str, section: ContentSection,
                                     user_id: str = Depends(BetterAuthBearer())) -> ContentSection:
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

@router.delete("/{video_pipeline_id}/sections/{index}", name="delete video pipeline section", dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("delete video pipeline section")
async def delete_video_pipeline_section(video_pipeline_id: str, 
                                        index: int,
                                        user_id: str = Depends(BetterAuthBearer())) -> DeleteVideoPipelineSectionResponse:
    logger.info("received request to delete pipeline section")
    # get pipeline using helper
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    await verify_pipeline_ownership(video_pipeline, user_id)
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

@router.post("/{video_pipeline_id}/process", name="process video pipeline content", dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("process video pipeline content")
async def process_video_pipeline_content(video_pipeline_id: str, request: CreateVideoOutlineRequest,
                                         user_id: str = Depends(BetterAuthBearer())) -> VideoPipeline:
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    await verify_pipeline_ownership(video_pipeline, user_id)
    # ensure no other stage is in progress
    if await any_stage_is_processing(video_pipeline):
        raise HTTPException(status_code=409, detail="another pipeline stage is currently in progress, please wait until it completes.")
    # process content
    target_segments = request.target_segments
    segment_duration = request.segment_duration
    # run content analysis task in the background
    execute_pipeline_task.delay(
                              video_pipeline.id, 
                              start_from_stage=VideoPipelineStage.CONTENT_ANALYSIS, 
                              target_segments=target_segments, 
                              segment_duration=segment_duration)
    # return pipeline summary
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))

@router.post("/{video_pipeline_id}/outline/segments", name="add video pipeline outline segment", dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("add video pipeline outline segment")
async def add_video_pipeline_outline_segment(video_pipeline_id: str,
                                            segment: VideoSegment,
                                            user_id: str = Depends(BetterAuthBearer())) -> VideoSegment:
    logger.info("received request to add pipeline video outline segment")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    await verify_pipeline_ownership(video_pipeline, user_id)
    try:
        # use reusable function to add segment
        added_segment = add_segment_to_outline(video_pipeline, segment)
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        return added_segment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{video_pipeline_id}/outline/segments/{index}", name="delete video pipeline outline segment")
@error_wrapper("delete video pipeline outline segment")
async def delete_video_pipeline_outline_segment(video_pipeline_id: str, index: int,
                                                user_id: str = Depends(BetterAuthBearer())) -> VideoSegment:
    logger.info("received request to delete pipeline video outline segment")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    await verify_pipeline_ownership(video_pipeline, user_id)
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
                                          user_id: str = Depends(BetterAuthBearer())) -> VideoPipeline:
    logger.info("received request to generate scripts and voiceovers")
    # get pipeline using helper
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    await verify_pipeline_ownership(video_pipeline, user_id)
    # ensure no other stage is in progress
    if await any_stage_is_processing(video_pipeline):
        raise HTTPException(status_code=409, detail="another pipeline stage is currently in progress, please wait until it completes.")
    # use modular operation to generate scripts
    voice_str = request.voice
    # run script generation task in the background using Celery
    execute_pipeline_task.delay(
                              video_pipeline.id, start_from_stage=VideoPipelineStage.SCRIPT_GENERATION, 
                              voice=voice_str)
    # return pipeline summary
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))

@router.post("/{video_pipeline_id}/generate", name="generate video pipeline output", dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("generate video pipeline output")
async def generate_video_pipeline_output(video_pipeline_id: str, request: GenerateVideoPipelineRequest,
                                         user_id: str = Depends(BetterAuthBearer())) -> VideoPipeline:
    logger.info("received request to generate video")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    await verify_pipeline_ownership(video_pipeline, user_id)
    # ensure no other stage is in progress
    if await any_stage_is_processing(video_pipeline):
        raise HTTPException(status_code=409, detail="another pipeline stage is currently in progress, please wait until it completes.")
    # run video generation task in the background
    execute_pipeline_task.delay(
                              video_pipeline.id, start_from_stage=VideoPipelineStage.VIDEO_GENERATION)
    # return pipeline summary
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))

@router.get("/{video_pipeline_id}/output/download", name="download video pipeline output", dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("download video pipeline output")
async def download_video_pipeline_output(video_pipeline_id: str,
                                          user_id: str = Depends(BetterAuthBearer())) -> FileResponse:
    logger.info("received request to download video")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    await verify_pipeline_ownership(video_pipeline, user_id)
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

@router.get("/{video_pipeline_id}/output/stream", name="stream video pipeline output", 
            # dependencies=[Depends(BetterAuthBearer())]
            )
@error_wrapper("stream video pipeline output")
async def stream_video_pipeline_output(video_pipeline_id: str, request: Request,
                                    #    user_id: str = Depends(BetterAuthBearer())
                                       ) -> StreamingResponse:
    # logger.info("received request to stream video")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
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

@router.post("/{video_pipeline_id}/review", name="add video pipeline review", dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("add video pipeline review")
async def add_video_pipeline_review(video_pipeline_id: str, request: VideoPipelineReviewRequest,
                                    user_id: str = Depends(BetterAuthBearer())) -> VideoPipeline:
    logger.info("received request to add pipeline review")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    # verify ownership
    await verify_pipeline_ownership(video_pipeline, user_id)
    if request.rating is not None:
        video_pipeline.rating = request.rating
    if request.feedback is not None:
        video_pipeline.feedback = request.feedback
    
    # update database
    await update_pipeline_in_db(video_pipeline_id, video_pipeline)
    
    logger.info(f"pipeline review added successfully: {video_pipeline.rating}, {video_pipeline.feedback}")
    return video_pipeline

async def receive_pipeline_ws_messages(websocket: WebSocket, pipeline: VideoPipeline, user_id: str) -> None:
    logger.info(f"received request to receive pipeline ws messages for pipeline {pipeline.name} and user {user_id}")
    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"received message from pipeline {pipeline.name} and user {user_id}: {data}")
    except (WebSocketDisconnect, Exception) as e:
        logger.info(f"stopped receiving pipeline ws messages for pipeline {pipeline.name} and user {user_id}: {type(e).__name__}")

async def send_pipeline_ws_messages(websocket: WebSocket, pipeline: VideoPipeline, user_id: str) -> None:
    logger.info(f"received request to send pipeline ws messages for pipeline {pipeline.name} and user {user_id}")
    listener_name = f"pipeline-ws-listener-{pipeline.id}-{user_id}"
    try:
        async for message in listen_for_messages(listener_name):
            # filter messages for this specific pipeline and user
            message_pipeline_id = message.get("pipeline_id")
            message_user_id = message.get("user_id")
            
            if message_pipeline_id == pipeline.id and message_user_id == user_id:
                logger.info(f"received message from pipeline {pipeline.name} and user {user_id}: {message}")
                await websocket.send_json(message)
                logger.info(f"sent message to pipeline {pipeline.name} for user {user_id}")
            else:
                logger.debug(f"filtered out message for pipeline {pipeline.name}: pipeline_id={message_pipeline_id}, user_id={message_user_id}")
    except (WebSocketDisconnect, Exception) as e:
        logger.info(f"stopped sending pipeline ws messages for pipeline {pipeline.name} and user {user_id}: {type(e).__name__}")

@router.websocket("/{video_pipeline_id}/ws", name="video pipeline state socket")
async def video_pipeline_state_socket(
    video_pipeline_id: str,
    websocket: WebSocket,
):
    """
    websocket endpoint for real-time pipeline updates.
    query parameter: user_id (required)
    """
    logger.info(f"received request to connect to pipeline state socket for pipeline {video_pipeline_id}")
    
    # extract user_id from query parameters
    query_params = dict(websocket.query_params)
    logger.info(f"websocket query params: {query_params}")
    user_id = query_params.get("user_id")
    
    if not user_id:
        logger.error(f"user_id not provided in websocket connection. query params: {query_params}")
        await websocket.close(code=1008, reason="user_id is required")
        return
    
    try:
        video_pipeline = await get_pipeline_by_id(video_pipeline_id)
        
        # verify ownership
        try:
            await verify_pipeline_ownership(video_pipeline, user_id)
        except HTTPException:
            logger.error(f"user {user_id} attempted to access pipeline {video_pipeline_id} owned by {video_pipeline.user_id}")
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        await websocket.accept()
        logger.info(f"websocket accepted for pipeline {video_pipeline.name} and user {user_id}")
        
        # send initial status message
        await websocket.send_json({
            "type": PipelineBroadcastMessageType.PIPELINE,
            "status": video_pipeline.status.value if hasattr(video_pipeline.status, 'value') else str(video_pipeline.status),
            "pipeline_id": video_pipeline.id,
            "user_id": video_pipeline.user_id or ""
        })
        logger.info(f"sent initial status message to pipeline {video_pipeline.name}: {video_pipeline.status}")
        
        # run both receive and send tasks concurrently
        await asyncio.gather(
            receive_pipeline_ws_messages(websocket, video_pipeline, user_id),
            send_pipeline_ws_messages(websocket, video_pipeline, user_id),
            return_exceptions=True
        )
            
    except (WebSocketDisconnect, asyncio.CancelledError) as e:
        logger.info(f"connection to pipeline state socket for pipeline {video_pipeline_id} {type(e).__name__.lower()}")
    except Exception as e:
        logger.error(f"error connecting to pipeline state socket for pipeline {video_pipeline_id}: {e}")
        await websocket.close(code=1011, reason="Internal server error")