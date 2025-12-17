"""
Context processor utility
Processes large context and splits it into smaller chunks with summaries.
"""

from typing import List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from openai import OpenAI
from utils.logger import get_logger
from core.pipeline_data import ContextChunk
logger = get_logger(__name__)


class ContextProcessor:
    """
    process large context and split it into smaller chunks.
    args:
        context: the large context to process
        api_key: openai api key
        document_title: the title of the document
        chunk_length: the length of each chunk
        split_by: the character to split the context by
    returns:
        list of smaller chunks with summaries
    """
    
    def __init__(self, context: str, api_key: str, document_title: str = "Untitled Document", 
                 chunk_length: int = 5000, split_by: str = '\n', prompts_dir: Optional[Path] = None):
        """
        initialize large context processor.
        args:
            context: the large context to process
            api_key: openai api key
            document_title: the title of the document
            chunk_length: the length of each chunk
            split_by: the character to split the context by
            prompts_dir: path to prompts directory
        """
        self.context = context
        self.document_title = document_title
        self.chunk_length = chunk_length
        self.split_by = split_by
        self.client = OpenAI(api_key=api_key)
        
        # initialize jinja2 environment for prompt templates
        if prompts_dir is None:
            from utils.config_loader import get_config
            config = get_config()
            prompts_dir = config.get_prompts_directory()
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def _generate_summary(self, prompt: str) -> str:
        """
        generate a summary of the context.
        args:
            prompt: the text chunk to summarize
        returns:
            summary of the context
        """
        # load system prompt from template
        system_template = self.jinja_env.get_template('bullet_summary_system.j2')
        system_prompt = system_template.render(document_title=self.document_title)
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response.choices[0].message.content

    def _split_context(self) -> List[str]:
        """
        split the context into smaller chunks.
        returns:
            list of smaller chunks
        """
        
        all_segments: List[str] = self.context.split(self.split_by)
        chunks: List[str] = []
        current_chunk: str = ""
        for segment in all_segments:
            if len(current_chunk) + len(segment) > self.chunk_length:
                chunks.append(current_chunk)
                current_chunk = ""
            current_chunk += segment + self.split_by
        if current_chunk:
            chunks.append(current_chunk)
        return chunks
    
    def get_chunks(self) -> List[ContextChunk]:
        """
        get the chunks of the context with summaries.
        returns:
            list of ContextChunk objects
        """
        chunks: List[str] = self._split_context()
        data: List[ContextChunk] = []
        for chunk in chunks:
            summary: str = self._generate_summary(chunk)
            data.append(ContextChunk(chunk=chunk, summary=summary))
        return data

