from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from api.data.users import User, SafeUser, RegisterUserRequest, \
                        LoginUserRequest, UserLoginResponse, ChangePasswordRequest, \
                        UpdateUserRequest, UpdateSubscriptionRequest, Subscription, \
                        PaymentMethod, CreatePaymentMethodRequest, UpdatePaymentMethodRequest, \
                        PaymentMethodResponse, UpdateCustomerIdRequest
from api.core.db import users_collection, payment_methods_collection
from bson.objectid import ObjectId
from api.core.auth import get_hashed_password, verify_password, sign_jwt, JWTBearer
from core.utils.logger import get_logger
from datetime import datetime
from typing import List
import os
from pathlib import Path
from api.utils.error_wrapper import error_wrapper

logger = get_logger("users")
router = APIRouter(tags=["users"])

@router.post("/register")
@error_wrapper("register user")
async def register(request: RegisterUserRequest) -> SafeUser:
    user = await users_collection.find_one({"email": request.email})
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # hash password
    hashed_password = get_hashed_password(request.password)
    # create user object
    user = User(username=request.username, 
                email=request.email, 
                password=hashed_password)
    # insert user into database
    db_user = await users_collection.insert_one(user.model_dump(mode="json"))
    # update user id
    await users_collection.update_one(
            {"_id": db_user.inserted_id},
            {"$set": {"id": str(db_user.inserted_id)}}
        )
    # return user
    user.id = str(db_user.inserted_id)
    return User(**user.model_dump(mode="json"))

@router.post("/login")
@error_wrapper("login user")
async def login(request: LoginUserRequest) -> UserLoginResponse:
    user = await users_collection.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    if not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    token = sign_jwt(user["id"])
    return UserLoginResponse(**user, token=token)

@router.get("/me", dependencies=[Depends(JWTBearer())])
@error_wrapper("get user")
async def me(user_id: str = Depends(JWTBearer())) -> User:
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@router.put("/me", dependencies=[Depends(JWTBearer())])
@error_wrapper("update user")
async def update_user(
    request: UpdateUserRequest,
    user_id: str = Depends(JWTBearer())
) -> User:
    # update user information (username and/or email)
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # check if email is being updated and if it's already taken
    if request.email and request.email != user.get("email"):
        existing_user = await users_collection.find_one({"email": request.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # build update data
    update_data = {"updated_at": datetime.now()}
    if request.username is not None:
        update_data["username"] = request.username
    if request.email is not None:
        update_data["email"] = request.email
    
    # update user in database
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    # fetch and return updated user
    updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info(f"User updated: {user_id}")
    
    return User(**updated_user)

@router.post("/change-password", dependencies=[Depends(JWTBearer())])
@error_wrapper("change password")
async def change_password(
    request: ChangePasswordRequest,
    user_id: str = Depends(JWTBearer())
) -> dict:
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # verify current password
    if not verify_password(request.current_password, user["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # hash new password
    hashed_password = get_hashed_password(request.new_password)
    
    # update password
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": hashed_password, "updated_at": datetime.now()}}
    )
    
    return {"message": "Password changed successfully"}

@router.post("/payment-methods", dependencies=[Depends(JWTBearer())])
@error_wrapper("create payment method")
async def create_payment_method(
    request: CreatePaymentMethodRequest,
    user_id: str = Depends(JWTBearer())
) -> PaymentMethodResponse:
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # if this is set as default, unset other default payment methods
    if request.is_default:
        await payment_methods_collection.update_many(
            {"user_id": user_id, "is_default": True},
            {"$set": {"is_default": False, "updated_at": datetime.now()}}
        )
    
    # create payment method
    payment_method = PaymentMethod(
        user_id=user_id,
        stripe_payment_method_id=request.stripe_payment_method_id,
        type=request.type,
        card=request.card,
        is_default=request.is_default
    )
    
    # insert into database
    db_payment_method = await payment_methods_collection.insert_one(
        payment_method.model_dump(mode="json", exclude={"id"})
    )
    
    # update payment method id
    await payment_methods_collection.update_one(
        {"_id": db_payment_method.inserted_id},
        {"$set": {"id": str(db_payment_method.inserted_id)}}
    )
    
    # fetch and return the created payment method
    created_payment_method = await payment_methods_collection.find_one(
        {"_id": db_payment_method.inserted_id}
    )
    
    return PaymentMethodResponse(**created_payment_method, id=str(created_payment_method["_id"]))

@router.get("/payment-methods", dependencies=[Depends(JWTBearer())])
@error_wrapper("get payment methods")
async def get_payment_methods(
    user_id: str = Depends(JWTBearer())
) -> List[PaymentMethodResponse]:
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    payment_methods = await payment_methods_collection.find({"user_id": user_id}).to_list(length=100)
    
    return [
        PaymentMethodResponse(**pm, id=str(pm["_id"]))
        for pm in payment_methods
    ]

@router.get("/payment-methods/{payment_method_id}", dependencies=[Depends(JWTBearer())])
@error_wrapper("get payment method")
async def get_payment_method(
    payment_method_id: str,
    user_id: str = Depends(JWTBearer())
) -> PaymentMethodResponse:
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    payment_method = await payment_methods_collection.find_one({
        "_id": ObjectId(payment_method_id),
        "user_id": user_id
    })
    
    if not payment_method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    return PaymentMethodResponse(**payment_method, id=str(payment_method["_id"]))

@router.put("/payment-methods/{payment_method_id}", dependencies=[Depends(JWTBearer())])
@error_wrapper("update payment method")
async def update_payment_method(
    payment_method_id: str,
    request: UpdatePaymentMethodRequest,
    user_id: str = Depends(JWTBearer())
) -> PaymentMethodResponse:
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    payment_method = await payment_methods_collection.find_one({
        "_id": ObjectId(payment_method_id),
        "user_id": user_id
    })
    
    if not payment_method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    # if setting as default, unset other default payment methods
    if request.is_default is not None and request.is_default:
        await payment_methods_collection.update_many(
            {"user_id": user_id, "is_default": True, "_id": {"$ne": ObjectId(payment_method_id)}},
            {"$set": {"is_default": False, "updated_at": datetime.now()}}
        )
    
    # build update dict
    update_data = {"updated_at": datetime.now()}
    if request.is_default is not None:
        update_data["is_default"] = request.is_default
    if request.card is not None:
        update_data["card"] = request.card.model_dump(mode="json")
    
    # Update payment method
    await payment_methods_collection.update_one(
        {"_id": ObjectId(payment_method_id)},
        {"$set": update_data}
    )
    
    # Fetch and return updated payment method
    updated_payment_method = await payment_methods_collection.find_one(
        {"_id": ObjectId(payment_method_id)}
    )
    
    return PaymentMethodResponse(**updated_payment_method, id=str(updated_payment_method["_id"]))

@router.delete("/payment-methods/{payment_method_id}", dependencies=[Depends(JWTBearer())])
@error_wrapper("delete payment method")
async def delete_payment_method(
    payment_method_id: str,
    user_id: str = Depends(JWTBearer())
) -> dict:
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    payment_method = await payment_methods_collection.find_one({
        "_id": ObjectId(payment_method_id),
        "user_id": user_id
    })
    
    if not payment_method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    # delete payment method
    await payment_methods_collection.delete_one({"_id": ObjectId(payment_method_id)})
    
    return {"message": "Payment method deleted successfully"}

@router.post("/profile-picture", dependencies=[Depends(JWTBearer())])
@error_wrapper("upload profile picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    user_id: str = Depends(JWTBearer())
) -> dict:
    # upload or update user profile picture
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # validate file type
    allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # create user directory if it doesn't exist
    temp_dir = "temp"
    user_dir = os.path.join(temp_dir, "users", user_id)
    Path(user_dir).mkdir(parents=True, exist_ok=True)
    
    # delete old profile picture if it exists
    old_profile_picture = user.get("profile_picture")
    if old_profile_picture:
        old_file_path = os.path.join(temp_dir, old_profile_picture)
        if os.path.exists(old_file_path):
            try:
                os.remove(old_file_path)
                logger.info(f"Deleted old profile picture: {old_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete old profile picture: {e}")
    
    # save new profile picture
    profile_picture_filename = f"profile_picture{file_ext}"
    profile_picture_path = os.path.join(user_dir, profile_picture_filename)
    
    with open(profile_picture_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    
    # update user in database
    profile_picture_relative_path = os.path.join("users", user_id, profile_picture_filename)
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "profile_picture": profile_picture_relative_path,
            "updated_at": datetime.now()
        }}
    )
    
    logger.info(f"Profile picture uploaded for user {user_id}: {profile_picture_relative_path}")
    
    return {
        "message": "Profile picture uploaded successfully",
        "profile_picture": profile_picture_relative_path
    }

@router.get("/profile-picture", dependencies=[Depends(JWTBearer())])
@error_wrapper("get profile picture")
async def get_profile_picture(
    user_id: str = Depends(JWTBearer())
) -> dict:
    """Get user profile picture URL"""
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile_picture = user.get("profile_picture")
    if not profile_picture:
        raise HTTPException(status_code=404, detail="Profile picture not found")
    
    # Return the relative path which can be accessed via /media endpoint
    return {
        "profile_picture": profile_picture,
        "url": f"/media/{profile_picture}"
    }

@router.delete("/profile-picture", dependencies=[Depends(JWTBearer())])
@error_wrapper("delete profile picture")
async def delete_profile_picture(
    user_id: str = Depends(JWTBearer())
) -> dict:
    """Delete user profile picture"""
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile_picture = user.get("profile_picture")
    if not profile_picture:
        raise HTTPException(status_code=404, detail="Profile picture not found")
    
    # delete file from filesystem
    file_path = os.path.join("temp", profile_picture)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Deleted profile picture: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete profile picture file: {e}")
    
    # update user in database
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "profile_picture": None,
            "updated_at": datetime.now()
        }}
    )
    
    logger.info(f"Profile picture deleted for user {user_id}")
    
    return {"message": "Profile picture deleted successfully"}

@router.put("/subscription", dependencies=[Depends(JWTBearer())])
@error_wrapper("update subscription")
async def update_subscription(
    request: UpdateSubscriptionRequest,
    user_id: str = Depends(JWTBearer())
) -> User:
    """Update user's payment plan/subscription"""
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # validate subscription value
    if request.subscription not in [Subscription.FREE, Subscription.PRO, Subscription.ENTERPRISE]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid subscription. Must be one of: {Subscription.FREE}, {Subscription.PRO}, {Subscription.ENTERPRISE}"
        )
    
    # update user subscription
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "current_subscription": request.subscription,
            "updated_at": datetime.now()
        }}
    )
    
    # fetch and return updated user
    updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info(f"Subscription updated for user {user_id}: {request.subscription}")
    
    return User(**updated_user)

@router.put("/customer-id", dependencies=[Depends(JWTBearer())])
@error_wrapper("update customer id")
async def update_customer_id(
    request: UpdateCustomerIdRequest,
    user_id: str = Depends(JWTBearer())
) -> User:
    """update user's stripe customer id in database"""
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update customer ID
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "stripe_customer_id": request.stripe_customer_id,
            "updated_at": datetime.now()
        }}
    )
    
    # fetch and return updated user
    updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info(f"Customer ID updated for user {user_id}: {request.stripe_customer_id}")
    
    return User(**updated_user)

@router.get("/customer-id", dependencies=[Depends(JWTBearer())])
@error_wrapper("get customer id")
async def get_customer_id(
    user_id: str = Depends(JWTBearer())
) -> dict:
    """Get user's Stripe customer ID"""
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "stripe_customer_id": user.get("stripe_customer_id")
    }

@router.put("/customer-id-by-email", dependencies=[Depends(JWTBearer())])
@error_wrapper("update customer id by email")
async def update_customer_id_by_email(
    request: UpdateCustomerIdRequest,
    email: str,
    user_id: str = Depends(JWTBearer())
) -> dict:
    """Update user's Stripe customer ID by email (for webhook use)"""
    # only allow if the email matches the authenticated user's email
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("email") != email:
        raise HTTPException(status_code=403, detail="Email does not match authenticated user")
    
    # update customer id
    await users_collection.update_one(
        {"email": email},
        {"$set": {
            "stripe_customer_id": request.stripe_customer_id,
            "updated_at": datetime.now()
        }}
    )
    
    logger.info(f"Customer ID updated for user with email {email}: {request.stripe_customer_id}")
    
    return {"message": "Customer ID updated successfully"}
