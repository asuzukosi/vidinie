"""
vidinie image generator module
"""
from typing import Optional, List
from pathlib import Path
import os
from core.clients.image_engine import ImagePrompt, generate_image
from core.utils.logger import get_logger
from core.data import VideoSegment, ImageSource

logger = get_logger("image_generator")


class ImageGenerator:
    """generate images using ai models."""
    
    def __init__(self, output_dir: str):
        """
        initialize image generator.
        """
        self.output_dir = Path(output_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
    def _generate_for_segment(self, 
                             index: int, 
                             output_dir: str,
                             segment: VideoSegment) -> VideoSegment:
        """
        generate an image for a segment.
        """
        for idx, image in enumerate(segment.images):
            if image.source == ImageSource.AI_GENERATED:
                prompt = ImagePrompt(
                    target=image.query,
                    aesthetics=[],
                    exemptions=[],
                    output_path=os.path.join(output_dir, f"segment_{index}_image_{idx}.png")
                )
                path = generate_image(prompt)
                image.path = path
                image.source = 'ai_generated'
        return segment
    
    def generate_for_segments(self, 
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
                segment = self._generate_for_segment(index=i, 
                                                     output_dir=output_dir, 
                                                     segment=segment)
            return segments
        except Exception as e:
            logger.error(f"error generating images for segments: {str(e)}", exc_info=True)
            return segments