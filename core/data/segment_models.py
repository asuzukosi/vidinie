"""
segment and outline models for video pipeline.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from core.data.image_models import SegmentImage, SegmentClip


class VideoSegment(BaseModel):
    """video pipeline segment model."""
    title: str
    purpose: str
    content: str
    key_points: List[str]
    visual_keywords: List[str]
    script: Optional[str] = None
    word_count: Optional[int] = None
    duration: int
    images: Optional[List[SegmentImage]] = None  # images to show with segment
    clips: Optional[List[SegmentClip]] = None  # clips to show with segment
    transition_to: Optional[str] = None
    transition_type: Optional[str] = None
    audio_file: Optional[str] = None
    audio_duration: Optional[float] = None


class VideoOutline(BaseModel):
    """video pipeline outline model."""
    title: str
    total_segments: int
    estimated_duration: int
    segments: List[VideoSegment]
    full_script: Optional[str] = Field(default="")
    background_music_query: Optional[str] = None  # query for generating background music
    background_music_path: Optional[str] = None  # path to generated background music file


def _escape_xml(text: str) -> str:
    """
    escape xml special characters in text.
    """
    if not text:
        return ""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))


def to_xml_prompt_context(outline: VideoOutline) -> str:
    """
    convert the video outline into a structured xml format for agentic video generation.
    """
    xml_parts = ['<video_outline>']
    
    # outline metadata
    xml_parts.append('  <metadata>')
    xml_parts.append(f'    <title>{_escape_xml(outline.title)}</title>')
    xml_parts.append(f'    <total_segments>{outline.total_segments}</total_segments>')
    xml_parts.append(f'    <estimated_duration>{outline.estimated_duration}</estimated_duration>')
    xml_parts.append('  </metadata>')
    
    # full script if available
    if outline.full_script:
        xml_parts.append('  <full_script>')
        xml_parts.append(f'    {_escape_xml(outline.full_script)}')
        xml_parts.append('  </full_script>')
    
    # segments
    xml_parts.append('  <segments>')
    for idx, segment in enumerate(outline.segments, 1):
        xml_parts.append(f'    <segment index="{idx}">')
        
        # basic segment info
        xml_parts.append('      <basic_info>')
        xml_parts.append(f'        <title>{_escape_xml(segment.title)}</title>')
        xml_parts.append(f'        <purpose>{_escape_xml(segment.purpose)}</purpose>')
        xml_parts.append(f'        <content>{_escape_xml(segment.content)}</content>')
        xml_parts.append('        <key_points>')
        for point in segment.key_points:
            xml_parts.append(f'          <point>{_escape_xml(point)}</point>')
        xml_parts.append('        </key_points>')
        xml_parts.append('        <visual_keywords>')
        for keyword in segment.visual_keywords:
            xml_parts.append(f'          <keyword>{_escape_xml(keyword)}</keyword>')
        xml_parts.append('        </visual_keywords>')
        xml_parts.append('      </basic_info>')
        
        # script and timing
        xml_parts.append('      <script_info>')
        if segment.script:
            xml_parts.append(f'        <script>{_escape_xml(segment.script)}</script>')
        if segment.word_count is not None:
            xml_parts.append(f'        <word_count>{segment.word_count}</word_count>')
        xml_parts.append(f'        <duration>{segment.duration}</duration>')
        xml_parts.append('      </script_info>')
        
        # visual assets - images
        if segment.images:
            xml_parts.append('      <images>')
            for img_idx, image in enumerate(segment.images, 1):
                xml_parts.append(f'        <image index="{img_idx}">')
                xml_parts.append(f'          <source>{image.source.value}</source>')
                if image.query:
                    xml_parts.append(f'          <query>{_escape_xml(image.query)}</query>')
                if image.path:
                    xml_parts.append(f'          <path>{_escape_xml(image.path)}</path>')
                if image.timing:
                    xml_parts.append(f'          <timing>{_escape_xml(image.timing)}</timing>')
                xml_parts.append('        </image>')
            xml_parts.append('      </images>')
        
        # visual assets - clips
        if segment.clips:
            xml_parts.append('      <clips>')
            for clip_idx, clip in enumerate(segment.clips, 1):
                xml_parts.append(f'        <clip index="{clip_idx}">')
                xml_parts.append(f'          <source>{clip.source.value}</source>')
                if clip.query:
                    xml_parts.append(f'          <query>{_escape_xml(clip.query)}</query>')
                if clip.path:
                    xml_parts.append(f'          <path>{_escape_xml(clip.path)}</path>')
                if clip.timing:
                    xml_parts.append(f'          <timing>{_escape_xml(clip.timing)}</timing>')
                xml_parts.append('        </clip>')
            xml_parts.append('      </clips>')
        
        # transitions
        if segment.transition_to or segment.transition_type:
            xml_parts.append('      <transitions>')
            if segment.transition_to:
                xml_parts.append(f'        <transition_to>{_escape_xml(segment.transition_to)}</transition_to>')
            if segment.transition_type:
                xml_parts.append(f'        <transition_type>{_escape_xml(segment.transition_type)}</transition_type>')
            xml_parts.append('      </transitions>')
        
        # audio
        if segment.audio_file or segment.audio_duration is not None:
            xml_parts.append('      <audio>')
            if segment.audio_file:
                xml_parts.append(f'        <audio_file>{_escape_xml(segment.audio_file)}</audio_file>')
            if segment.audio_duration is not None:
                xml_parts.append(f'        <audio_duration>{segment.audio_duration}</audio_duration>')
            xml_parts.append('      </audio>')
        
        xml_parts.append('    </segment>')
    
    xml_parts.append('  </segments>')
    
    # background music
    if outline.background_music_query or outline.background_music_path:
        xml_parts.append('  <background_music>')
        if outline.background_music_query:
            xml_parts.append(f'    <query>{_escape_xml(outline.background_music_query)}</query>')
        if outline.background_music_path:
            xml_parts.append(f'    <path>{_escape_xml(outline.background_music_path)}</path>')
        xml_parts.append('  </background_music>')
    
    xml_parts.append('</video_outline>')
    
    return '\n'.join(xml_parts)

