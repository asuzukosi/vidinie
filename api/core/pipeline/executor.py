"""
Pipeline execution orchestrator.
Coordinates the execution of multiple pipeline stages in sequence.
"""

from core.data import VideoPipeline, VideoPipelineStage, VideoPipelineStatus
from core.utils.logger import get_logger
from api.helpers.pipeline_helpers import get_pipeline_by_id
from api.core.signals import broadcast_message, PipelineBroadcastMessageType, PipelineBroadcastStatus
from api.core.pipeline.stage_handlers import (
    execute_document_processing_stage,
    execute_content_analysis_stage,
    execute_script_generation_stage,
    execute_video_generation_stage
)
from typing import Optional, Tuple

logger = get_logger("pipeline.executor")


PIPELINE_STAGES = [
    VideoPipelineStage.DOCUMENT_PROCESSING,
    VideoPipelineStage.CONTENT_ANALYSIS,
    VideoPipelineStage.SCRIPT_GENERATION,
    VideoPipelineStage.VIDEO_GENERATION,
]


async def _execute_document_processing(
    pipeline: VideoPipeline,
    **kwargs
) -> Tuple[VideoPipeline, bool]:
    """
    execute document processing stage.
    """
    pipeline = await get_pipeline_by_id(pipeline.id)
    try:
        pipeline = await execute_document_processing_stage(
            pipeline,
            extract_images=kwargs.get('extract_images', True),
            pdf_content=kwargs.get('pdf_content'),
            html_content=kwargs.get('html_content'),
            original_url=kwargs.get('original_url')
        )
        return pipeline, True
    except Exception as e:
        logger.error(f"Document processing failed for pipeline {pipeline.id}: {str(e)}")
        return pipeline, False


async def _execute_content_analysis(
    pipeline: VideoPipeline,
    **kwargs
) -> Tuple[VideoPipeline, bool]:
    """
    execute content analysis stage.
    """
    pipeline = await get_pipeline_by_id(pipeline.id)
    if pipeline.document_processing_status != VideoPipelineStatus.COMPLETED:
        logger.error(
            f"Document processing not completed for pipeline {pipeline.id}, "
            f"status: {pipeline.document_processing_status}. Skipping content analysis."
        )
        return pipeline, False
    
    try:
        pipeline = await execute_content_analysis_stage(
            pipeline,
            target_segments=kwargs.get('target_segments', 4),
            segment_duration=kwargs.get('segment_duration', 40)
        )
        return pipeline, True
    except Exception as e:
        logger.error(f"content analysis failed for pipeline {pipeline.id}: {str(e)}")
        return pipeline, False


async def _execute_script_generation(
    pipeline: VideoPipeline,
    **kwargs
) -> Tuple[VideoPipeline, bool]:
    """
    execute script generation stage.
    """
    pipeline = await get_pipeline_by_id(pipeline.id)
    if pipeline.content_analysis_status != VideoPipelineStatus.COMPLETED:
        logger.error(
            f"content analysis not completed for pipeline {pipeline.id}, "
            f"status: {pipeline.content_analysis_status}. Skipping script generation."
        )
        return pipeline, False
    
    try:
        pipeline = await execute_script_generation_stage(
            pipeline,
            voice=kwargs.get('voice')
        )
        return pipeline, True
    except Exception as e:
        logger.error(f"script generation failed for pipeline {pipeline.id}: {str(e)}")
        return pipeline, False


async def _execute_video_generation(
    pipeline: VideoPipeline,
    **kwargs
) -> Tuple[VideoPipeline, bool]:
    """
    execute video generation stage.
    """
    pipeline = await get_pipeline_by_id(pipeline.id)
    if pipeline.script_generation_status != VideoPipelineStatus.COMPLETED:
        logger.error(
            f"script generation not completed for pipeline {pipeline.id}, "
            f"status: {pipeline.script_generation_status}. Skipping video generation."
        )
        return pipeline, False
    
    try:
        pipeline = await execute_video_generation_stage(pipeline)
        return pipeline, True
    except Exception as e:
        logger.error(f"Video generation failed for pipeline {pipeline.id}: {str(e)}")
        return pipeline, False


async def _finalize_pipeline_execution(pipeline: VideoPipeline) -> VideoPipeline:
    """
    finalize pipeline execution by refreshing state and broadcasting completion.
    """
    pipeline = await get_pipeline_by_id(pipeline.id)
    logger.info(f"All pipeline stages completed for pipeline: {pipeline.id}")
    await broadcast_message({
        "type": PipelineBroadcastMessageType.PIPELINE,
        "pipeline_id": pipeline.id,
        "user_id": pipeline.user_id or "",
        "status": PipelineBroadcastStatus.COMPLETED
    })
    logger.info(f"Pipeline execution completed for pipeline: {pipeline.id}")
    return pipeline


async def execute_pipeline_stages(
    pipeline: VideoPipeline,
    start_from_stage: Optional[VideoPipelineStage] = None,
    **kwargs
) -> VideoPipeline:
    """
    execute pipeline stages sequentially, starting from the specified stage.
    """
    logger.info(f"executing pipeline stages for pipeline: {pipeline.id}, starting from: {start_from_stage}")
    
    # determine which stages to run
    if start_from_stage:
        stage_index = PIPELINE_STAGES.index(start_from_stage) if start_from_stage in PIPELINE_STAGES else 0
        stages_to_run = PIPELINE_STAGES[stage_index:]
    else:
        stages_to_run = PIPELINE_STAGES
    
    logger.info(f"stages to run: {stages_to_run}")
    
    # execute document processing stage
    if VideoPipelineStage.DOCUMENT_PROCESSING in stages_to_run:
        pipeline, should_continue = await _execute_document_processing(pipeline, **kwargs)
        if not should_continue:
            return pipeline
    
    # execute content analysis stage
    if VideoPipelineStage.CONTENT_ANALYSIS in stages_to_run:
        pipeline, should_continue = await _execute_content_analysis(pipeline, **kwargs)
        if not should_continue:
            return pipeline
    
    # execute script generation stage
    if VideoPipelineStage.SCRIPT_GENERATION in stages_to_run:
        pipeline, should_continue = await _execute_script_generation(pipeline, **kwargs)
        if not should_continue:
            return pipeline
    
    # execute video generation stage
    if VideoPipelineStage.VIDEO_GENERATION in stages_to_run:
        pipeline, should_continue = await _execute_video_generation(pipeline, **kwargs)
        if not should_continue:
            return pipeline
    
    # finalize pipeline execution
    return await _finalize_pipeline_execution(pipeline)


async def execute_pipeline_stages_for_id(
    pipeline_id: str,
    start_from_stage: Optional[VideoPipelineStage] = None,
    **kwargs
) -> VideoPipeline:
    """
    execute pipeline stages for a pipeline ID.
    """
    logger.info(f"executing pipeline stages for pipeline ID: {pipeline_id}")
    pipeline = await get_pipeline_by_id(pipeline_id)
    return await execute_pipeline_stages(pipeline, start_from_stage=start_from_stage, **kwargs)

