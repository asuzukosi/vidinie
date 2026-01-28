import os
from celery import Celery
from celery.signals import worker_process_init
from core.data import VideoPipeline, VideoPipelineStage, SourceType, VideoPipelineStatus
from core.utils.logger import get_logger
from api.core.signals import broadcast_message
from typing import Optional
import asyncio
from api.operations.document_operations import (
    process_pdf_document,
    process_html_document,
)
from api.operations.content_operations import process_content
from api.operations.script_operations import generate_scripts
from api.operations.video_operations import generate_video
from api.helpers.pipeline_helpers import update_pipeline_in_db
from api.helpers.pipeline_helpers import get_pipeline_by_id
from api.core.db import initialize_db

logger = get_logger("celery")


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

# use solo pool to avoid forking issues with async/event loops
# alternatively, we can use threads pool, but solo is safer for async operations
celery.conf.worker_pool = 'solo'


@worker_process_init.connect
def init_worker_process(**kwargs):
    """
    initialize database connection and event loop in each Celery worker process.
    ensures the MongoDB async client is properly initialized with an event loop.
    """
    logger.info("initializing database connection in Celery worker process")
    # create a new event loop for this worker process
    # close any existing loop first to avoid conflicts
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.close()
    except RuntimeError:
        pass
    
    # create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # initialize the database connection
    try:
        loop.run_until_complete(initialize_db())
        logger.info("Database connection initialized successfully in Celery worker")
    except Exception as e:
        logger.error(f"Failed to initialize database in Celery worker: {str(e)}")
        raise


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
            await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "document_processing", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.IN_PROGRESS})
            # update pipeline status
            video_pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.IN_PROGRESS)
            await update_pipeline_in_db(video_pipeline.id, video_pipeline)
            try:
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
                await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "document_processed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.COMPLETED})
                logger.info(f"document processing task completed for pipeline: {video_pipeline.id}")
            except Exception as e:
                logger.error(f"error during document processing task for pipeline: {video_pipeline.id}: {str(e)}")
                video_pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
                await update_pipeline_in_db(video_pipeline.id, video_pipeline)
                await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "document_processing_failed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.FAILED})
                logger.info(f"document processing task failed for pipeline: {video_pipeline.id}")
    
        elif video_pipeline.source_type == SourceType.HTML:
            logger.info(f"running document processing task for pipeline: {video_pipeline.id}")
            await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "document_processing", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.IN_PROGRESS})
            # update pipeline status
            video_pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.IN_PROGRESS)
            await update_pipeline_in_db(video_pipeline.id, video_pipeline)
            try:
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
                await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "document_processed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.COMPLETED})
                logger.info(f"document processing task completed for pipeline: {video_pipeline.id}")
            except Exception as e:
                logger.error(f"error during document processing task for pipeline: {video_pipeline.id}: {str(e)}")
                video_pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
                await update_pipeline_in_db(video_pipeline.id, video_pipeline)
                await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "document_processing_failed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.FAILED})
                logger.info(f"document processing task failed for pipeline: {video_pipeline.id}")
        else:
            raise ValueError(f"unsupported source type: {video_pipeline.source_type}")
    
    # check and run content analysis task
    if VideoPipelineStage.CONTENT_ANALYSIS in tasks_to_run:
        logger.info(f"running content analysis task for pipeline: {video_pipeline.id}")
        await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "content_analysis", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.IN_PROGRESS})
        # update pipeline status
        video_pipeline.update_stage(VideoPipelineStage.CONTENT_ANALYSIS, VideoPipelineStatus.IN_PROGRESS)
        await update_pipeline_in_db(video_pipeline.id, video_pipeline)
        try:
            # process content
            target_segments = kwargs.get('target_segments', 5)
            segment_duration = kwargs.get('segment_duration', 40)
            # process content
            video_pipeline = process_content(video_pipeline, 
                                            target_segments=target_segments, 
                                            segment_duration=segment_duration)
            # update database
            await update_pipeline_in_db(video_pipeline.id, video_pipeline)
            await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "content_processed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.COMPLETED})
            logger.info(f"content analysis task completed for pipeline: {video_pipeline.id}")
        except Exception as e:
            logger.error(f"error during content analysis task for pipeline: {video_pipeline.id}: {str(e)}")
            video_pipeline.update_stage(VideoPipelineStage.CONTENT_ANALYSIS, VideoPipelineStatus.FAILED)
            await update_pipeline_in_db(video_pipeline.id, video_pipeline)
            await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "content_analysis_failed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.FAILED})
            logger.info(f"content analysis task failed for pipeline: {video_pipeline.id}")
    
    # check and run script genratiion task
    if VideoPipelineStage.SCRIPT_GENERATION in tasks_to_run:
        logger.info(f"running script generation task for pipeline: {video_pipeline.id}")
        await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "script_generation", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.IN_PROGRESS})
        # update pipeline status
        video_pipeline.update_stage(VideoPipelineStage.SCRIPT_GENERATION, VideoPipelineStatus.IN_PROGRESS)
        await update_pipeline_in_db(video_pipeline.id, video_pipeline)
        try:
            video_pipeline = generate_scripts(video_pipeline)
            # update database
            await update_pipeline_in_db(video_pipeline.id, video_pipeline)
            # broadcast message
            await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "scripts_generated", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.COMPLETED})
            logger.info(f"script generation task completed for pipeline: {video_pipeline.id}")
        except Exception as e:
            logger.error(f"error during script generation task for pipeline: {video_pipeline.id}: {str(e)}")
            video_pipeline.update_stage(VideoPipelineStage.SCRIPT_GENERATION, VideoPipelineStatus.FAILED)
            await update_pipeline_in_db(video_pipeline.id, video_pipeline)
            await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "script_generation_failed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.FAILED})
            logger.info(f"script generation task failed for pipeline: {video_pipeline.id}")
    
    # check and run video generation task
    if VideoPipelineStage.VIDEO_GENERATION in tasks_to_run:
        logger.info(f"running video generation task for pipeline: {video_pipeline.id}")
        await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "video_generation", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.IN_PROGRESS})
        # update pipeline status
        video_pipeline.update_stage(VideoPipelineStage.VIDEO_GENERATION, VideoPipelineStatus.IN_PROGRESS)
        await update_pipeline_in_db(video_pipeline.id, video_pipeline)
        try:
            video_pipeline = generate_video(video_pipeline)
            # update database
            await update_pipeline_in_db(video_pipeline.id, video_pipeline)
            await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "video_generated", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.COMPLETED})
            logger.info(f"video generation task completed for pipeline: {video_pipeline.id}")
        except Exception as e:
            logger.error(f"error during video generation task for pipeline: {video_pipeline.id}: {str(e)}")
            video_pipeline.update_stage(VideoPipelineStage.VIDEO_GENERATION, VideoPipelineStatus.FAILED)
            await update_pipeline_in_db(video_pipeline.id, video_pipeline)
            await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "video_generation_failed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.FAILED})
            logger.info(f"video generation task failed for pipeline: {video_pipeline.id}")

    # all tasks completed for pipeline
    logger.info(f"all tasks completed for pipeline: {video_pipeline.id}")
    await broadcast_message(f"pipeline-tasks-{video_pipeline.id}", {"type": "pipeline_completed", "pipeline_id": video_pipeline.id, "status": VideoPipelineStatus.COMPLETED})
    logger.info(f"pipeline completed for pipeline: {video_pipeline.id}")
    return video_pipeline


async def run_next_stages_async(video_pipeline: VideoPipeline, stage: Optional[VideoPipelineStage] = None, **kwargs) -> VideoPipeline:
    """
    async function that retrieves the pipeline from the database and runs run_next_stages.
    """
    logger.info(f"run_next_stages_async: starting for pipeline {video_pipeline.id}")
    # retrieve pipeline from database
    video_pipeline = await get_pipeline_by_id(video_pipeline.id)
    # run the async run_next_stages function
    return await run_next_stages(video_pipeline, stage=stage, **kwargs)

@celery.task
def run_next_stages_task(video_pipeline_id: str, stage: Optional[VideoPipelineStage] = None, **kwargs) -> bool:
    """
    celery task wrapper that retrieves the pipeline from the database and runs run_next_stages.
    This separates the Celery task logic from the async pipeline execution logic.
    """
    logger.info(f"starting celery task to run stages")
    try:
        asyncio.run(run_next_stages_async(video_pipeline_id, stage=stage, **kwargs))
        return True
    except Exception as e:
        logger.error(f"run_next_stages_task: error for pipeline {video_pipeline_id}: {str(e)}")
        return False
