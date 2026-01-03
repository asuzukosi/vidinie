"""
content-related models for video pipeline.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class VideoPipelineContentSection(BaseModel):
    """
    parsed content section from the document for video pipeline.
    """
    title: Optional[str] = None
    content: Optional[str] = None
    level: Optional[int] = None


class VideoPipelineContentMetadata(BaseModel):
    """
    parsed content metadata from the document for video pipeline.
    """
    title: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None


class VideoPipelineParsedContent(BaseModel):
    """
    parsed content from the document for video pipeline.
    """
    title: Optional[str] = None
    total_pages: Optional[int] = None
    sections: List[VideoPipelineContentSection] = Field(default_factory=list)
    metadata: Optional[VideoPipelineContentMetadata] = None


class VideoPipelineContextChunk(BaseModel):
    """
    context chunk with summary for video pipeline.
    """
    chunk: str
    summary: str


class VideoPipelineContextProcessor(BaseModel):
    """
    context processor information for video pipeline.
    """
    document_title: str
    chunk_length: int
    split_by: str
    total_chunks: int
    total_content_length: int

