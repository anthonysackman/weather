"""Database models for weather display devices and users."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Device:
    """Device configuration model."""

    device_id: str
    user_id: int  # Owner of this device
    name: str
    address: str
    lat: Optional[float]
    lon: Optional[float]
    timezone: Optional[str]
    display_settings: Optional[str]  # JSON string for flexibility
    last_seen: Optional[str]
    created_at: str
    updated_at: str
    id: Optional[int] = None


@dataclass
class User:
    """User account model."""

    username: str
    email: str
    password_hash: str
    role: str  # 'admin' or 'user'
    created_at: str
    updated_at: str
    id: Optional[int] = None


@dataclass
class APIKey:
    """API Key model for authentication."""

    key_id: str  # Public identifier (e.g., "key_abc123...")
    key_secret_hash: str  # Hashed secret (like password)
    user_id: int  # Owner of this key
    name: str  # User-friendly name (e.g., "My ESP32")
    last_used: Optional[str]
    created_at: str
    expires_at: Optional[str]  # Optional expiration
    id: Optional[int] = None

