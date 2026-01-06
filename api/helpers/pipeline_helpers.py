"""
Helper functions for pipeline API routes.
Provides reusable functions for common operations like retrieving pipelines.
"""

from typing import Optional, Dict, Any, List
from bson.objectid import ObjectId
from fastapi import HTTPException
from core.data import VideoPipeline
from api.core.db import video_pipelines_collection
from api.data.pipelines import VideoPipelineSummary
from core.utils.logger import get_logger

logger = get_logger('pipeline_helpers')

async def get_pipeline_by_id(video_pipeline_id: str) -> VideoPipeline:
    if video_pipelines_collection is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")
    try:
        video_pipeline_dict: Optional[Dict[str, Any]] = await video_pipelines_collection.find_one(
            {"_id": ObjectId(video_pipeline_id)}
        )
        if not video_pipeline_dict:
            raise HTTPException(status_code=404, detail="pipeline not found")
        return VideoPipeline(**video_pipeline_dict)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"error retrieving pipeline with id: {video_pipeline_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"error retrieving pipeline: {str(e)}")


async def update_pipeline_in_db(video_pipeline_id: str, pipeline: VideoPipeline) -> None:
    if video_pipelines_collection is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")
    await video_pipelines_collection.update_one(
        {"_id": ObjectId(video_pipeline_id)},
        {"$set": pipeline.model_dump(mode="json")}
    )


async def create_pipeline_in_db(pipeline: VideoPipeline) -> VideoPipeline:
    """
    create a new pipeline in the database
    args:
        pipeline: the pipeline to create
    returns:
        the pipeline with the updated id field
    """
    if video_pipelines_collection is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")
    logger.info("creating new pipeline in database")
    # insert pipeline into database
    db_pipeline = await video_pipelines_collection.insert_one(pipeline.model_dump(mode="json"))
    new_id = str(db_pipeline.inserted_id)
    # update the pipeline's id field
    pipeline.id = new_id
    # put the database record with the new id
    await video_pipelines_collection.update_one(
        {"_id": ObjectId(new_id)},
        {"$set": {"id": new_id}}
    )
    logger.info(f"Pipeline created successfully with id: {new_id}")
    return pipeline


async def get_pipelines_for_user(user_id: str) -> List[VideoPipelineSummary]:
    """
    get all pipelines for a user
    """
    if video_pipelines_collection is None:
        raise HTTPException(status_code=500, detail="database is not initialized")
    try:
        pipelines: List[VideoPipelineSummary] = []
        async for video_pipeline in video_pipelines_collection.find({"user_id": user_id}):
            pipelines.append(VideoPipelineSummary(**video_pipeline))
        return pipelines
    except Exception as e:
        logger.error(f"error retrieving pipelines for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"error retrieving pipelines: {str(e)}")


async def delete_pipeline_from_db(video_pipeline_id: str) -> None:
    """
    delete a pipeline from the database.
    """
    if video_pipelines_collection is None:
        raise HTTPException(status_code=500, detail="database is not initialized")
    try:
        result = await video_pipelines_collection.delete_one({"_id": ObjectId(video_pipeline_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="pipeline not found")
        logger.info(f"pipeline deleted successfully with id: {video_pipeline_id}")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"error deleting pipeline with id: {video_pipeline_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"error deleting pipeline: {str(e)}")