"""
Pytest configuration and shared fixtures for AgTools tests.

Includes:
- Test database fixtures (SQLite in-memory)
- Auth token generation fixtures
- Authenticated client fixtures
- Sample data factories
- GenFin BDD test fixtures
"""

import os
import sys
import pytest
import tempfile
import secrets
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, Generator
from unittest.mock import MagicMock

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

# Set test environment before importing app
os.environ["AGTOOLS_DEV_MODE"] = "1"
os.environ["AGTOOLS_TEST_MODE"] = "1"

from fastapi.testclient import TestClient


# ============================================================================
# TEST DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_db_path() -> Generator[str, None, None]:
    """
    Create a temporary SQLite database for test isolation.
    Each test function gets its own fresh database.
    """
    # Create a temp file for the test database
    fd, db_path = tempfile.mkstemp(suffix=".db", prefix="agtools_test_")
    os.close(fd)

    # Set environment to use test database
    original_path = os.environ.get("AGTOOLS_DB_PATH")
    os.environ["AGTOOLS_DB_PATH"] = db_path

    yield db_path

    # Cleanup
    if original_path:
        os.environ["AGTOOLS_DB_PATH"] = original_path
    else:
        os.environ.pop("AGTOOLS_DB_PATH", None)

    # Remove temp database file
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture(scope="module")
def test_db_path_module() -> Generator[str, None, None]:
    """
    Create a temporary SQLite database for test isolation at module level.
    Shared across all tests in a module for better performance.
    """
    fd, db_path = tempfile.mkstemp(suffix=".db", prefix="agtools_test_module_")
    os.close(fd)

    original_path = os.environ.get("AGTOOLS_DB_PATH")
    os.environ["AGTOOLS_DB_PATH"] = db_path

    yield db_path

    if original_path:
        os.environ["AGTOOLS_DB_PATH"] = original_path
    else:
        os.environ.pop("AGTOOLS_DB_PATH", None)

    try:
        os.unlink(db_path)
    except OSError:
        pass


# ============================================================================
# FASTAPI TEST CLIENT FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """
    Provide a TestClient for the FastAPI application.
    Fresh client for each test function.
    """
    # Import app after env vars are set
    from main import app

    # Ensure all services are initialized (creates their tables)
    # This is needed because some services have cross-table dependencies
    from services.field_operations_service import get_field_operations_service
    from services.base_service import ServiceRegistry
    from services.user_service import get_user_service
    from services.auth_service import get_auth_service

    # Clear cached service instances to ensure fresh DB path is used
    ServiceRegistry.clear()

    # Initialize field_operations_service to create its table
    # (field_service queries depend on this table existing)
    get_field_operations_service()

    # Initialize user service and set known test password for admin
    user_service = get_user_service()
    auth_service = get_auth_service()

    # Update admin password to known test value
    import sqlite3
    conn = sqlite3.connect(user_service.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    test_password_hash = auth_service.hash_password("admin123")
    cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'admin'", (test_password_hash,))
    conn.commit()
    conn.close()

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def client_module() -> Generator[TestClient, None, None]:
    """
    Provide a TestClient for the FastAPI application at module level.
    Shared across tests in a module for better performance.
    """
    from main import app

    with TestClient(app) as test_client:
        yield test_client


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def admin_credentials() -> Dict[str, str]:
    """Default admin credentials for testing."""
    return {
        "username": "admin",
        "password": "admin123"  # Default dev mode password
    }


@pytest.fixture(scope="function")
def test_user_data() -> Dict[str, Any]:
    """Generate unique test user data."""
    suffix = secrets.token_hex(4)
    return {
        "username": f"testuser_{suffix}",
        "email": f"testuser_{suffix}@example.com",
        "password": "TestPass123!",
        "first_name": "Test",
        "last_name": "User",
        "phone": "555-0100",
        "role": "crew"
    }


@pytest.fixture(scope="function")
def auth_token(client: TestClient, admin_credentials: Dict[str, str]) -> Optional[str]:
    """
    Get an authentication token using admin credentials.
    Returns None if authentication fails.
    """
    response = client.post(
        "/api/v1/auth/login",
        json=admin_credentials
    )

    if response.status_code == 200:
        data = response.json()
        return data.get("tokens", {}).get("access_token")
    return None


@pytest.fixture(scope="function")
def auth_headers(auth_token: Optional[str]) -> Dict[str, str]:
    """
    Provide authorization headers for authenticated requests.
    """
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


@pytest.fixture(scope="function")
def authenticated_client(client: TestClient, auth_headers: Dict[str, str]) -> TestClient:
    """
    Provide a TestClient with authentication headers pre-configured.
    """
    # Store original headers
    original_headers = client.headers.copy() if hasattr(client, 'headers') else {}

    # Add auth headers to client
    client.headers.update(auth_headers)

    yield client

    # Restore original headers
    client.headers = original_headers


# ============================================================================
# SAMPLE DATA FACTORIES
# ============================================================================

class DataFactory:
    """Factory for generating test data."""

    @staticmethod
    def field(suffix: str = None) -> Dict[str, Any]:
        """Generate test field data."""
        suffix = suffix or secrets.token_hex(4)
        return {
            "name": f"Test Field {suffix}",
            "farm_name": "Test Farm",
            "acreage": 160.5,
            "current_crop": "corn",
            "soil_type": "loam",
            "irrigation_type": "center_pivot",
            "latitude": 42.0,
            "longitude": -93.5,
            "notes": "Test field for automated testing"
        }

    @staticmethod
    def task(suffix: str = None) -> Dict[str, Any]:
        """Generate test task data."""
        suffix = suffix or secrets.token_hex(4)
        return {
            "title": f"Test Task {suffix}",
            "description": "Test task description",
            "priority": "high",
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "estimated_hours": 4.0,
            "notes": "Test task for automated testing"
        }

    @staticmethod
    def equipment(suffix: str = None) -> Dict[str, Any]:
        """Generate test equipment data."""
        suffix = suffix or secrets.token_hex(4)
        return {
            "name": f"Test Tractor {suffix}",
            "equipment_type": "tractor",
            "make": "John Deere",
            "model": "8R 410",
            "year": 2023,
            "serial_number": f"SN{suffix}",
            "purchase_cost": 350000.00,
            "status": "available",
            "current_hours": 500.0,
            "notes": "Test equipment"
        }

    @staticmethod
    def inventory_item(suffix: str = None) -> Dict[str, Any]:
        """Generate test inventory item data."""
        suffix = suffix or secrets.token_hex(4)
        return {
            "name": f"Test Herbicide {suffix}",
            "category": "herbicide",
            "quantity": 50.0,
            "unit": "gallons",
            "unit_cost": 125.00,
            "min_quantity": 10.0,
            "storage_location": "Main Barn",
            "notes": "Test inventory item"
        }

    @staticmethod
    def user(suffix: str = None, role: str = "crew") -> Dict[str, Any]:
        """Generate test user data."""
        suffix = suffix or secrets.token_hex(4)
        return {
            "username": f"testuser_{suffix}",
            "email": f"testuser_{suffix}@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
            "phone": "555-0100",
            "role": role
        }

    @staticmethod
    def gdd_record(field_id: int, suffix: str = None) -> Dict[str, Any]:
        """Generate test GDD record data."""
        return {
            "field_id": field_id,
            "record_date": datetime.now().strftime("%Y-%m-%d"),
            "high_temp_f": 85.0,
            "low_temp_f": 62.0
        }

    @staticmethod
    def csv_import_data() -> str:
        """Generate sample CSV data for import testing."""
        return """Date,Description,Amount,Category
2024-01-15,Fertilizer Purchase,1500.00,fertilizer
2024-01-16,Seed Purchase,2500.00,seed
2024-01-17,Equipment Repair,750.00,repairs"""


@pytest.fixture
def data_factory() -> DataFactory:
    """Provide access to the data factory."""
    return DataFactory()


# ============================================================================
# TEST HELPERS
# ============================================================================

@pytest.fixture
def test_ids() -> Dict[str, Optional[int]]:
    """Store created entity IDs for use across tests in a session."""
    return {
        "field_id": None,
        "task_id": None,
        "equipment_id": None,
        "inventory_id": None,
        "user_id": None,
        "crew_id": None,
        "operation_id": None,
    }


# ============================================================================
# GENFIN BDD TEST FIXTURES (Legacy - preserved for compatibility)
# ============================================================================


class MockAccount:
    """Mock bank account for testing."""
    def __init__(self, name: str, balance: Decimal = Decimal("0.00")):
        self.name = name
        self.balance = balance
        self.last_reconciled_balance = Decimal("0.00")
        self.transactions = []


class MockVendor:
    """Mock vendor for testing."""
    def __init__(self, name: str):
        self.name = name
        self.credits = []


class MockCustomer:
    """Mock customer for testing."""
    def __init__(self, name: str):
        self.name = name


class MockTransaction:
    """Mock transaction for testing."""
    def __init__(self, trans_type: str, amount: Decimal, cleared: bool = False):
        self.type = trans_type
        self.amount = amount
        self.cleared = cleared


class MockBill:
    """Mock bill for testing."""
    def __init__(self, vendor: str, amount: Decimal):
        self.vendor = vendor
        self.amount = amount
        self.status = "Unpaid"
        self.due_date = None


class MockInvoice:
    """Mock invoice for testing."""
    def __init__(self, customer: str, amount: Decimal = Decimal("0.00")):
        self.customer = customer
        self.amount = amount
        self.balance_due = amount
        self.status = "Open"
        self.line_items = []


class MockCheck:
    """Mock check for testing."""
    def __init__(self, check_number: int, amount: Decimal):
        self.check_number = check_number
        self.amount = amount
        self.status = "Pending"
        self.printed = False
        self.print_date = None
        self.expense_lines = []


class MockVendorCredit:
    """Mock vendor credit for testing."""
    def __init__(self, vendor: str, amount: Decimal):
        self.vendor = vendor
        self.amount = amount
        self.consumed = False


class GenFinTestContext:
    """Shared test context for GenFin BDD tests."""

    def __init__(self):
        self.accounts = {}
        self.vendors = {}
        self.customers = {}
        self.bills = []
        self.invoices = []
        self.checks = []
        self.purchase_orders = []
        self.next_check_number = 1001
        self.accounts_receivable = Decimal("0.00")
        self.accounts_payable = Decimal("0.00")
        self.expenses = Decimal("0.00")
        self.income = Decimal("0.00")

        # Reconciliation state
        self.statement_ending_balance = Decimal("0.00")
        self.outstanding_checks = []
        self.deposits_in_transit = []
        self.book_balance = Decimal("0.00")
        self.reconciliation_difference = Decimal("0.00")
        self.reconciliation_succeeded = False
        self.is_reconciling = False

        # Current working objects
        self.current_invoice = None
        self.current_bill = None
        self.current_check = None
        self.current_account = None

    def add_account(self, name: str, balance: Decimal = Decimal("0.00")) -> MockAccount:
        account = MockAccount(name, balance)
        self.accounts[name] = account
        return account

    def add_vendor(self, name: str) -> MockVendor:
        vendor = MockVendor(name)
        self.vendors[name] = vendor
        return vendor

    def add_customer(self, name: str) -> MockCustomer:
        customer = MockCustomer(name)
        self.customers[name] = customer
        return customer

    def get_next_check_number(self) -> int:
        num = self.next_check_number
        self.next_check_number += 1
        return num


@pytest.fixture
def genfin_context():
    """Provide a fresh GenFin test context for each scenario."""
    return GenFinTestContext()


@pytest.fixture
def initialized_system(genfin_context):
    """Provide an initialized GenFin system context."""
    # System is considered initialized when context exists
    return genfin_context
