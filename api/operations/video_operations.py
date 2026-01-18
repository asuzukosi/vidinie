"""
video generation operations for the API.
composes final video from scripts, audio, and visual assets.
"""

import os
from datetime import datetime
from typing import Optional
from core.utils.logger import get_logger
from core.utils.config_loader import config
from core.data import (
    VideoPipeline,
    VideoPipelineStage,
    VideoPipelineStatus,
    BackgroundType,
)
from core.operations.video_generator import VideoGenerator

logger = get_logger("video_operations")


def generate_video(
    pipeline: VideoPipeline,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    resolution: tuple = (1920, 1080),
    fps: int = 30,
    title_duration: float = 3.0,
    end_duration: float = 3.0,
    transition_duration: float = 0.5,
    background_type: Optional[BackgroundType] = None
) -> VideoPipeline:
    """
    generate video from script and audio.
    args:
        pipeline: video pipeline object with script data and full audio path
        title: video title
        subtitle: video subtitle
        resolution: video resolution (width, height)
        fps: frames per second
        title_duration: title screen duration in seconds
        end_duration: end screen duration in seconds
        transition_duration: transition duration in seconds
        background_type: background type
    returns:
        updated video pipeline with video path
    """
    temp_dir = config.get('output.temp_directory', 'temp')
    
    pipeline.update_stage(VideoPipelineStage.VIDEO_GENERATION, VideoPipelineStatus.IN_PROGRESS)
    
    if not pipeline.full_audio_path:
        logger.error("Full audio path not found in pipeline data")
        pipeline.update_stage(VideoPipelineStage.VIDEO_GENERATION, VideoPipelineStatus.FAILED)
        return pipeline
    
    if not pipeline.full_audio_duration:
        logger.error("Full audio duration not found in pipeline data")
        pipeline.update_stage(VideoPipelineStage.VIDEO_GENERATION, VideoPipelineStatus.FAILED)
        return pipeline
    
    if not pipeline.script_data:
        logger.error("Script data not found in pipeline data")
        pipeline.update_stage(VideoPipelineStage.VIDEO_GENERATION, VideoPipelineStatus.FAILED)
        return pipeline
    
    try:
        script_data = pipeline.script_data
        logger.info(f"Using script data for {len(script_data.segments)} segments")
        
        # generate video
        video_dir = os.path.join(temp_dir, pipeline.id, 'video')
        os.makedirs(video_dir, exist_ok=True)
        
        video_path = os.path.join(video_dir, f"video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4")
        
        video_gen = VideoGenerator(
            config=config,
            video_title=title or script_data.title,
            subtitle=subtitle or "",
            resolution=resolution,
            fps=fps,
            title_duration=title_duration,
            end_duration=end_duration,
            transition_duration=transition_duration,
            background_type=background_type or BackgroundType.GRADIENT
        )
        
        generated_video_path = video_gen.generate_video(script_data, video_path)
        pipeline.video_path = generated_video_path
        pipeline.output_path = generated_video_path
        
        # clear rating and feedback when video is regenerated
        pipeline.rating = None
        pipeline.feedback = None
        
        pipeline.update_stage(VideoPipelineStage.VIDEO_GENERATION, VideoPipelineStatus.COMPLETED)
        logger.info(f"video generated successfully: {generated_video_path}")
        return pipeline
        
    except Exception as e:
        logger.error(f"error during video generation: {str(e)}", exc_info=True)
        pipeline.update_stage(VideoPipelineStage.VIDEO_GENERATION, VideoPipelineStatus.FAILED)
        return pipeline

