"""
Better Auth Bearer token authentication middleware.
"""
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.utils.logger import get_logger
from api.core.auth.jwt_verifier import verify_better_auth_jwt

logger = get_logger("auth.bearer")


class BetterAuthBearer(HTTPBearer):
    """
    bearer authentication middleware for better-auth jwt tokens.
    replaces the old JWTBearer class to work with better-auth tokens.
    """
    def __init__(self, auto_error: bool = True):
        super(BetterAuthBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> str:
        """
        verify better-auth jwt token and return user ID.
        """
        credentials: HTTPAuthorizationCredentials | None = await super(BetterAuthBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme")
            
            # verify the better-auth jwt token
            decoded_token = await verify_better_auth_jwt(credentials.credentials)
            if not decoded_token:
                raise HTTPException(status_code=403, detail="Invalid or expired token")
            
            # extract user ID from token
            user_id = decoded_token.get("id")
            if not user_id:
                logger.error(f"user id not found in token: {decoded_token}")
                raise HTTPException(status_code=403, detail="Invalid token: user ID not found")
            
            return user_id
        else:
            raise HTTPException(status_code=403, detail="Invalid authentication credentials")

