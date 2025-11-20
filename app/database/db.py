"""Database connection and operations."""

import aiosqlite
import os
import logging
from typing import Optional, List
from datetime import datetime
import json
from app.database.models import Device, User

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "./weather_display.db")


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Initialize database with schema."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create devices table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    lat REAL,
                    lon REAL,
                    timezone TEXT,
                    display_settings TEXT,
                    last_seen TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

            # Create users table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """
            )

            # Create index on device_id for fast lookups
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_device_id 
                ON devices(device_id)
            """
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
                        device_id, name, address, lat, lon, timezone,
                        display_settings, last_seen, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        device.device_id,
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
                    INSERT INTO users (username, password_hash, created_at)
                    VALUES (?, ?, ?)
                """,
                    (user.username, user.password_hash, user.created_at),
                )
                await db.commit()
                user.id = cursor.lastrowid
                logger.info(f"Created user: {user.username}")
                return user
        except aiosqlite.IntegrityError:
            logger.error(f"User {user.username} already exists")
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
                            password_hash=row["password_hash"],
                            created_at=row["created_at"],
                        )
                    return None
        except Exception as e:
            logger.error(f"Failed to get user {username}: {e}")
            return None


# Global database instance
db = Database()

