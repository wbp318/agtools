"""
Mobile Web Routes for Crew Interface
AgTools v2.6.0 Phase 6.2

Provides server-rendered HTML pages for mobile crew members:
- /m/login - Login page
- /m/logout - Logout and redirect
- /m/tasks - Task list (assigned to user)
- /m/tasks/{id} - Task detail (Phase 6.3)
"""

from typing import Optional
from datetime import date

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth import (
    get_session_user,
    set_session_cookie,
    clear_session_cookie,
    require_session,
)
from services.auth_service import get_auth_service
from services.task_service import get_task_service, TaskStatus, TaskPriority


# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(prefix="/m", tags=["Mobile Web"])

# Templates will be configured when router is included in main app
templates: Optional[Jinja2Templates] = None


def configure_templates(template_dir: str) -> None:
    """Configure Jinja2 templates directory."""
    global templates
    templates = Jinja2Templates(directory=template_dir)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_priority_class(priority: str) -> str:
    """Get CSS class for priority badge."""
    return {
        "urgent": "badge-danger",
        "high": "badge-warning",
        "medium": "badge-info",
        "low": "badge-secondary",
    }.get(priority, "badge-secondary")


def get_status_class(status: str) -> str:
    """Get CSS class for status badge."""
    return {
        "todo": "badge-secondary",
        "in_progress": "badge-primary",
        "completed": "badge-success",
        "cancelled": "badge-muted",
    }.get(status, "badge-secondary")


def get_status_label(status: str) -> str:
    """Get human-readable status label."""
    return {
        "todo": "To Do",
        "in_progress": "In Progress",
        "completed": "Completed",
        "cancelled": "Cancelled",
    }.get(status, status)


def is_overdue(due_date, status: str) -> bool:
    """Check if a task is overdue."""
    if not due_date or status in ("completed", "cancelled"):
        return False
    if isinstance(due_date, str):
        due_date = date.fromisoformat(due_date)
    return due_date < date.today()


# ============================================================================
# LOGIN ROUTES
# ============================================================================

@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    next: Optional[str] = None,
    error: Optional[str] = None
):
    """
    Display login page.

    Query params:
        next: URL to redirect to after login
        error: Error message to display
    """
    # Check if already logged in
    user = await get_session_user(request)
    if user:
        return RedirectResponse(url="/m/tasks", status_code=302)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "next": next,
            "error": error,
            "user": None,  # Not logged in
        }
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: Optional[str] = Form(None)
):
    """
    Process login form submission.

    Form fields:
        username: User's username
        password: User's password
        next: URL to redirect to after login
    """
    auth_service = get_auth_service()

    # Attempt authentication
    result = auth_service.authenticate_user(
        username=username,
        password=password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    if not result.get("success"):
        # Authentication failed - show login page with error
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": result.get("message", "Invalid username or password"),
                "username": username,
                "next": next,
                "user": None,
            }
        )

    # Authentication successful - set cookie and redirect
    redirect_url = next if next else "/m/tasks"
    response = RedirectResponse(url=redirect_url, status_code=302)
    set_session_cookie(response, result["access_token"])

    return response


@router.get("/logout")
async def logout(request: Request):
    """
    Logout user and redirect to login page.
    """
    response = RedirectResponse(url="/m/login", status_code=302)
    clear_session_cookie(response)
    return response


# ============================================================================
# TASK LIST ROUTES
# ============================================================================

@router.get("/tasks", response_class=HTMLResponse)
async def task_list(
    request: Request,
    status: Optional[str] = None,
    priority: Optional[str] = None,
):
    """
    Display list of tasks assigned to the current user.

    Query params:
        status: Filter by status (todo, in_progress, completed, cancelled)
        priority: Filter by priority (low, medium, high, urgent)
    """
    # Check authentication
    user = await get_session_user(request)
    if not user:
        return RedirectResponse(url="/m/login?next=/m/tasks", status_code=302)

    task_service = get_task_service()

    # Parse filter values
    status_filter = None
    if status and status in [s.value for s in TaskStatus]:
        status_filter = TaskStatus(status)

    priority_filter = None
    if priority and priority in [p.value for p in TaskPriority]:
        priority_filter = TaskPriority(priority)

    # Get tasks for this user
    tasks = task_service.list_tasks(
        status=status_filter,
        priority=priority_filter,
        user_id=user["id"],
        user_role=user["role"],
        my_tasks_only=True,  # Mobile view shows only user's assigned tasks
        is_active=True,
    )

    # Enrich tasks with display helpers
    enriched_tasks = []
    for task in tasks:
        task_dict = task.model_dump() if hasattr(task, 'model_dump') else task.__dict__
        task_dict["priority_class"] = get_priority_class(task_dict.get("priority", "medium"))
        task_dict["status_class"] = get_status_class(task_dict.get("status", "todo"))
        task_dict["status_label"] = get_status_label(task_dict.get("status", "todo"))
        task_dict["is_overdue"] = is_overdue(task_dict.get("due_date"), task_dict.get("status", ""))
        enriched_tasks.append(task_dict)

    # Count by status for summary
    status_counts = {
        "todo": len([t for t in enriched_tasks if t.get("status") == "todo"]),
        "in_progress": len([t for t in enriched_tasks if t.get("status") == "in_progress"]),
        "completed": len([t for t in enriched_tasks if t.get("status") == "completed"]),
    }

    return templates.TemplateResponse(
        "tasks/list.html",
        {
            "request": request,
            "user": user,
            "tasks": enriched_tasks,
            "status_counts": status_counts,
            "current_status": status,
            "current_priority": priority,
            "statuses": [s.value for s in TaskStatus if s != TaskStatus.CANCELLED],
            "priorities": [p.value for p in TaskPriority],
        }
    )


@router.get("/tasks/{task_id}", response_class=HTMLResponse)
async def task_detail(
    request: Request,
    task_id: int,
):
    """
    Display task detail page with actions.

    Phase 6.3 will implement full functionality:
    - Task details
    - Status update buttons
    - Time logging form
    - Photo upload
    """
    # Check authentication
    user = await get_session_user(request)
    if not user:
        return RedirectResponse(url=f"/m/login?next=/m/tasks/{task_id}", status_code=302)

    task_service = get_task_service()
    task = task_service.get_task_by_id(task_id)

    if not task:
        # Task not found - redirect to list
        return RedirectResponse(url="/m/tasks", status_code=302)

    # Check permission
    can_view = task_service.can_view_task(task_id, user["id"], user["role"])
    if not can_view:
        return RedirectResponse(url="/m/tasks", status_code=302)

    task_dict = task.model_dump() if hasattr(task, 'model_dump') else task.__dict__
    task_dict["priority_class"] = get_priority_class(task_dict.get("priority", "medium"))
    task_dict["status_class"] = get_status_class(task_dict.get("status", "todo"))
    task_dict["status_label"] = get_status_label(task_dict.get("status", "todo"))
    task_dict["is_overdue"] = is_overdue(task_dict.get("due_date"), task_dict.get("status", ""))

    # Determine available actions
    can_edit = task_service.can_edit_task(task_id, user["id"], user["role"])
    current_status = task_dict.get("status", "todo")

    # Available status transitions
    next_statuses = []
    if current_status == "todo":
        next_statuses = [("in_progress", "Start Task", "btn-primary")]
    elif current_status == "in_progress":
        next_statuses = [
            ("completed", "Mark Complete", "btn-success"),
            ("todo", "Move to To Do", "btn-secondary"),
        ]
    elif current_status == "completed":
        next_statuses = [("in_progress", "Reopen", "btn-warning")]

    return templates.TemplateResponse(
        "tasks/detail.html",
        {
            "request": request,
            "user": user,
            "task": task_dict,
            "can_edit": can_edit,
            "next_statuses": next_statuses,
        }
    )


@router.post("/tasks/{task_id}/status", response_class=HTMLResponse)
async def update_task_status(
    request: Request,
    task_id: int,
    status: str = Form(...),
):
    """
    Update task status (one-tap action).

    Form fields:
        status: New status value
    """
    # Check authentication
    user = await get_session_user(request)
    if not user:
        return RedirectResponse(url=f"/m/login?next=/m/tasks/{task_id}", status_code=302)

    task_service = get_task_service()

    # Check permission
    can_edit = task_service.can_edit_task(task_id, user["id"], user["role"])
    if not can_edit:
        return RedirectResponse(url="/m/tasks", status_code=302)

    # Validate status
    try:
        new_status = TaskStatus(status)
    except ValueError:
        return RedirectResponse(url=f"/m/tasks/{task_id}", status_code=302)

    # Update status
    task_service.change_status(task_id, new_status, user["id"])

    # Redirect back to task detail
    return RedirectResponse(url=f"/m/tasks/{task_id}", status_code=302)
