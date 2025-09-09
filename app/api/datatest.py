"""Main weather interface endpoints."""

from sanic import Blueprint
from sanic.response import json, html
from sanic.request import Request
from app.services.weather_client import WeatherClient
from app.services.geo_client import GeoClient
from app.services.astronomy_client import AstronomyClient
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", url_prefix="/")


@main_bp.get("/")
async def main_page(request: Request):
    """Serve the main weather interface."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weather Display Control Panel</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }
            .container { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, button { padding: 10px; margin: 5px 0; }
            input { width: 200px; }
            button { background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { background: white; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #007bff; }
            .error { border-left-color: #dc3545; }
            pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>🌤️ Weather Display Control Panel</h1>
        
        <!-- Location Detection -->
        <div class="container">
            <h2>📱 Auto-Detect Location</h2>
            <button onclick="detectLocation()" id="detect-btn">📍 Use My Current Location</button>
            <div id="location-status"></div>
        </div>
        
        <!-- Geocoding Test -->
        <div class="container">
            <h2>📍 Test Geocoding</h2>
            <div class="form-group">
                <label for="city">City Name:</label>
                <input type="text" id="city" placeholder="New York" value="New York">
            </div>
            <div class="form-group">
                <label for="state">State (optional):</label>
                <input type="text" id="state" placeholder="NY" value="NY">
            </div>
            <button onclick="testGeo()">Get Coordinates</button>
            <div id="geo-result"></div>
        </div>

        <!-- Weather Test -->
        <div class="container">
            <h2>🌤️ Test Weather</h2>
            <div class="form-group">
                <label for="lat">Latitude:</label>
                <input type="number" id="lat" step="any" placeholder="40.7128" value="40.7128">
            </div>
            <div class="form-group">
                <label for="lon">Longitude:</label>
                <input type="number" id="lon" step="any" placeholder="-74.0060" value="-74.0060">
            </div>
            <div class="form-group">
                <label for="timezone">Timezone:</label>
                <input type="text" id="timezone" placeholder="America/New_York" value="America/New_York">
            </div>
            <button onclick="testWeather()">Get Weather</button>
            <div id="weather-result"></div>
        </div>

        <!-- Moon Phase Test -->
        <div class="container">
            <h2>🌙 Test Moon Phase</h2>
            <div class="form-row">
                <div class="form-group">
                    <label for="moon-lat">Latitude:</label>
                    <input type="number" id="moon-lat" step="any" placeholder="40.7128" value="40.7128">
                </div>
                <div class="form-group">
                    <label for="moon-lon">Longitude:</label>
                    <input type="number" id="moon-lon" step="any" placeholder="-74.0060" value="-74.0060">
                </div>
            </div>
            <button onclick="testMoonPhase()">Get Moon Phase</button>
            <div id="moon-result"></div>
        </div>

        <!-- Combined Test -->
        <div class="container">
            <h2>🔗 Combined Test (Geo + Weather)</h2>
            <div class="form-group">
                <label for="combined-city">City:</label>
                <input type="text" id="combined-city" placeholder="Miami" value="Miami">
            </div>
            <div class="form-group">
                <label for="combined-state">State:</label>
                <input type="text" id="combined-state" placeholder="FL" value="FL">
            </div>
            <button onclick="testCombined()">Get Location + Weather</button>
            <div id="combined-result"></div>
        </div>

        <script>
            // Helper functions for weather display
            function getWindDirection(degrees) {
                if (degrees === null || degrees === undefined) return '';
                const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
                return directions[Math.round(degrees / 22.5) % 16];
            }
            
            function formatTime(timeString) {
                if (!timeString) return 'N/A';
                try {
                    const date = new Date(timeString);
                    return date.toLocaleTimeString('en-US', { 
                        hour: 'numeric', 
                        minute: '2-digit',
                        hour12: true 
                    });
                } catch {
                    return timeString;
                }
            }
            
            function formatDate(dateString) {
                if (!dateString) return 'N/A';
                try {
                    const date = new Date(dateString);
                    return date.toLocaleDateString('en-US', { 
                        weekday: 'short',
                        month: 'short', 
                        day: 'numeric' 
                    });
                } catch {
                    return dateString;
                }
            }

            function detectLocation() {
                const statusDiv = document.getElementById('location-status');
                const detectBtn = document.getElementById('detect-btn');
                
                if (!navigator.geolocation) {
                    statusDiv.innerHTML = `
                        <div class="result error">
                            <p>Geolocation is not supported by this browser.</p>
                        </div>
                    `;
                    return;
                }
                
                detectBtn.disabled = true;
                detectBtn.textContent = '🔍 Detecting location...';
                
                statusDiv.innerHTML = `
                    <div class="result">
                        <p>Requesting location permission...</p>
                    </div>
                `;
                
                navigator.geolocation.getCurrentPosition(
                    async function(position) {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        
                        statusDiv.innerHTML = `
                            <div class="result">
                                <p>✅ Location detected: ${lat.toFixed(4)}, ${lon.toFixed(4)}</p>
                                <p>Getting location details...</p>
                            </div>
                        `;
                        
                        // Reverse geocode to get city/state info
                        try {
                            const response = await fetch(`/reverse-geo?lat=${lat}&lon=${lon}`);
                            const data = await response.json();
                            
                            if (data.success) {
                                // Fill all forms with detected location
                                document.getElementById('lat').value = lat.toFixed(4);
                                document.getElementById('lon').value = lon.toFixed(4);
                                document.getElementById('timezone').value = data.timezone || 'America/New_York';
                                
                                // Fill city/state forms
                                document.getElementById('city').value = data.city || '';
                                document.getElementById('state').value = data.state || '';
                                document.getElementById('combined-city').value = data.city || '';
                                document.getElementById('combined-state').value = data.state || '';
                                
                                statusDiv.innerHTML = `
                                    <div class="result">
                                        <h3>✅ Location Auto-Filled!</h3>
                                        <p><strong>Location:</strong> ${data.city || 'Unknown'}, ${data.state || 'Unknown'}</p>
                                        <p><strong>Coordinates:</strong> ${lat.toFixed(4)}, ${lon.toFixed(4)}</p>
                                        <p><strong>Timezone:</strong> ${data.timezone || 'Unknown'}</p>
                                        <p>All forms have been populated with your location!</p>
                                    </div>
                                `;
                                
                                // Highlight all forms briefly
                                const containers = document.querySelectorAll('.container');
                                containers.forEach(container => {
                                    if (container.querySelector('h2').textContent.includes('Test')) {
                                        container.style.border = '2px solid #28a745';
                                        container.style.backgroundColor = '#f8fff9';
                                    }
                                });
                                setTimeout(() => {
                                    containers.forEach(container => {
                                        container.style.border = '';
                                        container.style.backgroundColor = '#f5f5f5';
                                    });
                                }, 3000);
                                
                            } else {
                                // Still fill coordinates even if reverse geocoding fails
                                document.getElementById('lat').value = lat.toFixed(4);
                                document.getElementById('lon').value = lon.toFixed(4);
                                
                                statusDiv.innerHTML = `
                                    <div class="result">
                                        <h3>⚠️ Partial Success</h3>
                                        <p><strong>Coordinates:</strong> ${lat.toFixed(4)}, ${lon.toFixed(4)}</p>
                                        <p>Could not determine city/state, but coordinates have been filled.</p>
                                    </div>
                                `;
                            }
                        } catch (error) {
                            // Still fill coordinates even if API fails
                            document.getElementById('lat').value = lat.toFixed(4);
                            document.getElementById('lon').value = lon.toFixed(4);
                            
                            statusDiv.innerHTML = `
                                <div class="result">
                                    <h3>⚠️ Partial Success</h3>
                                    <p><strong>Coordinates:</strong> ${lat.toFixed(4)}, ${lon.toFixed(4)}</p>
                                    <p>Coordinates filled, but couldn't get location details.</p>
                                </div>
                            `;
                        }
                        
                        detectBtn.disabled = false;
                        detectBtn.textContent = '📍 Use My Current Location';
                    },
                    function(error) {
                        let errorMessage = 'Unknown error occurred.';
                        switch(error.code) {
                            case error.PERMISSION_DENIED:
                                errorMessage = 'Location access denied by user.';
                                break;
                            case error.POSITION_UNAVAILABLE:
                                errorMessage = 'Location information unavailable.';
                                break;
                            case error.TIMEOUT:
                                errorMessage = 'Location request timed out.';
                                break;
                        }
                        
                        statusDiv.innerHTML = `
                            <div class="result error">
                                <h3>❌ Location Detection Failed</h3>
                                <p>${errorMessage}</p>
                                <p>You can still enter location manually below.</p>
                            </div>
                        `;
                        
                        detectBtn.disabled = false;
                        detectBtn.textContent = '📍 Use My Current Location';
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 300000 // 5 minutes
                    }
                );
            }

            async function testGeo() {
                const city = document.getElementById('city').value;
                const state = document.getElementById('state').value;
                const resultDiv = document.getElementById('geo-result');
                
                try {
                    const response = await fetch(`/geo?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}`);
                    const data = await response.json();
                    
                    resultDiv.innerHTML = `
                        <div class="result">
                            <h3>Geocoding Result:</h3>
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    `;
                    
                    // Auto-populate weather form if geocoding was successful
                    if (data.success && data.location) {
                        document.getElementById('lat').value = data.location.lat.toFixed(4);
                        document.getElementById('lon').value = data.location.lon.toFixed(4);
                        document.getElementById('timezone').value = data.location.timezone;
                        
                        // Add visual feedback
                        const weatherContainer = document.querySelector('.container:nth-child(3)');
                        weatherContainer.style.border = '2px solid #28a745';
                        weatherContainer.style.backgroundColor = '#f8fff9';
                        setTimeout(() => {
                            weatherContainer.style.border = '';
                            weatherContainer.style.backgroundColor = '#f5f5f5';
                        }, 2000);
                    }
                } catch (error) {
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <h3>Error:</h3>
                            <p>${error.message}</p>
                        </div>
                    `;
                }
            }

            async function testWeather() {
                const lat = document.getElementById('lat').value;
                const lon = document.getElementById('lon').value;
                const timezone = document.getElementById('timezone').value;
                const resultDiv = document.getElementById('weather-result');
                
                try {
                    const response = await fetch(`/weather?lat=${lat}&lon=${lon}&timezone=${encodeURIComponent(timezone)}`);
                    const data = await response.json();
                    
                    if (data.success && data.weather) {
                        const w = data.weather;
                        resultDiv.innerHTML = `
                            <div class="result">
                                <h3>🌤️ Current Weather</h3>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 10px 0;">
                                    <div>
                                        <strong>🌡️ Temperature:</strong> ${w.temperature}°F (feels like ${w.feels_like}°F)<br>
                                        <strong>📊 Condition:</strong> ${w.weather_description}<br>
                                        <strong>💧 Humidity:</strong> ${w.humidity}%<br>
                                        <strong>🌬️ Wind:</strong> ${w.windspeed} mph ${getWindDirection(w.winddirection)}<br>
                                        <strong>💨 Wind Gusts:</strong> ${w.wind_gusts} mph<br>
                                        <strong>☁️ Cloud Cover:</strong> ${w.cloud_cover}%
                                    </div>
                                    <div>
                                        <strong>🌅 Sunrise:</strong> ${formatTime(w.sunrise)}<br>
                                        <strong>🌇 Sunset:</strong> ${formatTime(w.sunset)}<br>
                                        <strong>📈 High:</strong> ${w.temp_max}°F<br>
                                        <strong>📉 Low:</strong> ${w.temp_min}°F<br>
                                        <strong>☀️ UV Index:</strong> ${w.uv_index}<br>
                                        <strong>🔍 Visibility:</strong> ${(w.visibility * 0.000621371).toFixed(1)} miles<br>
                                        <strong>🌙 Moon:</strong> ${w.moon_phase ? `${w.moon_phase.phase} (${w.moon_phase.illumination.toFixed(1)}%)` : 'N/A'}
                                    </div>
                                </div>
                                
                                ${w.precipitation > 0 ? `
                                <div style="background: #e3f2fd; padding: 10px; border-radius: 4px; margin: 10px 0;">
                                    <strong>🌧️ Precipitation:</strong> ${w.precipitation}" | 
                                    Rain: ${w.rain}" | Snow: ${w.snowfall}"
                                </div>
                                ` : ''}
                                
                                <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0;">
                                    <strong>📊 Pressure:</strong> ${(w.pressure * 0.02953).toFixed(2)} inHg
                                </div>
                                
                                ${w.moon_phase ? `
                                <div style="background: #f3e5f5; padding: 10px; border-radius: 4px; margin: 10px 0;">
                                    <strong>🌙 Moon Phase Details</strong><br>
                                    <strong>Phase:</strong> ${w.moon_phase.phase}<br>
                                    <strong>Illumination:</strong> ${w.moon_phase.illumination.toFixed(1)}%<br>
                                    <strong>Age:</strong> ${w.moon_phase.age.toFixed(1)} days<br>
                                    <strong>Distance:</strong> ${(w.moon_phase.distance * 0.621371).toFixed(0)} miles from Earth
                                </div>
                                ` : ''}
                                
                                <details style="margin: 10px 0;">
                                    <summary><strong>📅 7-Day Forecast</strong></summary>
                                    <div style="margin-top: 10px;">
                                        ${w.daily_forecast.map(day => `
                                            <div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #eee; font-size: 0.9em;">
                                                <span><strong>${formatDate(day.date)}</strong></span>
                                                <span>${day.weather_description || 'N/A'}</span>
                                                <span>${day.temp_max}°/${day.temp_min}°F</span>
                                                <span>☀️ ${day.daylight_duration || 'N/A'}h</span>
                                                <span>☔ ${day.precipitation_probability_max || 0}%</span>
                                                <span>💧 ${day.precipitation_sum || 0}"</span>
                                            </div>
                                        `).join('')}
                                    </div>
                                </details>
                                
                                <details style="margin: 10px 0;">
                                    <summary><strong>⏰ Hourly Forecast (next ${(() => {
                                        const futureHours = w.hourly_forecast.filter(hour => {
                                            const hourTime = new Date(hour.time);
                                            const now = new Date();
                                            return hourTime >= now;
                                        });
                                        return Math.min(24, futureHours.length);
                                    })()}h)</strong></summary>
                                    <div style="margin-top: 10px; max-height: 200px; overflow-y: auto;">
                                        ${w.hourly_forecast.filter((hour, index) => {
                                            const hourTime = new Date(hour.time);
                                            const now = new Date();
                                            return hourTime >= now;
                                        }).slice(0, 24).map(hour => `
                                            <div style="display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #f0f0f0; font-size: 0.9em;">
                                                <span><strong>${formatTime(hour.time)}</strong></span>
                                                <span>${hour.temperature}°F</span>
                                                <span>${hour.weather_description || 'N/A'}</span>
                                                <span>☔ ${hour.precipitation_probability || 0}%</span>
                                            </div>
                                        `).join('')}
                                    </div>
                                </details>
                                
                                <details style="margin: 10px 0;">
                                    <summary><strong>🔍 Raw Data</strong></summary>
                                    <pre style="font-size: 0.8em; max-height: 200px; overflow-y: auto;">${JSON.stringify(data, null, 2)}</pre>
                                </details>
                            </div>
                        `;
                    } else {
                        resultDiv.innerHTML = `
                            <div class="result error">
                                <h3>Weather Result:</h3>
                                <pre>${JSON.stringify(data, null, 2)}</pre>
                            </div>
                        `;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <h3>Error:</h3>
                            <p>${error.message}</p>
                        </div>
                    `;
                }
            }

            async function testMoonPhase() {
                const lat = document.getElementById('moon-lat').value;
                const lon = document.getElementById('moon-lon').value;
                const resultDiv = document.getElementById('moon-result');
                
                try {
                    const response = await fetch(`/moon?lat=${lat}&lon=${lon}`);
                    const data = await response.json();
                    
                    resultDiv.innerHTML = `
                        <div class="result">
                            <h3>🌙 Moon Phase Result:</h3>
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    `;
                } catch (error) {
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <h3>Error:</h3>
                            <p>${error.message}</p>
                        </div>
                    `;
                }
            }

            async function testCombined() {
                const city = document.getElementById('combined-city').value;
                const state = document.getElementById('combined-state').value;
                const resultDiv = document.getElementById('combined-result');
                
                try {
                    const response = await fetch(`/combined?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}`);
                    const data = await response.json();
                    
                    resultDiv.innerHTML = `
                        <div class="result">
                            <h3>Combined Result:</h3>
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    `;
                } catch (error) {
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <h3>Error:</h3>
                            <p>${error.message}</p>
                        </div>
                    `;
                }
            }
        </script>
    </body>
    </html>
    """
    return html(html_content)


@main_bp.get("/geo")
async def test_geo(request: Request):
    """Test geocoding client."""
    city = request.args.get("city", "New York")
    state = request.args.get("state", "")

    geo_client = GeoClient()
    location = await geo_client.get_coordinates(city, state)

    if location:
        return json(
            {
                "success": True,
                "location": {
                    "lat": location.lat,
                    "lon": location.lon,
                    "name": location.name,
                    "state": location.state,
                    "timezone": location.timezone,
                },
            }
        )
    else:
        return json({"success": False, "error": "Location not found"}, status=404)


@main_bp.get("/weather")
async def test_weather(request: Request):
    """Test weather client."""
    try:
        lat = float(request.args.get("lat", "40.7128"))
        lon = float(request.args.get("lon", "-74.0060"))
        timezone = request.args.get("timezone", "America/New_York")

        weather_client = WeatherClient()
        astronomy_client = AstronomyClient()

        # Get weather and moon phase data
        weather = await weather_client.get_current_weather(lat, lon, timezone)
        moon_phase = await astronomy_client.get_moon_phase(lat, lon)

        if weather:
            return json(
                {
                    "success": True,
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
                        # Weather alerts
                        "weather_alerts": weather.weather_alerts,
                        # Moon phase data
                        "moon_phase": {
                            "phase": moon_phase.phase if moon_phase else "Unknown",
                            "illumination": moon_phase.illumination
                            if moon_phase
                            else 0,
                            "age": moon_phase.age if moon_phase else 0,
                            "distance": moon_phase.distance if moon_phase else 0,
                        }
                        if moon_phase
                        else None,
                    },
                }
            )
        else:
            return json(
                {"success": False, "error": "Weather data not available"}, status=500
            )

    except ValueError:
        return json(
            {"success": False, "error": "Invalid latitude or longitude"}, status=400
        )


@main_bp.get("/reverse-geo")
async def reverse_geocode(request: Request):
    """Reverse geocode coordinates to get city/state info."""
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))

        # Use OpenStreetMap Nominatim for reverse geocoding (free service)
        import httpx

        nominatim_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1"

        try:
            async with httpx.AsyncClient() as client:
                # Set a proper user agent as required by Nominatim
                headers = {"User-Agent": "WeatherDisplayApp/1.0"}
                response = await client.get(nominatim_url, headers=headers)
                response.raise_for_status()
                data = response.json()

                # Extract city and state from the response
                address = data.get("address", {})

                # Try different city name fields in order of preference
                city = (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                    or address.get("hamlet")
                    or address.get("municipality")
                    or address.get("suburb")
                    or address.get("neighbourhood")
                    or address.get("locality")
                    or address.get("district")
                    or address.get("county")  # County as last resort
                    or ""
                )

                # Get state/province
                state = address.get("state") or address.get("province") or ""

                # Basic timezone estimation based on longitude
                timezone_offset = int(lon / 15)
                if -8 <= timezone_offset <= -5:  # US timezones
                    if timezone_offset == -8:
                        timezone = "America/Los_Angeles"
                    elif timezone_offset == -7:
                        timezone = "America/Denver"
                    elif timezone_offset == -6:
                        timezone = "America/Chicago"
                    else:  # -5
                        timezone = "America/New_York"
                else:
                    timezone = "America/New_York"  # Default

                return json(
                    {
                        "success": True,
                        "city": city,
                        "state": state,
                        "timezone": timezone,
                        "lat": lat,
                        "lon": lon,
                        "full_address": data.get("display_name", ""),
                        "country": address.get("country", ""),
                        "debug_address_fields": address,  # Temporary debug info
                    }
                )

        except Exception as api_error:
            logger.warning(f"Reverse geocoding failed: {api_error}")

            # Fallback to basic timezone only
            timezone_offset = int(lon / 15)
            if -8 <= timezone_offset <= -5:
                if timezone_offset == -8:
                    timezone = "America/Los_Angeles"
                elif timezone_offset == -7:
                    timezone = "America/Denver"
                elif timezone_offset == -6:
                    timezone = "America/Chicago"
                else:
                    timezone = "America/New_York"
            else:
                timezone = "America/New_York"

            return json(
                {
                    "success": True,
                    "city": "",
                    "state": "",
                    "timezone": timezone,
                    "lat": lat,
                    "lon": lon,
                    "note": "Reverse geocoding service unavailable, timezone estimated",
                }
            )

    except (ValueError, TypeError):
        return json({"success": False, "error": "Invalid coordinates"}, status=400)


@main_bp.get("/moon")
async def test_moon_phase(request: Request):
    """Test moon phase API."""
    try:
        lat = float(request.args.get("lat", "40.7128"))
        lon = float(request.args.get("lon", "-74.0060"))

        astronomy_client = AstronomyClient()
        moon_phase = await astronomy_client.get_moon_phase(lat, lon)

        if moon_phase:
            return json(
                {
                    "success": True,
                    "moon_phase": {
                        "phase": moon_phase.phase,
                        "illumination": moon_phase.illumination,
                        "age": moon_phase.age,
                        "distance": moon_phase.distance,
                        "angular_diameter": moon_phase.angular_diameter,
                    },
                }
            )
        else:
            return json(
                {
                    "success": False,
                    "error": "Moon phase data not available",
                    "debug": "Check logs for API errors",
                },
                status=500,
            )

    except ValueError:
        return json(
            {"success": False, "error": "Invalid latitude or longitude"}, status=400
        )


@main_bp.get("/combined")
async def test_combined(request: Request):
    """Test both clients together - get location then weather."""
    city = request.args.get("city", "Miami")
    state = request.args.get("state", "FL")

    # First get coordinates
    geo_client = GeoClient()
    location = await geo_client.get_coordinates(city, state)

    if not location:
        return json({"success": False, "error": "Location not found"}, status=404)

    # Then get weather for those coordinates
    weather_client = WeatherClient()
    weather = await weather_client.get_current_weather(
        location.lat, location.lon, location.timezone
    )

    if not weather:
        return json(
            {"success": False, "error": "Weather data not available for this location"},
            status=500,
        )

    return json(
        {
            "success": True,
            "location": {
                "lat": location.lat,
                "lon": location.lon,
                "name": location.name,
                "state": location.state,
                "timezone": location.timezone,
            },
            "weather": {
                "temperature": weather.temperature,
                "feels_like": weather.feels_like,
                "windspeed": weather.windspeed,
                "winddirection": weather.winddirection,
                "humidity": weather.humidity,
                "weathercode": weather.weathercode,
                "temp_min": weather.temp_min,
                "temp_max": weather.temp_max,
                "timestamp": weather.timestamp,
                "sunrise": weather.sunrise,
                "sunset": weather.sunset,
            },
        }
    )
