"""
vidinie unified video generator
creates presentation-style explainer videos with:
- slide backgrounds (gradient, solid, or images)
- text overlays synchronized with voiceover
- image displays (PDF and stock images from content analysis)
- smooth transitions between segments
- title and end cards
"""

import os
from typing import Dict, Optional
import numpy as np

# pillow 10.0.0+ compatibility fix for moviepy
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import (
    VideoClip, ImageClip, AudioFileClip,
    concatenate_videoclips
)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout

from utils.video_utils import VideoUtils
from utils.font_loader import FontLoader
from utils.logger import get_logger
from utils.config_loader import Config

logger = get_logger("video_generator")


class VideoGenerator:
    """unified video generator based on slideshow style."""
    
    def __init__(self, config: Config):
        """
        initialize video generator.
        args:
            config: configuration object
        """
        self.config = config
        resolution = config.get('video.resolution', [1920, 1080])
        self.width = resolution[0]
        self.height = resolution[1]
        self.fps = config.get('video.fps', 30)
        
        self.transition_duration = config.get('styles.slideshow.transition_duration', 0.5)
        self.background_type = config.get('styles.slideshow.background_type', 'gradient')
        self.enable_animations = config.get('styles.slideshow.enable_animations', False)
        
        # initialize font loader
        self.font_loader = FontLoader(config) # TODO: allow for setting of multiple font folders to load from
        VideoUtils.set_font_loader(self.font_loader)
        # video title will be set when generate_video is called
        self.video_title = "Untitled"
        logger.info(f"initialized video generator: {self.width}x{self.height} @ {self.fps}fps")
        # log available fonts
        available_fonts = self.font_loader.list_available_fonts()
        if available_fonts:
            logger.info(f"available fonts: {', '.join(available_fonts)}")
    
    def generate_video(self, script_with_audio: Dict, output_path: str) -> str:
        """
        generate video from script and audio data.
        args:
            script_with_audio: script data with audio files
            output_path: path to save output video
        returns:
            path to generated video
        """
        logger.info("starting video generation")
        clips = []
        
        # store video title for use in all segments
        self.video_title = script_with_audio.get('title', 'Untitled')
        
        # create title card
        title_clip = self._create_title_card(self.video_title)
        clips.append(title_clip)
        
        # create clips for each segment
        for i, segment in enumerate(script_with_audio['segments'], 1):
            logger.info(f"creating slide {i}/{len(script_with_audio['segments'])}: {segment['title']}")
            
            segment_clip = self._create_segment_clip(segment, i)
            if segment_clip is not None:
                clips.append(segment_clip)
        
        # create end card
        end_clip = self._create_end_card()
        clips.append(end_clip)
        
        # concatenate all clips
        logger.info("concatenating video clips...")
        final_video = concatenate_videoclips(clips, method='compose')
        
        # note: audio is already added per-segment in _create_segment_clip
        # full audio track is optional and would need pipeline_id to locate
        # for now, we rely on per-segment audio which is already set
        
        # write video file
        logger.info(f"writing video to {output_path}...")
        final_video.write_videofile(
            output_path,
            fps=self.fps,
            codec=self.config.get('output.codec', 'libx264'),
            audio_codec=self.config.get('output.audio_codec', 'aac'),
            temp_audiofile='temp_audio.m4a',
            remove_temp=True,
            # logger=None  # suppress moviepy's verbose output
        )
        
        logger.info(f"video generated successfully: {output_path}")
        return output_path
    
    def _create_title_card(self, title: str, duration: float = 3.0) -> VideoClip:
        """
        create title card clip. 
        args:
            title: video title
            duration: duration in seconds
        returns:
            video clip for title card
        """
        logger.info("creating title card...")
        
        title_card = VideoUtils.create_title_card(
            self.width,
            self.height,
            title,
            subtitle="Explainer Video by Vidinie"
        )
        
        clip = ImageClip(title_card).set_duration(duration)
        clip = clip.fx(fadein, 0.5).fx(fadeout, 0.5)
        
        return clip
    
    def _create_end_card(self, duration: float = 3.0) -> VideoClip:
        """
        create end card clip.
        args:
            duration: duration in seconds
        returns:
            video clip for end card
        """
        logger.info("creating end card...")
        
        end_card = VideoUtils.create_end_card(
            self.width,
            self.height,
            message="Thank you for watching!"
        )
        
        clip = ImageClip(end_card).set_duration(duration)
        clip = clip.fx(fadein, 0.5).fx(fadeout, 0.5)
        
        return clip
    
    def _create_segment_clip(self, segment: Dict, segment_number: int) -> Optional[VideoClip]:
        """
        create video clip for a segment.
        args:
            segment: segment data dictionary
            segment_number: segment number
        returns:
            video clip for segment or None if failed
        """
        try:
            # get duration from audio or estimate
            duration = segment.get('audio_duration', segment.get('duration', 45))
            
            # create background
            background = self._create_background(segment)
            
            # add image if available (from image field or legacy fields)
            image_path = self._get_image_path(segment)
            if image_path and os.path.exists(image_path):
                background = self._add_image_to_slide(background, image_path)
            
            # add text overlay
            background = self._add_text_overlay(background, segment)
            
            # create clip
            clip = ImageClip(background).set_duration(duration)
            
            # add audio if available
            audio_file = segment.get('audio_file')
            if audio_file and os.path.exists(audio_file):
                audio = AudioFileClip(audio_file)
                clip = clip.set_audio(audio)
                # ensure video duration matches audio
                clip = clip.set_duration(audio.duration)
            
            # add transitions
            clip = clip.fx(fadein, self.transition_duration)
            clip = clip.fx(fadeout, self.transition_duration)
            
            return clip
            
        except Exception as e:
            logger.error(f"error creating segment clip {segment_number}: {str(e)}", exc_info=True)
            return None
    
    def _get_image_path(self, segment: Dict) -> Optional[str]:
        """
        get image path from segment.
        prioritizes: image field > pdf_images > stock_image (legacy support).
        args:
            segment: segment data
        returns:
            path to image or None
        """
        # check new image field from content analyzer
        if segment.get('image'):
            img = segment['image']
            if img.get('source') == 'pdf' and img.get('path'):
                return img['path']
            elif img.get('source') == 'stock' and segment.get('stock_image'):
                # stock image should have been fetched
                return segment['stock_image'].get('filepath')
            elif img.get('source') == 'ai_generated' and img.get('path'):
                # ai-generated image path
                return img['path']
            elif img.get('source') == 'ai_generated' and segment.get('ai_generated_image'):
                # fallback to ai_generated_image metadata
                return segment['ai_generated_image'].get('filepath')
        
        # legacy support: check pdf_images and stock_image directly
        if segment.get('pdf_images') and len(segment['pdf_images']) > 0:
            img_data = segment['pdf_images'][0]
            if isinstance(img_data, dict):
                return img_data.get('filepath')
            elif isinstance(img_data, str):
                return img_data
        
        if segment.get('stock_image'):
            stock_img = segment['stock_image']
            if isinstance(stock_img, dict):
                return stock_img.get('filepath')
        
        return None
    
    def _create_background(self, segment: Dict) -> np.ndarray:
        """
        create background for slide.
        args:
            segment: segment data
        returns:
            background as numpy array
        """
        if self.background_type == 'gradient':
            return VideoUtils.create_gradient_background(
                self.width, self.height,
            )
        else:
            # solid color
            return VideoUtils.create_solid_background(
                self.width, self.height,
            )
    
    def _add_image_to_slide(self, background: np.ndarray, image_path: str) -> np.ndarray:
        """
        add image to slide background.
        image takes up 50% of horizontal space on the right side.
        args:
            background: background numpy array
            image_path: path to image file
        returns:
            background with image composited
        """
        if image_path and os.path.exists(image_path):
            try:
                # composite image on right side, taking 50% of width
                background = VideoUtils.composite_image_on_background(
                    background,
                    image_path,
                    position='right',
                    width_percentage=0.5,
                    mode='fill'
                )
            except Exception as e:
                logger.warning(f"could not add image {image_path}: {str(e)}")
        
        return background
    
    def _add_text_overlay(self, background: np.ndarray, segment: Dict) -> np.ndarray:
        """
        add text overlay to slide.
        video title is fixed at top, segment title below it, then bullet points.
        args:
            background: background with possible image
            segment: segment data
            segment_number: segment number
        returns:
            background with text overlay
        """
        img = Image.fromarray(background)
        
        # check if image exists to determine text area width
        image_path = self._get_image_path(segment)
        has_image = image_path and os.path.exists(image_path)
        
        # calculate text area width (50% if image exists as the image takes up 50% of the width, full width otherwise)
        if has_image:
            text_area_width = int(self.width * 0.5)
        else:
            text_area_width = self.width - 200
        position_x = 50
        position_y = 50

        line_spacing = 30
        # fixed video title at top (all segments)
        # use darker color for better contrast on pastel backgrounds
        img, space_used = VideoUtils.add_text_to_image(
            img,
            self.video_title,
            position=(position_x, position_y),
            font_size=70,
            color=(255, 255, 255),
            max_width=text_area_width - 100,
            align='left'
        )
        space_used += 30
        position_y += space_used + line_spacing

        # segment title below video title (no segment number prefix)
        img, space_used = VideoUtils.add_text_to_image(
            img,
            segment['title'],
            position=(position_x, position_y),
            font_size=50,
            color=(255, 255, 255),
            max_width=text_area_width,
            align='left'
        )

        position_y += space_used + line_spacing
        
        # add key points (first 3) with better spacing
        key_points = segment.get('key_points', [])[:3]
        if key_points:
            position_y += 20          
            for point in key_points:
                # add bullet point with proper alignment
                point_text = f"• {point}"
                img, space_used = VideoUtils.add_text_to_image(
                    img,
                    point_text,
                    position=(position_x + 20, position_y),  # indented for bullet
                    font_size=40,
                    color=(255, 255, 255),
                    max_width=text_area_width - 40,  # account for indentation
                    align='left'
                )
                position_y += space_used + line_spacing
        
        return np.array(img)


def generate_video(script_with_audio: Dict, config: Config, output_path: str) -> str:
    """
    convenience function to generate video.
    args:
        script_with_audio: script data with audio
        config: configuration object
        output_path: output video path
    returns:
        path to generated video
    """
    generator = VideoGenerator(config)
    return generator.generate_video(script_with_audio, output_path)

