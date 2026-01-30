"""
music generator module
generates background music from queries using the music engine.
handles music file creation and timing metadata.
"""

import os
from core.utils.logger import get_logger
from core.data import VideoOutline
from core.clients.music_engine import generate_musics, MusicPrompt


logger = get_logger(__name__)


class MusicGenerator:
    """generate background music from queries."""
    
    def __init__(self, output_dir: str = "temp/music"):
        """
        initialize music generator.
        args:
            output_dir: directory to save music files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    async def generate_background_music(self, script_data: VideoOutline) -> VideoOutline:
        """
        generate background music if query is provided.
        args:
            script_data: script data with background_music_query
        returns:
            updated script data with background_music_path
        """
        if not script_data.background_music_query:
            logger.info("No background music query provided, skipping music generation")
            return script_data
        
        logger.info(f"Generating background music with query: {script_data.background_music_query[:100]}...")
        
        # Generate music file
        music_output_path = os.path.join(self.output_dir, "background_music.mp3")
        music_prompt = MusicPrompt(
            prompt=script_data.background_music_query,
            output_path=music_output_path
        )
        
        try:
            results = await generate_musics([music_prompt])
            if results and len(results) > 0:
                script_data.background_music_path = results[0][0]
                logger.info(f"Background music generated: {script_data.background_music_path}")
            else:
                logger.warning("Music generation returned no results")
        except Exception as e:
            logger.error(f"Error generating background music: {str(e)}", exc_info=True)
        return script_data

