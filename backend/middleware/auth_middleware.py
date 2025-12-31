"""
Authentication Middleware for FastAPI
Provides dependency injection for protected routes.

AgTools v2.5.0
"""

import os
from typing import Optional, List
from functools import wraps

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from services.auth_service import (
    AuthService,
    TokenData,
    UserRole,
    get_auth_service
)
from services.user_service import UserService, UserResponse, get_user_service

# Dev mode for local desktop app - bypasses auth for testing
# SECURITY: Defaults to DISABLED. Set AGTOOLS_DEV_MODE=1 to enable (local dev only!)
DEV_MODE = os.environ.get("AGTOOLS_DEV_MODE", "0") == "1"


# ============================================================================
# SECURITY SCHEME
# ============================================================================

# Use Bearer token authentication
security = HTTPBearer(auto_error=False)


# ============================================================================
# AUTHENTICATED USER MODEL
# ============================================================================

class AuthenticatedUser(BaseModel):
    """Represents the currently authenticated user."""
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: UserRole
    is_active: bool

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.username

    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN

    @property
    def is_manager(self) -> bool:
        """Check if user is manager or admin."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]

    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role."""
        return self.role == role

    def has_any_role(self, roles: List[UserRole]) -> bool:
        """Check if user has any of the specified roles."""
        return self.role in roles


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthenticatedUser]:
    """
    Get current user from JWT token.
    Returns None if no valid token provided (for optional auth).

    Usage:
        @app.get("/items")
        async def get_items(user: Optional[AuthenticatedUser] = Depends(get_current_user)):
            if user:
                # Authenticated request
            else:
                # Anonymous request
    """
    if not credentials:
        return None

    auth_service = get_auth_service()
    token_data = auth_service.validate_access_token(credentials.credentials)

    if not token_data:
        return None

    # Get full user info from database
    user_service = get_user_service()
    user = user_service.get_user_by_id(token_data.user_id)

    if not user:
        return None

    return AuthenticatedUser(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=user.is_active
    )


async def get_current_active_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthenticatedUser:
    """
    Get current active user - raises 401 if not authenticated.
    In DEV_MODE, returns a default dev user for local desktop use.

    Usage:
        @app.get("/protected")
        async def protected_route(user: AuthenticatedUser = Depends(get_current_active_user)):
            return {"user": user.username}
    """
    # In dev mode, return a dev user for local desktop app
    if DEV_MODE and not credentials:
        return AuthenticatedUser(
            id=1,
            username="dev_user",
            email="dev@agtools.local",
            first_name="Dev",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=True
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    auth_service = get_auth_service()
    token_data = auth_service.validate_access_token(credentials.credentials)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Get full user info from database
    user_service = get_user_service()
    user = user_service.get_user_by_id(token_data.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    return AuthenticatedUser(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=user.is_active
    )


def require_role(allowed_roles: List[UserRole]):
    """
    Dependency factory for role-based access control.

    Usage:
        @app.post("/admin-only")
        async def admin_route(
            user: AuthenticatedUser = Depends(require_role([UserRole.ADMIN]))
        ):
            return {"admin": user.username}
    """
    async def role_checker(
        user: AuthenticatedUser = Depends(get_current_active_user)
    ) -> AuthenticatedUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(r.value for r in allowed_roles)}"
            )
        return user

    return role_checker


async def require_admin(
    user: AuthenticatedUser = Depends(get_current_active_user)
) -> AuthenticatedUser:
    """
    Require admin role.

    Usage:
        @app.delete("/users/{id}")
        async def delete_user(id: int, admin: AuthenticatedUser = Depends(require_admin)):
            ...
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


async def require_manager(
    user: AuthenticatedUser = Depends(get_current_active_user)
) -> AuthenticatedUser:
    """
    Require manager or admin role.

    Usage:
        @app.post("/tasks")
        async def create_task(manager: AuthenticatedUser = Depends(require_manager)):
            ...
    """
    if user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required"
        )
    return user


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_client_ip(request: Request) -> Optional[str]:
    """Get client IP address from request."""
    # Check for forwarded header (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to client host
    if request.client:
        return request.client.host

    return None


def get_user_agent(request: Request) -> Optional[str]:
    """Get user agent from request."""
    return request.headers.get("User-Agent")
