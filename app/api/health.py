from sanic import Blueprint
from sanic.response import json

health_bp = Blueprint("health", url_prefix="/")


@health_bp.get("/ping")
async def ping(request):
    return json({"message": "pong"})


@health_bp.get("/health")
async def root(request):
    return json({"message": "Weather API", "status": "running"})
