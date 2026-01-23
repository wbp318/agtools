#!/usr/bin/env python3
"""
GenFin v6.2.0 Smoke Test
Tests Recurring Transactions, Bank Feeds, and Fixed Assets
"""

import os
import requests
import json
from datetime import datetime

BASE_URL = os.environ.get('AGTOOLS_API_URL', 'http://localhost:8000/api/v1')
TEST_USER = os.environ.get('AGTOOLS_TEST_USER', 'admin')
TEST_PASS = os.environ.get('AGTOOLS_TEST_PASSWORD')  # No default - must be set

# Authentication - cached token
_cached_token = None

def get_auth_token():
    """Get auth token for API calls"""
    global _cached_token
    if _cached_token:
        return _cached_token

    if not TEST_PASS:
        print("ERROR: Set AGTOOLS_TEST_PASSWORD environment variable")
        return None

    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": TEST_USER, "password": TEST_PASS},
        timeout=10
    )
    if response.status_code == 200:
        _cached_token = response.json().get("tokens", {}).get("access_token")
        return _cached_token
    print(f"Auth failed: {response.status_code} - {response.text}")
    return None

def run_test(name, method, endpoint, expected_status=200, data=None, params=None):
    """Run a single API test"""
    token = get_auth_token()
    if not token:
        return {"name": name, "passed": False, "error": "Authentication failed"}

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, params=params)
        elif method == "PUT":
            response = requests.put(url, headers=headers, params=params)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)

        passed = response.status_code == expected_status
        return {
            "name": name,
            "passed": passed,
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text[:200]
        }
    except Exception as e:
        return {"name": name, "passed": False, "error": str(e)}

def main():
    print("=" * 60)
    print("GenFin v6.2.0 Smoke Test")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    tests = []

    # ============================================================
    # RECURRING TRANSACTIONS TESTS
    # ============================================================
    print("Testing Recurring Transactions...")

    tests.append(run_test(
        "Recurring Summary",
        "GET", "/genfin/recurring/summary"
    ))

    tests.append(run_test(
        "List Recurring Templates",
        "GET", "/genfin/recurring"
    ))

    tests.append(run_test(
        "Create Recurring Invoice",
        "POST", "/genfin/recurring/invoice",
        params={
            "template_name": "Monthly Consulting Fee",
            "customer_id": "cust_001",
            "frequency": "monthly",
            "base_amount": 2500.00,
            "start_date": "2025-01-01",
            "description": "Monthly consulting retainer"
        }
    ))

    tests.append(run_test(
        "Create Recurring Bill",
        "POST", "/genfin/recurring/bill",
        params={
            "template_name": "Monthly Rent",
            "vendor_id": "vend_001",
            "frequency": "monthly",
            "base_amount": 1500.00,
            "start_date": "2025-01-01",
            "description": "Office rent"
        }
    ))

    tests.append(run_test(
        "Create Recurring Journal Entry",
        "POST", "/genfin/recurring/journal-entry",
        params={
            "template_name": "Monthly Depreciation",
            "frequency": "monthly",
            "debit_account": "6200",
            "credit_account": "1550",
            "amount": 500.00,
            "start_date": "2025-01-01",
            "description": "Monthly depreciation entry"
        }
    ))

    tests.append(run_test(
        "Generate All Due Transactions",
        "POST", "/genfin/recurring/generate-all",
        params={"as_of_date": "2025-01-15"}
    ))

    # ============================================================
    # BANK FEEDS TESTS
    # ============================================================
    print("Testing Bank Feeds...")

    tests.append(run_test(
        "Bank Feeds Summary",
        "GET", "/genfin/bank-feeds/summary"
    ))

    tests.append(run_test(
        "List Import Files",
        "GET", "/genfin/bank-feeds/imports"
    ))

    tests.append(run_test(
        "List Imported Transactions",
        "GET", "/genfin/bank-feeds/transactions"
    ))

    tests.append(run_test(
        "List Category Rules",
        "GET", "/genfin/bank-feeds/rules"
    ))

    tests.append(run_test(
        "Create Category Rule",
        "POST", "/genfin/bank-feeds/rules",
        params={
            "rule_name": "Walmart Purchases",
            "pattern": "WALMART",
            "category_account": "5000",
            "pattern_type": "contains",
            "match_field": "description"
        }
    ))

    # Test OFX import with sample data
    sample_ofx = """
OFXHEADER:100
DATA:OFXSGML
<OFX>
<BANKMSGSRSV1>
<STMTRS>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20250115
<TRNAMT>-150.00
<FITID>2025011501
<NAME>WALMART SUPERCENTER
</STMTTRN>
</STMTRS>
</BANKMSGSRSV1>
</OFX>
"""
    tests.append(run_test(
        "Import Bank File (OFX)",
        "POST", "/genfin/bank-feeds/import",
        params={
            "file_content": sample_ofx,
            "file_type": "ofx",
            "bank_account_id": "1000"
        }
    ))

    tests.append(run_test(
        "Auto-Categorize Transactions",
        "POST", "/genfin/bank-feeds/auto-categorize"
    ))

    # ============================================================
    # FIXED ASSETS TESTS
    # ============================================================
    print("Testing Fixed Assets...")

    tests.append(run_test(
        "Fixed Assets Summary",
        "GET", "/genfin/fixed-assets/summary"
    ))

    tests.append(run_test(
        "List Fixed Assets",
        "GET", "/genfin/fixed-assets"
    ))

    tests.append(run_test(
        "Create Fixed Asset (Tractor)",
        "POST", "/genfin/fixed-assets",
        params={
            "name": "John Deere 8R Tractor",
            "purchase_date": "2024-03-15",
            "original_cost": 450000.00,
            "category": "farm_equipment",
            "depreciation_method": "macrs_7",
            "salvage_value": 50000.00,
            "description": "Primary farm tractor",
            "serial_number": "JD8R2024001"
        }
    ))

    tests.append(run_test(
        "Create Fixed Asset (Building)",
        "POST", "/genfin/fixed-assets",
        params={
            "name": "Equipment Storage Barn",
            "purchase_date": "2020-01-01",
            "original_cost": 150000.00,
            "category": "buildings",
            "depreciation_method": "macrs_20",
            "salvage_value": 20000.00,
            "description": "40x60 steel equipment storage"
        }
    ))

    tests.append(run_test(
        "Create Fixed Asset (Computer)",
        "POST", "/genfin/fixed-assets",
        params={
            "name": "Office Computer System",
            "purchase_date": "2024-06-01",
            "original_cost": 3500.00,
            "category": "office_equipment",
            "depreciation_method": "section_179",
            "description": "Farm office workstation"
        }
    ))

    tests.append(run_test(
        "Run All Depreciation",
        "POST", "/genfin/fixed-assets/run-depreciation-all",
        params={"year": 2025}
    ))

    tests.append(run_test(
        "Depreciation Summary Report",
        "GET", "/genfin/fixed-assets/reports/depreciation-summary",
        params={"year": 2025}
    ))

    tests.append(run_test(
        "Asset Register Report",
        "GET", "/genfin/fixed-assets/reports/asset-register"
    ))

    # ============================================================
    # RESULTS SUMMARY
    # ============================================================
    print()
    print("=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    passed = sum(1 for t in tests if t.get("passed"))
    failed = len(tests) - passed

    print()
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed} ({100*passed/len(tests):.0f}%)")
    print(f"Failed: {failed} ({100*failed/len(tests):.0f}%)")
    print()

    # Show results by category
    categories = {
        "Recurring Transactions": [],
        "Bank Feeds": [],
        "Fixed Assets": []
    }

    for test in tests:
        name = test["name"]
        if "Recurring" in name or "Journal Entry" in name or "Invoice" in name or "Bill" in name or "Generate" in name:
            categories["Recurring Transactions"].append(test)
        elif "Bank" in name or "Import" in name or "Rule" in name or "Categorize" in name:
            categories["Bank Feeds"].append(test)
        else:
            categories["Fixed Assets"].append(test)

    for category, cat_tests in categories.items():
        cat_passed = sum(1 for t in cat_tests if t.get("passed"))
        print(f"{category}: {cat_passed}/{len(cat_tests)} passed")
        for test in cat_tests:
            status = "PASS" if test.get("passed") else "FAIL"
            print(f"  [{status}] {test['name']}")
            if not test.get("passed"):
                print(f"       Error: {test.get('error') or test.get('response', '')[:100]}")

    print()
    print("=" * 60)

    if failed == 0:
        print("ALL TESTS PASSED! GenFin v6.2.0 is ready.")
    else:
        print(f"WARNING: {failed} test(s) failed. Please review.")

    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())
