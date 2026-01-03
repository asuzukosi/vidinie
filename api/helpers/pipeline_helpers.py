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
from core.utils.config_loader import config
import os
import shutil

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


async def create_pipeline_in_db(pipeline: VideoPipeline) -> VideoPipeline:
    """
    create a new pipeline in the database
    args:
        pipeline: the pipeline to create
    returns:
        the pipeline with the updated id field
    """
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


async def migrate_pipeline_files(old_id: str, new_id: str, pipeline: VideoPipeline) -> None:
    """
    move pipeline folder from old id path to new id path when MongoDB generates a new _id.
    args:
        old_id: the original UUID id before MongoDB save
        new_id: the new MongoDB ObjectId string
        pipeline: the VideoPipeline object (not used, kept for compatibility)
    """
    if old_id == new_id:
        return  # no migration needed
    
    temp_dir = config.get('output.temp_directory', 'temp')
    old_path = os.path.join(temp_dir, old_id)
    new_path = os.path.join(temp_dir, new_id)
    
    if not os.path.exists(old_path):
        logger.info(f"No folder to migrate from {old_path}")
        return
    
    logger.info(f"Moving pipeline folder from {old_path} to {new_path}")
    
    try:
        # move the entire folder
        shutil.move(old_path, new_path)
        logger.info(f"Successfully moved pipeline folder from {old_id} to {new_id}")
    except Exception as e:
        logger.error(f"Error moving pipeline folder from {old_id} to {new_id}: {str(e)}")