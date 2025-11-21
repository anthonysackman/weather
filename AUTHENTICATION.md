# Authentication System

## Overview

The Weather Display API supports **two authentication methods** that can be used interchangeably:

1. **Session Auth** (Basic Auth) - For web browsers and admin panel
2. **API Key Auth** (Bearer Token) - For ESP32 devices and programmatic access

## Authentication Methods

### 1. Session Authentication (Basic Auth)

Used by the web interface (admin panel, dashboard, etc.)

**Format:**
```
Authorization: Basic base64(username:password)
```

**Example:**
```bash
curl -u admin:password123 http://localhost:8000/api/devices
```

**Use Cases:**
- Admin panel
- User dashboard
- Web-based API testing

---

### 2. API Key Authentication (Bearer Token)

Used by ESP32 devices and external API consumers.

**Format:**
```
Authorization: Bearer {key_id}:{key_secret}
```

**Example:**
```bash
curl -H "Authorization: Bearer key_abc123:secret_xyz789" \
     http://localhost:8000/api/device/my-device-id/esp
```

**Use Cases:**
- ESP32 devices
- External applications
- Automated scripts
- Mobile apps

---

## Endpoint Authentication Requirements

### Public Endpoints (No Auth Required)
- `GET /docs` - API documentation
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

### Session-Only Endpoints
These require Basic Auth (username:password):

- `GET /admin` - Admin panel
- `GET /dashboard` - User dashboard
- `GET /login` - Login page
- `GET /register` - Registration page
- `POST /api/users/{id}/api-keys` - Generate API key (admin only)
- `DELETE /api/api-keys/{key_id}` - Revoke API key (admin only)

### Flexible Auth Endpoints
These accept **either** Session Auth **or** API Key Auth:

- `GET /api/devices` - List devices
- `POST /api/devices` - Create device
- `PUT /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Delete device
- `GET /api/device/{device_id}/data` - Get device data
- `GET /api/device/{device_id}/esp` - Get ESP32 optimized data
- `GET /api/users/{id}/api-keys` - View API keys
- `POST /api/api-keys/{key_id}/mark-viewed` - Mark secret as viewed
- `POST /api/api-keys/{key_id}/regenerate-secret` - Regenerate secret

---

## Getting an API Key

### For Users:
1. Log into your dashboard at `/dashboard`
2. Go to "API Keys" tab
3. If you have a key, it will be displayed
4. If you don't have a key, contact your administrator

### For Admins:
1. Log into admin panel at `/admin`
2. Go to "Users" tab
3. Click "Generate API Key" for any user
4. Copy the key_id and key_secret
5. The user will see the secret in their dashboard (once)

---

## Using API Keys

### In ESP32 Code

```cpp
#include <HTTPClient.h>

const char* API_KEY_ID = "key_abc123";
const char* API_KEY_SECRET = "secret_xyz789";
const char* DEVICE_ID = "my-device-id";

void getWeatherData() {
    HTTPClient http;
    
    // Build authorization header
    String auth = "Bearer " + String(API_KEY_ID) + ":" + String(API_KEY_SECRET);
    
    // Make request
    String url = "http://your-server.com/api/device/" + String(DEVICE_ID) + "/esp";
    http.begin(url);
    http.addHeader("Authorization", auth);
    
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        String payload = http.getString();
        // Parse JSON and display on screen
    } else {
        Serial.println("Error: " + String(httpCode));
    }
    
    http.end();
}
```

### In Python

```python
import requests

API_KEY_ID = "key_abc123"
API_KEY_SECRET = "secret_xyz789"
DEVICE_ID = "my-device-id"

headers = {
    "Authorization": f"Bearer {API_KEY_ID}:{API_KEY_SECRET}"
}

response = requests.get(
    f"http://your-server.com/api/device/{DEVICE_ID}/data",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### In JavaScript

```javascript
const API_KEY_ID = "key_abc123";
const API_KEY_SECRET = "secret_xyz789";
const DEVICE_ID = "my-device-id";

async function getWeatherData() {
    const response = await fetch(
        `http://your-server.com/api/device/${DEVICE_ID}/data`,
        {
            headers: {
                'Authorization': `Bearer ${API_KEY_ID}:${API_KEY_SECRET}`
            }
        }
    );
    
    if (response.ok) {
        const data = await response.json();
        console.log(data);
    } else {
        console.error('Error:', response.status);
    }
}
```

---

## Security Best Practices

### For API Keys:
1. **Never commit keys to version control** - Use environment variables
2. **Regenerate keys if compromised** - Use the dashboard regenerate feature
3. **Use HTTPS in production** - Encrypt all traffic
4. **One key per device/application** - Makes revocation easier
5. **Monitor last_used timestamps** - Detect unauthorized access

### For Passwords:
1. **Use strong passwords** - At least 12 characters
2. **Don't share admin credentials** - Create separate accounts
3. **Change passwords regularly** - Especially for admin accounts

---

## Error Responses

### 401 Unauthorized
No valid authentication provided:

```json
{
    "success": false,
    "error": "Authentication required",
    "hint": "Use Basic Auth (username:password) or Bearer token (key_id:key_secret)"
}
```

**Headers:**
```
WWW-Authenticate: Basic realm="Weather Display", Bearer realm="Weather Display API"
```

### 403 Forbidden
Authenticated but insufficient permissions:

```json
{
    "success": false,
    "error": "Unauthorized - you don't own this device"
}
```

or

```json
{
    "success": false,
    "error": "Insufficient permissions. Required role: admin"
}
```

---

## Implementation Details

### Flexible Auth Decorator

The `@flexible_auth()` decorator supports multiple authentication methods:

```python
from app.auth.flexible_auth import require_auth

# Accept both session and API key (default)
@devices_bp.get("/device/<device_id>/data")
@require_auth()
async def get_device_data(request, device_id):
    user = request.ctx.user  # Authenticated user
    auth_method = request.ctx.auth_method  # "session" or "api_key"
    pass

# Session only
@admin_bp.get("/admin")
@require_auth(methods=["session"])
async def admin_page(request):
    pass

# API key only
@devices_bp.get("/device/<device_id>/esp")
@require_auth(methods=["api_key"])
async def get_esp_data(request, device_id):
    pass

# Require admin role
@users_bp.post("/users/<user_id>/api-keys")
@require_auth(roles=["admin"])
async def generate_api_key(request, user_id):
    pass

# Session only + admin role
@admin_bp.delete("/users/<user_id>")
@require_auth(methods=["session"], roles=["admin"])
async def delete_user(request, user_id):
    pass
```

### Authentication Flow

1. **Request arrives** with `Authorization` header
2. **Decorator checks** which auth methods are allowed
3. **Try session auth** if `Authorization: Basic ...`
4. **Try API key auth** if `Authorization: Bearer ...`
5. **Verify credentials** against database
6. **Check role requirements** if specified
7. **Populate request context**:
   - `request.ctx.user` - Authenticated user object
   - `request.ctx.auth_method` - "session" or "api_key"
8. **Call route handler** or return 401/403

---

## Migration Guide

### Old Code (Session Only):
```python
from app.auth.middleware import require_auth

@devices_bp.get("/device/<device_id>/data")
@require_auth
async def get_device_data(request, device_id):
    pass
```

### New Code (Flexible Auth):
```python
from app.auth.flexible_auth import require_auth

@devices_bp.get("/device/<device_id>/data")
@require_auth()  # Note the parentheses!
async def get_device_data(request, device_id):
    pass
```

**Note:** The old `@require_auth` (without parentheses) still works but only accepts session auth for backwards compatibility.

---

## Testing Authentication

### Test Session Auth:
```bash
curl -u admin:password http://localhost:8000/api/devices
```

### Test API Key Auth:
```bash
curl -H "Authorization: Bearer key_abc:secret_xyz" \
     http://localhost:8000/api/device/test-device/esp
```

### Test in Browser:
1. Open `/admin` or `/dashboard`
2. Log in with username/password
3. Navigate to API Testing tab
4. Test endpoints (uses your session automatically)

---

## FAQ

**Q: Can I use API keys in the web browser?**
A: Yes, but session auth is more convenient. API keys are designed for programmatic access.

**Q: How long do API keys last?**
A: Forever, until revoked or regenerated.

**Q: Can I have multiple API keys?**
A: Currently, each user can have multiple keys (admins can generate multiple keys per user).

**Q: What happens if I lose my API key secret?**
A: Use the "Regenerate Secret" button in your dashboard. This will invalidate the old secret.

**Q: Can I use the same API key for multiple devices?**
A: Yes, but it's better to use one key per device for security and tracking.

**Q: Do API keys work with all endpoints?**
A: Most endpoints support API keys. Admin-specific operations (like user management) require session auth.

