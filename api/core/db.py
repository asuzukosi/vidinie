import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
db_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)

database = db_client["vidinie"]

users_collection = database["users"]
pipelines_collection = database["pipelines"]