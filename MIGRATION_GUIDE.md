# Database Migration Guide

## What Changed

We've upgraded the authentication system to support:
- ✅ User roles (admin/user)
- ✅ API key authentication with HMAC signatures
- ✅ Device ownership (devices belong to users)
- ✅ Multi-tenant support

## Migration Steps

### 1. Backup Your Data (Optional but Recommended)
```bash
cp weather_display.db weather_display.db.backup
```

### 2. Run the Migration Script
```bash
python migrate_database.py
```

This will:
- Add `email` and `role` fields to users table
- Create `api_keys` table
- Add `user_id` to devices table
- Assign all existing devices to the first admin user
- Make the first user an admin

### 3. Verify Migration
```bash
python -c "import sqlite3; conn = sqlite3.connect('weather_display.db'); cursor = conn.cursor(); cursor.execute('SELECT username, role FROM users'); print(cursor.fetchall())"
```

## What Happens to Existing Data

- **Users**: First user becomes admin, others become regular users
- **Devices**: All devices assigned to first admin user
- **Emails**: Placeholder emails generated (`username@example.com`)

## After Migration

### Create New Admin User (Optional)
```bash
python create_admin.py newadmin password123
```

### Start the Server
```bash
set DEBUG=true && set PYTHONPATH=%CD% && python app/main.py
```

## Fresh Install (No Migration Needed)

If you're starting fresh:
1. Delete `weather_display.db` (if it exists)
2. Run `python create_admin.py admin password123`
3. Start the server

The new schema will be created automatically!

## Rollback (If Needed)

If something goes wrong:
```bash
# Restore backup
cp weather_display.db.backup weather_display.db
```

## Next Steps

After migration, you can:
1. Generate API keys for users in the admin panel
2. Create new devices with proper ownership
3. Use HMAC authentication for device requests

## Schema Changes

### Users Table
```sql
-- Old
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    created_at TEXT
);

-- New
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT,
    role TEXT DEFAULT 'user',  -- NEW
    created_at TEXT,
    updated_at TEXT  -- NEW
);
```

### Devices Table
```sql
-- Old
CREATE TABLE devices (
    id INTEGER PRIMARY KEY,
    device_id TEXT UNIQUE,
    name TEXT,
    address TEXT,
    ...
);

-- New
CREATE TABLE devices (
    id INTEGER PRIMARY KEY,
    device_id TEXT UNIQUE,
    user_id INTEGER,  -- NEW (foreign key)
    name TEXT,
    address TEXT,
    ...
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### API Keys Table (NEW)
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    key_id TEXT UNIQUE,
    key_secret_hash TEXT,
    user_id INTEGER,
    name TEXT,
    last_used TEXT,
    created_at TEXT,
    expires_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

