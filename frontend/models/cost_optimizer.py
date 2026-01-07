"""
Cost Optimizer Data Models

Data classes for input cost optimization across labor, fertilizer, pesticides, and irrigation.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class OptimizationPriority(str, Enum):
    """Optimization priority options."""
    COST_REDUCTION = "cost_reduction"
    ROI_MAXIMIZATION = "roi_maximization"
    SUSTAINABILITY = "sustainability"
    RISK_REDUCTION = "risk_reduction"


class IrrigationType(str, Enum):
    """Irrigation system types."""
    CENTER_PIVOT = "center_pivot"
    DRIP = "drip"
    FLOOD = "flood"
    FURROW = "furrow"
    SPRINKLER = "sprinkler"
    NONE = "none"


@dataclass
class CropInfo:
    """Information about a crop for optimization."""
    crop: str = "corn"
    acres: float = 100
    yield_goal: float = 200

    def to_dict(self) -> dict:
        return {
            "crop": self.crop,
            "acres": self.acres,
            "yield_goal": self.yield_goal,
        }


@dataclass
class QuickEstimateRequest:
    """Request for quick cost estimate."""
    acres: float = 100
    crop: str = "corn"
    is_irrigated: bool = False
    yield_goal: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "acres": self.acres,
            "crop": self.crop,
            "is_irrigated": self.is_irrigated,
            "yield_goal": self.yield_goal,
        }


@dataclass
class QuickEstimateResponse:
    """Response from quick cost estimate."""
    crop: str
    acres: float
    yield_goal: float
    is_irrigated: bool
    cost_breakdown: Dict[str, float]
    total_cost_per_acre: float
    total_cost: float
    gross_revenue: float
    net_return: float
    return_per_acre: float
    break_even_yield: float
    potential_savings_low: float
    potential_savings_high: float

    @classmethod
    def from_dict(cls, data: dict) -> "QuickEstimateResponse":
        economics = data.get("economics", {})
        optimization = data.get("optimization_potential", {})

        return cls(
            crop=data.get("crop", ""),
            acres=data.get("acres", 0),
            yield_goal=data.get("yield_goal", 0),
            is_irrigated=data.get("is_irrigated", False),
            cost_breakdown=data.get("cost_breakdown_per_acre", {}),
            total_cost_per_acre=data.get("total_cost_per_acre", 0),
            total_cost=data.get("total_cost", 0),
            gross_revenue=economics.get("gross_revenue", 0),
            net_return=economics.get("net_return", 0),
            return_per_acre=economics.get("return_per_acre", 0),
            break_even_yield=economics.get("break_even_yield", 0),
            potential_savings_low=optimization.get("potential_savings_low", 0),
            potential_savings_high=optimization.get("potential_savings_high", 0),
        )


@dataclass
class FarmProfileRequest:
    """Complete farm profile for analysis."""
    total_acres: float = 500
    crops: List[CropInfo] = field(default_factory=lambda: [CropInfo()])
    irrigation_system: Optional[str] = None
    water_source: Optional[str] = None
    soil_test_results: Optional[Dict[str, float]] = None
    season_length_days: int = 120
    optimization_priority: str = "cost_reduction"

    def to_dict(self) -> dict:
        return {
            "farm_profile": {
                "total_acres": self.total_acres,
                "crops": [c.to_dict() for c in self.crops],
                "irrigation_system": self.irrigation_system,
                "water_source": self.water_source,
                "soil_test_results": self.soil_test_results,
            },
            "season_length_days": self.season_length_days,
            "optimization_priority": self.optimization_priority,
        }


@dataclass
class CostCategory:
    """Cost breakdown for a category."""
    category: str
    total_cost: float
    cost_per_acre: float
    potential_savings: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationOpportunity:
    """A single optimization opportunity."""
    category: str
    opportunity: str
    potential_savings: float
    implementation_cost: float
    roi_percent: float
    priority: str  # high, medium, low
    action_steps: List[str] = field(default_factory=list)


@dataclass
class CompleteAnalysisResponse:
    """Response from complete farm analysis."""
    total_acres: float
    crops: List[str]
    has_irrigation: bool
    optimization_priority: str

    # Cost totals
    total_variable_cost: float
    total_fixed_cost: float
    total_input_cost: float
    cost_per_acre: float
    total_potential_savings: float
    potential_savings_percent: float

    # Categories
    labor_costs: Optional[CostCategory] = None
    application_costs: Optional[CostCategory] = None
    irrigation_costs: Optional[CostCategory] = None

    # Opportunities
    opportunities: List[OptimizationOpportunity] = field(default_factory=list)
    action_plan: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "CompleteAnalysisResponse":
        summary = data.get("farm_summary", {})
        totals = data.get("total_costs", {})
        categories = data.get("cost_categories", {})

        # Parse cost categories
        labor = None
        if "labor" in categories:
            labor_data = categories["labor"]
            labor = CostCategory(
                category="labor",
                total_cost=labor_data.get("summary", {}).get("total_cost", 0),
                cost_per_acre=labor_data.get("summary", {}).get("cost_per_acre", 0),
                potential_savings=labor_data.get("potential_savings", 0),
                details=labor_data,
            )

        applications = None
        if "applications" in categories:
            app_data = categories["applications"]
            applications = CostCategory(
                category="applications",
                total_cost=app_data.get("summary", {}).get("total_cost", 0),
                cost_per_acre=app_data.get("summary", {}).get("cost_per_acre", 0),
                potential_savings=app_data.get("potential_savings", 0),
                details=app_data,
            )

        irrigation = None
        if "irrigation" in categories:
            irr_data = categories["irrigation"]
            irrigation = CostCategory(
                category="irrigation",
                total_cost=irr_data.get("summary", {}).get("total_cost", irr_data.get("summary", {}).get("variable_cost", 0)),
                cost_per_acre=irr_data.get("summary", {}).get("cost_per_acre", 0),
                potential_savings=irr_data.get("potential_savings", 0),
                details=irr_data,
            )

        # Parse opportunities
        opportunities = []
        for opp in data.get("optimization_opportunities", []):
            opportunities.append(OptimizationOpportunity(
                category=opp.get("category", ""),
                opportunity=opp.get("opportunity", opp.get("description", "")),
                potential_savings=opp.get("potential_savings", 0),
                implementation_cost=opp.get("implementation_cost", 0),
                roi_percent=opp.get("roi_percent", opp.get("roi", 0)),
                priority=opp.get("priority", "medium"),
                action_steps=opp.get("action_steps", []),
            ))

        return cls(
            total_acres=summary.get("total_acres", 0),
            crops=summary.get("crops", []),
            has_irrigation=summary.get("has_irrigation", False),
            optimization_priority=summary.get("optimization_priority", ""),
            total_variable_cost=totals.get("total_variable_cost", 0),
            total_fixed_cost=totals.get("total_fixed_cost", 0),
            total_input_cost=totals.get("total_input_cost", 0),
            cost_per_acre=totals.get("cost_per_acre", 0),
            total_potential_savings=totals.get("total_potential_savings", 0),
            potential_savings_percent=totals.get("potential_savings_percent", 0),
            labor_costs=labor,
            application_costs=applications,
            irrigation_costs=irrigation,
            opportunities=opportunities,
            action_plan=data.get("action_plan", []),
        )


@dataclass
class FertilizerRequest:
    """Request for fertilizer optimization."""
    crop: str = "corn"
    acres: float = 100
    yield_goal: float = 200
    soil_test_p_ppm: float = 20
    soil_test_k_ppm: float = 150
    soil_test_ph: float = 6.5
    previous_crop: Optional[str] = None
    organic_matter_percent: float = 3.0

    def to_dict(self) -> dict:
        # Calculate nitrogen credit from previous crop
        n_credit = 0
        if self.previous_crop == "soybean":
            n_credit = 40  # Soybean N credit
        elif self.previous_crop == "alfalfa":
            n_credit = 100  # Alfalfa N credit

        return {
            "crop": self.crop,
            "acres": self.acres,
            "yield_goal": self.yield_goal,
            "soil_test_p_ppm": self.soil_test_p_ppm,
            "soil_test_k_ppm": self.soil_test_k_ppm,
            "soil_ph": self.soil_test_ph,  # Backend expects soil_ph
            "organic_matter_percent": self.organic_matter_percent,
            "nitrogen_credit_lb_per_acre": n_credit,
        }


@dataclass
class NutrientRecommendation:
    """Fertilizer recommendation for a nutrient."""
    nutrient: str
    recommended_rate: float
    recommended_product: str
    cost_per_acre: float
    total_cost: float


@dataclass
class FertilizerResponse:
    """Response from fertilizer optimization."""
    recommendations: List[NutrientRecommendation]
    total_cost_per_acre: float
    total_cost: float
    potential_savings: float

    @classmethod
    def from_dict(cls, data: dict) -> "FertilizerResponse":
        recs = []
        acres = data.get("acres", 1)

        # Parse recommendations from backend format
        for rec in data.get("recommendations", []):
            # Backend format: {product, rate_per_acre, nutrient_supplied, cost_per_acre, timing}
            # Get nutrient name from nutrient_supplied dict (first key)
            nutrient_supplied = rec.get("nutrient_supplied", {})
            nutrient = list(nutrient_supplied.keys())[0] if nutrient_supplied else rec.get("nutrient", "")

            recs.append(NutrientRecommendation(
                nutrient=nutrient,
                recommended_rate=rec.get("rate_per_acre", rec.get("recommended_rate_lb_per_acre", 0)),
                recommended_product=rec.get("product", rec.get("recommended_product", "")),
                cost_per_acre=rec.get("cost_per_acre", 0),
                total_cost=rec.get("cost_per_acre", 0) * acres,
            ))

        # Get cost summary from backend
        cost_summary = data.get("cost_summary", {})
        total_cost_per_acre = cost_summary.get("cost_per_acre", data.get("total_fertilizer_cost_per_acre", 0))
        total_cost = cost_summary.get("total_cost", data.get("total_fertilizer_cost", 0))

        # Calculate potential savings from optimization opportunities
        opportunities = data.get("optimization_opportunities", [])
        potential_savings = sum(opp.get("potential_savings", 0) for opp in opportunities) if opportunities else 0

        return cls(
            recommendations=recs,
            total_cost_per_acre=total_cost_per_acre,
            total_cost=total_cost,
            potential_savings=potential_savings,
        )


@dataclass
class IrrigationCostRequest:
    """Request for irrigation cost analysis."""
    system_type: str = "center_pivot"
    acres: float = 125
    crop: str = "corn"
    water_applied_inches: float = 12
    pumping_depth_ft: float = 200
    water_cost_per_acre_inch: float = 5.0
    electricity_rate: float = 0.10

    def to_dict(self) -> dict:
        return {
            "system_type": self.system_type,
            "acres": self.acres,
            "crop": self.crop,
            "water_applied_inches": self.water_applied_inches,
            "pumping_depth_ft": self.pumping_depth_ft,
            "water_cost_per_acre_inch": self.water_cost_per_acre_inch,
            "electricity_rate": self.electricity_rate,
        }


@dataclass
class IrrigationCostResponse:
    """Response from irrigation cost analysis."""
    water_cost: float
    pumping_cost: float
    maintenance_cost: float
    total_variable_cost: float
    total_fixed_cost: float
    total_cost: float
    cost_per_acre: float
    cost_per_acre_inch: float
    efficiency_percent: float
    potential_savings: float

    @classmethod
    def from_dict(cls, data: dict) -> "IrrigationCostResponse":
        costs = data.get("costs", data)
        return cls(
            water_cost=costs.get("water_cost", 0),
            pumping_cost=costs.get("pumping_cost", costs.get("energy_cost", 0)),
            maintenance_cost=costs.get("maintenance_cost", 0),
            total_variable_cost=costs.get("total_variable_cost", 0),
            total_fixed_cost=costs.get("total_fixed_cost", 0),
            total_cost=costs.get("total_cost", 0),
            cost_per_acre=costs.get("cost_per_acre", 0),
            cost_per_acre_inch=costs.get("cost_per_acre_inch", 0),
            efficiency_percent=data.get("system_efficiency_percent", data.get("efficiency", 85)),
            potential_savings=data.get("potential_savings", 0),
        )


@dataclass
class LaborScoutingRequest:
    """Request for scouting labor analysis."""
    total_acres: float = 500
    fields: List[Dict[str, Any]] = field(default_factory=list)
    scouting_frequency_days: int = 7
    hours_per_100_acres: float = 2.0

    def to_dict(self) -> dict:
        return {
            "total_acres": self.total_acres,
            "fields": self.fields,
            "scouting_frequency_days": self.scouting_frequency_days,
            "hours_per_100_acres": self.hours_per_100_acres,
        }


@dataclass
class LaborScoutingResponse:
    """Response from scouting labor analysis."""
    total_hours: float
    total_cost: float
    cost_per_acre: float
    recommended_groupings: List[Dict[str, Any]]
    potential_savings: float

    @classmethod
    def from_dict(cls, data: dict) -> "LaborScoutingResponse":
        return cls(
            total_hours=data.get("total_scouting_hours", data.get("total_hours", 0)),
            total_cost=data.get("total_scouting_cost", data.get("total_cost", 0)),
            cost_per_acre=data.get("cost_per_acre", 0),
            recommended_groupings=data.get("recommended_field_groupings", []),
            potential_savings=data.get("potential_savings", 0),
        )
