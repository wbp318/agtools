"""
Equipment Management API Client

Handles equipment fleet management, maintenance, and usage tracking.
AgTools v2.5.0 Phase 4
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict

from .client import APIClient, get_api_client


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class EquipmentInfo:
    """Equipment information dataclass"""
    id: int
    name: str
    equipment_type: str
    make: Optional[str]
    model: Optional[str]
    year: Optional[int]
    serial_number: Optional[str]
    purchase_date: Optional[str]
    purchase_cost: Optional[float]
    current_value: Optional[float]
    hourly_rate: Optional[float]
    current_hours: float
    status: str
    current_location: Optional[str]
    notes: Optional[str]
    created_by_user_id: int
    created_by_user_name: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "EquipmentInfo":
        """Create EquipmentInfo from API response dict."""
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            equipment_type=data.get("equipment_type", "other"),
            make=data.get("make"),
            model=data.get("model"),
            year=data.get("year"),
            serial_number=data.get("serial_number"),
            purchase_date=data.get("purchase_date"),
            purchase_cost=data.get("purchase_cost"),
            current_value=data.get("current_value"),
            hourly_rate=data.get("hourly_rate"),
            current_hours=float(data.get("current_hours", 0)),
            status=data.get("status", "available"),
            current_location=data.get("current_location"),
            notes=data.get("notes"),
            created_by_user_id=data.get("created_by_user_id", 0),
            created_by_user_name=data.get("created_by_user_name"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )

    @property
    def type_display(self) -> str:
        """Get display-friendly equipment type."""
        return self.equipment_type.replace("_", " ").title()

    @property
    def status_display(self) -> str:
        """Get display-friendly status."""
        return self.status.replace("_", " ").title()

    @property
    def make_model_display(self) -> str:
        """Get combined make/model display."""
        parts = []
        if self.make:
            parts.append(self.make)
        if self.model:
            parts.append(self.model)
        if self.year:
            parts.append(f"({self.year})")
        return " ".join(parts) if parts else "Unknown"

    @property
    def value_display(self) -> str:
        """Get formatted value display."""
        if self.current_value:
            return f"${self.current_value:,.0f}"
        return "N/A"

    @property
    def hours_display(self) -> str:
        """Get formatted hours display."""
        return f"{self.current_hours:,.1f} hrs"

    @property
    def hourly_rate_display(self) -> str:
        """Get formatted hourly rate display."""
        if self.hourly_rate:
            return f"${self.hourly_rate:.2f}/hr"
        return "N/A"


@dataclass
class MaintenanceInfo:
    """Maintenance record information"""
    id: int
    equipment_id: int
    equipment_name: Optional[str]
    maintenance_type: str
    service_date: str
    next_service_date: Optional[str]
    next_service_hours: Optional[float]
    cost: Optional[float]
    performed_by: Optional[str]
    vendor: Optional[str]
    description: Optional[str]
    parts_used: Optional[str]
    created_by_user_id: int
    created_by_user_name: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "MaintenanceInfo":
        """Create MaintenanceInfo from API response dict."""
        return cls(
            id=data.get("id", 0),
            equipment_id=data.get("equipment_id", 0),
            equipment_name=data.get("equipment_name"),
            maintenance_type=data.get("maintenance_type", "other"),
            service_date=data.get("service_date", ""),
            next_service_date=data.get("next_service_date"),
            next_service_hours=data.get("next_service_hours"),
            cost=data.get("cost"),
            performed_by=data.get("performed_by"),
            vendor=data.get("vendor"),
            description=data.get("description"),
            parts_used=data.get("parts_used"),
            created_by_user_id=data.get("created_by_user_id", 0),
            created_by_user_name=data.get("created_by_user_name"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )

    @property
    def type_display(self) -> str:
        """Get display-friendly maintenance type."""
        return self.maintenance_type.replace("_", " ").title()

    @property
    def cost_display(self) -> str:
        """Get formatted cost display."""
        if self.cost:
            return f"${self.cost:,.2f}"
        return "N/A"


@dataclass
class MaintenanceAlert:
    """Maintenance alert information"""
    equipment_id: int
    equipment_name: str
    equipment_type: str
    maintenance_type: str
    last_service_date: Optional[str]
    next_service_date: Optional[str]
    next_service_hours: Optional[float]
    current_hours: float
    hours_until_service: Optional[float]
    days_until_service: Optional[int]
    urgency: str  # overdue, due_soon, upcoming

    @classmethod
    def from_dict(cls, data: dict) -> "MaintenanceAlert":
        """Create MaintenanceAlert from API response dict."""
        return cls(
            equipment_id=data.get("equipment_id", 0),
            equipment_name=data.get("equipment_name", ""),
            equipment_type=data.get("equipment_type", "other"),
            maintenance_type=data.get("maintenance_type", "other"),
            last_service_date=data.get("last_service_date"),
            next_service_date=data.get("next_service_date"),
            next_service_hours=data.get("next_service_hours"),
            current_hours=float(data.get("current_hours", 0)),
            hours_until_service=data.get("hours_until_service"),
            days_until_service=data.get("days_until_service"),
            urgency=data.get("urgency", "upcoming")
        )

    @property
    def urgency_display(self) -> str:
        """Get display-friendly urgency."""
        return self.urgency.replace("_", " ").title()

    @property
    def due_display(self) -> str:
        """Get due date/hours display."""
        if self.days_until_service is not None:
            if self.days_until_service < 0:
                return f"Overdue by {abs(self.days_until_service)} days"
            elif self.days_until_service == 0:
                return "Due today"
            else:
                return f"Due in {self.days_until_service} days"
        elif self.hours_until_service is not None:
            if self.hours_until_service < 0:
                return f"Overdue by {abs(self.hours_until_service):.0f} hours"
            else:
                return f"Due in {self.hours_until_service:.0f} hours"
        return "Unknown"


@dataclass
class EquipmentUsage:
    """Equipment usage record"""
    id: int
    equipment_id: int
    equipment_name: Optional[str]
    field_operation_id: Optional[int]
    usage_date: str
    hours_used: Optional[float]
    starting_hours: Optional[float]
    ending_hours: Optional[float]
    fuel_used: Optional[float]
    fuel_unit: Optional[str]
    operator_id: Optional[int]
    operator_name: Optional[str]
    notes: Optional[str]
    created_by_user_id: int
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "EquipmentUsage":
        """Create EquipmentUsage from API response dict."""
        return cls(
            id=data.get("id", 0),
            equipment_id=data.get("equipment_id", 0),
            equipment_name=data.get("equipment_name"),
            field_operation_id=data.get("field_operation_id"),
            usage_date=data.get("usage_date", ""),
            hours_used=data.get("hours_used"),
            starting_hours=data.get("starting_hours"),
            ending_hours=data.get("ending_hours"),
            fuel_used=data.get("fuel_used"),
            fuel_unit=data.get("fuel_unit", "gallons"),
            operator_id=data.get("operator_id"),
            operator_name=data.get("operator_name"),
            notes=data.get("notes"),
            created_by_user_id=data.get("created_by_user_id", 0),
            created_at=data.get("created_at", "")
        )

    @property
    def hours_display(self) -> str:
        """Get formatted hours display."""
        if self.hours_used:
            return f"{self.hours_used:.1f} hrs"
        return "N/A"

    @property
    def fuel_display(self) -> str:
        """Get formatted fuel display."""
        if self.fuel_used:
            return f"{self.fuel_used:.1f} {self.fuel_unit or 'gal'}"
        return "N/A"


@dataclass
class EquipmentSummary:
    """Equipment fleet summary statistics"""
    total_equipment: int
    equipment_by_type: Dict[str, int]
    equipment_by_status: Dict[str, int]
    total_value: float
    total_hours: float
    in_maintenance: int

    @classmethod
    def from_dict(cls, data: dict) -> "EquipmentSummary":
        """Create EquipmentSummary from API response dict."""
        return cls(
            total_equipment=data.get("total_equipment", 0),
            equipment_by_type=data.get("equipment_by_type", {}),
            equipment_by_status=data.get("equipment_by_status", {}),
            total_value=float(data.get("total_value", 0)),
            total_hours=float(data.get("total_hours", 0)),
            in_maintenance=data.get("in_maintenance", 0)
        )


# ============================================================================
# API CLIENT
# ============================================================================

class EquipmentAPI:
    """Equipment management API client"""

    # Equipment type options
    EQUIPMENT_TYPES = [
        ("tractor", "Tractor"),
        ("combine", "Combine"),
        ("sprayer", "Sprayer"),
        ("planter", "Planter"),
        ("tillage", "Tillage"),
        ("truck", "Truck"),
        ("atv", "ATV"),
        ("grain_cart", "Grain Cart"),
        ("wagon", "Wagon"),
        ("mower", "Mower"),
        ("baler", "Baler"),
        ("loader", "Loader"),
        ("drill", "Drill"),
        ("applicator", "Applicator"),
        ("other", "Other"),
    ]

    # Equipment status options
    EQUIPMENT_STATUSES = [
        ("available", "Available"),
        ("in_use", "In Use"),
        ("maintenance", "Maintenance"),
        ("retired", "Retired"),
    ]

    # Maintenance type options
    MAINTENANCE_TYPES = [
        ("oil_change", "Oil Change"),
        ("filter", "Filter"),
        ("repairs", "Repairs"),
        ("inspection", "Inspection"),
        ("tires", "Tires"),
        ("brakes", "Brakes"),
        ("hydraulics", "Hydraulics"),
        ("electrical", "Electrical"),
        ("winterization", "Winterization"),
        ("calibration", "Calibration"),
        ("greasing", "Greasing"),
        ("other", "Other"),
    ]

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    # ========================================================================
    # EQUIPMENT CRUD
    # ========================================================================

    def list_equipment(
        self,
        equipment_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[EquipmentInfo], Optional[str]]:
        """List equipment with optional filters."""
        params = {"limit": limit, "offset": offset}
        if equipment_type:
            params["equipment_type"] = equipment_type
        if status:
            params["status"] = status
        if search:
            params["search"] = search

        response = self._client.get("/equipment", params=params)
        if not response.success:
            return [], response.error_message

        return [EquipmentInfo.from_dict(e) for e in response.data], None

    def get_equipment(self, equipment_id: int) -> Tuple[Optional[EquipmentInfo], Optional[str]]:
        """Get equipment by ID."""
        response = self._client.get(f"/equipment/{equipment_id}")
        if not response.success:
            return None, response.error_message

        return EquipmentInfo.from_dict(response.data), None

    def create_equipment(
        self,
        name: str,
        equipment_type: str,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        serial_number: Optional[str] = None,
        purchase_date: Optional[str] = None,
        purchase_cost: Optional[float] = None,
        current_value: Optional[float] = None,
        hourly_rate: Optional[float] = None,
        current_hours: float = 0,
        status: str = "available",
        current_location: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[Optional[EquipmentInfo], Optional[str]]:
        """Create new equipment."""
        data = {
            "name": name,
            "equipment_type": equipment_type,
            "make": make,
            "model": model,
            "year": year,
            "serial_number": serial_number,
            "purchase_date": purchase_date,
            "purchase_cost": purchase_cost,
            "current_value": current_value,
            "hourly_rate": hourly_rate,
            "current_hours": current_hours,
            "status": status,
            "current_location": current_location,
            "notes": notes
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = self._client.post("/equipment", json=data)
        if not response.success:
            return None, response.error_message

        return EquipmentInfo.from_dict(response.data), None

    def update_equipment(
        self,
        equipment_id: int,
        **kwargs
    ) -> Tuple[Optional[EquipmentInfo], Optional[str]]:
        """Update equipment."""
        # Remove None values
        data = {k: v for k, v in kwargs.items() if v is not None}

        response = self._client.put(f"/equipment/{equipment_id}", json=data)
        if not response.success:
            return None, response.error_message

        return EquipmentInfo.from_dict(response.data), None

    def delete_equipment(self, equipment_id: int) -> Tuple[bool, Optional[str]]:
        """Delete (retire) equipment."""
        response = self._client.delete(f"/equipment/{equipment_id}")
        if not response.success:
            return False, response.error_message

        return True, None

    def update_hours(
        self,
        equipment_id: int,
        new_hours: float
    ) -> Tuple[Optional[EquipmentInfo], Optional[str]]:
        """Update equipment hour meter."""
        response = self._client.post(
            f"/equipment/{equipment_id}/hours",
            params={"new_hours": new_hours}
        )
        if not response.success:
            return None, response.error_message

        return EquipmentInfo.from_dict(response.data), None

    def get_summary(self) -> Tuple[Optional[EquipmentSummary], Optional[str]]:
        """Get equipment fleet summary."""
        response = self._client.get("/equipment/summary")
        if not response.success:
            return None, response.error_message

        return EquipmentSummary.from_dict(response.data), None

    # ========================================================================
    # MAINTENANCE
    # ========================================================================

    def list_maintenance(
        self,
        equipment_id: Optional[int] = None,
        maintenance_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100
    ) -> Tuple[List[MaintenanceInfo], Optional[str]]:
        """List maintenance records."""
        params = {"limit": limit}
        if equipment_id:
            params["equipment_id"] = equipment_id
        if maintenance_type:
            params["maintenance_type"] = maintenance_type
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = self._client.get("/maintenance", params=params)
        if not response.success:
            return [], response.error_message

        return [MaintenanceInfo.from_dict(m) for m in response.data], None

    def create_maintenance(
        self,
        equipment_id: int,
        maintenance_type: str,
        service_date: str,
        next_service_date: Optional[str] = None,
        next_service_hours: Optional[float] = None,
        cost: Optional[float] = None,
        performed_by: Optional[str] = None,
        vendor: Optional[str] = None,
        description: Optional[str] = None,
        parts_used: Optional[str] = None
    ) -> Tuple[Optional[MaintenanceInfo], Optional[str]]:
        """Log a maintenance record."""
        data = {
            "equipment_id": equipment_id,
            "maintenance_type": maintenance_type,
            "service_date": service_date,
            "next_service_date": next_service_date,
            "next_service_hours": next_service_hours,
            "cost": cost,
            "performed_by": performed_by,
            "vendor": vendor,
            "description": description,
            "parts_used": parts_used
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = self._client.post("/maintenance", json=data)
        if not response.success:
            return None, response.error_message

        return MaintenanceInfo.from_dict(response.data), None

    def get_maintenance_alerts(
        self,
        days_ahead: int = 30
    ) -> Tuple[List[MaintenanceAlert], Optional[str]]:
        """Get upcoming maintenance alerts."""
        response = self._client.get(
            "/maintenance/alerts",
            params={"days_ahead": days_ahead}
        )
        if not response.success:
            return [], response.error_message

        return [MaintenanceAlert.from_dict(a) for a in response.data], None

    def get_equipment_maintenance_history(
        self,
        equipment_id: int,
        limit: int = 50
    ) -> Tuple[List[MaintenanceInfo], Optional[str]]:
        """Get maintenance history for specific equipment."""
        response = self._client.get(
            f"/equipment/{equipment_id}/maintenance",
            params={"limit": limit}
        )
        if not response.success:
            return [], response.error_message

        return [MaintenanceInfo.from_dict(m) for m in response.data], None

    # ========================================================================
    # USAGE TRACKING
    # ========================================================================

    def log_usage(
        self,
        equipment_id: int,
        usage_date: str,
        hours_used: Optional[float] = None,
        starting_hours: Optional[float] = None,
        ending_hours: Optional[float] = None,
        fuel_used: Optional[float] = None,
        fuel_unit: str = "gallons",
        operator_id: Optional[int] = None,
        field_operation_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Tuple[Optional[EquipmentUsage], Optional[str]]:
        """Log equipment usage."""
        data = {
            "equipment_id": equipment_id,
            "usage_date": usage_date,
            "hours_used": hours_used,
            "starting_hours": starting_hours,
            "ending_hours": ending_hours,
            "fuel_used": fuel_used,
            "fuel_unit": fuel_unit,
            "operator_id": operator_id,
            "field_operation_id": field_operation_id,
            "notes": notes
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = self._client.post("/equipment/usage", json=data)
        if not response.success:
            return None, response.error_message

        return EquipmentUsage.from_dict(response.data), None

    def get_equipment_usage_history(
        self,
        equipment_id: int,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100
    ) -> Tuple[List[EquipmentUsage], Optional[str]]:
        """Get usage history for specific equipment."""
        params = {"limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = self._client.get(
            f"/equipment/{equipment_id}/usage",
            params=params
        )
        if not response.success:
            return [], response.error_message

        return [EquipmentUsage.from_dict(u) for u in response.data], None


# ============================================================================
# SINGLETON
# ============================================================================

_equipment_api: Optional[EquipmentAPI] = None


def get_equipment_api() -> EquipmentAPI:
    """Get or create the equipment API singleton."""
    global _equipment_api
    if _equipment_api is None:
        _equipment_api = EquipmentAPI()
    return _equipment_api
