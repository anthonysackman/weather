"""Migration script to add secret_viewed column to api_keys table."""

import sqlite3
import os
from datetime import datetime

DB_PATH = "./weather_display.db"


def migrate():
    """Add secret_viewed column to api_keys table."""
    
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    # Backup first
    backup_path = f"./weather_display_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f"✓ Created backup at {backup_path}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(api_keys)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'secret_viewed' not in columns:
            print("Adding 'secret_viewed' column...")
            cursor.execute("""
                ALTER TABLE api_keys 
                ADD COLUMN secret_viewed INTEGER DEFAULT 1
            """)
            print("✓ Added 'secret_viewed' column (defaulting to 1 for existing keys)")
        else:
            print("✓ Column 'secret_viewed' already exists")
        
        if 'pending_secret' not in columns:
            print("Adding 'pending_secret' column...")
            cursor.execute("""
                ALTER TABLE api_keys 
                ADD COLUMN pending_secret TEXT
            """)
            print("✓ Added 'pending_secret' column")
        else:
            print("✓ Column 'pending_secret' already exists")
        
        conn.commit()
        print("✓ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        print(f"Database restored from backup: {backup_path}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Add secret_viewed to api_keys")
    print("=" * 60)
    
    response = input("Continue with migration? (yes/no): ")
    if response.lower() == 'yes':
        migrate()
    else:
        print("Migration cancelled")

