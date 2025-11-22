"""Automatic database migrations that run on startup."""

import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def run_migrations(db_path: str = "./weather_display.db"):
    """
    Run all pending migrations.
    Safe to run multiple times - only applies missing changes.
    """
    if not os.path.exists(db_path):
        logger.info("Database doesn't exist yet, will be created by init_db")
        return
    
    logger.info("Checking for pending migrations...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get current schema
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(api_keys)")
        api_key_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(devices)")
        device_columns = [col[1] for col in cursor.fetchall()]
        
        migrations_applied = []
        
        # Migration 1: Add email, role, updated_at to users
        if 'email' not in user_columns:
            logger.info("Migration 1: Adding email, role, updated_at to users table")
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT DEFAULT 'user@example.com'")
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at TEXT")
            
            # Update existing users
            now = datetime.utcnow().isoformat()
            cursor.execute("UPDATE users SET updated_at = ? WHERE updated_at IS NULL", (now,))
            cursor.execute("UPDATE users SET role = 'admin' WHERE id = 1")  # First user is admin
            
            migrations_applied.append("users_multi_tenant")
        
        # Migration 2: Create api_keys table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_keys'")
        if not cursor.fetchone():
            logger.info("Migration 2: Creating api_keys table")
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
                    secret_viewed INTEGER DEFAULT 0,
                    pending_secret TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX idx_api_key_id ON api_keys(key_id)")
            cursor.execute("CREATE INDEX idx_user_id_api_keys ON api_keys(user_id)")
            migrations_applied.append("api_keys_table")
        
        # Migration 3: Add user_id to devices
        if 'user_id' not in device_columns:
            logger.info("Migration 3: Adding user_id to devices table")
            cursor.execute("ALTER TABLE devices ADD COLUMN user_id INTEGER DEFAULT 1")
            cursor.execute("CREATE INDEX idx_user_id_devices ON devices(user_id)")
            migrations_applied.append("devices_user_id")
        
        # Migration 4: Add secret_viewed to api_keys (if table exists but column doesn't)
        if 'secret_viewed' not in api_key_columns and api_key_columns:
            logger.info("Migration 4: Adding secret_viewed to api_keys table")
            cursor.execute("ALTER TABLE api_keys ADD COLUMN secret_viewed INTEGER DEFAULT 1")
            migrations_applied.append("api_keys_secret_viewed")
        
        # Migration 5: Add pending_secret to api_keys (if table exists but column doesn't)
        if 'pending_secret' not in api_key_columns and api_key_columns:
            logger.info("Migration 5: Adding pending_secret to api_keys table")
            cursor.execute("ALTER TABLE api_keys ADD COLUMN pending_secret TEXT")
            migrations_applied.append("api_keys_pending_secret")
        
        # Commit all migrations
        conn.commit()
        
        if migrations_applied:
            logger.info(f"✅ Applied {len(migrations_applied)} migration(s): {', '.join(migrations_applied)}")
        else:
            logger.info("✅ Database schema is up to date")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # For manual testing
    logging.basicConfig(level=logging.INFO)
    run_migrations()
    print("Migrations completed!")

