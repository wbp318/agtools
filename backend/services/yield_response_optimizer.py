"""
Yield Response Curve Optimizer
Calculates economic optimum rates (EOR) for fertilizer inputs
Uses diminishing returns models to find profit-maximizing application rates

This module helps answer: "What rate maximizes my profit?" not just "What does the crop need?"
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import math


class ResponseModel(str, Enum):
    """Mathematical models for yield response curves"""
    QUADRATIC = "quadratic"           # y = a + bx - cx²  (most common)
    QUADRATIC_PLATEAU = "quadratic_plateau"  # Quadratic until plateau
    LINEAR_PLATEAU = "linear_plateau"  # Linear until plateau
    MITSCHERLICH = "mitscherlich"     # y = a(1 - e^(-cx))  (exponential approach)
    SQUARE_ROOT = "square_root"       # y = a + bx^0.5 - cx


class NutrientType(str, Enum):
    NITROGEN = "nitrogen"
    PHOSPHORUS = "phosphorus"
    POTASSIUM = "potassium"
    SULFUR = "sulfur"


# Crop-specific yield response parameters (based on university research)
# These represent typical Midwest conditions - can be calibrated with local data
YIELD_RESPONSE_PARAMS = {
    "corn": {
        "nitrogen": {
            # Quadratic model: yield = base + (linear * N) - (quadratic * N²)
            "model": ResponseModel.QUADRATIC,
            "base_yield": 80,           # bu/acre with 0 N (residual soil N)
            "linear_coefficient": 0.85,  # bu/acre per lb N (initial response)
            "quadratic_coefficient": 0.0022,  # diminishing returns factor
            "plateau_yield": 220,        # maximum achievable yield
            "typical_range": (120, 220),  # lb N/acre typical range
            "soil_n_credit": {
                "soybean": 40,    # lb N credit after soybeans
                "corn": 0,        # no credit after corn
                "alfalfa_1yr": 100,
                "alfalfa_2yr": 80,
                "alfalfa_3yr": 60,
            },
            "notes": "Response varies with hybrid, soil type, and weather"
        },
        "phosphorus": {
            "model": ResponseModel.QUADRATIC_PLATEAU,
            "base_yield": 170,          # with adequate soil P
            "linear_coefficient": 0.25,
            "quadratic_coefficient": 0.0008,
            "plateau_yield": 200,
            "critical_soil_test": 15,   # ppm Bray-1 below which response expected
            "maintenance_rate": 0.37,   # lb P2O5 per bushel removed
            "notes": "Response mainly when soil test P < 15 ppm"
        },
        "potassium": {
            "model": ResponseModel.QUADRATIC_PLATEAU,
            "base_yield": 175,
            "linear_coefficient": 0.15,
            "quadratic_coefficient": 0.0005,
            "plateau_yield": 200,
            "critical_soil_test": 120,  # ppm below which response expected
            "maintenance_rate": 0.27,   # lb K2O per bushel removed
            "notes": "Response mainly when soil test K < 120 ppm"
        },
        "sulfur": {
            "model": ResponseModel.LINEAR_PLATEAU,
            "base_yield": 180,
            "linear_coefficient": 0.8,
            "plateau_yield": 200,
            "plateau_rate": 25,         # lb S where plateau begins
            "notes": "Response on sandy soils with low OM"
        }
    },
    "soybean": {
        "nitrogen": {
            # Soybeans fix their own N - typically no response to applied N
            "model": ResponseModel.LINEAR_PLATEAU,
            "base_yield": 50,
            "linear_coefficient": 0.0,   # No response - N fixation
            "plateau_yield": 50,
            "plateau_rate": 0,
            "notes": "Soybeans fix N via rhizobia - do not apply N fertilizer"
        },
        "phosphorus": {
            "model": ResponseModel.QUADRATIC_PLATEAU,
            "base_yield": 45,
            "linear_coefficient": 0.12,
            "quadratic_coefficient": 0.0006,
            "plateau_yield": 55,
            "critical_soil_test": 12,
            "maintenance_rate": 0.80,
            "notes": "Response when soil test P < 12 ppm"
        },
        "potassium": {
            "model": ResponseModel.QUADRATIC_PLATEAU,
            "base_yield": 40,
            "linear_coefficient": 0.08,
            "quadratic_coefficient": 0.0003,
            "plateau_yield": 55,
            "critical_soil_test": 120,
            "maintenance_rate": 1.40,
            "notes": "Soybeans have high K demand"
        },
        "sulfur": {
            "model": ResponseModel.LINEAR_PLATEAU,
            "base_yield": 48,
            "linear_coefficient": 0.3,
            "plateau_yield": 55,
            "plateau_rate": 20,
            "notes": "Response on sandy, low OM soils"
        }
    },
    "wheat": {
        "nitrogen": {
            "model": ResponseModel.QUADRATIC,
            "base_yield": 40,
            "linear_coefficient": 0.55,
            "quadratic_coefficient": 0.0025,
            "plateau_yield": 90,
            "typical_range": (80, 140),
            "soil_n_credit": {
                "soybean": 30,
                "corn": 0,
            },
            "notes": "Split applications improve efficiency"
        },
        "phosphorus": {
            "model": ResponseModel.QUADRATIC_PLATEAU,
            "base_yield": 55,
            "linear_coefficient": 0.15,
            "quadratic_coefficient": 0.0006,
            "plateau_yield": 70,
            "critical_soil_test": 15,
            "maintenance_rate": 0.50,
            "notes": "Starter P beneficial for early growth"
        },
        "potassium": {
            "model": ResponseModel.QUADRATIC_PLATEAU,
            "base_yield": 60,
            "linear_coefficient": 0.10,
            "quadratic_coefficient": 0.0004,
            "plateau_yield": 70,
            "critical_soil_test": 100,
            "maintenance_rate": 0.30,
            "notes": "Less K responsive than corn"
        },
        "sulfur": {
            "model": ResponseModel.LINEAR_PLATEAU,
            "base_yield": 62,
            "linear_coefficient": 0.4,
            "plateau_yield": 70,
            "plateau_rate": 20,
            "notes": "Response on sandy soils"
        }
    }
}

# Default input costs (can be overridden with pricing service)
DEFAULT_INPUT_COSTS = {
    "nitrogen": 0.50,       # $/lb N (average across sources)
    "phosphorus": 0.62,     # $/lb P2O5
    "potassium": 0.42,      # $/lb K2O
    "sulfur": 0.45,         # $/lb S
    "application": 8.00,    # $/acre per application
}

# Commodity prices (defaults, should be updated)
DEFAULT_COMMODITY_PRICES = {
    "corn": 4.50,           # $/bushel
    "soybean": 12.00,
    "wheat": 6.00,
}


@dataclass
class YieldPoint:
    """A single point on the yield response curve"""
    input_rate: float       # lb/acre of nutrient
    predicted_yield: float  # bu/acre
    input_cost: float       # $/acre
    gross_revenue: float    # $/acre
    net_return: float       # $/acre (revenue - input cost)
    marginal_return: float  # $/$ invested (return per dollar spent)


@dataclass
class EconomicOptimum:
    """Economic Optimum Rate calculation result"""
    optimum_rate: float           # lb/acre
    optimum_yield: float          # bu/acre at optimum rate
    agronomic_max_rate: float     # rate that maximizes yield (ignoring cost)
    agronomic_max_yield: float    # maximum achievable yield
    yield_at_optimum_vs_max: float  # % of max yield achieved at EOR

    total_input_cost: float       # $/acre at optimum
    gross_revenue: float          # $/acre at optimum
    net_return: float             # $/acre at optimum

    return_per_dollar: float      # $ return per $ invested
    breakeven_rate: float         # rate where return = cost

    price_ratio: float            # nutrient price / commodity price
    sensitivity: Dict[str, float]  # how optimum changes with prices


class YieldResponseOptimizer:
    """
    Calculates yield response curves and economic optimum rates

    Key concept: The agronomic optimum (maximum yield) is NOT the same as
    the economic optimum (maximum profit). Due to diminishing returns,
    the last units of fertilizer often cost more than they return.

    Economic Optimum Rate (EOR) is where:
    Marginal Cost = Marginal Revenue
    or: Price of nutrient = Value of yield increase
    """

    def __init__(
        self,
        custom_input_costs: Optional[Dict[str, float]] = None,
        custom_commodity_prices: Optional[Dict[str, float]] = None
    ):
        self.input_costs = {**DEFAULT_INPUT_COSTS}
        self.commodity_prices = {**DEFAULT_COMMODITY_PRICES}

        if custom_input_costs:
            self.input_costs.update(custom_input_costs)
        if custom_commodity_prices:
            self.commodity_prices.update(custom_commodity_prices)

    def calculate_yield_response(
        self,
        crop: str,
        nutrient: str,
        rate: float,
        soil_test_level: Optional[float] = None,
        previous_crop: Optional[str] = None
    ) -> float:
        """
        Calculate predicted yield at a given nutrient rate

        Args:
            crop: corn, soybean, wheat
            nutrient: nitrogen, phosphorus, potassium, sulfur
            rate: lb/acre of nutrient applied
            soil_test_level: ppm for P/K (adjusts response)
            previous_crop: for N credit calculation

        Returns:
            Predicted yield in bu/acre
        """
        crop_lower = crop.lower()
        nutrient_lower = nutrient.lower()

        if crop_lower not in YIELD_RESPONSE_PARAMS:
            raise ValueError(f"Crop '{crop}' not supported")

        if nutrient_lower not in YIELD_RESPONSE_PARAMS[crop_lower]:
            raise ValueError(f"Nutrient '{nutrient}' not supported for {crop}")

        params = YIELD_RESPONSE_PARAMS[crop_lower][nutrient_lower]
        model = params["model"]

        # Adjust rate for N credits if applicable
        effective_rate = rate
        if nutrient_lower == "nitrogen" and previous_crop:
            n_credits = params.get("soil_n_credit", {})
            credit = n_credits.get(previous_crop.lower(), 0)
            effective_rate = rate + credit  # Credit effectively adds to applied N

        # Adjust response for soil test level (P and K)
        response_factor = 1.0
        if soil_test_level is not None and nutrient_lower in ["phosphorus", "potassium"]:
            critical_level = params.get("critical_soil_test", 20)
            if soil_test_level >= critical_level * 2:
                response_factor = 0.1  # Very high - minimal response
            elif soil_test_level >= critical_level:
                response_factor = 0.5  # Adequate - reduced response
            else:
                # Below critical - full response expected
                response_factor = 1.0 + (critical_level - soil_test_level) / critical_level * 0.3

        # Calculate yield based on model type
        base = params["base_yield"]
        linear = params["linear_coefficient"] * response_factor
        plateau = params.get("plateau_yield", 300)

        if model == ResponseModel.QUADRATIC:
            quadratic = params["quadratic_coefficient"]
            predicted = base + (linear * effective_rate) - (quadratic * effective_rate ** 2)

        elif model == ResponseModel.QUADRATIC_PLATEAU:
            quadratic = params["quadratic_coefficient"]
            # Calculate where plateau begins
            if linear > 0 and quadratic > 0:
                plateau_rate = linear / (2 * quadratic)
                if effective_rate <= plateau_rate:
                    predicted = base + (linear * effective_rate) - (quadratic * effective_rate ** 2)
                else:
                    predicted = plateau
            else:
                predicted = base

        elif model == ResponseModel.LINEAR_PLATEAU:
            plateau_rate = params.get("plateau_rate", 50)
            if effective_rate <= plateau_rate:
                predicted = base + (linear * effective_rate)
            else:
                predicted = plateau

        elif model == ResponseModel.MITSCHERLICH:
            # Asymptotic model: y = plateau * (1 - e^(-c*x))
            c = params.get("curvature", 0.02)
            predicted = base + (plateau - base) * (1 - math.exp(-c * effective_rate))

        elif model == ResponseModel.SQUARE_ROOT:
            quadratic = params.get("quadratic_coefficient", 0.001)
            predicted = base + (linear * math.sqrt(effective_rate)) - (quadratic * effective_rate)

        else:
            predicted = base

        # Cap at plateau yield
        return min(predicted, plateau)

    def generate_response_curve(
        self,
        crop: str,
        nutrient: str,
        rate_range: Optional[Tuple[float, float]] = None,
        rate_step: float = 10,
        soil_test_level: Optional[float] = None,
        previous_crop: Optional[str] = None,
        commodity_price: Optional[float] = None,
        nutrient_cost: Optional[float] = None,
        application_cost: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete yield response curve with economics

        Returns curve data, economic analysis, and recommendations
        """
        crop_lower = crop.lower()
        nutrient_lower = nutrient.lower()

        # Get default range if not specified
        if rate_range is None:
            params = YIELD_RESPONSE_PARAMS.get(crop_lower, {}).get(nutrient_lower, {})
            typical = params.get("typical_range", (0, 200))
            rate_range = (0, typical[1] * 1.2)  # Go 20% beyond typical max

        # Get prices
        grain_price = commodity_price or self.commodity_prices.get(crop_lower, 5.0)
        fert_cost = nutrient_cost or self.input_costs.get(nutrient_lower, 0.50)
        app_cost = application_cost or self.input_costs.get("application", 8.0)

        # Generate curve points
        curve_points = []
        rates = []
        rate = rate_range[0]

        while rate <= rate_range[1]:
            predicted_yield = self.calculate_yield_response(
                crop, nutrient, rate, soil_test_level, previous_crop
            )

            input_cost = (rate * fert_cost) + (app_cost if rate > 0 else 0)
            gross_revenue = predicted_yield * grain_price
            net_return = gross_revenue - input_cost

            # Calculate marginal return (return per dollar)
            marginal_return = (gross_revenue / input_cost) if input_cost > 0 else 0

            point = YieldPoint(
                input_rate=rate,
                predicted_yield=round(predicted_yield, 1),
                input_cost=round(input_cost, 2),
                gross_revenue=round(gross_revenue, 2),
                net_return=round(net_return, 2),
                marginal_return=round(marginal_return, 2)
            )
            curve_points.append(point)
            rates.append(rate)
            rate += rate_step

        # Find economic optimum
        eor = self.calculate_economic_optimum(
            crop, nutrient, soil_test_level, previous_crop,
            grain_price, fert_cost, app_cost
        )

        return {
            "crop": crop,
            "nutrient": nutrient,
            "soil_test_level": soil_test_level,
            "previous_crop": previous_crop,
            "prices": {
                "commodity_price_per_bu": grain_price,
                "nutrient_cost_per_lb": fert_cost,
                "application_cost_per_acre": app_cost,
                "price_ratio": round(fert_cost / grain_price, 4)
            },
            "curve_data": [
                {
                    "rate": p.input_rate,
                    "yield": p.predicted_yield,
                    "input_cost": p.input_cost,
                    "gross_revenue": p.gross_revenue,
                    "net_return": p.net_return,
                    "return_per_dollar": p.marginal_return
                }
                for p in curve_points
            ],
            "economic_optimum": {
                "optimum_rate": eor.optimum_rate,
                "optimum_yield": eor.optimum_yield,
                "agronomic_max_rate": eor.agronomic_max_rate,
                "agronomic_max_yield": eor.agronomic_max_yield,
                "yield_at_optimum_pct_of_max": eor.yield_at_optimum_vs_max,
                "total_input_cost": eor.total_input_cost,
                "gross_revenue": eor.gross_revenue,
                "net_return": eor.net_return,
                "return_per_dollar": eor.return_per_dollar,
                "breakeven_rate": eor.breakeven_rate
            },
            "recommendation": self._generate_recommendation(eor, crop, nutrient, soil_test_level)
        }

    def calculate_economic_optimum(
        self,
        crop: str,
        nutrient: str,
        soil_test_level: Optional[float] = None,
        previous_crop: Optional[str] = None,
        commodity_price: Optional[float] = None,
        nutrient_cost: Optional[float] = None,
        application_cost: Optional[float] = None
    ) -> EconomicOptimum:
        """
        Calculate the Economic Optimum Rate (EOR)

        EOR is where: Marginal Value Product = Marginal Factor Cost
        Or: (dY/dN) * Grain Price = Nutrient Price

        For quadratic model y = a + bN - cN²:
        dY/dN = b - 2cN

        At optimum: (b - 2cN) * grain_price = nutrient_price
        Solving: N_opt = (b - price_ratio) / (2c)
        where price_ratio = nutrient_price / grain_price
        """
        crop_lower = crop.lower()
        nutrient_lower = nutrient.lower()

        params = YIELD_RESPONSE_PARAMS.get(crop_lower, {}).get(nutrient_lower, {})
        if not params:
            raise ValueError(f"No response data for {crop} {nutrient}")

        # Get prices
        grain_price = commodity_price or self.commodity_prices.get(crop_lower, 5.0)
        fert_cost = nutrient_cost or self.input_costs.get(nutrient_lower, 0.50)
        app_cost = application_cost or self.input_costs.get("application", 8.0)

        price_ratio = fert_cost / grain_price

        model = params["model"]
        base = params["base_yield"]
        linear = params["linear_coefficient"]
        plateau = params.get("plateau_yield", 300)

        # Adjust for soil test response
        response_factor = 1.0
        if soil_test_level is not None and nutrient_lower in ["phosphorus", "potassium"]:
            critical = params.get("critical_soil_test", 20)
            if soil_test_level >= critical * 2:
                response_factor = 0.1
            elif soil_test_level >= critical:
                response_factor = 0.5

        linear_adj = linear * response_factor

        # Calculate optimum based on model
        if model in [ResponseModel.QUADRATIC, ResponseModel.QUADRATIC_PLATEAU]:
            quadratic = params["quadratic_coefficient"]

            if quadratic > 0 and linear_adj > 0:
                # EOR: N = (b - price_ratio) / (2c)
                eor_rate = (linear_adj - price_ratio) / (2 * quadratic)
                eor_rate = max(0, eor_rate)  # Can't be negative

                # Agronomic max (ignoring cost): N = b / (2c)
                agro_max_rate = linear_adj / (2 * quadratic)

                # For plateau model, cap at plateau
                if model == ResponseModel.QUADRATIC_PLATEAU:
                    plateau_rate = linear_adj / (2 * quadratic)
                    eor_rate = min(eor_rate, plateau_rate)
                    agro_max_rate = plateau_rate
            else:
                eor_rate = 0
                agro_max_rate = 0

        elif model == ResponseModel.LINEAR_PLATEAU:
            plateau_rate = params.get("plateau_rate", 50)

            # For linear, any rate up to plateau is economical if linear > price_ratio
            if linear_adj > price_ratio:
                eor_rate = plateau_rate  # Go to plateau
            else:
                eor_rate = 0  # Not economical
            agro_max_rate = plateau_rate

        else:
            # Default - use iterative approach
            eor_rate = self._find_optimum_iterative(
                crop, nutrient, soil_test_level, previous_crop,
                grain_price, fert_cost, app_cost
            )
            agro_max_rate = eor_rate * 1.2  # Estimate

        # Adjust for N credits
        if nutrient_lower == "nitrogen" and previous_crop:
            n_credits = params.get("soil_n_credit", {})
            credit = n_credits.get(previous_crop.lower(), 0)
            eor_rate = max(0, eor_rate - credit)
            agro_max_rate = max(0, agro_max_rate - credit)

        # Calculate yields and economics at optimum
        yield_at_eor = self.calculate_yield_response(
            crop, nutrient, eor_rate, soil_test_level, previous_crop
        )
        yield_at_agro_max = self.calculate_yield_response(
            crop, nutrient, agro_max_rate, soil_test_level, previous_crop
        )

        total_cost = (eor_rate * fert_cost) + (app_cost if eor_rate > 0 else 0)
        gross_rev = yield_at_eor * grain_price
        net_ret = gross_rev - total_cost

        # Calculate return per dollar
        return_per_dollar = gross_rev / total_cost if total_cost > 0 else 0

        # Find breakeven rate (where net return = 0 vs no application)
        base_yield = self.calculate_yield_response(crop, nutrient, 0, soil_test_level, previous_crop)
        base_revenue = base_yield * grain_price
        breakeven_rate = self._find_breakeven_rate(
            crop, nutrient, soil_test_level, previous_crop,
            grain_price, fert_cost, app_cost, base_revenue
        )

        # Price sensitivity analysis
        sensitivity = self._calculate_sensitivity(
            crop, nutrient, soil_test_level, previous_crop,
            grain_price, fert_cost
        )

        return EconomicOptimum(
            optimum_rate=round(eor_rate, 1),
            optimum_yield=round(yield_at_eor, 1),
            agronomic_max_rate=round(agro_max_rate, 1),
            agronomic_max_yield=round(yield_at_agro_max, 1),
            yield_at_optimum_vs_max=round(yield_at_eor / yield_at_agro_max * 100, 1) if yield_at_agro_max > 0 else 100,
            total_input_cost=round(total_cost, 2),
            gross_revenue=round(gross_rev, 2),
            net_return=round(net_ret, 2),
            return_per_dollar=round(return_per_dollar, 2),
            breakeven_rate=round(breakeven_rate, 1),
            price_ratio=round(price_ratio, 4),
            sensitivity=sensitivity
        )

    def _find_optimum_iterative(
        self,
        crop: str,
        nutrient: str,
        soil_test_level: Optional[float],
        previous_crop: Optional[str],
        grain_price: float,
        fert_cost: float,
        app_cost: float
    ) -> float:
        """Find EOR through iterative search (for complex models)"""
        best_rate = 0
        best_return = -float('inf')

        for rate in range(0, 301, 5):
            yield_pred = self.calculate_yield_response(
                crop, nutrient, rate, soil_test_level, previous_crop
            )
            cost = (rate * fert_cost) + (app_cost if rate > 0 else 0)
            net_return = (yield_pred * grain_price) - cost

            if net_return > best_return:
                best_return = net_return
                best_rate = rate

        return float(best_rate)

    def _find_breakeven_rate(
        self,
        crop: str,
        nutrient: str,
        soil_test_level: Optional[float],
        previous_crop: Optional[str],
        grain_price: float,
        fert_cost: float,
        app_cost: float,
        base_revenue: float
    ) -> float:
        """Find rate where applying fertilizer breaks even vs. not applying"""
        for rate in range(5, 301, 5):
            yield_pred = self.calculate_yield_response(
                crop, nutrient, rate, soil_test_level, previous_crop
            )
            cost = (rate * fert_cost) + app_cost
            revenue = yield_pred * grain_price

            if revenue - cost < base_revenue:
                return float(rate - 5)

        return 300.0  # Never breaks even in range

    def _calculate_sensitivity(
        self,
        crop: str,
        nutrient: str,
        soil_test_level: Optional[float],
        previous_crop: Optional[str],
        base_grain_price: float,
        base_fert_cost: float
    ) -> Dict[str, float]:
        """Calculate how EOR changes with price changes"""
        # +/- 20% grain price
        eor_base = self.calculate_economic_optimum(
            crop, nutrient, soil_test_level, previous_crop,
            base_grain_price, base_fert_cost
        ).optimum_rate

        eor_high_grain = self.calculate_economic_optimum(
            crop, nutrient, soil_test_level, previous_crop,
            base_grain_price * 1.2, base_fert_cost
        ).optimum_rate

        eor_low_grain = self.calculate_economic_optimum(
            crop, nutrient, soil_test_level, previous_crop,
            base_grain_price * 0.8, base_fert_cost
        ).optimum_rate

        # +/- 20% fertilizer price
        eor_high_fert = self.calculate_economic_optimum(
            crop, nutrient, soil_test_level, previous_crop,
            base_grain_price, base_fert_cost * 1.2
        ).optimum_rate

        eor_low_fert = self.calculate_economic_optimum(
            crop, nutrient, soil_test_level, previous_crop,
            base_grain_price, base_fert_cost * 0.8
        ).optimum_rate

        return {
            "grain_price_up_20pct": round(eor_high_grain - eor_base, 1),
            "grain_price_down_20pct": round(eor_low_grain - eor_base, 1),
            "fertilizer_price_up_20pct": round(eor_high_fert - eor_base, 1),
            "fertilizer_price_down_20pct": round(eor_low_fert - eor_base, 1)
        }

    def _generate_recommendation(
        self,
        eor: EconomicOptimum,
        crop: str,
        nutrient: str,
        soil_test_level: Optional[float]
    ) -> Dict[str, Any]:
        """Generate practical recommendations from EOR analysis"""
        recommendations = []

        # Main rate recommendation
        if eor.optimum_rate > 0:
            recommendations.append(
                f"Apply {eor.optimum_rate:.0f} lb/acre of {nutrient} for maximum profit"
            )
        else:
            recommendations.append(
                f"No {nutrient} application recommended - not economical at current prices"
            )

        # Compare to agronomic max
        rate_diff = eor.agronomic_max_rate - eor.optimum_rate
        if rate_diff > 10:
            recommendations.append(
                f"Economic optimum is {rate_diff:.0f} lb/acre LESS than agronomic max - "
                f"last {rate_diff:.0f} lb costs more than it returns"
            )

        # Yield comparison
        if eor.yield_at_optimum_vs_max < 98:
            yield_sacrifice = 100 - eor.yield_at_optimum_vs_max
            recommendations.append(
                f"You achieve {eor.yield_at_optimum_vs_max:.0f}% of maximum yield at EOR - "
                f"sacrificing {yield_sacrifice:.1f}% yield saves ${eor.agronomic_max_rate - eor.optimum_rate:.0f} × cost/lb"
            )

        # ROI
        if eor.return_per_dollar > 1:
            recommendations.append(
                f"Expected return: ${eor.return_per_dollar:.2f} for every $1 invested in {nutrient}"
            )

        # Soil test specific
        if soil_test_level is not None and nutrient.lower() in ["phosphorus", "potassium"]:
            params = YIELD_RESPONSE_PARAMS.get(crop.lower(), {}).get(nutrient.lower(), {})
            critical = params.get("critical_soil_test", 20)

            if soil_test_level > critical * 2:
                recommendations.append(
                    f"Soil test very high ({soil_test_level} ppm vs {critical} critical) - "
                    "consider maintenance only or skip application"
                )
            elif soil_test_level > critical:
                recommendations.append(
                    f"Soil test adequate ({soil_test_level} ppm) - "
                    "response to additional {nutrient} will be limited"
                )
            else:
                recommendations.append(
                    f"Soil test below critical ({soil_test_level} ppm vs {critical}) - "
                    "expect good response to {nutrient} application"
                )

        # Price sensitivity
        sensitivity = eor.sensitivity
        if abs(sensitivity.get("grain_price_up_20pct", 0)) > 15:
            recommendations.append(
                "Rate is price-sensitive: monitor commodity prices and adjust accordingly"
            )

        return {
            "summary": recommendations[0] if recommendations else "No recommendation",
            "details": recommendations,
            "confidence": "high" if eor.optimum_rate > 0 else "low",
            "data_quality_note": "Based on typical Midwest response curves. Local calibration improves accuracy."
        }

    def compare_rate_scenarios(
        self,
        crop: str,
        nutrient: str,
        rates: List[float],
        soil_test_level: Optional[float] = None,
        previous_crop: Optional[str] = None,
        commodity_price: Optional[float] = None,
        nutrient_cost: Optional[float] = None,
        application_cost: Optional[float] = None,
        acres: float = 1.0
    ) -> Dict[str, Any]:
        """
        Compare multiple rate scenarios side-by-side
        Useful for "what if" analysis
        """
        crop_lower = crop.lower()
        nutrient_lower = nutrient.lower()

        grain_price = commodity_price or self.commodity_prices.get(crop_lower, 5.0)
        fert_cost = nutrient_cost or self.input_costs.get(nutrient_lower, 0.50)
        app_cost = application_cost or self.input_costs.get("application", 8.0)

        scenarios = []

        for rate in rates:
            yield_pred = self.calculate_yield_response(
                crop, nutrient, rate, soil_test_level, previous_crop
            )

            input_cost = (rate * fert_cost) + (app_cost if rate > 0 else 0)
            total_cost = input_cost * acres

            gross_revenue = yield_pred * grain_price * acres
            net_return = gross_revenue - total_cost

            scenarios.append({
                "rate_lb_per_acre": rate,
                "predicted_yield_bu_acre": round(yield_pred, 1),
                "total_bushels": round(yield_pred * acres, 0),
                "input_cost_per_acre": round(input_cost, 2),
                "total_input_cost": round(total_cost, 2),
                "gross_revenue": round(gross_revenue, 2),
                "net_return": round(net_return, 2),
                "return_per_dollar": round(gross_revenue / total_cost, 2) if total_cost > 0 else 0
            })

        # Find best scenario
        best = max(scenarios, key=lambda x: x["net_return"])

        # Calculate EOR for comparison
        eor = self.calculate_economic_optimum(
            crop, nutrient, soil_test_level, previous_crop,
            grain_price, fert_cost, app_cost
        )

        return {
            "crop": crop,
            "nutrient": nutrient,
            "acres": acres,
            "prices": {
                "commodity_price": grain_price,
                "nutrient_cost": fert_cost,
                "application_cost": app_cost
            },
            "scenarios": scenarios,
            "best_scenario": best,
            "economic_optimum_rate": eor.optimum_rate,
            "recommendation": (
                f"Best of tested rates: {best['rate_lb_per_acre']} lb/acre "
                f"(${best['net_return']:,.0f} net return). "
                f"Economic optimum is {eor.optimum_rate} lb/acre."
            )
        }

    def multi_nutrient_optimization(
        self,
        crop: str,
        acres: float,
        budget: Optional[float] = None,
        soil_test_p: Optional[float] = None,
        soil_test_k: Optional[float] = None,
        previous_crop: Optional[str] = None,
        commodity_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Optimize multiple nutrients together, optionally within a budget
        Returns prioritized recommendations
        """
        crop_lower = crop.lower()
        grain_price = commodity_price or self.commodity_prices.get(crop_lower, 5.0)

        # Calculate EOR for each nutrient
        nutrient_analysis = {}
        total_optimal_cost = 0

        nutrients_to_analyze = ["nitrogen", "phosphorus", "potassium", "sulfur"]

        for nutrient in nutrients_to_analyze:
            try:
                soil_test = None
                if nutrient == "phosphorus":
                    soil_test = soil_test_p
                elif nutrient == "potassium":
                    soil_test = soil_test_k

                eor = self.calculate_economic_optimum(
                    crop, nutrient, soil_test,
                    previous_crop if nutrient == "nitrogen" else None,
                    grain_price
                )

                nutrient_analysis[nutrient] = {
                    "optimum_rate": eor.optimum_rate,
                    "optimum_yield": eor.optimum_yield,
                    "input_cost": eor.total_input_cost,
                    "net_return": eor.net_return,
                    "return_per_dollar": eor.return_per_dollar,
                    "marginal_return_at_optimum": eor.return_per_dollar
                }

                total_optimal_cost += eor.total_input_cost * acres

            except ValueError:
                continue

        # If budget constraint, prioritize by return per dollar
        if budget is not None and total_optimal_cost > budget:
            # Rank by return per dollar
            ranked = sorted(
                nutrient_analysis.items(),
                key=lambda x: x[1]["return_per_dollar"],
                reverse=True
            )

            budget_allocation = {}
            remaining_budget = budget

            for nutrient, data in ranked:
                cost_at_optimum = data["input_cost"] * acres

                if remaining_budget >= cost_at_optimum:
                    # Full allocation
                    budget_allocation[nutrient] = {
                        "rate": data["optimum_rate"],
                        "cost": cost_at_optimum,
                        "status": "full_optimum"
                    }
                    remaining_budget -= cost_at_optimum
                elif remaining_budget > 0:
                    # Partial allocation - reduce rate proportionally
                    fraction = remaining_budget / cost_at_optimum
                    reduced_rate = data["optimum_rate"] * fraction
                    budget_allocation[nutrient] = {
                        "rate": round(reduced_rate, 0),
                        "cost": remaining_budget,
                        "status": "reduced"
                    }
                    remaining_budget = 0
                else:
                    budget_allocation[nutrient] = {
                        "rate": 0,
                        "cost": 0,
                        "status": "skipped"
                    }

            return {
                "crop": crop,
                "acres": acres,
                "budget": budget,
                "budget_constrained": True,
                "nutrient_analysis": nutrient_analysis,
                "budget_allocation": budget_allocation,
                "total_cost_at_optimum": round(total_optimal_cost, 2),
                "recommendation": (
                    f"Budget limits prevent full optimization. "
                    f"Prioritizing nutrients by return: "
                    f"{', '.join(n for n, d in ranked[:2])}"
                )
            }

        return {
            "crop": crop,
            "acres": acres,
            "budget": budget,
            "budget_constrained": False,
            "nutrient_analysis": nutrient_analysis,
            "total_cost_at_optimum": round(total_optimal_cost, 2),
            "total_cost_per_acre": round(total_optimal_cost / acres, 2) if acres > 0 else 0,
            "recommendation": (
                f"Apply all nutrients at economic optimum. "
                f"Total fertilizer investment: ${total_optimal_cost:,.0f} "
                f"(${total_optimal_cost/acres:.0f}/acre)"
            )
        }


# Singleton instance
_yield_optimizer = None


def get_yield_response_optimizer(
    custom_input_costs: Optional[Dict[str, float]] = None,
    custom_commodity_prices: Optional[Dict[str, float]] = None
) -> YieldResponseOptimizer:
    """Get or create yield response optimizer instance"""
    global _yield_optimizer
    if _yield_optimizer is None or custom_input_costs or custom_commodity_prices:
        _yield_optimizer = YieldResponseOptimizer(
            custom_input_costs,
            custom_commodity_prices
        )
    return _yield_optimizer


# Example usage
if __name__ == "__main__":
    optimizer = YieldResponseOptimizer()

    print("=== YIELD RESPONSE OPTIMIZER DEMO ===\n")

    # Generate nitrogen response curve for corn
    print("--- Corn Nitrogen Response Curve ---")
    curve = optimizer.generate_response_curve(
        crop="corn",
        nutrient="nitrogen",
        rate_range=(0, 250),
        rate_step=25,
        previous_crop="soybean",
        commodity_price=4.50,
        nutrient_cost=0.50
    )

    print(f"Economic Optimum Rate: {curve['economic_optimum']['optimum_rate']} lb N/acre")
    print(f"Agronomic Max Rate: {curve['economic_optimum']['agronomic_max_rate']} lb N/acre")
    print(f"Yield at EOR: {curve['economic_optimum']['optimum_yield']} bu/acre")
    print(f"Net Return at EOR: ${curve['economic_optimum']['net_return']}/acre")
    print(f"\nRecommendation: {curve['recommendation']['summary']}")

    # Compare scenarios
    print("\n--- Rate Scenario Comparison ---")
    comparison = optimizer.compare_rate_scenarios(
        crop="corn",
        nutrient="nitrogen",
        rates=[120, 150, 180, 200],
        previous_crop="soybean",
        acres=500
    )

    print(f"\n{comparison['recommendation']}")
    print("\nScenario Details:")
    for s in comparison["scenarios"]:
        print(f"  {s['rate_lb_per_acre']} lb/acre: "
              f"{s['predicted_yield_bu_acre']} bu/acre, "
              f"${s['net_return']:,.0f} net return")

    # Multi-nutrient with budget
    print("\n--- Multi-Nutrient Optimization (Budget Constrained) ---")
    multi = optimizer.multi_nutrient_optimization(
        crop="corn",
        acres=500,
        budget=50000,
        soil_test_p=18,
        soil_test_k=140,
        previous_crop="soybean"
    )

    print(f"Total optimal cost: ${multi['total_cost_at_optimum']:,.0f}")
    print(f"Budget: ${multi['budget']:,.0f}")
    print(f"Constrained: {multi['budget_constrained']}")
    print(f"\n{multi['recommendation']}")
