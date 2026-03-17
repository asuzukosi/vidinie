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
from core.data.segment_models import SegmentClip, SegmentImage
from core.data.enums import ImageSource, VideoSource

logger = get_logger(__name__)


class StockFetcher:
    """fetch stock images and videos from pexels api."""
    def __init__(
        self,
        output_dir: str = "temp/stock_images",
        video_output_dir: str = None
    ):
        """
        initialize stock fetcher.
        output_dir: directory for stock images
        video_output_dir: directory for stock videos (if None, uses output_dir)
        """
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        if not self.pexels_key:
            raise ValueError("Pexels API key is not set")
        self.output_dir = output_dir
        self.video_output_dir = video_output_dir
        # create output directories
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        if video_output_dir:
            Path(video_output_dir).mkdir(parents=True, exist_ok=True)

    def _generate_file_path(self, query: str, 
                            media_item: Union[SegmentImage, SegmentClip], 
                            index: int,
                            video_output_dir: str = None) -> str:
        """
        generate a file path for stock media based on the media item type.
        Videos go to clips/stock_videos, images go to images/stock_images.
        """
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        extension = ".jpg" if isinstance(media_item, SegmentImage) else ".mp4"
        filename = f"pexels_{query_hash}_{index}{extension}"
        
        # Use separate directory for videos if provided
        if isinstance(media_item, SegmentClip) and video_output_dir:
            return os.path.join(video_output_dir, filename)
        
        return os.path.join(self.output_dir, filename)
    
    async def _fetch_and_update_path(
        self,
        query: str,
        output_path: str,
        media_item: Union[SegmentImage, SegmentClip]
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
        
        # process all clips in the segment
        if segment.clips:
            for clip_idx, clip in enumerate(segment.clips):
                # only fetch if it's a stock video with a query and no path yet
                if (clip.source == VideoSource.STOCK and 
                    clip.query and 
                    not clip.path):
                    # generate path before fetching (videos go to video_output_dir)
                    output_path = self._generate_file_path(clip.query, clip, clip_idx, self.video_output_dir)
                    tasks.append(self._fetch_and_update_path(
                        clip.query, output_path, clip
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

