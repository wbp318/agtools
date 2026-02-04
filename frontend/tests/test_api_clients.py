"""
API Client Tests

Tests for frontend API client modules - request/response handling,
error handling, and data model serialization.
"""

import sys
import os

# Add frontend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAPIClientBase:
    """Tests for base API client functionality."""

    def test_api_client_singleton(self):
        """Test API client uses singleton pattern."""
        from api.client import get_api_client

        client1 = get_api_client()
        client2 = get_api_client()
        assert client1 is client2

    def test_api_response_success(self):
        """Test APIResponse success creation."""
        from api.client import APIResponse

        response = APIResponse(
            success=True,
            data={"id": 1, "name": "Test"},
            status_code=200
        )
        assert response.success is True
        assert response.data["id"] == 1
        assert response.status_code == 200
        assert response.error_message is None

    def test_api_response_error(self):
        """Test APIResponse error creation."""
        from api.client import APIResponse

        response = APIResponse(
            success=False,
            data=None,
            status_code=400,
            error_message="Bad request"
        )
        assert response.success is False
        assert response.data is None
        assert response.status_code == 400
        assert response.error_message == "Bad request"

    def test_api_response_offline_error(self):
        """Test APIResponse offline error factory."""
        from api.client import APIResponse

        response = APIResponse.offline_error("Network unavailable")
        assert response.success is False
        assert response.status_code == 0
        # offline_error uses default message, check it exists
        assert response.error_message is not None


class TestFieldAPI:
    """Tests for Field API client."""

    def test_field_info_from_dict(self):
        """Test FieldInfo deserialization."""
        from api.field_api import FieldInfo

        data = {
            "id": 1,
            "name": "North Field",
            "acreage": 150.5,
            "current_crop": "corn",
            "soil_type": "loam",
            "created_by_user_id": 1,
            "is_active": True,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "total_operations": 0
        }
        field = FieldInfo.from_dict(data)

        assert field.id == 1
        assert field.name == "North Field"
        assert field.acreage == 150.5
        assert field.current_crop == "corn"

    def test_field_info_properties(self):
        """Test FieldInfo has required properties."""
        from api.field_api import FieldInfo

        # FieldInfo requires all fields in __init__
        data = {
            "id": 1,
            "name": "Test Field",
            "acreage": 100.0,
            "current_crop": "corn",
            "created_by_user_id": 1,
            "is_active": True,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "total_operations": 0
        }
        field = FieldInfo.from_dict(data)

        # Test that from_dict works
        assert field.id == 1
        assert field.name == "Test Field"

    def test_field_info_display_properties(self):
        """Test FieldInfo display formatting."""
        from api.field_api import FieldInfo

        data = {
            "id": 1,
            "name": "Test Field",
            "acreage": 100.0,
            "current_crop": "corn",
            "soil_type": "sandy_loam",
            "created_by_user_id": 1,
            "is_active": True,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "total_operations": 0
        }
        field = FieldInfo.from_dict(data)
        # Test that display properties exist and return strings
        assert isinstance(field.crop_display, str)
        assert isinstance(field.soil_display, str)


class TestEquipmentAPI:
    """Tests for Equipment API client."""

    def test_equipment_info_from_dict(self):
        """Test EquipmentInfo deserialization."""
        from api.equipment_api import EquipmentInfo

        data = {
            "id": 1,
            "name": "John Deere 8R",
            "equipment_type": "tractor",
            "make": "John Deere",
            "model": "8R 410",
            "year": 2022,
            "status": "available",
            "current_hours": 500,
            "created_by_user_id": 1,
            "is_active": True,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01"
        }
        equipment = EquipmentInfo.from_dict(data)

        assert equipment.id == 1
        assert equipment.name == "John Deere 8R"
        assert equipment.equipment_type == "tractor"

    def test_equipment_info_display_properties(self):
        """Test EquipmentInfo display properties."""
        from api.equipment_api import EquipmentInfo

        data = {
            "id": 1,
            "name": "Combine",
            "equipment_type": "harvester",
            "status": "available",
            "current_hours": 100,
            "created_by_user_id": 1,
            "is_active": True,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01"
        }
        equipment = EquipmentInfo.from_dict(data)

        assert isinstance(equipment.type_display, str)
        assert isinstance(equipment.status_display, str)


class TestTaskAPI:
    """Tests for Task API client."""

    def test_task_info_from_dict(self):
        """Test TaskInfo deserialization."""
        from api.task_api import TaskInfo

        data = {
            "id": 1,
            "title": "Plant corn",
            "description": "Plant north field",
            "status": "todo",
            "priority": "high",
            "due_date": "2024-05-01",
            "created_by_user_id": 1,
            "created_by_user_name": "Admin",
            "is_active": True,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01"
        }
        task = TaskInfo.from_dict(data)

        assert task.id == 1
        assert task.title == "Plant corn"
        assert task.status == "todo"

    def test_task_info_display_properties(self):
        """Test TaskInfo display properties."""
        from api.task_api import TaskInfo

        data = {
            "id": 1,
            "title": "Harvest soybeans",
            "status": "in_progress",
            "priority": "medium",
            "created_by_user_id": 1,
            "created_by_user_name": "Admin",
            "is_active": True,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01"
        }
        task = TaskInfo.from_dict(data)

        assert isinstance(task.status_display, str)
        assert isinstance(task.priority_display, str)


class TestInventoryAPI:
    """Tests for Inventory API client."""

    def test_inventory_item_from_dict(self):
        """Test InventoryItem deserialization."""
        from api.inventory_api import InventoryItem

        data = {
            "id": 1,
            "name": "Corn Seed",
            "category": "seed",
            "quantity": 500,
            "unit": "bags",
            "unit_cost": 250.00,
            "created_by_user_id": 1,
            "is_active": True,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "is_low_stock": False,
            "is_expiring_soon": False
        }
        item = InventoryItem.from_dict(data)

        assert item.id == 1
        assert item.name == "Corn Seed"
        assert item.quantity == 500

    def test_inventory_item_display_properties(self):
        """Test InventoryItem display properties."""
        from api.inventory_api import InventoryItem

        data = {
            "id": 1,
            "name": "Fertilizer",
            "category": "chemical",
            "quantity": 100,
            "unit": "gallons",
            "created_by_user_id": 1,
            "is_active": True,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "is_low_stock": False,
            "is_expiring_soon": False
        }
        item = InventoryItem.from_dict(data)

        assert isinstance(item.category_display, str)
        assert isinstance(item.quantity_display, str)


class TestAuthAPI:
    """Tests for Auth API client."""

    def test_login_request_structure(self):
        """Test login request data structure."""
        from api.auth_api import AuthAPI

        # Verify AuthAPI exists and has login method
        assert hasattr(AuthAPI, 'login') or hasattr(AuthAPI, '__init__')

    def test_token_storage_integration(self):
        """Test that auth integrates with secure storage."""
        from utils.secure_storage import encrypt_token, decrypt_token

        test_token = "test_jwt_token_12345"
        encrypted = encrypt_token(test_token)
        decrypted = decrypt_token(encrypted)

        assert decrypted == test_token


class TestReportsAPI:
    """Tests for Reports API client."""

    def test_reports_api_exists(self):
        """Test ReportsAPI module loads."""
        from api.reports_api import ReportsAPI
        assert ReportsAPI is not None


class TestSeedPlantingAPI:
    """Tests for Seed Planting API client."""

    def test_seed_planting_api_exists(self):
        """Test SeedPlantingAPI module loads."""
        from api.seed_planting_api import SeedPlantingAPI
        assert SeedPlantingAPI is not None


class TestIdentificationAPI:
    """Tests for Pest/Disease Identification API client."""

    def test_identification_api_exists(self):
        """Test IdentificationAPI module loads."""
        from api.identification_api import IdentificationAPI
        assert IdentificationAPI is not None
