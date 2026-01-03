"""
script generation and voiceover operation
generate narration scripts   and voiceovers from video outline.
requires pipeline_id to load cached video pipeline.
workflow sequence:
    this is the third operation in the standard workflow:
    1. document_processing  - parse pdf and extract content (stage1)
    2. content_analysis     - analyze content and create video outline (stage2)
    3. script_generation    - generate narration scripts and voiceovers (THIS MODULE - stage3)
    4. video_generation     - compose final video from all assets (stage4)
    
    note: the workflow can be customized based on document type and requirements.
"""
import sys
import os
import argparse
from typing import Optional
from utils.logger import setup_logging, get_logger
from utils.config_loader import get_config
from core.data import VideoPipeline
from core.operations.script_generator import generate_scripts

setup_logging(log_dir='temp')
logger = get_logger('stage3_script')


def generate_scripts_and_voiceovers(pipeline_id: str,
                                    provider: Optional[str] = None) -> VideoPipeline:
    """
    generate scripts and voiceovers from video outline.
    requires pipeline_id to load cached video pipeline.
    args:
        pipeline_id: uuid of existing video pipeline
        provider: voiceover provider (elevenlabs or gtts)
    returns:
        video pipeline instance with scripts and audio
    """
    logger.info("stage 3: script generation and voiceover started")
    
    config = get_config()
    temp_dir = config.get('output.temp_directory', 'temp')
    # load video pipeline by ID (cache is required)
    try:
        video_pipeline = VideoPipeline.load_by_id(pipeline_id, temp_dir)
        logger.info(f"loaded video pipeline: {video_pipeline.id}")
    except FileNotFoundError:
        logger.error(f"video pipeline not found for ID: {pipeline_id}")
        logger.error("run stage1_parsing.py and stage2_content.py first")
        sys.exit(1)
    
    # use modular operation to generate scripts
    config = get_config()
    video_pipeline = generate_scripts(
        video_pipeline,
        provider=provider,
        openai_api_key=config.openai_api_key,
        elevenlabs_api_key=config.elevenlabs_api_key,
        voice_id=config.get('voiceover.voice_id'),
        prompts_dir=config.get_prompts_directory()
    )
    
    # save video pipeline
    if video_pipeline.status.value == "completed":
        temp_dir = config.get('output.temp_directory', 'temp')
        video_pipeline.save_to_folder(temp_dir)
        video_pipeline.save_to_pickle(os.path.join(temp_dir, f"pipeline_{video_pipeline.id}.pkl"))
    
    return video_pipeline


def main():
    parser = argparse.ArgumentParser(description='stage 3: generate scripts and voiceovers')
    parser.add_argument('--pipeline-id', type=str, required=True,
                        help='uuid of pipeline data (from stage 2)')
    parser.add_argument('--provider', type=str, choices=['elevenlabs', 'gtts'], default=None,
                        help='voiceover provider: elevenlabs or gtts')
    args = parser.parse_args()
    
    video_pipeline = generate_scripts_and_voiceovers(
        args.pipeline_id,
        provider=args.provider
    )
    
    if video_pipeline.status == "completed":
        logger.info(f"scripts and voiceovers generated successfully. pipeline id: {video_pipeline.id}")
        sys.exit(0)
    else:
        logger.error(f"script generation failed. pipeline id: {video_pipeline.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()

