"""
Real-Time and Custom Pricing Service
Manages dynamic pricing for fertilizers, pesticides, fuel, and other inputs
Allows farmers to input actual supplier quotes for accurate ROI calculations
Tracks historical prices for "buy now or wait" decisions
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class InputCategory(str, Enum):
    FERTILIZER = "fertilizer"
    PESTICIDE = "pesticide"
    SEED = "seed"
    FUEL = "fuel"
    CUSTOM_APPLICATION = "custom_application"


class PriceTrend(str, Enum):
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    VOLATILE = "volatile"


class BuyRecommendation(str, Enum):
    BUY_NOW = "buy_now"
    WAIT = "wait"
    CONSIDER_FORWARD_CONTRACT = "forward_contract"
    SPLIT_PURCHASE = "split_purchase"


# Default 2024/2025 baseline prices ($/unit as specified)
DEFAULT_FERTILIZER_PRICES = {
    # Nitrogen sources ($/lb N)
    "anhydrous_ammonia_82": {"price": 0.48, "unit": "lb_N", "description": "Anhydrous Ammonia 82-0-0"},
    "urea_46": {"price": 0.55, "unit": "lb_N", "description": "Urea 46-0-0"},
    "uan_28": {"price": 0.52, "unit": "lb_N", "description": "UAN 28-0-0"},
    "uan_32": {"price": 0.54, "unit": "lb_N", "description": "UAN 32-0-0"},
    "ams_21": {"price": 0.65, "unit": "lb_N", "description": "Ammonium Sulfate 21-0-0-24S"},

    # Phosphorus sources ($/lb P2O5)
    "dap_18_46": {"price": 0.62, "unit": "lb_P2O5", "description": "DAP 18-46-0"},
    "map_11_52": {"price": 0.65, "unit": "lb_P2O5", "description": "MAP 11-52-0"},
    "triple_super_phosphate": {"price": 0.58, "unit": "lb_P2O5", "description": "TSP 0-46-0"},

    # Potassium sources ($/lb K2O)
    "potash_60": {"price": 0.42, "unit": "lb_K2O", "description": "Potash 0-0-60"},
    "potash_muriate": {"price": 0.40, "unit": "lb_K2O", "description": "Muriate of Potash"},
    "sulfate_of_potash": {"price": 0.75, "unit": "lb_K2O", "description": "SOP 0-0-50-18S"},

    # Sulfur sources ($/lb S)
    "elemental_sulfur": {"price": 0.35, "unit": "lb_S", "description": "Elemental Sulfur 90%"},
    "gypsum": {"price": 0.15, "unit": "lb_S", "description": "Gypsum 18% S"},

    # Micronutrients ($/lb nutrient)
    "zinc_sulfate": {"price": 1.20, "unit": "lb_Zn", "description": "Zinc Sulfate 36%"},
    "boron": {"price": 2.50, "unit": "lb_B", "description": "Solubor 20.5% B"},
    "manganese_sulfate": {"price": 0.85, "unit": "lb_Mn", "description": "Manganese Sulfate 32%"},
}

DEFAULT_PESTICIDE_PRICES = {
    # Herbicides ($/acre at labeled rate)
    "glyphosate_generic": {"price": 4.50, "unit": "acre", "description": "Generic Glyphosate 4 lb/gal @ 32 oz"},
    "roundup_powermax": {"price": 8.00, "unit": "acre", "description": "Roundup PowerMax @ 32 oz"},
    "dicamba_xtendimax": {"price": 12.50, "unit": "acre", "description": "XtendiMax @ 22 oz"},
    "liberty_280": {"price": 14.00, "unit": "acre", "description": "Liberty 280 @ 32 oz"},
    "atrazine_4l": {"price": 5.50, "unit": "acre", "description": "Atrazine 4L @ 2 qt"},
    "dual_magnum": {"price": 18.00, "unit": "acre", "description": "Dual II Magnum @ 1.67 pt"},
    "warrant": {"price": 12.00, "unit": "acre", "description": "Warrant @ 3 qt"},
    "laudis": {"price": 11.00, "unit": "acre", "description": "Laudis @ 3 oz"},

    # Insecticides ($/acre at labeled rate)
    "bifenthrin_generic": {"price": 3.50, "unit": "acre", "description": "Generic Bifenthrin @ 6.4 oz"},
    "warrior_ii": {"price": 6.00, "unit": "acre", "description": "Warrior II @ 1.92 oz"},
    "prevathon": {"price": 18.00, "unit": "acre", "description": "Prevathon @ 20 oz"},
    "hero": {"price": 8.50, "unit": "acre", "description": "Hero @ 10.3 oz"},
    "lorsban_advanced": {"price": 11.00, "unit": "acre", "description": "Lorsban Advanced @ 2 pt"},

    # Fungicides ($/acre at labeled rate)
    "headline_amp": {"price": 22.00, "unit": "acre", "description": "Headline AMP @ 10 oz"},
    "trivapro": {"price": 24.00, "unit": "acre", "description": "Trivapro @ 13.7 oz"},
    "delaro_325": {"price": 20.00, "unit": "acre", "description": "Delaro 325 @ 8 oz"},
    "priaxor": {"price": 21.00, "unit": "acre", "description": "Priaxor @ 4 oz"},
    "miravis_neo": {"price": 26.00, "unit": "acre", "description": "Miravis Neo @ 13.7 oz"},
    "generic_azoxystrobin": {"price": 8.00, "unit": "acre", "description": "Generic Azoxystrobin @ 6 oz"},
    "generic_propiconazole": {"price": 4.50, "unit": "acre", "description": "Generic Propiconazole @ 4 oz"},
}

DEFAULT_SEED_PRICES = {
    # Corn ($/bag - 80K seeds)
    "corn_conventional": {"price": 180.00, "unit": "bag_80K", "description": "Conventional Corn Hybrid"},
    "corn_traited_single": {"price": 280.00, "unit": "bag_80K", "description": "Single-Trait Corn (RR or Bt)"},
    "corn_traited_stacked": {"price": 340.00, "unit": "bag_80K", "description": "Stacked-Trait Corn (VT2P, etc.)"},
    "corn_premium_genetics": {"price": 380.00, "unit": "bag_80K", "description": "Premium Genetics + Traits"},

    # Soybeans ($/bag - 140K seeds)
    "soybean_conventional": {"price": 45.00, "unit": "bag_140K", "description": "Conventional Soybean"},
    "soybean_roundup_ready": {"price": 55.00, "unit": "bag_140K", "description": "Roundup Ready 2 Xtend"},
    "soybean_xtend_flex": {"price": 65.00, "unit": "bag_140K", "description": "XtendFlex Soybean"},
    "soybean_enlist": {"price": 62.00, "unit": "bag_140K", "description": "Enlist E3 Soybean"},
}

DEFAULT_FUEL_PRICES = {
    "diesel": {"price": 3.50, "unit": "gallon", "description": "Off-road Diesel"},
    "gasoline": {"price": 3.20, "unit": "gallon", "description": "Regular Gasoline"},
    "propane": {"price": 1.50, "unit": "gallon", "description": "Propane LP"},
    "electricity": {"price": 0.12, "unit": "kWh", "description": "Agricultural Rate Electricity"},
}

DEFAULT_APPLICATION_COSTS = {
    "custom_spray_ground": {"price": 8.50, "unit": "acre", "description": "Custom Ground Spraying"},
    "custom_spray_aerial": {"price": 10.00, "unit": "acre", "description": "Custom Aerial Spraying"},
    "custom_fertilizer_dry": {"price": 6.00, "unit": "acre", "description": "Custom Dry Fertilizer Spreading"},
    "custom_fertilizer_liquid": {"price": 7.00, "unit": "acre", "description": "Custom Liquid Fertilizer"},
    "custom_anhydrous": {"price": 14.00, "unit": "acre", "description": "Custom Anhydrous Application"},
    "custom_lime": {"price": 8.00, "unit": "acre", "description": "Custom Lime Spreading"},
    "custom_combine_corn": {"price": 42.00, "unit": "acre", "description": "Custom Combining Corn"},
    "custom_combine_beans": {"price": 38.00, "unit": "acre", "description": "Custom Combining Soybeans"},
}

# Regional price adjustments (multipliers)
REGIONAL_ADJUSTMENTS = {
    "midwest_corn_belt": 1.00,  # Baseline (IA, IL, IN, OH)
    "northern_plains": 1.05,   # ND, SD, MN - slightly higher transport
    "southern_plains": 1.08,   # KS, OK, TX - higher transport costs
    "delta": 1.03,             # MS, AR, LA, MO
    "southeast": 1.10,         # GA, SC, NC - higher transport
    "pacific_northwest": 1.12, # WA, OR, ID - highest transport
    "mountain": 1.15,          # MT, WY, CO - remote areas
}


@dataclass
class PriceRecord:
    """Individual price record with metadata"""
    product_id: str
    price: float
    unit: str
    source: str  # 'default', 'user_quote', 'api', 'historical'
    date_recorded: datetime
    supplier: Optional[str] = None
    notes: Optional[str] = None
    valid_until: Optional[datetime] = None


@dataclass
class PriceHistory:
    """Historical price data for trend analysis"""
    product_id: str
    prices: List[PriceRecord] = field(default_factory=list)

    def add_price(self, record: PriceRecord):
        self.prices.append(record)
        self.prices.sort(key=lambda x: x.date_recorded)

    def get_trend(self, lookback_days: int = 90) -> PriceTrend:
        """Analyze price trend over lookback period"""
        if len(self.prices) < 2:
            return PriceTrend.STABLE

        cutoff = datetime.now() - timedelta(days=lookback_days)
        recent_prices = [p for p in self.prices if p.date_recorded >= cutoff]

        if len(recent_prices) < 2:
            return PriceTrend.STABLE

        # Calculate percent change
        first_price = recent_prices[0].price
        last_price = recent_prices[-1].price

        if first_price == 0:
            return PriceTrend.STABLE

        pct_change = ((last_price - first_price) / first_price) * 100

        # Check for volatility (standard deviation)
        prices = [p.price for p in recent_prices]
        avg = sum(prices) / len(prices)
        variance = sum((p - avg) ** 2 for p in prices) / len(prices)
        std_dev_pct = (variance ** 0.5) / avg * 100 if avg > 0 else 0

        if std_dev_pct > 15:
            return PriceTrend.VOLATILE
        elif pct_change > 10:
            return PriceTrend.RISING
        elif pct_change < -10:
            return PriceTrend.FALLING
        else:
            return PriceTrend.STABLE

    def get_average(self, lookback_days: int = 90) -> float:
        """Get average price over lookback period"""
        cutoff = datetime.now() - timedelta(days=lookback_days)
        recent = [p.price for p in self.prices if p.date_recorded >= cutoff]
        return sum(recent) / len(recent) if recent else 0


class PricingService:
    """
    Comprehensive pricing service for agricultural inputs

    Features:
    - Store and retrieve current prices (default + custom)
    - Track price history for trend analysis
    - Regional price adjustments
    - Supplier quote management
    - Buy now/wait recommendations
    - Price comparison across suppliers
    """

    def __init__(self, region: str = "midwest_corn_belt"):
        self.region = region
        self.regional_multiplier = REGIONAL_ADJUSTMENTS.get(region, 1.0)

        # Current prices (starts with defaults, updated with user data)
        self.current_prices: Dict[str, Dict[str, Any]] = {}
        self._load_default_prices()

        # Price history tracking
        self.price_history: Dict[str, PriceHistory] = {}

        # Supplier quotes (temporary storage)
        self.supplier_quotes: List[Dict[str, Any]] = []

    def _load_default_prices(self):
        """Load default prices with regional adjustment"""
        for product_id, data in DEFAULT_FERTILIZER_PRICES.items():
            self.current_prices[product_id] = {
                **data,
                "price": round(data["price"] * self.regional_multiplier, 2),
                "category": InputCategory.FERTILIZER,
                "source": "default"
            }

        for product_id, data in DEFAULT_PESTICIDE_PRICES.items():
            self.current_prices[product_id] = {
                **data,
                "price": round(data["price"] * self.regional_multiplier, 2),
                "category": InputCategory.PESTICIDE,
                "source": "default"
            }

        for product_id, data in DEFAULT_SEED_PRICES.items():
            self.current_prices[product_id] = {
                **data,
                "price": round(data["price"] * self.regional_multiplier, 2),
                "category": InputCategory.SEED,
                "source": "default"
            }

        for product_id, data in DEFAULT_FUEL_PRICES.items():
            self.current_prices[product_id] = {
                **data,
                "price": round(data["price"] * self.regional_multiplier, 2),
                "category": InputCategory.FUEL,
                "source": "default"
            }

        for product_id, data in DEFAULT_APPLICATION_COSTS.items():
            self.current_prices[product_id] = {
                **data,
                "price": round(data["price"] * self.regional_multiplier, 2),
                "category": InputCategory.CUSTOM_APPLICATION,
                "source": "default"
            }

    def set_custom_price(
        self,
        product_id: str,
        price: float,
        supplier: Optional[str] = None,
        valid_until: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set a custom price from a supplier quote

        Args:
            product_id: Product identifier (e.g., 'urea_46', 'glyphosate_generic')
            price: Quoted price
            supplier: Supplier name
            valid_until: Quote expiration date
            notes: Additional notes

        Returns:
            Updated price record with comparison to default
        """
        if product_id not in self.current_prices:
            # Allow new products
            self.current_prices[product_id] = {
                "price": price,
                "unit": "unit",
                "description": product_id,
                "category": InputCategory.FERTILIZER,
                "source": "user_quote"
            }

        old_price = self.current_prices[product_id]["price"]

        # Update current price
        self.current_prices[product_id]["price"] = price
        self.current_prices[product_id]["source"] = "user_quote"
        self.current_prices[product_id]["supplier"] = supplier
        self.current_prices[product_id]["valid_until"] = valid_until
        self.current_prices[product_id]["date_updated"] = datetime.now()

        # Add to history
        record = PriceRecord(
            product_id=product_id,
            price=price,
            unit=self.current_prices[product_id]["unit"],
            source="user_quote",
            date_recorded=datetime.now(),
            supplier=supplier,
            notes=notes,
            valid_until=valid_until
        )

        if product_id not in self.price_history:
            self.price_history[product_id] = PriceHistory(product_id=product_id)
        self.price_history[product_id].add_price(record)

        # Store in supplier quotes
        self.supplier_quotes.append({
            "product_id": product_id,
            "supplier": supplier,
            "price": price,
            "date_quoted": datetime.now().isoformat(),
            "valid_until": valid_until.isoformat() if valid_until else None,
            "notes": notes
        })

        # Calculate savings vs default
        default_price = self._get_default_price(product_id)
        savings_vs_default = default_price - price if default_price else 0
        savings_pct = (savings_vs_default / default_price * 100) if default_price else 0

        return {
            "product_id": product_id,
            "new_price": price,
            "old_price": old_price,
            "default_price": default_price,
            "savings_vs_default": round(savings_vs_default, 2),
            "savings_percent": round(savings_pct, 1),
            "supplier": supplier,
            "valid_until": valid_until.isoformat() if valid_until else None,
            "message": f"Price updated. {'Saving' if savings_vs_default > 0 else 'Paying'} ${abs(savings_vs_default):.2f}/unit vs average."
        }

    def _get_default_price(self, product_id: str) -> Optional[float]:
        """Get the default regional price for a product"""
        # Check each default dictionary
        for defaults in [DEFAULT_FERTILIZER_PRICES, DEFAULT_PESTICIDE_PRICES,
                         DEFAULT_SEED_PRICES, DEFAULT_FUEL_PRICES, DEFAULT_APPLICATION_COSTS]:
            if product_id in defaults:
                return defaults[product_id]["price"] * self.regional_multiplier
        return None

    def get_price(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get current price for a product"""
        return self.current_prices.get(product_id)

    def get_all_prices(self, category: Optional[InputCategory] = None) -> Dict[str, Dict[str, Any]]:
        """Get all current prices, optionally filtered by category"""
        if category is None:
            return self.current_prices

        return {
            pid: data for pid, data in self.current_prices.items()
            if data.get("category") == category
        }

    def bulk_update_prices(
        self,
        price_updates: List[Dict[str, Any]],
        supplier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk update prices from a supplier quote sheet

        Args:
            price_updates: List of {product_id, price, notes}
            supplier: Supplier name for all updates

        Returns:
            Summary of updates with total savings
        """
        results = []
        total_savings = 0

        for update in price_updates:
            result = self.set_custom_price(
                product_id=update["product_id"],
                price=update["price"],
                supplier=supplier or update.get("supplier"),
                notes=update.get("notes")
            )
            results.append(result)
            total_savings += result.get("savings_vs_default", 0)

        return {
            "updates_processed": len(results),
            "total_potential_savings_per_unit": round(total_savings, 2),
            "supplier": supplier,
            "timestamp": datetime.now().isoformat(),
            "details": results
        }

    def compare_suppliers(
        self,
        product_ids: List[str],
        acres: float = 1.0
    ) -> Dict[str, Any]:
        """
        Compare prices across suppliers for given products

        Args:
            product_ids: Products to compare
            acres: Acres to calculate total cost
        """
        # Group quotes by supplier
        supplier_totals: Dict[str, float] = {}
        product_comparison: Dict[str, List[Dict]] = {}

        for pid in product_ids:
            product_comparison[pid] = []

            # Get current price (best available)
            current = self.current_prices.get(pid)
            if current:
                product_comparison[pid].append({
                    "supplier": current.get("supplier", "Default/Best"),
                    "price": current["price"],
                    "source": current.get("source", "default")
                })

                supplier = current.get("supplier", "Default")
                if supplier not in supplier_totals:
                    supplier_totals[supplier] = 0
                supplier_totals[supplier] += current["price"] * acres

            # Get historical quotes
            quotes = [q for q in self.supplier_quotes if q["product_id"] == pid]
            for quote in quotes:
                product_comparison[pid].append({
                    "supplier": quote["supplier"],
                    "price": quote["price"],
                    "date_quoted": quote["date_quoted"]
                })

        # Find cheapest supplier overall
        if supplier_totals:
            cheapest = min(supplier_totals.items(), key=lambda x: x[1])
            most_expensive = max(supplier_totals.items(), key=lambda x: x[1])
        else:
            cheapest = ("N/A", 0)
            most_expensive = ("N/A", 0)

        return {
            "products_compared": product_ids,
            "acres": acres,
            "product_breakdown": product_comparison,
            "supplier_totals": supplier_totals,
            "recommendation": {
                "cheapest_supplier": cheapest[0],
                "cheapest_total": round(cheapest[1], 2),
                "potential_savings": round(most_expensive[1] - cheapest[1], 2) if most_expensive[1] > 0 else 0
            }
        }

    def get_buy_recommendation(
        self,
        product_id: str,
        quantity_needed: float,
        purchase_deadline: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Recommend whether to buy now or wait based on price trends

        Args:
            product_id: Product to analyze
            quantity_needed: How much needed
            purchase_deadline: When product must be purchased by
        """
        current = self.current_prices.get(product_id)
        if not current:
            return {"error": f"Product {product_id} not found"}

        current_price = current["price"]
        history = self.price_history.get(product_id)

        if history and len(history.prices) >= 2:
            trend = history.get_trend()
            avg_90_day = history.get_average(90)
            avg_30_day = history.get_average(30)
        else:
            trend = PriceTrend.STABLE
            avg_90_day = current_price
            avg_30_day = current_price

        # Calculate costs
        current_total_cost = current_price * quantity_needed

        # Determine recommendation
        vs_90_avg = ((current_price - avg_90_day) / avg_90_day * 100) if avg_90_day else 0

        # Decision logic
        if trend == PriceTrend.FALLING and vs_90_avg > 5:
            recommendation = BuyRecommendation.WAIT
            reasoning = f"Prices trending down. Currently {vs_90_avg:.1f}% above 90-day average."
            action = "Consider waiting 2-4 weeks for better pricing"

        elif trend == PriceTrend.RISING and vs_90_avg < -5:
            recommendation = BuyRecommendation.BUY_NOW
            reasoning = f"Prices trending up. Currently {abs(vs_90_avg):.1f}% below 90-day average."
            action = "Buy now before prices increase further"

        elif trend == PriceTrend.RISING:
            recommendation = BuyRecommendation.CONSIDER_FORWARD_CONTRACT
            reasoning = "Prices rising. Consider locking in current price."
            action = "Ask supplier about forward contract or early booking discount"

        elif trend == PriceTrend.VOLATILE:
            recommendation = BuyRecommendation.SPLIT_PURCHASE
            reasoning = "Price volatility detected. Hedge by splitting purchase."
            action = "Buy 50% now, 50% in 30-60 days"

        else:
            recommendation = BuyRecommendation.BUY_NOW
            reasoning = "Prices stable and near average."
            action = "Purchase when convenient"

        # Check deadline urgency
        if purchase_deadline:
            days_until_deadline = (purchase_deadline - datetime.now()).days
            if days_until_deadline < 14:
                recommendation = BuyRecommendation.BUY_NOW
                action = f"Purchase soon - only {days_until_deadline} days until deadline"

        return {
            "product_id": product_id,
            "product_description": current.get("description", product_id),
            "current_price": current_price,
            "unit": current.get("unit", "unit"),
            "quantity_needed": quantity_needed,
            "current_total_cost": round(current_total_cost, 2),
            "price_analysis": {
                "trend": trend.value,
                "current_vs_90_day_avg_percent": round(vs_90_avg, 1),
                "avg_90_day": round(avg_90_day, 2),
                "avg_30_day": round(avg_30_day, 2)
            },
            "recommendation": recommendation.value,
            "reasoning": reasoning,
            "suggested_action": action,
            "potential_savings_if_wait": round(
                (current_price - avg_90_day) * quantity_needed, 2
            ) if vs_90_avg > 0 else 0
        }

    def calculate_input_costs(
        self,
        crop: str,
        acres: float,
        yield_goal: float,
        inputs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate total input costs using current (custom or default) prices

        Args:
            crop: Crop type
            acres: Field/farm acres
            yield_goal: Target yield
            inputs: List of {product_id, rate_per_acre} or {product_id, total_quantity}
        """
        line_items = []
        total_cost = 0

        for inp in inputs:
            product_id = inp.get("product_id")
            product_data = self.current_prices.get(product_id)

            if not product_data:
                line_items.append({
                    "product_id": product_id,
                    "error": "Product not found"
                })
                continue

            # Calculate quantity
            if "rate_per_acre" in inp:
                quantity = inp["rate_per_acre"] * acres
                rate_display = f"{inp['rate_per_acre']} {product_data['unit']}/acre"
            else:
                quantity = inp.get("total_quantity", 0)
                rate_display = f"{quantity} {product_data['unit']} total"

            item_cost = quantity * product_data["price"]
            cost_per_acre = item_cost / acres if acres > 0 else 0

            line_items.append({
                "product_id": product_id,
                "description": product_data.get("description", product_id),
                "rate": rate_display,
                "quantity": round(quantity, 2),
                "unit_price": product_data["price"],
                "unit": product_data["unit"],
                "total_cost": round(item_cost, 2),
                "cost_per_acre": round(cost_per_acre, 2),
                "source": product_data.get("source", "default"),
                "supplier": product_data.get("supplier")
            })

            total_cost += item_cost

        cost_per_acre = total_cost / acres if acres > 0 else 0
        cost_per_bushel = cost_per_acre / yield_goal if yield_goal > 0 else 0

        # Break-even calculation
        grain_prices = {"corn": 4.50, "soybean": 12.00, "wheat": 6.00}
        grain_price = grain_prices.get(crop.lower(), 5.00)
        break_even_yield = cost_per_acre / grain_price if grain_price > 0 else 0

        return {
            "crop": crop,
            "acres": acres,
            "yield_goal": yield_goal,
            "line_items": line_items,
            "summary": {
                "total_cost": round(total_cost, 2),
                "cost_per_acre": round(cost_per_acre, 2),
                "cost_per_bushel_goal": round(cost_per_bushel, 2),
                "grain_price_used": grain_price,
                "break_even_yield": round(break_even_yield, 1),
                "yield_goal_margin": round(yield_goal - break_even_yield, 1)
            },
            "price_sources": {
                "custom_prices_used": sum(1 for li in line_items if li.get("source") == "user_quote"),
                "default_prices_used": sum(1 for li in line_items if li.get("source") == "default")
            }
        }

    def get_price_alerts(self) -> List[Dict[str, Any]]:
        """Get alerts for expiring quotes and significant price changes"""
        alerts = []
        now = datetime.now()

        for product_id, data in self.current_prices.items():
            # Check for expiring quotes
            valid_until = data.get("valid_until")
            if valid_until and isinstance(valid_until, datetime):
                days_until_expiry = (valid_until - now).days
                if days_until_expiry <= 7 and days_until_expiry > 0:
                    alerts.append({
                        "type": "quote_expiring",
                        "product_id": product_id,
                        "description": data.get("description"),
                        "supplier": data.get("supplier"),
                        "days_until_expiry": days_until_expiry,
                        "message": f"Quote expires in {days_until_expiry} days"
                    })

            # Check for prices significantly above average
            history = self.price_history.get(product_id)
            if history:
                avg = history.get_average(90)
                current = data["price"]
                if avg > 0 and current > avg * 1.15:
                    alerts.append({
                        "type": "price_above_average",
                        "product_id": product_id,
                        "description": data.get("description"),
                        "current_price": current,
                        "average_price": round(avg, 2),
                        "percent_above": round((current - avg) / avg * 100, 1),
                        "message": f"Current price {((current - avg) / avg * 100):.1f}% above 90-day average"
                    })

        return alerts

    def generate_budget_prices(self, crop: str) -> Dict[str, Any]:
        """
        Generate a complete price list for budget planning
        Uses custom prices where available, defaults otherwise
        """
        budget_items = {
            "fertilizers": {},
            "pesticides": {},
            "seed": {},
            "fuel": {},
            "custom_application": {}
        }

        for product_id, data in self.current_prices.items():
            category = data.get("category")
            if category == InputCategory.FERTILIZER:
                budget_items["fertilizers"][product_id] = {
                    "price": data["price"],
                    "unit": data["unit"],
                    "description": data.get("description"),
                    "source": data.get("source")
                }
            elif category == InputCategory.PESTICIDE:
                budget_items["pesticides"][product_id] = {
                    "price": data["price"],
                    "unit": data["unit"],
                    "description": data.get("description"),
                    "source": data.get("source")
                }
            elif category == InputCategory.SEED:
                budget_items["seed"][product_id] = {
                    "price": data["price"],
                    "unit": data["unit"],
                    "description": data.get("description"),
                    "source": data.get("source")
                }
            elif category == InputCategory.FUEL:
                budget_items["fuel"][product_id] = {
                    "price": data["price"],
                    "unit": data["unit"],
                    "description": data.get("description"),
                    "source": data.get("source")
                }
            elif category == InputCategory.CUSTOM_APPLICATION:
                budget_items["custom_application"][product_id] = {
                    "price": data["price"],
                    "unit": data["unit"],
                    "description": data.get("description"),
                    "source": data.get("source")
                }

        return {
            "crop": crop,
            "region": self.region,
            "regional_multiplier": self.regional_multiplier,
            "generated_date": datetime.now().isoformat(),
            "prices": budget_items,
            "notes": [
                "Prices marked 'user_quote' are from your supplier quotes",
                "Prices marked 'default' are regional averages",
                "Use set_custom_price() to update with actual quotes"
            ]
        }


# Singleton instance
_pricing_service = None


def get_pricing_service(region: str = "midwest_corn_belt") -> PricingService:
    """Get or create pricing service instance"""
    global _pricing_service
    if _pricing_service is None or _pricing_service.region != region:
        _pricing_service = PricingService(region=region)
    return _pricing_service


# Example usage
if __name__ == "__main__":
    service = PricingService(region="midwest_corn_belt")

    print("=== PRICING SERVICE DEMO ===\n")

    # Show default fertilizer prices
    print("Default Fertilizer Prices:")
    fert_prices = service.get_all_prices(InputCategory.FERTILIZER)
    for pid, data in list(fert_prices.items())[:5]:
        print(f"  {data['description']}: ${data['price']}/{data['unit']}")

    # Add custom quote
    print("\n--- Adding Supplier Quote ---")
    result = service.set_custom_price(
        product_id="urea_46",
        price=0.48,
        supplier="Local Co-op",
        notes="Early booking discount"
    )
    print(f"Updated: {result['message']}")
    print(f"Savings: ${result['savings_vs_default']}/unit ({result['savings_percent']}%)")

    # Get buy recommendation
    print("\n--- Buy Recommendation ---")
    rec = service.get_buy_recommendation(
        product_id="urea_46",
        quantity_needed=100000  # lbs
    )
    print(f"Product: {rec['product_description']}")
    print(f"Recommendation: {rec['recommendation']}")
    print(f"Reasoning: {rec['reasoning']}")
    print(f"Action: {rec['suggested_action']}")

    # Calculate input costs
    print("\n--- Input Cost Calculation ---")
    costs = service.calculate_input_costs(
        crop="corn",
        acres=500,
        yield_goal=200,
        inputs=[
            {"product_id": "urea_46", "rate_per_acre": 200},
            {"product_id": "dap_18_46", "rate_per_acre": 150},
            {"product_id": "potash_60", "rate_per_acre": 100}
        ]
    )
    print(f"Total Cost: ${costs['summary']['total_cost']:,.2f}")
    print(f"Cost/Acre: ${costs['summary']['cost_per_acre']:.2f}")
    print(f"Break-even Yield: {costs['summary']['break_even_yield']:.1f} bu/acre")
