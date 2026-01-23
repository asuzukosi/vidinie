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
    VideoPipelineOutline,
    VideoPipelineStage,
    VideoPipelineStatus,
    VideoPipelineContextChunk,
    VideoPipelineContentSection,
    VideoPipelineSegment,
)
from core.operations.content_analyzer import ContentAnalyzer
from core.operations.context_processor import ContextProcessor
from core.operations.stock_image_fetcher import StockImageFetcher
from core.operations.image_generator import ImageGenerator

logger = get_logger("content_operations")


def process_content(
    pipeline: VideoPipeline,
    skip_stock: bool = False,
    target_segments: int = 5,
    segment_duration: int = 40
) -> VideoPipeline:
    """
    analyze content and create video outline with visual asset planning.
    args:
        pipeline: video pipeline object with parsed content
        skip_stock: skip stock image fetching
        target_segments: target number of video segments
        segment_duration: target duration per segment in seconds
    returns:
        updated video pipeline with video outline
    """
    openai_api_key = config.openai_api_key
    temp_dir = config.get('output.temp_directory', 'temp')
    
    pipeline.update_stage(VideoPipelineStage.CONTENT_ANALYSIS, VideoPipelineStatus.IN_PROGRESS)
    
    if not openai_api_key:
        logger.error("openai api key required")
        pipeline.update_stage(VideoPipelineStage.CONTENT_ANALYSIS, VideoPipelineStatus.FAILED)
        return pipeline
    
    if not pipeline.parsed_content:
        logger.error("parsed content not found in pipeline data")
        pipeline.update_stage(VideoPipelineStage.CONTENT_ANALYSIS, VideoPipelineStatus.FAILED)
        return pipeline
    
    try:
        pdf_content = pipeline.parsed_content
        images_metadata = pipeline.images_metadata or []
        
        logger.info(f"loaded {len(pdf_content.sections)} sections and {len(images_metadata)} images")
        
        # Process context into chunks
        logger.info("processing context into chunks")
        all_content = ""
        for section in pdf_content.sections:
            all_content += section.content
        
        chunk_length = config.get('content.chunk_length', 4000)
        context_processor = ContextProcessor(
            all_content,
            pdf_content.title,
            chunk_length=chunk_length,
            split_by='\n'
        )
        chunks: List[VideoPipelineContextChunk] = context_processor.get_chunks()
        pipeline.chunks = chunks
        
        logger.info(f"generated {len(chunks)} chunks")
        
        # create video outline
        logger.info("creating video outline")
        analyzer = ContentAnalyzer(
            target_segments=target_segments,
            segment_duration=segment_duration
        )
        outline: VideoPipelineOutline = analyzer.analyze_content(
            chunks=chunks,
            images_metadata=images_metadata,
            document_title=pdf_content.title
        )
        
        # fetch stock images
        if not skip_stock and config.get('images.use_stock_images', True):
            logger.info("fetching stock images")
            stock_images_dir = os.path.join(temp_dir, pipeline.id, 'images', 'stock_images')
            fetcher = StockImageFetcher(output_dir=stock_images_dir)
            availability = fetcher.is_available()
            if availability['unsplash'] or availability['pexels']:
                preferred = config.get('images.preferred_stock_provider', 'unsplash')
                outline.segments = fetcher.fetch_for_segments(outline.segments, preferred)
            else:
                logger.info("no stock image api keys available")
        else:
            logger.info("skipping stock images")
        
        # generate ai images if enabled
        if config.get('images.use_ai_generated', False):
            logger.info("generating ai images")
            ai_images_dir = os.path.join(temp_dir, pipeline.id, 'images', 'ai_images')
            generator = ImageGenerator(
                model=config.get('images.ai_generator.model', 'dall-e-3'),
                quality=config.get('images.ai_generator.quality', 'standard'),
                size=config.get('images.ai_generator.size', '1024x1024'),
                output_dir=ai_images_dir
            )
            if generator.is_available():
                outline.segments = generator.generate_for_segments(
                    outline.segments,
                    pipeline_id=pipeline.id
                )
            else:
                logger.warning("image generation not available (missing api keys)")
        else:
            logger.info("skipping ai image generation")
        
        # update pipeline data
        pipeline.video_outline = outline
        pipeline.update_stage(VideoPipelineStage.CONTENT_ANALYSIS, VideoPipelineStatus.COMPLETED)
        
        logger.info(f"video outline created: {pipeline.id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"error during content analysis: {str(e)}", exc_info=True)
        pipeline.update_stage(VideoPipelineStage.CONTENT_ANALYSIS, VideoPipelineStatus.FAILED)
        return pipeline


def _validate_parsed_content(video_pipeline: VideoPipeline) -> None:
    """validate that parsed content exists in video pipeline."""
    if not video_pipeline.parsed_content:
        raise ValueError("parsed content not found in video pipeline")


def add_section_to_content(
    video_pipeline: VideoPipeline,
    section: VideoPipelineContentSection
) -> VideoPipelineContentSection:
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
) -> VideoPipelineContentSection:
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
    segment: VideoPipelineSegment
) -> VideoPipelineSegment:
    """add a segment to a video pipeline's outline."""
    _validate_video_outline(video_pipeline)
    video_pipeline.video_outline.segments.append(segment)
    return segment


def delete_segment_from_outline(
    video_pipeline: VideoPipeline,
    index: int
) -> VideoPipelineSegment:
    """delete a segment from a video pipeline's outline."""
    _validate_video_outline(video_pipeline)
    if index < 0 or index >= len(video_pipeline.video_outline.segments):
        raise IndexError(f"Segment index {index} out of range")
    segment = video_pipeline.video_outline.segments.pop(index)
    return segment
