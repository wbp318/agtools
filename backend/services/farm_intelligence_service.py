"""
Elite Farm Intelligence Service for AgTools
Version: 3.8.0

Comprehensive farm intelligence featuring:
- Market Intelligence Suite (commodity prices, basis, forward contracting)
- Crop Insurance Tools (coverage analysis, loss documentation)
- Soil Health Dashboard (multi-year tracking, trend analysis)
- Lender/Investor Reporting (professional financial reports)
- Harvest Analytics (yield analysis, field comparisons, trends)
- Input Procurement Optimizer (supplier comparison, order tracking)
"""

from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import statistics


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

# ----- Market Intelligence -----

class Commodity(Enum):
    """Tradeable commodities"""
    CORN = "corn"
    SOYBEANS = "soybeans"
    WHEAT = "wheat"
    RICE = "rice"
    COTTON = "cotton"
    SORGHUM = "sorghum"


class ContractMonth(Enum):
    """Futures contract months"""
    JAN = "F"
    MAR = "H"
    MAY = "K"
    JUL = "N"
    SEP = "U"
    DEC = "Z"


class ContractStatus(Enum):
    """Forward contract status"""
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class CommodityPrice:
    """Current commodity price data"""
    commodity: Commodity
    cash_price: float
    futures_price: float
    basis: float
    as_of_date: date
    delivery_location: str
    futures_month: str


@dataclass
class ForwardContract:
    """Forward contract record"""
    id: str
    commodity: Commodity
    bushels: float
    contract_price: float
    delivery_start: date
    delivery_end: date
    buyer: str
    contract_number: str
    status: ContractStatus
    created_date: date
    notes: str


@dataclass
class BasisHistory:
    """Historical basis record"""
    commodity: Commodity
    date: date
    cash_price: float
    futures_price: float
    basis: float
    location: str


# ----- Crop Insurance -----

class InsuranceType(Enum):
    """Crop insurance types"""
    YP = "yield_protection"
    RP = "revenue_protection"
    RP_HPE = "revenue_protection_harvest_price_exclusion"
    ARC_CO = "arc_county"
    PLC = "plc"
    SCO = "sco"
    ECO = "eco"


class CoverageLevel(Enum):
    """Coverage levels"""
    L50 = 50
    L55 = 55
    L60 = 60
    L65 = 65
    L70 = 70
    L75 = 75
    L80 = 80
    L85 = 85


@dataclass
class InsurancePolicy:
    """Crop insurance policy"""
    id: str
    crop_year: int
    crop: Commodity
    insurance_type: InsuranceType
    coverage_level: int
    acres: float
    aph_yield: float  # Actual Production History
    projected_price: float
    premium: float
    subsidy_pct: float
    producer_premium: float
    liability: float
    guarantee_bushels: float
    guarantee_revenue: float


@dataclass
class LossRecord:
    """Crop loss documentation"""
    id: str
    policy_id: str
    crop_year: int
    field_name: str
    acres_affected: float
    cause_of_loss: str
    date_of_loss: date
    date_reported: date
    estimated_loss_pct: float
    appraised_yield: Optional[float]
    documentation: List[str]
    adjuster_notes: str
    status: str  # reported, appraised, settled


# ----- Soil Health -----

@dataclass
class SoilTest:
    """Soil test result"""
    id: str
    field_id: str
    field_name: str
    sample_date: date
    lab_name: str
    sample_depth: str
    # Macronutrients
    ph: float
    organic_matter_pct: float
    nitrogen_ppm: float
    phosphorus_ppm: float
    potassium_ppm: float
    # Secondary
    calcium_ppm: float
    magnesium_ppm: float
    sulfur_ppm: float
    # Micronutrients
    zinc_ppm: float
    manganese_ppm: float
    iron_ppm: float
    copper_ppm: float
    boron_ppm: float
    # Physical
    cec: float  # Cation Exchange Capacity
    base_saturation_pct: float
    # Biological (optional)
    soil_respiration: Optional[float]
    active_carbon: Optional[float]


# ----- Harvest Analytics -----

@dataclass
class HarvestRecord:
    """Field harvest record"""
    id: str
    field_id: str
    field_name: str
    crop: Commodity
    crop_year: int
    harvest_date: date
    acres_harvested: float
    total_yield: float  # bushels or lbs
    yield_per_acre: float
    moisture_pct: float
    test_weight: float
    quality_notes: str
    storage_location: str


# ----- Input Procurement -----

class InputCategory(Enum):
    """Input categories"""
    SEED = "seed"
    FERTILIZER = "fertilizer"
    CHEMICAL = "chemical"
    FUEL = "fuel"
    PARTS = "parts"
    CUSTOM_SERVICES = "custom_services"


@dataclass
class Supplier:
    """Supplier record"""
    id: str
    name: str
    categories: List[InputCategory]
    contact_name: str
    phone: str
    email: str
    address: str
    payment_terms: str
    notes: str


@dataclass
class PurchaseOrder:
    """Purchase order"""
    id: str
    supplier_id: str
    supplier_name: str
    order_date: date
    expected_delivery: date
    category: InputCategory
    items: List[Dict[str, Any]]
    subtotal: float
    tax: float
    shipping: float
    total: float
    status: str  # draft, ordered, shipped, received, cancelled
    notes: str


@dataclass
class PriceQuote:
    """Supplier price quote"""
    id: str
    supplier_id: str
    supplier_name: str
    product_name: str
    category: InputCategory
    unit_price: float
    unit: str
    min_quantity: float
    quote_date: date
    valid_until: date
    notes: str


# =============================================================================
# MARKET DATA (Simulated - would connect to real feeds in production)
# =============================================================================

# Current market prices (December 2025 estimates)
CURRENT_PRICES = {
    Commodity.CORN: {
        "cash": 4.45,
        "futures": 4.52,
        "basis": -0.07,
        "unit": "bu"
    },
    Commodity.SOYBEANS: {
        "cash": 10.25,
        "futures": 10.45,
        "basis": -0.20,
        "unit": "bu"
    },
    Commodity.WHEAT: {
        "cash": 5.35,
        "futures": 5.55,
        "basis": -0.20,
        "unit": "bu"
    },
    Commodity.RICE: {
        "cash": 14.50,
        "futures": 14.75,
        "basis": -0.25,
        "unit": "cwt"
    },
    Commodity.COTTON: {
        "cash": 0.72,
        "futures": 0.74,
        "basis": -0.02,
        "unit": "lb"
    },
    Commodity.SORGHUM: {
        "cash": 4.10,
        "futures": 4.25,
        "basis": -0.15,
        "unit": "bu"
    },
}

# Historical basis averages by month
HISTORICAL_BASIS = {
    Commodity.CORN: {
        1: -0.15, 2: -0.12, 3: -0.10, 4: -0.08, 5: -0.05,
        6: -0.03, 7: 0.00, 8: -0.02, 9: -0.05, 10: -0.08,
        11: -0.10, 12: -0.12
    },
    Commodity.SOYBEANS: {
        1: -0.25, 2: -0.22, 3: -0.18, 4: -0.15, 5: -0.12,
        6: -0.10, 7: -0.08, 8: -0.10, 9: -0.15, 10: -0.20,
        11: -0.22, 12: -0.25
    },
}

# Insurance premium rates (simplified)
INSURANCE_RATES = {
    Commodity.CORN: {
        50: 0.015, 55: 0.018, 60: 0.022, 65: 0.028,
        70: 0.035, 75: 0.045, 80: 0.060, 85: 0.080
    },
    Commodity.SOYBEANS: {
        50: 0.018, 55: 0.022, 60: 0.027, 65: 0.034,
        70: 0.042, 75: 0.055, 80: 0.072, 85: 0.095
    },
}

# Soil test optimal ranges
SOIL_OPTIMAL_RANGES = {
    "ph": {"low": 6.0, "optimal_low": 6.2, "optimal_high": 6.8, "high": 7.2},
    "organic_matter_pct": {"low": 2.0, "optimal_low": 3.0, "optimal_high": 5.0, "high": 8.0},
    "phosphorus_ppm": {"low": 15, "optimal_low": 25, "optimal_high": 50, "high": 100},
    "potassium_ppm": {"low": 100, "optimal_low": 150, "optimal_high": 250, "high": 400},
    "cec": {"low": 8, "optimal_low": 12, "optimal_high": 25, "high": 40},
}


# =============================================================================
# FARM INTELLIGENCE SERVICE CLASS
# =============================================================================

class FarmIntelligenceService:
    """Elite farm intelligence service"""

    def __init__(self):
        # Market Intelligence
        self.price_history: List[CommodityPrice] = []
        self.forward_contracts: Dict[str, ForwardContract] = {}
        self.basis_history: List[BasisHistory] = []

        # Crop Insurance
        self.policies: Dict[str, InsurancePolicy] = {}
        self.loss_records: Dict[str, LossRecord] = {}

        # Soil Health
        self.soil_tests: Dict[str, SoilTest] = {}

        # Harvest Analytics
        self.harvest_records: Dict[str, HarvestRecord] = {}

        # Input Procurement
        self.suppliers: Dict[str, Supplier] = {}
        self.purchase_orders: Dict[str, PurchaseOrder] = {}
        self.price_quotes: Dict[str, PriceQuote] = {}

        self._counters = {
            "contract": 0, "policy": 0, "loss": 0, "soil": 0,
            "harvest": 0, "supplier": 0, "po": 0, "quote": 0
        }

    def _next_id(self, prefix: str) -> str:
        self._counters[prefix] += 1
        return f"{prefix.upper()}-{self._counters[prefix]:04d}"

    # =========================================================================
    # MARKET INTELLIGENCE SUITE
    # =========================================================================

    def get_current_prices(self, commodity: str = None) -> Dict[str, Any]:
        """Get current commodity prices"""
        if commodity:
            try:
                comm = Commodity(commodity)
                prices = CURRENT_PRICES[comm]
                return {
                    "commodity": commodity,
                    "cash_price": prices["cash"],
                    "futures_price": prices["futures"],
                    "basis": prices["basis"],
                    "unit": prices["unit"],
                    "as_of": date.today().isoformat(),
                    "source": "Market simulation"
                }
            except (ValueError, KeyError):
                return {"error": f"Unknown commodity: {commodity}"}

        return {
            "as_of": date.today().isoformat(),
            "prices": {
                comm.value: {
                    "cash": info["cash"],
                    "futures": info["futures"],
                    "basis": info["basis"],
                    "unit": info["unit"]
                }
                for comm, info in CURRENT_PRICES.items()
            }
        }

    def get_basis_analysis(self, commodity: str, location: str = "Local") -> Dict[str, Any]:
        """Analyze current vs historical basis"""
        try:
            comm = Commodity(commodity)
        except ValueError:
            return {"error": f"Unknown commodity: {commodity}"}

        current_month = date.today().month
        current_basis = CURRENT_PRICES[comm]["basis"]

        hist_basis = HISTORICAL_BASIS.get(comm, {})
        avg_basis = hist_basis.get(current_month, current_basis)

        # Calculate basis strength
        basis_vs_avg = current_basis - avg_basis
        if basis_vs_avg > 0.05:
            strength = "strong"
            recommendation = "Consider selling cash grain - basis is stronger than average"
        elif basis_vs_avg < -0.05:
            strength = "weak"
            recommendation = "Consider storing or using hedge-to-arrive - basis is weaker than average"
        else:
            strength = "normal"
            recommendation = "Basis is near historical average - evaluate other factors"

        return {
            "commodity": commodity,
            "location": location,
            "current_basis": current_basis,
            "historical_avg_basis": avg_basis,
            "basis_vs_average": round(basis_vs_avg, 3),
            "strength": strength,
            "recommendation": recommendation,
            "monthly_history": {
                f"Month {m}": b for m, b in hist_basis.items()
            } if hist_basis else None
        }

    def create_forward_contract(
        self,
        commodity: str,
        bushels: float,
        contract_price: float,
        delivery_start: date,
        delivery_end: date,
        buyer: str,
        contract_number: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Create a forward contract"""
        try:
            comm = Commodity(commodity)
        except ValueError:
            return {"error": f"Unknown commodity: {commodity}"}

        contract_id = self._next_id("contract")

        contract = ForwardContract(
            id=contract_id,
            commodity=comm,
            bushels=bushels,
            contract_price=contract_price,
            delivery_start=delivery_start,
            delivery_end=delivery_end,
            buyer=buyer,
            contract_number=contract_number,
            status=ContractStatus.OPEN,
            created_date=date.today(),
            notes=notes
        )

        self.forward_contracts[contract_id] = contract

        # Calculate contract value
        contract_value = bushels * contract_price
        current_cash = CURRENT_PRICES[comm]["cash"]
        current_value = bushels * current_cash
        gain_loss = contract_value - current_value

        return {
            "id": contract_id,
            "commodity": commodity,
            "bushels": bushels,
            "contract_price": contract_price,
            "delivery_period": f"{delivery_start.isoformat()} to {delivery_end.isoformat()}",
            "buyer": buyer,
            "contract_number": contract_number,
            "contract_value": round(contract_value, 2),
            "current_market_value": round(current_value, 2),
            "gain_loss_vs_market": round(gain_loss, 2),
            "status": "open",
            "message": f"Forward contract created for {bushels:,.0f} bu at ${contract_price:.2f}"
        }

    def get_marketing_summary(self) -> Dict[str, Any]:
        """Get summary of all forward contracts and marketing position"""
        by_commodity = {}

        for contract in self.forward_contracts.values():
            if contract.status != ContractStatus.OPEN:
                continue

            comm = contract.commodity.value
            if comm not in by_commodity:
                by_commodity[comm] = {
                    "total_bushels": 0,
                    "total_value": 0,
                    "avg_price": 0,
                    "contracts": []
                }

            by_commodity[comm]["total_bushels"] += contract.bushels
            by_commodity[comm]["total_value"] += contract.bushels * contract.contract_price
            by_commodity[comm]["contracts"].append({
                "id": contract.id,
                "bushels": contract.bushels,
                "price": contract.contract_price,
                "buyer": contract.buyer,
                "delivery": contract.delivery_start.isoformat()
            })

        # Calculate averages
        for comm, data in by_commodity.items():
            if data["total_bushels"] > 0:
                data["avg_price"] = round(data["total_value"] / data["total_bushels"], 4)
            data["total_value"] = round(data["total_value"], 2)

        return {
            "as_of": date.today().isoformat(),
            "open_contracts": len([c for c in self.forward_contracts.values()
                                  if c.status == ContractStatus.OPEN]),
            "by_commodity": by_commodity,
            "total_contracted_value": sum(d["total_value"] for d in by_commodity.values())
        }

    def calculate_marketing_plan(
        self,
        commodity: str,
        expected_production: float,
        target_avg_price: float
    ) -> Dict[str, Any]:
        """Calculate marketing plan to achieve target average price"""
        try:
            comm = Commodity(commodity)
        except ValueError:
            return {"error": f"Unknown commodity: {commodity}"}

        current_price = CURRENT_PRICES[comm]["cash"]

        # Get already contracted bushels
        contracted = 0
        contracted_value = 0
        for contract in self.forward_contracts.values():
            if contract.commodity == comm and contract.status == ContractStatus.OPEN:
                contracted += contract.bushels
                contracted_value += contract.bushels * contract.contract_price

        remaining = expected_production - contracted
        pct_contracted = contracted / expected_production * 100 if expected_production > 0 else 0

        # Calculate needed price for remaining bushels
        if remaining > 0:
            needed_revenue = target_avg_price * expected_production
            needed_remaining_revenue = needed_revenue - contracted_value
            needed_price_remaining = needed_remaining_revenue / remaining
        else:
            needed_price_remaining = 0

        # Generate recommendations
        recommendations = []
        if pct_contracted < 25:
            recommendations.append("Consider contracting 25-50% of expected production to lock in profitability")
        if current_price > target_avg_price:
            recommendations.append(f"Current price (${current_price:.2f}) exceeds target - good time to contract")
        if needed_price_remaining > current_price * 1.2:
            recommendations.append("Warning: Remaining bushels need price 20%+ above current market to hit target")

        return {
            "commodity": commodity,
            "expected_production": expected_production,
            "target_avg_price": target_avg_price,
            "current_market_price": current_price,
            "contracted": {
                "bushels": contracted,
                "value": round(contracted_value, 2),
                "avg_price": round(contracted_value / contracted, 4) if contracted > 0 else 0,
                "pct_of_production": round(pct_contracted, 1)
            },
            "remaining": {
                "bushels": remaining,
                "needed_avg_price": round(needed_price_remaining, 4),
                "at_current_market": round(remaining * current_price, 2)
            },
            "projected_revenue": {
                "at_target": round(expected_production * target_avg_price, 2),
                "at_current_market": round(contracted_value + remaining * current_price, 2)
            },
            "recommendations": recommendations
        }

    # =========================================================================
    # CROP INSURANCE TOOLS
    # =========================================================================

    def get_insurance_options(
        self,
        crop: str,
        acres: float,
        aph_yield: float,
        projected_price: float
    ) -> Dict[str, Any]:
        """Compare crop insurance coverage options"""
        try:
            comm = Commodity(crop)
        except ValueError:
            return {"error": f"Unknown crop: {crop}"}

        rates = INSURANCE_RATES.get(comm, INSURANCE_RATES[Commodity.CORN])
        subsidy_rates = {50: 0.67, 55: 0.64, 60: 0.64, 65: 0.59, 70: 0.59, 75: 0.55, 80: 0.48, 85: 0.38}

        options = []
        for level, rate in rates.items():
            guarantee_bushels = aph_yield * (level / 100)
            guarantee_revenue = guarantee_bushels * projected_price * acres
            liability = aph_yield * projected_price * acres * (level / 100)
            premium = liability * rate
            subsidy = premium * subsidy_rates[level]
            producer_premium = premium - subsidy

            options.append({
                "coverage_level": f"{level}%",
                "guarantee_yield": round(guarantee_bushels, 1),
                "guarantee_revenue": round(guarantee_revenue, 2),
                "liability": round(liability, 2),
                "total_premium": round(premium, 2),
                "subsidy": round(subsidy, 2),
                "producer_premium": round(producer_premium, 2),
                "premium_per_acre": round(producer_premium / acres, 2),
                "protection_per_dollar": round(liability / producer_premium, 1) if producer_premium > 0 else 0
            })

        # Find best value
        best_value = max(options, key=lambda x: x["protection_per_dollar"])

        return {
            "crop": crop,
            "acres": acres,
            "aph_yield": aph_yield,
            "projected_price": projected_price,
            "options": options,
            "recommendation": {
                "best_value_level": best_value["coverage_level"],
                "reason": f"${best_value['protection_per_dollar']:.0f} liability per $1 premium"
            }
        }

    def create_insurance_policy(
        self,
        crop: str,
        crop_year: int,
        insurance_type: str,
        coverage_level: int,
        acres: float,
        aph_yield: float,
        projected_price: float
    ) -> Dict[str, Any]:
        """Create an insurance policy record"""
        try:
            comm = Commodity(crop)
            ins_type = InsuranceType(insurance_type)
        except ValueError as e:
            return {"error": str(e)}

        policy_id = self._next_id("policy")

        rates = INSURANCE_RATES.get(comm, INSURANCE_RATES[Commodity.CORN])
        rate = rates.get(coverage_level, 0.05)
        subsidy_rates = {50: 0.67, 55: 0.64, 60: 0.64, 65: 0.59, 70: 0.59, 75: 0.55, 80: 0.48, 85: 0.38}

        guarantee_bushels = aph_yield * (coverage_level / 100) * acres
        guarantee_revenue = guarantee_bushels * projected_price
        liability = aph_yield * projected_price * acres * (coverage_level / 100)
        premium = liability * rate
        subsidy_pct = subsidy_rates.get(coverage_level, 0.50)
        producer_premium = premium * (1 - subsidy_pct)

        policy = InsurancePolicy(
            id=policy_id,
            crop_year=crop_year,
            crop=comm,
            insurance_type=ins_type,
            coverage_level=coverage_level,
            acres=acres,
            aph_yield=aph_yield,
            projected_price=projected_price,
            premium=premium,
            subsidy_pct=subsidy_pct,
            producer_premium=producer_premium,
            liability=liability,
            guarantee_bushels=guarantee_bushels,
            guarantee_revenue=guarantee_revenue
        )

        self.policies[policy_id] = policy

        return {
            "id": policy_id,
            "crop": crop,
            "crop_year": crop_year,
            "insurance_type": insurance_type,
            "coverage_level": f"{coverage_level}%",
            "acres": acres,
            "guarantee": {
                "bushels": round(guarantee_bushels, 1),
                "revenue": round(guarantee_revenue, 2)
            },
            "premium": {
                "total": round(premium, 2),
                "subsidy_pct": f"{subsidy_pct * 100:.0f}%",
                "producer_pays": round(producer_premium, 2),
                "per_acre": round(producer_premium / acres, 2)
            },
            "liability": round(liability, 2),
            "message": f"Policy created: {coverage_level}% RP on {acres} acres"
        }

    def record_loss(
        self,
        policy_id: str,
        field_name: str,
        acres_affected: float,
        cause_of_loss: str,
        date_of_loss: date,
        estimated_loss_pct: float,
        documentation: List[str] = None
    ) -> Dict[str, Any]:
        """Record a crop loss for insurance claim"""
        if policy_id not in self.policies:
            return {"error": f"Policy {policy_id} not found"}

        policy = self.policies[policy_id]
        loss_id = self._next_id("loss")

        loss = LossRecord(
            id=loss_id,
            policy_id=policy_id,
            crop_year=policy.crop_year,
            field_name=field_name,
            acres_affected=acres_affected,
            cause_of_loss=cause_of_loss,
            date_of_loss=date_of_loss,
            date_reported=date.today(),
            estimated_loss_pct=estimated_loss_pct,
            appraised_yield=None,
            documentation=documentation or [],
            adjuster_notes="",
            status="reported"
        )

        self.loss_records[loss_id] = loss

        # Estimate potential indemnity
        expected_yield = policy.aph_yield * (1 - estimated_loss_pct / 100)
        guarantee_yield = policy.aph_yield * (policy.coverage_level / 100)

        if expected_yield < guarantee_yield:
            yield_loss = guarantee_yield - expected_yield
            estimated_indemnity = yield_loss * policy.projected_price * acres_affected
        else:
            estimated_indemnity = 0

        return {
            "id": loss_id,
            "policy_id": policy_id,
            "field_name": field_name,
            "acres_affected": acres_affected,
            "cause_of_loss": cause_of_loss,
            "date_of_loss": date_of_loss.isoformat(),
            "estimated_loss_pct": estimated_loss_pct,
            "estimated_indemnity": round(estimated_indemnity, 2),
            "status": "reported",
            "next_steps": [
                "Contact insurance agent to report loss",
                "Do not destroy evidence of loss",
                "Take photos of damaged crop",
                "Wait for adjuster appointment"
            ],
            "message": f"Loss recorded - estimated indemnity ${estimated_indemnity:,.2f}"
        }

    def calculate_indemnity_scenarios(
        self,
        policy_id: str,
        yield_scenarios: List[float],
        harvest_price: float = None
    ) -> Dict[str, Any]:
        """Calculate potential indemnity payments for different yield scenarios"""
        if policy_id not in self.policies:
            return {"error": f"Policy {policy_id} not found"}

        policy = self.policies[policy_id]
        harvest_price = harvest_price or policy.projected_price

        scenarios = []
        for actual_yield in yield_scenarios:
            # Yield Protection calculation
            guarantee_yield = policy.aph_yield * (policy.coverage_level / 100)

            if actual_yield < guarantee_yield:
                yield_loss = guarantee_yield - actual_yield
                # For RP, use higher of projected or harvest price
                price_for_calc = max(policy.projected_price, harvest_price)
                indemnity = yield_loss * price_for_calc * policy.acres
            else:
                indemnity = 0

            scenarios.append({
                "actual_yield": actual_yield,
                "pct_of_aph": round(actual_yield / policy.aph_yield * 100, 1),
                "yield_shortfall": round(max(0, guarantee_yield - actual_yield), 1),
                "indemnity": round(indemnity, 2),
                "indemnity_per_acre": round(indemnity / policy.acres, 2)
            })

        return {
            "policy_id": policy_id,
            "crop": policy.crop.value,
            "coverage_level": f"{policy.coverage_level}%",
            "aph_yield": policy.aph_yield,
            "guarantee_yield": round(policy.aph_yield * policy.coverage_level / 100, 1),
            "projected_price": policy.projected_price,
            "harvest_price_used": harvest_price,
            "scenarios": scenarios
        }

    # =========================================================================
    # SOIL HEALTH DASHBOARD
    # =========================================================================

    def record_soil_test(
        self,
        field_id: str,
        field_name: str,
        sample_date: date,
        lab_name: str,
        ph: float,
        organic_matter_pct: float,
        phosphorus_ppm: float,
        potassium_ppm: float,
        nitrogen_ppm: float = 0,
        calcium_ppm: float = 0,
        magnesium_ppm: float = 0,
        sulfur_ppm: float = 0,
        zinc_ppm: float = 0,
        cec: float = 0,
        sample_depth: str = "0-6 inches",
        **kwargs
    ) -> Dict[str, Any]:
        """Record soil test results"""
        test_id = self._next_id("soil")

        test = SoilTest(
            id=test_id,
            field_id=field_id,
            field_name=field_name,
            sample_date=sample_date,
            lab_name=lab_name,
            sample_depth=sample_depth,
            ph=ph,
            organic_matter_pct=organic_matter_pct,
            nitrogen_ppm=nitrogen_ppm,
            phosphorus_ppm=phosphorus_ppm,
            potassium_ppm=potassium_ppm,
            calcium_ppm=calcium_ppm,
            magnesium_ppm=magnesium_ppm,
            sulfur_ppm=sulfur_ppm,
            zinc_ppm=zinc_ppm,
            manganese_ppm=kwargs.get("manganese_ppm", 0),
            iron_ppm=kwargs.get("iron_ppm", 0),
            copper_ppm=kwargs.get("copper_ppm", 0),
            boron_ppm=kwargs.get("boron_ppm", 0),
            cec=cec,
            base_saturation_pct=kwargs.get("base_saturation_pct", 0),
            soil_respiration=kwargs.get("soil_respiration"),
            active_carbon=kwargs.get("active_carbon")
        )

        self.soil_tests[test_id] = test

        # Interpret results
        interpretations = self._interpret_soil_test(test)

        return {
            "id": test_id,
            "field_id": field_id,
            "field_name": field_name,
            "sample_date": sample_date.isoformat(),
            "results": {
                "ph": ph,
                "organic_matter": f"{organic_matter_pct}%",
                "phosphorus": f"{phosphorus_ppm} ppm",
                "potassium": f"{potassium_ppm} ppm",
                "cec": cec
            },
            "interpretations": interpretations,
            "message": f"Soil test recorded for {field_name}"
        }

    def _interpret_soil_test(self, test: SoilTest) -> List[Dict[str, str]]:
        """Interpret soil test results"""
        interpretations = []

        # pH interpretation
        if test.ph < 6.0:
            interpretations.append({
                "parameter": "pH",
                "value": test.ph,
                "status": "low",
                "recommendation": "Consider lime application to raise pH"
            })
        elif test.ph > 7.2:
            interpretations.append({
                "parameter": "pH",
                "value": test.ph,
                "status": "high",
                "recommendation": "High pH may limit micronutrient availability"
            })
        else:
            interpretations.append({
                "parameter": "pH",
                "value": test.ph,
                "status": "optimal",
                "recommendation": "pH is in optimal range"
            })

        # Organic matter
        if test.organic_matter_pct < 2.0:
            interpretations.append({
                "parameter": "Organic Matter",
                "value": f"{test.organic_matter_pct}%",
                "status": "low",
                "recommendation": "Increase OM with cover crops, reduced tillage, or manure"
            })
        elif test.organic_matter_pct >= 3.0:
            interpretations.append({
                "parameter": "Organic Matter",
                "value": f"{test.organic_matter_pct}%",
                "status": "good",
                "recommendation": "Continue practices to maintain OM levels"
            })

        # Phosphorus
        if test.phosphorus_ppm < 15:
            interpretations.append({
                "parameter": "Phosphorus",
                "value": f"{test.phosphorus_ppm} ppm",
                "status": "low",
                "recommendation": "Apply phosphorus fertilizer at planting"
            })
        elif test.phosphorus_ppm > 50:
            interpretations.append({
                "parameter": "Phosphorus",
                "value": f"{test.phosphorus_ppm} ppm",
                "status": "high",
                "recommendation": "Can reduce P application, focus on N and K"
            })

        # Potassium
        if test.potassium_ppm < 100:
            interpretations.append({
                "parameter": "Potassium",
                "value": f"{test.potassium_ppm} ppm",
                "status": "low",
                "recommendation": "Apply potash fertilizer"
            })

        return interpretations

    def get_soil_health_trend(self, field_id: str) -> Dict[str, Any]:
        """Get soil health trends over time for a field"""
        field_tests = sorted(
            [t for t in self.soil_tests.values() if t.field_id == field_id],
            key=lambda x: x.sample_date
        )

        if not field_tests:
            return {"error": f"No soil tests found for field {field_id}"}

        if len(field_tests) == 1:
            test = field_tests[0]
            return {
                "field_id": field_id,
                "field_name": test.field_name,
                "tests_count": 1,
                "message": "Only one test available - need more tests for trend analysis",
                "latest_results": {
                    "date": test.sample_date.isoformat(),
                    "ph": test.ph,
                    "organic_matter": test.organic_matter_pct,
                    "phosphorus": test.phosphorus_ppm,
                    "potassium": test.potassium_ppm
                }
            }

        # Calculate trends
        first = field_tests[0]
        last = field_tests[-1]
        years = (last.sample_date - first.sample_date).days / 365

        trends = {
            "ph": {
                "first": first.ph,
                "latest": last.ph,
                "change": round(last.ph - first.ph, 2),
                "trend": "improving" if last.ph > first.ph and first.ph < 6.5 else
                        "stable" if abs(last.ph - first.ph) < 0.2 else "declining"
            },
            "organic_matter": {
                "first": first.organic_matter_pct,
                "latest": last.organic_matter_pct,
                "change": round(last.organic_matter_pct - first.organic_matter_pct, 2),
                "trend": "improving" if last.organic_matter_pct > first.organic_matter_pct else
                        "stable" if abs(last.organic_matter_pct - first.organic_matter_pct) < 0.2 else "declining"
            },
            "phosphorus": {
                "first": first.phosphorus_ppm,
                "latest": last.phosphorus_ppm,
                "change": round(last.phosphorus_ppm - first.phosphorus_ppm, 1),
                "trend": "building" if last.phosphorus_ppm > first.phosphorus_ppm else "drawing down"
            },
            "potassium": {
                "first": first.potassium_ppm,
                "latest": last.potassium_ppm,
                "change": round(last.potassium_ppm - first.potassium_ppm, 1),
                "trend": "building" if last.potassium_ppm > first.potassium_ppm else "drawing down"
            }
        }

        # Soil health score (0-100)
        score = 0
        if 6.0 <= last.ph <= 7.0:
            score += 25
        elif 5.5 <= last.ph <= 7.5:
            score += 15

        if last.organic_matter_pct >= 3.0:
            score += 25
        elif last.organic_matter_pct >= 2.0:
            score += 15

        if 25 <= last.phosphorus_ppm <= 50:
            score += 25
        elif 15 <= last.phosphorus_ppm <= 100:
            score += 15

        if 150 <= last.potassium_ppm <= 250:
            score += 25
        elif 100 <= last.potassium_ppm <= 400:
            score += 15

        return {
            "field_id": field_id,
            "field_name": last.field_name,
            "analysis_period": f"{first.sample_date.isoformat()} to {last.sample_date.isoformat()}",
            "years_of_data": round(years, 1),
            "tests_count": len(field_tests),
            "soil_health_score": score,
            "score_grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F",
            "trends": trends,
            "grant_summary": f"Soil health improved from score {self._calc_score(first)} to {score} over {round(years, 1)} years"
        }

    def _calc_score(self, test: SoilTest) -> int:
        """Calculate soil health score for a single test"""
        score = 0
        if 6.0 <= test.ph <= 7.0:
            score += 25
        elif 5.5 <= test.ph <= 7.5:
            score += 15
        if test.organic_matter_pct >= 3.0:
            score += 25
        elif test.organic_matter_pct >= 2.0:
            score += 15
        if 25 <= test.phosphorus_ppm <= 50:
            score += 25
        elif 15 <= test.phosphorus_ppm <= 100:
            score += 15
        if 150 <= test.potassium_ppm <= 250:
            score += 25
        elif 100 <= test.potassium_ppm <= 400:
            score += 15
        return score

    # =========================================================================
    # LENDER/INVESTOR REPORTING
    # =========================================================================

    def generate_lender_report(
        self,
        farm_name: str,
        operator_name: str,
        total_acres: float,
        crops: Dict[str, float],  # crop: acres
        year: int = None
    ) -> Dict[str, Any]:
        """Generate professional report for agricultural lenders"""
        if year is None:
            year = date.today().year

        # Calculate projected revenue
        revenue_by_crop = []
        total_revenue = 0
        for crop, acres in crops.items():
            try:
                comm = Commodity(crop)
                price = CURRENT_PRICES[comm]["cash"]
                # Use Louisiana average yields
                yields = {"corn": 180, "soybeans": 50, "rice": 7200, "cotton": 1100, "wheat": 55}
                exp_yield = yields.get(crop, 100)
                crop_revenue = acres * exp_yield * price

                revenue_by_crop.append({
                    "crop": crop,
                    "acres": acres,
                    "expected_yield": exp_yield,
                    "price": price,
                    "projected_revenue": round(crop_revenue, 2)
                })
                total_revenue += crop_revenue
            except (ValueError, TypeError, KeyError):
                # Skip invalid field data
                pass

        # Insurance coverage
        total_liability = sum(p.liability for p in self.policies.values()
                            if p.crop_year == year)

        # Marketing position
        total_contracted = sum(c.bushels * c.contract_price
                              for c in self.forward_contracts.values()
                              if c.status == ContractStatus.OPEN)

        return {
            "report_type": "Agricultural Operating Loan Package",
            "generated_date": datetime.now(timezone.utc).isoformat(),
            "farm_name": farm_name,
            "operator_name": operator_name,
            "crop_year": year,

            "operation_summary": {
                "total_acres": total_acres,
                "crops_grown": len(crops),
                "crop_mix": revenue_by_crop
            },

            "financial_projections": {
                "projected_gross_revenue": round(total_revenue, 2),
                "revenue_per_acre": round(total_revenue / total_acres, 2) if total_acres > 0 else 0
            },

            "risk_management": {
                "crop_insurance_liability": round(total_liability, 2),
                "forward_contracted_value": round(total_contracted, 2),
                "pct_production_contracted": "See marketing summary"
            },

            "compliance_status": {
                "regulatory_compliance": "Current",
                "insurance_in_place": len(self.policies) > 0,
                "fsa_enrolled": True  # Placeholder
            },

            "supporting_documents": [
                "Crop insurance policies",
                "Forward contracts",
                "FSA farm records",
                "Soil test results",
                "Equipment inventory"
            ]
        }

    def generate_investor_summary(
        self,
        farm_name: str,
        investment_amount: float,
        term_years: int
    ) -> Dict[str, Any]:
        """Generate investment summary for potential farm investors"""
        # Calculate historical metrics (placeholder - would use real data)
        avg_roi = 8.5
        risk_rating = "Moderate"

        return {
            "report_type": "Farm Investment Summary",
            "generated_date": datetime.now(timezone.utc).isoformat(),
            "farm_name": farm_name,

            "investment_overview": {
                "requested_amount": investment_amount,
                "term_years": term_years,
                "expected_annual_return": f"{avg_roi}%",
                "risk_rating": risk_rating
            },

            "farm_metrics": {
                "years_in_operation": 30,
                "management_experience": "Third generation",
                "technology_adoption": "Advanced (JD Operations Center, precision ag)",
                "sustainability_practices": "Cover crops, no-till, nutrient management"
            },

            "financial_strengths": [
                "Diversified crop mix reduces risk",
                "Long-term land ownership/leases",
                "Established buyer relationships",
                "Conservative debt levels",
                "Strong crop insurance coverage"
            ],

            "grant_funding": {
                "active_grants": 0,
                "pending_applications": len([a for a in getattr(self, 'applications', {}).values()
                                            if getattr(a, 'status', None) == 'preparing']),
                "potential_value": "See grant application tracker"
            }
        }

    # =========================================================================
    # HARVEST ANALYTICS
    # =========================================================================

    def record_harvest(
        self,
        field_id: str,
        field_name: str,
        crop: str,
        crop_year: int,
        harvest_date: date,
        acres_harvested: float,
        total_yield: float,
        moisture_pct: float,
        test_weight: float = 0,
        quality_notes: str = "",
        storage_location: str = ""
    ) -> Dict[str, Any]:
        """Record harvest data for a field"""
        try:
            comm = Commodity(crop)
        except ValueError:
            return {"error": f"Unknown crop: {crop}"}

        harvest_id = self._next_id("harvest")
        yield_per_acre = total_yield / acres_harvested if acres_harvested > 0 else 0

        record = HarvestRecord(
            id=harvest_id,
            field_id=field_id,
            field_name=field_name,
            crop=comm,
            crop_year=crop_year,
            harvest_date=harvest_date,
            acres_harvested=acres_harvested,
            total_yield=total_yield,
            yield_per_acre=yield_per_acre,
            moisture_pct=moisture_pct,
            test_weight=test_weight,
            quality_notes=quality_notes,
            storage_location=storage_location
        )

        self.harvest_records[harvest_id] = record

        # Compare to benchmark
        benchmarks = {"corn": 177, "soybeans": 50, "rice": 7500, "cotton": 1000}
        benchmark = benchmarks.get(crop, yield_per_acre)
        vs_benchmark = ((yield_per_acre - benchmark) / benchmark * 100) if benchmark > 0 else 0

        return {
            "id": harvest_id,
            "field_name": field_name,
            "crop": crop,
            "crop_year": crop_year,
            "harvest_date": harvest_date.isoformat(),
            "acres_harvested": acres_harvested,
            "total_yield": total_yield,
            "yield_per_acre": round(yield_per_acre, 1),
            "moisture_pct": moisture_pct,
            "vs_national_benchmark": f"{vs_benchmark:+.1f}%",
            "message": f"Harvest recorded: {yield_per_acre:.1f} per acre ({vs_benchmark:+.1f}% vs benchmark)"
        }

    def get_harvest_analytics(
        self,
        crop_year: int = None,
        crop: str = None
    ) -> Dict[str, Any]:
        """Get harvest analytics summary"""
        if crop_year is None:
            crop_year = date.today().year

        records = list(self.harvest_records.values())
        if crop_year:
            records = [r for r in records if r.crop_year == crop_year]
        if crop:
            try:
                comm = Commodity(crop)
                records = [r for r in records if r.crop == comm]
            except ValueError:
                pass

        if not records:
            return {
                "crop_year": crop_year,
                "message": "No harvest records found",
                "fields_harvested": 0
            }

        total_acres = sum(r.acres_harvested for r in records)
        _total_yield = sum(r.total_yield for r in records)

        # By crop summary
        by_crop = {}
        for r in records:
            crop_name = r.crop.value
            if crop_name not in by_crop:
                by_crop[crop_name] = {
                    "acres": 0,
                    "total_yield": 0,
                    "yields": []
                }
            by_crop[crop_name]["acres"] += r.acres_harvested
            by_crop[crop_name]["total_yield"] += r.total_yield
            by_crop[crop_name]["yields"].append(r.yield_per_acre)

        crop_summaries = []
        for crop_name, data in by_crop.items():
            avg_yield = statistics.mean(data["yields"]) if data["yields"] else 0
            crop_summaries.append({
                "crop": crop_name,
                "acres": data["acres"],
                "total_yield": round(data["total_yield"], 1),
                "avg_yield_per_acre": round(avg_yield, 1),
                "min_yield": round(min(data["yields"]), 1) if data["yields"] else 0,
                "max_yield": round(max(data["yields"]), 1) if data["yields"] else 0
            })

        # Field rankings
        field_rankings = sorted(
            [{"field": r.field_name, "crop": r.crop.value, "yield": r.yield_per_acre}
             for r in records],
            key=lambda x: x["yield"],
            reverse=True
        )

        return {
            "crop_year": crop_year,
            "summary": {
                "fields_harvested": len(set(r.field_id for r in records)),
                "total_acres": round(total_acres, 1),
                "crops_harvested": len(by_crop)
            },
            "by_crop": crop_summaries,
            "top_fields": field_rankings[:5],
            "bottom_fields": field_rankings[-5:] if len(field_rankings) > 5 else []
        }

    def get_yield_trend(
        self,
        field_id: str,
        crop: str
    ) -> Dict[str, Any]:
        """Get multi-year yield trend for a field"""
        try:
            comm = Commodity(crop)
        except ValueError:
            return {"error": f"Unknown crop: {crop}"}

        records = sorted(
            [r for r in self.harvest_records.values()
             if r.field_id == field_id and r.crop == comm],
            key=lambda x: x.crop_year
        )

        if not records:
            return {"error": f"No harvest records found for field {field_id} and crop {crop}"}

        years = []
        for r in records:
            years.append({
                "year": r.crop_year,
                "yield": r.yield_per_acre,
                "acres": r.acres_harvested,
                "moisture": r.moisture_pct
            })

        yields = [r.yield_per_acre for r in records]
        avg_yield = statistics.mean(yields)

        # Calculate trend
        if len(yields) >= 3:
            recent_avg = statistics.mean(yields[-3:])
            historical_avg = statistics.mean(yields[:-3]) if len(yields) > 3 else yields[0]
            trend = "improving" if recent_avg > historical_avg else "declining" if recent_avg < historical_avg else "stable"
        else:
            trend = "insufficient data"

        return {
            "field_id": field_id,
            "field_name": records[0].field_name,
            "crop": crop,
            "years_of_data": len(records),
            "yield_history": years,
            "statistics": {
                "average_yield": round(avg_yield, 1),
                "min_yield": round(min(yields), 1),
                "max_yield": round(max(yields), 1),
                "std_dev": round(statistics.stdev(yields), 1) if len(yields) > 1 else 0
            },
            "trend": trend
        }

    # =========================================================================
    # INPUT PROCUREMENT OPTIMIZER
    # =========================================================================

    def add_supplier(
        self,
        name: str,
        categories: List[str],
        contact_name: str,
        phone: str,
        email: str,
        address: str = "",
        payment_terms: str = "",
        notes: str = ""
    ) -> Dict[str, Any]:
        """Add a supplier to the database"""
        supplier_id = self._next_id("supplier")

        cat_enums = []
        for cat in categories:
            try:
                cat_enums.append(InputCategory(cat))
            except ValueError:
                pass

        supplier = Supplier(
            id=supplier_id,
            name=name,
            categories=cat_enums,
            contact_name=contact_name,
            phone=phone,
            email=email,
            address=address,
            payment_terms=payment_terms,
            notes=notes
        )

        self.suppliers[supplier_id] = supplier

        return {
            "id": supplier_id,
            "name": name,
            "categories": [c.value for c in cat_enums],
            "contact": contact_name,
            "phone": phone,
            "message": f"Supplier {name} added"
        }

    def add_price_quote(
        self,
        supplier_id: str,
        product_name: str,
        category: str,
        unit_price: float,
        unit: str,
        min_quantity: float,
        valid_until: date,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Add a price quote from a supplier"""
        if supplier_id not in self.suppliers:
            return {"error": f"Supplier {supplier_id} not found"}

        try:
            cat = InputCategory(category)
        except ValueError:
            return {"error": f"Invalid category: {category}"}

        quote_id = self._next_id("quote")
        supplier = self.suppliers[supplier_id]

        quote = PriceQuote(
            id=quote_id,
            supplier_id=supplier_id,
            supplier_name=supplier.name,
            product_name=product_name,
            category=cat,
            unit_price=unit_price,
            unit=unit,
            min_quantity=min_quantity,
            quote_date=date.today(),
            valid_until=valid_until,
            notes=notes
        )

        self.price_quotes[quote_id] = quote

        return {
            "id": quote_id,
            "supplier": supplier.name,
            "product": product_name,
            "price": f"${unit_price:.2f}/{unit}",
            "valid_until": valid_until.isoformat(),
            "message": f"Quote added: {product_name} at ${unit_price:.2f}/{unit}"
        }

    def compare_quotes(
        self,
        product_name: str = None,
        category: str = None
    ) -> Dict[str, Any]:
        """Compare quotes across suppliers"""
        quotes = list(self.price_quotes.values())

        # Filter active quotes
        quotes = [q for q in quotes if q.valid_until >= date.today()]

        if product_name:
            quotes = [q for q in quotes if product_name.lower() in q.product_name.lower()]

        if category:
            try:
                cat = InputCategory(category)
                quotes = [q for q in quotes if q.category == cat]
            except ValueError:
                pass

        if not quotes:
            return {
                "message": "No matching quotes found",
                "quotes": []
            }

        # Group by product
        by_product = {}
        for q in quotes:
            prod = q.product_name
            if prod not in by_product:
                by_product[prod] = []
            by_product[prod].append({
                "supplier": q.supplier_name,
                "price": q.unit_price,
                "unit": q.unit,
                "min_qty": q.min_quantity,
                "valid_until": q.valid_until.isoformat()
            })

        # Find best prices
        comparisons = []
        for prod, supplier_quotes in by_product.items():
            sorted_quotes = sorted(supplier_quotes, key=lambda x: x["price"])
            best = sorted_quotes[0]
            savings = 0
            if len(sorted_quotes) > 1:
                worst = sorted_quotes[-1]
                savings = worst["price"] - best["price"]

            comparisons.append({
                "product": prod,
                "best_price": best["price"],
                "best_supplier": best["supplier"],
                "quotes_count": len(sorted_quotes),
                "potential_savings_per_unit": round(savings, 2),
                "all_quotes": sorted_quotes
            })

        return {
            "as_of": date.today().isoformat(),
            "products_compared": len(comparisons),
            "comparisons": comparisons,
            "recommendation": f"Best overall savings with {comparisons[0]['best_supplier']}" if comparisons else None
        }

    def create_purchase_order(
        self,
        supplier_id: str,
        items: List[Dict[str, Any]],  # [{product, quantity, unit_price, unit}]
        expected_delivery: date,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Create a purchase order"""
        if supplier_id not in self.suppliers:
            return {"error": f"Supplier {supplier_id} not found"}

        supplier = self.suppliers[supplier_id]
        po_id = self._next_id("po")

        subtotal = sum(item["quantity"] * item["unit_price"] for item in items)
        tax = subtotal * 0.0  # Ag inputs often tax exempt
        shipping = 0  # Would be calculated or entered

        order = PurchaseOrder(
            id=po_id,
            supplier_id=supplier_id,
            supplier_name=supplier.name,
            order_date=date.today(),
            expected_delivery=expected_delivery,
            category=InputCategory.SEED,  # Would be set properly
            items=items,
            subtotal=subtotal,
            tax=tax,
            shipping=shipping,
            total=subtotal + tax + shipping,
            status="draft",
            notes=notes
        )

        self.purchase_orders[po_id] = order

        return {
            "id": po_id,
            "supplier": supplier.name,
            "order_date": date.today().isoformat(),
            "expected_delivery": expected_delivery.isoformat(),
            "items_count": len(items),
            "subtotal": round(subtotal, 2),
            "total": round(subtotal + tax + shipping, 2),
            "status": "draft",
            "message": f"PO created: ${subtotal:,.2f} from {supplier.name}"
        }

    def get_procurement_summary(self) -> Dict[str, Any]:
        """Get procurement summary and recommendations"""
        # Active quotes
        active_quotes = [q for q in self.price_quotes.values()
                        if q.valid_until >= date.today()]

        # Open POs
        open_pos = [po for po in self.purchase_orders.values()
                   if po.status in ["draft", "ordered", "shipped"]]

        # Expiring quotes
        week_out = date.today() + timedelta(days=7)
        expiring = [q for q in active_quotes if q.valid_until <= week_out]

        return {
            "suppliers": {
                "total": len(self.suppliers),
                "by_category": {}  # Would aggregate
            },
            "quotes": {
                "active": len(active_quotes),
                "expiring_soon": len(expiring),
                "expiring_quotes": [
                    {"product": q.product_name, "supplier": q.supplier_name,
                     "expires": q.valid_until.isoformat()}
                    for q in expiring
                ]
            },
            "purchase_orders": {
                "open": len(open_pos),
                "total_open_value": sum(po.total for po in open_pos)
            },
            "recommendations": [
                "Review expiring quotes and request renewals" if expiring else "All quotes current",
                "Compare prices across suppliers before ordering",
                "Consider early order discounts for next season inputs"
            ]
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_farm_intelligence_service: Optional[FarmIntelligenceService] = None


def get_farm_intelligence_service() -> FarmIntelligenceService:
    """Get or create the farm intelligence service singleton"""
    global _farm_intelligence_service
    if _farm_intelligence_service is None:
        _farm_intelligence_service = FarmIntelligenceService()
    return _farm_intelligence_service
