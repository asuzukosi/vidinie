"""
Abstract base class for the input document processors.
"""

from abc import ABC, abstractmethod
from typing import List
from core.data import (
    ParsedContent,
    ImageMetadata,
)

class DocumentProcessor(ABC):
    @abstractmethod
    def __enter__(self):
        """context manager entry"""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """context manager exit. must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def extract_text(self) -> str:
        """
        extract all text from the document.
        returns:
            complete text content of the document as a string
        """
        pass
    
    @abstractmethod
    def extract_structured_content(self) -> ParsedContent:
        """
        extract text with structure information (headings, paragraphs, sections).
        returns:
            parsed content object
        """
        pass
    
    @abstractmethod
    def extract_images(self, min_width: int = 100, min_height: int = 100) -> List[ImageMetadata]:
        """
        extract all images from the document.
        returns:
            list of image metadata objects
        """
        pass