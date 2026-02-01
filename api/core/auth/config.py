"""
Better Auth configuration and constants.
"""
import os
from dotenv import load_dotenv
from core.utils.logger import get_logger
from api.core.auth.enums import JWTAlgorithm

load_dotenv()

logger = get_logger("auth.config")

# better-auth jwt secret
BETTER_AUTH_SECRET = os.getenv("BETTER_AUTH_SECRET")
JWT_ALGORITHM = JWTAlgorithm(os.getenv("JWT_ALGORITHM", JWTAlgorithm.HS256))
BETTER_AUTH_URL = os.getenv("BETTER_AUTH_URL", "http://localhost:3000")

if not BETTER_AUTH_SECRET:
    logger.warning("better-auth secret not found. jwt verification may fail.")

