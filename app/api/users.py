"""User management and API key endpoints."""

from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from app.auth.middleware import require_auth
from app.auth.utils import hash_password
from app.database.db import db
from app.database.models import APIKey
from datetime import datetime
import secrets

users_bp = Blueprint("users", url_prefix="/api")


@users_bp.get("/users/<user_id:int>/api-keys")
@require_auth
async def get_user_api_keys(request: Request, user_id: int):
    """Get all API keys for a user."""
    # Users can only view their own keys, admins can view any
    auth_user = request.ctx.user
    if auth_user.id != user_id and auth_user.role != 'admin':
        return json(
            {"success": False, "error": "Unauthorized"},
            status=403
        )
    
    keys = await db.get_user_api_keys(user_id)
    
    return json({
        "success": True,
        "keys": [
            {
                "id": key.id,
                "key_id": key.key_id,
                "name": key.name,
                "last_used": key.last_used,
                "created_at": key.created_at,
                "expires_at": key.expires_at,
                "secret_viewed": key.secret_viewed,
                "pending_secret": key.pending_secret if not key.secret_viewed else None,
            }
            for key in keys
        ]
    })


@users_bp.post("/users/<user_id:int>/api-keys")
@require_auth
async def generate_api_key(request: Request, user_id: int):
    """Generate a new API key for a user (admin only)."""
    # Only admins can generate API keys
    auth_user = request.ctx.user
    if auth_user.role != 'admin':
        return json(
            {"success": False, "error": "Unauthorized - only admins can generate API keys"},
            status=403
        )
    
    try:
        data = request.json
        name = data.get("name", "Unnamed Key")
        
        # Generate key_id and key_secret
        key_id = f"key_{secrets.token_urlsafe(16)}"
        key_secret = secrets.token_urlsafe(32)
        
        # Hash the secret before storing
        key_secret_hash = hash_password(key_secret)
        
        # Create API key
        now = datetime.utcnow().isoformat()
        api_key = APIKey(
            key_id=key_id,
            key_secret_hash=key_secret_hash,
            user_id=user_id,
            name=name,
            last_used=None,
            created_at=now,
            expires_at=None,  # No expiration for now
            secret_viewed=False,
            pending_secret=key_secret,  # Store unhashed secret temporarily in DB
        )
        
        created_key = await db.create_api_key(api_key)
        
        if created_key:
            # Return the secret to admin
            return json({
                "success": True,
                "key_id": key_id,
                "key_secret": key_secret,  # Shown to admin
                "name": name,
                "message": "API key generated successfully. The user will see the secret in their dashboard."
            })
        else:
            return json(
                {"success": False, "error": "Failed to generate API key"},
                status=500
            )
            
    except Exception as e:
        return json(
            {"success": False, "error": str(e)},
            status=500
        )


@users_bp.post("/api-keys/<key_id>/mark-viewed")
@require_auth
async def mark_secret_viewed(request: Request, key_id: str):
    """Mark an API key secret as viewed by the user."""
    # Get the key
    api_key = await db.get_api_key(key_id)
    if not api_key:
        return json(
            {"success": False, "error": "API key not found"},
            status=404
        )
    
    # Users can only mark their own keys as viewed
    auth_user = request.ctx.user
    if auth_user.id != api_key.user_id and auth_user.role != 'admin':
        return json(
            {"success": False, "error": "Unauthorized"},
            status=403
        )
    
    # Mark as viewed (this will also clear pending_secret in DB)
    success = await db.mark_api_key_viewed(key_id)
    
    if success:
        return json({
            "success": True,
            "message": "Secret marked as viewed"
        })
    else:
        return json(
            {"success": False, "error": "Failed to mark secret as viewed"},
            status=500
        )


@users_bp.post("/api-keys/<key_id>/regenerate-secret")
@require_auth
async def regenerate_secret(request: Request, key_id: str):
    """Regenerate the secret for an API key."""
    # Get the key
    api_key = await db.get_api_key(key_id)
    if not api_key:
        return json(
            {"success": False, "error": "API key not found"},
            status=404
        )
    
    # Users can regenerate their own keys
    auth_user = request.ctx.user
    if auth_user.id != api_key.user_id and auth_user.role != 'admin':
        return json(
            {"success": False, "error": "Unauthorized"},
            status=403
        )
    
    try:
        # Generate new secret
        new_secret = secrets.token_urlsafe(32)
        new_secret_hash = hash_password(new_secret)
        
        # Update the key with new secret
        success = await db.regenerate_api_key_secret(key_id, new_secret_hash, new_secret)
        
        if success:
            return json({
                "success": True,
                "message": "Secret regenerated successfully. View it in your dashboard before it's hidden."
            })
        else:
            return json(
                {"success": False, "error": "Failed to regenerate secret"},
                status=500
            )
    except Exception as e:
        return json(
            {"success": False, "error": str(e)},
            status=500
        )


@users_bp.delete("/api-keys/<key_id>")
@require_auth
async def delete_api_key(request: Request, key_id: str):
    """Delete an API key (admin only)."""
    # Get the key to check it exists
    api_key = await db.get_api_key(key_id)
    if not api_key:
        return json(
            {"success": False, "error": "API key not found"},
            status=404
        )
    
    # Only admins can delete API keys
    auth_user = request.ctx.user
    if auth_user.role != 'admin':
        return json(
            {"success": False, "error": "Unauthorized - only admins can revoke API keys"},
            status=403
        )
    
    success = await db.delete_api_key(key_id)
    
    if success:
        return json({
            "success": True,
            "message": "API key deleted successfully"
        })
    else:
        return json(
            {"success": False, "error": "Failed to delete API key"},
            status=500
        )


@users_bp.get("/users/<user_id:int>/devices")
@require_auth
async def get_user_devices(request: Request, user_id: int):
    """Get all devices owned by a user."""
    # Users can only view their own devices, admins can view any
    auth_user = request.ctx.user
    if auth_user.id != user_id and auth_user.role != 'admin':
        return json(
            {"success": False, "error": "Unauthorized"},
            status=403
        )
    
    devices = await db.get_user_devices(user_id)
    
    return json({
        "success": True,
        "devices": [
            {
                "id": d.id,
                "device_id": d.device_id,
                "name": d.name,
                "address": d.address,
                "lat": d.lat,
                "lon": d.lon,
                "timezone": d.timezone,
                "last_seen": d.last_seen,
                "created_at": d.created_at,
            }
            for d in devices
        ]
    })

