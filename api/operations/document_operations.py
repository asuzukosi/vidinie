"""
document processing operations for the API.
processes documents (PDF or HTML) and extracts structured content and images.
"""

import os
import requests
from typing import Optional
from core.utils.logger import get_logger
from core.utils.config_loader import config
from core.data import (
    VideoPipeline,
    VideoPipelineStage,
    VideoPipelineStatus,
    VideoPipelineParsedContent,
    SourceType,
)
from core.processors.pdf_processor import PDFProcessor
from core.processors.html_processor import HTMLProcessor

logger = get_logger('document_operations')


def process_pdf_document(
    pipeline: VideoPipeline,
    extract_images: bool = True,
    pdf_content: Optional[bytes] = None,
    pdf_path: Optional[str] = None
) -> VideoPipeline:
    """
    process PDF document and extract structured content and images.
    args:
        pipeline: video pipeline object
        extract_images: whether to extract and label images
        pdf_content: pdf file content as bytes (optional if pdf_path is provided)
        pdf_path: path to pdf file (optional if pdf_content is provided)
    returns:
        updated video pipeline with parsed content and optionally labeled images
    """
    temp_dir = config.get('output.temp_directory', 'temp')
    images_dir = os.path.join(temp_dir, pipeline.id, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.IN_PROGRESS)
    
    # validate input
    if not pdf_content and not pdf_path:
        logger.error("either pdf_content or pdf_path must be provided")
        pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
        return pipeline
    
    # read file if pdf_path is provided
    if pdf_path:
        if not os.path.exists(pdf_path):
            logger.error(f"source file not found: {pdf_path}")
            pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
            return pipeline
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        logger.info(f"read pdf file from path: {pdf_path} ({len(pdf_content)} bytes)")
    
    try:
        # process with pdf_content
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


def process_html_document(
    pipeline: VideoPipeline,
    html_path: Optional[str] = None,
    extract_images: bool = True,
    html_content: Optional[str] = None
) -> VideoPipeline:
    """
    process HTML document (from URL, file path, or content) and extract structured content and images.
    args:
        pipeline: video pipeline object
        html_path: path to HTML file or URL to HTML content (optional if html_content is provided)
        extract_images: whether to extract and label images
        html_content: html content as string (optional if html_path is provided)
    returns:
        updated video pipeline with parsed content and optionally labeled images
    """
    temp_dir = config.get('output.temp_directory', 'temp')
    images_dir = os.path.join(temp_dir, pipeline.id, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.IN_PROGRESS)
    
    # validate input
    if not html_content and not html_path:
        logger.error("either html_content or html_path must be provided")
        pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
        return pipeline
    
    # read file or fetch from URL if html_path is provided
    if html_path:
        if html_path.startswith(('http://', 'https://')):
            # fetch from URL
            try:
                response = requests.get(html_path)
                response.raise_for_status()
                html_content = response.text
                logger.info(f"fetched html content from URL: {html_path} ({len(html_content)} characters)")
            except requests.exceptions.RequestException as e:
                logger.error(f"failed to fetch HTML from URL {html_path}: {str(e)}")
                pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
                return pipeline
        else:
            # read from file
            if not os.path.exists(html_path):
                logger.error(f"html file not found: {html_path}")
                pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
                return pipeline
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            logger.info(f"read html file from path: {html_path} ({len(html_content)} characters)")
    
    try:
        # process with html_content
        processor = HTMLProcessor(html_content=html_content, images_output_dir=images_dir)
        
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
        logger.info(f"html document processing complete. pipeline id: {pipeline.id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"Error during HTML document processing: {str(e)}", exc_info=True)
        pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
        return pipeline


def process_document(
    pipeline: VideoPipeline,
    extract_images: bool = True
) -> VideoPipeline:
    """
    process document (PDF or HTML) and extract structured content and images.
    this is a wrapper function that calls the appropriate processor based on source_type.
    args:
        pipeline: video pipeline object with source_path and source_type set
        extract_images: whether to extract and label images
    returns:
        updated video pipeline with parsed content and optionally labeled images
    """
    if pipeline.source_type == SourceType.PDF:
        return process_pdf_document(pipeline, extract_images=extract_images, pdf_path=pipeline.source_path)
    elif pipeline.source_type == SourceType.HTML:
        return process_html_document(pipeline, html_path=pipeline.source_path, extract_images=extract_images)
    else:
        logger.error(f"unsupported source type: {pipeline.source_type}")
        pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
        return pipeline

