"""
Task Service for Farm Operations Manager
Handles task CRUD operations, status management, and role-based access.

AgTools v6.13.6
"""

import sqlite3
from datetime import datetime, date, timezone
from enum import Enum
from typing import Optional, List, Tuple

from pydantic import BaseModel, Field

from .auth_service import UserRole
from database.db_utils import get_db_connection
from .base_service import BaseService


# ============================================================================
# ENUMS
# ============================================================================

class TaskStatus(str, Enum):
    """Task status values"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TaskCreate(BaseModel):
    """Create task request"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to_user_id: Optional[int] = None
    assigned_to_crew_id: Optional[int] = None
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    """Update task request"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to_user_id: Optional[int] = None
    assigned_to_crew_id: Optional[int] = None
    due_date: Optional[date] = None


class TaskResponse(BaseModel):
    """Task response with joined data"""
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    assigned_to_user_id: Optional[int]
    assigned_to_user_name: Optional[str] = None
    assigned_to_crew_id: Optional[int]
    assigned_to_crew_name: Optional[str] = None
    created_by_user_id: int
    created_by_user_name: str
    due_date: Optional[date]
    completed_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StatusChangeRequest(BaseModel):
    """Request to change task status"""
    status: TaskStatus


# ============================================================================
# TASK SERVICE CLASS
# ============================================================================

class TaskService(BaseService[TaskResponse]):
    """
    Task service handling:
    - Task CRUD operations
    - Status management
    - Role-based access control

    Inherits from BaseService for common CRUD patterns.
    """

    TABLE_NAME = "tasks"

    # Valid status transitions
    VALID_TRANSITIONS = {
        TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
        TaskStatus.IN_PROGRESS: [TaskStatus.TODO, TaskStatus.COMPLETED, TaskStatus.CANCELLED],
        TaskStatus.COMPLETED: [TaskStatus.IN_PROGRESS],  # Reopen
        TaskStatus.CANCELLED: [TaskStatus.TODO],  # Restore
    }

    def __init__(self, db_path: str = "agtools.db"):
        """
        Initialize task service.

        Args:
            db_path: Path to SQLite database
        """
        super().__init__(db_path)

    def _init_database(self) -> None:
        """Initialize database tables if they don't exist."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Create tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'todo',
                    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
                    assigned_to_user_id INTEGER,
                    assigned_to_crew_id INTEGER,
                    created_by_user_id INTEGER NOT NULL,
                    due_date DATE,
                    completed_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (assigned_to_user_id) REFERENCES users(id),
                    FOREIGN KEY (assigned_to_crew_id) REFERENCES crews(id),
                    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assigned_user ON tasks(assigned_to_user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assigned_crew ON tasks(assigned_to_crew_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by_user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_active ON tasks(is_active)")

            conn.commit()

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _row_to_response(self, row: sqlite3.Row, **kwargs) -> TaskResponse:
        """Convert a database row to TaskResponse."""
        return TaskResponse(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=TaskStatus(row["status"]),
            priority=TaskPriority(row["priority"]),
            assigned_to_user_id=row["assigned_to_user_id"],
            assigned_to_user_name=row["assigned_to_user_name"],
            assigned_to_crew_id=row["assigned_to_crew_id"],
            assigned_to_crew_name=row["assigned_to_crew_name"],
            created_by_user_id=row["created_by_user_id"],
            created_by_user_name=row["created_by_user_name"],
            due_date=row["due_date"],
            completed_at=row["completed_at"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def get_user_crew_ids(self, user_id: int) -> List[int]:
        """Get all crew IDs that a user belongs to."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT crew_id FROM crew_members WHERE user_id = ?
            """, (user_id,))

            return [row["crew_id"] for row in cursor.fetchall()]

    def _validate_status_transition(self, current: TaskStatus, new: TaskStatus) -> bool:
        """Check if a status transition is valid."""
        if current == new:
            return True
        return new in self.VALID_TRANSITIONS.get(current, [])

    # ========================================================================
    # AUTHORIZATION HELPERS
    # ========================================================================

    def can_view_task(self, task_id: int, user_id: int, user_role: str) -> bool:
        """
        Check if user can view a task.

        - Admin: can view all
        - Manager: can view own, created by self, or assigned to their crews
        - Crew: can view own tasks or crew-assigned tasks
        """
        if user_role == "admin":
            return True

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT assigned_to_user_id, assigned_to_crew_id, created_by_user_id
                FROM tasks WHERE id = ? AND is_active = 1
            """, (task_id,))

            row = cursor.fetchone()

            if not row:
                return False

            # Check direct assignment
            if row["assigned_to_user_id"] == user_id:
                return True

            # Check if created by user
            if row["created_by_user_id"] == user_id:
                return True

            # Check crew assignment
            if row["assigned_to_crew_id"]:
                user_crews = self.get_user_crew_ids(user_id)
                if row["assigned_to_crew_id"] in user_crews:
                    return True

        return False

    def can_edit_task(self, task_id: int, user_id: int, user_role: str) -> bool:
        """
        Check if user can edit a task.

        - Admin: can edit all
        - Manager: can edit own, created by self, or crew-assigned
        - Crew: can edit only own assigned tasks
        """
        if user_role == "admin":
            return True

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT assigned_to_user_id, assigned_to_crew_id, created_by_user_id
                FROM tasks WHERE id = ? AND is_active = 1
            """, (task_id,))

            row = cursor.fetchone()

            if not row:
                return False

            # Check direct assignment
            if row["assigned_to_user_id"] == user_id:
                return True

            # Check if created by user (manager can edit their own created tasks)
            if user_role == "manager" and row["created_by_user_id"] == user_id:
                return True

            # Manager can edit crew-assigned tasks
            if user_role == "manager" and row["assigned_to_crew_id"]:
                user_crews = self.get_user_crew_ids(user_id)
                if row["assigned_to_crew_id"] in user_crews:
                    return True

        return False

    # ========================================================================
    # CRUD METHODS
    # ========================================================================

    def create_task(
        self,
        task_data: TaskCreate,
        created_by: int
    ) -> Tuple[Optional[TaskResponse], Optional[str]]:
        """
        Create a new task.

        Args:
            task_data: Task creation data
            created_by: ID of user creating this task

        Returns:
            Tuple of (TaskResponse, error_message)
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO tasks (
                        title, description, status, priority,
                        assigned_to_user_id, assigned_to_crew_id, created_by_user_id,
                        due_date
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_data.title,
                    task_data.description,
                    task_data.status.value,
                    task_data.priority.value,
                    task_data.assigned_to_user_id,
                    task_data.assigned_to_crew_id,
                    created_by,
                    task_data.due_date.isoformat() if task_data.due_date else None
                ))

                task_id = cursor.lastrowid

                # Log action (thread-safe - pass connection explicitly)
                self.auth_service.log_action(
                    user_id=created_by,
                    action="create_task",
                    entity_type="task",
                    entity_id=task_id,
                    conn=conn
                )

                conn.commit()

            return self.get_task_by_id(task_id), None

        except Exception as e:
            return None, self._sanitize_error(e, "task creation")

    def get_task_by_id(self, task_id: int) -> Optional[TaskResponse]:
        """Get task by ID with joined user/crew names."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    t.id, t.title, t.description, t.status, t.priority,
                    t.assigned_to_user_id, t.assigned_to_crew_id, t.created_by_user_id,
                    t.due_date, t.completed_at, t.is_active, t.created_at, t.updated_at,
                    u1.first_name || ' ' || u1.last_name as assigned_to_user_name,
                    c.name as assigned_to_crew_name,
                    u2.first_name || ' ' || u2.last_name as created_by_user_name
                FROM tasks t
                LEFT JOIN users u1 ON t.assigned_to_user_id = u1.id
                LEFT JOIN crews c ON t.assigned_to_crew_id = c.id
                LEFT JOIN users u2 ON t.created_by_user_id = u2.id
                WHERE t.id = ?
            """, (task_id,))

            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_response(row)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to_user_id: Optional[int] = None,
        assigned_to_crew_id: Optional[int] = None,
        created_by_user_id: Optional[int] = None,
        due_before: Optional[date] = None,
        due_after: Optional[date] = None,
        is_active: Optional[bool] = True,
        # Role-based filtering
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        my_tasks_only: bool = False
    ) -> List[TaskResponse]:
        """
        List tasks with optional filters.

        Args:
            status: Filter by status
            priority: Filter by priority
            assigned_to_user_id: Filter by assigned user
            assigned_to_crew_id: Filter by assigned crew
            created_by_user_id: Filter by creator
            due_before: Filter tasks due before this date
            due_after: Filter tasks due after this date
            is_active: Filter by active status
            user_id: Current user ID for role-based filtering
            user_role: Current user role for role-based filtering
            my_tasks_only: Only show tasks assigned to current user

        Returns:
            List of TaskResponse
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    t.id, t.title, t.description, t.status, t.priority,
                    t.assigned_to_user_id, t.assigned_to_crew_id, t.created_by_user_id,
                    t.due_date, t.completed_at, t.is_active, t.created_at, t.updated_at,
                    u1.first_name || ' ' || u1.last_name as assigned_to_user_name,
                    c.name as assigned_to_crew_name,
                    u2.first_name || ' ' || u2.last_name as created_by_user_name
                FROM tasks t
                LEFT JOIN users u1 ON t.assigned_to_user_id = u1.id
                LEFT JOIN crews c ON t.assigned_to_crew_id = c.id
                LEFT JOIN users u2 ON t.created_by_user_id = u2.id
            """

            conditions = []
            params = []

            # Apply filters
            if status:
                conditions.append("t.status = ?")
                params.append(status.value)

            if priority:
                conditions.append("t.priority = ?")
                params.append(priority.value)

            if assigned_to_user_id:
                conditions.append("t.assigned_to_user_id = ?")
                params.append(assigned_to_user_id)

            if assigned_to_crew_id:
                conditions.append("t.assigned_to_crew_id = ?")
                params.append(assigned_to_crew_id)

            if created_by_user_id:
                conditions.append("t.created_by_user_id = ?")
                params.append(created_by_user_id)

            if due_before:
                conditions.append("t.due_date <= ?")
                params.append(due_before.isoformat())

            if due_after:
                conditions.append("t.due_date >= ?")
                params.append(due_after.isoformat())

            if is_active is not None:
                conditions.append("t.is_active = ?")
                params.append(1 if is_active else 0)

            # Role-based filtering
            if user_id and user_role:
                if user_role == "admin":
                    # Admin sees all tasks
                    pass
                elif user_role == "manager":
                    # Manager sees: own tasks, created tasks, crew-assigned tasks
                    user_crews = self.get_user_crew_ids(user_id)
                    if my_tasks_only:
                        conditions.append("t.assigned_to_user_id = ?")
                        params.append(user_id)
                    else:
                        crew_condition = ""
                        if user_crews:
                            placeholders = ",".join("?" * len(user_crews))
                            crew_condition = f" OR t.assigned_to_crew_id IN ({placeholders})"
                            params_for_crews = user_crews
                        else:
                            crew_condition = ""
                            params_for_crews = []

                        conditions.append(f"""
                            (t.assigned_to_user_id = ?
                             OR t.created_by_user_id = ?
                             {crew_condition})
                        """)
                        params.extend([user_id, user_id] + params_for_crews)
                else:  # crew
                    # Crew sees: only own assigned tasks or crew-assigned tasks
                    user_crews = self.get_user_crew_ids(user_id)
                    if my_tasks_only or not user_crews:
                        conditions.append("t.assigned_to_user_id = ?")
                        params.append(user_id)
                    else:
                        placeholders = ",".join("?" * len(user_crews))
                        conditions.append(f"""
                            (t.assigned_to_user_id = ?
                             OR t.assigned_to_crew_id IN ({placeholders}))
                        """)
                        params.extend([user_id] + user_crews)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY t.priority DESC, t.due_date ASC NULLS LAST, t.created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_response(row) for row in rows]

    def update_task(
        self,
        task_id: int,
        task_data: TaskUpdate,
        updated_by: int
    ) -> Tuple[Optional[TaskResponse], Optional[str]]:
        """
        Update a task.

        Args:
            task_id: Task ID to update
            task_data: Update data
            updated_by: ID of user performing update

        Returns:
            Tuple of (TaskResponse, error_message)
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Get current task to validate status transition and for optimistic locking
            cursor.execute("SELECT status, updated_at FROM tasks WHERE id = ? AND is_active = 1", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None, "Task not found"

            current_status = TaskStatus(row["status"])
            original_updated_at = row["updated_at"]  # For optimistic locking

            # Build update query dynamically
            updates = []
            params = []

            if task_data.title is not None:
                updates.append("title = ?")
                params.append(task_data.title)

            if task_data.description is not None:
                updates.append("description = ?")
                params.append(task_data.description)

            if task_data.status is not None:
                # Validate status transition
                if not self._validate_status_transition(current_status, task_data.status):
                    return None, f"Invalid status transition from {current_status.value} to {task_data.status.value}"

                updates.append("status = ?")
                params.append(task_data.status.value)

                # Set completed_at if completing
                if task_data.status == TaskStatus.COMPLETED:
                    updates.append("completed_at = ?")
                    params.append(datetime.now(timezone.utc).isoformat())
                elif current_status == TaskStatus.COMPLETED:
                    # Reopening - clear completed_at
                    updates.append("completed_at = NULL")

            if task_data.priority is not None:
                updates.append("priority = ?")
                params.append(task_data.priority.value)

            if task_data.assigned_to_user_id is not None:
                updates.append("assigned_to_user_id = ?")
                params.append(task_data.assigned_to_user_id if task_data.assigned_to_user_id > 0 else None)

            if task_data.assigned_to_crew_id is not None:
                updates.append("assigned_to_crew_id = ?")
                params.append(task_data.assigned_to_crew_id if task_data.assigned_to_crew_id > 0 else None)

            if task_data.due_date is not None:
                updates.append("due_date = ?")
                params.append(task_data.due_date.isoformat())

            if not updates:
                return self.get_task_by_id(task_id), None

            updates.append("updated_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())
            # Add optimistic locking: only update if record hasn't changed
            params.append(task_id)
            params.append(original_updated_at)

            try:
                cursor.execute(f"""
                    UPDATE tasks SET {', '.join(updates)}
                    WHERE id = ? AND updated_at = ?
                """, params)

                # Check for concurrent modification (optimistic locking)
                if cursor.rowcount == 0:
                    # Verify task still exists to distinguish "not found" from "concurrent update"
                    cursor.execute("SELECT id FROM tasks WHERE id = ? AND is_active = 1", (task_id,))
                    if cursor.fetchone():
                        return None, "Task was modified by another user. Please refresh and try again."
                    return None, "Task not found"

                # Log action (thread-safe - pass connection explicitly)
                self.auth_service.log_action(
                    user_id=updated_by,
                    action="update_task",
                    entity_type="task",
                    entity_id=task_id,
                    conn=conn
                )

                conn.commit()

                return self.get_task_by_id(task_id), None

            except Exception as e:
                return None, self._sanitize_error(e, "task update")

    def change_status(
        self,
        task_id: int,
        new_status: TaskStatus,
        changed_by: int
    ) -> Tuple[Optional[TaskResponse], Optional[str]]:
        """
        Change task status with validation.

        Args:
            task_id: Task ID
            new_status: New status
            changed_by: ID of user making change

        Returns:
            Tuple of (TaskResponse, error_message)
        """
        task_update = TaskUpdate(status=new_status)
        return self.update_task(task_id, task_update, changed_by)

    def delete_task(
        self,
        task_id: int,
        deleted_by: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Soft delete a task.

        Args:
            task_id: Task ID to delete
            deleted_by: ID of user performing deletion

        Returns:
            Tuple of (success, error_message)
        """
        return self.soft_delete(task_id, deleted_by, entity_name="Task")


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_task_service: Optional[TaskService] = None


def get_task_service(db_path: str = "agtools.db") -> TaskService:
    """Get or create the task service singleton."""
    global _task_service

    if _task_service is None:
        _task_service = TaskService(db_path)

    return _task_service
