"""
Offline Yield Response Calculator

Local implementation of yield response curves and Economic Optimum Rate (EOR)
calculations for use when the API server is unavailable.
"""

import math
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ResponseModel(Enum):
    """Yield response curve models."""
    QUADRATIC_PLATEAU = "quadratic_plateau"
    QUADRATIC = "quadratic"
    LINEAR_PLATEAU = "linear_plateau"
    MITSCHERLICH = "mitscherlich"
    SQUARE_ROOT = "square_root"


class SoilTestLevel(Enum):
    """Soil test levels for nutrient availability."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# Default crop parameters (cached locally during sync)
DEFAULT_CROP_PARAMETERS = {
    "corn": {
        "N": {
            "base_rate": 180,
            "max_yield": 220,
            "yield_potential_factor": 1.1,
            "response_model": "quadratic_plateau",
            "b0": 80,  # Intercept yield (bu/acre)
            "b1": 1.2,  # Linear coefficient
            "b2": -0.003,  # Quadratic coefficient
            "plateau_yield": 200,
            "plateau_rate": 170
        },
        "P": {
            "base_rate": 60,
            "response_factor": 0.8,
            "soil_test_adjustments": {
                "very_low": 1.5,
                "low": 1.25,
                "medium": 1.0,
                "high": 0.5,
                "very_high": 0.0
            }
        },
        "K": {
            "base_rate": 80,
            "response_factor": 0.6,
            "soil_test_adjustments": {
                "very_low": 1.5,
                "low": 1.25,
                "medium": 1.0,
                "high": 0.5,
                "very_high": 0.0
            }
        },
        "S": {
            "base_rate": 20,
            "response_factor": 0.4
        }
    },
    "soybean": {
        "N": {
            "base_rate": 0,  # Soybeans fix N
            "max_yield": 70,
            "notes": "Soybeans fix nitrogen - no N fertilizer needed"
        },
        "P": {
            "base_rate": 40,
            "response_factor": 0.9,
            "soil_test_adjustments": {
                "very_low": 1.5,
                "low": 1.25,
                "medium": 1.0,
                "high": 0.5,
                "very_high": 0.0
            }
        },
        "K": {
            "base_rate": 100,
            "response_factor": 0.8,
            "soil_test_adjustments": {
                "very_low": 1.5,
                "low": 1.25,
                "medium": 1.0,
                "high": 0.5,
                "very_high": 0.0
            }
        }
    },
    "wheat": {
        "N": {
            "base_rate": 120,
            "max_yield": 80,
            "yield_potential_factor": 1.0,
            "response_model": "quadratic_plateau",
            "b0": 35,
            "b1": 0.8,
            "b2": -0.0025,
            "plateau_yield": 75,
            "plateau_rate": 140
        },
        "P": {
            "base_rate": 35,
            "response_factor": 0.7,
            "soil_test_adjustments": {
                "very_low": 1.5,
                "low": 1.25,
                "medium": 1.0,
                "high": 0.5,
                "very_high": 0.0
            }
        },
        "K": {
            "base_rate": 50,
            "response_factor": 0.5,
            "soil_test_adjustments": {
                "very_low": 1.5,
                "low": 1.25,
                "medium": 1.0,
                "high": 0.5,
                "very_high": 0.0
            }
        }
    }
}

# Previous crop N credits (lb N/acre)
PREVIOUS_CROP_N_CREDITS = {
    "soybean": 40,
    "alfalfa": 80,
    "clover": 60,
    "peas": 30,
    "fallow": 20,
    "corn": 0,
    "wheat": 0,
    "other": 0
}


@dataclass
class YieldPoint:
    """A point on the yield response curve."""
    rate: float
    yield_value: float
    gross_revenue: float = 0.0
    fertilizer_cost: float = 0.0
    net_return: float = 0.0


@dataclass
class EORResult:
    """Economic Optimum Rate calculation result."""
    eor: float
    yield_at_eor: float
    max_yield: float
    max_yield_rate: float
    yield_sacrifice: float
    net_return_at_eor: float
    fertilizer_cost_at_eor: float
    gross_revenue_at_eor: float
    savings_vs_max: float
    price_ratio: float
    recommendation: str


@dataclass
class YieldCurveResult:
    """Yield response curve result."""
    curve_points: List[YieldPoint]
    eor: float
    max_yield_rate: float
    model_used: str
    crop: str
    nutrient: str


class OfflineYieldCalculator:
    """
    Offline calculator for yield response curves and EOR.

    Implements the same calculations as the backend service,
    allowing full functionality when disconnected from the server.
    """

    def __init__(self, crop_parameters: Optional[Dict] = None):
        """
        Initialize the calculator.

        Args:
            crop_parameters: Optional custom parameters (from local DB cache)
        """
        self._params = crop_parameters or DEFAULT_CROP_PARAMETERS

    def get_crop_parameters(self, crop: str) -> Optional[Dict]:
        """Get parameters for a crop."""
        return self._params.get(crop.lower())

    def calculate_yield(self, rate: float, crop: str, nutrient: str,
                        model: ResponseModel = ResponseModel.QUADRATIC_PLATEAU,
                        yield_potential: float = 200) -> float:
        """
        Calculate expected yield at a given fertilizer rate.

        Args:
            rate: Fertilizer application rate (lb/acre)
            crop: Crop type
            nutrient: Nutrient (N, P, K, S)
            model: Yield response model to use
            yield_potential: Target yield potential (bu/acre)

        Returns:
            Expected yield (bu/acre)
        """
        params = self._params.get(crop.lower(), {}).get(nutrient.upper(), {})

        if not params:
            return 0.0

        # Get model parameters with defaults
        b0 = params.get('b0', 80)
        b1 = params.get('b1', 1.0)
        b2 = params.get('b2', -0.003)
        plateau_yield = params.get('plateau_yield', yield_potential * 0.95)
        plateau_rate = params.get('plateau_rate', 170)

        # Scale to yield potential
        scale_factor = yield_potential / params.get('max_yield', 200)

        if model == ResponseModel.QUADRATIC_PLATEAU:
            # Quadratic up to plateau, then flat
            quad_yield = b0 + b1 * rate + b2 * rate * rate
            yield_value = min(quad_yield, plateau_yield) * scale_factor

        elif model == ResponseModel.QUADRATIC:
            # Pure quadratic (no plateau)
            yield_value = (b0 + b1 * rate + b2 * rate * rate) * scale_factor

        elif model == ResponseModel.LINEAR_PLATEAU:
            # Linear up to plateau
            if rate < plateau_rate:
                yield_value = (b0 + (plateau_yield - b0) * rate / plateau_rate) * scale_factor
            else:
                yield_value = plateau_yield * scale_factor

        elif model == ResponseModel.MITSCHERLICH:
            # Exponential approach to maximum
            a = plateau_yield
            c = 0.02  # Response coefficient
            yield_value = a * (1 - math.exp(-c * rate)) * scale_factor

        elif model == ResponseModel.SQUARE_ROOT:
            # Square root model
            yield_value = (b0 + b1 * math.sqrt(rate) + b2 * rate) * scale_factor

        else:
            yield_value = b0 * scale_factor

        return max(0, yield_value)

    def calculate_eor(self, crop: str, nutrient: str,
                      nutrient_cost: float, grain_price: float,
                      yield_potential: float = 200,
                      soil_test_level: SoilTestLevel = SoilTestLevel.MEDIUM,
                      previous_crop: str = "corn",
                      model: ResponseModel = ResponseModel.QUADRATIC_PLATEAU) -> EORResult:
        """
        Calculate the Economic Optimum Rate (EOR).

        EOR is the rate where marginal cost equals marginal revenue,
        maximizing profit rather than yield.

        Args:
            crop: Crop type
            nutrient: Nutrient (N, P, K, S)
            nutrient_cost: Cost per lb of nutrient ($/lb)
            grain_price: Grain price ($/bu)
            yield_potential: Target yield (bu/acre)
            soil_test_level: Soil test level
            previous_crop: Previous crop for N credits
            model: Yield response model

        Returns:
            EORResult with calculated values
        """
        params = self._params.get(crop.lower(), {}).get(nutrient.upper(), {})

        if not params:
            return EORResult(
                eor=0, yield_at_eor=0, max_yield=0, max_yield_rate=0,
                yield_sacrifice=0, net_return_at_eor=0, fertilizer_cost_at_eor=0,
                gross_revenue_at_eor=0, savings_vs_max=0, price_ratio=0,
                recommendation="Insufficient data for calculation"
            )

        # Price ratio (lb nutrient per bu grain)
        price_ratio = nutrient_cost / grain_price if grain_price > 0 else 0

        # Get model parameters
        b1 = params.get('b1', 1.0)
        b2 = params.get('b2', -0.003)
        plateau_rate = params.get('plateau_rate', 170)
        max_yield = params.get('max_yield', 200)

        # Scale to yield potential
        scale_factor = yield_potential / max_yield

        # Apply soil test adjustment
        soil_adj = params.get('soil_test_adjustments', {}).get(soil_test_level.value, 1.0)

        # Previous crop N credit
        n_credit = PREVIOUS_CROP_N_CREDITS.get(previous_crop.lower(), 0) if nutrient.upper() == 'N' else 0

        # Calculate EOR using marginal analysis
        # For quadratic: yield = b0 + b1*N + b2*N^2
        # Marginal yield = b1 + 2*b2*N
        # At EOR: marginal yield * grain_price = nutrient_cost
        # So: (b1 + 2*b2*N) * grain_price = nutrient_cost
        # Solving: N = (nutrient_cost/grain_price - b1) / (2*b2)

        if model in [ResponseModel.QUADRATIC, ResponseModel.QUADRATIC_PLATEAU]:
            if b2 != 0 and grain_price > 0:
                eor = (price_ratio / scale_factor - b1) / (2 * b2)
                eor = max(0, eor)

                # For quadratic plateau, cap at plateau rate
                if model == ResponseModel.QUADRATIC_PLATEAU:
                    eor = min(eor, plateau_rate)
            else:
                eor = params.get('base_rate', 150)
        else:
            # For other models, use numerical approximation
            eor = self._find_eor_numerically(
                crop, nutrient, nutrient_cost, grain_price,
                yield_potential, model
            )

        # Apply soil test adjustment and N credit
        eor = eor * soil_adj - n_credit
        eor = max(0, eor)

        # Calculate yields and economics
        yield_at_eor = self.calculate_yield(eor, crop, nutrient, model, yield_potential)

        # Find max yield rate (where marginal yield approaches 0)
        max_yield_rate = plateau_rate if model == ResponseModel.QUADRATIC_PLATEAU else -b1 / (2 * b2) if b2 != 0 else 200
        max_yield_rate = max_yield_rate * soil_adj - n_credit
        max_yield_rate = max(0, max_yield_rate)

        max_yield_value = self.calculate_yield(max_yield_rate, crop, nutrient, model, yield_potential)

        # Economics
        gross_revenue_at_eor = yield_at_eor * grain_price
        fertilizer_cost_at_eor = eor * nutrient_cost
        net_return_at_eor = gross_revenue_at_eor - fertilizer_cost_at_eor

        gross_revenue_at_max = max_yield_value * grain_price
        fertilizer_cost_at_max = max_yield_rate * nutrient_cost
        net_return_at_max = gross_revenue_at_max - fertilizer_cost_at_max

        yield_sacrifice = max_yield_value - yield_at_eor
        savings_vs_max = net_return_at_eor - net_return_at_max

        # Generate recommendation
        recommendation = self._generate_recommendation(
            eor, yield_at_eor, max_yield_value, max_yield_rate,
            savings_vs_max, nutrient, crop
        )

        return EORResult(
            eor=round(eor, 1),
            yield_at_eor=round(yield_at_eor, 1),
            max_yield=round(max_yield_value, 1),
            max_yield_rate=round(max_yield_rate, 1),
            yield_sacrifice=round(yield_sacrifice, 1),
            net_return_at_eor=round(net_return_at_eor, 2),
            fertilizer_cost_at_eor=round(fertilizer_cost_at_eor, 2),
            gross_revenue_at_eor=round(gross_revenue_at_eor, 2),
            savings_vs_max=round(savings_vs_max, 2),
            price_ratio=round(price_ratio, 4),
            recommendation=recommendation
        )

    def _find_eor_numerically(self, crop: str, nutrient: str,
                              nutrient_cost: float, grain_price: float,
                              yield_potential: float,
                              model: ResponseModel) -> float:
        """Find EOR using numerical search."""
        best_rate = 0
        best_net_return = float('-inf')

        for rate in range(0, 301, 5):
            yield_value = self.calculate_yield(rate, crop, nutrient, model, yield_potential)
            gross_revenue = yield_value * grain_price
            fert_cost = rate * nutrient_cost
            net_return = gross_revenue - fert_cost

            if net_return > best_net_return:
                best_net_return = net_return
                best_rate = rate

        # Refine with smaller steps
        for rate in range(max(0, best_rate - 10), min(301, best_rate + 10)):
            yield_value = self.calculate_yield(rate, crop, nutrient, model, yield_potential)
            gross_revenue = yield_value * grain_price
            fert_cost = rate * nutrient_cost
            net_return = gross_revenue - fert_cost

            if net_return > best_net_return:
                best_net_return = net_return
                best_rate = rate

        return float(best_rate)

    def _generate_recommendation(self, eor: float, yield_at_eor: float,
                                 max_yield: float, max_rate: float,
                                 savings: float, nutrient: str, crop: str) -> str:
        """Generate a human-readable recommendation."""
        parts = []

        if savings > 0:
            parts.append(
                f"Apply {eor:.0f} lb/acre of {nutrient} for {crop}. "
                f"This Economic Optimum Rate produces {yield_at_eor:.0f} bu/acre "
                f"with ${savings:.2f}/acre higher profit than the maximum yield rate."
            )
        else:
            parts.append(
                f"Apply {eor:.0f} lb/acre of {nutrient} for {crop}. "
                f"Expected yield: {yield_at_eor:.0f} bu/acre."
            )

        if yield_at_eor < max_yield:
            sacrifice_pct = (max_yield - yield_at_eor) / max_yield * 100
            if sacrifice_pct < 5:
                parts.append(f"You sacrifice only {sacrifice_pct:.1f}% yield for better economics.")
            else:
                parts.append(f"Yield sacrifice: {sacrifice_pct:.1f}%.")

        return " ".join(parts)

    def generate_yield_curve(self, crop: str, nutrient: str,
                             nutrient_cost: float, grain_price: float,
                             yield_potential: float = 200,
                             model: ResponseModel = ResponseModel.QUADRATIC_PLATEAU,
                             min_rate: int = 0, max_rate: int = 300,
                             step: int = 10) -> YieldCurveResult:
        """
        Generate a complete yield response curve.

        Args:
            crop: Crop type
            nutrient: Nutrient
            nutrient_cost: Cost per lb nutrient
            grain_price: Grain price per bu
            yield_potential: Target yield
            model: Response model
            min_rate: Minimum rate to calculate
            max_rate: Maximum rate to calculate
            step: Rate increment

        Returns:
            YieldCurveResult with curve points and key values
        """
        points = []

        for rate in range(min_rate, max_rate + 1, step):
            yield_value = self.calculate_yield(rate, crop, nutrient, model, yield_potential)
            gross_revenue = yield_value * grain_price
            fert_cost = rate * nutrient_cost
            net_return = gross_revenue - fert_cost

            points.append(YieldPoint(
                rate=rate,
                yield_value=round(yield_value, 1),
                gross_revenue=round(gross_revenue, 2),
                fertilizer_cost=round(fert_cost, 2),
                net_return=round(net_return, 2)
            ))

        # Find EOR and max yield points
        eor_result = self.calculate_eor(
            crop, nutrient, nutrient_cost, grain_price,
            yield_potential, SoilTestLevel.MEDIUM, "corn", model
        )

        return YieldCurveResult(
            curve_points=points,
            eor=eor_result.eor,
            max_yield_rate=eor_result.max_yield_rate,
            model_used=model.value,
            crop=crop,
            nutrient=nutrient
        )

    def compare_rates(self, rates: List[float], crop: str, nutrient: str,
                      nutrient_cost: float, grain_price: float,
                      yield_potential: float = 200,
                      model: ResponseModel = ResponseModel.QUADRATIC_PLATEAU) -> List[YieldPoint]:
        """
        Compare economics of different application rates.

        Args:
            rates: List of rates to compare
            crop: Crop type
            nutrient: Nutrient
            nutrient_cost: Cost per lb
            grain_price: Price per bu
            yield_potential: Target yield
            model: Response model

        Returns:
            List of YieldPoints for each rate, sorted by net return (best first)
        """
        results = []

        for rate in rates:
            yield_value = self.calculate_yield(rate, crop, nutrient, model, yield_potential)
            gross_revenue = yield_value * grain_price
            fert_cost = rate * nutrient_cost
            net_return = gross_revenue - fert_cost

            results.append(YieldPoint(
                rate=rate,
                yield_value=round(yield_value, 1),
                gross_revenue=round(gross_revenue, 2),
                fertilizer_cost=round(fert_cost, 2),
                net_return=round(net_return, 2)
            ))

        # Sort by net return descending
        results.sort(key=lambda x: x.net_return, reverse=True)

        return results

    def generate_price_ratio_guide(self, crop: str, nutrient: str,
                                   yield_potential: float = 200) -> List[Dict]:
        """
        Generate a price ratio lookup table for field reference.

        Shows optimal N rates for different price ratios.

        Returns:
            List of dicts with price_ratio and optimal_rate
        """
        results = []

        # Common price ratios
        price_ratios = [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30]

        for ratio in price_ratios:
            # Assume $5/bu grain price, calculate nutrient cost
            grain_price = 5.0
            nutrient_cost = ratio * grain_price

            eor = self.calculate_eor(
                crop, nutrient, nutrient_cost, grain_price, yield_potential
            )

            results.append({
                "price_ratio": ratio,
                "optimal_rate": eor.eor,
                "expected_yield": eor.yield_at_eor,
                "example_prices": f"${nutrient_cost:.2f}/lb N at ${grain_price}/bu"
            })

        return results


# Singleton instance
_offline_calculator: Optional[OfflineYieldCalculator] = None


def get_offline_yield_calculator(crop_params: Optional[Dict] = None) -> OfflineYieldCalculator:
    """Get the offline yield calculator instance."""
    global _offline_calculator
    if _offline_calculator is None or crop_params is not None:
        _offline_calculator = OfflineYieldCalculator(crop_params)
    return _offline_calculator
