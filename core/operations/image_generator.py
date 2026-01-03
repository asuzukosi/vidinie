"""
vidinie image generator module
generates images using ai models (dall-e) for video segments.
"""

import os
import requests
from typing import Optional, List
from pathlib import Path
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.utils.logger import get_logger
from core.utils.config_loader import get_config
from core.data import VideoPipelineSegment, VideoPipelineSegmentImage

logger = get_logger(__name__)


class ImageGenerator:
    """generate images using ai models for video segments."""
    
    def __init__(self, api_key: Optional[str] = None, 
                 model: str = "dall-e-3",
                 quality: str = "standard",
                 size: str = "1024x1024",
                 output_dir: str = "temp/ai_images",
                 prompts_dir: Optional[Path] = None):
        """
        initialize image generator.
        
        args:
            api_key: openai api key
            model: dalle model to use ("dall-e-2" or "dall-e-3")
            quality: image quality ("standard" or "hd" for dall-e-3)
            size: image size (dall-e-3: "1024x1024", "1792x1024", "1024x1792")
            output_dir: directory to save generated images
            prompts_dir: path to prompts directory
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("openai api key required for image generation")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.quality = quality
        self.size = size
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # initialize jinja2 environment for prompt templates
        if prompts_dir is None:
            config = get_config()
            prompts_dir = config.get_prompts_directory()
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def generate_image(self, segment: VideoPipelineSegment, output_filename: Optional[str] = None) -> Optional[VideoPipelineSegmentImage]:
        """
        generate an image for a video segment.
        
        args:
            segment: segment dictionary with title, purpose, visual_keywords, etc.
            output_filename: optional custom filename (defaults to segment-based name)
        
        returns:
            image metadata dictionary with filepath, or None if failed
        """
        try:
            # create prompt from template
            prompt = self._create_image_prompt(segment)
            
            logger.info(f"generating image for segment: {segment.get('title', 'unknown')}")
            logger.debug(f"image prompt: {prompt}")
            
            # generate image using dall-e
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=self.size,
                quality=self.quality,
                n=1
            )
            
            # get image url
            image_url = response.data[0].url
            
            # download image
            if not output_filename:
                # create filename from segment title
                safe_title = "".join(c for c in segment.get('title', 'image') if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_title = safe_title.replace(' ', '_')[:50]  # limit length
                output_filename = f"ai_{safe_title}.png"
            
            output_path = self.output_dir / output_filename
            
            # download and save image
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(img_response.content)
            
            logger.info(f"generated image saved to: {output_path}")
            
            return VideoPipelineSegmentImage(
                source='ai_generated',
                query=prompt,
                path=str(output_path)
            )
            
        except Exception as e:
            logger.error(f"failed to generate image: {str(e)}", exc_info=True)
            return None
    
    def _create_image_prompt(self, segment: VideoPipelineSegment) -> str:
        """
        create image generation prompt from segment data.
        args:
            segment: video segment
        
        returns:
            prompt string for image generation
        """
        # load and render template
        template = self.jinja_env.get_template('image_generation_instruction.j2')
        prompt = template.render(segment=segment.model_dump(mode="json"))
        
        return prompt.strip()
    
    def generate_for_segments(self, segments: List[VideoPipelineSegment], 
                              pipeline_id: Optional[str] = None) -> List[VideoPipelineSegment]:
        """
        generate images for multiple segments.
        only generates images for segments that specify ai_generated source.
        args:
            segments: list of video segments
            pipeline_id: optional pipeline id for organizing output
        returns:
            updated segments with generated segment image
        """
        original_output_dir = self.output_dir
        
        if pipeline_id:
            # create subdirectory for this pipeline
            pipeline_dir = self.output_dir / pipeline_id
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            self.output_dir = pipeline_dir
        
        try:
            generated_count = 0
            for i, segment in enumerate(segments, 1):
                # check if segment needs ai-generated image
                image_info = segment.image
                if image_info and image_info.source == 'ai_generated':
                    logger.info(f"generating ai image for segment {i}/{len(segments)}: {segment.title}")
                    output_filename = f"segment_{i:02d}_{segment.title[:30]}.png"
                    output_filename = "".join(c for c in output_filename if c.isalnum() or c in (' ', '-', '_', '.'))
                    logger.info(f"output filename: {output_filename}")
                    segment_image = self.generate_image(segment, output_filename)
                    if segment_image:
                        # update segment with generated image path
                        segment.image = segment_image
                        generated_count += 1
                    else:
                        logger.warning(f"failed to generate image for segment: {segment.title}")
                        # remove ai_generated source if generation failed
                        segment.image = None
            logger.info(f"generated {generated_count} ai images for {len(segments)} segments")
        finally:
            # restore original output directory
            self.output_dir = original_output_dir
        
        return segments
    
    def is_available(self) -> bool:
        """
        check if image generation is available.
        returns:
            True if api key is configured
        """
        return bool(self.api_key)

