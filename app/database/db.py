"""Database connection and operations."""

import aiosqlite
import os
import logging
from typing import Optional, List
from datetime import datetime
import json
from app.database.models import Device, User, APIKey

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "./weather_display.db")


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Initialize database with schema."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create users table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

            # Create API keys table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
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
            """
            )

            # Create devices table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
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
            """
            )

            # Create indexes for fast lookups
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_device_id ON devices(device_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_key_id ON api_keys(key_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_id_devices ON devices(user_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_id_api_keys ON api_keys(user_id)"
            )

            await db.commit()
            logger.info(f"Database initialized at {self.db_path}")

    # Device operations
    async def create_device(self, device: Device) -> Optional[Device]:
        """Create a new device."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    INSERT INTO devices (
                        device_id, user_id, name, address, lat, lon, timezone,
                        display_settings, last_seen, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        device.device_id,
                        device.user_id,
                        device.name,
                        device.address,
                        device.lat,
                        device.lon,
                        device.timezone,
                        device.display_settings,
                        device.last_seen,
                        device.created_at,
                        device.updated_at,
                    ),
                )
                await db.commit()
                device.id = cursor.lastrowid
                logger.info(f"Created device: {device.device_id}")
                return device
        except aiosqlite.IntegrityError:
            logger.error(f"Device {device.device_id} already exists")
            return None
        except Exception as e:
            logger.error(f"Failed to create device: {e}")
            return None

    async def get_device(self, device_id: str) -> Optional[Device]:
        """Get device by device_id."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM devices WHERE device_id = ?", (device_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return Device(
                            id=row["id"],
                            device_id=row["device_id"],
                            user_id=row["user_id"],
                            name=row["name"],
                            address=row["address"],
                            lat=row["lat"],
                            lon=row["lon"],
                            timezone=row["timezone"],
                            display_settings=row["display_settings"],
                            last_seen=row["last_seen"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
                    return None
        except Exception as e:
            logger.error(f"Failed to get device {device_id}: {e}")
            return None

    async def get_all_devices(self) -> List[Device]:
        """Get all devices."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM devices ORDER BY name") as cursor:
                    rows = await cursor.fetchall()
                    return [
                        Device(
                            id=row["id"],
                            device_id=row["device_id"],
                            user_id=row["user_id"],
                            name=row["name"],
                            address=row["address"],
                            lat=row["lat"],
                            lon=row["lon"],
                            timezone=row["timezone"],
                            display_settings=row["display_settings"],
                            last_seen=row["last_seen"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"Failed to get all devices: {e}")
            return []

    async def update_device(self, device_id: str, **kwargs) -> bool:
        """Update device fields."""
        try:
            # Build dynamic update query
            allowed_fields = [
                "name",
                "address",
                "lat",
                "lon",
                "timezone",
                "display_settings",
                "last_seen",
            ]
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not updates:
                return False

            # Always update the updated_at timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()

            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [device_id]

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    f"UPDATE devices SET {set_clause} WHERE device_id = ?", values
                )
                await db.commit()
                logger.info(f"Updated device {device_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update device {device_id}: {e}")
            return False

    async def delete_device(self, device_id: str) -> bool:
        """Delete a device."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
                await db.commit()
                logger.info(f"Deleted device {device_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete device {device_id}: {e}")
            return False

    async def update_device_heartbeat(self, device_id: str) -> bool:
        """Update device last_seen timestamp."""
        return await self.update_device(
            device_id, last_seen=datetime.utcnow().isoformat()
        )

    # User operations
    async def create_user(self, user: User) -> Optional[User]:
        """Create a new user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    INSERT INTO users (username, email, password_hash, role, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (user.username, user.email, user.password_hash, user.role, user.created_at, user.updated_at),
                )
                await db.commit()
                user.id = cursor.lastrowid
                logger.info(f"Created user: {user.username} (role: {user.role})")
                return user
        except aiosqlite.IntegrityError:
            logger.error(f"User {user.username} or email already exists")
            return None
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None

    async def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM users WHERE username = ?", (username,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return User(
                            id=row["id"],
                            username=row["username"],
                            email=row["email"],
                            password_hash=row["password_hash"],
                            role=row["role"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
                    return None
        except Exception as e:
            logger.error(f"Failed to get user {username}: {e}")
            return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM users WHERE id = ?", (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return User(
                            id=row["id"],
                            username=row["username"],
                            email=row["email"],
                            password_hash=row["password_hash"],
                            role=row["role"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
                    return None
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None

    async def get_all_users(self) -> List[User]:
        """Get all users."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM users ORDER BY username") as cursor:
                    rows = await cursor.fetchall()
                    return [
                        User(
                            id=row["id"],
                            username=row["username"],
                            email=row["email"],
                            password_hash=row["password_hash"],
                            role=row["role"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return []

    async def update_user_role(self, user_id: int, role: str) -> bool:
        """Update user role."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE users SET role = ?, updated_at = ? WHERE id = ?",
                    (role, datetime.utcnow().isoformat(), user_id),
                )
                await db.commit()
                logger.info(f"Updated user {user_id} role to {role}")
                return True
        except Exception as e:
            logger.error(f"Failed to update user role: {e}")
            return False

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user and all their devices/API keys (CASCADE)."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
                await db.commit()
                logger.info(f"Deleted user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False

    # API Key operations
    async def create_api_key(self, api_key: APIKey) -> Optional[APIKey]:
        """Create a new API key."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    INSERT INTO api_keys (
                        key_id, key_secret_hash, user_id, name, last_used, created_at, expires_at, secret_viewed, pending_secret
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        api_key.key_id,
                        api_key.key_secret_hash,
                        api_key.user_id,
                        api_key.name,
                        api_key.last_used,
                        api_key.created_at,
                        api_key.expires_at,
                        0,  # secret_viewed = False
                        api_key.pending_secret,  # Store unhashed secret temporarily
                    ),
                )
                await db.commit()
                api_key.id = cursor.lastrowid
                logger.info(f"Created API key: {api_key.key_id} for user {api_key.user_id}")
                return api_key
        except aiosqlite.IntegrityError:
            logger.error(f"API key {api_key.key_id} already exists")
            return None
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            return None

    async def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """Get API key by key_id."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM api_keys WHERE key_id = ?", (key_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return APIKey(
                            id=row["id"],
                            key_id=row["key_id"],
                            key_secret_hash=row["key_secret_hash"],
                            user_id=row["user_id"],
                            name=row["name"],
                            last_used=row["last_used"],
                            created_at=row["created_at"],
                            expires_at=row["expires_at"],
                            secret_viewed=bool(row["secret_viewed"]),
                            pending_secret=row["pending_secret"] if "pending_secret" in row.keys() else None,
                        )
                    return None
        except Exception as e:
            logger.error(f"Failed to get API key {key_id}: {e}")
            return None

    async def get_user_api_keys(self, user_id: int) -> List[APIKey]:
        """Get all API keys for a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [
                        APIKey(
                            id=row["id"],
                            key_id=row["key_id"],
                            key_secret_hash=row["key_secret_hash"],
                            user_id=row["user_id"],
                            name=row["name"],
                            last_used=row["last_used"],
                            created_at=row["created_at"],
                            expires_at=row["expires_at"],
                            secret_viewed=bool(row["secret_viewed"]),
                            pending_secret=row["pending_secret"] if "pending_secret" in row.keys() else None,
                        )
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"Failed to get API keys for user {user_id}: {e}")
            return []

    async def mark_api_key_viewed(self, key_id: str) -> bool:
        """Mark an API key secret as viewed and clear the pending secret."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE api_keys SET secret_viewed = 1, pending_secret = NULL WHERE key_id = ?",
                    (key_id,)
                )
                await db.commit()
                logger.info(f"Marked API key {key_id} as viewed and cleared pending secret")
                return True
        except Exception as e:
            logger.error(f"Failed to mark API key as viewed: {e}")
            return False

    async def regenerate_api_key_secret(self, key_id: str, new_secret_hash: str, new_secret: str) -> bool:
        """Regenerate the secret for an API key."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    UPDATE api_keys 
                    SET key_secret_hash = ?, secret_viewed = 0, pending_secret = ?
                    WHERE key_id = ?
                    """,
                    (new_secret_hash, new_secret, key_id)
                )
                await db.commit()
                logger.info(f"Regenerated secret for API key {key_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to regenerate API key secret: {e}")
            return False

    async def get_all_api_keys(self) -> List[APIKey]:
        """Get all API keys (admin only)."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM api_keys ORDER BY created_at DESC"
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [
                        APIKey(
                            id=row["id"],
                            key_id=row["key_id"],
                            key_secret_hash=row["key_secret_hash"],
                            user_id=row["user_id"],
                            name=row["name"],
                            last_used=row["last_used"],
                            created_at=row["created_at"],
                            expires_at=row["expires_at"],
                            secret_viewed=bool(row["secret_viewed"]),
                            pending_secret=row["pending_secret"] if "pending_secret" in row.keys() else None,
                        )
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"Failed to get all API keys: {e}")
            return []

    async def update_api_key_last_used(self, key_id: str) -> bool:
        """Update API key last_used timestamp."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE api_keys SET last_used = ? WHERE key_id = ?",
                    (datetime.utcnow().isoformat(), key_id),
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update API key last_used: {e}")
            return False

    async def delete_api_key(self, key_id: str) -> bool:
        """Delete an API key."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM api_keys WHERE key_id = ?", (key_id,))
                await db.commit()
                logger.info(f"Deleted API key {key_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete API key: {e}")
            return False

    async def get_user_devices(self, user_id: int) -> List[Device]:
        """Get all devices owned by a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM devices WHERE user_id = ? ORDER BY name", (user_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [
                        Device(
                            id=row["id"],
                            device_id=row["device_id"],
                            user_id=row["user_id"],
                            name=row["name"],
                            address=row["address"],
                            lat=row["lat"],
                            lon=row["lon"],
                            timezone=row["timezone"],
                            display_settings=row["display_settings"],
                            last_seen=row["last_seen"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"Failed to get devices for user {user_id}: {e}")
            return []


# Global database instance
db = Database()

