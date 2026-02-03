"""
vidinie stock fetcher utilities module
utility functions for fetching stock images and videos from pexels api.
"""

import os
import httpx
from typing import Optional, Literal, Union
from pathlib import Path
import hashlib
from pydantic import BaseModel
from retry import retry
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.utils.logger import get_logger
from core.utils.video_utils import convert_mp4_to_webm_and_delete_original

logger = get_logger(__name__)


class StockImageResult(BaseModel):
    """result from fetching a stock image."""
    filename: str
    filepath: str
    source: Literal["pexels"] = "pexels"
    query: str


class StockVideoResult(BaseModel):
    """result from fetching a stock video."""
    filename: str
    filepath: str
    source: Literal["pexels"] = "pexels"
    query: str


async def fetch_from_pexels_async(
    query: str,
    api_key: str,
    output_dir: str,
    media_type: Literal["image", "video"] = "image",
    output_path: Optional[str] = None
) -> Optional[Union[StockImageResult, StockVideoResult]]:
    """
    fetch image or video from pexels.
    """
    try:
        # ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        if media_type == "image":
            return await _fetch_image_from_pexels_async(query, api_key, output_dir, output_path)
        else:
            return await _fetch_video_from_pexels_async(query, api_key, output_dir, output_path)
            
    except Exception as e:
        logger.error(f"Error fetching {media_type} from Pexels: {str(e)}")
        return None


@retry(tries=5, delay=2, backoff=2)
async def _fetch_image_from_pexels_async(
    query: str,
    api_key: str,
    output_dir: str,
    output_path: Optional[str] = None
) -> Optional[StockImageResult]:
    """async internal function to fetch image from pexels."""
    pexels_base_url = "https://api.pexels.com/v1"
    
    # search for images
    search_url = f"{pexels_base_url}/search"
    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "per_page": 1,
        "orientation": "landscape"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('photos'):
            logger.warning(f"No Pexels results for query: {query}")
            return None
        
        photo = data['photos'][0]
        
        # download image (use large size)
        image_url = photo['src']['large']
        image_response = await client.get(image_url)
        image_response.raise_for_status()
        
        # use provided path or generate filename
        if output_path:
            filepath = output_path
            filename = os.path.basename(output_path)
        else:
            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            filename = f"pexels_{query_hash}_{photo['id']}.jpg"
            filepath = os.path.join(output_dir, filename)
        
        # save image
        with open(filepath, 'wb') as f:
            f.write(image_response.content)
        
        logger.info(f"Downloaded Pexels image for '{query}': {filename}")
        
        return StockImageResult(
            filename=filename,
            filepath=filepath,
            query=query
        )


@retry(tries=5, delay=2, backoff=2)
async def _fetch_video_from_pexels_async(
    query: str,
    api_key: str,
    output_dir: str,
    output_path: Optional[str] = None
) -> Optional[StockVideoResult]:
    """async internal function to fetch video from pexels."""
    pexels_base_url = "https://api.pexels.com/videos"
    
    # search for videos
    search_url = f"{pexels_base_url}/search"
    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "per_page": 1,
        "orientation": "landscape"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('videos'):
            logger.warning(f"No Pexels video results for query: {query}")
            return None
        
        video = data['videos'][0]
        
        # find the SD quality video file to save cost and time (prefer SD, fallback to first)
        video_file = None
        for vf in video.get('video_files', []):
            if vf.get('quality') == 'sd':
                video_file = vf
                break
        
        if not video_file:
            video_file = video['video_files'][0]
        
        # download video
        video_url = video_file['link']
        async with client.stream('GET', video_url) as video_response:
            video_response.raise_for_status()
            
            # use provided path or generate filename
            if output_path:
                filepath = output_path
                filename = os.path.basename(output_path)
            else:
                query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
                filename = f"pexels_{query_hash}_{video['id']}.mp4"
                filepath = os.path.join(output_dir, filename)
            
            # save video
            with open(filepath, 'wb') as f:
                async for chunk in video_response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
        
        # validate video file after download
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            logger.error(f"downloaded video file is empty: {filename}")
            os.remove(filepath)
            return None
        
        # check if file is too small
        if file_size < 1024:  # less than 1KB is suspicious
            logger.warning(f"downloaded video file is very small ({file_size} bytes): {filename}, may be corrupted")
            os.remove(filepath)
            return None
        
        logger.info(f"downloaded pexels video for '{query}': {filename} ({file_size} bytes)")
        webm_path = await convert_mp4_to_webm_and_delete_original(filepath)
        return StockVideoResult(
            filename=os.path.basename(webm_path),
            filepath=webm_path,
            query=query
        )