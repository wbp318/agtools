#!/usr/bin/env python3
"""
AgTools v2.6.0 Comprehensive Smoke Tests
Tests all major API endpoints including new Mobile/Crew Interface (Phase 6)
"""

import json
import os
import sys
from datetime import datetime

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

BASE_URL = os.environ.get("AGTOOLS_TEST_URL", "http://127.0.0.1:8000")
TEST_USERNAME = os.environ.get("AGTOOLS_TEST_USERNAME", "admin")
TEST_PASSWORD = os.environ.get("AGTOOLS_TEST_PASSWORD", "admin123")  # nosec B105
RESULTS = []
TOKEN = None
SESSION_COOKIE = None


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

    # Login
    try:
        r = httpx.post(f"{BASE_URL}/api/v1/auth/login",
                       json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
                       timeout=10)
        if r.status_code == 200:
            data = r.json()
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
            log_result("Auth", "POST /auth/login", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Auth", "POST /auth/login", False, str(e))

    # Get current user
    if TOKEN:
        try:
            headers = {"Authorization": f"Bearer {TOKEN}"}
            r = httpx.get(f"{BASE_URL}/api/v1/auth/me", headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                log_result("Auth", "GET /auth/me", True,
                           f"User: {data.get('username')} ({data.get('role')})")
            else:
                log_result("Auth", "GET /auth/me", False, f"Status: {r.status_code}")
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


def test_pricing_api():
    """Test pricing service endpoints"""
    print("\n=== 8. PRICING SERVICE ===")
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


def test_yield_response():
    """Test yield response optimizer endpoints"""
    print("\n=== 9. YIELD RESPONSE OPTIMIZER ===")
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


def test_spray_timing():
    """Test spray timing optimizer endpoints"""
    print("\n=== 10. SPRAY TIMING OPTIMIZER ===")
    try:
        r = httpx.post(f"{BASE_URL}/api/v1/spray-timing/evaluate",
                       json={
                           "weather": {
                               "datetime": "2025-12-22T10:00:00",
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


def test_cost_optimizer():
    """Test cost optimizer endpoints"""
    print("\n=== 11. COST OPTIMIZER ===")
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


def test_equipment_management():
    """Test equipment management endpoints"""
    print("\n=== 13. EQUIPMENT MANAGEMENT ===")
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/equipment", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else 0
            log_result("Equipment", "GET /equipment", True, f"{count} items")
        else:
            log_result("Equipment", "GET /equipment", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Equipment", "GET /equipment", False, str(e))

    try:
        r = httpx.get(f"{BASE_URL}/api/v1/equipment/summary", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            log_result("Equipment", "GET /equipment/summary", True,
                       f"{data.get('total_equipment', 0)} items")
        else:
            log_result("Equipment", "GET /equipment/summary", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Equipment", "GET /equipment/summary", False, str(e))


def test_inventory_management():
    """Test inventory management endpoints"""
    print("\n=== 14. INVENTORY MANAGEMENT ===")
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/inventory", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else 0
            log_result("Inventory", "GET /inventory", True, f"{count} items")
        else:
            log_result("Inventory", "GET /inventory", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Inventory", "GET /inventory", False, str(e))

    try:
        r = httpx.get(f"{BASE_URL}/api/v1/inventory/summary", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            log_result("Inventory", "GET /inventory/summary", True,
                       f"{data.get('total_items', 0)} items")
        else:
            log_result("Inventory", "GET /inventory/summary", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Inventory", "GET /inventory/summary", False, str(e))


def test_reports_dashboard():
    """Test reports & analytics endpoints"""
    print("\n=== 15. REPORTS & ANALYTICS ===")
    try:
        r = httpx.get(f"{BASE_URL}/api/v1/reports/dashboard", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            log_result("Reports", "GET /reports/dashboard", True, "Dashboard loaded")
        else:
            log_result("Reports", "GET /reports/dashboard", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Reports", "GET /reports/dashboard", False, str(e))

    try:
        r = httpx.get(f"{BASE_URL}/api/v1/reports/operations", headers=get_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            log_result("Reports", "GET /reports/operations", True,
                       f"{data.get('total_operations', 0)} ops")
        else:
            log_result("Reports", "GET /reports/operations", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Reports", "GET /reports/operations", False, str(e))


def test_api_docs():
    """Test API documentation endpoints"""
    print("\n=== 16. API DOCUMENTATION ===")
    try:
        r = httpx.get(f"{BASE_URL}/docs", timeout=10)
        log_result("Docs", "GET /docs (Swagger UI)", r.status_code == 200,
                   f"Status: {r.status_code}")
    except Exception as e:
        log_result("Docs", "GET /docs (Swagger UI)", False, str(e))

    try:
        r = httpx.get(f"{BASE_URL}/openapi.json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            paths = len(data.get("paths", {}))
            log_result("Docs", "GET /openapi.json", True, f"{paths} endpoints")
        else:
            log_result("Docs", "GET /openapi.json", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("Docs", "GET /openapi.json", False, str(e))


# ============================================================================
# v2.6.0 NEW TESTS - Mobile/Crew Interface
# ============================================================================

def test_mobile_static_files():
    """Test mobile static file serving (v2.6.0)"""
    print("\n=== 17. MOBILE STATIC FILES (v2.6.0) ===")

    # Test mobile CSS
    try:
        r = httpx.get(f"{BASE_URL}/static/css/mobile.css", timeout=10)
        if r.status_code == 200:
            size = len(r.text)
            log_result("MobileStatic", "GET /static/css/mobile.css", True, f"{size} bytes")
        else:
            log_result("MobileStatic", "GET /static/css/mobile.css", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("MobileStatic", "GET /static/css/mobile.css", False, str(e))

    # Test mobile JavaScript
    try:
        r = httpx.get(f"{BASE_URL}/static/js/app.js", timeout=10)
        if r.status_code == 200:
            size = len(r.text)
            log_result("MobileStatic", "GET /static/js/app.js", True, f"{size} bytes")
        else:
            log_result("MobileStatic", "GET /static/js/app.js", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("MobileStatic", "GET /static/js/app.js", False, str(e))

    # Test service worker
    try:
        r = httpx.get(f"{BASE_URL}/static/js/sw.js", timeout=10)
        if r.status_code == 200:
            size = len(r.text)
            log_result("MobileStatic", "GET /static/js/sw.js", True, f"{size} bytes")
        else:
            log_result("MobileStatic", "GET /static/js/sw.js", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("MobileStatic", "GET /static/js/sw.js", False, str(e))

    # Test PWA manifest
    try:
        r = httpx.get(f"{BASE_URL}/static/manifest.json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            name = data.get("name", "Unknown")
            log_result("MobileStatic", "GET /static/manifest.json", True, f"App: {name}")
        else:
            log_result("MobileStatic", "GET /static/manifest.json", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("MobileStatic", "GET /static/manifest.json", False, str(e))


def test_mobile_login_page():
    """Test mobile login page (v2.6.0)"""
    print("\n=== 18. MOBILE LOGIN (v2.6.0) ===")

    # Test login page GET
    try:
        r = httpx.get(f"{BASE_URL}/m/login", timeout=10)
        if r.status_code == 200:
            has_form = "form" in r.text.lower() and "password" in r.text.lower()
            log_result("MobileLogin", "GET /m/login", has_form,
                       "Login form found" if has_form else "HTML returned but no form")
        else:
            log_result("MobileLogin", "GET /m/login", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("MobileLogin", "GET /m/login", False, str(e))

    # Test login POST with valid credentials - use a client to persist cookies
    global SESSION_COOKIE
    try:
        with httpx.Client(timeout=10, follow_redirects=False) as client:
            r = client.post(f"{BASE_URL}/m/login",
                           data={"username": TEST_USERNAME, "password": TEST_PASSWORD})
            # Should redirect to /m/tasks on success
            if r.status_code in [302, 303, 307]:
                # Get cookie from the response - cookie name is agtools_session
                SESSION_COOKIE = r.cookies.get("agtools_session")
                if not SESSION_COOKIE:
                    # Try from cookies jar
                    for cookie in r.cookies.jar:
                        if cookie.name == "agtools_session":
                            SESSION_COOKIE = cookie.value
                            break
                log_result("MobileLogin", "POST /m/login (valid)", True,
                           f"Redirect to {r.headers.get('location', 'unknown')}")
            elif r.status_code == 200:
                has_tasks = "task" in r.text.lower()
                SESSION_COOKIE = r.cookies.get("session")
                log_result("MobileLogin", "POST /m/login (valid)", has_tasks,
                           "Tasks page rendered" if has_tasks else "Login page (re-check)")
            else:
                log_result("MobileLogin", "POST /m/login (valid)", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("MobileLogin", "POST /m/login (valid)", False, str(e))

    # Test login POST with invalid credentials
    try:
        r = httpx.post(f"{BASE_URL}/m/login",
                       data={"username": "baduser", "password": "badpass"},
                       follow_redirects=False,
                       timeout=10)
        # Should return login page with error or 401
        if r.status_code == 200:
            has_error = "error" in r.text.lower() or "invalid" in r.text.lower()
            log_result("MobileLogin", "POST /m/login (invalid)", True,
                       "Error message shown" if has_error else "Stayed on login page")
        elif r.status_code == 401:
            log_result("MobileLogin", "POST /m/login (invalid)", True, "401 Unauthorized")
        else:
            log_result("MobileLogin", "POST /m/login (invalid)", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("MobileLogin", "POST /m/login (invalid)", False, str(e))


def get_mobile_cookies():
    """Get cookies for mobile session"""
    if SESSION_COOKIE:
        return {"agtools_session": SESSION_COOKIE}
    return {}


def test_mobile_task_list():
    """Test mobile task list (v2.6.0)"""
    print("\n=== 19. MOBILE TASK LIST (v2.6.0) ===")

    # Test task list without auth (should redirect to login)
    try:
        r = httpx.get(f"{BASE_URL}/m/tasks", follow_redirects=False, timeout=10)
        if r.status_code in [302, 303, 307]:
            location = r.headers.get("location", "")
            is_login = "login" in location.lower()
            log_result("MobileTaskList", "GET /m/tasks (no auth)", is_login,
                       f"Redirects to {location}")
        elif r.status_code == 401:
            log_result("MobileTaskList", "GET /m/tasks (no auth)", True, "401 Unauthorized")
        else:
            log_result("MobileTaskList", "GET /m/tasks (no auth)", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("MobileTaskList", "GET /m/tasks (no auth)", False, str(e))

    # Test task list with auth
    if SESSION_COOKIE:
        try:
            r = httpx.get(f"{BASE_URL}/m/tasks", cookies=get_mobile_cookies(), timeout=10)
            if r.status_code == 200:
                has_tasks_ui = "task" in r.text.lower()
                log_result("MobileTaskList", "GET /m/tasks (with auth)", has_tasks_ui,
                           "Task list page loaded" if has_tasks_ui else "Page returned")
            else:
                log_result("MobileTaskList", "GET /m/tasks (with auth)", False, f"Status: {r.status_code}")
        except Exception as e:
            log_result("MobileTaskList", "GET /m/tasks (with auth)", False, str(e))
    else:
        log_result("MobileTaskList", "GET /m/tasks (with auth)", False, "No session cookie")

    # Test task list with filters
    if SESSION_COOKIE:
        try:
            r = httpx.get(f"{BASE_URL}/m/tasks?status=pending&priority=high",
                         cookies=get_mobile_cookies(), timeout=10)
            if r.status_code == 200:
                log_result("MobileTaskList", "GET /m/tasks?status&priority", True, "Filtered list loaded")
            else:
                log_result("MobileTaskList", "GET /m/tasks?status&priority", False, f"Status: {r.status_code}")
        except Exception as e:
            log_result("MobileTaskList", "GET /m/tasks?status&priority", False, str(e))
    else:
        log_result("MobileTaskList", "GET /m/tasks?status&priority", False, "No session cookie")


def test_mobile_offline_page():
    """Test mobile offline page (v2.6.0)"""
    print("\n=== 20. MOBILE OFFLINE PAGE (v2.6.0) ===")

    try:
        r = httpx.get(f"{BASE_URL}/m/offline", timeout=10)
        if r.status_code == 200:
            has_offline_msg = "offline" in r.text.lower()
            log_result("MobileOffline", "GET /m/offline", has_offline_msg,
                       "Offline page with message" if has_offline_msg else "Page returned")
        else:
            log_result("MobileOffline", "GET /m/offline", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("MobileOffline", "GET /m/offline", False, str(e))


def test_mobile_templates():
    """Test that templates render without errors (v2.6.0)"""
    print("\n=== 21. MOBILE TEMPLATES (v2.6.0) ===")

    # Base template test - login page uses base.html
    try:
        r = httpx.get(f"{BASE_URL}/m/login", timeout=10)
        if r.status_code == 200:
            has_doctype = "<!doctype html>" in r.text.lower() or "<!DOCTYPE html>" in r.text
            has_viewport = "viewport" in r.text.lower()
            log_result("MobileTemplates", "base.html (via /m/login)",
                       has_doctype and has_viewport,
                       "Valid HTML with viewport meta")
        else:
            log_result("MobileTemplates", "base.html (via /m/login)", False, f"Status: {r.status_code}")
    except Exception as e:
        log_result("MobileTemplates", "base.html (via /m/login)", False, str(e))

    # Task list template
    if SESSION_COOKIE:
        try:
            r = httpx.get(f"{BASE_URL}/m/tasks", cookies=get_mobile_cookies(), timeout=10)
            if r.status_code == 200:
                has_summary = "to do" in r.text.lower() or "pending" in r.text.lower()
                log_result("MobileTemplates", "tasks/list.html", True,
                           "Task list template rendered")
            else:
                log_result("MobileTemplates", "tasks/list.html", False, f"Status: {r.status_code}")
        except Exception as e:
            log_result("MobileTemplates", "tasks/list.html", False, str(e))
    else:
        log_result("MobileTemplates", "tasks/list.html", False, "No session cookie")


def test_frontend_imports():
    """Test frontend module imports"""
    print("\n=== 22. FRONTEND IMPORTS ===")

    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    if frontend_path not in sys.path:
        sys.path.insert(0, frontend_path)

    screens = [
        "ui.screens.dashboard",
        "ui.screens.yield_response",
        "ui.screens.spray_timing",
        "ui.screens.cost_optimizer",
        "ui.screens.pricing",
        "ui.screens.pest_identification",
        "ui.screens.disease_identification",
        "ui.screens.settings",
        "ui.screens.login",
        "ui.screens.user_management",
        "ui.screens.crew_management",
        "ui.screens.task_management",
        "ui.screens.field_management",
        "ui.screens.operations_log",
        "ui.screens.equipment_management",
        "ui.screens.inventory_management",
        "ui.screens.maintenance_schedule",
        "ui.screens.reports_dashboard",
    ]

    for screen in screens:
        try:
            __import__(screen)
            log_result("Frontend", f"import {screen.split('.')[-1]}", True, "OK")
        except Exception as e:
            log_result("Frontend", f"import {screen.split('.')[-1]}", False, str(e)[:50])

    apis = [
        "api.client",
        "api.auth_api",
        "api.yield_response_api",
        "api.spray_api",
        "api.pricing_api",
        "api.cost_optimizer_api",
        "api.identification_api",
        "api.task_api",
        "api.field_api",
        "api.operations_api",
        "api.equipment_api",
        "api.inventory_api",
        "api.reports_api",
    ]

    for api in apis:
        try:
            __import__(api)
            log_result("Frontend", f"import {api.split('.')[-1]}", True, "OK")
        except Exception as e:
            log_result("Frontend", f"import {api.split('.')[-1]}", False, str(e)[:50])


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
        "version": "2.6.0",
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{passed/total*100:.1f}%",
        "results": RESULTS,
        "by_category": categories
    }


def main():
    print("=" * 60)
    print("AGTOOLS v2.6.0 COMPREHENSIVE SMOKE TESTS")
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
    test_equipment_management()
    test_inventory_management()
    test_reports_dashboard()
    test_api_docs()

    # v2.6.0 New Mobile Interface Tests
    test_mobile_static_files()
    test_mobile_login_page()
    test_mobile_task_list()
    test_mobile_offline_page()
    test_mobile_templates()

    # Frontend imports
    test_frontend_imports()

    # Generate report
    report = generate_report()

    # Save report
    report_path = os.path.join(os.path.dirname(__file__), "smoke_test_results_v26.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nResults saved to: {report_path}")

    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
