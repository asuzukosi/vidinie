from broadcaster import Broadcast
import json
from typing import AsyncGenerator
from core.utils.logger import get_logger

logger = get_logger("signals")

broadcast = Broadcast("memory://")

async def connect_to_broadcast() -> bool:
    try:
        await broadcast.connect()
    except Exception as e:
        logger.error(f"Error connecting to broadcast: {e}")
        return False
    return True

async def disconnect_from_broadcast() -> bool:
    try:
        await broadcast.disconnect()
    except Exception as e:
        logger.error(f"Error disconnecting from broadcast: {e}")
        return False
    return True

async def broadcast_message(channel: str, message: dict) -> bool:
    data = json.dumps(message)
    try:
        await broadcast.publish(channel=channel, message=data)
    except Exception as e:
        logger.error(f"Error broadcasting message: {message} to channel {channel}: {e}")
        return False
    return True


async def listen_for_messages(channel: str, listener_name: str) -> AsyncGenerator[dict, None]:
    logger.info(f"listening for messages on channel {channel} with listener {listener_name}")
    async with broadcast.subscribe(channel=channel) as subscriber:
        message_count = 0
        async for event in subscriber:
            try:
                logger.info(f"listener {listener_name} received message {message_count} on channel {channel}")
                message_count += 1
                yield json.loads(event.message)
            except Exception as e:
                logger.error(f"listener {listener_name} error parsing message {message_count} on channel {channel}: {e}")
                continue

