"""Database migration script to add user roles, API keys, and device ownership."""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "./weather_display.db")


def migrate():
    """Run database migrations."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Starting database migration...")
    
    # Check if migration is needed
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'email' in columns and 'role' in columns:
        print("✅ Database already migrated!")
        conn.close()
        return
    
    print("📝 Backing up existing data...")
    
    # Backup existing users
    cursor.execute("SELECT id, username, password_hash, created_at FROM users")
    existing_users = cursor.fetchall()
    
    # Backup existing devices
    cursor.execute("SELECT * FROM devices")
    existing_devices = cursor.fetchall()
    
    print(f"   Found {len(existing_users)} users and {len(existing_devices)} devices")
    
    # Drop old tables
    print("🗑️  Dropping old tables...")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS devices")
    cursor.execute("DROP INDEX IF EXISTS idx_device_id")
    
    # Create new users table with role and email
    print("📊 Creating new users table...")
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Create API keys table
    print("🔑 Creating API keys table...")
    cursor.execute("""
        CREATE TABLE api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_id TEXT UNIQUE NOT NULL,
            key_secret_hash TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            last_used TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Create new devices table with user_id
    print("📱 Creating new devices table...")
    cursor.execute("""
        CREATE TABLE devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            lat REAL,
            lon REAL,
            timezone TEXT,
            display_settings TEXT,
            last_seen TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes
    print("📇 Creating indexes...")
    cursor.execute("CREATE INDEX idx_device_id ON devices(device_id)")
    cursor.execute("CREATE INDEX idx_api_key_id ON api_keys(key_id)")
    cursor.execute("CREATE INDEX idx_user_id_devices ON devices(user_id)")
    cursor.execute("CREATE INDEX idx_user_id_api_keys ON api_keys(user_id)")
    
    # Restore users (make first user admin, others regular users)
    print("👥 Restoring users...")
    now = datetime.utcnow().isoformat()
    for i, (user_id, username, password_hash, created_at) in enumerate(existing_users):
        role = 'admin' if i == 0 else 'user'  # First user becomes admin
        email = f"{username}@example.com"  # Generate placeholder email
        cursor.execute(
            """
            INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, email, password_hash, role, created_at, now)
        )
        print(f"   ✓ Restored user: {username} (role: {role})")
    
    # Restore devices (assign all to first user for now)
    if existing_devices and existing_users:
        print("📱 Restoring devices...")
        first_user_id = existing_users[0][0]
        
        for device in existing_devices:
            # device tuple: (id, device_id, name, address, lat, lon, timezone, display_settings, last_seen, created_at, updated_at)
            cursor.execute(
                """
                INSERT INTO devices (
                    id, device_id, user_id, name, address, lat, lon, timezone,
                    display_settings, last_seen, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    device[0],  # id
                    device[1],  # device_id
                    first_user_id,  # user_id (assign to first user)
                    device[2],  # name
                    device[3],  # address
                    device[4],  # lat
                    device[5],  # lon
                    device[6],  # timezone
                    device[7],  # display_settings
                    device[8],  # last_seen
                    device[9],  # created_at
                    device[10], # updated_at
                )
            )
        print(f"   ✓ Restored {len(existing_devices)} devices (assigned to first admin)")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Migration completed successfully!")
    print("\n📋 Summary:")
    print(f"   - Users migrated: {len(existing_users)}")
    print(f"   - Devices migrated: {len(existing_devices)}")
    print(f"   - First user is now admin")
    print(f"   - All devices assigned to first admin user")
    print("\n⚠️  Note: All users now have placeholder emails (username@example.com)")
    print("   Users should update their emails after logging in.")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

