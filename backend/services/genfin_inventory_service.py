"""
GenFin Inventory & Items Service - Complete Inventory Management like QuickBooks
Full inventory tracking, item types, COGS, assemblies, reorder points
SQLite-backed persistence
"""

from datetime import datetime, date
from typing import Dict, List, Optional
from enum import Enum
import uuid
import sqlite3


class ItemType(Enum):
    """QuickBooks-style item types"""
    SERVICE = "service"  # Services you sell
    INVENTORY = "inventory"  # Items you track quantity
    NON_INVENTORY = "non_inventory"  # Items you don't track quantity
    OTHER_CHARGE = "other_charge"  # Shipping, handling, etc.
    SUBTOTAL = "subtotal"  # Subtotal line item
    GROUP = "group"  # Group of items
    DISCOUNT = "discount"  # Discount line item
    PAYMENT = "payment"  # Payment item
    SALES_TAX_ITEM = "sales_tax_item"  # Sales tax
    SALES_TAX_GROUP = "sales_tax_group"  # Group of taxes
    ASSEMBLY = "assembly"  # Built from other items


class InventoryValuationMethod(Enum):
    """Inventory valuation methods"""
    FIFO = "fifo"  # First In, First Out
    LIFO = "lifo"  # Last In, First Out
    AVERAGE = "average"  # Weighted Average Cost


class AdjustmentType(Enum):
    """Inventory adjustment types"""
    QUANTITY = "quantity"  # Quantity adjustment
    VALUE = "value"  # Value adjustment
    SHRINKAGE = "shrinkage"  # Loss/theft
    DAMAGE = "damage"  # Damaged goods
    RECOUNT = "recount"  # Physical count correction


class GenFinInventoryService:
    """
    GenFin Inventory & Items Service - SQLite backed

    Complete QuickBooks-like inventory management:
    - Multiple item types (service, inventory, non-inventory, group, assembly, etc.)
    - Quantity tracking with FIFO/LIFO/Average costing
    - Automatic COGS calculation
    - Assemblies/Bill of Materials
    - Reorder points and alerts
    - Physical inventory counts
    - Price levels for customer pricing
    - Sales tax items
    """

    _instance = None

    def __new__(cls, db_path: str = "agtools.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "agtools.db"):
        if self._initialized:
            return
        self.db_path = db_path
        self._init_tables()
        self._initialize_default_tax_codes()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_items (
                    item_id TEXT PRIMARY KEY,
                    item_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    sku TEXT DEFAULT '',
                    barcode TEXT DEFAULT '',
                    manufacturer_part_number TEXT DEFAULT '',
                    sales_price REAL DEFAULT 0.0,
                    cost REAL DEFAULT 0.0,
                    markup_percent REAL DEFAULT 0.0,
                    quantity_on_hand REAL DEFAULT 0.0,
                    quantity_on_order REAL DEFAULT 0.0,
                    quantity_on_sales_order REAL DEFAULT 0.0,
                    reorder_point REAL DEFAULT 0.0,
                    reorder_quantity REAL DEFAULT 0.0,
                    valuation_method TEXT DEFAULT 'average',
                    average_cost REAL DEFAULT 0.0,
                    asset_value REAL DEFAULT 0.0,
                    income_account_id TEXT,
                    expense_account_id TEXT,
                    asset_account_id TEXT,
                    category TEXT DEFAULT '',
                    subcategory TEXT DEFAULT '',
                    is_taxable INTEGER DEFAULT 1,
                    tax_code TEXT DEFAULT '',
                    preferred_vendor_id TEXT,
                    purchase_description TEXT DEFAULT '',
                    purchase_cost REAL DEFAULT 0.0,
                    unit_of_measure TEXT DEFAULT 'each',
                    purchase_uom TEXT DEFAULT '',
                    uom_conversion REAL DEFAULT 1.0,
                    discount_percent REAL DEFAULT 0.0,
                    discount_amount REAL DEFAULT 0.0,
                    tax_rate REAL DEFAULT 0.0,
                    tax_agency_id TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_purchasable INTEGER DEFAULT 1,
                    is_sellable INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Item components (for assemblies/groups)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_item_components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL,
                    component_item_id TEXT NOT NULL,
                    quantity REAL DEFAULT 1.0,
                    FOREIGN KEY (item_id) REFERENCES genfin_items (item_id)
                )
            """)

            # Inventory lots for FIFO/LIFO
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_inventory_lots (
                    lot_id TEXT PRIMARY KEY,
                    item_id TEXT NOT NULL,
                    received_date TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    cost_per_unit REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    remaining_quantity REAL NOT NULL,
                    vendor_id TEXT,
                    po_number TEXT DEFAULT '',
                    lot_number TEXT DEFAULT '',
                    expiration_date TEXT,
                    location TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (item_id) REFERENCES genfin_items (item_id)
                )
            """)

            # Inventory adjustments
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_inventory_adjustments (
                    adjustment_id TEXT PRIMARY KEY,
                    adjustment_date TEXT NOT NULL,
                    adjustment_type TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    quantity_change REAL DEFAULT 0.0,
                    value_change REAL DEFAULT 0.0,
                    old_quantity REAL DEFAULT 0.0,
                    new_quantity REAL DEFAULT 0.0,
                    old_value REAL DEFAULT 0.0,
                    new_value REAL DEFAULT 0.0,
                    reason TEXT DEFAULT '',
                    reference_number TEXT DEFAULT '',
                    adjustment_account_id TEXT,
                    created_by TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (item_id) REFERENCES genfin_items (item_id)
                )
            """)

            # Physical inventory counts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_physical_counts (
                    count_id TEXT PRIMARY KEY,
                    count_date TEXT NOT NULL,
                    location TEXT DEFAULT '',
                    status TEXT DEFAULT 'in_progress',
                    total_items INTEGER DEFAULT 0,
                    items_counted INTEGER DEFAULT 0,
                    items_with_variance INTEGER DEFAULT 0,
                    total_variance_value REAL DEFAULT 0.0,
                    counted_by TEXT DEFAULT '',
                    verified_by TEXT DEFAULT '',
                    posted_at TEXT,
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Physical count items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_physical_count_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    count_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    item_name TEXT DEFAULT '',
                    sku TEXT DEFAULT '',
                    expected_quantity REAL DEFAULT 0.0,
                    counted_quantity REAL,
                    variance REAL,
                    adjusted INTEGER DEFAULT 0,
                    FOREIGN KEY (count_id) REFERENCES genfin_physical_counts (count_id)
                )
            """)

            # Price levels
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_price_levels (
                    price_level_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    price_level_type TEXT DEFAULT 'fixed',
                    adjust_percent REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)

            # Price level item prices
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_price_level_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    price_level_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    custom_price REAL NOT NULL,
                    FOREIGN KEY (price_level_id) REFERENCES genfin_price_levels (price_level_id)
                )
            """)

            # Tax codes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_tax_codes (
                    tax_code_id TEXT PRIMARY KEY,
                    code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    is_taxable INTEGER DEFAULT 1,
                    tax_rate REAL DEFAULT 0.0,
                    tax_agency TEXT DEFAULT '',
                    is_active INTEGER DEFAULT 1
                )
            """)

            conn.commit()

    def _initialize_default_tax_codes(self):
        """Initialize default tax codes if not exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if tax codes already exist
            cursor.execute("SELECT COUNT(*) as count FROM genfin_tax_codes")
            if cursor.fetchone()['count'] > 0:
                return

            default_codes = [
                {"code": "TAX", "name": "Taxable", "is_taxable": True, "rate": 0.0},
                {"code": "NON", "name": "Non-Taxable", "is_taxable": False, "rate": 0.0},
                {"code": "OUT", "name": "Out of State", "is_taxable": False, "rate": 0.0},
            ]

            for tc in default_codes:
                cursor.execute("""
                    INSERT INTO genfin_tax_codes (
                        tax_code_id, code, name, is_taxable, tax_rate, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (str(uuid.uuid4()), tc["code"], tc["name"], 1 if tc["is_taxable"] else 0, tc["rate"], 1))

            conn.commit()

    # ==================== ITEM MANAGEMENT ====================

    def create_item(
        self,
        item_type: str,
        name: str,
        description: str = "",
        sku: str = "",
        sales_price: float = 0.0,
        cost: float = 0.0,
        quantity_on_hand: float = 0.0,
        reorder_point: float = 0.0,
        income_account_id: Optional[str] = None,
        expense_account_id: Optional[str] = None,
        asset_account_id: Optional[str] = None,
        category: str = "",
        is_taxable: bool = True,
        preferred_vendor_id: Optional[str] = None,
        unit_of_measure: str = "each",
        **kwargs
    ) -> Dict:
        """Create a new item"""
        item_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # Calculate initial asset value for inventory items
        asset_value = 0.0
        if item_type == "inventory":
            asset_value = quantity_on_hand * cost

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_items (
                    item_id, item_type, name, description, sku, sales_price, cost,
                    average_cost, quantity_on_hand, reorder_point, income_account_id,
                    expense_account_id, asset_account_id, category, is_taxable,
                    preferred_vendor_id, unit_of_measure, asset_value,
                    barcode, manufacturer_part_number, markup_percent, quantity_on_order,
                    quantity_on_sales_order, reorder_quantity, valuation_method,
                    subcategory, tax_code, purchase_description, purchase_cost,
                    purchase_uom, uom_conversion, discount_percent, discount_amount,
                    tax_rate, tax_agency_id, is_active, is_purchasable, is_sellable,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id, item_type, name, description, sku, sales_price, cost,
                cost, quantity_on_hand, reorder_point, income_account_id,
                expense_account_id, asset_account_id, category, 1 if is_taxable else 0,
                preferred_vendor_id, unit_of_measure, asset_value,
                kwargs.get('barcode', ''), kwargs.get('manufacturer_part_number', ''),
                kwargs.get('markup_percent', 0.0), kwargs.get('quantity_on_order', 0.0),
                kwargs.get('quantity_on_sales_order', 0.0), kwargs.get('reorder_quantity', 0.0),
                kwargs.get('valuation_method', 'average'), kwargs.get('subcategory', ''),
                kwargs.get('tax_code', ''), kwargs.get('purchase_description', ''),
                kwargs.get('purchase_cost', 0.0), kwargs.get('purchase_uom', ''),
                kwargs.get('uom_conversion', 1.0), kwargs.get('discount_percent', 0.0),
                kwargs.get('discount_amount', 0.0), kwargs.get('tax_rate', 0.0),
                kwargs.get('tax_agency_id'), 1, 1, 1, now, now
            ))
            conn.commit()

        item = self.get_item(item_id)
        return {
            "success": True,
            "item_id": item_id,
            "item": item
        }

    def create_service_item(
        self,
        name: str,
        description: str = "",
        sales_price: float = 0.0,
        cost: float = 0.0,
        income_account_id: Optional[str] = None,
        expense_account_id: Optional[str] = None,
        is_taxable: bool = False
    ) -> Dict:
        """Create a service item"""
        return self.create_item(
            item_type="service",
            name=name,
            description=description,
            sales_price=sales_price,
            cost=cost,
            income_account_id=income_account_id,
            expense_account_id=expense_account_id,
            is_taxable=is_taxable
        )

    def create_inventory_item(
        self,
        name: str,
        description: str = "",
        sku: str = "",
        sales_price: float = 0.0,
        cost: float = 0.0,
        quantity_on_hand: float = 0.0,
        reorder_point: float = 0.0,
        income_account_id: Optional[str] = None,
        cogs_account_id: Optional[str] = None,
        asset_account_id: Optional[str] = None,
        preferred_vendor_id: Optional[str] = None
    ) -> Dict:
        """Create an inventory item with quantity tracking"""
        return self.create_item(
            item_type="inventory",
            name=name,
            description=description,
            sku=sku,
            sales_price=sales_price,
            cost=cost,
            quantity_on_hand=quantity_on_hand,
            reorder_point=reorder_point,
            income_account_id=income_account_id,
            expense_account_id=cogs_account_id,
            asset_account_id=asset_account_id,
            preferred_vendor_id=preferred_vendor_id
        )

    def create_assembly_item(
        self,
        name: str,
        description: str = "",
        components: List[Dict] = None,
        sales_price: float = 0.0,
        income_account_id: Optional[str] = None,
        cogs_account_id: Optional[str] = None,
        asset_account_id: Optional[str] = None
    ) -> Dict:
        """Create an assembly item (built from components)"""
        item_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # Calculate cost from components
        total_cost = 0.0
        if components:
            for comp in components:
                comp_item = self.get_item(comp.get("item_id"))
                if comp_item:
                    total_cost += comp_item.get("cost", 0) * comp.get("quantity", 1)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert item
            cursor.execute("""
                INSERT INTO genfin_items (
                    item_id, item_type, name, description, sales_price, cost,
                    average_cost, income_account_id, expense_account_id, asset_account_id,
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id, "assembly", name, description, sales_price, total_cost,
                total_cost, income_account_id, cogs_account_id, asset_account_id,
                1, now, now
            ))

            # Insert components
            if components:
                for comp in components:
                    cursor.execute("""
                        INSERT INTO genfin_item_components (item_id, component_item_id, quantity)
                        VALUES (?, ?, ?)
                    """, (item_id, comp.get("item_id"), comp.get("quantity", 1)))

            conn.commit()

        return {
            "success": True,
            "item_id": item_id,
            "item": self.get_item(item_id),
            "component_cost": total_cost
        }

    def create_group_item(
        self,
        name: str,
        description: str = "",
        items: List[Dict] = None,
        print_items_on_forms: bool = True
    ) -> Dict:
        """Create a group item (bundle of items)"""
        item_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # Calculate total price and cost
        total_price = 0.0
        total_cost = 0.0
        if items:
            for i in items:
                sub_item = self.get_item(i.get("item_id"))
                if sub_item:
                    qty = i.get("quantity", 1)
                    total_price += sub_item.get("sales_price", 0) * qty
                    total_cost += sub_item.get("cost", 0) * qty

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert item
            cursor.execute("""
                INSERT INTO genfin_items (
                    item_id, item_type, name, description, sales_price, cost,
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item_id, "group", name, description, total_price, total_cost, 1, now, now))

            # Insert components
            if items:
                for i in items:
                    cursor.execute("""
                        INSERT INTO genfin_item_components (item_id, component_item_id, quantity)
                        VALUES (?, ?, ?)
                    """, (item_id, i.get("item_id"), i.get("quantity", 1)))

            conn.commit()

        return {
            "success": True,
            "item_id": item_id,
            "item": self.get_item(item_id),
            "total_price": total_price,
            "total_cost": total_cost
        }

    def create_discount_item(
        self,
        name: str,
        description: str = "",
        discount_percent: float = 0.0,
        discount_amount: float = 0.0,
        income_account_id: Optional[str] = None
    ) -> Dict:
        """Create a discount item"""
        item_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_items (
                    item_id, item_type, name, description, discount_percent,
                    discount_amount, income_account_id, is_taxable, is_active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item_id, "discount", name, description, discount_percent,
                  discount_amount, income_account_id, 0, 1, now, now))
            conn.commit()

        return {
            "success": True,
            "item_id": item_id,
            "item": self.get_item(item_id)
        }

    def create_sales_tax_item(
        self,
        name: str,
        description: str = "",
        tax_rate: float = 0.0,
        tax_agency: str = ""
    ) -> Dict:
        """Create a sales tax item"""
        item_id = str(uuid.uuid4())
        tax_code_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert item
            cursor.execute("""
                INSERT INTO genfin_items (
                    item_id, item_type, name, description, tax_rate, is_taxable,
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item_id, "sales_tax_item", name, description, tax_rate, 0, 1, now, now))

            # Insert tax code
            cursor.execute("""
                INSERT INTO genfin_tax_codes (
                    tax_code_id, code, name, description, is_taxable, tax_rate,
                    tax_agency, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (tax_code_id, name[:3].upper(), name, description, 1, tax_rate, tax_agency, 1))

            conn.commit()

        return {
            "success": True,
            "item_id": item_id,
            "item": self.get_item(item_id),
            "tax_code_id": tax_code_id
        }

    def update_item(self, item_id: str, **kwargs) -> Dict:
        """Update an item"""
        item = self.get_item(item_id)
        if not item:
            return {"success": False, "error": "Item not found"}

        # Build update statement
        updates = []
        values = []

        field_mapping = {
            'name': 'name', 'description': 'description', 'sku': 'sku',
            'barcode': 'barcode', 'sales_price': 'sales_price', 'cost': 'cost',
            'markup_percent': 'markup_percent', 'quantity_on_hand': 'quantity_on_hand',
            'quantity_on_order': 'quantity_on_order', 'reorder_point': 'reorder_point',
            'reorder_quantity': 'reorder_quantity', 'average_cost': 'average_cost',
            'asset_value': 'asset_value', 'income_account_id': 'income_account_id',
            'expense_account_id': 'expense_account_id', 'asset_account_id': 'asset_account_id',
            'category': 'category', 'subcategory': 'subcategory', 'is_taxable': 'is_taxable',
            'tax_code': 'tax_code', 'preferred_vendor_id': 'preferred_vendor_id',
            'unit_of_measure': 'unit_of_measure', 'is_active': 'is_active'
        }

        for key, value in kwargs.items():
            if key in field_mapping and value is not None:
                if key in ['is_taxable', 'is_active']:
                    value = 1 if value else 0
                updates.append(f"{field_mapping[key]} = ?")
                values.append(value)

        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(item_id)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE genfin_items SET {', '.join(updates)} WHERE item_id = ?",
                    values
                )
                conn.commit()

        return {
            "success": True,
            "item": self.get_item(item_id)
        }

    def get_item(self, item_id: str) -> Optional[Dict]:
        """Get item by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_items WHERE item_id = ? AND is_active = 1",
                (item_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_item(row, cursor)
        return None

    def delete_item(self, item_id: str) -> bool:
        """Delete an item (soft delete)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE genfin_items SET is_active = 0, updated_at = ? WHERE item_id = ?",
                (datetime.now().isoformat(), item_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_items(
        self,
        item_type: Optional[str] = None,
        category: Optional[str] = None,
        active_only: bool = True,
        low_stock_only: bool = False
    ) -> List[Dict]:
        """List items with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_items WHERE 1=1"
            params = []

            if active_only:
                query += " AND is_active = 1"
            if item_type:
                query += " AND item_type = ?"
                params.append(item_type)
            if category:
                query += " AND category = ?"
                params.append(category)
            if low_stock_only:
                query += " AND item_type = 'inventory' AND quantity_on_hand <= reorder_point AND reorder_point > 0"

            query += " ORDER BY name"

            cursor.execute(query, params)
            return [self._row_to_item(row, cursor) for row in cursor.fetchall()]

    def search_items(self, query: str) -> List[Dict]:
        """Search items by name, SKU, or description"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT * FROM genfin_items
                WHERE is_active = 1 AND (
                    name LIKE ? OR sku LIKE ? OR description LIKE ?
                )
                ORDER BY name
            """, (search_term, search_term, search_term))
            return [self._row_to_item(row, cursor) for row in cursor.fetchall()]

    def _row_to_item(self, row: sqlite3.Row, cursor: sqlite3.Cursor) -> Dict:
        """Convert item row to dictionary"""
        result = {
            "item_id": row['item_id'],
            "item_type": row['item_type'],
            "name": row['name'],
            "description": row['description'] or '',
            "sku": row['sku'] or '',
            "barcode": row['barcode'] or '',
            "sales_price": row['sales_price'] or 0.0,
            "cost": row['cost'] or 0.0,
            "category": row['category'] or '',
            "subcategory": row['subcategory'] or '',
            "is_taxable": bool(row['is_taxable']),
            "unit_of_measure": row['unit_of_measure'] or 'each',
            "income_account_id": row['income_account_id'],
            "expense_account_id": row['expense_account_id'],
            "is_active": bool(row['is_active']),
            "created_at": row['created_at']
        }

        # Add inventory-specific fields
        if row['item_type'] == 'inventory':
            result.update({
                "quantity_on_hand": row['quantity_on_hand'] or 0.0,
                "quantity_on_order": row['quantity_on_order'] or 0.0,
                "reorder_point": row['reorder_point'] or 0.0,
                "average_cost": round(row['average_cost'] or 0.0, 4),
                "asset_value": round(row['asset_value'] or 0.0, 2),
                "valuation_method": row['valuation_method'] or 'average',
                "asset_account_id": row['asset_account_id'],
                "preferred_vendor_id": row['preferred_vendor_id']
            })

        # Add components for assembly/group
        if row['item_type'] in ['assembly', 'group']:
            cursor.execute(
                "SELECT component_item_id, quantity FROM genfin_item_components WHERE item_id = ?",
                (row['item_id'],)
            )
            result["components"] = [
                {"item_id": c['component_item_id'], "quantity": c['quantity']}
                for c in cursor.fetchall()
            ]

        # Add discount fields
        if row['item_type'] == 'discount':
            result.update({
                "discount_percent": row['discount_percent'] or 0.0,
                "discount_amount": row['discount_amount'] or 0.0
            })

        # Add tax fields
        if row['item_type'] == 'sales_tax_item':
            result["tax_rate"] = row['tax_rate'] or 0.0

        return result

    # ==================== INVENTORY OPERATIONS ====================

    def receive_inventory(
        self,
        item_id: str,
        quantity: float,
        cost_per_unit: float,
        received_date: str,
        vendor_id: Optional[str] = None,
        po_number: str = "",
        lot_number: str = "",
        location: str = ""
    ) -> Dict:
        """Receive inventory (from purchase)"""
        item = self.get_item(item_id)
        if not item:
            return {"success": False, "error": "Item not found"}

        if item["item_type"] != "inventory":
            return {"success": False, "error": "Item is not an inventory item"}

        lot_id = str(uuid.uuid4())
        total_cost = quantity * cost_per_unit
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert lot
            cursor.execute("""
                INSERT INTO genfin_inventory_lots (
                    lot_id, item_id, received_date, quantity, cost_per_unit,
                    total_cost, remaining_quantity, vendor_id, po_number,
                    lot_number, location, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lot_id, item_id, received_date, quantity, cost_per_unit,
                total_cost, quantity, vendor_id, po_number, lot_number,
                location, now, 1
            ))

            # Update item quantities and average cost
            old_qty = item["quantity_on_hand"]
            old_value = item.get("asset_value", 0.0)

            new_qty = old_qty + quantity
            new_value = old_value + total_cost
            new_avg_cost = new_value / new_qty if new_qty > 0 else cost_per_unit

            cursor.execute("""
                UPDATE genfin_items
                SET quantity_on_hand = ?, asset_value = ?, average_cost = ?, updated_at = ?
                WHERE item_id = ?
            """, (new_qty, new_value, new_avg_cost, now, item_id))

            conn.commit()

        return {
            "success": True,
            "lot_id": lot_id,
            "new_quantity": new_qty,
            "new_average_cost": round(new_avg_cost, 4),
            "new_asset_value": round(new_value, 2)
        }

    def sell_inventory(
        self,
        item_id: str,
        quantity: float,
        sale_date: str
    ) -> Dict:
        """Sell inventory (reduce quantity, calculate COGS)"""
        item = self.get_item(item_id)
        if not item:
            return {"success": False, "error": "Item not found"}

        if item["item_type"] != "inventory":
            return {"success": False, "error": "Item is not an inventory item"}

        if item["quantity_on_hand"] < quantity:
            return {"success": False, "error": "Insufficient quantity on hand"}

        # Calculate COGS based on valuation method
        valuation = item.get("valuation_method", "average")
        if valuation == "average":
            cogs = quantity * item.get("average_cost", 0)
        elif valuation == "fifo":
            cogs = self._calculate_fifo_cogs(item_id, quantity)
        else:  # lifo
            cogs = self._calculate_lifo_cogs(item_id, quantity)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            new_qty = item["quantity_on_hand"] - quantity
            new_value = item.get("asset_value", 0) - cogs

            cursor.execute("""
                UPDATE genfin_items
                SET quantity_on_hand = ?, asset_value = ?, updated_at = ?
                WHERE item_id = ?
            """, (new_qty, new_value, datetime.now().isoformat(), item_id))

            conn.commit()

        return {
            "success": True,
            "quantity_sold": quantity,
            "cogs": round(cogs, 2),
            "remaining_quantity": new_qty,
            "remaining_value": round(new_value, 2)
        }

    def _calculate_fifo_cogs(self, item_id: str, quantity: float) -> float:
        """Calculate COGS using FIFO method"""
        cogs = 0.0
        remaining = quantity

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT lot_id, remaining_quantity, cost_per_unit
                FROM genfin_inventory_lots
                WHERE item_id = ? AND remaining_quantity > 0 AND is_active = 1
                ORDER BY received_date ASC
            """, (item_id,))

            for lot in cursor.fetchall():
                if remaining <= 0:
                    break

                use_qty = min(lot['remaining_quantity'], remaining)
                cogs += use_qty * lot['cost_per_unit']

                cursor.execute("""
                    UPDATE genfin_inventory_lots SET remaining_quantity = ?
                    WHERE lot_id = ?
                """, (lot['remaining_quantity'] - use_qty, lot['lot_id']))

                remaining -= use_qty

            conn.commit()

        return cogs

    def _calculate_lifo_cogs(self, item_id: str, quantity: float) -> float:
        """Calculate COGS using LIFO method"""
        cogs = 0.0
        remaining = quantity

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT lot_id, remaining_quantity, cost_per_unit
                FROM genfin_inventory_lots
                WHERE item_id = ? AND remaining_quantity > 0 AND is_active = 1
                ORDER BY received_date DESC
            """, (item_id,))

            for lot in cursor.fetchall():
                if remaining <= 0:
                    break

                use_qty = min(lot['remaining_quantity'], remaining)
                cogs += use_qty * lot['cost_per_unit']

                cursor.execute("""
                    UPDATE genfin_inventory_lots SET remaining_quantity = ?
                    WHERE lot_id = ?
                """, (lot['remaining_quantity'] - use_qty, lot['lot_id']))

                remaining -= use_qty

            conn.commit()

        return cogs

    def adjust_inventory(
        self,
        item_id: str,
        adjustment_type: str,
        adjustment_date: str,
        quantity_change: Optional[float] = None,
        value_change: Optional[float] = None,
        reason: str = "",
        adjustment_account_id: Optional[str] = None
    ) -> Dict:
        """Adjust inventory quantity or value"""
        item = self.get_item(item_id)
        if not item:
            return {"success": False, "error": "Item not found"}

        if item["item_type"] != "inventory":
            return {"success": False, "error": "Item is not an inventory item"}

        adj_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        old_qty = item["quantity_on_hand"]
        old_value = item.get("asset_value", 0)

        new_qty = old_qty
        new_value = old_value

        if quantity_change is not None:
            new_qty = old_qty + quantity_change
            if old_qty > 0:
                new_value = new_qty * item.get("average_cost", 0)
            else:
                new_value = new_qty * item.get("cost", 0)

        if value_change is not None:
            new_value = old_value + value_change

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert adjustment record
            cursor.execute("""
                INSERT INTO genfin_inventory_adjustments (
                    adjustment_id, adjustment_date, adjustment_type, item_id,
                    quantity_change, value_change, old_quantity, new_quantity,
                    old_value, new_value, reason, adjustment_account_id,
                    created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                adj_id, adjustment_date, adjustment_type, item_id,
                quantity_change or 0, value_change or 0, old_qty, new_qty,
                old_value, new_value, reason, adjustment_account_id, now, 1
            ))

            # Update item
            new_avg_cost = new_value / new_qty if new_qty > 0 else item.get("average_cost", 0)
            cursor.execute("""
                UPDATE genfin_items
                SET quantity_on_hand = ?, asset_value = ?, average_cost = ?, updated_at = ?
                WHERE item_id = ?
            """, (new_qty, new_value, new_avg_cost, now, item_id))

            conn.commit()

        return {
            "success": True,
            "adjustment_id": adj_id,
            "old_quantity": old_qty,
            "new_quantity": new_qty,
            "old_value": round(old_value, 2),
            "new_value": round(new_value, 2),
            "variance": round(new_value - old_value, 2)
        }

    def build_assembly(
        self,
        item_id: str,
        quantity_to_build: float,
        build_date: str
    ) -> Dict:
        """Build assembly items from components"""
        item = self.get_item(item_id)
        if not item:
            return {"success": False, "error": "Item not found"}

        if item["item_type"] != "assembly":
            return {"success": False, "error": "Item is not an assembly item"}

        # Check component availability
        components = item.get("components", [])
        for comp in components:
            comp_item = self.get_item(comp.get("item_id"))
            if not comp_item:
                return {"success": False, "error": f"Component not found: {comp.get('item_id')}"}

            required_qty = comp.get("quantity", 1) * quantity_to_build
            if comp_item.get("quantity_on_hand", 0) < required_qty:
                return {
                    "success": False,
                    "error": f"Insufficient quantity of {comp_item['name']}: need {required_qty}, have {comp_item.get('quantity_on_hand', 0)}"
                }

        # Consume components
        total_component_cost = 0.0
        for comp in components:
            comp_item = self.get_item(comp.get("item_id"))
            required_qty = comp.get("quantity", 1) * quantity_to_build

            result = self.sell_inventory(comp_item["item_id"], required_qty, build_date)
            if result.get("success"):
                total_component_cost += result.get("cogs", 0)

        # Add assembled items
        with self._get_connection() as conn:
            cursor = conn.cursor()

            new_qty = item.get("quantity_on_hand", 0) + quantity_to_build
            new_value = item.get("asset_value", 0) + total_component_cost
            new_avg_cost = new_value / new_qty if new_qty > 0 else 0

            cursor.execute("""
                UPDATE genfin_items
                SET quantity_on_hand = ?, asset_value = ?, average_cost = ?, updated_at = ?
                WHERE item_id = ?
            """, (new_qty, new_value, new_avg_cost, datetime.now().isoformat(), item_id))

            conn.commit()

        return {
            "success": True,
            "quantity_built": quantity_to_build,
            "component_cost": round(total_component_cost, 2),
            "cost_per_unit": round(total_component_cost / quantity_to_build, 4),
            "new_quantity": new_qty
        }

    # ==================== PHYSICAL INVENTORY ====================

    def start_physical_count(
        self,
        count_date: str,
        location: str = "",
        item_ids: List[str] = None
    ) -> Dict:
        """Start a physical inventory count"""
        count_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get inventory items to count
            if item_ids:
                placeholders = ','.join('?' * len(item_ids))
                cursor.execute(f"""
                    SELECT item_id, name, sku, quantity_on_hand
                    FROM genfin_items
                    WHERE is_active = 1 AND item_type = 'inventory' AND item_id IN ({placeholders})
                """, item_ids)
            else:
                cursor.execute("""
                    SELECT item_id, name, sku, quantity_on_hand
                    FROM genfin_items
                    WHERE is_active = 1 AND item_type = 'inventory'
                """)

            items_to_count = cursor.fetchall()

            # Insert count header
            cursor.execute("""
                INSERT INTO genfin_physical_counts (
                    count_id, count_date, location, status, total_items,
                    items_counted, items_with_variance, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (count_id, count_date, location, 'in_progress', len(items_to_count), 0, 0, now, 1))

            # Insert count items
            items_list = []
            for item in items_to_count:
                cursor.execute("""
                    INSERT INTO genfin_physical_count_items (
                        count_id, item_id, item_name, sku, expected_quantity
                    ) VALUES (?, ?, ?, ?, ?)
                """, (count_id, item['item_id'], item['name'], item['sku'] or '', item['quantity_on_hand']))

                items_list.append({
                    "item_id": item['item_id'],
                    "item_name": item['name'],
                    "sku": item['sku'] or '',
                    "expected_quantity": item['quantity_on_hand'],
                    "counted_quantity": None,
                    "variance": None,
                    "adjusted": False
                })

            conn.commit()

        return {
            "success": True,
            "count_id": count_id,
            "total_items": len(items_list),
            "items": items_list
        }

    def record_count(
        self,
        count_id: str,
        item_id: str,
        counted_quantity: float
    ) -> Dict:
        """Record a physical count for an item"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check count exists and is in progress
            cursor.execute(
                "SELECT status FROM genfin_physical_counts WHERE count_id = ? AND is_active = 1",
                (count_id,)
            )
            count = cursor.fetchone()
            if not count:
                return {"success": False, "error": "Count not found"}
            if count['status'] != 'in_progress':
                return {"success": False, "error": "Count is not in progress"}

            # Get the count item
            cursor.execute("""
                SELECT id, expected_quantity, counted_quantity
                FROM genfin_physical_count_items
                WHERE count_id = ? AND item_id = ?
            """, (count_id, item_id))
            item = cursor.fetchone()
            if not item:
                return {"success": False, "error": "Item not in count"}

            variance = counted_quantity - item['expected_quantity']
            was_not_counted = item['counted_quantity'] is None

            # Update count item
            cursor.execute("""
                UPDATE genfin_physical_count_items
                SET counted_quantity = ?, variance = ?
                WHERE count_id = ? AND item_id = ?
            """, (counted_quantity, variance, count_id, item_id))

            # Update count header stats
            if was_not_counted:
                cursor.execute("""
                    UPDATE genfin_physical_counts
                    SET items_counted = items_counted + 1
                    WHERE count_id = ?
                """, (count_id,))

            if abs(variance) > 0.001:
                cursor.execute("""
                    UPDATE genfin_physical_counts
                    SET items_with_variance = items_with_variance + 1
                    WHERE count_id = ?
                """, (count_id,))

            conn.commit()

        return {"success": True, "message": "Count recorded"}

    def post_physical_count(self, count_id: str, post_adjustments: bool = True) -> Dict:
        """Post physical count and optionally adjust inventory"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check count exists
            cursor.execute(
                "SELECT * FROM genfin_physical_counts WHERE count_id = ? AND is_active = 1",
                (count_id,)
            )
            count = cursor.fetchone()
            if not count:
                return {"success": False, "error": "Count not found"}
            if count['status'] != 'in_progress':
                return {"success": False, "error": "Count is not in progress"}

            # Get count items with variance
            cursor.execute("""
                SELECT item_id, counted_quantity, variance
                FROM genfin_physical_count_items
                WHERE count_id = ? AND counted_quantity IS NOT NULL
            """, (count_id,))

            adjustments_made = []
            total_variance_value = 0.0

            for item_count in cursor.fetchall():
                variance = item_count['variance'] or 0
                if abs(variance) > 0.001 and post_adjustments:
                    result = self.adjust_inventory(
                        item_id=item_count['item_id'],
                        adjustment_type="recount",
                        adjustment_date=count['count_date'],
                        quantity_change=variance,
                        reason=f"Physical count adjustment - Count #{count_id[:8]}"
                    )

                    if result.get("success"):
                        cursor.execute("""
                            UPDATE genfin_physical_count_items
                            SET adjusted = 1
                            WHERE count_id = ? AND item_id = ?
                        """, (count_id, item_count['item_id']))
                        adjustments_made.append(result)
                        total_variance_value += result.get("variance", 0)

            # Update count status
            cursor.execute("""
                UPDATE genfin_physical_counts
                SET status = ?, posted_at = ?, total_variance_value = ?
                WHERE count_id = ?
            """, ('posted', datetime.now().isoformat(), total_variance_value, count_id))

            conn.commit()

        return {
            "success": True,
            "count_id": count_id,
            "items_counted": count['items_counted'],
            "items_with_variance": count['items_with_variance'],
            "adjustments_made": len(adjustments_made),
            "total_variance_value": round(total_variance_value, 2)
        }

    # ==================== PRICE LEVELS ====================

    def create_price_level(
        self,
        name: str,
        price_level_type: str = "percent",
        adjust_percent: float = 0.0
    ) -> Dict:
        """Create a price level"""
        price_level_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_price_levels (
                    price_level_id, name, price_level_type, adjust_percent,
                    is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (price_level_id, name, price_level_type, adjust_percent, 1, now))
            conn.commit()

        return {
            "success": True,
            "price_level_id": price_level_id,
            "price_level": {
                "price_level_id": price_level_id,
                "name": name,
                "type": price_level_type,
                "adjust_percent": adjust_percent
            }
        }

    def set_item_price_level(
        self,
        price_level_id: str,
        item_id: str,
        custom_price: float
    ) -> Dict:
        """Set a custom price for an item in a price level"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check price level exists
            cursor.execute(
                "SELECT 1 FROM genfin_price_levels WHERE price_level_id = ? AND is_active = 1",
                (price_level_id,)
            )
            if not cursor.fetchone():
                return {"success": False, "error": "Price level not found"}

            # Check item exists
            if not self.get_item(item_id):
                return {"success": False, "error": "Item not found"}

            # Upsert price
            cursor.execute("""
                DELETE FROM genfin_price_level_items
                WHERE price_level_id = ? AND item_id = ?
            """, (price_level_id, item_id))

            cursor.execute("""
                INSERT INTO genfin_price_level_items (price_level_id, item_id, custom_price)
                VALUES (?, ?, ?)
            """, (price_level_id, item_id, custom_price))

            conn.commit()

        return {"success": True, "message": "Price set"}

    def get_item_price(self, item_id: str, price_level_id: Optional[str] = None) -> Dict:
        """Get item price, optionally with price level adjustment"""
        item = self.get_item(item_id)
        if not item:
            return {"error": "Item not found"}

        base_price = item.get("sales_price", 0)

        if price_level_id:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Check for custom price
                cursor.execute("""
                    SELECT pli.custom_price, pl.name
                    FROM genfin_price_level_items pli
                    JOIN genfin_price_levels pl ON pl.price_level_id = pli.price_level_id
                    WHERE pli.price_level_id = ? AND pli.item_id = ? AND pl.is_active = 1
                """, (price_level_id, item_id))
                custom = cursor.fetchone()

                if custom:
                    return {
                        "item_id": item_id,
                        "base_price": base_price,
                        "price_level": custom['name'],
                        "adjusted_price": custom['custom_price'],
                        "adjustment_type": "fixed"
                    }

                # Check for percentage adjustment
                cursor.execute("""
                    SELECT name, price_level_type, adjust_percent
                    FROM genfin_price_levels
                    WHERE price_level_id = ? AND is_active = 1
                """, (price_level_id,))
                level = cursor.fetchone()

                if level and level['price_level_type'] == 'percent':
                    adjustment = base_price * (level['adjust_percent'] / 100)
                    adjusted_price = base_price + adjustment
                    return {
                        "item_id": item_id,
                        "base_price": base_price,
                        "price_level": level['name'],
                        "adjusted_price": round(adjusted_price, 2),
                        "adjustment_percent": level['adjust_percent'],
                        "adjustment_type": "percent"
                    }

        return {
            "item_id": item_id,
            "base_price": base_price,
            "price_level": None,
            "adjusted_price": base_price,
            "adjustment_type": "none"
        }

    # ==================== REPORTS ====================

    def get_inventory_valuation_report(self) -> Dict:
        """Get inventory valuation summary"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT item_id, name, sku, quantity_on_hand, average_cost, asset_value
                FROM genfin_items
                WHERE is_active = 1 AND item_type = 'inventory'
                ORDER BY asset_value DESC
            """)

            items = []
            total_value = 0.0

            for row in cursor.fetchall():
                value = row['asset_value'] or 0
                total_value += value
                items.append({
                    "item_id": row['item_id'],
                    "name": row['name'],
                    "sku": row['sku'] or '',
                    "quantity_on_hand": row['quantity_on_hand'] or 0,
                    "average_cost": round(row['average_cost'] or 0, 4),
                    "asset_value": round(value, 2),
                    "percent_of_total": 0
                })

            # Calculate percentages
            for i in items:
                if total_value > 0:
                    i["percent_of_total"] = round((i["asset_value"] / total_value) * 100, 2)

        return {
            "report": "Inventory Valuation Summary",
            "as_of_date": date.today().isoformat(),
            "total_items": len(items),
            "total_value": round(total_value, 2),
            "items": items
        }

    def get_reorder_report(self) -> Dict:
        """Get items needing reorder"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT item_id, name, sku, quantity_on_hand, reorder_point,
                       reorder_quantity, cost, preferred_vendor_id
                FROM genfin_items
                WHERE is_active = 1 AND item_type = 'inventory'
                  AND reorder_point > 0 AND quantity_on_hand <= reorder_point
                ORDER BY quantity_on_hand
            """)

            items_to_reorder = []
            for row in cursor.fetchall():
                suggested_order = row['reorder_quantity'] or (row['reorder_point'] * 2)
                items_to_reorder.append({
                    "item_id": row['item_id'],
                    "name": row['name'],
                    "sku": row['sku'] or '',
                    "quantity_on_hand": row['quantity_on_hand'] or 0,
                    "reorder_point": row['reorder_point'],
                    "suggested_order": suggested_order,
                    "preferred_vendor_id": row['preferred_vendor_id'],
                    "estimated_cost": round((row['cost'] or 0) * suggested_order, 2)
                })

        return {
            "report": "Reorder Report",
            "as_of_date": date.today().isoformat(),
            "items_needing_reorder": len(items_to_reorder),
            "items": items_to_reorder
        }

    def get_inventory_stock_status(self) -> Dict:
        """Get overall inventory stock status"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    SUM(CASE WHEN quantity_on_hand > reorder_point THEN 1 ELSE 0 END) as in_stock,
                    SUM(CASE WHEN quantity_on_hand <= reorder_point AND quantity_on_hand > 0 AND reorder_point > 0 THEN 1 ELSE 0 END) as low_stock,
                    SUM(CASE WHEN quantity_on_hand <= 0 THEN 1 ELSE 0 END) as out_of_stock,
                    SUM(CASE WHEN quantity_on_order > 0 THEN 1 ELSE 0 END) as on_order,
                    COUNT(*) as total
                FROM genfin_items
                WHERE is_active = 1 AND item_type = 'inventory'
            """)
            row = cursor.fetchone()

        return {
            "in_stock": row['in_stock'] or 0,
            "low_stock": row['low_stock'] or 0,
            "out_of_stock": row['out_of_stock'] or 0,
            "on_order": row['on_order'] or 0,
            "total_inventory_items": row['total'] or 0
        }

    def list_lots(self, item_id: Optional[str] = None) -> Dict:
        """List all inventory lots, optionally filtered by item"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if item_id:
                cursor.execute("""
                    SELECT l.*, i.name as item_name
                    FROM genfin_inventory_lots l
                    JOIN genfin_items i ON i.item_id = l.item_id
                    WHERE l.is_active = 1 AND l.item_id = ?
                    ORDER BY l.received_date DESC
                """, (item_id,))
            else:
                cursor.execute("""
                    SELECT l.*, i.name as item_name
                    FROM genfin_inventory_lots l
                    JOIN genfin_items i ON i.item_id = l.item_id
                    WHERE l.is_active = 1
                    ORDER BY l.received_date DESC
                """)

            lots_list = []
            total_value = 0.0

            for row in cursor.fetchall():
                lot_value = row['remaining_quantity'] * row['cost_per_unit']
                total_value += lot_value
                lots_list.append({
                    "lot_id": row['lot_id'],
                    "item_id": row['item_id'],
                    "item_name": row['item_name'],
                    "received_date": row['received_date'],
                    "quantity": row['quantity'],
                    "remaining_quantity": row['remaining_quantity'],
                    "cost_per_unit": round(row['cost_per_unit'], 4),
                    "total_cost": round(row['total_cost'], 2),
                    "vendor_id": row['vendor_id'],
                    "po_number": row['po_number'] or '',
                    "lot_number": row['lot_number'] or '',
                    "location": row['location'] or ''
                })

        return {
            "lots": lots_list,
            "total_lots": len(lots_list),
            "total_value": round(total_value, 2)
        }

    def get_service_summary(self) -> Dict:
        """Get service summary"""
        stock_status = self.get_inventory_stock_status()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM genfin_items WHERE is_active = 1")
            total_items = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_items WHERE is_active = 1 AND item_type = 'inventory'")
            inventory_items = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_items WHERE is_active = 1 AND item_type = 'service'")
            service_items = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_items WHERE is_active = 1 AND item_type = 'assembly'")
            assemblies = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_price_levels WHERE is_active = 1")
            price_levels = cursor.fetchone()['count']

        return {
            "service": "GenFin Inventory & Items",
            "version": "2.0.0",
            "storage": "SQLite",
            "features": [
                "Multiple Item Types (Service, Inventory, Non-Inventory, etc.)",
                "Quantity Tracking with FIFO/LIFO/Average",
                "Assembly/Bill of Materials",
                "Physical Inventory Counts",
                "Price Levels",
                "Reorder Alerts",
                "COGS Calculation"
            ],
            "total_items": total_items,
            "inventory_items": inventory_items,
            "service_items": service_items,
            "assemblies": assemblies,
            "stock_status": stock_status,
            "price_levels": price_levels
        }


# Singleton instance
genfin_inventory_service = GenFinInventoryService()
