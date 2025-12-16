#!/usr/bin/env python3
"""
AgTools v2.5.0 Comprehensive Smoke Tests
Tests all major API endpoints across all phases
"""

import json
import sys
from datetime import datetime

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

BASE_URL = "http://127.0.0.1:8000"
RESULTS = []
TOKEN = None


def log_result(category: str, test: str, passed: bool, details: str = ""):
    """Log a test result"""
    status = "[PASS]" if passed else "[FAIL]"
    RESULTS.append({
        "category": category,
        "test": test,
        "passed": passed,
        "details": details
    })
    print(f"  {status}: {test}" + (f" - {details}" if details else ""))


def test_root():
    """Test root endpoint"""
    print("\n=== 1. ROOT ENDPOINT ===")
    try:
        r = httpx.get(f"{BASE_URL}/", timeout=10)
        data = r.json()
        log_result("Root", "GET /", r.status_code == 200,
                   f"{data.get('name')} - {data.get('status')}")
    except Exception as e:
        log_result("Root", "GET /", False, str(e))


def test_authentication():
    """Test authentication endpoints"""
    global TOKEN
    print("\n=== 2. AUTHENTICATION ===")

    # Login (token is nested: data["tokens"]["access_token"])
    try:
        r = httpx.post(f"{BASE_URL}/api/v1/auth/login",
                       json={"username": "admin", "password": "admin123"},
                       timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Token is nested under "tokens"
            tokens = data.get("tokens", {})
            TOKEN = tokens.get("access_token")
            if TOKEN and TOKEN != "None":
                user = data.get("user", {})
                log_result("Auth", "POST /auth/login", True,
                           f"User: {user.get('username')} ({user.get('role')})")
            else:
                log_result("Auth", "POST /auth/login", False, "No token in response")
                TOKEN = None
        else:
            log_result("Auth", "POST /auth/login", False, f"Status: {r.status_code} - {r.text[:100]}")
    except Exception as e:
        log_result("Auth", "POST /auth/login", False, str(e))

    # Get current user
    if TOKEN:
        try:
            headers = {"Authorization": f"Bearer {TOKEN}"}
            r = httpx.get(f"{BASE_URL}/api/v1/auth/me",
                          headers=headers,
                          timeout=10)
            if r.status_code == 200:
                data = r.json()
                log_result("Auth", "GET /auth/me", True,
                           f"User: {data.get('username')} ({data.get('role')})")
            else:
                # Debug: show what we're sending
                log_result("Auth", "GET /auth/me", False,
                           f"Status: {r.status_code} (token len: {len(TOKEN) if TOKEN else 0})")
        except Exception as e:
            log_result("Auth", "GET /auth/me", False, str(e))
    else:
        log_result("Auth", "GET /auth/me", False, "Skipped - no token")


def get_headers():
    """Get auth headers"""
    return {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


def test_user_management():
    """Test user management endpoints"""
    print("\n=== 3. USER MANAGEMENT ===")

    # List users
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/users", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else data.get("total", 0)
            log_result("Users", "GET /users", True, f"{count} users")
        else:
            log_result("Users", "GET /users", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Users", "GET /users", False, str(e))


def test_crew_management():
    """Test crew management endpoints"""
    print("\n=== 4. CREW MANAGEMENT ===")

    # List crews
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/crews", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else 0
            log_result("Crews", "GET /crews", True, f"{count} crews")
        else:
            log_result("Crews", "GET /crews", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Crews", "GET /crews", False, str(e))


def test_task_management():
    """Test task management endpoints"""
    print("\n=== 5. TASK MANAGEMENT ===")

    # List tasks
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/tasks", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else 0
            log_result("Tasks", "GET /tasks", True, f"{count} tasks")
        else:
            log_result("Tasks", "GET /tasks", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Tasks", "GET /tasks", False, str(e))


def test_field_management():
    """Test field management endpoints"""
    print("\n=== 6. FIELD MANAGEMENT ===")

    # List fields
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/fields", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else 0
            log_result("Fields", "GET /fields", True, f"{count} fields")
        else:
            log_result("Fields", "GET /fields", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Fields", "GET /fields", False, str(e))

    # Field summary
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/fields/summary", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            log_result("Fields", "GET /fields/summary", True,
                       f"Total acres: {data.get('total_acres', 0)}")
        else:
            log_result("Fields", "GET /fields/summary", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Fields", "GET /fields/summary", False, str(e))


def test_operations_logging():
    """Test operations logging endpoints"""
    print("\n=== 7. OPERATIONS LOGGING ===")

    # List operations
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/operations", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else 0
            log_result("Operations", "GET /operations", True, f"{count} operations")
        else:
            log_result("Operations", "GET /operations", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Operations", "GET /operations", False, str(e))

    # Operations summary
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/operations/summary", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            log_result("Operations", "GET /operations/summary", True,
                       f"Total cost: ${data.get('total_cost', 0):.2f}")
        else:
            log_result("Operations", "GET /operations/summary", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Operations", "GET /operations/summary", False, str(e))


def test_pricing_api():
    """Test pricing service endpoints"""
    print("\n=== 8. PRICING SERVICE ===")

    # Get all prices
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/pricing/prices", timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else 0
            log_result("Pricing", "GET /pricing/prices", True, f"{count} products")
        else:
            log_result("Pricing", "GET /pricing/prices", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Pricing", "GET /pricing/prices", False, str(e))

    # Buy recommendation (correct schema: product_id, quantity_needed, purchase_deadline)
    try:
        r = httpx.post(f"{BASE_URL}/api/v1/pricing/buy-recommendation",
                       json={"product_id": "urea_46", "quantity_needed": 10.0},
                       timeout=10)
        if r.status_code == 200:
            data = r.json()
            rec = data.get("recommendation", "unknown")
            log_result("Pricing", "POST /pricing/buy-recommendation", True, f"Rec: {rec}")
        else:
            log_result("Pricing", "POST /pricing/buy-recommendation", False,
                       f"Status: {r.status_code}")
    except Exception as e:
        log_result("Pricing", "POST /pricing/buy-recommendation", False, str(e))


def test_yield_response():
    """Test yield response optimizer endpoints"""
    print("\n=== 9. YIELD RESPONSE OPTIMIZER ===")

    # Economic optimum rate (correct schema: crop, nutrient, nutrient_price_per_lb, grain_price_per_bu)
    try:
        r = httpx.post(f"{BASE_URL}/api/v1/yield-response/economic-optimum",
                       json={
                           "crop": "corn",
                           "nutrient": "nitrogen",
                           "soil_test_level": "medium",
                           "nutrient_price_per_lb": 0.50,
                           "grain_price_per_bu": 5.00,
                           "acres": 100
                       },
                       timeout=10)
        if r.status_code == 200:
            data = r.json()
            eor = data.get("eor_rate", data.get("optimal_rate", 0))
            log_result("YieldResponse", "POST /yield-response/economic-optimum", True,
                       f"EOR: {eor:.1f} lb/acre")
        else:
            log_result("YieldResponse", "POST /yield-response/economic-optimum", False,
                       f"Status: {r.status_code}")
    except Exception as e:
        log_result("YieldResponse", "POST /yield-response/economic-optimum", False, str(e))

    # Crop parameters
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/yield-response/crop-parameters/corn", timeout=10)
        if r.status_code == 200:
            data = r.json()
            nutrients = list(data.keys()) if isinstance(data, dict) else []
            log_result("YieldResponse", "GET /yield-response/crop-parameters/corn", True,
                       f"Nutrients: {', '.join(nutrients)}")
        else:
            log_result("YieldResponse", "GET /yield-response/crop-parameters/corn", False,
                       f"Status: {r.status_code}")
    except Exception as e:
        log_result("YieldResponse", "GET /yield-response/crop-parameters/corn", False, str(e))


def test_spray_timing():
    """Test spray timing optimizer endpoints"""
    print("\n=== 10. SPRAY TIMING OPTIMIZER ===")

    # Evaluate conditions (correct schema: nested weather object)
    try:
        r = httpx.post(f"{BASE_URL}/api/v1/spray-timing/evaluate",
                       json={
                           "weather": {
                               "datetime": "2025-12-16T10:00:00",
                               "temp_f": 72.0,
                               "humidity_pct": 55.0,
                               "wind_mph": 8.0,
                               "wind_direction": "SW",
                               "precip_chance_pct": 10.0
                           },
                           "spray_type": "herbicide"
                       },
                       timeout=10)
        if r.status_code == 200:
            data = r.json()
            risk = data.get("risk_level", "unknown")
            score = data.get("score", data.get("overall_score", 0))
            log_result("SprayTiming", "POST /spray-timing/evaluate", True,
                       f"Risk: {risk}, Score: {score}")
        else:
            log_result("SprayTiming", "POST /spray-timing/evaluate", False,
                       f"Status: {r.status_code}")
    except Exception as e:
        log_result("SprayTiming", "POST /spray-timing/evaluate", False, str(e))

    # Growth stage timing
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/spray-timing/growth-stage-timing/corn/V6", timeout=10)
        if r.status_code == 200:
            data = r.json()
            log_result("SprayTiming", "GET /spray-timing/growth-stage-timing/corn/V6", True,
                       f"Stage: {data.get('growth_stage', 'V6')}")
        else:
            log_result("SprayTiming", "GET /spray-timing/growth-stage-timing/corn/V6", False,
                       f"Status: {r.status_code}")
    except Exception as e:
        log_result("SprayTiming", "GET /spray-timing/growth-stage-timing/corn/V6", False, str(e))


def test_cost_optimizer():
    """Test cost optimizer endpoints"""
    print("\n=== 11. COST OPTIMIZER ===")

    # Quick estimate
    try:
        r = httpx.post(f"{BASE_URL}/api/v1/optimize/quick-estimate",
                       json={
                           "crop": "corn",
                           "acres": 500,
                           "yield_goal": 200,
                           "irrigated": False
                       },
                       timeout=10)
        if r.status_code == 200:
            data = r.json()
            total = data.get("total_cost", 0)
            log_result("CostOptimizer", "POST /optimize/quick-estimate", True,
                       f"Total: ${total:,.2f}")
        else:
            log_result("CostOptimizer", "POST /optimize/quick-estimate", False,
                       f"Status: {r.status_code}")
    except Exception as e:
        log_result("CostOptimizer", "POST /optimize/quick-estimate", False, str(e))


def test_pest_identification():
    """Test pest identification endpoints"""
    print("\n=== 12. PEST IDENTIFICATION ===")

    # Identify pest (response is a direct list)
    try:
        r = httpx.post(f"{BASE_URL}/api/v1/identify/pest",
                       json={
                           "crop": "corn",
                           "growth_stage": "V6",
                           "symptoms": ["leaf_feeding", "holes_in_leaves"],
                           "severity_rating": 5
                       },
                       timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Response is a direct list of matches
            matches = data if isinstance(data, list) else data.get("matches", [])
            if matches:
                top_pest = matches[0].get("common_name", "Unknown")
                confidence = matches[0].get("confidence", 0)
                log_result("PestID", "POST /identify/pest", True,
                           f"Top: {top_pest} ({confidence:.0%})")
            else:
                log_result("PestID", "POST /identify/pest", True, "No matches")
        else:
            log_result("PestID", "POST /identify/pest", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("PestID", "POST /identify/pest", False, str(e))


def test_disease_identification():
    """Test disease identification endpoints"""
    print("\n=== 13. DISEASE IDENTIFICATION ===")

    # Identify disease (response is a direct list)
    try:
        r = httpx.post(f"{BASE_URL}/api/v1/identify/disease",
                       json={
                           "crop": "corn",
                           "growth_stage": "V6",
                           "symptoms": ["leaf_spots", "yellowing"],
                           "severity_rating": 6
                       },
                       timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Response is a direct list of matches
            matches = data if isinstance(data, list) else data.get("matches", [])
            if matches:
                top_disease = matches[0].get("common_name", "Unknown")
                confidence = matches[0].get("confidence", 0)
                log_result("DiseaseID", "POST /identify/disease", True,
                           f"Top: {top_disease} ({confidence:.0%})")
            else:
                log_result("DiseaseID", "POST /identify/disease", True, "No matches")
        else:
            log_result("DiseaseID", "POST /identify/disease", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("DiseaseID", "POST /identify/disease", False, str(e))


def test_api_docs():
    """Test API documentation endpoints"""
    print("\n=== 14. API DOCUMENTATION ===")

    # OpenAPI docs
    try:
        r = httpx.get(f"{BASE_URL}/docs", timeout=10)
        log_result("Docs", "GET /docs (Swagger UI)", r.status_code == 200,
                   f"Status: {r.status_code}")
    except Exception as e:
        log_result("Docs", "GET /docs (Swagger UI)", False, str(e))

    # OpenAPI JSON
    try:
        r = httpx.get(f"{BASE_URL}/openapi.json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            paths = len(data.get("paths", {}))
            log_result("Docs", "GET /openapi.json", True, f"{paths} endpoints documented")
        else:
            log_result("Docs", "GET /openapi.json", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Docs", "GET /openapi.json", False, str(e))


def generate_report():
    """Generate test report"""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in RESULTS if r["passed"])
    failed = sum(1 for r in RESULTS if not r["passed"])
    total = len(RESULTS)

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")

    if failed > 0:
        print("\n--- FAILED TESTS ---")
        for r in RESULTS:
            if not r["passed"]:
                print(f"  [X] [{r['category']}] {r['test']}: {r['details']}")

    # Group by category
    print("\n--- BY CATEGORY ---")
    categories = {}
    for r in RESULTS:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"passed": 0, "failed": 0}
        if r["passed"]:
            categories[cat]["passed"] += 1
        else:
            categories[cat]["failed"] += 1

    for cat, counts in categories.items():
        status = "[OK]" if counts["failed"] == 0 else "[X]"
        print(f"  {status} {cat}: {counts['passed']}/{counts['passed']+counts['failed']} passed")

    return {
        "timestamp": datetime.now().isoformat(),
        "version": "2.5.0",
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{passed/total*100:.1f}%",
        "results": RESULTS,
        "by_category": categories
    }


def main():
    print("=" * 60)
    print("AGTOOLS v2.5.0 COMPREHENSIVE SMOKE TESTS")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Run all tests
    test_root()
    test_authentication()
    test_user_management()
    test_crew_management()
    test_task_management()
    test_field_management()
    test_operations_logging()
    test_pricing_api()
    test_yield_response()
    test_spray_timing()
    test_cost_optimizer()
    test_pest_identification()
    test_disease_identification()
    test_api_docs()

    # Generate report
    report = generate_report()

    # Save report
    report_path = "tests/smoke_test_results_v25.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nResults saved to: {report_path}")

    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
