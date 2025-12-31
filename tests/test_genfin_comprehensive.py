#!/usr/bin/env python3
"""
Comprehensive GenFin Bug Finder
Automatically finds field mismatches, broken workflows, and API issues.
"""

import sys
import os
import re
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from typing import Dict, List, Tuple, Any, Set
from dataclasses import dataclass

BASE_URL = "http://127.0.0.1:8000/api/v1/genfin"

# Test credentials
AUTH = ("admin", "admin")

@dataclass
class Bug:
    category: str
    severity: str  # critical, high, medium, low
    location: str
    description: str
    suggestion: str

bugs_found: List[Bug] = []

def api_get(endpoint: str) -> Tuple[bool, Any]:
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", auth=AUTH, timeout=10)
        if r.status_code == 200:
            return True, r.json()
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)

def api_post(endpoint: str, data: dict) -> Tuple[bool, Any]:
    try:
        r = requests.post(f"{BASE_URL}{endpoint}", json=data, auth=AUTH, timeout=10)
        if r.status_code in [200, 201]:
            return True, r.json()
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)

def api_put(endpoint: str, data: dict) -> Tuple[bool, Any]:
    try:
        r = requests.put(f"{BASE_URL}{endpoint}", json=data, auth=AUTH, timeout=10)
        if r.status_code == 200:
            return True, r.json()
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)

def api_delete(endpoint: str) -> Tuple[bool, Any]:
    try:
        r = requests.delete(f"{BASE_URL}{endpoint}", auth=AUTH, timeout=10)
        if r.status_code == 200:
            return True, r.json()
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)

def log_bug(category: str, severity: str, location: str, description: str, suggestion: str):
    bugs_found.append(Bug(category, severity, location, description, suggestion))

# =============================================================================
# TEST 1: API Response Field Analysis
# =============================================================================
def test_api_fields():
    """Analyze API responses for field naming consistency."""
    print("\n" + "="*60)
    print("TEST 1: API FIELD ANALYSIS")
    print("="*60)

    # Expected field patterns for different entity types
    expected_fields = {
        "customers": {
            "id_field": "customer_id",
            "name_fields": ["display_name", "company_name"],
            "required": ["customer_id", "display_name"]
        },
        "vendors": {
            "id_field": "vendor_id",
            "name_fields": ["display_name", "company_name"],
            "required": ["vendor_id", "display_name"]
        },
        "employees": {
            "id_field": "employee_id",
            "name_fields": ["full_name", "first_name", "last_name"],
            "required": ["employee_id"]
        },
        "invoices": {
            "id_field": "invoice_id",
            "required": ["invoice_id", "customer_id", "total"]
        },
        "bills": {
            "id_field": "bill_id",
            "required": ["bill_id", "vendor_id", "total"]
        },
        "accounts": {
            "id_field": "account_id",
            "name_fields": ["name", "account_name"],
            "required": ["account_id", "name"]
        }
    }

    for endpoint, expectations in expected_fields.items():
        ok, data = api_get(f"/{endpoint}")
        if not ok:
            log_bug("API", "high", f"/{endpoint}", f"Endpoint failed: {data}", "Check if endpoint exists and returns data")
            print(f"  [!] /{endpoint}: FAILED - {data[:50]}")
            continue

        items = data if isinstance(data, list) else data.get(endpoint, data.get("items", []))
        if not items:
            print(f"  [i] /{endpoint}: No data to analyze")
            continue

        sample = items[0] if items else {}
        fields = set(sample.keys())

        # Check for required fields
        for req in expectations.get("required", []):
            if req not in fields:
                log_bug("API", "high", f"/{endpoint}",
                       f"Missing required field: {req}",
                       f"Add '{req}' to API response")
                print(f"  [!] /{endpoint}: Missing required field '{req}'")

        # Check for common naming issues
        if "name" in fields and endpoint in ["customers", "vendors"]:
            log_bug("API", "medium", f"/{endpoint}",
                   "Using generic 'name' field instead of 'display_name'",
                   "Rename 'name' to 'display_name' for consistency")
            print(f"  [!] /{endpoint}: Uses 'name' instead of 'display_name'")

        print(f"  [OK] /{endpoint}: Fields = {sorted(fields)}")

# =============================================================================
# TEST 2: Frontend/Backend Field Mismatch Detection
# =============================================================================
def test_frontend_backend_mismatches():
    """Scan frontend code for field access patterns that don't match API."""
    print("\n" + "="*60)
    print("TEST 2: FRONTEND/BACKEND FIELD MISMATCHES")
    print("="*60)

    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

    # Patterns to search for potential mismatches
    problematic_patterns = [
        # Generic "name" access on customer/vendor objects
        (r'\.get\(["\']name["\']', "Using .get('name') - may need display_name/company_name"),
        # Missing null checks
        (r'customer\[', "Direct dict access customer[] - should use .get() for safety"),
        (r'vendor\[', "Direct dict access vendor[] - should use .get() for safety"),
        # Potential ID field mismatches
        (r'\.get\(["\']id["\']', "Using .get('id') - may need customer_id/vendor_id/etc"),
        # Amount/total confusion
        (r'\.get\(["\']amount["\'].*total', "Mixing 'amount' and 'total' fields"),
    ]

    issues_found = 0
    files_scanned = 0

    for root, dirs, files in os.walk(frontend_path):
        # Skip __pycache__ and other non-essential dirs
        dirs[:] = [d for d in dirs if not d.startswith('__') and d != '.git']

        for filename in files:
            if not filename.endswith('.py'):
                continue

            filepath = os.path.join(root, filename)
            files_scanned += 1

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    for pattern, description in problematic_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Skip if it's a proper fix (has display_name or company_name nearby)
                            if 'display_name' in line or 'company_name' in line:
                                continue
                            # Skip comments
                            if line.strip().startswith('#'):
                                continue

                            rel_path = os.path.relpath(filepath, frontend_path)
                            location = f"{rel_path}:{line_num}"

                            # Only log if it looks like customer/vendor context
                            context_keywords = ['customer', 'vendor', 'client', 'supplier']
                            if any(kw in line.lower() or kw in lines[max(0,line_num-3):line_num+1] for kw in context_keywords):
                                log_bug("Frontend", "medium", location,
                                       f"{description}: {line.strip()[:60]}...",
                                       "Verify field name matches API response")
                                issues_found += 1

            except Exception as e:
                pass

    print(f"  Scanned {files_scanned} files, found {issues_found} potential issues")

# =============================================================================
# TEST 3: CRUD Operation Completeness
# =============================================================================
def test_crud_completeness():
    """Test that all entities have complete CRUD operations."""
    print("\n" + "="*60)
    print("TEST 3: CRUD OPERATION COMPLETENESS")
    print("="*60)

    entities = {
        "customers": {
            "create_data": {"company_name": "CRUD Test Co", "display_name": "CRUD Test Co"},
            "id_field": "customer_id",
            "update_data": {"display_name": "CRUD Test Updated"}
        },
        "vendors": {
            "create_data": {"company_name": "CRUD Vendor", "display_name": "CRUD Vendor"},
            "id_field": "vendor_id",
            "update_data": {"display_name": "CRUD Vendor Updated"}
        },
        "employees": {
            "create_data": {"first_name": "Test", "last_name": "Employee", "email": "test@crud.com"},
            "id_field": "employee_id",
            "update_data": {"first_name": "Updated"}
        },
        "accounts": {
            "create_data": {"name": "CRUD Test Account", "account_type": "Expense", "account_number": "9999"},
            "id_field": "account_id",
            "update_data": {"name": "CRUD Updated Account"}
        },
        "inventory": {
            "create_data": {"name": "CRUD Item", "sku": "CRUD-001", "item_type": "Inventory"},
            "id_field": "item_id",
            "update_data": {"name": "CRUD Item Updated"}
        }
    }

    for entity_name, config in entities.items():
        print(f"\n  Testing /{entity_name}:")
        results = {"create": False, "read": False, "update": False, "delete": False, "list": False}
        entity_id = None

        # CREATE
        ok, data = api_post(f"/{entity_name}", config["create_data"])
        if ok and data.get("success", True):
            results["create"] = True
            entity_id = data.get(config["id_field"]) or data.get("data", {}).get(config["id_field"])
            print(f"    [OK] CREATE - ID: {entity_id}")
        else:
            # Try to extract ID from error (might already exist)
            print(f"    [!] CREATE - {str(data)[:50]}")
            log_bug("CRUD", "high", f"/{entity_name}", f"CREATE failed: {data}", "Check create endpoint")

        # LIST
        ok, data = api_get(f"/{entity_name}")
        if ok:
            results["list"] = True
            items = data if isinstance(data, list) else data.get(entity_name, data.get("items", []))
            print(f"    [OK] LIST - {len(items)} items")
            # Try to find our created item
            if not entity_id and items:
                for item in items:
                    if config["create_data"].get("name", "") in str(item.values()) or \
                       config["create_data"].get("company_name", "") in str(item.values()):
                        entity_id = item.get(config["id_field"])
                        break
        else:
            print(f"    [!] LIST - {data}")
            log_bug("CRUD", "high", f"/{entity_name}", f"LIST failed: {data}", "Check list endpoint")

        if entity_id:
            # READ single
            ok, data = api_get(f"/{entity_name}/{entity_id}")
            if ok:
                results["read"] = True
                print(f"    [OK] READ")
            else:
                print(f"    [!] READ - {data}")
                log_bug("CRUD", "medium", f"/{entity_name}/{{id}}", f"GET single failed: {data}", "Add GET by ID endpoint")

            # UPDATE
            ok, data = api_put(f"/{entity_name}/{entity_id}", config["update_data"])
            if ok:
                results["update"] = True
                print(f"    [OK] UPDATE")
            else:
                print(f"    [!] UPDATE - {data}")
                log_bug("CRUD", "medium", f"/{entity_name}/{{id}}", f"PUT failed: {data}", "Add PUT endpoint")

            # DELETE
            ok, data = api_delete(f"/{entity_name}/{entity_id}")
            if ok:
                results["delete"] = True
                print(f"    [OK] DELETE")
            else:
                print(f"    [!] DELETE - {data}")
                log_bug("CRUD", "medium", f"/{entity_name}/{{id}}", f"DELETE failed: {data}", "Add DELETE endpoint")

        # Summary
        missing = [op for op, success in results.items() if not success]
        if missing:
            print(f"    Missing operations: {missing}")

# =============================================================================
# TEST 4: Workflow Integration Tests
# =============================================================================
def test_workflows():
    """Test complete business workflows end-to-end."""
    print("\n" + "="*60)
    print("TEST 4: BUSINESS WORKFLOW TESTS")
    print("="*60)

    # Workflow 1: Create Customer -> Create Invoice -> Verify Link
    print("\n  Workflow: Customer -> Invoice")

    # Create customer
    ok, cust_data = api_post("/customers", {
        "company_name": "Workflow Test Inc",
        "display_name": "Workflow Test Inc",
        "email": "workflow@test.com"
    })

    if not ok:
        print(f"    [!] Failed to create customer: {cust_data}")
        log_bug("Workflow", "critical", "Customer->Invoice", "Cannot create customer for invoice", "Fix customer creation")
    else:
        customer_id = cust_data.get("customer_id")
        print(f"    [OK] Created customer: {customer_id}")

        # Create invoice for this customer
        ok, inv_data = api_post("/invoices", {
            "customer_id": customer_id,
            "invoice_date": "2025-12-30",
            "due_date": "2025-01-30",
            "lines": [{"description": "Test Service", "quantity": 1, "rate": 100, "amount": 100}],
            "total": 100
        })

        if not ok:
            print(f"    [!] Failed to create invoice: {inv_data}")
            log_bug("Workflow", "critical", "Customer->Invoice", "Cannot create invoice for customer", "Fix invoice creation")
        else:
            invoice_id = inv_data.get("invoice_id")
            print(f"    [OK] Created invoice: {invoice_id}")

            # Verify invoice links to customer
            ok, inv_detail = api_get(f"/invoices/{invoice_id}")
            if ok:
                linked_customer = inv_detail.get("customer_id")
                if linked_customer == customer_id:
                    print(f"    [OK] Invoice correctly linked to customer")
                else:
                    print(f"    [!] Invoice customer mismatch: {linked_customer} != {customer_id}")
                    log_bug("Workflow", "high", "Customer->Invoice", "Invoice not linked to correct customer", "Check customer_id handling")

            # Cleanup
            api_delete(f"/invoices/{invoice_id}")

        api_delete(f"/customers/{customer_id}")

    # Workflow 2: Create Vendor -> Create Bill -> Verify
    print("\n  Workflow: Vendor -> Bill")

    ok, vend_data = api_post("/vendors", {
        "company_name": "Vendor Workflow Test",
        "display_name": "Vendor Workflow Test"
    })

    if not ok:
        print(f"    [!] Failed to create vendor: {vend_data}")
    else:
        vendor_id = vend_data.get("vendor_id")
        print(f"    [OK] Created vendor: {vendor_id}")

        ok, bill_data = api_post("/bills", {
            "vendor_id": vendor_id,
            "bill_date": "2025-12-30",
            "due_date": "2025-01-30",
            "lines": [{"description": "Test Purchase", "quantity": 1, "rate": 50, "amount": 50}],
            "total": 50
        })

        if not ok:
            print(f"    [!] Failed to create bill: {bill_data}")
            log_bug("Workflow", "critical", "Vendor->Bill", "Cannot create bill for vendor", "Fix bill creation")
        else:
            bill_id = bill_data.get("bill_id")
            print(f"    [OK] Created bill: {bill_id}")
            api_delete(f"/bills/{bill_id}")

        api_delete(f"/vendors/{vendor_id}")

# =============================================================================
# TEST 5: Data Validation
# =============================================================================
def test_data_validation():
    """Test that API properly validates input data."""
    print("\n" + "="*60)
    print("TEST 5: DATA VALIDATION TESTS")
    print("="*60)

    validation_tests = [
        # (endpoint, data, should_fail, description)
        ("/customers", {}, True, "Empty customer data"),
        ("/customers", {"display_name": ""}, True, "Empty display_name"),
        ("/invoices", {"customer_id": "nonexistent"}, True, "Invoice with invalid customer"),
        ("/invoices", {"lines": []}, True, "Invoice with no lines"),
        ("/bills", {"vendor_id": "nonexistent"}, True, "Bill with invalid vendor"),
        ("/accounts", {"name": "", "account_type": "Invalid"}, True, "Account with invalid type"),
    ]

    for endpoint, data, should_fail, description in validation_tests:
        ok, result = api_post(endpoint, data)

        if should_fail and ok and result.get("success", True):
            print(f"  [!] {description}: Should have failed but succeeded")
            log_bug("Validation", "medium", endpoint, f"Missing validation: {description}", "Add input validation")
        elif not should_fail and not ok:
            print(f"  [!] {description}: Should have succeeded but failed")
        else:
            print(f"  [OK] {description}")

# =============================================================================
# TEST 6: Report Endpoint Consistency
# =============================================================================
def test_reports():
    """Test all report endpoints return valid data structures."""
    print("\n" + "="*60)
    print("TEST 6: REPORT ENDPOINTS")
    print("="*60)

    reports = [
        ("/reports/trial-balance", ["accounts", "total_debits", "total_credits"]),
        ("/reports/balance-sheet", ["assets", "liabilities", "equity"]),
        ("/reports/profit-loss", ["revenue", "expenses"]),
        ("/reports/income-statement", ["revenue", "expenses"]),
        ("/reports/ar-aging", ["aging_buckets", "customers"]),
        ("/reports/ap-aging", ["aging_buckets", "vendors"]),
        ("/reports/cash-flow", []),
        ("/reports/general-ledger", []),
    ]

    for endpoint, expected_keys in reports:
        ok, data = api_get(endpoint)
        if not ok:
            print(f"  [!] {endpoint}: FAILED - {str(data)[:50]}")
            log_bug("Reports", "medium", endpoint, f"Report failed: {data}", "Check report endpoint")
            continue

        if expected_keys:
            missing = [k for k in expected_keys if k not in data]
            if missing:
                print(f"  [!] {endpoint}: Missing keys {missing}")
                log_bug("Reports", "low", endpoint, f"Missing expected keys: {missing}", "Add missing report fields")
            else:
                print(f"  [OK] {endpoint}")
        else:
            print(f"  [OK] {endpoint} (structure not validated)")

# =============================================================================
# TEST 7: Search for Common Code Smells
# =============================================================================
def test_code_smells():
    """Search for common bugs in the codebase."""
    print("\n" + "="*60)
    print("TEST 7: CODE SMELL DETECTION")
    print("="*60)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    smells = [
        # (pattern, description, severity, file_filter)
        (r'except\s*:', "Bare except clause - may hide errors", "medium", ".py"),
        (r'# TODO|# FIXME|# HACK|# XXX', "Unresolved TODO/FIXME comment", "low", ".py"),
        (r'print\s*\(.*password|print\s*\(.*secret', "Potential credential logging", "high", ".py"),
        (r'\.get\(["\'][a-z_]+["\']\)\s*\[', "Unsafe .get() followed by [] access", "medium", ".py"),
        (r'if\s+\w+\s*==\s*None', "Using == None instead of 'is None'", "low", ".py"),
        (r'except.*pass\s*$', "Silent exception swallowing", "medium", ".py"),
    ]

    issues_by_type = {}

    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', '.git', 'dist']]

        for filename in files:
            for pattern, desc, severity, file_filter in smells:
                if not filename.endswith(file_filter):
                    continue

                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if re.search(pattern, line, re.IGNORECASE):
                                rel_path = os.path.relpath(filepath, project_root)
                                if desc not in issues_by_type:
                                    issues_by_type[desc] = []
                                issues_by_type[desc].append(f"{rel_path}:{line_num}")
                except:
                    pass

    for desc, locations in issues_by_type.items():
        count = len(locations)
        sample = locations[:3]
        print(f"  [{count}x] {desc}")
        for loc in sample:
            print(f"       {loc}")
        if count > 3:
            print(f"       ... and {count - 3} more")

# =============================================================================
# MAIN
# =============================================================================
def main():
    print("="*60)
    print("GENFIN COMPREHENSIVE BUG FINDER")
    print("="*60)

    # Check server
    try:
        r = requests.get(f"{BASE_URL}/summary", auth=AUTH, timeout=5)
        if r.status_code != 200:
            print(f"[!] Server returned {r.status_code}")
            return
        print("[OK] Server is running\n")
    except Exception as e:
        print(f"[!] Cannot connect to server: {e}")
        print("    Start server: cd backend && python -m uvicorn main:app --port 8000")
        return

    # Run all tests
    test_api_fields()
    test_frontend_backend_mismatches()
    test_crud_completeness()
    test_workflows()
    test_data_validation()
    test_reports()
    test_code_smells()

    # Summary
    print("\n" + "="*60)
    print("BUG SUMMARY")
    print("="*60)

    if not bugs_found:
        print("\n  No bugs found!")
    else:
        by_severity = {"critical": [], "high": [], "medium": [], "low": []}
        for bug in bugs_found:
            by_severity[bug.severity].append(bug)

        for severity in ["critical", "high", "medium", "low"]:
            bugs = by_severity[severity]
            if bugs:
                print(f"\n  [{severity.upper()}] - {len(bugs)} issues:")
                for bug in bugs[:10]:  # Show max 10 per category
                    print(f"    - [{bug.category}] {bug.location}")
                    print(f"      {bug.description}")
                    print(f"      Fix: {bug.suggestion}")
                if len(bugs) > 10:
                    print(f"    ... and {len(bugs) - 10} more")

    total = len(bugs_found)
    critical = len([b for b in bugs_found if b.severity == "critical"])
    high = len([b for b in bugs_found if b.severity == "high"])

    print(f"\n  TOTAL: {total} bugs ({critical} critical, {high} high)")
    print("="*60)

if __name__ == "__main__":
    main()
