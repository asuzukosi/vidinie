"""
html processor module
extracts text, structure, and images from HTML documents.
uses BeautifulSoup for HTML parsing.
"""

import os
import json
import hashlib
import io
from pathlib import Path
from typing import List, Any, Optional
from bs4 import BeautifulSoup
from PIL import Image
import requests
from core.utils.logger import get_logger
from datetime import datetime
from core.processors.base import DocumentProcessor
from core.data import (
    ImageMetadata,
    ParsedContent,
    ContentMetadata,
    ContentSection,
)
from core.operations.image_labeler import ImageLabeler
from urllib.parse import urljoin
import random

# setup the html processor logger
logger = get_logger('html_processor')


class HTMLProcessor(DocumentProcessor):
    """
    processor for extracting text, structure, and images from html documents.
    """
    
    def __init__(self, html_content: str, 
                 images_output_dir: str = "temp/images", 
                 original_url: Optional[str] = None,
                 user_instructions: str = ""):
        """
        initialize HTML processor.
        args:
            html_content: html content as string
            images_output_dir: directory to save extracted images
            original_url: original url of the html document
            user_instructions: user instructions to guide AI operations
        """
        self.user_instructions = user_instructions
        if not html_content:
            raise ValueError("html_content must be provided")
        
        self.html_content = html_content
        self.images_output_dir = images_output_dir
        self.soup = None
        self.images_metadata: List[ImageMetadata] = []
        self.original_url = original_url

        # create output directory for images
        Path(images_output_dir).mkdir(parents=True, exist_ok=True)
        
    def __enter__(self):
        """context manager entry."""
        # create instance of beautifulsoup with html content and html.parser parser.
        self.soup = BeautifulSoup(self.html_content, 'html.parser')
        return self
        
    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        """context manager exit."""
        self.soup = None
        self.html_content = None
    
    def extract_text(self) -> str:
        """
        extract all text from the html document.
        returns:
            complete text content of the html document
        """
        if not self.soup:
            raise ValueError("html document not opened. use context manager or call __enter__()")
        
        # remove script and style elements
        for script in self.soup(["script", "style"]):
            script.decompose()
        
        # get text
        text = self.soup.get_text()
        
        # clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        logger.info("exxtracted text from html document")
        return text
    
    def extract_structured_content(self) -> ParsedContent:
        """
        extract text with structure information (headings, paragraphs, sections).
        returns:
            parsed content object
        """
        if not self.soup:
            raise ValueError("html document not opened. use context manager or call __enter__()")
        # extract title
        title = self._extract_title()
        # extract sections based on headings
        sections: List[ContentSection] = self._extract_sections()
        # count "pages" (approximate by major sections)
        total_sections = len([s for s in sections if s.level == 1])
        
        structured_content = ParsedContent()
        structured_content.title = title
        structured_content.sections = sections
        structured_content.total_pages = max(total_sections, 1)
        structured_content.metadata = ContentMetadata(
            title=title,
            creator="html processor",
            producer="html processor",
            creation_date=datetime.now().isoformat(),
            modification_date=None
        )
        return structured_content
    
    def _extract_title(self) -> str:
        """
        extract document title from html.
        returns:
            document title
        """
        # try <title> tag first
        title_tag = self.soup.find('title')
        if title_tag and title_tag.get_text().strip():
            return title_tag.get_text().strip()
        
        # try <h1> tag
        h1_tag = self.soup.find('h1')
        if h1_tag and h1_tag.get_text().strip():
            return h1_tag.get_text().strip()
        
        # try meta title
        meta_title = self.soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title.get('content').strip()
        
        return "untitled document"
    
    def _extract_sections(self) -> List[ContentSection]:
        """
        extract sections from html based on heading tags.
        returns:
            list of sections with title and content
        """
        sections: List[ContentSection] = []
        current_section = None
        
        # find all heading and content elements
        elements = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div'])
        
        for element in elements:
            tag_name = element.name
            # check if it's a heading
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # save previous section if it exists
                if current_section and current_section.content.strip():
                    sections.append(current_section)
                # start new section
                level = int(tag_name[1])  # h1 -> 1, h2 -> 2, etc.
                title = element.get_text().strip()
                current_section = ContentSection()
                current_section.title = title if title else "untitled section"
                current_section.content = ""
                current_section.level = level
            
            elif current_section and tag_name in ['p', 'div']:
                # add content to current section
                text = element.get_text().strip()
                if text:
                    current_section.content += text + "\n\n"
        # add the last section if it exists
        if current_section and current_section.content.strip():
            sections.append(current_section)
        # if no sections found, create one with all content
        if not sections:
            text = self.extract_text()
            sections.append(ContentSection(
                title="content",
                content=text,
                level=1
            ))
        
        logger.info(f"identified {len(sections)} sections")
        return sections
    
    def extract_images(self, min_width: int = 100, min_height: int = 100, max_images: int = 10) -> List[ImageMetadata]:
        """
        extract all images from the html document.
        """
        if not self.soup:
            raise ValueError("html document not opened. use context manager or call __enter__()")
        logger.info("starting image extraction from html content")
        # initialize image count and list
        image_count = 0
        images_list = []
        # find all img tags
        img_tags = self.soup.find_all('img')
        # iterate over img tags
        for img_index, img_tag in enumerate(img_tags):
            try:
                # get image source
                src = img_tag.get('src') or img_tag.get('data-src') or ''
                if not src:
                    continue
                
                # if path is relative, check if we have the original url to resolve it
                if not src.startswith(('http://', 'https://')):
                    if self.original_url:
                        img_url = urljoin(self.original_url, src)
                        logger.info(f"Resolved relative image URL to: {img_url}")
                    else:
                        logger.warning(f"Skipping relative image URL (cannot resolve without source path): {src}")
                        continue
                else:
                    img_url = src
                
                # try to download image from URL
                try:
                    response = requests.get(img_url, timeout=10)
                    response.raise_for_status()
                    image_bytes = response.content
                except Exception as e:
                    logger.warning(f"Could not load image {img_url}: {str(e)}")
                    continue
                # try to get image dimensions
                try:
                    with Image.open(io.BytesIO(image_bytes)) as pil_img:
                        width, height = pil_img.size
                        format_name = pil_img.format
                        mode = pil_img.mode
                except Exception as e:
                    logger.warning(f"Could not read image metadata: {str(e)}")
                    continue
                # filter by size
                if width < min_width or height < min_height:
                    logger.debug(f"Skipping small image: {width}x{height}")
                    continue
                # generate unique filename  
                image_hash = hashlib.md5(image_bytes).hexdigest()[:10]
                ext = format_name.lower() if format_name else 'jpg'
                filename = f"img_html_{img_index}_{image_hash}.{ext}"
                filepath = os.path.join(self.images_output_dir, filename)                
                # save image
                with open(filepath, "wb") as img_file:
                    img_file.write(image_bytes)
                # try to get alt text
                alt_text = img_tag.get('alt', '')
                # store metadata
                image_metadata = ImageMetadata(
                    filename=filename,
                    filepath=filepath,
                    label=alt_text,
                )
                # add metadata to list
                images_list.append(image_metadata)
                image_count += 1
                # log image extraction
                logger.info(f"extracted image {image_count}: {filename} ({width}x{height})")
            # handle exceptions
            except Exception as e:
                logger.error(f"Error extracting image {img_index}: {str(e)}")
                continue
        # limit the number of images extracted
        if len(images_list) > max_images:
            images_list = random.sample(images_list, max_images)
        # update the images metadata list
        self.images_metadata = images_list
        # log total number of images extracted
        logger.info(f"extracted {image_count} images from html document")
        # save metadata to json
        self._save_image_metadata()
        # return images data
        return self.images_metadata
    
    def _extract_text_context(self, img_tag, context_chars: int = 500) -> str:
        """
        extract text near an image in the html.
        args:
            img_tag: BeautifulSoup image tag
            context_chars: number of characters to extract
        returns:
            text context surrounding the image
        """
        try:
            # get parent element and extract text
            parent = img_tag.find_parent(['article', 'section', 'div', 'p'])
            if parent:
                text = parent.get_text().strip()
                if len(text) > context_chars:
                    return text[:context_chars]
                return text.strip()
            return img_tag.get('alt', '').strip()
        except Exception as e:
            logger.debug(f"could not extract text context: {str(e)}")
            return ""
    
    def _save_image_metadata(self):
        """save image metadata to json file."""
        metadata_path = os.path.join(self.images_output_dir, "images_metadata.json")
        # save metadata to json file
        with open(metadata_path, 'w') as f:
            data = [img.model_dump(mode="json") for img in self.images_metadata]
            json.dump(data, f, indent=2, ensure_ascii=False)
        # log saved metadata
        logger.info(f"Saved metadata to {metadata_path}")
        
    def label_images(self):
        logger.info("labeling images")
        images_metadata = self.extract_images()
        
        if images_metadata:
            logger.info(f"extracted {len(images_metadata)} images")
            
        logger.info("labeling images")
        labeler = ImageLabeler(user_instructions=self.user_instructions)
        labeled_metadata = labeler.label_images_batch(images_metadata)
        self.images_metadata = labeled_metadata
        logger.info(f"labeled {len(labeled_metadata)} images")

