"""
Document processing operations.
Processes documents (PDF or HTML) and extracts structured content and images.
"""

import os
from typing import Optional
from core.utils.logger import get_logger
from core.utils.config_loader import get_config
from core.data import (
    VideoPipeline,
    VideoPipelineStage,
    VideoPipelineStatus,
    VideoPipelineParsedContent,
    SourceType,
)
from core.processors.pdf_processor import PDFProcessor
from core.processors.html_processor import HTMLProcessor

logger = get_logger('document_processor')


def process_pdf_document(
    pipeline: VideoPipeline,
    extract_images: bool = True,
    openai_api_key: Optional[str] = None,
    prompts_dir: Optional[str] = None
) -> VideoPipeline:
    """
    process PDF document and extract structured content and images.
    args:
        pipeline: video pipeline object with source_path set to PDF file path
        extract_images: whether to extract and label images
        openai_api key: openai api key
        prompts_dir: path to prompts directory
    returns:
        updated video pipeline with parsed content and optionally labeled images
    """
    config = get_config()
    openai_api_key = openai_api_key or config.openai_api_key
    prompts_dir = prompts_dir or config.get_prompts_directory()
    temp_dir = config.get('output.temp_directory', 'temp')
    images_dir = os.path.join(temp_dir, pipeline.id, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.IN_PROGRESS)
    
    if not os.path.exists(pipeline.source_path):
        logger.error(f"Source file not found: {pipeline.source_path}")
        pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
        return pipeline
    
    try:
        with PDFProcessor(pipeline.source_path, images_output_dir=images_dir) as processor:
            content: VideoPipelineParsedContent = processor.extract_structured_content()
            pipeline.parsed_content = content
            
            logger.info(f"Title: {content.title}")
            logger.info(f"Total pages: {content.total_pages}")
            logger.info(f"Sections: {len(content.sections)}")
            
            if extract_images:
                logger.info("Labeling images")
                processor.label_images(openai_api_key, prompts_dir)
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
    html_path: str,
    extract_images: bool = True,
    openai_api_key: Optional[str] = None,
    prompts_dir: Optional[str] = None
) -> VideoPipeline:
    """
    process HTML document (from URL or file path) and extract structured content and images.
    args:
        pipeline: video pipeline object
        html_path: path to HTML file or URL to HTML content
        extract_images: whether to extract and label images
        openai_api_key: openai api key
        prompts_dir: path to prompts directory
    returns:
        updated video pipeline with parsed content and optionally labeled images
    """
    config = get_config()
    openai_api_key = openai_api_key or config.openai_api_key
    prompts_dir = prompts_dir or config.get_prompts_directory()
    temp_dir = config.get('output.temp_directory', 'temp')
    images_dir = os.path.join(temp_dir, pipeline.id, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.IN_PROGRESS)
    
    try:
        with HTMLProcessor(html_path=html_path, images_output_dir=images_dir) as processor:
            content: VideoPipelineParsedContent = processor.extract_structured_content()
            pipeline.parsed_content = content
            
            logger.info(f"Title: {content.title}")
            logger.info(f"Total pages: {content.total_pages}")
            logger.info(f"Sections: {len(content.sections)}")
            
            if extract_images:
                logger.info("Labeling images")
                processor.label_images(openai_api_key, prompts_dir)
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
    extract_images: bool = True,
    openai_api_key: Optional[str] = None,
    prompts_dir: Optional[str] = None
) -> VideoPipeline:
    """
    process document (PDF or HTML) and extract structured content and images.
    this is a wrapper function that calls the appropriate processor based on source_type.
    args:
        pipeline: video pipeline object with source_path and source_type set
        extract_images: whether to extract and label images
        openai_api_key: openai api key
        prompts_dir: path to prompts directory
    returns:
        updated video pipeline with parsed content and optionally labeled images
    """
    if pipeline.source_type == SourceType.PDF:
        return process_pdf_document(pipeline, extract_images, openai_api_key, prompts_dir)
    elif pipeline.source_type == SourceType.HTML:
        return process_html_document(pipeline, pipeline.source_path, extract_images, openai_api_key, prompts_dir)
    else:
        logger.error(f"Unsupported source type: {pipeline.source_type}")
        pipeline.update_stage(VideoPipelineStage.DOCUMENT_PROCESSING, VideoPipelineStatus.FAILED)
        return pipeline

