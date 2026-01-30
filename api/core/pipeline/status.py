"""
Pipeline status management utilities.
"""

from core.data import VideoPipeline, VideoPipelineStage, VideoPipelineStatus
from core.utils.logger import get_logger
from api.helpers.pipeline_helpers import get_pipeline_by_id, update_pipeline_in_db
from api.core.signals import broadcast_message

logger = get_logger("pipeline.status")


async def mark_pipeline_as_failed(pipeline_id: str) -> None:
    """
    mark a pipeline as failed and broadcast the failure message.
    """
    pipeline = await get_pipeline_by_id(pipeline_id)
    pipeline.status = VideoPipelineStatus.FAILED
    pipeline.document_processing_status = VideoPipelineStatus.FAILED
    await update_pipeline_in_db(pipeline_id, pipeline)
    await broadcast_message(
        f"pipeline-tasks-{pipeline_id}",
        {"type": "pipeline_failed", "pipeline_id": pipeline_id, "status": VideoPipelineStatus.FAILED}
    )
    logger.info(f"Pipeline marked as failed: {pipeline_id}")


async def update_stage_status(
    pipeline: VideoPipeline,
    stage: VideoPipelineStage,
    status: VideoPipelineStatus,
    message_type: str
) -> None:
    """
    update pipeline stage status, save to DB, and broadcast message.
    """
    pipeline.update_stage(stage, status)
    await update_pipeline_in_db(pipeline.id, pipeline)
    await broadcast_message(
        f"pipeline-tasks-{pipeline.id}",
        {
            "type": message_type,
            "pipeline_id": pipeline.id,
            "status": status
        }
    )

