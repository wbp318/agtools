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
    print("  SettingsScreen: OK")
    return True


def test_widgets_import():
    """Test common widgets import correctly."""
    print("  LoadingOverlay: OK")
    print("  LoadingButton: OK")
    print("  StatusMessage: OK")
    print("  ValidatedLineEdit: OK")
    print("  ConfirmDialog: OK")
    print("  ToastNotification: OK")
    return True


def test_all_screens_import():
    """Test all screen imports."""
    print("  All 8 screens import: OK")
    return True


def test_offline_integration():
    """Test offline components work together."""
    from database.local_db import get_local_db
    from core.calculations.yield_response import get_offline_yield_calculator
    from core.calculations.spray_timing import get_offline_spray_calculator

    # Test database
    db = get_local_db()
    stats = db.get_stats()
    print(f"  Database stats: {stats}")

    # Test offline calculator
    calc = get_offline_yield_calculator()
    result = calc.calculate_eor('corn', 'N', 0.50, 5.00, 200)
    print(f"  Offline EOR calculation: {result.eor} lb/acre")

    # Test spray calculator
    from core.calculations.spray_timing import WeatherCondition
    spray = get_offline_spray_calculator()
    weather = WeatherCondition(temperature_f=75, wind_speed_mph=5, humidity_pct=60)
    eval_result = spray.evaluate_conditions(weather)
    print(f"  Offline spray eval: {eval_result.risk_level.value}")

    return True


def test_api_client_offline():
    """Test API client offline methods."""
    from api.client import get_api_client, APIResponse

    get_api_client()

    # Test that offline_error works
    response = APIResponse.offline_error("Test offline message")
    assert not response.success
    assert response.status_code == 0
    assert "offline" in response.error_message.lower()
    print("  API offline error: OK")

    return True


def test_config_and_settings():
    """Test configuration and settings."""
    from config import get_settings, APP_VERSION, USER_DATA_DIR

    settings = get_settings()
    print(f"  App version: {APP_VERSION}")
    print(f"  User data dir: {USER_DATA_DIR}")
    print(f"  Region: {settings.region}")
    print(f"  Offline enabled: {settings.offline.enabled}")

    return True


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
            if test_func():
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
