"""Air Quality client for Open-Meteo Air Quality API."""

import httpx
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class AirQuality:
    """Air quality data structure with AQI and pollutant information."""

    # Overall Air Quality Index (US EPA standard, 0-500)
    aqi: int
    category: str  # Good, Moderate, Unhealthy for Sensitive Groups, Unhealthy, Very Unhealthy, Hazardous
    dominant_pollutant: str  # Which pollutant is causing the worst AQI
    health_message: str  # Brief health recommendation

    # Current pollutant concentrations
    pm2_5: float  # PM2.5 (µg/m³)
    pm10: float  # PM10 (µg/m³)
    ozone: float  # O3 (µg/m³)
    nitrogen_dioxide: float  # NO2 (µg/m³)
    carbon_monoxide: float  # CO (µg/m³)
    sulfur_dioxide: float  # SO2 (µg/m³)

    # Individual AQI values per pollutant
    pm2_5_aqi: int
    pm10_aqi: int
    ozone_aqi: int
    no2_aqi: int
    co_aqi: int
    so2_aqi: int

    # Timestamp
    timestamp: str

    # Hourly forecast
    hourly_forecast: list


class AirQualityClient:
    """Client for fetching air quality data from Open-Meteo Air Quality API."""

    def __init__(self):
        self.base_url = "https://air-quality-api.open-meteo.com/v1/air-quality"

        # US EPA AQI categories
        self.aqi_categories = [
            (0, 50, "Good", "Air quality is satisfactory, and air pollution poses little or no risk."),
            (51, 100, "Moderate", "Air quality is acceptable. However, there may be a risk for some people, particularly those who are unusually sensitive to air pollution."),
            (101, 150, "Unhealthy for Sensitive Groups", "Members of sensitive groups may experience health effects. The general public is less likely to be affected."),
            (151, 200, "Unhealthy", "Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects."),
            (201, 300, "Very Unhealthy", "Health alert: The risk of health effects is increased for everyone."),
            (301, 500, "Hazardous", "Health warning of emergency conditions: everyone is more likely to be affected."),
        ]

        # US EPA AQI breakpoints for PM2.5 (24-hour average approximated)
        self.pm2_5_breakpoints = [
            (0.0, 12.0, 0, 50),
            (12.1, 35.4, 51, 100),
            (35.5, 55.4, 101, 150),
            (55.5, 150.4, 151, 200),
            (150.5, 250.4, 201, 300),
            (250.5, 500.4, 301, 500),
        ]

        # US EPA AQI breakpoints for PM10 (24-hour average)
        self.pm10_breakpoints = [
            (0, 54, 0, 50),
            (55, 154, 51, 100),
            (155, 254, 101, 150),
            (255, 354, 151, 200),
            (355, 424, 201, 300),
            (425, 604, 301, 500),
        ]

        # US EPA AQI breakpoints for O3 (8-hour average, µg/m³)
        # Converted from ppm: 1 ppm O3 ≈ 2000 µg/m³ at 25°C
        self.ozone_breakpoints = [
            (0, 108, 0, 50),
            (109, 140, 51, 100),
            (141, 170, 101, 150),
            (171, 210, 151, 200),
            (211, 400, 201, 300),
            (401, 800, 301, 500),
        ]

        # US EPA AQI breakpoints for NO2 (1-hour average, µg/m³)
        # Converted from ppb: 1 ppb NO2 ≈ 1.88 µg/m³ at 25°C
        self.no2_breakpoints = [
            (0, 100, 0, 50),
            (101, 188, 51, 100),
            (189, 677, 101, 150),
            (678, 1221, 151, 200),
            (1222, 2349, 201, 300),
            (2350, 3840, 301, 500),
        ]

        # US EPA AQI breakpoints for CO (8-hour average, µg/m³)
        # Converted from ppm: 1 ppm CO ≈ 1145 µg/m³ at 25°C
        self.co_breakpoints = [
            (0, 4400, 0, 50),
            (4401, 9400, 51, 100),
            (9401, 12400, 101, 150),
            (12401, 15400, 151, 200),
            (15401, 30400, 201, 300),
            (30401, 50400, 301, 500),
        ]

        # US EPA AQI breakpoints for SO2 (1-hour average, µg/m³)
        # Converted from ppb: 1 ppb SO2 ≈ 2.62 µg/m³ at 25°C
        self.so2_breakpoints = [
            (0, 91, 0, 50),
            (92, 196, 51, 100),
            (197, 486, 101, 150),
            (487, 797, 151, 200),
            (798, 1583, 201, 300),
            (1584, 2630, 301, 500),
        ]

    def _calculate_aqi(self, concentration: float, breakpoints: list) -> int:
        """
        Calculate AQI for a given pollutant concentration using EPA formula.
        
        AQI = ((I_high - I_low) / (C_high - C_low)) * (C - C_low) + I_low
        
        Where:
        - C = pollutant concentration
        - C_low, C_high = concentration breakpoints that bracket C
        - I_low, I_high = AQI values corresponding to C_low and C_high
        """
        if concentration is None or concentration < 0:
            return 0

        for c_low, c_high, i_low, i_high in breakpoints:
            if c_low <= concentration <= c_high:
                # Linear interpolation
                aqi = ((i_high - i_low) / (c_high - c_low)) * (concentration - c_low) + i_low
                return round(aqi)

        # If concentration exceeds all breakpoints, return max AQI
        return 500

    def _get_category_and_message(self, aqi: int) -> tuple[str, str]:
        """Get AQI category and health message for a given AQI value."""
        for low, high, category, message in self.aqi_categories:
            if low <= aqi <= high:
                return category, message
        return "Hazardous", "Extremely dangerous air quality conditions."

    def _get_dominant_pollutant(self, aqi_values: dict) -> str:
        """Determine which pollutant is causing the highest AQI."""
        pollutant_names = {
            "pm2_5_aqi": "PM2.5",
            "pm10_aqi": "PM10",
            "ozone_aqi": "Ozone",
            "no2_aqi": "NO2",
            "co_aqi": "CO",
            "so2_aqi": "SO2",
        }
        
        max_pollutant = max(aqi_values, key=aqi_values.get)
        return pollutant_names.get(max_pollutant, "Unknown")

    async def get_air_quality(
        self, lat: float, lon: float, timezone: str
    ) -> Optional[AirQuality]:
        """
        Get current air quality data for the given coordinates.

        Args:
            lat: Latitude
            lon: Longitude
            timezone: Timezone string (e.g., "America/New_York")

        Returns:
            AirQuality object or None if request failed
        """
        current_params = [
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
            "dust",
            "uv_index",
            "us_aqi",  # Open-Meteo's built-in US AQI
            "us_aqi_pm2_5",
            "us_aqi_pm10",
            "us_aqi_nitrogen_dioxide",
            "us_aqi_ozone",
            "us_aqi_sulphur_dioxide",
            "us_aqi_carbon_monoxide",
        ]

        hourly_params = [
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
            "us_aqi",
        ]

        url = (
            f"{self.base_url}"
            f"?latitude={lat:.4f}"
            f"&longitude={lon:.4f}"
            f"&current={','.join(current_params)}"
            f"&hourly={','.join(hourly_params)}"
            f"&timezone={timezone}"
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                return self._parse_air_quality_response(data)

        except Exception as e:
            logger.error(f"Air Quality API request failed: {e}")
            return None

    def _parse_air_quality_response(self, data: dict) -> Optional[AirQuality]:
        """Parse the API response into AirQuality object."""
        try:
            current = data.get("current", {})
            hourly = data.get("hourly", {})

            # Get pollutant concentrations (all in µg/m³)
            pm2_5 = current.get("pm2_5", 0.0) or 0.0
            pm10 = current.get("pm10", 0.0) or 0.0
            ozone = current.get("ozone", 0.0) or 0.0
            no2 = current.get("nitrogen_dioxide", 0.0) or 0.0
            co = current.get("carbon_monoxide", 0.0) or 0.0
            so2 = current.get("sulphur_dioxide", 0.0) or 0.0

            # Use Open-Meteo's pre-calculated AQI values (they use US EPA standard)
            pm2_5_aqi = current.get("us_aqi_pm2_5", 0) or 0
            pm10_aqi = current.get("us_aqi_pm10", 0) or 0
            ozone_aqi = current.get("us_aqi_ozone", 0) or 0
            no2_aqi = current.get("us_aqi_nitrogen_dioxide", 0) or 0
            co_aqi = current.get("us_aqi_carbon_monoxide", 0) or 0
            so2_aqi = current.get("us_aqi_sulphur_dioxide", 0) or 0
            
            # Overall AQI from Open-Meteo (or calculate as max of all)
            overall_aqi = current.get("us_aqi", 0) or max(pm2_5_aqi, pm10_aqi, ozone_aqi, no2_aqi, co_aqi, so2_aqi)

            # Determine dominant pollutant
            aqi_values = {
                "pm2_5_aqi": pm2_5_aqi,
                "pm10_aqi": pm10_aqi,
                "ozone_aqi": ozone_aqi,
                "no2_aqi": no2_aqi,
                "co_aqi": co_aqi,
                "so2_aqi": so2_aqi,
            }
            dominant_pollutant = self._get_dominant_pollutant(aqi_values)

            # Get category and health message
            category, health_message = self._get_category_and_message(overall_aqi)

            # Build hourly forecast
            hourly_forecast = []
            if hourly.get("time"):
                for i in range(len(hourly["time"])):
                    hourly_item = {
                        "time": hourly["time"][i],
                        "aqi": hourly.get("us_aqi", [None])[i],
                        "pm2_5": hourly.get("pm2_5", [None])[i],
                        "pm10": hourly.get("pm10", [None])[i],
                        "ozone": hourly.get("ozone", [None])[i],
                        "no2": hourly.get("nitrogen_dioxide", [None])[i],
                        "co": hourly.get("carbon_monoxide", [None])[i],
                        "so2": hourly.get("sulphur_dioxide", [None])[i],
                    }
                    hourly_forecast.append(hourly_item)

            # Create AirQuality object
            air_quality = AirQuality(
                aqi=overall_aqi,
                category=category,
                dominant_pollutant=dominant_pollutant,
                health_message=health_message,
                pm2_5=pm2_5,
                pm10=pm10,
                ozone=ozone,
                nitrogen_dioxide=no2,
                carbon_monoxide=co,
                sulfur_dioxide=so2,
                pm2_5_aqi=pm2_5_aqi,
                pm10_aqi=pm10_aqi,
                ozone_aqi=ozone_aqi,
                no2_aqi=no2_aqi,
                co_aqi=co_aqi,
                so2_aqi=so2_aqi,
                timestamp=current.get("time", ""),
                hourly_forecast=hourly_forecast,
            )

            return air_quality

        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Failed to parse air quality response: {e}")
            return None

