"""
Task Management API Client

Handles task CRUD operations for the Farm Operations Manager.
AgTools v2.5.0 Phase 2
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List, Tuple

from .client import APIClient, get_api_client


@dataclass
class TaskInfo:
    """Task information dataclass"""
    id: int
    title: str
    description: Optional[str]
    status: str  # todo, in_progress, completed, cancelled
    priority: str  # low, medium, high, urgent
    assigned_to_user_id: Optional[int]
    assigned_to_user_name: Optional[str]
    assigned_to_crew_id: Optional[int]
    assigned_to_crew_name: Optional[str]
    created_by_user_id: int
    created_by_user_name: str
    due_date: Optional[str]
    completed_at: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "TaskInfo":
        """Create TaskInfo from API response dict."""
        return cls(
            id=data.get("id", 0),
            title=data.get("title", ""),
            description=data.get("description"),
            status=data.get("status", "todo"),
            priority=data.get("priority", "medium"),
            assigned_to_user_id=data.get("assigned_to_user_id"),
            assigned_to_user_name=data.get("assigned_to_user_name"),
            assigned_to_crew_id=data.get("assigned_to_crew_id"),
            assigned_to_crew_name=data.get("assigned_to_crew_name"),
            created_by_user_id=data.get("created_by_user_id", 0),
            created_by_user_name=data.get("created_by_user_name", ""),
            due_date=data.get("due_date"),
            completed_at=data.get("completed_at"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date or self.status in ("completed", "cancelled"):
            return False
        try:
            due = datetime.fromisoformat(self.due_date.replace("Z", "+00:00"))
            return due.date() < date.today()
        except (ValueError, AttributeError):
            return False

    @property
    def status_display(self) -> str:
        """Get display-friendly status text."""
        return {
            "todo": "To Do",
            "in_progress": "In Progress",
            "completed": "Completed",
            "cancelled": "Cancelled"
        }.get(self.status, self.status.title())

    @property
    def priority_display(self) -> str:
        """Get display-friendly priority text."""
        return self.priority.title()

    @property
    def assigned_to_display(self) -> str:
        """Get display text for assignment."""
        if self.assigned_to_user_name:
            return self.assigned_to_user_name
        if self.assigned_to_crew_name:
            return f"Crew: {self.assigned_to_crew_name}"
        return "Unassigned"


class TaskAPI:
    """Task management API client"""

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to_user_id: Optional[int] = None,
        assigned_to_crew_id: Optional[int] = None,
        due_before: Optional[str] = None,
        due_after: Optional[str] = None,
        my_tasks: bool = False
    ) -> Tuple[List[TaskInfo], Optional[str]]:
        """
        List tasks with filters.

        Args:
            status: Filter by status (todo, in_progress, completed, cancelled)
            priority: Filter by priority (low, medium, high, urgent)
            assigned_to_user_id: Filter by assigned user
            assigned_to_crew_id: Filter by assigned crew
            due_before: Filter tasks due before this date (YYYY-MM-DD)
            due_after: Filter tasks due after this date (YYYY-MM-DD)
            my_tasks: Only show tasks assigned to current user

        Returns:
            Tuple of (list of TaskInfo, error_message)
        """
        params = {}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        if assigned_to_user_id:
            params["assigned_to_user_id"] = assigned_to_user_id
        if assigned_to_crew_id:
            params["assigned_to_crew_id"] = assigned_to_crew_id
        if due_before:
            params["due_before"] = due_before
        if due_after:
            params["due_after"] = due_after
        if my_tasks:
            params["my_tasks"] = "true"

        response = self._client.get("/tasks", params=params if params else None)

        if not response.success:
            return [], response.error_message

        tasks = [TaskInfo.from_dict(t) for t in response.data.get("tasks", [])]
        return tasks, None

    def get_task(self, task_id: int) -> Tuple[Optional[TaskInfo], Optional[str]]:
        """
        Get task by ID.

        Returns:
            Tuple of (TaskInfo, error_message)
        """
        response = self._client.get(f"/tasks/{task_id}")

        if not response.success:
            return None, response.error_message

        return TaskInfo.from_dict(response.data), None

    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        status: str = "todo",
        priority: str = "medium",
        assigned_to_user_id: Optional[int] = None,
        assigned_to_crew_id: Optional[int] = None,
        due_date: Optional[str] = None
    ) -> Tuple[Optional[TaskInfo], Optional[str]]:
        """
        Create a new task.

        Args:
            title: Task title (required)
            description: Task description
            status: Initial status (default: todo)
            priority: Priority level (default: medium)
            assigned_to_user_id: Assign to specific user
            assigned_to_crew_id: Assign to crew
            due_date: Due date (YYYY-MM-DD format)

        Returns:
            Tuple of (created TaskInfo, error_message)
        """
        data = {
            "title": title,
            "status": status,
            "priority": priority
        }
        if description:
            data["description"] = description
        if assigned_to_user_id:
            data["assigned_to_user_id"] = assigned_to_user_id
        if assigned_to_crew_id:
            data["assigned_to_crew_id"] = assigned_to_crew_id
        if due_date:
            data["due_date"] = due_date

        response = self._client.post("/tasks", data=data)

        if not response.success:
            return None, response.error_message

        return TaskInfo.from_dict(response.data), None

    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to_user_id: Optional[int] = None,
        assigned_to_crew_id: Optional[int] = None,
        due_date: Optional[str] = None
    ) -> Tuple[Optional[TaskInfo], Optional[str]]:
        """
        Update a task.

        Returns:
            Tuple of (updated TaskInfo, error_message)
        """
        data = {}
        if title is not None:
            data["title"] = title
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status
        if priority is not None:
            data["priority"] = priority
        if assigned_to_user_id is not None:
            data["assigned_to_user_id"] = assigned_to_user_id
        if assigned_to_crew_id is not None:
            data["assigned_to_crew_id"] = assigned_to_crew_id
        if due_date is not None:
            data["due_date"] = due_date

        response = self._client.put(f"/tasks/{task_id}", data=data)

        if not response.success:
            return None, response.error_message

        return TaskInfo.from_dict(response.data), None

    def delete_task(self, task_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete a task (soft delete).

        Returns:
            Tuple of (success, error_message)
        """
        response = self._client.delete(f"/tasks/{task_id}")

        if not response.success:
            return False, response.error_message

        return True, None

    def change_status(
        self,
        task_id: int,
        new_status: str
    ) -> Tuple[Optional[TaskInfo], Optional[str]]:
        """
        Change task status.

        Args:
            task_id: Task ID
            new_status: New status (todo, in_progress, completed, cancelled)

        Returns:
            Tuple of (updated TaskInfo, error_message)
        """
        data = {"status": new_status}

        response = self._client.post(f"/tasks/{task_id}/status", data=data)

        if not response.success:
            return None, response.error_message

        return TaskInfo.from_dict(response.data), None


# Singleton instance
_task_api: Optional[TaskAPI] = None


def get_task_api() -> TaskAPI:
    """Get or create the task API singleton."""
    global _task_api
    if _task_api is None:
        _task_api = TaskAPI()
    return _task_api
