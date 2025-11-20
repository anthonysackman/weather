#!/usr/bin/env python3
"""Test script to directly update timezone in database."""

import asyncio
import sys
from app.database.db import db

async def test_update():
    """Test updating timezone."""
    await db.init_db()
    
    # Get all devices
    devices = await db.get_all_devices()
    print(f"Found {len(devices)} devices:")
    for d in devices:
        print(f"  - {d.name}: {d.timezone}")
    
    if not devices:
        print("No devices to test with!")
        return
    
    # Update first device
    device = devices[0]
    print(f"\nUpdating {device.name} timezone to Europe/Paris...")
    
    success = await db.update_device(
        device.device_id,
        timezone="Europe/Paris"
    )
    
    print(f"Update success: {success}")
    
    # Read it back
    updated = await db.get_device(device.device_id)
    print(f"New timezone: {updated.timezone}")

if __name__ == "__main__":
    asyncio.run(test_update())

