from anthropic import Anthropic
from typing import Any, List, Callable
import asyncio
import os
# import sys
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import base64
from urllib.parse import urlparse

import httpx
from retry import retry
from dotenv import load_dotenv
from core.utils.logger import get_logger
from pydantic import BaseModel


load_dotenv()
logger = get_logger("reasoning_engine")


class ReasoningPrompt(BaseModel):
    """reasoning prompts with task and optional images."""
    task: str
    images: List[str] = [] # list of image paths or urls


class ReasoningEngine:
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("anthropic API key is required")
        logger.info(f"initializing reasoning engine with anthropic")
        self.client = Anthropic(api_key=api_key)

    @staticmethod
    def _is_url(image_path: str) -> bool:
        """
        check if a string is a valid url.
        """
        try:
            result = urlparse(image_path)
            return all([result.scheme, result.netloc]) # True if it's a url by checking if scheme and netloc are present, False otherwise
        except Exception: # if any error occurs, return False
            return False

    @staticmethod
    def _encode_image_to_base64(image_path: str) -> str:
        """
        encode an image file or URL to a base64 string.
        """
        if ReasoningEngine._is_url(image_path):
            # fetch image from URL
            response = httpx.get(image_path)
            response.raise_for_status()
            return base64.b64encode(response.content).decode("utf-8")
        else:
            # check if file exists before attempting to read
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")

    @staticmethod
    def _get_mime(image_path: str) -> str:
        """
        extract the correct mime type based on file extension or url.
        """
        if ReasoningEngine._is_url(image_path):
            # extract extension from URL path
            parsed = urlparse(image_path)
            ext = os.path.splitext(parsed.path)[1].lower()
        else:
            ext = os.path.splitext(image_path)[1].lower()
        
        return {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }.get(ext, 'image/jpeg')

    @retry(tries=5, delay=2, backoff=2)
    def _reason(self, system_prompt: str, prompt: ReasoningPrompt, *, schema: Any) -> str:
        logger.info("reasoning task started")
        content =[]
        if prompt.images:
            for image in prompt.images:
                image_data = self._encode_image_to_base64(image)
                image_media_type = self._get_mime(image)
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_media_type,
                        "data": image_data,
                    },
                })
        content.append({"type": "text", "text": prompt.task})
        response = self.client.beta.messages.parse(
            model="claude-sonnet-4-5",
            system=system_prompt,
            max_tokens=16384,
            betas=["structured-outputs-2025-11-13"],
            messages=[{"role": "user", "content": content}],
            output_format=schema,
        )
        logger.info(f"reasoning task completed")
        return response.parsed_output
    
    async def _reason_async(self, system_prompt: str, prompt: ReasoningPrompt, *, schema: Any) -> str:
        # run the synchronous blocking api call in a thread pool to enable parallelism
        return await asyncio.to_thread(self._reason, system_prompt, prompt, schema=schema)
    

    async def reason(self, system_prompt: str, prompts: List[ReasoningPrompt], 
               *, schema: Any, combine_function: Callable[[List[Any]], Any] = None) -> Any:
        """
        reason engine function takes a list of prompts and a system prompt and runs all in parallel
        then returns the combined result of the prompts
        """
        tasks = [self._reason_async(system_prompt, prompt, schema=schema) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        return combine_function(results) if combine_function else results


async def reason(system_prompt: str, prompts: List[ReasoningPrompt], *, schema: Any, combine_function: Callable[[List[Any]], Any] = None) -> Any:
    """async module-level function for reasoning."""
    reasoning_engine = ReasoningEngine()
    return await reasoning_engine.reason(system_prompt, prompts, schema=schema, combine_function=combine_function)