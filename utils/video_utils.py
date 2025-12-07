"""
vidinie video utilities module

provides shared utilities for all video style generators.
provides common functions for video composition, text rendering, and effects.
"""

from typing import Tuple, Optional, Literal
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import (
    TextClip
)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from utils.logger import get_logger
from utils.font_loader import FontLoader
from enum import Enum

class PanelBackground(Enum):
    """background type for panel."""
    SOLID = "solid"
    GRADIENT = "gradient"
    IMAGE = "image"
    COMPOSITE = "composite"

logger = get_logger(__name__)

# TODO: create Panel class, create ImagePanel class, create TextPanel class, create ContentPanel class

class VideoUtils:
    """utility functions for video generation."""

    _font_loader: Optional[FontLoader] = None

    @classmethod
    def set_font_loader(cls, font_loader: FontLoader) -> None:
        """
        set font loader for video utils.

        args:
            font_loader: FontLoader instance
        """
        cls._font_loader = font_loader

    @staticmethod
    def create_gradient_background(
        width: int, height: int, 
        color1: Tuple[int, int, int] = (254, 234, 201),
        color2: Tuple[int, int, int] = (255, 205, 201),
        direction: Literal['vertical', 'horizontal'] = 'vertical'
    ) -> np.ndarray:
        """
        create a gradient background with smooth color transition.
        args:
            width: image width
            height: image height
            color1: start color (RGB)
            color2: end color (RGB)
            direction: 'vertical' (default) or 'horizontal'
        returns:
            numpy array representing the image
        """
        # Create a linear gradient using numpy broadcasting for better visual quality
        if direction == 'vertical':
            ramp = np.linspace(0, 1, height).reshape(-1, 1, 1)
        else:  # horizontal
            ramp = np.linspace(0, 1, width).reshape(1, -1, 1)

        color1 = np.array(color1, dtype=np.float32)
        color2 = np.array(color2, dtype=np.float32)
        gradient = ((1 - ramp) * color1 + ramp * color2).astype(np.uint8)

        if direction == 'vertical':
            gradient = np.tile(gradient, (1, width, 1))
        else:
            gradient = np.tile(gradient, (height, 1, 1))

        return gradient

    @staticmethod
    def create_solid_background(width: int, height: int,
                               color: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
        """
        create a solid color background.
        args:
            width: image width
            height: image height
            color: rgb color tuple
        returns:
            numpy array representing the image
        """
        background = np.zeros((height, width, 3), dtype=np.uint8)
        background[:] = color
        return background

    @staticmethod
    def create_image_background(width: int, height: int, image_path: str, mode: str = "fit", fill_color: Tuple[int, int, int]=(0,0,0)) -> np.ndarray:
        """
        create an image background for the video of a given width and height.
        the supplied image is either fit or filled into the background area.
        args:
            width: output image width
            height: output image height
            image_path: path to the image file to use as background
            mode: "fit" (default) will maintain aspect ratio and letterbox/pillarbox, "fill" will crop/zoom to fill
            fill_color: RGB color tuple for any padded area if using "fit"
        returns:
            numpy array of the resulting background
        """
        img = Image.open(image_path).convert("RGB")
        if mode == "fill":
            # crop and zoom to fill the background exactly
            scale = max(width / img.width, height / img.height)
            new_size = (int(img.width * scale), int(img.height * scale))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            x_offset = (resized.width - width) // 2
            y_offset = (resized.height - height) // 2
            cropped = resized.crop((x_offset, y_offset, x_offset + width, y_offset + height))
            return np.array(cropped)
        else:
            # "fit"
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            bg = Image.new("RGB", (width, height), fill_color)
            x_offset = (width - img.width) // 2
            y_offset = (height - img.height) // 2
            bg.paste(img, (x_offset, y_offset))
            return np.array(bg)

    @staticmethod
    def resize_image_to_fit(image_path: str, max_width: int, max_height: int,
                           maintain_aspect: bool = True) -> Image.Image:
        """
        resize image to fit within dimensions while maintaining aspect ratio.
        args:
            image_path: path to image file
            max_width: maximum width
            max_height: maximum height
            maintain_aspect: whether to maintain aspect ratio
        returns:
            resized pil image
        """
        img = Image.open(image_path)

        if maintain_aspect:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        else:
            img = img.resize((max_width, max_height), Image.Resampling.LANCZOS)

        return img

    @staticmethod
    def add_text_to_image(
        image: Image.Image,
        text: str,
        position: Tuple[int, int],
        font_size: int = 60,
        color: Tuple[int, int, int] = (255, 255, 255),
        max_width: Optional[int] = None,
        align: str = 'left'
    ) -> Tuple[Image.Image, int]:
        """
        add text to a pil image.
        args:
            image: pil image
            text: text to add
            position: (x, y) position
            font_size: Font size
            color: Text color RGB
            max_width: Maximum width for text wrapping
            align: Text alignment ('left', 'center', 'right')
            font_type: font type to use ('title', 'body', 'subtitle', 'default')
        returns:
            (pil image with text added, total height used by the drawn text)
        """
        img = image.copy()
        draw = ImageDraw.Draw(img)

        # load font using font loader if available
        if VideoUtils._font_loader:
            # get font from font loader
            font = VideoUtils._font_loader.get_font("BebasNeue-Regular.ttf", font_size)
        else:
            # fallback to default font
            logger.warning(f"no font loader available, falling back to default font")
            font = ImageFont.load_default()
            logger.info(f"loaded default font (size: {font_size})")
        # wrap text if max_width specified
        display_text = text
        if max_width:
            display_text = VideoUtils._wrap_text(text, font, max_width, draw)

        # Compute bounding box for used text area (so caller knows where to place next text after)
        # For multiline, textbbox returns the bounding box for the entire block
        bbox = draw.textbbox(position, display_text, font=font, align=align)
        total_height = bbox[3] - bbox[1]  # height of the drawn text box

        draw.text(position, display_text, font=font, fill=color, align=align)

        return img, total_height

    @staticmethod
    def _wrap_text(text: str, font, max_width: int, draw) -> str:
        """wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return '\n'.join(lines)

    @staticmethod
    def _get_background(
        width: int,
        height: int,
        background_type: Literal['gradient', 'solid', 'image', 'composite'] = 'gradient',
        background_options: Optional[dict] = None
    ) -> np.ndarray:
        """
        Utility to get a background numpy array given the type and options.
        Used by create_title_card and create_end_card.
        Supports an additional "composite" type which overlays an image on a gradient background.
        """
        background_options = background_options or {}
        if background_type == "solid":
            color = background_options.get('color', (255, 255, 255))
            logger.info(f"creating background with solid color")
            return VideoUtils.create_solid_background(width, height, color)
        elif background_type == "image":
            image_path = background_options.get('image_path')
            if not image_path:
                raise ValueError("background_options must include 'image_path' for image background_type")
            mode = background_options.get('mode', 'fill')
            fill_color = background_options.get('fill_color', (0, 0, 0))
            logger.info(f"creating background with image")
            return VideoUtils.create_image_background(width, height, image_path, mode, fill_color)
        elif background_type == "composite":
            # Composite: overlay image on a gradient background.
            logger.info(f"creating composite background with gradient and an image overlayed")
            # gradient part
            color1 = background_options.get('color1', (254, 234, 201))
            color2 = background_options.get('color2', (255, 205, 201))
            direction = background_options.get('direction', 'vertical')
            gradient_bg = VideoUtils.create_gradient_background(width, height, color1, color2, direction)
            # image part
            image_path = background_options.get('image_path')
            if not image_path:
                raise ValueError("background_options must include 'image_path' for composite background_type")
            composite_position = background_options.get('position', 'right')
            image_mode = background_options.get('mode', 'fill')
            width_percentage = background_options.get('width_percentage', None)
            fill_color = background_options.get('fill_color', (0,0,0))
            composited = VideoUtils.composite_image_on_background(
                gradient_bg, 
                image_path=image_path,
                position=composite_position,
                mode=image_mode,
                width_percentage=width_percentage,
                fill_color=fill_color
            )
            return composited
        else:  # gradient (default)
            color1 = background_options.get('color1', (254, 234, 201))
            color2 = background_options.get('color2', (255, 205, 201))
            direction = background_options.get('direction', 'vertical')
            logger.info(f"creating background with gradient")
            return VideoUtils.create_gradient_background(width, height, color1, color2, direction)

    @staticmethod
    def create_title_card(
        width: int, height: int, title: str,
        subtitle: Optional[str] = None,
        background_type: Literal['gradient', 'solid', 'image', 'composite'] = 'gradient',
        background_options: Optional[dict] = None
    ) -> np.ndarray:
        """
        create a title card for video.
        args:
            width: video width
            height: video height
            title: main title text
            subtitle: optional subtitle
            background_type: 'gradient', 'solid', 'image', or 'composite' (default: 'gradient')
            background_options: options for the background, e.g. for 'solid': {'color': (r,g,b)},
                                for 'gradient': {'color1': (r,g,b), 'color2': (r,g,b), 'direction': 'vertical'|'horizontal'},
                                for 'image': {'image_path': 'path', 'mode': 'fit'|'fill', 'fill_color': (r,g,b)}
                                for 'composite': all composite options (see _get_background)
        returns:
            numpy array representing the title card
        """
        background = VideoUtils._get_background(width, height, background_type, background_options)
        img = Image.fromarray(background)

        # add title
        title_y = height // 2 - 100 if subtitle else height // 2
        img, title_height = VideoUtils.add_text_to_image(
            img, title,
            position=(100, title_y),
            font_size=150,
            color=(255, 255, 255),
            max_width=width,
            align='left',
        )

        # add subtitle if provided
        if subtitle:
            subtitle_y = title_y + title_height + 50 if title_height else height // 2 + 50
            img, _ = VideoUtils.add_text_to_image(
                img, subtitle,
                position=(100, subtitle_y),
                font_size=80,
                color=(255, 255, 255),
                max_width=width - 200,
                align='left',
            )
        return np.array(img)

    @staticmethod
    def create_end_card(
        width: int, height: int, 
        message: str = "Thank you for watching!",
        background_type: Literal['gradient', 'solid', 'image', 'composite'] = "gradient",
        background_options: Optional[dict] = None
    ) -> np.ndarray:
        """
        create an end card for video.
        args:
            width: video width
            height: video height
            message: main message
            background_type: 'gradient', 'solid', 'image', or 'composite' (default: 'gradient')
            background_options: options for the background, e.g. for 'solid': {'color': (r,g,b)},
                                for 'gradient': {'color1': (r,g,b), 'color2': (r,g,b), 'direction': 'vertical'|'horizontal'},
                                for 'image': {'image_path': 'path', 'mode': 'fit'|'fill', 'fill_color': (r,g,b)}
                                for 'composite': all composite options (see _get_background)
        returns:
            numpy array representing the end card
        """
        background = VideoUtils._get_background(width, height, background_type, background_options)
        img = Image.fromarray(background)
        img, _ = VideoUtils.add_text_to_image(
            img, message,
            position=(width // 3, height // 2 - 100),
            font_size=150,
            color=(255, 255, 255),
            max_width=width - 100,
            align='center', 
        )
        return np.array(img)

    @staticmethod
    def add_fade_transition(clip, fade_duration: float = 0.5):
        """
        add fade in and fade out to a clip.
        args:
            clip: video clip
            fade_duration: duration of fade in seconds
        returns:
            clip with fade effects
        """
        return clip.fx(fadein, fade_duration).fx(fadeout, fade_duration)

    @staticmethod
    def composite_image_on_background(
        background: np.ndarray, 
        image_path: str,
        position: str = 'center',
        mode: str = 'fit',
        width_percentage: Optional[float] = None,
        fill_color: Optional[Tuple[int, int, int]] = None,
    ) -> np.ndarray:
        """
        composite an image onto a background

        args:
            background: background as numpy array
            image_path: path to image file
            position: 'center', 'left', 'right', 'top', or 'bottom'
            mode: "fit" (maintain aspect ratio, letterbox/pillarbox if needed), or "fill" (crop/zoom to fill allocation)
            width_percentage: if set, desired width of overlay as % of background width (0-1)
            fill_color: rgb tuple for any padding (used in fit mode, default to (0,0,0) if not set)
        returns:
            composited image as numpy array
        """
        bg_height, bg_width = background.shape[:2]
        fill_color = fill_color if fill_color is not None else (0, 0, 0)

        # determine area for the overlay
        if width_percentage is not None:
            target_width = max(1, int(bg_width * width_percentage))
        else:
            target_width = int(bg_width * 0.5)
        target_height = bg_height

        img = Image.open(image_path).convert("RGB")

        if mode == "fill":
            # scale so that one side covers required area, then crop central region
            scale = max(target_width / img.width, target_height / img.height)
            new_size = (int(img.width * scale), int(img.height * scale))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            x_crop = max(0, (resized.width - target_width) // 2)
            y_crop = max(0, (resized.height - target_height) // 2)
            img_overlay = resized.crop((x_crop, y_crop, x_crop + target_width, y_crop + target_height))
        else:
            # "fit"
            img_copy = img.copy()
            img_copy.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
            img_overlay = Image.new("RGB", (target_width, target_height), fill_color)
            x_offset = (target_width - img_copy.width) // 2
            y_offset = (target_height - img_copy.height) // 2
            img_overlay.paste(img_copy, (x_offset, y_offset))

        img_array = np.array(img_overlay)

        img_height, img_width = img_array.shape[0], img_array.shape[1]

        # compute paste position on the background
        if position == 'center':
            x = (bg_width - img_width) // 2
            y = (bg_height - img_height) // 2
        elif position == 'left':
            x = 0  # align to the very left
            y = (bg_height - img_height) // 2
        elif position == 'right':
            x = bg_width - img_width
            y = (bg_height - img_height) // 2
        elif position == 'top':
            x = (bg_width - img_width) // 2
            y = 0
        elif position == 'bottom':
            x = (bg_width - img_width) // 2
            y = bg_height - img_height
        else:
            x = (bg_width - img_width) // 2
            y = (bg_height - img_height) // 2

        # protect against out-of-bounds pasting
        x = max(0, min(bg_width - img_width, x))
        y = max(0, min(bg_height - img_height, y))

        # compose the image
        result = background.copy()
        result[y:y+img_height, x:x+img_width] = img_array

        return result

    @staticmethod
    def create_text_clip(text: str, duration: float, size: Tuple[int, int],
                        font_size: int = 60, color: str = 'white',
                        bg_color: str = 'transparent',
                        position: Tuple = ('center', 'center')) -> TextClip:
        """
        create a text clip for video.
        args:
            text: text to display
            duration: duration in seconds
            size: (width, height) of video
            font_size: font size
            color: text color
            bg_color: background color
            position: position tuple
        returns:
            textclip object
        """
        try:
            txt_clip = TextClip(
                text,
                fontsize=font_size,
                color=color,
                bg_color=bg_color,
                size=size,
                method='caption'
            ).set_duration(duration).set_position(position)
            return txt_clip
        except Exception as e:
            logger.warning(f"error creating textclip: {e}")
            # Fallback: return None
            return None
