"""
script generation operations for the api.
generates narration scripts and voiceovers from video outline.
"""
import os
from core.utils.logger import get_logger
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

logger = get_logger("script_operations")


def generate_scripts(
    pipeline: VideoPipeline
) -> VideoPipeline:
    """
    generate narration scripts and voiceovers from video outline.
    args:
        pipeline: video pipeline object with video outline
    returns:
        updated video pipeline with script data, full audio path, and full audio duration
    """
    temp_dir = config.output_temp_directory
    
    pipeline.update_stage(VideoPipelineStage.SCRIPT_GENERATION, VideoPipelineStatus.IN_PROGRESS)
    
    if not pipeline.video_outline:
        logger.error("Video outline not found in pipeline data")
        pipeline.update_stage(VideoPipelineStage.SCRIPT_GENERATION, VideoPipelineStatus.FAILED)
        return pipeline
    
    try:
        outline = pipeline.video_outline
        logger.info(f"Using outline with {len(outline.segments)} segments")
        
        # Generate scripts
        logger.info("Generating scripts")
        script_gen = ScriptGenerator(user_instructions=pipeline.instructions)
        script_data: VideoOutline = script_gen.generate_script(outline)
        pipeline.script_data = script_data
        logger.info(f"Generated scripts for {len(script_data.segments)} segments")
        
        # Generate voiceovers
        audio_dir = os.path.join(temp_dir, pipeline.id, 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        voiceover_gen = VoiceoverGenerator(
            voice=pipeline.voice,
            output_dir=audio_dir
        )
        
        script_data_with_audio: VideoOutline = voiceover_gen.generate_voiceovers(script_data)
        pipeline.script_data = script_data_with_audio
        logger.info(f"Generated voiceovers for {len(script_data_with_audio.segments)} segments")
        
        # senerate background music if query is provided
        music_dir = os.path.join(temp_dir, pipeline.id, 'music')
        os.makedirs(music_dir, exist_ok=True)
        
        music_gen = MusicGenerator(output_dir=music_dir)
        script_data_with_music: VideoOutline = music_gen.generate_background_music(script_data_with_audio)
        pipeline.script_data = script_data_with_music
        if script_data_with_music.background_music_path:
            logger.info(f"generated background music: {script_data_with_music.background_music_path}")
        
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
