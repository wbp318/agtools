"""
Weather-Smart Spray Timing Optimizer
Predicts optimal spray windows based on weather forecasts
Calculates cost-of-waiting and helps avoid wasted applications
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta, timezone


class SprayType(str, Enum):
    HERBICIDE = "herbicide"
    INSECTICIDE = "insecticide"
    FUNGICIDE = "fungicide"
    GROWTH_REGULATOR = "growth_regulator"
    DESICCANT = "desiccant"


class ApplicationRisk(str, Enum):
    EXCELLENT = "excellent"  # Ideal conditions
    GOOD = "good"           # Minor issues but acceptable
    MARGINAL = "marginal"   # Proceed with caution
    POOR = "poor"           # High risk of failure or drift
    DO_NOT_SPRAY = "do_not_spray"  # Conditions prohibit spraying


class WeatherFactor(str, Enum):
    WIND = "wind"
    RAIN = "rain"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    INVERSION = "inversion"
    LEAF_WETNESS = "leaf_wetness"


# Optimal spray conditions by product type
OPTIMAL_CONDITIONS = {
    SprayType.HERBICIDE: {
        "wind_min_mph": 3,
        "wind_max_mph": 10,
        "temp_min_f": 45,
        "temp_max_f": 85,
        "humidity_min_pct": 40,
        "humidity_max_pct": 95,
        "rain_free_hours_before": 1,
        "rain_free_hours_after": 4,  # Most herbicides need 4+ hours
        "avoid_inversion": True,
        "leaf_wetness_ok": False  # Dry leaves preferred
    },
    SprayType.INSECTICIDE: {
        "wind_min_mph": 2,
        "wind_max_mph": 10,
        "temp_min_f": 50,
        "temp_max_f": 90,
        "humidity_min_pct": 30,
        "humidity_max_pct": 90,
        "rain_free_hours_before": 1,
        "rain_free_hours_after": 2,  # Most insecticides dry faster
        "avoid_inversion": True,
        "leaf_wetness_ok": True  # Can spray with dew
    },
    SprayType.FUNGICIDE: {
        "wind_min_mph": 2,
        "wind_max_mph": 12,
        "temp_min_f": 50,
        "temp_max_f": 85,
        "humidity_min_pct": 50,  # Higher humidity helps uptake
        "humidity_max_pct": 95,
        "rain_free_hours_before": 0,  # Can spray after rain
        "rain_free_hours_after": 2,
        "avoid_inversion": False,  # Less drift sensitive
        "leaf_wetness_ok": True   # OK with morning dew
    },
    SprayType.GROWTH_REGULATOR: {
        "wind_min_mph": 3,
        "wind_max_mph": 8,
        "temp_min_f": 55,
        "temp_max_f": 80,
        "humidity_min_pct": 40,
        "humidity_max_pct": 85,
        "rain_free_hours_before": 2,
        "rain_free_hours_after": 6,
        "avoid_inversion": True,
        "leaf_wetness_ok": False
    },
    SprayType.DESICCANT: {
        "wind_min_mph": 3,
        "wind_max_mph": 15,  # More tolerant
        "temp_min_f": 60,
        "temp_max_f": 95,
        "humidity_min_pct": 20,
        "humidity_max_pct": 80,
        "rain_free_hours_before": 2,
        "rain_free_hours_after": 1,
        "avoid_inversion": True,
        "leaf_wetness_ok": False
    }
}

# Product-specific rain-free requirements (hours after application)
RAINFASTNESS_HOURS = {
    # Herbicides
    "glyphosate": 4,
    "dicamba": 4,
    "2,4-d": 6,
    "liberty": 4,
    "atrazine": 1,
    "metolachlor": 0,  # Activated by rain

    # Insecticides
    "bifenthrin": 2,
    "lambda_cyhalothrin": 1,
    "chlorantraniliprole": 2,
    "imidacloprid": 4,

    # Fungicides
    "azoxystrobin": 2,
    "propiconazole": 1,
    "pyraclostrobin": 1,
    "trifloxystrobin": 2,
    "fluxapyroxad": 1,

    # Default
    "default": 4
}

# Disease pressure factors by weather conditions
DISEASE_PRESSURE_FACTORS = {
    "gray_leaf_spot": {
        "humidity_threshold": 90,
        "temp_range": (70, 85),
        "leaf_wetness_hours": 11,
        "description": "High humidity + warm temps + extended leaf wetness"
    },
    "northern_corn_leaf_blight": {
        "humidity_threshold": 85,
        "temp_range": (65, 80),
        "leaf_wetness_hours": 6,
        "description": "Moderate temps + frequent dews/fogs"
    },
    "southern_rust": {
        "humidity_threshold": 80,
        "temp_range": (75, 90),
        "leaf_wetness_hours": 4,
        "description": "Hot + humid conditions"
    },
    "frogeye_leaf_spot": {
        "humidity_threshold": 85,
        "temp_range": (75, 90),
        "leaf_wetness_hours": 10,
        "description": "Warm humid weather in soybeans"
    },
    "sudden_death_syndrome": {
        "humidity_threshold": 70,
        "temp_range": (60, 75),
        "leaf_wetness_hours": 0,  # Soil moisture driven
        "description": "Cool wet soils early season"
    },
    "white_mold": {
        "humidity_threshold": 90,
        "temp_range": (60, 75),
        "leaf_wetness_hours": 12,
        "description": "Cool + wet during flowering"
    }
}

# Pest activity by temperature
PEST_ACTIVITY_TEMPS = {
    "corn_rootworm_adult": {"min": 65, "max": 90, "optimal": 78},
    "japanese_beetle": {"min": 70, "max": 95, "optimal": 85},
    "soybean_aphid": {"min": 50, "max": 85, "optimal": 72},
    "spider_mite": {"min": 75, "max": 100, "optimal": 90},  # Hot dry weather
    "corn_earworm": {"min": 65, "max": 90, "optimal": 80},
    "armyworm": {"min": 55, "max": 85, "optimal": 70},
    "stink_bug": {"min": 60, "max": 90, "optimal": 80}
}


@dataclass
class WeatherCondition:
    """Weather conditions at a specific time"""
    datetime: datetime
    temp_f: float
    humidity_pct: float
    wind_mph: float
    wind_direction: str
    precip_chance_pct: float
    precip_amount_in: float
    cloud_cover_pct: float
    dew_point_f: float

    @property
    def has_inversion_risk(self) -> bool:
        """Check if temperature inversion is likely (evening/night, calm winds, clear sky)"""
        hour = self.datetime.hour
        is_night_or_evening = hour < 8 or hour > 18
        calm_winds = self.wind_mph < 3
        clear_sky = self.cloud_cover_pct < 30
        return is_night_or_evening and calm_winds and clear_sky

    @property
    def leaf_wetness_likely(self) -> bool:
        """Estimate if leaves are wet (dew, recent rain, high humidity)"""
        hour = self.datetime.hour
        morning = 4 <= hour <= 9
        high_humidity = self.humidity_pct > 85
        recent_rain = self.precip_amount_in > 0
        temp_near_dew = abs(self.temp_f - self.dew_point_f) < 5
        return (morning and high_humidity) or recent_rain or temp_near_dew


@dataclass
class SprayWindow:
    """A window of time suitable for spraying"""
    start: datetime
    end: datetime
    quality: ApplicationRisk
    avg_conditions: Dict[str, float]
    limiting_factors: List[str]
    notes: List[str]

    @property
    def duration_hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600


class SprayTimingOptimizer:
    """
    Optimizes spray timing based on weather conditions

    Features:
    - Evaluate current conditions for spraying
    - Find optimal spray windows in forecast
    - Calculate cost of waiting vs. spraying now
    - Disease/pest pressure forecasting
    - Rain avoidance optimization
    - Product-specific recommendations
    """

    def __init__(self):
        self.optimal_conditions = OPTIMAL_CONDITIONS
        self.rainfastness = RAINFASTNESS_HOURS

    def evaluate_current_conditions(
        self,
        weather: WeatherCondition,
        spray_type: SprayType,
        product_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate if current conditions are suitable for spraying

        Args:
            weather: Current weather conditions
            spray_type: Type of application
            product_name: Specific product for rainfastness requirements
        """
        optimal = self.optimal_conditions.get(spray_type, OPTIMAL_CONDITIONS[SprayType.HERBICIDE])
        issues = []
        warnings = []
        score = 100  # Start at perfect, deduct for issues

        # Wind evaluation
        if weather.wind_mph < optimal["wind_min_mph"]:
            issues.append(f"Wind too calm ({weather.wind_mph:.1f} mph) - inversion risk")
            score -= 25
        elif weather.wind_mph > optimal["wind_max_mph"]:
            issues.append(f"Wind too high ({weather.wind_mph:.1f} mph) - drift risk")
            score -= 30 if weather.wind_mph > optimal["wind_max_mph"] + 5 else 15
        elif weather.wind_mph > optimal["wind_max_mph"] - 2:
            warnings.append(f"Wind approaching limit ({weather.wind_mph:.1f} mph)")

        # Temperature evaluation
        if weather.temp_f < optimal["temp_min_f"]:
            issues.append(f"Too cold ({weather.temp_f:.0f}°F) - reduced efficacy")
            score -= 20
        elif weather.temp_f > optimal["temp_max_f"]:
            issues.append(f"Too hot ({weather.temp_f:.0f}°F) - volatilization/stress risk")
            score -= 25
        elif weather.temp_f > optimal["temp_max_f"] - 5:
            warnings.append(f"Temperature high ({weather.temp_f:.0f}°F)")

        # Humidity evaluation
        if weather.humidity_pct < optimal["humidity_min_pct"]:
            issues.append(f"Humidity too low ({weather.humidity_pct:.0f}%) - increased drift")
            score -= 15
        elif weather.humidity_pct > optimal["humidity_max_pct"]:
            issues.append(f"Humidity too high ({weather.humidity_pct:.0f}%)")
            score -= 10

        # Rain risk
        if weather.precip_chance_pct > 50:
            rainfree_needed = self.rainfastness.get(
                product_name.lower() if product_name else "default",
                self.rainfastness["default"]
            )
            issues.append(f"Rain likely ({weather.precip_chance_pct:.0f}% chance) - need {rainfree_needed}hr rain-free")
            score -= 30
        elif weather.precip_chance_pct > 30:
            warnings.append(f"Rain possible ({weather.precip_chance_pct:.0f}% chance)")
            score -= 10

        # Inversion risk
        if optimal["avoid_inversion"] and weather.has_inversion_risk:
            issues.append("Temperature inversion likely - high drift potential")
            score -= 35

        # Leaf wetness
        if not optimal["leaf_wetness_ok"] and weather.leaf_wetness_likely:
            warnings.append("Leaf wetness detected - may reduce contact herbicide efficacy")
            score -= 5

        # Determine overall rating
        if score >= 90:
            risk_level = ApplicationRisk.EXCELLENT
        elif score >= 75:
            risk_level = ApplicationRisk.GOOD
        elif score >= 55:
            risk_level = ApplicationRisk.MARGINAL
        elif score >= 35:
            risk_level = ApplicationRisk.POOR
        else:
            risk_level = ApplicationRisk.DO_NOT_SPRAY

        return {
            "datetime": weather.datetime.isoformat(),
            "spray_type": spray_type.value,
            "product": product_name,
            "conditions": {
                "temperature_f": weather.temp_f,
                "humidity_pct": weather.humidity_pct,
                "wind_mph": weather.wind_mph,
                "wind_direction": weather.wind_direction,
                "precip_chance_pct": weather.precip_chance_pct,
                "inversion_risk": weather.has_inversion_risk,
                "leaf_wetness": weather.leaf_wetness_likely
            },
            "evaluation": {
                "risk_level": risk_level.value,
                "score": score,
                "issues": issues,
                "warnings": warnings
            },
            "recommendation": self._get_spray_recommendation(risk_level, issues)
        }

    def _get_spray_recommendation(
        self,
        risk_level: ApplicationRisk,
        issues: List[str]
    ) -> str:
        """Generate actionable recommendation based on conditions"""
        if risk_level == ApplicationRisk.EXCELLENT:
            return "Excellent conditions - proceed with application"
        elif risk_level == ApplicationRisk.GOOD:
            return "Good conditions - proceed with application, monitor for changes"
        elif risk_level == ApplicationRisk.MARGINAL:
            return f"Marginal conditions - consider waiting. Issues: {'; '.join(issues[:2])}"
        elif risk_level == ApplicationRisk.POOR:
            return f"Poor conditions - delay application if possible. Issues: {'; '.join(issues[:2])}"
        else:
            return f"DO NOT SPRAY - conditions prohibit safe/effective application. Issues: {'; '.join(issues)}"

    def find_spray_windows(
        self,
        forecast: List[WeatherCondition],
        spray_type: SprayType,
        min_window_hours: float = 3.0,
        product_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find optimal spray windows in a weather forecast

        Args:
            forecast: List of hourly weather conditions
            spray_type: Type of application
            min_window_hours: Minimum window duration to consider
            product_name: Specific product name
        """
        if not forecast:
            return {"error": "No forecast data provided"}

        windows: List[SprayWindow] = []
        current_window_start = None
        current_window_conditions = []
        current_window_issues = []

        for weather in forecast:
            eval_result = self.evaluate_current_conditions(weather, spray_type, product_name)
            risk_level = ApplicationRisk(eval_result["evaluation"]["risk_level"])

            is_sprayable = risk_level in [ApplicationRisk.EXCELLENT, ApplicationRisk.GOOD]

            if is_sprayable:
                if current_window_start is None:
                    current_window_start = weather.datetime
                    current_window_conditions = []
                    current_window_issues = []

                current_window_conditions.append({
                    "temp": weather.temp_f,
                    "humidity": weather.humidity_pct,
                    "wind": weather.wind_mph,
                    "rain_chance": weather.precip_chance_pct,
                    "quality": risk_level.value
                })
                current_window_issues.extend(eval_result["evaluation"]["warnings"])
            else:
                # End current window if one exists
                if current_window_start is not None:
                    window_duration = (weather.datetime - current_window_start).total_seconds() / 3600

                    if window_duration >= min_window_hours:
                        # Calculate average conditions
                        avg_conditions = {
                            "temp_f": sum(c["temp"] for c in current_window_conditions) / len(current_window_conditions),
                            "humidity_pct": sum(c["humidity"] for c in current_window_conditions) / len(current_window_conditions),
                            "wind_mph": sum(c["wind"] for c in current_window_conditions) / len(current_window_conditions),
                            "rain_chance_pct": sum(c["rain_chance"] for c in current_window_conditions) / len(current_window_conditions)
                        }

                        # Determine window quality
                        excellent_hours = sum(1 for c in current_window_conditions if c["quality"] == "excellent")
                        quality = ApplicationRisk.EXCELLENT if excellent_hours >= len(current_window_conditions) * 0.7 else ApplicationRisk.GOOD

                        windows.append(SprayWindow(
                            start=current_window_start,
                            end=weather.datetime,
                            quality=quality,
                            avg_conditions=avg_conditions,
                            limiting_factors=list(set(current_window_issues)),
                            notes=self._generate_window_notes(avg_conditions, spray_type)
                        ))

                current_window_start = None
                current_window_conditions = []
                current_window_issues = []

        # Close final window if still open
        if current_window_start is not None and forecast:
            window_duration = (forecast[-1].datetime - current_window_start).total_seconds() / 3600
            if window_duration >= min_window_hours:
                avg_conditions = {
                    "temp_f": sum(c["temp"] for c in current_window_conditions) / len(current_window_conditions),
                    "humidity_pct": sum(c["humidity"] for c in current_window_conditions) / len(current_window_conditions),
                    "wind_mph": sum(c["wind"] for c in current_window_conditions) / len(current_window_conditions),
                    "rain_chance_pct": sum(c["rain_chance"] for c in current_window_conditions) / len(current_window_conditions)
                }

                windows.append(SprayWindow(
                    start=current_window_start,
                    end=forecast[-1].datetime,
                    quality=ApplicationRisk.GOOD,
                    avg_conditions=avg_conditions,
                    limiting_factors=list(set(current_window_issues)),
                    notes=self._generate_window_notes(avg_conditions, spray_type)
                ))

        # Format response
        formatted_windows = []
        for w in windows:
            formatted_windows.append({
                "start": w.start.isoformat(),
                "end": w.end.isoformat(),
                "duration_hours": round(w.duration_hours, 1),
                "quality": w.quality.value,
                "avg_conditions": {k: round(v, 1) for k, v in w.avg_conditions.items()},
                "limiting_factors": w.limiting_factors,
                "notes": w.notes
            })

        # Find best window
        best_window = None
        if formatted_windows:
            excellent_windows = [w for w in formatted_windows if w["quality"] == "excellent"]
            if excellent_windows:
                best_window = max(excellent_windows, key=lambda x: x["duration_hours"])
            else:
                best_window = max(formatted_windows, key=lambda x: x["duration_hours"])

        return {
            "spray_type": spray_type.value,
            "product": product_name,
            "forecast_hours_analyzed": len(forecast),
            "min_window_required_hours": min_window_hours,
            "windows_found": len(formatted_windows),
            "windows": formatted_windows,
            "best_window": best_window,
            "recommendation": self._generate_overall_recommendation(formatted_windows, best_window)
        }

    def _generate_window_notes(
        self,
        avg_conditions: Dict[str, float],
        spray_type: SprayType
    ) -> List[str]:
        """Generate helpful notes for a spray window"""
        notes = []

        if avg_conditions.get("wind_mph", 0) < 5:
            notes.append("Light winds - good coverage potential")
        elif avg_conditions.get("wind_mph", 0) > 8:
            notes.append("Moderate winds - consider drift reduction tips")

        if avg_conditions.get("temp_f", 70) > 80:
            if spray_type == SprayType.HERBICIDE:
                notes.append("Warm conditions - consider adjuvant to reduce volatility")

        if avg_conditions.get("humidity_pct", 50) > 80:
            if spray_type == SprayType.FUNGICIDE:
                notes.append("High humidity - excellent fungicide uptake conditions")

        if avg_conditions.get("rain_chance_pct", 0) > 20:
            notes.append("Monitor radar closely for pop-up showers")

        return notes

    def _generate_overall_recommendation(
        self,
        windows: List[Dict],
        best_window: Optional[Dict]
    ) -> str:
        """Generate overall recommendation based on available windows"""
        if not windows:
            return "No suitable spray windows found in forecast. Check extended forecast or consider adjusting timing."

        total_hours = sum(w["duration_hours"] for w in windows)

        if best_window and best_window["quality"] == "excellent":
            return f"Excellent spray window available: {best_window['start'][:16]} ({best_window['duration_hours']}hr). Plan to spray during this window."
        elif best_window:
            return f"Good spray window available: {best_window['start'][:16]} ({best_window['duration_hours']}hr). Conditions acceptable for application."
        else:
            return f"Limited spray windows ({total_hours:.1f} total hours). Consider partial application or alternative timing."

    def calculate_cost_of_waiting(
        self,
        current_conditions: WeatherCondition,
        forecast: List[WeatherCondition],
        spray_type: SprayType,
        acres: float,
        product_cost_per_acre: float,
        application_cost_per_acre: float,
        target_pest_or_disease: Optional[str] = None,
        current_pressure: str = "moderate",  # low, moderate, high
        crop: str = "corn",
        yield_goal: float = 200,
        grain_price: float = 4.50
    ) -> Dict[str, Any]:
        """
        Calculate the economic cost of waiting to spray vs. spraying now

        This helps answer: "Should I spray today in marginal conditions or wait?"

        Args:
            current_conditions: Current weather
            forecast: Upcoming weather forecast
            spray_type: Type of application
            acres: Field size
            product_cost_per_acre: Product cost
            application_cost_per_acre: Application cost
            target_pest_or_disease: What you're treating
            current_pressure: Current pest/disease pressure level
            crop: Crop type
            yield_goal: Target yield
            grain_price: Commodity price
        """
        # Evaluate current conditions
        current_eval = self.evaluate_current_conditions(current_conditions, spray_type)
        current_risk = ApplicationRisk(current_eval["evaluation"]["risk_level"])

        # Find next good window
        windows_result = self.find_spray_windows(forecast, spray_type, min_window_hours=2)
        next_window = windows_result.get("best_window")

        # Calculate waiting time
        if next_window:
            next_window_start = datetime.fromisoformat(next_window["start"])
            wait_hours = (next_window_start - current_conditions.datetime).total_seconds() / 3600
        else:
            wait_hours = 72  # Assume 3 days if no window found

        # Cost components
        total_application_cost = (product_cost_per_acre + application_cost_per_acre) * acres

        # Estimate yield loss from waiting
        # This varies by pest/disease and current pressure
        daily_yield_loss_pct = self._estimate_daily_yield_loss(
            target_pest_or_disease, current_pressure, spray_type
        )
        wait_days = wait_hours / 24
        estimated_yield_loss_pct = min(daily_yield_loss_pct * wait_days, 15)  # Cap at 15%

        yield_loss_bushels = yield_goal * (estimated_yield_loss_pct / 100) * acres
        yield_loss_dollars = yield_loss_bushels * grain_price

        # Estimate efficacy reduction from poor conditions
        efficacy_reduction = self._estimate_efficacy_reduction(current_risk)
        wasted_product_risk = efficacy_reduction * total_application_cost

        # Calculate scenarios
        spray_now_cost = total_application_cost + wasted_product_risk
        wait_cost = yield_loss_dollars
        net_cost_of_waiting = wait_cost - wasted_product_risk

        # Make recommendation
        if current_risk == ApplicationRisk.DO_NOT_SPRAY:
            recommendation = "WAIT"
            reasoning = "Current conditions prohibit safe/effective application. Risk of complete product waste."
        elif current_risk == ApplicationRisk.POOR:
            if net_cost_of_waiting > total_application_cost * 0.3:
                recommendation = "SPRAY NOW (with caution)"
                reasoning = f"Yield loss risk (${yield_loss_dollars:.0f}) outweighs efficacy risk. Use drift reduction measures."
            else:
                recommendation = "WAIT"
                reasoning = "Conditions poor and yield loss risk manageable. Wait for better window."
        elif current_risk == ApplicationRisk.MARGINAL:
            if net_cost_of_waiting > total_application_cost * 0.2:
                recommendation = "SPRAY NOW"
                reasoning = f"Yield loss from waiting (${yield_loss_dollars:.0f}) exceeds efficacy risk."
            else:
                recommendation = "WAIT IF POSSIBLE"
                reasoning = "Better window coming soon with minimal yield loss risk."
        else:
            recommendation = "SPRAY NOW"
            reasoning = "Conditions favorable for application."

        return {
            "analysis_time": current_conditions.datetime.isoformat(),
            "current_conditions": {
                "risk_level": current_risk.value,
                "score": current_eval["evaluation"]["score"],
                "issues": current_eval["evaluation"]["issues"]
            },
            "next_good_window": {
                "start": next_window["start"] if next_window else "None found in forecast",
                "hours_from_now": round(wait_hours, 1),
                "quality": next_window["quality"] if next_window else "N/A"
            },
            "economic_analysis": {
                "acres": acres,
                "application_cost": round(total_application_cost, 2),
                "wait_analysis": {
                    "wait_hours": round(wait_hours, 1),
                    "daily_yield_loss_estimate_pct": round(daily_yield_loss_pct, 2),
                    "total_yield_loss_estimate_pct": round(estimated_yield_loss_pct, 2),
                    "yield_loss_bushels": round(yield_loss_bushels, 1),
                    "yield_loss_dollars": round(yield_loss_dollars, 2)
                },
                "spray_now_analysis": {
                    "efficacy_reduction_estimate_pct": round(efficacy_reduction * 100, 1),
                    "wasted_product_risk_dollars": round(wasted_product_risk, 2)
                },
                "cost_comparison": {
                    "cost_to_spray_now": round(spray_now_cost, 2),
                    "cost_to_wait": round(wait_cost, 2),
                    "net_cost_of_waiting": round(net_cost_of_waiting, 2)
                }
            },
            "recommendation": recommendation,
            "reasoning": reasoning,
            "action_items": self._generate_action_items(recommendation, current_risk, spray_type)
        }

    def _estimate_daily_yield_loss(
        self,
        pest_or_disease: Optional[str],
        pressure: str,
        spray_type: SprayType
    ) -> float:
        """Estimate daily yield loss percentage from delaying treatment"""
        # Base daily loss rates by pressure level
        base_rates = {
            "low": 0.1,
            "moderate": 0.3,
            "high": 0.8
        }
        base_rate = base_rates.get(pressure, 0.3)

        # Adjust for specific pests/diseases
        high_damage_pests = ["spider_mite", "corn_rootworm", "sudden_death_syndrome", "southern_rust"]
        moderate_damage = ["soybean_aphid", "gray_leaf_spot", "frogeye_leaf_spot"]

        if pest_or_disease:
            pest_lower = pest_or_disease.lower().replace(" ", "_")
            if pest_lower in high_damage_pests:
                base_rate *= 1.5
            elif pest_lower in moderate_damage:
                base_rate *= 1.2

        # Fungicides during disease pressure escalate faster
        if spray_type == SprayType.FUNGICIDE and pressure == "high":
            base_rate *= 1.3

        return base_rate

    def _estimate_efficacy_reduction(self, risk_level: ApplicationRisk) -> float:
        """Estimate what percentage of product may be wasted due to poor conditions"""
        reductions = {
            ApplicationRisk.EXCELLENT: 0.0,
            ApplicationRisk.GOOD: 0.05,
            ApplicationRisk.MARGINAL: 0.15,
            ApplicationRisk.POOR: 0.35,
            ApplicationRisk.DO_NOT_SPRAY: 0.70
        }
        return reductions.get(risk_level, 0.2)

    def _generate_action_items(
        self,
        recommendation: str,
        risk_level: ApplicationRisk,
        spray_type: SprayType
    ) -> List[str]:
        """Generate specific action items based on recommendation"""
        items = []

        if "SPRAY NOW" in recommendation:
            if risk_level in [ApplicationRisk.MARGINAL, ApplicationRisk.POOR]:
                items.append("Use drift reduction nozzles (AI, TTI)")
                items.append("Reduce spray pressure to 30-40 PSI")
                items.append("Increase carrier volume to 15+ GPA")
                items.append("Avoid field edges near sensitive areas")
            items.append("Monitor weather radar during application")
            items.append("Document conditions for records")

        elif recommendation == "WAIT":
            items.append("Set weather alert for next spray window")
            items.append("Continue scouting to monitor pressure")
            items.append("Check extended forecast for planning")
            if spray_type == SprayType.FUNGICIDE:
                items.append("Monitor disease development closely")

        return items

    def assess_disease_pressure(
        self,
        weather_history: List[WeatherCondition],
        crop: str,
        growth_stage: str
    ) -> Dict[str, Any]:
        """
        Assess disease pressure based on recent weather conditions

        Args:
            weather_history: Past 7-14 days of weather
            crop: Crop type
            growth_stage: Current growth stage
        """
        if not weather_history:
            return {"error": "Weather history required"}

        # Calculate averages and accumulations
        avg_temp = sum(w.temp_f for w in weather_history) / len(weather_history)
        avg_humidity = sum(w.humidity_pct for w in weather_history) / len(weather_history)
        wet_hours = sum(1 for w in weather_history if w.leaf_wetness_likely)
        rainy_hours = sum(1 for w in weather_history if w.precip_amount_in > 0)

        # Select relevant diseases based on crop
        if crop.lower() == "corn":
            diseases_to_check = ["gray_leaf_spot", "northern_corn_leaf_blight", "southern_rust"]
        elif crop.lower() in ["soybean", "soybeans"]:
            diseases_to_check = ["frogeye_leaf_spot", "sudden_death_syndrome", "white_mold"]
        else:
            diseases_to_check = list(DISEASE_PRESSURE_FACTORS.keys())

        disease_risks = []
        for disease in diseases_to_check:
            factors = DISEASE_PRESSURE_FACTORS.get(disease)
            if not factors:
                continue

            # Score each factor
            score = 0
            conditions_met = []

            # Humidity
            if avg_humidity >= factors["humidity_threshold"]:
                score += 30
                conditions_met.append(f"Humidity above {factors['humidity_threshold']}%")

            # Temperature
            temp_min, temp_max = factors["temp_range"]
            if temp_min <= avg_temp <= temp_max:
                score += 30
                conditions_met.append(f"Temp in optimal range ({temp_min}-{temp_max}°F)")
            elif abs(avg_temp - (temp_min + temp_max) / 2) < 10:
                score += 15  # Partial credit for close temps

            # Leaf wetness
            if wet_hours >= factors["leaf_wetness_hours"]:
                score += 40
                conditions_met.append(f"Leaf wetness hours met ({wet_hours}hr)")
            elif wet_hours >= factors["leaf_wetness_hours"] * 0.5:
                score += 20

            # Determine risk level
            if score >= 80:
                risk = "HIGH"
            elif score >= 50:
                risk = "MODERATE"
            elif score >= 25:
                risk = "LOW"
            else:
                risk = "MINIMAL"

            disease_risks.append({
                "disease": disease,
                "risk_level": risk,
                "score": score,
                "conditions_met": conditions_met,
                "description": factors["description"]
            })

        # Sort by risk
        disease_risks.sort(key=lambda x: x["score"], reverse=True)

        # Generate recommendation
        high_risk_diseases = [d for d in disease_risks if d["risk_level"] == "HIGH"]
        if high_risk_diseases:
            recommendation = f"High disease pressure for {', '.join(d['disease'] for d in high_risk_diseases)}. Consider preventive fungicide."
        elif any(d["risk_level"] == "MODERATE" for d in disease_risks):
            recommendation = "Moderate disease pressure. Scout frequently and be prepared to spray if symptoms appear."
        else:
            recommendation = "Disease pressure low. Continue monitoring but fungicide likely not needed."

        return {
            "crop": crop,
            "growth_stage": growth_stage,
            "analysis_period_hours": len(weather_history),
            "weather_summary": {
                "avg_temp_f": round(avg_temp, 1),
                "avg_humidity_pct": round(avg_humidity, 1),
                "wet_hours": wet_hours,
                "rainy_hours": rainy_hours
            },
            "disease_risks": disease_risks,
            "recommendation": recommendation
        }

    def get_spray_timing_by_growth_stage(
        self,
        crop: str,
        growth_stage: str,
        spray_type: SprayType
    ) -> Dict[str, Any]:
        """Get optimal spray timing guidance by crop and growth stage"""

        corn_timings = {
            "V3-V5": {
                SprayType.HERBICIDE: {
                    "timing": "Ideal for post-emergence herbicides",
                    "considerations": ["Weeds should be 2-4 inches", "Crop tolerance highest"],
                    "products": ["Glyphosate", "Atrazine", "Laudis", "Status"]
                },
                SprayType.INSECTICIDE: {
                    "timing": "Scout for early-season pests",
                    "considerations": ["Cutworm, armyworm activity", "Treat at threshold"],
                    "products": ["Bifenthrin", "Warrior"]
                }
            },
            "V6-V8": {
                SprayType.HERBICIDE: {
                    "timing": "Last window for most post herbicides",
                    "considerations": ["Drop nozzles may be needed", "Watch for crop injury"],
                    "products": ["Glyphosate with drop nozzles"]
                },
                SprayType.INSECTICIDE: {
                    "timing": "Scout for rootworm adults, aphids",
                    "considerations": ["European corn borer activity possible"],
                    "products": ["Warrior", "Prevathon"]
                }
            },
            "VT-R1": {
                SprayType.FUNGICIDE: {
                    "timing": "OPTIMAL timing for fungicide ROI",
                    "considerations": ["Apply at VT to R2", "Protect ear leaf"],
                    "products": ["Headline AMP", "Trivapro", "Miravis Neo"]
                },
                SprayType.INSECTICIDE: {
                    "timing": "Japanese beetle, corn rootworm adults",
                    "considerations": ["Silk clipping threshold: 3 beetles/plant"],
                    "products": ["Warrior", "Hero"]
                }
            },
            "R3-R5": {
                SprayType.FUNGICIDE: {
                    "timing": "Late fungicide if disease present",
                    "considerations": ["ROI diminishes after R3", "Only if disease active"],
                    "products": ["Generic triazole if late"]
                }
            }
        }

        soybean_timings = {
            "V2-V4": {
                SprayType.HERBICIDE: {
                    "timing": "Ideal post-emergence window",
                    "considerations": ["Weeds 2-4 inches", "Before canopy closure"],
                    "products": ["Glyphosate", "Liberty", "Flexstar"]
                }
            },
            "R1-R2": {
                SprayType.INSECTICIDE: {
                    "timing": "Scout for soybean aphids",
                    "considerations": ["Threshold: 250 aphids/plant with increasing population"],
                    "products": ["Lambda-cyhalothrin", "Imidacloprid"]
                }
            },
            "R3": {
                SprayType.FUNGICIDE: {
                    "timing": "OPTIMAL timing for fungicide ROI",
                    "considerations": ["Apply at R3 for best results", "Protect pods"],
                    "products": ["Priaxor", "Delaro", "Miravis Top"]
                },
                SprayType.INSECTICIDE: {
                    "timing": "Stink bugs, pod feeders active",
                    "considerations": ["Scout field edges first"],
                    "products": ["Bifenthrin", "Hero"]
                }
            },
            "R5-R6": {
                SprayType.FUNGICIDE: {
                    "timing": "Late application for white mold",
                    "considerations": ["Only if disease active", "ROI questionable"],
                    "products": ["Contans (biological)"]
                }
            }
        }

        crop_lower = crop.lower()
        if crop_lower == "corn":
            timings = corn_timings
        elif crop_lower in ["soybean", "soybeans"]:
            timings = soybean_timings
        else:
            return {"error": f"Timing data not available for {crop}"}

        stage_data = timings.get(growth_stage, {})
        spray_data = stage_data.get(spray_type, {})

        if not spray_data:
            return {
                "crop": crop,
                "growth_stage": growth_stage,
                "spray_type": spray_type.value,
                "message": f"No specific {spray_type.value} recommendation for {crop} at {growth_stage}",
                "general_advice": "Continue scouting and treat at threshold if needed"
            }

        return {
            "crop": crop,
            "growth_stage": growth_stage,
            "spray_type": spray_type.value,
            "timing_recommendation": spray_data.get("timing"),
            "considerations": spray_data.get("considerations", []),
            "suggested_products": spray_data.get("products", [])
        }


# Singleton instance
_spray_optimizer = None


def get_spray_timing_optimizer() -> SprayTimingOptimizer:
    """Get or create spray timing optimizer instance"""
    global _spray_optimizer
    if _spray_optimizer is None:
        _spray_optimizer = SprayTimingOptimizer()
    return _spray_optimizer


# Example usage and testing
if __name__ == "__main__":
    optimizer = SprayTimingOptimizer()

    print("=== SPRAY TIMING OPTIMIZER DEMO ===\n")

    # Create sample current conditions
    current = WeatherCondition(
        datetime=datetime.now(timezone.utc),
        temp_f=78,
        humidity_pct=65,
        wind_mph=7,
        wind_direction="SW",
        precip_chance_pct=20,
        precip_amount_in=0,
        cloud_cover_pct=40,
        dew_point_f=62
    )

    # Evaluate current conditions
    print("--- Current Conditions Evaluation ---")
    result = optimizer.evaluate_current_conditions(
        current, SprayType.HERBICIDE, "glyphosate"
    )
    print(f"Risk Level: {result['evaluation']['risk_level']}")
    print(f"Score: {result['evaluation']['score']}")
    print(f"Recommendation: {result['recommendation']}")

    if result['evaluation']['issues']:
        print(f"Issues: {', '.join(result['evaluation']['issues'])}")
    if result['evaluation']['warnings']:
        print(f"Warnings: {', '.join(result['evaluation']['warnings'])}")

    # Create sample forecast
    print("\n--- Finding Spray Windows ---")
    forecast = []
    base_time = datetime.now(timezone.utc)
    for hour in range(48):
        # Simulate varying conditions
        time = base_time + timedelta(hours=hour)
        is_day = 7 <= time.hour <= 20

        forecast.append(WeatherCondition(
            datetime=time,
            temp_f=75 + (10 if is_day else -5) + (hour % 5),
            humidity_pct=60 + (hour % 20) - (10 if is_day else 0),
            wind_mph=5 + (hour % 8),
            wind_direction="SW",
            precip_chance_pct=10 + (20 if 24 <= hour <= 30 else 0),
            precip_amount_in=0.1 if 26 <= hour <= 28 else 0,
            cloud_cover_pct=30 + (hour % 30),
            dew_point_f=58
        ))

    windows_result = optimizer.find_spray_windows(
        forecast, SprayType.FUNGICIDE, min_window_hours=3
    )

    print(f"Windows Found: {windows_result['windows_found']}")
    if windows_result['best_window']:
        print(f"Best Window: {windows_result['best_window']['start'][:16]}")
        print(f"  Duration: {windows_result['best_window']['duration_hours']} hours")
        print(f"  Quality: {windows_result['best_window']['quality']}")
    print(f"Recommendation: {windows_result['recommendation']}")

    # Cost of waiting analysis
    print("\n--- Cost of Waiting Analysis ---")
    cost_result = optimizer.calculate_cost_of_waiting(
        current_conditions=current,
        forecast=forecast,
        spray_type=SprayType.FUNGICIDE,
        acres=500,
        product_cost_per_acre=22.00,
        application_cost_per_acre=8.50,
        target_pest_or_disease="gray_leaf_spot",
        current_pressure="moderate",
        crop="corn",
        yield_goal=200,
        grain_price=4.50
    )

    print(f"Recommendation: {cost_result['recommendation']}")
    print(f"Reasoning: {cost_result['reasoning']}")
    print(f"Cost to spray now: ${cost_result['economic_analysis']['cost_comparison']['cost_to_spray_now']:,.2f}")
    print(f"Cost to wait: ${cost_result['economic_analysis']['cost_comparison']['cost_to_wait']:,.2f}")

    # Growth stage timing
    print("\n--- Growth Stage Timing ---")
    timing = optimizer.get_spray_timing_by_growth_stage("corn", "VT-R1", SprayType.FUNGICIDE)
    print(f"Crop: {timing['crop']} at {timing['growth_stage']}")
    print(f"Timing: {timing['timing_recommendation']}")
    print(f"Considerations: {', '.join(timing['considerations'])}")
    print(f"Products: {', '.join(timing['suggested_products'])}")
