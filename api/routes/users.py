from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from api.data.users import User, SafeUser, RegisterUserRequest, \
                        LoginUserRequest, UserLoginResponse, ChangePasswordRequest, \
                        UpdateUserRequest, UpdateSubscriptionRequest, SubscriptionType, Subscription, \
                        GoogleOAuthVerifiedRequest, UpdateCustomerIdRequest
from api.helpers.user_helpers import (
    get_user_by_id,
    get_user_by_email,
    get_user_by_google_id,
    update_user_in_db,
    create_user_in_db,
    check_email_exists
)
from api.helpers.subscription_helpers import (
    get_subscription_by_id,
    get_subscriptions_for_user,
    get_active_subscription_for_user,
)
from api.core.auth import get_hashed_password, verify_password, sign_jwt, JWTBearer
from core.utils.logger import get_logger
from datetime import datetime
from typing import List, Optional
import os
from pathlib import Path
from api.utils.error_wrapper import error_wrapper

logger = get_logger("users")
router = APIRouter(tags=["users"])

@router.post("/register")
@error_wrapper("register user")
async def register(request: RegisterUserRequest) -> SafeUser:
    # check if email already exists
    if await check_email_exists(request.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # hash password
    hashed_password = get_hashed_password(request.password)
    
    # create user object
    user = User(
        email=request.email, 
        password=hashed_password
    )
    
    # create user in database using helper
    user = await create_user_in_db(user)
    
    # return safe user (without password)
    return SafeUser(**user.model_dump(mode="json", exclude={"password"}))

@router.post("/login")
@error_wrapper("login user")
async def login(request: LoginUserRequest) -> UserLoginResponse:
    user = await get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    if not user.password:
        raise HTTPException(status_code=400, detail="Please use Google sign-in for this account")
    if not verify_password(request.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    token = sign_jwt(user.id)
    user_dict = user.model_dump(mode="json", exclude={"password"})
    return UserLoginResponse(**user_dict, token=token)

@router.post("/auth/google")
@error_wrapper("google oauth")
async def google_oauth(request: GoogleOAuthVerifiedRequest) -> UserLoginResponse:
    """
    handle google oauth authentication
    """
    try:
        # extract user information from verified request
        google_id = request.google_id
        email = request.email
        picture = request.picture
        email_verified = request.email_verified
        
        if not email:
            raise HTTPException(status_code=400, detail="email not provided")
        
        # check if user exists with this google id
        existing_user = await get_user_by_google_id(google_id)
        
        # if not found by google id, check by email
        if not existing_user:
            existing_user = await get_user_by_email(email)
        
        if existing_user:
            # user exists - log them in
            # update google id if not set (linking account)
            if not existing_user.google_id:
                existing_user.google_id = google_id
                if picture and not existing_user.profile_picture:
                    existing_user.profile_picture = picture
                existing_user.updated_at = datetime.now()
                await update_user_in_db(existing_user.id, existing_user)
            elif existing_user.google_id != google_id:
                raise HTTPException(status_code=400, detail="email already registered with different google account")
            
            # update email verification status if verified by google
            if email_verified and not existing_user.is_verified:
                existing_user.is_verified = True
                existing_user.updated_at = datetime.now()
                await update_user_in_db(existing_user.id, existing_user)
        else:
            # user doesn't exist - create new account
            user = User(
                email=email,
                password=None,  # no password for oauth users
                google_id=google_id,
                is_verified=email_verified,
                profile_picture=picture
            )
            existing_user = await create_user_in_db(user)
            logger.info(f"New user created via Google OAuth: {email}")
        
        # generate jwt token
        token = sign_jwt(existing_user.id)
        user_dict = existing_user.model_dump(mode="json", exclude={"password"})
        return UserLoginResponse(**user_dict, token=token)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Google OAuth: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/me", dependencies=[Depends(JWTBearer())])
@error_wrapper("get user")
async def me(user_id: str = Depends(JWTBearer())) -> User:
    user = await get_user_by_id(user_id)
    return user

@router.put("/me", dependencies=[Depends(JWTBearer())])
@error_wrapper("update user")
async def update_user(
    request: UpdateUserRequest,
    user_id: str = Depends(JWTBearer())
) -> User:
    # get user using helper
    user = await get_user_by_id(user_id)
    
    # check if email is being updated and if it's already taken
    if request.email and request.email != user.email:
        if await check_email_exists(request.email, exclude_user_id=user_id):
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = request.email
    
    # update timestamp
    user.updated_at = datetime.now()
    
    # update user in database using helper
    await update_user_in_db(user_id, user)
    
    logger.info(f"User updated: {user_id}")
    
    # fetch and return updated user
    return await get_user_by_id(user_id)

@router.post("/change-password", dependencies=[Depends(JWTBearer())])
@error_wrapper("change password")
async def change_password(
    request: ChangePasswordRequest,
    user_id: str = Depends(JWTBearer())
) -> dict:
    user = await get_user_by_id(user_id)
    
    # verify current password
    if not verify_password(request.current_password, user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # hash new password
    user.password = get_hashed_password(request.new_password)
    user.updated_at = datetime.now()
    
    # update password using helper
    await update_user_in_db(user_id, user)
    
    return {"message": "Password changed successfully"}

@router.get("/subscriptions", dependencies=[Depends(JWTBearer())])
@error_wrapper("get subscriptions")
async def get_subscriptions(
    user_id: str = Depends(JWTBearer())
) -> List[Subscription]:
    """Get all subscriptions for the current user"""
    # verify user exists using helper
    await get_user_by_id(user_id)
    
    # get subscriptions using helper
    subscriptions = await get_subscriptions_for_user(user_id)
    
    return [
        Subscription(**sub.model_dump(mode="json"), id=sub.id)
        for sub in subscriptions
    ]

@router.get("/subscriptions/active", dependencies=[Depends(JWTBearer())])
@error_wrapper("get active subscription")
async def get_active_subscription(
    user_id: str = Depends(JWTBearer())
) -> Optional[Subscription]:
    """Get the active subscription for the current user"""
    # verify user exists using helper
    await get_user_by_id(user_id)
    
    # get active subscription using helper
    subscription = await get_active_subscription_for_user(user_id)
    
    if not subscription:
        return None
    
    return Subscription(**subscription.model_dump(mode="json"), id=subscription.id)

@router.get("/subscriptions/{subscription_id}", dependencies=[Depends(JWTBearer())])
@error_wrapper("get subscription")
async def get_subscription(
    subscription_id: str,
    user_id: str = Depends(JWTBearer())
) -> Subscription:
    """Get a specific subscription by ID"""
    # verify user exists using helper
    await get_user_by_id(user_id)
    
    # get subscription using helper
    subscription = await get_subscription_by_id(subscription_id, user_id)
    
    return Subscription(**subscription.model_dump(mode="json"), id=subscription.id)

@router.post("/profile-picture", dependencies=[Depends(JWTBearer())])
@error_wrapper("upload profile picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    user_id: str = Depends(JWTBearer())
) -> dict:
    # get user using helper
    user = await get_user_by_id(user_id)
    
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
    old_profile_picture = user.profile_picture
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
    user.profile_picture = profile_picture_relative_path
    user.updated_at = datetime.now()
    await update_user_in_db(user_id, user)
    
    logger.info(f"Profile picture uploaded for user {user_id}: {profile_picture_relative_path}")
    
    return {
        "message": "Profile picture uploaded successfully",
        "profile_picture": profile_picture_relative_path
    }


@router.put("/subscription", dependencies=[Depends(JWTBearer())])
@error_wrapper("update subscription")
async def update_subscription(
    request: UpdateSubscriptionRequest,
    user_id: str = Depends(JWTBearer())
) -> User:
    """Update user's current subscription"""
    user = await get_user_by_id(user_id)
    
    # validate subscription value
    if request.subscription not in [SubscriptionType.STARTER, SubscriptionType.PROFESSIONAL]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid subscription. Must be one of: {SubscriptionType.STARTER}, {SubscriptionType.PROFESSIONAL}"
        )
    
    # update user subscription
    logger.info(f"updating subscription for user {user_id}: {request.subscription}")
    user.current_subscription = request.subscription
    # increment number of videos left
    if request.subscription == SubscriptionType.STARTER:
        user.num_videos_left = 5
    elif request.subscription == SubscriptionType.PROFESSIONAL:
        user.num_videos_left = 20
    user.updated_at = datetime.now()
    await update_user_in_db(user_id, user)
    
    logger.info(f"Subscription updated for user {user_id}: {request.subscription}")
    
    # fetch and return updated user
    return await get_user_by_id(user_id)

@router.put("/customer-id", dependencies=[Depends(JWTBearer())])
@error_wrapper("update customer id")
async def update_customer_id(
    request: UpdateCustomerIdRequest,
    user_id: str = Depends(JWTBearer())
) -> User:
    """update user's customer id"""
    user = await get_user_by_id(user_id)
    
    # update customer id
    user.stripe_customer_id = request.stripe_customer_id
    user.updated_at = datetime.now()
    await update_user_in_db(user_id, user)
    
    logger.info(f"customer id updated for user {user_id}: {request.stripe_customer_id}")
    
    # fetch and return updated user
    return await get_user_by_id(user_id)
