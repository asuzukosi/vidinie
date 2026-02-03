import motor.motor_asyncio
from dotenv import load_dotenv
import os
from core.utils.logger import get_logger

logger = get_logger("db")

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://mongodb:27017")
db_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
database = db_client["vidinie"]
users_collection = database["users"]
video_pipelines_collection = database["video_pipelines"]
subscriptions_collection = database["subscriptions"]

async def initialize_db():
    """
    initialize the database object
    """
    try:
        logger.info("database initalized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False
    return True

async def disconnect_from_db():
    """
    disconnect from the database
    """
    try:
        logger.info("disconnecting from database")
        logger.info("database disconnected successfully")
    except Exception as e:
        logger.error(f"Error disconnecting from database: {e}")
        return False
    return True