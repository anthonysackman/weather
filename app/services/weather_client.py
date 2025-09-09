"""Weather client for Open-Meteo API."""

import httpx
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Weather:
    """Enhanced weather data structure with all available Open-Meteo data."""

    # Current conditions
    temperature: float
    feels_like: float
    windspeed: float
    winddirection: float
    wind_gusts: float
    humidity: int
    weathercode: int
    weather_description: str  # Human-readable weather condition
    timestamp: str

    # Daily data
    temp_min: float
    temp_max: float
    sunrise: str
    sunset: str

    # Additional current data
    pressure: float
    visibility: float
    uv_index: float
    cloud_cover: int

    # Precipitation
    precipitation: float
    rain: float
    snowfall: float

    # Hourly forecast (next 24 hours)
    hourly_forecast: list

    # Daily forecast (next 7 days)
    daily_forecast: list

    # Weather alerts
    weather_alerts: list


class WeatherClient:
    """Client for fetching weather data from Open-Meteo API."""

    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"

        # WMO Weather interpretation codes
        self.weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }

    async def get_current_weather(
        self, lat: float, lon: float, timezone: str
    ) -> Optional[Weather]:
        """
        Get current weather data for the given coordinates.

        Args:
            lat: Latitude
            lon: Longitude
            timezone: Timezone string (e.g., "America/New_York")

        Returns:
            Weather object or None if request failed
        """
        # Build comprehensive API request with all available data
        current_params = [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "rain",
            "snowfall",
            "weather_code",
            "cloud_cover",
            "pressure_msl",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "visibility",
            "uv_index",
        ]

        hourly_params = [
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "rain",
            "snowfall",
            "weather_code",
            "pressure_msl",
            "cloud_cover",
            "visibility",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "uv_index",
        ]

        daily_params = [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "apparent_temperature_max",
            "apparent_temperature_min",
            "sunrise",
            "sunset",
            "daylight_duration",
            "precipitation_sum",
            "rain_sum",
            "snowfall_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "wind_direction_10m_dominant",
            "uv_index_max",
        ]

        url = (
            f"{self.base_url}"
            f"?latitude={lat:.4f}"
            f"&longitude={lon:.4f}"
            f"&current={','.join(current_params)}"
            f"&hourly={','.join(hourly_params)}"
            f"&daily={','.join(daily_params)}"
            f"&temperature_unit=fahrenheit"
            f"&windspeed_unit=mph"
            f"&precipitation_unit=inch"
            f"&timezone={timezone}"
            f"&forecast_days=7"
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                return self._parse_weather_response(data)

        except Exception as e:
            logger.error(f"Weather API request failed: {e}")
            return None

    def _parse_weather_response(self, data: dict) -> Optional[Weather]:
        """Parse the comprehensive API response into Weather object."""
        try:
            current = data.get("current", {})
            hourly = data.get("hourly", {})
            daily = data.get("daily", {})

            # Get current weather code and description
            weather_code = current.get("weather_code", 0)
            weather_description = self.weather_codes.get(weather_code, "Unknown")

            # Build hourly forecast (all available hours)
            hourly_forecast = []
            if hourly.get("time"):
                logger.info(
                    f"[WeatherClient] Got {len(hourly['time'])} hours of data from API"
                )
                for i in range(len(hourly["time"])):
                    hourly_item = {
                        "time": hourly["time"][i],
                        "temperature": hourly.get("temperature_2m", [None])[i],
                        "feels_like": hourly.get("apparent_temperature", [None])[i],
                        "humidity": hourly.get("relative_humidity_2m", [None])[i],
                        "precipitation_probability": hourly.get(
                            "precipitation_probability", [None]
                        )[i],
                        "precipitation": hourly.get("precipitation", [None])[i],
                        "weather_code": hourly.get("weather_code", [None])[i],
                        "wind_speed": hourly.get("wind_speed_10m", [None])[i],
                        "wind_direction": hourly.get("wind_direction_10m", [None])[i],
                        "uv_index": hourly.get("uv_index", [None])[i],
                    }
                    if hourly_item["weather_code"] is not None:
                        hourly_item["weather_description"] = self.weather_codes.get(
                            hourly_item["weather_code"], "Unknown"
                        )
                    hourly_forecast.append(hourly_item)

            # Build daily forecast (next 7 days)
            daily_forecast = []
            if daily.get("time"):
                for i in range(len(daily["time"])):
                    # Convert daylight duration from seconds to hours
                    daylight_seconds = daily.get("daylight_duration", [None])[i]
                    daylight_hours = (
                        round(daylight_seconds / 3600, 1)
                        if daylight_seconds is not None
                        else None
                    )

                    daily_item = {
                        "date": daily["time"][i],
                        "temp_max": daily.get("temperature_2m_max", [None])[i],
                        "temp_min": daily.get("temperature_2m_min", [None])[i],
                        "weather_code": daily.get("weather_code", [None])[i],
                        "sunrise": daily.get("sunrise", [None])[i],
                        "sunset": daily.get("sunset", [None])[i],
                        "daylight_duration": daylight_hours,
                        "precipitation_sum": daily.get("precipitation_sum", [None])[i],
                        "precipitation_probability_max": daily.get(
                            "precipitation_probability_max", [None]
                        )[i],
                        "wind_speed_max": daily.get("wind_speed_10m_max", [None])[i],
                        "wind_gusts_max": daily.get("wind_gusts_10m_max", [None])[i],
                        "uv_index_max": daily.get("uv_index_max", [None])[i],
                    }
                    if daily_item["weather_code"] is not None:
                        daily_item["weather_description"] = self.weather_codes.get(
                            daily_item["weather_code"], "Unknown"
                        )
                    daily_forecast.append(daily_item)

            # Create Weather object with all data
            weather = Weather(
                # Current conditions
                temperature=current.get("temperature_2m", 0.0),
                feels_like=current.get("apparent_temperature", 0.0),
                windspeed=current.get("wind_speed_10m", 0.0),
                winddirection=current.get("wind_direction_10m", 0.0),
                wind_gusts=current.get("wind_gusts_10m", 0.0),
                humidity=current.get("relative_humidity_2m", 0),
                weathercode=weather_code,
                weather_description=weather_description,
                timestamp=current.get("time", ""),
                # Daily data (today)
                temp_min=daily.get("temperature_2m_min", [0.0])[0]
                if daily.get("temperature_2m_min")
                else 0.0,
                temp_max=daily.get("temperature_2m_max", [0.0])[0]
                if daily.get("temperature_2m_max")
                else 0.0,
                sunrise=daily.get("sunrise", [""])[0] if daily.get("sunrise") else "",
                sunset=daily.get("sunset", [""])[0] if daily.get("sunset") else "",
                # Additional current data
                pressure=current.get("pressure_msl", 0.0),
                visibility=current.get("visibility", 0.0),
                uv_index=current.get("uv_index", 0.0),
                cloud_cover=current.get("cloud_cover", 0),
                # Precipitation
                precipitation=current.get("precipitation", 0.0),
                rain=current.get("rain", 0.0),
                snowfall=current.get("snowfall", 0.0),
                # Forecasts
                hourly_forecast=hourly_forecast,
                daily_forecast=daily_forecast,
                # Weather alerts (would need separate API call)
                weather_alerts=[],
            )

            return weather

        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Failed to parse weather response: {e}")
            return None
