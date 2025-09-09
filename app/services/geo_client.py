"""Geocoding client for Open-Meteo API."""

import httpx
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# US State abbreviation to full name mapping
STATE_MAPPING = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}


@dataclass
class Location:
    """Location data structure matching the C++ version."""

    lat: float
    lon: float
    name: str
    state: str
    timezone: str


class GeoClient:
    """Client for fetching location data from Open-Meteo Geocoding API."""

    def __init__(self):
        self.base_url = "https://geocoding-api.open-meteo.com/v1/search"

    async def get_coordinates(
        self, city_name: str, state_name: str = ""
    ) -> Optional[Location]:
        """
        Get coordinates for a city and state.

        Args:
            city_name: Name of the city
            state_name: Name of the state (optional, helps with disambiguation)

        Returns:
            Location object or None if not found
        """
        # Convert state abbreviation to full name if needed
        mapped_state = self._map_state_name(state_name)

        url = f"{self.base_url}?name={city_name}"

        logger.info(
            f"[GeoClient] Requesting: {url} (original state: '{state_name}', mapped: '{mapped_state}')"
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                return self._find_matching_location(data, city_name, mapped_state)

        except Exception as e:
            logger.error(f"Geocoding API request failed: {e}")
            return None

    def _find_matching_location(
        self, data: dict, city_name: str, state_name: str
    ) -> Optional[Location]:
        """Find the best matching location from API response."""
        if "results" not in data:
            logger.warning("[GeoClient] No 'results' in JSON response")
            return None

        results = data["results"]

        for result in results:
            result_city = result.get("name", "")
            result_state = result.get("admin1", "")

            # If state_name is provided, look for exact match
            if state_name:
                if (
                    result_city.lower() == city_name.lower()
                    and result_state.lower() == state_name.lower()
                ):
                    location = Location(
                        lat=result["latitude"],
                        lon=result["longitude"],
                        name=result_city,
                        state=result_state,
                        timezone=result.get("timezone", ""),
                    )

                    logger.info(
                        f"[GeoClient] Found: {location.name}, {location.state} ({location.lat:.4f}, {location.lon:.4f})"
                    )
                    return location
            else:
                # If no state specified, take first city match
                if result_city.lower() == city_name.lower():
                    location = Location(
                        lat=result["latitude"],
                        lon=result["longitude"],
                        name=result_city,
                        state=result_state,
                        timezone=result.get("timezone", ""),
                    )

                    logger.info(
                        f"[GeoClient] Found: {location.name}, {location.state} ({location.lat:.4f}, {location.lon:.4f})"
                    )
                    return location

        logger.warning("[GeoClient] No matching location found")
        return None

    def _map_state_name(self, state_name: str) -> str:
        """
        Map state abbreviation to full name if needed.

        Args:
            state_name: State name or abbreviation

        Returns:
            Full state name or original string if not found
        """
        if not state_name:
            return state_name

        # Check if it's a 2-letter abbreviation
        state_upper = state_name.upper().strip()
        if len(state_upper) == 2 and state_upper in STATE_MAPPING:
            mapped = STATE_MAPPING[state_upper]
            logger.info(f"[GeoClient] Mapped state '{state_name}' -> '{mapped}'")
            return mapped

        # Return original if not an abbreviation or not found
        return state_name
