"""
configuration loader
loads configuration from config.yaml and environment variables.
"""

import os
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
        # load from environment variables
        self._load_env()
    
    def _set_defaults(self):
        """set default configuration values as flat attributes."""
        # project root directory
        self.project_root = Path(__file__).parent.parent.parent
        # content settings
        self.content_chunk_length = 512_000
        # output settings
        self.output_directory = self.project_root / 'outputs'
        self.logs_directory = self.project_root / 'logs'
        # path settings
        self.prompts_directory = self.project_root / 'core' / 'prompts'
        self.base_project_path = self.project_root / '_base'
        self.remotion_tool_path = self.project_root / '.claude' / 'skills' / 'remotion-best-practices'
        # api keys (will be loaded from env)
        self.anthropic_api_key = None
        self.replicate_api_token = None
        self.elevenlabs_api_key = None
        self.pexels_api_key = None

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
        """ensure output and logs directories exist."""
        self.output_directory.mkdir(exist_ok=True)
        self.logs_directory.mkdir(exist_ok=True)
        self.prompts_directory.mkdir(exist_ok=True)
        
        logger.info(f"ensured directories: {self.output_directory}, {self.logs_directory}, {self.prompts_directory}")
    
    def get_prompts_directory(self) -> Path:
        """
        get the prompts directory path.
        returns:
            Path object for prompts directory
        """
        return self.prompts_directory


# singleton instance
config = Config()
