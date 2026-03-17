"""
api operations module

this module contains operation functions that wrap core classes with API-specific
functionality like broadcast messages, database updates, and error handling.

the core team maintains the classes in core/operations/, while the api team
handles the operation functions here with API integration.
"""

from api.operations.document_operations import (
    process_pdf_document,
    process_html_document,
    process_document,
)
from api.operations.content_operations import (
    process_content,
    add_section_to_content,
    delete_section_from_content,
    add_segment_to_outline,
    delete_segment_from_outline,
)
from api.operations.image_operations import (
    add_image_to_pipeline,
    delete_image_from_pipeline,
)
from api.operations.script_operations import generate_scripts
from api.operations.video_operations import generate_video

__all__ = [
    # document operations
    'process_pdf_document',
    'process_html_document',
    'process_document',
    # content operations
    'process_content',
    'add_section_to_content',
    'delete_section_from_content',
    'add_segment_to_outline',
    'delete_segment_from_outline',
    # image operations
    'add_image_to_pipeline',
    'delete_image_from_pipeline',
    # script operations
    'generate_scripts',
    # video operations
    'generate_video',
]
