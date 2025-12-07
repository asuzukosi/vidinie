"""
script generation and voiceover operation
generate narration scripts   and voiceovers from video outline.
requires pipeline_id to load cached pipeline data.
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
# add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logging, get_logger
from utils.config_loader import get_config
from core.script_generator import ScriptGenerator
from core.voiceover_generator import VoiceoverGenerator
from core.pipeline_data import PipelineData

setup_logging(log_dir='temp')
logger = get_logger('stage3_script')


def generate_scripts_and_voiceovers(pipeline_id: str,
                                    provider: Optional[str] = None) -> PipelineData:
    """
    generate scripts and voiceovers from video outline.
    requires pipeline_id to load cached pipeline data.
    args:
        pipeline_id: uuid of existing pipeline data
        provider: voiceover provider (elevenlabs or gtts)
    returns:
        pipelinedata instance with scripts and audio
    """
    logger.info("stage 3: script generation and voiceover started")
    
    config = get_config()
    temp_dir = config.get('output.temp_directory', 'temp')
    # load pipeline data by ID (cache is required)
    try:
        pipeline_data = PipelineData.load_by_id(pipeline_id, temp_dir)
        logger.info(f"loaded pipeline data: {pipeline_data.id}")
    except FileNotFoundError:
        logger.error(f"pipeline data not found for ID: {pipeline_id}")
        logger.error("run stage1_parsing.py and stage2_content.py first")
        sys.exit(1)
    
    pipeline_data.update_stage("script_generation", "in_progress")
    
    if not pipeline_data.video_outline:
        logger.error("video outline not found in pipeline data")
        logger.error("run stage2_content.py first")
        pipeline_data.update_stage("script_generation", "failed")
        return pipeline_data
    
    try:
        outline = pipeline_data.video_outline
        logger.info(f"using outline with {len(outline['segments'])} segments")
        
        # generate scripts
        logger.info("generating scripts")
        script_gen = ScriptGenerator(api_key=config.openai_api_key, prompts_dir=config.get_prompts_directory())
        script_data = script_gen.generate_script(outline)
        pipeline_data.script_data = script_data
        logger.info(f"generated scripts for {len(script_data['segments'])} segments")
        
        # generate voiceovers
        voiceover_provider = provider or config.get('voiceover.provider', 'elevenlabs')
        logger.info(f"using voiceover provider: {voiceover_provider}")
        
        audio_dir = os.path.join(temp_dir, pipeline_data.id, 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        voiceover_gen = VoiceoverGenerator(
            provider=voiceover_provider,
            api_key=config.elevenlabs_api_key,
            voice_id=config.get('voiceover.voice_id'),
            output_dir=audio_dir
        )
        
        script_with_audio = voiceover_gen.generate_voiceovers(script_data)
        pipeline_data.script_with_audio = script_with_audio
        logger.info(f"generated voiceovers for {len(script_with_audio['segments'])} segments")
        
        # generate combined audio
        combined_audio_path = os.path.join(audio_dir, 'full_voiceover.mp3')
        total_duration = voiceover_gen.generate_full_audio(script_with_audio, combined_audio_path)
        logger.info(f"combined audio generated: {combined_audio_path} ({total_duration:.1f}s)")
        
        # save pipeline data
        pipeline_data.update_stage("script_generation", "completed")
        pipeline_data.save_to_folder(temp_dir)
        pipeline_data.save_to_pickle(os.path.join(temp_dir, f"pipeline_{pipeline_data.id}.pkl"))
        
        logger.info(f"scripts and voiceovers generated. pipeline ID: {pipeline_data.id}")
        return pipeline_data
        
    except Exception as e:
        logger.error(f"error during script generation: {str(e)}", exc_info=True)
        pipeline_data.update_stage("script_generation", "failed")
        return pipeline_data


def main():
    parser = argparse.ArgumentParser(description='stage 3: generate scripts and voiceovers')
    parser.add_argument('--pipeline-id', type=str, required=True,
                        help='uuid of pipeline data (from stage 2)')
    parser.add_argument('--provider', type=str, choices=['elevenlabs', 'gtts'], default=None,
                        help='voiceover provider: elevenlabs or gtts')
    args = parser.parse_args()
    
    pipeline_data = generate_scripts_and_voiceovers(
        args.pipeline_id,
        provider=args.provider
    )
    
    if pipeline_data.status == "completed":
        logger.info(f"scripts and voiceovers generated successfully. pipeline id: {pipeline_data.id}")
        sys.exit(0)
    else:
        logger.error(f"script generation failed. pipeline id: {pipeline_data.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()

