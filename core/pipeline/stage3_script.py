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
from utils.logger import setup_logging, get_logger
from core.utils.config_loader import config
from core.data import (
    VideoPipeline,
    VideoOutline,
    VideoPipelineStage,
    VideoPipelineStatus,
)
from core.operations.script_generator import ScriptGenerator
from core.operations.voiceover_generator import VoiceoverGenerator
from core.operations.music_generator import MusicGenerator
from core.clients.audio_engine import AudioVoiceString

setup_logging(log_dir='temp')
logger = get_logger('stage3_script')


def generate_scripts_impl(
    pipeline: VideoPipeline
) -> VideoPipeline:
    """
    generate narration scripts and voiceovers from video outline.
    Explicit implementation using ScriptGenerator and VoiceoverGenerator classes directly.
    """
    # Use pipeline voice (required)
    if not pipeline.voice:
        raise ValueError("Voice is required but not found in pipeline")
    try:
        voice = AudioVoiceString(pipeline.voice)
    except (ValueError, ImportError):
        raise ValueError(f"Invalid voice value in pipeline: {pipeline.voice}")
    temp_dir = config.output_temp_directory
    
    pipeline.update_stage(VideoPipelineStage.SCRIPT_GENERATION, VideoPipelineStatus.IN_PROGRESS)
    
    if not pipeline.video_outline:
        logger.error("Video outline not found in pipeline data")
        pipeline.update_stage(VideoPipelineStage.SCRIPT_GENERATION, VideoPipelineStatus.FAILED)
        return pipeline
    
    try:
        outline = pipeline.video_outline
        logger.info(f"Using outline with {len(outline.segments)} segments")
        
        # Generate scripts using ScriptGenerator class
        logger.info("Generating scripts")
        script_gen = ScriptGenerator(user_instructions=pipeline.instructions)
        script_data: VideoOutline = script_gen.generate_script(outline)
        pipeline.script_data = script_data
        logger.info(f"Generated scripts for {len(script_data.segments)} segments")
        
        # Generate voiceovers using VoiceoverGenerator class
        audio_dir = os.path.join(temp_dir, pipeline.id, 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        voiceover_gen = VoiceoverGenerator(
            voice=voice,
            output_dir=audio_dir
        )
        
        script_data_with_audio: VideoOutline = voiceover_gen.generate_voiceovers(script_data)
        pipeline.script_data = script_data_with_audio
        logger.info(f"Generated voiceovers for {len(script_data_with_audio.segments)} segments")
        
        # Generate background music if query is provided
        music_dir = os.path.join(temp_dir, pipeline.id, 'music')
        os.makedirs(music_dir, exist_ok=True)
        
        music_gen = MusicGenerator(output_dir=music_dir)
        script_data_with_music: VideoOutline = music_gen.generate_background_music(script_data_with_audio)
        pipeline.script_data = script_data_with_music
        if script_data_with_music.background_music_path:
            logger.info(f"Generated background music: {script_data_with_music.background_music_path}")
        
        # Generate combined audio
        combined_audio_path = os.path.join(audio_dir, 'full_voiceover.mp3')
        total_duration = voiceover_gen.generate_full_audio(script_data_with_audio, combined_audio_path)
        pipeline.full_audio_path = combined_audio_path
        pipeline.full_audio_duration = total_duration
        logger.info(f"Combined audio generated: {combined_audio_path} ({total_duration:.1f}s)")
        
        # Update pipeline data
        pipeline.update_stage(VideoPipelineStage.SCRIPT_GENERATION, VideoPipelineStatus.COMPLETED)
        
        logger.info(f"Scripts and voiceovers generated. Pipeline ID: {pipeline.id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"Error during script generation: {str(e)}", exc_info=True)
        pipeline.update_stage(VideoPipelineStage.SCRIPT_GENERATION, VideoPipelineStatus.FAILED)
        return pipeline


def generate_scripts_and_voiceovers(pipeline_id: str) -> VideoPipeline:
    """
    generate scripts and voiceovers from video outline.
    requires pipeline_id to load cached video pipeline.
    args:
        pipeline_id: uuid of existing video pipeline
    returns:
        video pipeline instance with scripts and audio
    """
    logger.info("stage 3: script generation and voiceover started")
    
    temp_dir = config.output_temp_directory
    # load video pipeline by ID (cache is required)
    try:
        video_pipeline = VideoPipeline.load_by_id(pipeline_id, temp_dir)
        logger.info(f"loaded video pipeline: {video_pipeline.id}")
    except FileNotFoundError:
        logger.error(f"video pipeline not found for ID: {pipeline_id}")
        logger.error("run stage1_parsing.py and stage2_content.py first")
        sys.exit(1)
    
    # use explicit implementation to generate scripts
    video_pipeline = generate_scripts_impl(video_pipeline)
    
    # save video pipeline
    if video_pipeline.status.value == "completed":
        temp_dir = config.output_temp_directory
        video_pipeline.save_to_folder(temp_dir)
        video_pipeline.save_to_pickle(os.path.join(temp_dir, f"pipeline_{video_pipeline.id}.pkl"))
    
    return video_pipeline


def main():
    parser = argparse.ArgumentParser(description='stage 3: generate scripts and voiceovers')
    parser.add_argument('--pipeline-id', type=str, required=True,
                        help='uuid of pipeline data (from stage 2)')
    args = parser.parse_args()
    
    video_pipeline = generate_scripts_and_voiceovers(args.pipeline_id)
    
    if video_pipeline.status == "completed":
        logger.info(f"scripts and voiceovers generated successfully. pipeline id: {video_pipeline.id}")
        sys.exit(0)
    else:
        logger.error(f"script generation failed. pipeline id: {video_pipeline.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
