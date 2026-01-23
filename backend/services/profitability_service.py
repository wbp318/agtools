"""
Profitability Analysis Service
Comprehensive tools for farm profitability planning and input optimization.

Includes:
- Break-even calculator (yield and price)
- Input ROI ranker (identify what to cut first)
- Scenario planner (what-if analysis)
- Budget tracker with targets and alerts

AgTools v2.8.0
"""

from datetime import date
from enum import Enum
from typing import Optional, List, Dict, Any
import sqlite3

from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class CropType(str, Enum):
    """Supported crop types"""
    CORN = "corn"
    SOYBEANS = "soybeans"
    RICE = "rice"
    WHEAT = "wheat"
    COTTON = "cotton"
    GRAIN_SORGHUM = "grain_sorghum"


class InputCategory(str, Enum):
    """Input cost categories for ROI analysis"""
    SEED = "seed"
    FERTILIZER = "fertilizer"
    CHEMICAL = "chemical"  # herbicides, insecticides, fungicides
    FUEL = "fuel"
    REPAIRS = "repairs"
    LABOR = "labor"
    CUSTOM_HIRE = "custom_hire"
    LAND_RENT = "land_rent"
    CROP_INSURANCE = "crop_insurance"
    IRRIGATION = "irrigation"
    DRYING_STORAGE = "drying_storage"
    INTEREST = "interest"
    OTHER = "other"


class BudgetStatus(str, Enum):
    """Budget tracking status"""
    ON_TRACK = "on_track"
    WARNING = "warning"  # 80-100% of budget
    OVER_BUDGET = "over_budget"
    CRITICAL = "critical"  # >120% of budget


class ScenarioType(str, Enum):
    """Types of what-if scenarios"""
    PRICE_CHANGE = "price_change"
    YIELD_CHANGE = "yield_change"
    COST_CHANGE = "cost_change"
    COMBINED = "combined"


# ============================================================================
# CROP PARAMETERS - Including Rice for Louisiana
# ============================================================================

CROP_PARAMETERS = {
    CropType.CORN: {
        "default_yield": 180,  # bu/acre
        "yield_unit": "bu",
        "price_unit": "$/bu",
        "default_price": 4.50,
        "variable_costs_per_acre": {
            InputCategory.SEED: 125,
            InputCategory.FERTILIZER: 180,
            InputCategory.CHEMICAL: 50,
            InputCategory.FUEL: 35,
            InputCategory.REPAIRS: 25,
            InputCategory.LABOR: 25,
            InputCategory.CUSTOM_HIRE: 30,
            InputCategory.CROP_INSURANCE: 25,
            InputCategory.DRYING_STORAGE: 35,
            InputCategory.INTEREST: 20,
            InputCategory.OTHER: 15,
        },
        "irrigation_cost_per_acre": 85,
        "typical_yield_range": (140, 220),
        "typical_price_range": (3.50, 6.50),
        # ROI coefficients - yield response to each input
        "input_yield_impact": {
            InputCategory.SEED: 0.15,  # 15% yield impact from good seed
            InputCategory.FERTILIZER: 0.30,  # 30% yield impact
            InputCategory.CHEMICAL: 0.10,  # 10% yield protection
            InputCategory.IRRIGATION: 0.25,  # 25% in dry years
            InputCategory.LABOR: 0.05,  # 5% from good management
        },
    },
    CropType.SOYBEANS: {
        "default_yield": 50,
        "yield_unit": "bu",
        "price_unit": "$/bu",
        "default_price": 11.50,
        "variable_costs_per_acre": {
            InputCategory.SEED: 70,
            InputCategory.FERTILIZER: 35,
            InputCategory.CHEMICAL: 45,
            InputCategory.FUEL: 25,
            InputCategory.REPAIRS: 20,
            InputCategory.LABOR: 20,
            InputCategory.CUSTOM_HIRE: 25,
            InputCategory.CROP_INSURANCE: 20,
            InputCategory.DRYING_STORAGE: 15,
            InputCategory.INTEREST: 15,
            InputCategory.OTHER: 10,
        },
        "irrigation_cost_per_acre": 65,
        "typical_yield_range": (35, 70),
        "typical_price_range": (9.00, 15.00),
        "input_yield_impact": {
            InputCategory.SEED: 0.12,
            InputCategory.FERTILIZER: 0.10,
            InputCategory.CHEMICAL: 0.15,
            InputCategory.IRRIGATION: 0.20,
            InputCategory.LABOR: 0.05,
        },
    },
    CropType.RICE: {
        "default_yield": 7500,  # lbs/acre (or ~167 bu at 45 lbs/bu)
        "yield_unit": "cwt",  # hundredweight
        "price_unit": "$/cwt",
        "default_price": 15.00,  # per cwt
        "variable_costs_per_acre": {
            InputCategory.SEED: 85,
            InputCategory.FERTILIZER: 145,
            InputCategory.CHEMICAL: 95,  # Higher herbicide costs for rice
            InputCategory.FUEL: 45,
            InputCategory.REPAIRS: 30,
            InputCategory.LABOR: 35,
            InputCategory.CUSTOM_HIRE: 50,  # Aerial application common
            InputCategory.CROP_INSURANCE: 35,
            InputCategory.DRYING_STORAGE: 55,
            InputCategory.INTEREST: 25,
            InputCategory.IRRIGATION: 120,  # Flood irrigation is expensive
            InputCategory.OTHER: 20,
        },
        "irrigation_cost_per_acre": 120,  # Included by default for rice
        "typical_yield_range": (6000, 9000),  # lbs/acre
        "typical_price_range": (12.00, 20.00),
        "input_yield_impact": {
            InputCategory.SEED: 0.12,
            InputCategory.FERTILIZER: 0.25,
            InputCategory.CHEMICAL: 0.15,
            InputCategory.IRRIGATION: 0.35,  # Critical for rice
            InputCategory.LABOR: 0.08,
        },
        "notes": "Rice yields often quoted in lbs/acre or cwt. 1 cwt = 100 lbs.",
    },
    CropType.WHEAT: {
        "default_yield": 55,
        "yield_unit": "bu",
        "price_unit": "$/bu",
        "default_price": 6.00,
        "variable_costs_per_acre": {
            InputCategory.SEED: 35,
            InputCategory.FERTILIZER: 90,
            InputCategory.CHEMICAL: 35,
            InputCategory.FUEL: 25,
            InputCategory.REPAIRS: 18,
            InputCategory.LABOR: 18,
            InputCategory.CUSTOM_HIRE: 20,
            InputCategory.CROP_INSURANCE: 15,
            InputCategory.DRYING_STORAGE: 10,
            InputCategory.INTEREST: 12,
            InputCategory.OTHER: 10,
        },
        "irrigation_cost_per_acre": 60,
        "typical_yield_range": (40, 80),
        "typical_price_range": (4.50, 8.50),
        "input_yield_impact": {
            InputCategory.SEED: 0.10,
            InputCategory.FERTILIZER: 0.30,
            InputCategory.CHEMICAL: 0.12,
            InputCategory.IRRIGATION: 0.15,
            InputCategory.LABOR: 0.05,
        },
    },
    CropType.COTTON: {
        "default_yield": 1000,  # lbs lint/acre
        "yield_unit": "lb",
        "price_unit": "$/lb",
        "default_price": 0.80,
        "variable_costs_per_acre": {
            InputCategory.SEED: 95,
            InputCategory.FERTILIZER: 120,
            InputCategory.CHEMICAL: 130,  # High pest pressure
            InputCategory.FUEL: 40,
            InputCategory.REPAIRS: 35,
            InputCategory.LABOR: 30,
            InputCategory.CUSTOM_HIRE: 75,  # Defoliation, picking
            InputCategory.CROP_INSURANCE: 45,
            InputCategory.DRYING_STORAGE: 25,
            InputCategory.INTEREST: 25,
            InputCategory.OTHER: 25,
        },
        "irrigation_cost_per_acre": 90,
        "typical_yield_range": (800, 1400),
        "typical_price_range": (0.60, 1.00),
        "input_yield_impact": {
            InputCategory.SEED: 0.10,
            InputCategory.FERTILIZER: 0.20,
            InputCategory.CHEMICAL: 0.25,
            InputCategory.IRRIGATION: 0.20,
            InputCategory.LABOR: 0.08,
        },
    },
    CropType.GRAIN_SORGHUM: {
        "default_yield": 100,  # bu/acre
        "yield_unit": "bu",
        "price_unit": "$/bu",
        "default_price": 4.25,
        "variable_costs_per_acre": {
            InputCategory.SEED: 45,
            InputCategory.FERTILIZER: 95,
            InputCategory.CHEMICAL: 40,
            InputCategory.FUEL: 28,
            InputCategory.REPAIRS: 20,
            InputCategory.LABOR: 20,
            InputCategory.CUSTOM_HIRE: 25,
            InputCategory.CROP_INSURANCE: 18,
            InputCategory.DRYING_STORAGE: 20,
            InputCategory.INTEREST: 15,
            InputCategory.OTHER: 12,
        },
        "irrigation_cost_per_acre": 55,
        "typical_yield_range": (70, 140),
        "typical_price_range": (3.25, 5.50),
        "input_yield_impact": {
            InputCategory.SEED: 0.10,
            InputCategory.FERTILIZER: 0.25,
            InputCategory.CHEMICAL: 0.10,
            InputCategory.IRRIGATION: 0.20,
            InputCategory.LABOR: 0.05,
        },
    },
}


# ============================================================================
# PYDANTIC MODELS - REQUESTS/RESPONSES
# ============================================================================

class BreakEvenRequest(BaseModel):
    """Request for break-even calculation"""
    crop: CropType
    acres: float = Field(..., gt=0)
    total_costs: Optional[float] = None  # If not provided, uses defaults
    cost_per_acre: Optional[float] = None
    expected_yield: Optional[float] = None
    expected_price: Optional[float] = None
    include_land_rent: bool = True
    land_rent_per_acre: Optional[float] = None


class BreakEvenResponse(BaseModel):
    """Break-even analysis results"""
    crop: str
    acres: float
    total_costs: float
    cost_per_acre: float

    # Break-even yields at different prices
    break_even_yields: Dict[str, float]  # price -> yield needed

    # Break-even prices at different yields
    break_even_prices: Dict[str, float]  # yield -> price needed

    # Current scenario
    current_scenario: Dict[str, Any]

    # Margin of safety
    margin_analysis: Dict[str, Any]

    # Recommendations
    recommendations: List[str]


class InputROIRequest(BaseModel):
    """Request for input ROI ranking"""
    crop: CropType
    acres: float = Field(..., gt=0)
    expected_yield: Optional[float] = None
    grain_price: Optional[float] = None
    current_costs: Optional[Dict[str, float]] = None  # category -> cost per acre
    is_irrigated: bool = False


class InputROIItem(BaseModel):
    """Single input ROI analysis"""
    category: str
    cost_per_acre: float
    total_cost: float
    yield_impact_percent: float
    estimated_yield_contribution: float
    revenue_contribution: float
    roi_ratio: float  # revenue / cost
    cut_priority: int  # 1 = cut first if needed
    cut_risk: str  # low, medium, high - risk of yield loss if cut
    notes: str


class InputROIResponse(BaseModel):
    """Input ROI ranking results"""
    crop: str
    acres: float
    grain_price: float
    expected_yield: float

    # All inputs ranked by ROI
    inputs_by_roi: List[InputROIItem]

    # Suggested cuts if needed
    cut_recommendations: List[Dict[str, Any]]

    # Summary
    total_input_cost: float
    total_revenue: float
    current_profit: float

    # What-if cuts
    if_cut_lowest_roi: Dict[str, Any]


class ScenarioRequest(BaseModel):
    """Request for scenario planning"""
    crop: CropType
    acres: float = Field(..., gt=0)
    base_yield: Optional[float] = None
    base_price: Optional[float] = None
    base_cost_per_acre: Optional[float] = None

    # Scenarios to run
    price_scenarios: Optional[List[float]] = None  # e.g., [4.00, 4.50, 5.00, 5.50]
    yield_scenarios: Optional[List[float]] = None  # e.g., [150, 175, 200, 225]
    cost_change_percents: Optional[List[float]] = None  # e.g., [-20, -10, 0, 10, 20]


class ScenarioResult(BaseModel):
    """Single scenario result"""
    scenario_name: str
    yield_per_acre: float
    price: float
    cost_per_acre: float
    revenue_per_acre: float
    profit_per_acre: float
    total_profit: float
    break_even: bool
    margin_percent: float


class ScenarioResponse(BaseModel):
    """Scenario planning results"""
    crop: str
    acres: float
    base_case: ScenarioResult
    scenarios: List[ScenarioResult]

    # Summary
    best_case: ScenarioResult
    worst_case: ScenarioResult
    break_even_scenarios: int
    profitable_scenarios: int

    # Sensitivity analysis
    price_sensitivity: Dict[str, float]  # $/bu change -> profit change
    yield_sensitivity: Dict[str, float]  # bu/acre change -> profit change

    # Recommendations
    risk_assessment: str
    recommendations: List[str]


class BudgetTarget(BaseModel):
    """Budget target for a category"""
    category: str
    target_amount: float
    actual_amount: float = 0
    percent_used: float = 0
    status: BudgetStatus = BudgetStatus.ON_TRACK
    remaining: float = 0


class BudgetTrackerRequest(BaseModel):
    """Request to set up budget tracking"""
    crop_year: int
    crop: CropType
    acres: float = Field(..., gt=0)
    target_cost_per_acre: Optional[float] = None
    category_targets: Optional[Dict[str, float]] = None  # category -> target per acre
    grain_price_target: Optional[float] = None
    yield_goal: Optional[float] = None


class BudgetTrackerResponse(BaseModel):
    """Budget tracking status"""
    crop_year: int
    crop: str
    acres: float

    # Overall budget
    total_budget: float
    total_spent: float
    total_remaining: float
    overall_status: BudgetStatus
    percent_of_season: float  # Estimate based on date

    # By category
    category_budgets: List[BudgetTarget]

    # Alerts
    alerts: List[Dict[str, Any]]

    # Projected outcome
    projected_profit: float
    break_even_status: str

    # Recommendations
    recommendations: List[str]


# ============================================================================
# PROFITABILITY SERVICE
# ============================================================================

class ProfitabilityService:
    """
    Comprehensive profitability analysis for farm operations.

    Key features:
    - Break-even analysis (yield and price)
    - Input ROI ranking with cut recommendations
    - What-if scenario planning
    - Budget tracking with alerts
    """

    def __init__(self, db_path: str = "agtools.db"):
        self.db_path = db_path
        self.crop_params = CROP_PARAMETERS

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ========================================================================
    # BREAK-EVEN CALCULATOR
    # ========================================================================

    def calculate_break_even(self, request: BreakEvenRequest) -> BreakEvenResponse:
        """
        Calculate break-even yields and prices.

        Answers:
        - What yield do I need at price X to break even?
        - What price do I need at yield Y to break even?
        """
        crop_data = self.crop_params.get(request.crop, self.crop_params[CropType.CORN])

        # Determine costs
        if request.cost_per_acre:
            cost_per_acre = request.cost_per_acre
        elif request.total_costs:
            cost_per_acre = request.total_costs / request.acres
        else:
            # Use defaults
            cost_per_acre = sum(crop_data["variable_costs_per_acre"].values())
            if request.include_land_rent and request.land_rent_per_acre:
                cost_per_acre += request.land_rent_per_acre

        total_costs = cost_per_acre * request.acres

        # Expected values
        expected_yield = request.expected_yield or crop_data["default_yield"]
        expected_price = request.expected_price or crop_data["default_price"]

        # Calculate break-even yields at different prices
        price_range = crop_data["typical_price_range"]
        prices_to_check = [
            round(price_range[0], 2),
            round((price_range[0] + price_range[1]) / 2 - 0.50, 2),
            round((price_range[0] + price_range[1]) / 2, 2),
            round((price_range[0] + price_range[1]) / 2 + 0.50, 2),
            round(price_range[1], 2),
        ]

        break_even_yields = {}
        for price in prices_to_check:
            if price > 0:
                be_yield = cost_per_acre / price
                break_even_yields[f"${price:.2f}"] = round(be_yield, 1)

        # Calculate break-even prices at different yields
        yield_range = crop_data["typical_yield_range"]
        yields_to_check = [
            yield_range[0],
            (yield_range[0] + yield_range[1]) // 2 - 20,
            (yield_range[0] + yield_range[1]) // 2,
            (yield_range[0] + yield_range[1]) // 2 + 20,
            yield_range[1],
        ]

        break_even_prices = {}
        for yld in yields_to_check:
            if yld > 0:
                be_price = cost_per_acre / yld
                break_even_prices[f"{yld} {crop_data['yield_unit']}"] = round(be_price, 2)

        # Current scenario
        gross_revenue = expected_yield * expected_price * request.acres
        net_profit = gross_revenue - total_costs
        profit_per_acre = net_profit / request.acres if request.acres > 0 else 0
        be_yield_current = cost_per_acre / expected_price if expected_price > 0 else 0
        be_price_current = cost_per_acre / expected_yield if expected_yield > 0 else 0

        current_scenario = {
            "expected_yield": expected_yield,
            "expected_price": expected_price,
            "gross_revenue": round(gross_revenue, 2),
            "total_costs": round(total_costs, 2),
            "net_profit": round(net_profit, 2),
            "profit_per_acre": round(profit_per_acre, 2),
            "break_even_yield": round(be_yield_current, 1),
            "break_even_price": round(be_price_current, 2),
            "profitable": net_profit > 0,
        }

        # Margin of safety analysis
        yield_margin = expected_yield - be_yield_current
        yield_margin_pct = (yield_margin / expected_yield * 100) if expected_yield > 0 else 0
        price_margin = expected_price - be_price_current
        price_margin_pct = (price_margin / expected_price * 100) if expected_price > 0 else 0

        margin_analysis = {
            "yield_cushion": round(yield_margin, 1),
            "yield_cushion_percent": round(yield_margin_pct, 1),
            "price_cushion": round(price_margin, 2),
            "price_cushion_percent": round(price_margin_pct, 1),
            "bushels_to_spare": round(yield_margin * request.acres, 0),
            "risk_level": self._assess_margin_risk(yield_margin_pct, price_margin_pct),
        }

        # Generate recommendations
        recommendations = self._generate_break_even_recommendations(
            current_scenario, margin_analysis, crop_data
        )

        return BreakEvenResponse(
            crop=request.crop.value,
            acres=request.acres,
            total_costs=round(total_costs, 2),
            cost_per_acre=round(cost_per_acre, 2),
            break_even_yields=break_even_yields,
            break_even_prices=break_even_prices,
            current_scenario=current_scenario,
            margin_analysis=margin_analysis,
            recommendations=recommendations,
        )

    def _assess_margin_risk(self, yield_margin_pct: float, price_margin_pct: float) -> str:
        """Assess overall risk based on margins."""
        avg_margin = (yield_margin_pct + price_margin_pct) / 2
        if avg_margin < 0:
            return "CRITICAL - Currently below break-even"
        elif avg_margin < 10:
            return "HIGH - Very thin margins"
        elif avg_margin < 20:
            return "MODERATE - Some cushion but vulnerable"
        elif avg_margin < 30:
            return "LOW - Healthy margins"
        else:
            return "VERY LOW - Strong profit potential"

    def _generate_break_even_recommendations(
        self,
        scenario: Dict,
        margins: Dict,
        crop_data: Dict
    ) -> List[str]:
        """Generate actionable recommendations based on break-even analysis."""
        recs = []

        if not scenario["profitable"]:
            recs.append(f"⚠️ ALERT: Currently projecting a LOSS of ${abs(scenario['net_profit']):,.2f}")
            recs.append(f"Need to either: cut costs by ${abs(scenario['profit_per_acre']):.2f}/acre OR increase revenue")

        if margins["yield_cushion_percent"] < 10:
            recs.append(f"Yield margin is tight ({margins['yield_cushion_percent']:.1f}%). Consider crop insurance.")

        if margins["price_cushion_percent"] < 10:
            recs.append(f"Price margin is tight ({margins['price_cushion_percent']:.1f}%). Consider forward contracting.")

        if margins["risk_level"].startswith("HIGH") or margins["risk_level"].startswith("CRITICAL"):
            recs.append("Review all input costs for potential cuts - see Input ROI analysis")
            recs.append("Consider reducing acres of this crop if alternatives are more profitable")

        if scenario["profitable"] and margins["yield_cushion_percent"] > 20:
            recs.append(f"Good position - {margins['bushels_to_spare']:.0f} bushels cushion before break-even")

        return recs

    # ========================================================================
    # INPUT ROI RANKER
    # ========================================================================

    def rank_inputs_by_roi(self, request: InputROIRequest) -> InputROIResponse:
        """
        Rank all inputs by their return on investment.

        Identifies:
        - Which inputs give the best return per dollar spent
        - Which inputs to cut first if you need to reduce costs
        - Risk of yield loss for each potential cut
        """
        crop_data = self.crop_params.get(request.crop, self.crop_params[CropType.CORN])

        # Get costs
        if request.current_costs:
            costs = request.current_costs
        else:
            costs = {k.value: v for k, v in crop_data["variable_costs_per_acre"].items()}
            if request.is_irrigated:
                costs[InputCategory.IRRIGATION.value] = crop_data.get("irrigation_cost_per_acre", 0)

        expected_yield = request.expected_yield or crop_data["default_yield"]
        grain_price = request.grain_price or crop_data["default_price"]

        # Calculate ROI for each input
        input_rois = []
        yield_impacts = crop_data.get("input_yield_impact", {})

        for category, cost_per_acre in costs.items():
            if cost_per_acre <= 0:
                continue

            total_cost = cost_per_acre * request.acres

            # Get yield impact for this input
            try:
                cat_enum = InputCategory(category)
                impact_pct = yield_impacts.get(cat_enum, 0.02)  # Default 2% impact
            except ValueError:
                impact_pct = 0.02

            yield_contribution = expected_yield * impact_pct
            revenue_contribution = yield_contribution * grain_price * request.acres

            roi_ratio = revenue_contribution / total_cost if total_cost > 0 else 0

            # Determine cut risk
            if impact_pct >= 0.25:
                cut_risk = "HIGH"
                risk_note = "Cutting this will likely cause significant yield loss"
            elif impact_pct >= 0.10:
                cut_risk = "MEDIUM"
                risk_note = "Cutting may cause some yield loss"
            else:
                cut_risk = "LOW"
                risk_note = "Can likely reduce without major yield impact"

            input_rois.append(InputROIItem(
                category=category,
                cost_per_acre=round(cost_per_acre, 2),
                total_cost=round(total_cost, 2),
                yield_impact_percent=round(impact_pct * 100, 1),
                estimated_yield_contribution=round(yield_contribution, 1),
                revenue_contribution=round(revenue_contribution, 2),
                roi_ratio=round(roi_ratio, 2),
                cut_priority=0,  # Will be set after sorting
                cut_risk=cut_risk,
                notes=risk_note,
            ))

        # Sort by ROI ratio (lowest ROI = cut first)
        input_rois.sort(key=lambda x: x.roi_ratio)

        # Assign cut priorities
        for i, item in enumerate(input_rois):
            item.cut_priority = i + 1

        # Calculate totals
        total_input_cost = sum(costs.values()) * request.acres
        total_revenue = expected_yield * grain_price * request.acres
        current_profit = total_revenue - total_input_cost

        # Generate cut recommendations
        cut_recs = []
        cumulative_savings = 0
        for item in input_rois[:5]:  # Top 5 cut candidates
            cumulative_savings += item.total_cost
            potential_yield_loss = item.yield_impact_percent / 100 * expected_yield
            potential_revenue_loss = potential_yield_loss * grain_price * request.acres
            net_savings = item.total_cost - potential_revenue_loss

            cut_recs.append({
                "priority": item.cut_priority,
                "category": item.category,
                "potential_savings": round(item.total_cost, 2),
                "potential_yield_loss": round(potential_yield_loss, 1),
                "potential_revenue_loss": round(potential_revenue_loss, 2),
                "net_benefit": round(net_savings, 2),
                "risk": item.cut_risk,
                "recommendation": "CUT" if net_savings > 0 else "KEEP - yield loss exceeds savings",
            })

        # What if we cut the lowest ROI input?
        if input_rois:
            lowest_roi = input_rois[0]
            new_profit = current_profit + (lowest_roi.total_cost - lowest_roi.revenue_contribution)
            if_cut_lowest = {
                "input_to_cut": lowest_roi.category,
                "savings": round(lowest_roi.total_cost, 2),
                "estimated_yield_loss": round(lowest_roi.estimated_yield_contribution, 1),
                "estimated_revenue_loss": round(lowest_roi.revenue_contribution, 2),
                "new_projected_profit": round(new_profit, 2),
                "profit_change": round(new_profit - current_profit, 2),
                "worth_cutting": new_profit > current_profit,
            }
        else:
            if_cut_lowest = {}

        return InputROIResponse(
            crop=request.crop.value,
            acres=request.acres,
            grain_price=grain_price,
            expected_yield=expected_yield,
            inputs_by_roi=input_rois,
            cut_recommendations=cut_recs,
            total_input_cost=round(total_input_cost, 2),
            total_revenue=round(total_revenue, 2),
            current_profit=round(current_profit, 2),
            if_cut_lowest_roi=if_cut_lowest,
        )

    # ========================================================================
    # SCENARIO PLANNER
    # ========================================================================

    def run_scenarios(self, request: ScenarioRequest) -> ScenarioResponse:
        """
        Run what-if scenario analysis.

        Models different combinations of:
        - Grain prices
        - Yields
        - Cost changes
        """
        crop_data = self.crop_params.get(request.crop, self.crop_params[CropType.CORN])

        # Base values
        base_yield = request.base_yield or crop_data["default_yield"]
        base_price = request.base_price or crop_data["default_price"]
        base_cost = request.base_cost_per_acre or sum(crop_data["variable_costs_per_acre"].values())

        # Default scenarios if not provided
        price_scenarios = request.price_scenarios or [
            round(base_price * 0.80, 2),
            round(base_price * 0.90, 2),
            base_price,
            round(base_price * 1.10, 2),
            round(base_price * 1.20, 2),
        ]

        yield_scenarios = request.yield_scenarios or [
            round(base_yield * 0.70),
            round(base_yield * 0.85),
            base_yield,
            round(base_yield * 1.10),
            round(base_yield * 1.15),
        ]

        cost_changes = request.cost_change_percents or [0]  # Default no cost change

        # Calculate base case
        base_revenue = base_yield * base_price
        base_profit = base_revenue - base_cost

        base_case = ScenarioResult(
            scenario_name="Base Case",
            yield_per_acre=base_yield,
            price=base_price,
            cost_per_acre=base_cost,
            revenue_per_acre=round(base_revenue, 2),
            profit_per_acre=round(base_profit, 2),
            total_profit=round(base_profit * request.acres, 2),
            break_even=base_profit >= 0,
            margin_percent=round(base_profit / base_revenue * 100 if base_revenue > 0 else 0, 1),
        )

        # Run all scenario combinations
        scenarios = []
        for price in price_scenarios:
            for yld in yield_scenarios:
                for cost_pct in cost_changes:
                    adj_cost = base_cost * (1 + cost_pct / 100)
                    revenue = yld * price
                    profit = revenue - adj_cost

                    # Skip base case (already calculated)
                    if price == base_price and yld == base_yield and cost_pct == 0:
                        continue

                    scenario_name = f"${price:.2f} @ {yld} {crop_data['yield_unit']}"
                    if cost_pct != 0:
                        scenario_name += f" ({cost_pct:+.0f}% costs)"

                    scenarios.append(ScenarioResult(
                        scenario_name=scenario_name,
                        yield_per_acre=yld,
                        price=price,
                        cost_per_acre=round(adj_cost, 2),
                        revenue_per_acre=round(revenue, 2),
                        profit_per_acre=round(profit, 2),
                        total_profit=round(profit * request.acres, 2),
                        break_even=profit >= 0,
                        margin_percent=round(profit / revenue * 100 if revenue > 0 else 0, 1),
                    ))

        # Sort by profit
        scenarios.sort(key=lambda x: x.total_profit, reverse=True)

        # Find best and worst
        best_case = scenarios[0] if scenarios else base_case
        worst_case = scenarios[-1] if scenarios else base_case

        # Count scenarios
        profitable_count = sum(1 for s in scenarios if s.break_even)
        break_even_count = sum(1 for s in scenarios if abs(s.profit_per_acre) < 10)  # Within $10 of break-even

        # Price sensitivity ($/bu change impact on profit per acre)
        price_sensitivity = {}
        for price in price_scenarios:
            price_diff = price - base_price
            if price_diff != 0:
                profit_at_price = base_yield * price - base_cost
                profit_diff = profit_at_price - base_profit
                price_sensitivity[f"${price_diff:+.2f}/bu"] = round(profit_diff, 2)

        # Yield sensitivity (bu/acre change impact on profit per acre)
        yield_sensitivity = {}
        for yld in yield_scenarios:
            yield_diff = yld - base_yield
            if yield_diff != 0:
                profit_at_yield = yld * base_price - base_cost
                profit_diff = profit_at_yield - base_profit
                yield_sensitivity[f"{yield_diff:+.0f} bu"] = round(profit_diff, 2)

        # Risk assessment
        if profitable_count / max(len(scenarios), 1) >= 0.8:
            risk = "LOW - Most scenarios are profitable"
        elif profitable_count / max(len(scenarios), 1) >= 0.5:
            risk = "MODERATE - About half of scenarios are profitable"
        elif profitable_count > 0:
            risk = "HIGH - Only a few scenarios are profitable"
        else:
            risk = "CRITICAL - No scenarios show profitability"

        # Recommendations
        recs = self._generate_scenario_recommendations(
            base_case, best_case, worst_case, profitable_count, len(scenarios), base_price, base_yield
        )

        return ScenarioResponse(
            crop=request.crop.value,
            acres=request.acres,
            base_case=base_case,
            scenarios=scenarios,
            best_case=best_case,
            worst_case=worst_case,
            break_even_scenarios=break_even_count,
            profitable_scenarios=profitable_count,
            price_sensitivity=price_sensitivity,
            yield_sensitivity=yield_sensitivity,
            risk_assessment=risk,
            recommendations=recs,
        )

    def _generate_scenario_recommendations(
        self,
        base: ScenarioResult,
        best: ScenarioResult,
        worst: ScenarioResult,
        profitable_count: int,
        total_count: int,
        base_price: float,
        base_yield: float
    ) -> List[str]:
        """Generate recommendations from scenario analysis."""
        recs = []

        profit_range = best.total_profit - worst.total_profit
        recs.append(f"Profit range: ${worst.total_profit:,.2f} to ${best.total_profit:,.2f} (${profit_range:,.2f} swing)")

        if profitable_count == 0:
            recs.append("⚠️ CRITICAL: No scenarios show profitability. Must cut costs or reconsider this crop.")
        elif profitable_count < total_count * 0.5:
            recs.append("⚠️ High risk - consider hedging or forward contracting at profitable prices")

        # Price advice
        if best.price > base_price:
            recs.append(f"Best case requires ${best.price:.2f} - consider setting price targets")

        # Yield advice
        if best.yield_per_acre > base_yield:
            recs.append(f"Best case requires {best.yield_per_acre:.0f} yield - focus on agronomics")

        if worst.total_profit < -10000:
            recs.append(f"Worst case loss of ${abs(worst.total_profit):,.2f} - ensure adequate crop insurance")

        return recs

    # ========================================================================
    # BUDGET TRACKER
    # ========================================================================

    def setup_budget_tracker(self, request: BudgetTrackerRequest) -> BudgetTrackerResponse:
        """
        Set up and calculate budget tracking status.

        Compares:
        - Target vs actual spending by category
        - Projected outcome vs goals
        - Alerts for over-budget categories
        """
        crop_data = self.crop_params.get(request.crop, self.crop_params[CropType.CORN])

        # Get target cost per acre
        if request.target_cost_per_acre:
            target_per_acre = request.target_cost_per_acre
        else:
            target_per_acre = sum(crop_data["variable_costs_per_acre"].values())

        total_budget = target_per_acre * request.acres

        # Set up category targets
        if request.category_targets:
            cat_targets = request.category_targets
        else:
            cat_targets = {k.value: v for k, v in crop_data["variable_costs_per_acre"].items()}

        # Get actual spending from database (if available)
        actual_spending = self._get_actual_spending(request.crop_year)

        # Build category budgets
        category_budgets = []
        total_spent = 0
        alerts = []

        for category, target_per_acre in cat_targets.items():
            target = target_per_acre * request.acres
            actual = actual_spending.get(category, 0)
            total_spent += actual

            percent_used = (actual / target * 100) if target > 0 else 0
            remaining = target - actual

            # Determine status
            if percent_used >= 120:
                status = BudgetStatus.CRITICAL
                alerts.append({
                    "category": category,
                    "severity": "critical",
                    "message": f"{category} is {percent_used:.0f}% of budget (${actual:,.2f} of ${target:,.2f})",
                })
            elif percent_used >= 100:
                status = BudgetStatus.OVER_BUDGET
                alerts.append({
                    "category": category,
                    "severity": "warning",
                    "message": f"{category} is over budget by ${actual - target:,.2f}",
                })
            elif percent_used >= 80:
                status = BudgetStatus.WARNING
                alerts.append({
                    "category": category,
                    "severity": "info",
                    "message": f"{category} is at {percent_used:.0f}% - ${remaining:,.2f} remaining",
                })
            else:
                status = BudgetStatus.ON_TRACK

            category_budgets.append(BudgetTarget(
                category=category,
                target_amount=round(target, 2),
                actual_amount=round(actual, 2),
                percent_used=round(percent_used, 1),
                status=status,
                remaining=round(remaining, 2),
            ))

        # Sort by percent used (highest first)
        category_budgets.sort(key=lambda x: x.percent_used, reverse=True)

        # Overall status
        total_remaining = total_budget - total_spent
        overall_percent = (total_spent / total_budget * 100) if total_budget > 0 else 0

        if overall_percent >= 120:
            overall_status = BudgetStatus.CRITICAL
        elif overall_percent >= 100:
            overall_status = BudgetStatus.OVER_BUDGET
        elif overall_percent >= 80:
            overall_status = BudgetStatus.WARNING
        else:
            overall_status = BudgetStatus.ON_TRACK

        # Estimate percent of season complete
        today = date.today()
        if today.month >= 3 and today.month <= 6:
            season_pct = 30 + (today.month - 3) * 20  # Planting season
        elif today.month >= 7 and today.month <= 9:
            season_pct = 70 + (today.month - 7) * 10  # Growing season
        elif today.month >= 10:
            season_pct = 95  # Harvest
        else:
            season_pct = 10  # Off-season

        # Project profit
        yield_goal = request.yield_goal or crop_data["default_yield"]
        grain_price = request.grain_price_target or crop_data["default_price"]
        projected_revenue = yield_goal * grain_price * request.acres

        # Estimate final costs based on spending rate
        if season_pct > 0:
            projected_total_cost = total_spent / (season_pct / 100)
        else:
            projected_total_cost = total_budget

        projected_profit = projected_revenue - projected_total_cost

        # Break-even status
        be_yield = projected_total_cost / request.acres / grain_price if grain_price > 0 else 0
        if yield_goal > be_yield * 1.1:
            be_status = "ON TRACK - Yield goal exceeds break-even by good margin"
        elif yield_goal > be_yield:
            be_status = "TIGHT - Yield goal barely exceeds break-even"
        else:
            be_status = "AT RISK - Yield goal below break-even"

        # Recommendations
        recs = self._generate_budget_recommendations(
            overall_status, category_budgets, projected_profit, be_status
        )

        return BudgetTrackerResponse(
            crop_year=request.crop_year,
            crop=request.crop.value,
            acres=request.acres,
            total_budget=round(total_budget, 2),
            total_spent=round(total_spent, 2),
            total_remaining=round(total_remaining, 2),
            overall_status=overall_status,
            percent_of_season=season_pct,
            category_budgets=category_budgets,
            alerts=alerts,
            projected_profit=round(projected_profit, 2),
            break_even_status=be_status,
            recommendations=recs,
        )

    def _get_actual_spending(self, crop_year: int) -> Dict[str, float]:
        """Get actual spending by category from database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT category, SUM(amount) as total
                FROM expenses
                WHERE tax_year = ? AND is_active = 1
                GROUP BY category
            """, (crop_year,))

            rows = cursor.fetchall()
            conn.close()

            return {row["category"]: float(row["total"]) for row in rows}
        except Exception:
            return {}  # Return empty if no database or table

    def _generate_budget_recommendations(
        self,
        status: BudgetStatus,
        categories: List[BudgetTarget],
        projected_profit: float,
        be_status: str
    ) -> List[str]:
        """Generate budget recommendations."""
        recs = []

        if status == BudgetStatus.CRITICAL:
            recs.append("⚠️ CRITICAL: Spending significantly over budget. Immediate cost review needed.")
        elif status == BudgetStatus.OVER_BUDGET:
            recs.append("⚠️ Over budget - review remaining purchases carefully")
        elif status == BudgetStatus.WARNING:
            recs.append("Approaching budget limits - monitor closely")
        else:
            recs.append("✓ Spending on track with budget")

        # Find worst categories
        over_budget = [c for c in categories if c.status in [BudgetStatus.OVER_BUDGET, BudgetStatus.CRITICAL]]
        if over_budget:
            worst = over_budget[0]
            recs.append(f"Highest concern: {worst.category} at {worst.percent_used:.0f}% of budget")

        if projected_profit < 0:
            recs.append(f"⚠️ Currently projecting a LOSS of ${abs(projected_profit):,.2f}")
            recs.append("Must either cut remaining costs or increase price/yield targets")
        else:
            recs.append(f"Projected profit: ${projected_profit:,.2f}")

        if "AT RISK" in be_status:
            recs.append("Break-even at risk - consider cost cuts or yield improvement")

        return recs

    # ========================================================================
    # QUICK SUMMARY - ALL IN ONE
    # ========================================================================

    def get_profitability_summary(
        self,
        crop: CropType,
        acres: float,
        expected_yield: Optional[float] = None,
        expected_price: Optional[float] = None,
        cost_per_acre: Optional[float] = None,
        is_irrigated: bool = False
    ) -> Dict[str, Any]:
        """
        Quick profitability summary combining all analyses.

        One call to get:
        - Break-even analysis
        - Input ROI ranking
        - Key scenarios
        - Recommendations
        """
        # Break-even
        be_request = BreakEvenRequest(
            crop=crop,
            acres=acres,
            expected_yield=expected_yield,
            expected_price=expected_price,
            cost_per_acre=cost_per_acre,
        )
        break_even = self.calculate_break_even(be_request)

        # Input ROI
        roi_request = InputROIRequest(
            crop=crop,
            acres=acres,
            expected_yield=expected_yield,
            grain_price=expected_price,
            is_irrigated=is_irrigated,
        )
        input_roi = self.rank_inputs_by_roi(roi_request)

        # Scenarios
        scenario_request = ScenarioRequest(
            crop=crop,
            acres=acres,
            base_yield=expected_yield,
            base_price=expected_price,
            base_cost_per_acre=cost_per_acre,
        )
        scenarios = self.run_scenarios(scenario_request)

        # Compile summary
        return {
            "overview": {
                "crop": crop.value,
                "acres": acres,
                "expected_yield": break_even.current_scenario["expected_yield"],
                "expected_price": break_even.current_scenario["expected_price"],
                "cost_per_acre": break_even.cost_per_acre,
                "projected_profit": break_even.current_scenario["net_profit"],
                "profitable": break_even.current_scenario["profitable"],
            },
            "break_even": {
                "yield_needed": break_even.current_scenario["break_even_yield"],
                "price_needed": break_even.current_scenario["break_even_price"],
                "yield_cushion": break_even.margin_analysis["yield_cushion_percent"],
                "price_cushion": break_even.margin_analysis["price_cushion_percent"],
                "risk_level": break_even.margin_analysis["risk_level"],
            },
            "top_cuts": [
                {
                    "category": c["category"],
                    "savings": c["potential_savings"],
                    "risk": c["risk"],
                    "recommendation": c["recommendation"],
                }
                for c in input_roi.cut_recommendations[:3]
            ],
            "scenario_range": {
                "best_profit": scenarios.best_case.total_profit,
                "worst_profit": scenarios.worst_case.total_profit,
                "profitable_scenarios": f"{scenarios.profitable_scenarios}/{len(scenarios.scenarios)}",
                "risk": scenarios.risk_assessment,
            },
            "key_recommendations": (
                break_even.recommendations[:2] +
                scenarios.recommendations[:2]
            ),
        }


# ============================================================================
# SINGLETON
# ============================================================================

_profitability_service: Optional[ProfitabilityService] = None


def get_profitability_service(db_path: str = "agtools.db") -> ProfitabilityService:
    """Get or create the profitability service singleton."""
    global _profitability_service
    if _profitability_service is None:
        _profitability_service = ProfitabilityService(db_path)
    return _profitability_service
