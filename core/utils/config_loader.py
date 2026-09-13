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

        # pipeline subpaths (relative to output_directory/pipeline_id)
        self.pipeline_public_path = 'public'
        self.pipeline_source_path = self.pipeline_public_path + '/sources'
        self.pipeline_audio_path = self.pipeline_public_path + '/audio'
        self.pipeline_music_path = self.pipeline_public_path + '/music'
        self.pipeline_images_path = self.pipeline_public_path + '/images'
        self.pipeline_clips_path = self.pipeline_public_path + '/clips'
        self.pipeline_stock_images_path = self.pipeline_images_path + '/stock_images'
        self.pipeline_stock_videos_path = self.pipeline_clips_path + '/stock_videos'
        self.pipeline_ai_images_path = self.pipeline_images_path + '/ai_images'
        self.pipeline_ai_videos_path = self.pipeline_clips_path + '/ai_videos'
        self.pipeline_result_path = 'result'
        self.pipeline_remotion_output_path = 'out/VidinieComposition.mp4'

        # r2 object storage (optional; falls back to local disk alone)
        self.r2_account_id = None
        self.r2_bucket = None
        self.r2_access_key_id = None
        self.r2_secret_access_key = None

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

        # load r2 settings from environment
        self.r2_account_id = os.getenv('R2_ACCOUNT_ID') or self.r2_account_id
        self.r2_bucket = os.getenv('R2_BUCKET') or self.r2_bucket
        self.r2_access_key_id = os.getenv('R2_ACCESS_KEY_ID') or self.r2_access_key_id
        self.r2_secret_access_key = os.getenv('R2_SECRET_ACCESS_KEY') or self.r2_secret_access_key

    @property
    def r2_endpoint(self) -> str:
        return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"
    
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
