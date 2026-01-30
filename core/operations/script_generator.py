"""
vidinie script generator module

generates natural narration scripts from video outline segments.
uses the reasoning engine to convert structured content into engaging voiceover scripts.
"""
from typing import List
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.clients.reasoning_engine import ReasoningPrompt, reason
from core.utils.logger import get_logger
from core.utils.config_loader import config
from core.data import (
    VideoOutline,
    VideoSegment,
)
from pydantic import BaseModel

logger = get_logger("script_generator")


class ScriptSegment(BaseModel):
    """script segment model."""
    segment_number: int
    script: str

class ScriptResponse(BaseModel):
    """script response model."""
    title: str
    segments: List[ScriptSegment]


class ScriptGenerator:
    """generate voiceover scripts from video segments."""
    
    def __init__(self, user_instructions: str = ""):
        """
        initialize script generator.
        """
        self.user_instructions = user_instructions
        # initialize jinja2 environment for prompt templates
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(config.get_prompts_directory())),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    async def generate_script(self, video_outline: VideoOutline) -> VideoOutline:
        """
        generate complete voiceover script from video outline.
        """
        logger.info(f"generating script for {len(video_outline.segments)} segments")
        segment_json = [segment.model_dump(mode="json") for segment in video_outline.segments]
        system_prompt = self.jinja_env.get_template('script_system.j2').render(
            user_instructions=self.user_instructions if self.user_instructions else None
        )
        
        prompt = self.jinja_env.get_template('script_instruction.j2').render(
            video_outline=video_outline.model_dump(mode="json"),
            segments=segment_json
        )
        reasoning_prompt = ReasoningPrompt(task=prompt)
        results: List[ScriptResponse] = await reason(system_prompt, [reasoning_prompt], schema=ScriptResponse)
        result: ScriptResponse = results[0]
        if result.title != video_outline.title:
            video_outline.title = result.title
        for segment in result.segments:
            video_outline.segments[segment.segment_number].script = segment.script
        video_outline.full_script = self._compile_full_script(video_outline.segments)
        return video_outline
    
    def _compile_full_script(self, segments: List[VideoSegment]) -> str:
        """
        compile full script from all segments
        """
        full_script_parts = []
        
        for i, segment in enumerate(segments, 1):
            full_script_parts.append(f"**SEGMENT {i}: {segment.title}**")
            full_script_parts.append(segment.script)
            full_script_parts.append("")  # empty line between segments
        return '\n'.join(full_script_parts)
    
