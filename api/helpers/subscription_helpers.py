from typing import Optional, Dict, Any, List
from bson.objectid import ObjectId
from fastapi import HTTPException
from api.data.users import Subscription
from api.core.db import subscriptions_collection
from core.utils.logger import get_logger
from datetime import datetime

logger = get_logger('subscription_helpers')

async def get_subscription_by_id(subscription_id: str, user_id: str) -> Subscription:
    """
    get a subscription by its id and user id.
    """
    if subscriptions_collection is None:
        raise HTTPException(status_code=500, detail="database is not initialized")
    try:
        subscription_dict: Optional[Dict[str, Any]] = await subscriptions_collection.find_one({
            "_id": ObjectId(subscription_id),
            "user_id": user_id
        })
        if not subscription_dict:
            raise HTTPException(status_code=404, detail="subscription not found")
        return Subscription(**subscription_dict)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"error retrieving subscription with id: {subscription_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"error retrieving subscription: {str(e)}")


async def get_subscriptions_for_user(user_id: str, limit: int = 100) -> List[Subscription]:
    """
    get all subscriptions for a user.
    """
    if subscriptions_collection is None:
        raise HTTPException(status_code=500, detail="database is not initialized")
    try:
        subscriptions = []
        async for sub_dict in subscriptions_collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit):
            subscriptions.append(Subscription(**sub_dict))
        return subscriptions
    except Exception as e:
        logger.error(f"error retrieving subscriptions for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving subscriptions: {str(e)}")


async def get_active_subscription_for_user(user_id: str) -> Optional[Subscription]:
    """
    get the active subscription for a user.
    """
    if subscriptions_collection is None:
        raise HTTPException(status_code=500, detail="database is not initialized")
    try:
        subscription_dict = await subscriptions_collection.find_one({
            "user_id": user_id,
            "status": {"$in": ["active", "trialing"]}
        }, sort=[("created_at", -1)])
        if not subscription_dict:
            return None
        return Subscription(**subscription_dict)
    except Exception as e:
        logger.error(f"error retrieving active subscription for user {user_id}: {str(e)}")
        return None


async def create_subscription_in_db(subscription: Subscription) -> Subscription:
    """
    create a new subscription in the database.
    """
    if subscriptions_collection is None:
        raise HTTPException(status_code=500, detail="database is not initialized")
    logger.info("creating new subscription in database")
    # insert subscription into database
    db_subscription = await subscriptions_collection.insert_one(
        subscription.model_dump(mode="json", exclude={"id"})
    )
    new_id = str(db_subscription.inserted_id)
    # update the subscription's id field
    subscription.id = new_id
    # put the database record with the new id
    await subscriptions_collection.update_one(
        {"_id": ObjectId(new_id)},
        {"$set": {"id": new_id}}
    )
    logger.info(f"subscription created successfully with id: {new_id}")
    return subscription


async def update_subscription_in_db(subscription_id: str, update_data: Dict[str, Any]) -> None:
    """
    update a subscription in the database.
    """
    if subscriptions_collection is None:
        raise HTTPException(status_code=500, detail="database is not initialized")
    update_data["updated_at"] = datetime.now()
    await subscriptions_collection.update_one(
        {"_id": ObjectId(subscription_id)},
        {"$set": update_data}
    )

