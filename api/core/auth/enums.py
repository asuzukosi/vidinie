"""
jwt algorithm enums for better-auth.
"""
from enum import Enum

class JWTAlgorithm(str, Enum):
    """
    supported jwt algorithms for better-auth.
    """
    HS256 = "HS256"  # symmetric algorithm using shared secret
    ED25519 = "EdDSA"  # asymmetric algorithm using Ed25519 (EdDSA)

