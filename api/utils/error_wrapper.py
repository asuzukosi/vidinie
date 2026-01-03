from pymongo.errors import DuplicateKeyError, OperationFailure, ConnectionFailure
from fastapi import HTTPException
from core.utils.logger import get_logger
from functools import wraps
from typing import Callable
import inspect

logger = get_logger("error_wrapper")

def error_wrapper(operation_name: str = None):
    """
    decorator to wrap async endpoint functions with error handling.
    usage:
        @error_wrapper("register user")
        async def register(request: RegisterUserRequest):
            ...
    or with default operation name:
        @error_wrapper()
        async def some_endpoint():
            ...
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__.replace("_", " ")
        
        # check if function is async
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except HTTPException:
                    # re-raise http exceptions as-is (they're intentional)
                    raise
                except (DuplicateKeyError, OperationFailure, ConnectionFailure) as e:
                    logger.error(f"Database error in {op_name}: {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to {op_name} due to database error")
                except Exception as e:
                    logger.error(f"Failed to {op_name}: {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to {op_name}")
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except HTTPException:
                    # re-raise http exceptions as-is (they're intentional)
                    raise
                except (DuplicateKeyError, OperationFailure, ConnectionFailure) as e:
                    logger.error(f"Database error in {op_name}: {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to {op_name} due to database error")
                except Exception as e:
                    logger.error(f"Failed to {op_name}: {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to {op_name}")
            return sync_wrapper
    return decorator