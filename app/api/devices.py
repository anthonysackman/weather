"""Device management API endpoints."""

from sanic import Blueprint
from sanic.response import json
from sanic.request import Request
from sanic.log import logger
from app.auth.middleware import require_auth
from app.database.db import db
from app.database.models import Device
from app.services.address_client import AddressClient
from app.services.weather_client import WeatherClient
from app.services.astronomy_client import AstronomyClient
from datetime import datetime
import secrets

devices_bp = Blueprint("devices", url_prefix="/api")


# Add a middleware to log all requests to this blueprint
@devices_bp.middleware("request")
async def log_request(request):
    print(f"========== REQUEST: {request.method} {request.path} ==========")


# Admin endpoints (require authentication)
@devices_bp.get("/devices")
@require_auth
async def list_devices(request: Request):
    """List all devices (admin only)."""
    devices = await db.get_all_devices()

    return json(
        {
            "success": True,
            "devices": [
                {
                    "device_id": d.device_id,
                    "name": d.name,
                    "address": d.address,
                    "lat": d.lat,
                    "lon": d.lon,
                    "timezone": d.timezone,
                    "last_seen": d.last_seen,
                    "created_at": d.created_at,
                    "updated_at": d.updated_at,
                }
                for d in devices
            ],
        }
    )


@devices_bp.post("/devices")
@require_auth
async def create_device(request: Request):
    """Create a new device (admin only)."""
    try:
        data = request.json
        name = data.get("name")
        address = data.get("address")
        timezone = data.get("timezone")

        if not name or not address or not timezone:
            return json(
                {"success": False, "error": "Name, address, and timezone are required"},
                status=400,
            )

        # Generate unique device ID
        device_id = secrets.token_urlsafe(16)

        # Geocode the address
        address_client = AddressClient()
        geocode_result = await address_client.geocode_address(address)

        if not geocode_result:
            return json(
                {"success": False, "error": "Failed to geocode address"}, status=400
            )

        lat, lon, _, formatted_address = geocode_result
        final_timezone = timezone

        # Create device
        device = Device(
            device_id=device_id,
            name=name,
            address=formatted_address,
            lat=lat,
            lon=lon,
            timezone=final_timezone,
            display_settings=None,
            last_seen=None,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )

        created = await db.create_device(device)
        if not created:
            return json(
                {"success": False, "error": "Failed to create device"}, status=500
            )

        logger.info(f"Created device {device_id} for {name}")

        return json(
            {
                "success": True,
                "device": {
                    "device_id": device.device_id,
                    "name": device.name,
                    "address": device.address,
                    "lat": device.lat,
                    "lon": device.lon,
                    "timezone": device.timezone,
                },
            }
        )

    except Exception as e:
        logger.error(f"Failed to create device: {e}")
        return json({"success": False, "error": str(e)}, status=500)


@devices_bp.get("/devices/<device_id>")
@require_auth
async def get_device(request: Request, device_id: str):
    """Get device details (admin only)."""
    device = await db.get_device(device_id)

    if not device:
        return json({"success": False, "error": "Device not found"}, status=404)

    return json(
        {
            "success": True,
            "device": {
                "device_id": device.device_id,
                "name": device.name,
                "address": device.address,
                "lat": device.lat,
                "lon": device.lon,
                "timezone": device.timezone,
                "last_seen": device.last_seen,
                "created_at": device.created_at,
                "updated_at": device.updated_at,
            },
        }
    )


@devices_bp.put("/devices/<device_id>")
@require_auth
async def update_device(request: Request, device_id: str):
    """Update device (admin only)."""
    try:
        data = request.json
        import sys
        print(f"========== [UPDATE] Received data: {data} ==========", flush=True)
        sys.stdout.flush()
        logger.info(f"[UPDATE] Received data: {data}")

        # Check if device exists
        device = await db.get_device(device_id)
        if not device:
            return json({"success": False, "error": "Device not found"}, status=404)

        # Require timezone
        if not data.get("timezone"):
            return json(
                {"success": False, "error": "Timezone is required"},
                status=400,
            )

        # If address changed, geocode it
        if "address" in data:
            old_addr = (device.address or "").strip().lower()
            new_addr = (data["address"] or "").strip().lower()
            
            if old_addr != new_addr:
                # Address changed, geocode it
                address_client = AddressClient()
                geocode_result = await address_client.geocode_address(data["address"])

                if not geocode_result:
                    return json(
                        {"success": False, "error": "Failed to geocode address"},
                        status=400,
                    )

                lat, lon, _, formatted_address = geocode_result
                data["address"] = formatted_address
                data["lat"] = lat
                data["lon"] = lon

        # Update device
        success = await db.update_device(device_id, **data)

        if not success:
            return json(
                {"success": False, "error": "Failed to update device"}, status=500
            )

        # Get updated device
        updated_device = await db.get_device(device_id)

        return json(
            {
                "success": True,
                "device": {
                    "device_id": updated_device.device_id,
                    "name": updated_device.name,
                    "address": updated_device.address,
                    "lat": updated_device.lat,
                    "lon": updated_device.lon,
                    "timezone": updated_device.timezone,
                },
            }
        )

    except Exception as e:
        logger.error(f"Failed to update device: {e}")
        return json({"success": False, "error": str(e)}, status=500)


@devices_bp.delete("/devices/<device_id>")
@require_auth
async def delete_device(request: Request, device_id: str):
    """Delete device (admin only)."""
    success = await db.delete_device(device_id)

    if not success:
        return json({"success": False, "error": "Device not found"}, status=404)

    return json({"success": True, "message": "Device deleted"})


# ESP32 endpoint (no auth required - device ID is the authentication)
@devices_bp.get("/device/<device_id>/weather")
async def get_device_weather(request: Request, device_id: str):
    """Get weather for a specific device (ESP32 endpoint)."""
    # Get device configuration
    device = await db.get_device(device_id)

    if not device:
        return json({"success": False, "error": "Device not found"}, status=404)

    # Check if device has location configured
    if not device.lat or not device.lon or not device.timezone:
        return json(
            {"success": False, "error": "Device location not configured"}, status=400
        )

    # Update last_seen timestamp
    await db.update_device_heartbeat(device_id)

    # Get weather data
    weather_client = WeatherClient()
    astronomy_client = AstronomyClient()

    weather = await weather_client.get_current_weather(
        device.lat, device.lon, device.timezone
    )
    moon_phase = await astronomy_client.get_moon_phase(device.lat, device.lon)

    if not weather:
        return json(
            {"success": False, "error": "Weather data not available"}, status=500
        )

    # Return comprehensive weather data
    return json(
        {
            "success": True,
            "device": {
                "device_id": device.device_id,
                "name": device.name,
                "address": device.address,
            },
            "weather": {
                # Current conditions
                "temperature": weather.temperature,
                "feels_like": weather.feels_like,
                "windspeed": weather.windspeed,
                "winddirection": weather.winddirection,
                "wind_gusts": weather.wind_gusts,
                "humidity": weather.humidity,
                "weathercode": weather.weathercode,
                "weather_description": weather.weather_description,
                "timestamp": weather.timestamp,
                # Daily data
                "temp_min": weather.temp_min,
                "temp_max": weather.temp_max,
                "sunrise": weather.sunrise,
                "sunset": weather.sunset,
                # Additional current data
                "pressure": weather.pressure,
                "visibility": weather.visibility,
                "uv_index": weather.uv_index,
                "cloud_cover": weather.cloud_cover,
                # Precipitation
                "precipitation": weather.precipitation,
                "rain": weather.rain,
                "snowfall": weather.snowfall,
                # Forecasts
                "hourly_forecast": weather.hourly_forecast,
                "daily_forecast": weather.daily_forecast,
                # Moon phase
                "moon_phase": {
                    "phase": moon_phase.phase if moon_phase else "Unknown",
                    "illumination": moon_phase.illumination if moon_phase else 0,
                    "age": moon_phase.age if moon_phase else 0,
                    "distance": moon_phase.distance if moon_phase else 0,
                }
                if moon_phase
                else None,
            },
        }
    )


@devices_bp.get("/device/<device_id>/data")
async def get_device_data(request: Request, device_id: str):
    """Get flexible filtered data for a device (web apps, testing)."""
    # Get device configuration
    device = await db.get_device(device_id)

    if not device:
        return json({"success": False, "error": "Device not found"}, status=404)

    # Check if device has location configured
    if not device.lat or not device.lon or not device.timezone:
        return json(
            {"success": False, "error": "Device location not configured"}, status=400
        )

    # Update last_seen timestamp
    await db.update_device_heartbeat(device_id)

    # Parse query parameters
    include = request.args.get("include", "").split(",") if request.args.get("include") else []
    exclude = request.args.get("exclude", "").split(",") if request.args.get("exclude") else []
    hourly_limit = int(request.args.get("hourly_limit", 168))
    daily_limit = int(request.args.get("daily_limit", 7))

    # Determine what to include (default: everything)
    include_all = not include  # If no include specified, include everything
    
    categories = {
        "weather": include_all or "weather" in include,
        "hourly": include_all or "hourly" in include,
        "daily": include_all or "daily" in include,
        "lunar": include_all or "lunar" in include,
        "astronomy": include_all or "astronomy" in include,
    }

    # Apply excludes
    for cat in exclude:
        if cat in categories:
            categories[cat] = False

    # Get weather data if needed
    weather = None
    if categories["weather"] or categories["hourly"] or categories["daily"] or categories["astronomy"]:
        weather_client = WeatherClient()
        weather = await weather_client.get_current_weather(
            device.lat, device.lon, device.timezone
        )
        if not weather:
            return json(
                {"success": False, "error": "Weather data not available"}, status=500
            )

    # Get moon phase if needed
    moon_phase = None
    if categories["lunar"]:
        astronomy_client = AstronomyClient()
        moon_phase = await astronomy_client.get_moon_phase(device.lat, device.lon)

    # Build response
    response = {
        "success": True,
        "device": {
            "device_id": device.device_id,
            "name": device.name,
            "address": device.address,
        },
        "data": {}
    }

    # Add weather data
    if categories["weather"] and weather:
        response["data"]["weather"] = {
            "temperature": weather.temperature,
            "feels_like": weather.feels_like,
            "windspeed": weather.windspeed,
            "winddirection": weather.winddirection,
            "wind_gusts": weather.wind_gusts,
            "humidity": weather.humidity,
            "weathercode": weather.weathercode,
            "weather_description": weather.weather_description,
            "timestamp": weather.timestamp,
            "temp_min": weather.temp_min,
            "temp_max": weather.temp_max,
            "pressure": weather.pressure,
            "visibility": weather.visibility,
            "uv_index": weather.uv_index,
            "cloud_cover": weather.cloud_cover,
            "precipitation": weather.precipitation,
            "rain": weather.rain,
            "snowfall": weather.snowfall,
        }

    # Add hourly forecast
    if categories["hourly"] and weather:
        response["data"]["hourly_forecast"] = weather.hourly_forecast[:hourly_limit]

    # Add daily forecast
    if categories["daily"] and weather:
        response["data"]["daily_forecast"] = weather.daily_forecast[:daily_limit]

    # Add astronomy data
    if categories["astronomy"] and weather:
        response["data"]["astronomy"] = {
            "sunrise": weather.sunrise,
            "sunset": weather.sunset,
        }

    # Add lunar data
    if categories["lunar"] and moon_phase:
        response["data"]["lunar"] = {
            "phase": moon_phase.phase,
            "illumination": moon_phase.illumination,
            "age": moon_phase.age,
            "distance": moon_phase.distance,
            "angular_diameter": moon_phase.angular_diameter,
        }

    return json(response)


@devices_bp.get("/device/<device_id>/esp")
async def get_device_esp(request: Request, device_id: str):
    """Get minimal optimized data for ESP32 (memory-conscious)."""
    # Get device configuration
    device = await db.get_device(device_id)

    if not device:
        return json({"success": False, "error": "Device not found"}, status=404)

    # Check if device has location configured
    if not device.lat or not device.lon or not device.timezone:
        return json(
            {"success": False, "error": "Device location not configured"}, status=400
        )

    # Update last_seen timestamp
    await db.update_device_heartbeat(device_id)

    # Get weather data
    weather_client = WeatherClient()
    astronomy_client = AstronomyClient()

    weather = await weather_client.get_current_weather(
        device.lat, device.lon, device.timezone
    )
    moon_phase = await astronomy_client.get_moon_phase(device.lat, device.lon)

    if not weather:
        return json(
            {"success": False, "error": "Weather data not available"}, status=500
        )

    # Helper function to get wind direction from degrees
    def get_wind_direction(degrees):
        if degrees is None:
            return "N"
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        return directions[round(degrees / 22.5) % 16]

    # Helper function to format time (HH:MM)
    def format_time(iso_time):
        if not iso_time:
            return "00:00"
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
            return dt.strftime("%H:%M")
        except:
            return "00:00"

    # Return minimal flat structure
    return json({
        "temp": round(weather.temperature, 1),
        "feels": round(weather.feels_like, 1),
        "humid": weather.humidity,
        "condition": weather.weather_description,
        "wind_speed": round(weather.windspeed, 1),
        "wind_dir": get_wind_direction(weather.winddirection),
        "sunrise": format_time(weather.sunrise),
        "sunset": format_time(weather.sunset),
        "moon_phase": moon_phase.phase if moon_phase else "Unknown",
        "moon_illum": round(moon_phase.illumination) if moon_phase else 0,
    })

