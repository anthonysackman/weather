"""Admin web interface endpoints."""

from sanic import Blueprint
from sanic.response import html
from sanic.request import Request
import os

admin_bp = Blueprint("admin", url_prefix="/admin")


@admin_bp.get("/")
async def admin_page(request: Request):
    """Serve the admin interface."""
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

