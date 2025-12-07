from moviepy.editor import (
    VideoClip, ImageClip, AudioFileClip,
    concatenate_videoclips
)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from utils.video_utils import VideoUtils
from utils.font_loader import FontLoader
from utils.logger import get_logger
from utils.config_loader import get_config
from time import time

logger = get_logger(__name__)

def test_video():
    """test video generation."""
    logger.info("testing video generation...")
    config = get_config()
    font_loader = FontLoader(config)
    available_fonts = font_loader.list_available_fonts()
    if available_fonts:
        logger.info(f"Available fonts: {', '.join(available_fonts)}")
    else:
        logger.info("No fonts found.")
    VideoUtils.set_font_loader(font_loader)
    # test title card
    title_card = VideoUtils.create_title_card(width=1920, height=1080, 
                                              title="Test Video", subtitle="A subtitle",
                                              background_type="composite", background_options={"image_path": "sample.jpg"})
    title_clip = ImageClip(title_card).set_duration(3.0)
    title_clip = title_clip.fx(fadein, 0.5).fx(fadeout, 0.5)
    # test end card
    end_card = VideoUtils.create_end_card(1920, 1080, "Thank you for watching!")
    end_clip = ImageClip(end_card).set_duration(3.0)
    end_clip = end_clip.fx(fadein, 0.5).fx(fadeout, 0.5)
    start_time = time()
    # concatenate title and end cards
    final_video = concatenate_videoclips([title_clip, end_clip])
    final_video.write_videofile("test_video.mp4", fps=30, codec='libx264', audio_codec='aac')
    logger.info("test video generated successfully")
    end_time = time()
    logger.info(f"test video generated in {end_time - start_time} seconds")


if __name__ == "__main__":
    test_video()