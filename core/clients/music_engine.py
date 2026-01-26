from enum import Enum
import os
import sys
import asyncio
from typing import List, Tuple
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
from pydub import AudioSegment
from pydantic import BaseModel
from retry import retry

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.utils.logger import get_logger
load_dotenv()

logger = get_logger("music_engine")


class MusicPrompt(BaseModel):
    """music prompt with description."""
    prompt: str
    output_path: str


class MusicEngine:
    """music engine using elevenlabs."""
    
    def __init__(self, api_key: str = None):
        """initialize elevenlabs music engine client."""
        api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("elevenlabs api key is required")
        logger.info(f"initializing elevenlabs music engine client with api key")
        self.client = ElevenLabs(api_key=api_key)
        logger.info("initialized elevenlabs music engine client")

    @retry(tries=5, delay=2, backoff=2)
    def _generate_music(self, prompt: MusicPrompt) -> Tuple[str, float]:
        """generate music using elevenlabs."""
        assert prompt.output_path.endswith(".mp3"), "output path must end with .mp3"
        logger.info(f"generating music using elevenlabs with prompt: {prompt.prompt[:100]}...")
        
        track = self.client.music.compose(
            prompt=prompt.prompt,
            music_length_ms=30000,
        )
        
        logger.info(f"generated music using elevenlabs")
        
        # save the track to a file
        with open(prompt.output_path, "wb") as f:
            for chunk in track:
                f.write(chunk)
        
        logger.info("retrieving duration of music")
        audio = AudioSegment.from_mp3(prompt.output_path)
        duration = len(audio) / 1000.0
        return (prompt.output_path, duration)
    
    async def _generate_music_async(self, prompt: MusicPrompt) -> Tuple[str, float]:
        """run the synchronous blocking api call in a thread pool to enable parallelism"""
        return await asyncio.to_thread(self._generate_music, prompt)

    async def async_generate_musics(self, prompts: List[MusicPrompt]) -> List[Tuple[str, float]]:
        """
        music engine function takes a list of prompts and runs all in parallel
        then returns the list of (output_path, duration) tuples
        """
        tasks = [self._generate_music_async(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        return results
        
    def generate_musics(self, prompts: List[MusicPrompt]) -> List[Tuple[str, float]]:
        return asyncio.run(self.async_generate_musics(prompts))


def generate_musics(prompts: List[MusicPrompt]) -> List[Tuple[str, float]]:
    """
    generate multiple music tracks in parallel based on the prompts.
    returns:
        list of tuples (output_path, duration)
    """
    music_engine = MusicEngine()
    return music_engine.generate_musics(prompts)


if __name__ == "__main__":
    prompts = [
        MusicPrompt(
            prompt="Create an intense, fast-paced electronic track for a high-adrenaline video game scene. Use driving synth arpeggios, punchy drums, distorted bass, glitch effects, and aggressive rhythmic textures. The tempo should be fast, 130–150 bpm, with rising tension, quick transitions, and dynamic energy bursts.",
            output_path="test_music1.mp3"
        ),
        MusicPrompt(
            prompt="Create a calm, ambient background track with soft piano, gentle strings, and subtle atmospheric textures. The mood should be peaceful and contemplative, perfect for a meditation or relaxation video.",
            output_path="test_music2.mp3"
        ),
    ]
    generate_musics(prompts)

