"""
User Management API Client

Handles user CRUD operations for admin/manager users.
"""

from typing import Optional, List, Tuple

from .client import APIClient, APIResponse, get_api_client
from .auth_api import UserInfo


class UserAPI:
    """User management API client"""

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def list_users(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        crew_id: Optional[int] = None
    ) -> Tuple[List[UserInfo], Optional[str]]:
        """
        List all users (manager/admin only).

        Args:
            role: Filter by role (admin, manager, crew)
            is_active: Filter by active status
            crew_id: Filter by crew membership

        Returns:
            Tuple of (list of UserInfo, error_message)
        """
        params = {}
        if role:
            params["role"] = role
        if is_active is not None:
            params["is_active"] = str(is_active).lower()
        if crew_id:
            params["crew_id"] = crew_id

        response = self._client.get("/users", params=params if params else None)

        if not response.success:
            return [], response.error_message

        users = [UserInfo.from_dict(u) for u in response.data]
        return users, None

    def get_user(self, user_id: int) -> Tuple[Optional[UserInfo], Optional[str]]:
        """Get user by ID."""
        response = self._client.get(f"/users/{user_id}")

        if not response.success:
            return None, response.error_message

        return UserInfo.from_dict(response.data), None

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        role: str = "crew"
    ) -> Tuple[Optional[UserInfo], Optional[str]]:
        """
        Create a new user (admin only).

        Returns:
            Tuple of (created UserInfo, error_message)
        """
        data = {
            "username": username,
            "email": email,
            "password": password,
            "role": role
        }
        if first_name:
            data["first_name"] = first_name
        if last_name:
            data["last_name"] = last_name
        if phone:
            data["phone"] = phone

        response = self._client.post("/users", data=data)

        if not response.success:
            return None, response.error_message

        return UserInfo.from_dict(response.data), None

    def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[Optional[UserInfo], Optional[str]]:
        """
        Update a user (admin only).

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
        if role is not None:
            data["role"] = role
        if is_active is not None:
            data["is_active"] = is_active

        response = self._client.put(f"/users/{user_id}", data=data)

        if not response.success:
            return None, response.error_message

        return UserInfo.from_dict(response.data), None

    def deactivate_user(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Deactivate a user (admin only).

        Returns:
            Tuple of (success, error_message)
        """
        response = self._client.delete(f"/users/{user_id}")

        if not response.success:
            return False, response.error_message

        return True, None

    def reactivate_user(self, user_id: int) -> Tuple[Optional[UserInfo], Optional[str]]:
        """
        Reactivate a deactivated user.

        Returns:
            Tuple of (updated UserInfo, error_message)
        """
        return self.update_user(user_id, is_active=True)


# Singleton instance
_user_api: Optional[UserAPI] = None


def get_user_api() -> UserAPI:
    """Get or create the user API singleton."""
    global _user_api
    if _user_api is None:
        _user_api = UserAPI()
    return _user_api
