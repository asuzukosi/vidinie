import motor.motor_asyncio
from dotenv import load_dotenv
import os
from core.utils.logger import get_logger

logger = get_logger("db")

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
db_client = None
users_collection = None
video_pipelines_collection = None
subscriptions_collection = None

async def initialize_db():
    """
    initialize the database object
    """
    try:
        global db_client
        global users_collection
        global video_pipelines_collection
        global subscriptions_collection
        logger.info("initializing database")
        db_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
        logger.info("database client initialized successfully")
        database = db_client["vidinie"]
        logger.info("database initialized successfully")
        users_collection = database["users"]
        logger.info("users collection initialized successfully")
        video_pipelines_collection = database["video_pipelines"]
        logger.info("video pipelines collection initialized successfully")
        subscriptions_collection = database["subscriptions"]
        logger.info("subscriptions collection initialized successfully")
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
        global db_client
        global users_collection
        global video_pipelines_collection
        global subscriptions_collection
        logger.info("disconnecting from database")
        await db_client.close()
        logger.info("database closed successfully")
        db_client = None
        logger.info("database client disconnected successfully")
        users_collection = None
        logger.info("users collection disconnected successfully")
        video_pipelines_collection = None
        logger.info("video pipelines collection disconnected successfully")
        subscriptions_collection = None
        logger.info("subscriptions collection disconnected successfully")
        logger.info("database disconnected successfully")
    except Exception as e:
        logger.error(f"Error disconnecting from database: {e}")
        return False
    return True