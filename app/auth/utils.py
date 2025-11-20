"""Authentication utilities."""

import bcrypt
import base64
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False


def parse_basic_auth(auth_header: str) -> Optional[Tuple[str, str]]:
    """Parse HTTP Basic Auth header.
    
    Args:
        auth_header: The Authorization header value
        
    Returns:
        Tuple of (username, password) or None if invalid
    """
    try:
        if not auth_header.startswith("Basic "):
            return None

        # Decode base64 credentials
        encoded_credentials = auth_header[6:]  # Remove "Basic " prefix
        decoded = base64.b64decode(encoded_credentials).decode("utf-8")

        # Split username:password
        if ":" not in decoded:
            return None

        username, password = decoded.split(":", 1)
        return (username, password)

    except Exception as e:
        logger.error(f"Failed to parse Basic Auth header: {e}")
        return None

