"""
AgTools API Client Package

HTTP client for communicating with the FastAPI backend.
"""

from api.client import (
    APIClient,
    APIResponse,
    APIError,
    ConnectionError,
    ValidationError,
    NotFoundError,
    ServerError,
    get_api_client,
    reset_api_client,
)
from api.yield_response_api import YieldResponseAPI, get_yield_response_api
from api.spray_api import SprayTimingAPI, get_spray_timing_api
from api.pricing_api import PricingAPI, get_pricing_api
from api.cost_optimizer_api import CostOptimizerAPI, get_cost_optimizer_api
from api.identification_api import IdentificationAPI, get_identification_api
from api.auth_api import AuthAPI, get_auth_api, AuthToken, UserInfo, LoginResult
from api.task_api import TaskAPI, TaskInfo, get_task_api
from api.field_api import FieldAPI, FieldInfo, FieldSummary, get_field_api
from api.operations_api import OperationsAPI, OperationInfo, OperationsSummary, FieldOperationHistory, get_operations_api
from api.equipment_api import (
    EquipmentAPI, EquipmentInfo, MaintenanceInfo, MaintenanceAlert,
    EquipmentUsage, EquipmentSummary, get_equipment_api
)
from api.inventory_api import (
    InventoryAPI, InventoryItem, InventoryTransaction, InventoryAlert,
    InventorySummary, get_inventory_api
)
from api.reports_api import (
    ReportsAPI, OperationsReport, FinancialReport, EquipmentReport,
    InventoryReport, FieldPerformanceReport, DashboardSummary, get_reports_api
)

__all__ = [
    # Base client
    "APIClient",
    "APIResponse",
    "APIError",
    "ConnectionError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    "get_api_client",
    "reset_api_client",
    # Yield Response
    "YieldResponseAPI",
    "get_yield_response_api",
    # Spray Timing
    "SprayTimingAPI",
    "get_spray_timing_api",
    # Pricing
    "PricingAPI",
    "get_pricing_api",
    # Cost Optimizer
    "CostOptimizerAPI",
    "get_cost_optimizer_api",
    # Identification
    "IdentificationAPI",
    "get_identification_api",
    # Authentication
    "AuthAPI",
    "get_auth_api",
    "AuthToken",
    "UserInfo",
    "LoginResult",
    # Task Management
    "TaskAPI",
    "TaskInfo",
    "get_task_api",
    # Field Management
    "FieldAPI",
    "FieldInfo",
    "FieldSummary",
    "get_field_api",
    # Operations
    "OperationsAPI",
    "OperationInfo",
    "OperationsSummary",
    "FieldOperationHistory",
    "get_operations_api",
    # Equipment Management
    "EquipmentAPI",
    "EquipmentInfo",
    "MaintenanceInfo",
    "MaintenanceAlert",
    "EquipmentUsage",
    "EquipmentSummary",
    "get_equipment_api",
    # Inventory Management
    "InventoryAPI",
    "InventoryItem",
    "InventoryTransaction",
    "InventoryAlert",
    "InventorySummary",
    "get_inventory_api",
    # Reports
    "ReportsAPI",
    "OperationsReport",
    "FinancialReport",
    "EquipmentReport",
    "InventoryReport",
    "FieldPerformanceReport",
    "DashboardSummary",
    "get_reports_api",
]
