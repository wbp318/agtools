"""
Task Management Router
AgTools v6.13.2

Handles:
- Task CRUD operations
- Task status management
- Role-based task access
"""

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from middleware.auth_middleware import (
    get_current_active_user,
    require_manager,
    AuthenticatedUser
)
from middleware.rate_limiter import limiter, RATE_MODERATE
from services.auth_service import UserRole
from services.task_service import (
    get_task_service,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatus,
    TaskPriority,
    StatusChangeRequest
)

router = APIRouter(prefix="/api/v1", tags=["Tasks"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class TaskListResponse(BaseModel):
    """Response for task list endpoint"""
    count: int
    tasks: List[TaskResponse]


# ============================================================================
# TASK MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/tasks", response_model=TaskListResponse, tags=["Tasks"])
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to_user_id: Optional[int] = None,
    assigned_to_crew_id: Optional[int] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    my_tasks: bool = False,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    List tasks with role-based filtering.

    - Admin: sees all tasks
    - Manager: sees own tasks, created tasks, and crew-assigned tasks
    - Crew: sees only own assigned tasks or tasks assigned to their crews

    Filters:
    - status: todo, in_progress, completed, cancelled
    - priority: low, medium, high, urgent
    - my_tasks: true to show only tasks assigned to current user
    """
    task_service = get_task_service()

    status_enum = TaskStatus(status) if status else None
    priority_enum = TaskPriority(priority) if priority else None

    tasks = task_service.list_tasks(
        status=status_enum,
        priority=priority_enum,
        assigned_to_user_id=assigned_to_user_id,
        assigned_to_crew_id=assigned_to_crew_id,
        due_before=due_before,
        due_after=due_after,
        user_id=user.id,
        user_role=user.role.value,
        my_tasks_only=my_tasks
    )

    return TaskListResponse(count=len(tasks), tasks=tasks)


@router.post("/tasks", response_model=TaskResponse, tags=["Tasks"])
@limiter.limit(RATE_MODERATE)
async def create_task(
    request: Request,
    task_data: TaskCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create a new task. Rate limited: 30/minute.

    - All users can create tasks
    - Crew members can only assign tasks to themselves
    - Managers/admins can assign to anyone
    """
    task_service = get_task_service()

    if user.role == UserRole.CREW:
        if task_data.assigned_to_user_id and task_data.assigned_to_user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Crew members can only assign tasks to themselves"
            )
        if not task_data.assigned_to_user_id and not task_data.assigned_to_crew_id:
            task_data.assigned_to_user_id = user.id

    task, error = task_service.create_task(task_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return task


@router.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task(
    task_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get task by ID."""
    task_service = get_task_service()

    if not task_service.can_view_task(task_id, user.id, user.role.value):
        raise HTTPException(status_code=403, detail="Access denied")

    task = task_service.get_task_by_id(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
@limiter.limit(RATE_MODERATE)
async def update_task(
    request: Request,
    task_id: int,
    task_data: TaskUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Update a task. Rate limited: 30/minute.

    - Admin: can update any task
    - Manager: can update own tasks, created tasks, or crew-assigned tasks
    - Crew: can only update tasks assigned to them
    """
    task_service = get_task_service()

    if not task_service.can_edit_task(task_id, user.id, user.role.value):
        raise HTTPException(status_code=403, detail="Access denied")

    if user.role == UserRole.CREW:
        if task_data.assigned_to_user_id and task_data.assigned_to_user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Crew members cannot reassign tasks to others"
            )

    task, error = task_service.update_task(task_id, task_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.delete("/tasks/{task_id}", tags=["Tasks"])
async def delete_task(
    task_id: int,
    user: AuthenticatedUser = Depends(require_manager)
):
    """
    Delete a task (soft delete).

    Manager/admin only.
    """
    task_service = get_task_service()

    if user.role == UserRole.MANAGER:
        if not task_service.can_edit_task(task_id, user.id, user.role.value):
            raise HTTPException(status_code=403, detail="Access denied")

    success, error = task_service.delete_task(task_id, user.id)

    if not success:
        raise HTTPException(status_code=400, detail=error or "Failed to delete task")

    return {"message": "Task deleted successfully"}


@router.post("/tasks/{task_id}/status", response_model=TaskResponse, tags=["Tasks"])
@limiter.limit(RATE_MODERATE)
async def change_task_status(
    request: Request,
    task_id: int,
    status_data: StatusChangeRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Change task status. Rate limited: 30/minute.

    Valid transitions:
    - todo -> in_progress, cancelled
    - in_progress -> todo, completed, cancelled
    - completed -> in_progress (reopen)
    - cancelled -> todo (restore)
    """
    task_service = get_task_service()

    if not task_service.can_edit_task(task_id, user.id, user.role.value):
        raise HTTPException(status_code=403, detail="Access denied")

    task, error = task_service.change_status(task_id, status_data.status, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task
