#!/usr/bin/env python3
"""
AgTools v3.1 Full System Smoke Test
Tests all modules and routes without requiring a running server
Includes v3.1 features: PDF Reports, Email Notifications, Docker
"""

import os
import sys
import io
from datetime import datetime

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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


def test_pdf_service():
    """Test PDF report generation service"""
    print("\n" + "="*60)
    print("📄 Testing PDF Report Service")
    print("="*60)

    try:
        from services.pdf_report_service import get_pdf_report_service, ReportConfig
        log_result("PDF", "PDFReportService import", True)
    except ImportError as e:
        log_result("PDF", "PDFReportService import", False, str(e)[:50])
        return

    try:
        service = get_pdf_report_service()
        log_result("PDF", "PDFReportService singleton", True)
    except Exception as e:
        log_result("PDF", "PDFReportService singleton", False, str(e)[:50])
        return

    # Test scouting report generation
    try:
        pdf_bytes = service.generate_scouting_report(
            field_name="Test Field",
            crop="corn",
            growth_stage="V6",
            observations=[{"type": "Pest", "finding": "Aphids", "severity": "Low", "location": "North"}],
            recommendations=["Monitor weekly", "No treatment needed"]
        )
        log_result("PDF", "Generate scouting report", len(pdf_bytes) > 0, f"{len(pdf_bytes)} bytes")
    except Exception as e:
        log_result("PDF", "Generate scouting report", False, str(e)[:50])

    # Test spray recommendation report
    try:
        pdf_bytes = service.generate_spray_recommendation(
            field_name="Test Field",
            crop="soybean",
            target_pest="Soybean Aphid",
            products=[{"name": "Test Product", "rate": "8 oz/acre", "cost_per_acre": 12.50, "moa_group": "4A", "phi_days": 21}],
            economics={"treatment_cost": 18.50, "yield_loss_bu": 5, "saved_value": 45, "net_benefit": 26.50, "roi_percent": 143}
        )
        log_result("PDF", "Generate spray report", len(pdf_bytes) > 0, f"{len(pdf_bytes)} bytes")
    except Exception as e:
        log_result("PDF", "Generate spray report", False, str(e)[:50])

    # Test cost per acre report
    try:
        pdf_bytes = service.generate_cost_per_acre_report(
            crop_year=2025,
            fields=[{"name": "Field 1", "acres": 160, "crop": "corn", "total_cost": 45000, "cost_per_acre": 281.25}],
            summary={"total_fields": 1, "total_acres": 160, "total_cost": 45000, "avg_cost_per_acre": 281.25}
        )
        log_result("PDF", "Generate cost report", len(pdf_bytes) > 0, f"{len(pdf_bytes)} bytes")
    except Exception as e:
        log_result("PDF", "Generate cost report", False, str(e)[:50])


def test_email_service():
    """Test email notification service"""
    print("\n" + "="*60)
    print("📧 Testing Email Notification Service")
    print("="*60)

    try:
        from services.email_notification_service import (
            get_email_notification_service, NotificationType, NotificationPriority
        )
        log_result("Email", "EmailNotificationService import", True)
    except ImportError as e:
        log_result("Email", "EmailNotificationService import", False, str(e)[:50])
        return

    try:
        service = get_email_notification_service()
        log_result("Email", "EmailNotificationService singleton", True)
    except Exception as e:
        log_result("Email", "EmailNotificationService singleton", False, str(e)[:50])
        return

    # Test notification types
    types = service.get_notification_types()
    log_result("Email", "Notification types loaded", len(types) > 0, f"{len(types)} types")

    # Test notification creation (without sending)
    try:
        notification = service.create_notification(
            notification_type=NotificationType.MAINTENANCE_DUE,
            recipients=["test@example.com"],
            data={
                "equipment_name": "John Deere 8R",
                "maintenance_type": "Oil Change",
                "due_date": "2025-01-15",
                "current_hours": 450
            }
        )
        log_result("Email", "Create notification", notification is not None)
        log_result("Email", "Notification has subject", bool(notification.subject))
        log_result("Email", "Notification has body", bool(notification.body_text))
    except Exception as e:
        log_result("Email", "Create notification", False, str(e)[:50])


def test_docker_config():
    """Test Docker configuration files exist"""
    print("\n" + "="*60)
    print("🐳 Testing Docker Configuration")
    print("="*60)

    base_dir = os.path.dirname(os.path.dirname(__file__))

    files_to_check = [
        ("Dockerfile", "Dockerfile"),
        ("docker-compose.yml", "docker-compose.yml"),
        (".env.example", ".env.example"),
        (".dockerignore", ".dockerignore"),
    ]

    for name, filename in files_to_check:
        path = os.path.join(base_dir, filename)
        exists = os.path.exists(path)
        log_result("Docker", f"{name} exists", exists)

    # Check Dockerfile has required content
    dockerfile_path = os.path.join(base_dir, "Dockerfile")
    if os.path.exists(dockerfile_path):
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        log_result("Docker", "Dockerfile has FROM", "FROM python" in content)
        log_result("Docker", "Dockerfile has EXPOSE", "EXPOSE 8000" in content)
        log_result("Docker", "Dockerfile has CMD", "CMD" in content)


def test_export_service():
    """Test data export service"""
    print("\n" + "="*60)
    print("📊 Testing Data Export Service")
    print("="*60)

    try:
        from services.data_export_service import get_data_export_service, ExportFormat, ExportConfig
        log_result("Export", "DataExportService import", True)
    except ImportError as e:
        log_result("Export", "DataExportService import", False, str(e)[:50])
        return

    try:
        service = get_data_export_service()
        log_result("Export", "DataExportService singleton", True)
    except Exception as e:
        log_result("Export", "DataExportService singleton", False, str(e)[:50])
        return

    # Test CSV export
    test_data = [
        {"name": "Field 1", "acres": 160, "crop": "corn"},
        {"name": "Field 2", "acres": 80, "crop": "soybean"}
    ]

    try:
        csv_bytes = service.export_to_csv(test_data)
        log_result("Export", "CSV export", len(csv_bytes) > 0, f"{len(csv_bytes)} bytes")
        # Check CSV has headers
        csv_content = csv_bytes.decode('utf-8-sig')
        has_headers = "Name" in csv_content and "Acres" in csv_content
        log_result("Export", "CSV has headers", has_headers)
    except Exception as e:
        log_result("Export", "CSV export", False, str(e)[:50])

    # Test Excel export
    try:
        excel_bytes = service.export_to_excel(test_data)
        log_result("Export", "Excel export", len(excel_bytes) > 0, f"{len(excel_bytes)} bytes")
        # Excel files start with PK (zip format)
        is_valid_xlsx = excel_bytes[:2] == b'PK'
        log_result("Export", "Excel file valid", is_valid_xlsx)
    except ImportError:
        log_result("Export", "Excel export", False, "openpyxl not installed")
    except Exception as e:
        log_result("Export", "Excel export", False, str(e)[:50])

    # Test pre-configured exports
    try:
        fields_csv = service.export_fields(test_data, ExportFormat.CSV)
        log_result("Export", "Fields export", len(fields_csv) > 0)
    except Exception as e:
        log_result("Export", "Fields export", False, str(e)[:50])


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
    print("📋 FULL SMOKE TEST REPORT - AgTools v3.1")
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
        f.write(f"# Full Smoke Test Results - AgTools v3.1\n\n")
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
    print("🧪 FULL SMOKE TEST - AgTools v3.1")
    print("="*60)

    test_main_app()
    test_services()
    test_database_schema()
    test_ai_services()
    test_mobile_interface()
    test_pdf_service()
    test_email_service()
    test_docker_config()
    test_export_service()

    success = generate_report()
    sys.exit(0 if success else 1)
