# Weather Display API - UI Structure

## 🎯 Overview

The application now has a **login-first** architecture where all features are gated behind authentication.

## 📄 Page Structure

### Public Pages (No Authentication Required)

#### `/` - Home / Login
- **Purpose**: Main entry point and login page
- **Features**:
  - Username/password login
  - Link to registration
  - Link to API docs
- **Redirects**:
  - Regular users → `/dashboard`
  - Admins → `/admin`

#### `/register` - User Registration
- **Purpose**: Self-service account creation
- **Features**:
  - Username, email, password fields
  - Password confirmation
  - Automatic account creation
- **After Registration**: Redirects to `/login`

#### `/docs` - API Documentation
- **Purpose**: Public API documentation
- **Features**:
  - Complete API reference
  - Code examples
  - Authentication guide
  - No login required (for developers)

---

### Authenticated Pages (Login Required)

#### `/dashboard` - User Dashboard
- **Purpose**: Main hub for regular users
- **Access**: All authenticated users
- **Features**:
  - **API Keys Tab**:
    - View all API keys
    - Generate new keys
    - Delete keys
    - See key usage stats
    - ⚠️ Secrets shown only once
  - **My Devices Tab**:
    - View devices owned by user
    - See device status (last seen)
    - Device details (ID, address, timezone)
  - **Profile Tab**:
    - Username, email, role
    - Account information

#### `/test` - API Test Interface
- **Purpose**: Interactive API testing tool
- **Access**: All authenticated users
- **Features**:
  - Location detection
  - Geocoding test
  - Weather data test
  - Moon phase test
  - Combined data test
  - Real-time results

---

### Admin Pages (Admin Role Required)

#### `/admin` - Admin Panel
- **Purpose**: System administration
- **Access**: Users with `role='admin'` only
- **Current Features**:
  - **Devices Tab**:
    - View all devices
    - Add new devices
    - Edit devices
    - Delete devices
    - Test device weather
- **Planned Features** (Next Phase):
  - **Users Tab**:
    - View all users
    - Grant/revoke admin role
    - Manage user API keys
    - Delete users
  - **API Keys Tab**:
    - View all API keys system-wide
    - See key usage
    - Revoke any key

---

## 🔐 Authentication Flow

### Login Flow
```
1. User visits / (or any protected page)
2. If not logged in → Redirect to /
3. User enters credentials
4. Backend validates with Basic Auth
5. Store credentials in localStorage
6. Redirect based on role:
   - admin → /admin
   - user → /dashboard
```

### Session Management
- **Method**: HTTP Basic Authentication
- **Storage**: localStorage (browser)
- **Credentials**: Base64 encoded username:password
- **Validation**: Every API request includes `Authorization: Basic {credentials}`

### Logout Flow
```
1. User clicks Logout
2. Clear localStorage (auth_credentials, user)
3. Redirect to /
```

---

## 🎨 Navigation Structure

### Public Pages Navigation
```
Login/Register:
- Link to /docs
- Link between /login and /register
```

### Authenticated Pages Navigation
```
Top Navigation Bar:
┌─────────────────────────────────────────────┐
│ ⛅ Weather Display  [Dashboard] [API Test] [Docs] [User Menu ▼] │
└─────────────────────────────────────────────┘

User Menu Dropdown:
- Dashboard
- API Test
- ─────────
- Logout
```

### Admin Navigation
```
Same as authenticated + Admin link
```

---

## 🔑 API Key System

### Key Structure
```javascript
{
  "key_id": "key_abc123...",      // Public identifier
  "key_secret": "secret_xyz...",  // Secret (shown once)
  "name": "My ESP32",             // User-friendly name
  "created_at": "2024-01-15...",
  "last_used": "2024-01-16...",
  "expires_at": null              // Optional expiration
}
```

### Key Usage
- **Belongs to**: Users (not devices)
- **Used with**: Any device owned by the user
- **Authentication**: HMAC signature (coming in Phase 2)
- **Management**:
  - Users can generate/delete their own keys
  - Admins can manage any user's keys

---

## 📊 User Roles

### Regular User (`role='user'`)
**Can Access**:
- `/dashboard` - View/manage own API keys and devices
- `/test` - Test API endpoints
- `/docs` - Read documentation

**Cannot Access**:
- `/admin` - Admin panel
- Other users' data

**Permissions**:
- ✅ Generate own API keys
- ✅ Delete own API keys
- ✅ View own devices
- ❌ Create devices (admin only)
- ❌ Manage other users

### Admin (`role='admin'`)
**Can Access**:
- Everything regular users can
- `/admin` - Full admin panel

**Permissions**:
- ✅ All user permissions
- ✅ Create/edit/delete devices
- ✅ Assign devices to users
- ✅ View all users
- ✅ Grant/revoke admin role
- ✅ Manage any user's API keys
- ✅ View system-wide stats

---

## 🚀 Quick Start for Users

### New User Flow
```
1. Visit http://localhost:8000/
2. Click "Create one" → Register
3. Fill in username, email, password
4. Click "Create Account"
5. Login with credentials
6. Dashboard opens
7. Go to "API Keys" tab
8. Click "Generate New Key"
9. Copy key_id and key_secret
10. Use with ESP32 or API calls
```

### Existing User Flow
```
1. Visit http://localhost:8000/
2. Enter username/password
3. Click "Login"
4. Access dashboard, test tools, etc.
```

---

## 📱 Mobile Responsiveness

All pages are mobile-friendly:
- Responsive layouts
- Touch-friendly buttons
- Readable on small screens
- Dropdown menus work on mobile

---

## 🔒 Security Features

### Current
- ✅ Password hashing (bcrypt)
- ✅ Basic Authentication
- ✅ Role-based access control
- ✅ API key hashing
- ✅ Secrets shown only once
- ✅ User data isolation

### Coming Soon (Phase 2)
- 🔄 HMAC request signing
- 🔄 Timestamp validation
- 🔄 Replay attack prevention
- 🔄 API key expiration
- 🔄 Rate limiting

---

## 📝 API Endpoints

### Authentication
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### User Management
- `GET /api/users/{id}/api-keys` - List user's API keys
- `POST /api/users/{id}/api-keys` - Generate new API key
- `DELETE /api/api-keys/{key_id}` - Delete API key
- `GET /api/users/{id}/devices` - List user's devices

### Device Management (Admin)
- `GET /api/devices` - List all devices
- `POST /api/devices` - Create device
- `GET /api/devices/{id}` - Get device
- `PUT /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Delete device

### Weather Data (Public with device_id)
- `GET /api/device/{device_id}/esp` - ESP32 optimized
- `GET /api/device/{device_id}/data` - Full data with filtering
- `GET /api/device/{device_id}/weather` - Legacy endpoint

---

## 🎯 Next Steps

### Phase 2: HMAC Authentication
- Implement HMAC signature validation
- Update ESP32 code examples
- Add timestamp checking
- Prevent replay attacks

### Phase 3: Admin Enhancements
- Add Users tab to admin panel
- Add API Keys tab to admin panel
- User role management
- System statistics

### Phase 4: Advanced Features
- API key permissions/scoping
- Rate limiting per user
- Usage analytics
- Email notifications
- Password reset flow

---

## 🐛 Troubleshooting

### Can't Login
- Check username/password
- Ensure user exists (check database)
- Clear browser cache/localStorage

### API Key Not Working
- Ensure key is not deleted
- Check key belongs to user
- Verify device belongs to user

### Page Won't Load
- Check if logged in
- Clear localStorage and re-login
- Check browser console for errors

---

## 📞 Support

For issues:
1. Check browser console (F12)
2. Check server logs
3. Verify database state
4. Check authentication credentials

