"""
vidinie stock image fetcher module
fetches stock images from unsplash and pexels apis.
"""

import os
from typing import Optional, List, Dict
from pathlib import Path
from utils.logger import get_logger
from utils.stock_image_utils import fetch_from_unsplash, fetch_from_pexels

logger = get_logger(__name__)


class StockImageFetcher:
    """fetch stock images from free apis."""
    
    def __init__(self, unsplash_key: Optional[str] = None, 
                 pexels_key: Optional[str] = None,
                 output_dir: str = "temp/stock_images"):
        """
        initialize stock image fetcher.
        args:
            unsplash_key: unsplash api access key
            pexels_key: pexels api key
            output_dir: directory to save images
        """
        self.unsplash_key = unsplash_key or os.getenv('UNSPLASH_ACCESS_KEY')
        self.pexels_key = pexels_key or os.getenv('PEXELS_API_KEY')
        self.output_dir = output_dir
        
        # create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def is_available(self) -> Dict[str, bool]:
        """
        check which providers are available.
        returns:
            dictionary of provider availability
        """
        return {
            'unsplash': bool(self.unsplash_key),
            'pexels': bool(self.pexels_key)
        }
    
    def fetch_image(self, query: str, provider: str = "unsplash") -> Optional[Dict]:
        """
        fetch a single stock image for a query.
        args:
            query: search query
            provider: "unsplash" or "pexels"
        returns:
            image metadata dictionary or None if failed
        """
        if provider == "unsplash" and self.unsplash_key:
            return fetch_from_unsplash(query, self.unsplash_key, self.output_dir)
        elif provider == "pexels" and self.pexels_key:
            return fetch_from_pexels(query, self.pexels_key, self.output_dir)
        else:
            logger.warning(f"{provider} API key not available")
            return None
    
    def fetch_for_segments(self, segments: List[Dict], preferred_provider: str = "unsplash") -> List[Dict]:
        """
        fetch stock images for video segments.
        args:
            segments: list of segment dictionaries with 'stock_image_query'
            preferred_provider: "unsplash" or "pexels"
        returns:
            updated segments with stock_image metadata
        """
        logger.info(f"fetching stock images for {len(segments)} segments")
        
        # determine provider order
        providers = []
        all_providers = ["unsplash", "pexels"]
        if preferred_provider in all_providers:
            providers.append(preferred_provider)
        providers += [p for p in all_providers if p != preferred_provider]
        
        for i, segment in enumerate(segments, 1):
            query = segment.get('stock_image_query')
            if not query:
                logger.debug(f"Segment {i} has no stock image query: {segment['title']}")
                continue
            
            image_data = None
            for provider in providers:
                try:
                    image_data = self.fetch_image(query, provider)
                    segment['stock_image'] = image_data
                    break
                except Exception as e:
                    logger.error(f"Error fetching stock image for segment {i} with provider {provider}: {str(e)}")
                    continue   

        return segments 
