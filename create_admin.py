#!/usr/bin/env python3
"""CLI tool to create an admin user."""

import asyncio
import sys
from datetime import datetime
from app.database.db import db
from app.database.models import User
from app.auth.utils import hash_password


async def create_admin_user(username: str, password: str):
    """Create an admin user."""
    # Initialize database
    await db.init_db()

    # Check if user already exists
    existing_user = await db.get_user(username)
    if existing_user:
        print(f"❌ User '{username}' already exists!")
        return False

    # Create user
    user = User(
        username=username,
        password_hash=hash_password(password),
        created_at=datetime.utcnow().isoformat(),
    )

    created_user = await db.create_user(user)

    if created_user:
        print(f"✅ Admin user '{username}' created successfully!")
        print(f"\nYou can now login at: http://localhost:8000/admin")
        print(f"Username: {username}")
        print(f"Password: {password}")
        return True
    else:
        print(f"❌ Failed to create user '{username}'")
        return False


async def main():
    """Main function."""
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <username> <password>")
        print("\nExample:")
        print("  python create_admin.py admin mypassword123")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    if len(password) < 6:
        print("❌ Password must be at least 6 characters long")
        sys.exit(1)

    await create_admin_user(username, password)


if __name__ == "__main__":
    asyncio.run(main())

