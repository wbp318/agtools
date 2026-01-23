"""
Authentication, Users, and Crews Router
AgTools v6.13.2

Handles:
- Authentication endpoints (login, logout, refresh, password change)
- User management (admin/manager operations)
- Crew management
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from middleware.auth_middleware import (
    get_current_active_user,
    require_admin,
    require_manager,
    AuthenticatedUser,
    get_client_ip,
    get_user_agent
)
from middleware.rate_limiter import limiter, RATE_STRICT
from services.auth_service import (
    UserRole,
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
    LoginRequest,
    PasswordChange
)
from services.user_service import (
    get_user_service,
    CrewCreate,
    CrewUpdate,
    CrewResponse,
    CrewMemberResponse
)

router = APIRouter(prefix="/api/v1", tags=["Authentication"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class LoginResponse(BaseModel):
    """Login response with tokens and user info"""
    tokens: Token
    user: UserResponse


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/auth/login", response_model=LoginResponse, tags=["Authentication"])
@limiter.limit(RATE_STRICT)
async def login(request: Request, login_data: LoginRequest):
    """
    Authenticate user and return JWT tokens.

    Returns access_token (24h) and refresh_token (7d).
    Rate limited to 5 attempts per minute per IP.
    """
    user_service = get_user_service()

    tokens, user, error = user_service.authenticate(
        username=login_data.username,
        password=login_data.password,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )

    if error:
        raise HTTPException(
            status_code=401,
            detail=error
        )

    return LoginResponse(tokens=tokens, user=user)


@router.post("/auth/logout", tags=["Authentication"])
async def logout(
    request: Request,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Logout current user and invalidate session."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    user_service = get_user_service()
    user_service.logout(token, user.id, get_client_ip(request))

    return {"message": "Logged out successfully"}


@router.post("/auth/refresh", response_model=Token, tags=["Authentication"])
async def refresh_tokens(refresh_token: str):
    """Get new access token using refresh token."""
    user_service = get_user_service()

    tokens, error = user_service.refresh_tokens(refresh_token)

    if error:
        raise HTTPException(status_code=401, detail=error)

    return tokens


@router.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(user: AuthenticatedUser = Depends(get_current_active_user)):
    """Get current authenticated user's info."""
    user_service = get_user_service()
    return user_service.get_user_by_id(user.id)


@router.put("/auth/me", response_model=UserResponse, tags=["Authentication"])
async def update_current_user(
    user_data: UserUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update current user's profile (non-admin fields only)."""
    safe_update = UserUpdate(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone
    )

    user_service = get_user_service()
    updated_user, error = user_service.update_user(user.id, safe_update, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return updated_user


@router.post("/auth/change-password", tags=["Authentication"])
@limiter.limit(RATE_STRICT)
async def change_password(
    request: Request,
    password_data: PasswordChange,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Change current user's password. Rate limited to 3 attempts per minute."""
    user_service = get_user_service()

    success, error = user_service.change_password(
        user_id=user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {"message": "Password changed successfully. Please login again."}


# ============================================================================
# USER MANAGEMENT ENDPOINTS (Admin/Manager)
# ============================================================================

@router.get("/users", response_model=List[UserResponse], tags=["Users"])
async def list_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    crew_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(require_manager)
):
    """List all users (manager/admin only)."""
    user_service = get_user_service()
    return user_service.list_users(role=role, is_active=is_active, crew_id=crew_id)


@router.post("/users", response_model=UserResponse, tags=["Users"])
async def create_user(
    user_data: UserCreate,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """Create a new user (admin only)."""
    user_service = get_user_service()

    new_user, error = user_service.create_user(user_data, admin.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return new_user


@router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(
    user_id: int,
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """Get user by ID (manager/admin only)."""
    user_service = get_user_service()
    user = user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.put("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """Update a user (admin only)."""
    user_service = get_user_service()

    updated_user, error = user_service.update_user(user_id, user_data, admin.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return updated_user


@router.delete("/users/{user_id}", tags=["Users"])
async def deactivate_user(
    user_id: int,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """Deactivate a user (admin only). Soft delete - can be reactivated."""
    user_service = get_user_service()

    success, error = user_service.delete_user(user_id, admin.id)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {"message": "User deactivated successfully"}


# ============================================================================
# CREW MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/crews", response_model=List[CrewResponse], tags=["Crews"])
async def list_crews(
    is_active: Optional[bool] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List all crews."""
    user_service = get_user_service()
    return user_service.list_crews(is_active=is_active)


@router.post("/crews", response_model=CrewResponse, tags=["Crews"])
async def create_crew(
    crew_data: CrewCreate,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """Create a new crew (admin only)."""
    user_service = get_user_service()

    crew, error = user_service.create_crew(crew_data, admin.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return crew


@router.get("/crews/{crew_id}", response_model=CrewResponse, tags=["Crews"])
async def get_crew(
    crew_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get crew by ID."""
    user_service = get_user_service()
    crew = user_service.get_crew_by_id(crew_id)

    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")

    return crew


@router.put("/crews/{crew_id}", response_model=CrewResponse, tags=["Crews"])
async def update_crew(
    crew_id: int,
    crew_data: CrewUpdate,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """Update a crew (admin only)."""
    user_service = get_user_service()

    crew, error = user_service.update_crew(crew_id, crew_data, admin.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")

    return crew


@router.get("/crews/{crew_id}/members", response_model=List[CrewMemberResponse], tags=["Crews"])
async def get_crew_members(
    crew_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get all members of a crew."""
    user_service = get_user_service()
    return user_service.get_crew_members(crew_id)


@router.post("/crews/{crew_id}/members/{user_id}", tags=["Crews"])
async def add_crew_member(
    crew_id: int,
    user_id: int,
    manager: AuthenticatedUser = Depends(require_manager)
):
    """Add a user to a crew (manager/admin only)."""
    user_service = get_user_service()

    success, error = user_service.add_crew_member(crew_id, user_id, manager.id)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {"message": "Member added successfully"}


@router.delete("/crews/{crew_id}/members/{user_id}", tags=["Crews"])
async def remove_crew_member(
    crew_id: int,
    user_id: int,
    manager: AuthenticatedUser = Depends(require_manager)
):
    """Remove a user from a crew (manager/admin only)."""
    user_service = get_user_service()

    success, error = user_service.remove_crew_member(crew_id, user_id, manager.id)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {"message": "Member removed successfully"}


@router.get("/users/{user_id}/crews", response_model=List[CrewResponse], tags=["Crews"])
async def get_user_crews(
    user_id: int,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get all crews a user belongs to."""
    if user_id != current_user.id and not current_user.is_manager:
        raise HTTPException(status_code=403, detail="Access denied")

    user_service = get_user_service()
    return user_service.get_user_crews(user_id)
