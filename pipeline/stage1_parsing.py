"""
document processing operation

parse pdf document, extract structured content, and label images with AI.
creates initial pipeline data object with all extracted content.

workflow sequence:
    this is typically the first operation in the standard workflow:
    1. document_processing  - parse pdf and extract content (THIS MODULE)
    2. content_analysis     - analyze content and create video outline
    3. script_generation    - generate narration scripts and voiceovers
    4. video_generation     - compose final video from all assets
    
    note: the workflow can be customized based on document type and requirements.
"""

import sys
import os
import argparse
from pathlib import Path

# add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logging, get_logger
from utils.config_loader import get_config
from core.processors.pdf_processor import PDFProcessor
from core.pipeline_data import PipelineData, ParsedContent, SourceType
from core.pipeline_data import PipelineStage, PipelineStatus
setup_logging(log_dir='temp')
logger = get_logger('document_processing')


def parse_document(pdf_path: str, extract_images: bool = True) -> PipelineData:
    """
    parse document, extract structured content, and optionally extract/label images.
    creates new pipeline data.
    
    args:
        pdf_path: path to the pdf file
        extract_images: whether to extract and label images (default: True)
    
    returns:
        pipeline data with parsed content and optionally labeled images
    """
    logger.info("document processing started")
    
    # create new pipeline data
    pipeline_data = PipelineData()
    pipeline_data.source_path = pdf_path
    pipeline_data.source_type = SourceType.PDF
    logger.info(f"created new pipeline with id: {pipeline_data.id}")
    
    pipeline_data.update_stage(PipelineStage.DOCUMENT_PROCESSING, PipelineStatus.IN_PROGRESS)
    
    if not os.path.exists(pdf_path):
        logger.error(f"pdf file not found: {pdf_path}")
        pipeline_data.update_stage(PipelineStage.DOCUMENT_PROCESSING, PipelineStatus.FAILED)
        return pipeline_data
    
    try:
        config = get_config()
        temp_dir = config.get('output.temp_directory', 'temp')
        images_dir = os.path.join(temp_dir, pipeline_data.id, 'images')
        
        # parsing pdf and extracting structured content
        logger.info(f"parsing pdf: {pdf_path}")
        with PDFProcessor(pdf_path, images_output_dir=images_dir) as processor:
            content: ParsedContent = processor.extract_structured_content()
            pipeline_data.parsed_content = content
            
            # logging content info
            logger.info(f"title: {content.title}")
            logger.info(f"total pages: {content.total_pages}")
            logger.info(f"sections: {len(content.sections)}")
            
            # extract and label images if requested
            if extract_images:
                logger.info("labeling images")
                processor.label_images(config.openai_api_key, config.get_prompts_directory())
                pipeline_data.images_metadata = processor.images_metadata
                logger.info(f"labeled {len(processor.images_metadata)} images")
            else:
                logger.info("skipping image labeling")
                pipeline_data.images_metadata = []
                logger.info("no images set for pipeline data")
        
        # updating and saving pipeline data
        pipeline_data.update_stage(PipelineStage.DOCUMENT_PROCESSING, PipelineStatus.COMPLETED)
        pipeline_data.save_to_folder(temp_dir)
        pipeline_data.save_to_pickle(os.path.join(temp_dir, f"pipeline_{pipeline_data.id}.pkl"))
        
        logger.info(f"document processing complete. pipeline ID: {pipeline_data.id}")
        return pipeline_data
        
    except Exception as e:
        logger.error(f"error during document processing: {str(e)}", exc_info=True)
        pipeline_data.update_stage(PipelineStage.DOCUMENT_PROCESSING, PipelineStatus.FAILED)
        return pipeline_data


def main():
    parser = argparse.ArgumentParser(description='parse pdf and extract content including images')
    parser.add_argument('pdf_file', type=str, help='path to the pdf file')
    parser.add_argument('--skip-images', action='store_true', 
                       help='skip image extraction and labeling')
    args = parser.parse_args()
    
    pipeline_data = parse_document(args.pdf_file, extract_images=not args.skip_images)

    if pipeline_data.status == PipelineStatus.COMPLETED:
        logger.info(f"document processing successful. pipeline ID: {pipeline_data.id}")
        sys.exit(0)
    else:
        logger.error(f"document processing failed. pipeline ID: {pipeline_data.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
