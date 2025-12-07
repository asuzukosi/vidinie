from pymongo import AsyncMongoClient
from api.core.config import settings

client = AsyncMongoClient(settings["mongo_uri"])
db = client["vidinie"]
users_collection = db["users"]
pipelines_collection = db["pipelines"]

async def get_user(user_id: str):
    return await users_collection.find_one({"_id": user_id})

async def get_pipeline(pipeline_id: str):
    return await pipelines_collection.find_one({"_id": pipeline_id})