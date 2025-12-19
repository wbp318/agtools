"""
Cookie-based Session Authentication for Mobile Web Interface
AgTools v2.6.0 Phase 6

Uses HTTP-only cookies to store JWT tokens (more secure for web than localStorage).
"""

from functools import wraps
from typing import Optional, Dict, Any

from fastapi import Request, Response
from fastapi.responses import RedirectResponse

from services.auth_service import get_auth_service, UserRole


# ============================================================================
# CONFIGURATION
# ============================================================================

COOKIE_NAME = "agtools_session"
COOKIE_MAX_AGE = 60 * 60 * 24  # 24 hours (matches JWT expiration)


# ============================================================================
# SESSION HELPERS
# ============================================================================

async def get_session_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get user from session cookie.

    Args:
        request: FastAPI request object

    Returns:
        User dict with id, username, first_name, last_name, role
        or None if not authenticated
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None

    auth_service = get_auth_service()
    token_data = auth_service.validate_access_token(token)

    if not token_data:
        return None

    # Return basic user info from token
    # Note: For full user data, query user_service.get_user_by_id()
    return {
        "id": token_data.user_id,
        "username": token_data.username,
        "role": token_data.role.value,
        "is_admin": token_data.role == UserRole.ADMIN,
        "is_manager": token_data.role in (UserRole.ADMIN, UserRole.MANAGER),
    }


def set_session_cookie(response: Response, token: str) -> None:
    """
    Set session cookie with JWT token.

    Args:
        response: FastAPI response object
        token: JWT access token
    """
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,       # Prevents JavaScript access (XSS protection)
        samesite="lax",      # CSRF protection
        secure=False,        # Set True in production with HTTPS
        path="/",            # Available for all paths
    )


def clear_session_cookie(response: Response) -> None:
    """
    Clear session cookie (logout).

    Args:
        response: FastAPI response object
    """
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
    )


def require_session(func):
    """
    Decorator to require authenticated session for web routes.

    Redirects to login page if not authenticated.
    Sets request.state.user with user data if authenticated.

    Usage:
        @router.get("/tasks")
        @require_session
        async def task_list(request: Request):
            user = request.state.user
            ...
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = await get_session_user(request)
        if not user:
            # Redirect to login with return URL
            return_url = str(request.url.path)
            return RedirectResponse(
                url=f"/m/login?next={return_url}",
                status_code=302
            )

        # Attach user to request state for use in route handler
        request.state.user = user
        return await func(request, *args, **kwargs)

    return wrapper


# ============================================================================
# PERMISSION HELPERS
# ============================================================================

def can_view_task(user: Dict[str, Any], task: Dict[str, Any]) -> bool:
    """
    Check if user can view a task.

    Crew can view tasks assigned to them or their crew.
    Managers/admins can view all tasks.
    """
    if user.get("is_manager"):
        return True

    user_id = user.get("id")

    # Check direct assignment
    if task.get("assigned_to_user_id") == user_id:
        return True

    # Check crew assignment (would need to verify user is in crew)
    # For now, allow if assigned to any crew the user might be in
    if task.get("assigned_to_crew_id"):
        return True  # Full check requires crew membership lookup

    return False


def can_edit_task(user: Dict[str, Any], task: Dict[str, Any]) -> bool:
    """
    Check if user can edit a task.

    Crew can only update tasks directly assigned to them.
    Managers/admins can edit any task.
    """
    if user.get("is_manager"):
        return True

    # Crew can only edit tasks assigned directly to them
    return task.get("assigned_to_user_id") == user.get("id")
