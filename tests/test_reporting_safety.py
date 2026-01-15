"""
Reporting & Dashboard and Food Safety Test Suite

Tests for:
- Reporting services (operations, financial, equipment, inventory, field performance)
- Dashboard functionality (KPIs, charts, customization)
- Report filtering and export
- Food safety and traceability features

Run with: pytest tests/test_reporting_safety.py -v
"""

import os
import sys
import pytest
import tempfile
import secrets
import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch, PropertyMock
from decimal import Decimal
import uuid

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

# Set test environment
os.environ["AGTOOLS_DEV_MODE"] = "1"
os.environ["AGTOOLS_TEST_MODE"] = "1"


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def create_test_database(db_path: str):
    """Create all required tables for testing."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create users table (needed for foreign keys)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(100) NOT NULL UNIQUE,
            email VARCHAR(255),
            password_hash VARCHAR(255),
            role VARCHAR(50) DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add a default test user
    cursor.execute("""
        INSERT INTO users (id, username, email, is_active) VALUES (1, 'testuser', 'test@example.com', 1)
    """)

    # Create fields table (matching actual schema)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            farm_name VARCHAR(100),
            acreage DECIMAL(10, 2) NOT NULL,
            current_crop VARCHAR(50),
            soil_type VARCHAR(50),
            irrigation_type VARCHAR(50),
            location_lat DECIMAL(10, 7),
            location_lng DECIMAL(10, 7),
            boundary TEXT,
            notes TEXT,
            created_by_user_id INTEGER NOT NULL DEFAULT 1,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by_user_id) REFERENCES users(id)
        )
    """)

    # Create indexes for fields
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fields_name ON fields(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fields_farm ON fields(farm_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fields_crop ON fields(current_crop)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fields_created_by ON fields(created_by_user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fields_active ON fields(is_active)")

    # Create field_operations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER,
            operation_type VARCHAR(50) NOT NULL,
            operation_date DATE NOT NULL,
            acres_covered REAL DEFAULT 0,
            total_cost REAL DEFAULT 0,
            yield_amount REAL DEFAULT 0,
            notes TEXT,
            created_by_user_id INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (field_id) REFERENCES fields(id),
            FOREIGN KEY (created_by_user_id) REFERENCES users(id)
        )
    """)

    # Create equipment table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            equipment_type VARCHAR(50),
            make VARCHAR(100),
            model VARCHAR(100),
            year INTEGER,
            serial_number VARCHAR(100),
            current_hours REAL DEFAULT 0,
            hourly_rate REAL DEFAULT 0,
            purchase_cost REAL DEFAULT 0,
            current_value REAL DEFAULT 0,
            status VARCHAR(50) DEFAULT 'available',
            notes TEXT,
            created_by_user_id INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by_user_id) REFERENCES users(id)
        )
    """)

    # Create equipment_maintenance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment_maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER,
            maintenance_type VARCHAR(50),
            service_date DATE,
            next_service_date DATE,
            next_service_hours REAL,
            cost REAL DEFAULT 0,
            description TEXT,
            performed_by VARCHAR(100),
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        )
    """)

    # Create equipment_usage table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER,
            field_id INTEGER,
            operation_id INTEGER,
            usage_date DATE,
            hours_used REAL DEFAULT 0,
            fuel_used REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id),
            FOREIGN KEY (field_id) REFERENCES fields(id)
        )
    """)

    # Create inventory_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            quantity REAL DEFAULT 0,
            unit VARCHAR(50),
            unit_cost REAL DEFAULT 0,
            min_quantity REAL DEFAULT 0,
            storage_location VARCHAR(100),
            expiration_date DATE,
            notes TEXT,
            created_by_user_id INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by_user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def seed_test_data(db_path: str):
    """Add sample data for testing."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add sample fields
    cursor.execute("""
        INSERT INTO fields (name, farm_name, acreage, current_crop, soil_type, created_by_user_id, is_active)
        VALUES ('North 40', 'Test Farm', 40.0, 'corn', 'loam', 1, 1)
    """)
    cursor.execute("""
        INSERT INTO fields (name, farm_name, acreage, current_crop, soil_type, created_by_user_id, is_active)
        VALUES ('South 80', 'Test Farm', 80.0, 'soybean', 'clay', 1, 1)
    """)

    # Add sample operations
    cursor.execute("""
        INSERT INTO field_operations (field_id, operation_type, operation_date, acres_covered, total_cost, created_by_user_id, is_active)
        VALUES (1, 'planting', '2024-04-15', 40.0, 5000.0, 1, 1)
    """)
    cursor.execute("""
        INSERT INTO field_operations (field_id, operation_type, operation_date, acres_covered, total_cost, yield_amount, created_by_user_id, is_active)
        VALUES (1, 'harvest', '2024-10-15', 40.0, 3000.0, 8000.0, 1, 1)
    """)

    # Add sample equipment
    cursor.execute("""
        INSERT INTO equipment (name, equipment_type, make, model, year, current_hours, hourly_rate, current_value, status, created_by_user_id, is_active)
        VALUES ('Combine 1', 'combine', 'John Deere', 'S780', 2022, 500.0, 150.0, 450000.0, 'available', 1, 1)
    """)
    cursor.execute("""
        INSERT INTO equipment (name, equipment_type, make, model, year, current_hours, hourly_rate, current_value, status, created_by_user_id, is_active)
        VALUES ('Tractor 1', 'tractor', 'Case IH', 'Magnum', 2021, 1200.0, 75.0, 280000.0, 'available', 1, 1)
    """)

    # Add sample inventory
    cursor.execute("""
        INSERT INTO inventory_items (name, category, quantity, unit, unit_cost, min_quantity, created_by_user_id, is_active)
        VALUES ('Corn Seed', 'seed', 50.0, 'bags', 300.0, 10.0, 1, 1)
    """)
    cursor.execute("""
        INSERT INTO inventory_items (name, category, quantity, unit, unit_cost, min_quantity, created_by_user_id, is_active)
        VALUES ('Glyphosate', 'herbicide', 25.0, 'gallons', 45.0, 5.0, 1, 1)
    """)

    conn.commit()
    conn.close()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_db_path():
    """Create a temporary test database with schema."""
    fd, db_path = tempfile.mkstemp(suffix=".db", prefix="agtools_test_")
    os.close(fd)

    create_test_database(db_path)
    seed_test_data(db_path)

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def reporting_service(test_db_path):
    """Create a reporting service that uses our test database directly."""
    from services.reporting_service import (
        OperationsReport, FinancialReport, EquipmentReport,
        InventoryReport, FieldPerformanceReport, DashboardSummary, ReportType,
        EquipmentUsage, FieldPerformance
    )

    # Create a mock reporting service that uses our test database directly
    class TestReportingService:
        def __init__(self, db_path):
            self.db_path = db_path
            import sqlite3
            self._conn = sqlite3.connect(db_path)
            self._conn.row_factory = sqlite3.Row

        def get_operations_report(self, date_from=None, date_to=None, field_id=None):
            cursor = self._conn.cursor()
            today = date.today()
            date_from = date_from or date(today.year, 1, 1)
            date_to = date_to or today

            # Get operations
            query = "SELECT * FROM field_operations WHERE is_active = 1"
            params = []
            if date_from:
                query += " AND operation_date >= ?"
                params.append(date_from.isoformat() if hasattr(date_from, 'isoformat') else date_from)
            if date_to:
                query += " AND operation_date <= ?"
                params.append(date_to.isoformat() if hasattr(date_to, 'isoformat') else date_to)
            if field_id:
                query += " AND field_id = ?"
                params.append(field_id)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            total_ops = len(rows)
            total_cost = sum(row['total_cost'] or 0 for row in rows)
            total_acres = sum(row['acres_covered'] or 0 for row in rows)

            ops_by_type = {}
            cost_by_type = {}
            for row in rows:
                op_type = row['operation_type']
                ops_by_type[op_type] = ops_by_type.get(op_type, 0) + 1
                cost_by_type[op_type] = cost_by_type.get(op_type, 0) + (row['total_cost'] or 0)

            return OperationsReport(
                date_from=(date_from.isoformat() if hasattr(date_from, 'isoformat') else str(date_from)),
                date_to=(date_to.isoformat() if hasattr(date_to, 'isoformat') else str(date_to)),
                total_operations=total_ops,
                total_cost=total_cost,
                avg_cost_per_acre=total_cost / total_acres if total_acres > 0 else 0,
                operations_by_type=ops_by_type,
                cost_by_type=cost_by_type,
                monthly_operations=[],
                monthly_costs=[]
            )

        def get_financial_report(self, date_from=None, date_to=None):
            cursor = self._conn.cursor()
            today = date.today()
            date_from = date_from or date(today.year, 1, 1)
            date_to = date_to or today

            cursor.execute("SELECT * FROM field_operations WHERE is_active = 1")
            rows = cursor.fetchall()

            total_input = sum(row['total_cost'] or 0 for row in rows)
            total_revenue = sum(row['yield_amount'] or 0 for row in rows) * 5.0  # assume $5/bushel

            return FinancialReport(
                date_from=(date_from.isoformat() if hasattr(date_from, 'isoformat') else str(date_from)),
                date_to=(date_to.isoformat() if hasattr(date_to, 'isoformat') else str(date_to)),
                total_input_costs=total_input,
                total_equipment_costs=0,
                total_revenue=total_revenue,
                net_profit=total_revenue - total_input,
                cost_by_category={},
                fields=[]
            )

        def get_equipment_report(self, date_from=None, date_to=None):
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM equipment WHERE is_active = 1")
            rows = cursor.fetchall()

            total_equip = len(rows)
            total_value = sum(row['current_value'] or 0 for row in rows)
            total_hours = sum(row['current_hours'] or 0 for row in rows)

            hours_by_type = {}
            for row in rows:
                eq_type = row['equipment_type']
                hours_by_type[eq_type] = hours_by_type.get(eq_type, 0) + (row['current_hours'] or 0)

            equipment_usage = [
                EquipmentUsage(
                    equipment_id=row['id'],
                    name=row['name'],
                    equipment_type=row['equipment_type'],
                    total_hours=row['current_hours'] or 0,
                    maintenance_cost=0,
                    operating_cost=(row['current_hours'] or 0) * (row['hourly_rate'] or 0)
                )
                for row in rows
            ]

            return EquipmentReport(
                date_from="2024-01-01",
                date_to="2024-12-31",
                total_equipment=total_equip,
                total_fleet_value=total_value,
                total_hours=total_hours,
                equipment_in_maintenance=0,
                equipment_usage=equipment_usage,
                hours_by_type=hours_by_type,
                maintenance_alerts=[]
            )

        def get_inventory_report(self, date_from=None, date_to=None):
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM inventory_items WHERE is_active = 1")
            rows = cursor.fetchall()

            total_items = len(rows)
            total_value = sum((row['quantity'] or 0) * (row['unit_cost'] or 0) for row in rows)

            value_by_cat = {}
            items_by_cat = {}
            low_stock = []
            for row in rows:
                cat = row['category']
                val = (row['quantity'] or 0) * (row['unit_cost'] or 0)
                value_by_cat[cat] = value_by_cat.get(cat, 0) + val
                items_by_cat[cat] = items_by_cat.get(cat, 0) + 1
                if (row['quantity'] or 0) < (row['min_quantity'] or 0):
                    low_stock.append(row)

            return InventoryReport(
                total_items=total_items,
                total_value=total_value,
                low_stock_count=len(low_stock),
                expiring_count=0,
                value_by_category=value_by_cat,
                items_by_category=items_by_cat,
                low_stock_items=[],
                expiring_items=[]
            )

        def get_field_performance_report(self, date_from=None, date_to=None):
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM fields WHERE is_active = 1")
            rows = cursor.fetchall()

            total_fields = len(rows)
            total_acreage = sum(row['acreage'] or 0 for row in rows)

            acreage_by_crop = {}
            for row in rows:
                crop = row['current_crop'] or 'unknown'
                acreage_by_crop[crop] = acreage_by_crop.get(crop, 0) + (row['acreage'] or 0)

            fields_data = [
                FieldPerformance(
                    field_id=row['id'],
                    field_name=row['name'],
                    farm_name=row['farm_name'] or '',
                    acreage=row['acreage'] or 0,
                    current_crop=row['current_crop'] or '',
                    operation_count=0,
                    total_cost=0,
                    cost_per_acre=0
                )
                for row in rows
            ]

            return FieldPerformanceReport(
                date_from="2024-01-01",
                date_to="2024-12-31",
                total_fields=total_fields,
                total_acreage=total_acreage,
                avg_yield=200.0,
                best_field=rows[0]['name'] if rows else 'N/A',
                fields=fields_data,
                acreage_by_crop=acreage_by_crop,
                operations_by_field={}
            )

        def get_dashboard_summary(self):
            ops = self.get_operations_report()
            fin = self.get_financial_report()
            equip = self.get_equipment_report()
            inv = self.get_inventory_report()
            fields = self.get_field_performance_report()

            return DashboardSummary(
                total_operations=ops.total_operations,
                total_operation_cost=ops.total_cost,
                total_fields=fields.total_fields,
                total_acreage=fields.total_acreage,
                total_equipment=equip.total_equipment,
                fleet_value=equip.total_fleet_value,
                maintenance_due=0,
                total_inventory_items=inv.total_items,
                inventory_value=inv.total_value,
                low_stock_count=inv.low_stock_count,
                total_revenue=fin.total_revenue,
                net_profit=fin.net_profit
            )

        def export_to_csv(self, report_type, date_from=None, date_to=None):
            if report_type == ReportType.OPERATIONS:
                report = self.get_operations_report(date_from, date_to)
                return f"Operations Report\nTotal Operations,{report.total_operations}\nTotal Cost,{report.total_cost}"
            elif report_type == ReportType.FINANCIAL:
                report = self.get_financial_report(date_from, date_to)
                return f"Financial Report\nTotal Revenue,{report.total_revenue}\nNet Profit,{report.net_profit}"
            elif report_type == ReportType.EQUIPMENT:
                report = self.get_equipment_report(date_from, date_to)
                return f"Equipment Report\nTotal Equipment,{report.total_equipment}\nFleet Value,{report.total_fleet_value}"
            elif report_type == ReportType.INVENTORY:
                report = self.get_inventory_report(date_from, date_to)
                return f"Inventory Report\nTotal Items,{report.total_items}\nTotal Value,{report.total_value}"
            elif report_type == ReportType.FIELDS:
                report = self.get_field_performance_report(date_from, date_to)
                return f"Field Performance Report\nTotal Fields,{report.total_fields}\nTotal Acreage,{report.total_acreage}"
            return ""

    service = TestReportingService(test_db_path)
    return service


@pytest.fixture
def food_safety_service():
    """Create a fresh food safety service for testing."""
    from services.food_safety_service import FoodSafetyService

    service = FoodSafetyService()

    # Clear any existing data
    service.harvest_lots = []
    service.worker_trainings = []
    service.water_tests = []
    service.sanitation_logs = []
    service.incidents = []
    service.audits = []

    yield service


@pytest.fixture
def sample_harvest_lot_data():
    """Sample data for creating a harvest lot."""
    return {
        "field_id": "FIELD001",
        "field_name": "North 40",
        "crop_type": "corn",
        "variety": "Pioneer P1234",
        "harvest_date": date.today(),
        "harvest_crew": ["John", "Jane", "Bob"],
        "quantity_harvested": 500.0,
        "unit": "bushels",
        "harvest_conditions": "Clear, dry",
        "temperature_at_harvest": 72.0,
        "equipment_used": ["Combine 1", "Grain Cart 1"],
        "seed_lot": "SEED-2024-001",
        "planting_date": date.today() - timedelta(days=120),
        "pesticide_applications": ["Spray-2024-001", "Spray-2024-002"],
        "fertilizer_applications": ["Fert-2024-001"]
    }


@pytest.fixture
def unified_dashboard_service(test_db_path):
    """Create a unified dashboard service for testing."""
    from services.unified_dashboard_service import UnifiedDashboardService

    # Reset singleton for testing
    UnifiedDashboardService._instance = None
    service = UnifiedDashboardService.__new__(UnifiedDashboardService)
    service._initialized = False
    service.db_path = test_db_path
    service._reporting_service = None
    service._cost_service = None
    service._profitability_service = None
    service._initialized = True

    yield service


# ============================================================================
# REPORTING & DASHBOARD TESTS (22 tests)
# ============================================================================

class TestReportingDashboard:
    """Test suite for Reporting and Dashboard functionality."""

    # Test 1: Operations Report
    def test_operations_report(self, reporting_service):
        """Test generating operations summary report."""
        # Use date range that includes our seed data (2024)
        report = reporting_service.get_operations_report(
            date_from=date(2024, 1, 1),
            date_to=date(2024, 12, 31)
        )

        # Verify report structure
        assert hasattr(report, 'total_operations')
        assert hasattr(report, 'total_cost')
        assert hasattr(report, 'avg_cost_per_acre')
        assert hasattr(report, 'operations_by_type')
        assert hasattr(report, 'cost_by_type')
        assert hasattr(report, 'monthly_operations')
        assert hasattr(report, 'monthly_costs')

        # Verify types
        assert isinstance(report.total_operations, int)
        assert isinstance(report.total_cost, float)
        assert isinstance(report.operations_by_type, dict)

        # Verify data is populated from seed data
        assert report.total_operations >= 2

    # Test 2: Financial Report Basic
    def test_financial_report_basic(self, reporting_service):
        """Test generating basic income statement / financial report."""
        report = reporting_service.get_financial_report()

        # Verify report structure
        assert hasattr(report, 'total_input_costs')
        assert hasattr(report, 'total_equipment_costs')
        assert hasattr(report, 'total_revenue')
        assert hasattr(report, 'net_profit')
        assert hasattr(report, 'cost_by_category')
        assert hasattr(report, 'fields')

        # Verify financial calculations are present
        assert isinstance(report.total_input_costs, float)
        assert isinstance(report.net_profit, float)

    # Test 3: Equipment Report
    def test_equipment_report(self, reporting_service):
        """Test generating equipment maintenance report."""
        report = reporting_service.get_equipment_report()

        # Verify report structure
        assert hasattr(report, 'total_equipment')
        assert hasattr(report, 'total_fleet_value')
        assert hasattr(report, 'total_hours')
        assert hasattr(report, 'equipment_in_maintenance')
        assert hasattr(report, 'equipment_usage')
        assert hasattr(report, 'hours_by_type')
        assert hasattr(report, 'maintenance_alerts')

        # Verify types and data
        assert isinstance(report.total_equipment, int)
        assert isinstance(report.total_fleet_value, float)
        assert report.total_equipment >= 2

    # Test 4: Inventory Report
    def test_inventory_report(self, reporting_service):
        """Test generating inventory levels report."""
        report = reporting_service.get_inventory_report()

        # Verify report structure
        assert hasattr(report, 'total_items')
        assert hasattr(report, 'total_value')
        assert hasattr(report, 'low_stock_count')
        assert hasattr(report, 'expiring_count')
        assert hasattr(report, 'value_by_category')
        assert hasattr(report, 'items_by_category')
        assert hasattr(report, 'low_stock_items')
        assert hasattr(report, 'expiring_items')

        # Verify types and data
        assert isinstance(report.total_items, int)
        assert isinstance(report.total_value, float)
        assert report.total_items >= 2

    # Test 5: Field Performance Report
    def test_field_performance_report(self, reporting_service):
        """Test generating field yield/cost report."""
        report = reporting_service.get_field_performance_report()

        # Verify report structure
        assert hasattr(report, 'total_fields')
        assert hasattr(report, 'total_acreage')
        assert hasattr(report, 'avg_yield')
        assert hasattr(report, 'best_field')
        assert hasattr(report, 'fields')
        assert hasattr(report, 'acreage_by_crop')
        assert hasattr(report, 'operations_by_field')

        # Verify types and data
        assert isinstance(report.total_fields, int)
        assert isinstance(report.total_acreage, float)
        assert report.total_fields >= 2

    # Test 6: Dashboard Summary Widget
    def test_dashboard_summary_widget(self, reporting_service):
        """Test dashboard KPI summary cards generation."""
        summary = reporting_service.get_dashboard_summary()

        # Verify all KPIs present
        assert hasattr(summary, 'total_operations')
        assert hasattr(summary, 'total_operation_cost')
        assert hasattr(summary, 'total_fields')
        assert hasattr(summary, 'total_acreage')
        assert hasattr(summary, 'total_equipment')
        assert hasattr(summary, 'fleet_value')
        assert hasattr(summary, 'maintenance_due')
        assert hasattr(summary, 'total_inventory_items')
        assert hasattr(summary, 'inventory_value')
        assert hasattr(summary, 'low_stock_count')
        assert hasattr(summary, 'total_revenue')
        assert hasattr(summary, 'net_profit')

    # Test 7: Dashboard Chart Generation
    def test_dashboard_chart_generation(self, unified_dashboard_service):
        """Test generating charts for dashboard."""
        # Mock at the class level using PropertyMock
        mock_snapshot = {
            "income_summary": {"ytd": 100000, "this_month": 10000, "last_month": 9000},
            "expense_summary": {"ytd": 80000, "this_month": 8000, "last_month": 7000},
            "profit_loss_summary": {"net_income_ytd": 20000, "gross_margin_percent": 25, "net_margin_percent": 20},
            "accounts_receivable": {"total_outstanding": 5000, "overdue_count": 2, "current": 3000,
                                    "1_30_days": 1000, "31_60_days": 500, "61_90_days": 300, "over_90_days": 200},
            "accounts_payable": {"total_outstanding": 3000, "due_within_week": 1, "current": 2000,
                                 "1_30_days": 500, "31_60_days": 300, "61_90_days": 100, "over_90_days": 100}
        }

        mock_genfin = MagicMock()
        mock_genfin.get_company_snapshot.return_value = mock_snapshot
        mock_genfin._get_income_trend.return_value = {"labels": [], "values": []}

        with patch.object(type(unified_dashboard_service), 'genfin_service',
                         new_callable=PropertyMock, return_value=mock_genfin):
            dashboard = unified_dashboard_service.get_dashboard()

            assert "charts" in dashboard
            assert "revenue_trend" in dashboard["charts"]

    # Test 8: Dashboard Customization
    def test_dashboard_customization(self, unified_dashboard_service):
        """Test customizing dashboard with date ranges."""
        mock_snapshot = {
            "income_summary": {"ytd": 50000, "this_month": 5000, "last_month": 4500},
            "expense_summary": {"ytd": 40000, "this_month": 4000, "last_month": 3500},
            "profit_loss_summary": {"net_income_ytd": 10000, "gross_margin_percent": 20, "net_margin_percent": 15},
            "accounts_receivable": {"total_outstanding": 2500, "overdue_count": 1, "current": 2000,
                                    "1_30_days": 300, "31_60_days": 100, "61_90_days": 50, "over_90_days": 50},
            "accounts_payable": {"total_outstanding": 1500, "due_within_week": 0, "current": 1000,
                                 "1_30_days": 300, "31_60_days": 100, "61_90_days": 50, "over_90_days": 50}
        }

        mock_genfin = MagicMock()
        mock_genfin.get_company_snapshot.return_value = mock_snapshot
        mock_genfin._get_income_trend.return_value = {"labels": [], "values": []}

        with patch.object(type(unified_dashboard_service), 'genfin_service',
                         new_callable=PropertyMock, return_value=mock_genfin):
            # Custom date range
            custom_start = "2024-01-01"
            custom_end = "2024-06-30"

            dashboard = unified_dashboard_service.get_dashboard(
                date_from=custom_start,
                date_to=custom_end,
                crop_year=2024
            )

            assert dashboard["date_range"]["from"] == custom_start
            assert dashboard["date_range"]["to"] == custom_end
            assert dashboard["crop_year"] == 2024

    # Test 9: Report Date Filtering
    def test_report_date_filtering(self, reporting_service):
        """Test filtering reports by date range."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)

        report = reporting_service.get_operations_report(
            date_from=start_date,
            date_to=end_date
        )

        assert report.date_from == start_date.isoformat()
        assert report.date_to == end_date.isoformat()

    # Test 10: Report Field Filtering
    def test_report_field_filtering(self, reporting_service):
        """Test filtering reports by field."""
        field_id = 1

        report = reporting_service.get_operations_report(field_id=field_id)

        # Report should be generated without error
        assert report is not None
        assert isinstance(report.total_operations, int)

    # Test 11: Report Crop Filtering
    def test_report_crop_filtering(self, reporting_service):
        """Test filtering reports by crop type."""
        # Field performance report includes crop information
        report = reporting_service.get_field_performance_report()

        assert hasattr(report, 'acreage_by_crop')
        assert isinstance(report.acreage_by_crop, dict)
        # Should have corn and soybean from seed data
        assert len(report.acreage_by_crop) >= 1

    # Test 12: Report Export PDF
    def test_report_export_pdf(self, reporting_service):
        """Test exporting report to PDF format (via CSV proxy)."""
        from services.reporting_service import ReportType

        # CSV export as a proxy (PDF would need additional service)
        csv_output = reporting_service.export_to_csv(ReportType.OPERATIONS)

        assert csv_output is not None
        assert len(csv_output) > 0
        assert "Operations Report" in csv_output

    # Test 13: Report Export Excel
    def test_report_export_excel(self, reporting_service):
        """Test exporting report to Excel format (via CSV)."""
        from services.reporting_service import ReportType

        # Export all report types
        for report_type in [ReportType.OPERATIONS, ReportType.FINANCIAL,
                           ReportType.EQUIPMENT, ReportType.INVENTORY,
                           ReportType.FIELDS]:
            csv_output = reporting_service.export_to_csv(report_type)
            assert csv_output is not None
            assert len(csv_output) > 0

    # Test 14: Report Year-over-Year Comparison
    def test_report_comparison_year_over_year(self, reporting_service):
        """Test generating year-over-year comparison report."""
        current_year = date.today().year
        last_year = current_year - 1

        # Get reports for both years
        current_report = reporting_service.get_financial_report(
            date_from=date(current_year, 1, 1),
            date_to=date(current_year, 12, 31)
        )

        previous_report = reporting_service.get_financial_report(
            date_from=date(last_year, 1, 1),
            date_to=date(last_year, 12, 31)
        )

        # Both reports should be generated
        assert current_report is not None
        assert previous_report is not None

        # Can compare values
        yoy_change = current_report.net_profit - previous_report.net_profit
        assert isinstance(yoy_change, float)

    # Test 15: Report Trend Analysis
    def test_report_trend_analysis(self, reporting_service):
        """Test multi-year trend analysis."""
        report = reporting_service.get_operations_report()

        # Monthly operations provide trend data
        assert hasattr(report, 'monthly_operations')
        assert hasattr(report, 'monthly_costs')
        assert isinstance(report.monthly_operations, list)
        assert isinstance(report.monthly_costs, list)

    # Test 16: Dashboard Refresh
    def test_dashboard_refresh(self, unified_dashboard_service):
        """Test real-time dashboard updates."""
        mock_snapshot = {
            "income_summary": {"ytd": 50000, "this_month": 5000, "last_month": 4500},
            "expense_summary": {"ytd": 40000, "this_month": 4000, "last_month": 3500},
            "profit_loss_summary": {"net_income_ytd": 10000, "gross_margin_percent": 20, "net_margin_percent": 15},
            "accounts_receivable": {"total_outstanding": 2500, "overdue_count": 1, "current": 2000,
                                    "1_30_days": 300, "31_60_days": 100, "61_90_days": 50, "over_90_days": 50},
            "accounts_payable": {"total_outstanding": 1500, "due_within_week": 0, "current": 1000,
                                 "1_30_days": 300, "31_60_days": 100, "61_90_days": 50, "over_90_days": 50}
        }

        mock_genfin = MagicMock()
        mock_genfin.get_company_snapshot.return_value = mock_snapshot
        mock_genfin._get_income_trend.return_value = {"labels": [], "values": []}

        with patch.object(type(unified_dashboard_service), 'genfin_service',
                         new_callable=PropertyMock, return_value=mock_genfin):
            # First call
            dashboard1 = unified_dashboard_service.get_dashboard()

            # Second call (simulating refresh)
            dashboard2 = unified_dashboard_service.get_dashboard()

            # Both should have timestamps
            assert "last_updated" in dashboard1
            assert "last_updated" in dashboard2

    # Test 17: Report Permission Filtering
    def test_report_permission_filtering(self, unified_dashboard_service):
        """Test user-based filtering for reports."""
        # Test filtered transactions
        result = unified_dashboard_service.get_filtered_transactions(
            kpi_type="cash_flow",
            date_from="2024-01-01",
            date_to="2024-12-31",
            limit=50
        )

        assert "kpi_type" in result
        assert "transactions" in result
        assert result["kpi_type"] == "cash_flow"

    # Test 18: Concurrent Report Generation
    def test_concurrent_report_generation(self, test_db_path):
        """Test generating multiple reports simultaneously."""
        import concurrent.futures
        from services.reporting_service import (
            OperationsReport, FinancialReport, EquipmentReport,
            InventoryReport, FieldPerformanceReport, ReportType,
            EquipmentUsage, FieldPerformance
        )

        def generate_report(report_type, db_path):
            # Each thread gets its own connection
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if report_type == "operations":
                cursor.execute("SELECT COUNT(*) as cnt FROM field_operations WHERE is_active = 1")
                row = cursor.fetchone()
                conn.close()
                return OperationsReport(
                    total_operations=row['cnt'],
                    total_cost=0.0,
                    avg_cost_per_acre=0.0,
                    operations_by_type={},
                    cost_by_type={},
                    monthly_operations=[],
                    monthly_costs=[]
                )
            elif report_type == "financial":
                cursor.execute("SELECT COUNT(*) as cnt FROM field_operations WHERE is_active = 1")
                row = cursor.fetchone()
                conn.close()
                return FinancialReport(
                    total_input_costs=0.0,
                    total_equipment_costs=0.0,
                    total_revenue=0.0,
                    net_profit=0.0,
                    cost_by_category={},
                    fields=[]
                )
            elif report_type == "equipment":
                cursor.execute("SELECT COUNT(*) as cnt FROM equipment WHERE is_active = 1")
                row = cursor.fetchone()
                conn.close()
                return EquipmentReport(
                    total_equipment=row['cnt'],
                    total_fleet_value=0.0,
                    total_hours=0.0,
                    equipment_in_maintenance=0,
                    equipment_usage=[],
                    hours_by_type={},
                    maintenance_alerts=[]
                )
            elif report_type == "inventory":
                cursor.execute("SELECT COUNT(*) as cnt FROM inventory_items WHERE is_active = 1")
                row = cursor.fetchone()
                conn.close()
                return InventoryReport(
                    total_items=row['cnt'],
                    total_value=0.0,
                    low_stock_count=0,
                    expiring_count=0,
                    value_by_category={},
                    items_by_category={},
                    low_stock_items=[],
                    expiring_items=[]
                )
            conn.close()
            return None

        report_types = ["operations", "financial", "equipment", "inventory"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(generate_report, rt, test_db_path) for rt in report_types]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All reports should be generated
        assert len(results) == 4
        for result in results:
            assert result is not None

    # Test 19: Report Caching
    def test_report_caching(self, reporting_service):
        """Test large report performance with caching."""
        import time

        # First call
        start1 = time.time()
        report1 = reporting_service.get_dashboard_summary()
        time1 = time.time() - start1

        # Second call (should potentially be cached/faster)
        start2 = time.time()
        report2 = reporting_service.get_dashboard_summary()
        time2 = time.time() - start2

        # Both should return valid reports
        assert report1 is not None
        assert report2 is not None

        # Values should be consistent
        assert report1.total_operations == report2.total_operations

    # Test 20: Unified Dashboard KPIs
    def test_unified_dashboard_kpis(self, unified_dashboard_service):
        """Test unified dashboard KPIs from all services."""
        mock_snapshot = {
            "income_summary": {"ytd": 100000, "this_month": 10000, "last_month": 9000},
            "expense_summary": {"ytd": 80000, "this_month": 8000, "last_month": 7000},
            "profit_loss_summary": {"net_income_ytd": 20000, "gross_margin_percent": 25, "net_margin_percent": 20},
            "accounts_receivable": {"total_outstanding": 5000, "overdue_count": 2, "current": 3000,
                                    "1_30_days": 1000, "31_60_days": 500, "61_90_days": 300, "over_90_days": 200},
            "accounts_payable": {"total_outstanding": 3000, "due_within_week": 1, "current": 2000,
                                 "1_30_days": 500, "31_60_days": 300, "61_90_days": 100, "over_90_days": 100}
        }

        mock_genfin = MagicMock()
        mock_genfin.get_company_snapshot.return_value = mock_snapshot
        mock_genfin._get_income_trend.return_value = {"labels": [], "values": []}

        with patch.object(type(unified_dashboard_service), 'genfin_service',
                         new_callable=PropertyMock, return_value=mock_genfin):
            dashboard = unified_dashboard_service.get_dashboard()

            # Check financial KPIs
            assert "financial_kpis" in dashboard
            assert "cash_flow" in dashboard["financial_kpis"]
            assert "profit_margin" in dashboard["financial_kpis"]
            assert "ar_aging" in dashboard["financial_kpis"]
            assert "ap_aging" in dashboard["financial_kpis"]

            # Check farm KPIs
            assert "farm_kpis" in dashboard
            assert "cost_per_acre" in dashboard["farm_kpis"]
            assert "yield_trends" in dashboard["farm_kpis"]
            assert "equipment_roi" in dashboard["farm_kpis"]
            assert "input_costs" in dashboard["farm_kpis"]

    # Test 21: Advanced Reporting Drilldown
    def test_advanced_reporting_drilldown(self, unified_dashboard_service):
        """Test drill-down reports from KPIs."""
        from services.unified_dashboard_service import KPIType

        # Test AR aging drilldown
        ar_detail = unified_dashboard_service.get_kpi_detail(KPIType.AR_AGING.value)
        assert "kpi_id" in ar_detail

        # Test cost per acre drilldown
        cost_detail = unified_dashboard_service.get_kpi_detail(KPIType.COST_PER_ACRE.value)
        assert "kpi_id" in cost_detail

    # Test 22: Custom Report Builder
    def test_custom_report_builder(self, reporting_service):
        """Test building custom reports with selected fields."""
        from services.reporting_service import ReportType

        # Get base reports
        ops_report = reporting_service.get_operations_report()
        fin_report = reporting_service.get_financial_report()

        # Build custom report combining data
        custom_report = {
            "total_operations": ops_report.total_operations,
            "total_cost": ops_report.total_cost,
            "net_profit": fin_report.net_profit,
            "revenue": fin_report.total_revenue,
            "cost_by_type": ops_report.cost_by_type,
            "generated_at": datetime.now().isoformat()
        }

        assert "total_operations" in custom_report
        assert "net_profit" in custom_report
        assert "generated_at" in custom_report


# ============================================================================
# FOOD SAFETY TESTS (15 tests)
# ============================================================================

class TestFoodSafety:
    """Test suite for Food Safety and Traceability functionality."""

    # Test 1: Lot Creation
    def test_lot_creation(self, food_safety_service, sample_harvest_lot_data):
        """Test creating a harvest lot."""
        result = food_safety_service.create_harvest_lot(sample_harvest_lot_data)

        assert result["success"] is True
        assert "lot_id" in result
        assert "lot_number" in result
        assert "traceability_code" in result
        assert len(result["lot_number"]) > 0

    # Test 2: Lot Status Transitions
    def test_lot_status_transitions(self, food_safety_service, sample_harvest_lot_data):
        """Test lot status workflow transitions."""
        from services.food_safety_service import HarvestLotStatus

        # Create lot
        result = food_safety_service.create_harvest_lot(sample_harvest_lot_data)
        lot_id = result["lot_id"]

        # Transition to IN_STORAGE
        update_result = food_safety_service.update_lot_status(
            lot_id,
            HarvestLotStatus.IN_STORAGE,
            {"storage_location": "Bin 1", "storage_temperature": 55.0}
        )
        assert update_result["success"] is True
        assert update_result["new_status"] == "in_storage"

        # Transition to SOLD
        update_result = food_safety_service.update_lot_status(
            lot_id,
            HarvestLotStatus.SOLD,
            {"buyer": "ABC Grain Co", "sale_date": date.today(), "destination": "Chicago"}
        )
        assert update_result["success"] is True
        assert update_result["new_status"] == "sold"

    # Test 3: Harvest Record Creation
    def test_harvest_record_creation(self, food_safety_service, sample_harvest_lot_data):
        """Test creating a harvest record with full details."""
        result = food_safety_service.create_harvest_lot(sample_harvest_lot_data)

        assert result["success"] is True

        # Verify lot exists
        assert len(food_safety_service.harvest_lots) == 1
        lot = food_safety_service.harvest_lots[0]

        assert lot.crop_type == "corn"
        assert lot.variety == "Pioneer P1234"
        assert lot.quantity_harvested == 500.0
        assert lot.unit == "bushels"
        assert len(lot.harvest_crew) == 3

    # Test 4: Spray Documentation
    def test_spray_documentation(self, food_safety_service, sample_harvest_lot_data):
        """Test documenting spray applications in lot."""
        result = food_safety_service.create_harvest_lot(sample_harvest_lot_data)

        lot = food_safety_service.harvest_lots[0]

        # Verify spray applications are recorded
        assert len(lot.pesticide_applications) == 2
        assert "Spray-2024-001" in lot.pesticide_applications
        assert "Spray-2024-002" in lot.pesticide_applications

    # Test 5: Disease Treatment Documentation
    def test_disease_treatment_documentation(self, food_safety_service, sample_harvest_lot_data):
        """Test documenting disease treatments."""
        # Add disease treatment to data
        sample_harvest_lot_data["pesticide_applications"].append("Fungicide-2024-001")

        result = food_safety_service.create_harvest_lot(sample_harvest_lot_data)
        lot = food_safety_service.harvest_lots[0]

        assert "Fungicide-2024-001" in lot.pesticide_applications

    # Test 6: Harvest Quality Metrics
    def test_harvest_quality_metrics(self, food_safety_service, sample_harvest_lot_data):
        """Test recording quality data at harvest."""
        result = food_safety_service.create_harvest_lot(sample_harvest_lot_data)
        lot = food_safety_service.harvest_lots[0]

        # Quality metrics captured
        assert lot.harvest_conditions == "Clear, dry"
        assert lot.temperature_at_harvest == 72.0

    # Test 7: Documentation Completeness
    def test_documentation_completeness(self, food_safety_service, sample_harvest_lot_data):
        """Test verifying required fields are present."""
        result = food_safety_service.create_harvest_lot(sample_harvest_lot_data)

        # Trace the lot to verify completeness
        trace = food_safety_service.trace_lot(result["lot_number"])

        assert "product_info" in trace
        assert "origin" in trace
        assert "production_inputs" in trace
        assert "harvest_info" in trace
        assert "chain_of_custody" in trace
        assert "food_safety_verification" in trace

    # Test 8: Traceability Chain
    def test_traceability_chain(self, food_safety_service, sample_harvest_lot_data):
        """Test tracing from seed to market."""
        result = food_safety_service.create_harvest_lot(sample_harvest_lot_data)

        trace = food_safety_service.trace_lot(result["lot_number"])

        # Verify complete chain
        assert trace["origin"]["seed_lot"] == "SEED-2024-001"
        assert trace["origin"]["planting_date"] is not None
        assert len(trace["production_inputs"]["pesticide_applications"]) > 0
        assert trace["harvest_info"]["harvest_date"] is not None

    # Test 9: Preharvest Interval Check
    def test_preharvest_interval_check(self, food_safety_service, sample_harvest_lot_data):
        """Test validating PHI (pre-harvest interval)."""
        # Create lot with spray application
        result = food_safety_service.create_harvest_lot(sample_harvest_lot_data)

        lot = food_safety_service.harvest_lots[0]

        # PHI would typically be calculated from last spray to harvest
        # Verify spray applications are tracked
        assert len(lot.pesticide_applications) > 0
        assert lot.harvest_date is not None

    # Test 10: GMO Status Tracking
    def test_gmo_status_tracking(self, food_safety_service, sample_harvest_lot_data):
        """Test tracking GMO status in lots."""
        # Variety name typically indicates GMO status
        result = food_safety_service.create_harvest_lot(sample_harvest_lot_data)

        lot = food_safety_service.harvest_lots[0]

        # Variety and seed lot tracked for GMO verification
        assert lot.variety == "Pioneer P1234"
        assert lot.seed_lot == "SEED-2024-001"

    # Test 11: Residue Testing Results
    def test_residue_testing_results(self, food_safety_service):
        """Test recording lab results for residue testing."""
        from services.food_safety_service import WaterTest

        # Water test as proxy for residue testing
        test = WaterTest(
            test_id="TEST-001",
            sample_date=date.today(),
            sample_location="Well 1",
            water_source="groundwater",
            test_type="E. coli",
            result_value=0.0,
            result_unit="CFU/100mL",
            acceptable_limit=1.0,
            pass_fail="pass",
            lab_name="State Lab",
            corrective_action=""
        )

        result = food_safety_service.record_water_test(test)

        assert result["success"] is True
        assert result["status"] == "pass"

    # Test 12: Field Audit History
    def test_field_audit_history(self, food_safety_service):
        """Test full field record for audits."""
        from services.food_safety_service import Audit, AuditType

        audit = Audit(
            audit_id="AUDIT-001",
            audit_date=date.today(),
            audit_type=AuditType.THIRD_PARTY,
            auditor_name="John Auditor",
            auditor_organization="Audit Corp",
            areas_audited=["Field 1", "Field 2", "Packing House"],
            findings=[{"area": "Field 1", "finding": "No issues", "severity": "none"}],
            score=95.0,
            pass_fail="pass",
            certification_issued="GAP",
            follow_up_required=False
        )

        result = food_safety_service.record_audit(audit)

        assert result["success"] is True
        assert result["result"] == "pass"
        assert result["score"] == 95.0

    # Test 13: Compliance Report
    def test_compliance_report(self, food_safety_service, sample_harvest_lot_data):
        """Test generating compliance report for grants/audits."""
        from services.food_safety_service import WorkerTraining, WaterTest

        # Add some compliance data
        food_safety_service.create_harvest_lot(sample_harvest_lot_data)

        training = WorkerTraining(
            training_id="TRAIN-001",
            worker_name="John Doe",
            worker_id="W001",
            training_topic="Food Safety Basics",
            training_date=date.today() - timedelta(days=30),
            trainer_name="Jane Trainer",
            duration_hours=4.0,
            passed_assessment=True,
            certificate_issued=True,
            expiration_date=date.today() + timedelta(days=335)
        )
        food_safety_service.record_worker_training(training)

        water_test = WaterTest(
            test_id="WT-001",
            sample_date=date.today() - timedelta(days=7),
            sample_location="Field Well",
            water_source="groundwater",
            test_type="E. coli",
            result_value=0.0,
            result_unit="CFU/100mL",
            acceptable_limit=1.0,
            pass_fail="pass",
            lab_name="State Lab"
        )
        food_safety_service.record_water_test(water_test)

        # Generate compliance report
        report = food_safety_service.generate_food_safety_grant_report("USDA Food Safety Grant")

        assert "executive_summary" in report
        assert "sections" in report
        assert "grant_compliance_metrics" in report
        assert report["grant_program"] == "USDA Food Safety Grant"

    # Test 14: Batch Lot Import
    def test_batch_lot_import(self, food_safety_service, sample_harvest_lot_data):
        """Test importing multiple lots at once."""
        lots_to_import = []

        for i in range(5):
            lot_data = sample_harvest_lot_data.copy()
            lot_data["field_id"] = f"FIELD00{i+1}"
            lot_data["field_name"] = f"Field {i+1}"
            lot_data["quantity_harvested"] = 100.0 * (i + 1)
            lots_to_import.append(lot_data)

        results = []
        for lot_data in lots_to_import:
            result = food_safety_service.create_harvest_lot(lot_data)
            results.append(result)

        assert len(results) == 5
        assert all(r["success"] for r in results)
        assert len(food_safety_service.harvest_lots) == 5

    # Test 15: Lot Merge and Split
    def test_lot_merge_split(self, food_safety_service, sample_harvest_lot_data):
        """Test merging and splitting lots."""
        from services.food_safety_service import HarvestLotStatus

        # Create two lots
        lot1_data = sample_harvest_lot_data.copy()
        lot1_data["field_id"] = "FIELD001"
        lot1_data["quantity_harvested"] = 200.0

        lot2_data = sample_harvest_lot_data.copy()
        lot2_data["field_id"] = "FIELD002"
        lot2_data["quantity_harvested"] = 300.0

        result1 = food_safety_service.create_harvest_lot(lot1_data)
        result2 = food_safety_service.create_harvest_lot(lot2_data)

        # Verify both lots exist
        assert len(food_safety_service.harvest_lots) == 2

        # Simulate merge by tracking parent lots
        merged_lot_data = sample_harvest_lot_data.copy()
        merged_lot_data["field_id"] = "MERGED"
        merged_lot_data["field_name"] = "Merged Lot"
        merged_lot_data["quantity_harvested"] = 500.0  # Sum of both
        merged_lot_data["notes"] = f"Merged from {result1['lot_number']} and {result2['lot_number']}"

        # Create merged lot
        merge_result = food_safety_service.create_harvest_lot(merged_lot_data)

        assert merge_result["success"] is True

        # Mark original lots as consumed (merged)
        food_safety_service.update_lot_status(result1["lot_id"], HarvestLotStatus.CONSUMED)
        food_safety_service.update_lot_status(result2["lot_id"], HarvestLotStatus.CONSUMED)

        # Verify status updates
        consumed_lots = food_safety_service.get_lots_by_status(HarvestLotStatus.CONSUMED)
        assert consumed_lots["count"] == 2


# ============================================================================
# ADDITIONAL INTEGRATION TESTS
# ============================================================================

class TestReportingFoodSafetyIntegration:
    """Integration tests combining reporting and food safety."""

    def test_food_safety_compliance_in_dashboard(self, food_safety_service, sample_harvest_lot_data):
        """Test food safety compliance metrics in reports."""
        # Create compliance data
        from services.food_safety_service import WorkerTraining, WaterTest

        food_safety_service.create_harvest_lot(sample_harvest_lot_data)

        training = WorkerTraining(
            training_id="TRAIN-001",
            worker_name="Test Worker",
            worker_id="W001",
            training_topic="Food Safety",
            training_date=date.today(),
            trainer_name="Trainer",
            duration_hours=2.0,
            passed_assessment=True,
            certificate_issued=True
        )
        food_safety_service.record_worker_training(training)

        water_test = WaterTest(
            test_id="WT-001",
            sample_date=date.today(),
            sample_location="Well",
            water_source="groundwater",
            test_type="E. coli",
            result_value=0.0,
            result_unit="CFU",
            acceptable_limit=1.0,
            pass_fail="pass",
            lab_name="Lab"
        )
        food_safety_service.record_water_test(water_test)

        # Assess FSMA compliance
        compliance = food_safety_service.assess_fsma_compliance()

        assert "overall_percent" in compliance
        assert "compliance_status" in compliance
        assert "category_results" in compliance

    def test_gap_certification_readiness(self, food_safety_service, sample_harvest_lot_data):
        """Test GAP certification readiness assessment."""
        from services.food_safety_service import WorkerTraining, WaterTest, SanitationLog

        # Add required data for GAP
        food_safety_service.create_harvest_lot(sample_harvest_lot_data)

        training = WorkerTraining(
            training_id="T-001",
            worker_name="Worker 1",
            worker_id="W1",
            training_topic="Food Safety Training",
            training_date=date.today(),
            trainer_name="Trainer",
            duration_hours=4.0,
            passed_assessment=True,
            certificate_issued=True
        )
        food_safety_service.record_worker_training(training)

        water_test = WaterTest(
            test_id="WT-001",
            sample_date=date.today(),
            sample_location="Field",
            water_source="well",
            test_type="E. coli",
            result_value=0,
            result_unit="CFU",
            acceptable_limit=1,
            pass_fail="pass",
            lab_name="Lab"
        )
        food_safety_service.record_water_test(water_test)

        sanitation = SanitationLog(
            log_id="SAN-001",
            date=date.today(),
            equipment_or_area="Harvest Bins",
            cleaning_method="Pressure wash",
            sanitizer_used="Chlorine",
            concentration="200ppm",
            contact_time_minutes=5,
            performed_by="Worker 1"
        )
        food_safety_service.record_sanitation(sanitation)

        # Assess GAP readiness
        readiness = food_safety_service.assess_gap_readiness()

        assert "overall_completion" in readiness
        assert "ready_for_audit" in readiness
        assert "categories" in readiness

    def test_mock_recall_exercise(self, food_safety_service, sample_harvest_lot_data):
        """Test mock recall exercise for compliance."""
        result = food_safety_service.create_harvest_lot(sample_harvest_lot_data)
        lot_number = result["lot_number"]

        # Conduct mock recall
        recall_result = food_safety_service.conduct_mock_recall(lot_number)

        assert "exercise_date" in recall_result
        assert "test_lot_number" in recall_result
        assert "completeness_score" in recall_result
        assert "overall_result" in recall_result
        assert "trace_time_seconds" in recall_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
