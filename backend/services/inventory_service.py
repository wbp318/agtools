"""
Inventory Service for Farm Operations Manager
Handles inventory tracking, transactions, and alerts.

AgTools v2.5.0 Phase 4
"""

import sqlite3
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional, List, Tuple

from pydantic import BaseModel, Field

from .auth_service import get_auth_service


# ============================================================================
# ENUMS
# ============================================================================

class InventoryCategory(str, Enum):
    """Categories of inventory items"""
    SEED = "seed"
    FERTILIZER = "fertilizer"
    HERBICIDE = "herbicide"
    FUNGICIDE = "fungicide"
    INSECTICIDE = "insecticide"
    ADJUVANT = "adjuvant"
    FUEL = "fuel"
    PARTS = "parts"
    SUPPLIES = "supplies"
    OTHER = "other"


class TransactionType(str, Enum):
    """Types of inventory transactions"""
    PURCHASE = "purchase"
    USAGE = "usage"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    RETURN = "return"
    WASTE = "waste"


# ============================================================================
# PYDANTIC MODELS - INVENTORY ITEMS
# ============================================================================

class InventoryItemCreate(BaseModel):
    """Create inventory item request"""
    name: str = Field(..., min_length=1, max_length=200)
    category: InventoryCategory

    # Product identification
    manufacturer: Optional[str] = Field(None, max_length=100)
    product_code: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=50)

    # Quantity
    quantity: float = Field(0, ge=0)
    unit: str = Field(..., min_length=1, max_length=50)
    min_quantity: Optional[float] = Field(None, ge=0)

    # Storage
    storage_location: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    expiration_date: Optional[date] = None

    # Cost
    unit_cost: Optional[float] = Field(None, ge=0)

    # Notes
    notes: Optional[str] = None


class InventoryItemUpdate(BaseModel):
    """Update inventory item request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[InventoryCategory] = None
    manufacturer: Optional[str] = Field(None, max_length=100)
    product_code: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=50)
    quantity: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    min_quantity: Optional[float] = Field(None, ge=0)
    storage_location: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    expiration_date: Optional[date] = None
    unit_cost: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class InventoryItemResponse(BaseModel):
    """Inventory item response"""
    id: int
    name: str
    category: InventoryCategory
    manufacturer: Optional[str]
    product_code: Optional[str]
    sku: Optional[str]
    quantity: float
    unit: str
    min_quantity: Optional[float]
    storage_location: Optional[str]
    batch_number: Optional[str]
    expiration_date: Optional[date]
    unit_cost: Optional[float]
    total_value: Optional[float]
    notes: Optional[str]
    created_by_user_id: int
    created_by_user_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Computed flags
    is_low_stock: bool = False
    is_expiring_soon: bool = False


# ============================================================================
# PYDANTIC MODELS - TRANSACTIONS
# ============================================================================

class TransactionCreate(BaseModel):
    """Create transaction request"""
    inventory_item_id: int
    transaction_type: TransactionType
    quantity: float  # Positive for additions, negative for deductions

    # Cost
    unit_cost: Optional[float] = Field(None, ge=0)
    total_cost: Optional[float] = Field(None, ge=0)

    # Reference
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[int] = None

    # Vendor info
    vendor: Optional[str] = Field(None, max_length=100)
    invoice_number: Optional[str] = Field(None, max_length=100)

    # Notes
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    """Transaction response"""
    id: int
    inventory_item_id: int
    item_name: Optional[str] = None
    transaction_type: TransactionType
    quantity: float
    unit_cost: Optional[float]
    total_cost: Optional[float]
    reference_type: Optional[str]
    reference_id: Optional[int]
    vendor: Optional[str]
    invoice_number: Optional[str]
    notes: Optional[str]
    created_by_user_id: int
    created_by_user_name: Optional[str] = None
    created_at: datetime


# ============================================================================
# PYDANTIC MODELS - SUMMARY & ALERTS
# ============================================================================

class InventorySummary(BaseModel):
    """Summary of inventory"""
    total_items: int
    items_by_category: dict
    total_value: float
    value_by_category: dict
    low_stock_count: int
    expiring_soon_count: int


class InventoryAlert(BaseModel):
    """Inventory alert (low stock or expiring)"""
    item_id: int
    item_name: str
    category: InventoryCategory
    alert_type: str  # low_stock, expiring, expired
    current_quantity: float
    min_quantity: Optional[float]
    unit: str
    expiration_date: Optional[date]
    days_until_expiration: Optional[int]
    storage_location: Optional[str]


class QuickPurchaseRequest(BaseModel):
    """Quick purchase entry"""
    inventory_item_id: int
    quantity: float = Field(..., gt=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    vendor: Optional[str] = Field(None, max_length=100)
    invoice_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class AdjustQuantityRequest(BaseModel):
    """Adjust inventory quantity"""
    inventory_item_id: int
    new_quantity: float = Field(..., ge=0)
    reason: Optional[str] = None


# ============================================================================
# INVENTORY SERVICE CLASS
# ============================================================================

class InventoryService:
    """
    Inventory service handling:
    - Inventory item CRUD
    - Transaction logging
    - Quantity tracking
    - Low stock and expiration alerts
    """

    def __init__(self, db_path: str = "agtools.db"):
        """
        Initialize inventory service.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.auth_service = get_auth_service()
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        """Initialize database tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create inventory_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                category VARCHAR(50) NOT NULL,
                manufacturer VARCHAR(100),
                product_code VARCHAR(100),
                sku VARCHAR(50),
                quantity DECIMAL(12, 3) NOT NULL DEFAULT 0,
                unit VARCHAR(50) NOT NULL,
                min_quantity DECIMAL(12, 3),
                storage_location VARCHAR(100),
                batch_number VARCHAR(100),
                expiration_date DATE,
                unit_cost DECIMAL(10, 3),
                total_value DECIMAL(12, 2),
                notes TEXT,
                created_by_user_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by_user_id) REFERENCES users(id)
            )
        """)

        # Create inventory_transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_item_id INTEGER NOT NULL,
                transaction_type VARCHAR(50) NOT NULL,
                quantity DECIMAL(12, 3) NOT NULL,
                unit_cost DECIMAL(10, 3),
                total_cost DECIMAL(12, 2),
                reference_type VARCHAR(50),
                reference_id INTEGER,
                vendor VARCHAR(100),
                invoice_number VARCHAR(100),
                notes TEXT,
                created_by_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id),
                FOREIGN KEY (created_by_user_id) REFERENCES users(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_name ON inventory_items(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_category ON inventory_items(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_location ON inventory_items(storage_location)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_expiration ON inventory_items(expiration_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_active ON inventory_items(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_item ON inventory_transactions(inventory_item_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_type ON inventory_transactions(transaction_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_date ON inventory_transactions(created_at)")

        conn.commit()
        conn.close()

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _safe_get(self, row: sqlite3.Row, key: str, default=None):
        """Safely get a value from a sqlite3.Row."""
        try:
            return row[key]
        except (KeyError, IndexError):
            return default

    def _row_to_item_response(self, row: sqlite3.Row) -> InventoryItemResponse:
        """Convert a database row to InventoryItemResponse."""
        quantity = float(row["quantity"]) if row["quantity"] else 0
        min_qty = float(row["min_quantity"]) if row["min_quantity"] else None
        unit_cost = float(row["unit_cost"]) if row["unit_cost"] else None
        total_value = quantity * unit_cost if unit_cost else None

        # Check if low stock
        is_low_stock = False
        if min_qty is not None and quantity < min_qty:
            is_low_stock = True

        # Check if expiring soon (within 30 days)
        is_expiring_soon = False
        if row["expiration_date"]:
            exp_date = row["expiration_date"]
            if isinstance(exp_date, str):
                exp_date = date.fromisoformat(exp_date)
            days_until = (exp_date - date.today()).days
            if days_until <= 30:
                is_expiring_soon = True

        return InventoryItemResponse(
            id=row["id"],
            name=row["name"],
            category=InventoryCategory(row["category"]),
            manufacturer=row["manufacturer"],
            product_code=row["product_code"],
            sku=row["sku"],
            quantity=quantity,
            unit=row["unit"],
            min_quantity=min_qty,
            storage_location=row["storage_location"],
            batch_number=row["batch_number"],
            expiration_date=row["expiration_date"],
            unit_cost=unit_cost,
            total_value=total_value,
            notes=row["notes"],
            created_by_user_id=row["created_by_user_id"],
            created_by_user_name=self._safe_get(row, "created_by_user_name"),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_low_stock=is_low_stock,
            is_expiring_soon=is_expiring_soon
        )

    def _row_to_transaction_response(self, row: sqlite3.Row) -> TransactionResponse:
        """Convert a database row to TransactionResponse."""
        return TransactionResponse(
            id=row["id"],
            inventory_item_id=row["inventory_item_id"],
            item_name=self._safe_get(row, "item_name"),
            transaction_type=TransactionType(row["transaction_type"]),
            quantity=float(row["quantity"]),
            unit_cost=float(row["unit_cost"]) if row["unit_cost"] else None,
            total_cost=float(row["total_cost"]) if row["total_cost"] else None,
            reference_type=row["reference_type"],
            reference_id=row["reference_id"],
            vendor=row["vendor"],
            invoice_number=row["invoice_number"],
            notes=row["notes"],
            created_by_user_id=row["created_by_user_id"],
            created_by_user_name=self._safe_get(row, "created_by_user_name"),
            created_at=row["created_at"]
        )

    def _update_item_total_value(self, cursor, item_id: int) -> None:
        """Update the total_value for an inventory item."""
        cursor.execute("""
            UPDATE inventory_items
            SET total_value = quantity * COALESCE(unit_cost, 0),
                updated_at = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), item_id))

    # ========================================================================
    # INVENTORY ITEM CRUD
    # ========================================================================

    def create_item(
        self,
        item_data: InventoryItemCreate,
        created_by: int
    ) -> Tuple[Optional[InventoryItemResponse], Optional[str]]:
        """Create a new inventory item."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Calculate total value
        total_value = None
        if item_data.unit_cost:
            total_value = item_data.quantity * item_data.unit_cost

        try:
            cursor.execute("""
                INSERT INTO inventory_items (
                    name, category, manufacturer, product_code, sku,
                    quantity, unit, min_quantity,
                    storage_location, batch_number, expiration_date,
                    unit_cost, total_value, notes, created_by_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_data.name,
                item_data.category.value,
                item_data.manufacturer,
                item_data.product_code,
                item_data.sku,
                item_data.quantity,
                item_data.unit,
                item_data.min_quantity,
                item_data.storage_location,
                item_data.batch_number,
                item_data.expiration_date.isoformat() if item_data.expiration_date else None,
                item_data.unit_cost,
                total_value,
                item_data.notes,
                created_by
            ))

            item_id = cursor.lastrowid
            conn.commit()

            self.auth_service.log_action(
                created_by,
                "create_inventory_item",
                f"Created inventory item: {item_data.name}"
            )

            return self.get_item_by_id(item_id), None

        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            conn.close()

    def get_item_by_id(self, item_id: int) -> Optional[InventoryItemResponse]:
        """Get inventory item by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                i.*,
                u.first_name || ' ' || u.last_name as created_by_user_name
            FROM inventory_items i
            LEFT JOIN users u ON i.created_by_user_id = u.id
            WHERE i.id = ? AND i.is_active = 1
        """, (item_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_item_response(row)
        return None

    def list_items(
        self,
        category: Optional[InventoryCategory] = None,
        search: Optional[str] = None,
        storage_location: Optional[str] = None,
        low_stock_only: bool = False,
        expiring_only: bool = False,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[InventoryItemResponse]:
        """List inventory items with filters."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                i.*,
                u.first_name || ' ' || u.last_name as created_by_user_name
            FROM inventory_items i
            LEFT JOIN users u ON i.created_by_user_id = u.id
        """

        conditions = []
        params = []

        conditions.append("i.is_active = ?")
        params.append(1 if is_active else 0)

        if category:
            conditions.append("i.category = ?")
            params.append(category.value)

        if search:
            conditions.append("(i.name LIKE ? OR i.manufacturer LIKE ? OR i.product_code LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        if storage_location:
            conditions.append("i.storage_location = ?")
            params.append(storage_location)

        if low_stock_only:
            conditions.append("i.quantity < i.min_quantity")

        if expiring_only:
            thirty_days = (date.today() + timedelta(days=30)).isoformat()
            conditions.append("i.expiration_date IS NOT NULL AND i.expiration_date <= ?")
            params.append(thirty_days)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY i.name LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_item_response(row) for row in rows]

    def update_item(
        self,
        item_id: int,
        item_data: InventoryItemUpdate,
        updated_by: int
    ) -> Tuple[Optional[InventoryItemResponse], Optional[str]]:
        """Update inventory item."""
        conn = self._get_connection()
        cursor = conn.cursor()

        updates = []
        params = []

        if item_data.name is not None:
            updates.append("name = ?")
            params.append(item_data.name)
        if item_data.category is not None:
            updates.append("category = ?")
            params.append(item_data.category.value)
        if item_data.manufacturer is not None:
            updates.append("manufacturer = ?")
            params.append(item_data.manufacturer)
        if item_data.product_code is not None:
            updates.append("product_code = ?")
            params.append(item_data.product_code)
        if item_data.sku is not None:
            updates.append("sku = ?")
            params.append(item_data.sku)
        if item_data.quantity is not None:
            updates.append("quantity = ?")
            params.append(item_data.quantity)
        if item_data.unit is not None:
            updates.append("unit = ?")
            params.append(item_data.unit)
        if item_data.min_quantity is not None:
            updates.append("min_quantity = ?")
            params.append(item_data.min_quantity)
        if item_data.storage_location is not None:
            updates.append("storage_location = ?")
            params.append(item_data.storage_location)
        if item_data.batch_number is not None:
            updates.append("batch_number = ?")
            params.append(item_data.batch_number)
        if item_data.expiration_date is not None:
            updates.append("expiration_date = ?")
            params.append(item_data.expiration_date.isoformat())
        if item_data.unit_cost is not None:
            updates.append("unit_cost = ?")
            params.append(item_data.unit_cost)
        if item_data.notes is not None:
            updates.append("notes = ?")
            params.append(item_data.notes)

        if not updates:
            return self.get_item_by_id(item_id), None

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(item_id)

        try:
            cursor.execute(
                f"UPDATE inventory_items SET {', '.join(updates)} WHERE id = ? AND is_active = 1",
                params
            )

            if cursor.rowcount == 0:
                conn.close()
                return None, "Item not found"

            # Update total value
            self._update_item_total_value(cursor, item_id)

            conn.commit()

            self.auth_service.log_action(
                updated_by,
                "update_inventory_item",
                f"Updated inventory item ID: {item_id}"
            )

            return self.get_item_by_id(item_id), None

        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            conn.close()

    def delete_item(
        self,
        item_id: int,
        deleted_by: int
    ) -> Tuple[bool, Optional[str]]:
        """Soft delete inventory item."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE inventory_items
                SET is_active = 0, updated_at = ?
                WHERE id = ? AND is_active = 1
            """, (datetime.utcnow().isoformat(), item_id))

            if cursor.rowcount == 0:
                conn.close()
                return False, "Item not found"

            conn.commit()

            self.auth_service.log_action(
                deleted_by,
                "delete_inventory_item",
                f"Deleted inventory item ID: {item_id}"
            )

            return True, None

        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    # ========================================================================
    # TRANSACTIONS
    # ========================================================================

    def record_transaction(
        self,
        trans_data: TransactionCreate,
        created_by: int
    ) -> Tuple[Optional[TransactionResponse], Optional[str]]:
        """Record an inventory transaction and update quantity."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify item exists and get current quantity
        cursor.execute("""
            SELECT id, quantity, unit_cost FROM inventory_items
            WHERE id = ? AND is_active = 1
        """, (trans_data.inventory_item_id,))
        item = cursor.fetchone()

        if not item:
            conn.close()
            return None, "Inventory item not found"

        current_qty = float(item["quantity"])
        new_qty = current_qty + trans_data.quantity

        # Prevent negative inventory
        if new_qty < 0:
            conn.close()
            return None, f"Insufficient quantity. Current: {current_qty}, Requested: {abs(trans_data.quantity)}"

        # Calculate total cost if not provided
        total_cost = trans_data.total_cost
        if total_cost is None and trans_data.unit_cost:
            total_cost = abs(trans_data.quantity) * trans_data.unit_cost

        try:
            # Insert transaction
            cursor.execute("""
                INSERT INTO inventory_transactions (
                    inventory_item_id, transaction_type, quantity,
                    unit_cost, total_cost,
                    reference_type, reference_id,
                    vendor, invoice_number, notes,
                    created_by_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trans_data.inventory_item_id,
                trans_data.transaction_type.value,
                trans_data.quantity,
                trans_data.unit_cost,
                total_cost,
                trans_data.reference_type,
                trans_data.reference_id,
                trans_data.vendor,
                trans_data.invoice_number,
                trans_data.notes,
                created_by
            ))

            trans_id = cursor.lastrowid

            # Update item quantity
            cursor.execute("""
                UPDATE inventory_items
                SET quantity = ?, updated_at = ?
                WHERE id = ?
            """, (new_qty, datetime.utcnow().isoformat(), trans_data.inventory_item_id))

            # Update total value
            self._update_item_total_value(cursor, trans_data.inventory_item_id)

            # If purchase and unit_cost provided, update item's unit_cost
            if trans_data.transaction_type == TransactionType.PURCHASE and trans_data.unit_cost:
                cursor.execute("""
                    UPDATE inventory_items SET unit_cost = ? WHERE id = ?
                """, (trans_data.unit_cost, trans_data.inventory_item_id))

            conn.commit()

            self.auth_service.log_action(
                created_by,
                "inventory_transaction",
                f"{trans_data.transaction_type.value}: {trans_data.quantity} for item ID: {trans_data.inventory_item_id}"
            )

            return self.get_transaction_by_id(trans_id), None

        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            conn.close()

    def get_transaction_by_id(self, trans_id: int) -> Optional[TransactionResponse]:
        """Get transaction by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                t.*,
                i.name as item_name,
                u.first_name || ' ' || u.last_name as created_by_user_name
            FROM inventory_transactions t
            LEFT JOIN inventory_items i ON t.inventory_item_id = i.id
            LEFT JOIN users u ON t.created_by_user_id = u.id
            WHERE t.id = ?
        """, (trans_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_transaction_response(row)
        return None

    def get_item_transactions(
        self,
        item_id: int,
        transaction_type: Optional[TransactionType] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 100
    ) -> List[TransactionResponse]:
        """Get transaction history for an item."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                t.*,
                i.name as item_name,
                u.first_name || ' ' || u.last_name as created_by_user_name
            FROM inventory_transactions t
            LEFT JOIN inventory_items i ON t.inventory_item_id = i.id
            LEFT JOIN users u ON t.created_by_user_id = u.id
            WHERE t.inventory_item_id = ?
        """

        params = [item_id]

        if transaction_type:
            query += " AND t.transaction_type = ?"
            params.append(transaction_type.value)

        if date_from:
            query += " AND DATE(t.created_at) >= ?"
            params.append(date_from.isoformat())

        if date_to:
            query += " AND DATE(t.created_at) <= ?"
            params.append(date_to.isoformat())

        query += " ORDER BY t.created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_transaction_response(row) for row in rows]

    def quick_purchase(
        self,
        purchase_data: QuickPurchaseRequest,
        created_by: int
    ) -> Tuple[Optional[InventoryItemResponse], Optional[str]]:
        """Quick purchase entry - adds quantity and records transaction."""
        trans_data = TransactionCreate(
            inventory_item_id=purchase_data.inventory_item_id,
            transaction_type=TransactionType.PURCHASE,
            quantity=purchase_data.quantity,
            unit_cost=purchase_data.unit_cost,
            vendor=purchase_data.vendor,
            invoice_number=purchase_data.invoice_number,
            notes=purchase_data.notes
        )

        trans, error = self.record_transaction(trans_data, created_by)
        if error:
            return None, error

        return self.get_item_by_id(purchase_data.inventory_item_id), None

    def adjust_quantity(
        self,
        adjust_data: AdjustQuantityRequest,
        adjusted_by: int
    ) -> Tuple[Optional[InventoryItemResponse], Optional[str]]:
        """Adjust inventory quantity (for counts, corrections)."""
        item = self.get_item_by_id(adjust_data.inventory_item_id)
        if not item:
            return None, "Item not found"

        # Calculate difference
        difference = adjust_data.new_quantity - item.quantity

        if difference == 0:
            return item, None

        trans_data = TransactionCreate(
            inventory_item_id=adjust_data.inventory_item_id,
            transaction_type=TransactionType.ADJUSTMENT,
            quantity=difference,
            notes=adjust_data.reason or "Inventory count adjustment"
        )

        trans, error = self.record_transaction(trans_data, adjusted_by)
        if error:
            return None, error

        return self.get_item_by_id(adjust_data.inventory_item_id), None

    def deduct_for_operation(
        self,
        item_id: int,
        quantity: float,
        operation_id: int,
        deducted_by: int
    ) -> Tuple[Optional[TransactionResponse], Optional[str]]:
        """Deduct inventory for a field operation."""
        trans_data = TransactionCreate(
            inventory_item_id=item_id,
            transaction_type=TransactionType.USAGE,
            quantity=-abs(quantity),  # Ensure negative
            reference_type="field_operation",
            reference_id=operation_id,
            notes="Used in field operation"
        )

        return self.record_transaction(trans_data, deducted_by)

    # ========================================================================
    # SUMMARY AND ALERTS
    # ========================================================================

    def get_inventory_summary(self, is_active: bool = True) -> InventorySummary:
        """Get summary of inventory."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get counts and values by category
        cursor.execute("""
            SELECT category, COUNT(*) as count, COALESCE(SUM(total_value), 0) as value
            FROM inventory_items WHERE is_active = ?
            GROUP BY category
        """, (1 if is_active else 0,))

        by_category = {}
        value_by_category = {}
        for row in cursor.fetchall():
            by_category[row["category"]] = row["count"]
            value_by_category[row["category"]] = float(row["value"])

        # Get totals
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COALESCE(SUM(total_value), 0) as total_value
            FROM inventory_items WHERE is_active = ?
        """, (1 if is_active else 0,))
        totals = cursor.fetchone()

        # Get low stock count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM inventory_items
            WHERE is_active = ? AND min_quantity IS NOT NULL AND quantity < min_quantity
        """, (1 if is_active else 0,))
        low_stock = cursor.fetchone()["count"]

        # Get expiring soon count (within 30 days)
        thirty_days = (date.today() + timedelta(days=30)).isoformat()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM inventory_items
            WHERE is_active = ? AND expiration_date IS NOT NULL AND expiration_date <= ?
        """, (1 if is_active else 0, thirty_days))
        expiring = cursor.fetchone()["count"]

        conn.close()

        return InventorySummary(
            total_items=totals["total"],
            items_by_category=by_category,
            total_value=float(totals["total_value"]),
            value_by_category=value_by_category,
            low_stock_count=low_stock,
            expiring_soon_count=expiring
        )

    def get_alerts(self, expiry_days: int = 30) -> List[InventoryAlert]:
        """Get inventory alerts (low stock and expiring items)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        alerts = []
        today = date.today()
        expiry_threshold = (today + timedelta(days=expiry_days)).isoformat()

        # Get low stock items
        cursor.execute("""
            SELECT id, name, category, quantity, min_quantity, unit,
                   expiration_date, storage_location
            FROM inventory_items
            WHERE is_active = 1 AND min_quantity IS NOT NULL AND quantity < min_quantity
        """)

        for row in cursor.fetchall():
            alerts.append(InventoryAlert(
                item_id=row["id"],
                item_name=row["name"],
                category=InventoryCategory(row["category"]),
                alert_type="low_stock",
                current_quantity=float(row["quantity"]),
                min_quantity=float(row["min_quantity"]),
                unit=row["unit"],
                expiration_date=row["expiration_date"],
                days_until_expiration=None,
                storage_location=row["storage_location"]
            ))

        # Get expiring items
        cursor.execute("""
            SELECT id, name, category, quantity, min_quantity, unit,
                   expiration_date, storage_location
            FROM inventory_items
            WHERE is_active = 1 AND expiration_date IS NOT NULL AND expiration_date <= ?
        """, (expiry_threshold,))

        for row in cursor.fetchall():
            exp_date = row["expiration_date"]
            if isinstance(exp_date, str):
                exp_date = date.fromisoformat(exp_date)
            days_until = (exp_date - today).days

            alert_type = "expired" if days_until < 0 else "expiring"

            alerts.append(InventoryAlert(
                item_id=row["id"],
                item_name=row["name"],
                category=InventoryCategory(row["category"]),
                alert_type=alert_type,
                current_quantity=float(row["quantity"]),
                min_quantity=float(row["min_quantity"]) if row["min_quantity"] else None,
                unit=row["unit"],
                expiration_date=exp_date,
                days_until_expiration=days_until,
                storage_location=row["storage_location"]
            ))

        conn.close()

        # Sort: expired first, then low_stock, then expiring
        alert_order = {"expired": 0, "low_stock": 1, "expiring": 2}
        alerts.sort(key=lambda a: (alert_order.get(a.alert_type, 3), a.days_until_expiration or 999))

        return alerts

    def get_categories(self) -> List[dict]:
        """Get list of inventory categories for dropdowns."""
        return [
            {"value": c.value, "label": c.value.replace("_", " ").title()}
            for c in InventoryCategory
        ]

    def get_storage_locations(self) -> List[str]:
        """Get list of unique storage locations."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT storage_location
            FROM inventory_items
            WHERE is_active = 1 AND storage_location IS NOT NULL
            ORDER BY storage_location
        """)

        locations = [row["storage_location"] for row in cursor.fetchall()]
        conn.close()

        return locations


# ============================================================================
# SINGLETON
# ============================================================================

_inventory_service: Optional[InventoryService] = None


def get_inventory_service(db_path: str = "agtools.db") -> InventoryService:
    """Get or create the inventory service singleton."""
    global _inventory_service

    if _inventory_service is None:
        _inventory_service = InventoryService(db_path)

    return _inventory_service
