"""
vidinie stock fetcher module
fetches stock images and videos from pexels api.
"""

import os
import asyncio
import hashlib
from typing import List, Union
from pathlib import Path
from core.utils.logger import get_logger
from core.utils.stock_fetcher import (
    fetch_from_pexels_async,
)
from core.data import VideoSegment
from core.data.segment_models import SegmentVideoClip, SegmentImage
from core.data.enums import ImageSource, VideoSource

logger = get_logger(__name__)


class StockFetcher:
    """fetch stock images and videos from pexels api."""
    def __init__(
        self,
        output_dir: str = "temp/stock_images"
    ):
        """
        initialize stock fetcher.
        """
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        if not self.pexels_key:
            raise ValueError("Pexels API key is not set")
        self.output_dir = output_dir
        # create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def _generate_file_path(self, query: str, 
                            media_item: Union[SegmentImage, SegmentVideoClip], 
                            index: int) -> str:
        """
        generate a file path for stock media based on the media item type.
        """
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        extension = ".jpg" if isinstance(media_item, SegmentImage) else ".mp4"
        filename = f"pexels_{query_hash}_{index}{extension}"
        return os.path.join(self.output_dir, filename)
    
    async def _fetch_and_update_path(
        self,
        query: str,
        output_path: str,
        media_item: Union[SegmentImage, SegmentVideoClip]
    ) -> bool:
        """
        fetch stock media and save to the specified path.
        """
        # determine media type from the object type
        media_type = "image" if isinstance(media_item, SegmentImage) else "video"
        result = await fetch_from_pexels_async(
            query, 
            self.pexels_key, 
            self.output_dir, 
            media_type=media_type,
            output_path=output_path
        )
        if result and os.path.exists(output_path):
            media_item.path = output_path
            return True
        
        return False
    
    async def _fetch_for_segment_async(self, segment: VideoSegment) -> VideoSegment:
        """
        fetch all stock images and video clips for a single segment.
        """
        # collect all fetch tasks for this segment
        tasks = []
        
        # process all images in the segment
        if segment.images:
            for img_idx, image in enumerate(segment.images):
                # only fetch if it's a stock image with a query and no path yet
                if (image.source == ImageSource.STOCK and 
                    image.query and 
                    not image.path):
                    # generate path before fetching
                    output_path = self._generate_file_path(image.query, image, img_idx)
                    tasks.append(self._fetch_and_update_path(
                        image.query, output_path, image
                    ))
        
        # process all video clips in the segment
        if segment.video_clips:
            for clip_idx, video_clip in enumerate(segment.video_clips):
                # only fetch if it's a stock video with a query and no path yet
                if (video_clip.source == VideoSource.STOCK and 
                    video_clip.query and 
                    not video_clip.path):
                    # generate path before fetching
                    output_path = self._generate_file_path(video_clip.query, video_clip, clip_idx)
                    tasks.append(self._fetch_and_update_path(
                        video_clip.query, output_path, video_clip
                    ))
        
        # execute all fetches for this segment in parallel
        await asyncio.gather(*tasks, return_exceptions=True)
        return segment
    
    async def fetch_for_segments_async(
        self,
        segments: List[VideoSegment],
    ) -> List[VideoSegment]:
        """
        fetch stock images/videos for video segments in parallel.
        """
        logger.info(f"fetching stock images and videos for {len(segments)} segments")

        # create one task per segment
        tasks = [self._fetch_for_segment_async(segment) for segment in segments]
        # execute all segment tasks in parallel
        await asyncio.gather(*tasks, return_exceptions=True)
        return segments

