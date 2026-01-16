"""
Base Service Class for AgTools
Provides common CRUD patterns, database management, and utilities.

AgTools v6.13.8
"""

import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Tuple, Any, Type, TypeVar, Dict, Generic
from pydantic import BaseModel

from database.db_utils import get_db_connection, DatabaseManager


# Type variables for generic typing
ResponseT = TypeVar('ResponseT', bound=BaseModel)
CreateT = TypeVar('CreateT', bound=BaseModel)
UpdateT = TypeVar('UpdateT', bound=BaseModel)


class BaseService(ABC, Generic[ResponseT]):
    """
    Abstract base service class providing common functionality.

    Features:
    - Database connection management with context managers
    - Common CRUD operation patterns
    - Row conversion utilities
    - Audit logging integration
    - Query building helpers

    Subclasses should:
    1. Set TABLE_NAME class attribute
    2. Implement _init_database() for table creation
    3. Implement _row_to_response() for row conversion
    4. Optionally override CRUD methods for custom logic
    """

    # Subclasses should override
    TABLE_NAME: str = None

    def __init__(self, db_path: str = "agtools.db"):
        """
        Initialize base service.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.db = DatabaseManager(db_path)
        self._auth_service = None  # Lazy loaded to avoid circular imports
        self._init_database()

    @property
    def auth_service(self):
        """Lazy load auth service to avoid circular imports."""
        if self._auth_service is None:
            from .auth_service import get_auth_service
            self._auth_service = get_auth_service()
        return self._auth_service

    # ========================================================================
    # DATABASE MANAGEMENT
    # ========================================================================

    @abstractmethod
    def _init_database(self) -> None:
        """
        Initialize database tables.

        Subclasses must implement to create their tables and indexes.
        Should use context managers for connection handling.
        """
        pass

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.

        DEPRECATED: Use context managers instead:
            with get_db_connection(self.db_path) as conn:
                ...
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    @staticmethod
    def _safe_get(row: sqlite3.Row, key: str, default=None):
        """
        Safely get a value from a sqlite3.Row.

        Args:
            row: Database row
            key: Column name
            default: Default value if key not found

        Returns:
            Value or default
        """
        try:
            return row[key]
        except (KeyError, IndexError, TypeError):
            return default

    @staticmethod
    def _sanitize_error(error: Exception, operation: str = "operation") -> str:
        """
        Sanitize error message for user display.

        Logs the full error internally but returns a generic message to prevent
        information disclosure. Specific safe errors are allowed through.

        Args:
            error: The exception that occurred
            operation: Description of the operation for the error message

        Returns:
            Sanitized error message safe for user display
        """
        import logging
        error_str = str(error)

        # Log full error for debugging (internal only)
        logging.warning(f"Error during {operation}: {error_str}")

        # Allow specific safe error messages through
        safe_patterns = [
            "not found",
            "already exists",
            "invalid",
            "required",
            "must be",
            "cannot",
            "permission denied",
            "unauthorized",
            "conflict",
        ]

        error_lower = error_str.lower()
        for pattern in safe_patterns:
            if pattern in error_lower:
                # Return the error but strip any sensitive path or technical info
                # Limit length and remove path-like patterns
                import re
                sanitized = re.sub(r'[A-Za-z]:\\[^\s]+', '[path]', error_str)
                sanitized = re.sub(r'/[^\s]+/', '[path]/', sanitized)
                return sanitized[:200] if len(sanitized) > 200 else sanitized

        # For SQL and other technical errors, return generic message
        if any(keyword in error_lower for keyword in [
            'sql', 'database', 'constraint', 'foreign key', 'unique',
            'syntax', 'column', 'table', 'index', 'transaction'
        ]):
            return f"Database error during {operation}. Please try again or contact support."

        # Default generic error
        return f"An error occurred during {operation}. Please try again."

    @abstractmethod
    def _row_to_response(self, row: sqlite3.Row, **kwargs) -> ResponseT:
        """
        Convert database row to response model.

        Subclasses must implement for their specific response type.

        Args:
            row: Database row
            **kwargs: Additional conversion options

        Returns:
            Response model instance
        """
        pass

    # ========================================================================
    # QUERY BUILDING HELPERS
    # ========================================================================

    @staticmethod
    def build_conditions(
        filters: Dict[str, Any],
        field_mapping: Optional[Dict[str, str]] = None
    ) -> Tuple[List[str], List[Any]]:
        """
        Build WHERE conditions from a filter dictionary.

        Args:
            filters: Dictionary of field -> value pairs (None values ignored)
            field_mapping: Optional mapping of filter keys to SQL column names

        Returns:
            Tuple of (conditions list, params list)

        Example:
            filters = {"status": "active", "user_id": 5, "name": None}
            conditions, params = build_conditions(filters)
            # conditions = ["status = ?", "user_id = ?"]
            # params = ["active", 5]
        """
        conditions = []
        params = []
        mapping = field_mapping or {}

        for key, value in filters.items():
            if value is not None:
                column = mapping.get(key, key)
                conditions.append(f"{column} = ?")
                params.append(value)

        return conditions, params

    @staticmethod
    def build_like_conditions(
        search: str,
        fields: List[str]
    ) -> Tuple[str, List[str]]:
        """
        Build LIKE search condition across multiple fields.

        Args:
            search: Search term
            fields: List of field names to search

        Returns:
            Tuple of (condition string, params list)

        Example:
            condition, params = build_like_conditions("john", ["name", "email"])
            # condition = "(name LIKE ? OR email LIKE ?)"
            # params = ["%john%", "%john%"]
        """
        if not search or not fields:
            return "", []

        search_param = f"%{search}%"
        conditions = [f"{field} LIKE ?" for field in fields]
        params = [search_param] * len(fields)

        return f"({' OR '.join(conditions)})", params

    @staticmethod
    def build_update_params(
        data: BaseModel,
        field_mapping: Optional[Dict[str, str]] = None,
        enum_fields: Optional[List[str]] = None
    ) -> Tuple[List[str], List[Any]]:
        """
        Build UPDATE SET clause from a Pydantic model.

        Args:
            data: Pydantic model with update data
            field_mapping: Optional mapping of model fields to SQL columns
            enum_fields: List of fields that are enums (need .value)

        Returns:
            Tuple of (update clauses, params)

        Example:
            data = TaskUpdate(title="New Title", status=TaskStatus.DONE)
            updates, params = build_update_params(data, enum_fields=["status"])
            # updates = ["title = ?", "status = ?"]
            # params = ["New Title", "done"]
        """
        updates = []
        params = []
        mapping = field_mapping or {}
        enums = set(enum_fields or [])

        for field_name, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                column = mapping.get(field_name, field_name)
                updates.append(f"{column} = ?")

                # Handle enum values
                if field_name in enums and hasattr(value, 'value'):
                    params.append(value.value)
                else:
                    params.append(value)

        return updates, params

    # ========================================================================
    # STANDARD CRUD OPERATIONS
    # ========================================================================

    def get_by_id(
        self,
        entity_id: int,
        query: Optional[str] = None,
        include_inactive: bool = False
    ) -> Optional[ResponseT]:
        """
        Get entity by ID.

        Args:
            entity_id: Entity ID
            query: Optional custom SELECT query (must select by id param)
            include_inactive: Include soft-deleted records

        Returns:
            Response model or None if not found
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            if query:
                cursor.execute(query, (entity_id,))
            else:
                active_clause = "" if include_inactive else " AND is_active = 1"
                cursor.execute(
                    f"SELECT * FROM {self.TABLE_NAME} WHERE id = ?{active_clause}",
                    (entity_id,)
                )

            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_response(row)

    # Maximum records per query to prevent memory exhaustion
    MAX_LIMIT = 10000

    @staticmethod
    def _sanitize_order_by(order_by: str) -> str:
        """
        Sanitize ORDER BY clause to prevent SQL injection.

        Only allows alphanumeric column names with optional ASC/DESC.

        Args:
            order_by: Raw ORDER BY clause

        Returns:
            Sanitized ORDER BY clause

        Raises:
            ValueError: If order_by contains invalid characters
        """
        import re
        # Pattern: column_name (ASC|DESC)?, column_name (ASC|DESC)?
        # Allows: id DESC, name ASC, created_at, f.name DESC
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?\s*(ASC|DESC)?(\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?\s*(ASC|DESC)?)*$'
        if not re.match(pattern, order_by.strip(), re.IGNORECASE):
            raise ValueError(f"Invalid ORDER BY clause: {order_by}")
        return order_by

    def list_entities(
        self,
        query: str,
        conditions: Optional[List[str]] = None,
        params: Optional[List[Any]] = None,
        order_by: str = "id DESC",
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ResponseT]:
        """
        List entities with filters.

        Args:
            query: Base SELECT query
            conditions: List of WHERE conditions
            params: Parameters for conditions
            order_by: ORDER BY clause (sanitized for SQL injection)
            limit: Maximum records to return (capped at MAX_LIMIT)
            offset: Records to skip

        Returns:
            List of response models

        Raises:
            ValueError: If order_by contains invalid characters
        """
        # Sanitize order_by to prevent SQL injection
        safe_order_by = self._sanitize_order_by(order_by)

        # Cap limit to prevent memory exhaustion
        if limit is not None and limit > self.MAX_LIMIT:
            limit = self.MAX_LIMIT

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            final_query = query
            final_params = list(params or [])

            if conditions:
                final_query += " WHERE " + " AND ".join(conditions)

            final_query += f" ORDER BY {safe_order_by}"

            if limit:
                final_query += " LIMIT ? OFFSET ?"
                final_params.extend([limit, offset])

            cursor.execute(final_query, final_params)
            rows = cursor.fetchall()

            return [self._row_to_response(row) for row in rows]

    def soft_delete(
        self,
        entity_id: int,
        deleted_by: int,
        entity_name: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Soft delete an entity (set is_active = 0).

        Args:
            entity_id: Entity ID to delete
            deleted_by: User ID performing deletion
            entity_name: Optional name for error message (defaults to TABLE_NAME)

        Returns:
            Tuple of (success, error_message)
        """
        name = entity_name or self.TABLE_NAME

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
                UPDATE {self.TABLE_NAME}
                SET is_active = 0, updated_at = ?
                WHERE id = ? AND is_active = 1
            """, (datetime.utcnow(), entity_id))

            if cursor.rowcount == 0:
                return False, f"{name.title()} not found"

            # Log action (thread-safe - pass connection explicitly)
            self.auth_service.log_action(
                user_id=deleted_by,
                action=f"delete_{self.TABLE_NAME}",
                entity_type=self.TABLE_NAME,
                entity_id=entity_id,
                conn=conn
            )

            conn.commit()

        return True, None

    def log_action(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        action: str,
        entity_id: Optional[int] = None
    ) -> None:
        """
        Log an audit action (thread-safe wrapper).

        Args:
            conn: Database connection (for transaction consistency)
            user_id: User performing action
            action: Action name (e.g., "create_field")
            entity_id: Related entity ID
        """
        self.auth_service.log_action(
            user_id=user_id,
            action=action,
            entity_type=self.TABLE_NAME,
            entity_id=entity_id,
            conn=conn
        )


# ============================================================================
# SINGLETON FACTORY
# ============================================================================

class ServiceRegistry:
    """
    Singleton registry for service instances.

    Provides centralized service instance management with support
    for multiple database paths.
    """

    _instances: Dict[str, BaseService] = {}

    @classmethod
    def get_service(
        cls,
        service_class: Type[BaseService],
        db_path: str = "agtools.db"
    ) -> BaseService:
        """
        Get or create a service singleton.

        Args:
            service_class: Service class to instantiate
            db_path: Database path

        Returns:
            Service instance
        """
        key = f"{service_class.__name__}:{db_path}"

        if key not in cls._instances:
            cls._instances[key] = service_class(db_path)

        return cls._instances[key]

    @classmethod
    def clear(cls) -> None:
        """Clear all service instances (useful for testing)."""
        cls._instances.clear()


def get_service(
    service_class: Type[BaseService],
    db_path: str = "agtools.db"
) -> BaseService:
    """
    Convenience function to get service instance.

    Args:
        service_class: Service class
        db_path: Database path

    Returns:
        Service instance
    """
    return ServiceRegistry.get_service(service_class, db_path)


def sanitize_error(error: Exception, operation: str = "operation") -> str:
    """
    Sanitize error message for user display (standalone function).

    Use this function in services that don't inherit from BaseService.

    Args:
        error: The exception that occurred
        operation: Description of the operation for the error message

    Returns:
        Sanitized error message safe for user display
    """
    return BaseService._sanitize_error(error, operation)
