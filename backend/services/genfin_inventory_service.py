"""
GenFin Inventory & Items Service - Complete Inventory Management like QuickBooks
Full inventory tracking, item types, COGS, assemblies, reorder points
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid


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


@dataclass
class Item:
    """Product/Service item - core of QuickBooks item system"""
    item_id: str
    item_type: ItemType
    name: str
    description: str = ""

    # Identification
    sku: str = ""
    barcode: str = ""
    manufacturer_part_number: str = ""

    # Pricing
    sales_price: float = 0.0
    cost: float = 0.0
    markup_percent: float = 0.0

    # Quantity (for inventory items)
    quantity_on_hand: float = 0.0
    quantity_on_order: float = 0.0
    quantity_on_sales_order: float = 0.0
    reorder_point: float = 0.0
    reorder_quantity: float = 0.0

    # Valuation
    valuation_method: InventoryValuationMethod = InventoryValuationMethod.AVERAGE
    average_cost: float = 0.0
    asset_value: float = 0.0

    # Accounts (for proper COGS tracking)
    income_account_id: Optional[str] = None
    expense_account_id: Optional[str] = None  # COGS for inventory
    asset_account_id: Optional[str] = None  # Inventory asset

    # Categories
    category: str = ""
    subcategory: str = ""

    # Tax
    is_taxable: bool = True
    tax_code: str = ""

    # Purchasing
    preferred_vendor_id: Optional[str] = None
    purchase_description: str = ""
    purchase_cost: float = 0.0

    # Unit of Measure
    unit_of_measure: str = "each"
    purchase_uom: str = ""
    uom_conversion: float = 1.0  # How many purchase units = 1 sale unit

    # For Group/Assembly items
    components: List[Dict] = field(default_factory=list)  # [{item_id, quantity}]

    # For Discount items
    discount_percent: float = 0.0
    discount_amount: float = 0.0

    # For Sales Tax items
    tax_rate: float = 0.0
    tax_agency_id: Optional[str] = None

    # Status
    is_active: bool = True
    is_purchasable: bool = True
    is_sellable: bool = True

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class InventoryLot:
    """Inventory lot for FIFO/LIFO tracking"""
    lot_id: str
    item_id: str
    received_date: date
    quantity: float
    cost_per_unit: float
    total_cost: float
    remaining_quantity: float
    vendor_id: Optional[str] = None
    po_number: str = ""
    lot_number: str = ""
    expiration_date: Optional[date] = None
    location: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class InventoryAdjustment:
    """Inventory adjustment record"""
    adjustment_id: str
    adjustment_date: date
    adjustment_type: AdjustmentType
    item_id: str

    quantity_change: float = 0.0
    value_change: float = 0.0

    old_quantity: float = 0.0
    new_quantity: float = 0.0
    old_value: float = 0.0
    new_value: float = 0.0

    reason: str = ""
    reference_number: str = ""
    adjustment_account_id: Optional[str] = None

    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PhysicalInventoryCount:
    """Physical inventory count worksheet"""
    count_id: str
    count_date: date
    location: str = ""
    status: str = "in_progress"  # in_progress, completed, posted

    items: List[Dict] = field(default_factory=list)
    # [{item_id, expected_quantity, counted_quantity, variance, adjusted}]

    total_items: int = 0
    items_counted: int = 0
    items_with_variance: int = 0
    total_variance_value: float = 0.0

    counted_by: str = ""
    verified_by: str = ""
    posted_at: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PriceLevel:
    """Price levels for customer-specific pricing"""
    price_level_id: str
    name: str
    price_level_type: str = "fixed"  # fixed, percent

    # For percent type
    adjust_percent: float = 0.0  # Positive = increase, negative = decrease

    # For fixed type - item-specific prices
    item_prices: Dict[str, float] = field(default_factory=dict)  # {item_id: price}

    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SalesTaxCode:
    """Sales tax code"""
    tax_code_id: str
    code: str
    name: str
    description: str = ""
    is_taxable: bool = True
    tax_rate: float = 0.0
    tax_agency: str = ""
    is_active: bool = True


class GenFinInventoryService:
    """
    GenFin Inventory & Items Service

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

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.items: Dict[str, Item] = {}
        self.lots: Dict[str, InventoryLot] = {}
        self.adjustments: Dict[str, InventoryAdjustment] = {}
        self.counts: Dict[str, PhysicalInventoryCount] = {}
        self.price_levels: Dict[str, PriceLevel] = {}
        self.tax_codes: Dict[str, SalesTaxCode] = {}

        self._initialize_default_tax_codes()
        self._initialized = True

    def _initialize_default_tax_codes(self):
        """Initialize default tax codes"""
        default_codes = [
            {"code": "TAX", "name": "Taxable", "is_taxable": True, "rate": 0.0},
            {"code": "NON", "name": "Non-Taxable", "is_taxable": False, "rate": 0.0},
            {"code": "OUT", "name": "Out of State", "is_taxable": False, "rate": 0.0},
        ]

        for tc in default_codes:
            tax_code = SalesTaxCode(
                tax_code_id=str(uuid.uuid4()),
                code=tc["code"],
                name=tc["name"],
                is_taxable=tc["is_taxable"],
                tax_rate=tc["rate"]
            )
            self.tax_codes[tax_code.tax_code_id] = tax_code

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

        # Calculate initial asset value for inventory items
        asset_value = 0.0
        if item_type == "inventory":
            asset_value = quantity_on_hand * cost

        item = Item(
            item_id=item_id,
            item_type=ItemType(item_type),
            name=name,
            description=description,
            sku=sku,
            sales_price=sales_price,
            cost=cost,
            average_cost=cost,
            quantity_on_hand=quantity_on_hand,
            reorder_point=reorder_point,
            income_account_id=income_account_id,
            expense_account_id=expense_account_id,
            asset_account_id=asset_account_id,
            category=category,
            is_taxable=is_taxable,
            preferred_vendor_id=preferred_vendor_id,
            unit_of_measure=unit_of_measure,
            asset_value=asset_value,
            **{k: v for k, v in kwargs.items() if hasattr(Item, k)}
        )

        self.items[item_id] = item

        return {
            "success": True,
            "item_id": item_id,
            "item": self._item_to_dict(item)
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

        # Calculate cost from components
        total_cost = 0.0
        if components:
            for comp in components:
                comp_item = self.items.get(comp.get("item_id"))
                if comp_item:
                    total_cost += comp_item.cost * comp.get("quantity", 1)

        item = Item(
            item_id=item_id,
            item_type=ItemType.ASSEMBLY,
            name=name,
            description=description,
            sales_price=sales_price,
            cost=total_cost,
            average_cost=total_cost,
            income_account_id=income_account_id,
            expense_account_id=cogs_account_id,
            asset_account_id=asset_account_id,
            components=components or []
        )

        self.items[item_id] = item

        return {
            "success": True,
            "item_id": item_id,
            "item": self._item_to_dict(item),
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

        # Calculate total price and cost
        total_price = 0.0
        total_cost = 0.0
        if items:
            for i in items:
                sub_item = self.items.get(i.get("item_id"))
                if sub_item:
                    qty = i.get("quantity", 1)
                    total_price += sub_item.sales_price * qty
                    total_cost += sub_item.cost * qty

        item = Item(
            item_id=item_id,
            item_type=ItemType.GROUP,
            name=name,
            description=description,
            sales_price=total_price,
            cost=total_cost,
            components=items or []
        )

        self.items[item_id] = item

        return {
            "success": True,
            "item_id": item_id,
            "item": self._item_to_dict(item),
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

        item = Item(
            item_id=item_id,
            item_type=ItemType.DISCOUNT,
            name=name,
            description=description,
            discount_percent=discount_percent,
            discount_amount=discount_amount,
            income_account_id=income_account_id,
            is_taxable=False
        )

        self.items[item_id] = item

        return {
            "success": True,
            "item_id": item_id,
            "item": self._item_to_dict(item)
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

        item = Item(
            item_id=item_id,
            item_type=ItemType.SALES_TAX_ITEM,
            name=name,
            description=description,
            tax_rate=tax_rate,
            is_taxable=False
        )

        # Also create a tax code
        tax_code = SalesTaxCode(
            tax_code_id=str(uuid.uuid4()),
            code=name[:3].upper(),
            name=name,
            description=description,
            is_taxable=True,
            tax_rate=tax_rate,
            tax_agency=tax_agency
        )
        self.tax_codes[tax_code.tax_code_id] = tax_code

        self.items[item_id] = item

        return {
            "success": True,
            "item_id": item_id,
            "item": self._item_to_dict(item),
            "tax_code_id": tax_code.tax_code_id
        }

    def update_item(self, item_id: str, **kwargs) -> Dict:
        """Update an item"""
        if item_id not in self.items:
            return {"success": False, "error": "Item not found"}

        item = self.items[item_id]

        for key, value in kwargs.items():
            if hasattr(item, key) and value is not None:
                setattr(item, key, value)

        item.updated_at = datetime.now()

        return {
            "success": True,
            "item": self._item_to_dict(item)
        }

    def get_item(self, item_id: str) -> Optional[Dict]:
        """Get item by ID"""
        if item_id not in self.items:
            return None
        return self._item_to_dict(self.items[item_id])

    def list_items(
        self,
        item_type: Optional[str] = None,
        category: Optional[str] = None,
        active_only: bool = True,
        low_stock_only: bool = False
    ) -> List[Dict]:
        """List items with filtering"""
        result = []

        for item in self.items.values():
            if active_only and not item.is_active:
                continue
            if item_type and item.item_type.value != item_type:
                continue
            if category and item.category != category:
                continue
            if low_stock_only:
                if item.item_type != ItemType.INVENTORY:
                    continue
                if item.quantity_on_hand > item.reorder_point:
                    continue

            result.append(self._item_to_dict(item))

        return sorted(result, key=lambda i: i["name"])

    def search_items(self, query: str) -> List[Dict]:
        """Search items by name, SKU, or description"""
        query = query.lower()
        result = []

        for item in self.items.values():
            if not item.is_active:
                continue
            if (query in item.name.lower() or
                query in item.sku.lower() or
                query in item.description.lower()):
                result.append(self._item_to_dict(item))

        return sorted(result, key=lambda i: i["name"])

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
        if item_id not in self.items:
            return {"success": False, "error": "Item not found"}

        item = self.items[item_id]

        if item.item_type != ItemType.INVENTORY:
            return {"success": False, "error": "Item is not an inventory item"}

        lot_id = str(uuid.uuid4())
        r_date = datetime.strptime(received_date, "%Y-%m-%d").date()
        total_cost = quantity * cost_per_unit

        lot = InventoryLot(
            lot_id=lot_id,
            item_id=item_id,
            received_date=r_date,
            quantity=quantity,
            cost_per_unit=cost_per_unit,
            total_cost=total_cost,
            remaining_quantity=quantity,
            vendor_id=vendor_id,
            po_number=po_number,
            lot_number=lot_number,
            location=location
        )

        self.lots[lot_id] = lot

        # Update item quantities and average cost
        old_qty = item.quantity_on_hand
        old_value = item.asset_value

        new_qty = old_qty + quantity
        new_value = old_value + total_cost

        if new_qty > 0:
            item.average_cost = new_value / new_qty

        item.quantity_on_hand = new_qty
        item.asset_value = new_value
        item.updated_at = datetime.now()

        return {
            "success": True,
            "lot_id": lot_id,
            "new_quantity": new_qty,
            "new_average_cost": round(item.average_cost, 4),
            "new_asset_value": round(new_value, 2)
        }

    def sell_inventory(
        self,
        item_id: str,
        quantity: float,
        sale_date: str
    ) -> Dict:
        """Sell inventory (reduce quantity, calculate COGS)"""
        if item_id not in self.items:
            return {"success": False, "error": "Item not found"}

        item = self.items[item_id]

        if item.item_type != ItemType.INVENTORY:
            return {"success": False, "error": "Item is not an inventory item"}

        if item.quantity_on_hand < quantity:
            return {"success": False, "error": "Insufficient quantity on hand"}

        s_date = datetime.strptime(sale_date, "%Y-%m-%d").date()

        # Calculate COGS based on valuation method
        if item.valuation_method == InventoryValuationMethod.AVERAGE:
            cogs = quantity * item.average_cost
        elif item.valuation_method == InventoryValuationMethod.FIFO:
            cogs = self._calculate_fifo_cogs(item_id, quantity)
        else:  # LIFO
            cogs = self._calculate_lifo_cogs(item_id, quantity)

        # Update item
        item.quantity_on_hand -= quantity
        item.asset_value -= cogs
        item.updated_at = datetime.now()

        return {
            "success": True,
            "quantity_sold": quantity,
            "cogs": round(cogs, 2),
            "remaining_quantity": item.quantity_on_hand,
            "remaining_value": round(item.asset_value, 2)
        }

    def _calculate_fifo_cogs(self, item_id: str, quantity: float) -> float:
        """Calculate COGS using FIFO method"""
        cogs = 0.0
        remaining = quantity

        # Get lots sorted by received date (oldest first)
        item_lots = sorted(
            [l for l in self.lots.values() if l.item_id == item_id and l.remaining_quantity > 0],
            key=lambda l: l.received_date
        )

        for lot in item_lots:
            if remaining <= 0:
                break

            use_qty = min(lot.remaining_quantity, remaining)
            cogs += use_qty * lot.cost_per_unit
            lot.remaining_quantity -= use_qty
            remaining -= use_qty

        return cogs

    def _calculate_lifo_cogs(self, item_id: str, quantity: float) -> float:
        """Calculate COGS using LIFO method"""
        cogs = 0.0
        remaining = quantity

        # Get lots sorted by received date (newest first)
        item_lots = sorted(
            [l for l in self.lots.values() if l.item_id == item_id and l.remaining_quantity > 0],
            key=lambda l: l.received_date,
            reverse=True
        )

        for lot in item_lots:
            if remaining <= 0:
                break

            use_qty = min(lot.remaining_quantity, remaining)
            cogs += use_qty * lot.cost_per_unit
            lot.remaining_quantity -= use_qty
            remaining -= use_qty

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
        if item_id not in self.items:
            return {"success": False, "error": "Item not found"}

        item = self.items[item_id]

        if item.item_type != ItemType.INVENTORY:
            return {"success": False, "error": "Item is not an inventory item"}

        adj_id = str(uuid.uuid4())
        a_date = datetime.strptime(adjustment_date, "%Y-%m-%d").date()

        old_qty = item.quantity_on_hand
        old_value = item.asset_value

        new_qty = old_qty
        new_value = old_value

        if quantity_change is not None:
            new_qty = old_qty + quantity_change
            # Adjust value proportionally
            if old_qty > 0:
                new_value = new_qty * item.average_cost
            else:
                new_value = new_qty * item.cost

        if value_change is not None:
            new_value = old_value + value_change
            # Recalculate average cost
            if new_qty > 0:
                item.average_cost = new_value / new_qty

        adjustment = InventoryAdjustment(
            adjustment_id=adj_id,
            adjustment_date=a_date,
            adjustment_type=AdjustmentType(adjustment_type),
            item_id=item_id,
            quantity_change=quantity_change or 0,
            value_change=value_change or 0,
            old_quantity=old_qty,
            new_quantity=new_qty,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            adjustment_account_id=adjustment_account_id
        )

        self.adjustments[adj_id] = adjustment

        item.quantity_on_hand = new_qty
        item.asset_value = new_value
        item.updated_at = datetime.now()

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
        if item_id not in self.items:
            return {"success": False, "error": "Item not found"}

        item = self.items[item_id]

        if item.item_type != ItemType.ASSEMBLY:
            return {"success": False, "error": "Item is not an assembly item"}

        # Check component availability
        for comp in item.components:
            comp_item = self.items.get(comp.get("item_id"))
            if not comp_item:
                return {"success": False, "error": f"Component not found: {comp.get('item_id')}"}

            required_qty = comp.get("quantity", 1) * quantity_to_build
            if comp_item.quantity_on_hand < required_qty:
                return {
                    "success": False,
                    "error": f"Insufficient quantity of {comp_item.name}: need {required_qty}, have {comp_item.quantity_on_hand}"
                }

        # Consume components
        total_component_cost = 0.0
        for comp in item.components:
            comp_item = self.items.get(comp.get("item_id"))
            required_qty = comp.get("quantity", 1) * quantity_to_build

            result = self.sell_inventory(comp_item.item_id, required_qty, build_date)
            if result.get("success"):
                total_component_cost += result.get("cogs", 0)

        # Add assembled items
        item.quantity_on_hand += quantity_to_build
        item.asset_value += total_component_cost
        if item.quantity_on_hand > 0:
            item.average_cost = item.asset_value / item.quantity_on_hand
        item.updated_at = datetime.now()

        return {
            "success": True,
            "quantity_built": quantity_to_build,
            "component_cost": round(total_component_cost, 2),
            "cost_per_unit": round(total_component_cost / quantity_to_build, 4),
            "new_quantity": item.quantity_on_hand
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
        c_date = datetime.strptime(count_date, "%Y-%m-%d").date()

        # Build count worksheet
        items_to_count = []

        for item in self.items.values():
            if item.item_type != ItemType.INVENTORY:
                continue
            if not item.is_active:
                continue
            if item_ids and item.item_id not in item_ids:
                continue

            items_to_count.append({
                "item_id": item.item_id,
                "item_name": item.name,
                "sku": item.sku,
                "expected_quantity": item.quantity_on_hand,
                "counted_quantity": None,
                "variance": None,
                "adjusted": False
            })

        count = PhysicalInventoryCount(
            count_id=count_id,
            count_date=c_date,
            location=location,
            items=items_to_count,
            total_items=len(items_to_count)
        )

        self.counts[count_id] = count

        return {
            "success": True,
            "count_id": count_id,
            "total_items": len(items_to_count),
            "items": items_to_count
        }

    def record_count(
        self,
        count_id: str,
        item_id: str,
        counted_quantity: float
    ) -> Dict:
        """Record a physical count for an item"""
        if count_id not in self.counts:
            return {"success": False, "error": "Count not found"}

        count = self.counts[count_id]

        if count.status != "in_progress":
            return {"success": False, "error": "Count is not in progress"}

        # Find and update the item in the count
        for item in count.items:
            if item["item_id"] == item_id:
                item["counted_quantity"] = counted_quantity
                item["variance"] = counted_quantity - item["expected_quantity"]
                count.items_counted += 1
                if abs(item["variance"]) > 0.001:
                    count.items_with_variance += 1
                break
        else:
            return {"success": False, "error": "Item not in count"}

        return {"success": True, "message": "Count recorded"}

    def post_physical_count(self, count_id: str, post_adjustments: bool = True) -> Dict:
        """Post physical count and optionally adjust inventory"""
        if count_id not in self.counts:
            return {"success": False, "error": "Count not found"}

        count = self.counts[count_id]

        if count.status != "in_progress":
            return {"success": False, "error": "Count is not in progress"}

        adjustments_made = []
        total_variance_value = 0.0

        for item_count in count.items:
            if item_count["counted_quantity"] is None:
                continue

            variance = item_count["variance"] or 0

            if abs(variance) > 0.001 and post_adjustments:
                item = self.items.get(item_count["item_id"])
                if item:
                    # Create adjustment
                    result = self.adjust_inventory(
                        item_id=item_count["item_id"],
                        adjustment_type="recount",
                        adjustment_date=count.count_date.isoformat(),
                        quantity_change=variance,
                        reason=f"Physical count adjustment - Count #{count_id[:8]}"
                    )

                    if result.get("success"):
                        item_count["adjusted"] = True
                        adjustments_made.append(result)
                        total_variance_value += result.get("variance", 0)

        count.total_variance_value = total_variance_value
        count.status = "posted"
        count.posted_at = datetime.now()

        return {
            "success": True,
            "count_id": count_id,
            "items_counted": count.items_counted,
            "items_with_variance": count.items_with_variance,
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

        price_level = PriceLevel(
            price_level_id=price_level_id,
            name=name,
            price_level_type=price_level_type,
            adjust_percent=adjust_percent
        )

        self.price_levels[price_level_id] = price_level

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
        if price_level_id not in self.price_levels:
            return {"success": False, "error": "Price level not found"}
        if item_id not in self.items:
            return {"success": False, "error": "Item not found"}

        price_level = self.price_levels[price_level_id]
        price_level.item_prices[item_id] = custom_price

        return {"success": True, "message": "Price set"}

    def get_item_price(self, item_id: str, price_level_id: Optional[str] = None) -> Dict:
        """Get item price, optionally with price level adjustment"""
        if item_id not in self.items:
            return {"error": "Item not found"}

        item = self.items[item_id]
        base_price = item.sales_price

        if price_level_id and price_level_id in self.price_levels:
            level = self.price_levels[price_level_id]

            # Check for fixed price
            if item_id in level.item_prices:
                return {
                    "item_id": item_id,
                    "base_price": base_price,
                    "price_level": level.name,
                    "adjusted_price": level.item_prices[item_id],
                    "adjustment_type": "fixed"
                }

            # Apply percentage adjustment
            if level.price_level_type == "percent":
                adjustment = base_price * (level.adjust_percent / 100)
                adjusted_price = base_price + adjustment
                return {
                    "item_id": item_id,
                    "base_price": base_price,
                    "price_level": level.name,
                    "adjusted_price": round(adjusted_price, 2),
                    "adjustment_percent": level.adjust_percent,
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
        items = []
        total_value = 0.0
        total_items = 0

        for item in self.items.values():
            if item.item_type != ItemType.INVENTORY:
                continue
            if not item.is_active:
                continue

            value = item.asset_value
            total_value += value
            total_items += 1

            items.append({
                "item_id": item.item_id,
                "name": item.name,
                "sku": item.sku,
                "quantity_on_hand": item.quantity_on_hand,
                "average_cost": round(item.average_cost, 4),
                "asset_value": round(value, 2),
                "percent_of_total": 0  # Calculate after totaling
            })

        # Calculate percentages
        for i in items:
            if total_value > 0:
                i["percent_of_total"] = round((i["asset_value"] / total_value) * 100, 2)

        return {
            "report": "Inventory Valuation Summary",
            "as_of_date": date.today().isoformat(),
            "total_items": total_items,
            "total_value": round(total_value, 2),
            "items": sorted(items, key=lambda x: x["asset_value"], reverse=True)
        }

    def get_reorder_report(self) -> Dict:
        """Get items needing reorder"""
        items_to_reorder = []

        for item in self.items.values():
            if item.item_type != ItemType.INVENTORY:
                continue
            if not item.is_active:
                continue
            if item.reorder_point <= 0:
                continue

            if item.quantity_on_hand <= item.reorder_point:
                items_to_reorder.append({
                    "item_id": item.item_id,
                    "name": item.name,
                    "sku": item.sku,
                    "quantity_on_hand": item.quantity_on_hand,
                    "reorder_point": item.reorder_point,
                    "suggested_order": item.reorder_quantity or (item.reorder_point * 2),
                    "preferred_vendor_id": item.preferred_vendor_id,
                    "estimated_cost": round(item.cost * (item.reorder_quantity or item.reorder_point * 2), 2)
                })

        return {
            "report": "Reorder Report",
            "as_of_date": date.today().isoformat(),
            "items_needing_reorder": len(items_to_reorder),
            "items": sorted(items_to_reorder, key=lambda x: x["quantity_on_hand"])
        }

    def get_inventory_stock_status(self) -> Dict:
        """Get overall inventory stock status"""
        in_stock = 0
        low_stock = 0
        out_of_stock = 0
        on_order = 0

        for item in self.items.values():
            if item.item_type != ItemType.INVENTORY:
                continue
            if not item.is_active:
                continue

            if item.quantity_on_hand <= 0:
                out_of_stock += 1
            elif item.quantity_on_hand <= item.reorder_point:
                low_stock += 1
            else:
                in_stock += 1

            if item.quantity_on_order > 0:
                on_order += 1

        return {
            "in_stock": in_stock,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "on_order": on_order,
            "total_inventory_items": in_stock + low_stock + out_of_stock
        }

    # ==================== UTILITY METHODS ====================

    def _item_to_dict(self, item: Item) -> Dict:
        """Convert Item to dictionary"""
        result = {
            "item_id": item.item_id,
            "item_type": item.item_type.value,
            "name": item.name,
            "description": item.description,
            "sku": item.sku,
            "barcode": item.barcode,
            "sales_price": item.sales_price,
            "cost": item.cost,
            "category": item.category,
            "subcategory": item.subcategory,
            "is_taxable": item.is_taxable,
            "unit_of_measure": item.unit_of_measure,
            "income_account_id": item.income_account_id,
            "expense_account_id": item.expense_account_id,
            "is_active": item.is_active,
            "created_at": item.created_at.isoformat()
        }

        # Add inventory-specific fields
        if item.item_type == ItemType.INVENTORY:
            result.update({
                "quantity_on_hand": item.quantity_on_hand,
                "quantity_on_order": item.quantity_on_order,
                "reorder_point": item.reorder_point,
                "average_cost": round(item.average_cost, 4),
                "asset_value": round(item.asset_value, 2),
                "valuation_method": item.valuation_method.value,
                "asset_account_id": item.asset_account_id,
                "preferred_vendor_id": item.preferred_vendor_id
            })

        # Add assembly/group components
        if item.item_type in [ItemType.ASSEMBLY, ItemType.GROUP]:
            result["components"] = item.components

        # Add discount fields
        if item.item_type == ItemType.DISCOUNT:
            result.update({
                "discount_percent": item.discount_percent,
                "discount_amount": item.discount_amount
            })

        # Add tax fields
        if item.item_type == ItemType.SALES_TAX_ITEM:
            result["tax_rate"] = item.tax_rate

        return result

    def get_service_summary(self) -> Dict:
        """Get service summary"""
        stock_status = self.get_inventory_stock_status()

        return {
            "service": "GenFin Inventory & Items",
            "version": "1.0.0",
            "features": [
                "Multiple Item Types (Service, Inventory, Non-Inventory, etc.)",
                "Quantity Tracking with FIFO/LIFO/Average",
                "Assembly/Bill of Materials",
                "Physical Inventory Counts",
                "Price Levels",
                "Reorder Alerts",
                "COGS Calculation"
            ],
            "total_items": len(self.items),
            "inventory_items": sum(1 for i in self.items.values() if i.item_type == ItemType.INVENTORY),
            "service_items": sum(1 for i in self.items.values() if i.item_type == ItemType.SERVICE),
            "assemblies": sum(1 for i in self.items.values() if i.item_type == ItemType.ASSEMBLY),
            "stock_status": stock_status,
            "price_levels": len(self.price_levels)
        }


# Singleton instance
genfin_inventory_service = GenFinInventoryService()
