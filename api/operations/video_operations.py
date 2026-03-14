"""
video generation operations for the API.
composes final video from scripts, audio, and visual assets.
"""

import os
from typing import Optional
from core.utils.logger import get_logger
from core.utils.config_loader import config
from core.data import (
    VideoPipeline,
    VideoPipelineStage,
    VideoPipelineStatus,
)
from core.operations.video_generator import VideoGenerator, VideoResolution

logger = get_logger("video_operations")


async def generate_video(
    pipeline: VideoPipeline,
    resolution: Optional[VideoResolution] = VideoResolution.RESOLUTION_1080P
) -> VideoPipeline:
    """
    generate video from script and audio.
    args:
        pipeline: video pipeline object with script data and full audio path
        resolution: video resolution enum
    returns:
        updated video pipeline with video path
    """
    output_dir = str(config.output_directory)
    
    if not pipeline.full_audio_path:
        logger.error("Full audio path not found in pipeline data")
        raise ValueError("Full audio path not found in pipeline data")
    
    if not pipeline.full_audio_duration:
        logger.error("Full audio duration not found in pipeline data")
        raise ValueError("Full audio duration not found in pipeline data")
    
    if not pipeline.script_data:
        logger.error("Script data not found in pipeline data")
        raise ValueError("Script data not found in pipeline data")
    
    try:
        script_data = pipeline.script_data
        logger.info(f"Using script data for {len(script_data.segments)} segments")
        
        # generate video
        video_dir = os.path.join(output_dir, pipeline.id)
        os.makedirs(video_dir, exist_ok=True)
        
        video_gen = VideoGenerator(
            resolution=resolution,
            user_instructions=pipeline.instructions
        )
        
        generated_video_path = await video_gen.generate_video(script_data, video_dir)
        pipeline.video_path = generated_video_path
        pipeline.output_path = generated_video_path
        
        # clear rating and feedback when video is regenerated
        pipeline.rating = None
        pipeline.feedback = None
        
        logger.info(f"video generated successfully: {generated_video_path}")
        return pipeline
        
    except Exception as e:
        logger.error(f"error during video generation: {str(e)}", exc_info=True)
        raise

