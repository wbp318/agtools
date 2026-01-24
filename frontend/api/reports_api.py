"""
Reports API Client

Handles reporting endpoints for the Farm Operations Manager.
AgTools v2.5.0 Phase 5
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict

from .client import APIClient, get_api_client


# ============================================================================
# DATA CLASSES - OPERATIONS REPORT
# ============================================================================

@dataclass
class MonthlyData:
    """Monthly aggregation data point"""
    month: str
    count: int = 0
    cost: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "MonthlyData":
        return cls(
            month=data.get("month", ""),
            count=data.get("count", 0),
            cost=float(data.get("cost", 0))
        )


@dataclass
class OperationsReport:
    """Operations report with aggregations"""
    total_operations: int
    total_cost: float
    avg_cost_per_acre: float
    top_operation_type: Optional[str]
    operations_by_type: Dict[str, int]
    cost_by_type: Dict[str, float]
    monthly_operations: List[MonthlyData]
    monthly_costs: List[MonthlyData]
    date_from: Optional[str]
    date_to: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "OperationsReport":
        return cls(
            total_operations=data.get("total_operations", 0),
            total_cost=float(data.get("total_cost", 0)),
            avg_cost_per_acre=float(data.get("avg_cost_per_acre", 0)),
            top_operation_type=data.get("top_operation_type"),
            operations_by_type=data.get("operations_by_type", {}),
            cost_by_type=data.get("cost_by_type", {}),
            monthly_operations=[MonthlyData.from_dict(m) for m in data.get("monthly_operations", [])],
            monthly_costs=[MonthlyData.from_dict(m) for m in data.get("monthly_costs", [])],
            date_from=data.get("date_from"),
            date_to=data.get("date_to")
        )

    @property
    def total_cost_display(self) -> str:
        return f"${self.total_cost:,.2f}"

    @property
    def avg_cost_per_acre_display(self) -> str:
        return f"${self.avg_cost_per_acre:,.2f}"


# ============================================================================
# DATA CLASSES - FINANCIAL REPORT
# ============================================================================

@dataclass
class FieldFinancial:
    """Financial data for a single field"""
    field_id: int
    field_name: str
    farm_name: Optional[str]
    acreage: float
    total_cost: float
    cost_per_acre: float
    revenue: float
    profit: float
    operation_count: int

    @classmethod
    def from_dict(cls, data: dict) -> "FieldFinancial":
        return cls(
            field_id=data.get("field_id", 0),
            field_name=data.get("field_name", ""),
            farm_name=data.get("farm_name"),
            acreage=float(data.get("acreage", 0)),
            total_cost=float(data.get("total_cost", 0)),
            cost_per_acre=float(data.get("cost_per_acre", 0)),
            revenue=float(data.get("revenue", 0)),
            profit=float(data.get("profit", 0)),
            operation_count=data.get("operation_count", 0)
        )

    @property
    def profit_display(self) -> str:
        return f"${self.profit:,.2f}"

    @property
    def profit_color(self) -> str:
        return "#2e7d32" if self.profit >= 0 else "#d32f2f"


@dataclass
class FinancialReport:
    """Financial analysis report"""
    total_input_costs: float
    total_equipment_costs: float
    total_revenue: float
    net_profit: float
    cost_by_category: Dict[str, float]
    fields: List[FieldFinancial]
    date_from: Optional[str]
    date_to: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "FinancialReport":
        return cls(
            total_input_costs=float(data.get("total_input_costs", 0)),
            total_equipment_costs=float(data.get("total_equipment_costs", 0)),
            total_revenue=float(data.get("total_revenue", 0)),
            net_profit=float(data.get("net_profit", 0)),
            cost_by_category=data.get("cost_by_category", {}),
            fields=[FieldFinancial.from_dict(f) for f in data.get("fields", [])],
            date_from=data.get("date_from"),
            date_to=data.get("date_to")
        )

    @property
    def net_profit_display(self) -> str:
        return f"${self.net_profit:,.2f}"

    @property
    def net_profit_color(self) -> str:
        return "#2e7d32" if self.net_profit >= 0 else "#d32f2f"


# ============================================================================
# DATA CLASSES - EQUIPMENT REPORT
# ============================================================================

@dataclass
class EquipmentUsage:
    """Equipment usage data"""
    equipment_id: int
    name: str
    equipment_type: str
    total_hours: float
    maintenance_cost: float
    operating_cost: float

    @classmethod
    def from_dict(cls, data: dict) -> "EquipmentUsage":
        return cls(
            equipment_id=data.get("equipment_id", 0),
            name=data.get("name", ""),
            equipment_type=data.get("equipment_type", ""),
            total_hours=float(data.get("total_hours", 0)),
            maintenance_cost=float(data.get("maintenance_cost", 0)),
            operating_cost=float(data.get("operating_cost", 0))
        )

    @property
    def type_display(self) -> str:
        return self.equipment_type.replace("_", " ").title()


@dataclass
class MaintenanceItem:
    """Maintenance alert item"""
    equipment_id: int
    equipment_name: str
    equipment_type: str
    maintenance_type: Optional[str]
    next_service_date: Optional[str]
    days_until: Optional[int]
    urgency: str

    @classmethod
    def from_dict(cls, data: dict) -> "MaintenanceItem":
        return cls(
            equipment_id=data.get("equipment_id", 0),
            equipment_name=data.get("equipment_name", ""),
            equipment_type=data.get("equipment_type", ""),
            maintenance_type=data.get("maintenance_type"),
            next_service_date=data.get("next_service_date"),
            days_until=data.get("days_until"),
            urgency=data.get("urgency", "upcoming")
        )

    @property
    def urgency_color(self) -> str:
        colors = {
            "overdue": "#d32f2f",
            "due_soon": "#f57c00",
            "upcoming": "#1976d2"
        }
        return colors.get(self.urgency, "#757575")


@dataclass
class EquipmentReport:
    """Equipment utilization report"""
    total_equipment: int
    total_fleet_value: float
    total_hours: float
    equipment_in_maintenance: int
    equipment_usage: List[EquipmentUsage]
    hours_by_type: Dict[str, float]
    maintenance_alerts: List[MaintenanceItem]
    date_from: Optional[str]
    date_to: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "EquipmentReport":
        return cls(
            total_equipment=data.get("total_equipment", 0),
            total_fleet_value=float(data.get("total_fleet_value", 0)),
            total_hours=float(data.get("total_hours", 0)),
            equipment_in_maintenance=data.get("equipment_in_maintenance", 0),
            equipment_usage=[EquipmentUsage.from_dict(e) for e in data.get("equipment_usage", [])],
            hours_by_type=data.get("hours_by_type", {}),
            maintenance_alerts=[MaintenanceItem.from_dict(m) for m in data.get("maintenance_alerts", [])],
            date_from=data.get("date_from"),
            date_to=data.get("date_to")
        )

    @property
    def fleet_value_display(self) -> str:
        return f"${self.total_fleet_value:,.2f}"


# ============================================================================
# DATA CLASSES - INVENTORY REPORT
# ============================================================================

@dataclass
class InventoryItemReport:
    """Inventory item summary for reports"""
    item_id: int
    name: str
    category: str
    quantity: float
    unit: str
    value: float
    is_low_stock: bool
    is_expiring: bool
    expiration_date: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "InventoryItemReport":
        return cls(
            item_id=data.get("item_id", 0),
            name=data.get("name", ""),
            category=data.get("category", ""),
            quantity=float(data.get("quantity", 0)),
            unit=data.get("unit", ""),
            value=float(data.get("value", 0)),
            is_low_stock=data.get("is_low_stock", False),
            is_expiring=data.get("is_expiring", False),
            expiration_date=data.get("expiration_date")
        )

    @property
    def category_display(self) -> str:
        return self.category.replace("_", " ").title()


@dataclass
class InventoryReport:
    """Inventory status report"""
    total_items: int
    total_value: float
    low_stock_count: int
    expiring_count: int
    value_by_category: Dict[str, float]
    items_by_category: Dict[str, int]
    low_stock_items: List[InventoryItemReport]
    expiring_items: List[InventoryItemReport]

    @classmethod
    def from_dict(cls, data: dict) -> "InventoryReport":
        return cls(
            total_items=data.get("total_items", 0),
            total_value=float(data.get("total_value", 0)),
            low_stock_count=data.get("low_stock_count", 0),
            expiring_count=data.get("expiring_count", 0),
            value_by_category=data.get("value_by_category", {}),
            items_by_category=data.get("items_by_category", {}),
            low_stock_items=[InventoryItemReport.from_dict(i) for i in data.get("low_stock_items", [])],
            expiring_items=[InventoryItemReport.from_dict(i) for i in data.get("expiring_items", [])]
        )

    @property
    def total_value_display(self) -> str:
        return f"${self.total_value:,.2f}"


# ============================================================================
# DATA CLASSES - FIELD PERFORMANCE REPORT
# ============================================================================

@dataclass
class FieldPerformance:
    """Performance data for a single field"""
    field_id: int
    field_name: str
    farm_name: Optional[str]
    acreage: float
    current_crop: Optional[str]
    operation_count: int
    total_cost: float
    cost_per_acre: float
    yield_amount: Optional[float]
    yield_per_acre: Optional[float]

    @classmethod
    def from_dict(cls, data: dict) -> "FieldPerformance":
        return cls(
            field_id=data.get("field_id", 0),
            field_name=data.get("field_name", ""),
            farm_name=data.get("farm_name"),
            acreage=float(data.get("acreage", 0)),
            current_crop=data.get("current_crop"),
            operation_count=data.get("operation_count", 0),
            total_cost=float(data.get("total_cost", 0)),
            cost_per_acre=float(data.get("cost_per_acre", 0)),
            yield_amount=data.get("yield_amount"),
            yield_per_acre=data.get("yield_per_acre")
        )

    @property
    def crop_display(self) -> str:
        return (self.current_crop or "Unknown").replace("_", " ").title()

    @property
    def yield_display(self) -> str:
        if self.yield_per_acre:
            return f"{self.yield_per_acre:.1f} bu/acre"
        return "-"


@dataclass
class FieldPerformanceReport:
    """Field performance report"""
    total_fields: int
    total_acreage: float
    avg_yield: Optional[float]
    best_field: Optional[str]
    fields: List[FieldPerformance]
    acreage_by_crop: Dict[str, float]
    operations_by_field: Dict[str, int]
    date_from: Optional[str]
    date_to: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "FieldPerformanceReport":
        return cls(
            total_fields=data.get("total_fields", 0),
            total_acreage=float(data.get("total_acreage", 0)),
            avg_yield=data.get("avg_yield"),
            best_field=data.get("best_field"),
            fields=[FieldPerformance.from_dict(f) for f in data.get("fields", [])],
            acreage_by_crop=data.get("acreage_by_crop", {}),
            operations_by_field=data.get("operations_by_field", {}),
            date_from=data.get("date_from"),
            date_to=data.get("date_to")
        )


# ============================================================================
# DATA CLASSES - DASHBOARD SUMMARY
# ============================================================================

@dataclass
class DashboardSummary:
    """Combined dashboard summary"""
    total_operations: int
    total_operation_cost: float
    total_fields: int
    total_acreage: float
    total_equipment: int
    fleet_value: float
    maintenance_due: int
    total_inventory_items: int
    inventory_value: float
    low_stock_count: int
    total_revenue: float
    net_profit: float

    @classmethod
    def from_dict(cls, data: dict) -> "DashboardSummary":
        return cls(
            total_operations=data.get("total_operations", 0),
            total_operation_cost=float(data.get("total_operation_cost", 0)),
            total_fields=data.get("total_fields", 0),
            total_acreage=float(data.get("total_acreage", 0)),
            total_equipment=data.get("total_equipment", 0),
            fleet_value=float(data.get("fleet_value", 0)),
            maintenance_due=data.get("maintenance_due", 0),
            total_inventory_items=data.get("total_inventory_items", 0),
            inventory_value=float(data.get("inventory_value", 0)),
            low_stock_count=data.get("low_stock_count", 0),
            total_revenue=float(data.get("total_revenue", 0)),
            net_profit=float(data.get("net_profit", 0))
        )

    @property
    def net_profit_display(self) -> str:
        return f"${self.net_profit:,.2f}"

    @property
    def net_profit_color(self) -> str:
        return "#2e7d32" if self.net_profit >= 0 else "#d32f2f"


# ============================================================================
# REPORTS API CLIENT
# ============================================================================

class ReportsAPI:
    """API client for reports endpoints"""

    REPORT_TYPES = [
        ("operations", "Operations Report"),
        ("financial", "Financial Report"),
        ("equipment", "Equipment Report"),
        ("inventory", "Inventory Report"),
        ("fields", "Field Performance Report"),
        ("dashboard", "Dashboard Summary")
    ]

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def get_operations_report(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        field_id: Optional[int] = None
    ) -> Tuple[Optional[OperationsReport], Optional[str]]:
        """
        Get operations report with aggregations.

        Returns:
            Tuple of (OperationsReport, error_message or None)
        """
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if field_id:
            params["field_id"] = field_id

        response = self._client.get("/reports/operations", params=params if params else None)

        if response.error_message:
            return None, response.error_message

        return OperationsReport.from_dict(response.data), None

    def get_financial_report(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Tuple[Optional[FinancialReport], Optional[str]]:
        """
        Get financial analysis report.

        Returns:
            Tuple of (FinancialReport, error_message or None)
        """
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = self._client.get("/reports/financial", params=params if params else None)

        if response.error_message:
            return None, response.error_message

        return FinancialReport.from_dict(response.data), None

    def get_equipment_report(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Tuple[Optional[EquipmentReport], Optional[str]]:
        """
        Get equipment utilization report.

        Returns:
            Tuple of (EquipmentReport, error_message or None)
        """
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = self._client.get("/reports/equipment", params=params if params else None)

        if response.error_message:
            return None, response.error_message

        return EquipmentReport.from_dict(response.data), None

    def get_inventory_report(self) -> Tuple[Optional[InventoryReport], Optional[str]]:
        """
        Get inventory status report.

        Returns:
            Tuple of (InventoryReport, error_message or None)
        """
        response = self._client.get("/reports/inventory")

        if response.error_message:
            return None, response.error_message

        return InventoryReport.from_dict(response.data), None

    def get_field_performance_report(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Tuple[Optional[FieldPerformanceReport], Optional[str]]:
        """
        Get field performance report.

        Returns:
            Tuple of (FieldPerformanceReport, error_message or None)
        """
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = self._client.get("/reports/fields", params=params if params else None)

        if response.error_message:
            return None, response.error_message

        return FieldPerformanceReport.from_dict(response.data), None

    def get_dashboard_summary(self) -> Tuple[Optional[DashboardSummary], Optional[str]]:
        """
        Get combined dashboard summary.

        Returns:
            Tuple of (DashboardSummary, error_message or None)
        """
        response = self._client.get("/reports/dashboard")

        if response.error_message:
            return None, response.error_message

        return DashboardSummary.from_dict(response.data), None

    def export_csv(
        self,
        report_type: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Export report data to CSV.

        Returns:
            Tuple of (CSV content string, error_message or None)
        """
        data = {"report_type": report_type}
        if date_from:
            data["date_from"] = date_from
        if date_to:
            data["date_to"] = date_to

        response = self._client.post("/reports/export/csv", json=data)

        if response.error_message:
            return None, response.error_message

        # The response should be the CSV content
        if isinstance(response.data, str):
            return response.data, None

        return str(response.data), None


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_reports_api: Optional[ReportsAPI] = None


def get_reports_api() -> ReportsAPI:
    """Get or create the reports API singleton."""
    global _reports_api

    if _reports_api is None:
        _reports_api = ReportsAPI()

    return _reports_api
