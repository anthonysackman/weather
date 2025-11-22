# API Key Secret Viewing Flow

## Problem
When an admin generates an API key for a user, only the admin sees the secret in a popup. The user never gets to see their own secret, making it impossible for them to use the API key.

## Solution
Implement a "view once" system where the secret is shown to the user in their dashboard until they acknowledge they've saved it.

## How It Works

### 1. **Secret Generation** (Admin)
- Admin generates API key for a user via admin panel
- Secret is hashed and stored in database
- **Unhashed secret is temporarily stored in memory** (`pending_secrets` dict)
- `secret_viewed` flag is set to `False` (0) in database
- Admin sees the secret in a popup (for their records)

### 2. **User Views Secret** (User Dashboard)
- User logs into their dashboard
- API keys with `secret_viewed = False` are highlighted with:
  - Yellow background
  - "NEW" badge
  - Warning message
  - The actual secret displayed
  - "Copy Secret" button
  - "I've Saved It" button

### 3. **User Acknowledges** (User Action)
- User clicks "I've Saved It" button
- Confirmation dialog appears
- On confirmation:
  - API endpoint `/api/api-keys/{key_id}/mark-viewed` is called
  - `secret_viewed` flag is set to `True` (1) in database
  - Secret is removed from memory (`pending_secrets`)
  - Dashboard reloads and secret is no longer visible

### 4. **Subsequent Views**
- Once `secret_viewed = True`, the secret is never shown again
- Only the `key_id` is displayed
- If lost, a new API key must be generated

## Database Schema

```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id TEXT UNIQUE NOT NULL,
    key_secret_hash TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    last_used TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    secret_viewed INTEGER DEFAULT 0,  -- NEW COLUMN
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

## API Endpoints

### Get User's API Keys
```
GET /api/users/{user_id}/api-keys
```

Response includes:
```json
{
  "success": true,
  "keys": [
    {
      "id": 1,
      "key_id": "key_abc123...",
      "name": "My ESP32",
      "secret_viewed": false,
      "pending_secret": "actual_secret_here",  // Only if not viewed
      "created_at": "2025-11-21T...",
      ...
    }
  ]
}
```

### Mark Secret as Viewed
```
POST /api/api-keys/{key_id}/mark-viewed
```

Response:
```json
{
  "success": true,
  "message": "Secret marked as viewed"
}
```

## Security Considerations

### ✅ Secure
- Secrets are hashed in database (like passwords)
- Secrets are only shown once to the user
- User must explicitly acknowledge they've saved it
- Memory storage is cleared after acknowledgment

### ⚠️ Considerations
- **Memory storage**: `pending_secrets` dict is in-memory
  - Lost on server restart
  - Not shared across multiple server instances
  - **For production**: Use Redis or similar shared cache

### 🔄 Production Improvements
```python
# Use Redis instead of in-memory dict
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Store secret with expiration (e.g., 24 hours)
redis_client.setex(f"pending_secret:{key_id}", 86400, key_secret)

# Retrieve secret
secret = redis_client.get(f"pending_secret:{key_id}")

# Delete after viewing
redis_client.delete(f"pending_secret:{key_id}")
```

## Migration

Run the migration script to add the `secret_viewed` column:

```bash
python migrate_add_secret_viewed.py
```

This will:
1. Create a backup of the database
2. Add `secret_viewed` column (defaults to 1 for existing keys)
3. Rollback on failure

## User Experience

### Admin Flow
1. Go to "Users" tab in admin panel
2. Click "Generate API Key" for a user
3. Enter key name
4. See popup with key_id and key_secret
5. User is notified to check their dashboard

### User Flow
1. Log into dashboard
2. See highlighted "NEW" API key
3. Read warning message
4. Copy secret to safe location
5. Click "I've Saved It"
6. Confirm in dialog
7. Secret disappears, never to be seen again

## Testing

1. Generate an API key for a user (as admin)
2. Log in as that user
3. Verify secret is shown with yellow highlight
4. Copy the secret
5. Click "I've Saved It" and confirm
6. Verify secret is no longer visible
7. Refresh page - secret should still be hidden

