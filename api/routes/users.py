from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from api.helpers.user_helpers import (
    get_user_by_id,
    update_user_in_db,
)
from api.core.auth import BetterAuthBearer
from core.utils.logger import get_logger
from datetime import datetime
import os
from pathlib import Path
from api.utils.error_wrapper import error_wrapper

logger = get_logger("users")
router = APIRouter(tags=["users"])

@router.post("/profile-picture", dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("upload profile picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    user_id: str = Depends(BetterAuthBearer())
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


