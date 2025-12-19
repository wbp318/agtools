"""
Reporting Service for Farm Operations Manager
Aggregates data from all services for comprehensive reports.

AgTools v2.5.0 Phase 5
"""

import sqlite3
import csv
import io
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple

from pydantic import BaseModel, Field

from .field_service import get_field_service
from .field_operations_service import get_field_operations_service, OperationType
from .equipment_service import get_equipment_service
from .inventory_service import get_inventory_service


# ============================================================================
# ENUMS
# ============================================================================

class ReportType(str, Enum):
    """Types of reports available"""
    OPERATIONS = "operations"
    FINANCIAL = "financial"
    EQUIPMENT = "equipment"
    INVENTORY = "inventory"
    FIELDS = "fields"
    DASHBOARD = "dashboard"


# ============================================================================
# PYDANTIC MODELS - OPERATIONS REPORT
# ============================================================================

class MonthlyData(BaseModel):
    """Monthly aggregation data point"""
    month: str  # YYYY-MM format
    count: int = 0
    cost: float = 0.0


class OperationsReport(BaseModel):
    """Operations report with aggregations"""
    # Summary
    total_operations: int
    total_cost: float
    avg_cost_per_acre: float
    top_operation_type: Optional[str] = None

    # Breakdowns
    operations_by_type: Dict[str, int]
    cost_by_type: Dict[str, float]

    # Time series for charts
    monthly_operations: List[MonthlyData]
    monthly_costs: List[MonthlyData]

    # Date range
    date_from: Optional[str] = None
    date_to: Optional[str] = None


# ============================================================================
# PYDANTIC MODELS - FINANCIAL REPORT
# ============================================================================

class FieldFinancial(BaseModel):
    """Financial data for a single field"""
    field_id: int
    field_name: str
    farm_name: Optional[str] = None
    acreage: float
    total_cost: float
    cost_per_acre: float
    revenue: float  # From harvest
    profit: float
    operation_count: int


class FinancialReport(BaseModel):
    """Financial analysis report"""
    # Summary
    total_input_costs: float
    total_equipment_costs: float
    total_revenue: float
    net_profit: float

    # Cost breakdown by category
    cost_by_category: Dict[str, float]

    # Per-field analysis
    fields: List[FieldFinancial]

    # Date range
    date_from: Optional[str] = None
    date_to: Optional[str] = None


# ============================================================================
# PYDANTIC MODELS - EQUIPMENT REPORT
# ============================================================================

class EquipmentUsage(BaseModel):
    """Equipment usage data"""
    equipment_id: int
    name: str
    equipment_type: str
    total_hours: float
    maintenance_cost: float
    operating_cost: float  # hours * hourly_rate


class MaintenanceItem(BaseModel):
    """Maintenance alert item"""
    equipment_id: int
    equipment_name: str
    equipment_type: str
    maintenance_type: Optional[str] = None
    next_service_date: Optional[str] = None
    days_until: Optional[int] = None
    urgency: str  # overdue, due_soon, upcoming


class EquipmentReport(BaseModel):
    """Equipment utilization report"""
    # Summary
    total_equipment: int
    total_fleet_value: float
    total_hours: float
    equipment_in_maintenance: int

    # Usage by equipment
    equipment_usage: List[EquipmentUsage]

    # Hours by type
    hours_by_type: Dict[str, float]

    # Maintenance alerts
    maintenance_alerts: List[MaintenanceItem]

    # Date range
    date_from: Optional[str] = None
    date_to: Optional[str] = None


# ============================================================================
# PYDANTIC MODELS - INVENTORY REPORT
# ============================================================================

class InventoryItem(BaseModel):
    """Inventory item summary"""
    item_id: int
    name: str
    category: str
    quantity: float
    unit: str
    value: float
    is_low_stock: bool
    is_expiring: bool
    expiration_date: Optional[str] = None


class InventoryReport(BaseModel):
    """Inventory status report"""
    # Summary
    total_items: int
    total_value: float
    low_stock_count: int
    expiring_count: int

    # Value by category
    value_by_category: Dict[str, float]
    items_by_category: Dict[str, int]

    # Alert items
    low_stock_items: List[InventoryItem]
    expiring_items: List[InventoryItem]


# ============================================================================
# PYDANTIC MODELS - FIELD PERFORMANCE REPORT
# ============================================================================

class FieldPerformance(BaseModel):
    """Performance data for a single field"""
    field_id: int
    field_name: str
    farm_name: Optional[str] = None
    acreage: float
    current_crop: Optional[str] = None
    operation_count: int
    total_cost: float
    cost_per_acre: float
    yield_amount: Optional[float] = None
    yield_per_acre: Optional[float] = None


class FieldPerformanceReport(BaseModel):
    """Field performance report"""
    # Summary
    total_fields: int
    total_acreage: float
    avg_yield: Optional[float] = None
    best_field: Optional[str] = None

    # Fields breakdown
    fields: List[FieldPerformance]

    # Aggregations
    acreage_by_crop: Dict[str, float]
    operations_by_field: Dict[str, int]

    # Date range
    date_from: Optional[str] = None
    date_to: Optional[str] = None


# ============================================================================
# PYDANTIC MODELS - DASHBOARD SUMMARY
# ============================================================================

class DashboardSummary(BaseModel):
    """Combined dashboard summary"""
    # Operations
    total_operations: int
    total_operation_cost: float

    # Fields
    total_fields: int
    total_acreage: float

    # Equipment
    total_equipment: int
    fleet_value: float
    maintenance_due: int

    # Inventory
    total_inventory_items: int
    inventory_value: float
    low_stock_count: int

    # Financial
    total_revenue: float
    net_profit: float


# ============================================================================
# REPORTING SERVICE CLASS
# ============================================================================

class ReportingService:
    """
    Reporting service that aggregates data from all services.
    Provides comprehensive reports with filtering and CSV export.
    """

    def __init__(self, db_path: str = "agtools.db"):
        """Initialize reporting service."""
        self.db_path = db_path
        self._field_service = get_field_service(db_path)
        self._ops_service = get_field_operations_service(db_path)
        self._equipment_service = get_equipment_service(db_path)
        self._inventory_service = get_inventory_service(db_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ========================================================================
    # OPERATIONS REPORT
    # ========================================================================

    def get_operations_report(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        field_id: Optional[int] = None
    ) -> OperationsReport:
        """
        Generate operations report with aggregations.

        Args:
            date_from: Start date filter
            date_to: End date filter
            field_id: Filter by specific field

        Returns:
            OperationsReport with all aggregations
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build WHERE clause
        conditions = ["is_active = 1"]
        params = []

        if date_from:
            conditions.append("operation_date >= ?")
            params.append(date_from.isoformat())

        if date_to:
            conditions.append("operation_date <= ?")
            params.append(date_to.isoformat())

        if field_id:
            conditions.append("field_id = ?")
            params.append(field_id)

        where_clause = " AND ".join(conditions)

        # Get totals
        cursor.execute(f"""
            SELECT
                COUNT(*) as total_operations,
                COALESCE(SUM(total_cost), 0) as total_cost,
                COALESCE(SUM(acres_covered), 0) as total_acres
            FROM field_operations
            WHERE {where_clause}
        """, params)

        row = cursor.fetchone()
        total_operations = row["total_operations"]
        total_cost = float(row["total_cost"])
        total_acres = float(row["total_acres"]) if row["total_acres"] else 0
        avg_cost_per_acre = total_cost / total_acres if total_acres > 0 else 0

        # Operations by type
        cursor.execute(f"""
            SELECT operation_type, COUNT(*) as count, COALESCE(SUM(total_cost), 0) as cost
            FROM field_operations
            WHERE {where_clause}
            GROUP BY operation_type
            ORDER BY count DESC
        """, params)

        ops_by_type = {}
        cost_by_type = {}
        top_type = None

        for row in cursor.fetchall():
            op_type = row["operation_type"]
            ops_by_type[op_type] = row["count"]
            cost_by_type[op_type] = float(row["cost"])
            if top_type is None:
                top_type = op_type

        # Monthly aggregation
        cursor.execute(f"""
            SELECT
                strftime('%Y-%m', operation_date) as month,
                COUNT(*) as count,
                COALESCE(SUM(total_cost), 0) as cost
            FROM field_operations
            WHERE {where_clause}
            GROUP BY strftime('%Y-%m', operation_date)
            ORDER BY month
        """, params)

        monthly_operations = []
        monthly_costs = []

        for row in cursor.fetchall():
            month = row["month"]
            monthly_operations.append(MonthlyData(month=month, count=row["count"]))
            monthly_costs.append(MonthlyData(month=month, cost=float(row["cost"])))

        conn.close()

        return OperationsReport(
            total_operations=total_operations,
            total_cost=total_cost,
            avg_cost_per_acre=round(avg_cost_per_acre, 2),
            top_operation_type=top_type,
            operations_by_type=ops_by_type,
            cost_by_type=cost_by_type,
            monthly_operations=monthly_operations,
            monthly_costs=monthly_costs,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None
        )

    # ========================================================================
    # FINANCIAL REPORT
    # ========================================================================

    def get_financial_report(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> FinancialReport:
        """
        Generate financial analysis report.

        Args:
            date_from: Start date filter
            date_to: End date filter

        Returns:
            FinancialReport with cost/revenue analysis
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build WHERE clause for operations
        conditions = ["o.is_active = 1"]
        params = []

        if date_from:
            conditions.append("o.operation_date >= ?")
            params.append(date_from.isoformat())

        if date_to:
            conditions.append("o.operation_date <= ?")
            params.append(date_to.isoformat())

        where_clause = " AND ".join(conditions)

        # Cost breakdown by operation type (category)
        cursor.execute(f"""
            SELECT
                o.operation_type,
                COALESCE(SUM(o.total_cost), 0) as cost
            FROM field_operations o
            WHERE {where_clause}
            GROUP BY o.operation_type
        """, params)

        cost_by_category = {}
        total_input_costs = 0.0

        for row in cursor.fetchall():
            cost = float(row["cost"])
            cost_by_category[row["operation_type"]] = cost
            total_input_costs += cost

        # Revenue from harvest operations (yield * estimated price)
        # Using $5/bushel as default grain price
        grain_price = 5.0
        cursor.execute(f"""
            SELECT COALESCE(SUM(yield_amount), 0) as total_yield
            FROM field_operations o
            WHERE {where_clause} AND o.operation_type = 'harvest'
        """, params)

        row = cursor.fetchone()
        total_yield = float(row["total_yield"]) if row["total_yield"] else 0
        total_revenue = total_yield * grain_price

        # Equipment costs (maintenance costs in date range)
        equip_conditions = ["m.is_active = 1"]
        equip_params = []

        if date_from:
            equip_conditions.append("m.service_date >= ?")
            equip_params.append(date_from.isoformat())

        if date_to:
            equip_conditions.append("m.service_date <= ?")
            equip_params.append(date_to.isoformat())

        equip_where = " AND ".join(equip_conditions)

        cursor.execute(f"""
            SELECT COALESCE(SUM(cost), 0) as total_maintenance
            FROM equipment_maintenance m
            WHERE {equip_where}
        """, equip_params)

        row = cursor.fetchone()
        total_equipment_costs = float(row["total_maintenance"]) if row["total_maintenance"] else 0

        # Net profit
        net_profit = total_revenue - total_input_costs - total_equipment_costs

        # Per-field financial data
        cursor.execute(f"""
            SELECT
                f.id as field_id,
                f.name as field_name,
                f.farm_name,
                f.acreage,
                COUNT(o.id) as operation_count,
                COALESCE(SUM(o.total_cost), 0) as total_cost,
                COALESCE(SUM(CASE WHEN o.operation_type = 'harvest' THEN o.yield_amount ELSE 0 END), 0) as total_yield
            FROM fields f
            LEFT JOIN field_operations o ON f.id = o.field_id AND {where_clause}
            WHERE f.is_active = 1
            GROUP BY f.id
            ORDER BY f.name
        """, params)

        fields = []
        for row in cursor.fetchall():
            acreage = float(row["acreage"])
            total_cost = float(row["total_cost"])
            yield_amt = float(row["total_yield"]) if row["total_yield"] else 0
            revenue = yield_amt * grain_price

            fields.append(FieldFinancial(
                field_id=row["field_id"],
                field_name=row["field_name"],
                farm_name=row["farm_name"],
                acreage=acreage,
                total_cost=total_cost,
                cost_per_acre=round(total_cost / acreage, 2) if acreage > 0 else 0,
                revenue=revenue,
                profit=round(revenue - total_cost, 2),
                operation_count=row["operation_count"]
            ))

        conn.close()

        return FinancialReport(
            total_input_costs=round(total_input_costs, 2),
            total_equipment_costs=round(total_equipment_costs, 2),
            total_revenue=round(total_revenue, 2),
            net_profit=round(net_profit, 2),
            cost_by_category=cost_by_category,
            fields=fields,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None
        )

    # ========================================================================
    # EQUIPMENT REPORT
    # ========================================================================

    def get_equipment_report(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> EquipmentReport:
        """
        Generate equipment utilization report.

        Args:
            date_from: Start date filter
            date_to: End date filter

        Returns:
            EquipmentReport with utilization data
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get all active equipment
        cursor.execute("""
            SELECT
                id, name, equipment_type, current_hours,
                hourly_rate, current_value, status
            FROM equipment
            WHERE is_active = 1
            ORDER BY name
        """)

        equipment_list = cursor.fetchall()
        total_equipment = len(equipment_list)
        total_fleet_value = sum(float(e["current_value"] or 0) for e in equipment_list)
        total_hours = sum(float(e["current_hours"] or 0) for e in equipment_list)
        in_maintenance = sum(1 for e in equipment_list if e["status"] == "maintenance")

        # Equipment usage and maintenance costs
        equipment_usage = []
        hours_by_type = {}

        for equip in equipment_list:
            equip_id = equip["id"]
            equip_type = equip["equipment_type"]
            hours = float(equip["current_hours"] or 0)
            hourly_rate = float(equip["hourly_rate"] or 0)

            # Get maintenance costs in date range
            maint_conditions = ["equipment_id = ?", "is_active = 1"]
            maint_params = [equip_id]

            if date_from:
                maint_conditions.append("service_date >= ?")
                maint_params.append(date_from.isoformat())

            if date_to:
                maint_conditions.append("service_date <= ?")
                maint_params.append(date_to.isoformat())

            cursor.execute(f"""
                SELECT COALESCE(SUM(cost), 0) as maint_cost
                FROM equipment_maintenance
                WHERE {" AND ".join(maint_conditions)}
            """, maint_params)

            maint_row = cursor.fetchone()
            maint_cost = float(maint_row["maint_cost"]) if maint_row["maint_cost"] else 0

            equipment_usage.append(EquipmentUsage(
                equipment_id=equip_id,
                name=equip["name"],
                equipment_type=equip_type,
                total_hours=hours,
                maintenance_cost=maint_cost,
                operating_cost=round(hours * hourly_rate, 2)
            ))

            # Aggregate hours by type
            if equip_type in hours_by_type:
                hours_by_type[equip_type] += hours
            else:
                hours_by_type[equip_type] = hours

        # Maintenance alerts
        maintenance_alerts = []
        cursor.execute("""
            SELECT
                e.id as equipment_id,
                e.name as equipment_name,
                e.equipment_type,
                m.maintenance_type,
                m.next_service_date,
                e.current_hours,
                m.next_service_hours
            FROM equipment e
            LEFT JOIN (
                SELECT equipment_id, maintenance_type, next_service_date, next_service_hours,
                       ROW_NUMBER() OVER (PARTITION BY equipment_id ORDER BY service_date DESC) as rn
                FROM equipment_maintenance
                WHERE is_active = 1
            ) m ON e.id = m.equipment_id AND m.rn = 1
            WHERE e.is_active = 1 AND (m.next_service_date IS NOT NULL OR m.next_service_hours IS NOT NULL)
            ORDER BY m.next_service_date
        """)

        today = date.today()
        for row in cursor.fetchall():
            next_date = row["next_service_date"]
            days_until = None
            urgency = "upcoming"

            if next_date:
                try:
                    next_dt = datetime.strptime(next_date, "%Y-%m-%d").date()
                    days_until = (next_dt - today).days
                    if days_until < 0:
                        urgency = "overdue"
                    elif days_until <= 7:
                        urgency = "due_soon"
                except:
                    pass

            maintenance_alerts.append(MaintenanceItem(
                equipment_id=row["equipment_id"],
                equipment_name=row["equipment_name"],
                equipment_type=row["equipment_type"],
                maintenance_type=row["maintenance_type"],
                next_service_date=next_date,
                days_until=days_until,
                urgency=urgency
            ))

        conn.close()

        return EquipmentReport(
            total_equipment=total_equipment,
            total_fleet_value=round(total_fleet_value, 2),
            total_hours=round(total_hours, 1),
            equipment_in_maintenance=in_maintenance,
            equipment_usage=equipment_usage,
            hours_by_type=hours_by_type,
            maintenance_alerts=maintenance_alerts,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None
        )

    # ========================================================================
    # INVENTORY REPORT
    # ========================================================================

    def get_inventory_report(self) -> InventoryReport:
        """
        Generate inventory status report.

        Returns:
            InventoryReport with current stock levels and alerts
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get all active inventory items
        cursor.execute("""
            SELECT
                id, name, category, quantity, unit,
                unit_cost, min_quantity, expiration_date
            FROM inventory_items
            WHERE is_active = 1
            ORDER BY category, name
        """)

        items = cursor.fetchall()
        total_items = len(items)
        total_value = 0.0
        low_stock_count = 0
        expiring_count = 0

        value_by_category = {}
        items_by_category = {}
        low_stock_items = []
        expiring_items = []

        today = date.today()
        expiry_threshold = 30  # days

        for item in items:
            quantity = float(item["quantity"] or 0)
            unit_cost = float(item["unit_cost"] or 0)
            value = quantity * unit_cost
            total_value += value

            category = item["category"]
            if category in value_by_category:
                value_by_category[category] += value
                items_by_category[category] += 1
            else:
                value_by_category[category] = value
                items_by_category[category] = 1

            # Check low stock
            min_qty = float(item["min_quantity"] or 0)
            is_low_stock = quantity < min_qty if min_qty > 0 else False
            if is_low_stock:
                low_stock_count += 1

            # Check expiration
            is_expiring = False
            exp_date = item["expiration_date"]
            if exp_date:
                try:
                    exp_dt = datetime.strptime(exp_date, "%Y-%m-%d").date()
                    days_until = (exp_dt - today).days
                    if days_until <= expiry_threshold:
                        is_expiring = True
                        expiring_count += 1
                except:
                    pass

            inv_item = InventoryItem(
                item_id=item["id"],
                name=item["name"],
                category=category,
                quantity=quantity,
                unit=item["unit"] or "",
                value=round(value, 2),
                is_low_stock=is_low_stock,
                is_expiring=is_expiring,
                expiration_date=exp_date
            )

            if is_low_stock:
                low_stock_items.append(inv_item)
            if is_expiring:
                expiring_items.append(inv_item)

        conn.close()

        return InventoryReport(
            total_items=total_items,
            total_value=round(total_value, 2),
            low_stock_count=low_stock_count,
            expiring_count=expiring_count,
            value_by_category={k: round(v, 2) for k, v in value_by_category.items()},
            items_by_category=items_by_category,
            low_stock_items=low_stock_items,
            expiring_items=expiring_items
        )

    # ========================================================================
    # FIELD PERFORMANCE REPORT
    # ========================================================================

    def get_field_performance_report(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> FieldPerformanceReport:
        """
        Generate field performance report.

        Args:
            date_from: Start date filter
            date_to: End date filter

        Returns:
            FieldPerformanceReport with per-field metrics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build WHERE clause for operations
        conditions = ["o.is_active = 1"]
        params = []

        if date_from:
            conditions.append("o.operation_date >= ?")
            params.append(date_from.isoformat())

        if date_to:
            conditions.append("o.operation_date <= ?")
            params.append(date_to.isoformat())

        where_clause = " AND ".join(conditions)

        # Get field performance data
        cursor.execute(f"""
            SELECT
                f.id as field_id,
                f.name as field_name,
                f.farm_name,
                f.acreage,
                f.current_crop,
                COUNT(o.id) as operation_count,
                COALESCE(SUM(o.total_cost), 0) as total_cost,
                COALESCE(SUM(CASE WHEN o.operation_type = 'harvest' THEN o.yield_amount ELSE 0 END), 0) as total_yield
            FROM fields f
            LEFT JOIN field_operations o ON f.id = o.field_id AND {where_clause}
            WHERE f.is_active = 1
            GROUP BY f.id
            ORDER BY f.name
        """, params)

        fields = []
        total_fields = 0
        total_acreage = 0.0
        total_yield = 0.0
        total_yield_acres = 0.0
        best_field = None
        best_yield_per_acre = 0.0

        acreage_by_crop = {}
        operations_by_field = {}

        for row in cursor.fetchall():
            total_fields += 1
            acreage = float(row["acreage"])
            total_acreage += acreage

            total_cost = float(row["total_cost"])
            yield_amt = float(row["total_yield"]) if row["total_yield"] else 0

            if yield_amt > 0:
                total_yield += yield_amt
                total_yield_acres += acreage

            yield_per_acre = yield_amt / acreage if acreage > 0 and yield_amt > 0 else None

            if yield_per_acre and yield_per_acre > best_yield_per_acre:
                best_yield_per_acre = yield_per_acre
                best_field = row["field_name"]

            fields.append(FieldPerformance(
                field_id=row["field_id"],
                field_name=row["field_name"],
                farm_name=row["farm_name"],
                acreage=acreage,
                current_crop=row["current_crop"],
                operation_count=row["operation_count"],
                total_cost=total_cost,
                cost_per_acre=round(total_cost / acreage, 2) if acreage > 0 else 0,
                yield_amount=yield_amt if yield_amt > 0 else None,
                yield_per_acre=round(yield_per_acre, 1) if yield_per_acre else None
            ))

            # Aggregate by crop
            crop = row["current_crop"] or "Unknown"
            if crop in acreage_by_crop:
                acreage_by_crop[crop] += acreage
            else:
                acreage_by_crop[crop] = acreage

            # Operations by field
            operations_by_field[row["field_name"]] = row["operation_count"]

        conn.close()

        avg_yield = total_yield / total_yield_acres if total_yield_acres > 0 else None

        return FieldPerformanceReport(
            total_fields=total_fields,
            total_acreage=round(total_acreage, 1),
            avg_yield=round(avg_yield, 1) if avg_yield else None,
            best_field=best_field,
            fields=fields,
            acreage_by_crop=acreage_by_crop,
            operations_by_field=operations_by_field,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None
        )

    # ========================================================================
    # DASHBOARD SUMMARY
    # ========================================================================

    def get_dashboard_summary(self) -> DashboardSummary:
        """
        Generate combined dashboard summary.

        Returns:
            DashboardSummary with key metrics from all areas
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Operations totals
        cursor.execute("""
            SELECT COUNT(*) as total, COALESCE(SUM(total_cost), 0) as cost
            FROM field_operations WHERE is_active = 1
        """)
        ops_row = cursor.fetchone()
        total_operations = ops_row["total"]
        total_operation_cost = float(ops_row["cost"])

        # Fields totals
        cursor.execute("""
            SELECT COUNT(*) as total, COALESCE(SUM(acreage), 0) as acreage
            FROM fields WHERE is_active = 1
        """)
        fields_row = cursor.fetchone()
        total_fields = fields_row["total"]
        total_acreage = float(fields_row["acreage"])

        # Equipment totals
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COALESCE(SUM(current_value), 0) as value,
                   SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) as maint
            FROM equipment WHERE is_active = 1
        """)
        equip_row = cursor.fetchone()
        total_equipment = equip_row["total"]
        fleet_value = float(equip_row["value"])

        # Count maintenance alerts (due within 7 days or overdue)
        cursor.execute("""
            SELECT COUNT(*) as due
            FROM equipment_maintenance
            WHERE is_active = 1 AND next_service_date IS NOT NULL
            AND date(next_service_date) <= date('now', '+7 days')
        """)
        maint_row = cursor.fetchone()
        maintenance_due = maint_row["due"]

        # Inventory totals
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COALESCE(SUM(quantity * unit_cost), 0) as value,
                   SUM(CASE WHEN quantity < min_quantity AND min_quantity > 0 THEN 1 ELSE 0 END) as low
            FROM inventory_items WHERE is_active = 1
        """)
        inv_row = cursor.fetchone()
        total_inventory = inv_row["total"]
        inventory_value = float(inv_row["value"])
        low_stock = inv_row["low"]

        # Revenue from harvest (using $5/bushel default)
        grain_price = 5.0
        cursor.execute("""
            SELECT COALESCE(SUM(yield_amount), 0) as yield
            FROM field_operations
            WHERE is_active = 1 AND operation_type = 'harvest'
        """)
        harvest_row = cursor.fetchone()
        total_revenue = float(harvest_row["yield"]) * grain_price

        conn.close()

        # Net profit = revenue - operation costs
        net_profit = total_revenue - total_operation_cost

        return DashboardSummary(
            total_operations=total_operations,
            total_operation_cost=round(total_operation_cost, 2),
            total_fields=total_fields,
            total_acreage=round(total_acreage, 1),
            total_equipment=total_equipment,
            fleet_value=round(fleet_value, 2),
            maintenance_due=maintenance_due,
            total_inventory_items=total_inventory,
            inventory_value=round(inventory_value, 2),
            low_stock_count=low_stock,
            total_revenue=round(total_revenue, 2),
            net_profit=round(net_profit, 2)
        )

    # ========================================================================
    # CSV EXPORT
    # ========================================================================

    def export_to_csv(
        self,
        report_type: ReportType,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> str:
        """
        Export report data to CSV format.

        Args:
            report_type: Type of report to export
            date_from: Start date filter
            date_to: End date filter

        Returns:
            CSV string content
        """
        output = io.StringIO()
        writer = csv.writer(output)

        if report_type == ReportType.OPERATIONS:
            report = self.get_operations_report(date_from, date_to)

            # Summary section
            writer.writerow(["Operations Report"])
            writer.writerow(["Date Range", report.date_from or "All", "to", report.date_to or "All"])
            writer.writerow([])
            writer.writerow(["Summary"])
            writer.writerow(["Total Operations", report.total_operations])
            writer.writerow(["Total Cost", f"${report.total_cost:,.2f}"])
            writer.writerow(["Avg Cost/Acre", f"${report.avg_cost_per_acre:,.2f}"])
            writer.writerow([])

            # By type
            writer.writerow(["Operations by Type"])
            writer.writerow(["Type", "Count", "Cost"])
            for op_type, count in report.operations_by_type.items():
                cost = report.cost_by_type.get(op_type, 0)
                writer.writerow([op_type, count, f"${cost:,.2f}"])
            writer.writerow([])

            # Monthly
            writer.writerow(["Monthly Summary"])
            writer.writerow(["Month", "Operations", "Cost"])
            for i, monthly in enumerate(report.monthly_operations):
                cost = report.monthly_costs[i].cost if i < len(report.monthly_costs) else 0
                writer.writerow([monthly.month, monthly.count, f"${cost:,.2f}"])

        elif report_type == ReportType.FINANCIAL:
            report = self.get_financial_report(date_from, date_to)

            writer.writerow(["Financial Report"])
            writer.writerow(["Date Range", report.date_from or "All", "to", report.date_to or "All"])
            writer.writerow([])
            writer.writerow(["Summary"])
            writer.writerow(["Total Input Costs", f"${report.total_input_costs:,.2f}"])
            writer.writerow(["Total Equipment Costs", f"${report.total_equipment_costs:,.2f}"])
            writer.writerow(["Total Revenue", f"${report.total_revenue:,.2f}"])
            writer.writerow(["Net Profit", f"${report.net_profit:,.2f}"])
            writer.writerow([])

            # By field
            writer.writerow(["By Field"])
            writer.writerow(["Field", "Farm", "Acres", "Cost", "Cost/Acre", "Revenue", "Profit"])
            for f in report.fields:
                writer.writerow([
                    f.field_name, f.farm_name or "", f.acreage,
                    f"${f.total_cost:,.2f}", f"${f.cost_per_acre:,.2f}",
                    f"${f.revenue:,.2f}", f"${f.profit:,.2f}"
                ])

        elif report_type == ReportType.EQUIPMENT:
            report = self.get_equipment_report(date_from, date_to)

            writer.writerow(["Equipment Report"])
            writer.writerow([])
            writer.writerow(["Summary"])
            writer.writerow(["Total Equipment", report.total_equipment])
            writer.writerow(["Fleet Value", f"${report.total_fleet_value:,.2f}"])
            writer.writerow(["Total Hours", report.total_hours])
            writer.writerow([])

            # Usage
            writer.writerow(["Equipment Usage"])
            writer.writerow(["Equipment", "Type", "Hours", "Maintenance Cost", "Operating Cost"])
            for e in report.equipment_usage:
                writer.writerow([
                    e.name, e.equipment_type, e.total_hours,
                    f"${e.maintenance_cost:,.2f}", f"${e.operating_cost:,.2f}"
                ])

        elif report_type == ReportType.INVENTORY:
            report = self.get_inventory_report()

            writer.writerow(["Inventory Report"])
            writer.writerow([])
            writer.writerow(["Summary"])
            writer.writerow(["Total Items", report.total_items])
            writer.writerow(["Total Value", f"${report.total_value:,.2f}"])
            writer.writerow(["Low Stock Items", report.low_stock_count])
            writer.writerow(["Expiring Items", report.expiring_count])
            writer.writerow([])

            # By category
            writer.writerow(["Value by Category"])
            writer.writerow(["Category", "Items", "Value"])
            for cat, value in report.value_by_category.items():
                count = report.items_by_category.get(cat, 0)
                writer.writerow([cat, count, f"${value:,.2f}"])
            writer.writerow([])

            # Low stock
            if report.low_stock_items:
                writer.writerow(["Low Stock Items"])
                writer.writerow(["Item", "Category", "Quantity", "Unit"])
                for item in report.low_stock_items:
                    writer.writerow([item.name, item.category, item.quantity, item.unit])

        elif report_type == ReportType.FIELDS:
            report = self.get_field_performance_report(date_from, date_to)

            writer.writerow(["Field Performance Report"])
            writer.writerow(["Date Range", report.date_from or "All", "to", report.date_to or "All"])
            writer.writerow([])
            writer.writerow(["Summary"])
            writer.writerow(["Total Fields", report.total_fields])
            writer.writerow(["Total Acreage", report.total_acreage])
            writer.writerow(["Average Yield", report.avg_yield or "N/A"])
            writer.writerow(["Best Field", report.best_field or "N/A"])
            writer.writerow([])

            # Fields
            writer.writerow(["Field Performance"])
            writer.writerow(["Field", "Farm", "Acres", "Crop", "Operations", "Cost", "Cost/Acre", "Yield", "Yield/Acre"])
            for f in report.fields:
                writer.writerow([
                    f.field_name, f.farm_name or "", f.acreage, f.current_crop or "",
                    f.operation_count, f"${f.total_cost:,.2f}", f"${f.cost_per_acre:,.2f}",
                    f.yield_amount or "", f.yield_per_acre or ""
                ])

        return output.getvalue()


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_reporting_service: Optional[ReportingService] = None


def get_reporting_service(db_path: str = "agtools.db") -> ReportingService:
    """Get or create the reporting service singleton."""
    global _reporting_service

    if _reporting_service is None:
        _reporting_service = ReportingService(db_path)

    return _reporting_service
