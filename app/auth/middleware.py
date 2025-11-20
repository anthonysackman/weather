"""Authentication middleware for Sanic."""

from functools import wraps
from sanic.response import json
from sanic.request import Request
from app.auth.utils import parse_basic_auth, verify_password
from app.database.db import db
import logging

logger = logging.getLogger(__name__)


def require_auth(f):
    """Decorator to require authentication for a route."""

    @wraps(f)
    async def decorated_function(request: Request, *args, **kwargs):
        # Get Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return json(
                {"success": False, "error": "Authentication required"},
                status=401,
                headers={"WWW-Authenticate": 'Basic realm="Weather Display Admin"'},
            )

        # Parse credentials
        credentials = parse_basic_auth(auth_header)
        if not credentials:
            return json(
                {"success": False, "error": "Invalid authentication format"},
                status=401,
                headers={"WWW-Authenticate": 'Basic realm="Weather Display Admin"'},
            )

        username, password = credentials

        # Verify credentials
        user = await db.get_user(username)
        if not user or not verify_password(password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {username}")
            return json(
                {"success": False, "error": "Invalid credentials"},
                status=401,
                headers={"WWW-Authenticate": 'Basic realm="Weather Display Admin"'},
            )

        # Add user to request context
        request.ctx.user = user

        # Call the actual route handler
        return await f(request, *args, **kwargs)

    return decorated_function

