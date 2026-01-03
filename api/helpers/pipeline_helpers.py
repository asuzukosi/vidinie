"""
Helper functions for pipeline API routes.
Provides reusable functions for common operations like retrieving pipelines.
"""

from typing import Optional, Dict, Any
from bson.objectid import ObjectId
from fastapi import HTTPException
from core.data import VideoPipeline
from api.core.db import video_pipelines_collection
from core.utils.logger import get_logger
from core.data import VideoPipeline

logger = get_logger('pipeline_helpers')

async def get_pipeline_by_id(video_pipeline_id: str) -> VideoPipeline:
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
    await video_pipelines_collection.update_one(
        {"_id": ObjectId(video_pipeline_id)},
        {"$set": pipeline.model_dump(mode="json")}
    )

