"""
configuration loader
loads configuration from config.yaml and environment variables.
"""

import os
import yaml
from typing import Dict
from pathlib import Path
from dotenv import load_dotenv
from core.utils.logger import get_logger

logger = get_logger("config_loader")


class Config:
    """
    configuration manager for the application.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        initialize configuration.
        args:
            config_path: path to config.yaml file
        """
        self.config_path = config_path
        # set default values
        self._set_defaults()
        # load from yaml file
        self._load_config()
        # load from environment variables
        self._load_env()
    
    def _set_defaults(self):
        """set default configuration values as flat attributes."""
        # content settings
        self.content_chunk_length = 4000

        # output settings
        self.output_directory = 'output'
        self.output_temp_directory = 'temp'
        self.output_codec = 'libx264'
        self.output_audio_codec = 'aac'
        
        # path settings
        self.paths_prompts_directory = 'core/prompts'
        
        # font settings
        self.fonts_fonts_directory = 'fonts'
        self.fonts_default_font = None
        
        # api keys (will be loaded from env)
        self.anthropic_api_key = None
        self.replicate_api_token = None
        self.elevenlabs_api_key = None
        self.pexels_api_key = None
    
    def _load_config(self):
        """Load configuration from flat YAML file and set as attributes."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file {self.config_path} not found. Using default configuration.")
            return
        
        with open(self.config_path, 'r') as f:
            yaml_data = yaml.safe_load(f)
            if not yaml_data:
                return
        
        logger.info(f"Configuration loaded from {self.config_path}")
        
        # directly set attributes from flat yaml structure
        for key, value in yaml_data.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"Unknown config key: {key}")
    
    def _load_env(self):
        """load environment variables from .env file and override config."""
        load_dotenv()
        
        # load api keys from environment
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY') or self.anthropic_api_key
        self.replicate_api_token = os.getenv('REPLICATE_API_TOKEN') or self.replicate_api_token
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY') or self.elevenlabs_api_key
        self.pexels_api_key = os.getenv('PEXELS_API_KEY') or self.pexels_api_key
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """
        validate that required API keys are present.
        returns:
            dictionary mapping service names to boolean indicating if key is present
        """
        return [
            ('anthropic', bool(self.anthropic_api_key)),
            ('replicate', bool(self.replicate_api_token)),
            ('elevenlabs', bool(self.elevenlabs_api_key)),
            ('pexels', bool(self.pexels_api_key))
        ]
    
    def ensure_directories(self):
        """ensure output and temp directories exist."""
        Path(self.output_directory).mkdir(exist_ok=True)
        Path(self.output_temp_directory).mkdir(exist_ok=True)
        
        logger.info(f"Ensured directories: {self.output_directory}, {self.output_temp_directory}")
    
    def get_prompts_directory(self) -> Path:
        """
        get the prompts directory path.
        returns:
            Path object for prompts directory
        """
        # resolve relative to project root
        project_root = Path(__file__).parent.parent.parent
        return project_root / self.paths_prompts_directory


# singleton instance
config = Config()
