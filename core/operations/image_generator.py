"""
vidinie image generator module
"""
from typing import Optional, List
from pathlib import Path
import os
from core.clients.image_engine import ImagePrompt, generate_images
from core.utils.logger import get_logger
from core.data import VideoSegment, ImageSource
from retry import retry

logger = get_logger("image_generator")


class ImageGenerator:
    """generate images using ai models."""
    
    def __init__(self, output_dir: str):
        """
        initialize image generator.
        """
        self.output_dir = Path(output_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
    @retry(tries=3, delay=1, backoff=2)
    async def _generate_for_segment(self, 
                             index: int, 
                             output_dir: str,
                             segment: VideoSegment) -> VideoSegment:
        """
        generate an image for a segment.
        """
        prompts = []
        prompt_indices = []
        for idx, image in enumerate(segment.images):
            if image.source == ImageSource.AI_GENERATED:
                prompt = ImagePrompt(
                    target=image.query,
                    aesthetics=[],
                    exemptions=[],
                    output_path=os.path.join(output_dir, f"segment_{index}_image_{idx}.png")
                )
                prompts.append(prompt)
                prompt_indices.append(idx)
        
        if prompts:
            paths = await generate_images(prompts)
            for idx, path in zip(prompt_indices, paths):
                segment.images[idx].path = path
                segment.images[idx].source = 'ai_generated'
        return segment
    
    async def generate_for_segments(self, 
                              pipeline_id: Optional[str],
                              segments: List[VideoSegment]
                              ) -> List[VideoSegment]:
        """
        generate images for all segments in the pipeline.
        """
        output_dir = os.path.join(self.output_dir, pipeline_id)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            for i, segment in enumerate(segments, 1):
                segment = await self._generate_for_segment(index=i, 
                                                     output_dir=output_dir, 
                                                     segment=segment)
            return segments
        except Exception as e:
            logger.error(f"error generating images for segments: {str(e)}", exc_info=True)
            return segments