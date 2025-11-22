"""Authentication and session management endpoints."""

from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import json
from app.database.db import db
from app.database.models import User
from app.auth.utils import hash_password, verify_password
from datetime import datetime
import secrets

auth_bp = Blueprint("auth", url_prefix="/api/auth")


@auth_bp.post("/register")
async def register(request: Request):
    """Register a new user account."""
    try:
        data = request.json
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        
        # Validation
        if not username or not email or not password:
            return json(
                {"success": False, "error": "Username, email, and password are required"},
                status=400
            )
        
        if len(password) < 6:
            return json(
                {"success": False, "error": "Password must be at least 6 characters"},
                status=400
            )
        
        if "@" not in email:
            return json(
                {"success": False, "error": "Invalid email address"},
                status=400
            )
        
        # Check if user already exists
        existing_user = await db.get_user(username)
        if existing_user:
            return json(
                {"success": False, "error": "Username already taken"},
                status=400
            )
        
        # Create user
        now = datetime.utcnow().isoformat()
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role='user',  # New users are regular users
            created_at=now,
            updated_at=now,
        )
        
        created_user = await db.create_user(user)
        
        if created_user:
            # Create session token
            session_token = secrets.token_urlsafe(32)
            
            # Store session in request context (we'll add proper session management later)
            return json({
                "success": True,
                "user": {
                    "id": created_user.id,
                    "username": created_user.username,
                    "email": created_user.email,
                    "role": created_user.role,
                },
                "message": "Account created successfully"
            })
        else:
            return json(
                {"success": False, "error": "Failed to create account"},
                status=500
            )
            
    except Exception as e:
        return json(
            {"success": False, "error": str(e)},
            status=500
        )


@auth_bp.post("/login")
async def login(request: Request):
    """Login with username/password."""
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return json(
                {"success": False, "error": "Username and password are required"},
                status=400
            )
        
        # Get user
        user = await db.get_user(username)
        if not user:
            return json(
                {"success": False, "error": "Invalid username or password"},
                status=401
            )
        
        # Verify password
        if not verify_password(password, user.password_hash):
            return json(
                {"success": False, "error": "Invalid username or password"},
                status=401
            )
        
        # Create session token (simplified - we'll use Basic Auth for now)
        # In production, you'd create a proper session/JWT here
        session_token = secrets.token_urlsafe(32)
        
        return json({
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
            "credentials": f"{username}:{password}",  # For Basic Auth
            "message": "Login successful"
        })
        
    except Exception as e:
        return json(
            {"success": False, "error": str(e)},
            status=500
        )


@auth_bp.get("/me")
async def get_current_user(request: Request):
    """Get current user info from Basic Auth."""
    try:
        from app.auth.utils import parse_basic_auth
        
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return json(
                {"success": False, "error": "Not authenticated"},
                status=401
            )
        
        username, password = parse_basic_auth(auth_header)
        if not username:
            return json(
                {"success": False, "error": "Invalid authentication"},
                status=401
            )
        
        user = await db.get_user(username)
        if not user or not verify_password(password, user.password_hash):
            return json(
                {"success": False, "error": "Invalid credentials"},
                status=401
            )
        
        return json({
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            }
        })
        
    except Exception as e:
        return json(
            {"success": False, "error": str(e)},
            status=500
        )


@auth_bp.post("/logout")
async def logout(request: Request):
    """Logout (client-side will clear credentials)."""
    return json({
        "success": True,
        "message": "Logged out successfully"
    })

