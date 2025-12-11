"""
Offline Spray Timing Calculator

Local implementation of spray timing evaluation for use when
the API server is unavailable.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class RiskLevel(Enum):
    """Spray risk level categories."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DO_NOT_SPRAY = "do_not_spray"


class SprayType(Enum):
    """Types of spray applications."""
    HERBICIDE = "herbicide"
    INSECTICIDE = "insecticide"
    FUNGICIDE = "fungicide"
    GROWTH_REGULATOR = "growth_regulator"
    DESICCANT = "desiccant"


@dataclass
class WeatherCondition:
    """Current weather conditions for spray evaluation."""
    temperature_f: float = 75.0
    wind_speed_mph: float = 5.0
    wind_direction: str = "N"
    humidity_pct: float = 60.0
    rain_chance_pct: float = 10.0
    dew_point_f: float = 55.0
    cloud_cover_pct: float = 30.0


@dataclass
class ConditionAssessment:
    """Assessment of a single weather factor."""
    factor: str
    value: str
    status: str  # "suitable", "marginal", "unsuitable"
    message: str
    score: int  # 0-100


@dataclass
class SprayEvaluation:
    """Complete spray timing evaluation result."""
    risk_level: RiskLevel
    overall_score: int  # 0-100
    delta_t: float
    conditions: List[ConditionAssessment]
    concerns: List[str]
    recommendations: List[str]
    spray_type: SprayType
    is_suitable: bool


# Thresholds for spray conditions
SPRAY_THRESHOLDS = {
    "wind": {
        "excellent": (2, 6),
        "good": (1, 10),
        "marginal": (0, 15),
        "unsuitable": 15  # Above this
    },
    "temperature": {
        "excellent": (50, 85),
        "good": (40, 90),
        "marginal": (35, 95),
        "unsuitable_low": 35,
        "unsuitable_high": 95
    },
    "humidity": {
        "excellent": (40, 80),
        "good": (30, 85),
        "marginal": (20, 95),
        "too_low": 20,
        "too_high": 95
    },
    "delta_t": {
        "ideal": (2, 8),
        "acceptable": (1, 10),
        "marginal": (0, 14),
        "inversion_risk": 2  # Below this
    },
    "rain_chance": {
        "excellent": 10,
        "good": 20,
        "marginal": 40,
        "unsuitable": 60
    }
}

# Rainfastness requirements by product type (hours needed without rain)
RAINFASTNESS_HOURS = {
    SprayType.HERBICIDE: 4,
    SprayType.INSECTICIDE: 2,
    SprayType.FUNGICIDE: 2,
    SprayType.GROWTH_REGULATOR: 4,
    SprayType.DESICCANT: 6
}


class OfflineSprayCalculator:
    """
    Offline calculator for spray timing evaluation.

    Evaluates weather conditions against agronomic thresholds
    to determine spray application suitability.
    """

    def calculate_delta_t(self, temp_f: float, humidity_pct: float,
                          dew_point_f: float) -> float:
        """
        Calculate Delta T (temperature inversion indicator).

        Delta T = Dry bulb temperature - Wet bulb temperature
        Ideal range: 2-8°F

        Args:
            temp_f: Dry bulb temperature (°F)
            humidity_pct: Relative humidity (%)
            dew_point_f: Dew point temperature (°F)

        Returns:
            Delta T value
        """
        # Approximate wet bulb using simplified formula
        # More accurate would use psychrometric calculations
        rh = humidity_pct / 100.0

        # Simple wet bulb approximation
        wet_bulb = temp_f * (0.151977 * (rh + 8.313659) ** 0.5) + \
                   (temp_f - 14.381) ** 0.5 - 1.21 if rh > 0.01 else temp_f

        # Alternate simpler method for field use
        wet_bulb_simple = temp_f - ((100 - humidity_pct) / 5)

        delta_t = temp_f - wet_bulb_simple

        return round(delta_t, 1)

    def evaluate_conditions(self, weather: WeatherCondition,
                            spray_type: SprayType = SprayType.HERBICIDE,
                            product_name: str = None) -> SprayEvaluation:
        """
        Evaluate spray conditions and generate recommendations.

        Args:
            weather: Current weather conditions
            spray_type: Type of spray application
            product_name: Optional specific product name

        Returns:
            SprayEvaluation with risk level and recommendations
        """
        conditions = []
        concerns = []
        recommendations = []
        total_score = 0
        factor_count = 0

        # Calculate Delta T
        delta_t = self.calculate_delta_t(
            weather.temperature_f,
            weather.humidity_pct,
            weather.dew_point_f
        )

        # 1. Wind Assessment
        wind_assessment = self._assess_wind(weather.wind_speed_mph, spray_type)
        conditions.append(wind_assessment)
        total_score += wind_assessment.score
        factor_count += 1

        if wind_assessment.status == "unsuitable":
            concerns.append(f"Wind speed ({weather.wind_speed_mph} mph) too high - drift risk")
            recommendations.append("Wait for wind to decrease below 10 mph")
        elif wind_assessment.status == "marginal":
            concerns.append(f"Wind speed ({weather.wind_speed_mph} mph) marginal")
            recommendations.append("Use drift-reducing nozzles if spraying")

        # 2. Temperature Assessment
        temp_assessment = self._assess_temperature(weather.temperature_f, spray_type)
        conditions.append(temp_assessment)
        total_score += temp_assessment.score
        factor_count += 1

        if temp_assessment.status == "unsuitable":
            if weather.temperature_f < 40:
                concerns.append(f"Temperature ({weather.temperature_f}°F) too cold")
                recommendations.append("Wait for warmer conditions (above 50°F)")
            else:
                concerns.append(f"Temperature ({weather.temperature_f}°F) too hot")
                recommendations.append("Spray early morning or evening when cooler")
        elif temp_assessment.status == "marginal":
            recommendations.append("Monitor for temperature extremes")

        # 3. Humidity Assessment
        humidity_assessment = self._assess_humidity(weather.humidity_pct, spray_type)
        conditions.append(humidity_assessment)
        total_score += humidity_assessment.score
        factor_count += 1

        if humidity_assessment.status == "unsuitable":
            if weather.humidity_pct < 30:
                concerns.append(f"Humidity ({weather.humidity_pct}%) too low - evaporation risk")
                recommendations.append("Spray during higher humidity periods")
            else:
                concerns.append(f"Humidity ({weather.humidity_pct}%) very high")

        # 4. Delta T Assessment
        delta_assessment = self._assess_delta_t(delta_t)
        conditions.append(delta_assessment)
        total_score += delta_assessment.score
        factor_count += 1

        if delta_t < 2:
            concerns.append(f"Delta T ({delta_t}°F) indicates inversion risk")
            recommendations.append("Temperature inversion possible - delay spraying")
        elif delta_t > 10:
            concerns.append(f"Delta T ({delta_t}°F) high - evaporation risk")
            recommendations.append("Use larger droplet size to reduce evaporation")

        # 5. Rain Chance Assessment
        rain_assessment = self._assess_rain(weather.rain_chance_pct, spray_type)
        conditions.append(rain_assessment)
        total_score += rain_assessment.score
        factor_count += 1

        rainfastness = RAINFASTNESS_HOURS.get(spray_type, 4)
        if weather.rain_chance_pct > 40:
            concerns.append(f"Rain chance ({weather.rain_chance_pct}%) high")
            recommendations.append(f"Product needs {rainfastness} hours without rain")

        # Calculate overall score
        overall_score = total_score // factor_count if factor_count > 0 else 50

        # Determine risk level
        risk_level = self._determine_risk_level(overall_score, conditions)

        # Is it suitable to spray?
        is_suitable = risk_level in [RiskLevel.EXCELLENT, RiskLevel.GOOD, RiskLevel.FAIR]

        # Add general recommendations
        if risk_level == RiskLevel.EXCELLENT:
            recommendations.insert(0, "Conditions are excellent for spraying")
        elif risk_level == RiskLevel.GOOD:
            recommendations.insert(0, "Conditions are good for spraying")
        elif risk_level == RiskLevel.FAIR:
            recommendations.insert(0, "Conditions acceptable but not ideal")
        elif risk_level == RiskLevel.POOR:
            recommendations.insert(0, "Poor conditions - consider waiting")
        else:
            recommendations.insert(0, "DO NOT SPRAY - conditions unsuitable")

        return SprayEvaluation(
            risk_level=risk_level,
            overall_score=overall_score,
            delta_t=delta_t,
            conditions=conditions,
            concerns=concerns,
            recommendations=recommendations,
            spray_type=spray_type,
            is_suitable=is_suitable
        )

    def _assess_wind(self, wind_mph: float, spray_type: SprayType) -> ConditionAssessment:
        """Assess wind conditions."""
        thresholds = SPRAY_THRESHOLDS["wind"]

        if thresholds["excellent"][0] <= wind_mph <= thresholds["excellent"][1]:
            status = "suitable"
            score = 95
            message = "Ideal wind speed"
        elif thresholds["good"][0] <= wind_mph <= thresholds["good"][1]:
            status = "suitable"
            score = 80
            message = "Good wind conditions"
        elif wind_mph <= thresholds["marginal"][1]:
            status = "marginal"
            score = 55
            message = "Wind marginal - watch for changes"
        else:
            status = "unsuitable"
            score = 20
            message = "Wind too high - drift risk severe"

        # Calm conditions also problematic (inversion)
        if wind_mph < 2:
            status = "marginal"
            score = 60
            message = "Very calm - possible inversion conditions"

        return ConditionAssessment(
            factor="Wind Speed",
            value=f"{wind_mph} mph",
            status=status,
            message=message,
            score=score
        )

    def _assess_temperature(self, temp_f: float, spray_type: SprayType) -> ConditionAssessment:
        """Assess temperature conditions."""
        thresholds = SPRAY_THRESHOLDS["temperature"]

        if thresholds["excellent"][0] <= temp_f <= thresholds["excellent"][1]:
            status = "suitable"
            score = 95
            message = "Ideal temperature range"
        elif thresholds["good"][0] <= temp_f <= thresholds["good"][1]:
            status = "suitable"
            score = 80
            message = "Good temperature"
        elif thresholds["marginal"][0] <= temp_f <= thresholds["marginal"][1]:
            status = "marginal"
            score = 55
            message = "Temperature marginal"
        else:
            status = "unsuitable"
            score = 15
            if temp_f < thresholds["unsuitable_low"]:
                message = "Too cold for effective application"
            else:
                message = "Too hot - volatilization and plant stress risk"

        return ConditionAssessment(
            factor="Temperature",
            value=f"{temp_f}°F",
            status=status,
            message=message,
            score=score
        )

    def _assess_humidity(self, humidity_pct: float, spray_type: SprayType) -> ConditionAssessment:
        """Assess humidity conditions."""
        thresholds = SPRAY_THRESHOLDS["humidity"]

        if thresholds["excellent"][0] <= humidity_pct <= thresholds["excellent"][1]:
            status = "suitable"
            score = 95
            message = "Ideal humidity"
        elif thresholds["good"][0] <= humidity_pct <= thresholds["good"][1]:
            status = "suitable"
            score = 80
            message = "Good humidity level"
        elif thresholds["marginal"][0] <= humidity_pct <= thresholds["marginal"][1]:
            status = "marginal"
            score = 55
            message = "Humidity marginal"
        else:
            status = "unsuitable"
            score = 20
            if humidity_pct < thresholds["too_low"]:
                message = "Too dry - rapid evaporation risk"
            else:
                message = "Very humid - slow drying"

        return ConditionAssessment(
            factor="Humidity",
            value=f"{humidity_pct}%",
            status=status,
            message=message,
            score=score
        )

    def _assess_delta_t(self, delta_t: float) -> ConditionAssessment:
        """Assess Delta T (inversion risk indicator)."""
        thresholds = SPRAY_THRESHOLDS["delta_t"]

        if thresholds["ideal"][0] <= delta_t <= thresholds["ideal"][1]:
            status = "suitable"
            score = 95
            message = "Ideal Delta T - good spray conditions"
        elif thresholds["acceptable"][0] <= delta_t <= thresholds["acceptable"][1]:
            status = "suitable"
            score = 75
            message = "Acceptable Delta T"
        elif thresholds["marginal"][0] <= delta_t <= thresholds["marginal"][1]:
            status = "marginal"
            score = 50
            message = "Delta T marginal"
        elif delta_t < thresholds["inversion_risk"]:
            status = "unsuitable"
            score = 15
            message = "Inversion conditions likely - high drift risk"
        else:
            status = "unsuitable"
            score = 25
            message = "Delta T very high - evaporation risk"

        return ConditionAssessment(
            factor="Delta T",
            value=f"{delta_t}°F",
            status=status,
            message=message,
            score=score
        )

    def _assess_rain(self, rain_chance: float, spray_type: SprayType) -> ConditionAssessment:
        """Assess rain probability."""
        thresholds = SPRAY_THRESHOLDS["rain_chance"]
        rainfastness = RAINFASTNESS_HOURS.get(spray_type, 4)

        if rain_chance <= thresholds["excellent"]:
            status = "suitable"
            score = 95
            message = "Low rain probability"
        elif rain_chance <= thresholds["good"]:
            status = "suitable"
            score = 80
            message = "Rain chance acceptable"
        elif rain_chance <= thresholds["marginal"]:
            status = "marginal"
            score = 50
            message = f"Monitor rain - need {rainfastness}hr rainfast"
        else:
            status = "unsuitable"
            score = 20
            message = "High rain probability - product may wash off"

        return ConditionAssessment(
            factor="Rain Chance",
            value=f"{rain_chance}%",
            status=status,
            message=message,
            score=score
        )

    def _determine_risk_level(self, overall_score: int,
                              conditions: List[ConditionAssessment]) -> RiskLevel:
        """Determine overall risk level from score and conditions."""
        # Check for any unsuitable conditions (critical factors)
        unsuitable_count = sum(1 for c in conditions if c.status == "unsuitable")
        marginal_count = sum(1 for c in conditions if c.status == "marginal")

        if unsuitable_count >= 2:
            return RiskLevel.DO_NOT_SPRAY
        elif unsuitable_count == 1:
            return RiskLevel.POOR

        if overall_score >= 85:
            return RiskLevel.EXCELLENT
        elif overall_score >= 70:
            return RiskLevel.GOOD
        elif overall_score >= 55:
            return RiskLevel.FAIR
        elif overall_score >= 40:
            return RiskLevel.POOR
        else:
            return RiskLevel.DO_NOT_SPRAY

    def calculate_cost_of_waiting(self, crop: str, acres: float,
                                  yield_goal: float, grain_price: float,
                                  days_to_wait: int = 1,
                                  pest_pressure: str = "moderate") -> Dict:
        """
        Calculate economic impact of delaying spray application.

        Args:
            crop: Crop type
            acres: Field size in acres
            yield_goal: Target yield (bu/acre)
            grain_price: Current grain price ($/bu)
            days_to_wait: Number of days delay
            pest_pressure: Pest pressure level (low, moderate, high)

        Returns:
            Dict with cost analysis
        """
        # Yield loss estimates per day of delay (% per day)
        yield_loss_rates = {
            "low": 0.5,
            "moderate": 1.5,
            "high": 3.0
        }

        daily_loss_pct = yield_loss_rates.get(pest_pressure.lower(), 1.5)
        total_loss_pct = min(daily_loss_pct * days_to_wait, 25)  # Cap at 25%

        yield_loss_bu = yield_goal * (total_loss_pct / 100)
        revenue_loss_per_acre = yield_loss_bu * grain_price
        total_revenue_loss = revenue_loss_per_acre * acres

        # Recommendation
        if total_loss_pct < 2:
            recommendation = "WAIT"
            reason = "Yield loss minimal - wait for better conditions"
        elif total_loss_pct < 5:
            recommendation = "EVALUATE"
            reason = "Moderate yield risk - weigh conditions vs cost"
        else:
            recommendation = "SPRAY NOW"
            reason = "Significant yield at risk - spray as soon as safe"

        return {
            "recommendation": recommendation,
            "reason": reason,
            "yield_loss_pct": round(total_loss_pct, 1),
            "yield_loss_bu_per_acre": round(yield_loss_bu, 1),
            "revenue_loss_per_acre": round(revenue_loss_per_acre, 2),
            "total_revenue_loss": round(total_revenue_loss, 2),
            "days_delay": days_to_wait,
            "pest_pressure": pest_pressure
        }


# Singleton instance
_spray_calculator: Optional[OfflineSprayCalculator] = None


def get_offline_spray_calculator() -> OfflineSprayCalculator:
    """Get the offline spray calculator instance."""
    global _spray_calculator
    if _spray_calculator is None:
        _spray_calculator = OfflineSprayCalculator()
    return _spray_calculator
