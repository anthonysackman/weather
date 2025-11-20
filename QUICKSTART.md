# Quick Start Guide

Get your Weather Display API up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Create Your First Admin User

```bash
python create_admin.py admin mypassword123
```

You should see:
```
✅ Admin user 'admin' created successfully!

You can now login at: http://localhost:8000/admin
Username: admin
Password: mypassword123
```

## Step 3: Start the Server

```bash
python app/main.py
```

You should see:
```
[INFO] Database initialized
[INFO] Sanic app running on http://0.0.0.0:8000
```

## Step 4: Access the Admin Interface

1. Open your browser to: `http://localhost:8000/admin`
2. Login with your credentials (username: `admin`, password: `mypassword123`)
3. Add your first device:
   - **Device Name**: "My Weather Display"
   - **Address**: "123 Main St, Miami, FL 33101"
4. Click "Add Device"

The system will automatically:
- Geocode your address to coordinates
- Determine the timezone
- Generate a unique device ID

## Step 5: Test Your Device

After adding a device, you'll see it in the list with a device ID like: `abc123xyz...`

Click "Test Weather" to see current weather data!

## Step 6: Use the Device ID in Your ESP32

Copy the device ID and use it in your ESP32 code:

```cpp
const char* DEVICE_ID = "your_device_id_here";
const char* API_URL = "http://your-server:8000/api/device/";

void getWeather() {
  HTTPClient http;
  String url = String(API_URL) + DEVICE_ID + "/weather";
  
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String payload = http.getString();
    // Parse and display weather data
  }
  
  http.end();
}
```

## Testing Without ESP32

You can test the device endpoint directly:

```bash
curl http://localhost:8000/api/device/YOUR_DEVICE_ID/weather
```

## What's Next?

- Add more devices for different locations
- Customize the display settings (coming soon)
- Deploy to a cloud server for remote access
- Flash your ESP32 and enjoy your weather display!

## Troubleshooting

### "Failed to geocode address"
- Make sure you're using a complete street address
- Try a simpler format: "City, State ZIP"
- Check your internet connection (needs to reach OpenStreetMap)

### "Moon phase data not available"
- This is optional - the API works without it
- To enable: Sign up at [AstronomyAPI](https://astronomyapi.com/)
- Add credentials to `.env` file

### Database errors
- Make sure the app has write permissions in the current directory
- Check that `weather_display.db` isn't locked by another process

## Need Help?

Check the full [README.md](README.md) for detailed documentation!

