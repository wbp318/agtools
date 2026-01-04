"""
Farm Operations Comprehensive Workflow Test Suite
==================================================

Tests all Farm Operations features end-to-end (non-GenFin areas):
- Field Management (CRUD)
- Equipment Management (CRUD + maintenance)
- Farm Inventory (CRUD + transactions)
- Task Management (CRUD + status)
- Crew Management (CRUD + members)
- Field Operations
- Climate/GDD Tracking
- Sustainability Metrics
- Profitability Analysis
- Farm Reports

Run with: python tests/test_farm_workflow.py

NOTE: Requires AGTOOLS_DEV_MODE=1 or the backend must be running with dev mode enabled.
"""

import os
import requests
import json
import sys
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Ensure dev mode is enabled for testing
os.environ["AGTOOLS_DEV_MODE"] = "1"

API_BASE = "http://127.0.0.1:8000/api/v1"

# Test results tracking
results = {"passed": 0, "failed": 0, "errors": []}


def log_result(test_name: str, passed: bool, details: str = ""):
    """Log test result."""
    status = "\u2705 PASS" if passed else "\u274c FAIL"
    print(f"  {status}: {test_name}")
    if not passed and details:
        print(f"         \u2514\u2500 {details[:100]}")
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

RAND_SUFFIX = random.randint(1000, 9999)

TEST_FIELD = {
    "name": f"Test Field {RAND_SUFFIX}",
    "farm_name": "Test Farm",
    "acreage": 160.5,
    "current_crop": "corn",
    "soil_type": "loam",
    "irrigation_type": "center_pivot",
    "latitude": 42.0,
    "longitude": -93.5,
    "notes": "Workflow test field"
}

TEST_EQUIPMENT = {
    "name": f"Test Tractor {RAND_SUFFIX}",
    "equipment_type": "tractor",
    "make": "John Deere",
    "model": "8R 410",
    "year": 2023,
    "serial_number": f"TEST{RAND_SUFFIX}",
    "purchase_cost": 350000.00,
    "status": "available",
    "current_hours": 500.0,
    "notes": "Workflow test equipment"
}

TEST_MAINTENANCE = {
    "maintenance_type": "oil_change",
    "description": "Oil change and filter replacement",
    "cost": 450.00,
    "service_date": datetime.now().strftime("%Y-%m-%d"),
    "next_service_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
}

TEST_INVENTORY_ITEM = {
    "name": f"Test Herbicide {RAND_SUFFIX}",
    "category": "herbicide",
    "quantity": 50.0,
    "unit": "gallons",
    "unit_cost": 125.00,
    "min_quantity": 10.0,
    "storage_location": "Main Barn",
    "notes": "Workflow test inventory"
}

TEST_TASK = {
    "title": f"Test Task {RAND_SUFFIX}",
    "description": "Workflow test task description",
    "priority": "high",
    "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
    "estimated_hours": 4.0,
    "notes": "Workflow test task"
}

TEST_CREW = {
    "name": f"Test Crew {RAND_SUFFIX}",
    "description": "Workflow test crew"
}

TEST_OPERATION = {
    "operation_type": "planting",
    "operation_date": datetime.now().strftime("%Y-%m-%d"),
    "notes": "Workflow test operation"
}

TEST_GDD = {
    "record_date": datetime.now().strftime("%Y-%m-%d"),
    "high_temp_f": 85.0,
    "low_temp_f": 62.0
}

TEST_PRECIPITATION = {
    "record_date": datetime.now().strftime("%Y-%m-%d"),
    "amount_inches": 0.75,
    "precip_type": "rain"
}

TEST_SUSTAINABILITY_INPUT = {
    "application_date": datetime.now().strftime("%Y-%m-%d"),
    "category": "fertilizer_nitrogen",
    "product_name": "Test Fertilizer",
    "quantity": 200.0,
    "unit": "lbs",
    "cost": 150.00,
    "notes": "Workflow test input"
}

TEST_CARBON = {
    "activity_date": datetime.now().strftime("%Y-%m-%d"),
    "source": "fuel_combustion",
    "carbon_kg": 100.0,
    "description": "Workflow test carbon"
}

# Store created IDs for cleanup and cross-references
created_ids = {
    "field_id": None,
    "equipment_id": None,
    "maintenance_id": None,
    "inventory_id": None,
    "task_id": None,
    "crew_id": None,
    "operation_id": None,
}


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_api_health():
    """Test API is running."""
    print("\n\U0001F4E1 API Health Check")
    print("-" * 40)

    # Use fields/summary for health check as it doesn't require complex row conversion
    ok, data = api_get("/fields/summary")
    log_result("API responding", ok, str(data)[:100] if not ok else "")
    return ok


# -----------------------------------------------------------------------------
# FIELD MANAGEMENT
# -----------------------------------------------------------------------------

def test_fields():
    """Test Field CRUD operations."""
    print("\n\U0001F33E Field Management")
    print("-" * 40)

    # CREATE
    ok, data = api_post("/fields", TEST_FIELD)
    log_result("Create field", ok and data.get("id"), str(data)[:100])
    if ok and data.get("id"):
        created_ids["field_id"] = data["id"]

    # READ (list)
    ok, data = api_get("/fields")
    log_result("List fields", ok and "fields" in data, str(data)[:100])

    # READ (single)
    if created_ids["field_id"]:
        ok, data = api_get(f"/fields/{created_ids['field_id']}")
        log_result("Get field by ID", ok and data.get("id"), str(data)[:100])

    # UPDATE
    if created_ids["field_id"]:
        update_data = {"notes": "Updated workflow test notes"}
        ok, data = api_put(f"/fields/{created_ids['field_id']}", update_data)
        log_result("Update field", ok, str(data)[:100])

    # SUMMARY
    ok, data = api_get("/fields/summary")
    log_result("Field summary", ok, str(data)[:100])

    # FARMS list
    ok, data = api_get("/fields/farms")
    log_result("List farms", ok, str(data)[:100])


# -----------------------------------------------------------------------------
# EQUIPMENT MANAGEMENT
# -----------------------------------------------------------------------------

def test_equipment():
    """Test Equipment CRUD operations."""
    print("\n\U0001F69C Equipment Management")
    print("-" * 40)

    # CREATE
    ok, data = api_post("/equipment", TEST_EQUIPMENT)
    log_result("Create equipment", ok and data.get("id"), str(data)[:100])
    if ok and data.get("id"):
        created_ids["equipment_id"] = data["id"]

    # READ (list)
    ok, data = api_get("/equipment")
    log_result("List equipment", ok and isinstance(data, list), str(data)[:100])

    # READ (single)
    if created_ids["equipment_id"]:
        ok, data = api_get(f"/equipment/{created_ids['equipment_id']}")
        log_result("Get equipment by ID", ok and data.get("id"), str(data)[:100])

    # UPDATE
    if created_ids["equipment_id"]:
        update_data = {"notes": "Updated workflow test notes"}
        ok, data = api_put(f"/equipment/{created_ids['equipment_id']}", update_data)
        log_result("Update equipment", ok, str(data)[:100])

    # SUMMARY
    ok, data = api_get("/equipment/summary")
    log_result("Equipment summary", ok, str(data)[:100])

    # TYPES
    ok, data = api_get("/equipment/types")
    log_result("Equipment types", ok, str(data)[:100])

    # STATUSES
    ok, data = api_get("/equipment/statuses")
    log_result("Equipment statuses", ok, str(data)[:100])

    # UPDATE HOURS
    if created_ids["equipment_id"]:
        # Use query parameter for hours update
        try:
            r = requests.post(f"{API_BASE}/equipment/{created_ids['equipment_id']}/hours?new_hours=510.5", timeout=10)
            ok = r.status_code == 200
            data = r.json() if r.status_code == 200 else r.text
        except Exception as e:
            ok, data = False, str(e)
        log_result("Update equipment hours", ok, str(data)[:100])


def test_maintenance():
    """Test Maintenance operations."""
    print("\n\U0001F527 Maintenance Management")
    print("-" * 40)

    if not created_ids["equipment_id"]:
        log_result("Create maintenance", False, "No equipment ID - run equipment test first")
        return

    maintenance_data = {**TEST_MAINTENANCE, "equipment_id": created_ids["equipment_id"]}

    # CREATE
    ok, data = api_post("/maintenance", maintenance_data)
    log_result("Create maintenance record", ok and data.get("id"), str(data)[:100])
    if ok and data.get("id"):
        created_ids["maintenance_id"] = data["id"]

    # READ (list)
    ok, data = api_get("/maintenance")
    log_result("List maintenance", ok and isinstance(data, list), str(data)[:100])

    # ALERTS
    ok, data = api_get("/maintenance/alerts")
    log_result("Maintenance alerts", ok, str(data)[:100])

    # TYPES
    ok, data = api_get("/maintenance/types")
    log_result("Maintenance types", ok, str(data)[:100])

    # EQUIPMENT MAINTENANCE HISTORY
    if created_ids["equipment_id"]:
        ok, data = api_get(f"/equipment/{created_ids['equipment_id']}/maintenance")
        log_result("Equipment maintenance history", ok, str(data)[:100])


# -----------------------------------------------------------------------------
# FARM INVENTORY
# -----------------------------------------------------------------------------

def test_farm_inventory():
    """Test Farm Inventory CRUD operations."""
    print("\n\U0001F4E6 Farm Inventory")
    print("-" * 40)

    # CREATE
    ok, data = api_post("/inventory", TEST_INVENTORY_ITEM)
    log_result("Create inventory item", ok and data.get("id"), str(data)[:100])
    if ok and data.get("id"):
        created_ids["inventory_id"] = data["id"]

    # READ (list)
    ok, data = api_get("/inventory")
    log_result("List inventory", ok and isinstance(data, list), str(data)[:100])

    # READ (single)
    if created_ids["inventory_id"]:
        ok, data = api_get(f"/inventory/{created_ids['inventory_id']}")
        log_result("Get inventory item by ID", ok and data.get("id"), str(data)[:100])

    # UPDATE
    if created_ids["inventory_id"]:
        update_data = {"notes": "Updated workflow test notes"}
        ok, data = api_put(f"/inventory/{created_ids['inventory_id']}", update_data)
        log_result("Update inventory item", ok, str(data)[:100])

    # SUMMARY
    ok, data = api_get("/inventory/summary")
    log_result("Inventory summary", ok, str(data)[:100])

    # CATEGORIES
    ok, data = api_get("/inventory/categories")
    log_result("Inventory categories", ok, str(data)[:100])

    # LOCATIONS
    ok, data = api_get("/inventory/locations")
    log_result("Inventory locations", ok, str(data)[:100])

    # ALERTS
    ok, data = api_get("/inventory/alerts")
    log_result("Inventory alerts", ok, str(data)[:100])

    # TRANSACTION
    if created_ids["inventory_id"]:
        tx_data = {
            "inventory_item_id": created_ids["inventory_id"],
            "transaction_type": "adjustment",
            "quantity": -5.0,
            "notes": "Workflow test transaction"
        }
        ok, data = api_post("/inventory/transaction", tx_data)
        log_result("Create inventory transaction", ok, str(data)[:100])

        # TRANSACTION HISTORY
        ok, data = api_get(f"/inventory/{created_ids['inventory_id']}/transactions")
        log_result("Get transaction history", ok, str(data)[:100])


# -----------------------------------------------------------------------------
# TASK MANAGEMENT
# -----------------------------------------------------------------------------

def test_tasks():
    """Test Task CRUD operations."""
    print("\n\U0001F4CB Task Management")
    print("-" * 40)

    # CREATE
    ok, data = api_post("/tasks", TEST_TASK)
    log_result("Create task", ok and data.get("id"), str(data)[:100])
    if ok and data.get("id"):
        created_ids["task_id"] = data["id"]

    # READ (list)
    ok, data = api_get("/tasks")
    log_result("List tasks", ok and "tasks" in data, str(data)[:100])

    # READ (single)
    if created_ids["task_id"]:
        ok, data = api_get(f"/tasks/{created_ids['task_id']}")
        log_result("Get task by ID", ok and data.get("id"), str(data)[:100])

    # UPDATE
    if created_ids["task_id"]:
        update_data = {"notes": "Updated workflow test notes"}
        ok, data = api_put(f"/tasks/{created_ids['task_id']}", update_data)
        log_result("Update task", ok, str(data)[:100])

    # STATUS CHANGE
    if created_ids["task_id"]:
        status_data = {"status": "in_progress"}
        ok, data = api_post(f"/tasks/{created_ids['task_id']}/status", status_data)
        log_result("Change task status", ok, str(data)[:100])


# -----------------------------------------------------------------------------
# CREW MANAGEMENT
# -----------------------------------------------------------------------------

def test_crews():
    """Test Crew CRUD operations."""
    print("\n\U0001F465 Crew Management")
    print("-" * 40)

    # CREATE
    ok, data = api_post("/crews", TEST_CREW)
    log_result("Create crew", ok and data.get("id"), str(data)[:100])
    if ok and data.get("id"):
        created_ids["crew_id"] = data["id"]

    # READ (list)
    ok, data = api_get("/crews")
    log_result("List crews", ok and isinstance(data, list), str(data)[:100])

    # READ (single)
    if created_ids["crew_id"]:
        ok, data = api_get(f"/crews/{created_ids['crew_id']}")
        log_result("Get crew by ID", ok and data.get("id"), str(data)[:100])

    # UPDATE
    if created_ids["crew_id"]:
        update_data = {"description": "Updated workflow test description"}
        ok, data = api_put(f"/crews/{created_ids['crew_id']}", update_data)
        log_result("Update crew", ok, str(data)[:100])

    # MEMBERS list
    if created_ids["crew_id"]:
        ok, data = api_get(f"/crews/{created_ids['crew_id']}/members")
        log_result("List crew members", ok, str(data)[:100])


# -----------------------------------------------------------------------------
# FIELD OPERATIONS
# -----------------------------------------------------------------------------

def test_operations():
    """Test Field Operations."""
    print("\n\U0001F3A1 Field Operations")
    print("-" * 40)

    if not created_ids["field_id"]:
        log_result("Create operation", False, "No field ID - run field test first")
        return

    operation_data = {**TEST_OPERATION, "field_id": created_ids["field_id"]}

    # CREATE
    ok, data = api_post("/operations", operation_data)
    log_result("Create operation", ok and data.get("id"), str(data)[:100])
    if ok and data.get("id"):
        created_ids["operation_id"] = data["id"]

    # READ (list)
    ok, data = api_get("/operations")
    log_result("List operations", ok and "operations" in data, str(data)[:100])

    # READ (single)
    if created_ids["operation_id"]:
        ok, data = api_get(f"/operations/{created_ids['operation_id']}")
        log_result("Get operation by ID", ok and data.get("id"), str(data)[:100])

    # SUMMARY
    ok, data = api_get("/operations/summary")
    log_result("Operations summary", ok, str(data)[:100])

    # FIELD OPERATION HISTORY
    if created_ids["field_id"]:
        ok, data = api_get(f"/fields/{created_ids['field_id']}/operations")
        log_result("Field operation history", ok, str(data)[:100])


# -----------------------------------------------------------------------------
# CLIMATE / GDD
# -----------------------------------------------------------------------------

def test_climate():
    """Test Climate/GDD operations."""
    print("\n\u2600\ufe0f Climate & GDD Tracking")
    print("-" * 40)

    if not created_ids["field_id"]:
        log_result("Create GDD record", False, "No field ID - run field test first")
        return

    field_id = created_ids["field_id"]
    year = datetime.now().year

    # CREATE GDD record
    gdd_data = {**TEST_GDD, "field_id": field_id}
    ok, data = api_post("/climate/gdd", gdd_data)
    log_result("Create GDD record", ok, str(data)[:100])

    # LIST GDD
    ok, data = api_get(f"/climate/gdd?field_id={field_id}")
    log_result("List GDD records", ok, str(data)[:100])

    # GDD ACCUMULATED
    planting_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    ok, data = api_get(f"/climate/gdd/accumulated?field_id={field_id}&crop_type=corn&planting_date={planting_date}")
    log_result("GDD accumulated", ok, str(data)[:100])

    # GDD SUMMARY
    ok, data = api_get(f"/climate/gdd/summary?field_id={field_id}&crop_type=corn&planting_date={planting_date}")
    log_result("GDD summary", ok, str(data)[:100])

    # GDD STAGES
    ok, data = api_get("/climate/gdd/stages?crop=corn")
    log_result("GDD growth stages", ok, str(data)[:100])

    # BASE TEMPS
    ok, data = api_get("/climate/gdd/base-temps")
    log_result("GDD base temperatures", ok, str(data)[:100])

    # CREATE PRECIPITATION
    precip_data = {**TEST_PRECIPITATION, "field_id": field_id}
    ok, data = api_post("/climate/precipitation", precip_data)
    log_result("Create precipitation record", ok, str(data)[:100])

    # LIST PRECIPITATION
    ok, data = api_get("/climate/precipitation")
    log_result("List precipitation", ok, str(data)[:100])

    # PRECIPITATION SUMMARY
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    ok, data = api_get(f"/climate/precipitation/summary?start_date={start_date}&end_date={end_date}")
    log_result("Precipitation summary", ok, str(data)[:100])

    # PRECIPITATION TYPES
    ok, data = api_get("/climate/precipitation/types")
    log_result("Precipitation types", ok, str(data)[:100])

    # CLIMATE SUMMARY
    ok, data = api_get(f"/climate/summary?year={year}")
    log_result("Climate summary", ok, str(data)[:100])


# -----------------------------------------------------------------------------
# SUSTAINABILITY
# -----------------------------------------------------------------------------

def test_sustainability():
    """Test Sustainability operations."""
    print("\n\U0001F331 Sustainability Metrics")
    print("-" * 40)

    if not created_ids["field_id"]:
        log_result("Create input usage", False, "No field ID - run field test first")
        return

    field_id = created_ids["field_id"]
    year = datetime.now().year

    # CREATE INPUT USAGE
    input_data = {**TEST_SUSTAINABILITY_INPUT, "field_id": field_id}
    ok, data = api_post("/sustainability/inputs", input_data)
    log_result("Create input usage", ok, str(data)[:100])

    # LIST INPUTS
    ok, data = api_get("/sustainability/inputs")
    log_result("List input usage", ok, str(data)[:100])

    # INPUT SUMMARY
    ok, data = api_get(f"/sustainability/inputs/summary?year={year}")
    log_result("Input usage summary", ok, str(data)[:100])

    # CREATE CARBON ENTRY
    carbon_data = {**TEST_CARBON, "field_id": field_id}
    ok, data = api_post("/sustainability/carbon", carbon_data)
    log_result("Create carbon entry", ok, str(data)[:100])

    # CARBON SUMMARY
    ok, data = api_get(f"/sustainability/carbon/summary?year={year}")
    log_result("Carbon summary", ok, str(data)[:100])

    # WATER USAGE
    water_data = {
        "usage_date": datetime.now().strftime("%Y-%m-%d"),
        "gallons": 1000.0,
        "source": "well",
        "field_id": field_id
    }
    ok, data = api_post("/sustainability/water", water_data)
    log_result("Create water usage", ok, str(data)[:100])

    # WATER SUMMARY
    ok, data = api_get(f"/sustainability/water/summary?year={year}")
    log_result("Water summary", ok, str(data)[:100])

    # PRACTICES
    practice_data = {
        "practice": "cover_crops",
        "year": datetime.now().year,
        "acres_implemented": 100.0,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "details": "Workflow test practice",
        "field_id": field_id
    }
    ok, data = api_post("/sustainability/practices", practice_data)
    log_result("Create sustainability practice", ok, str(data)[:100])

    # LIST PRACTICES
    ok, data = api_get("/sustainability/practices")
    log_result("List practices", ok, str(data)[:100])

    # PRACTICE TYPES
    ok, data = api_get("/sustainability/practices/types")
    log_result("Practice types", ok, str(data)[:100])

    # SCORECARD
    ok, data = api_get(f"/sustainability/scorecard?year={year}")
    log_result("Sustainability scorecard", ok, str(data)[:100])

    # SCORES HISTORY
    ok, data = api_get("/sustainability/scores/history")
    log_result("Scores history", ok, str(data)[:100])

    # FULL REPORT
    ok, data = api_get(f"/sustainability/report?year={year}")
    log_result("Sustainability report", ok, str(data)[:100])

    # CARBON FACTORS
    ok, data = api_get("/sustainability/carbon-factors")
    log_result("Carbon factors", ok, str(data)[:100])

    # INPUT CATEGORIES
    ok, data = api_get("/sustainability/input-categories")
    log_result("Input categories", ok, str(data)[:100])

    # CARBON SOURCES
    ok, data = api_get("/sustainability/carbon-sources")
    log_result("Carbon sources", ok, str(data)[:100])


# -----------------------------------------------------------------------------
# PROFITABILITY
# -----------------------------------------------------------------------------

def test_profitability():
    """Test Profitability Analysis operations."""
    print("\n\U0001F4B0 Profitability Analysis")
    print("-" * 40)

    crop_year = datetime.now().year

    # BREAK-EVEN
    breakeven_data = {
        "crop": "corn",
        "acres": 160,
        "total_costs": 800,
        "expected_yield": 200,
        "price_per_bushel": 5.50
    }
    ok, data = api_post("/profitability/break-even", breakeven_data)
    log_result("Break-even analysis", ok, str(data)[:100])

    # INPUT ROI
    roi_data = {
        "crop": "corn",
        "acres": 160,
        "expected_yield": 200,
        "grain_price": 5.50
    }
    ok, data = api_post("/profitability/input-roi", roi_data)
    log_result("Input ROI analysis", ok, str(data)[:100])

    # SCENARIOS
    scenario_data = {
        "crop": "corn",
        "acres": 160,
        "base_costs": 750,
        "base_yield": 190,
        "base_price": 5.25,
        "scenarios": [
            {"name": "High Yield", "yield_change": 20, "cost_change": 50},
            {"name": "Low Price", "price_change": -0.75}
        ]
    }
    ok, data = api_post("/profitability/scenarios", scenario_data)
    log_result("Scenario analysis", ok, str(data)[:100])

    # BUDGET TRACKER
    budget_data = {
        "crop_year": crop_year,
        "crop": "corn",
        "acres": 160,
        "target_cost_per_acre": 800
    }
    ok, data = api_post("/profitability/budget", budget_data)
    log_result("Budget tracker", ok, str(data)[:100])

    # SUMMARY BY CROP
    ok, data = api_get(f"/profitability/summary/corn?acres=160")
    log_result("Profitability summary (corn)", ok, str(data)[:100])

    # CROPS LIST
    ok, data = api_get("/profitability/crops")
    log_result("Profitability crops list", ok, str(data)[:100])

    # INPUT CATEGORIES
    ok, data = api_get("/profitability/input-categories")
    log_result("Profitability input categories", ok, str(data)[:100])


# -----------------------------------------------------------------------------
# FARM REPORTS
# -----------------------------------------------------------------------------

def test_farm_reports():
    """Test Farm Reports operations."""
    print("\n\U0001F4CA Farm Reports")
    print("-" * 40)

    # OPERATIONS REPORT
    ok, data = api_get("/reports/operations")
    log_result("Operations report", ok, str(data)[:100])

    # FINANCIAL REPORT
    ok, data = api_get("/reports/financial")
    log_result("Financial report", ok, str(data)[:100])

    # EQUIPMENT REPORT
    ok, data = api_get("/reports/equipment")
    log_result("Equipment report", ok, str(data)[:100])

    # INVENTORY REPORT
    ok, data = api_get("/reports/inventory")
    log_result("Inventory report", ok, str(data)[:100])

    # FIELD PERFORMANCE REPORT
    ok, data = api_get("/reports/fields")
    log_result("Field performance report", ok, str(data)[:100])

    # DASHBOARD SUMMARY
    ok, data = api_get("/reports/dashboard")
    log_result("Dashboard summary", ok, str(data)[:100])


# -----------------------------------------------------------------------------
# COST TRACKING
# -----------------------------------------------------------------------------

def test_cost_tracking():
    """Test Cost Tracking operations."""
    print("\n\U0001F4B5 Cost Tracking")
    print("-" * 40)

    crop_year = datetime.now().year

    # CREATE EXPENSE
    expense_data = {
        "expense_date": datetime.now().strftime("%Y-%m-%d"),
        "description": "Workflow test expense",
        "amount": 500.00,
        "category": "repairs",
        "vendor": "Test Vendor",
        "tax_year": crop_year
    }
    ok, data = api_post("/costs/expenses", expense_data)
    expense_id = data.get("id") if ok and isinstance(data, dict) else None
    log_result("Create expense", ok, str(data)[:100])

    # LIST EXPENSES
    ok, data = api_get("/costs/expenses")
    log_result("List expenses", ok, str(data)[:100])

    # GET EXPENSE
    if expense_id:
        ok, data = api_get(f"/costs/expenses/{expense_id}")
        log_result("Get expense by ID", ok, str(data)[:100])

    # REVIEW EXPENSES
    ok, data = api_get("/costs/review")
    log_result("Review pending expenses", ok, str(data)[:100])

    # UNALLOCATED EXPENSES
    ok, data = api_get("/costs/unallocated")
    log_result("Unallocated expenses", ok, str(data)[:100])

    # COST PER ACRE REPORT
    ok, data = api_get(f"/costs/reports/per-acre?crop_year={crop_year}")
    log_result("Cost per acre report", ok, str(data)[:100])

    # COST BY CATEGORY
    ok, data = api_get(f"/costs/reports/by-category?crop_year={crop_year}")
    log_result("Cost by category report", ok, str(data)[:100])

    # COST BY CROP
    ok, data = api_get(f"/costs/reports/by-crop?crop_year={crop_year}")
    log_result("Cost by crop report", ok, str(data)[:100])

    # CATEGORIES
    ok, data = api_get("/costs/categories")
    log_result("Cost categories", ok, str(data)[:100])

    # MAPPINGS
    ok, data = api_get("/costs/mappings")
    log_result("Saved cost mappings", ok, str(data)[:100])

    # IMPORT BATCHES
    ok, data = api_get("/costs/imports")
    log_result("Import batches", ok, str(data)[:100])


# -----------------------------------------------------------------------------
# CLEANUP
# -----------------------------------------------------------------------------

def test_cleanup():
    """Optional cleanup of test data."""
    print("\n\U0001F9F9 Cleanup (Optional)")
    print("-" * 40)

    # Don't delete - keep for future testing
    log_result("Test data preserved", True, "Field, Equipment, Inventory, Task, Crew kept for UI testing")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("\U0001F9EA FARM OPERATIONS COMPREHENSIVE WORKFLOW TEST")
    print("=" * 60)
    print(f"API: {API_BASE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run tests
    if not test_api_health():
        print("\n\u274c API not responding. Start the backend first!")
        print("   Run: python backend/main.py")
        sys.exit(1)

    # Core Farm Operations
    test_fields()
    test_equipment()
    test_maintenance()
    test_farm_inventory()
    test_tasks()
    test_crews()
    test_operations()

    # Analytics & Tracking
    test_climate()
    test_sustainability()
    test_profitability()
    test_cost_tracking()

    # Reports
    test_farm_reports()

    # Cleanup
    test_cleanup()

    # Summary
    print("\n" + "=" * 60)
    print("\U0001F4CA TEST SUMMARY")
    print("=" * 60)
    total = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0

    print(f"\u2705 Passed: {results['passed']}")
    print(f"\u274c Failed: {results['failed']}")
    print(f"\U0001F4C8 Pass Rate: {pass_rate:.1f}%")

    if results["errors"]:
        print("\n\u274c Failed Tests:")
        for err in results["errors"][:10]:  # Show first 10
            print(f"   \u2022 {err[:80]}")

    print("\n" + "=" * 60)

    # Exit code
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
