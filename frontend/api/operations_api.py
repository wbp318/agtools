"""
Field Operations API Client

Handles operation logging for the Farm Operations Manager.
AgTools v2.5.0 Phase 3
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any

from .client import APIClient, get_api_client


@dataclass
class OperationInfo:
    """Field operation information dataclass"""
    id: int
    field_id: int
    field_name: str
    farm_name: Optional[str]
    operation_type: str
    operation_date: str
    product_name: Optional[str]
    rate: Optional[float]
    rate_unit: Optional[str]
    quantity: Optional[float]
    quantity_unit: Optional[str]
    acres_covered: Optional[float]
    product_cost: Optional[float]
    application_cost: Optional[float]
    total_cost: Optional[float]
    yield_amount: Optional[float]
    yield_unit: Optional[str]
    moisture_percent: Optional[float]
    weather_temp: Optional[float]
    weather_wind: Optional[float]
    weather_humidity: Optional[float]
    weather_notes: Optional[str]
    operator_id: Optional[int]
    operator_name: Optional[str]
    task_id: Optional[int]
    notes: Optional[str]
    created_by_user_id: int
    created_by_user_name: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "OperationInfo":
        """Create OperationInfo from API response dict."""
        return cls(
            id=data.get("id", 0),
            field_id=data.get("field_id", 0),
            field_name=data.get("field_name", ""),
            farm_name=data.get("farm_name"),
            operation_type=data.get("operation_type", ""),
            operation_date=data.get("operation_date", ""),
            product_name=data.get("product_name"),
            rate=data.get("rate"),
            rate_unit=data.get("rate_unit"),
            quantity=data.get("quantity"),
            quantity_unit=data.get("quantity_unit"),
            acres_covered=data.get("acres_covered"),
            product_cost=data.get("product_cost"),
            application_cost=data.get("application_cost"),
            total_cost=data.get("total_cost"),
            yield_amount=data.get("yield_amount"),
            yield_unit=data.get("yield_unit"),
            moisture_percent=data.get("moisture_percent"),
            weather_temp=data.get("weather_temp"),
            weather_wind=data.get("weather_wind"),
            weather_humidity=data.get("weather_humidity"),
            weather_notes=data.get("weather_notes"),
            operator_id=data.get("operator_id"),
            operator_name=data.get("operator_name"),
            task_id=data.get("task_id"),
            notes=data.get("notes"),
            created_by_user_id=data.get("created_by_user_id", 0),
            created_by_user_name=data.get("created_by_user_name"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )

    @property
    def operation_type_display(self) -> str:
        """Get display-friendly operation type text."""
        type_map = {
            "spray": "Spray Application",
            "fertilizer": "Fertilizer",
            "planting": "Planting",
            "harvest": "Harvest",
            "tillage": "Tillage",
            "scouting": "Scouting",
            "irrigation": "Irrigation",
            "seed_treatment": "Seed Treatment",
            "cover_crop": "Cover Crop",
            "other": "Other"
        }
        return type_map.get(self.operation_type, self.operation_type.replace("_", " ").title())

    @property
    def rate_display(self) -> str:
        """Get formatted rate display."""
        if self.rate is None:
            return "-"
        unit = self.rate_unit or ""
        return f"{self.rate:.2f} {unit}".strip()

    @property
    def cost_display(self) -> str:
        """Get formatted cost display."""
        if self.total_cost is None:
            return "-"
        return f"${self.total_cost:,.2f}"

    @property
    def yield_display(self) -> str:
        """Get formatted yield display for harvest operations."""
        if self.yield_amount is None:
            return "-"
        unit = self.yield_unit or "bu/acre"
        return f"{self.yield_amount:.1f} {unit}"

    @property
    def operator_display(self) -> str:
        """Get display text for operator."""
        return self.operator_name or "Not specified"


@dataclass
class OperationsSummary:
    """Summary statistics for operations"""
    total_operations: int
    operations_by_type: Dict[str, int]
    total_cost: float
    cost_by_type: Dict[str, float]
    date_range: Dict[str, Optional[str]]

    @classmethod
    def from_dict(cls, data: dict) -> "OperationsSummary":
        """Create OperationsSummary from API response dict."""
        return cls(
            total_operations=data.get("total_operations", 0),
            operations_by_type=data.get("operations_by_type", {}),
            total_cost=float(data.get("total_cost", 0)),
            cost_by_type=data.get("cost_by_type", {}),
            date_range=data.get("date_range", {})
        )


@dataclass
class FieldOperationHistory:
    """Complete operation history for a field"""
    field_id: int
    field_name: str
    farm_name: Optional[str]
    acreage: float
    operations: List[OperationInfo]
    summary: OperationsSummary

    @classmethod
    def from_dict(cls, data: dict) -> "FieldOperationHistory":
        """Create FieldOperationHistory from API response dict."""
        return cls(
            field_id=data.get("field_id", 0),
            field_name=data.get("field_name", ""),
            farm_name=data.get("farm_name"),
            acreage=float(data.get("acreage", 0)),
            operations=[OperationInfo.from_dict(op) for op in data.get("operations", [])],
            summary=OperationsSummary.from_dict(data.get("summary", {}))
        )


class OperationsAPI:
    """Field operations API client"""

    # Operation type options
    OPERATION_TYPES = [
        ("spray", "Spray Application"),
        ("fertilizer", "Fertilizer"),
        ("planting", "Planting"),
        ("harvest", "Harvest"),
        ("tillage", "Tillage"),
        ("scouting", "Scouting"),
        ("irrigation", "Irrigation"),
        ("seed_treatment", "Seed Treatment"),
        ("cover_crop", "Cover Crop"),
        ("other", "Other"),
    ]

    # Common rate units
    RATE_UNITS = [
        "oz/acre",
        "lb/acre",
        "gal/acre",
        "qt/acre",
        "pt/acre",
        "fl oz/acre",
        "seeds/acre",
        "units/acre",
        "in/acre",  # irrigation
    ]

    # Common quantity units
    QUANTITY_UNITS = [
        "gallons",
        "pounds",
        "tons",
        "bushels",
        "bags",
        "units",
        "acres",
        "acre-inches",
    ]

    # Yield units
    YIELD_UNITS = [
        "bu/acre",
        "tons/acre",
        "bales/acre",
    ]

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def list_operations(
        self,
        field_id: Optional[int] = None,
        operation_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        operator_id: Optional[int] = None,
        farm_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[OperationInfo], Optional[str]]:
        """
        List operations with filters.

        Args:
            field_id: Filter by field
            operation_type: Filter by operation type
            date_from: Filter operations on or after this date (YYYY-MM-DD)
            date_to: Filter operations on or before this date (YYYY-MM-DD)
            operator_id: Filter by operator
            farm_name: Filter by farm name
            limit: Max results to return
            offset: Results offset for pagination

        Returns:
            Tuple of (list of OperationInfo, error_message)
        """
        params = {"limit": limit, "offset": offset}
        if field_id:
            params["field_id"] = field_id
        if operation_type:
            params["operation_type"] = operation_type
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if operator_id:
            params["operator_id"] = operator_id
        if farm_name:
            params["farm_name"] = farm_name

        response = self._client.get("/api/v1/operations", params=params)

        if not response.success:
            return [], response.error_message

        operations = [OperationInfo.from_dict(op) for op in response.data.get("operations", [])]
        return operations, None

    def get_operation(self, operation_id: int) -> Tuple[Optional[OperationInfo], Optional[str]]:
        """
        Get operation by ID.

        Returns:
            Tuple of (OperationInfo, error_message)
        """
        response = self._client.get(f"/api/v1/operations/{operation_id}")

        if not response.success:
            return None, response.error_message

        return OperationInfo.from_dict(response.data), None

    def create_operation(
        self,
        field_id: int,
        operation_type: str,
        operation_date: str,
        product_name: Optional[str] = None,
        rate: Optional[float] = None,
        rate_unit: Optional[str] = None,
        quantity: Optional[float] = None,
        quantity_unit: Optional[str] = None,
        acres_covered: Optional[float] = None,
        product_cost: Optional[float] = None,
        application_cost: Optional[float] = None,
        total_cost: Optional[float] = None,
        yield_amount: Optional[float] = None,
        yield_unit: Optional[str] = None,
        moisture_percent: Optional[float] = None,
        weather_temp: Optional[float] = None,
        weather_wind: Optional[float] = None,
        weather_humidity: Optional[float] = None,
        weather_notes: Optional[str] = None,
        operator_id: Optional[int] = None,
        task_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Tuple[Optional[OperationInfo], Optional[str]]:
        """
        Create a new field operation.

        Args:
            field_id: Field ID (required)
            operation_type: Type of operation (required)
            operation_date: Date of operation YYYY-MM-DD (required)
            ... (other optional fields)

        Returns:
            Tuple of (created OperationInfo, error_message)
        """
        data = {
            "field_id": field_id,
            "operation_type": operation_type,
            "operation_date": operation_date
        }

        # Add optional fields if provided
        if product_name:
            data["product_name"] = product_name
        if rate is not None:
            data["rate"] = rate
        if rate_unit:
            data["rate_unit"] = rate_unit
        if quantity is not None:
            data["quantity"] = quantity
        if quantity_unit:
            data["quantity_unit"] = quantity_unit
        if acres_covered is not None:
            data["acres_covered"] = acres_covered
        if product_cost is not None:
            data["product_cost"] = product_cost
        if application_cost is not None:
            data["application_cost"] = application_cost
        if total_cost is not None:
            data["total_cost"] = total_cost
        if yield_amount is not None:
            data["yield_amount"] = yield_amount
        if yield_unit:
            data["yield_unit"] = yield_unit
        if moisture_percent is not None:
            data["moisture_percent"] = moisture_percent
        if weather_temp is not None:
            data["weather_temp"] = weather_temp
        if weather_wind is not None:
            data["weather_wind"] = weather_wind
        if weather_humidity is not None:
            data["weather_humidity"] = weather_humidity
        if weather_notes:
            data["weather_notes"] = weather_notes
        if operator_id:
            data["operator_id"] = operator_id
        if task_id:
            data["task_id"] = task_id
        if notes:
            data["notes"] = notes

        response = self._client.post("/api/v1/operations", data=data)

        if not response.success:
            return None, response.error_message

        return OperationInfo.from_dict(response.data), None

    def update_operation(
        self,
        operation_id: int,
        **kwargs
    ) -> Tuple[Optional[OperationInfo], Optional[str]]:
        """
        Update an operation.

        Args:
            operation_id: Operation ID
            **kwargs: Fields to update

        Returns:
            Tuple of (updated OperationInfo, error_message)
        """
        data = {k: v for k, v in kwargs.items() if v is not None}

        response = self._client.put(f"/api/v1/operations/{operation_id}", data=data)

        if not response.success:
            return None, response.error_message

        return OperationInfo.from_dict(response.data), None

    def delete_operation(self, operation_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete an operation (soft delete).

        Returns:
            Tuple of (success, error_message)
        """
        response = self._client.delete(f"/api/v1/operations/{operation_id}")

        if not response.success:
            return False, response.error_message

        return True, None

    def get_summary(
        self,
        field_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Tuple[Optional[OperationsSummary], Optional[str]]:
        """
        Get summary statistics for operations.

        Returns:
            Tuple of (OperationsSummary, error_message)
        """
        params = {}
        if field_id:
            params["field_id"] = field_id
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = self._client.get("/api/v1/operations/summary", params=params if params else None)

        if not response.success:
            return None, response.error_message

        return OperationsSummary.from_dict(response.data), None

    def get_field_history(self, field_id: int) -> Tuple[Optional[FieldOperationHistory], Optional[str]]:
        """
        Get complete operation history for a field.

        Returns:
            Tuple of (FieldOperationHistory, error_message)
        """
        response = self._client.get(f"/api/v1/fields/{field_id}/operations")

        if not response.success:
            return None, response.error_message

        return FieldOperationHistory.from_dict(response.data), None


# Singleton instance
_operations_api: Optional[OperationsAPI] = None


def get_operations_api() -> OperationsAPI:
    """Get or create the operations API singleton."""
    global _operations_api
    if _operations_api is None:
        _operations_api = OperationsAPI()
    return _operations_api
