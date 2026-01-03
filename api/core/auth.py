import os
import time
from typing import Dict
from core.utils.logger import get_logger
import jwt
from dotenv import load_dotenv
import bcrypt
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials



logger = get_logger("auth")
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION"))

DAY = 86400

def sign_jwt(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": time.time() + (JWT_EXPIRATION * DAY)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decode_jwt(token: str) -> Dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token
    except jwt.ExpiredSignatureError:
        logger.error("token is expired")
        return None
    except jwt.InvalidTokenError:
        logger.error("token is invalid")
        return None
    except Exception as e:
        logger.error(f"error decoding jwt: {e}")
        return None
    
def get_hashed_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


class JWTBearer(HTTPBearer):
    # bearer authentication middlware
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        credentials: HTTPAuthorizationCredentials | None = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme")
            decoded_token = decode_jwt(credentials.credentials)
            if not decoded_token:
                raise HTTPException(status_code=403, detail="Invalid token")
            return decoded_token["user_id"]
        else:
            raise HTTPException(status_code=403, detail="invalid authentication credentials")
        