from core.data import VideoPipeline, VideoPipelineStage, VideoPipelineStatus, SourceType
from core.utils.logger import get_logger
from api.helpers.pipeline_helpers import update_pipeline_in_db
from api.core.pipeline.status import update_stage_status
from api.core.signals import broadcast_message, PipelineBroadcastMessageType, PipelineBroadcastStatus
from api.operations.document_operations import process_pdf_document, process_html_document
from api.operations.content_operations import process_content
from api.operations.script_operations import generate_scripts
from api.operations.video_operations import generate_video

logger = get_logger("pipeline.stage_handlers")


async def execute_document_processing_stage(
    pipeline: VideoPipeline,
    extract_images: bool = True,
    pdf_content: bytes = None,
    html_content: str = None,
    original_url: str = None
) -> VideoPipeline:
    """
    execute the document processing stage.
    """
    logger.info(f"executing document processing for pipeline: {pipeline.id}")
    await broadcast_message({
        "type": PipelineBroadcastMessageType.DOCUMENT_PROCESSING,
        "pipeline_id": pipeline.id,
        "user_id": pipeline.user_id or "",
        "status": PipelineBroadcastStatus.IN_PROGRESS
    })
    
    await update_stage_status(
        pipeline,
        VideoPipelineStage.DOCUMENT_PROCESSING,
        VideoPipelineStatus.IN_PROGRESS,
        PipelineBroadcastMessageType.DOCUMENT_PROCESSING
    )
    
    try:
        if pipeline.source_type == SourceType.PDF:
            if not pdf_content:
                raise ValueError("pdf_content must be provided")
            
            pipeline = await process_pdf_document(
                pipeline,
                extract_images=extract_images,
                pdf_content=pdf_content
            )
                
        elif pipeline.source_type == SourceType.HTML:
            if not html_content:
                raise ValueError("html_content must be provided")
            
            if not original_url:
                raise ValueError("original_url must be provided for HTML processing")
            
            pipeline = await process_html_document(
                pipeline,
                extract_images=extract_images,
                html_content=html_content,
                original_url=original_url
            )
        else:
            raise ValueError(f"unsupported source type: {pipeline.source_type}")
        
        await update_stage_status(
            pipeline,
            VideoPipelineStage.DOCUMENT_PROCESSING,
            VideoPipelineStatus.COMPLETED,
            PipelineBroadcastMessageType.DOCUMENT_PROCESSING
        )
        logger.info(f"document processing completed for pipeline: {pipeline.id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"error during document processing for pipeline {pipeline.id}: {str(e)}")
        await update_stage_status(
            pipeline,
            VideoPipelineStage.DOCUMENT_PROCESSING,
            VideoPipelineStatus.FAILED,
            PipelineBroadcastMessageType.DOCUMENT_PROCESSING
        )
        raise


async def execute_content_analysis_stage(
    pipeline: VideoPipeline,
    target_segments: int = 4,
    segment_duration: int = 40
) -> VideoPipeline:
    """
    execute the content analysis stage.
    """
    logger.info(f"executing content analysis for pipeline: {pipeline.id}")
    await broadcast_message({
        "type": PipelineBroadcastMessageType.CONTENT_ANALYSIS,
        "pipeline_id": pipeline.id,
        "user_id": pipeline.user_id or "",
        "status": PipelineBroadcastStatus.IN_PROGRESS
    })
    
    await update_stage_status(
        pipeline,
        VideoPipelineStage.CONTENT_ANALYSIS,
        VideoPipelineStatus.IN_PROGRESS,
        PipelineBroadcastMessageType.CONTENT_ANALYSIS
    )
    
    try:
        pipeline = await process_content(
            pipeline,
            target_segments=target_segments,
            segment_duration=segment_duration
        )
        
        await update_stage_status(
            pipeline,
            VideoPipelineStage.CONTENT_ANALYSIS,
            VideoPipelineStatus.COMPLETED,
            PipelineBroadcastMessageType.CONTENT_ANALYSIS
        )
        logger.info(f"content analysis completed for pipeline: {pipeline.id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"error during content analysis for pipeline {pipeline.id}: {str(e)}")
        await update_stage_status(
            pipeline,
            VideoPipelineStage.CONTENT_ANALYSIS,
            VideoPipelineStatus.FAILED,
            PipelineBroadcastMessageType.CONTENT_ANALYSIS
        )
        raise


async def execute_script_generation_stage(
    pipeline: VideoPipeline,
    voice: str = None
) -> VideoPipeline:
    """
    execute the script generation stage.
    """
    logger.info(f"executing script generation for pipeline: {pipeline.id}")
    
    # update voice if provided
    if voice:
        pipeline.voice = voice
        await update_pipeline_in_db(pipeline.id, pipeline)
    
    await broadcast_message({
        "type": PipelineBroadcastMessageType.SCRIPT_GENERATION,
        "pipeline_id": pipeline.id,
        "user_id": pipeline.user_id or "",
        "status": PipelineBroadcastStatus.IN_PROGRESS
    })
    
    await update_stage_status(
        pipeline,
        VideoPipelineStage.SCRIPT_GENERATION,
        VideoPipelineStatus.IN_PROGRESS,
        PipelineBroadcastMessageType.SCRIPT_GENERATION
    )
    
    try:
        pipeline = await generate_scripts(pipeline)
        
        await update_stage_status(
            pipeline,
            VideoPipelineStage.SCRIPT_GENERATION,
            VideoPipelineStatus.COMPLETED,
            PipelineBroadcastMessageType.SCRIPT_GENERATION
        )
        logger.info(f"script generation completed for pipeline: {pipeline.id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"error during script generation for pipeline {pipeline.id}: {str(e)}")
        await update_stage_status(
            pipeline,
            VideoPipelineStage.SCRIPT_GENERATION,
            VideoPipelineStatus.FAILED,
            PipelineBroadcastMessageType.SCRIPT_GENERATION
        )
        raise


async def execute_video_generation_stage(pipeline: VideoPipeline) -> VideoPipeline:
    """
    execute the video generation stage.
    """
    logger.info(f"executing video generation for pipeline: {pipeline.id}")
    await broadcast_message({
        "type": PipelineBroadcastMessageType.VIDEO_GENERATION,
        "pipeline_id": pipeline.id,
        "user_id": pipeline.user_id or "",
        "status": PipelineBroadcastStatus.IN_PROGRESS
    })
    
    await update_stage_status(
        pipeline,
        VideoPipelineStage.VIDEO_GENERATION,
        VideoPipelineStatus.IN_PROGRESS,
        PipelineBroadcastMessageType.VIDEO_GENERATION
    )
    
    try:
        pipeline = await generate_video(pipeline)
        
        await update_stage_status(
            pipeline,
            VideoPipelineStage.VIDEO_GENERATION,
            VideoPipelineStatus.COMPLETED,
            PipelineBroadcastMessageType.VIDEO_GENERATION
        )
        logger.info(f"video generation completed for pipeline: {pipeline.id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"error during video generation for pipeline {pipeline.id}: {str(e)}")
        await update_stage_status(
            pipeline,
            VideoPipelineStage.VIDEO_GENERATION,
            VideoPipelineStatus.FAILED,
            PipelineBroadcastMessageType.VIDEO_GENERATION
        )
        raise

