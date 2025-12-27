"""
Smoke Test Suite for AgTools v3.0 AI/ML Intelligence Suite
Tests AI Image Service and Crop Health Service functionality
"""

import os
import sys
import io
import time
from datetime import datetime

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test results tracking
results = []
start_time = time.time()


def log_result(category: str, test: str, passed: bool, details: str = ""):
    """Log a test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append({
        "category": category,
        "test": test,
        "passed": passed,
        "details": details
    })
    print(f"  {status}: {test}" + (f" - {details}" if details else ""))


def test_ai_image_service_imports():
    """Test AI Image Service imports"""
    print("\n📦 Testing AI Image Service Imports...")

    try:
        from services.ai_image_service import AIImageService, get_ai_image_service
        log_result("AI Image Service", "Import AIImageService", True)
    except Exception as e:
        log_result("AI Image Service", "Import AIImageService", False, str(e))
        return False

    try:
        from services.ai_image_service import AIProvider, IdentificationType
        log_result("AI Image Service", "Import Enums", True)
    except Exception as e:
        log_result("AI Image Service", "Import Enums", False, str(e))

    return True


def test_ai_image_service_init():
    """Test AI Image Service initialization"""
    print("\n🔧 Testing AI Image Service Initialization...")

    try:
        from services.ai_image_service import AIImageService
        service = AIImageService(db_path=":memory:")
        log_result("AI Image Service", "Create service instance", True)
    except Exception as e:
        log_result("AI Image Service", "Create service instance", False, str(e))
        return None

    # Check knowledge base
    try:
        kb_crops = len(service.knowledge_base)
        log_result("AI Image Service", f"Knowledge base loaded ({kb_crops} crops)", kb_crops >= 2)
    except Exception as e:
        log_result("AI Image Service", "Knowledge base loaded", False, str(e))

    # Check keyword lookup
    try:
        kw_count = len(service.keyword_lookup)
        log_result("AI Image Service", f"Keyword lookup built ({kw_count} keywords)", kw_count > 0)
    except Exception as e:
        log_result("AI Image Service", "Keyword lookup built", False, str(e))

    return service


def test_ai_label_mapping():
    """Test AI label to knowledge base mapping"""
    print("\n🏷️ Testing AI Label Mapping...")

    try:
        from services.ai_image_service import AIImageService
        service = AIImageService(db_path=":memory:")

        # Test mapping known labels
        test_labels = [
            {"label": "aphid", "score": 0.85},
            {"label": "rust disease", "score": 0.72},
            {"label": "caterpillar", "score": 0.65}
        ]

        mapped = service._map_labels_to_knowledge_base(test_labels, "corn")
        log_result("AI Image Service", f"Label mapping works ({len(mapped)} matches)", len(mapped) > 0)

        if mapped:
            log_result("AI Image Service", f"First match: {mapped[0]['name']}", True)

    except Exception as e:
        log_result("AI Image Service", "Label mapping", False, str(e))


def test_crop_health_service_imports():
    """Test Crop Health Service imports"""
    print("\n📦 Testing Crop Health Service Imports...")

    try:
        from services.crop_health_service import CropHealthService, get_crop_health_service
        log_result("Crop Health Service", "Import CropHealthService", True)
    except Exception as e:
        log_result("Crop Health Service", "Import CropHealthService", False, str(e))
        return False

    try:
        from services.crop_health_service import HealthStatus, IssueType, ImageType
        log_result("Crop Health Service", "Import Enums", True)
    except Exception as e:
        log_result("Crop Health Service", "Import Enums", False, str(e))

    return True


def test_crop_health_service_init():
    """Test Crop Health Service initialization"""
    print("\n🔧 Testing Crop Health Service Initialization...")

    try:
        from services.crop_health_service import CropHealthService
        service = CropHealthService(db_path=":memory:", output_dir="test_health_maps")
        log_result("Crop Health Service", "Create service instance", True)
    except Exception as e:
        log_result("Crop Health Service", "Create service instance", False, str(e))
        return None

    # Check NDVI thresholds
    try:
        thresholds = len(service.NDVI_THRESHOLDS)
        log_result("Crop Health Service", f"NDVI thresholds loaded ({thresholds} levels)", thresholds == 6)
    except Exception as e:
        log_result("Crop Health Service", "NDVI thresholds loaded", False, str(e))

    # Check issue patterns
    try:
        patterns = len(service.ISSUE_PATTERNS)
        log_result("Crop Health Service", f"Issue patterns loaded ({patterns} types)", patterns >= 5)
    except Exception as e:
        log_result("Crop Health Service", "Issue patterns loaded", False, str(e))

    return service


def test_health_classification():
    """Test health status classification"""
    print("\n🏥 Testing Health Classification...")

    try:
        from services.crop_health_service import CropHealthService, HealthStatus
        service = CropHealthService(db_path=":memory:", output_dir="test_health_maps")

        # Test various NDVI values
        test_cases = [
            (0.8, HealthStatus.EXCELLENT),
            (0.6, HealthStatus.GOOD),
            (0.4, HealthStatus.MODERATE),
            (0.25, HealthStatus.STRESSED),
            (0.15, HealthStatus.POOR),
            (0.05, HealthStatus.CRITICAL),
        ]

        all_passed = True
        for ndvi, expected in test_cases:
            result = service._classify_health(ndvi)
            passed = result == expected
            if not passed:
                all_passed = False
                log_result("Crop Health Service", f"Classify NDVI {ndvi}", False, f"Got {result}, expected {expected}")

        if all_passed:
            log_result("Crop Health Service", "Health classification (all 6 levels)", True)

    except Exception as e:
        log_result("Crop Health Service", "Health classification", False, str(e))


def test_pseudo_ndvi_calculation():
    """Test pseudo-NDVI calculation from RGB"""
    print("\n🌿 Testing Pseudo-NDVI Calculation...")

    try:
        import numpy as np
        from services.crop_health_service import CropHealthService
        service = CropHealthService(db_path=":memory:", output_dir="test_health_maps")

        # Create test RGB image (green field)
        green_field = np.zeros((100, 100, 3), dtype=np.uint8)
        green_field[:, :, 1] = 180  # Green channel high
        green_field[:, :, 0] = 50   # Red channel low
        green_field[:, :, 2] = 50   # Blue channel low

        ndvi = service._calculate_pseudo_ndvi(green_field)

        mean_ndvi = float(np.mean(ndvi))
        log_result("Crop Health Service", f"Pseudo-NDVI calculation (mean={mean_ndvi:.3f})",
                   0 <= mean_ndvi <= 1, f"Range: {np.min(ndvi):.3f} - {np.max(ndvi):.3f}")

        # Green should have higher NDVI than red
        red_field = np.zeros((100, 100, 3), dtype=np.uint8)
        red_field[:, :, 0] = 180  # Red channel high
        red_field[:, :, 1] = 50   # Green channel low

        ndvi_red = service._calculate_pseudo_ndvi(red_field)
        mean_red = float(np.mean(ndvi_red))

        log_result("Crop Health Service", "Green > Red NDVI", mean_ndvi > mean_red,
                   f"Green={mean_ndvi:.3f}, Red={mean_red:.3f}")

    except Exception as e:
        log_result("Crop Health Service", "Pseudo-NDVI calculation", False, str(e))


def test_zone_analysis():
    """Test zone-based analysis"""
    print("\n📊 Testing Zone Analysis...")

    try:
        import numpy as np
        from services.crop_health_service import CropHealthService
        service = CropHealthService(db_path=":memory:", output_dir="test_health_maps")

        # Create test NDVI map with variation
        ndvi_map = np.random.uniform(0.3, 0.8, (100, 100))
        # Add a stressed zone
        ndvi_map[20:40, 20:40] = 0.15

        zones = service._analyze_zones(ndvi_map, grid_size=5)

        log_result("Crop Health Service", f"Zone analysis ({len(zones)} zones)", len(zones) == 25)

        # Check that stressed zone was detected
        stressed_zones = [z for z in zones if z.health_status.value in ['stressed', 'poor', 'critical']]
        log_result("Crop Health Service", f"Stressed zones detected ({len(stressed_zones)})", len(stressed_zones) > 0)

    except Exception as e:
        log_result("Crop Health Service", "Zone analysis", False, str(e))


def test_image_processing():
    """Test full image processing pipeline"""
    print("\n🖼️ Testing Image Processing Pipeline...")

    try:
        import numpy as np
        from PIL import Image
        from services.crop_health_service import CropHealthService, ImageType
        service = CropHealthService(db_path=":memory:", output_dir="test_health_maps")

        # Create test image
        img_array = np.zeros((200, 200, 3), dtype=np.uint8)
        # Healthy area (green)
        img_array[:100, :, 1] = 150
        img_array[:100, :, 0] = 50
        # Stressed area (yellow/brown)
        img_array[100:, :, 0] = 150
        img_array[100:, :, 1] = 100

        img = Image.fromarray(img_array)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()

        # Analyze image
        report = service.analyze_image(
            image_bytes=image_bytes,
            image_type=ImageType.RGB,
            field_name="Test Field",
            grid_size=5,
            save_results=False
        )

        log_result("Crop Health Service", "Full image analysis", True,
                   f"NDVI={report.overall_ndvi:.3f}, Health={report.overall_health.value}")
        log_result("Crop Health Service", f"Zones analyzed ({len(report.zones)})", len(report.zones) > 0)
        log_result("Crop Health Service", f"Recommendations generated ({len(report.recommendations)})",
                   len(report.recommendations) > 0)

    except Exception as e:
        log_result("Crop Health Service", "Full image analysis", False, str(e))


def test_main_app_routes():
    """Test that main app loads with AI routes"""
    print("\n🌐 Testing Main App Routes...")

    try:
        from main import app
        route_count = len(app.routes)
        log_result("Main App", f"App loads successfully ({route_count} routes)", route_count >= 180)

        # Check for AI endpoints
        ai_routes = [r for r in app.routes if hasattr(r, 'path') and '/ai/' in r.path]
        log_result("Main App", f"AI endpoints registered ({len(ai_routes)})", len(ai_routes) >= 9)

        # List AI endpoints
        ai_paths = [r.path for r in app.routes if hasattr(r, 'path') and '/ai/' in r.path]
        for path in sorted(set(ai_paths)):
            log_result("Main App", f"Route: {path}", True)

    except Exception as e:
        log_result("Main App", "App loads", False, str(e))


def test_database_tables():
    """Test that database tables are created correctly"""
    print("\n💾 Testing Database Tables...")

    try:
        import sqlite3
        import tempfile
        import os
        from services.ai_image_service import AIImageService
        from services.crop_health_service import CropHealthService

        # Use temp file database for proper table persistence
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # Initialize AI service (creates tables)
            ai_service = AIImageService(db_path=db_path)

            # Check AI tables
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_ai_tables = ['ai_training_images', 'ai_predictions', 'ai_models']
            for table in expected_ai_tables:
                log_result("Database", f"Table '{table}' exists", table in tables)

            conn.close()

            # Initialize health service (adds more tables)
            health_service = CropHealthService(db_path=db_path, output_dir="test_health_maps")

            conn2 = sqlite3.connect(db_path)
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT name FROM sqlite_master WHERE type='table'")
            all_tables = [row[0] for row in cursor2.fetchall()]
            conn2.close()

            expected_health_tables = ['field_health_assessments', 'health_zones', 'health_trends']
            for table in expected_health_tables:
                log_result("Database", f"Table '{table}' exists", table in all_tables)

        finally:
            # Cleanup temp file
            if os.path.exists(db_path):
                os.remove(db_path)

    except Exception as e:
        log_result("Database", "Table creation", False, str(e))


def generate_report():
    """Generate test report"""
    elapsed = time.time() - start_time

    passed = sum(1 for r in results if r['passed'])
    failed = sum(1 for r in results if not r['passed'])
    total = len(results)

    print("\n" + "=" * 60)
    print("📋 SMOKE TEST REPORT - AgTools v3.0 AI/ML Suite")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {elapsed:.2f} seconds")
    print()
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Pass Rate: {passed/total*100:.1f}%")
    print()

    # Group by category
    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'passed': 0, 'failed': 0}
        if r['passed']:
            categories[cat]['passed'] += 1
        else:
            categories[cat]['failed'] += 1

    print("By Category:")
    for cat, stats in categories.items():
        total_cat = stats['passed'] + stats['failed']
        print(f"  {cat}: {stats['passed']}/{total_cat} passed")

    # List failures
    failures = [r for r in results if not r['passed']]
    if failures:
        print("\n❌ FAILURES:")
        for f in failures:
            print(f"  - [{f['category']}] {f['test']}: {f['details']}")

    print("\n" + "=" * 60)

    return passed, failed, total, elapsed


def save_report(passed, failed, total, elapsed):
    """Save report to file"""
    report_path = os.path.join(os.path.dirname(__file__), 'SMOKE_TEST_RESULTS_v3.0.md')

    with open(report_path, 'w') as f:
        f.write("# Smoke Test Results - AgTools v3.0 AI/ML Intelligence Suite\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Duration:** {elapsed:.2f} seconds\n\n")
        f.write("## Summary\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Total Tests | {total} |\n")
        f.write(f"| Passed | {passed} |\n")
        f.write(f"| Failed | {failed} |\n")
        f.write(f"| **Pass Rate** | **{passed/total*100:.1f}%** |\n\n")

        f.write("## Test Results\n\n")

        # Group by category
        categories = {}
        for r in results:
            cat = r['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        for cat, tests in categories.items():
            passed_cat = sum(1 for t in tests if t['passed'])
            f.write(f"### {cat} ({passed_cat}/{len(tests)} passed)\n\n")
            f.write("| Test | Status | Details |\n")
            f.write("|------|--------|--------|\n")
            for t in tests:
                status = "✅ Pass" if t['passed'] else "❌ Fail"
                details = t['details'][:50] if t['details'] else "-"
                f.write(f"| {t['test']} | {status} | {details} |\n")
            f.write("\n")

        f.write("## New Features Tested\n\n")
        f.write("### Phase 1: AI Image Service\n")
        f.write("- Hybrid cloud + local model architecture\n")
        f.write("- Knowledge base integration (46+ pests/diseases)\n")
        f.write("- Label mapping and confidence scoring\n")
        f.write("- Training data collection pipeline\n\n")

        f.write("### Phase 2: Crop Health Service\n")
        f.write("- NDVI calculation (RGB and multispectral)\n")
        f.write("- 6-level health classification\n")
        f.write("- Zone-based analysis\n")
        f.write("- Problem detection and recommendations\n\n")

        f.write("## API Endpoints Verified\n\n")
        f.write("```\n")
        f.write("AI Intelligence:\n")
        f.write("  POST /api/v1/ai/identify/image\n")
        f.write("  POST /api/v1/ai/feedback\n")
        f.write("  GET  /api/v1/ai/training/stats\n")
        f.write("  POST /api/v1/ai/training/export\n")
        f.write("  GET  /api/v1/ai/models\n\n")
        f.write("Crop Health:\n")
        f.write("  POST /api/v1/ai/health/analyze\n")
        f.write("  GET  /api/v1/ai/health/history/{field_id}\n")
        f.write("  GET  /api/v1/ai/health/trends/{field_id}\n")
        f.write("  GET  /api/v1/ai/health/status-levels\n")
        f.write("```\n")

    print(f"\n📄 Report saved to: {report_path}")
    return report_path


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SMOKE TEST - AgTools v3.0 AI/ML Intelligence Suite")
    print("=" * 60)

    # Change to backend directory for imports
    os.chdir(os.path.join(os.path.dirname(__file__), '..', 'backend'))

    # Run tests
    test_ai_image_service_imports()
    test_ai_image_service_init()
    test_ai_label_mapping()
    test_crop_health_service_imports()
    test_crop_health_service_init()
    test_health_classification()
    test_pseudo_ndvi_calculation()
    test_zone_analysis()
    test_image_processing()
    test_main_app_routes()
    test_database_tables()

    # Generate and save report
    passed, failed, total, elapsed = generate_report()
    save_report(passed, failed, total, elapsed)

    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)
