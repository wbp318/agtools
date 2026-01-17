"""
Automated GenFin API Tests
Tests all CRUD operations for every GenFin endpoint
"""

import sys
import io

# Fix Windows encoding (skip if running under pytest to avoid capture issues)
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

BASE_URL = "http://127.0.0.1:8000/api/v1/genfin"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def success(self, test_name: str):
        self.passed += 1
        print(f"  ✓ {test_name}")

    def fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  ✗ {test_name}: {error}")

    def summary(self):
        print(f"\n{'='*60}")
        print(f"RESULTS: {self.passed} passed, {self.failed} failed")
        if self.errors:
            print(f"\nFailed tests:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        print(f"{'='*60}")

results = TestResults()

def api_get(endpoint: str) -> Tuple[bool, any]:
    """GET request to API"""
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def api_post(endpoint: str, data: Dict) -> Tuple[bool, any]:
    """POST request to API"""
    try:
        r = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def api_put(endpoint: str, data: Dict) -> Tuple[bool, any]:
    """PUT request to API"""
    try:
        r = requests.put(f"{BASE_URL}{endpoint}", json=data, timeout=10)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def api_delete(endpoint: str) -> Tuple[bool, any]:
    """DELETE request to API"""
    try:
        r = requests.delete(f"{BASE_URL}{endpoint}", timeout=10)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)


# ============================================================
# CHART OF ACCOUNTS TESTS
# ============================================================
def test_accounts():
    print("\n📊 CHART OF ACCOUNTS")

    # Create
    ok, data = api_post("/accounts", {
        "account_number": "1000",
        "name": "Test Bank Account",
        "account_type": "bank",
        "sub_type": "checking",
        "description": "Test account"
    })
    if ok and data.get("success"):
        account_id = data.get("account_id")
        results.success("Create account")
    else:
        results.fail("Create account", str(data))
        return

    # List
    ok, data = api_get("/accounts")
    if ok and isinstance(data, list):
        results.success("List accounts")
    else:
        results.fail("List accounts", str(data))

    # Get
    ok, data = api_get(f"/accounts/{account_id}")
    if ok and data.get("account_id") == account_id:
        results.success("Get account")
    else:
        results.fail("Get account", str(data))

    # Update
    ok, data = api_put(f"/accounts/{account_id}", {
        "name": "Updated Bank Account",
        "description": "Updated description"
    })
    if ok:
        results.success("Update account")
    else:
        results.fail("Update account", str(data))

    # Delete
    ok, data = api_delete(f"/accounts/{account_id}")
    if ok:
        results.success("Delete account")
    else:
        results.fail("Delete account", str(data))


# ============================================================
# CUSTOMER TESTS
# ============================================================
def test_customers():
    print("\n👥 CUSTOMERS")

    # Create
    ok, data = api_post("/customers", {
        "company_name": "Test Customer Inc",
        "display_name": "Test Customer Inc",
        "contact_name": "John Doe",
        "email": "john@testcustomer.com",
        "phone": "555-1234",
        "billing_address_line1": "123 Main St",
        "billing_city": "Springfield",
        "billing_state": "IL",
        "billing_zip": "62701",
        "payment_terms": "Net 30"
    })
    if ok and data.get("success"):
        customer_id = data.get("customer_id")
        results.success("Create customer")
    else:
        results.fail("Create customer", str(data))
        return None

    # List
    ok, data = api_get("/customers")
    if ok and isinstance(data, list):
        # Check that we can find our customer and it has correct fields
        found = False
        for c in data:
            if c.get("customer_id") == customer_id:
                found = True
                # Verify response has expected fields
                if c.get("display_name") or c.get("company_name"):
                    results.success("List customers (with correct name fields)")
                else:
                    results.fail("List customers", "Missing display_name/company_name")
                break
        if not found:
            results.fail("List customers", "Created customer not in list")
    else:
        results.fail("List customers", str(data))

    # Get
    ok, data = api_get(f"/customers/{customer_id}")
    if ok and data.get("customer_id") == customer_id:
        results.success("Get customer")
    else:
        results.fail("Get customer", str(data))

    # Update
    ok, data = api_put(f"/customers/{customer_id}", {
        "company_name": "Updated Customer Inc",
        "email": "updated@testcustomer.com"
    })
    if ok:
        results.success("Update customer")
    else:
        results.fail("Update customer", str(data))

    # Delete
    ok, data = api_delete(f"/customers/{customer_id}")
    if ok:
        results.success("Delete customer")
    else:
        results.fail("Delete customer", str(data))

    return customer_id


# ============================================================
# VENDOR TESTS
# ============================================================
def test_vendors():
    print("\n🏪 VENDORS")

    # Create
    ok, data = api_post("/vendors", {
        "company_name": "Test Vendor LLC",
        "display_name": "Test Vendor LLC",
        "contact_name": "Jane Smith",
        "email": "jane@testvendor.com",
        "phone": "555-5678",
        "billing_address_line1": "456 Oak Ave",
        "billing_city": "Chicago",
        "billing_state": "IL",
        "billing_zip": "60601",
        "payment_terms": "Net 30",
        "is_1099_vendor": False
    })
    if ok and data.get("success"):
        vendor_id = data.get("vendor_id")
        results.success("Create vendor")
    else:
        results.fail("Create vendor", str(data))
        return None

    # List
    ok, data = api_get("/vendors")
    if ok and isinstance(data, list):
        found = any(v.get("vendor_id") == vendor_id for v in data)
        if found:
            results.success("List vendors")
        else:
            results.fail("List vendors", "Created vendor not in list")
    else:
        results.fail("List vendors", str(data))

    # Get
    ok, data = api_get(f"/vendors/{vendor_id}")
    if ok and data.get("vendor_id") == vendor_id:
        results.success("Get vendor")
    else:
        results.fail("Get vendor", str(data))

    # Update
    ok, data = api_put(f"/vendors/{vendor_id}", {
        "company_name": "Updated Vendor LLC"
    })
    if ok:
        results.success("Update vendor")
    else:
        results.fail("Update vendor", str(data))

    # Delete
    ok, data = api_delete(f"/vendors/{vendor_id}")
    if ok:
        results.success("Delete vendor")
    else:
        results.fail("Delete vendor", str(data))

    return vendor_id


# ============================================================
# EMPLOYEE TESTS
# ============================================================
def test_employees():
    print("\n👷 EMPLOYEES")

    # Create
    ok, data = api_post("/employees", {
        "first_name": "Test",
        "last_name": "Employee",
        "email": "test@employee.com",
        "phone": "555-9999",
        "employee_type": "full_time",
        "pay_type": "hourly",
        "pay_rate": 25.00,
        "hire_date": "2024-01-01"
    })
    if ok and data.get("success"):
        employee_id = data.get("employee_id")
        results.success("Create employee")
    else:
        results.fail("Create employee", str(data))
        return

    # List
    ok, data = api_get("/employees")
    if ok and isinstance(data, list):
        results.success("List employees")
    else:
        results.fail("List employees", str(data))

    # Get
    ok, data = api_get(f"/employees/{employee_id}")
    if ok and data.get("employee_id") == employee_id:
        results.success("Get employee")
    else:
        results.fail("Get employee", str(data))

    # Delete
    ok, data = api_delete(f"/employees/{employee_id}")
    if ok:
        results.success("Delete employee")
    else:
        results.fail("Delete employee", str(data))


# ============================================================
# INVOICE TESTS (requires customer)
# ============================================================
def test_invoices():
    print("\n📄 INVOICES")

    # First create a customer
    ok, cust_data = api_post("/customers", {
        "company_name": "Invoice Test Customer",
        "display_name": "Invoice Test Customer"
    })
    if not ok:
        results.fail("Create customer for invoice", str(cust_data))
        return
    customer_id = cust_data.get("customer_id")

    # Create an account for line items
    ok, acct_data = api_post("/accounts", {
        "account_number": "4000",
        "name": "Sales Revenue",
        "account_type": "income",
        "sub_type": "sales"
    })
    account_id = acct_data.get("account_id") if ok else None

    # Create invoice
    ok, data = api_post("/invoices", {
        "customer_id": customer_id,
        "invoice_date": date.today().isoformat(),
        "lines": [{
            "account_id": account_id or "default",
            "description": "Test Service",
            "quantity": 1,
            "unit_price": 100.00
        }],
        "terms": "Net 30",
        "memo": "Test invoice"
    })
    if ok and data.get("success"):
        invoice_id = data.get("invoice_id")
        results.success("Create invoice")
    else:
        results.fail("Create invoice", str(data))
        # Cleanup
        api_delete(f"/customers/{customer_id}")
        return

    # List
    ok, data = api_get("/invoices")
    if ok and isinstance(data, list):
        results.success("List invoices")
    else:
        results.fail("List invoices", str(data))

    # Get
    ok, data = api_get(f"/invoices/{invoice_id}")
    if ok and data.get("invoice_id") == invoice_id:
        results.success("Get invoice")
    else:
        results.fail("Get invoice", str(data))

    # Delete invoice
    ok, data = api_delete(f"/invoices/{invoice_id}")
    if ok:
        results.success("Delete invoice")
    else:
        results.fail("Delete invoice", str(data))

    # Cleanup
    api_delete(f"/customers/{customer_id}")
    if account_id:
        api_delete(f"/accounts/{account_id}")


# ============================================================
# BILL TESTS (requires vendor)
# ============================================================
def test_bills():
    print("\n📋 BILLS")

    # First create a vendor
    ok, vendor_data = api_post("/vendors", {
        "company_name": "Bill Test Vendor",
        "display_name": "Bill Test Vendor"
    })
    if not ok:
        results.fail("Create vendor for bill", str(vendor_data))
        return
    vendor_id = vendor_data.get("vendor_id")

    # Create an expense account
    ok, acct_data = api_post("/accounts", {
        "account_number": "5000",
        "name": "Test Expenses",
        "account_type": "expense",
        "sub_type": "expense"
    })
    account_id = acct_data.get("account_id") if ok else None

    # Create bill
    ok, data = api_post("/bills", {
        "vendor_id": vendor_id,
        "bill_date": date.today().isoformat(),
        "lines": [{
            "account_id": account_id or "default",
            "description": "Test Expense",
            "quantity": 1,
            "unit_price": 50.00
        }],
        "terms": "Net 30",
        "memo": "Test bill"
    })
    if ok and data.get("success"):
        bill_id = data.get("bill_id")
        results.success("Create bill")
    else:
        results.fail("Create bill", str(data))
        api_delete(f"/vendors/{vendor_id}")
        return

    # List
    ok, data = api_get("/bills")
    if ok and isinstance(data, list):
        results.success("List bills")
    else:
        results.fail("List bills", str(data))

    # Get
    ok, data = api_get(f"/bills/{bill_id}")
    if ok and data.get("bill_id") == bill_id:
        results.success("Get bill")
    else:
        results.fail("Get bill", str(data))

    # Delete
    ok, data = api_delete(f"/bills/{bill_id}")
    if ok:
        results.success("Delete bill")
    else:
        results.fail("Delete bill", str(data))

    # Cleanup
    api_delete(f"/vendors/{vendor_id}")
    if account_id:
        api_delete(f"/accounts/{account_id}")


# ============================================================
# JOURNAL ENTRY TESTS
# ============================================================
def test_journal_entries():
    print("\n📝 JOURNAL ENTRIES")

    # Create accounts for JE
    ok, debit_acct = api_post("/accounts", {
        "account_number": "1100",
        "name": "Cash for JE",
        "account_type": "bank",
        "sub_type": "checking"
    })
    debit_id = debit_acct.get("account_id") if ok else None

    ok, credit_acct = api_post("/accounts", {
        "account_number": "3000",
        "name": "Owner Equity",
        "account_type": "equity",
        "sub_type": "equity"
    })
    credit_id = credit_acct.get("account_id") if ok else None

    # Create JE
    ok, data = api_post("/journal-entries", {
        "entry_date": date.today().isoformat(),
        "lines": [
            {"account_id": debit_id or "default", "debit": 1000.00, "credit": 0, "description": "Debit"},
            {"account_id": credit_id or "default", "debit": 0, "credit": 1000.00, "description": "Credit"}
        ],
        "memo": "Test journal entry"
    })
    if ok and data.get("success"):
        je_id = data.get("entry_id")
        results.success("Create journal entry")
    else:
        results.fail("Create journal entry", str(data))
        return

    # List
    ok, data = api_get("/journal-entries")
    if ok and isinstance(data, list):
        results.success("List journal entries")
    else:
        results.fail("List journal entries", str(data))

    # Delete
    ok, data = api_delete(f"/journal-entries/{je_id}")
    if ok:
        results.success("Delete journal entry")
    else:
        results.fail("Delete journal entry", str(data))

    # Cleanup
    if debit_id:
        api_delete(f"/accounts/{debit_id}")
    if credit_id:
        api_delete(f"/accounts/{credit_id}")


# ============================================================
# INVENTORY/ITEMS TESTS
# ============================================================
def test_inventory():
    print("\n📦 INVENTORY ITEMS")

    # Create
    ok, data = api_post("/inventory", {
        "name": "Test Product",
        "sku": "TEST-001",
        "item_type": "inventory",
        "description": "A test product",
        "sale_price": 29.99,
        "cost": 15.00,
        "quantity_on_hand": 100
    })
    if ok and data.get("success"):
        item_id = data.get("item_id")
        results.success("Create inventory item")
    else:
        results.fail("Create inventory item", str(data))
        return

    # List
    ok, data = api_get("/inventory")
    if ok and isinstance(data, list):
        results.success("List inventory items")
    else:
        results.fail("List inventory items", str(data))

    # Get
    ok, data = api_get(f"/inventory/{item_id}")
    if ok and data.get("item_id") == item_id:
        results.success("Get inventory item")
    else:
        results.fail("Get inventory item", str(data))

    # Delete
    ok, data = api_delete(f"/inventory/{item_id}")
    if ok:
        results.success("Delete inventory item")
    else:
        results.fail("Delete inventory item", str(data))


# ============================================================
# BANK ACCOUNTS / CHECKS / DEPOSITS
# ============================================================
def test_banking():
    print("\n🏦 BANKING")

    # Create bank account
    ok, data = api_post("/accounts", {
        "account_number": "1010",
        "name": "Operating Account",
        "account_type": "bank",
        "sub_type": "checking"
    })
    if ok:
        bank_account_id = data.get("account_id")
        results.success("Create bank account")
    else:
        results.fail("Create bank account", str(data))
        return

    # List bank accounts
    ok, data = api_get("/bank-accounts")
    if ok:
        results.success("List bank accounts")
    else:
        results.fail("List bank accounts", str(data))

    # Create expense account for checks
    ok, expense_data = api_post("/accounts", {
        "account_number": "5010",
        "name": "Office Supplies",
        "account_type": "expense",
        "sub_type": "expense"
    })
    expense_id = expense_data.get("account_id") if ok else None

    # Write check
    ok, data = api_post("/checks", {
        "bank_account_id": bank_account_id,
        "payee": "Office Depot",
        "check_date": date.today().isoformat(),
        "amount": 150.00,
        "lines": [{"account_id": expense_id or "default", "amount": 150.00}],
        "memo": "Office supplies"
    })
    if ok and data.get("success"):
        check_id = data.get("check_id")
        results.success("Write check")
    else:
        results.fail("Write check", str(data))
        check_id = None

    # List checks
    ok, data = api_get("/checks")
    if ok:
        results.success("List checks")
    else:
        results.fail("List checks", str(data))

    # Create income account for deposits
    ok, income_data = api_post("/accounts", {
        "account_number": "4010",
        "name": "Service Revenue",
        "account_type": "income",
        "sub_type": "sales"
    })
    income_id = income_data.get("account_id") if ok else None

    # Make deposit
    ok, data = api_post("/deposits", {
        "bank_account_id": bank_account_id,
        "deposit_date": date.today().isoformat(),
        "lines": [{"account_id": income_id or "default", "amount": 500.00, "description": "Customer payment"}],
        "memo": "Daily deposits"
    })
    if ok and data.get("success"):
        deposit_id = data.get("deposit_id")
        results.success("Make deposit")
    else:
        results.fail("Make deposit", str(data))
        deposit_id = None

    # List deposits
    ok, data = api_get("/deposits")
    if ok:
        results.success("List deposits")
    else:
        results.fail("List deposits", str(data))

    # Cleanup
    if check_id:
        api_delete(f"/checks/{check_id}")
    if deposit_id:
        api_delete(f"/deposits/{deposit_id}")
    api_delete(f"/accounts/{bank_account_id}")
    if expense_id:
        api_delete(f"/accounts/{expense_id}")
    if income_id:
        api_delete(f"/accounts/{income_id}")


# ============================================================
# REPORTS TESTS
# ============================================================
def test_reports():
    print("\n📈 REPORTS")

    today = date.today().isoformat()
    start = f"{date.today().year}-01-01"

    # Trial Balance
    ok, data = api_get(f"/reports/trial-balance?as_of_date={today}")
    if ok:
        results.success("Trial Balance report")
    else:
        results.fail("Trial Balance report", str(data))

    # Balance Sheet
    ok, data = api_get(f"/reports/balance-sheet?as_of_date={today}")
    if ok:
        results.success("Balance Sheet report")
    else:
        results.fail("Balance Sheet report", str(data))

    # Income Statement
    ok, data = api_get(f"/reports/income-statement?start_date={start}&end_date={today}")
    if ok:
        results.success("Income Statement report")
    else:
        results.fail("Income Statement report", str(data))

    # Accounts Receivable Aging
    ok, data = api_get(f"/reports/ar-aging?as_of_date={today}")
    if ok:
        results.success("A/R Aging report")
    else:
        results.fail("A/R Aging report", str(data))

    # Accounts Payable Aging
    ok, data = api_get(f"/reports/ap-aging?as_of_date={today}")
    if ok:
        results.success("A/P Aging report")
    else:
        results.fail("A/P Aging report", str(data))


# ============================================================
# MAIN TEST RUNNER
# ============================================================
def run_all_tests():
    print("=" * 60)
    print("GENFIN API AUTOMATED TESTS")
    print(f"Testing: {BASE_URL}")
    print("=" * 60)

    # Check server is running
    try:
        r = requests.get(f"{BASE_URL}/summary", timeout=5)
        if r.status_code != 200:
            print("❌ Server not responding correctly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Make sure backend is running: python backend/main.py")
        return

    print("✓ Server is running\n")

    # Run all tests
    test_accounts()
    test_customers()
    test_vendors()
    test_employees()
    test_invoices()
    test_bills()
    test_journal_entries()
    test_inventory()
    test_banking()
    test_reports()

    # Print summary
    results.summary()


if __name__ == "__main__":
    run_all_tests()
