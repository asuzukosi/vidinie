from dotenv import load_dotenv
from core.utils.logger import get_logger
import os

load_dotenv()
logger = get_logger("config")

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")

settings = {
    "mongodb_uri": MONGODB_URI,
}

async def initialize_config():
    """
    initialize the configuration object
    """
    logger.info("configuration initalized successfully")

async def destroy_config():
    """
    destroy the configuration object
    """
    logger.info("configuration destroyed successfully")