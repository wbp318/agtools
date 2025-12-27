#!/usr/bin/env python3
"""
AgTools v3.0 Full System Smoke Test
Tests all modules and routes without requiring a running server
"""

import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

RESULTS = []
START_TIME = datetime.now()


def log_result(category: str, test: str, passed: bool, details: str = ""):
    """Log a test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    RESULTS.append({
        "category": category,
        "test": test,
        "passed": passed,
        "details": details
    })
    detail_str = f" - {details}" if details else ""
    print(f"  {status}: {test}{detail_str}")


def test_main_app():
    """Test main FastAPI app loads with all routes"""
    print("\n" + "="*60)
    print("🌐 Testing Main Application")
    print("="*60)

    try:
        from main import app
        route_count = len(app.routes)
        log_result("Main App", "FastAPI app loads", True, f"{route_count} routes")

        # Count routes by category
        routes = [r.path for r in app.routes if hasattr(r, 'path')]

        categories = {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "crews": "/api/v1/crews",
            "tasks": "/api/v1/tasks",
            "fields": "/api/v1/fields",
            "operations": "/api/v1/operations",
            "equipment": "/api/v1/equipment",
            "maintenance": "/api/v1/maintenance",
            "inventory": "/api/v1/inventory",
            "reports": "/api/v1/reports",
            "costs": "/api/v1/costs",
            "quickbooks": "/api/v1/quickbooks",
            "profitability": "/api/v1/profitability",
            "ai": "/api/v1/ai",
            "optimize": "/api/v1/optimize",
            "pricing": "/api/v1/pricing",
            "spray-timing": "/api/v1/spray-timing",
            "yield-response": "/api/v1/yield-response",
            "identify": "/api/v1/identify",
            "recommend": "/api/v1/recommend",
            "mobile": "/m/",
        }

        for name, prefix in categories.items():
            count = len([r for r in routes if r.startswith(prefix)])
            if count > 0:
                log_result("Routes", f"{name} endpoints", True, f"{count} routes")

        return True
    except Exception as e:
        log_result("Main App", "FastAPI app loads", False, str(e))
        return False


def test_services():
    """Test all service modules import correctly"""
    print("\n" + "="*60)
    print("📦 Testing Service Imports")
    print("="*60)

    services = [
        ("auth_service", "AuthService"),
        ("user_service", "UserService"),
        ("task_service", "TaskService"),
        ("field_service", "FieldService"),
        ("field_operations_service", "FieldOperationsService"),
        ("equipment_service", "EquipmentService"),
        ("inventory_service", "InventoryService"),
        ("reporting_service", "ReportingService"),
        ("time_entry_service", "TimeEntryService"),
        ("photo_service", "PhotoService"),
        ("cost_tracking_service", "CostTrackingService"),
        ("quickbooks_import", "QuickBooksImportService"),
        ("profitability_service", "ProfitabilityService"),
        ("ai_image_service", "AIImageService"),
        ("crop_health_service", "CropHealthService"),
        ("yield_prediction_service", "YieldPredictionService"),
        ("expense_categorization_service", "ExpenseCategorizationService"),
        ("spray_ai_service", "SprayAIService"),
    ]

    passed = 0
    for module_name, class_name in services:
        try:
            module = __import__(f"services.{module_name}", fromlist=[class_name])
            cls = getattr(module, class_name, None)
            if cls:
                log_result("Services", f"{class_name}", True)
                passed += 1
            else:
                log_result("Services", f"{class_name}", False, "Class not found")
        except Exception as e:
            log_result("Services", f"{class_name}", False, str(e)[:50])

    return passed == len(services)


def test_database_schema():
    """Test database schema files exist and are valid"""
    print("\n" + "="*60)
    print("💾 Testing Database Schema")
    print("="*60)

    # Check schema file exists
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
    exists = os.path.exists(schema_path)
    log_result("Database", "schema.sql exists", exists)

    if exists:
        with open(schema_path, 'r') as f:
            schema = f.read()
        log_result("Database", "Schema readable", len(schema) > 0, f"{len(schema)} bytes")

        # Check for key table definitions
        tables_to_check = [
            ("crops", "CREATE TABLE crops"),
            ("pests", "CREATE TABLE pests"),
            ("diseases", "CREATE TABLE diseases"),
            ("fields", "CREATE TABLE fields"),
            ("products", "CREATE TABLE products"),
        ]

        for table_name, pattern in tables_to_check:
            found = pattern.lower() in schema.lower()
            log_result("Database", f"Table definition: {table_name}", found)

    # Check seed data
    seed_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'seed_data.py')
    exists = os.path.exists(seed_path)
    log_result("Database", "seed_data.py exists", exists)

    if exists:
        try:
            # Just check it imports
            import importlib.util
            spec = importlib.util.spec_from_file_location("seed_data", seed_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            pest_count = len(getattr(module, 'CORN_PESTS', [])) + len(getattr(module, 'SOYBEAN_PESTS', []))
            disease_count = len(getattr(module, 'CORN_DISEASES', [])) + len(getattr(module, 'SOYBEAN_DISEASES', []))
            log_result("Database", "Seed data loads", True, f"{pest_count} pests, {disease_count} diseases")
        except Exception as e:
            log_result("Database", "Seed data loads", False, str(e)[:50])

    # Check chemical database
    chem_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'chemical_database.py')
    exists = os.path.exists(chem_path)
    log_result("Database", "chemical_database.py exists", exists)

    return True


def test_ai_services():
    """Test AI service functionality"""
    print("\n" + "="*60)
    print("🤖 Testing AI/ML Services")
    print("="*60)

    # Test AI Image Service
    try:
        from services.ai_image_service import get_ai_image_service
        service = get_ai_image_service()
        log_result("AI", "AIImageService singleton", True)
        kb = getattr(service, 'knowledge_base', {})
        log_result("AI", "Knowledge base loaded", bool(kb), f"{len(kb)} crops")
    except Exception as e:
        log_result("AI", "AIImageService", False, str(e)[:50])

    # Test Crop Health Service
    try:
        from services.crop_health_service import get_crop_health_service
        service = get_crop_health_service()
        log_result("AI", "CropHealthService singleton", True)
        log_result("AI", "CropHealthService ready", service is not None)
    except Exception as e:
        log_result("AI", "CropHealthService", False, str(e)[:50])

    # Test Yield Prediction Service
    try:
        from services.yield_prediction_service import get_yield_prediction_service
        service = get_yield_prediction_service()
        log_result("AI", "YieldPredictionService singleton", True)
        log_result("AI", "YieldPredictionService ready", service is not None)
    except Exception as e:
        log_result("AI", "YieldPredictionService", False, str(e)[:50])

    # Test Expense Categorization Service
    try:
        from services.expense_categorization_service import get_expense_categorization_service
        service = get_expense_categorization_service()
        log_result("AI", "ExpenseCategorizationService singleton", True)
        log_result("AI", "ExpenseCategorizationService ready", service is not None)
    except Exception as e:
        log_result("AI", "ExpenseCategorizationService", False, str(e)[:50])

    # Test Spray AI Service
    try:
        from services.spray_ai_service import get_spray_ai_service
        service = get_spray_ai_service()
        log_result("AI", "SprayAIService singleton", True)
        log_result("AI", "SprayAIService ready", service is not None)
    except Exception as e:
        log_result("AI", "SprayAIService", False, str(e)[:50])


def test_mobile_interface():
    """Test mobile interface modules"""
    print("\n" + "="*60)
    print("📱 Testing Mobile Interface")
    print("="*60)

    try:
        from mobile import routes
        log_result("Mobile", "Mobile routes module", True)
    except Exception as e:
        log_result("Mobile", "Mobile routes module", False, str(e)[:50])

    try:
        from mobile import auth
        log_result("Mobile", "Mobile auth module", True)
    except Exception as e:
        log_result("Mobile", "Mobile auth module", False, str(e)[:50])

    # Check templates exist
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'backend', 'templates')
    templates = ['base.html', 'login.html', 'offline.html']
    for t in templates:
        path = os.path.join(template_dir, t)
        exists = os.path.exists(path)
        log_result("Mobile", f"Template: {t}", exists)


def generate_report():
    """Generate test report"""
    duration = (datetime.now() - START_TIME).total_seconds()

    passed = sum(1 for r in RESULTS if r['passed'])
    failed = sum(1 for r in RESULTS if not r['passed'])
    total = len(RESULTS)
    pass_rate = (passed / total * 100) if total > 0 else 0

    # Group by category
    categories = {}
    for r in RESULTS:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'passed': 0, 'failed': 0}
        if r['passed']:
            categories[cat]['passed'] += 1
        else:
            categories[cat]['failed'] += 1

    print("\n" + "="*60)
    print("📋 FULL SMOKE TEST REPORT - AgTools v3.0")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration:.2f} seconds")
    print()
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print()
    print("By Category:")
    for cat, counts in sorted(categories.items()):
        total_cat = counts['passed'] + counts['failed']
        print(f"  {cat}: {counts['passed']}/{total_cat} passed")

    # Save report
    report_path = os.path.join(os.path.dirname(__file__), 'SMOKE_TEST_RESULTS_FULL.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# Full Smoke Test Results - AgTools v3.0\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Duration:** {duration:.2f} seconds\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Total Tests | {total} |\n")
        f.write(f"| Passed | {passed} |\n")
        f.write(f"| Failed | {failed} |\n")
        f.write(f"| **Pass Rate** | **{pass_rate:.1f}%** |\n\n")

        f.write(f"## Results by Category\n\n")
        for cat, counts in sorted(categories.items()):
            total_cat = counts['passed'] + counts['failed']
            f.write(f"### {cat} ({counts['passed']}/{total_cat} passed)\n\n")
            f.write(f"| Test | Status | Details |\n")
            f.write(f"|------|--------|--------|\n")
            for r in RESULTS:
                if r['category'] == cat:
                    status = "✅ Pass" if r['passed'] else "❌ Fail"
                    details = r.get('details', '-') or '-'
                    f.write(f"| {r['test']} | {status} | {details} |\n")
            f.write(f"\n")

    print(f"\n📄 Report saved to: {report_path}")

    return failed == 0


if __name__ == "__main__":
    print("="*60)
    print("🧪 FULL SMOKE TEST - AgTools v3.0")
    print("="*60)

    test_main_app()
    test_services()
    test_database_schema()
    test_ai_services()
    test_mobile_interface()

    success = generate_report()
    sys.exit(0 if success else 1)
