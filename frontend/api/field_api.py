"""
Field Management API Client

Handles field CRUD operations for the Farm Operations Manager.
AgTools v2.5.0 Phase 3
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any

from .client import APIClient, get_api_client


@dataclass
class FieldInfo:
    """Field information dataclass"""
    id: int
    name: str
    farm_name: Optional[str]
    acreage: float
    current_crop: Optional[str]
    soil_type: Optional[str]
    irrigation_type: Optional[str]
    location_lat: Optional[float]
    location_lng: Optional[float]
    boundary: Optional[str]
    notes: Optional[str]
    created_by_user_id: int
    created_by_user_name: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str
    total_operations: int
    last_operation_date: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "FieldInfo":
        """Create FieldInfo from API response dict."""
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            farm_name=data.get("farm_name"),
            acreage=float(data.get("acreage", 0)),
            current_crop=data.get("current_crop"),
            soil_type=data.get("soil_type"),
            irrigation_type=data.get("irrigation_type"),
            location_lat=data.get("location_lat"),
            location_lng=data.get("location_lng"),
            boundary=data.get("boundary"),
            notes=data.get("notes"),
            created_by_user_id=data.get("created_by_user_id", 0),
            created_by_user_name=data.get("created_by_user_name"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            total_operations=data.get("total_operations", 0),
            last_operation_date=data.get("last_operation_date")
        )

    @property
    def crop_display(self) -> str:
        """Get display-friendly crop text."""
        if not self.current_crop:
            return "Not set"
        return self.current_crop.replace("_", " ").title()

    @property
    def soil_display(self) -> str:
        """Get display-friendly soil type text."""
        if not self.soil_type:
            return "Not set"
        return self.soil_type.replace("_", " ").title()

    @property
    def irrigation_display(self) -> str:
        """Get display-friendly irrigation text."""
        if not self.irrigation_type or self.irrigation_type == "none":
            return "None"
        return self.irrigation_type.replace("_", " ").title()

    @property
    def farm_display(self) -> str:
        """Get display text for farm grouping."""
        return self.farm_name or "Unassigned"


@dataclass
class FieldSummary:
    """Summary statistics for all fields"""
    total_fields: int
    total_acreage: float
    fields_by_crop: Dict[str, Dict[str, Any]]
    fields_by_farm: Dict[str, Dict[str, Any]]

    @classmethod
    def from_dict(cls, data: dict) -> "FieldSummary":
        """Create FieldSummary from API response dict."""
        return cls(
            total_fields=data.get("total_fields", 0),
            total_acreage=float(data.get("total_acreage", 0)),
            fields_by_crop=data.get("fields_by_crop", {}),
            fields_by_farm=data.get("fields_by_farm", {})
        )


class FieldAPI:
    """Field management API client"""

    # Crop type options
    CROP_TYPES = [
        ("corn", "Corn"),
        ("soybean", "Soybean"),
        ("wheat", "Wheat"),
        ("cotton", "Cotton"),
        ("rice", "Rice"),
        ("sorghum", "Sorghum"),
        ("alfalfa", "Alfalfa"),
        ("hay", "Hay"),
        ("pasture", "Pasture"),
        ("fallow", "Fallow"),
        ("other", "Other"),
    ]

    # Soil type options
    SOIL_TYPES = [
        ("clay", "Clay"),
        ("clay_loam", "Clay Loam"),
        ("loam", "Loam"),
        ("sandy_loam", "Sandy Loam"),
        ("sandy", "Sandy"),
        ("silt_loam", "Silt Loam"),
        ("silty_clay", "Silty Clay"),
        ("organic", "Organic"),
        ("other", "Other"),
    ]

    # Irrigation type options
    IRRIGATION_TYPES = [
        ("none", "None"),
        ("center_pivot", "Center Pivot"),
        ("drip", "Drip"),
        ("flood", "Flood"),
        ("furrow", "Furrow"),
        ("sprinkler", "Sprinkler"),
        ("subsurface", "Subsurface"),
        ("other", "Other"),
    ]

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def list_fields(
        self,
        farm_name: Optional[str] = None,
        current_crop: Optional[str] = None,
        soil_type: Optional[str] = None,
        irrigation_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[FieldInfo], Optional[str]]:
        """
        List fields with filters.

        Args:
            farm_name: Filter by farm name
            current_crop: Filter by crop type
            soil_type: Filter by soil type
            irrigation_type: Filter by irrigation type
            search: Search by field or farm name

        Returns:
            Tuple of (list of FieldInfo, error_message)
        """
        params = {}
        if farm_name:
            params["farm_name"] = farm_name
        if current_crop:
            params["current_crop"] = current_crop
        if soil_type:
            params["soil_type"] = soil_type
        if irrigation_type:
            params["irrigation_type"] = irrigation_type
        if search:
            params["search"] = search

        response = self._client.get("/api/v1/fields", params=params if params else None)

        if not response.success:
            return [], response.error_message

        fields = [FieldInfo.from_dict(f) for f in response.data.get("fields", [])]
        return fields, None

    def get_field(self, field_id: int) -> Tuple[Optional[FieldInfo], Optional[str]]:
        """
        Get field by ID.

        Returns:
            Tuple of (FieldInfo, error_message)
        """
        response = self._client.get(f"/api/v1/fields/{field_id}")

        if not response.success:
            return None, response.error_message

        return FieldInfo.from_dict(response.data), None

    def create_field(
        self,
        name: str,
        acreage: float,
        farm_name: Optional[str] = None,
        current_crop: Optional[str] = None,
        soil_type: Optional[str] = None,
        irrigation_type: Optional[str] = None,
        location_lat: Optional[float] = None,
        location_lng: Optional[float] = None,
        boundary: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[Optional[FieldInfo], Optional[str]]:
        """
        Create a new field.

        Args:
            name: Field name (required)
            acreage: Field size in acres (required)
            farm_name: Farm grouping name
            current_crop: Current crop type
            soil_type: Soil type
            irrigation_type: Irrigation system type
            location_lat: Latitude of field center
            location_lng: Longitude of field center
            boundary: GeoJSON boundary string
            notes: Additional notes

        Returns:
            Tuple of (created FieldInfo, error_message)
        """
        data = {
            "name": name,
            "acreage": acreage
        }
        if farm_name:
            data["farm_name"] = farm_name
        if current_crop:
            data["current_crop"] = current_crop
        if soil_type:
            data["soil_type"] = soil_type
        if irrigation_type:
            data["irrigation_type"] = irrigation_type
        if location_lat is not None:
            data["location_lat"] = location_lat
        if location_lng is not None:
            data["location_lng"] = location_lng
        if boundary:
            data["boundary"] = boundary
        if notes:
            data["notes"] = notes

        response = self._client.post("/api/v1/fields", data=data)

        if not response.success:
            return None, response.error_message

        return FieldInfo.from_dict(response.data), None

    def update_field(
        self,
        field_id: int,
        name: Optional[str] = None,
        acreage: Optional[float] = None,
        farm_name: Optional[str] = None,
        current_crop: Optional[str] = None,
        soil_type: Optional[str] = None,
        irrigation_type: Optional[str] = None,
        location_lat: Optional[float] = None,
        location_lng: Optional[float] = None,
        boundary: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[Optional[FieldInfo], Optional[str]]:
        """
        Update a field.

        Returns:
            Tuple of (updated FieldInfo, error_message)
        """
        data = {}
        if name is not None:
            data["name"] = name
        if acreage is not None:
            data["acreage"] = acreage
        if farm_name is not None:
            data["farm_name"] = farm_name
        if current_crop is not None:
            data["current_crop"] = current_crop
        if soil_type is not None:
            data["soil_type"] = soil_type
        if irrigation_type is not None:
            data["irrigation_type"] = irrigation_type
        if location_lat is not None:
            data["location_lat"] = location_lat
        if location_lng is not None:
            data["location_lng"] = location_lng
        if boundary is not None:
            data["boundary"] = boundary
        if notes is not None:
            data["notes"] = notes

        response = self._client.put(f"/api/v1/fields/{field_id}", data=data)

        if not response.success:
            return None, response.error_message

        return FieldInfo.from_dict(response.data), None

    def delete_field(self, field_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete a field (soft delete).

        Returns:
            Tuple of (success, error_message)
        """
        response = self._client.delete(f"/api/v1/fields/{field_id}")

        if not response.success:
            return False, response.error_message

        return True, None

    def get_summary(self) -> Tuple[Optional[FieldSummary], Optional[str]]:
        """
        Get summary statistics for all fields.

        Returns:
            Tuple of (FieldSummary, error_message)
        """
        response = self._client.get("/api/v1/fields/summary")

        if not response.success:
            return None, response.error_message

        return FieldSummary.from_dict(response.data), None

    def get_farm_names(self) -> Tuple[List[str], Optional[str]]:
        """
        Get list of unique farm names.

        Returns:
            Tuple of (list of farm names, error_message)
        """
        response = self._client.get("/api/v1/fields/farms")

        if not response.success:
            return [], response.error_message

        return response.data.get("farms", []), None


# Singleton instance
_field_api: Optional[FieldAPI] = None


def get_field_api() -> FieldAPI:
    """Get or create the field API singleton."""
    global _field_api
    if _field_api is None:
        _field_api = FieldAPI()
    return _field_api
