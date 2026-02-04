"""
Screen Tests

Tests for UI screen components - initialization, structure, and behavior.
"""

import sys
import os
import pytest

# Add frontend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PyQt6 is required for these tests
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QWidget


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestDashboardScreen:
    """Tests for Dashboard screen."""

    def test_dashboard_import(self):
        """Test Dashboard screen imports."""
        from ui.screens.dashboard import DashboardScreen
        assert DashboardScreen is not None

    def test_dashboard_initialization(self, qapp):
        """Test Dashboard screen initializes."""
        from ui.screens.dashboard import DashboardScreen

        screen = DashboardScreen()
        assert screen is not None
        assert isinstance(screen, QWidget)

    def test_dashboard_has_layout(self, qapp):
        """Test Dashboard has a layout."""
        from ui.screens.dashboard import DashboardScreen

        screen = DashboardScreen()
        assert screen.layout() is not None


class TestLoginScreen:
    """Tests for Login screen."""

    def test_login_import(self):
        """Test Login screen imports."""
        from ui.screens.login import LoginScreen
        assert LoginScreen is not None

    def test_login_initialization(self, qapp):
        """Test Login screen initializes."""
        from ui.screens.login import LoginScreen

        screen = LoginScreen()
        assert screen is not None
        assert isinstance(screen, QWidget)


class TestSettingsScreen:
    """Tests for Settings screen."""

    def test_settings_import(self):
        """Test Settings screen imports."""
        from ui.screens.settings import SettingsScreen
        assert SettingsScreen is not None

    def test_settings_initialization(self, qapp):
        """Test Settings screen initializes."""
        from ui.screens.settings import SettingsScreen

        screen = SettingsScreen()
        assert screen is not None


class TestFieldManagementScreen:
    """Tests for Field Management screen."""

    def test_field_management_import(self):
        """Test FieldManagement screen imports."""
        from ui.screens.field_management import FieldManagementScreen
        assert FieldManagementScreen is not None

    def test_field_management_initialization(self, qapp):
        """Test FieldManagement screen initializes."""
        from ui.screens.field_management import FieldManagementScreen

        screen = FieldManagementScreen()
        assert screen is not None


class TestEquipmentManagementScreen:
    """Tests for Equipment Management screen."""

    def test_equipment_management_import(self):
        """Test EquipmentManagement screen imports."""
        from ui.screens.equipment_management import EquipmentManagementScreen
        assert EquipmentManagementScreen is not None

    def test_equipment_management_initialization(self, qapp):
        """Test EquipmentManagement screen initializes."""
        from ui.screens.equipment_management import EquipmentManagementScreen

        screen = EquipmentManagementScreen()
        assert screen is not None


class TestTaskManagementScreen:
    """Tests for Task Management screen."""

    def test_task_management_import(self):
        """Test TaskManagement screen imports."""
        from ui.screens.task_management import TaskManagementScreen
        assert TaskManagementScreen is not None

    def test_task_management_initialization(self, qapp):
        """Test TaskManagement screen initializes."""
        from ui.screens.task_management import TaskManagementScreen

        screen = TaskManagementScreen()
        assert screen is not None


class TestInventoryManagementScreen:
    """Tests for Inventory Management screen."""

    def test_inventory_management_import(self):
        """Test InventoryManagement screen imports."""
        from ui.screens.inventory_management import InventoryManagementScreen
        assert InventoryManagementScreen is not None

    def test_inventory_management_initialization(self, qapp):
        """Test InventoryManagement screen initializes."""
        from ui.screens.inventory_management import InventoryManagementScreen

        screen = InventoryManagementScreen()
        assert screen is not None


class TestYieldResponseScreen:
    """Tests for Yield Response screen."""

    def test_yield_response_import(self):
        """Test YieldResponse screen imports."""
        from ui.screens.yield_response import YieldResponseScreen
        assert YieldResponseScreen is not None

    def test_yield_response_initialization(self, qapp):
        """Test YieldResponse screen initializes."""
        from ui.screens.yield_response import YieldResponseScreen

        screen = YieldResponseScreen()
        assert screen is not None


class TestSprayTimingScreen:
    """Tests for Spray Timing screen."""

    def test_spray_timing_import(self):
        """Test SprayTiming screen imports."""
        from ui.screens.spray_timing import SprayTimingScreen
        assert SprayTimingScreen is not None

    def test_spray_timing_initialization(self, qapp):
        """Test SprayTiming screen initializes."""
        from ui.screens.spray_timing import SprayTimingScreen

        screen = SprayTimingScreen()
        assert screen is not None


class TestPestIdentificationScreen:
    """Tests for Pest Identification screen."""

    def test_pest_identification_import(self):
        """Test PestIdentification screen imports."""
        from ui.screens.pest_identification import PestIdentificationScreen
        assert PestIdentificationScreen is not None

    def test_pest_identification_initialization(self, qapp):
        """Test PestIdentification screen initializes."""
        from ui.screens.pest_identification import PestIdentificationScreen

        screen = PestIdentificationScreen()
        assert screen is not None


class TestDiseaseIdentificationScreen:
    """Tests for Disease Identification screen."""

    def test_disease_identification_import(self):
        """Test DiseaseIdentification screen imports."""
        from ui.screens.disease_identification import DiseaseIdentificationScreen
        assert DiseaseIdentificationScreen is not None

    def test_disease_identification_initialization(self, qapp):
        """Test DiseaseIdentification screen initializes."""
        from ui.screens.disease_identification import DiseaseIdentificationScreen

        screen = DiseaseIdentificationScreen()
        assert screen is not None


class TestGenFinScreen:
    """Tests for GenFin accounting screen."""

    def test_genfin_import(self):
        """Test GenFin screen imports."""
        from ui.screens.genfin import GenFinScreen
        assert GenFinScreen is not None

    def test_genfin_initialization(self, qapp):
        """Test GenFin screen initializes."""
        from ui.screens.genfin import GenFinScreen

        screen = GenFinScreen()
        assert screen is not None


class TestReportsDashboardScreen:
    """Tests for Reports Dashboard screen."""

    def test_reports_dashboard_import(self):
        """Test ReportsDashboard screen imports."""
        from ui.screens.reports_dashboard import ReportsDashboardScreen
        assert ReportsDashboardScreen is not None

    def test_reports_dashboard_initialization(self, qapp):
        """Test ReportsDashboard screen initializes."""
        from ui.screens.reports_dashboard import ReportsDashboardScreen

        screen = ReportsDashboardScreen()
        assert screen is not None


class TestCropCostAnalysisScreen:
    """Tests for Crop Cost Analysis screen."""

    def test_crop_cost_analysis_import(self):
        """Test CropCostAnalysis screen imports."""
        from ui.screens.crop_cost_analysis import CropCostAnalysisScreen
        assert CropCostAnalysisScreen is not None

    def test_crop_cost_analysis_initialization(self, qapp):
        """Test CropCostAnalysis screen initializes."""
        from ui.screens.crop_cost_analysis import CropCostAnalysisScreen

        screen = CropCostAnalysisScreen()
        assert screen is not None


class TestSeedPlantingScreen:
    """Tests for Seed Planting screen."""

    def test_seed_planting_import(self):
        """Test SeedPlanting screen imports."""
        from ui.screens.seed_planting import SeedPlantingScreen
        assert SeedPlantingScreen is not None

    def test_seed_planting_initialization(self, qapp):
        """Test SeedPlanting screen initializes."""
        from ui.screens.seed_planting import SeedPlantingScreen

        screen = SeedPlantingScreen()
        assert screen is not None


class TestOperationsLogScreen:
    """Tests for Operations Log screen."""

    def test_operations_log_import(self):
        """Test OperationsLog screen imports."""
        from ui.screens.operations_log import OperationsLogScreen
        assert OperationsLogScreen is not None

    def test_operations_log_initialization(self, qapp):
        """Test OperationsLog screen initializes."""
        from ui.screens.operations_log import OperationsLogScreen

        screen = OperationsLogScreen()
        assert screen is not None


class TestCrewManagementScreen:
    """Tests for Crew Management screen."""

    def test_crew_management_import(self):
        """Test CrewManagement screen imports."""
        from ui.screens.crew_management import CrewManagementScreen
        assert CrewManagementScreen is not None

    def test_crew_management_initialization(self, qapp):
        """Test CrewManagement screen initializes."""
        from ui.screens.crew_management import CrewManagementScreen

        screen = CrewManagementScreen()
        assert screen is not None


class TestUserManagementScreen:
    """Tests for User Management screen."""

    def test_user_management_import(self):
        """Test UserManagement screen imports."""
        from ui.screens.user_management import UserManagementScreen
        assert UserManagementScreen is not None

    def test_user_management_initialization(self, qapp):
        """Test UserManagement screen initializes."""
        from ui.screens.user_management import UserManagementScreen

        screen = UserManagementScreen()
        assert screen is not None


class TestLivestockManagementScreen:
    """Tests for Livestock Management screen."""

    def test_livestock_management_import(self):
        """Test LivestockManagement screen imports."""
        from ui.screens.livestock_management import LivestockManagementScreen
        assert LivestockManagementScreen is not None

    def test_livestock_management_initialization(self, qapp):
        """Test LivestockManagement screen initializes."""
        from ui.screens.livestock_management import LivestockManagementScreen

        screen = LivestockManagementScreen()
        assert screen is not None

    def test_livestock_management_has_refresh(self, qapp):
        """Test LivestockManagement has refresh method."""
        from ui.screens.livestock_management import LivestockManagementScreen

        screen = LivestockManagementScreen()
        assert hasattr(screen, 'refresh')
        assert callable(screen.refresh)


class TestScreenRefreshMethods:
    """Tests for screen refresh functionality."""

    def test_screens_have_refresh_method(self, qapp):
        """Test that screens have refresh methods."""
        from ui.screens.dashboard import DashboardScreen
        from ui.screens.field_management import FieldManagementScreen
        from ui.screens.equipment_management import EquipmentManagementScreen

        screens = [
            DashboardScreen(),
            FieldManagementScreen(),
            EquipmentManagementScreen(),
        ]

        for screen in screens:
            assert hasattr(screen, 'refresh') or hasattr(screen, 'load_data')
