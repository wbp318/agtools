"""
Yield Response Data Models

Data classes for yield response curve and economic optimum rate calculations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum


class Crop(str, Enum):
    """Supported crop types."""
    CORN = "corn"
    SOYBEAN = "soybean"
    WHEAT = "wheat"


class Nutrient(str, Enum):
    """Nutrient types for yield response."""
    NITROGEN = "nitrogen"
    PHOSPHORUS = "phosphorus"
    POTASSIUM = "potassium"
    SULFUR = "sulfur"


class SoilTestLevel(str, Enum):
    """Soil test fertility levels."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ResponseModel(str, Enum):
    """Yield response curve model types."""
    QUADRATIC = "quadratic"
    QUADRATIC_PLATEAU = "quadratic_plateau"
    LINEAR_PLATEAU = "linear_plateau"
    MITSCHERLICH = "mitscherlich"
    SQUARE_ROOT = "square_root"


@dataclass
class YieldCurvePoint:
    """A single point on the yield response curve."""
    rate_lb_per_acre: float
    yield_bu_per_acre: float
    marginal_yield: float = 0.0
    marginal_response: float = 0.0


@dataclass
class YieldCurveRequest:
    """Request parameters for generating a yield response curve."""
    crop: str = "corn"
    nutrient: str = "nitrogen"
    min_rate: float = 0
    max_rate: float = 250
    rate_step: float = 10
    soil_test_level: str = "medium"
    yield_potential: float = 200
    previous_crop: Optional[str] = None
    response_model: str = "quadratic_plateau"

    def to_dict(self) -> dict:
        """Convert to dictionary for API request."""
        return {
            "crop": self.crop,
            "nutrient": self.nutrient,
            "min_rate": self.min_rate,
            "max_rate": self.max_rate,
            "rate_step": self.rate_step,
            "soil_test_level": self.soil_test_level,
            "yield_potential": self.yield_potential,
            "previous_crop": self.previous_crop,
            "response_model": self.response_model,
        }


@dataclass
class YieldCurveResponse:
    """Response containing yield curve data."""
    curve_data: List[YieldCurvePoint]
    model_type: str
    crop: str
    nutrient: str
    plateau_yield: Optional[float] = None
    plateau_rate: Optional[float] = None
    max_yield: Optional[float] = None
    max_yield_rate: Optional[float] = None

    @classmethod
    def from_dict(cls, data: dict) -> "YieldCurveResponse":
        """Create from API response dictionary."""
        curve_points = []
        for point in data.get("curve_data", []):
            curve_points.append(YieldCurvePoint(
                rate_lb_per_acre=point.get("rate_lb_per_acre", 0),
                yield_bu_per_acre=point.get("yield_bu_per_acre", 0),
                marginal_yield=point.get("marginal_yield", 0),
                marginal_response=point.get("marginal_response", 0),
            ))

        plateau_info = data.get("plateau_info", {})

        return cls(
            curve_data=curve_points,
            model_type=data.get("model_type", ""),
            crop=data.get("crop", ""),
            nutrient=data.get("nutrient", ""),
            plateau_yield=plateau_info.get("plateau_yield"),
            plateau_rate=plateau_info.get("plateau_rate"),
            max_yield=data.get("max_yield"),
            max_yield_rate=data.get("max_yield_rate"),
        )


@dataclass
class EORRequest:
    """Request parameters for Economic Optimum Rate calculation."""
    crop: str = "corn"
    nutrient: str = "nitrogen"
    nutrient_cost_per_lb: float = 0.65
    grain_price_per_bu: float = 4.50
    soil_test_level: str = "medium"
    yield_potential: float = 200
    previous_crop: Optional[str] = None
    response_model: str = "quadratic_plateau"
    acres: float = 100

    def to_dict(self) -> dict:
        """Convert to dictionary for API request."""
        return {
            "crop": self.crop,
            "nutrient": self.nutrient,
            "nutrient_price_per_lb": self.nutrient_cost_per_lb,
            "grain_price_per_bu": self.grain_price_per_bu,
            "soil_test_level": self.soil_test_level,
            "yield_potential": self.yield_potential,
            "previous_crop": self.previous_crop,
            "response_model": self.response_model,
            "acres": self.acres,
        }


@dataclass
class EORResult:
    """Economic Optimum Rate calculation result."""
    economic_optimum_rate: float
    eor_yield: float
    max_yield_rate: float
    max_yield: float
    yield_sacrifice: float
    price_ratio: float
    net_return_at_eor: float
    net_return_at_max: float
    savings_vs_max: float
    fertilizer_savings_lb: float
    recommendation: str
    crop: str = ""
    nutrient: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "EORResult":
        """Create from API response dictionary."""
        return cls(
            economic_optimum_rate=data.get("economic_optimum_rate_lb_per_acre", data.get("economic_optimum_rate", 0)),
            eor_yield=data.get("eor_yield_bu_per_acre", data.get("expected_yield_at_eor", 0)),
            max_yield_rate=data.get("max_yield_rate", 0),
            max_yield=data.get("max_possible_yield", data.get("max_yield", 0)),
            yield_sacrifice=data.get("yield_sacrifice", 0),
            price_ratio=data.get("price_ratio", 0),
            net_return_at_eor=data.get("eor_net_return_per_acre", data.get("net_return_at_eor", 0)),
            net_return_at_max=data.get("net_return_at_max_yield", 0),
            savings_vs_max=data.get("savings_vs_max_yield", 0),
            fertilizer_savings_lb=data.get("fertilizer_savings_lb", 0),
            recommendation=data.get("recommendation", ""),
            crop=data.get("crop", ""),
            nutrient=data.get("nutrient", ""),
        )


@dataclass
class RateComparison:
    """Comparison of different application rates."""
    rate: float
    yield_bu: float
    gross_revenue: float
    fertilizer_cost: float
    net_return: float
    rank: int = 0


@dataclass
class CompareRatesRequest:
    """Request for comparing multiple application rates."""
    crop: str = "corn"
    nutrient: str = "nitrogen"
    rates_to_compare: List[float] = field(default_factory=lambda: [120, 150, 180, 210])
    nutrient_cost_per_lb: float = 0.65
    grain_price_per_bu: float = 4.50
    soil_test_level: str = "medium"
    yield_potential: float = 200
    acres: float = 100

    def to_dict(self) -> dict:
        return {
            "crop": self.crop,
            "nutrient": self.nutrient,
            "rates": self.rates_to_compare,
            "nutrient_price_per_lb": self.nutrient_cost_per_lb,
            "grain_price_per_bu": self.grain_price_per_bu,
            "soil_test_level": self.soil_test_level,
            "yield_potential": self.yield_potential,
            "acres": self.acres,
        }


@dataclass
class CompareRatesResponse:
    """Response with rate comparison data."""
    comparisons: List[RateComparison]
    best_rate: float
    best_net_return: float

    @classmethod
    def from_dict(cls, data: dict) -> "CompareRatesResponse":
        comparisons = []
        for i, comp in enumerate(data.get("rate_comparisons", data.get("comparisons", []))):
            comparisons.append(RateComparison(
                rate=comp.get("rate", 0),
                yield_bu=comp.get("yield_bu_per_acre", comp.get("yield_bu", 0)),
                gross_revenue=comp.get("gross_revenue", 0),
                fertilizer_cost=comp.get("fertilizer_cost", 0),
                net_return=comp.get("net_return", comp.get("net_return_per_acre", 0)),
                rank=comp.get("rank", i + 1),
            ))

        return cls(
            comparisons=comparisons,
            best_rate=data.get("best_rate", comparisons[0].rate if comparisons else 0),
            best_net_return=data.get("best_net_return", comparisons[0].net_return if comparisons else 0),
        )


@dataclass
class PriceSensitivityRequest:
    """Request for price sensitivity analysis."""
    crop: str = "corn"
    nutrient: str = "nitrogen"
    soil_test_level: str = "medium"
    yield_potential: float = 200
    nutrient_cost_range: List[float] = field(default_factory=lambda: [0.45, 0.55, 0.65, 0.75, 0.85])
    grain_price_range: List[float] = field(default_factory=lambda: [4.00, 4.50, 5.00, 5.50])

    def to_dict(self) -> dict:
        return {
            "crop": self.crop,
            "nutrient": self.nutrient,
            "soil_test_level": self.soil_test_level,
            "yield_potential": self.yield_potential,
            "nutrient_cost_range": self.nutrient_cost_range,
            "grain_price_range": self.grain_price_range,
        }


@dataclass
class PriceSensitivityCell:
    """Single cell in price sensitivity matrix."""
    nutrient_cost: float
    grain_price: float
    optimal_rate: float
    price_ratio: float


@dataclass
class PriceSensitivityResponse:
    """Response with price sensitivity matrix."""
    matrix: List[PriceSensitivityCell]
    nutrient_costs: List[float]
    grain_prices: List[float]

    @classmethod
    def from_dict(cls, data: dict) -> "PriceSensitivityResponse":
        cells = []
        matrix_data = data.get("sensitivity_matrix", data.get("matrix", []))

        for row in matrix_data:
            cells.append(PriceSensitivityCell(
                nutrient_cost=row.get("nutrient_cost", 0),
                grain_price=row.get("grain_price", 0),
                optimal_rate=row.get("optimal_rate", row.get("eor", 0)),
                price_ratio=row.get("price_ratio", 0),
            ))

        return cls(
            matrix=cells,
            nutrient_costs=data.get("nutrient_costs", []),
            grain_prices=data.get("grain_prices", []),
        )


@dataclass
class MultiNutrientRequest:
    """Request for multi-nutrient optimization."""
    crop: str = "corn"
    yield_potential: float = 200
    soil_test_p_ppm: float = 20
    soil_test_k_ppm: float = 150
    previous_crop: Optional[str] = None
    budget_per_acre: Optional[float] = None
    nutrient_prices: Dict[str, float] = field(default_factory=lambda: {
        "nitrogen": 0.65,
        "phosphorus": 0.75,
        "potassium": 0.45
    })
    grain_price: float = 4.50
    acres: float = 100

    def to_dict(self) -> dict:
        return {
            "crop": self.crop,
            "yield_potential": self.yield_potential,
            "soil_test_p_ppm": self.soil_test_p_ppm,
            "soil_test_k_ppm": self.soil_test_k_ppm,
            "previous_crop": self.previous_crop,
            "budget_per_acre": self.budget_per_acre,
            "nutrient_prices": self.nutrient_prices,
            "grain_price": self.grain_price,
            "acres": self.acres,
        }


@dataclass
class MultiNutrientResult:
    """Result of multi-nutrient optimization."""
    nitrogen_rate: float
    p2o5_rate: float
    k2o_rate: float
    total_cost_per_acre: float
    expected_yield: float
    expected_net_return: float
    budget_status: str
    recommendations: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> "MultiNutrientResult":
        optimal_rates = data.get("optimal_rates", {})
        return cls(
            nitrogen_rate=optimal_rates.get("nitrogen", 0),
            p2o5_rate=optimal_rates.get("p2o5", 0),
            k2o_rate=optimal_rates.get("k2o", 0),
            total_cost_per_acre=data.get("total_cost_per_acre", 0),
            expected_yield=data.get("expected_yield", 0),
            expected_net_return=data.get("expected_net_return", 0),
            budget_status=data.get("limiting_factor", data.get("budget_status", "")),
            recommendations=data.get("recommendations", []),
        )


@dataclass
class PriceRatioGuide:
    """Price ratio quick reference guide."""
    entries: List[Dict[str, str]]
    crop: str
    nutrient: str

    @classmethod
    def from_dict(cls, data: dict) -> "PriceRatioGuide":
        return cls(
            entries=data.get("guide", data.get("entries", [])),
            crop=data.get("crop", "corn"),
            nutrient=data.get("nutrient", "nitrogen"),
        )
