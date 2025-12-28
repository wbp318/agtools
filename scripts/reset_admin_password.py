#!/usr/bin/env python3
"""
Reset admin password for AgTools.
"""

import sys
import os
import sqlite3

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.auth_service import get_auth_service

def reset_admin_password():
    """Reset the admin password."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'agtools.db')

    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return

    # Get auth service to hash password
    auth = get_auth_service()
    new_password = "agtools123"
    hashed = auth.hash_password(new_password)

    # Update password in database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'admin'", (hashed,))

    if cursor.rowcount > 0:
        conn.commit()
        print("=" * 50)
        print("  Password reset successfully!")
        print("=" * 50)
        print()
        print("  Username: admin")
        print("  Password: agtools123")
        print()
        print("=" * 50)
    else:
        print("Admin user not found in database.")

    conn.close()


if __name__ == "__main__":
    reset_admin_password()
