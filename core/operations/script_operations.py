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
)
from core.operators.script_generator import ScriptGenerator
from core.operators.voiceover_generator import VoiceoverGenerator
from core.operators.music_generator import MusicGenerator

logger = get_logger("script_operations")


async def generate_scripts(
    pipeline: VideoPipeline
) -> VideoPipeline:
    """
    generate narration scripts and voiceovers from video outline.
    args:
        pipeline: video pipeline object with video outline
    returns:
        updated video pipeline with script data, full audio path, and full audio duration
    """
    output_dir = str(config.output_directory)
    
    if not pipeline.video_outline:
        logger.error("Video outline not found in pipeline data")
        raise ValueError("Video outline not found in pipeline data")
    
    try:
        outline = pipeline.video_outline
        logger.info(f"Using outline with {len(outline.segments)} segments")
        
        # Generate scripts
        logger.info("Generating scripts")
        script_gen = ScriptGenerator(user_instructions=pipeline.instructions)
        video_outline: VideoOutline = await script_gen.generate_script(outline)
        pipeline.video_outline = video_outline
        logger.info(f"Generated scripts for {len(video_outline.segments)} segments")
        
        # Generate voiceovers
        audio_dir = os.path.join(output_dir, pipeline.id, config.pipeline_audio_path)
        os.makedirs(audio_dir, exist_ok=True)
        
        voiceover_gen = VoiceoverGenerator(
            voice=pipeline.voice,
            output_dir=audio_dir
        )
        
        video_outline_with_audio: VideoOutline = await voiceover_gen.generate_voiceovers(video_outline)
        pipeline.video_outline = video_outline_with_audio
        logger.info(f"Generated voiceovers for {len(video_outline.segments)} segments")
        
        # senerate background music if query is provided
        music_dir = os.path.join(output_dir, pipeline.id, config.pipeline_music_path)
        os.makedirs(music_dir, exist_ok=True)
        
        music_gen = MusicGenerator(output_dir=music_dir)
        video_outline_with_music: VideoOutline = await music_gen.generate_background_music(video_outline_with_audio)
        pipeline.video_outline = video_outline_with_music
        if video_outline_with_music.background_music_path:
            logger.info(f"generated background music: {video_outline_with_music.background_music_path}")
        
        # Generate combined audio
        combined_audio_path = os.path.join(audio_dir, 'full_voiceover.mp3')
        total_duration = await voiceover_gen.generate_full_audio(video_outline_with_music, combined_audio_path)
        pipeline.full_audio_path = combined_audio_path
        pipeline.full_audio_duration = total_duration
        logger.info(f"Combined audio generated: {combined_audio_path} ({total_duration:.1f}s)")
        
        logger.info(f"Scripts and voiceovers generated. Pipeline ID: {pipeline.id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"Error during script generation: {str(e)}", exc_info=True)
        raise
