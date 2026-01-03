from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request, WebSocket, BackgroundTasks
import re
from fastapi.responses import StreamingResponse, FileResponse
from core.data import (
    VideoPipeline,
    SourceType,
    VideoPipelineStage,
    VideoPipelineStatus,
    VideoPipelineParsedContent,
    VideoPipelineSegment,
    VideoPipelineContentSection,
    VideoPipelineImageMetadata,
    VideoPipelineContextChunk,
    VideoPipelineScript,
    VideoPipelineOutline,
    BackgroundType,
    get_next_stage,
    get_previous_stage,
)
from core.utils.logger import setup_logging, get_logger
from core.operations.document_processor import (
    process_pdf_document,
    process_html_document,
)
from core.operations.content_analyzer import (
    process_content,
    add_section_to_content as add_section_to_pipeline,
    update_section_in_content as update_section_in_pipeline,
    delete_section_from_content as delete_section_from_pipeline,
    add_segment_to_outline,
    update_segment_in_outline,
    delete_segment_from_outline,
    generate_images_for_segments,
    update_segment_background,
)
from core.operations.script_generator import (
    generate_scripts,
    update_scripts_in_pipeline,
)
from core.operations.video_generator import generate_video
from core.operations.image_labeler import (
    add_image_to_pipeline,
    update_image_in_pipeline,
    delete_image_from_pipeline,
)
from api.helpers.pipeline_helpers import (
    get_pipeline_by_id,
    update_pipeline_in_db,
)
from typing import List
import os
from pathlib import Path
from api.core.db import video_pipelines_collection
from api.data.pipeline import CreateVideoPipelineRequest, VideoPipelineSummary, \
                               DeleteVideoPipelineResponse, VideoPipelineStageDetails, \
                               UpdateVideoPipelineImageRequest, DeleteVideoPipelineImageResponse, \
                               VideoPipelineContentMinimal, DeleteVideoPipelineSectionResponse, \
                               CreateVideoPipelineOutlineRequest, GenerateVideoPipelineRequest, \
                               VideoPipelineSegmentBackground, VideoPipelineReviewRequest, VideoResolution, \
                               RunVideoPipelineOperationsRequest
from core.utils.config_loader import get_config
from core.operations.voiceover_generator import VoiceoverGenerator
from bson.objectid import ObjectId
from datetime import datetime
from typing import Optional, Tuple, List
import shutil
import requests
import asyncio


# setup logging
setup_logging(log_dir='temp')
logger = get_logger('pipelines')

# get config
config = get_config()

router = APIRouter(tags=["pipelines"])



@router.post("/from-file", name="create video pipeline from file")
async def create_video_pipeline_from_file(
    name: str = Form(...),
    description: str = Form(...),
    tags: Optional[List[str]] = Form(...),
    projects: Optional[List[str]] = Form(...),
    file: UploadFile = File(...),
) -> VideoPipelineSummary:
    logger.info("received request to start pipeline with file")
    if file.filename == "" or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type must be a PDF file")
    # create pipeline data object
    logger.info("creating pipeline data object")
    video_pipeline = VideoPipeline()
    video_pipeline.name = name
    video_pipeline.description = description
    video_pipeline.tags = tags[0].split(",") or []
    video_pipeline.projects = projects[0].split(",") or []
    video_pipeline.source_type = SourceType.PDF
    video_pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.IN_PROGRESS)
    logger.info("pipeline data object created")

    # create temp directory for metadata
    temp_dir = config.get('output.temp_directory', 'temp')
    images_dir = os.path.join(temp_dir, video_pipeline.id, 'images')
    Path(images_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"created temp directory for metadata: {images_dir}")
    # save file to temp directory
    with open(os.path.join(temp_dir, video_pipeline.id, file.filename), 'wb') as f:
        f.write(file.file.read())
    logger.info(f"saved file to temp directory: {os.path.join(temp_dir, video_pipeline.id, file.filename)}")
    video_pipeline.source_path = os.path.join(temp_dir, video_pipeline.id, file.filename)

    # process PDF document using modular operation
    video_pipeline = process_pdf_document(
        video_pipeline,
        extract_images=True,
        openai_api_key=config.openai_api_key,
        prompts_dir=config.get_prompts_directory()
    )

    # save pipeline data to database
    logger.info("saving pipeline data to database")
    video_pipeline.path_id = video_pipeline.id
    db_pipeline = await video_pipelines_collection.insert_one(video_pipeline.model_dump(mode="json"))
    video_pipeline.id = str(db_pipeline.inserted_id)
    # we have to update the id to the actual id because the id is generated by mongodb and not by us
    await video_pipelines_collection.update_one(
            {"_id": ObjectId(db_pipeline.inserted_id)},
            {"$set": {"id": video_pipeline.id}}
        )
    logger.info(f"pipeline data saved to database with id: {video_pipeline.id}")
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))

@router.post("/from-url", name="create video pipeline from url")
async def create_video_pipeline_from_url(request: CreateVideoPipelineRequest) -> VideoPipelineSummary:
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
    video_pipeline = VideoPipeline()
    video_pipeline.name = request.name
    video_pipeline.description = request.description
    video_pipeline.tags = request.tags or []
    video_pipeline.projects = request.projects or []
    video_pipeline.source_type = SourceType.HTML
    video_pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING,
                               VideoPipelineStatus.IN_PROGRESS)


    logger.info("pipeline data object created")
    # create temp directory for metadata
    temp_dir = config.get('output.temp_directory', 'temp')
    images_dir = os.path.join(temp_dir, video_pipeline.id, 'images')
    Path(images_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"created temp directory for metadata: {images_dir}")
    # save file to temp directory
    with open(os.path.join(temp_dir, video_pipeline.id, 'data.html'), 'wb') as f:
        f.write(response.content)
    logger.info(f"saved file to temp directory: {os.path.join(temp_dir, video_pipeline.id, 'data.html')}")
    video_pipeline.source_path = os.path.join(temp_dir, video_pipeline.id, 'data.html')

    # process HTML document using modular operation
    video_pipeline = process_html_document(
        video_pipeline,
        html_path=request.url,
        extract_images=True,
        openai_api_key=config.openai_api_key,
        prompts_dir=config.get_prompts_directory()
    )

    # save pipeline data to database
    logger.info("saving pipeline data to database")
    video_pipeline.path_id = video_pipeline.id
    db_pipeline = await video_pipelines_collection.insert_one(video_pipeline.model_dump(mode="json"))
    video_pipeline.id = str(db_pipeline.inserted_id)
    logger.info(f"pipeline data saved to database with id: {video_pipeline.id}")
    # we have to update the id to the actual id because the id is generated by mongodb and not by us
    await video_pipelines_collection.update_one(
            {"_id": ObjectId(db_pipeline.inserted_id)},
            {"$set": {"id": video_pipeline.id}}
        )
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))

@router.get("/", name="get all video pipelines")
async def get_all_video_pipelines() -> List[VideoPipelineSummary]:
    logger.info("received request to get all pipelines")
    pipelines: List[VideoPipelineSummary] = []
    async for video_pipeline in video_pipelines_collection.find():
        pipelines.append(VideoPipelineSummary(**video_pipeline))
    return pipelines



@router.delete("/{video_pipeline_id}", name="delete video pipeline")
async def delete_video_pipeline(video_pipeline_id: str) -> DeleteVideoPipelineResponse:
    logger.info("received request to delete pipeline")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    path_id = video_pipeline.path_id
    logger.info(f"deleting pipeline with id: {video_pipeline_id}")
    result = await video_pipelines_collection.delete_one({"_id": ObjectId(video_pipeline_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete pipeline")
    logger.info(f"pipeline deleted successfully with id: {video_pipeline_id}")
    # delete temp directory
    if path_id:
        temp_dir = config.get('output.temp_directory', 'temp')
        shutil.rmtree(os.path.join(temp_dir, path_id))
        logger.info(f"temp directory deleted successfully with id: {path_id}")
    else:
        logger.info(f"no temp directory found for pipeline with id: {video_pipeline_id}")
    return DeleteVideoPipelineResponse(video_pipeline_id=video_pipeline_id, message="Pipeline deleted successfully", path_id=path_id)

@router.get("/{video_pipeline_id}", name="get video pipeline details")
async def get_video_pipeline_details(video_pipeline_id: str) -> VideoPipeline:
    logger.info("received request to get pipeline details")
    return await get_pipeline_by_id(video_pipeline_id)



@router.get("/{video_pipeline_id}/stages/{stage}", name="get video pipeline stage details")
async def get_video_pipeline_stage_details(video_pipeline_id: str) -> VideoPipelineStageDetails:
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    next_stage = get_next_stage(video_pipeline.current_stage)
    previous_stage = get_previous_stage(video_pipeline.current_stage)

    return VideoPipelineStageDetails(
        stage=video_pipeline.current_stage.value if hasattr(video_pipeline.current_stage, 'value') else str(video_pipeline.current_stage),
        status=video_pipeline.status.value if hasattr(video_pipeline.status, 'value') else str(video_pipeline.status),
        next_stage=next_stage.value if hasattr(next_stage, 'value') else str(next_stage),
        previous_stage=previous_stage.value if hasattr(previous_stage, 'value') else str(previous_stage),
        stage_statuses={k.value if hasattr(k, 'value') else str(k): v.value if hasattr(v, 'value') else str(v) 
                      for k, v in video_pipeline.stage_statuses.items()} if video_pipeline.stage_statuses else None
    )

@router.get("/{video_pipeline_id}/images", name="get video pipeline images")
async def get_video_pipeline_images(video_pipeline_id: str) -> List[VideoPipelineImageMetadata]:
    logger.info("received request to view pipeline images")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    return video_pipeline.images_metadata

@router.post("/{video_pipeline_id}/images", name="add video pipeline image")
async def add_video_pipeline_image(video_pipeline_id: str, image: UploadFile,
                             text_context: Optional[str] = None,
                             label: Optional[bool] = False) -> VideoPipelineImageMetadata:
    logger.info("received request to add pipeline image")
    
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    try:
        # use reusable function to add image
        image_metadata = add_image_to_pipeline(
            video_pipeline,
            image,
            text_context=text_context,
            label=label or False,
            openai_api_key=config.openai_api_key,
            prompts_dir=config.get_prompts_directory()
        )
        
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        return image_metadata
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.put("/{video_pipeline_id}/images", name="update video pipeline image")
async def update_video_pipeline_image(video_pipeline_id: str, request: UpdateVideoPipelineImageRequest) -> VideoPipelineImageMetadata:
    logger.info("received request to update pipeline image metadata")
    
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    try:
        # use reusable function to update image
        image_metadata = update_image_in_pipeline(
            video_pipeline,
            request.index,
            filename=request.filename,
            text_context=request.text_context,
            label=request.label,
            description=request.description,
            relevance_score=request.relevance_score,
            image_type=request.image_type,
            key_elements=request.key_elements,
            ai_relevance=request.ai_relevance
        )
        
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        return image_metadata
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))



@router.delete("/{video_pipeline_id}/images/{index}", name="delete video pipeline image")
async def delete_video_pipeline_image(video_pipeline_id: str, index: int) -> DeleteVideoPipelineImageResponse:
    logger.info("received request to delete pipeline image")
    
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    try:
        # use reusable function to delete image
        image_metadata = delete_image_from_pipeline(video_pipeline, index)
        
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        
        return DeleteVideoPipelineImageResponse(
            video_pipeline_id=video_pipeline_id,
            message=f"Image {image_metadata.filename} deleted successfully",
            filename=image_metadata.filename,
            path_id=video_pipeline.path_id
        )
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))



@router.get("/{video_pipeline_id}/content", name="get video pipeline content info")
async def get_video_pipeline_content_info(video_pipeline_id: str) -> VideoPipelineContentMinimal:
    logger.info("received request to get pipeline parsed content info")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    if not video_pipeline.parsed_content:
        raise HTTPException(status_code=404, detail="Parsed content not found")
    
    return VideoPipelineContentMinimal(
        title=video_pipeline.parsed_content.title,
        total_pages=video_pipeline.parsed_content.total_pages,
        num_sections=len(video_pipeline.parsed_content.sections),
        metadata=video_pipeline.parsed_content.metadata
    )


@router.get("/{video_pipeline_id}/sections", name="get video pipeline sections")
async def get_video_pipeline_sections(video_pipeline_id: str) -> List[VideoPipelineContentSection]:
    logger.info("received request to get pipeline sections")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    if not video_pipeline.parsed_content:
        raise HTTPException(status_code=404, detail="Parsed content not found")
    
    return video_pipeline.parsed_content.sections

@router.post("/{video_pipeline_id}/sections", name="add video pipeline section")
async def add_video_pipeline_section(video_pipeline_id: str, section: VideoPipelineContentSection) -> VideoPipelineContentSection:
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

@router.put("/{video_pipeline_id}/sections/{index}", name="update video pipeline section")
async def update_video_pipeline_section(video_pipeline_id: str, index: int, section: VideoPipelineContentSection) -> VideoPipelineContentSection:
    logger.info("received request to update pipeline section")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    try:
        # use reusable function to update section
        updated_section = update_section_in_pipeline(video_pipeline, index, section)
        
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        return updated_section
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=404, detail=str(e))



@router.delete("/{video_pipeline_id}/sections/{index}", name="delete video pipeline section")
async def delete_video_pipeline_section(video_pipeline_id: str, index: int) -> DeleteVideoPipelineSectionResponse:
    logger.info("received request to delete pipeline section")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
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




@router.post("/{video_pipeline_id}/process", name="process video pipeline content")
async def process_video_pipeline_content(video_pipeline_id: str, request: CreateVideoPipelineOutlineRequest) -> VideoPipeline:
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    # use modular operation to process content
    video_pipeline = process_content(
        video_pipeline,
        skip_stock=request.skip_stock,
        target_segments=request.target_segments,
        segment_duration=request.segment_duration,
        openai_api_key=config.openai_api_key,
        unsplash_access_key=config.unsplash_access_key,
        pexels_api_key=config.pexels_api_key,
        prompts_dir=config.get_prompts_directory()
    )
    
    # Save to database
    await update_pipeline_in_db(video_pipeline_id, video_pipeline)
    return video_pipeline

@router.get("/{video_pipeline_id}/context-chunks", name="get video pipeline context chunks")
async def get_video_pipeline_context_chunks(video_pipeline_id: str) -> List[VideoPipelineContextChunk]:
    logger.info("received request to get pipeline context chunks")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    return video_pipeline.chunks

@router.get("/{video_pipeline_id}/outline", name="get video pipeline outline")
async def get_video_pipeline_outline(video_pipeline_id: str) -> VideoPipelineOutline:
    logger.info("received request to get pipeline video outline")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    if not video_pipeline.video_outline:
        raise HTTPException(status_code=404, detail="Video outline not found")
    
    return video_pipeline.video_outline

@router.get("/{video_pipeline_id}/outline/segments", name="get video pipeline outline segments")
async def get_video_pipeline_outline_segments(video_pipeline_id: str) -> List[VideoPipelineSegment]:
    logger.info("received request to get pipeline video outline segments")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    if not video_pipeline.video_outline:
        raise HTTPException(status_code=404, detail="Video outline not found")
    
    return video_pipeline.video_outline.segments

@router.post("/{video_pipeline_id}/outline/segments", name="add video pipeline outline segment")
async def add_video_pipeline_outline_segment(video_pipeline_id: str, segment: VideoPipelineSegment) -> VideoPipelineSegment:
    logger.info("received request to add pipeline video outline segment")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    try:
        # use reusable function to add segment
        added_segment = add_segment_to_outline(video_pipeline, segment)
        
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        return added_segment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{video_pipeline_id}/outline/segments/{index}", name="update video pipeline outline segment")
async def update_video_pipeline_outline_segment(video_pipeline_id: str, index: int, segment: VideoPipelineSegment) -> VideoPipelineSegment:
    logger.info("received request to update pipeline video outline segment")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    try:
        # use reusable function to update segment
        updated_segment = update_segment_in_outline(video_pipeline, index, segment)
        
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        return updated_segment
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{video_pipeline_id}/outline/segments/{index}", name="delete video pipeline outline segment")
async def delete_video_pipeline_outline_segment(video_pipeline_id: str, index: int) -> VideoPipelineSegment:
    logger.info("received request to delete pipeline video outline segment")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    try:
        # use reusable function to delete segment
        deleted_segment = delete_segment_from_outline(video_pipeline, index)
        
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        return deleted_segment
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{video_pipeline_id}/generate-segment-images", name="generate video pipeline segment images")
async def generate_video_pipeline_segment_images(video_pipeline_id: str, indexes: List[int]) -> VideoPipelineOutline:
    logger.info("received request to generate images for pipeline segments")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    try:
        # use reusable function to generate segment images
        generate_images_for_segments(
            video_pipeline,
            indexes,
            openai_api_key=config.openai_api_key,
            prompts_dir=config.get_prompts_directory()
        )
        
        # update database
        await update_pipeline_in_db(video_pipeline_id, video_pipeline)
        
        if not video_pipeline.video_outline:
            raise HTTPException(status_code=404, detail="Video outline not found")
        
        return video_pipeline.video_outline
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{video_pipeline_id}/generate-scripts", name="generate video pipeline scripts")
async def generate_video_pipeline_scripts(video_pipeline_id: str, provider: Optional[str] = 'elevenlabs') -> VideoPipeline:
    logger.info("received request to generate scripts and voiceovers")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    # use modular operation to generate scripts
    video_pipeline = generate_scripts(
        video_pipeline,
        provider=provider,
        openai_api_key=config.openai_api_key,
        elevenlabs_api_key=config.elevenlabs_api_key,
        voice_id=config.get('voiceover.voice_id'),
        prompts_dir=config.get_prompts_directory()
    )
    
    # save to database
    await update_pipeline_in_db(video_pipeline_id, video_pipeline)
    logger.info(f"scripts and voiceovers generated. pipeline ID: {video_pipeline.id}")
    return video_pipeline

@router.get("/{video_pipeline_id}/scripts", name="get video pipeline scripts")
async def get_video_pipeline_scripts(video_pipeline_id: str) -> VideoPipelineScript:
    logger.info("received request to view pipeline script data")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    if not video_pipeline.script_data:
        raise HTTPException(status_code=404, detail="Script data not found")
    
    return video_pipeline.script_data

@router.put("/{video_pipeline_id}/scripts", name="update video pipeline scripts")
async def update_video_pipeline_scripts(video_pipeline_id: str, script_data: VideoPipelineScript) -> VideoPipelineScript:
    logger.info("received request to update pipeline script data")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    # use reusable function to update scripts
    updated_script = update_scripts_in_pipeline(video_pipeline, script_data)
    
    # update database
    await update_pipeline_in_db(video_pipeline_id, video_pipeline)
    return updated_script



resolution_map = {
    VideoResolution.RESOLUTION_4K: (3840, 2160),
    VideoResolution.RESOLUTION_1080P: (1920, 1080),
    VideoResolution.RESOLUTION_720P: (1280, 720),
    VideoResolution.RESOLUTION_480P: (640, 480),
}


@router.post("/{video_pipeline_id}/generate", name="generate video pipeline output")
async def generate_video_pipeline_output(video_pipeline_id: str, request: GenerateVideoPipelineRequest) -> VideoPipeline:
    logger.info("received request to generate video")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    # use modular operation to generate video
    video_pipeline = generate_video(
        video_pipeline,
        title=request.title,
        subtitle=request.subtitle,
        resolution=resolution_map[request.resolution],
        fps=request.fps,
        title_duration=request.title_duration,
        end_duration=request.end_duration,
        transition_duration=request.transition_duration,
        background_type=request.background_type
    )
    
    # save to database
    await update_pipeline_in_db(video_pipeline_id, video_pipeline)
    logger.info(f"video generated successfully: {video_pipeline.video_path}")
    return video_pipeline


@router.put("/{video_pipeline_id}/segments/{index}/background", name="update video pipeline segment background")
async def update_video_pipeline_segment_background(video_pipeline_id: str, index: int, background: VideoPipelineSegmentBackground) -> VideoPipelineOutline:
    logger.info("received request to update video segment background")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    # Use reusable function to update segment background
    update_segment_background(
        video_pipeline,
        index,
        background_colors=background.colors,
        background_type=background.type,
        background_image_path=background.image_path
    )
    
    # update database
    await update_pipeline_in_db(video_pipeline_id, video_pipeline)
    
    if not video_pipeline.video_outline:
        raise HTTPException(status_code=404, detail="Video outline not found")
    
    logger.info(f"video segment background updated successfully: {background.colors}, {background.type}, {background.image_path}")
    return video_pipeline.video_outline


async def regenerate_video_pipeline_segment_audio(video_pipeline_id: str, provider: Optional[str] = 'elevenlabs') -> VideoPipeline:
    logger.info("received request to regenerate audio for pipeline segments")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    script_data = video_pipeline.script_data
    if not script_data:
        raise HTTPException(status_code=500, detail="Script data not found")
    output_dir = os.path.join(config.get('output.temp_directory', 'temp'), video_pipeline.path_id, 'audio')
    os.makedirs(output_dir, exist_ok=True)
    voiceover_gen = VoiceoverGenerator(
        provider=provider,
        api_key=config.elevenlabs_api_key,
        voice_id=config.get('voiceover.voice_id'),
        output_dir=output_dir
    )
    script_data_with_audio: VideoPipelineScript = voiceover_gen.generate_voiceovers(script_data)
    video_pipeline.script_data = script_data_with_audio
    logger.info(f"generated voiceovers for {len(script_data_with_audio.segments)} segments")
    # generate combined audio
    combined_audio_path = os.path.join(output_dir, 'full_voiceover.mp3')
    total_duration = voiceover_gen.generate_full_audio(script_data_with_audio, combined_audio_path)
    video_pipeline.full_audio_path = combined_audio_path
    video_pipeline.full_audio_duration = total_duration
    logger.info(f"combined audio generated: {combined_audio_path} ({total_duration:.1f}s)")
    # update database using helper function
    await update_pipeline_in_db(video_pipeline_id, video_pipeline)
    logger.info(f"audio regenerated successfully. pipeline ID: {video_pipeline.id}")
    return video_pipeline

@router.get("/{video_pipeline_id}/output/download", name="download video pipeline output")
async def download_video_pipeline_output(video_pipeline_id: str) -> FileResponse:
    logger.info("received request to download video")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
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

@router.get("/{video_pipeline_id}/output/stream", name="stream video pipeline output")
async def stream_video_pipeline_output(video_pipeline_id: str, request: Request) -> StreamingResponse:
    logger.info("received request to stream video")
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

@router.post("/{video_pipeline_id}/review", name="add video pipeline review")
async def add_video_pipeline_review(video_pipeline_id: str, request: VideoPipelineReviewRequest) -> VideoPipeline:
    logger.info("received request to add pipeline review")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    if request.rating is not None:
        video_pipeline.rating = request.rating
    if request.feedback is not None:
        video_pipeline.feedback = request.feedback
    
    # update database
    await update_pipeline_in_db(video_pipeline_id, video_pipeline)
    
    logger.info(f"pipeline review added successfully: {video_pipeline.rating}, {video_pipeline.feedback}")
    return video_pipeline

@router.websocket("/{video_pipeline_id}/ws", name="video pipeline state socket")
async def video_pipeline_state_socket(video_pipeline_id: str, websocket: WebSocket) -> VideoPipeline:
    logger.info("received request to connect to pipeline state socket")
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    await websocket.accept()
    while True:
        # wait for updates to the pipeline data
        await asyncio.sleep(1)
        # send updated pipeline data to the client
        await websocket.send_json(video_pipeline.model_dump(mode="json", exclude={"user_id"}))

async def run_all_video_pipeline_operations_background(video_pipeline_id: str,
                                                 target_segments: int,
                                                 segment_duration: int,
                                                 provider: str,
                                                 title: Optional[str] = None,
                                                 subtitle: Optional[str] = None,
                                                 resolution: Optional[VideoResolution] = VideoResolution.RESOLUTION_720P,
                                                 fps: Optional[int] = 30,
                                                 title_duration: Optional[float] = 3.0,
                                                 end_duration: Optional[float] = 3.0,
                                                 transition_duration: Optional[float] = 0.5,
                                                 background_type: Optional[BackgroundType] = BackgroundType.GRADIENT) -> None:
    # get pipeline using helper function
    video_pipeline = await get_pipeline_by_id(video_pipeline_id)
    
    # use modular operation to process content
    video_pipeline = process_content(
        video_pipeline,
        skip_stock=False,
        target_segments=target_segments,
        segment_duration=segment_duration,
        openai_api_key=config.openai_api_key,
        unsplash_access_key=config.unsplash_access_key,
        pexels_api_key=config.pexels_api_key,
        prompts_dir=config.get_prompts_directory()
    )
    
    # save to database
    await update_pipeline_in_db(video_pipeline_id, video_pipeline)
    
    # use modular operation to generate scripts
    video_pipeline = generate_scripts(
        video_pipeline,
        provider=provider,
        openai_api_key=config.openai_api_key,
        elevenlabs_api_key=config.elevenlabs_api_key,
        voice_id=config.get('voiceover.voice_id'),
        prompts_dir=config.get_prompts_directory()
    )
    
    # save to database
    await update_pipeline_in_db(video_pipeline_id, video_pipeline)
    
    # use modular operation to generate video
    video_pipeline = generate_video(
        video_pipeline,
        title=title,
        subtitle=subtitle,
        resolution=resolution_map[resolution],
        fps=fps,
        title_duration=title_duration,
        end_duration=end_duration,
        transition_duration=transition_duration,
        background_type=background_type
    )
    # save to database
    await update_pipeline_in_db(video_pipeline_id, video_pipeline)
    logger.info(f"all pipeline operations completed successfully. pipeline id: {video_pipeline.id}")
    return video_pipeline

async def run_all_video_pipeline_operations(request: RunVideoPipelineOperationsRequest,
                                      background_tasks: BackgroundTasks) -> VideoPipelineSummary:
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
    video_pipeline = VideoPipeline()
    video_pipeline.name = request.name
    video_pipeline.description = request.description
    video_pipeline.tags = request.tags or []
    video_pipeline.projects = request.projects or []
    video_pipeline.source_type = SourceType.HTML
    video_pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING,
                               VideoPipelineStatus.IN_PROGRESS)


    logger.info("pipeline data object created")
    # create temp directory for metadata
    temp_dir = config.get('output.temp_directory', 'temp')
    images_dir = os.path.join(temp_dir, video_pipeline.id, 'images')
    Path(images_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"created temp directory for metadata: {images_dir}")
    # save file to temp directory
    with open(os.path.join(temp_dir, video_pipeline.id, 'data.html'), 'wb') as f:
        f.write(response.content)
    logger.info(f"saved file to temp directory: {os.path.join(temp_dir, video_pipeline.id, 'data.html')}")
    video_pipeline.source_path = os.path.join(temp_dir, video_pipeline.id, 'data.html')

    # process HTML document using modular operation
    video_pipeline = process_html_document(
        video_pipeline,
        html_path=request.url,
        extract_images=True,
        openai_api_key=config.openai_api_key,
        prompts_dir=config.get_prompts_directory()
    )

    # save pipeline data to database
    logger.info("saving pipeline data to database")
    video_pipeline.path_id = video_pipeline.id
    db_pipeline = await video_pipelines_collection.insert_one(video_pipeline.model_dump(mode="json"))
    video_pipeline.id = str(db_pipeline.inserted_id)
    logger.info(f"pipeline data saved to database with id: {video_pipeline.id}")
    # we have to update the id to the actual id because the id is generated by mongodb and not by us
    await video_pipelines_collection.update_one(
            {"_id": ObjectId(db_pipeline.inserted_id)},
            {"$set": {"id": video_pipeline.id}}
        )
    background_tasks.add_task(run_all_video_pipeline_operations_background, video_pipeline.id,
                              request.target_segments,
                              request.segment_duration,
                              request.provider,
                              request.title, request.subtitle, request.resolution,
                              request.fps, request.title_duration, request.end_duration,
                              request.transition_duration, request.background_type)
    return VideoPipelineSummary(**video_pipeline.model_dump(mode="json"))