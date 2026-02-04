"""
Grain & Storage Service for AgTools
Version: 4.1.0

Comprehensive grain management featuring:
- Bin Management (capacity tracking, moisture monitoring, inventory)
- Drying Cost Calculator (fuel, shrink, time calculations)
- Grain Accounting (bushel tracking from field to sale)
- Basis Alerts (automated notifications when basis hits targets)
"""

from datetime import datetime, date, timezone
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class GrainType(Enum):
    """Grain types"""
    CORN = "corn"
    SOYBEANS = "soybeans"
    WHEAT = "wheat"
    RICE = "rice"
    SORGHUM = "sorghum"
    OATS = "oats"


class BinType(Enum):
    """Storage bin types"""
    ROUND_STEEL = "round_steel"
    FLAT_STORAGE = "flat_storage"
    CONCRETE = "concrete"
    TEMPORARY = "temporary"
    HOPPER_BOTTOM = "hopper_bottom"


class BinStatus(Enum):
    """Bin status"""
    EMPTY = "empty"
    PARTIALLY_FILLED = "partially_filled"
    FULL = "full"
    UNDER_AERATION = "under_aeration"
    DRYING = "drying"
    PROBLEM = "problem"


class DryerType(Enum):
    """Dryer types"""
    IN_BIN = "in_bin"
    CONTINUOUS_FLOW = "continuous_flow"
    BATCH = "batch"
    NATURAL_AIR = "natural_air"


class TransactionType(Enum):
    """Grain transaction types"""
    HARVEST_IN = "harvest_in"
    PURCHASE_IN = "purchase_in"
    SALE_OUT = "sale_out"
    TRANSFER_OUT = "transfer_out"
    TRANSFER_IN = "transfer_in"
    SHRINK = "shrink"
    FEED_USE = "feed_use"


class AlertType(Enum):
    """Alert types"""
    BASIS_TARGET_HIT = "basis_target_hit"
    PRICE_TARGET_HIT = "price_target_hit"
    MOISTURE_HIGH = "moisture_high"
    TEMPERATURE_HIGH = "temperature_high"
    BIN_CAPACITY = "bin_capacity"


@dataclass
class StorageBin:
    """Storage bin record"""
    id: str
    name: str
    bin_type: BinType
    capacity_bushels: float
    diameter_feet: float
    height_feet: float
    has_aeration: bool
    has_dryer: bool
    dryer_type: Optional[DryerType]
    dryer_capacity_bph: float  # Bushels per hour
    location: str
    notes: str


@dataclass
class BinInventory:
    """Current bin inventory"""
    bin_id: str
    grain_type: GrainType
    bushels: float
    moisture_pct: float
    test_weight: float
    temperature: float
    date_loaded: date
    source_field: str
    status: BinStatus
    last_checked: date


@dataclass
class GrainTransaction:
    """Grain movement transaction"""
    id: str
    transaction_type: TransactionType
    grain_type: GrainType
    bushels_gross: float
    moisture_pct: float
    test_weight: float
    bushels_dry: float  # After shrink adjustment
    transaction_date: date
    source: str  # Field, bin, or buyer
    destination: str  # Bin, buyer, or use
    price_per_bushel: Optional[float]
    total_value: Optional[float]
    ticket_number: str
    notes: str


@dataclass
class DryingRecord:
    """Drying operation record"""
    id: str
    bin_id: str
    grain_type: GrainType
    bushels: float
    start_moisture: float
    end_moisture: float
    points_removed: float
    start_date: date
    end_date: Optional[date]
    dryer_type: DryerType
    fuel_type: str
    fuel_used: float
    fuel_cost: float
    electric_cost: float
    shrink_bushels: float
    total_cost: float
    cost_per_bushel: float
    cost_per_point: float


@dataclass
class BasisAlert:
    """Basis alert configuration"""
    id: str
    grain_type: GrainType
    target_basis: float
    current_basis: float
    direction: str  # "above" or "below"
    delivery_location: str
    bushels_to_sell: float
    is_active: bool
    triggered: bool
    triggered_date: Optional[date]
    notes: str


@dataclass
class PriceAlert:
    """Price alert configuration"""
    id: str
    grain_type: GrainType
    target_price: float
    current_price: float
    direction: str  # "above" or "below"
    bushels_to_sell: float
    is_active: bool
    triggered: bool
    triggered_date: Optional[date]
    notes: str


# =============================================================================
# GRAIN DATA
# =============================================================================

# Standard bushel weights (lbs/bu)
BUSHEL_WEIGHTS = {
    GrainType.CORN: 56,
    GrainType.SOYBEANS: 60,
    GrainType.WHEAT: 60,
    GrainType.RICE: 45,  # rough rice
    GrainType.SORGHUM: 56,
    GrainType.OATS: 32
}

# Target moisture levels
TARGET_MOISTURE = {
    GrainType.CORN: 15.0,
    GrainType.SOYBEANS: 13.0,
    GrainType.WHEAT: 13.5,
    GrainType.RICE: 12.5,
    GrainType.SORGHUM: 14.0,
    GrainType.OATS: 14.0
}

# Drying costs per point ($ per bushel per point removed)
DRYING_COSTS = {
    DryerType.IN_BIN: 0.03,
    DryerType.CONTINUOUS_FLOW: 0.04,
    DryerType.BATCH: 0.045,
    DryerType.NATURAL_AIR: 0.02
}

# Shrink factors (% weight loss per point moisture removed)
SHRINK_FACTORS = {
    GrainType.CORN: 1.4,  # 1.4% per point
    GrainType.SOYBEANS: 1.3,
    GrainType.WHEAT: 1.3,
    GrainType.RICE: 1.5,
    GrainType.SORGHUM: 1.4
}

# Handling shrink (% loss per handling)
HANDLING_SHRINK = 0.25  # 0.25% per handling

# LP gas consumption (gallons per point per 1000 bushels)
LP_GAS_USAGE = {
    DryerType.CONTINUOUS_FLOW: 0.02,  # gallons per bushel per point
    DryerType.BATCH: 0.025,
    DryerType.IN_BIN: 0.015
}

# Current prices (would be fetched from market data)
CURRENT_PRICES = {
    GrainType.CORN: {"cash": 4.45, "basis": -0.07},
    GrainType.SOYBEANS: {"cash": 10.25, "basis": -0.20},
    GrainType.WHEAT: {"cash": 5.35, "basis": -0.20},
    GrainType.RICE: {"cash": 14.50, "basis": -0.25},
    GrainType.SORGHUM: {"cash": 4.10, "basis": -0.15}
}


# =============================================================================
# GRAIN & STORAGE SERVICE CLASS
# =============================================================================

class GrainStorageService:
    """Grain and storage management service"""

    def __init__(self):
        self.bins: Dict[str, StorageBin] = {}
        self.inventories: Dict[str, BinInventory] = {}
        self.transactions: Dict[str, GrainTransaction] = {}
        self.drying_records: Dict[str, DryingRecord] = {}
        self.basis_alerts: Dict[str, BasisAlert] = {}
        self.price_alerts: Dict[str, PriceAlert] = {}

        self._counters = {
            "bin": 0, "txn": 0, "dry": 0, "basis_alert": 0, "price_alert": 0
        }

    def _next_id(self, prefix: str) -> str:
        self._counters[prefix] += 1
        return f"{prefix.upper()}-{self._counters[prefix]:04d}"

    # =========================================================================
    # BIN MANAGEMENT
    # =========================================================================

    def add_bin(
        self,
        name: str,
        bin_type: str,
        capacity_bushels: float,
        diameter_feet: float = 0,
        height_feet: float = 0,
        has_aeration: bool = True,
        has_dryer: bool = False,
        dryer_type: str = None,
        dryer_capacity_bph: float = 0,
        location: str = "",
        notes: str = ""
    ) -> Dict[str, Any]:
        """Add a storage bin"""
        try:
            btype = BinType(bin_type)
        except ValueError:
            return {"error": f"Invalid bin type: {bin_type}"}

        dtype = None
        if dryer_type:
            try:
                dtype = DryerType(dryer_type)
            except ValueError:
                return {"error": f"Invalid dryer type: {dryer_type}"}

        bin_id = self._next_id("bin")

        storage_bin = StorageBin(
            id=bin_id,
            name=name,
            bin_type=btype,
            capacity_bushels=capacity_bushels,
            diameter_feet=diameter_feet,
            height_feet=height_feet,
            has_aeration=has_aeration,
            has_dryer=has_dryer,
            dryer_type=dtype,
            dryer_capacity_bph=dryer_capacity_bph,
            location=location,
            notes=notes
        )

        self.bins[bin_id] = storage_bin

        # Initialize empty inventory
        self.inventories[bin_id] = None

        return {
            "id": bin_id,
            "name": name,
            "type": bin_type,
            "capacity": f"{capacity_bushels:,.0f} bushels",
            "features": {
                "aeration": has_aeration,
                "dryer": has_dryer,
                "dryer_type": dryer_type
            },
            "message": f"Bin '{name}' added with {capacity_bushels:,.0f} bu capacity"
        }

    def load_bin(
        self,
        bin_id: str,
        grain_type: str,
        bushels: float,
        moisture_pct: float,
        test_weight: float,
        source_field: str,
        temperature: float = 70
    ) -> Dict[str, Any]:
        """Load grain into a bin"""
        if bin_id not in self.bins:
            return {"error": f"Bin {bin_id} not found"}

        try:
            gtype = GrainType(grain_type)
        except ValueError:
            return {"error": f"Invalid grain type: {grain_type}"}

        bin_obj = self.bins[bin_id]
        current_inv = self.inventories.get(bin_id)

        # Check capacity
        current_bushels = current_inv.bushels if current_inv else 0
        if current_bushels + bushels > bin_obj.capacity_bushels:
            return {
                "error": f"Exceeds capacity. Available: {bin_obj.capacity_bushels - current_bushels:,.0f} bu"
            }

        # Check if mixing grains
        if current_inv and current_inv.grain_type != gtype:
            return {"error": f"Bin contains {current_inv.grain_type.value} - cannot mix with {grain_type}"}

        # Update or create inventory
        if current_inv:
            # Weighted average moisture
            total_bushels = current_bushels + bushels
            new_moisture = (current_inv.moisture_pct * current_bushels + moisture_pct * bushels) / total_bushels
            new_test_weight = (current_inv.test_weight * current_bushels + test_weight * bushels) / total_bushels

            current_inv.bushels = total_bushels
            current_inv.moisture_pct = new_moisture
            current_inv.test_weight = new_test_weight
            current_inv.last_checked = date.today()
            current_inv.status = BinStatus.FULL if total_bushels >= bin_obj.capacity_bushels * 0.95 else BinStatus.PARTIALLY_FILLED
        else:
            self.inventories[bin_id] = BinInventory(
                bin_id=bin_id,
                grain_type=gtype,
                bushels=bushels,
                moisture_pct=moisture_pct,
                test_weight=test_weight,
                temperature=temperature,
                date_loaded=date.today(),
                source_field=source_field,
                status=BinStatus.PARTIALLY_FILLED if bushels < bin_obj.capacity_bushels * 0.95 else BinStatus.FULL,
                last_checked=date.today()
            )

        # Record transaction
        txn_id = self._next_id("txn")
        txn = GrainTransaction(
            id=txn_id,
            transaction_type=TransactionType.HARVEST_IN,
            grain_type=gtype,
            bushels_gross=bushels,
            moisture_pct=moisture_pct,
            test_weight=test_weight,
            bushels_dry=bushels,  # Will adjust if dried
            transaction_date=date.today(),
            source=source_field,
            destination=bin_obj.name,
            price_per_bushel=None,
            total_value=None,
            ticket_number="",
            notes=""
        )
        self.transactions[txn_id] = txn

        inv = self.inventories[bin_id]
        pct_full = inv.bushels / bin_obj.capacity_bushels * 100

        return {
            "bin_id": bin_id,
            "bin_name": bin_obj.name,
            "loaded": f"{bushels:,.0f} bushels",
            "grain_type": grain_type,
            "moisture": f"{moisture_pct}%",
            "current_inventory": {
                "bushels": f"{inv.bushels:,.0f}",
                "moisture": f"{inv.moisture_pct:.1f}%",
                "pct_full": f"{pct_full:.1f}%"
            },
            "transaction_id": txn_id,
            "message": f"Loaded {bushels:,.0f} bu into {bin_obj.name} ({pct_full:.1f}% full)"
        }

    def unload_bin(
        self,
        bin_id: str,
        bushels: float,
        destination: str,
        price_per_bushel: float = None,
        ticket_number: str = ""
    ) -> Dict[str, Any]:
        """Unload grain from a bin"""
        if bin_id not in self.bins:
            return {"error": f"Bin {bin_id} not found"}

        inv = self.inventories.get(bin_id)
        if not inv or inv.bushels == 0:
            return {"error": f"Bin {bin_id} is empty"}

        if bushels > inv.bushels:
            return {"error": f"Only {inv.bushels:,.0f} bushels available"}

        bin_obj = self.bins[bin_id]

        # Record transaction
        txn_id = self._next_id("txn")
        total_value = bushels * price_per_bushel if price_per_bushel else None

        txn = GrainTransaction(
            id=txn_id,
            transaction_type=TransactionType.SALE_OUT,
            grain_type=inv.grain_type,
            bushels_gross=bushels,
            moisture_pct=inv.moisture_pct,
            test_weight=inv.test_weight,
            bushels_dry=bushels,
            transaction_date=date.today(),
            source=bin_obj.name,
            destination=destination,
            price_per_bushel=price_per_bushel,
            total_value=total_value,
            ticket_number=ticket_number,
            notes=""
        )
        self.transactions[txn_id] = txn

        # Update inventory
        inv.bushels -= bushels
        inv.last_checked = date.today()
        if inv.bushels <= 0:
            inv.status = BinStatus.EMPTY
            inv.bushels = 0
        else:
            inv.status = BinStatus.PARTIALLY_FILLED

        return {
            "bin_id": bin_id,
            "bin_name": bin_obj.name,
            "unloaded": f"{bushels:,.0f} bushels",
            "destination": destination,
            "price": f"${price_per_bushel:.2f}/bu" if price_per_bushel else "N/A",
            "total_value": f"${total_value:,.2f}" if total_value else "N/A",
            "remaining": f"{inv.bushels:,.0f} bushels",
            "transaction_id": txn_id,
            "message": f"Unloaded {bushels:,.0f} bu from {bin_obj.name}"
        }

    def get_bin_status(self, bin_id: str = None) -> Dict[str, Any]:
        """Get status of one or all bins"""
        if bin_id:
            if bin_id not in self.bins:
                return {"error": f"Bin {bin_id} not found"}
            bins_to_check = {bin_id: self.bins[bin_id]}
        else:
            bins_to_check = self.bins

        statuses = []
        total_capacity = 0
        total_stored = 0

        for bid, bin_obj in bins_to_check.items():
            inv = self.inventories.get(bid)
            bushels = inv.bushels if inv else 0
            pct_full = bushels / bin_obj.capacity_bushels * 100 if bin_obj.capacity_bushels > 0 else 0

            status = {
                "bin_id": bid,
                "name": bin_obj.name,
                "type": bin_obj.bin_type.value,
                "capacity": bin_obj.capacity_bushels,
                "stored": bushels,
                "pct_full": round(pct_full, 1),
                "available": bin_obj.capacity_bushels - bushels,
                "status": inv.status.value if inv else "empty"
            }

            if inv and bushels > 0:
                status["contents"] = {
                    "grain": inv.grain_type.value,
                    "moisture": f"{inv.moisture_pct:.1f}%",
                    "test_weight": inv.test_weight,
                    "temperature": f"{inv.temperature}F",
                    "days_stored": (date.today() - inv.date_loaded).days
                }

            statuses.append(status)
            total_capacity += bin_obj.capacity_bushels
            total_stored += bushels

        return {
            "bins_count": len(statuses),
            "total_capacity": total_capacity,
            "total_stored": total_stored,
            "overall_pct_full": round(total_stored / total_capacity * 100, 1) if total_capacity > 0 else 0,
            "available_capacity": total_capacity - total_stored,
            "bins": statuses
        }

    def update_bin_conditions(
        self,
        bin_id: str,
        moisture_pct: float = None,
        temperature: float = None
    ) -> Dict[str, Any]:
        """Update bin monitoring conditions"""
        if bin_id not in self.bins:
            return {"error": f"Bin {bin_id} not found"}

        inv = self.inventories.get(bin_id)
        if not inv:
            return {"error": f"Bin {bin_id} is empty"}

        alerts = []
        if moisture_pct is not None:
            _old_moisture = inv.moisture_pct
            inv.moisture_pct = moisture_pct
            target = TARGET_MOISTURE.get(inv.grain_type, 15.0)
            if moisture_pct > target + 2:
                alerts.append(f"High moisture: {moisture_pct}% (target: {target}%)")

        if temperature is not None:
            _old_temp = inv.temperature
            inv.temperature = temperature
            if temperature > 70:
                alerts.append(f"High temperature: {temperature}F - check aeration")

        inv.last_checked = date.today()

        return {
            "bin_id": bin_id,
            "bin_name": self.bins[bin_id].name,
            "updated_conditions": {
                "moisture": f"{inv.moisture_pct:.1f}%",
                "temperature": f"{inv.temperature}F"
            },
            "target_moisture": f"{TARGET_MOISTURE.get(inv.grain_type, 15.0)}%",
            "alerts": alerts,
            "message": "Bin conditions updated"
        }

    # =========================================================================
    # DRYING COST CALCULATOR
    # =========================================================================

    def calculate_drying_cost(
        self,
        grain_type: str,
        bushels: float,
        start_moisture: float,
        target_moisture: float = None,
        dryer_type: str = "continuous_flow",
        fuel_price_per_gallon: float = 2.50,
        electric_rate_per_kwh: float = 0.12
    ) -> Dict[str, Any]:
        """Calculate comprehensive drying costs"""
        try:
            gtype = GrainType(grain_type)
            dtype = DryerType(dryer_type)
        except ValueError as e:
            return {"error": str(e)}

        if target_moisture is None:
            target_moisture = TARGET_MOISTURE.get(gtype, 15.0)

        if start_moisture <= target_moisture:
            return {
                "message": f"Grain already at or below target moisture ({target_moisture}%)",
                "drying_needed": False
            }

        points_to_remove = start_moisture - target_moisture

        # Calculate shrink
        shrink_factor = SHRINK_FACTORS.get(gtype, 1.4)
        shrink_pct = points_to_remove * shrink_factor
        shrink_bushels = bushels * shrink_pct / 100
        dry_bushels = bushels - shrink_bushels

        # Calculate fuel usage
        lp_per_bu_per_point = LP_GAS_USAGE.get(dtype, 0.02)
        total_fuel = bushels * points_to_remove * lp_per_bu_per_point
        fuel_cost = total_fuel * fuel_price_per_gallon

        # Electric cost (fans, handling)
        kwh_per_bushel = 0.05  # Approximate
        electric_kwh = bushels * kwh_per_bushel
        electric_cost = electric_kwh * electric_rate_per_kwh

        # Total cost
        total_cost = fuel_cost + electric_cost
        cost_per_bushel = total_cost / bushels if bushels > 0 else 0
        _cost_per_point = total_cost / points_to_remove / bushels * 100 if points_to_remove > 0 and bushels > 0 else 0

        # Value of shrink
        grain_price = CURRENT_PRICES.get(gtype, {"cash": 4.50})["cash"]
        shrink_value = shrink_bushels * grain_price

        # Total economic cost
        total_economic_cost = total_cost + shrink_value

        return {
            "grain_type": grain_type,
            "bushels_wet": bushels,
            "moisture": {
                "start": f"{start_moisture}%",
                "target": f"{target_moisture}%",
                "points_removed": round(points_to_remove, 1)
            },
            "shrink": {
                "shrink_pct": f"{round(shrink_pct, 2)}%",
                "bushels_lost": round(shrink_bushels, 1),
                "dry_bushels": round(dry_bushels, 1),
                "shrink_value": f"${round(shrink_value, 2)}"
            },
            "drying_costs": {
                "fuel_gallons": round(total_fuel, 1),
                "fuel_cost": f"${round(fuel_cost, 2)}",
                "electric_cost": f"${round(electric_cost, 2)}",
                "total_cost": f"${round(total_cost, 2)}"
            },
            "per_bushel": {
                "drying_cost": f"${round(cost_per_bushel, 3)}/bu",
                "shrink_cost": f"${round(shrink_value / bushels, 3)}/bu" if bushels > 0 else "$0",
                "total_cost": f"${round(total_economic_cost / bushels, 3)}/bu" if bushels > 0 else "$0"
            },
            "total_economic_cost": f"${round(total_economic_cost, 2)}",
            "break_even_analysis": {
                "need_price_increase": f"${round(total_economic_cost / dry_bushels, 3)}/bu" if dry_bushels > 0 else "N/A",
                "days_to_dry_estimate": round(points_to_remove * 2, 0)  # Rough estimate
            }
        }

    def record_drying_operation(
        self,
        bin_id: str,
        start_moisture: float,
        end_moisture: float,
        fuel_used: float,
        fuel_cost: float,
        electric_cost: float,
        start_date: date,
        end_date: date = None
    ) -> Dict[str, Any]:
        """Record a completed drying operation"""
        if bin_id not in self.bins:
            return {"error": f"Bin {bin_id} not found"}

        inv = self.inventories.get(bin_id)
        if not inv:
            return {"error": f"Bin {bin_id} is empty"}

        bin_obj = self.bins[bin_id]
        if not bin_obj.has_dryer:
            return {"error": f"Bin {bin_id} does not have a dryer"}

        dry_id = self._next_id("dry")
        points_removed = start_moisture - end_moisture

        # Calculate shrink
        shrink_factor = SHRINK_FACTORS.get(inv.grain_type, 1.4)
        shrink_pct = points_removed * shrink_factor
        shrink_bushels = inv.bushels * shrink_pct / 100

        total_cost = fuel_cost + electric_cost
        cost_per_bushel = total_cost / inv.bushels if inv.bushels > 0 else 0
        cost_per_point = cost_per_bushel / points_removed if points_removed > 0 else 0

        record = DryingRecord(
            id=dry_id,
            bin_id=bin_id,
            grain_type=inv.grain_type,
            bushels=inv.bushels,
            start_moisture=start_moisture,
            end_moisture=end_moisture,
            points_removed=points_removed,
            start_date=start_date,
            end_date=end_date or date.today(),
            dryer_type=bin_obj.dryer_type or DryerType.CONTINUOUS_FLOW,
            fuel_type="LP",
            fuel_used=fuel_used,
            fuel_cost=fuel_cost,
            electric_cost=electric_cost,
            shrink_bushels=shrink_bushels,
            total_cost=total_cost,
            cost_per_bushel=cost_per_bushel,
            cost_per_point=cost_per_point
        )

        self.drying_records[dry_id] = record

        # Update inventory
        inv.moisture_pct = end_moisture
        inv.bushels -= shrink_bushels
        inv.status = BinStatus.PARTIALLY_FILLED
        inv.last_checked = date.today()

        return {
            "id": dry_id,
            "bin_name": bin_obj.name,
            "drying_summary": {
                "start_moisture": f"{start_moisture}%",
                "end_moisture": f"{end_moisture}%",
                "points_removed": round(points_removed, 1),
                "days": (end_date or date.today() - start_date).days if end_date else 0
            },
            "costs": {
                "fuel_cost": f"${fuel_cost:.2f}",
                "electric_cost": f"${electric_cost:.2f}",
                "total": f"${total_cost:.2f}",
                "per_bushel": f"${cost_per_bushel:.3f}",
                "per_point": f"${cost_per_point:.3f}"
            },
            "shrink": {
                "bushels_lost": round(shrink_bushels, 1),
                "remaining": round(inv.bushels, 1)
            },
            "message": f"Drying record saved - {points_removed:.1f} points removed"
        }

    # =========================================================================
    # GRAIN ACCOUNTING
    # =========================================================================

    def get_grain_inventory(self, grain_type: str = None) -> Dict[str, Any]:
        """Get total grain inventory across all bins"""
        inventory_by_grain = {}

        for bin_id, inv in self.inventories.items():
            if not inv or inv.bushels == 0:
                continue

            grain = inv.grain_type.value
            if grain_type and grain != grain_type:
                continue

            if grain not in inventory_by_grain:
                inventory_by_grain[grain] = {
                    "bushels": 0,
                    "bins": [],
                    "avg_moisture": 0,
                    "total_moisture_bushels": 0
                }

            inventory_by_grain[grain]["bushels"] += inv.bushels
            inventory_by_grain[grain]["total_moisture_bushels"] += inv.bushels * inv.moisture_pct
            inventory_by_grain[grain]["bins"].append({
                "bin_id": bin_id,
                "bin_name": self.bins[bin_id].name,
                "bushels": inv.bushels,
                "moisture": f"{inv.moisture_pct:.1f}%"
            })

        # Calculate averages and values
        for grain, data in inventory_by_grain.items():
            data["avg_moisture"] = round(data["total_moisture_bushels"] / data["bushels"], 1) if data["bushels"] > 0 else 0
            del data["total_moisture_bushels"]

            price_data = CURRENT_PRICES.get(GrainType(grain), {"cash": 0})
            data["current_price"] = price_data["cash"]
            data["total_value"] = round(data["bushels"] * price_data["cash"], 2)

        return {
            "as_of": date.today().isoformat(),
            "total_bushels": sum(d["bushels"] for d in inventory_by_grain.values()),
            "total_value": sum(d["total_value"] for d in inventory_by_grain.values()),
            "by_grain": inventory_by_grain
        }

    def get_transaction_history(
        self,
        grain_type: str = None,
        start_date: date = None,
        end_date: date = None,
        transaction_type: str = None
    ) -> Dict[str, Any]:
        """Get grain transaction history"""
        transactions = []

        for txn in self.transactions.values():
            if grain_type and txn.grain_type.value != grain_type:
                continue
            if start_date and txn.transaction_date < start_date:
                continue
            if end_date and txn.transaction_date > end_date:
                continue
            if transaction_type and txn.transaction_type.value != transaction_type:
                continue

            transactions.append({
                "id": txn.id,
                "date": txn.transaction_date.isoformat(),
                "type": txn.transaction_type.value,
                "grain": txn.grain_type.value,
                "bushels": txn.bushels_gross,
                "moisture": f"{txn.moisture_pct}%",
                "source": txn.source,
                "destination": txn.destination,
                "price": f"${txn.price_per_bushel:.2f}" if txn.price_per_bushel else None,
                "value": f"${txn.total_value:,.2f}" if txn.total_value else None
            })

        transactions.sort(key=lambda x: x["date"], reverse=True)

        # Summary
        total_in = sum(t["bushels"] for t in transactions if "IN" in t["type"].upper())
        total_out = sum(t["bushels"] for t in transactions if "OUT" in t["type"].upper())
        total_sales = sum(float(t["value"].replace("$", "").replace(",", "")) for t in transactions if t["value"] and "SALE" in t["type"].upper())

        return {
            "transaction_count": len(transactions),
            "summary": {
                "total_in": total_in,
                "total_out": total_out,
                "net_change": total_in - total_out,
                "total_sales_value": f"${total_sales:,.2f}"
            },
            "transactions": transactions
        }

    def calculate_basis_position(self, grain_type: str) -> Dict[str, Any]:
        """Calculate current basis position for stored grain"""
        try:
            gtype = GrainType(grain_type)
        except ValueError:
            return {"error": f"Invalid grain type: {grain_type}"}

        # Get inventory
        total_bushels = 0
        for inv in self.inventories.values():
            if inv and inv.grain_type == gtype:
                total_bushels += inv.bushels

        if total_bushels == 0:
            return {
                "grain_type": grain_type,
                "stored_bushels": 0,
                "message": "No grain in storage"
            }

        # Get current prices
        price_data = CURRENT_PRICES.get(gtype, {"cash": 4.50, "basis": -0.10})
        current_cash = price_data["cash"]
        current_basis = price_data["basis"]

        # Calculate position value
        current_value = total_bushels * current_cash

        # Storage cost estimate (per month)
        storage_cost_per_bu_month = 0.03
        _days_stored = 30  # Average assumption

        monthly_storage_cost = total_bushels * storage_cost_per_bu_month
        break_even_basis_improvement = storage_cost_per_bu_month

        return {
            "grain_type": grain_type,
            "stored_bushels": total_bushels,
            "current_market": {
                "cash_price": current_cash,
                "basis": current_basis,
                "current_value": round(current_value, 2)
            },
            "storage_cost": {
                "monthly_cost": round(monthly_storage_cost, 2),
                "cost_per_bushel_month": storage_cost_per_bu_month
            },
            "basis_analysis": {
                "current_basis": current_basis,
                "break_even_basis": round(current_basis + break_even_basis_improvement, 3),
                "recommendation": "Hold - expecting basis improvement" if current_basis < -0.15 else "Consider selling - basis near normal"
            }
        }

    # =========================================================================
    # BASIS ALERTS
    # =========================================================================

    def create_basis_alert(
        self,
        grain_type: str,
        target_basis: float,
        direction: str,  # "above" or "below"
        delivery_location: str,
        bushels_to_sell: float,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Create a basis alert"""
        try:
            gtype = GrainType(grain_type)
        except ValueError:
            return {"error": f"Invalid grain type: {grain_type}"}

        if direction not in ["above", "below"]:
            return {"error": "Direction must be 'above' or 'below'"}

        alert_id = self._next_id("basis_alert")

        current_basis = CURRENT_PRICES.get(gtype, {"basis": -0.10})["basis"]

        alert = BasisAlert(
            id=alert_id,
            grain_type=gtype,
            target_basis=target_basis,
            current_basis=current_basis,
            direction=direction,
            delivery_location=delivery_location,
            bushels_to_sell=bushels_to_sell,
            is_active=True,
            triggered=False,
            triggered_date=None,
            notes=notes
        )

        self.basis_alerts[alert_id] = alert

        # Check if already triggered
        triggered = (direction == "above" and current_basis >= target_basis) or \
                   (direction == "below" and current_basis <= target_basis)

        if triggered:
            alert.triggered = True
            alert.triggered_date = date.today()

        return {
            "id": alert_id,
            "grain_type": grain_type,
            "target_basis": target_basis,
            "direction": direction,
            "current_basis": current_basis,
            "bushels": bushels_to_sell,
            "location": delivery_location,
            "triggered": triggered,
            "message": f"Basis alert created - notify when basis goes {direction} ${target_basis:.2f}"
        }

    def create_price_alert(
        self,
        grain_type: str,
        target_price: float,
        direction: str,
        bushels_to_sell: float,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Create a price alert"""
        try:
            gtype = GrainType(grain_type)
        except ValueError:
            return {"error": f"Invalid grain type: {grain_type}"}

        alert_id = self._next_id("price_alert")

        current_price = CURRENT_PRICES.get(gtype, {"cash": 4.50})["cash"]

        alert = PriceAlert(
            id=alert_id,
            grain_type=gtype,
            target_price=target_price,
            current_price=current_price,
            direction=direction,
            bushels_to_sell=bushels_to_sell,
            is_active=True,
            triggered=False,
            triggered_date=None,
            notes=notes
        )

        self.price_alerts[alert_id] = alert

        triggered = (direction == "above" and current_price >= target_price) or \
                   (direction == "below" and current_price <= target_price)

        if triggered:
            alert.triggered = True
            alert.triggered_date = date.today()

        return {
            "id": alert_id,
            "grain_type": grain_type,
            "target_price": target_price,
            "direction": direction,
            "current_price": current_price,
            "bushels": bushels_to_sell,
            "triggered": triggered,
            "message": f"Price alert created - notify when price goes {direction} ${target_price:.2f}"
        }

    def check_alerts(self) -> Dict[str, Any]:
        """Check all active alerts against current prices"""
        triggered_alerts = []
        active_alerts = []

        # Check basis alerts
        for alert in self.basis_alerts.values():
            if not alert.is_active:
                continue

            current_basis = CURRENT_PRICES.get(alert.grain_type, {"basis": -0.10})["basis"]
            alert.current_basis = current_basis

            should_trigger = (alert.direction == "above" and current_basis >= alert.target_basis) or \
                           (alert.direction == "below" and current_basis <= alert.target_basis)

            if should_trigger and not alert.triggered:
                alert.triggered = True
                alert.triggered_date = date.today()
                triggered_alerts.append({
                    "type": "basis",
                    "id": alert.id,
                    "grain": alert.grain_type.value,
                    "target": alert.target_basis,
                    "current": current_basis,
                    "bushels": alert.bushels_to_sell,
                    "message": f"BASIS ALERT: {alert.grain_type.value} basis at ${current_basis:.2f} (target: ${alert.target_basis:.2f})"
                })
            elif alert.is_active and not alert.triggered:
                active_alerts.append({
                    "type": "basis",
                    "id": alert.id,
                    "grain": alert.grain_type.value,
                    "target": alert.target_basis,
                    "current": current_basis,
                    "bushels": alert.bushels_to_sell
                })

        # Check price alerts
        for alert in self.price_alerts.values():
            if not alert.is_active:
                continue

            current_price = CURRENT_PRICES.get(alert.grain_type, {"cash": 4.50})["cash"]
            alert.current_price = current_price

            should_trigger = (alert.direction == "above" and current_price >= alert.target_price) or \
                           (alert.direction == "below" and current_price <= alert.target_price)

            if should_trigger and not alert.triggered:
                alert.triggered = True
                alert.triggered_date = date.today()
                triggered_alerts.append({
                    "type": "price",
                    "id": alert.id,
                    "grain": alert.grain_type.value,
                    "target": alert.target_price,
                    "current": current_price,
                    "bushels": alert.bushels_to_sell,
                    "message": f"PRICE ALERT: {alert.grain_type.value} at ${current_price:.2f} (target: ${alert.target_price:.2f})"
                })
            elif alert.is_active and not alert.triggered:
                active_alerts.append({
                    "type": "price",
                    "id": alert.id,
                    "grain": alert.grain_type.value,
                    "target": alert.target_price,
                    "current": current_price,
                    "bushels": alert.bushels_to_sell
                })

        return {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "triggered_count": len(triggered_alerts),
            "active_count": len(active_alerts),
            "triggered_alerts": triggered_alerts,
            "active_alerts": active_alerts
        }

    def get_grain_types(self) -> Dict[str, Any]:
        """Get available grain types"""
        return {
            "types": [
                {
                    "id": g.value,
                    "name": g.value.title(),
                    "bushel_weight": BUSHEL_WEIGHTS[g],
                    "target_moisture": TARGET_MOISTURE[g]
                }
                for g in GrainType
            ]
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_grain_storage_service: Optional[GrainStorageService] = None


def get_grain_storage_service() -> GrainStorageService:
    """Get or create the grain storage service singleton"""
    global _grain_storage_service
    if _grain_storage_service is None:
        _grain_storage_service = GrainStorageService()
    return _grain_storage_service
