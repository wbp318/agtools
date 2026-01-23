#!/usr/bin/env python3
"""
GenFin v6.3.0 Smoke Test
Tests Multi-Entity, 1099 Tracking, Payroll, and Budgets
"""

import os
import requests
import json
from datetime import datetime, date

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
    print("GenFin v6.3.0 Smoke Test")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    tests = []
    current_year = date.today().year

    # ============================================================
    # MULTI-ENTITY TESTS
    # ============================================================
    print("Testing Multi-Entity...")

    tests.append(run_test(
        "Entity Service Summary",
        "GET", "/genfin/entities/summary"
    ))

    tests.append(run_test(
        "List Entities",
        "GET", "/genfin/entities"
    ))

    tests.append(run_test(
        "Create Entity (North Farm)",
        "POST", "/genfin/entities",
        params={
            "name": "North Farm",
            "entity_type": "farm",
            "legal_name": "North Farm LLC",
            "state_of_formation": "IA"
        }
    ))

    tests.append(run_test(
        "Create Entity (South Farm)",
        "POST", "/genfin/entities",
        params={
            "name": "South Farm",
            "entity_type": "llc",
            "legal_name": "South Farm Holdings LLC",
            "tax_id": "12-3456789"
        }
    ))

    tests.append(run_test(
        "Get Entity Details",
        "GET", "/genfin/entities/1"
    ))

    tests.append(run_test(
        "Create Inter-Entity Transfer",
        "POST", "/genfin/entities/transfer",
        params={
            "from_entity_id": 1,
            "to_entity_id": 2,
            "amount": 5000.00,
            "description": "Equipment purchase transfer"
        }
    ))

    tests.append(run_test(
        "List Inter-Entity Transfers",
        "GET", "/genfin/entities/transfers"
    ))

    tests.append(run_test(
        "Consolidated Summary",
        "GET", "/genfin/entities/consolidated"
    ))

    # ============================================================
    # 1099 TRACKING TESTS
    # ============================================================
    print("Testing 1099 Tracking...")

    tests.append(run_test(
        "1099 Service Summary",
        "GET", "/genfin/1099/summary"
    ))

    tests.append(run_test(
        "Record 1099 Payment (Contractor 1)",
        "POST", "/genfin/1099/payments",
        params={
            "vendor_id": "contractor_001",
            "amount": 2500.00,
            "payment_date": f"{current_year}-03-15",
            "form_type": "1099-NEC",
            "box_number": 1,
            "description": "Consulting services"
        }
    ))

    tests.append(run_test(
        "Record 1099 Payment (Contractor 1 - 2nd)",
        "POST", "/genfin/1099/payments",
        params={
            "vendor_id": "contractor_001",
            "amount": 1500.00,
            "payment_date": f"{current_year}-06-20",
            "form_type": "1099-NEC",
            "description": "Additional consulting"
        }
    ))

    tests.append(run_test(
        "Record 1099 Payment (Rent)",
        "POST", "/genfin/1099/payments",
        params={
            "vendor_id": "landlord_001",
            "amount": 12000.00,
            "payment_date": f"{current_year}-12-01",
            "form_type": "1099-MISC",
            "box_number": 1,
            "description": "Annual land rent"
        }
    ))

    tests.append(run_test(
        "Get Vendor 1099 Payments",
        "GET", f"/genfin/1099/payments/contractor_001/{current_year}"
    ))

    tests.append(run_test(
        "Generate 1099 Forms",
        "POST", "/genfin/1099/generate",
        params={"tax_year": current_year}
    ))

    tests.append(run_test(
        "List 1099 Forms",
        "GET", "/genfin/1099/forms",
        params={"tax_year": current_year}
    ))

    tests.append(run_test(
        "Get 1099 Year Summary",
        "GET", f"/genfin/1099/year/{current_year}"
    ))

    tests.append(run_test(
        "Vendors Needing 1099 Forms",
        "GET", f"/genfin/1099/vendors-needing-forms/{current_year}"
    ))

    tests.append(run_test(
        "1099 Forms Missing Info",
        "GET", f"/genfin/1099/missing-info/{current_year}"
    ))

    # ============================================================
    # PAYROLL TESTS (using existing service)
    # ============================================================
    print("Testing Payroll (existing service check)...")

    tests.append(run_test(
        "Payroll Service Summary",
        "GET", "/genfin/payroll/summary"
    ))

    tests.append(run_test(
        "List Employees",
        "GET", "/genfin/payroll/employees"
    ))

    # ============================================================
    # BUDGET TESTS (using existing service)
    # ============================================================
    print("Testing Budget (existing service check)...")

    tests.append(run_test(
        "Budget Service Summary",
        "GET", "/genfin/budget/summary"
    ))

    tests.append(run_test(
        "List Budgets",
        "GET", "/genfin/budget/list"
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
        "Multi-Entity": [],
        "1099 Tracking": [],
        "Payroll": [],
        "Budget": []
    }

    for test in tests:
        name = test["name"]
        if "Entity" in name or "Transfer" in name or "Consolidated" in name:
            categories["Multi-Entity"].append(test)
        elif "1099" in name or "Vendor" in name:
            categories["1099 Tracking"].append(test)
        elif "Payroll" in name or "Employee" in name:
            categories["Payroll"].append(test)
        else:
            categories["Budget"].append(test)

    for category, cat_tests in categories.items():
        if not cat_tests:
            continue
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
        print("ALL TESTS PASSED! GenFin v6.3.0 is ready.")
    else:
        print(f"WARNING: {failed} test(s) failed. Please review.")

    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())
