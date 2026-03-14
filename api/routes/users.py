from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, WebSocket, WebSocketDisconnect
from api.core.auth import BetterAuthBearer
from core.utils.logger import get_logger
from api.core.signals import listen_for_messages
import os
import asyncio
from pathlib import Path
from api.utils.error_wrapper import error_wrapper
from core.utils.config_loader import config

logger = get_logger("users")
router = APIRouter(tags=["users"])

@router.post("/profile-picture", dependencies=[Depends(BetterAuthBearer())])
@error_wrapper("upload profile picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    user_id: str = Depends(BetterAuthBearer())
) -> dict:
    # validate file type
    allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # create user directory if it doesn't exist
    output_dir = str(config.output_directory)
    user_dir = os.path.join(output_dir, "users", user_id)
    Path(user_dir).mkdir(parents=True, exist_ok=True)
    
    # try to delete old profile picture if it exists
    for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
        old_file_path = os.path.join(user_dir, f"profile_picture{ext}")
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
    
    # profile picture path (frontend will handle database update)
    profile_picture_relative_path = os.path.join("users", user_id, profile_picture_filename)
    
    logger.info(f"Profile picture uploaded for user {user_id}: {profile_picture_relative_path}")
    
    return {
        "message": "Profile picture uploaded successfully",
        "profile_picture": profile_picture_relative_path
    }


async def send_user_video_pipeline_ws_messages(websocket: WebSocket, user_id: str) -> None:
    """
    send pipeline updates to a user for all their pipelines.
    listens to the pipeline-tasks channel and filters messages by user_id.
    """
    logger.info(f"received request to send pipeline ws messages for user {user_id}")
    listener_name = f"user-ws-listener-{user_id}"
    try:
        async for message in listen_for_messages(listener_name):
            # filter messages for this specific user
            message_user_id = message.get("user_id")
            
            if message_user_id == user_id:
                logger.info(f"received message for user {user_id}: {message}")
                await websocket.send_json(message)
                logger.debug(f"sent message to user {user_id} for pipeline {message.get('pipeline_id')}")
            else:
                logger.debug(f"filtered out message for user {user_id}: user_id={message_user_id}")
    except (WebSocketDisconnect, Exception) as e:
        logger.info(f"stopped sending pipeline ws messages for user {user_id}: {type(e).__name__}")

@router.websocket("/{user_id}/video-pipelines/ws", name="user video pipeline state socket")
async def user_video_pipeline_state_socket(
    user_id: str,
    websocket: WebSocket,
):
    """
    websocket endpoint for real-time pipeline updates for all pipelines belonging to a user.
    """
    logger.info(f"received request to connect to user pipeline state socket for user {user_id}")
    
    try:
        await websocket.accept()
        logger.info(f"websocket accepted for user {user_id}")
        
        # send updates for all user's pipelines
        await send_user_video_pipeline_ws_messages(websocket, user_id)
            
    except (WebSocketDisconnect, asyncio.CancelledError) as e:
        logger.info(f"connection to user pipeline state socket for user {user_id} {type(e).__name__.lower()}")
    except Exception as e:
        logger.error(f"error connecting to user pipeline state socket for user {user_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass

