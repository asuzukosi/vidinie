"""
script generation operations for the api.
generates narration scripts and voiceovers from video outline.
"""
import os
from typing import Optional
from core.utils.logger import get_logger
from core.utils.config_loader import config
from core.data import (
    VideoPipeline,
    VideoPipelineScript,
    VideoPipelineStage,
    VideoPipelineStatus,
)
from core.operations.script_generator import ScriptGenerator
from core.operations.voiceover_generator import VoiceoverGenerator

logger = get_logger("script_operations")


def generate_scripts(
    pipeline: VideoPipeline,
    provider: Optional[str] = None,
    voice_id: Optional[str] = None
) -> VideoPipeline:
    """
    generate narration scripts and voiceovers from video outline.
    args:
        pipeline: video pipeline object with video outline
        provider: voiceover provider ('elevenlabs' or 'gtts') (optional, uses config if not provided)
        voice_id: elevenlabs voice id (optional, uses config if not provided)
    returns:
        updated video pipeline with script data, full audio path, and full audio duration
    """
    voice_id = voice_id or config.get('voiceover.voice_id')
    provider = provider or config.get('voiceover.provider', 'elevenlabs')
    temp_dir = config.get('output.temp_directory', 'temp')
    
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
        script_gen = ScriptGenerator()
        script_data: VideoPipelineScript = script_gen.generate_script(outline)
        pipeline.script_data = script_data
        logger.info(f"Generated scripts for {len(script_data.segments)} segments")
        
        # Generate voiceovers
        logger.info(f"Using voiceover provider: {provider}")
        audio_dir = os.path.join(temp_dir, pipeline.id, 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        voiceover_gen = VoiceoverGenerator(
            provider=provider,
            voice_id=voice_id,
            output_dir=audio_dir
        )
        
        script_data_with_audio: VideoPipelineScript = voiceover_gen.generate_voiceovers(script_data)
        pipeline.script_data = script_data_with_audio
        logger.info(f"Generated voiceovers for {len(script_data_with_audio.segments)} segments")
        
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
