"""Database models for weather display devices and users."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Device:
    """Device configuration model."""

    device_id: str
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
    """Admin user model."""

    username: str
    password_hash: str
    created_at: str
    id: Optional[int] = None

