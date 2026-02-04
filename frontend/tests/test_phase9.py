"""
Phase 9 Integration Tests

Tests for Settings screen, common widgets, and overall frontend functionality.
"""

import sys
import os

# Add frontend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_settings_screen_import():
    """Test Settings screen imports correctly."""
    from ui.screens.settings import SettingsScreen
    assert SettingsScreen is not None


def test_widgets_import():
    """Test common widgets import correctly."""
    from ui.widgets.common import (
        LoadingOverlay, LoadingButton, StatusMessage,
        ValidatedLineEdit, ConfirmDialog, ToastNotification
    )
    assert LoadingOverlay is not None
    assert LoadingButton is not None
    assert StatusMessage is not None
    assert ValidatedLineEdit is not None
    assert ConfirmDialog is not None
    assert ToastNotification is not None


def test_all_screens_import():
    """Test all screen imports."""
    from ui.screens.dashboard import DashboardScreen
    from ui.screens.login import LoginScreen
    from ui.screens.settings import SettingsScreen
    from ui.screens.field_management import FieldManagementScreen
    from ui.screens.equipment_management import EquipmentManagementScreen
    from ui.screens.task_management import TaskManagementScreen
    from ui.screens.inventory_management import InventoryManagementScreen
    from ui.screens.yield_response import YieldResponseScreen

    assert DashboardScreen is not None
    assert LoginScreen is not None
    assert SettingsScreen is not None
    assert FieldManagementScreen is not None
    assert EquipmentManagementScreen is not None
    assert TaskManagementScreen is not None
    assert InventoryManagementScreen is not None
    assert YieldResponseScreen is not None


def test_offline_integration():
    """Test offline components work together."""
    from database.local_db import get_local_db
    from core.calculations.yield_response import get_offline_yield_calculator
    from core.calculations.spray_timing import get_offline_spray_calculator, WeatherCondition

    # Test database
    db = get_local_db()
    stats = db.get_stats()
    assert stats is not None

    # Test offline calculator
    calc = get_offline_yield_calculator()
    result = calc.calculate_eor('corn', 'N', 0.50, 5.00, 200)
    assert result is not None
    assert result.eor > 0

    # Test spray calculator
    spray = get_offline_spray_calculator()
    weather = WeatherCondition(temperature_f=75, wind_speed_mph=5, humidity_pct=60)
    eval_result = spray.evaluate_conditions(weather)
    assert eval_result is not None


def test_api_client_offline():
    """Test API client offline methods."""
    from api.client import get_api_client, APIResponse

    get_api_client()

    # Test that offline_error works
    response = APIResponse.offline_error("Test offline message")
    assert not response.success
    assert response.status_code == 0
    assert "offline" in response.error_message.lower()


def test_config_and_settings():
    """Test configuration and settings."""
    from config import get_settings, APP_VERSION, USER_DATA_DIR

    settings = get_settings()
    assert APP_VERSION is not None
    assert USER_DATA_DIR is not None
    assert settings.region is not None
    assert settings.offline is not None


def run_all_tests():
    """Run all Phase 9 tests."""
    print("=" * 50)
    print("Phase 9 Integration Tests")
    print("=" * 50)

    tests = [
        ("Settings Screen Import", test_settings_screen_import),
        ("Common Widgets Import", test_widgets_import),
        ("All Screens Import", test_all_screens_import),
        ("Offline Integration", test_offline_integration),
        ("API Client Offline", test_api_client_offline),
        ("Config and Settings", test_config_and_settings),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n{name}:")
        try:
            test_func()
            print("  OK")
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
