from typing import Optional, Dict, Any
from bson.objectid import ObjectId
from fastapi import HTTPException
from api.data.users import User
from api.core.db import users_collection
from core.utils.logger import get_logger

logger = get_logger('user_helpers')

async def get_user_by_id(user_id: str) -> User:
    """
    get a user by their id.
    """
    if users_collection is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")
    try:
        user_dict: Optional[Dict[str, Any]] = await users_collection.find_one(
            {"_id": ObjectId(user_id)}
        )
        if not user_dict:
            raise HTTPException(status_code=404, detail="User not found")
        return User(**user_dict)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"error retrieving user with id: {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"error retrieving user: {str(e)}")


async def get_user_by_email(email: str) -> Optional[User]:
    """
    get a user by their email.
    """
    if users_collection is None:
        raise HTTPException(status_code=500, detail="database is not initialized")
    try:
        user_dict: Optional[Dict[str, Any]] = await users_collection.find_one(
            {"email": email}
        )
        if not user_dict:
            return None
        return User(**user_dict)
    except Exception as e:
        logger.error(f"error retrieving user with email: {email}: {str(e)}")
        return None


async def update_user_in_db(user_id: str, user: User) -> None:
    """
    update a user in the database.
    """
    if users_collection is None:
        raise HTTPException(status_code=500, detail="database is not initialized")
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user.model_dump(mode="json")}
    )


async def create_user_in_db(user: User) -> User:
    """
    create a new user in the database.
    """
    if users_collection is None:
        raise HTTPException(status_code=500, detail="database is not initialized")
    logger.info("creating new user in database")
    # insert user into database
    db_user = await users_collection.insert_one(user.model_dump(mode="json"))
    new_id = str(db_user.inserted_id)
    # update the user's id field
    user.id = new_id
    # put the database record with the new id
    await users_collection.update_one(
        {"_id": ObjectId(new_id)},
        {"$set": {"id": new_id}}
    )
    logger.info(f"user created successfully with id: {new_id}")
    return user


async def get_user_by_google_id(google_id: str) -> Optional[User]:
    """
    get a user by their google id.
    """
    if users_collection is None:
        raise HTTPException(status_code=500, detail="database is not initialized")
    try:
        user_dict: Optional[Dict[str, Any]] = await users_collection.find_one(
            {"google_id": google_id}
        )
        if not user_dict:
            return None
        return User(**user_dict)
    except Exception as e:
        logger.error(f"error retrieving user with google_id: {google_id}: {str(e)}")
        return None


async def check_email_exists(email: str, exclude_user_id: Optional[str] = None) -> bool:
    """
    check if an email is already registered.
    """
    if users_collection is None:
        raise HTTPException(status_code=500, detail="database is not initialized")
    query = {"email": email}
    if exclude_user_id:
        query["_id"] = {"$ne": ObjectId(exclude_user_id)}
    
    existing_user = await users_collection.find_one(query)
    return existing_user is not None

