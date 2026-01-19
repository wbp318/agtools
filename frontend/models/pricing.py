"""
Pricing Service Data Models

Data classes for pricing, supplier quotes, and cost calculations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime


class ProductCategory(str, Enum):
    """Product categories for pricing."""
    FERTILIZER = "fertilizer"
    PESTICIDE = "pesticide"
    SEED = "seed"
    FUEL = "fuel"
    CUSTOM_APPLICATION = "custom_application"


class Region(str, Enum):
    """Geographic regions for price adjustments."""
    MIDWEST_CORN_BELT = "midwest_corn_belt"
    NORTHERN_PLAINS = "northern_plains"
    SOUTHERN_PLAINS = "southern_plains"
    DELTA = "delta"
    SOUTHEAST = "southeast"
    PACIFIC_NORTHWEST = "pacific_northwest"
    MOUNTAIN = "mountain"


class PriceTrend(str, Enum):
    """Price trend indicators."""
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    VOLATILE = "volatile"


class BuyRecommendation(str, Enum):
    """Purchase recommendations."""
    BUY_NOW = "buy_now"
    WAIT = "wait"
    SPLIT_PURCHASE = "split_purchase"
    FORWARD_CONTRACT = "forward_contract"


@dataclass
class ProductPrice:
    """Price information for a single product."""
    product_id: str
    price: float
    unit: str
    description: str
    category: str
    source: str = "default"  # "default", "custom", "supplier"
    supplier: Optional[str] = None
    valid_until: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, product_id: str, data: dict) -> "ProductPrice":
        return cls(
            product_id=product_id,
            price=data.get("price", 0),
            unit=data.get("unit", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
            source=data.get("source", "default"),
            supplier=data.get("supplier"),
            valid_until=data.get("valid_until"),
            notes=data.get("notes"),
        )


@dataclass
class GetPricesResponse:
    """Response containing multiple product prices."""
    region: str
    category: str
    count: int
    prices: Dict[str, ProductPrice]

    @classmethod
    def from_dict(cls, data: dict) -> "GetPricesResponse":
        prices = {}
        prices_data = data.get("prices", [])

        # Handle both list and dict formats for backwards compatibility
        if isinstance(prices_data, list):
            for price_info in prices_data:
                product_id = price_info.get("product_id", "")
                prices[product_id] = ProductPrice.from_dict(product_id, price_info)
        else:
            # Legacy dict format
            for product_id, price_info in prices_data.items():
                prices[product_id] = ProductPrice.from_dict(product_id, price_info)

        return cls(
            region=data.get("region", ""),
            category=data.get("category", "all"),
            count=data.get("count", len(prices)),
            prices=prices,
        )


@dataclass
class SetPriceRequest:
    """Request to set a custom supplier price."""
    product_id: str
    price: float
    supplier: Optional[str] = None
    valid_until: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "price": self.price,
            "supplier": self.supplier,
            "valid_until": self.valid_until,
            "notes": self.notes,
        }


@dataclass
class SetPriceResponse:
    """Response after setting a custom price."""
    product_id: str
    new_price: float
    old_price: float
    default_price: float
    savings_vs_default: float
    savings_percent: float
    supplier: Optional[str]
    message: str

    @classmethod
    def from_dict(cls, data: dict) -> "SetPriceResponse":
        return cls(
            product_id=data.get("product_id", ""),
            new_price=data.get("new_price", 0),
            old_price=data.get("old_price", 0),
            default_price=data.get("default_price", 0),
            savings_vs_default=data.get("savings_vs_default", 0),
            savings_percent=data.get("savings_percent", 0),
            supplier=data.get("supplier"),
            message=data.get("message", ""),
        )


@dataclass
class BulkPriceUpdate:
    """Single price update in a bulk update."""
    product_id: str
    price: float
    notes: Optional[str] = None


@dataclass
class BulkUpdateRequest:
    """Request for bulk price updates."""
    price_updates: List[BulkPriceUpdate] = field(default_factory=list)
    supplier: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "price_updates": [
                {"product_id": u.product_id, "price": u.price, "notes": u.notes}
                for u in self.price_updates
            ],
            "supplier": self.supplier,
        }


@dataclass
class BulkUpdateResponse:
    """Response from bulk price update."""
    updated_count: int
    total_savings: float
    updates: List[SetPriceResponse]
    message: str

    @classmethod
    def from_dict(cls, data: dict) -> "BulkUpdateResponse":
        updates = [SetPriceResponse.from_dict(u) for u in data.get("updates", [])]
        return cls(
            updated_count=data.get("updated_count", len(updates)),
            total_savings=data.get("total_savings", 0),
            updates=updates,
            message=data.get("message", ""),
        )


@dataclass
class BuyRecommendationRequest:
    """Request for buy now vs wait recommendation."""
    product_id: str
    quantity_needed: float
    purchase_deadline: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "quantity_needed": self.quantity_needed,
            "purchase_deadline": self.purchase_deadline,
        }


@dataclass
class PriceAnalysis:
    """Price trend analysis."""
    trend: str  # rising, falling, stable, volatile
    current_vs_90_day_avg_percent: float
    avg_90_day: float
    avg_30_day: float


@dataclass
class BuyRecommendationResponse:
    """Response with buy recommendation."""
    product_id: str
    product_description: str
    current_price: float
    unit: str
    quantity_needed: float
    current_total_cost: float
    price_analysis: PriceAnalysis
    recommendation: str  # buy_now, wait, split_purchase, forward_contract
    reasoning: str
    suggested_action: str
    potential_savings_if_wait: float

    @classmethod
    def from_dict(cls, data: dict) -> "BuyRecommendationResponse":
        analysis_data = data.get("price_analysis", {})
        analysis = PriceAnalysis(
            trend=analysis_data.get("trend", "stable"),
            current_vs_90_day_avg_percent=analysis_data.get("current_vs_90_day_avg_percent", 0),
            avg_90_day=analysis_data.get("avg_90_day", 0),
            avg_30_day=analysis_data.get("avg_30_day", 0),
        )

        return cls(
            product_id=data.get("product_id", ""),
            product_description=data.get("product_description", ""),
            current_price=data.get("current_price", 0),
            unit=data.get("unit", ""),
            quantity_needed=data.get("quantity_needed", 0),
            current_total_cost=data.get("current_total_cost", 0),
            price_analysis=analysis,
            recommendation=data.get("recommendation", ""),
            reasoning=data.get("reasoning", ""),
            suggested_action=data.get("suggested_action", ""),
            potential_savings_if_wait=data.get("potential_savings_if_wait", 0),
        )


@dataclass
class InputCostItem:
    """Line item in input cost calculation."""
    product_id: str
    description: str
    rate: str
    quantity: float
    unit_price: float
    unit: str
    total_cost: float
    cost_per_acre: float
    source: str


@dataclass
class InputCostSummary:
    """Summary of input costs."""
    total_cost: float
    cost_per_acre: float
    cost_per_bushel_goal: float
    grain_price_used: float
    break_even_yield: float
    yield_goal_margin: float


@dataclass
class InputCostRequest:
    """Request for input cost calculation."""
    crop: str = "corn"
    acres: float = 500
    yield_goal: float = 200
    inputs: List[Dict] = field(default_factory=list)  # {"product_id": str, "rate_per_acre": float}

    def to_dict(self) -> dict:
        return {
            "crop": self.crop,
            "acres": self.acres,
            "yield_goal": self.yield_goal,
            "inputs": self.inputs,
        }


@dataclass
class InputCostResponse:
    """Response with calculated input costs."""
    crop: str
    acres: float
    yield_goal: float
    line_items: List[InputCostItem]
    summary: InputCostSummary
    custom_prices_used: int
    default_prices_used: int

    @classmethod
    def from_dict(cls, data: dict) -> "InputCostResponse":
        items = []
        for item in data.get("line_items", []):
            items.append(InputCostItem(
                product_id=item.get("product_id", ""),
                description=item.get("description", ""),
                rate=item.get("rate", ""),
                quantity=item.get("quantity", 0),
                unit_price=item.get("unit_price", 0),
                unit=item.get("unit", ""),
                total_cost=item.get("total_cost", 0),
                cost_per_acre=item.get("cost_per_acre", 0),
                source=item.get("source", "default"),
            ))

        summary_data = data.get("summary", {})
        summary = InputCostSummary(
            total_cost=summary_data.get("total_cost", 0),
            cost_per_acre=summary_data.get("cost_per_acre", 0),
            cost_per_bushel_goal=summary_data.get("cost_per_bushel_goal", 0),
            grain_price_used=summary_data.get("grain_price_used", 0),
            break_even_yield=summary_data.get("break_even_yield", 0),
            yield_goal_margin=summary_data.get("yield_goal_margin", 0),
        )

        sources = data.get("price_sources", {})

        return cls(
            crop=data.get("crop", ""),
            acres=data.get("acres", 0),
            yield_goal=data.get("yield_goal", 0),
            line_items=items,
            summary=summary,
            custom_prices_used=sources.get("custom_prices_used", 0),
            default_prices_used=sources.get("default_prices_used", 0),
        )


@dataclass
class PriceAlert:
    """A price alert notification."""
    alert_type: str  # "quote_expiring", "above_average", etc.
    product_id: str
    description: str
    supplier: Optional[str]
    days_until_expiry: Optional[int]
    message: str


@dataclass
class PriceAlertsResponse:
    """Response with price alerts."""
    region: str
    alert_count: int
    alerts: List[PriceAlert]

    @classmethod
    def from_dict(cls, data: dict) -> "PriceAlertsResponse":
        alerts = []
        for a in data.get("alerts", []):
            alerts.append(PriceAlert(
                alert_type=a.get("type", ""),
                product_id=a.get("product_id", ""),
                description=a.get("description", ""),
                supplier=a.get("supplier"),
                days_until_expiry=a.get("days_until_expiry"),
                message=a.get("message", ""),
            ))

        return cls(
            region=data.get("region", ""),
            alert_count=data.get("alert_count", len(alerts)),
            alerts=alerts,
        )


@dataclass
class SupplierComparisonRequest:
    """Request for supplier comparison."""
    product_ids: List[str] = field(default_factory=list)
    acres: float = 500

    def to_dict(self) -> dict:
        return {
            "product_ids": self.product_ids,
            "acres": self.acres,
        }


@dataclass
class SupplierComparison:
    """Comparison data for a supplier."""
    supplier: str
    products: Dict[str, float]  # product_id -> price
    total_cost: float
    savings_vs_default: float


@dataclass
class SupplierComparisonResponse:
    """Response with supplier comparisons."""
    suppliers: List[SupplierComparison]
    cheapest_supplier: str
    potential_savings: float

    @classmethod
    def from_dict(cls, data: dict) -> "SupplierComparisonResponse":
        suppliers = []
        for s in data.get("suppliers", []):
            suppliers.append(SupplierComparison(
                supplier=s.get("supplier", ""),
                products=s.get("products", {}),
                total_cost=s.get("total_cost", 0),
                savings_vs_default=s.get("savings_vs_default", 0),
            ))

        return cls(
            suppliers=suppliers,
            cheapest_supplier=data.get("cheapest_supplier", ""),
            potential_savings=data.get("potential_savings", 0),
        )
