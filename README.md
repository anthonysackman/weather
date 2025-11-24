# Weather Display API

A comprehensive weather API designed for ESP32 weather displays with device management, authentication, and address-based configuration.

<!-- Workflow test: will trigger GitHub Actions deploy when pushed -->

## Features

- 🌤️ **Comprehensive Weather Data** - Current conditions, hourly/daily forecasts, moon phase
- 📍 **Address Geocoding** - Convert street addresses to coordinates automatically
- 🔐 **Secure Admin Interface** - Basic auth protected device management
- 🎯 **Device Management** - Register and configure multiple ESP32 devices
- 🌍 **Multiple Data Sources**
  - Open-Meteo API (weather & geocoding)
  - AstronomyAPI (moon phase)
  - OpenStreetMap Nominatim (address geocoding)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file:

```env
# Optional: Astronomy API credentials (for moon phase data)
ASTRONOMY_API_ID=your_app_id
ASTRONOMY_API_SECRET=your_app_secret

# Optional: Custom database path
DB_PATH=./weather_display.db

# Optional: Custom port
PORT=8000
```

### 3. Create Admin User

```bash
python create_admin.py admin yourpassword123
```

### 4. Run the Server

```bash
python app/main.py
```

The server will start on `http://localhost:8000`

## API Endpoints

### Public Endpoints (No Auth Required)

#### Get Device Weather
```
GET /api/device/{device_id}/weather
```

Returns comprehensive weather data for a registered device.

**Response:**
```json
{
  "success": true,
  "device": {
    "device_id": "abc123...",
    "name": "Living Room Display",
    "address": "123 Main St, Miami, FL"
  },
  "weather": {
    "temperature": 75.2,
    "feels_like": 73.8,
    "humidity": 65,
    "weather_description": "Partly cloudy",
    "windspeed": 8.5,
    "sunrise": "2024-01-15T06:45:00",
    "sunset": "2024-01-15T18:30:00",
    "hourly_forecast": [...],
    "daily_forecast": [...],
    "moon_phase": {
      "phase": "Waxing Crescent",
      "illumination": 23.5
    }
  }
}
```

### Admin Endpoints (Basic Auth Required)

#### List All Devices
```
GET /api/devices
Authorization: Basic base64(username:password)
```

#### Create Device
```
POST /api/devices
Authorization: Basic base64(username:password)
Content-Type: application/json

{
  "name": "Living Room Display",
  "address": "123 Main St, Miami, FL 33101"
}
```

The API will automatically geocode the address to coordinates.

#### Get Device Details
```
GET /api/devices/{device_id}
Authorization: Basic base64(username:password)
```

#### Update Device
```
PUT /api/devices/{device_id}
Authorization: Basic base64(username:password)
Content-Type: application/json

{
  "name": "Updated Name",
  "address": "New Address"
}
```

#### Delete Device
```
DELETE /api/devices/{device_id}
Authorization: Basic base64(username:password)
```

### Legacy Test Endpoints

These endpoints are available for testing:

- `GET /` - Test interface
- `GET /geo?city=Miami&state=FL` - Geocoding test
- `GET /weather?lat=25.7617&lon=-80.1918&timezone=America/New_York` - Weather test
- `GET /moon?lat=25.7617&lon=-80.1918` - Moon phase test
- `GET /combined?city=Miami&state=FL` - Combined test

## Admin Web Interface

Access the admin interface at `http://localhost:8000/admin`

Features:
- 🔐 Secure login with Basic Auth
- ➕ Add new devices with address autocomplete
- 📝 View all registered devices
- 🗑️ Delete devices
- 🧪 Test weather data for each device
- 📊 View device last-seen timestamps

## ESP32 Integration

### Example ESP32 Code

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* DEVICE_ID = "your_device_id_here";
const char* API_URL = "http://your-server:8000/api/device/";

void getWeather() {
  HTTPClient http;
  String url = String(API_URL) + DEVICE_ID + "/weather";
  
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String payload = http.getString();
    
    // Parse JSON
    DynamicJsonDocument doc(8192);
    deserializeJson(doc, payload);
    
    float temp = doc["weather"]["temperature"];
    int humidity = doc["weather"]["humidity"];
    String description = doc["weather"]["weather_description"];
    
    // Update your display here
    Serial.printf("Temp: %.1f°F, Humidity: %d%%, %s\n", 
                  temp, humidity, description.c_str());
  }
  
  http.end();
}
```

### Device ID

When you create a device in the admin interface, a unique device ID is generated. Use this ID in your ESP32 code to fetch weather data.

The device ID serves as authentication - only devices with valid IDs can access weather data.

## Database Schema

### Devices Table
- `device_id` - Unique identifier (auto-generated)
- `name` - Display name
- `address` - Street address
- `lat`, `lon` - Geocoded coordinates
- `timezone` - IANA timezone
- `display_settings` - JSON settings (future use)
- `last_seen` - Last API call timestamp
- `created_at`, `updated_at` - Timestamps

### Users Table
- `username` - Admin username
- `password_hash` - Bcrypt hashed password
- `created_at` - Creation timestamp

## Development

### Project Structure

```
weather/
├── app/
│   ├── api/
│   │   ├── admin.py          # Admin web interface
│   │   ├── datatest.py       # Legacy test endpoints
│   │   ├── devices.py        # Device management API
│   │   └── health.py         # Health check endpoints
│   ├── auth/
│   │   ├── middleware.py     # Auth decorator
│   │   └── utils.py          # Password hashing
│   ├── database/
│   │   ├── db.py            # Database operations
│   │   └── models.py        # Data models
│   ├── services/
│   │   ├── address_client.py    # Address geocoding
│   │   ├── astronomy_client.py  # Moon phase
│   │   ├── geo_client.py        # City/state geocoding
│   │   └── weather_client.py    # Weather data
│   ├── templates/
│   │   ├── admin.html       # Admin interface
│   │   └── index.html       # Test interface
│   └── main.py              # Application entry point
├── create_admin.py          # CLI tool to create admin users
├── requirements.txt
└── README.md
```

### Adding New Admin Users

```bash
python create_admin.py <username> <password>
```

### Database Location

By default, the SQLite database is created at `./weather_display.db`

You can customize this with the `DB_PATH` environment variable.

## Docker Deployment

Build and run with Docker Compose (the stack is defined in `compose.yaml`):

```bash
docker compose -f compose.yaml build
docker compose -f compose.yaml up -d --force-recreate --remove-orphans
```

For local development you can override the production paths by setting `ENV_FILE`/`DB_FILE` before running Compose so it uses repo-local secrets:

```bash
mkdir -p etc/weather
cat <<'EOF' > etc/weather/.env
DB_PATH=./weather_display.db
PORT=8000
ASTRONOMY_API_ID=...
ASTRONOMY_API_SECRET=...
EOF

ENV_FILE=./etc/weather/.env DB_FILE=./weather_display.db docker compose -f compose.yaml up -d --force-recreate --remove-orphans
```

## Security Notes

- **Device IDs** serve as authentication for ESP32 devices
- **Basic Auth** protects admin endpoints
- Store your `.env` file securely and don't commit it to version control
- Use HTTPS in production
- Consider adding rate limiting for production use

## Gift-Ready Setup

This API is designed to be easily gifted:

1. Deploy the API to a server (Heroku, DigitalOcean, etc.)
2. Create a device in the admin interface with the recipient's address
3. Flash the ESP32 with the device ID
4. The recipient gets a working weather display with no configuration needed!

## Future Enhancements

- [ ] Weather alerts and notifications
- [ ] Custom display themes per device
- [ ] Historical weather data storage
- [ ] Multiple location support per device
- [ ] Email notifications for offline devices
- [ ] API rate limiting
- [ ] OAuth2 authentication option

## License

MIT License - Feel free to use this for personal or commercial projects!

## Credits

- Weather data: [Open-Meteo](https://open-meteo.com/)
- Moon phase: [AstronomyAPI](https://astronomyapi.com/)
- Geocoding: [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/)
