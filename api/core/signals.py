from broadcaster import Broadcast
import json
import os
from typing import AsyncGenerator, TypedDict
from enum import Enum
from core.utils.logger import get_logger

logger = get_logger("signals")
broadcast = Broadcast(os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379"))

# fixed channel for all pipeline messages
PIPELINE_TASKS_CHANNEL = "pipeline-tasks"

# status enum for broadcast messages - defined here to differentiate from application status types
class PipelineBroadcastStatus(str, Enum):
    """
    status values for pipeline broadcast messages.
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


# message type definitions for broadcast messages
class PipelineBroadcastMessageType(str, Enum):
    """
    fixed types for pipeline broadcast messages - represents the operation/stage.
    """
    PIPELINE = "pipeline"
    DOCUMENT_PROCESSING = "document_processing"
    CONTENT_ANALYSIS = "content_analysis"
    SCRIPT_GENERATION = "script_generation"
    VIDEO_GENERATION = "video_generation"
    IMAGE = "image"


class PipelineBroadcastMessage(TypedDict):
    """
    base structure for all pipeline broadcast messages.
    """
    type: str
    pipeline_id: str
    user_id: str
    status: str

async def connect_to_broadcast() -> bool:
    """
    connect to the broadcast channel.
    """
    try:
        await broadcast.connect()
    except Exception as e:
        logger.error(f"Error connecting to broadcast: {e}")
        return False
    return True

async def disconnect_from_broadcast() -> bool:
    """
    disconnect from the broadcast channel.
    """
    try:
        await broadcast.disconnect()
    except Exception as e:
        logger.error(f"Error disconnecting from broadcast: {e}")
        return False
    return True

async def broadcast_message(message: PipelineBroadcastMessage) -> bool:
    """
    broadcast a pipeline message to the fixed pipeline-tasks channel.
    all messages must include type, pipeline_id, user_id, and status.
    """
    # validate required fields
    if "type" not in message:
        logger.error(f"Message missing required field 'type': {message}")
        return False
    if "pipeline_id" not in message:
        logger.error(f"Message missing required field 'pipeline_id': {message}")
        return False
    if "user_id" not in message:
        logger.error(f"Message missing required field 'user_id': {message}")
        return False
    if "status" not in message:
        logger.error(f"Message missing required field 'status': {message}")
        return False
    
    data = json.dumps(message)
    try:
        await broadcast.publish(channel=PIPELINE_TASKS_CHANNEL, message=data)
        logger.debug(f"Broadcasted message type '{message['type']}' status '{message['status']}' for pipeline {message['pipeline_id']}")
    except Exception as e:
        logger.error(f"Error broadcasting message: {message} to channel {PIPELINE_TASKS_CHANNEL}: {e}")
        return False
    return True


async def listen_for_messages(listener_name: str) -> AsyncGenerator[PipelineBroadcastMessage, None]:
    """
    listen for messages on the fixed pipeline-tasks channel.
    """
    logger.info(f"listening for messages on channel {PIPELINE_TASKS_CHANNEL} with listener {listener_name}")
    async with broadcast.subscribe(channel=PIPELINE_TASKS_CHANNEL) as subscriber:
        message_count = 0
        async for event in subscriber:
            try:
                message = json.loads(event.message)
                logger.debug(f"listener {listener_name} received message {message_count} on channel {PIPELINE_TASKS_CHANNEL}: type={message.get('type')}, pipeline_id={message.get('pipeline_id')}")
                message_count += 1
                yield message
            except Exception as e:
                logger.error(f"listener {listener_name} error parsing message {message_count} on channel {PIPELINE_TASKS_CHANNEL}: {e}")
                continue

