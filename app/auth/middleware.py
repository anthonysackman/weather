"""Authentication middleware for Sanic.

DEPRECATED: This module is kept for backwards compatibility.
New code should use app.auth.flexible_auth.require_auth instead.
"""

from app.auth.flexible_auth import require_auth as flexible_require_auth
import logging

logger = logging.getLogger(__name__)


def require_auth(f):
    """
    Decorator to require authentication for a route.
    
    DEPRECATED: Use app.auth.flexible_auth.require_auth instead.
    This wrapper provides backwards compatibility by only accepting session auth.
    """
    # Use flexible auth with session-only for backwards compatibility
    return flexible_require_auth(methods=["session"])(f)

