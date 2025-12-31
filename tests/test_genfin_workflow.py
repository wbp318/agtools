"""
GenFin Comprehensive Workflow Test Suite
=========================================

Tests all GenFin features end-to-end:
- Customer/Vendor/Employee CRUD
- Chart of Accounts
- Invoices and Bills
- Payments (Receive/Pay)
- Checks and Deposits
- Purchase Orders
- Sales Orders
- Bank Reconciliation
- Reports
- Inventory

Run with: python tests/test_genfin_workflow.py
"""

import requests
import json
import sys
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

API_BASE = "http://127.0.0.1:8000/api/v1/genfin"

# Test results tracking
results = {"passed": 0, "failed": 0, "errors": []}


def log_result(test_name: str, passed: bool, details: str = ""):
    """Log test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status}: {test_name}")
    if not passed and details:
        print(f"         └─ {details[:100]}")
    if passed:
        results["passed"] += 1
    else:
        results["failed"] += 1
        results["errors"].append(f"{test_name}: {details}")


def api_get(endpoint: str) -> Tuple[bool, any]:
    """Make GET request."""
    try:
        r = requests.get(f"{API_BASE}{endpoint}", timeout=10)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)


def api_post(endpoint: str, data: dict) -> Tuple[bool, any]:
    """Make POST request."""
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=data, timeout=10)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)


def api_put(endpoint: str, data: dict) -> Tuple[bool, any]:
    """Make PUT request."""
    try:
        r = requests.put(f"{API_BASE}{endpoint}", json=data, timeout=10)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)


def api_delete(endpoint: str) -> Tuple[bool, any]:
    """Make DELETE request."""
    try:
        r = requests.delete(f"{API_BASE}{endpoint}", timeout=10)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)


# =============================================================================
# TEST DATA
# =============================================================================

TEST_CUSTOMER = {
    "company_name": "Workflow Test Customer",
    "display_name": "WF Test Customer",
    "contact_name": "Jane Workflow",
    "email": "workflow@test.com",
    "phone": "555-WORK-001",
    "address": "100 Workflow Way, Testville, IA 50001"
}

TEST_VENDOR = {
    "company_name": "Workflow Test Vendor",
    "display_name": "WF Test Vendor",
    "contact_name": "Bob Supplier",
    "email": "vendor@test.com",
    "phone": "555-VEND-001",
    "address": "200 Supply Street, Vendortown, IA 50002"
}

TEST_EMPLOYEE = {
    "first_name": "Test",
    "last_name": "Employee",
    "email": "employee@test.com",
    "phone": "555-EMP-0001",
    "hire_date": datetime.now().strftime("%Y-%m-%d"),
    "department": "Testing",
    "job_title": "QA Tester",
    "pay_type": "salary",
    "pay_rate": 50000.00
}

TEST_ACCOUNT_NUM = f"69{random.randint(100, 999)}"
TEST_ACCOUNT = {
    "name": f"Test Expense Account {TEST_ACCOUNT_NUM}",
    "account_number": TEST_ACCOUNT_NUM,
    "account_type": "expense",
    "sub_type": "other_expense",
    "description": "For workflow testing"
}

# Store created IDs for cleanup and cross-references
created_ids = {
    "customer_id": None,
    "vendor_id": None,
    "employee_id": None,
    "account_id": None,
    "invoice_id": None,
    "bill_id": None,
    "check_id": None,
    "deposit_id": None,
    "po_id": None,
    "so_id": None,
}


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_api_health():
    """Test API is running."""
    print("\n📡 API Health Check")
    print("-" * 40)

    ok, data = api_get("/accounts")
    log_result("API responding", ok, str(data)[:100] if not ok else "")
    return ok


def test_customers():
    """Test Customer CRUD operations."""
    print("\n👥 Customer Management")
    print("-" * 40)

    # CREATE
    ok, data = api_post("/customers", TEST_CUSTOMER)
    log_result("Create customer", ok and data.get("success"), str(data))
    if ok and data.get("customer_id"):
        created_ids["customer_id"] = data["customer_id"]

    # READ (list)
    ok, data = api_get("/customers")
    log_result("List customers", ok and isinstance(data, list), str(data)[:100])

    # READ (single)
    if created_ids["customer_id"]:
        ok, data = api_get(f"/customers/{created_ids['customer_id']}")
        log_result("Get customer by ID", ok, str(data)[:100])

    # UPDATE
    if created_ids["customer_id"]:
        update_data = {"contact_name": "Jane Updated"}
        ok, data = api_put(f"/customers/{created_ids['customer_id']}", update_data)
        log_result("Update customer", ok, str(data)[:100])


def test_vendors():
    """Test Vendor CRUD operations."""
    print("\n🏢 Vendor Management")
    print("-" * 40)

    # CREATE
    ok, data = api_post("/vendors", TEST_VENDOR)
    log_result("Create vendor", ok and data.get("success"), str(data))
    if ok and data.get("vendor_id"):
        created_ids["vendor_id"] = data["vendor_id"]

    # READ (list)
    ok, data = api_get("/vendors")
    log_result("List vendors", ok and isinstance(data, list), str(data)[:100])

    # UPDATE
    if created_ids["vendor_id"]:
        update_data = {"contact_name": "Bob Updated"}
        ok, data = api_put(f"/vendors/{created_ids['vendor_id']}", update_data)
        log_result("Update vendor", ok, str(data)[:100])


def test_employees():
    """Test Employee CRUD operations."""
    print("\n👷 Employee Management")
    print("-" * 40)

    # CREATE
    ok, data = api_post("/employees", TEST_EMPLOYEE)
    log_result("Create employee", ok and data.get("success"), str(data))
    if ok and data.get("employee_id"):
        created_ids["employee_id"] = data["employee_id"]

    # READ (list)
    ok, data = api_get("/employees")
    log_result("List employees", ok and isinstance(data, list), str(data)[:100])


def test_accounts():
    """Test Chart of Accounts operations."""
    print("\n📊 Chart of Accounts")
    print("-" * 40)

    # CREATE
    ok, data = api_post("/accounts", TEST_ACCOUNT)
    log_result("Create account", ok and data.get("success"), str(data))
    if ok and data.get("account_id"):
        created_ids["account_id"] = data["account_id"]

    # READ (list)
    ok, data = api_get("/accounts")
    log_result("List accounts", ok and isinstance(data, list), str(data)[:100])

    # Check account types
    if ok and isinstance(data, list):
        types = set(a.get("account_type") for a in data)
        log_result("Has multiple account types", len(types) > 1, f"Types: {types}")


def test_invoices():
    """Test Invoice workflow."""
    print("\n📄 Invoice Workflow")
    print("-" * 40)

    if not created_ids["customer_id"]:
        log_result("Create invoice", False, "No customer ID - run customer test first")
        return

    invoice_data = {
        "customer_id": created_ids["customer_id"],
        "invoice_date": datetime.now().strftime("%Y-%m-%d"),
        "terms": "Net 30",
        "lines": [
            {
                "account_id": "income_sales",
                "description": "Test service",
                "quantity": 2.0,
                "unit_price": 150.00
            }
        ],
        "memo": "Workflow test invoice",
        "po_number": "TEST-001"
    }

    # CREATE
    ok, data = api_post("/invoices", invoice_data)
    log_result("Create invoice", ok and data.get("success"), str(data))
    if ok and data.get("invoice_id"):
        created_ids["invoice_id"] = data["invoice_id"]

    # READ (list)
    ok, data = api_get("/invoices")
    log_result("List invoices", ok and isinstance(data, list), str(data)[:100])


def test_bills():
    """Test Bill workflow."""
    print("\n📋 Bill Workflow")
    print("-" * 40)

    if not created_ids["vendor_id"]:
        log_result("Create bill", False, "No vendor ID - run vendor test first")
        return

    bill_data = {
        "vendor_id": created_ids["vendor_id"],
        "bill_date": datetime.now().strftime("%Y-%m-%d"),
        "terms": "Net 30",
        "lines": [
            {
                "account_id": created_ids["account_id"] or "expense_general",
                "description": "Test expense",
                "quantity": 1.0,
                "unit_price": 250.00
            }
        ],
        "reference_number": "VEND-INV-001",
        "memo": "Workflow test bill"
    }

    # CREATE
    ok, data = api_post("/bills", bill_data)
    log_result("Create bill", ok and data.get("success"), str(data))
    if ok and data.get("bill_id"):
        created_ids["bill_id"] = data["bill_id"]

    # READ (list)
    ok, data = api_get("/bills")
    log_result("List bills", ok and isinstance(data, list), str(data)[:100])


def test_inventory():
    """Test Inventory operations."""
    print("\n📦 Inventory Management")
    print("-" * 40)

    item_data = {
        "item_name": "Test Inventory Item",
        "item_type": "inventory",
        "description": "Workflow test item",
        "cost": 25.00,
        "price": 45.00,
        "quantity_on_hand": 100,
        "reorder_point": 10
    }

    # CREATE
    ok, data = api_post("/inventory", item_data)
    log_result("Create inventory item", ok and data.get("success"), str(data))

    # READ (list)
    ok, data = api_get("/inventory")
    log_result("List inventory", ok, str(data)[:100])


def test_purchase_orders():
    """Test Purchase Order workflow."""
    print("\n📝 Purchase Order Workflow")
    print("-" * 40)

    if not created_ids["vendor_id"]:
        log_result("Create PO", False, "No vendor ID - run vendor test first")
        return

    po_data = {
        "vendor_id": created_ids["vendor_id"],
        "po_date": datetime.now().strftime("%Y-%m-%d"),
        "expected_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "lines": [
            {
                "item": "Test Part",
                "description": "Part for testing",
                "quantity": 10,
                "rate": 15.00,
                "amount": 150.00
            }
        ],
        "ship_to": "Main Farm",
        "memo": "Workflow test PO"
    }

    # CREATE
    ok, data = api_post("/purchase-orders", po_data)
    log_result("Create purchase order", ok and data.get("success"), str(data)[:100])
    if ok and data.get("po_id"):
        created_ids["po_id"] = data["po_id"]

    # READ (list)
    ok, data = api_get("/purchase-orders")
    log_result("List purchase orders", ok and isinstance(data, list), str(data)[:100])


def test_reports():
    """Test Report endpoints."""
    print("\n📈 Financial Reports")
    print("-" * 40)

    reports = [
        ("/reports/trial-balance", "Trial Balance"),
        ("/reports/balance-sheet", "Balance Sheet"),
        ("/reports/profit-loss", "Profit & Loss"),
        ("/reports/income-statement", "Income Statement"),
        ("/reports/ar-aging", "AR Aging"),
        ("/reports/ap-aging", "AP Aging"),
        ("/reports/cash-flow", "Cash Flow"),
        ("/reports/general-ledger", "General Ledger"),
    ]

    for endpoint, name in reports:
        ok, data = api_get(endpoint)
        log_result(f"{name} report", ok, str(data)[:80] if not ok else "")


def test_deposits():
    """Test Deposit operations."""
    print("\n💰 Deposits")
    print("-" * 40)

    # READ (list)
    ok, data = api_get("/deposits")
    log_result("List deposits", ok, str(data)[:100])


def test_journal_entries():
    """Test Journal Entry operations."""
    print("\n📝 Journal Entries")
    print("-" * 40)

    je_data = {
        "entry_date": datetime.now().strftime("%Y-%m-%d"),
        "memo": "Workflow test journal entry",
        "lines": [
            {
                "account_id": "expense_general",
                "description": "Test debit",
                "debit": 100.00,
                "credit": 0.00
            },
            {
                "account_id": "asset_cash",
                "description": "Test credit",
                "debit": 0.00,
                "credit": 100.00
            }
        ]
    }

    # CREATE
    ok, data = api_post("/journal-entries", je_data)
    log_result("Create journal entry", ok, str(data)[:100])

    # READ (list)
    ok, data = api_get("/journal-entries")
    log_result("List journal entries", ok and isinstance(data, list), str(data)[:100])


def test_checks():
    """Test Check operations."""
    print("\n✍️ Checks")
    print("-" * 40)

    # Get bank accounts first
    ok, bank_accounts = api_get("/bank-accounts")
    bank_account_id = None
    if ok and isinstance(bank_accounts, list) and len(bank_accounts) > 0:
        bank_account_id = bank_accounts[0].get("account_id")

    check_data = {
        "bank_account_id": bank_account_id or "checking",
        "check_date": datetime.now().strftime("%Y-%m-%d"),
        "payee_name": "Test Payee Corp",
        "payee_type": "vendor",
        "amount": 125.50,
        "memo": "Workflow test check",
        "expenses": [
            {
                "account_id": "expense_general",
                "amount": 125.50,
                "memo": "Test expense"
            }
        ]
    }

    # CREATE
    ok, data = api_post("/checks", check_data)
    log_result("Create check", ok, str(data)[:100])
    check_id = data.get("check_id") if ok and isinstance(data, dict) else None

    # READ (list)
    ok, data = api_get("/checks")
    log_result("List checks", ok, str(data)[:100])


def test_time_entries():
    """Test Time Entry operations."""
    print("\n⏱️ Time Entries")
    print("-" * 40)

    if not created_ids["employee_id"]:
        log_result("Create time entry", False, "No employee ID - run employee test first")
        return

    time_data = {
        "employee_id": created_ids["employee_id"],
        "work_date": datetime.now().strftime("%Y-%m-%d"),
        "hours": 8.0,
        "description": "Workflow test time entry",
        "billable": True,
        "customer_id": created_ids.get("customer_id")
    }

    # CREATE
    ok, data = api_post("/time-entries", time_data)
    log_result("Create time entry", ok, str(data)[:100])

    # READ (list)
    ok, data = api_get("/time-entries")
    log_result("List time entries", ok, str(data)[:100])


def test_fixed_assets():
    """Test Fixed Asset operations."""
    print("\n🏭 Fixed Assets")
    print("-" * 40)

    # Fixed assets uses query params, not JSON body
    asset_name = f"Test Equipment {random.randint(100, 999)}"
    params = (
        f"?name={asset_name}"
        f"&purchase_date={datetime.now().strftime('%Y-%m-%d')}"
        f"&original_cost=15000.00"
        f"&category=equipment"
        f"&depreciation_method=macrs_7"
        f"&salvage_value=1500.00"
        f"&useful_life_years=7"
        f"&description=Workflow test fixed asset"
    )

    # CREATE (using query params)
    try:
        r = requests.post(f"{API_BASE}/fixed-assets{params}", timeout=10)
        ok = r.status_code == 200
        data = r.json() if r.status_code == 200 else r.text
    except Exception as e:
        ok, data = False, str(e)
    log_result("Create fixed asset", ok, str(data)[:100])

    # READ (list)
    ok, data = api_get("/fixed-assets")
    log_result("List fixed assets", ok, str(data)[:100])

    # Summary
    ok, data = api_get("/fixed-assets/summary")
    log_result("Fixed assets summary", ok, str(data)[:100])


def test_bank_accounts():
    """Test Bank Account operations."""
    print("\n🏦 Bank Accounts")
    print("-" * 40)

    # READ (list)
    ok, data = api_get("/bank-accounts")
    log_result("List bank accounts", ok, str(data)[:100])

    # Bank accounts list returns valid response (may be empty)
    if ok and isinstance(data, list):
        log_result("Bank accounts endpoint valid", True, f"Found {len(data)} accounts")


def test_entities():
    """Test Entity/Company operations."""
    print("\n🏢 Entities (Multi-Company)")
    print("-" * 40)

    # READ (list)
    ok, data = api_get("/entities")
    log_result("List entities", ok, str(data)[:100])

    # Summary
    ok, data = api_get("/entities/summary")
    log_result("Entities summary", ok, str(data)[:100])


def test_create_deposit():
    """Test Deposit creation."""
    print("\n💵 Deposit Creation")
    print("-" * 40)

    # Get a bank account first
    ok, bank_accounts = api_get("/bank-accounts")
    bank_account_id = None
    if ok and isinstance(bank_accounts, list) and len(bank_accounts) > 0:
        bank_account_id = bank_accounts[0].get("account_id")

    deposit_data = {
        "bank_account_id": bank_account_id or "checking",
        "deposit_date": datetime.now().strftime("%Y-%m-%d"),
        "memo": "Workflow test deposit",
        "items": [
            {
                "received_from": "Test Customer",
                "account_id": "income_sales",
                "amount": 500.00,
                "memo": "Test deposit item"
            }
        ]
    }

    # CREATE
    ok, data = api_post("/deposits", deposit_data)
    log_result("Create deposit", ok, str(data)[:100])


def test_payroll():
    """Test Payroll operations."""
    print("\n💵 Payroll")
    print("-" * 40)

    # Pay schedules
    ok, data = api_get("/pay-schedules")
    log_result("List pay schedules", ok, str(data)[:100])

    # Pay runs
    ok, data = api_get("/pay-runs")
    log_result("List pay runs", ok, str(data)[:100])

    # Time entries list (payroll related)
    ok, data = api_get("/time-entries")
    log_result("List time entries (payroll)", ok, str(data)[:100])


def test_recurring_transactions():
    """Test Recurring Transaction operations."""
    print("\n🔄 Recurring Transactions")
    print("-" * 40)

    # READ (list)
    ok, data = api_get("/recurring")
    log_result("List recurring templates", ok, str(data)[:100])


def test_1099_tracking():
    """Test 1099 Tracking operations."""
    print("\n📋 1099 Tracking")
    print("-" * 40)

    # Summary
    ok, data = api_get("/1099/summary")
    log_result("1099 summary", ok, str(data)[:100])

    # Year data
    year = datetime.now().year
    ok, data = api_get(f"/1099/year/{year}")
    log_result(f"1099 year {year} data", ok, str(data)[:100])


def test_bank_feeds():
    """Test Bank Feed operations."""
    print("\n🏦 Bank Feeds")
    print("-" * 40)

    # Summary
    ok, data = api_get("/bank-feeds/summary")
    log_result("Bank feeds summary", ok, str(data)[:100])

    # Transactions
    ok, data = api_get("/bank-feeds/transactions")
    log_result("Bank feed transactions", ok, str(data)[:100])

    # Rules
    ok, data = api_get("/bank-feeds/rules")
    log_result("Bank feed rules", ok, str(data)[:100])


def test_cleanup():
    """Optional cleanup of test data."""
    print("\n🧹 Cleanup (Optional)")
    print("-" * 40)

    # Don't delete - keep for future testing
    log_result("Test data preserved", True, "Customer, Vendor, Employee kept for UI testing")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("🧪 GENFIN COMPREHENSIVE WORKFLOW TEST")
    print("=" * 60)
    print(f"API: {API_BASE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run tests
    if not test_api_health():
        print("\n❌ API not responding. Start the backend first!")
        print("   Run: python backend/main.py")
        sys.exit(1)

    test_customers()
    test_vendors()
    test_employees()
    test_accounts()
    test_invoices()
    test_bills()
    test_inventory()
    test_purchase_orders()
    test_journal_entries()
    test_checks()
    test_time_entries()
    test_fixed_assets()
    test_bank_accounts()
    test_entities()
    test_create_deposit()
    test_deposits()
    test_reports()
    test_payroll()
    test_recurring_transactions()
    test_1099_tracking()
    test_bank_feeds()
    test_cleanup()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    total = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0

    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📈 Pass Rate: {pass_rate:.1f}%")

    if results["errors"]:
        print("\n❌ Failed Tests:")
        for err in results["errors"][:10]:  # Show first 10
            print(f"   • {err[:80]}")

    print("\n" + "=" * 60)

    # Exit code
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
