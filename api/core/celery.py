import os
import asyncio
from celery import Celery
from celery.signals import worker_process_init
from core.data import VideoPipelineStage
from core.utils.logger import get_logger
from api.core.db import initialize_db
from api.core.execution.executor import execute_pipeline_stages_for_id
from api.core.execution.status import mark_pipeline_as_failed
from typing import Optional

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
    logger.info("initializing database connection in celery worker process")
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
        logger.info("database connection initialized successfully in celery worker")
    except Exception as e:
        logger.error(f"failed to initialize database in celery worker: {str(e)}")
        raise


@celery.task
def execute_pipeline_task(
    pipeline_id: str,
    start_from_stage: Optional[VideoPipelineStage] = None,
    **kwargs
) -> bool:
    """
    celery task to execute pipeline stages.
    """
    logger.info(f"starting celery task to execute pipeline stages for pipeline: {pipeline_id}")
    
    # get or create event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(initialize_db())
    except RuntimeError:
        # if no event loop exists, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize_db())
    
    try:
        logger.info(f"Executing pipeline stages for pipeline: {pipeline_id}")
        loop.run_until_complete(
            execute_pipeline_stages_for_id(
                pipeline_id,
                start_from_stage=start_from_stage,
                **kwargs
            )
        )
        logger.info(f"Pipeline execution completed successfully for pipeline: {pipeline_id}")
        return True
    except Exception as e:
        logger.error(f"Pipeline execution failed for pipeline {pipeline_id}: {str(e)}")
        try:
            loop.run_until_complete(mark_pipeline_as_failed(pipeline_id))
        except Exception as failure_error:
            logger.error(f"Failed to mark pipeline as failed: {str(failure_error)}")
        return False
