"""Address geocoding client using multiple services."""

import httpx
from typing import Optional, Tuple
import logging
from app.services.geo_client import GeoClient

logger = logging.getLogger(__name__)


class AddressClient:
    """Client for geocoding street addresses."""

    def __init__(self):
        self.geo_client = GeoClient()

    async def geocode_address(
        self, address: str
    ) -> Optional[Tuple[float, float, str, str]]:
        """
        Geocode a street address to coordinates.

        Args:
            address: Full street address (e.g., "123 Main St, Miami, FL 33101")

        Returns:
            Tuple of (lat, lon, timezone, formatted_address) or None if failed
        """
        # Try OpenStreetMap Nominatim first (free, no API key needed)
        result = await self._geocode_nominatim(address)
        if result:
            return result

        # Could add other services here as fallback (Google, Mapbox, etc.)
        logger.warning(f"Failed to geocode address: {address}")
        return None

    async def _geocode_nominatim(
        self, address: str
    ) -> Optional[Tuple[float, float, str, str]]:
        """Geocode using OpenStreetMap Nominatim."""
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": address,
                "format": "json",
                "limit": 1,
                "addressdetails": 1,
            }

            async with httpx.AsyncClient() as client:
                headers = {"User-Agent": "WeatherDisplayApp/1.0"}
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                if not data or len(data) == 0:
                    logger.warning(f"No results for address: {address}")
                    return None

                result = data[0]
                lat = float(result["lat"])
                lon = float(result["lon"])
                formatted_address = result.get("display_name", address)

                # Estimate timezone based on longitude
                timezone = self._estimate_timezone(lon)

                logger.info(
                    f"Geocoded '{address}' to ({lat:.4f}, {lon:.4f}) - {timezone}"
                )
                return (lat, lon, timezone, formatted_address)

        except Exception as e:
            logger.error(f"Nominatim geocoding failed: {e}")
            return None

    def _estimate_timezone(self, lon: float) -> str:
        """Estimate timezone from longitude (US-focused for now)."""
        # Simple US timezone estimation
        timezone_offset = int(lon / 15)

        if -8 <= timezone_offset <= -5:
            if timezone_offset == -8:
                return "America/Los_Angeles"
            elif timezone_offset == -7:
                return "America/Denver"
            elif timezone_offset == -6:
                return "America/Chicago"
            else:  # -5
                return "America/New_York"
        elif lon < -125:
            return "America/Anchorage"  # Alaska
        elif lon < -155:
            return "Pacific/Honolulu"  # Hawaii
        else:
            return "America/New_York"  # Default

    async def parse_city_state_address(
        self, address: str
    ) -> Optional[Tuple[str, str]]:
        """
        Try to extract city and state from an address string.

        Args:
            address: Address string

        Returns:
            Tuple of (city, state) or None
        """
        # Simple parsing - look for common patterns
        # "City, State" or "City, ST" at the end
        parts = address.split(",")
        if len(parts) >= 2:
            city = parts[-2].strip()
            state = parts[-1].strip().split()[0]  # Get first word (state code)
            return (city, state)

        return None

