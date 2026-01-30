"""
JWKS (JSON Web Key Set) fetching and key management for Better Auth.
Handles fetching public keys from Better Auth's JWKS endpoint and caching them.
"""
from typing import Dict, Optional
from core.utils.logger import get_logger
import httpx
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from api.core.auth.config import BETTER_AUTH_URL

logger = get_logger("auth.jwks")

# cache for jwks keys (keys don't change frequently, can be cached indefinitely)
_jwks_cache: Optional[Dict[str, str]] = None


async def fetch_jwks() -> Dict[str, str]:
    """
    fetch jwks (json web key set) from better-auth's jwks endpoint.
    returns a dictionary mapping kid to public key in pem format.
    """
    global _jwks_cache
    
    try:
        jwks_url = f"{BETTER_AUTH_URL}/api/auth/jwks"
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url, timeout=5.0)
            response.raise_for_status()
            jwks = response.json()
        
        # Convert JWKS keys to PEM format and cache them
        keys_dict = {}
        for key in jwks.get("keys", []):
            kid = key.get("kid")
            if not kid:
                continue
            
            # Convert Ed25519 JWK to PEM format
            # Ed25519 keys use OKP (Octet Key Pair) with crv="Ed25519"
            if key.get("kty") == "OKP" and key.get("crv") == "Ed25519":
                x = key.get("x")  # Public key point (base64url encoded)
                if x:
                    try:
                        # Decode base64url to bytes
                        # base64url doesn't use padding, but urlsafe_b64decode needs it
                        # Add padding if needed (base64url padding is optional)
                        missing_padding = len(x) % 4
                        if missing_padding:
                            x += "=" * (4 - missing_padding)
                        public_key_bytes = base64.urlsafe_b64decode(x)
                        
                        # Create Ed25519 public key object
                        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
                        
                        # Serialize to PEM format
                        public_key_pem = public_key.public_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PublicFormat.SubjectPublicKeyInfo
                        ).decode()
                        keys_dict[kid] = public_key_pem
                    except Exception as e:
                        logger.error(f"Error converting JWK to PEM for kid {kid}: {e}")
                        continue
        
        _jwks_cache = keys_dict
        logger.info(f"Fetched and cached {len(keys_dict)} JWKS keys")
        return keys_dict
    except Exception as e:
        logger.error(f"Error fetching JWKS: {e}")
        return _jwks_cache or {}


async def get_jwt_public_key(kid: str) -> Optional[str]:
    """
    get jwt public key from jwks cache or fetch from better-auth's jwks endpoint.
    if a new kid is encountered, fetches jwks again.
    """
    global _jwks_cache
    
    # check cache first 
    if _jwks_cache and kid in _jwks_cache:
        return _jwks_cache[kid]
    # if not in cache or cache is empty, fetch jwks
    # this handles the case where a new kid is encountered
    keys_dict = await fetch_jwks()
    return keys_dict.get(kid)

