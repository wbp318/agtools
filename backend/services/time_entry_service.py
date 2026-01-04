"""
Time Entry Service for Mobile Crew Interface
Handles time logging for tasks - crew members can track hours worked.

AgTools v2.6.0 Phase 6.4
"""

import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class TimeEntryType(str, Enum):
    """Type of time entry"""
    WORK = "work"
    TRAVEL = "travel"
    BREAK = "break"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TimeEntryCreate(BaseModel):
    """Create time entry request"""
    task_id: int
    hours: float = Field(..., gt=0, le=24, description="Hours worked (0-24)")
    entry_type: TimeEntryType = TimeEntryType.WORK
    work_date: Optional[date] = None  # Defaults to today
    notes: Optional[str] = Field(None, max_length=500)


class TimeEntryUpdate(BaseModel):
    """Update time entry request"""
    hours: Optional[float] = Field(None, gt=0, le=24)
    entry_type: Optional[TimeEntryType] = None
    work_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)


class TimeEntryResponse(BaseModel):
    """Time entry response with joined data"""
    id: int
    task_id: int
    task_title: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    hours: float
    entry_type: TimeEntryType
    work_date: date
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class TaskTimeSummary(BaseModel):
    """Summary of time logged for a task"""
    task_id: int
    task_title: str
    total_hours: float
    work_hours: float
    travel_hours: float
    break_hours: float
    entry_count: int
    contributors: List[str]


class UserTimeSummary(BaseModel):
    """Summary of time logged by a user"""
    user_id: int
    user_name: str
    period_start: date
    period_end: date
    total_hours: float
    work_hours: float
    travel_hours: float
    task_count: int
    entries: List[TimeEntryResponse]


# ============================================================================
# TIME ENTRY SERVICE CLASS
# ============================================================================

class TimeEntryService:
    """
    Service for managing time entries:
    - Log hours worked on tasks
    - View time history
    - Generate time summaries
    """

    def __init__(self, db_path: str = "agtools.db"):
        """Initialize time entry service."""
        self.db_path = db_path
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

        # Create time_entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                hours REAL NOT NULL,
                entry_type VARCHAR(20) NOT NULL DEFAULT 'work',
                work_date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_task ON time_entries(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_user ON time_entries(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_date ON time_entries(work_date)")

        conn.commit()
        conn.close()

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _safe_get(self, row: sqlite3.Row, key: str, default=None):
        """Safely get a value from a sqlite3.Row."""
        try:
            return row[key]
        except (KeyError, IndexError):
            return default

    def _row_to_response(self, row: sqlite3.Row) -> TimeEntryResponse:
        """Convert a database row to TimeEntryResponse."""
        work_date = row["work_date"]
        if isinstance(work_date, str):
            work_date = date.fromisoformat(work_date)

        return TimeEntryResponse(
            id=row["id"],
            task_id=row["task_id"],
            task_title=self._safe_get(row, "task_title"),
            user_id=row["user_id"],
            user_name=self._safe_get(row, "user_name"),
            hours=row["hours"],
            entry_type=TimeEntryType(row["entry_type"]),
            work_date=work_date,
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    # ========================================================================
    # CRUD METHODS
    # ========================================================================

    def create_entry(
        self,
        entry_data: TimeEntryCreate,
        user_id: int
    ) -> Tuple[Optional[TimeEntryResponse], Optional[str]]:
        """
        Create a new time entry.

        Args:
            entry_data: Time entry data
            user_id: ID of user logging time

        Returns:
            Tuple of (TimeEntryResponse, error_message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify task exists
        cursor.execute("SELECT id FROM tasks WHERE id = ? AND is_active = 1", (entry_data.task_id,))
        if not cursor.fetchone():
            conn.close()
            return None, "Task not found"

        work_date = entry_data.work_date or date.today()

        try:
            cursor.execute("""
                INSERT INTO time_entries (
                    task_id, user_id, hours, entry_type, work_date, notes
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry_data.task_id,
                user_id,
                entry_data.hours,
                entry_data.entry_type.value,
                work_date.isoformat(),
                entry_data.notes
            ))

            entry_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return self.get_entry_by_id(entry_id), None

        except Exception as e:
            conn.close()
            return None, str(e)

    def get_entry_by_id(self, entry_id: int) -> Optional[TimeEntryResponse]:
        """Get time entry by ID with joined data."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                te.id, te.task_id, te.user_id, te.hours, te.entry_type,
                te.work_date, te.notes, te.created_at, te.updated_at,
                t.title as task_title,
                u.first_name || ' ' || u.last_name as user_name
            FROM time_entries te
            LEFT JOIN tasks t ON te.task_id = t.id
            LEFT JOIN users u ON te.user_id = u.id
            WHERE te.id = ?
        """, (entry_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_response(row)

    def list_entries_for_task(
        self,
        task_id: int,
        limit: int = 50
    ) -> List[TimeEntryResponse]:
        """Get all time entries for a task."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                te.id, te.task_id, te.user_id, te.hours, te.entry_type,
                te.work_date, te.notes, te.created_at, te.updated_at,
                t.title as task_title,
                u.first_name || ' ' || u.last_name as user_name
            FROM time_entries te
            LEFT JOIN tasks t ON te.task_id = t.id
            LEFT JOIN users u ON te.user_id = u.id
            WHERE te.task_id = ?
            ORDER BY te.work_date DESC, te.created_at DESC
            LIMIT ?
        """, (task_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_response(row) for row in rows]

    def list_entries_for_user(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[TimeEntryResponse]:
        """Get time entries for a user within date range."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Default to current week
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=7)

        cursor.execute("""
            SELECT
                te.id, te.task_id, te.user_id, te.hours, te.entry_type,
                te.work_date, te.notes, te.created_at, te.updated_at,
                t.title as task_title,
                u.first_name || ' ' || u.last_name as user_name
            FROM time_entries te
            LEFT JOIN tasks t ON te.task_id = t.id
            LEFT JOIN users u ON te.user_id = u.id
            WHERE te.user_id = ?
              AND te.work_date >= ?
              AND te.work_date <= ?
            ORDER BY te.work_date DESC, te.created_at DESC
            LIMIT ?
        """, (user_id, start_date.isoformat(), end_date.isoformat(), limit))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_response(row) for row in rows]

    def update_entry(
        self,
        entry_id: int,
        entry_data: TimeEntryUpdate,
        user_id: int
    ) -> Tuple[Optional[TimeEntryResponse], Optional[str]]:
        """
        Update a time entry.
        Users can only update their own entries.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify ownership
        cursor.execute(
            "SELECT user_id FROM time_entries WHERE id = ?",
            (entry_id,)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None, "Entry not found"

        if row["user_id"] != user_id:
            conn.close()
            return None, "Can only update your own entries"

        # Build update query
        updates = []
        params = []

        if entry_data.hours is not None:
            updates.append("hours = ?")
            params.append(entry_data.hours)

        if entry_data.entry_type is not None:
            updates.append("entry_type = ?")
            params.append(entry_data.entry_type.value)

        if entry_data.work_date is not None:
            updates.append("work_date = ?")
            params.append(entry_data.work_date.isoformat())

        if entry_data.notes is not None:
            updates.append("notes = ?")
            params.append(entry_data.notes)

        if not updates:
            conn.close()
            return self.get_entry_by_id(entry_id), None

        updates.append("updated_at = ?")
        params.append(datetime.utcnow())
        params.append(entry_id)

        try:
            cursor.execute(f"""
                UPDATE time_entries SET {', '.join(updates)} WHERE id = ?
            """, params)

            conn.commit()
            conn.close()

            return self.get_entry_by_id(entry_id), None

        except Exception as e:
            conn.close()
            return None, str(e)

    def delete_entry(
        self,
        entry_id: int,
        user_id: int,
        is_admin: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete a time entry.
        Users can delete their own entries, admins can delete any.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify ownership or admin
        cursor.execute(
            "SELECT user_id FROM time_entries WHERE id = ?",
            (entry_id,)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False, "Entry not found"

        if row["user_id"] != user_id and not is_admin:
            conn.close()
            return False, "Can only delete your own entries"

        cursor.execute("DELETE FROM time_entries WHERE id = ?", (entry_id,))
        conn.commit()
        conn.close()

        return True, None

    # ========================================================================
    # SUMMARY METHODS
    # ========================================================================

    def get_task_time_summary(self, task_id: int) -> Optional[TaskTimeSummary]:
        """Get time summary for a task."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get task title
        cursor.execute("SELECT title FROM tasks WHERE id = ?", (task_id,))
        task_row = cursor.fetchone()
        if not task_row:
            conn.close()
            return None

        # Get time summary
        cursor.execute("""
            SELECT
                COUNT(*) as entry_count,
                COALESCE(SUM(hours), 0) as total_hours,
                COALESCE(SUM(CASE WHEN entry_type = 'work' THEN hours ELSE 0 END), 0) as work_hours,
                COALESCE(SUM(CASE WHEN entry_type = 'travel' THEN hours ELSE 0 END), 0) as travel_hours,
                COALESCE(SUM(CASE WHEN entry_type = 'break' THEN hours ELSE 0 END), 0) as break_hours
            FROM time_entries
            WHERE task_id = ?
        """, (task_id,))

        summary_row = cursor.fetchone()

        # Get contributors
        cursor.execute("""
            SELECT DISTINCT u.first_name || ' ' || u.last_name as name
            FROM time_entries te
            JOIN users u ON te.user_id = u.id
            WHERE te.task_id = ?
        """, (task_id,))

        contributors = [row["name"] for row in cursor.fetchall()]
        conn.close()

        return TaskTimeSummary(
            task_id=task_id,
            task_title=task_row["title"],
            total_hours=summary_row["total_hours"],
            work_hours=summary_row["work_hours"],
            travel_hours=summary_row["travel_hours"],
            break_hours=summary_row["break_hours"],
            entry_count=summary_row["entry_count"],
            contributors=contributors
        )

    def get_user_time_summary(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[UserTimeSummary]:
        """Get time summary for a user within date range."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Default to current week
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=7)

        # Get user name
        cursor.execute(
            "SELECT first_name || ' ' || last_name as name FROM users WHERE id = ?",
            (user_id,)
        )
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return None

        # Get summary stats
        cursor.execute("""
            SELECT
                COALESCE(SUM(hours), 0) as total_hours,
                COALESCE(SUM(CASE WHEN entry_type = 'work' THEN hours ELSE 0 END), 0) as work_hours,
                COALESCE(SUM(CASE WHEN entry_type = 'travel' THEN hours ELSE 0 END), 0) as travel_hours,
                COUNT(DISTINCT task_id) as task_count
            FROM time_entries
            WHERE user_id = ?
              AND work_date >= ?
              AND work_date <= ?
        """, (user_id, start_date.isoformat(), end_date.isoformat()))

        summary_row = cursor.fetchone()
        conn.close()

        # Get entries
        entries = self.list_entries_for_user(user_id, start_date, end_date)

        return UserTimeSummary(
            user_id=user_id,
            user_name=user_row["name"],
            period_start=start_date,
            period_end=end_date,
            total_hours=summary_row["total_hours"],
            work_hours=summary_row["work_hours"],
            travel_hours=summary_row["travel_hours"],
            task_count=summary_row["task_count"],
            entries=entries
        )


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_time_entry_service: Optional[TimeEntryService] = None


def get_time_entry_service(db_path: str = "agtools.db") -> TimeEntryService:
    """Get or create the time entry service singleton."""
    global _time_entry_service

    if _time_entry_service is None:
        _time_entry_service = TimeEntryService(db_path)

    return _time_entry_service
