"""
content analysis operations for the api.
analyzes content and creates video outlines with visual asset planning.
"""

import os
from typing import List
from core.utils.logger import get_logger
from core.utils.config_loader import config
from core.data import (
    VideoPipeline,
    VideoOutline,
    VideoPipelineStage,
    VideoPipelineStatus,
    ContentSection,
    VideoSegment,
)
from core.operations.content_analyzer import ContentAnalyzer
from core.operations.stock_fetcher import StockFetcher
from core.operations.image_generator import ImageGenerator
from core.operations.video_clip_generator import VideoClipGenerator

logger = get_logger("content_operations")


async def process_content(
    pipeline: VideoPipeline,
    target_segments: int = 4,
    segment_duration: int = 40
) -> VideoPipeline:
    """
    analyze content and create video outline with visual asset planning.
    args:
        pipeline: video pipeline object with parsed content
        target_segments: target number of video segments
        segment_duration: target duration per segment in seconds
    returns:
        updated video pipeline with video outline
    """
    anthropic_api_key = config.anthropic_api_key
    temp_dir = config.output_temp_directory
    
    if not anthropic_api_key:
        logger.error("anthropic api key required")
        raise ValueError("anthropic api key required")
    
    if not pipeline.parsed_content:
        logger.error("parsed content not found in pipeline data")
        raise ValueError("parsed content not found in pipeline data")
    
    try:
        pdf_content = pipeline.parsed_content
        images_metadata = pipeline.images_metadata or []
        
        logger.info(f"loaded {len(pdf_content.sections)} sections and {len(images_metadata)} images")
        
        # combine all sections into a single content string
        logger.info("combining content from all sections")
        all_content = ""
        for section in pdf_content.sections:
            if section.content:
                all_content += section.content + "\n"
        
        # create video outline
        # ContentAnalyzer handles iterative summarization internally
        logger.info("creating video outline")
        analyzer = ContentAnalyzer(
            target_segments=target_segments,
            segment_duration=segment_duration,
            user_instructions=pipeline.instructions
        )
        outline: VideoOutline = await analyzer.analyze_content(
            title=pdf_content.title or "",
            content=all_content,
            images_metadata=images_metadata
        )
        
        # fetch stock images and videos
        logger.info("fetching stock images and videos")
        stock_images_dir = os.path.join(temp_dir, pipeline.id, 'images', 'stock_images')
        stock_videos_dir = os.path.join(temp_dir, pipeline.id, 'video_clips', 'stock_videos')
        try:
            fetcher = StockFetcher(output_dir=stock_images_dir, video_output_dir=stock_videos_dir)
            outline.segments = await fetcher.fetch_for_segments_async(outline.segments)
        except ValueError as e:
            logger.warning(f"stock fetcher not available: {str(e)}")
        
        # generate ai images
        logger.info("generating ai images")
        ai_images_dir = os.path.join(temp_dir, pipeline.id, 'images', 'ai_images')
        generator = ImageGenerator(output_dir=ai_images_dir)
        outline.segments = await generator.generate_for_segments(
            pipeline_id=pipeline.id,
            segments=outline.segments
        )
        
        # generate ai video clips
        logger.info("generating ai video clips")
        ai_videos_dir = os.path.join(temp_dir, pipeline.id, 'video_clips', 'ai_video_clips')
        video_clip_generator = VideoClipGenerator(output_dir=ai_videos_dir)
        outline.segments = await video_clip_generator.generate_for_segments(
            pipeline_id=pipeline.id,
            segments=outline.segments
        )
        
        # update pipeline data
        pipeline.video_outline = outline
        
        logger.info(f"video outline created: {pipeline.id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"error during content analysis: {str(e)}", exc_info=True)
        raise


def _validate_parsed_content(video_pipeline: VideoPipeline) -> None:
    """validate that parsed content exists in video pipeline."""
    if not video_pipeline.parsed_content:
        raise ValueError("parsed content not found in video pipeline")


def add_section_to_content(
    video_pipeline: VideoPipeline,
    section: ContentSection
) -> ContentSection:
    """
    add a section to a video pipeline's parsed content.
    args:
        video_pipeline: video pipeline object
        section: section to add
    returns:
        added section
    """
    _validate_parsed_content(video_pipeline)
    video_pipeline.parsed_content.sections.append(section)
    return section


def delete_section_from_content(
    video_pipeline: VideoPipeline,
    index: int
) -> ContentSection:
    """delete a section from a video pipeline's parsed content."""
    _validate_parsed_content(video_pipeline)
    if index < 0 or index >= len(video_pipeline.parsed_content.sections):
        raise IndexError(f"Section index {index} out of range")
    section = video_pipeline.parsed_content.sections.pop(index)
    return section


def _validate_video_outline(video_pipeline: VideoPipeline) -> None:
    """validate that video outline exists in video pipeline."""
    if not video_pipeline.video_outline:
        raise ValueError("video outline not found in video pipeline")


def add_segment_to_outline(
    video_pipeline: VideoPipeline,
    segment: VideoSegment
) -> VideoSegment:
    """add a segment to a video pipeline's outline."""
    _validate_video_outline(video_pipeline)
    video_pipeline.video_outline.segments.append(segment)
    return segment


def delete_segment_from_outline(
    video_pipeline: VideoPipeline,
    index: int
) -> VideoSegment:
    """delete a segment from a video pipeline's outline."""
    _validate_video_outline(video_pipeline)
    if index < 0 or index >= len(video_pipeline.video_outline.segments):
        raise IndexError(f"Segment index {index} out of range")
    segment = video_pipeline.video_outline.segments.pop(index)
    return segment
