"""
document processing operations for the API.
processes documents (PDF or HTML) and extracts structured content and images.
"""

import os
from core.utils.logger import get_logger
from core.utils.config_loader import config
from core.data import (
    VideoPipeline,
    ParsedContent,
    SourceType,
)
from core.processors.pdf_processor import PDFProcessor
from core.processors.html_processor import HTMLProcessor

logger = get_logger('document_operations')


async def process_pdf_document(
    pipeline: VideoPipeline,
    extract_images: bool = True,
    pdf_content: bytes = None
) -> VideoPipeline:
    """
    process PDF document and extract structured content and images.
    args:
        pipeline: video pipeline object
        extract_images: whether to extract and label images
        pdf_content: pdf file content as bytes
    returns:
        updated video pipeline with parsed content and optionally labeled images
    """
    temp_dir = config.output_temp_directory
    images_dir = os.path.join(temp_dir, pipeline.id, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    # validate input
    if not pdf_content:
        logger.error("pdf_content must be provided")
        raise ValueError("pdf_content must be provided")
    
    try:
        # process with pdf_content
        processor = PDFProcessor(pdf_content=pdf_content, images_output_dir=images_dir, user_instructions=pipeline.instructions)
        
        with processor:
            content: ParsedContent = processor.extract_structured_content()
            pipeline.parsed_content = content
            
            logger.info(f"Title: {content.title}")
            logger.info(f"Total pages: {content.total_pages}")
            logger.info(f"Sections: {len(content.sections)}")
            
            if extract_images:
                logger.info("Labeling images")
                await processor.label_images()
                pipeline.images_metadata = processor.images_metadata
                logger.info(f"Labeled {len(processor.images_metadata)} images")
            else:
                pipeline.images_metadata = []
        
        logger.info(f"PDF document processing complete. Pipeline ID: {pipeline.id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"Error during PDF document processing: {str(e)}", exc_info=True)
        raise


async def process_html_document(
    pipeline: VideoPipeline,
    extract_images: bool = True,
    html_content: str = None,
    original_url: str = None
) -> VideoPipeline:
    """
    process HTML document and extract structured content and images.
    args:
        pipeline: video pipeline object
        extract_images: whether to extract and label images
        html_content: html content as string
        original_url: original URL of the HTML document (required for resolving relative image paths)
    returns:
        updated video pipeline with parsed content and optionally labeled images
    """
    temp_dir = config.output_temp_directory
    images_dir = os.path.join(temp_dir, pipeline.id, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    # validate input
    if not html_content:
        logger.error("html_content must be provided")
        raise ValueError("html_content must be provided")
    
    if not original_url:
        logger.error("original_url must be provided for HTML processing")
        raise ValueError("original_url must be provided for HTML processing")
    
    try:
        # process with html_content
        processor = HTMLProcessor(
            html_content=html_content,
            original_url=original_url,
            images_output_dir=images_dir,
            user_instructions=pipeline.instructions
        )
        
        with processor:
            content: ParsedContent = processor.extract_structured_content()
            pipeline.parsed_content = content
            
            logger.info(f"Title: {content.title}")
            logger.info(f"Total pages: {content.total_pages}")
            logger.info(f"Sections: {len(content.sections)}")
            
            if extract_images:
                logger.info("Labeling images")
                await processor.label_images()
                pipeline.images_metadata = processor.images_metadata
                logger.info(f"Labeled {len(processor.images_metadata)} images")
            else:
                pipeline.images_metadata = []
        
        logger.info(f"html document processing complete. pipeline id: {pipeline.id}")
        return pipeline
        
    except Exception as e:
        logger.error(f"Error during HTML document processing: {str(e)}", exc_info=True)
        raise


async def process_document(
    pipeline: VideoPipeline,
    extract_images: bool = True,
    pdf_content: bytes = None,
    html_content: str = None,
    original_url: str = None
) -> VideoPipeline:
    """
    process document (PDF or HTML) and extract structured content and images.
    this is a wrapper function that calls the appropriate processor based on source_type.
    args:
        pipeline: video pipeline object with source_type set
        extract_images: whether to extract and label images
        pdf_content: pdf file content as bytes (required for PDF source)
        html_content: html content as string (required for HTML source)
        original_url: original URL of the HTML document (required for HTML source)
    returns:
        updated video pipeline with parsed content and optionally labeled images
    """
    if pipeline.source_type == SourceType.PDF:
        if not pdf_content:
            raise ValueError("pdf_content must be provided for PDF source")
        return await process_pdf_document(pipeline, extract_images=extract_images, pdf_content=pdf_content)
    elif pipeline.source_type == SourceType.HTML:
        if not html_content:
            raise ValueError("html_content must be provided for HTML source")
        if not original_url:
            raise ValueError("original_url must be provided for HTML source")
        return await process_html_document(pipeline, extract_images=extract_images, html_content=html_content, original_url=original_url)
    else:
        logger.error(f"unsupported source type: {pipeline.source_type}")
        raise ValueError(f"unsupported source type: {pipeline.source_type}")