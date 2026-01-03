"""
document processors module
provides abstract base class and implementations for processing different document types.
"""

from core.processors.base import DocumentProcessor
from core.processors.pdf_processor import PDFProcessor
from core.processors.html_processor import HTMLProcessor

__all__ = ['DocumentProcessor', 'PDFProcessor', 'HTMLProcessor']

