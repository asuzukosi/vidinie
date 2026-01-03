"""
vidinie script generator module

generates natural narration scripts from video outline segments.
uses openai to convert structured content into engaging voiceover scripts.
"""

import os
import json
from typing import List, Optional
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from utils.logger import get_logger
from utils.config_loader import get_config
from core.data import (
    VideoPipelineOutline,
    VideoPipelineScript,
    VideoPipelineSegment,
    VideoPipelineStage,
    VideoPipelineStatus,
)
from core.operations.voiceover_generator import VoiceoverGenerator
from core.data import VideoPipeline
logger = get_logger("script_generator")


class ScriptGenerator:
    """generate voiceover scripts from video segments."""
    
    def __init__(self, api_key: Optional[str] = None, prompts_dir: Optional[Path] = None):
        """
        initialize script generator.
        args:
            api_key: openai api key
            prompts_dir: path to prompts directory (from config)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("openai api key is required")
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"
        
        # initialize jinja2 environment for prompt templates
        if prompts_dir is None:
            config = get_config()
            prompts_dir = config.get_prompts_directory()
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def generate_script(self, video_outline: VideoPipelineOutline) -> VideoPipelineScript:
        """
        generate complete voiceover script from video outline.
        args:
            video_outline: video outline with segments
        returns:
            dictionary with generated scripts for each segment
        """
        logger.info(f"generating script for {len(video_outline.segments)} segments")
        for i, segment in enumerate(video_outline.segments, 1):
            logger.info(f"generating script for segment {i}: {segment.title}")
            
            script_text = self._generate_segment_script(
                segment,
                i,
                len(video_outline.segments),
                video_outline.title
            )
            # add script to segment
            segment.script = script_text
            segment.word_count = len(script_text.split())
            
        
        # generate transitions
        video_outline.segments = self._add_transitions(video_outline.segments)
        
        script_data = VideoPipelineScript(
            title=video_outline.title,
            total_segments=len(video_outline.segments),
            segments=video_outline.segments,
            full_script=self._compile_full_script(video_outline.segments)
        )
        logger.info("script generation complete")
        return script_data
    
    def _generate_segment_script(self, segment: VideoPipelineSegment, segment_num: int, 
                                 total_segments: int, video_title: str) -> str:
        """
        generate script for a single segment.
        args:
            segment: video segment
            segment_num: segment number
            total_segments: total number of segments
            video_title: overall video title
        returns:
            generated script text
        """
        prompt = self._create_script_prompt(segment, segment_num, total_segments, video_title)
        try:
            # load system prompt from template
            system_template = self.jinja_env.get_template('script_system.j2')
            system_prompt = system_template.render()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            script = response.choices[0].message.content.strip()
            
            # clean up the script
            script = self._clean_script(script)
            
            logger.info(f"generated {len(script.split())} words for segment {segment_num}")
            return script
            
        except Exception as e:
            logger.error(f"error generating script for segment {segment_num}: {str(e)}")
            # fallback to basic script
            return self._create_fallback_script(segment)
    
    def _create_script_prompt(self, segment: VideoPipelineSegment, segment_num: int, 
                             total_segments: int, video_title: str) -> str:
        """
        create prompt for script generation.
        args:
            segment: video segment
            segment_num: segment number
            total_segments: total number of segments
            video_title: overall video title
        returns:
            prompt for script generation
        """
        is_intro = segment_num == 1
        is_conclusion = segment_num == total_segments
        
        key_points_text = "\n".join([f"- {point}" for point in segment.key_points])
        
        # load and render template
        template = self.jinja_env.get_template('script_instruction.j2')
        prompt = template.render(
            segment=segment.model_dump(mode="json"),
            segment_num=segment_num,
            total_segments=total_segments,
            video_title=video_title,
            key_points_text=key_points_text,
            is_intro=is_intro,
            is_conclusion=is_conclusion
        )
        
        return prompt
    
    def _clean_script(self, script: str) -> str:
        """
        clean up generated script text to remove any stage directions or formatting markers used by the model.
        args:
            script: raw script text
        returns:
            cleaned script text
        """
        # remove any stage directions or formatting markers
        script = script.replace('[', '').replace(']', '')
        script = script.replace('**', '')
        
        # remove labels like "SCRIPT:" or "Narrator:"
        lines = []
        for line in script.split('\n'):
            line = line.strip()
            if line and not line.endswith(':') or len(line) > 20:
                # remove common prefixes
                for prefix in ['SCRIPT:', 'Narrator:', 'Voice:', 'VO:', 'VOICEOVER:', 'NARRATOR:', 'VOICE:', 'SCENE:', 'SEGMENT:']:
                    if line.startswith(prefix):
                        line = line[len(prefix):].strip()
                lines.append(line)
        
        return ' '.join(lines)
    
    def _create_fallback_script(self, segment: VideoPipelineSegment) -> str:
        """
        create a basic script as fallback.
        args:
            segment: video segment
        returns:
            basic script text
        """
        title = segment.title
        purpose = segment.purpose
        key_points = segment.key_points
        
        script_parts = [f"Let's talk about {title}."]
        
        if purpose:
            script_parts.append(purpose)
        
        for point in key_points[:3]:
            script_parts.append(point)
        
        return ' '.join(script_parts)
    
    def _add_transitions(self, segments: List[VideoPipelineSegment]) -> List[VideoPipelineSegment]:
        """
        add smooth transitions between segments.
        args:
            segments: list of video segments
        returns:
            updated segments with transitions
        """
        for i in range(len(segments) - 1):
            current: VideoPipelineSegment = segments[i]
            next_seg: VideoPipelineSegment = segments[i + 1]
            
            # add transition hint (can be used in video generation)
            current.transition_to = next_seg.title
            current.transition_type = 'fade'  # default transition
        
        return segments
    
    def _compile_full_script(self, segments: List[VideoPipelineSegment]) -> str:
        """
        compile full script from all segments.
        args:
            segments: list of video segments
        returns:
            full script text
        """
        full_script_parts = []
        
        for i, segment in enumerate(segments, 1):
            full_script_parts.append(f"[SEGMENT {i}: {segment.title}]")
            full_script_parts.append(segment.script)
            full_script_parts.append("")  # empty line between segments
        
        return '\n'.join(full_script_parts)
    
    def save_script(self, script_data: VideoPipelineScript, output_path: str):
        """
        save script data to JSON file.
        args:
            script_data: script data
            output_path: path to save JSON
        """
        with open(output_path, 'w') as f:
            json.dump(script_data, f, indent=2)
        
        logger.info(f"saved script to {output_path}")
    
    def export_script_text(self, script_data: VideoPipelineScript, output_path: str):
        """
        export script as plain text file.
        args:
            script_data: script data
            output_path: path to save text file
        """
        with open(output_path, 'w') as f:
            f.write(f"SCRIPT: {script_data.title}\n")
            f.write("=" * 80 + "\n\n")
            f.write(script_data.full_script)
        
        logger.info(f"exported script text to {output_path}")


def update_scripts_in_pipeline(
    video_pipeline,
    script_data: VideoPipelineScript
) -> VideoPipelineScript:
    """
    Update scripts in a video pipeline.
    
    Args:
        video_pipeline: VideoPipeline object
        script_data: Updated script data
    
    Returns:
        Updated VideoPipelineScript object
    """
    video_pipeline.script_data = script_data
    return script_data


def generate_scripts(
    pipeline: VideoPipeline,
    provider: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    elevenlabs_api_key: Optional[str] = None,
    voice_id: Optional[str] = None,
    prompts_dir: Optional[str] = None
) -> VideoPipeline:
    """
    generate narration scripts and voiceovers from video outline.
    args:
        pipeline: video pipeline object with video outline
        provider: voiceover provider ('elevenlabs' or 'gtts')
        openai_api key: openai api key
        elevenlabs_api_key: elevenlabs api key
        voice_id: elevenlabs voice id
        prompts_dir: path to prompts directory
    returns:
        updated video pipeline with script data, full audio path, and full audio duration
    """
    config = get_config()
    openai_api_key = openai_api_key or config.openai_api_key
    elevenlabs_api_key = elevenlabs_api_key or config.elevenlabs_api_key
    voice_id = voice_id or config.get('voiceover.voice_id')
    provider = provider or config.get('voiceover.provider', 'elevenlabs')
    prompts_dir = prompts_dir or config.get_prompts_directory()
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
        script_gen = ScriptGenerator(api_key=openai_api_key, prompts_dir=prompts_dir)
        script_data: VideoPipelineScript = script_gen.generate_script(outline)
        pipeline.script_data = script_data
        logger.info(f"Generated scripts for {len(script_data.segments)} segments")
        
        # Generate voiceovers
        logger.info(f"Using voiceover provider: {provider}")
        audio_dir = os.path.join(temp_dir, pipeline.path_id or pipeline.id, 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        voiceover_gen = VoiceoverGenerator(
            provider=provider,
            api_key=elevenlabs_api_key,
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

