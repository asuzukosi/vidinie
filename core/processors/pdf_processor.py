"""
pdf processor module
extracts text, structure, and images from pdf documents.
uses pdfplumber for text extraction and pymupdf for image extraction.
"""

import pdfplumber
import fitz
from PIL import Image
import io
import os
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List
from core.utils.logger import get_logger
from core.processors.base import DocumentProcessor
from core.operations.image_labeler import ImageLabeler
from core.data import (
    VideoPipelineParsedContent,
    VideoPipelineImageMetadata,
    VideoPipelineContentMetadata,
    VideoPipelineContentSection,
    VideoPipelineImageStats,
)

logger = get_logger('pdf_processor')


class PDFProcessor(DocumentProcessor):
    """
    processor for extracting text, structure, and images from pdf documents.
    args:
        pdf_path: path to the pdf file
        images_output_dir: directory to save extracted images (default: "temp/images")
    """
    
    def __init__(self, pdf_path: str, images_output_dir: str = "temp/images"):
        """
        initialize pdf processor.
        args:
            pdf_path: path to the pdf file
            images_output_dir: directory to save extracted images
        """
        self.pdf_path = pdf_path
        self.images_output_dir = images_output_dir
        self.pdf = None
        self.pdf_document = None
        self.pages_data = []
        self.images_metadata: List[VideoPipelineImageMetadata] = []
        
        # create output directory for images
        Path(images_output_dir).mkdir(parents=True, exist_ok=True)
        
    def __enter__(self):
        """context manager entry."""
        self.pdf = pdfplumber.open(self.pdf_path)
        self.pdf_document = fitz.open(self.pdf_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """context manager exit."""
        if self.pdf:
            self.pdf.close()
        if self.pdf_document:
            self.pdf_document.close()
        
    def extract_text(self) -> str:
        """
        extract all text from the pdf document.
        returns:
            complete text content of the pdf document
        """
        if not self.pdf:
            raise ValueError("pdf document not opened. use context manager or call __enter__()")
        # initialize full text
        full_text = []
        for page_num, page in enumerate(self.pdf.pages, 1):
            text = page.extract_text()
            if text:
                full_text.append(text)
                logger.info(f"extracted text from page {page_num}")
        
        return "\n\n".join(full_text)
    
    def extract_structured_content(self) -> VideoPipelineParsedContent:
        """
        extract text with structure information (headings, paragraphs, lists).
        returns:
            parsed content object
        """
        if not self.pdf:
            raise ValueError("pdf document not opened. use context manager or call __enter__()")
            
        parsed_content = VideoPipelineParsedContent()
        parsed_content.title = self._extract_title()
        parsed_content.total_pages = len(self.pdf.pages)
        parsed_content.metadata = VideoPipelineContentMetadata(
            title=self.pdf.metadata.get('Title', ''),
            creator=self.pdf.metadata.get('Author', ''),
            producer=self.pdf.metadata.get('Producer', ''),
            creation_date=self.pdf.metadata.get('CreationDate', ''),
            modification_date=self.pdf.metadata.get('ModDate', '')
        )
        full_text = self.extract_text()
        parsed_content.sections = self._identify_sections(full_text)
        
        return parsed_content
    
    def _extract_title(self) -> str:
        """
        extract document title from metadata or first page.
        
        returns:
            document title
        """
        # try metadata first
        if self.pdf.metadata and 'Title' in self.pdf.metadata:
            title = self.pdf.metadata['Title']
            if title and len(title.strip()) > 0:
                return title.strip()
        
        # fallback: try to get title from first page
        if self.pdf.pages:
            first_page_text = self.pdf.pages[0].extract_text()
            if first_page_text:
                lines = first_page_text.split('\n')
                for line in lines[:5]:  # check first 5 lines
                    line = line.strip()
                    if len(line) > 10 and len(line) < 150:  # reasonable title length
                        return line
        
        return "untitled document"
    
    def _identify_sections(self, text: str) -> List[VideoPipelineContentSection]:
        """
        identify sections in the text based on headings.
        returns:
            list of sections with title and content
        """
        sections: List[VideoPipelineContentSection] = []
        
        # split by double newlines (paragraphs)
        paragraphs = text.split('\n\n')
        
        current_section = VideoPipelineContentSection()
        current_section.title = "introduction"
        current_section.content = ""
        current_section.level = 1
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # detect headings (simple heuristic: short lines, possibly with numbers)
            if self._is_likely_heading(para):
                # save previous section if it has content
                if current_section.content.strip():
                    sections.append(current_section)
                
                # start new section
                current_section = VideoPipelineContentSection(
                    title=para,
                    content="",
                    level=self._detect_heading_level(para)
                )
            else:
                # add to current section
                current_section.content += para + "\n\n"
        
        # add the last section
        if current_section.content.strip():
            sections.append(current_section)
        
        # if no sections were detected, create one section with all content
        if not sections:
            sections.append(VideoPipelineContentSection(
                title="content",
                content=text,
                level=1
            ))
        
        logger.info(f"identified {len(sections)} sections")
        return sections
    
    def _is_likely_heading(self, text: str) -> bool:
        """
        determine if a line of text is likely a heading.
        args:
            text: text to check
        returns:
            true if likely a heading
        """
        # heuristics for heading detection
        text = text.strip()
        
        # too long for a heading
        if len(text) > 200:
            return False
        
        # too short
        if len(text) < 3:
            return False
        
        # contains heading patterns
        heading_patterns = [
            r'^\d+\.',  # starts with number and dot (1. introduction)
            r'^Chapter \d+',  # chapter x
            r'^Section \d+',  # section x
            r'^[A-Z][A-Z\s]+$',  # all caps
            r'^\d+\.\d+',  # numbered subsection (1.1)
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True
        
        # short line with mostly capital letters
        if len(text) < 100:
            capital_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if capital_ratio > 0.5:
                return True
        
        return False
    
    def _detect_heading_level(self, heading: str) -> int:
        """
        detect the level of a heading (1 = main, 2 = sub, etc.).
        args:
            heading: heading to check
        returns:
            heading level (1-3)
        """
        # check for numbered headings
        if re.match(r'^\d+\.\.\.\d+', heading):
            return 3
        elif re.match(r'^\d+\.\d+', heading):
            return 2
        elif re.match(r'^\d+\.', heading):
            return 1
        
        # all caps = level 1
        if heading.isupper():
            return 1
        
        # default
        return 2
    
    def get_page_count(self) -> int:
        """
        get the total number of pages in the pdf document.
        returns:
            number of pages
        """
        if not self.pdf:
            raise ValueError("pdf document not opened. use context manager or call __enter__()")
        return len(self.pdf.pages)
    
    def extract_text_by_page(self) -> List[str]:
        """
        extract text from each page separately.
        
        returns:
            list of text content per page
        """
        if not self.pdf:
            raise ValueError("pdf not opened")
            
        pages_text = []
        for page in self.pdf.pages:
            text = page.extract_text()
            pages_text.append(text if text else "")
        
        return pages_text
    
    
    def extract_images(self, min_width: int = 100, min_height: int = 100) -> List[VideoPipelineImageMetadata]:
        """
        extract all images from the pdf document.
        args:
            min_width: minimum image width to extract (filters small icons)
            min_height: minimum image height to extract
        returns:
            list of image metadata
        """
        if not self.pdf_document:
            raise ValueError("pdf document not opened. use context manager or call __enter__()")
        
        logger.info(f"starting image extraction from {self.pdf_path}")
        
        # initialize image count
        image_count = 0
        self.images_metadata = []
        
        # iterate over pages
        for page_num in range(len(self.pdf_document)):
            page = self.pdf_document[page_num]
            image_list = page.get_images(full=True)
            
            # log number of images found on the page
            logger.info(f"page {page_num + 1}: found {len(image_list)} images")
            
            # iterate over images on the page
            for img_index, img_info in enumerate(image_list):
                try:
                    # extract image data
                    xref = img_info[0]
                    base_image = self.pdf_document.extract_image(xref)
                    
                    # get image bytes and metadata
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)
                    
                    # filter out small images (likely icons or decorations)
                    if width < min_width or height < min_height:
                        logger.debug(f"skipping small image: {width}x{height}")
                        continue
                    
                    # generate unique filename using hash
                    image_hash = hashlib.md5(image_bytes).hexdigest()[:10]
                    filename = f"img_p{page_num + 1}_{img_index}_{image_hash}.{image_ext}"
                    filepath = os.path.join(self.images_output_dir, filename)
                    
                    # save image
                    with open(filepath, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    # get additional metadata
                    try:
                        with Image.open(io.BytesIO(image_bytes)) as pil_img:
                            format_name = pil_img.format
                            mode = pil_img.mode
                    except Exception:
                        format_name = image_ext
                        mode = "unknown"
                    
                    # get surrounding text context (text near the image on the page)
                    text_context = self._extract_text_context(page, img_info)
                    
                    # store metadata
                    image_metadata = VideoPipelineImageMetadata()
                    image_metadata.filename = filename
                    image_metadata.filepath = filepath
                    image_metadata.page_number = page_num + 1
                    image_metadata.width = width
                    image_metadata.height = height
                    image_metadata.format = format_name
                    image_metadata.mode = mode
                    image_metadata.size_bytes = len(image_bytes)
                    image_metadata.text_context = text_context
                    image_metadata.xref = xref
                    image_metadata.index_on_page = img_index
                    image_metadata.label = None  # to be filled by image_labeler
                    image_metadata.description = None  # to be filled by image_labeler
                    image_metadata.relevance_score = None  # to be filled by content_analyzer
                    
                    # add metadata to list
                    self.images_metadata.append(image_metadata)
                    image_count += 1
                    
                    # log image extraction
                    logger.info(f"extracted image {image_count}: {filename} ({width}x{height})")
                    
                except Exception as e:
                    logger.error(f"error extracting image {img_index} from page {page_num + 1}: {str(e)}")
                    continue
        
        logger.info(f"extracted {image_count} images from {len(self.pdf_document)} pages")
        
        # save metadata to json
        self._save_image_metadata()
        
        # return images metadata
        return self.images_metadata
    
    def _extract_text_context(self, page, img_info, context_chars: int = 500) -> str:
        """
        extract text near an image on the page.
        
        args:
            page: pdf page object
            img_info: image information
            context_chars: number of characters to extract
        
        returns:
            text context surrounding the image
        """
        try:
            # get all text from the page
            page_text = page.get_text()
            # return a snippet of the page text
            if len(page_text) > context_chars:
                return page_text[:context_chars]
            return page_text
            
        except Exception as e:
            logger.debug(f"could not extract text context: {str(e)}")
            return ""
    
    def _save_image_metadata(self):
        """save image metadata to json file."""
        metadata_path = os.path.join(self.images_output_dir, "images_metadata.json")
        # save metadata to json file
        with open(metadata_path, 'w') as f:
            data = [img.model_dump(mode="json") for img in self.images_metadata]
            json.dump(data, f, indent=2)
        
        logger.info(f"saved metadata to {metadata_path}")
    
    def load_image_metadata(self) -> List[Dict]:
        """
        load previously saved image metadata.
        
        returns:
            list of image metadata dictionaries
        """
        metadata_path = os.path.join(self.images_output_dir, "images_metadata.json")
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                data = json.load(f)
                self.images_metadata = [VideoPipelineImageMetadata(**item) for item in data]
            logger.info(f"loaded metadata for {len(self.images_metadata)} images")
            return self.images_metadata
        else:
            logger.warning("no metadata file found")
            return []
    
    def get_images_by_page(self, page_number: int) -> List[Dict]:
        """
        get all images from a specific page.
        args:
            page_number: page number (1-indexed)
        returns:
            list of image metadata for that page
        """
        return [img for img in self.images_metadata if img.page_number == page_number]
    
    def get_image_stats(self) -> VideoPipelineImageStats:
        """
        get statistics about extracted images.
        
        returns:
            VideoPipelineImageStats object with image statistics
        """
        if not self.images_metadata:
            return VideoPipelineImageStats(
                total_images=0,
                average_size=0,
                total_size=0,
                formats={},
                pages_with_images=0
            )
        
        # get total size of all images
        total_size = sum(img.size_bytes or 0 for img in self.images_metadata)
        
        # get formats of all images
        formats: Dict[str, int] = {}
        for img in self.images_metadata:
            fmt = img.format or 'unknown'
            formats[fmt] = formats.get(fmt, 0) + 1
        
        return VideoPipelineImageStats(
            total_images=len(self.images_metadata),
            average_size=total_size // len(self.images_metadata) if self.images_metadata else 0,
            total_size=total_size,
            formats=formats,
            pages_with_images=len(set(img.page_number for img in self.images_metadata if img.page_number is not None))
        )
    
    def label_images(self, openai_api_key: str, prompts_dir: str):
        logger.info("extracting images from pdf")
        images_metadata = self.extract_images()
        
        if images_metadata:
            stats = self.get_image_stats()
            logger.info(f"extracted {stats.total_images} images")
            
            # label images with ai if api key is available
            if openai_api_key:
                logger.info("labeling images with AI")
                labeler = ImageLabeler(openai_api_key, 
                                        prompts_dir=prompts_dir)
                labeled_metadata = labeler.label_images_batch(images_metadata)
                
                # save labeled metadata
                Path(self.images_output_dir).mkdir(parents=True, exist_ok=True)
                metadata_path = os.path.join(self.images_output_dir, 'images_metadata_labeled.json')
                labeler.save_labeled_metadata(labeled_metadata, metadata_path)
                
                self.images_metadata = labeled_metadata
                logger.info(f"labeled {len(labeled_metadata)} images")
            
            else:
                logger.warning("openai api key not found, skipping image labeling")
                self.images_metadata = images_metadata
        else:
            logger.info("no images found in pdf")
            self.images_metadata = []

