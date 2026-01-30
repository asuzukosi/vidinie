from enum import Enum
import os
import sys
import asyncio
from typing import List, Tuple
from dotenv import load_dotenv
from elevenlabs import ElevenLabs, VoiceSettings
from elevenlabs import save
from pydub import AudioSegment
from pydantic import BaseModel
from retry import retry

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.utils.logger import get_logger
load_dotenv()

logger = get_logger("audio_engine")

class AudioVoices(str, Enum):
    """audio voices enum."""
    NARRATIVE_EXPRESSIVE_MALE = "pVnrL6sighQX7hVz89cp"
    FUN_VIBRANT_FEMALE = "T7eLpgAAhoXHlrNajG8v"
    CALM_NARRATIVE_MALE = "C9fbwSpEaejywLWx722Z"
    CALM_SOOTHING_FEMALE = "bD9maNcCuQQS75DGuteM"
    SOOTHING_BRITISH_MALE = "UmQN7jS1Ee8B1czsUtQh"
    EXPRESSIVE_PROFESSIONAL_MALE = "XwswTF89pZKbWpVX4A7R"

class AudioVoiceString(str, Enum):
    """audio voice to string enum."""
    NARRATIVE_EXPRESSIVE_MALE = "Narrative Expressive Male" # default voice
    FUN_VIBRANT_FEMALE = "Fun Vibrant Female"
    CALM_NARRATIVE_MALE = "Calm Narrative Male"
    CALM_SOOTHING_FEMALE = "Calm Soothing Female"
    SOOTHING_BRITISH_MALE = "Soothing British Male"
    EXPRESSIVE_PROFESSIONAL_MALE = "Expressive Professional Male"


def get_audio_voice_from_string(voice_string: AudioVoiceString) -> AudioVoices:
    """get audio voice from string."""
    if voice_string == AudioVoiceString.NARRATIVE_EXPRESSIVE_MALE:
        return AudioVoices.NARRATIVE_EXPRESSIVE_MALE
    elif voice_string == AudioVoiceString.FUN_VIBRANT_FEMALE:
        return AudioVoices.FUN_VIBRANT_FEMALE
    elif voice_string == AudioVoiceString.CALM_NARRATIVE_MALE:
        return AudioVoices.CALM_NARRATIVE_MALE
    elif voice_string == AudioVoiceString.CALM_SOOTHING_FEMALE:
        return AudioVoices.CALM_SOOTHING_FEMALE
    elif voice_string == AudioVoiceString.SOOTHING_BRITISH_MALE:
        return AudioVoices.SOOTHING_BRITISH_MALE
    elif voice_string == AudioVoiceString.EXPRESSIVE_PROFESSIONAL_MALE:
        return AudioVoices.EXPRESSIVE_PROFESSIONAL_MALE
    else:
        return None

class AudioPrompt(BaseModel):
    """audio prompt with text and voice."""
    text: str
    voice: AudioVoiceString
    output_path: str

class AudioEngine:
    """audio engine using elevenlabs."""
    
    def __init__(self, api_key: str = None):
        """ initialize elevenlabs audio engine client."""
        api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("elevenlabs api key is required")
        logger.info(f"initializing elevenlabs audio engine client with api key")
        self.client = ElevenLabs(api_key=api_key)
        self.voice_settings = VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True
        )
        self.model_id = "eleven_turbo_v2_5" # best for speed and performance
        logger.info("initialized elevenlabs audio engine client")

    @retry(tries=5, delay=2, backoff=2)
    def _generate_audio(self, prompt: AudioPrompt) -> Tuple[str, float]:
        """generate audio using elevenlabs."""
        assert prompt.output_path.endswith(".mp3"), "output path must end with .mp3"
        voice_id = get_audio_voice_from_string(prompt.voice)
        if not voice_id:
            raise ValueError(f"invalid voice: {prompt.voice}")
        logger.info(f"generating audio using elevenlabs voice: {prompt.voice}")
        audio = self.client.text_to_speech.convert(
            voice_id=voice_id,
            text=prompt.text,
            model_id=self.model_id,
            voice_settings=self.voice_settings
        )
        logger.info(f"generated audio using elevenlabs")
        save(audio, prompt.output_path)
        logger.info("retreiving duration of audio")
        audio = AudioSegment.from_mp3(prompt.output_path)
        duration = len(audio) / 1000.0
        return (prompt.output_path, duration)
    
    async def _generate_audio_async(self, prompt: AudioPrompt) -> Tuple[str, float]:
        """run the synchronous blocking api call in a thread pool to enable parallelism"""
        return await asyncio.to_thread(self._generate_audio, prompt)

    async def generate_audios(self, prompts: List[AudioPrompt]) -> List[Tuple[str, float]]:
        """
        audio engine function takes a list of prompts and runs all in parallel
        then returns the list of (output_path, duration) tuples
        """
        tasks = [self._generate_audio_async(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        return results


async def generate_audios(prompts: List[AudioPrompt]) -> List[Tuple[str, float]]:
    """async module-level function for generating audios."""
    audio_engine = AudioEngine()
    return await audio_engine.generate_audios(prompts)

if __name__ == "__main__":
    prompts = [
        AudioPrompt(text="Hello, how are you? This is a test for the vidinie audio engine.", voice=AudioVoiceString.NARRATIVE_EXPRESSIVE_MALE, output_path="hello1.mp3"),
        AudioPrompt(text="Hello, how are you? This is a test for the vidinie audio engine.", voice=AudioVoiceString.FUN_VIBRANT_FEMALE, output_path="hello2.mp3"),
        AudioPrompt(text="Hello, how are you? This is a test for the vidinie audio engine.", voice=AudioVoiceString.CALM_NARRATIVE_MALE, output_path="hello3.mp3"),
        AudioPrompt(text="Hello, how are you? This is a test for the vidinie audio engine.", voice=AudioVoiceString.CALM_SOOTHING_FEMALE, output_path="hello4.mp3"),
        AudioPrompt(text="Hello, how are you? This is a test for the vidinie audio engine.", voice=AudioVoiceString.SOOTHING_BRITISH_MALE, output_path="hello5.mp3"),
        AudioPrompt(text="Hello, how are you? This is a test for the vidinie audio engine.", voice=AudioVoiceString.EXPRESSIVE_PROFESSIONAL_MALE, output_path="hello6.mp3"),
    ]
    audio_engine = AudioEngine()
    asyncio.run(audio_engine.generate_audios(prompts))
