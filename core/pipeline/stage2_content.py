"""
content analysis operation
analyze content and create video outline with visual asset planning.
requires pipeline_id to load cached video pipeline.
workflow sequence:
    this is the second operation in the standard workflow:
    1. document_processing  - parse pdf and extract content (stage1)
    2. content_analysis     - analyze content and create video outline (THIS MODULE - stage2)
    3. script_generation    - generate narration scripts and voiceovers (stage3)
    4. video_generation     - compose final video from all assets (stage4)
    
    note: the workflow can be customized based on document type and requirements.
"""

import sys
import os
import argparse
from utils.logger import setup_logging, get_logger
from core.utils.config_loader import config
from core.data import VideoPipeline
from core.operations.content_analyzer import process_content

setup_logging(log_dir='temp')
logger = get_logger('stage2_content')


def create_video_outline(pipeline_id: str,
                         skip_stock: bool = False,
                         target_segments: int = 7,
                         segment_duration: int = 45) -> VideoPipeline:
    """
    analyze content and create video outline.
    requires pipeline_id to load cached video pipeline (cache is required).
    args:
        pipeline_id: uuid of existing video pipeline
        skip_stock: skip stock image fetching
        target_segments: target number of video segments
        segment_duration: target duration per segment in seconds
    returns:
        video pipeline instance with video outline
    """
    logger.info("stage 2: content analysis started")
    temp_dir = config.get('output.temp_directory', 'temp')
    
    # load video pipeline by id (cache is required)
    try:
        video_pipeline = VideoPipeline.load_by_id(pipeline_id, temp_dir)
        logger.info(f"loaded video pipeline: {video_pipeline.id}")
    except FileNotFoundError:
        logger.error(f"video pipeline not found for id: {pipeline_id}")
        logger.error("run stage1_parsing.py first")
        sys.exit(1)
    
    # use modular operation to process content
    video_pipeline = process_content(
        video_pipeline,
        skip_stock=skip_stock,
        target_segments=target_segments,
        segment_duration=segment_duration
    )
    
    # save video pipeline
    if video_pipeline.status.value == "completed":
        temp_dir = config.get('output.temp_directory', 'temp')
        video_pipeline.save_to_folder(temp_dir)
        video_pipeline.save_to_pickle(os.path.join(temp_dir, f"pipeline_{video_pipeline.id}.pkl"))
    
    return video_pipeline


def main():
    parser = argparse.ArgumentParser(description='stage 2: analyze content and create video outline')
    parser.add_argument('--pipeline-id', type=str, required=True,
                        help='uuid of pipeline data (from stage 1)')
    parser.add_argument('--skip-stock', action='store_true', help='skip stock image fetching')
    parser.add_argument('--target-segments', type=int, default=7, help='target number of video segments')
    parser.add_argument('--segment-duration', type=int, default=45, help='target duration per segment in seconds')
    args = parser.parse_args()
    
    video_pipeline = create_video_outline(
        args.pipeline_id,
        skip_stock=args.skip_stock,
        target_segments=args.target_segments,
        segment_duration=args.segment_duration
    )
    
    if video_pipeline.status == "completed":
        logger.info(f"video outline created successfully. pipeline id: {video_pipeline.id}")
        sys.exit(0)
    else:
        logger.error(f"video outline creation failed. pipeline id: {video_pipeline.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()

