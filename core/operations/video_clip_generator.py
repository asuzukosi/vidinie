"""
vidinie video clip generator module
generates ai video clips for segments using video engine.
"""
from typing import Optional, List
from pathlib import Path
import os
from core.clients.video_engine import VideoPrompt, generate_videos
from core.utils.logger import get_logger
from core.data import VideoSegment, VideoSource

logger = get_logger("video_clip_generator")


class VideoClipGenerator:
    """generate ai video clips for segments using video engine."""
    
    def __init__(self, output_dir: str):
        """
        initialize video clip generator.
        """
        self.output_dir = Path(output_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
    async def _generate_for_segment(self, 
                             index: int, 
                             output_dir: str,
                             segment: VideoSegment) -> VideoSegment:
        """
        generate ai video clips for a segment.
        """
        if not segment.video_clips:
            return segment
            
        # generate videos for all video clips in the segment
        prompts = []
        prompt_indices = []
        for idx, clip in enumerate(segment.video_clips):
            if clip.source == VideoSource.AI_GENERATED:
                prompt = VideoPrompt(
                    target=clip.query,
                    aesthetics=[],
                    exemptions=[],
                    output_path=os.path.join(output_dir, f"segment_{index}_video_{idx}.mp4")
                )
                prompts.append(prompt)
                prompt_indices.append(idx)
        
        if prompts:
            paths = await generate_videos(prompts)
            for idx, path in zip(prompt_indices, paths):
                segment.video_clips[idx].path = path
                segment.video_clips[idx].source = VideoSource.AI_GENERATED
        return segment
    
    async def generate_for_segments(self, 
                              pipeline_id: Optional[str],
                              segments: List[VideoSegment]
                              ) -> List[VideoSegment]:
        """
        generate ai video clips for all segments in the pipeline.
        """
        output_dir = os.path.join(self.output_dir, pipeline_id) if pipeline_id else str(self.output_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            for i, segment in enumerate(segments, 1):
                segment = await self._generate_for_segment(index=i, 
                                                     output_dir=output_dir, 
                                                     segment=segment)
            return segments
        except Exception as e:
            logger.error(f"error generating video clips for segments: {str(e)}", exc_info=True)
            return segments
