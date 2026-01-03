"""
configuration loader
loads configuration from config.yaml and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger(__name__)


class Config:
    """
    configuration manager for the application.
 
    example:
        from utils.config_loader import Config
        config = Config()
        print(config.get('video.resolution')) # [1920, 1080]
        print(config.get('content.target_segments')) # 7
        print(config.get('voiceover.provider')) # elevenlabs
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        initialize configuration.
        args:
            config_path: path to config.yaml file
        """
        self.config_path = config_path
        self.config = {}
        self.load_config()
        self.load_env()
        
    def load_config(self):
        """ 
        load configuration from yaml file
        """
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
                logger.info(f"configuration loaded from {self.config_path}")
        else:
            logger.warning(f"configuration file {self.config_path} not found. using default configuration.")
            self.config = self._get_default_config()
    
    def load_env(self):
        """ 
        load environment variables from .env file.
        """
        load_dotenv()
        
        # Load API keys from environment
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        self.unsplash_access_key = os.getenv('UNSPLASH_ACCESS_KEY')
        self.pexels_api_key = os.getenv('PEXELS_API_KEY')
        
        # Override config with env vars if present
        voice_id = os.getenv('VOICE_ID')
        if voice_id:
            self.config['voiceover']['voice_id'] = voice_id
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        get configuration value using dot notation.
        args:
            key_path: dot-separated path (e.g., 'video.resolution')
            default: default value if key not found
        returns:
            configuration value
        example:
            from utils.config_loader import Config
            config = Config()
            print(config.get('video.resolution')) # [1920, 1080]
        """
        keys = key_path.split('.')
        value = self.config
        # we recursively traverse the dictionary to get the value
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def _get_default_config(self) -> Dict:
        """
        retreive default configuration.
        """
        return {
            'video': {
                'resolution': [1920, 1080],
                'fps': 30,
                'default_style': 'slideshow'
            },
            'content': {
                'target_segments': 7,
                'segment_duration': 45
            },
            'voiceover': {
                'provider': 'elevenlabs',
                'voice_id': '21m00Tcm4TlvDq8ikWAM',
                'model': 'eleven_monolingual_v1'
            },
            'images': {
                'extract_from_pdf': True,
                'use_stock_images': True,
                'max_stock_images_per_segment': 1,
                'preferred_stock_provider': 'unsplash'
            },
            'output': {
                'directory': 'output',
                'temp_directory': 'temp',
                'keep_temp_files': False,
                'codec': 'libx264',
                'audio_codec': 'aac'
            },
            'paths': {
                'prompts_directory': 'core/prompts'
            }
        }
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """
        validate that required API keys are present.
        returns:
            dictionary of API key availability
        example:
            from utils.config_loader import Config
            config = Config()
            print(config.validate_api_keys()) # {'openai': True, 'elevenlabs': True, 'unsplash': True, 'pexels': True}
        """
        return {
            'openai': bool(self.openai_api_key),
            'elevenlabs': bool(self.elevenlabs_api_key),
            'unsplash': bool(self.unsplash_access_key),
            'pexels': bool(self.pexels_api_key)
        }
    
    def ensure_directories(self):
        """
        ensure output and temp directories exist.
        """
        output_dir = self.get('output.directory', 'output')
        temp_dir = self.get('output.temp_directory', 'temp')
        
        Path(output_dir).mkdir(exist_ok=True)
        Path(temp_dir).mkdir(exist_ok=True)
        
        logger.info(f"Ensured directories: {output_dir}, {temp_dir}")
    
    def get_prompts_directory(self) -> Path:
        """
        Get the prompts directory path.
        
        Returns:
            Path object pointing to prompts directory
        """
        prompts_dir = self.get('paths.prompts_directory', 'core/prompts')
        # Resolve relative to project root
        project_root = Path(__file__).parent.parent
        return project_root / prompts_dir


# global config instance
_config_instance = None


def get_config(config_path: str = "config.yaml") -> Config:
    """
    get or create global configuration instance.
    
    args:
        config_path: path to config file
    returns:
        config instance
    example:
        from utils.config_loader import get_config
        config = get_config()
        print(config.get('video.resolution')) # [1920, 1080]
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance



