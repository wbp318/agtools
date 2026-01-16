"""
Authentication Service for Farm Operations Manager
Handles JWT tokens, password hashing, and session management.

AgTools v2.5.0
"""

import os
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from enum import Enum

from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# CONFIGURATION
# ============================================================================

# Secret key for JWT - in production, use environment variable
SECRET_KEY = os.getenv("AGTOOLS_SECRET_KEY", "dev-secret-key-change-in-production-" + secrets.token_hex(16))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    CREW = "crew"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TokenData(BaseModel):
    """Data encoded in JWT token"""
    user_id: int
    username: str
    role: UserRole
    exp: datetime


class Token(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserCreate(BaseModel):
    """Create new user request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.CREW


class UserUpdate(BaseModel):
    """Update user request"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response (no password)"""
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


class PasswordChange(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str


# ============================================================================
# AUTH SERVICE CLASS
# ============================================================================

class AuthService:
    """
    Authentication service handling:
    - Password hashing and verification
    - JWT token creation and validation
    - Session management
    """

    def __init__(self, db_connection=None):
        """
        Initialize auth service.

        Args:
            db_connection: Database connection (sqlite3 or similar)
        """
        self.db = db_connection
        self._users_cache: Dict[int, dict] = {}  # Simple cache

    # ========================================================================
    # PASSWORD METHODS
    # ========================================================================

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        # Truncate to 72 bytes (bcrypt limit)
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        password_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        try:
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception:
            return False

    # ========================================================================
    # TOKEN METHODS
    # ========================================================================

    def create_access_token(
        self,
        user_id: int,
        username: str,
        role: UserRole,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User's database ID
            username: User's username
            role: User's role
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode = {
            "sub": str(user_id),
            "username": username,
            "role": role.value,
            "exp": expire,
            "type": "access"
        }

        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def create_refresh_token(self, user_id: int) -> str:
        """
        Create a refresh token.

        Args:
            user_id: User's database ID

        Returns:
            Encoded JWT refresh token string
        """
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh",
            "jti": secrets.token_hex(16)  # Unique token ID
        }

        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def create_tokens(
        self,
        user_id: int,
        username: str,
        role: UserRole
    ) -> Token:
        """
        Create both access and refresh tokens.

        Args:
            user_id: User's database ID
            username: User's username
            role: User's role

        Returns:
            Token object with both tokens
        """
        access_token = self.create_access_token(user_id, username, role)
        refresh_token = self.create_refresh_token(user_id)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    def validate_access_token(self, token: str) -> Optional[TokenData]:
        """
        Validate an access token and return user data.

        Args:
            token: JWT access token string

        Returns:
            TokenData if valid, None otherwise
        """
        payload = self.decode_token(token)

        if not payload:
            return None

        if payload.get("type") != "access":
            return None

        try:
            return TokenData(
                user_id=int(payload["sub"]),
                username=payload["username"],
                role=UserRole(payload["role"]),
                exp=datetime.fromtimestamp(payload["exp"])
            )
        except (KeyError, ValueError):
            return None

    def validate_refresh_token(self, token: str) -> Optional[int]:
        """
        Validate a refresh token and return user ID.

        Args:
            token: JWT refresh token string

        Returns:
            User ID if valid, None otherwise
        """
        payload = self.decode_token(token)

        if not payload:
            return None

        if payload.get("type") != "refresh":
            return None

        try:
            return int(payload["sub"])
        except (KeyError, ValueError):
            return None

    # ========================================================================
    # SESSION METHODS (Database-backed)
    # ========================================================================

    def hash_token_for_storage(self, token: str) -> str:
        """Hash a token for secure storage in database."""
        return hashlib.sha256(token.encode()).hexdigest()

    def store_session(
        self,
        user_id: int,
        access_token: str,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None
    ) -> Optional[int]:
        """
        Store a session in the database.

        Thread-safe: Pass connection explicitly via conn parameter.

        Args:
            user_id: User's database ID
            access_token: Access token to store
            refresh_token: Refresh token to store
            ip_address: Client IP address
            user_agent: Client user agent
            conn: Database connection (preferred - thread-safe)

        Returns:
            Session ID or None if failed
        """
        db_conn = conn if conn is not None else self.db
        if not db_conn:
            return None

        try:
            cursor = db_conn.cursor()

            access_hash = self.hash_token_for_storage(access_token)
            refresh_hash = self.hash_token_for_storage(refresh_token)

            expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            refresh_expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

            cursor.execute("""
                INSERT INTO sessions
                (user_id, token_hash, refresh_token_hash, expires_at, refresh_expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, access_hash, refresh_hash, expires_at, refresh_expires_at, ip_address, user_agent))

            # Only commit if we own the connection (self.db), not if passed externally
            if conn is None and self.db:
                self.db.commit()
            return cursor.lastrowid

        except Exception as e:
            print(f"Error storing session: {e}")
            return None

    def invalidate_session(
        self,
        token: str,
        conn: Optional[sqlite3.Connection] = None
    ) -> bool:
        """
        Invalidate a session (logout).

        Thread-safe: Pass connection explicitly via conn parameter.

        Args:
            token: Access token to invalidate
            conn: Database connection (preferred - thread-safe)

        Returns:
            True if invalidated, False otherwise
        """
        db_conn = conn if conn is not None else self.db
        if not db_conn:
            return False

        try:
            cursor = db_conn.cursor()
            token_hash = self.hash_token_for_storage(token)

            cursor.execute("""
                UPDATE sessions SET is_valid = 0 WHERE token_hash = ?
            """, (token_hash,))

            # Only commit if we own the connection (self.db), not if passed externally
            if conn is None and self.db:
                self.db.commit()
            return cursor.rowcount > 0

        except Exception as e:
            print(f"Error invalidating session: {e}")
            return False

    def invalidate_all_user_sessions(
        self,
        user_id: int,
        conn: Optional[sqlite3.Connection] = None
    ) -> int:
        """
        Invalidate all sessions for a user (e.g., password change).

        Thread-safe: Pass connection explicitly via conn parameter.

        Args:
            user_id: User's database ID
            conn: Database connection (preferred - thread-safe)

        Returns:
            Number of sessions invalidated
        """
        db_conn = conn if conn is not None else self.db
        if not db_conn:
            return 0

        try:
            cursor = db_conn.cursor()

            cursor.execute("""
                UPDATE sessions SET is_valid = 0 WHERE user_id = ? AND is_valid = 1
            """, (user_id,))

            # Only commit if we own the connection (self.db), not if passed externally
            if conn is None and self.db:
                self.db.commit()
            return cursor.rowcount

        except Exception as e:
            print(f"Error invalidating user sessions: {e}")
            return 0

    def is_session_valid(self, token: str) -> bool:
        """
        Check if a session is still valid in database.

        Args:
            token: Access token to check

        Returns:
            True if valid, False otherwise
        """
        if not self.db:
            # Without DB, just validate token signature
            return self.validate_access_token(token) is not None

        try:
            cursor = self.db.cursor()
            token_hash = self.hash_token_for_storage(token)

            cursor.execute("""
                SELECT is_valid, expires_at FROM sessions
                WHERE token_hash = ?
            """, (token_hash,))

            row = cursor.fetchone()

            if not row:
                return False

            is_valid, expires_at = row

            if not is_valid:
                return False

            # Check expiration
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)

            return datetime.utcnow() < expires_at

        except Exception as e:
            print(f"Error checking session: {e}")
            return False

    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from database.

        Returns:
            Number of sessions removed
        """
        if not self.db:
            return 0

        try:
            cursor = self.db.cursor()

            cursor.execute("""
                DELETE FROM sessions
                WHERE expires_at < ? OR is_valid = 0
            """, (datetime.utcnow(),))

            self.db.commit()
            return cursor.rowcount

        except Exception as e:
            print(f"Error cleaning sessions: {e}")
            return 0

    # ========================================================================
    # AUDIT LOG
    # ========================================================================

    # Critical actions that should trigger fallback logging on failure
    CRITICAL_AUDIT_ACTIONS = {
        "login", "logout", "change_password", "create_user", "delete_user",
        "deactivate_user", "update_user_role"
    }

    def log_action(
        self,
        user_id: Optional[int],
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None
    ) -> bool:
        """
        Log an action to the audit log.

        Thread-safe: Pass connection explicitly via conn parameter.

        For critical security actions, failures are logged to a fallback file
        to ensure audit trail is maintained even during database issues.

        Args:
            user_id: User performing the action
            action: Action type (login, logout, create_user, etc.)
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            details: JSON string with additional details
            ip_address: Client IP address
            conn: Database connection (preferred - thread-safe)

        Returns:
            True if logged successfully, False if failed (but operation continues)
        """
        import logging
        import json

        # Use provided connection (thread-safe) or fall back to self.db (deprecated)
        db_conn = conn if conn is not None else self.db

        audit_data = {
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat()
        }

        if not db_conn:
            # No database connection - log warning and use fallback for critical actions
            logging.warning(f"No database connection for audit log: {action}")
            if action in self.CRITICAL_AUDIT_ACTIONS:
                self._fallback_audit_log(audit_data)
            return False

        try:
            cursor = db_conn.cursor()

            cursor.execute("""
                INSERT INTO audit_log
                (user_id, action, entity_type, entity_id, details, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, action, entity_type, entity_id, details, ip_address))

            # Only commit if we own the connection (self.db), not if passed externally
            # External connections should be committed by the caller for transaction consistency
            if conn is None and self.db:
                self.db.commit()

            return True

        except Exception as e:
            # Log detailed error information
            logging.error(
                f"Failed to log audit action: action={action}, user_id={user_id}, "
                f"entity_type={entity_type}, entity_id={entity_id}, error={e}"
            )

            # For critical security actions, use fallback file-based logging
            if action in self.CRITICAL_AUDIT_ACTIONS:
                self._fallback_audit_log(audit_data)

            return False

    def _fallback_audit_log(self, audit_data: dict) -> None:
        """
        Write audit log entry to a fallback file when database logging fails.

        This ensures critical security events are never lost, even during
        database outages. The fallback file should be monitored and
        entries should be reconciled with the database when it recovers.

        Args:
            audit_data: Dictionary containing the audit log entry
        """
        import logging
        import json
        import os

        try:
            # Write to a fallback audit log file
            fallback_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "logs",
                "audit_fallback.jsonl"
            )

            # Ensure logs directory exists
            os.makedirs(os.path.dirname(fallback_path), exist_ok=True)

            # Append as JSON lines format for easy parsing
            with open(fallback_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(audit_data) + "\n")

            logging.info(f"Critical audit action written to fallback: {audit_data['action']}")

        except Exception as fallback_error:
            # Last resort: at least log to the standard logger
            logging.critical(
                f"CRITICAL: Failed to write fallback audit log! "
                f"Original data: {audit_data}, Error: {fallback_error}"
            )


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_auth_service: Optional[AuthService] = None


def get_auth_service(db_connection=None) -> AuthService:
    """Get or create the auth service singleton."""
    global _auth_service

    if _auth_service is None:
        _auth_service = AuthService(db_connection)
    elif db_connection is not None and _auth_service.db is None:
        _auth_service.db = db_connection

    return _auth_service


def set_auth_db(db_connection) -> None:
    """Set the database connection for the auth service."""
    service = get_auth_service()
    service.db = db_connection
