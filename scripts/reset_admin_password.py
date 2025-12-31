#!/usr/bin/env python3
"""
Reset admin password for AgTools.
SECURITY: Generates a random secure password or prompts for one.
"""

import sys
import os
import sqlite3
import secrets
import string
import getpass

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.auth_service import get_auth_service


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def reset_admin_password():
    """Reset the admin password."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'agtools.db')

    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return

    # Prompt for password or generate random one
    print("=" * 50)
    print("  AgTools Admin Password Reset")
    print("=" * 50)
    print()
    print("Options:")
    print("  1. Enter a custom password")
    print("  2. Generate a secure random password")
    print()

    choice = input("Choose option (1 or 2): ").strip()

    if choice == "1":
        new_password = getpass.getpass("Enter new password: ")
        confirm = getpass.getpass("Confirm password: ")
        if new_password != confirm:
            print("Passwords do not match!")
            return
        if len(new_password) < 8:
            print("Password must be at least 8 characters!")
            return
    else:
        new_password = generate_secure_password()

    # Get auth service to hash password
    auth = get_auth_service()
    hashed = auth.hash_password(new_password)

    # Update password in database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'admin'", (hashed,))

    if cursor.rowcount > 0:
        conn.commit()
        print()
        print("=" * 50)
        print("  Password reset successfully!")
        print("=" * 50)
        print()
        print("  Username: admin")
        print(f"  Password: {new_password}")
        print()
        print("  IMPORTANT: Save this password securely!")
        print("=" * 50)
    else:
        print("Admin user not found in database.")

    conn.close()


if __name__ == "__main__":
    reset_admin_password()
