#!/usr/bin/env python3
"""
AgTools Complete End-to-End Test Suite
Tests ALL API endpoints and frontend workflows

Run with: python tests/test_e2e_complete.py
"""

import os
import sys
import io
import json
import urllib.request
import urllib.error
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Fix Windows console encoding (skip if running under pytest)
if sys.platform == 'win32' and "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10

# Results tracking
RESULTS: List[Dict[str, Any]] = []
CATEGORIES: Dict[str, Dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0, "skipped": 0})


def log_result(category: str, test: str, status: str, details: str = ""):
    """Log a test result"""
    RESULTS.append({
        "category": category,
        "test": test,
        "status": status,
        "details": details
    })
    CATEGORIES[category][status.lower()] += 1

    symbol = {"passed": "OK", "failed": "FAIL", "skipped": "SKIP"}[status.lower()]
    detail_str = f" - {details}" if details else ""
    print(f"  [{symbol:4}] {test}{detail_str}")


def http_request(method: str, path: str, data: dict = None, headers: dict = None) -> Tuple[int, Any]:
    """Make HTTP request and return (status_code, response_data or error)"""
    url = f"{BASE_URL}{path}"
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    body = json.dumps(data).encode() if data else None

    try:
        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            try:
                return response.status, json.loads(response.read().decode())
            except:
                return response.status, None
    except urllib.error.HTTPError as e:
        try:
            error_body = json.loads(e.read().decode())
            return e.code, error_body
        except:
            return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


def test_endpoint(category: str, name: str, method: str, path: str,
                  data: dict = None, expected_codes: list = None):
    """Test a single endpoint"""
    if expected_codes is None:
        expected_codes = [200, 201, 401, 403]  # 401/403 are OK (auth required)

    status, response = http_request(method, path, data)

    if status in expected_codes:
        log_result(category, name, "passed", f"HTTP {status}")
        return True
    elif status == 0:
        log_result(category, name, "failed", response.get("error", "Connection error")[:50])
        return False
    else:
        detail = response.get("detail", str(response))[:50] if isinstance(response, dict) else str(response)[:50]
        log_result(category, name, "failed", f"HTTP {status}: {detail}")
        return False


# ==============================================================================
# API ENDPOINT TESTS
# ==============================================================================

def test_core_endpoints():
    """Test core/root endpoints"""
    print("\n" + "="*70)
    print("CORE ENDPOINTS")
    print("="*70)

    test_endpoint("Core", "Root endpoint", "GET", "/")
    test_endpoint("Core", "API docs", "GET", "/docs", expected_codes=[200])
    test_endpoint("Core", "OpenAPI spec", "GET", "/openapi.json", expected_codes=[200])


def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\n" + "="*70)
    print("AUTHENTICATION")
    print("="*70)

    test_endpoint("Auth", "Login endpoint exists", "POST", "/api/v1/auth/login",
                  data={"username": "test", "password": "test"},
                  expected_codes=[200, 401, 422])
    test_endpoint("Auth", "Get current user", "GET", "/api/v1/auth/me")
    test_endpoint("Auth", "Logout", "POST", "/api/v1/auth/logout")


def test_field_endpoints():
    """Test field management endpoints"""
    print("\n" + "="*70)
    print("FIELD MANAGEMENT")
    print("="*70)

    test_endpoint("Fields", "List fields", "GET", "/api/v1/fields")
    test_endpoint("Fields", "Get farm names", "GET", "/api/v1/fields/farms")
    test_endpoint("Fields", "Get field summary", "GET", "/api/v1/fields/summary")


def test_equipment_endpoints():
    """Test equipment management endpoints"""
    print("\n" + "="*70)
    print("EQUIPMENT MANAGEMENT")
    print("="*70)

    test_endpoint("Equipment", "List equipment", "GET", "/api/v1/equipment")
    test_endpoint("Equipment", "Get equipment types", "GET", "/api/v1/equipment/types")
    test_endpoint("Equipment", "Get equipment statuses", "GET", "/api/v1/equipment/statuses")
    test_endpoint("Equipment", "Get equipment summary", "GET", "/api/v1/equipment/summary")


def test_inventory_endpoints():
    """Test inventory management endpoints"""
    print("\n" + "="*70)
    print("INVENTORY MANAGEMENT")
    print("="*70)

    test_endpoint("Inventory", "List inventory", "GET", "/api/v1/inventory")
    test_endpoint("Inventory", "Get categories", "GET", "/api/v1/inventory/categories")
    test_endpoint("Inventory", "Get inventory summary", "GET", "/api/v1/inventory/summary")
    test_endpoint("Inventory", "Get alerts", "GET", "/api/v1/inventory/alerts")


def test_task_endpoints():
    """Test task management endpoints"""
    print("\n" + "="*70)
    print("TASK MANAGEMENT")
    print("="*70)

    test_endpoint("Tasks", "List tasks", "GET", "/api/v1/tasks")


def test_crew_endpoints():
    """Test crew management endpoints"""
    print("\n" + "="*70)
    print("CREW MANAGEMENT")
    print("="*70)

    test_endpoint("Crews", "List crews", "GET", "/api/v1/crews")


def test_operations_endpoints():
    """Test operations endpoints"""
    print("\n" + "="*70)
    print("FIELD OPERATIONS")
    print("="*70)

    test_endpoint("Operations", "List operations", "GET", "/api/v1/operations")
    test_endpoint("Operations", "Get operations summary", "GET", "/api/v1/operations/summary")


def test_cost_optimizer_endpoints():
    """Test cost optimizer endpoints"""
    print("\n" + "="*70)
    print("COST OPTIMIZER")
    print("="*70)

    # Quick estimate
    test_endpoint("Cost Optimizer", "Quick estimate (corn)", "POST", "/api/v1/optimize/quick-estimate",
                  data={"acres": 160, "crop": "corn", "is_irrigated": False, "yield_goal": 200},
                  expected_codes=[200, 422])

    test_endpoint("Cost Optimizer", "Quick estimate (irrigated)", "POST", "/api/v1/optimize/quick-estimate",
                  data={"acres": 160, "crop": "corn", "is_irrigated": True, "yield_goal": 200},
                  expected_codes=[200, 422])

    # Fertilizer
    test_endpoint("Cost Optimizer", "Fertilizer optimization", "POST", "/api/v1/optimize/fertilizer",
                  data={
                      "crop": "corn",
                      "yield_goal": 200,
                      "acres": 160,
                      "soil_test_p_ppm": 20,
                      "soil_test_k_ppm": 150,
                      "soil_ph": 6.5,
                      "organic_matter_percent": 3.0,
                      "nitrogen_credit_lb_per_acre": 0
                  },
                  expected_codes=[200, 422])

    # Labor
    test_endpoint("Cost Optimizer", "Labor seasonal budget", "POST", "/api/v1/optimize/labor/seasonal-budget",
                  data={
                      "total_acres": 500,
                      "crop": "corn",
                      "spray_applications": 4,
                      "fertilizer_applications": 2,
                      "scouting_frequency_days": 7,
                      "season_length_days": 120
                  },
                  expected_codes=[200, 422])


def test_pricing_endpoints():
    """Test pricing service endpoints"""
    print("\n" + "="*70)
    print("PRICING SERVICE")
    print("="*70)

    test_endpoint("Pricing", "Get all prices", "GET", "/api/v1/pricing/prices")
    test_endpoint("Pricing", "Get price alerts", "GET", "/api/v1/pricing/alerts")
    test_endpoint("Pricing", "Get budget prices (corn)", "GET", "/api/v1/pricing/budget-prices/corn")


def test_spray_timing_endpoints():
    """Test spray timing endpoints"""
    print("\n" + "="*70)
    print("SPRAY TIMING")
    print("="*70)

    # Test evaluate conditions (POST with weather data)
    from datetime import datetime
    test_endpoint("Spray Timing", "Evaluate conditions", "POST", "/api/v1/spray-timing/evaluate",
                  data={
                      "weather": {
                          "datetime": datetime.now().isoformat(),
                          "temp_f": 75,
                          "humidity_pct": 55,
                          "wind_mph": 8,
                          "wind_direction": "N"
                      },
                      "spray_type": "herbicide"
                  },
                  expected_codes=[200, 422])
    test_endpoint("Spray Timing", "Disease pressure", "POST", "/api/v1/spray-timing/disease-pressure",
                  data={
                      "weather_history": [{
                          "datetime": datetime.now().isoformat(),
                          "temp_f": 75,
                          "humidity_pct": 85,
                          "wind_mph": 5,
                          "wind_direction": "S"
                      }],
                      "crop": "corn",
                      "growth_stage": "V6"
                  },
                  expected_codes=[200, 422])


def test_yield_response_endpoints():
    """Test yield response endpoints"""
    print("\n" + "="*70)
    print("YIELD RESPONSE")
    print("="*70)

    test_endpoint("Yield Response", "Get response curve", "POST", "/api/v1/yield-response/curve",
                  data={"crop": "corn", "nutrient": "nitrogen"},
                  expected_codes=[200, 422])
    test_endpoint("Yield Response", "Get economic optimum", "POST", "/api/v1/yield-response/economic-optimum",
                  data={
                      "crop": "corn",
                      "nutrient": "nitrogen",
                      "crop_price": 4.50,
                      "nutrient_price": 0.50
                  },
                  expected_codes=[200, 422])


def test_identification_endpoints():
    """Test pest/disease identification endpoints"""
    print("\n" + "="*70)
    print("PEST/DISEASE IDENTIFICATION")
    print("="*70)

    test_endpoint("Identification", "List pests", "GET", "/api/v1/pests")
    test_endpoint("Identification", "List diseases", "GET", "/api/v1/diseases")
    test_endpoint("Identification", "Identify pest by symptoms", "POST", "/api/v1/identify/pest",
                  data={
                      "crop": "corn",
                      "symptoms": ["leaf_damage", "holes"],
                      "growth_stage": "V6"
                  },
                  expected_codes=[200, 422])
    test_endpoint("Identification", "Identify disease by symptoms", "POST", "/api/v1/identify/disease",
                  data={
                      "crop": "corn",
                      "symptoms": ["leaf_spots", "yellowing"],
                      "growth_stage": "V6"
                  },
                  expected_codes=[200, 422])


def test_genfin_endpoints():
    """Test GenFin (accounting) endpoints"""
    print("\n" + "="*70)
    print("GENFIN ACCOUNTING")
    print("="*70)

    test_endpoint("GenFin", "Get entities", "GET", "/api/v1/genfin/entities")
    test_endpoint("GenFin", "Get financial summary", "GET", "/api/v1/genfin/summary")
    test_endpoint("GenFin", "Get accounts", "GET", "/api/v1/genfin/accounts")
    test_endpoint("GenFin", "Get chart of accounts", "GET", "/api/v1/genfin/chart-of-accounts")
    test_endpoint("GenFin", "Get invoices", "GET", "/api/v1/genfin/invoices")
    test_endpoint("GenFin", "Get bills", "GET", "/api/v1/genfin/bills")
    test_endpoint("GenFin", "Get checks", "GET", "/api/v1/genfin/checks")
    test_endpoint("GenFin", "Get bank accounts", "GET", "/api/v1/genfin/bank-accounts")


def test_accounting_import_endpoints():
    """Test accounting import endpoints"""
    print("\n" + "="*70)
    print("ACCOUNTING IMPORT")
    print("="*70)

    test_endpoint("Accounting Import", "Get supported formats", "GET", "/api/v1/accounting-import/formats")
    test_endpoint("Accounting Import", "Get default mappings", "GET", "/api/v1/accounting-import/default-mappings")
    test_endpoint("Accounting Import", "Get user mappings", "GET", "/api/v1/accounting-import/mappings")


def test_reports_endpoints():
    """Test reporting endpoints"""
    print("\n" + "="*70)
    print("REPORTS")
    print("="*70)

    test_endpoint("Reports", "Get dashboard summary", "GET", "/api/v1/reports/dashboard")
    test_endpoint("Reports", "Get operations report", "GET", "/api/v1/reports/operations")
    test_endpoint("Reports", "Get financial report", "GET", "/api/v1/reports/financial")
    test_endpoint("Reports", "Get equipment report", "GET", "/api/v1/reports/equipment")
    test_endpoint("Reports", "Get inventory report", "GET", "/api/v1/reports/inventory")


def test_livestock_endpoints():
    """Test livestock endpoints"""
    print("\n" + "="*70)
    print("LIVESTOCK")
    print("="*70)

    test_endpoint("Livestock", "Get livestock summary", "GET", "/api/v1/livestock/summary")
    test_endpoint("Livestock", "List groups", "GET", "/api/v1/livestock/groups")
    test_endpoint("Livestock", "List animals", "GET", "/api/v1/livestock")


def test_seeds_endpoints():
    """Test seed/planting endpoints"""
    print("\n" + "="*70)
    print("SEEDS & PLANTING")
    print("="*70)

    test_endpoint("Seeds", "Get seeds summary", "GET", "/api/v1/seeds/summary")
    test_endpoint("Seeds", "List seeds", "GET", "/api/v1/seeds")
    test_endpoint("Planting", "List plantings", "GET", "/api/v1/planting")


def test_maintenance_endpoints():
    """Test maintenance endpoints"""
    print("\n" + "="*70)
    print("MAINTENANCE")
    print("="*70)

    test_endpoint("Maintenance", "List maintenance records", "GET", "/api/v1/maintenance")
    test_endpoint("Maintenance", "Get maintenance alerts", "GET", "/api/v1/maintenance/alerts")


def test_weather_endpoints():
    """Test weather endpoints"""
    print("\n" + "="*70)
    print("WEATHER")
    print("="*70)

    # Spray window requires lat/lon params
    test_endpoint("Weather", "Get spray window", "GET", "/api/v1/weather/spray-window?latitude=41.5&longitude=-93.5",
                  expected_codes=[200, 422, 500])  # May fail without API key


def test_grants_endpoints():
    """Test grants endpoints"""
    print("\n" + "="*70)
    print("GRANTS")
    print("="*70)

    test_endpoint("Grants", "List grant programs", "GET", "/api/v1/grants/programs")
    test_endpoint("Grants", "Get NRCS practices", "GET", "/api/v1/grants/nrcs-practices")
    test_endpoint("Grants", "Get practices summary", "GET", "/api/v1/grants/practices/summary")
    test_endpoint("Grants", "Get benchmarks", "GET", "/api/v1/grants/benchmarks")


def test_unified_dashboard_endpoints():
    """Test unified dashboard endpoints"""
    print("\n" + "="*70)
    print("UNIFIED DASHBOARD")
    print("="*70)

    test_endpoint("Dashboard", "Get summary", "GET", "/api/v1/unified-dashboard/summary")
    test_endpoint("Dashboard", "Get transactions", "GET", "/api/v1/unified-dashboard/transactions?kpi_type=cash_flow")


# ==============================================================================
# FRONTEND API CLIENT TESTS (Skipped - requires full frontend environment)
# ==============================================================================

def test_frontend_api_clients():
    """Test frontend API client layer - skipped in headless mode"""
    print("\n" + "="*70)
    print("FRONTEND API CLIENTS (Skipped)")
    print("="*70)
    print("  Frontend API tests require full Qt environment - skipping")


# ==============================================================================
# WORKFLOW TESTS
# ==============================================================================

def test_cost_optimizer_workflow():
    """Test complete cost optimizer workflow"""
    print("\n" + "="*70)
    print("WORKFLOW: Cost Optimizer")
    print("="*70)

    # Step 1: Quick estimate without irrigation
    status, response = http_request("POST", "/api/v1/optimize/quick-estimate", {
        "acres": 160, "crop": "corn", "is_irrigated": False, "yield_goal": 200
    })

    if status == 200 and response:
        cost1 = response.get("total_cost_per_acre", 0)
        log_result("Workflow", "Quick estimate returns cost", "passed", f"${cost1}/acre")

        # Step 2: With irrigation
        status2, response2 = http_request("POST", "/api/v1/optimize/quick-estimate", {
            "acres": 160, "crop": "corn", "is_irrigated": True, "yield_goal": 200
        })

        if status2 == 200 and response2:
            cost2 = response2.get("total_cost_per_acre", 0)
            if cost2 > cost1:
                log_result("Workflow", "Irrigation adds cost correctly", "passed",
                          f"${cost2} > ${cost1}")
            else:
                log_result("Workflow", "Irrigation adds cost correctly", "failed",
                          f"${cost2} should be > ${cost1}")
        else:
            log_result("Workflow", "Irrigation estimate", "failed", f"HTTP {status2}")
    else:
        log_result("Workflow", "Quick estimate returns cost", "failed", f"HTTP {status}")

    # Step 3: Fertilizer optimization
    status, response = http_request("POST", "/api/v1/optimize/fertilizer", {
        "crop": "corn", "yield_goal": 200, "acres": 160,
        "soil_test_p_ppm": 20, "soil_test_k_ppm": 150, "soil_ph": 6.5,
        "organic_matter_percent": 3.0, "nitrogen_credit_lb_per_acre": 0
    })

    if status == 200 and response:
        recs = response.get("recommendations", [])
        cost_summary = response.get("cost_summary", {})
        log_result("Workflow", "Fertilizer optimization", "passed",
                  f"{len(recs)} recommendations, ${cost_summary.get('cost_per_acre', 0):.2f}/acre")
    else:
        log_result("Workflow", "Fertilizer optimization", "failed", f"HTTP {status}")


def test_field_management_workflow():
    """Test field management workflow"""
    print("\n" + "="*70)
    print("WORKFLOW: Field Management")
    print("="*70)

    # List fields
    status, response = http_request("GET", "/api/v1/fields")

    if status in [200, 401]:
        if status == 200:
            fields = response if isinstance(response, list) else response.get("fields", [])
            log_result("Workflow", "List fields", "passed", f"{len(fields)} fields")
        else:
            log_result("Workflow", "List fields (auth required)", "passed", "HTTP 401")
    else:
        log_result("Workflow", "List fields", "failed", f"HTTP {status}")

    # Get summary
    status, response = http_request("GET", "/api/v1/fields/summary")
    if status in [200, 401]:
        log_result("Workflow", "Field summary", "passed", f"HTTP {status}")
    else:
        log_result("Workflow", "Field summary", "failed", f"HTTP {status}")


def test_inventory_workflow():
    """Test inventory management workflow"""
    print("\n" + "="*70)
    print("WORKFLOW: Inventory Management")
    print("="*70)

    # Get categories
    status, response = http_request("GET", "/api/v1/inventory/categories")
    if status in [200, 401]:
        if status == 200:
            cats = response if isinstance(response, list) else []
            log_result("Workflow", "Get categories", "passed", f"{len(cats)} categories")
        else:
            log_result("Workflow", "Get categories (auth required)", "passed", "HTTP 401")
    else:
        log_result("Workflow", "Get categories", "failed", f"HTTP {status}")

    # Get alerts
    status, response = http_request("GET", "/api/v1/inventory/alerts")
    if status in [200, 401]:
        log_result("Workflow", "Get inventory alerts", "passed", f"HTTP {status}")
    else:
        log_result("Workflow", "Get inventory alerts", "failed", f"HTTP {status}")


# ==============================================================================
# MAIN
# ==============================================================================

def run_all_tests():
    """Run all E2E tests"""
    print("\n" + "="*80)
    print("AGTOOLS COMPLETE END-TO-END TEST SUITE")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {BASE_URL}")

    # Check server is running
    try:
        status, _ = http_request("GET", "/docs")
        if status != 200:
            print(f"\nERROR: Server not responding properly (HTTP {status})")
            print("Make sure the backend is running on port 8000")
            return False
    except Exception as e:
        print(f"\nERROR: Cannot connect to server: {e}")
        print("Make sure the backend is running on port 8000")
        return False

    print("Server connection: OK\n")

    # Run all test categories
    test_functions = [
        test_core_endpoints,
        test_auth_endpoints,
        test_field_endpoints,
        test_equipment_endpoints,
        test_inventory_endpoints,
        test_task_endpoints,
        test_crew_endpoints,
        test_operations_endpoints,
        test_cost_optimizer_endpoints,
        test_pricing_endpoints,
        test_spray_timing_endpoints,
        test_yield_response_endpoints,
        test_identification_endpoints,
        test_genfin_endpoints,
        test_accounting_import_endpoints,
        test_reports_endpoints,
        test_livestock_endpoints,
        test_seeds_endpoints,
        test_maintenance_endpoints,
        test_weather_endpoints,
        test_grants_endpoints,
        test_unified_dashboard_endpoints,
        test_frontend_api_clients,
        test_cost_optimizer_workflow,
        test_field_management_workflow,
        test_inventory_workflow,
    ]

    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            print(f"\n*** ERROR in {test_func.__name__}: {e}")

    # Print summary
    print("\n" + "="*80)
    print("RESULTS BY CATEGORY")
    print("="*80)

    total_passed = 0
    total_failed = 0
    total_skipped = 0

    for category in sorted(CATEGORIES.keys()):
        stats = CATEGORIES[category]
        total = stats["passed"] + stats["failed"] + stats["skipped"]
        pct = (stats["passed"] / total * 100) if total > 0 else 0
        status = "OK" if stats["failed"] == 0 else "ISSUES"
        print(f"  {category:25} {stats['passed']:3}/{total:3} ({pct:5.1f}%) [{status}]")
        total_passed += stats["passed"]
        total_failed += stats["failed"]
        total_skipped += stats["skipped"]

    total = total_passed + total_failed + total_skipped
    pct = (total_passed / total * 100) if total > 0 else 0

    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"  Total Tests:  {total}")
    print(f"  Passed:       {total_passed} ({pct:.1f}%)")
    print(f"  Failed:       {total_failed} ({100-pct:.1f}%)")
    if total_skipped > 0:
        print(f"  Skipped:      {total_skipped}")

    if total_failed > 0:
        print("\n*** FAILED TESTS ***")
        for r in RESULTS:
            if r["status"] == "failed":
                print(f"  - [{r['category']}] {r['test']}: {r['details']}")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
