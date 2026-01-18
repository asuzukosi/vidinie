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
# add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logging, get_logger
from core.utils.config_loader import config
from core.data import (
    VideoPipeline,
    VideoPipelineStage,
    VideoPipelineStatus,
    VideoPipelineParsedContent,
    SourceType,
)
from core.processors.pdf_processor import PDFProcessor

setup_logging(log_dir='temp')
logger = get_logger('document_processing')


def process_pdf_document_impl(
    pipeline: VideoPipeline,
    extract_images: bool = True,
    pdf_path: str = None
) -> VideoPipeline:
    """
    process pdf document and extract structured content and images.
    explicit implementation using PDFProcessor class directly.
    """
    temp_dir = config.get('output.temp_directory', 'temp')
    images_dir = os.path.join(temp_dir, pipeline.id, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.IN_PROGRESS)
    
    if not pdf_path or not os.path.exists(pdf_path):
        logger.error(f"Source file not found: {pdf_path}")
        pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
        return pipeline
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    logger.info(f"read pdf file from path: {pdf_path} ({len(pdf_content)} bytes)")
    
    try:
        processor = PDFProcessor(pdf_content=pdf_content, images_output_dir=images_dir)
        
        with processor:
            content: VideoPipelineParsedContent = processor.extract_structured_content()
            pipeline.parsed_content = content
            
            logger.info(f"Title: {content.title}")
            logger.info(f"Total pages: {content.total_pages}")
            logger.info(f"Sections: {len(content.sections)}")
            
            if extract_images:
                logger.info("Labeling images")
                processor.label_images()
                pipeline.images_metadata = processor.images_metadata
                logger.info(f"Labeled {len(processor.images_metadata)} images")
            else:
                pipeline.images_metadata = []
        
        pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.COMPLETED)
        logger.info(f"PDF document processing complete. Pipeline ID: {pipeline.id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"Error during PDF document processing: {str(e)}", exc_info=True)
        pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
        return pipeline


def parse_document(pdf_path: str, extract_images: bool = True) -> VideoPipeline:
    """
    parse document, extract structured content, and optionally extract/label images.
    creates new video pipeline.
    
    args:
        pdf_path: path to the pdf file
        extract_images: whether to extract and label images (default: True)
    
    returns:
        video pipeline with parsed content and optionally labeled images
    """
    logger.info("document processing started")
    
    # create new video pipeline
    video_pipeline = VideoPipeline()
    video_pipeline.source_path = pdf_path
    video_pipeline.source_type = SourceType.PDF
    logger.info(f"created new pipeline with id: {video_pipeline.id}")
    
    # use explicit implementation to process document
    video_pipeline = process_pdf_document_impl(
        video_pipeline,
        extract_images=extract_images,
        pdf_path=pdf_path
    )
    
    # save video pipeline
    if video_pipeline.status.value == "completed":
        temp_dir = config.get('output.temp_directory', 'temp')
        video_pipeline.save_to_folder(temp_dir)
        video_pipeline.save_to_pickle(os.path.join(temp_dir, f"pipeline_{video_pipeline.id}.pkl"))
    
    return video_pipeline


def main():
    parser = argparse.ArgumentParser(description='parse pdf and extract content including images')
    parser.add_argument('pdf_file', type=str, help='path to the pdf file')
    parser.add_argument('--skip-images', action='store_true', 
                       help='skip image extraction and labeling')
    args = parser.parse_args()
    
    video_pipeline = parse_document(args.pdf_file, extract_images=not args.skip_images)

    if video_pipeline.status.value == "completed":
        logger.info(f"document processing successful. pipeline ID: {video_pipeline.id}")
        sys.exit(0)
    else:
        logger.error(f"document processing failed. pipeline ID: {video_pipeline.id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
