"""
voiceover generator module
generates audio voiceovers from scripts using elevenlabs or gtts.
handles audio file creation and timing metadata.
"""

import os
import json
from typing import  Optional, Tuple
from pathlib import Path
from core.utils.logger import get_logger
from core.utils.config_loader import get_config
from elevenlabs import save
from pydub import AudioSegment
from core.data import VideoPipelineScript


logger = get_logger(__name__)


class VoiceoverGenerator:
    """generate voiceover audio from scripts."""
    
    def __init__(self, provider: str = "elevenlabs", 
                 api_key: Optional[str] = None,
                 voice_id: Optional[str] = None,
                 output_dir: str = "temp/audio"):
        """
        initialize voiceover generator.
        args:
            provider: "elevenlabs" or "gtts"
            api_key: elevenlabs api key (if using elevenlabs)
            voice_id: elevenlabs voice id
            output_dir: directory to save audio files
        """
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        self.voice_id = voice_id or os.getenv('VOICE_ID', '21m00Tcm4TlvDq8ikWAM')
        self.output_dir = output_dir
        
        # create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # always initialize gtts as fallback
        self._init_gtts()
        
        # initialize provider
        if self.provider == "elevenlabs":
            if not self.api_key:
                logger.warning("elevenlabs api key not found. falling back to gtts.")
                self.provider = "gtts"
            else:
                self._init_elevenlabs()
    
    def _init_elevenlabs(self):
        """initialize elevenlabs client."""
        try:
            from elevenlabs import ElevenLabs, VoiceSettings
            self.client = ElevenLabs(api_key=self.api_key)
            self.voice_settings = VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
            logger.info("initialized elevenlabs voiceover generator")
        except ImportError:
            logger.error("elevenlabs package not installed. install with: pip install elevenlabs")
            self.provider = "gtts"
        except Exception as e:
            logger.error(f"error initializing elevenlabs: {str(e)}")
            self.provider = "gtts"
    
    def _init_gtts(self):
        """initialize gtts."""
        try:
            from gtts import gTTS
            self.gtts_class = gTTS
            logger.info("initialized gtts voiceover generator (free fallback)")
        except ImportError:
            logger.error("gtts package not installed. install with: pip install gtts")
            raise
    
    def generate_voiceovers(self, script_data: VideoPipelineScript) -> VideoPipelineScript:
        """
        generate voiceover audio for all segments.
        args:
            script_data: script data with segments
        returns:
            updated script data with audio file paths and metadata
        """
        logger.info(f"generating voiceovers for {len(script_data.segments)} segments using {self.provider}")
                
        for i, segment in enumerate(script_data.segments, 1):
            logger.info(f"generating audio for segment {i}: {segment.title}")
            
            script_text = segment.script
            if not script_text:
                logger.warning(f"no script found for segment {i}")
                continue
            
            # generate audio
            audio_path, duration = self._generate_segment_audio(script_text, i, segment.title)
            
            # update segment with audio info
            segment.audio_file = audio_path
            segment.audio_duration = duration
            segment.voiceover_provider = self.provider
        
        logger.info(f"Generated {len(script_data.segments)} voiceovers, total duration: {sum(s.audio_duration for s in script_data.segments):.1f}s")
        
        return script_data
    
    def _generate_segment_audio(self, text: str, segment_num: int, title: str) -> Tuple[str, float]:
        """
        generate audio for a single segment.
        args:
            text: script text
            segment_num: segment number
            title: segment title
        returns:
            tuple of (audio_file_path, duration_seconds)
        """
        # create filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:30]
        filename = f"segment_{segment_num:02d}_{safe_title}.mp3"
        filepath = os.path.join(self.output_dir, filename)
        
        if self.provider == "elevenlabs":
            duration = self._generate_elevenlabs_audio(text, filepath)
        else:
            duration = self._generate_gtts_audio(text, filepath)
        
        logger.info(f"Generated audio: {filename} ({duration:.1f}s)")
        return filepath, duration
    
    def _generate_elevenlabs_audio(self, text: str, output_path: str) -> float:
        """
        generate audio using elevenlabs.
        args:
            text: text to convert to speech
            output_path: path to save audio file
        returns:
            duration in seconds
        """
        try:
            # generate audio
            # using eleven_turbo_v2_5 which is available on free tier
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id="eleven_turbo_v2_5",
                voice_settings=self.voice_settings
            )
            save(audio_generator, output_path)
            # calculate duration (approximate: 150 words per minute)
            word_count = len(text.split())
            duration = (word_count / 150.0) * 60.0
            # get actual duration if available
            audio = AudioSegment.from_mp3(output_path)
            duration = len(audio) / 1000.0
            return duration
            
        except Exception as e:
            logger.error(f"Error generating ElevenLabs audio: {str(e)}")
            # Fallback to gTTS
            logger.info("Falling back to gTTS for this segment")
            return self._generate_gtts_audio(text, output_path)
    
    def _generate_gtts_audio(self, text: str, output_path: str) -> float:
        """
        generate audio using gtts (free fallback).
        args:
            text: text to convert to speech
            output_path: path to save audio file
        returns:
            duration in seconds
        """
        try:
            tts = self.gtts_class(text=text, lang='en', slow=False)
            tts.save(output_path)
            
            # Calculate duration
            word_count = len(text.split())
            duration = (word_count / 150.0) * 60.0  # Approximate
            
            # Get actual duration if available
            audio = AudioSegment.from_mp3(output_path)
            duration = len(audio) / 1000.0
            
            return duration
            
        except Exception as e:
            logger.error(f"Error generating gTTS audio: {str(e)}")
            raise
    
    def generate_full_audio(self, script_data: VideoPipelineScript, output_path: str) -> float:
        """
        generate a single audio file combining all segments.
        args:
            script_data: script data
            output_path: path to save combined audio
        returns:
            total duration in seconds
        """
        logger.info("**** combining all segments into single audio file ****")
            
        combined = AudioSegment.empty()
        for segment in script_data.segments:
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
    
    def save_metadata(self, script_data: VideoPipelineScript, output_path: str):
        """
        save script data with audio metadata.
        args:
            script_data: script data with audio info
            output_path: path to save JSON
        """
        with open(output_path, 'w') as f:
            json.dump(script_data.model_dump(mode="json"), f, indent=2)
        logger.info(f"saved audio metadata to {output_path}")
