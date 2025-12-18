"""
Inventory Management API Client

Handles inventory tracking, transactions, and alerts.
AgTools v2.5.0 Phase 4
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, List, Tuple, Dict, Any

from .client import APIClient, get_api_client


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class InventoryItem:
    """Inventory item information dataclass"""
    id: int
    name: str
    category: str
    manufacturer: Optional[str]
    product_code: Optional[str]
    sku: Optional[str]
    quantity: float
    unit: str
    min_quantity: Optional[float]
    storage_location: Optional[str]
    batch_number: Optional[str]
    expiration_date: Optional[str]
    unit_cost: Optional[float]
    total_value: Optional[float]
    notes: Optional[str]
    created_by_user_id: int
    created_by_user_name: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str
    is_low_stock: bool
    is_expiring_soon: bool

    @classmethod
    def from_dict(cls, data: dict) -> "InventoryItem":
        """Create InventoryItem from API response dict."""
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            category=data.get("category", "other"),
            manufacturer=data.get("manufacturer"),
            product_code=data.get("product_code"),
            sku=data.get("sku"),
            quantity=float(data.get("quantity", 0)),
            unit=data.get("unit", ""),
            min_quantity=float(data.get("min_quantity")) if data.get("min_quantity") else None,
            storage_location=data.get("storage_location"),
            batch_number=data.get("batch_number"),
            expiration_date=data.get("expiration_date"),
            unit_cost=float(data.get("unit_cost")) if data.get("unit_cost") else None,
            total_value=float(data.get("total_value")) if data.get("total_value") else None,
            notes=data.get("notes"),
            created_by_user_id=data.get("created_by_user_id", 0),
            created_by_user_name=data.get("created_by_user_name"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            is_low_stock=data.get("is_low_stock", False),
            is_expiring_soon=data.get("is_expiring_soon", False)
        )

    @property
    def category_display(self) -> str:
        """Get display-friendly category."""
        return self.category.replace("_", " ").title()

    @property
    def quantity_display(self) -> str:
        """Get formatted quantity display."""
        return f"{self.quantity:,.2f} {self.unit}"

    @property
    def value_display(self) -> str:
        """Get formatted value display."""
        if self.total_value:
            return f"${self.total_value:,.2f}"
        return "N/A"

    @property
    def unit_cost_display(self) -> str:
        """Get formatted unit cost display."""
        if self.unit_cost:
            return f"${self.unit_cost:,.2f}/{self.unit}"
        return "N/A"

    @property
    def stock_status(self) -> str:
        """Get stock status text."""
        if self.is_low_stock:
            return "Low Stock"
        return "In Stock"

    @property
    def expiry_status(self) -> str:
        """Get expiry status text."""
        if self.is_expiring_soon:
            return "Expiring Soon"
        if self.expiration_date:
            return f"Expires: {self.expiration_date}"
        return "No Expiry"


@dataclass
class InventoryTransaction:
    """Inventory transaction record"""
    id: int
    inventory_item_id: int
    item_name: Optional[str]
    transaction_type: str
    quantity: float
    unit_cost: Optional[float]
    total_cost: Optional[float]
    reference_type: Optional[str]
    reference_id: Optional[int]
    vendor: Optional[str]
    invoice_number: Optional[str]
    notes: Optional[str]
    created_by_user_id: int
    created_by_user_name: Optional[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "InventoryTransaction":
        """Create InventoryTransaction from API response dict."""
        return cls(
            id=data.get("id", 0),
            inventory_item_id=data.get("inventory_item_id", 0),
            item_name=data.get("item_name"),
            transaction_type=data.get("transaction_type", "adjustment"),
            quantity=float(data.get("quantity", 0)),
            unit_cost=float(data.get("unit_cost")) if data.get("unit_cost") else None,
            total_cost=float(data.get("total_cost")) if data.get("total_cost") else None,
            reference_type=data.get("reference_type"),
            reference_id=data.get("reference_id"),
            vendor=data.get("vendor"),
            invoice_number=data.get("invoice_number"),
            notes=data.get("notes"),
            created_by_user_id=data.get("created_by_user_id", 0),
            created_by_user_name=data.get("created_by_user_name"),
            created_at=data.get("created_at", "")
        )

    @property
    def type_display(self) -> str:
        """Get display-friendly transaction type."""
        return self.transaction_type.replace("_", " ").title()

    @property
    def quantity_display(self) -> str:
        """Get formatted quantity with sign."""
        if self.quantity > 0:
            return f"+{self.quantity:,.2f}"
        return f"{self.quantity:,.2f}"

    @property
    def cost_display(self) -> str:
        """Get formatted cost display."""
        if self.total_cost:
            return f"${self.total_cost:,.2f}"
        return "N/A"


@dataclass
class InventoryAlert:
    """Inventory alert (low stock or expiring)"""
    item_id: int
    item_name: str
    category: str
    alert_type: str  # low_stock, expiring, expired
    current_quantity: float
    min_quantity: Optional[float]
    unit: str
    expiration_date: Optional[str]
    days_until_expiration: Optional[int]
    storage_location: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "InventoryAlert":
        """Create InventoryAlert from API response dict."""
        return cls(
            item_id=data.get("item_id", 0),
            item_name=data.get("item_name", ""),
            category=data.get("category", "other"),
            alert_type=data.get("alert_type", "low_stock"),
            current_quantity=float(data.get("current_quantity", 0)),
            min_quantity=float(data.get("min_quantity")) if data.get("min_quantity") else None,
            unit=data.get("unit", ""),
            expiration_date=data.get("expiration_date"),
            days_until_expiration=data.get("days_until_expiration"),
            storage_location=data.get("storage_location")
        )

    @property
    def alert_type_display(self) -> str:
        """Get display-friendly alert type."""
        return self.alert_type.replace("_", " ").title()

    @property
    def urgency_display(self) -> str:
        """Get urgency display text."""
        if self.alert_type == "expired":
            return "EXPIRED"
        if self.alert_type == "low_stock":
            return f"Low: {self.current_quantity:,.2f} / {self.min_quantity:,.2f} {self.unit}"
        if self.days_until_expiration is not None:
            if self.days_until_expiration <= 0:
                return "Expired"
            elif self.days_until_expiration == 1:
                return "Expires tomorrow"
            else:
                return f"Expires in {self.days_until_expiration} days"
        return "Unknown"


@dataclass
class InventorySummary:
    """Summary of inventory"""
    total_items: int
    items_by_category: Dict[str, int]
    total_value: float
    value_by_category: Dict[str, float]
    low_stock_count: int
    expiring_soon_count: int

    @classmethod
    def from_dict(cls, data: dict) -> "InventorySummary":
        """Create InventorySummary from API response dict."""
        return cls(
            total_items=data.get("total_items", 0),
            items_by_category=data.get("items_by_category", {}),
            total_value=float(data.get("total_value", 0)),
            value_by_category=data.get("value_by_category", {}),
            low_stock_count=data.get("low_stock_count", 0),
            expiring_soon_count=data.get("expiring_soon_count", 0)
        )


# ============================================================================
# API CLIENT
# ============================================================================

class InventoryAPI:
    """Inventory management API client"""

    # Inventory category options
    CATEGORIES = [
        ("seed", "Seed"),
        ("fertilizer", "Fertilizer"),
        ("herbicide", "Herbicide"),
        ("fungicide", "Fungicide"),
        ("insecticide", "Insecticide"),
        ("adjuvant", "Adjuvant"),
        ("fuel", "Fuel"),
        ("parts", "Parts"),
        ("supplies", "Supplies"),
        ("other", "Other"),
    ]

    # Transaction type options
    TRANSACTION_TYPES = [
        ("purchase", "Purchase"),
        ("usage", "Usage"),
        ("adjustment", "Adjustment"),
        ("transfer", "Transfer"),
        ("return", "Return"),
        ("waste", "Waste"),
    ]

    # Common units
    UNITS = [
        "gallons",
        "quarts",
        "ounces",
        "pounds",
        "tons",
        "bags",
        "units",
        "cases",
        "liters",
        "kilograms",
        "bushels",
        "each",
    ]

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    # ========================================================================
    # INVENTORY ITEM CRUD
    # ========================================================================

    def list_items(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        storage_location: Optional[str] = None,
        low_stock_only: bool = False,
        expiring_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[InventoryItem], Optional[str]]:
        """List inventory items with optional filters."""
        params = {"limit": limit, "offset": offset}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        if storage_location:
            params["storage_location"] = storage_location
        if low_stock_only:
            params["low_stock_only"] = "true"
        if expiring_only:
            params["expiring_only"] = "true"

        response = self._client.get("/api/v1/inventory", params=params)
        if not response.success:
            return [], response.error

        return [InventoryItem.from_dict(i) for i in response.data], None

    def get_item(self, item_id: int) -> Tuple[Optional[InventoryItem], Optional[str]]:
        """Get inventory item by ID."""
        response = self._client.get(f"/api/v1/inventory/{item_id}")
        if not response.success:
            return None, response.error

        return InventoryItem.from_dict(response.data), None

    def create_item(
        self,
        name: str,
        category: str,
        unit: str,
        quantity: float = 0,
        manufacturer: Optional[str] = None,
        product_code: Optional[str] = None,
        sku: Optional[str] = None,
        min_quantity: Optional[float] = None,
        storage_location: Optional[str] = None,
        batch_number: Optional[str] = None,
        expiration_date: Optional[str] = None,
        unit_cost: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Tuple[Optional[InventoryItem], Optional[str]]:
        """Create new inventory item."""
        data = {
            "name": name,
            "category": category,
            "unit": unit,
            "quantity": quantity,
            "manufacturer": manufacturer,
            "product_code": product_code,
            "sku": sku,
            "min_quantity": min_quantity,
            "storage_location": storage_location,
            "batch_number": batch_number,
            "expiration_date": expiration_date,
            "unit_cost": unit_cost,
            "notes": notes
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = self._client.post("/api/v1/inventory", json=data)
        if not response.success:
            return None, response.error

        return InventoryItem.from_dict(response.data), None

    def update_item(
        self,
        item_id: int,
        **kwargs
    ) -> Tuple[Optional[InventoryItem], Optional[str]]:
        """Update inventory item."""
        # Remove None values
        data = {k: v for k, v in kwargs.items() if v is not None}

        response = self._client.put(f"/api/v1/inventory/{item_id}", json=data)
        if not response.success:
            return None, response.error

        return InventoryItem.from_dict(response.data), None

    def delete_item(self, item_id: int) -> Tuple[bool, Optional[str]]:
        """Delete (deactivate) inventory item."""
        response = self._client.delete(f"/api/v1/inventory/{item_id}")
        if not response.success:
            return False, response.error

        return True, None

    def get_summary(self) -> Tuple[Optional[InventorySummary], Optional[str]]:
        """Get inventory summary."""
        response = self._client.get("/api/v1/inventory/summary")
        if not response.success:
            return None, response.error

        return InventorySummary.from_dict(response.data), None

    def get_categories(self) -> Tuple[List[dict], Optional[str]]:
        """Get list of inventory categories."""
        response = self._client.get("/api/v1/inventory/categories")
        if not response.success:
            return [], response.error

        return response.data, None

    def get_storage_locations(self) -> Tuple[List[str], Optional[str]]:
        """Get list of storage locations."""
        response = self._client.get("/api/v1/inventory/locations")
        if not response.success:
            return [], response.error

        return response.data, None

    # ========================================================================
    # TRANSACTIONS
    # ========================================================================

    def record_transaction(
        self,
        inventory_item_id: int,
        transaction_type: str,
        quantity: float,
        unit_cost: Optional[float] = None,
        total_cost: Optional[float] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        vendor: Optional[str] = None,
        invoice_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[Optional[InventoryTransaction], Optional[str]]:
        """Record an inventory transaction."""
        data = {
            "inventory_item_id": inventory_item_id,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "unit_cost": unit_cost,
            "total_cost": total_cost,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "vendor": vendor,
            "invoice_number": invoice_number,
            "notes": notes
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = self._client.post("/api/v1/inventory/transaction", json=data)
        if not response.success:
            return None, response.error

        return InventoryTransaction.from_dict(response.data), None

    def get_item_transactions(
        self,
        item_id: int,
        transaction_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100
    ) -> Tuple[List[InventoryTransaction], Optional[str]]:
        """Get transaction history for an item."""
        params = {"limit": limit}
        if transaction_type:
            params["transaction_type"] = transaction_type
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = self._client.get(
            f"/api/v1/inventory/{item_id}/transactions",
            params=params
        )
        if not response.success:
            return [], response.error

        return [InventoryTransaction.from_dict(t) for t in response.data], None

    def quick_purchase(
        self,
        inventory_item_id: int,
        quantity: float,
        unit_cost: Optional[float] = None,
        vendor: Optional[str] = None,
        invoice_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[Optional[InventoryItem], Optional[str]]:
        """Quick purchase entry - adds quantity and records transaction."""
        data = {
            "inventory_item_id": inventory_item_id,
            "quantity": quantity,
            "unit_cost": unit_cost,
            "vendor": vendor,
            "invoice_number": invoice_number,
            "notes": notes
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = self._client.post("/api/v1/inventory/purchase", json=data)
        if not response.success:
            return None, response.error

        return InventoryItem.from_dict(response.data), None

    def adjust_quantity(
        self,
        inventory_item_id: int,
        new_quantity: float,
        reason: Optional[str] = None
    ) -> Tuple[Optional[InventoryItem], Optional[str]]:
        """Adjust inventory quantity (for counts, corrections)."""
        data = {
            "inventory_item_id": inventory_item_id,
            "new_quantity": new_quantity,
            "reason": reason
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = self._client.post("/api/v1/inventory/adjust", json=data)
        if not response.success:
            return None, response.error

        return InventoryItem.from_dict(response.data), None

    # ========================================================================
    # ALERTS
    # ========================================================================

    def get_alerts(
        self,
        expiry_days: int = 30
    ) -> Tuple[List[InventoryAlert], Optional[str]]:
        """Get inventory alerts (low stock and expiring items)."""
        response = self._client.get(
            "/api/v1/inventory/alerts",
            params={"expiry_days": expiry_days}
        )
        if not response.success:
            return [], response.error

        return [InventoryAlert.from_dict(a) for a in response.data], None


# ============================================================================
# SINGLETON
# ============================================================================

_inventory_api: Optional[InventoryAPI] = None


def get_inventory_api() -> InventoryAPI:
    """Get or create the inventory API singleton."""
    global _inventory_api
    if _inventory_api is None:
        _inventory_api = InventoryAPI()
    return _inventory_api
