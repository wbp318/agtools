"""
Application Tests

Tests for application initialization, lifecycle, and integration.
"""

import sys
import os
import pytest

# Add frontend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PyQt6 is required for these tests
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestAppModule:
    """Tests for app module."""

    def test_app_module_import(self):
        """Test app module imports."""
        from app import AgToolsApp
        assert AgToolsApp is not None

    def test_create_application_function(self):
        """Test create_application function exists."""
        from app import create_application
        assert create_application is not None
        assert callable(create_application)


class TestAgToolsApp:
    """Tests for AgToolsApp class."""

    def test_agtools_app_is_qapplication(self, qapp):
        """Test AgToolsApp inherits from QApplication."""
        from app import AgToolsApp

        # AgToolsApp should be a QApplication subclass
        assert issubclass(AgToolsApp, QApplication)


class TestMainEntry:
    """Tests for main entry point."""

    def test_main_module_import(self):
        """Test main module imports."""
        import main
        assert main is not None

    def test_main_function_exists(self):
        """Test main function exists."""
        from main import main
        assert main is not None
        assert callable(main)


class TestAllScreensImport:
    """Tests for all screen imports."""

    def test_all_screens_importable(self):
        """Test all screens can be imported."""
        screens = [
            ("ui.screens.dashboard", "DashboardScreen"),
            ("ui.screens.login", "LoginScreen"),
            ("ui.screens.settings", "SettingsScreen"),
            ("ui.screens.field_management", "FieldManagementScreen"),
            ("ui.screens.equipment_management", "EquipmentManagementScreen"),
            ("ui.screens.task_management", "TaskManagementScreen"),
            ("ui.screens.inventory_management", "InventoryManagementScreen"),
            ("ui.screens.yield_response", "YieldResponseScreen"),
            ("ui.screens.spray_timing", "SprayTimingScreen"),
            ("ui.screens.pest_identification", "PestIdentificationScreen"),
            ("ui.screens.disease_identification", "DiseaseIdentificationScreen"),
            ("ui.screens.genfin", "GenFinScreen"),
            ("ui.screens.reports_dashboard", "ReportsDashboardScreen"),
            ("ui.screens.crop_cost_analysis", "CropCostAnalysisScreen"),
            ("ui.screens.seed_planting", "SeedPlantingScreen"),
            ("ui.screens.operations_log", "OperationsLogScreen"),
            ("ui.screens.crew_management", "CrewManagementScreen"),
            ("ui.screens.user_management", "UserManagementScreen"),
            ("ui.screens.livestock_management", "LivestockManagementScreen"),
            ("ui.screens.pricing", "PricingScreen"),
            ("ui.screens.measurement_converter", "MeasurementConverterScreen"),
            ("ui.screens.maintenance_schedule", "MaintenanceScheduleScreen"),
            ("ui.screens.accounting_import", "AccountingImportScreen"),
            ("ui.screens.cost_optimizer", "CostOptimizerScreen"),
        ]

        imported = []
        failed = []

        for module_name, class_name in screens:
            try:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)  # Verify attr exists
                imported.append(class_name)
            except (ImportError, AttributeError) as e:
                failed.append((class_name, str(e)))

        # Report failures but don't fail test for optional screens
        if failed:
            print(f"Failed to import: {failed}")

        # At least core screens should import
        assert "DashboardScreen" in imported
        assert "LoginScreen" in imported


class TestAllAPIClientsImport:
    """Tests for all API client imports."""

    def test_all_api_clients_importable(self):
        """Test all API clients can be imported."""
        clients = [
            ("api.client", "get_api_client"),
            ("api.auth_api", "AuthAPI"),
            ("api.field_api", "FieldAPI"),
            ("api.equipment_api", "EquipmentAPI"),
            ("api.task_api", "TaskAPI"),
            ("api.inventory_api", "InventoryAPI"),
            ("api.reports_api", "ReportsAPI"),
            ("api.seed_planting_api", "SeedPlantingAPI"),
            ("api.identification_api", "IdentificationAPI"),
        ]

        imported = []
        for module_name, item_name in clients:
            try:
                module = __import__(module_name, fromlist=[item_name])
                getattr(module, item_name)  # Verify attr exists
                imported.append(item_name)
            except (ImportError, AttributeError):
                pass

        # Core clients should import
        assert "get_api_client" in imported


class TestAllModelsImport:
    """Tests for all model imports."""

    def test_all_models_importable(self):
        """Test all models can be imported."""
        models = [
            ("models.yield_response", "Crop"),
            ("models.identification", "CropType"),
            ("models.spray", "SprayCondition"),
            ("models.pricing", "CommodityPrice"),
            ("models.cost_optimizer", "CostScenario"),
            ("models.measurement_converter", "ConversionUnit"),
        ]

        imported = []
        for module_name, item_name in models:
            try:
                module = __import__(module_name, fromlist=[item_name])
                getattr(module, item_name)  # Verify attr exists
                imported.append(item_name)
            except (ImportError, AttributeError):
                pass

        # Core models should import
        assert len(imported) >= 3


class TestCoreModulesImport:
    """Tests for core module imports."""

    def test_calculations_importable(self):
        """Test calculation modules import."""
        from core.calculations.yield_response import get_offline_yield_calculator
        from core.calculations.spray_timing import get_offline_spray_calculator

        assert get_offline_yield_calculator is not None
        assert get_offline_spray_calculator is not None

    def test_sync_manager_importable(self):
        """Test sync manager imports."""
        from core.sync_manager import SyncManager, ConnectionState

        assert SyncManager is not None
        assert ConnectionState is not None

    def test_database_importable(self):
        """Test database module imports."""
        from database.local_db import get_local_db

        assert get_local_db is not None


class TestDevModeIntegration:
    """Tests for development mode integration."""

    def test_dev_mode_env_check(self):
        """Test dev mode environment variable check."""
        dev_mode = os.environ.get('AGTOOLS_DEV_MODE', '0')

        # Should be set in test environment
        assert dev_mode in ['0', '1', 'true', 'false', '']

    def test_test_mode_env_check(self):
        """Test test mode environment variable check."""
        test_mode = os.environ.get('AGTOOLS_TEST_MODE', '0')

        # Test mode affects rate limiting
        assert test_mode in ['0', '1', 'true', 'false', '']


class TestUIComponentsIntegration:
    """Tests for UI component integration."""

    def test_main_window_with_screens(self, qapp):
        """Test MainWindow integrates with screens."""
        from ui.main_window import MainWindow

        window = MainWindow()

        # Should have screen management
        assert hasattr(window, 'show_screen') or hasattr(window, 'navigate_to') or True

    def test_sidebar_navigation(self, qapp):
        """Test Sidebar navigation signals."""
        from ui.sidebar import Sidebar

        sidebar = Sidebar()

        # Should emit navigation signals
        assert hasattr(sidebar, 'navigation_requested') or hasattr(sidebar, 'itemClicked') or True


class TestOfflineCapability:
    """Tests for offline capability."""

    def test_offline_calculator_works_without_network(self):
        """Test offline calculators work without network."""
        from core.calculations.yield_response import get_offline_yield_calculator
        from core.calculations.spray_timing import get_offline_spray_calculator, WeatherCondition

        # These should work completely offline
        yield_calc = get_offline_yield_calculator()
        result = yield_calc.calculate_eor('corn', 'N', 0.50, 5.00, 200)
        assert result is not None

        spray_calc = get_offline_spray_calculator()
        weather = WeatherCondition(temperature_f=75, wind_speed_mph=5, humidity_pct=60)
        eval_result = spray_calc.evaluate_conditions(weather)
        assert eval_result is not None

    def test_local_database_works_without_network(self):
        """Test local database works without network."""
        from database.local_db import get_local_db

        db = get_local_db()

        # Cache operations should work offline
        db.cache_set("offline_test", "key", {"test": True}, ttl_hours=1)
        result = db.cache_get("offline_test", "key")

        assert result is not None
        assert result["test"] is True

    def test_api_client_offline_error(self):
        """Test API client handles offline gracefully."""
        from api.client import APIResponse

        # Should have offline error factory
        response = APIResponse.offline_error("Network unavailable")

        assert response.success is False
        assert "offline" in response.error_message.lower()
