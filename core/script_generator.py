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
from core.pipeline_data import VideoOutline, ScriptData
from core.pipeline_data import VideoSegment
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
            from utils.config_loader import get_config
            config = get_config()
            prompts_dir = config.get_prompts_directory()
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def generate_script(self, video_outline: VideoOutline) -> ScriptData:
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
        
        script_data = ScriptData(
            title=video_outline.title,
            total_segments=len(video_outline.segments),
            segments=video_outline.segments,
            full_script=self._compile_full_script(video_outline.segments)
        )
        logger.info("script generation complete")
        return script_data
    
    def _generate_segment_script(self, segment: VideoSegment, segment_num: int, 
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
    
    def _create_script_prompt(self, segment: VideoSegment, segment_num: int, 
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
        
        key_points_text = "\n".join([f"- {point}" for point in segment.get('key_points', [])])
        
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
    
    def _create_fallback_script(self, segment: VideoSegment) -> str:
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
    
    def _add_transitions(self, segments: List[VideoSegment]) -> List[VideoSegment]:
        """
        add smooth transitions between segments.
        args:
            segments: list of video segments
        returns:
            updated segments with transitions
        """
        for i in range(len(segments) - 1):
            current: VideoSegment = segments[i]
            next_seg: VideoSegment = segments[i + 1]
            
            # add transition hint (can be used in video generation)
            current.transition_to = next_seg.title
            current.transition_type = 'fade'  # default transition
        
        return segments
    
    def _compile_full_script(self, segments: List[VideoSegment]) -> str:
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
    
    def save_script(self, script_data: ScriptData, output_path: str):
        """
        save script data to JSON file.
        args:
            script_data: script data
            output_path: path to save JSON
        """
        with open(output_path, 'w') as f:
            json.dump(script_data, f, indent=2)
        
        logger.info(f"saved script to {output_path}")
    
    def export_script_text(self, script_data: ScriptData, output_path: str):
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

