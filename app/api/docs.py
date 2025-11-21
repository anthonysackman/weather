"""API documentation endpoint."""

from sanic import Blueprint
from sanic.response import html
from pathlib import Path

docs_bp = Blueprint("docs", url_prefix="")


@docs_bp.get("/docs")
async def api_docs(request):
    """Serve API documentation page."""
    docs_path = Path(__file__).parent.parent / "templates" / "docs.html"
    with open(docs_path, "r", encoding="utf-8") as f:
        content = f.read()
    return html(content)


