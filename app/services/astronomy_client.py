"""Astronomy client for moon phase and astronomical data."""

import httpx
import os
from dataclasses import dataclass
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MoonPhase:
    """Moon phase data structure."""

    phase: str  # e.g., "New Moon", "Waxing Crescent", etc.
    illumination: float  # Percentage illuminated (0-100)
    age: float  # Days since new moon
    distance: float  # Distance from Earth in km
    angular_diameter: float  # Angular diameter in degrees


@dataclass
class AstronomicalData:
    """Complete astronomical data."""

    moon_phase: MoonPhase
    sunrise: str
    sunset: str
    moonrise: str
    moonset: str


class AstronomyClient:
    """Client for fetching astronomical data from Astronomy API."""

    def __init__(self):
        self.base_url = "https://api.astronomyapi.com/api/v2"
        self.app_id = os.getenv("ASTRONOMY_API_ID")
        self.app_secret = os.getenv("ASTRONOMY_API_SECRET")

        # Check if credentials are available
        if self.app_id and self.app_secret:
            logger.info(
                f"[AstronomyClient] Credentials loaded - ID: {self.app_id[:8]}..."
            )
        else:
            logger.error("Astronomy API credentials not found in environment variables")
            logger.error("Please set ASTRONOMY_API_ID and ASTRONOMY_API_SECRET")

    async def get_moon_phase(
        self, lat: float, lon: float, date: str = None
    ) -> Optional[MoonPhase]:
        """
        Get moon phase data for the given coordinates and date.

        Args:
            lat: Latitude
            lon: Longitude
            date: Date in YYYY-MM-DD format (defaults to today)

        Returns:
            MoonPhase object or None if request failed
        """
        if not self.app_id or not self.app_secret:
            logger.error("Astronomy API credentials not configured")
            return None

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        url = f"{self.base_url}/studio/moon-phase"

        params = {
            "observer_latitude": lat,
            "observer_longitude": lon,
            "utc_date": date,
            "format": "json",
        }

        logger.info(f"[AstronomyClient] Making request to: {url}")
        logger.info(f"[AstronomyClient] Params: {params}")
        logger.info(f"[AstronomyClient] Using httpx Basic Auth")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    auth=(self.app_id, self.app_secret),
                    timeout=10.0,
                )
                logger.info(
                    f"[AstronomyClient] Response status: {response.status_code}"
                )

                if response.status_code == 403:
                    logger.error(
                        f"[AstronomyClient] 403 Forbidden - check credentials and API endpoint"
                    )
                    logger.error(f"[AstronomyClient] Response: {response.text}")
                    return None

                response.raise_for_status()
                data = response.json()
                logger.info(f"[AstronomyClient] Success! Got data: {data}")

                return self._parse_moon_phase(data)

        except Exception as e:
            logger.error(f"Astronomy API request failed: {e}")
            return None

    async def get_astronomical_data(
        self, lat: float, lon: float, date: str = None
    ) -> Optional[AstronomicalData]:
        """
        Get complete astronomical data including moon phase and sun/moon times.

        Args:
            lat: Latitude
            lon: Longitude
            date: Date in YYYY-MM-DD format (defaults to today)

        Returns:
            AstronomicalData object or None if request failed
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        # Get moon phase
        moon_phase = await self.get_moon_phase(lat, lon, date)
        if not moon_phase:
            return None

        # Get sun and moon times
        sun_moon_times = await self._get_sun_moon_times(lat, lon, date)

        return AstronomicalData(
            moon_phase=moon_phase,
            sunrise=sun_moon_times.get("sunrise", ""),
            sunset=sun_moon_times.get("sunset", ""),
            moonrise=sun_moon_times.get("moonrise", ""),
            moonset=sun_moon_times.get("moonset", ""),
        )

    async def _get_sun_moon_times(self, lat: float, lon: float, date: str) -> dict:
        """Get sunrise, sunset, moonrise, moonset times."""
        url = f"{self.base_url}/sun/rise-set"

        params = {"latitude": lat, "longitude": lon, "date": date, "format": "json"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    auth=(self.app_id, self.app_secret),
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "sunrise": data.get("data", {}).get("sunrise", ""),
                    "sunset": data.get("data", {}).get("sunset", ""),
                    "moonrise": data.get("data", {}).get("moonrise", ""),
                    "moonset": data.get("data", {}).get("moonset", ""),
                }

        except Exception as e:
            logger.warning(f"Sun/Moon times request failed: {e}")
            return {}

    def _parse_moon_phase(self, data: dict) -> Optional[MoonPhase]:
        """Parse the moon phase API response."""
        try:
            moon_data = data.get("data", {})

            return MoonPhase(
                phase=moon_data.get("phase", {}).get("name", "Unknown"),
                illumination=float(
                    moon_data.get("illumination", {}).get("percentage", 0)
                ),
                age=float(moon_data.get("age", {}).get("days", 0)),
                distance=float(moon_data.get("distance", {}).get("km", 0)),
                angular_diameter=float(
                    moon_data.get("angular_diameter", {}).get("degrees", 0)
                ),
            )

        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Failed to parse moon phase response: {e}")
            return None
