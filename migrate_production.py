"""Production-safe database migration script with rollback support."""

import sqlite3
import os
import shutil
from datetime import datetime
import sys

DB_PATH = os.getenv("DB_PATH", "./weather_display.db")


def create_backup():
    """Create timestamped backup of database."""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{DB_PATH}.backup.{timestamp}"
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None


def verify_database():
    """Verify database is accessible and get current state."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if 'users' not in tables or 'devices' not in tables:
            print("❌ Required tables not found")
            conn.close()
            return False
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM devices")
        device_count = cursor.fetchone()[0]
        
        # Check if already migrated
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        conn.close()
        
        print(f"\n📊 Current Database State:")
        print(f"   Users: {user_count}")
        print(f"   Devices: {device_count}")
        print(f"   User columns: {', '.join(columns)}")
        
        if 'email' in columns and 'role' in columns:
            print("\n⚠️  Database appears to be already migrated!")
            response = input("Continue anyway? (yes/no): ")
            return response.lower() == 'yes'
        
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False


def run_migration():
    """Run the migration."""
    print("\n🔄 Running migration...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Backup existing data
        print("   📝 Reading existing data...")
        cursor.execute("SELECT id, username, password_hash, created_at FROM users")
        existing_users = cursor.fetchall()
        
        cursor.execute("SELECT * FROM devices")
        existing_devices = cursor.fetchall()
        
        # Drop old tables
        print("   🗑️  Dropping old tables...")
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS devices")
        cursor.execute("DROP INDEX IF EXISTS idx_device_id")
        
        # Create new schema
        print("   📊 Creating new schema...")
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
        print("   📇 Creating indexes...")
        cursor.execute("CREATE INDEX idx_device_id ON devices(device_id)")
        cursor.execute("CREATE INDEX idx_api_key_id ON api_keys(key_id)")
        cursor.execute("CREATE INDEX idx_user_id_devices ON devices(user_id)")
        cursor.execute("CREATE INDEX idx_user_id_api_keys ON api_keys(user_id)")
        
        # Restore users
        print("   👥 Migrating users...")
        now = datetime.utcnow().isoformat()
        for i, (user_id, username, password_hash, created_at) in enumerate(existing_users):
            role = 'admin' if i == 0 else 'user'
            email = f"{username}@example.com"
            cursor.execute(
                """
                INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, username, email, password_hash, role, created_at, now)
            )
            print(f"      ✓ {username} (role: {role})")
        
        # Restore devices
        if existing_devices and existing_users:
            print("   📱 Migrating devices...")
            first_user_id = existing_users[0][0]
            
            for device in existing_devices:
                cursor.execute(
                    """
                    INSERT INTO devices (
                        id, device_id, user_id, name, address, lat, lon, timezone,
                        display_settings, last_seen, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        device[0], device[1], first_user_id, device[2], device[3],
                        device[4], device[5], device[6], device[7], device[8],
                        device[9], device[10]
                    )
                )
            print(f"      ✓ {len(existing_devices)} devices migrated")
        
        # Commit transaction
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify migration
        cursor.execute("SELECT COUNT(*) FROM users")
        new_user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM devices")
        new_device_count = cursor.fetchone()[0]
        
        print(f"\n📊 Post-Migration State:")
        print(f"   Users: {new_user_count}")
        print(f"   Devices: {new_device_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("   Rolling back...")
        conn.rollback()
        conn.close()
        return False


def rollback(backup_path):
    """Rollback to backup."""
    if not backup_path or not os.path.exists(backup_path):
        print("❌ No backup available for rollback")
        return False
    
    try:
        shutil.copy2(backup_path, DB_PATH)
        print(f"✅ Rolled back to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False


def main():
    """Main migration flow."""
    print("=" * 60)
    print("🚀 Weather API - Production Database Migration")
    print("=" * 60)
    
    # Pre-flight checks
    print("\n1️⃣  Pre-flight Checks")
    if not verify_database():
        print("\n❌ Pre-flight checks failed. Aborting.")
        sys.exit(1)
    
    # Confirm migration
    print("\n⚠️  WARNING: This will modify your database!")
    print("   A backup will be created automatically.")
    response = input("\nProceed with migration? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Migration cancelled by user")
        sys.exit(0)
    
    # Create backup
    print("\n2️⃣  Creating Backup")
    backup_path = create_backup()
    if not backup_path:
        print("❌ Cannot proceed without backup. Aborting.")
        sys.exit(1)
    
    # Run migration
    print("\n3️⃣  Running Migration")
    success = run_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ MIGRATION SUCCESSFUL!")
        print("=" * 60)
        print(f"\n📁 Backup saved at: {backup_path}")
        print("\n📋 Next Steps:")
        print("   1. Test your application")
        print("   2. Generate API keys for users in admin panel")
        print("   3. Update ESP32 devices with new authentication")
        print(f"\n💡 To rollback: mv {backup_path} {DB_PATH}")
    else:
        print("\n" + "=" * 60)
        print("❌ MIGRATION FAILED!")
        print("=" * 60)
        print("\nAttempting automatic rollback...")
        if rollback(backup_path):
            print("✅ Database restored to pre-migration state")
        else:
            print(f"❌ Automatic rollback failed!")
            print(f"   Manual restore: mv {backup_path} {DB_PATH}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

