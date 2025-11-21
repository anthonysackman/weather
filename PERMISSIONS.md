# Weather Display API - Permissions Model

## 🔐 Permission Structure

### Regular Users (`role='user'`)

#### ✅ CAN DO:
- **Account Management**:
  - Register new account
  - Login/logout
  - View own profile
  
- **API Keys** (Read-Only):
  - ✅ View their own API keys
  - ✅ See key details (key_id, name, created_at, last_used)
  - ❌ Cannot generate new keys
  - ❌ Cannot delete/revoke keys
  - 📝 Must contact admin for key management

- **Devices** (Full Control):
  - ✅ Create new devices
  - ✅ View their own devices
  - ✅ Delete their own devices
  - ✅ See device status (last seen)
  - ❌ Cannot view other users' devices
  - ❌ Cannot delete other users' devices

- **API Access**:
  - ✅ Use API test interface (`/test`)
  - ✅ View API documentation (`/docs`)
  - ✅ Access dashboard (`/dashboard`)

#### ❌ CANNOT DO:
- Generate API keys
- Revoke API keys
- View other users' data
- Access admin panel
- Manage users
- Grant/revoke admin role

---

### Administrators (`role='admin'`)

#### ✅ CAN DO:
- **Everything Users Can Do** PLUS:

- **API Key Management**:
  - ✅ Generate API keys for any user
  - ✅ Revoke API keys for any user
  - ✅ View all API keys system-wide
  - ✅ See key usage statistics

- **User Management**:
  - ✅ View all users
  - ✅ Grant admin role to users
  - ✅ Revoke admin role from users
  - ✅ Delete users
  - ✅ View user statistics

- **Device Management**:
  - ✅ View all devices (all users)
  - ✅ Create devices for any user
  - ✅ Edit any device
  - ✅ Delete any device
  - ✅ Assign device ownership

- **System Access**:
  - ✅ Access admin panel (`/admin`)
  - ✅ View system-wide statistics
  - ✅ Manage all resources

---

## 📊 Permission Matrix

| Action | User | Admin |
|--------|------|-------|
| **Account** |
| Register account | ✅ | ✅ |
| Login/logout | ✅ | ✅ |
| View own profile | ✅ | ✅ |
| **API Keys** |
| View own keys | ✅ | ✅ |
| Generate own key | ❌ | ✅ |
| Revoke own key | ❌ | ✅ |
| View all keys | ❌ | ✅ |
| Generate key for others | ❌ | ✅ |
| Revoke any key | ❌ | ✅ |
| **Devices** |
| Create device | ✅ | ✅ |
| View own devices | ✅ | ✅ |
| Delete own device | ✅ | ✅ |
| View all devices | ❌ | ✅ |
| Delete any device | ❌ | ✅ |
| Assign device owner | ❌ | ✅ |
| **Users** |
| View all users | ❌ | ✅ |
| Grant admin role | ❌ | ✅ |
| Revoke admin role | ❌ | ✅ |
| Delete users | ❌ | ✅ |
| **Pages** |
| `/dashboard` | ✅ | ✅ |
| `/test` | ✅ | ✅ |
| `/docs` | ✅ (public) | ✅ |
| `/admin` | ❌ | ✅ |

---

## 🔑 API Key Workflow

### For Users:
```
1. User creates account
2. User creates devices
3. User contacts admin: "I need an API key"
4. Admin generates key in admin panel
5. Admin shares key_id + key_secret with user
6. User uses key with their devices
7. If compromised: User contacts admin to revoke
```

### For Admins:
```
1. Admin logs into /admin
2. Goes to Users tab
3. Selects user
4. Clicks "Generate API Key"
5. Enters key name (e.g., "John's ESP32")
6. System generates key_id + key_secret
7. Admin copies and shares with user
8. Key is stored (hashed) in database
```

---

## 🚀 Device Creation Workflow

### Users Can Create Their Own Devices:
```
1. User logs into /dashboard
2. Goes to "My Devices" tab
3. Clicks "Add Device"
4. Enters:
   - Device name (e.g., "Living Room Display")
   - Address (e.g., "123 Main St, Miami, FL")
   - Timezone (e.g., "America/New_York")
5. System:
   - Generates unique device_id
   - Geocodes address to lat/lon
   - Assigns device to user
6. Device ready to use!
```

### Device Ownership:
- Devices belong to the user who created them
- Users can only see/delete their own devices
- Admins can see/manage all devices
- Device ownership can be transferred (admin only)

---

## 🔒 Security Considerations

### Why Users Can't Generate Keys:
1. **Centralized Control**: Admins can track and audit all keys
2. **Security**: Prevents key proliferation
3. **Accountability**: Admin knows who has keys
4. **Revocation**: Admin can quickly revoke compromised keys
5. **Rate Limiting**: Future feature - limit keys per user

### Why Users CAN Create Devices:
1. **Self-Service**: Users don't need admin for every device
2. **Scalability**: Reduces admin workload
3. **Ownership**: Users manage their own devices
4. **Future**: Rate limiting will prevent abuse

---

## 📝 API Endpoint Permissions

### Public (No Auth):
```
GET  /                    - Login page
GET  /register            - Registration page
GET  /docs                - API documentation
POST /api/auth/register   - Create account
POST /api/auth/login      - Login
```

### Authenticated (User + Admin):
```
GET  /dashboard                      - User dashboard
GET  /test                           - API test interface
GET  /api/auth/me                    - Get current user
GET  /api/users/{id}/api-keys        - View own keys (users) or any keys (admin)
GET  /api/users/{id}/devices         - View own devices (users) or any devices (admin)
POST /api/devices                    - Create device (assigned to self)
DELETE /api/devices/{id}             - Delete own device (users) or any device (admin)
```

### Admin Only:
```
GET  /admin                          - Admin panel
GET  /api/devices                    - List all devices
POST /api/users/{id}/api-keys        - Generate API key for user
DELETE /api/api-keys/{key_id}        - Revoke API key
GET  /api/users                      - List all users (coming soon)
PUT  /api/users/{id}/role            - Change user role (coming soon)
```

### Device Endpoints (No Auth - device_id is auth):
```
GET  /api/device/{device_id}/esp     - ESP32 optimized data
GET  /api/device/{device_id}/data    - Full data with filtering
GET  /api/device/{device_id}/weather - Legacy endpoint
```

---

## 🎯 Future Enhancements

### Rate Limiting (Coming Soon):
```javascript
{
  "user_limits": {
    "devices_per_user": 10,
    "api_keys_per_user": 3,
    "requests_per_hour": 1000
  }
}
```

### API Key Scopes (Coming Soon):
```javascript
{
  "key_permissions": [
    "read:weather",      // Can fetch weather
    "read:devices",      // Can list devices
    "write:devices"      // Can create/update devices
  ]
}
```

### Device Transfer (Coming Soon):
```
Admin can transfer device ownership:
1. Admin goes to device
2. Clicks "Transfer Ownership"
3. Selects new owner
4. Device now belongs to new user
```

---

## 🐛 Common Issues

### "I can't generate an API key"
- **Solution**: Contact your administrator. Only admins can generate keys.

### "I can't see my API key secret"
- **Solution**: Secrets are shown only once when generated. Contact admin to generate a new key.

### "I can't delete someone else's device"
- **Solution**: You can only delete your own devices. Admins can delete any device.

### "My device isn't showing up"
- **Solution**: Check that you're logged in as the user who created it. Devices are user-specific.

---

## 📞 Support

### For Users:
- Can't generate key? → Contact admin
- Lost key secret? → Contact admin for new key
- Need help? → Check `/docs` or contact admin

### For Admins:
- User needs key? → Generate in admin panel
- Key compromised? → Revoke and generate new one
- User has too many devices? → Implement rate limiting (coming soon)

