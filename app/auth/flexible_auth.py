"""Flexible authentication supporting multiple methods."""

from functools import wraps
from typing import List, Optional
from sanic.response import json
from sanic.request import Request
from app.auth.utils import parse_basic_auth, verify_password
from app.database.db import db
from app.database.models import User
import logging

logger = logging.getLogger(__name__)


async def authenticate_session(request: Request) -> Optional[User]:
    """Authenticate using Basic Auth (session-style)."""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Basic "):
        return None
    
    # Parse credentials
    credentials = parse_basic_auth(auth_header)
    if not credentials:
        return None
    
    username, password = credentials
    
    # Verify credentials
    user = await db.get_user(username)
    if not user or not verify_password(password, user.password_hash):
        logger.warning(f"Failed session auth for user: {username}")
        return None
    
    logger.info(f"Session auth successful for user: {username}")
    return user


async def authenticate_api_key(request: Request) -> Optional[User]:
    """Authenticate using API Key (Bearer token)."""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    # Extract token (format: "Bearer key_id:key_secret")
    token = auth_header.replace("Bearer ", "").strip()
    
    if ":" not in token:
        logger.warning("Invalid API key format (missing colon)")
        return None
    
    key_id, key_secret = token.split(":", 1)
    
    # Get API key from database
    api_key = await db.get_api_key(key_id)
    if not api_key:
        logger.warning(f"API key not found: {key_id}")
        return None
    
    # Verify secret
    if not verify_password(key_secret, api_key.key_secret_hash):
        logger.warning(f"Invalid secret for API key: {key_id}")
        return None
    
    # Update last_used timestamp
    await db.update_api_key_last_used(key_id)
    
    # Get the user who owns this API key
    user = await db.get_user_by_id(api_key.user_id)
    if not user:
        logger.error(f"User not found for API key: {key_id}")
        return None
    
    logger.info(f"API key auth successful for user: {user.username} (key: {key_id})")
    return user


def require_auth(methods: List[str] = None, roles: List[str] = None):
    """
    Flexible authentication decorator.
    
    Args:
        methods: List of auth methods to accept. Options: ["session", "api_key"]
                 Default: ["session", "api_key"] (accepts both)
        roles: List of required roles. Options: ["admin", "user"]
               Default: None (any authenticated user)
    
    Examples:
        @require_auth()  # Accept any auth method, any role
        @require_auth(methods=["session"])  # Session only
        @require_auth(methods=["api_key"])  # API key only
        @require_auth(roles=["admin"])  # Any auth, admin only
        @require_auth(methods=["session"], roles=["admin"])  # Session + admin
    """
    if methods is None:
        methods = ["session", "api_key"]  # Accept both by default
    
    def decorator(f):
        @wraps(f)
        async def decorated_function(request: Request, *args, **kwargs):
            user = None
            auth_method = None
            
            # Try each authentication method in order
            if "session" in methods:
                user = await authenticate_session(request)
                if user:
                    auth_method = "session"
            
            if not user and "api_key" in methods:
                user = await authenticate_api_key(request)
                if user:
                    auth_method = "api_key"
            
            # If no auth succeeded
            if not user:
                # Determine WWW-Authenticate header
                auth_challenges = []
                if "session" in methods:
                    auth_challenges.append('Basic realm="Weather Display"')
                if "api_key" in methods:
                    auth_challenges.append('Bearer realm="Weather Display API"')
                
                return json(
                    {
                        "success": False,
                        "error": "Authentication required",
                        "hint": "Use Basic Auth (username:password) or Bearer token (key_id:key_secret)"
                    },
                    status=401,
                    headers={"WWW-Authenticate": ", ".join(auth_challenges)},
                )
            
            # Check role requirements
            if roles and user.role not in roles:
                return json(
                    {
                        "success": False,
                        "error": f"Insufficient permissions. Required role: {', '.join(roles)}"
                    },
                    status=403,
                )
            
            # Add user and auth method to request context
            request.ctx.user = user
            request.ctx.auth_method = auth_method
            
            # Call the actual route handler
            return await f(request, *args, **kwargs)
        
        return decorated_function
    
    return decorator

