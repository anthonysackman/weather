"""Admin-only API endpoints."""

from sanic import Blueprint
from sanic.request import Request
from sanic.response import json
from app.auth.middleware import require_auth
from app.database.db import db

admin_api_bp = Blueprint("admin_api", url_prefix="/api/admin")


@admin_api_bp.get("/users")
@require_auth
async def get_all_users(request: Request):
    """Get all users (admin only)."""
    user = request.ctx.user
    
    if user.role != 'admin':
        return json(
            {"success": False, "error": "Unauthorized - admin access required"},
            status=403
        )
    
    users = await db.get_all_users()
    
    return json({
        "success": True,
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "created_at": u.created_at,
                "updated_at": u.updated_at,
            }
            for u in users
        ]
    })


@admin_api_bp.put("/users/<user_id:int>/role")
@require_auth
async def update_user_role(request: Request, user_id: int):
    """Update user role (admin only)."""
    user = request.ctx.user
    
    if user.role != 'admin':
        return json(
            {"success": False, "error": "Unauthorized - admin access required"},
            status=403
        )
    
    # Prevent demoting yourself
    if user.id == user_id:
        return json(
            {"success": False, "error": "Cannot change your own role"},
            status=400
        )
    
    data = request.json
    new_role = data.get("role")
    
    if new_role not in ['user', 'admin']:
        return json(
            {"success": False, "error": "Invalid role. Must be 'user' or 'admin'"},
            status=400
        )
    
    success = await db.update_user_role(user_id, new_role)
    
    if success:
        return json({
            "success": True,
            "message": f"User role updated to {new_role}"
        })
    else:
        return json(
            {"success": False, "error": "Failed to update user role"},
            status=500
        )


@admin_api_bp.delete("/users/<user_id:int>")
@require_auth
async def delete_user(request: Request, user_id: int):
    """Delete user (admin only)."""
    user = request.ctx.user
    
    if user.role != 'admin':
        return json(
            {"success": False, "error": "Unauthorized - admin access required"},
            status=403
        )
    
    # Prevent deleting yourself
    if user.id == user_id:
        return json(
            {"success": False, "error": "Cannot delete your own account"},
            status=400
        )
    
    success = await db.delete_user(user_id)
    
    if success:
        return json({
            "success": True,
            "message": "User deleted successfully"
        })
    else:
        return json(
            {"success": False, "error": "Failed to delete user"},
            status=500
        )


@admin_api_bp.get("/api-keys")
@require_auth
async def get_all_api_keys(request: Request):
    """Get all API keys system-wide (admin only)."""
    user = request.ctx.user
    
    if user.role != 'admin':
        return json(
            {"success": False, "error": "Unauthorized - admin access required"},
            status=403
        )
    
    keys = await db.get_all_api_keys()
    
    # Get user info for each key
    keys_with_users = []
    for key in keys:
        user_info = await db.get_user_by_id(key.user_id)
        keys_with_users.append({
            "id": key.id,
            "key_id": key.key_id,
            "name": key.name,
            "user_id": key.user_id,
            "username": user_info.username if user_info else "Unknown",
            "last_used": key.last_used,
            "created_at": key.created_at,
            "expires_at": key.expires_at,
        })
    
    return json({
        "success": True,
        "keys": keys_with_users
    })


@admin_api_bp.get("/users/<user_id:int>/stats")
@require_auth
async def get_user_stats(request: Request, user_id: int):
    """Get user statistics (admin only)."""
    user = request.ctx.user
    
    if user.role != 'admin':
        return json(
            {"success": False, "error": "Unauthorized - admin access required"},
            status=403
        )
    
    # Get user's devices and API keys
    devices = await db.get_user_devices(user_id)
    api_keys = await db.get_user_api_keys(user_id)
    
    return json({
        "success": True,
        "stats": {
            "device_count": len(devices),
            "api_key_count": len(api_keys),
        }
    })

