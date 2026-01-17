#!/usr/bin/env python3
"""
AgTools Comprehensive Workflow Test Suite
Tests all backend services and API workflows

Run with: python tests/test_all_workflows.py
"""

import os
import sys
import io

# Fix Windows console encoding (skip if running under pytest)
if sys.platform == 'win32' and "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import datetime, date
from typing import List, Dict, Any
import json
import traceback

# Test results tracking
RESULTS: List[Dict[str, Any]] = []
CATEGORIES: Dict[str, Dict[str, int]] = {}


def log_result(category: str, test: str, passed: bool, details: str = ""):
    """Log a test result"""
    status = "PASS" if passed else "FAIL"
    RESULTS.append({
        "category": category,
        "test": test,
        "passed": passed,
        "details": details
    })

    if category not in CATEGORIES:
        CATEGORIES[category] = {"passed": 0, "failed": 0}
    if passed:
        CATEGORIES[category]["passed"] += 1
    else:
        CATEGORIES[category]["failed"] += 1

    detail_str = f" - {details}" if details else ""
    print(f"  [{status}] {test}{detail_str}")


# ==============================================================================
# COST OPTIMIZER WORKFLOWS
# ==============================================================================

def test_input_cost_optimizer():
    """Test InputCostOptimizer service"""
    print("\n" + "="*70)
    print("INPUT COST OPTIMIZER")
    print("="*70)

    try:
        from services.input_cost_optimizer import InputCostOptimizer
        optimizer = InputCostOptimizer()

        # Test 1: Quick estimate - non-irrigated
        result = optimizer.quick_cost_estimate(
            acres=160, crop="corn", is_irrigated=False, yield_goal=200
        )
        assert "total_cost_per_acre" in result
        non_irr_cost = result["total_cost_per_acre"]
        log_result("Input Cost", "Quick estimate (non-irrigated corn)", True,
                   f"${non_irr_cost}/acre")

        # Test 2: Quick estimate - irrigated (should be higher)
        result_irr = optimizer.quick_cost_estimate(
            acres=160, crop="corn", is_irrigated=True, yield_goal=200
        )
        irr_cost = result_irr["total_cost_per_acre"]
        passed = irr_cost > non_irr_cost
        log_result("Input Cost", "Irrigated adds cost", passed,
                   f"${irr_cost}/acre vs ${non_irr_cost}/acre")

        # Test 3: Soybean estimate
        result_soy = optimizer.quick_cost_estimate(
            acres=100, crop="soybean", is_irrigated=False, yield_goal=55
        )
        log_result("Input Cost", "Quick estimate (soybean)", True,
                   f"${result_soy['total_cost_per_acre']}/acre")

        # Test 4: Wheat estimate
        result_wheat = optimizer.quick_cost_estimate(
            acres=200, crop="wheat", is_irrigated=False, yield_goal=70
        )
        log_result("Input Cost", "Quick estimate (wheat)", True,
                   f"${result_wheat['total_cost_per_acre']}/acre")

        # Test 5: Budget worksheet
        worksheet = optimizer.generate_budget_worksheet(
            crop="corn", acres=160, yield_goal=200
        )
        assert "line_items" in worksheet or "budget" in worksheet or worksheet
        log_result("Input Cost", "Generate budget worksheet", True)

        # Test 6: Compare strategies
        try:
            comparison = optimizer.compare_input_strategies(
                crop="corn", acres=160, strategies=["standard", "high_input", "low_input"]
            )
            log_result("Input Cost", "Compare input strategies", True)
        except Exception as e:
            log_result("Input Cost", "Compare input strategies", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Input Cost", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


def test_application_cost_optimizer():
    """Test ApplicationCostOptimizer service"""
    print("\n" + "="*70)
    print("APPLICATION COST OPTIMIZER (Fertilizer/Pesticide)")
    print("="*70)

    try:
        from services.application_cost_optimizer import ApplicationCostOptimizer
        optimizer = ApplicationCostOptimizer()

        # Test 1: Fertilizer optimization - corn
        result = optimizer.optimize_fertilizer_program(
            crop="corn",
            yield_goal=200,
            acres=160,
            soil_test_results={"P": 20, "K": 150, "pH": 6.5, "OM": 3.0, "n_credit": 0}
        )
        assert "recommendations" in result
        assert "cost_summary" in result
        cost = result["cost_summary"]["cost_per_acre"]
        log_result("Application Cost", "Fertilizer optimization (corn)", True,
                   f"${cost:.2f}/acre")

        # Test 2: Fertilizer with N credit (previous soybean)
        result_ncredit = optimizer.optimize_fertilizer_program(
            crop="corn",
            yield_goal=200,
            acres=160,
            soil_test_results={"P": 20, "K": 150, "pH": 6.5, "OM": 3.0, "n_credit": 40}
        )
        cost_ncredit = result_ncredit["cost_summary"]["cost_per_acre"]
        passed = cost_ncredit < cost  # Should be cheaper with N credit
        log_result("Application Cost", "N credit reduces cost", passed,
                   f"${cost_ncredit:.2f} vs ${cost:.2f}")

        # Test 3: Soybean fertilizer
        result_soy = optimizer.optimize_fertilizer_program(
            crop="soybean",
            yield_goal=55,
            acres=100,
            soil_test_results={"P": 25, "K": 140, "pH": 6.8, "OM": 2.5}
        )
        log_result("Application Cost", "Fertilizer optimization (soybean)", True,
                   f"${result_soy['cost_summary']['cost_per_acre']:.2f}/acre")

        # Test 4: Compare pesticide options
        try:
            comparison = optimizer.compare_pesticide_options(
                product_options=[
                    {"name": "Roundup PowerMax", "cost_per_acre": 8.50, "rate": "32 oz/acre"},
                    {"name": "Generic Glyphosate", "cost_per_acre": 4.25, "rate": "32 oz/acre"}
                ],
                acres=160,
                application_method="foliar_ground"
            )
            log_result("Application Cost", "Pesticide comparison", True)
        except Exception as e:
            log_result("Application Cost", "Pesticide comparison", False, str(e)[:50])

        # Test 5: Spray program costs
        try:
            spray_costs = optimizer.calculate_spray_program_costs(
                applications=[
                    {"product": "Pre-emerge herbicide", "rate": 2.0, "timing": "preplant"},
                    {"product": "Post herbicide", "rate": 32, "timing": "V4"},
                ],
                acres=160
            )
            log_result("Application Cost", "Spray program costs", True)
        except Exception as e:
            log_result("Application Cost", "Spray program costs", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Application Cost", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# PRICING SERVICE WORKFLOWS
# ==============================================================================

def test_pricing_service():
    """Test PricingService"""
    print("\n" + "="*70)
    print("PRICING SERVICE")
    print("="*70)

    try:
        from services.pricing_service import PricingService
        service = PricingService()

        # Test 1: Get all prices
        prices = service.get_all_prices()
        assert prices is not None
        log_result("Pricing", "Get all prices", True, f"{len(prices)} items")

        # Test 2: Get specific price
        try:
            price = service.get_price("urea")
            log_result("Pricing", "Get specific price (urea)", True, f"${price}")
        except Exception as e:
            log_result("Pricing", "Get specific price", False, str(e)[:50])

        # Test 3: Price alerts
        try:
            alerts = service.get_price_alerts()
            log_result("Pricing", "Get price alerts", True, f"{len(alerts)} alerts")
        except Exception as e:
            log_result("Pricing", "Get price alerts", False, str(e)[:50])

        # Test 4: Buy recommendation
        try:
            rec = service.get_buy_recommendation("fertilizer")
            log_result("Pricing", "Buy recommendation", True)
        except Exception as e:
            log_result("Pricing", "Buy recommendation", False, str(e)[:50])

        # Test 5: Compare suppliers
        try:
            comparison = service.compare_suppliers("urea", quantity=10)
            log_result("Pricing", "Compare suppliers", True)
        except Exception as e:
            log_result("Pricing", "Compare suppliers", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Pricing", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# SPRAY TIMING WORKFLOWS
# ==============================================================================

def test_spray_timing():
    """Test SprayTimingOptimizer"""
    print("\n" + "="*70)
    print("SPRAY TIMING OPTIMIZER")
    print("="*70)

    try:
        from services.spray_timing_optimizer import SprayTimingOptimizer
        optimizer = SprayTimingOptimizer()

        # Test 1: Find spray windows
        try:
            windows = optimizer.find_spray_windows(
                crop="corn",
                product_type="herbicide",
                weather_forecast=[
                    {"day": 1, "temp_high": 78, "temp_low": 55, "wind": 8, "precip_chance": 10},
                    {"day": 2, "temp_high": 82, "temp_low": 58, "wind": 12, "precip_chance": 30},
                    {"day": 3, "temp_high": 75, "temp_low": 52, "wind": 5, "precip_chance": 5},
                ]
            )
            log_result("Spray Timing", "Find spray windows", True)
        except Exception as e:
            log_result("Spray Timing", "Find spray windows", False, str(e)[:50])

        # Test 2: Evaluate current conditions
        try:
            eval_result = optimizer.evaluate_current_conditions(
                temperature=75,
                wind_speed=8,
                humidity=55,
                dew_point=52
            )
            log_result("Spray Timing", "Evaluate conditions", True)
        except Exception as e:
            log_result("Spray Timing", "Evaluate conditions", False, str(e)[:50])

        # Test 3: Spray timing by growth stage
        try:
            timing = optimizer.get_spray_timing_by_growth_stage(
                crop="corn",
                growth_stage="V6",
                application_type="post_herbicide"
            )
            log_result("Spray Timing", "Timing by growth stage", True)
        except Exception as e:
            log_result("Spray Timing", "Timing by growth stage", False, str(e)[:50])

        # Test 4: Cost of waiting
        try:
            cost = optimizer.calculate_cost_of_waiting(
                crop="corn",
                pest_type="weeds",
                current_pressure="medium",
                days_delay=5
            )
            log_result("Spray Timing", "Cost of waiting", True)
        except Exception as e:
            log_result("Spray Timing", "Cost of waiting", False, str(e)[:50])

        # Test 5: Disease pressure
        try:
            pressure = optimizer.assess_disease_pressure(
                crop="corn",
                disease="gray_leaf_spot",
                weather_conditions={"humidity": 85, "recent_rain": True}
            )
            log_result("Spray Timing", "Disease pressure assessment", True)
        except Exception as e:
            log_result("Spray Timing", "Disease pressure assessment", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Spray Timing", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# YIELD RESPONSE WORKFLOWS
# ==============================================================================

def test_yield_response():
    """Test YieldResponseOptimizer"""
    print("\n" + "="*70)
    print("YIELD RESPONSE OPTIMIZER")
    print("="*70)

    try:
        from services.yield_response_optimizer import YieldResponseOptimizer
        optimizer = YieldResponseOptimizer()

        # Test 1: Calculate yield response
        try:
            response = optimizer.calculate_yield_response(
                crop="corn",
                nutrient="nitrogen",
                current_rate=150,
                base_yield=180
            )
            log_result("Yield Response", "Calculate yield response", True)
        except Exception as e:
            log_result("Yield Response", "Calculate yield response", False, str(e)[:50])

        # Test 2: Economic optimum
        try:
            optimum = optimizer.calculate_economic_optimum(
                crop="corn",
                nutrient="nitrogen",
                crop_price=4.50,
                nutrient_price=0.50
            )
            log_result("Yield Response", "Economic optimum", True)
        except Exception as e:
            log_result("Yield Response", "Economic optimum", False, str(e)[:50])

        # Test 3: Compare rate scenarios
        try:
            scenarios = optimizer.compare_rate_scenarios(
                crop="corn",
                nutrient="nitrogen",
                rates=[120, 150, 180, 200],
                crop_price=4.50,
                nutrient_price=0.50
            )
            log_result("Yield Response", "Compare rate scenarios", True)
        except Exception as e:
            log_result("Yield Response", "Compare rate scenarios", False, str(e)[:50])

        # Test 4: Response curve
        try:
            curve = optimizer.generate_response_curve(
                crop="corn",
                nutrient="nitrogen"
            )
            log_result("Yield Response", "Generate response curve", True)
        except Exception as e:
            log_result("Yield Response", "Generate response curve", False, str(e)[:50])

        # Test 5: Price ratio guide
        try:
            guide = optimizer.generate_price_ratio_guide(
                crop="corn",
                nutrient="nitrogen"
            )
            log_result("Yield Response", "Price ratio guide", True)
        except Exception as e:
            log_result("Yield Response", "Price ratio guide", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Yield Response", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# INVENTORY SERVICE WORKFLOWS
# ==============================================================================

def test_inventory_service():
    """Test InventoryService"""
    print("\n" + "="*70)
    print("INVENTORY SERVICE")
    print("="*70)

    try:
        from services.inventory_service import InventoryService
        service = InventoryService()

        # Test 1: Get categories
        try:
            categories = service.get_categories()
            log_result("Inventory", "Get categories", True, f"{len(categories)} categories")
        except Exception as e:
            log_result("Inventory", "Get categories", False, str(e)[:50])

        # Test 2: Get inventory summary
        try:
            summary = service.get_inventory_summary()
            log_result("Inventory", "Get inventory summary", True)
        except Exception as e:
            log_result("Inventory", "Get inventory summary", False, str(e)[:50])

        # Test 3: Get alerts (low stock)
        try:
            alerts = service.get_alerts()
            log_result("Inventory", "Get alerts", True, f"{len(alerts)} alerts")
        except Exception as e:
            log_result("Inventory", "Get alerts", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Inventory", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# EQUIPMENT SERVICE WORKFLOWS
# ==============================================================================

def test_equipment_service():
    """Test EquipmentService"""
    print("\n" + "="*70)
    print("EQUIPMENT SERVICE")
    print("="*70)

    try:
        from services.equipment_service import EquipmentService
        service = EquipmentService()

        # Test 1: Get equipment types
        try:
            types = service.get_equipment_types()
            log_result("Equipment", "Get equipment types", True, f"{len(types)} types")
        except Exception as e:
            log_result("Equipment", "Get equipment types", False, str(e)[:50])

        # Test 2: Get equipment statuses
        try:
            statuses = service.get_equipment_statuses()
            log_result("Equipment", "Get equipment statuses", True)
        except Exception as e:
            log_result("Equipment", "Get equipment statuses", False, str(e)[:50])

        # Test 3: Get equipment summary
        try:
            summary = service.get_equipment_summary()
            log_result("Equipment", "Get equipment summary", True)
        except Exception as e:
            log_result("Equipment", "Get equipment summary", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Equipment", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# FIELD SERVICE WORKFLOWS
# ==============================================================================

def test_field_service():
    """Test FieldService"""
    print("\n" + "="*70)
    print("FIELD SERVICE")
    print("="*70)

    try:
        from services.field_service import FieldService
        service = FieldService()

        # Test 1: List fields
        try:
            fields = service.list_fields()
            log_result("Fields", "List fields", True, f"{len(fields)} fields")
        except Exception as e:
            log_result("Fields", "List fields", False, str(e)[:50])

        # Test 2: Get farm names
        try:
            farms = service.get_farm_names()
            log_result("Fields", "Get farm names", True, f"{len(farms)} farms")
        except Exception as e:
            log_result("Fields", "Get farm names", False, str(e)[:50])

        # Test 3: Get field summary
        try:
            summary = service.get_field_summary()
            log_result("Fields", "Get field summary", True)
        except Exception as e:
            log_result("Fields", "Get field summary", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Fields", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# FIELD OPERATIONS SERVICE
# ==============================================================================

def test_field_operations_service():
    """Test FieldOperationsService"""
    print("\n" + "="*70)
    print("FIELD OPERATIONS SERVICE")
    print("="*70)

    try:
        from services.field_operations_service import FieldOperationsService
        service = FieldOperationsService()

        # Test 1: List operations
        try:
            ops = service.list_operations()
            log_result("Operations", "List operations", True, f"{len(ops)} operations")
        except Exception as e:
            log_result("Operations", "List operations", False, str(e)[:50])

        # Test 2: Get operations summary
        try:
            summary = service.get_operations_summary()
            log_result("Operations", "Get operations summary", True)
        except Exception as e:
            log_result("Operations", "Get operations summary", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Operations", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# TASK SERVICE WORKFLOWS
# ==============================================================================

def test_task_service():
    """Test TaskService"""
    print("\n" + "="*70)
    print("TASK SERVICE")
    print("="*70)

    try:
        from services.task_service import TaskService
        service = TaskService()

        # Test 1: List tasks
        try:
            tasks = service.list_tasks()
            log_result("Tasks", "List tasks", True, f"{len(tasks)} tasks")
        except Exception as e:
            log_result("Tasks", "List tasks", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Tasks", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# LIVESTOCK SERVICE WORKFLOWS
# ==============================================================================

def test_livestock_service():
    """Test LivestockService"""
    print("\n" + "="*70)
    print("LIVESTOCK SERVICE")
    print("="*70)

    try:
        from services.livestock_service import LivestockService
        service = LivestockService()

        # Test: Service loads
        log_result("Livestock", "Service initialization", True)

        return True
    except Exception as e:
        log_result("Livestock", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# SEED PLANTING SERVICE WORKFLOWS
# ==============================================================================

def test_seed_planting_service():
    """Test SeedPlantingService"""
    print("\n" + "="*70)
    print("SEED PLANTING SERVICE")
    print("="*70)

    try:
        from services.seed_planting_service import SeedPlantingService
        service = SeedPlantingService()

        # Test: Service loads
        log_result("Seed Planting", "Service initialization", True)

        return True
    except Exception as e:
        log_result("Seed Planting", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# GENFIN CORE SERVICE WORKFLOWS
# ==============================================================================

def test_genfin_service():
    """Test GenFinCoreService"""
    print("\n" + "="*70)
    print("GENFIN CORE SERVICE")
    print("="*70)

    try:
        from services.genfin_core_service import GenFinCoreService
        service = GenFinCoreService()

        # Test: Service loads
        log_result("GenFin", "Service initialization", True)

        return True
    except Exception as e:
        log_result("GenFin", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# ACCOUNTING IMPORT SERVICE
# ==============================================================================

def test_accounting_import_service():
    """Test AccountingImportService"""
    print("\n" + "="*70)
    print("ACCOUNTING IMPORT SERVICE")
    print("="*70)

    try:
        from services.accounting_import import AccountingImportService
        service = AccountingImportService()

        # Test 1: Get supported formats
        try:
            formats = service.get_supported_formats()
            log_result("Accounting Import", "Get supported formats", True, f"{len(formats)} formats")
        except Exception as e:
            log_result("Accounting Import", "Get supported formats", False, str(e)[:50])

        # Test 2: Get category list
        try:
            categories = service.get_category_list()
            log_result("Accounting Import", "Get category list", True, f"{len(categories)} categories")
        except Exception as e:
            log_result("Accounting Import", "Get category list", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Accounting Import", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# REPORTING SERVICE WORKFLOWS
# ==============================================================================

def test_reporting_service():
    """Test ReportingService"""
    print("\n" + "="*70)
    print("REPORTING SERVICE")
    print("="*70)

    try:
        from services.reporting_service import ReportingService
        service = ReportingService()

        # Test 1: Dashboard summary
        try:
            summary = service.get_dashboard_summary()
            log_result("Reporting", "Get dashboard summary", True)
        except Exception as e:
            log_result("Reporting", "Get dashboard summary", False, str(e)[:50])

        # Test 2: Equipment report
        try:
            report = service.get_equipment_report()
            log_result("Reporting", "Get equipment report", True)
        except Exception as e:
            log_result("Reporting", "Get equipment report", False, str(e)[:50])

        # Test 3: Inventory report
        try:
            report = service.get_inventory_report()
            log_result("Reporting", "Get inventory report", True)
        except Exception as e:
            log_result("Reporting", "Get inventory report", False, str(e)[:50])

        # Test 4: Operations report
        try:
            report = service.get_operations_report()
            log_result("Reporting", "Get operations report", True)
        except Exception as e:
            log_result("Reporting", "Get operations report", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Reporting", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# CROP COST ANALYSIS SERVICE
# ==============================================================================

def test_crop_cost_analysis_service():
    """Test CropCostAnalysisService"""
    print("\n" + "="*70)
    print("CROP COST ANALYSIS SERVICE")
    print("="*70)

    try:
        from services.crop_cost_analysis_service import (
            get_crop_cost_analysis_service,
            CropAnalysisSummary,
            FieldCostDetail,
            FieldComparisonMatrix,
            CropComparisonItem,
            YearOverYearData,
            ROIAnalysisItem,
            TrendDataPoint
        )
        service = get_crop_cost_analysis_service()
        log_result("Crop Analysis", "Service initialization", True)

        crop_year = datetime.now().year

        # Test 1: Get summary
        try:
            summary = service.get_summary(crop_year)
            assert isinstance(summary, CropAnalysisSummary)
            log_result("Crop Analysis", "Get summary", True,
                       f"fields={summary.field_count}, total_cost=${summary.total_cost:.2f}")
        except Exception as e:
            log_result("Crop Analysis", "Get summary", False, str(e)[:50])

        # Test 2: Field comparison
        try:
            comparison = service.get_field_comparison(crop_year)
            assert isinstance(comparison, FieldComparisonMatrix)
            log_result("Crop Analysis", "Field comparison", True,
                       f"fields={len(comparison.fields)}")
        except Exception as e:
            log_result("Crop Analysis", "Field comparison", False, str(e)[:50])

        # Test 3: Crop comparison
        try:
            crops = service.get_crop_comparison(crop_year)
            assert isinstance(crops, list)
            log_result("Crop Analysis", "Crop comparison", True,
                       f"crops={len(crops)}")
        except Exception as e:
            log_result("Crop Analysis", "Crop comparison", False, str(e)[:50])

        # Test 4: Year over year
        try:
            yoy = service.get_year_comparison([crop_year - 1, crop_year])
            assert isinstance(yoy, list)
            log_result("Crop Analysis", "Year over year", True,
                       f"years={len(yoy)}")
        except Exception as e:
            log_result("Crop Analysis", "Year over year", False, str(e)[:50])

        # Test 5: ROI breakdown
        try:
            roi = service.get_roi_breakdown(crop_year)
            assert isinstance(roi, list)
            log_result("Crop Analysis", "ROI breakdown", True,
                       f"items={len(roi)}")
        except Exception as e:
            log_result("Crop Analysis", "ROI breakdown", False, str(e)[:50])

        # Test 6: Trend data
        try:
            trends = service.get_trend_data(crop_year - 2, crop_year, "cost_per_acre")
            assert isinstance(trends, list)
            log_result("Crop Analysis", "Trend data", True,
                       f"points={len(trends)}")
        except Exception as e:
            log_result("Crop Analysis", "Trend data", False, str(e)[:50])

        return True
    except Exception as e:
        log_result("Crop Analysis", "Service initialization", False, str(e))
        traceback.print_exc()
        return False


# ==============================================================================
# API ENDPOINT TESTS (via HTTP)
# ==============================================================================

def test_api_endpoints():
    """Test API endpoints directly"""
    print("\n" + "="*70)
    print("API ENDPOINT TESTS")
    print("="*70)

    import urllib.request
    import urllib.error

    base_url = "http://localhost:8000"

    endpoints = [
        ("GET", "/api/v1/health", "Health check"),
        ("GET", "/api/v1/pricing/current", "Current prices"),
        ("GET", "/api/v1/inventory/categories", "Inventory categories"),
        ("GET", "/api/v1/equipment/types", "Equipment types"),
        ("GET", "/docs", "API documentation"),
    ]

    for method, path, name in endpoints:
        try:
            url = f"{base_url}{path}"
            req = urllib.request.Request(url, method=method)
            with urllib.request.urlopen(req, timeout=5) as response:
                status = response.status
                passed = status in [200, 401]  # 401 is OK for auth-protected endpoints
                log_result("API", name, passed, f"HTTP {status}")
        except urllib.error.HTTPError as e:
            # 401/403 for auth endpoints is expected
            passed = e.code in [401, 403]
            log_result("API", name, passed, f"HTTP {e.code}")
        except Exception as e:
            log_result("API", name, False, str(e)[:50])

    return True


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

def run_all_tests():
    """Run all workflow tests"""
    print("\n" + "="*80)
    print("AGTOOLS COMPREHENSIVE WORKFLOW TEST SUITE")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")

    tests = [
        # Core optimization services
        test_input_cost_optimizer,
        test_application_cost_optimizer,
        test_pricing_service,
        test_spray_timing,
        test_yield_response,

        # Farm management services
        test_inventory_service,
        test_equipment_service,
        test_field_service,
        test_field_operations_service,
        test_task_service,

        # Specialty services
        test_livestock_service,
        test_seed_planting_service,

        # Financial services
        test_genfin_service,
        test_accounting_import_service,

        # Reporting
        test_reporting_service,

        # Analytics
        test_crop_cost_analysis_service,

        # API endpoints
        test_api_endpoints,
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"\n*** CRITICAL ERROR in {test.__name__}: {e}")
            traceback.print_exc()

    # Summary by category
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

    # Final summary
    total = total_passed + total_failed
    pct = (total_passed / total * 100) if total > 0 else 0

    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"  Total Tests: {total}")
    print(f"  Passed:      {total_passed} ({pct:.1f}%)")
    print(f"  Failed:      {total_failed} ({100-pct:.1f}%)")

    if total_failed > 0:
        print("\n*** FAILED TESTS ***")
        for r in RESULTS:
            if not r["passed"]:
                print(f"  - [{r['category']}] {r['test']}: {r['details']}")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Return exit code
    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
