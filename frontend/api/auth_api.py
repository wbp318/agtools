"""
Authentication API Client

Handles login, logout, token refresh, and user profile operations.
"""

from typing import Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .client import APIClient, APIResponse, get_api_client


@dataclass
class AuthToken:
    """Authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int  # seconds

    @classmethod
    def from_dict(cls, data: dict) -> "AuthToken":
        return cls(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            token_type=data.get("token_type", "bearer"),
            expires_in=data.get("expires_in", 86400)
        )


@dataclass
class UserInfo:
    """User information"""
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    role: str  # admin, manager, crew
    is_active: bool
    created_at: Optional[str]
    last_login: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "UserInfo":
        return cls(
            id=data.get("id", 0),
            username=data.get("username", ""),
            email=data.get("email", ""),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            phone=data.get("phone"),
            role=data.get("role", "crew"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            last_login=data.get("last_login")
        )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.username

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_manager(self) -> bool:
        return self.role in ["admin", "manager"]


@dataclass
class LoginResult:
    """Login operation result"""
    success: bool
    tokens: Optional[AuthToken] = None
    user: Optional[UserInfo] = None
    error: Optional[str] = None


class AuthAPI:
    """Authentication API client"""

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def login(self, username: str, password: str) -> LoginResult:
        """
        Authenticate user and get tokens.

        Args:
            username: Username or email
            password: Password

        Returns:
            LoginResult with tokens and user info if successful
        """
        response = self._client.post(
            "/auth/login",
            data={"username": username, "password": password}
        )

        if not response.success:
            return LoginResult(
                success=False,
                error=response.error_message or "Login failed"
            )

        data = response.data
        tokens = AuthToken.from_dict(data.get("tokens", {}))
        user = UserInfo.from_dict(data.get("user", {}))

        # Store token in client for subsequent requests
        self._client.set_auth_token(tokens.access_token)

        return LoginResult(
            success=True,
            tokens=tokens,
            user=user
        )

    def logout(self) -> bool:
        """
        Logout current user.

        Returns:
            True if successful
        """
        response = self._client.post("/auth/logout")
        self._client.clear_auth_token()
        return response.success

    def refresh_tokens(self, refresh_token: str) -> Tuple[Optional[AuthToken], Optional[str]]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (AuthToken, error_message)
        """
        response = self._client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token}
        )

        if not response.success:
            return None, response.error_message

        tokens = AuthToken.from_dict(response.data)
        self._client.set_auth_token(tokens.access_token)

        return tokens, None

    def get_current_user(self) -> Tuple[Optional[UserInfo], Optional[str]]:
        """
        Get current authenticated user's info.

        Returns:
            Tuple of (UserInfo, error_message)
        """
        response = self._client.get("/auth/me")

        if not response.success:
            return None, response.error_message

        return UserInfo.from_dict(response.data), None

    def update_profile(
        self,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Tuple[Optional[UserInfo], Optional[str]]:
        """
        Update current user's profile.

        Returns:
            Tuple of (updated UserInfo, error_message)
        """
        data = {}
        if email is not None:
            data["email"] = email
        if first_name is not None:
            data["first_name"] = first_name
        if last_name is not None:
            data["last_name"] = last_name
        if phone is not None:
            data["phone"] = phone

        response = self._client.put("/auth/me", data=data)

        if not response.success:
            return None, response.error_message

        return UserInfo.from_dict(response.data), None

    def change_password(
        self,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Change current user's password.

        Returns:
            Tuple of (success, error_message)
        """
        response = self._client.post(
            "/auth/change-password",
            data={
                "current_password": current_password,
                "new_password": new_password
            }
        )

        if not response.success:
            return False, response.error_message

        return True, None


# Singleton instance
_auth_api: Optional[AuthAPI] = None


def get_auth_api() -> AuthAPI:
    """Get or create the auth API singleton."""
    global _auth_api
    if _auth_api is None:
        _auth_api = AuthAPI()
    return _auth_api
