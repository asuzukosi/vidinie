"""
Better Auth authentication module.
Provides JWT verification and Bearer token authentication for Better Auth tokens.
"""
from api.core.auth.bearer import BetterAuthBearer
from api.core.auth.jwt_verifier import verify_better_auth_jwt
from api.core.auth.jwks import fetch_jwks, get_jwt_public_key
from api.core.auth.config import BETTER_AUTH_SECRET, JWT_ALGORITHM, BETTER_AUTH_URL
from api.core.auth.enums import JWTAlgorithm

__all__ = [
    "BetterAuthBearer",
    "verify_better_auth_jwt",
    "fetch_jwks",
    "get_jwt_public_key",
    "BETTER_AUTH_SECRET",
    "JWT_ALGORITHM",
    "BETTER_AUTH_URL",
    "JWTAlgorithm",
]

