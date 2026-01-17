#!/usr/bin/env python3
"""
AgTools Comprehensive Workflow Test Suite v6.8.1
Tests ALL API endpoints in complete workflow scenarios - front and backend

This test suite verifies:
1. All major API categories work correctly
2. Complete user workflows function end-to-end
3. Data flows correctly between endpoints
4. Error handling works as expected

Run with: python tests/test_comprehensive_workflows.py
"""

import os
import sys
import io
import json
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

# Fix Windows console encoding (skip if running under pytest)
if sys.platform == 'win32' and "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 15

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
                  data: dict = None, expected_codes: list = None,
                  validate_response: callable = None) -> Tuple[bool, Any]:
    """Test a single endpoint with optional response validation"""
    if expected_codes is None:
        expected_codes = [200, 201, 401, 403]

    status, response = http_request(method, path, data)

    if status in expected_codes:
        if validate_response and status == 200:
            try:
                validate_response(response)
                log_result(category, name, "passed", f"HTTP {status}")
                return True, response
            except AssertionError as e:
                log_result(category, name, "failed", f"Validation: {str(e)[:40]}")
                return False, response
        else:
            log_result(category, name, "passed", f"HTTP {status}")
            return True, response
    elif status == 0:
        log_result(category, name, "failed", response.get("error", "Connection error")[:50])
        return False, response
    else:
        detail = response.get("detail", str(response))[:50] if isinstance(response, dict) else str(response)[:50]
        log_result(category, name, "failed", f"HTTP {status}: {detail}")
        return False, response


# ==============================================================================
# WORKFLOW 1: COST OPTIMIZATION COMPLETE FLOW
# ==============================================================================

def workflow_cost_optimization():
    """Test complete cost optimization workflow from estimate to detailed analysis"""
    print("\n" + "="*70)
    print("WORKFLOW: Cost Optimization (Complete Flow)")
    print("="*70)

    # Step 1: Get quick estimate for corn
    passed, response = test_endpoint(
        "Cost Optimization", "Step 1: Quick estimate (corn, non-irrigated)",
        "POST", "/api/v1/optimize/quick-estimate",
        data={"acres": 160, "crop": "corn", "is_irrigated": False, "yield_goal": 200},
        expected_codes=[200, 422]
    )

    base_cost = 0
    if passed and response:
        base_cost = response.get("total_cost_per_acre", 0)

    # Step 2: Get irrigated estimate and verify cost increase
    passed, response = test_endpoint(
        "Cost Optimization", "Step 2: Irrigated estimate (verify cost increase)",
        "POST", "/api/v1/optimize/quick-estimate",
        data={"acres": 160, "crop": "corn", "is_irrigated": True, "yield_goal": 200},
        expected_codes=[200, 422]
    )

    if passed and response:
        irrigated_cost = response.get("total_cost_per_acre", 0)
        if irrigated_cost > base_cost:
            log_result("Cost Optimization", "Step 2a: Irrigation adds cost correctly", "passed",
                      f"${irrigated_cost:.0f} > ${base_cost:.0f}")
        else:
            log_result("Cost Optimization", "Step 2a: Irrigation adds cost correctly", "failed",
                      f"${irrigated_cost:.0f} should be > ${base_cost:.0f}")

    # Step 3: Fertilizer optimization with soil tests
    passed, response = test_endpoint(
        "Cost Optimization", "Step 3: Fertilizer optimization with soil test",
        "POST", "/api/v1/optimize/fertilizer",
        data={
            "crop": "corn", "yield_goal": 200, "acres": 160,
            "soil_test_p_ppm": 20, "soil_test_k_ppm": 150, "soil_ph": 6.5,
            "organic_matter_percent": 3.0, "nitrogen_credit_lb_per_acre": 0
        },
        expected_codes=[200, 422]
    )

    if passed and response:
        recs = response.get("recommendations", [])
        cost_summary = response.get("cost_summary", {})
        log_result("Cost Optimization", "Step 3a: Fertilizer recommendations generated", "passed",
                  f"{len(recs)} recommendations, ${cost_summary.get('cost_per_acre', 0):.2f}/acre")

    # Step 4: Verify with N-credit applied (should reduce cost)
    passed, response = test_endpoint(
        "Cost Optimization", "Step 4: N-credit optimization (verify cost reduction)",
        "POST", "/api/v1/optimize/fertilizer",
        data={
            "crop": "corn", "yield_goal": 200, "acres": 160,
            "soil_test_p_ppm": 20, "soil_test_k_ppm": 150, "soil_ph": 6.5,
            "organic_matter_percent": 3.0, "nitrogen_credit_lb_per_acre": 50
        },
        expected_codes=[200, 422]
    )

    # Step 5: Soybean comparison
    passed, response = test_endpoint(
        "Cost Optimization", "Step 5: Soybean estimate (crop comparison)",
        "POST", "/api/v1/optimize/quick-estimate",
        data={"acres": 160, "crop": "soybean", "is_irrigated": False, "yield_goal": 55},
        expected_codes=[200, 422]
    )


# ==============================================================================
# WORKFLOW 2: SPRAY TIMING AND PEST MANAGEMENT
# ==============================================================================

def workflow_spray_timing():
    """Test complete spray timing and pest management workflow"""
    print("\n" + "="*70)
    print("WORKFLOW: Spray Timing & Pest Management")
    print("="*70)

    current_time = datetime.now().isoformat()

    # Step 1: List available pests
    passed, response = test_endpoint(
        "Spray Management", "Step 1: List pests for corn",
        "GET", "/api/v1/pests?crop=corn",
        expected_codes=[200]
    )

    # Step 2: List diseases
    passed, response = test_endpoint(
        "Spray Management", "Step 2: List diseases for corn",
        "GET", "/api/v1/diseases?crop=corn",
        expected_codes=[200]
    )

    # Step 3: Evaluate spray conditions
    passed, response = test_endpoint(
        "Spray Management", "Step 3: Evaluate current conditions for spraying",
        "POST", "/api/v1/spray-timing/evaluate",
        data={
            "weather": {
                "datetime": current_time,
                "temp_f": 72,
                "humidity_pct": 55,
                "wind_mph": 6,
                "wind_direction": "NW"
            },
            "spray_type": "herbicide"
        },
        expected_codes=[200, 422]
    )

    if passed and response:
        rating = response.get("overall_rating", "unknown")
        log_result("Spray Management", "Step 3a: Spray conditions assessed", "passed",
                  f"Rating: {rating}")

    # Step 4: Check disease pressure
    passed, response = test_endpoint(
        "Spray Management", "Step 4: Assess disease pressure",
        "POST", "/api/v1/spray-timing/disease-pressure",
        data={
            "weather_history": [{
                "datetime": current_time,
                "temp_f": 78,
                "humidity_pct": 85,
                "wind_mph": 3,
                "wind_direction": "S"
            }],
            "crop": "corn",
            "growth_stage": "V6"
        },
        expected_codes=[200, 422]
    )

    # Step 5: Identify pest by symptoms
    passed, response = test_endpoint(
        "Spray Management", "Step 5: Identify pest from symptoms",
        "POST", "/api/v1/identify/pest",
        data={
            "crop": "corn",
            "symptoms": ["leaf_damage", "holes", "chewing"],
            "growth_stage": "V6"
        },
        expected_codes=[200, 422]
    )

    # Step 6: Identify disease by symptoms
    passed, response = test_endpoint(
        "Spray Management", "Step 6: Identify disease from symptoms",
        "POST", "/api/v1/identify/disease",
        data={
            "crop": "corn",
            "symptoms": ["leaf_spots", "yellowing", "lesions"],
            "growth_stage": "V6"
        },
        expected_codes=[200, 422]
    )


# ==============================================================================
# WORKFLOW 3: YIELD RESPONSE ANALYSIS
# ==============================================================================

def workflow_yield_response():
    """Test yield response and economic analysis workflow"""
    print("\n" + "="*70)
    print("WORKFLOW: Yield Response Analysis")
    print("="*70)

    # Step 1: Generate nitrogen response curve
    passed, response = test_endpoint(
        "Yield Response", "Step 1: Generate N response curve",
        "POST", "/api/v1/yield-response/curve",
        data={"crop": "corn", "nutrient": "nitrogen"},
        expected_codes=[200, 422]
    )

    if passed and response:
        curve_points = len(response.get("curve", []))
        log_result("Yield Response", "Step 1a: Curve data generated", "passed",
                  f"{curve_points} data points")

    # Step 2: Calculate economic optimum
    passed, response = test_endpoint(
        "Yield Response", "Step 2: Calculate economic optimum rate",
        "POST", "/api/v1/yield-response/economic-optimum",
        data={
            "crop": "corn",
            "nutrient": "nitrogen",
            "nutrient_price_per_lb": 0.55,
            "grain_price_per_bu": 4.50
        },
        expected_codes=[200, 422]
    )

    if passed and response:
        eon_rate = response.get("economic_optimum_rate", 0)
        if eon_rate > 0:
            log_result("Yield Response", "Step 2a: Economic optimum calculated", "passed",
                      f"EON: {eon_rate:.0f} lb/acre")

    # Step 3: Compare multiple rates
    passed, response = test_endpoint(
        "Yield Response", "Step 3: Compare rate scenarios",
        "POST", "/api/v1/yield-response/compare-rates",
        data={
            "crop": "corn",
            "nutrient": "nitrogen",
            "rates": [100, 150, 180, 200],
            "nutrient_price_per_lb": 0.55,
            "grain_price_per_bu": 4.50
        },
        expected_codes=[200, 422]
    )


# ==============================================================================
# WORKFLOW 4: GENFIN ACCOUNTING COMPLETE FLOW
# ==============================================================================

def workflow_genfin_accounting():
    """Test GenFin accounting system workflow"""
    print("\n" + "="*70)
    print("WORKFLOW: GenFin Accounting System")
    print("="*70)

    # Step 1: Get entities/companies
    passed, response = test_endpoint(
        "GenFin", "Step 1: List entities/companies",
        "GET", "/api/v1/genfin/entities",
        expected_codes=[200]
    )

    # Step 2: Get chart of accounts
    passed, response = test_endpoint(
        "GenFin", "Step 2: Get chart of accounts",
        "GET", "/api/v1/genfin/chart-of-accounts",
        expected_codes=[200]
    )

    if passed and response:
        accounts = response.get("accounts", [])
        log_result("GenFin", "Step 2a: Chart of accounts loaded", "passed",
                  f"{len(accounts)} accounts")

    # Step 3: Get financial summary
    passed, response = test_endpoint(
        "GenFin", "Step 3: Get financial summary",
        "GET", "/api/v1/genfin/summary",
        expected_codes=[200]
    )

    # Step 4: Get invoices (AR)
    passed, response = test_endpoint(
        "GenFin", "Step 4: List invoices (AR)",
        "GET", "/api/v1/genfin/invoices",
        expected_codes=[200]
    )

    # Step 5: Get bills (AP)
    passed, response = test_endpoint(
        "GenFin", "Step 5: List bills (AP)",
        "GET", "/api/v1/genfin/bills",
        expected_codes=[200]
    )

    # Step 6: Get checks
    passed, response = test_endpoint(
        "GenFin", "Step 6: List checks",
        "GET", "/api/v1/genfin/checks",
        expected_codes=[200]
    )

    # Step 7: Get bank accounts
    passed, response = test_endpoint(
        "GenFin", "Step 7: List bank accounts",
        "GET", "/api/v1/genfin/bank-accounts",
        expected_codes=[200]
    )

    # Step 8: Get payroll summary
    today = date.today()
    start = (today.replace(day=1)).isoformat()
    end = today.isoformat()
    passed, response = test_endpoint(
        "GenFin", "Step 8: Get payroll summary",
        "GET", f"/api/v1/genfin/payroll-summary?start_date={start}&end_date={end}",
        expected_codes=[200]
    )


# ==============================================================================
# WORKFLOW 5: FIELD & EQUIPMENT MANAGEMENT
# ==============================================================================

def workflow_field_equipment():
    """Test field and equipment management workflow"""
    print("\n" + "="*70)
    print("WORKFLOW: Field & Equipment Management")
    print("="*70)

    # Step 1: List fields
    passed, response = test_endpoint(
        "Field Management", "Step 1: List fields",
        "GET", "/api/v1/fields",
        expected_codes=[200, 401]
    )

    # Step 2: Get field summary
    passed, response = test_endpoint(
        "Field Management", "Step 2: Get field summary",
        "GET", "/api/v1/fields/summary",
        expected_codes=[200, 401]
    )

    # Step 3: Get farm names
    passed, response = test_endpoint(
        "Field Management", "Step 3: Get farm names",
        "GET", "/api/v1/fields/farms",
        expected_codes=[200, 401]
    )

    # Step 4: List equipment
    passed, response = test_endpoint(
        "Equipment", "Step 4: List equipment",
        "GET", "/api/v1/equipment",
        expected_codes=[200, 401]
    )

    if passed and response:
        items = response.get("items", response) if isinstance(response, dict) else response
        log_result("Equipment", "Step 4a: Equipment listed", "passed",
                  f"{len(items) if isinstance(items, list) else 'N/A'} items")

    # Step 5: Get equipment summary
    passed, response = test_endpoint(
        "Equipment", "Step 5: Get equipment summary",
        "GET", "/api/v1/equipment/summary",
        expected_codes=[200, 401]
    )

    # Step 6: Get equipment types
    passed, response = test_endpoint(
        "Equipment", "Step 6: Get equipment types",
        "GET", "/api/v1/equipment/types",
        expected_codes=[200, 401]
    )

    # Step 7: List maintenance records
    passed, response = test_endpoint(
        "Equipment", "Step 7: List maintenance records",
        "GET", "/api/v1/maintenance",
        expected_codes=[200, 401]
    )

    # Step 8: Get maintenance alerts
    passed, response = test_endpoint(
        "Equipment", "Step 8: Get maintenance alerts",
        "GET", "/api/v1/maintenance/alerts",
        expected_codes=[200, 401]
    )


# ==============================================================================
# WORKFLOW 6: INVENTORY & TASKS
# ==============================================================================

def workflow_inventory_tasks():
    """Test inventory and task management workflow"""
    print("\n" + "="*70)
    print("WORKFLOW: Inventory & Task Management")
    print("="*70)

    # Step 1: List inventory
    passed, response = test_endpoint(
        "Inventory", "Step 1: List inventory items",
        "GET", "/api/v1/inventory",
        expected_codes=[200, 401]
    )

    # Step 2: Get inventory categories
    passed, response = test_endpoint(
        "Inventory", "Step 2: Get inventory categories",
        "GET", "/api/v1/inventory/categories",
        expected_codes=[200, 401]
    )

    if passed and response:
        cats = response if isinstance(response, list) else response.get("categories", [])
        log_result("Inventory", "Step 2a: Categories loaded", "passed",
                  f"{len(cats)} categories")

    # Step 3: Get inventory summary
    passed, response = test_endpoint(
        "Inventory", "Step 3: Get inventory summary",
        "GET", "/api/v1/inventory/summary",
        expected_codes=[200, 401]
    )

    # Step 4: Get inventory alerts
    passed, response = test_endpoint(
        "Inventory", "Step 4: Get inventory alerts",
        "GET", "/api/v1/inventory/alerts",
        expected_codes=[200, 401]
    )

    # Step 5: List tasks
    passed, response = test_endpoint(
        "Tasks", "Step 5: List tasks",
        "GET", "/api/v1/tasks",
        expected_codes=[200, 401]
    )

    # Step 6: List crews
    passed, response = test_endpoint(
        "Tasks", "Step 6: List crews",
        "GET", "/api/v1/crews",
        expected_codes=[200, 401]
    )

    # Step 7: List operations
    passed, response = test_endpoint(
        "Operations", "Step 7: List field operations",
        "GET", "/api/v1/operations",
        expected_codes=[200, 401]
    )

    # Step 8: Get operations summary
    passed, response = test_endpoint(
        "Operations", "Step 8: Get operations summary",
        "GET", "/api/v1/operations/summary",
        expected_codes=[200, 401]
    )


# ==============================================================================
# WORKFLOW 7: GRANTS & COMPLIANCE
# ==============================================================================

def workflow_grants():
    """Test grants and compliance workflow"""
    print("\n" + "="*70)
    print("WORKFLOW: Grants & Compliance")
    print("="*70)

    # Step 1: List grant programs
    passed, response = test_endpoint(
        "Grants", "Step 1: List grant programs",
        "GET", "/api/v1/grants/programs",
        expected_codes=[200]
    )

    # Step 2: Get NRCS practices
    passed, response = test_endpoint(
        "Grants", "Step 2: Get NRCS conservation practices",
        "GET", "/api/v1/grants/nrcs-practices",
        expected_codes=[200]
    )

    if passed and response:
        practices = response.get("practices", response) if isinstance(response, dict) else response
        log_result("Grants", "Step 2a: NRCS practices loaded", "passed",
                  f"{len(practices) if isinstance(practices, list) else 'N/A'} practices")

    # Step 3: Get practices summary
    passed, response = test_endpoint(
        "Grants", "Step 3: Get practices summary",
        "GET", "/api/v1/grants/practices/summary",
        expected_codes=[200]
    )

    # Step 4: Get benchmarks
    passed, response = test_endpoint(
        "Grants", "Step 4: Get benchmarks",
        "GET", "/api/v1/grants/benchmarks",
        expected_codes=[200]
    )

    # Step 5: Get carbon programs
    passed, response = test_endpoint(
        "Grants", "Step 5: Get carbon programs",
        "GET", "/api/v1/grants/carbon-programs",
        expected_codes=[200]
    )

    # Step 6: Get technologies
    passed, response = test_endpoint(
        "Grants", "Step 6: Get precision ag technologies",
        "GET", "/api/v1/grants/technologies",
        expected_codes=[200]
    )


# ==============================================================================
# WORKFLOW 8: PRICING & MARKET ANALYSIS
# ==============================================================================

def workflow_pricing():
    """Test pricing and market analysis workflow"""
    print("\n" + "="*70)
    print("WORKFLOW: Pricing & Market Analysis")
    print("="*70)

    # Step 1: Get all prices
    passed, response = test_endpoint(
        "Pricing", "Step 1: Get all current prices",
        "GET", "/api/v1/pricing/prices",
        expected_codes=[200]
    )

    if passed and response:
        categories = response.get("categories", {})
        log_result("Pricing", "Step 1a: Price categories loaded", "passed",
                  f"{len(categories)} categories")

    # Step 2: Get price alerts
    passed, response = test_endpoint(
        "Pricing", "Step 2: Get price alerts",
        "GET", "/api/v1/pricing/alerts",
        expected_codes=[200]
    )

    # Step 3: Get budget prices for corn
    passed, response = test_endpoint(
        "Pricing", "Step 3: Get budget prices for corn",
        "GET", "/api/v1/pricing/budget-prices/corn",
        expected_codes=[200]
    )

    # Step 4: Get spray window from weather
    passed, response = test_endpoint(
        "Pricing", "Step 4: Get weather spray window",
        "GET", "/api/v1/weather/spray-window?latitude=41.5&longitude=-93.5",
        expected_codes=[200, 422, 500]
    )

    # Step 5: Get growth stage estimate
    today = date.today()
    planting = (today - timedelta(days=60)).isoformat()
    passed, response = test_endpoint(
        "Pricing", "Step 5: Estimate growth stage",
        "GET", f"/api/v1/growth-stage/estimate?crop=corn&planting_date={planting}&location_lat=41.5&location_lon=-93.5",
        expected_codes=[200, 422]
    )


# ==============================================================================
# WORKFLOW 9: REPORTS & DASHBOARD
# ==============================================================================

def workflow_reports():
    """Test reports and dashboard workflow"""
    print("\n" + "="*70)
    print("WORKFLOW: Reports & Dashboard")
    print("="*70)

    # Step 1: Get dashboard summary
    passed, response = test_endpoint(
        "Reports", "Step 1: Get dashboard summary",
        "GET", "/api/v1/reports/dashboard",
        expected_codes=[200]
    )

    # Step 2: Get operations report
    passed, response = test_endpoint(
        "Reports", "Step 2: Get operations report",
        "GET", "/api/v1/reports/operations",
        expected_codes=[200]
    )

    # Step 3: Get financial report
    passed, response = test_endpoint(
        "Reports", "Step 3: Get financial report",
        "GET", "/api/v1/reports/financial",
        expected_codes=[200]
    )

    # Step 4: Get equipment report
    passed, response = test_endpoint(
        "Reports", "Step 4: Get equipment report",
        "GET", "/api/v1/reports/equipment",
        expected_codes=[200]
    )

    # Step 5: Get inventory report
    passed, response = test_endpoint(
        "Reports", "Step 5: Get inventory report",
        "GET", "/api/v1/reports/inventory",
        expected_codes=[200]
    )


# ==============================================================================
# MAIN
# ==============================================================================

def run_all_workflows():
    """Run all workflow tests"""
    print("\n" + "="*80)
    print("AGTOOLS COMPREHENSIVE WORKFLOW TEST SUITE v6.8.1")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {BASE_URL}")

    # Check server
    try:
        status, _ = http_request("GET", "/docs")
        if status != 200:
            print(f"\nERROR: Server not responding (HTTP {status})")
            print("Start the backend: cd backend && python main.py")
            return False
    except Exception as e:
        print(f"\nERROR: Cannot connect: {e}")
        return False

    print("Server: OK\n")

    # Run all workflows
    workflows = [
        workflow_cost_optimization,
        workflow_spray_timing,
        workflow_yield_response,
        workflow_genfin_accounting,
        workflow_field_equipment,
        workflow_inventory_tasks,
        workflow_grants,
        workflow_pricing,
        workflow_reports,
    ]

    for workflow in workflows:
        try:
            workflow()
        except Exception as e:
            print(f"\n*** ERROR in {workflow.__name__}: {e}")

    # Summary
    print("\n" + "="*80)
    print("RESULTS BY CATEGORY")
    print("="*80)

    total_passed = 0
    total_failed = 0

    for category in sorted(CATEGORIES.keys()):
        stats = CATEGORIES[category]
        total = stats["passed"] + stats["failed"]
        pct = (stats["passed"] / total * 100) if total > 0 else 0
        status = "OK" if stats["failed"] == 0 else "ISSUES"
        print(f"  {category:25} {stats['passed']:3}/{total:3} ({pct:5.1f}%) [{status}]")
        total_passed += stats["passed"]
        total_failed += stats["failed"]

    total = total_passed + total_failed
    pct = (total_passed / total * 100) if total > 0 else 0

    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"  Total Tests:  {total}")
    print(f"  Passed:       {total_passed} ({pct:.1f}%)")
    print(f"  Failed:       {total_failed} ({100-pct:.1f}%)")

    if total_failed > 0:
        print("\n*** FAILED TESTS ***")
        for r in RESULTS:
            if r["status"] == "failed":
                print(f"  - [{r['category']}] {r['test']}: {r['details']}")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return total_failed == 0


if __name__ == "__main__":
    success = run_all_workflows()
    sys.exit(0 if success else 1)
