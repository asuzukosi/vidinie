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
from typing import Optional, Tuple
import numpy as np
from core.data import (
    VideoPipelineScript,
    VideoPipelineSegment,
    BackgroundType,
)
from core.utils.config_loader import Config
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import (
    VideoClip, ImageClip, AudioFileClip,
    concatenate_videoclips
)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout

from core.utils.video_utils import VideoUtils
from core.utils.font_loader import FontLoader
from core.utils.logger import get_logger

logger = get_logger("video_generator")


class VideoGenerator:
    """unified video generator based on slideshow style."""
    
    def __init__(self, config: Config, 
                 video_title: Optional[str] = 'Untitled',
                 subtitle: Optional[str] = 'Explainer Video by Vidinie',
                 resolution: Optional[Tuple[int, int]] = [1920, 1080],
                 fps: Optional[int] = 30,
                 title_duration: Optional[float] = 3.0,
                 end_duration: Optional[float] = 3.0,
                 transition_duration: Optional[float] = 0.5,
                 background_type: Optional[BackgroundType] = BackgroundType.GRADIENT):
        """
        initialize video generator.
        args:
            config: configuration object
        """
        self.config = config
        self.width = resolution[0]
        self.height = resolution[1]
        self.fps = fps
        self.subtitle = subtitle
        self.title_duration = title_duration
        self.end_duration = end_duration
        self.transition_duration = transition_duration
        self.background_type = background_type
        
        # initialize font loader
        self.font_loader = FontLoader(config)
        VideoUtils.set_font_loader(self.font_loader)
        # video title will be set when generate_video is called
        self.video_title = video_title
        logger.info(f"initialized video generator: {self.width}x{self.height} @ {self.fps}fps")
        # log available fonts
        available_fonts = self.font_loader.list_available_fonts()
        if available_fonts:
            logger.info(f"available fonts: {', '.join(available_fonts)}")
    
    def generate_video(self, script_data: VideoPipelineScript, output_path: str) -> str:
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
        self.video_title = self.video_title if self.video_title else script_data.title
        
        # create title card
        title_clip = self._create_title_card(self.video_title)
        clips.append(title_clip)
        
        # create clips for each segment
        for i, segment in enumerate(script_data.segments, 1):
            logger.info(f"creating slide {i}/{len(script_data.segments)}: {segment.title}")
            segment_clip = self._create_segment_clip(segment, i)
            if segment_clip is not None:
                clips.append(segment_clip)
        
        # create end card
        end_clip = self._create_end_card()
        clips.append(end_clip)
        
        # concatenate all clips
        logger.info("concatenating video clips...")
        final_video = concatenate_videoclips(clips, method='compose')
        
        # write video file
        logger.info(f"writing video to {output_path}...")
        final_video.write_videofile(
            output_path,
            fps=self.fps,
            codec=self.config.get('output.codec', 'libx264'),
            audio_codec=self.config.get('output.audio_codec', 'aac'),
            temp_audiofile='temp_audio.m4a',
            remove_temp=True,
        )
        
        logger.info(f"video generated successfully: {output_path}")
        return output_path
    
    def _create_title_card(self, title: str) -> VideoClip:
        """
        create title card clip. 
        args:
            title: video title
        returns:
            video clip for title card
        """
        logger.info("creating title card...")
        
        title_card = VideoUtils.create_title_card(
            self.width,
            self.height,
            title,
            subtitle=self.subtitle
        )
        
        clip = ImageClip(title_card).set_duration(self.title_duration)
        clip = clip.fx(fadein, 0.5).fx(fadeout, 0.5)
        
        return clip
    
    def _create_end_card(self) -> VideoClip:
        """
        create end card clip.
        returns:
            video clip for end card
        """
        logger.info("creating end card...")
        
        end_card = VideoUtils.create_end_card(
            self.width,
            self.height,
            message="Thank you for watching!"
        )
        
        clip = ImageClip(end_card).set_duration(self.end_duration)
        clip = clip.fx(fadein, 0.5).fx(fadeout, 0.5)
        
        return clip
    
    def _create_segment_clip(self, 
                            segment: VideoPipelineSegment, 
                            segment_number: int) -> Optional[VideoClip]:
        """
        create video clip for a segment.
        args:
            segment: video segment data
            segment_number: segment number
        returns:
            video clip for segment or None if failed
        """
        try:
            # get duration from audio or estimate
            duration = segment.audio_duration if segment.audio_duration else 40
            
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
            audio_file = segment.audio_file
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
    
    def _get_image_path(self, segment: VideoPipelineSegment) -> Optional[str]:
        """
        get image path from segment.
        prioritizes: image field > pdf_images > stock_image (legacy support).
        args:
            segment: segment data
        returns:
            path to image or None
        """
        # check new image field from content analyzer
        if segment.image:
            return segment.image.path
        return None
    
    def _create_background(self, segment: VideoPipelineSegment) -> np.ndarray:
        """
        create background for slide.
        args:
            segment: segment data
        returns:
            background as numpy array
        """
        if self.background_type == BackgroundType.GRADIENT:
            return VideoUtils.create_gradient_background(
                self.width, self.height,
                color1=(0, 0, 0),
                color2=(0, 0, 0),
            )
        elif self.background_type == BackgroundType.SOLID:
            # solid color
            return VideoUtils.create_solid_background(
                self.width, self.height,
                color=(0, 0, 0),
            )
        elif self.background_type == BackgroundType.IMAGE:
            # image background
            return VideoUtils.create_image_background(
                self.width, self.height,
                segment.background_image_path if segment.background_image_path else None
            )
        else:
            logger.warning(f"unsupported background type: {self.background_type}")
            return None
    
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
    
    def _add_text_overlay(self, background: np.ndarray, segment: VideoPipelineSegment) -> np.ndarray:
        """
        add text overlay to slide.
        video title is fixed at top, segment title below it, then bullet points.
        args:
            background: background with possible image
            segment: segment data
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
            segment.title,
            position=(position_x, position_y),
            font_size=50,
            color=(255, 255, 255),
            max_width=text_area_width,
            align='left'
        )

        position_y += space_used + line_spacing
        
        # add key points (first 3) with better spacing
        key_points = segment.key_points[:3]
        if key_points:
            position_y += 20          
            for point in key_points:
                # add bullet point with proper alignment
                point_text = f"• {point}"
                img, space_used = VideoUtils.add_text_to_image(
                    img,
                    point_text,
                    position=(position_x + 20, position_y),
                    font_size=40,
                    color=(255, 255, 255),
                    max_width=text_area_width - 40,
                    align='left'
                )
                position_y += space_used + line_spacing
        
        return np.array(img)