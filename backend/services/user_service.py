"""
User Service for Farm Operations Manager
Handles user CRUD operations, crews, and team management.

AgTools v2.5.0
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from pydantic import BaseModel, EmailStr, Field

from .auth_service import (
    AuthService,
    UserRole,
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
    get_auth_service
)
from .base_service import sanitize_error


# ============================================================================
# ADDITIONAL PYDANTIC MODELS
# ============================================================================

class CrewCreate(BaseModel):
    """Create crew request"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    manager_id: Optional[int] = None


class CrewUpdate(BaseModel):
    """Update crew request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None


class CrewResponse(BaseModel):
    """Crew response"""
    id: int
    name: str
    description: Optional[str]
    manager_id: Optional[int]
    manager_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    member_count: int = 0


class CrewMemberResponse(BaseModel):
    """Crew member info"""
    user_id: int
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: UserRole
    joined_at: datetime


class UserWithCrews(UserResponse):
    """User response with crew memberships"""
    crews: List[Dict[str, Any]] = []


# ============================================================================
# USER SERVICE CLASS
# ============================================================================

class UserService:
    """
    User service handling:
    - User CRUD operations
    - Crew/team management
    - User-crew associations
    """

    def __init__(self, db_path: str = "agtools.db"):
        """
        Initialize user service.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.auth_service = get_auth_service()
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        """Initialize database tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                phone VARCHAR(20),
                role VARCHAR(20) NOT NULL DEFAULT 'crew',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash VARCHAR(255) NOT NULL,
                refresh_token_hash VARCHAR(255),
                expires_at TIMESTAMP NOT NULL,
                refresh_expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                user_agent TEXT,
                is_valid BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Create crews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                manager_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manager_id) REFERENCES users(id)
            )
        """)

        # Create crew_members table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crew_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crew_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(crew_id, user_id),
                FOREIGN KEY (crew_id) REFERENCES crews(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Create audit_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50),
                entity_id INTEGER,
                details TEXT,
                ip_address VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crew_members_user_id ON crew_members(user_id)")

        conn.commit()
        conn.close()

        # Check if admin exists, create default if not
        self._ensure_admin_exists()

    def _ensure_admin_exists(self) -> None:
        """Create default admin user if no admin exists."""
        import secrets
        import string

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        count = cursor.fetchone()[0]

        if count == 0:
            # SECURITY: Generate a random secure password for default admin
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            random_password = ''.join(secrets.choice(alphabet) for _ in range(16))
            password_hash = self.auth_service.hash_password(random_password)

            cursor.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name, role)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("admin", "admin@farm.local", password_hash, "Farm", "Admin", "admin"))
            conn.commit()

            # SECURITY: Write credentials to secure file instead of console
            # User must check this file and delete it after reading
            import logging
            logging.warning("DEFAULT ADMIN ACCOUNT CREATED - Check admin_credentials.txt")
            credentials_file = os.path.join(os.path.dirname(self.db_path), "admin_credentials.txt")
            with open(credentials_file, "w") as f:
                f.write("=" * 60 + "\n")
                f.write("  DEFAULT ADMIN ACCOUNT CREATED\n")
                f.write("=" * 60 + "\n")
                f.write("  Username: admin\n")
                f.write(f"  Password: {random_password}\n")
                f.write("\n")
                f.write("  IMPORTANT: Delete this file after saving the password!\n")
                f.write("  Use scripts/reset_admin_password.py to reset if lost.\n")
                f.write("=" * 60 + "\n")

        conn.close()

    # ========================================================================
    # AUTHENTICATION METHODS
    # ========================================================================

    def authenticate(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[Optional[Token], Optional[UserResponse], Optional[str]]:
        """
        Authenticate a user and return tokens.

        Args:
            username: Username or email
            password: Plain text password
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            Tuple of (Token, UserResponse, error_message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Find user by username or email
        cursor.execute("""
            SELECT id, username, email, password_hash, first_name, last_name,
                   phone, role, is_active, created_at, last_login
            FROM users
            WHERE (username = ? OR email = ?)
        """, (username, username))

        row = cursor.fetchone()

        if not row:
            conn.close()
            return None, None, "Invalid username or password"

        user_dict = dict(row)

        if not user_dict["is_active"]:
            conn.close()
            return None, None, "Account is disabled"

        if not self.auth_service.verify_password(password, user_dict["password_hash"]):
            conn.close()
            return None, None, "Invalid username or password"

        # Update last login
        cursor.execute("""
            UPDATE users SET last_login = ? WHERE id = ?
        """, (datetime.utcnow(), user_dict["id"]))

        conn.commit()

        # Create tokens
        tokens = self.auth_service.create_tokens(
            user_id=user_dict["id"],
            username=user_dict["username"],
            role=UserRole(user_dict["role"])
        )

        # Store session (thread-safe - pass connection explicitly)
        self.auth_service.store_session(
            user_id=user_dict["id"],
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            conn=conn
        )

        # Log action (thread-safe - pass connection explicitly)
        self.auth_service.log_action(
            user_id=user_dict["id"],
            action="login",
            ip_address=ip_address,
            conn=conn
        )

        conn.close()

        # Build user response
        user_response = UserResponse(
            id=user_dict["id"],
            username=user_dict["username"],
            email=user_dict["email"],
            first_name=user_dict["first_name"],
            last_name=user_dict["last_name"],
            phone=user_dict["phone"],
            role=UserRole(user_dict["role"]),
            is_active=user_dict["is_active"],
            created_at=user_dict["created_at"],
            last_login=datetime.utcnow()
        )

        return tokens, user_response, None

    def logout(self, token: str, user_id: int, ip_address: Optional[str] = None) -> bool:
        """
        Logout a user by invalidating their session.

        Args:
            token: Access token to invalidate
            user_id: User's ID for audit log
            ip_address: Client IP

        Returns:
            True if successful
        """
        conn = self._get_connection()

        result = self.auth_service.invalidate_session(token, conn=conn)

        # Log action (thread-safe - pass connection explicitly)
        self.auth_service.log_action(
            user_id=user_id,
            action="logout",
            ip_address=ip_address,
            conn=conn
        )

        conn.close()
        return result

    def refresh_tokens(self, refresh_token: str) -> Tuple[Optional[Token], Optional[str]]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (new Token, error_message)
        """
        user_id = self.auth_service.validate_refresh_token(refresh_token)

        if not user_id:
            return None, "Invalid or expired refresh token"

        # Get user info
        user = self.get_user_by_id(user_id)
        if not user:
            return None, "User not found"

        if not user.is_active:
            return None, "Account is disabled"

        # Create new tokens
        tokens = self.auth_service.create_tokens(
            user_id=user.id,
            username=user.username,
            role=user.role
        )

        return tokens, None

    # ========================================================================
    # USER CRUD METHODS
    # ========================================================================

    def create_user(self, user_data: UserCreate, created_by: Optional[int] = None) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Create a new user.

        Args:
            user_data: User creation data
            created_by: ID of user creating this user

        Returns:
            Tuple of (UserResponse, error_message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check for existing username
        cursor.execute("SELECT id FROM users WHERE username = ?", (user_data.username,))
        if cursor.fetchone():
            conn.close()
            return None, "Username already exists"

        # Check for existing email
        cursor.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
        if cursor.fetchone():
            conn.close()
            return None, "Email already exists"

        # Hash password
        password_hash = self.auth_service.hash_password(user_data.password)

        # Insert user
        try:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name, phone, role)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data.username,
                user_data.email,
                password_hash,
                user_data.first_name,
                user_data.last_name,
                user_data.phone,
                user_data.role.value
            ))

            user_id = cursor.lastrowid

            # Log action (thread-safe - pass connection explicitly)
            self.auth_service.log_action(
                user_id=created_by,
                action="create_user",
                entity_type="user",
                entity_id=user_id,
                conn=conn
            )

            conn.commit()
            conn.close()

            return self.get_user_by_id(user_id), None

        except Exception as e:
            conn.close()
            return None, sanitize_error(e, "user creation")

    def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """Get user by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, email, first_name, last_name, phone, role,
                   is_active, created_at, last_login
            FROM users
            WHERE id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return UserResponse(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            phone=row["phone"],
            role=UserRole(row["role"]),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            last_login=row["last_login"]
        )

    def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """Get user by username."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, email, first_name, last_name, phone, role,
                   is_active, created_at, last_login
            FROM users
            WHERE username = ?
        """, (username,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return UserResponse(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            phone=row["phone"],
            role=UserRole(row["role"]),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            last_login=row["last_login"]
        )

    def list_users(
        self,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        crew_id: Optional[int] = None
    ) -> List[UserResponse]:
        """
        List users with optional filters.

        Args:
            role: Filter by role
            is_active: Filter by active status
            crew_id: Filter by crew membership

        Returns:
            List of UserResponse
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT DISTINCT u.id, u.username, u.email, u.first_name, u.last_name,
                   u.phone, u.role, u.is_active, u.created_at, u.last_login
            FROM users u
        """
        params = []
        conditions = []

        if crew_id:
            query += " JOIN crew_members cm ON u.id = cm.user_id"
            conditions.append("cm.crew_id = ?")
            params.append(crew_id)

        if role:
            conditions.append("u.role = ?")
            params.append(role.value)

        if is_active is not None:
            conditions.append("u.is_active = ?")
            params.append(1 if is_active else 0)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY u.username"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            UserResponse(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                phone=row["phone"],
                role=UserRole(row["role"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                last_login=row["last_login"]
            )
            for row in rows
        ]

    def update_user(
        self,
        user_id: int,
        user_data: UserUpdate,
        updated_by: Optional[int] = None
    ) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Update a user.

        Args:
            user_id: User ID to update
            user_data: Update data
            updated_by: ID of user performing update

        Returns:
            Tuple of (UserResponse, error_message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        updates = []
        params = []

        if user_data.email is not None:
            # Check for duplicate email
            cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (user_data.email, user_id))
            if cursor.fetchone():
                conn.close()
                return None, "Email already exists"
            updates.append("email = ?")
            params.append(user_data.email)

        if user_data.first_name is not None:
            updates.append("first_name = ?")
            params.append(user_data.first_name)

        if user_data.last_name is not None:
            updates.append("last_name = ?")
            params.append(user_data.last_name)

        if user_data.phone is not None:
            updates.append("phone = ?")
            params.append(user_data.phone)

        if user_data.role is not None:
            updates.append("role = ?")
            params.append(user_data.role.value)

        if user_data.is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if user_data.is_active else 0)

        if not updates:
            conn.close()
            return self.get_user_by_id(user_id), None

        updates.append("updated_at = ?")
        params.append(datetime.utcnow())
        params.append(user_id)

        try:
            cursor.execute(f"""
                UPDATE users SET {', '.join(updates)} WHERE id = ?
            """, params)

            # Log action (thread-safe - pass connection explicitly)
            self.auth_service.log_action(
                user_id=updated_by,
                action="update_user",
                entity_type="user",
                entity_id=user_id,
                conn=conn
            )

            conn.commit()
            conn.close()

            return self.get_user_by_id(user_id), None

        except Exception as e:
            conn.close()
            return None, sanitize_error(e, "user update")

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Change a user's password.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password

        Returns:
            Tuple of (success, error_message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get current password hash
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False, "User not found"

        if not self.auth_service.verify_password(current_password, row["password_hash"]):
            conn.close()
            return False, "Current password is incorrect"

        # Update password
        new_hash = self.auth_service.hash_password(new_password)
        cursor.execute("""
            UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?
        """, (new_hash, datetime.utcnow(), user_id))

        # Invalidate all sessions (thread-safe - pass connection explicitly)
        self.auth_service.invalidate_all_user_sessions(user_id, conn=conn)

        # Log action (thread-safe - pass connection explicitly)
        self.auth_service.log_action(
            user_id=user_id,
            action="change_password",
            conn=conn
        )

        conn.commit()
        conn.close()

        return True, None

    def delete_user(self, user_id: int, deleted_by: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Deactivate a user (soft delete).

        Args:
            user_id: User ID to deactivate
            deleted_by: ID of user performing deletion

        Returns:
            Tuple of (success, error_message)
        """
        # Don't allow deleting yourself
        if user_id == deleted_by:
            return False, "Cannot deactivate your own account"

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users SET is_active = 0, updated_at = ? WHERE id = ?
        """, (datetime.utcnow(), user_id))

        # Invalidate all sessions (thread-safe - pass connection explicitly)
        self.auth_service.invalidate_all_user_sessions(user_id, conn=conn)

        # Log action (thread-safe - pass connection explicitly)
        self.auth_service.log_action(
            user_id=deleted_by,
            action="deactivate_user",
            entity_type="user",
            entity_id=user_id,
            conn=conn
        )

        conn.commit()
        conn.close()

        return True, None

    # ========================================================================
    # CREW MANAGEMENT METHODS
    # ========================================================================

    def create_crew(self, crew_data: CrewCreate, created_by: Optional[int] = None) -> Tuple[Optional[CrewResponse], Optional[str]]:
        """Create a new crew."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO crews (name, description, manager_id)
                VALUES (?, ?, ?)
            """, (crew_data.name, crew_data.description, crew_data.manager_id))

            crew_id = cursor.lastrowid

            # Log action (thread-safe - pass connection explicitly)
            self.auth_service.log_action(
                user_id=created_by,
                action="create_crew",
                entity_type="crew",
                entity_id=crew_id,
                conn=conn
            )

            conn.commit()
            conn.close()

            return self.get_crew_by_id(crew_id), None

        except Exception as e:
            conn.close()
            return None, sanitize_error(e, "crew creation")

    def get_crew_by_id(self, crew_id: int) -> Optional[CrewResponse]:
        """Get crew by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.id, c.name, c.description, c.manager_id, c.is_active, c.created_at,
                   u.first_name || ' ' || u.last_name as manager_name,
                   (SELECT COUNT(*) FROM crew_members WHERE crew_id = c.id) as member_count
            FROM crews c
            LEFT JOIN users u ON c.manager_id = u.id
            WHERE c.id = ?
        """, (crew_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return CrewResponse(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            manager_id=row["manager_id"],
            manager_name=row["manager_name"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            member_count=row["member_count"]
        )

    def list_crews(self, is_active: Optional[bool] = None) -> List[CrewResponse]:
        """List all crews."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT c.id, c.name, c.description, c.manager_id, c.is_active, c.created_at,
                   u.first_name || ' ' || u.last_name as manager_name,
                   (SELECT COUNT(*) FROM crew_members WHERE crew_id = c.id) as member_count
            FROM crews c
            LEFT JOIN users u ON c.manager_id = u.id
        """

        if is_active is not None:
            query += " WHERE c.is_active = ?"
            cursor.execute(query + " ORDER BY c.name", (1 if is_active else 0,))
        else:
            cursor.execute(query + " ORDER BY c.name")

        rows = cursor.fetchall()
        conn.close()

        return [
            CrewResponse(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                manager_id=row["manager_id"],
                manager_name=row["manager_name"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                member_count=row["member_count"]
            )
            for row in rows
        ]

    def update_crew(
        self,
        crew_id: int,
        crew_data: CrewUpdate,
        updated_by: Optional[int] = None
    ) -> Tuple[Optional[CrewResponse], Optional[str]]:
        """Update a crew."""
        conn = self._get_connection()
        cursor = conn.cursor()

        updates = []
        params = []

        if crew_data.name is not None:
            updates.append("name = ?")
            params.append(crew_data.name)

        if crew_data.description is not None:
            updates.append("description = ?")
            params.append(crew_data.description)

        if crew_data.manager_id is not None:
            updates.append("manager_id = ?")
            params.append(crew_data.manager_id)

        if crew_data.is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if crew_data.is_active else 0)

        if not updates:
            conn.close()
            return self.get_crew_by_id(crew_id), None

        updates.append("updated_at = ?")
        params.append(datetime.utcnow())
        params.append(crew_id)

        try:
            cursor.execute(f"""
                UPDATE crews SET {', '.join(updates)} WHERE id = ?
            """, params)

            # Log action (thread-safe - pass connection explicitly)
            self.auth_service.log_action(
                user_id=updated_by,
                action="update_crew",
                entity_type="crew",
                entity_id=crew_id,
                conn=conn
            )

            conn.commit()
            conn.close()

            return self.get_crew_by_id(crew_id), None

        except Exception as e:
            conn.close()
            return None, sanitize_error(e, "crew update")

    def add_crew_member(
        self,
        crew_id: int,
        user_id: int,
        added_by: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """Add a user to a crew."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO crew_members (crew_id, user_id)
                VALUES (?, ?)
            """, (crew_id, user_id))

            # Log action (thread-safe - pass connection explicitly)
            self.auth_service.log_action(
                user_id=added_by,
                action="add_crew_member",
                entity_type="crew",
                entity_id=crew_id,
                details=f'{{"user_id": {user_id}}}',
                conn=conn
            )

            conn.commit()
            conn.close()
            return True, None

        except sqlite3.IntegrityError:
            conn.close()
            return False, "User is already a member of this crew"
        except Exception as e:
            conn.close()
            return False, sanitize_error(e, "adding crew member")

    def remove_crew_member(
        self,
        crew_id: int,
        user_id: int,
        removed_by: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """Remove a user from a crew."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM crew_members WHERE crew_id = ? AND user_id = ?
        """, (crew_id, user_id))

        if cursor.rowcount == 0:
            conn.close()
            return False, "User is not a member of this crew"

        # Log action (thread-safe - pass connection explicitly)
        self.auth_service.log_action(
            user_id=removed_by,
            action="remove_crew_member",
            entity_type="crew",
            entity_id=crew_id,
            details=f'{{"user_id": {user_id}}}',
            conn=conn
        )

        conn.commit()
        conn.close()
        return True, None

    def get_crew_members(self, crew_id: int) -> List[CrewMemberResponse]:
        """Get all members of a crew."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.id as user_id, u.username, u.first_name, u.last_name, u.role, cm.joined_at
            FROM crew_members cm
            JOIN users u ON cm.user_id = u.id
            WHERE cm.crew_id = ?
            ORDER BY u.username
        """, (crew_id,))

        rows = cursor.fetchall()
        conn.close()

        return [
            CrewMemberResponse(
                user_id=row["user_id"],
                username=row["username"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                role=UserRole(row["role"]),
                joined_at=row["joined_at"]
            )
            for row in rows
        ]

    def get_user_crews(self, user_id: int) -> List[CrewResponse]:
        """Get all crews a user belongs to."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.id, c.name, c.description, c.manager_id, c.is_active, c.created_at,
                   u.first_name || ' ' || u.last_name as manager_name,
                   (SELECT COUNT(*) FROM crew_members WHERE crew_id = c.id) as member_count
            FROM crews c
            JOIN crew_members cm ON c.id = cm.crew_id
            LEFT JOIN users u ON c.manager_id = u.id
            WHERE cm.user_id = ?
            ORDER BY c.name
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [
            CrewResponse(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                manager_id=row["manager_id"],
                manager_name=row["manager_name"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                member_count=row["member_count"]
            )
            for row in rows
        ]


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_user_service: Optional[UserService] = None


def get_user_service(db_path: str = "agtools.db") -> UserService:
    """Get or create the user service singleton."""
    global _user_service

    if _user_service is None:
        _user_service = UserService(db_path)

    return _user_service
