from sanic import Blueprint
from sanic.response import json

weather_bp = Blueprint("weather", url_prefix="/weather")


@weather_bp.get("/")
async def weather_info(request):
    return json({"message": "Weather endpoints coming soon"})
