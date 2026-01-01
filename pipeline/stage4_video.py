"""
video generation operation

compose final video from scripts, audio, and visual assets.
requires pipeline_id to load cached pipeline data.

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
from core.operations.video_generator import VideoGenerator
from core.data.pipeline import PipelineData, PipelineStage, PipelineStatus

setup_logging(log_dir='temp')
logger = get_logger('stage4_video')


def generate_video(pipeline_id: str,
                     output_path: Optional[str] = None) -> PipelineData:
    """
    generate video from script and audio.
    requires pipeline_id to load cached pipeline data.
    args:
        pipeline_id: uuid of existing pipeline data
        output_path: custom output path for video (default: output/video.mp4)
    returns:
        pipeline data instance with video path
    """
    logger.info("stage 4: video generation started")
    
    config = get_config()
    temp_dir = config.get('output.temp_directory', 'temp')
    
    # load pipeline data by id (cache is required)
    try:
        pipeline_data = PipelineData.load_by_id(pipeline_id, temp_dir)
        logger.info(f"loaded pipeline data for id: {pipeline_id}")
    except FileNotFoundError:
        logger.error(f"pipeline data not found for id: {pipeline_id}")
        logger.error("run stages 1-3 first to create pipeline data")
        sys.exit(1)
    
    pipeline_data.update_stage("video_generation", "in_progress")
    
    if not pipeline_data.full_audio_path:
        logger.error("full audio path not found in pipeline data")
        logger.error("run stage3_script.py first")
        pipeline_data.update_stage(PipelineStage.VIDEO_GENERATION, PipelineStatus.FAILED)
        return pipeline_data
    
    try:
        script_data = pipeline_data.script_data
        logger.info(f"using script data for {len(script_data.segments)} segments in total")
        
        # determine output path (use pipeline id for filename)
        if not output_path:
            output_dir = config.get('output.directory', 'output')
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            output_path = os.path.join(output_dir, f"video_{pipeline_data.id}.mp4")
        
        # store output path in pipeline data
        pipeline_data.output_path = output_path
        
        logger.info(f"generating video...")
        logger.info(f"output: {output_path}")
        
        # generate video
        video_gen = VideoGenerator(config)
        video_path = video_gen.generate_video(script_data, output_path)
        
        if os.path.exists(video_path):
            pipeline_data.video_path = video_path
            pipeline_data.output_path = output_path  # ensure it's stored
            pipeline_data.update_stage(PipelineStage.VIDEO_GENERATION, PipelineStatus.COMPLETED)
            logger.info(f"video generated successfully: {video_path}")
        else:
            logger.error("video file was not created")
            pipeline_data.update_stage(PipelineStage.VIDEO_GENERATION, PipelineStatus.FAILED)
            return pipeline_data
        
        # save pipeline data to folder and pickle file
        pipeline_data.save_to_folder(temp_dir)
        pipeline_data.save_to_pickle(os.path.join(temp_dir, f"pipeline_{pipeline_data.id}.pkl"))
        
        logger.info(f"video generation complete. pipeline id: {pipeline_data.id}")
        return pipeline_data
        
    except Exception as e:
        logger.error(f"error during video generation: {str(e)}", exc_info=True)
        pipeline_data.update_stage(PipelineStage.VIDEO_GENERATION, PipelineStatus.FAILED)
        return pipeline_data


def main():
    parser = argparse.ArgumentParser(description='stage 4: generate video from script and audio')
    parser.add_argument('--pipeline-id', type=str, required=True,
                        help='uuid of pipeline data (from stage 3)')
    parser.add_argument('--output', type=str, default=None,
                        help='custom output path for video')
    args = parser.parse_args()
    
    pipeline_data = generate_video(
        args.pipeline_id,
        output_path=args.output
    )
    
    if pipeline_data.status == "completed" and pipeline_data.video_path:
        logger.info(f"video generated successfully: {pipeline_data.video_path}")
        logger.info(f"pipeline id: {pipeline_data.id}")
        sys.exit(0)
    else:
        logger.error(f"video generation failed. pipeline id: {pipeline_data.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()

