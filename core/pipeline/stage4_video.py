"""
video generation operation

compose final video from scripts, audio, and visual assets.
requires pipeline_id to load cached video pipeline.

workflow sequence:
    this is the fourth and final operation in the standard workflow:
    1. document_processing  - parse pdf and extract content (stage1)
    2. content_analysis     - analyze content and create video outline (stage2)
    3. script_generation    - generate narration scripts and voiceovers (stage3)
    4. video_generation     - compose final video from all assets (THIS MODULE - stage4)
    
    note: the workflow can be customized based on document type and requirements.
"""
import sys
import os
import argparse
from pathlib import Path
from typing import Optional
# add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logging, get_logger
from utils.config_loader import get_config
from core.data import VideoPipeline
from core.operations.video_generator import generate_video as generate_video_operation

setup_logging(log_dir='temp')
logger = get_logger('stage4_video')


def generate_video(pipeline_id: str,
                     output_path: Optional[str] = None) -> VideoPipeline:
    """
    generate video from script and audio.
    requires pipeline_id to load cached video pipeline.
    args:
        pipeline_id: uuid of existing video pipeline
        output_path: custom output path for video (default: output/video.mp4)
    returns:
        video pipeline instance with video path
    """
    logger.info("stage 4: video generation started")
    
    config = get_config()
    temp_dir = config.get('output.temp_directory', 'temp')
    
    # load video pipeline by id (cache is required)
    try:
        video_pipeline = VideoPipeline.load_by_id(pipeline_id, temp_dir)
        logger.info(f"loaded video pipeline for id: {pipeline_id}")
    except FileNotFoundError:
        logger.error(f"video pipeline not found for id: {pipeline_id}")
        logger.error("run stages 1-3 first to create video pipeline")
        sys.exit(1)
    
    # use modular operation to generate video
    config = get_config()
    
    # determine output path if not provided
    if not output_path:
        output_dir = config.get('output.directory', 'output')
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_path = os.path.join(output_dir, f"video_{video_pipeline.id}.mp4")
    
    video_pipeline = generate_video_operation(
        video_pipeline,
        title=None,  # set default from script_data
        subtitle=None,  # set default from script_data
        resolution=(1920, 1080),  # Default resolution
        fps=30,  # set default fps
        title_duration=3.0,  # set default title duration
        end_duration=3.0,  # set default end duration
        transition_duration=0.5,  # set default transition duration
        background_type=None  # set default background type
    )
    
    # save video pipeline
    if video_pipeline.status.value == "completed":
        temp_dir = config.get('output.temp_directory', 'temp')
        video_pipeline.save_to_folder(temp_dir)
        video_pipeline.save_to_pickle(os.path.join(temp_dir, f"pipeline_{video_pipeline.id}.pkl"))
    
    return video_pipeline


def main():
    parser = argparse.ArgumentParser(description='stage 4: generate video from script and audio')
    parser.add_argument('--pipeline-id', type=str, required=True,
                        help='uuid of pipeline data (from stage 3)')
    parser.add_argument('--output', type=str, default=None,
                        help='custom output path for video')
    args = parser.parse_args()
    
    video_pipeline = generate_video(
        args.pipeline_id,
        output_path=args.output
    )
    
    if video_pipeline.status == "completed" and video_pipeline.video_path:
        logger.info(f"video generated successfully: {video_pipeline.video_path}")
        logger.info(f"pipeline id: {video_pipeline.id}")
        sys.exit(0)
    else:
        logger.error(f"video generation failed. pipeline id: {video_pipeline.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()

