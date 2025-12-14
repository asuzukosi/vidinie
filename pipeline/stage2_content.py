"""
content analysis operation
analyze content and create video outline with visual asset planning.
requires pipeline_id to load cached pipeline data.
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

# add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logging, get_logger
from utils.config_loader import get_config
from core.context_processor import ContextProcessor
from core.content_analyzer import ContentAnalyzer
from core.stock_image_fetcher import StockImageFetcher
from core.image_generator import ImageGenerator
from core.pipeline_data import PipelineData, PipelineStage, PipelineStatus

setup_logging(log_dir='temp')
logger = get_logger('stage2_content')


def create_video_outline(pipeline_id: str,
                         skip_stock: bool = False,
                         target_segments: int = 7,
                         segment_duration: int = 45) -> PipelineData:
    """
    analyze content and create video outline.
    requires pipeline_id to load cached pipeline data (cache is required).
    args:
        pipeline_id: uuid of existing pipeline data
        skip_stock: skip stock image fetching
        target_segments: target number of video segments
        segment_duration: target duration per segment in seconds
    returns:
        pipelinedata instance with video outline
    """
    logger.info("stage 2: content analysis started")
    config = get_config()
    temp_dir = config.get('output.temp_directory', 'temp')
    
    # load pipeline data by id (cache is required)
    try:
        pipeline_data = PipelineData.load_by_id(pipeline_id, temp_dir)
        logger.info(f"loaded pipeline data: {pipeline_data.id}")
    except FileNotFoundError:
        logger.error(f"pipeline data not found for id: {pipeline_id}")
        logger.error("run stage1_parsing.py first")
        sys.exit(1)
    
    pipeline_data.update_stage(PipelineStage.CONTENT_ANALYSIS, PipelineStatus.IN_PROGRESS)
    
    if not config.openai_api_key:
        logger.error("openai api key required")
        pipeline_data.update_stage(PipelineStage.CONTENT_ANALYSIS, PipelineStatus.FAILED)
        return pipeline_data
    
    if not pipeline_data.parsed_content:
        logger.error("parsed content not found in pipeline data")
        pipeline_data.update_stage(PipelineStage.CONTENT_ANALYSIS, PipelineStatus.FAILED)
        return pipeline_data
    
    try:
        pdf_content = pipeline_data.parsed_content
        images_metadata = pipeline_data.images_metadata or []
        
        logger.info(f"loaded {len(pdf_content['sections'])} sections and {len(images_metadata)} images")
        
        # process context into chunks
        logger.info("processing context into chunks")
        all_content = ""
        for section in pdf_content['sections']:
            all_content += section['content']
        
        prompts_dir = config.get_prompts_directory()
        chunk_length = config.get('content.chunk_length', 4000)
        context_processor = ContextProcessor(
            all_content,
            config.openai_api_key,
            pdf_content['title'],
            chunk_length=chunk_length,
            split_by='\n',
            prompts_dir=prompts_dir
        )
        chunks = context_processor.get_chunks()
        pipeline_data.chunks = chunks
        
        # store context processor information
        pipeline_data.context_processor_info = {
            'document_title': pdf_content['title'],
            'chunk_length': chunk_length,
            'split_by': '\n',
            'total_chunks': len(chunks),
            'total_content_length': len(all_content)
        }
        
        logger.info(f"generated {len(chunks)} chunks")
        
        # create video outline
        logger.info("creating video outline")
        analyzer = ContentAnalyzer(
            api_key=config.openai_api_key,
            target_segments=target_segments,
            segment_duration=segment_duration,
            prompts_dir=prompts_dir
        )
        outline = analyzer.analyze_content(
            chunks=chunks,
            images_metadata=images_metadata,
            document_title=pdf_content['title']
        )
        
        # fetch stock images
        if not skip_stock and config.get('images.use_stock_images', True):
            logger.info("fetching stock images")
            fetcher = StockImageFetcher(config.unsplash_access_key, config.pexels_api_key, output_dir=os.path.join(temp_dir, 
                                                                                                                   pipeline_data.id, 'images', 
                                                                                                                   'stock_images'))
            availability = fetcher.is_available()
            if availability['unsplash'] or availability['pexels']:
                preferred = config.get('images.preferred_stock_provider', 'unsplash')
                outline['segments'] = fetcher.fetch_for_segments(outline['segments'], preferred)
            else:
                logger.info("no stock image api keys available")
        else:
            logger.info("skipping stock images")
        
        # generate ai images if enabled
        if config.get('images.use_ai_generated', False):
            logger.info("generating ai images")
            generator = ImageGenerator(
                api_key=config.openai_api_key,
                model=config.get('images.ai_generator.model', 'dall-e-3'),
                quality=config.get('images.ai_generator.quality', 'standard'),
                size=config.get('images.ai_generator.size', '1024x1024'),
                output_dir=os.path.join(temp_dir, pipeline_data.id, 'ai_images'),
                prompts_dir=config.get_prompts_directory()
            )
            if generator.is_available():
                outline['segments'] = generator.generate_for_segments(
                    outline['segments'],
                    pipeline_id=pipeline_data.id
                )
            else:
                logger.warning("image generation not available (missing api keys)")
        else:
            logger.info("skipping ai image generation")
        
        # update pipeline data
        pipeline_data.video_outline = outline
        pipeline_data.update_stage(PipelineStage.CONTENT_ANALYSIS, PipelineStatus.COMPLETED)
        
        # save pipeline data
        pipeline_data.save_to_folder(temp_dir)
        pipeline_data.save_to_pickle(os.path.join(temp_dir, f"pipeline_{pipeline_data.id}.pkl"))
        
        logger.info(f"video outline created: {pipeline_data.id}")
        return pipeline_data
        
    except Exception as e:
        logger.error(f"error during content analysis: {str(e)}")
        pipeline_data.update_stage(PipelineStage.CONTENT_ANALYSIS, PipelineStatus.FAILED)
        return pipeline_data


def main():
    parser = argparse.ArgumentParser(description='stage 2: analyze content and create video outline')
    parser.add_argument('--pipeline-id', type=str, required=True,
                        help='uuid of pipeline data (from stage 1)')
    parser.add_argument('--skip-stock', action='store_true', help='skip stock image fetching')
    parser.add_argument('--target-segments', type=int, default=7, help='target number of video segments')
    parser.add_argument('--segment-duration', type=int, default=45, help='target duration per segment in seconds')
    args = parser.parse_args()
    
    pipeline_data = create_video_outline(
        args.pipeline_id,
        skip_stock=args.skip_stock,
        target_segments=args.target_segments,
        segment_duration=args.segment_duration
    )
    
    if pipeline_data.status == "completed":
        logger.info(f"video outline created successfully. pipeline id: {pipeline_data.id}")
        sys.exit(0)
    else:
        logger.error(f"video outline creation failed. pipeline id: {pipeline_data.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()

