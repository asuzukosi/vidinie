"""
vidinie content analyzer module
analyzes pdf content and creates structured video segments.
"""
import re
from typing import List, Optional
from pydantic import BaseModel
from core.clients.reasoning_engine import reason, ReasoningPrompt
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.utils.logger import get_logger
from core.utils.config_loader import config
from core.data import (
    VideoOutline,
    ImageMetadata,
    VideoSegment,
)
from core.data.image_models import SegmentImage, SegmentVideoClip

logger = get_logger("content_analyzer")


def clean_text_fn(text):
    # remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    # remove page numbers
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)
    return text.strip()

class GenerateSummary(BaseModel):
    """
    generated summary of a text chunk.
    """
    summary: str

class ContentAnalyzerOutlineSegment(BaseModel):
    title: str
    purpose: str
    key_points: List[str]
    content: str
    narrative_hook: str
    transition_from_previous: str
    transition_to_next: str
    visual_keywords: List[str]
    duration: int
    images: List[SegmentImage]
    video_clips: List[SegmentVideoClip]

class ContentAnalyzerOutline(BaseModel):
    title: str
    total_segments: int
    estimated_duration: int
    narrative_arc: str
    background_music_query: Optional[str] = None
    segments: List[ContentAnalyzerOutlineSegment]


class ContentAnalyzer:
    """
    analyze and structure content for video creation.
    """
    def __init__(self, 
                 target_segments: int = 5, 
                 segment_duration: int = 40,
                 user_instructions: str = ""):
        """
        initialize content analyzer.
        """
        # set target segments and segment duration
        self.target_segments = target_segments
        self.segment_duration = segment_duration
        self.user_instructions = user_instructions
        

    def _split_context(self, context: str, split_by: str = '\n', chunk_length: int = 360000) -> List[str]:
        """
        split the context into smaller chunks.
        """
        all_segments: List[str] = context.split(split_by)
        chunks: List[str] = []
        current_chunk: str = ""
        for segment in all_segments:
            if len(current_chunk) + len(segment) > chunk_length:
                chunks.append(current_chunk)
                current_chunk = ""
            current_chunk += segment + split_by
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def _clean_text(self, text: str) -> str:
        """
        clean the text of llm processing
        """
        return clean_text_fn(text)

    async def iterative_summarization(self, 
                                title: str,
                                context: str, 
                                split_by: str = '\n', 
                                chunk_length: int = 360000, 
                                max_size: int = 480000 ) -> str:
        """
        iteratively summarize the context.
        """
        # load system prompt from template
        jinja_env = Environment(
            loader=FileSystemLoader(str(config.prompts_directory)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        # render system prompt
        system_template = jinja_env.get_template('bullet_summary_system.j2')
        system_prompt = system_template.render(
            document_title=title,
            user_instructions=self.user_instructions if self.user_instructions else None
        )

        # combine summaries function
        def combine_summaries(summaries: List[GenerateSummary]) -> str:
            """
            combine the summaries into a single string.
            """
            return "\n".join([summary.summary for summary in summaries])
        
        # iteratively summarize the context
        logger.info(f"iteratively summarizing context of length {len(context)}")
        context = self._clean_text(context)
        while len(context) > max_size:
            chunks: List[str] = self._split_context(context, split_by, chunk_length)
            prompts: List[str] = [jinja_env.get_template('bullet_summary_prompt.j2').render(context=chunk) for chunk in chunks]
            reasoning_prompts: List[ReasoningPrompt] = [ReasoningPrompt(task=prompt, images=[]) for prompt in prompts]
            context: str = await reason(system_prompt, reasoning_prompts, schema=GenerateSummary, combine_function=combine_summaries)
        logger.info(f"successfully summarized context of length {len(context)}")
        return context

    
    async def analyze_content(self, title: str, 
                        content: str, 
                        images_metadata: List[ImageMetadata]) -> VideoOutline:
        """
        analyze content and create video segments.
        """
        logger.info("starting content analysis")
        # iteratively summarize the content
        content = await self.iterative_summarization(title, content, split_by='\n', 
                                               chunk_length=360000, max_size=480000)
        logger.info(f"successfully iteratively summarized content")
        # create video outline
        outline = await self._create_video_outline(title=title, content=content, images_metadata=images_metadata)
        logger.info(f"successfully created video outline")
        return outline
    
    def _extract_images_prompt(self, images_metadata: List[ImageMetadata]) -> str:
        """
        extract the prompt for video outline generation in xml tag format.
        """
        if not images_metadata:
            return ""
        images_list = []
        for img in images_metadata:
            label = str(img.label) if img.label is not None else ""
            description = img.description or ""
            image_type = img.image_type or ""
            key_elements = img.key_elements or []
            key_elements_str = ", ".join(key_elements)
            filepath = img.filepath or ""
            relevance = img.relevance or ""
            # Render as XML tag per image
            img_xml = (
                f"<image>"
                f"  <label>{label}</label>"
                f"  <description>{description}</description>"
                f"  <type>{image_type}</type>"
                f"  <key_elements>{key_elements_str}</key_elements>"
                f"  <filepath>{filepath}</filepath>"
                f"  <relevance>{relevance}</relevance>"
                f"</image>"
            )
            images_list.append(img_xml)
        images_text = "<images>\n" + "\n".join(images_list) + "\n</images>"
        return images_text

    async def _create_video_outline(self, title: str, 
                              content: str, 
                              images_metadata: List[ImageMetadata]) -> VideoOutline:
        """
        create structured video outline from content and metadata.
        """
        logger.info("creating video outline with ai model")
        # get the prompt for video outline generation
        images_text = self._extract_images_prompt(images_metadata)
        jinja_env = Environment(
            loader=FileSystemLoader(str(config.prompts_directory)),
            autoescape=select_autoescape(['html', 'xml'])
        )

        system_prompt = jinja_env.get_template('outline_system.j2').render(
            user_instructions=self.user_instructions if self.user_instructions else None
        )
        template = jinja_env.get_template('outline_instruction.j2')
        prompt = template.render(
            title=title,
            target_segments=self.target_segments,
            duration=self.segment_duration,
            content=content,
            images_text=images_text,
            has_images=len(images_metadata) > 0
        )
        reasoning_prompt = ReasoningPrompt(task=prompt, images=[])
        outline: List[ContentAnalyzerOutline] = await reason(system_prompt, [reasoning_prompt], schema=ContentAnalyzerOutline)
        outline: ContentAnalyzerOutline = outline[0]
        # convert content analyzer outline to video outline
        segments: List[ContentAnalyzerOutlineSegment] = []
        for segment in outline.segments:
            segments.append(VideoSegment(
                title=segment.title,
                purpose=segment.purpose,
                key_points=segment.key_points,
                content=segment.content,
                narrative_hook=segment.narrative_hook,
                transition_from_previous=segment.transition_from_previous,
                transition_to_next=segment.transition_to_next,
                visual_keywords=segment.visual_keywords,
                duration=segment.duration,
                images=segment.images,
                video_clips=segment.video_clips,
            ))
        video_outline = VideoOutline(
            title=outline.title,
            total_segments=outline.total_segments,
            estimated_duration=outline.estimated_duration,
            narrative_arc=outline.narrative_arc,
            background_music_query=outline.background_music_query,
            segments=segments,
        )
        return video_outline
