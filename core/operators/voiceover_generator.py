"""
voiceover generator module
generates audio voiceovers from scripts using the audio engine.
handles audio file creation and timing metadata.
"""

import os
from typing import Union
from core.utils.logger import get_logger
from pydub import AudioSegment
from core.data import VideoOutline
from core.clients.audio_engine import generate_audios, AudioPrompt, AudioVoiceString


logger = get_logger(__name__)


class VoiceoverGenerator:
    """generate voiceover audio from scripts."""
    
    def __init__(self, 
                 voice: AudioVoiceString = AudioVoiceString.NARRATIVE_EXPRESSIVE_MALE,
                 output_dir: str = "temp/audio"):
        """
        initialize voiceover generator.
        args:
            voice: audio voice enum
            output_dir: directory to save audio files
        """
        self.output_dir = output_dir
        self.voice = voice
    
    async def generate_voiceovers(self,
                            video_outline: VideoOutline) -> VideoOutline:
        """
        generate voiceover audio for all segments.
        args:
            video_outline: video outline with segments
        returns:
            updated script data with audio file paths and metadata
        """
        logger.info(f"generating voiceovers for {len(video_outline.segments)} segments")
        audio_prompts = [AudioPrompt(text=segment.script, voice=self.voice, output_path=os.path.join(self.output_dir, f"segment_{i:02d}_{segment.title}.mp3")) for i, segment in enumerate(video_outline.segments)]
        audio_paths = await generate_audios(audio_prompts)
        for i, segment in enumerate(video_outline.segments):
            segment.audio_file = audio_paths[i][0]
            segment.audio_duration = audio_paths[i][1]
        return video_outline
    
    async def generate_full_audio(self, video_outline: VideoOutline, 
                            output_path: str) -> float:
        """
        generate a single audio file combining all segments.
        """
        logger.info("combining all segments into single audio file")
            
        combined = AudioSegment.empty()
        for segment in video_outline.segments:
            audio_file = segment.audio_file
            if audio_file and os.path.exists(audio_file):
                audio = AudioSegment.from_mp3(audio_file)
                combined += audio
                silence = AudioSegment.silent(duration=500)
                combined += silence
        combined.export(output_path, format="mp3")
        duration = len(combined) / 1000.0
        logger.info(f"combined audio generated: {output_path} ({duration:.1f}s)")
        return duration
