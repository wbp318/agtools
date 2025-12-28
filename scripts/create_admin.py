#!/usr/bin/env python3
"""
Create default admin user for AgTools.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.user_service import get_user_service
from services.auth_service import UserCreate, UserRole

def create_admin():
    """Create the admin user."""
    user_service = get_user_service()

    # Create admin user
    admin_data = UserCreate(
        username="admin",
        email="admin@example.com",
        password="agtools123",  # Default password
        first_name="Farm",
        last_name="Admin",
        role=UserRole.ADMIN
    )

    user, error = user_service.create_user(admin_data)

    if error:
        if "already exists" in error.lower():
            print("=" * 50)
            print("  Admin user already exists!")
            print("=" * 50)
            print()
            print("  Username: admin")
            print("  (Use your existing password)")
            print("=" * 50)
        else:
            print(f"Error creating admin: {error}")
        return

    print("=" * 50)
    print("  Admin user created successfully!")
    print("=" * 50)
    print()
    print("  Username: admin")
    print("  Password: agtools123")
    print()
    print("  Please change your password after first login!")
    print("=" * 50)


if __name__ == "__main__":
    create_admin()
