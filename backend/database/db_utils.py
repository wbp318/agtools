"""
Database Utilities
AgTools v6.13.5

Provides context managers and utilities for safe database connection handling.
Ensures connections are properly closed even when exceptions occur.
"""

import os
import sys
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional


def get_default_db_path() -> str:
    """
    Get the default database path.

    In bundled mode (PyInstaller), uses AppData for writable storage.
    In development, uses the current directory.

    The path can be overridden via AGTOOLS_DB_PATH environment variable.
    """
    # Check for explicit override
    env_path = os.environ.get('AGTOOLS_DB_PATH')
    if env_path:
        # Ensure directory exists
        db_dir = os.path.dirname(env_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        return env_path

    if getattr(sys, 'frozen', False):
        # Running as bundled exe - use AppData for writable storage
        app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        db_dir = os.path.join(app_data, 'AgTools')
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, 'agtools.db')
    else:
        # Development mode - use current directory
        return 'agtools.db'


# Default database path (computed on module load)
DEFAULT_DB_PATH = get_default_db_path()


@contextmanager
def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.

    Ensures the connection is properly closed even if an exception occurs.
    Sets row_factory to sqlite3.Row for dict-like access.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM fields")
            rows = cursor.fetchall()
            conn.commit()  # if needed

    Args:
        db_path: Path to the SQLite database file

    Yields:
        sqlite3.Connection with row_factory set to sqlite3.Row
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn:
            conn.close()


@contextmanager
def get_db_cursor(db_path: str = DEFAULT_DB_PATH, commit: bool = False) -> Generator[sqlite3.Cursor, None, None]:
    """
    Context manager for database cursor with automatic connection handling.

    Optionally commits changes on successful completion.

    Usage:
        # Read-only query
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM fields")
            rows = cursor.fetchall()

        # Write operation with commit
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("INSERT INTO fields ...")

    Args:
        db_path: Path to the SQLite database file
        commit: If True, commits the transaction on successful completion

    Yields:
        sqlite3.Cursor
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise


class DatabaseManager:
    """
    Database manager class for services that need persistent connection management.

    Provides context manager methods and connection pooling-like behavior.

    Usage:
        class MyService:
            def __init__(self, db_path: str = "agtools.db"):
                self.db = DatabaseManager(db_path)

            def get_items(self):
                with self.db.connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM items")
                    return cursor.fetchall()

            def create_item(self, name: str):
                with self.db.transaction() as cursor:
                    cursor.execute("INSERT INTO items (name) VALUES (?)", (name,))
                    return cursor.lastrowid
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        Initialize database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a database connection using context manager.

        Usage:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                # ... use cursor
        """
        with get_db_connection(self.db_path) as conn:
            yield conn

    @contextmanager
    def cursor(self, commit: bool = False) -> Generator[sqlite3.Cursor, None, None]:
        """
        Get a database cursor using context manager.

        Args:
            commit: If True, commits on successful completion

        Usage:
            with self.db.cursor() as cursor:
                cursor.execute("SELECT ...")
        """
        with get_db_cursor(self.db_path, commit=commit) as cursor:
            yield cursor

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        Get a database cursor with automatic commit on success.

        Rolls back on exception.

        Usage:
            with self.db.transaction() as cursor:
                cursor.execute("INSERT ...")
                cursor.execute("UPDATE ...")
                # Commits automatically if no exception
        """
        with get_db_cursor(self.db_path, commit=True) as cursor:
            yield cursor

    def execute(self, sql: str, params: tuple = ()) -> list:
        """
        Execute a query and return all results.

        Args:
            sql: SQL query string
            params: Query parameters

        Returns:
            List of rows (sqlite3.Row objects)
        """
        with self.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def execute_one(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Execute a query and return a single result.

        Args:
            sql: SQL query string
            params: Query parameters

        Returns:
            Single row or None
        """
        with self.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def execute_write(self, sql: str, params: tuple = ()) -> int:
        """
        Execute a write operation (INSERT, UPDATE, DELETE) and return lastrowid.

        Args:
            sql: SQL statement
            params: Statement parameters

        Returns:
            lastrowid for INSERT, or number of affected rows
        """
        with self.transaction() as cursor:
            cursor.execute(sql, params)
            return cursor.lastrowid

    def execute_many(self, sql: str, params_list: list) -> int:
        """
        Execute a statement with multiple parameter sets.

        Args:
            sql: SQL statement
            params_list: List of parameter tuples

        Returns:
            Number of rows affected
        """
        with self.transaction() as cursor:
            cursor.executemany(sql, params_list)
            return cursor.rowcount


# Convenience function for simple queries
def query(sql: str, params: tuple = (), db_path: str = DEFAULT_DB_PATH) -> list:
    """
    Execute a query and return all results.

    Args:
        sql: SQL query string
        params: Query parameters
        db_path: Database path

    Returns:
        List of sqlite3.Row objects
    """
    with get_db_cursor(db_path) as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def query_one(sql: str, params: tuple = (), db_path: str = DEFAULT_DB_PATH) -> Optional[sqlite3.Row]:
    """
    Execute a query and return a single result.

    Args:
        sql: SQL query string
        params: Query parameters
        db_path: Database path

    Returns:
        Single sqlite3.Row or None
    """
    with get_db_cursor(db_path) as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()
