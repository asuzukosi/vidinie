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
    SourceType,
)
from core.operations.document_processor import process_document
setup_logging(log_dir='temp')
logger = get_logger('document_processing')


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
    
    # use modular operation to process document
    video_pipeline = process_document(
        video_pipeline,
        extract_images=extract_images
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
