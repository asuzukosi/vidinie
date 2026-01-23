"""
content analysis operation
analyze content and create video outline with visual asset planning.
requires pipeline_id to load cached video pipeline.
workflow sequence:
    this is the second operation in the standard workflow:
    1. document_processing  - parse pdf and extract content (stage1)
    2. content_analysis     - analyze content and create video outline (THIS MODULE - stage2)
    3. script_generation    - generate narration scripts and voiceovers (stage3)
    4. video_generation     - compose final video from all assets (stage4)
    
    note: the workflow can be customized based on document type and requirements.
"""

import sys
import os
import argparse
from typing import List
from utils.logger import setup_logging, get_logger
from core.utils.config_loader import config
from core.data import (
    VideoPipeline,
    VideoPipelineOutline,
    VideoPipelineStage,
    VideoPipelineStatus,
    VideoPipelineContextChunk,
)
from core.operations.content_analyzer import ContentAnalyzer
from core.operations.context_processor import ContextProcessor
from core.operations.stock_image_fetcher import StockImageFetcher
from core.operations.image_generator import ImageGenerator

setup_logging(log_dir='temp')
logger = get_logger('stage2_content')


def process_content_impl(
    pipeline: VideoPipeline,
    skip_stock: bool = False,
    target_segments: int = 5,
    segment_duration: int = 40
) -> VideoPipeline:
    """
    analyze content and create video outline with visual asset planning.
    Explicit implementation using ContentAnalyzer, ContextProcessor, and other classes directly.
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
        
        # Process context into chunks using ContextProcessor class
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
        
        # create video outline using ContentAnalyzer class
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
        
        # fetch stock images using StockImageFetcher class
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
        
        # generate ai images if enabled using ImageGenerator class
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


def create_video_outline(pipeline_id: str,
                         skip_stock: bool = False,
                         target_segments: int = 5,
                         segment_duration: int = 40) -> VideoPipeline:
    """
    analyze content and create video outline.
    requires pipeline_id to load cached video pipeline (cache is required).
    args:
        pipeline_id: uuid of existing video pipeline
        skip_stock: skip stock image fetching
        target_segments: target number of video segments
        segment_duration: target duration per segment in seconds
    returns:
        video pipeline instance with video outline
    """
    logger.info("stage 2: content analysis started")
    temp_dir = config.get('output.temp_directory', 'temp')
    
    # load video pipeline by id (cache is required)
    try:
        video_pipeline = VideoPipeline.load_by_id(pipeline_id, temp_dir)
        logger.info(f"loaded video pipeline: {video_pipeline.id}")
    except FileNotFoundError:
        logger.error(f"video pipeline not found for id: {pipeline_id}")
        logger.error("run stage1_parsing.py first")
        sys.exit(1)
    
    # use explicit implementation to process content
    video_pipeline = process_content_impl(
        video_pipeline,
        skip_stock=skip_stock,
        target_segments=target_segments,
        segment_duration=segment_duration
    )
    
    # save video pipeline
    if video_pipeline.status.value == "completed":
        temp_dir = config.get('output.temp_directory', 'temp')
        video_pipeline.save_to_folder(temp_dir)
        video_pipeline.save_to_pickle(os.path.join(temp_dir, f"pipeline_{video_pipeline.id}.pkl"))
    
    return video_pipeline


def main():
    parser = argparse.ArgumentParser(description='stage 2: analyze content and create video outline')
    parser.add_argument('--pipeline-id', type=str, required=True,
                        help='uuid of pipeline data (from stage 1)')
    parser.add_argument('--skip-stock', action='store_true', help='skip stock image fetching')
    parser.add_argument('--target-segments', type=int, default=5, help='target number of video segments')
    parser.add_argument('--segment-duration', type=int, default=40, help='target duration per segment in seconds')
    args = parser.parse_args()
    
    video_pipeline = create_video_outline(
        args.pipeline_id,
        skip_stock=args.skip_stock,
        target_segments=args.target_segments,
        segment_duration=args.segment_duration
    )
    
    if video_pipeline.status == "completed":
        logger.info(f"video outline created successfully. pipeline id: {video_pipeline.id}")
        sys.exit(0)
    else:
        logger.error(f"video outline creation failed. pipeline id: {video_pipeline.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
