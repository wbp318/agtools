"""
Crew Management API Client

Handles crew/team CRUD operations.
"""

from typing import Optional, List, Tuple
from dataclasses import dataclass

from .client import APIClient, APIResponse, get_api_client


@dataclass
class CrewInfo:
    """Crew information"""
    id: int
    name: str
    description: Optional[str]
    manager_id: Optional[int]
    manager_name: Optional[str]
    is_active: bool
    created_at: Optional[str]
    member_count: int

    @classmethod
    def from_dict(cls, data: dict) -> "CrewInfo":
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            description=data.get("description"),
            manager_id=data.get("manager_id"),
            manager_name=data.get("manager_name"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            member_count=data.get("member_count", 0)
        )


@dataclass
class CrewMember:
    """Crew member information"""
    user_id: int
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    joined_at: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "CrewMember":
        return cls(
            user_id=data.get("user_id", 0),
            username=data.get("username", ""),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            role=data.get("role", "crew"),
            joined_at=data.get("joined_at")
        )

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.username


class CrewAPI:
    """Crew management API client"""

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def list_crews(self, is_active: Optional[bool] = None) -> Tuple[List[CrewInfo], Optional[str]]:
        """
        List all crews.

        Args:
            is_active: Filter by active status

        Returns:
            Tuple of (list of CrewInfo, error_message)
        """
        params = {}
        if is_active is not None:
            params["is_active"] = str(is_active).lower()

        response = self._client.get("/crews", params=params if params else None)

        if not response.success:
            return [], response.error_message

        crews = [CrewInfo.from_dict(c) for c in response.data]
        return crews, None

    def get_crew(self, crew_id: int) -> Tuple[Optional[CrewInfo], Optional[str]]:
        """Get crew by ID."""
        response = self._client.get(f"/crews/{crew_id}")

        if not response.success:
            return None, response.error_message

        return CrewInfo.from_dict(response.data), None

    def create_crew(
        self,
        name: str,
        description: Optional[str] = None,
        manager_id: Optional[int] = None
    ) -> Tuple[Optional[CrewInfo], Optional[str]]:
        """
        Create a new crew (admin only).

        Returns:
            Tuple of (created CrewInfo, error_message)
        """
        data = {"name": name}
        if description:
            data["description"] = description
        if manager_id:
            data["manager_id"] = manager_id

        response = self._client.post("/crews", data=data)

        if not response.success:
            return None, response.error_message

        return CrewInfo.from_dict(response.data), None

    def update_crew(
        self,
        crew_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        manager_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[Optional[CrewInfo], Optional[str]]:
        """
        Update a crew (admin only).

        Returns:
            Tuple of (updated CrewInfo, error_message)
        """
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if manager_id is not None:
            data["manager_id"] = manager_id
        if is_active is not None:
            data["is_active"] = is_active

        response = self._client.put(f"/crews/{crew_id}", data=data)

        if not response.success:
            return None, response.error_message

        return CrewInfo.from_dict(response.data), None

    def get_crew_members(self, crew_id: int) -> Tuple[List[CrewMember], Optional[str]]:
        """Get all members of a crew."""
        response = self._client.get(f"/crews/{crew_id}/members")

        if not response.success:
            return [], response.error_message

        members = [CrewMember.from_dict(m) for m in response.data]
        return members, None

    def add_crew_member(self, crew_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """Add a user to a crew (manager/admin only)."""
        response = self._client.post(f"/crews/{crew_id}/members/{user_id}")

        if not response.success:
            return False, response.error_message

        return True, None

    def remove_crew_member(self, crew_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """Remove a user from a crew (manager/admin only)."""
        response = self._client.delete(f"/crews/{crew_id}/members/{user_id}")

        if not response.success:
            return False, response.error_message

        return True, None

    def get_user_crews(self, user_id: int) -> Tuple[List[CrewInfo], Optional[str]]:
        """Get all crews a user belongs to."""
        response = self._client.get(f"/users/{user_id}/crews")

        if not response.success:
            return [], response.error_message

        crews = [CrewInfo.from_dict(c) for c in response.data]
        return crews, None


# Singleton instance
_crew_api: Optional[CrewAPI] = None


def get_crew_api() -> CrewAPI:
    """Get or create the crew API singleton."""
    global _crew_api
    if _crew_api is None:
        _crew_api = CrewAPI()
    return _crew_api
