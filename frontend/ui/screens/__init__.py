"""
AgTools Screen Components

Individual screens for each feature area of the application.
"""

from ui.screens.dashboard import DashboardScreen
from ui.screens.yield_response import YieldResponseScreen
from ui.screens.spray_timing import SprayTimingScreen
from ui.screens.cost_optimizer import CostOptimizerScreen
from ui.screens.pricing import PricingScreen
from ui.screens.pest_identification import PestIdentificationScreen
from ui.screens.disease_identification import DiseaseIdentificationScreen
from ui.screens.settings import SettingsScreen
from ui.screens.login import LoginScreen
from ui.screens.user_management import UserManagementScreen
from ui.screens.crew_management import CrewManagementScreen
from ui.screens.task_management import TaskManagementScreen
from ui.screens.field_management import FieldManagementScreen
from ui.screens.operations_log import OperationsLogScreen
from ui.screens.equipment_management import EquipmentManagementScreen
from ui.screens.inventory_management import InventoryManagementScreen
from ui.screens.maintenance_schedule import MaintenanceScheduleScreen
from ui.screens.reports_dashboard import ReportsDashboardScreen

__all__ = [
    "DashboardScreen",
    "YieldResponseScreen",
    "SprayTimingScreen",
    "CostOptimizerScreen",
    "PricingScreen",
    "PestIdentificationScreen",
    "DiseaseIdentificationScreen",
    "SettingsScreen",
    "LoginScreen",
    "UserManagementScreen",
    "CrewManagementScreen",
    "TaskManagementScreen",
    "FieldManagementScreen",
    "OperationsLogScreen",
    "EquipmentManagementScreen",
    "InventoryManagementScreen",
    "MaintenanceScheduleScreen",
    "ReportsDashboardScreen",
]
