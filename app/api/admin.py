"""Admin web interface and public pages endpoints."""

from sanic import Blueprint
from sanic.response import html, redirect
from sanic.request import Request
from app.auth.flexible_auth import require_auth
import os

admin_bp = Blueprint("admin", url_prefix="/admin")
pages_bp = Blueprint("pages", url_prefix="")


@admin_bp.get("/")
async def admin_page(request: Request):
    """Serve the admin interface (admin only - enforced by client-side check)."""
    # Read the admin.html template
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates", "admin.html"
    )

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        return html(content)
    except Exception as e:
        return html(f"<h1>Error loading admin page</h1><p>{str(e)}</p>", status=500)


@pages_bp.get("/")
async def home_page(request: Request):
    """Serve login page as home."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates", "login.html"
    )
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        return html(content)
    except Exception as e:
        return html(f"<h1>Error loading login page</h1><p>{str(e)}</p>", status=500)


@pages_bp.get("/login")
async def login_page(request: Request):
    """Serve login page (alias for /)."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates", "login.html"
    )
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        return html(content)
    except Exception as e:
        return html(f"<h1>Error loading login page</h1><p>{str(e)}</p>", status=500)


@pages_bp.get("/register")
async def register_page(request: Request):
    """Serve registration page."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates", "register.html"
    )
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        return html(content)
    except Exception as e:
        return html(f"<h1>Error loading registration page</h1><p>{str(e)}</p>", status=500)


@pages_bp.get("/dashboard")
async def dashboard_page(request: Request):
    """Serve user dashboard page."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates", "dashboard.html"
    )
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        return html(content)
    except Exception as e:
        return html(f"<h1>Error loading dashboard</h1><p>{str(e)}</p>", status=500)

