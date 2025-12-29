"""
Precision Intelligence Service for AgTools
Version: 4.0.0

Advanced precision agriculture intelligence featuring:
- Yield Prediction Engine (ML-based forecasting using historical + weather)
- Prescription Generator (variable rate seeding/fertilizer recommendations)
- Field Zone Analytics (management zones, productivity mapping)
- Decision Support AI (planting, spraying, harvest timing recommendations)
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import random
import math


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class PredictionModel(Enum):
    """Yield prediction model types"""
    HISTORICAL_AVG = "historical_average"
    TREND_ANALYSIS = "trend_analysis"
    WEATHER_ADJUSTED = "weather_adjusted"
    MACHINE_LEARNING = "machine_learning"


class ZoneType(Enum):
    """Management zone types"""
    HIGH_PRODUCTIVITY = "high_productivity"
    MEDIUM_PRODUCTIVITY = "medium_productivity"
    LOW_PRODUCTIVITY = "low_productivity"
    VARIABLE = "variable"
    PROBLEM_AREA = "problem_area"


class PrescriptionType(Enum):
    """Prescription types"""
    SEEDING = "seeding"
    NITROGEN = "nitrogen"
    PHOSPHORUS = "phosphorus"
    POTASSIUM = "potassium"
    LIME = "lime"
    FUNGICIDE = "fungicide"
    GROWTH_REGULATOR = "growth_regulator"


class RecommendationType(Enum):
    """Decision support recommendation types"""
    PLANTING = "planting"
    SPRAYING = "spraying"
    IRRIGATION = "irrigation"
    HARVEST = "harvest"
    FERTILITY = "fertility"
    SCOUTING = "scouting"


class ConfidenceLevel(Enum):
    """Confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CropStage(Enum):
    """Crop growth stages"""
    PRE_PLANT = "pre_plant"
    PLANTING = "planting"
    EMERGENCE = "emergence"
    VEGETATIVE = "vegetative"
    REPRODUCTIVE = "reproductive"
    GRAIN_FILL = "grain_fill"
    MATURITY = "maturity"
    HARVEST = "harvest"


@dataclass
class YieldPrediction:
    """Yield prediction result"""
    id: str
    field_id: str
    field_name: str
    crop: str
    crop_year: int
    prediction_date: date
    model_used: PredictionModel
    predicted_yield: float
    confidence_interval_low: float
    confidence_interval_high: float
    confidence_level: ConfidenceLevel
    factors: Dict[str, Any]
    recommendations: List[str]


@dataclass
class ManagementZone:
    """Field management zone"""
    id: str
    field_id: str
    zone_name: str
    zone_type: ZoneType
    acres: float
    avg_yield: float
    yield_potential: float
    soil_properties: Dict[str, float]
    recommendations: List[str]
    polygon_coords: List[Tuple[float, float]]


@dataclass
class Prescription:
    """Variable rate prescription"""
    id: str
    field_id: str
    prescription_type: PrescriptionType
    crop: str
    crop_year: int
    created_date: date
    zones: List[Dict[str, Any]]  # Zone-specific rates
    total_acres: float
    avg_rate: float
    total_product: float
    estimated_cost: float
    notes: str


@dataclass
class DecisionRecommendation:
    """AI decision support recommendation"""
    id: str
    recommendation_type: RecommendationType
    field_id: str
    field_name: str
    recommendation: str
    reasoning: List[str]
    confidence: ConfidenceLevel
    timing_window: str
    priority: str  # high, medium, low
    weather_factors: Dict[str, Any]
    economic_impact: Dict[str, float]
    created_date: date
    valid_until: date


# =============================================================================
# AGRONOMIC DATA AND MODELS
# =============================================================================

# Louisiana yield potentials by soil type (bu/acre for corn)
YIELD_POTENTIAL_BY_SOIL = {
    "sharkey_clay": 195,
    "commerce_silt_loam": 210,
    "mhoon_silty_clay_loam": 200,
    "gigger_silt_loam": 215,
    "norwood_silt_loam": 205,
    "gallion_very_fine_sandy_loam": 190,
    "default": 180
}

# Crop-specific seeding rates by zone productivity
SEEDING_RATES = {
    "corn": {
        ZoneType.HIGH_PRODUCTIVITY: 36000,
        ZoneType.MEDIUM_PRODUCTIVITY: 34000,
        ZoneType.LOW_PRODUCTIVITY: 32000,
        ZoneType.PROBLEM_AREA: 30000
    },
    "soybeans": {
        ZoneType.HIGH_PRODUCTIVITY: 140000,
        ZoneType.MEDIUM_PRODUCTIVITY: 130000,
        ZoneType.LOW_PRODUCTIVITY: 120000,
        ZoneType.PROBLEM_AREA: 110000
    }
}

# Nitrogen recommendations by yield goal (lbs N/acre for corn)
NITROGEN_RATES = {
    "corn": lambda yield_goal: yield_goal * 1.2 - 40,  # 1.2 lbs N per bu, minus soil credit
    "cotton": lambda yield_goal: yield_goal * 0.12,
    "rice": lambda yield_goal: yield_goal * 0.018
}

# Weather impact factors on yield
WEATHER_IMPACT = {
    "excessive_heat_days": -2.5,  # bu/acre per day >95F during pollination
    "drought_stress_days": -1.8,  # bu/acre per day of stress
    "excessive_rain_days": -1.2,  # bu/acre per day >2" rain
    "optimal_gdd_deviation": -0.3  # bu/acre per % deviation from optimal
}

# Optimal planting windows (Louisiana)
PLANTING_WINDOWS = {
    "corn": {"optimal_start": (3, 1), "optimal_end": (4, 15), "late_plant": (5, 1)},
    "soybeans": {"optimal_start": (4, 15), "optimal_end": (6, 1), "late_plant": (6, 30)},
    "cotton": {"optimal_start": (4, 20), "optimal_end": (5, 20), "late_plant": (6, 10)},
    "rice": {"optimal_start": (3, 15), "optimal_end": (5, 1), "late_plant": (6, 1)}
}

# Spray timing factors
SPRAY_TIMING = {
    "min_temp": 40,
    "max_temp": 85,
    "max_wind": 10,  # mph
    "max_humidity_herbicide": 80,
    "min_humidity_fungicide": 50,
    "no_rain_hours": 4
}


# =============================================================================
# PRECISION INTELLIGENCE SERVICE CLASS
# =============================================================================

class PrecisionIntelligenceService:
    """Advanced precision agriculture intelligence service"""

    def __init__(self):
        self.predictions: Dict[str, YieldPrediction] = {}
        self.zones: Dict[str, ManagementZone] = {}
        self.prescriptions: Dict[str, Prescription] = {}
        self.recommendations: Dict[str, DecisionRecommendation] = {}

        # Historical data storage
        self.field_history: Dict[str, List[Dict[str, Any]]] = {}
        self.weather_data: Dict[str, Dict[str, Any]] = {}

        self._counters = {
            "prediction": 0, "zone": 0, "prescription": 0, "recommendation": 0
        }

    def _next_id(self, prefix: str) -> str:
        self._counters[prefix] += 1
        return f"{prefix.upper()}-{self._counters[prefix]:04d}"

    # =========================================================================
    # YIELD PREDICTION ENGINE
    # =========================================================================

    def predict_yield(
        self,
        field_id: str,
        field_name: str,
        crop: str,
        crop_year: int,
        acres: float,
        historical_yields: List[float] = None,
        soil_type: str = "default",
        current_conditions: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Predict yield using multiple models.

        Combines historical data, trend analysis, and weather adjustments.
        """
        prediction_id = self._next_id("prediction")

        # Get yield potential for soil type
        yield_potential = YIELD_POTENTIAL_BY_SOIL.get(soil_type, YIELD_POTENTIAL_BY_SOIL["default"])

        # Historical average model
        if historical_yields and len(historical_yields) >= 3:
            hist_avg = statistics.mean(historical_yields)
            hist_std = statistics.stdev(historical_yields)

            # Trend analysis (simple linear)
            if len(historical_yields) >= 5:
                years = list(range(len(historical_yields)))
                n = len(years)
                sum_x = sum(years)
                sum_y = sum(historical_yields)
                sum_xy = sum(x * y for x, y in zip(years, historical_yields))
                sum_x2 = sum(x ** 2 for x in years)

                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
                intercept = (sum_y - slope * sum_x) / n
                trend_prediction = intercept + slope * len(historical_yields)
            else:
                trend_prediction = hist_avg
                slope = 0

            model_used = PredictionModel.TREND_ANALYSIS
        else:
            # Use yield potential with adjustment
            hist_avg = yield_potential * 0.85  # Assume 85% of potential
            hist_std = yield_potential * 0.10
            trend_prediction = hist_avg
            slope = 0
            model_used = PredictionModel.HISTORICAL_AVG

        # Weather adjustments
        weather_adjustment = 0
        weather_factors = {}

        if current_conditions:
            # Heat stress during pollination
            heat_days = current_conditions.get("excessive_heat_days", 0)
            if heat_days > 0:
                heat_impact = heat_days * WEATHER_IMPACT["excessive_heat_days"]
                weather_adjustment += heat_impact
                weather_factors["heat_stress"] = f"{heat_days} days, {heat_impact:+.1f} bu/ac"

            # Drought stress
            drought_days = current_conditions.get("drought_stress_days", 0)
            if drought_days > 0:
                drought_impact = drought_days * WEATHER_IMPACT["drought_stress_days"]
                weather_adjustment += drought_impact
                weather_factors["drought_stress"] = f"{drought_days} days, {drought_impact:+.1f} bu/ac"

            # Excessive rainfall
            wet_days = current_conditions.get("excessive_rain_days", 0)
            if wet_days > 0:
                wet_impact = wet_days * WEATHER_IMPACT["excessive_rain_days"]
                weather_adjustment += wet_impact
                weather_factors["excess_moisture"] = f"{wet_days} days, {wet_impact:+.1f} bu/ac"

            # GDD deviation
            gdd_deviation = current_conditions.get("gdd_deviation_pct", 0)
            if abs(gdd_deviation) > 5:
                gdd_impact = abs(gdd_deviation) * WEATHER_IMPACT["optimal_gdd_deviation"]
                weather_adjustment -= gdd_impact
                weather_factors["gdd_deviation"] = f"{gdd_deviation}%, {-gdd_impact:+.1f} bu/ac"

            model_used = PredictionModel.WEATHER_ADJUSTED

        # Final prediction
        base_prediction = trend_prediction if slope > 0 else hist_avg
        predicted_yield = base_prediction + weather_adjustment

        # Confidence intervals
        confidence_range = hist_std * 1.5 if hist_std else yield_potential * 0.12
        ci_low = predicted_yield - confidence_range
        ci_high = predicted_yield + confidence_range

        # Determine confidence level
        if historical_yields and len(historical_yields) >= 5:
            confidence = ConfidenceLevel.HIGH
        elif historical_yields and len(historical_yields) >= 3:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        # Generate recommendations
        recommendations = []
        if predicted_yield < yield_potential * 0.7:
            recommendations.append("Consider soil testing to identify limiting factors")
        if slope < 0:
            recommendations.append("Declining yield trend - review management practices")
        if weather_adjustment < -10:
            recommendations.append("Significant weather impact - consider crop insurance review")
        if predicted_yield > hist_avg * 1.1:
            recommendations.append("Strong yield potential - ensure adequate marketing coverage")

        # Store prediction
        prediction = YieldPrediction(
            id=prediction_id,
            field_id=field_id,
            field_name=field_name,
            crop=crop,
            crop_year=crop_year,
            prediction_date=date.today(),
            model_used=model_used,
            predicted_yield=predicted_yield,
            confidence_interval_low=ci_low,
            confidence_interval_high=ci_high,
            confidence_level=confidence,
            factors={
                "yield_potential": yield_potential,
                "historical_avg": round(hist_avg, 1) if historical_yields else None,
                "trend_slope": round(slope, 2),
                "weather_adjustment": round(weather_adjustment, 1),
                "weather_factors": weather_factors
            },
            recommendations=recommendations
        )

        self.predictions[prediction_id] = prediction

        # Calculate projected production
        projected_production = predicted_yield * acres

        return {
            "id": prediction_id,
            "field_name": field_name,
            "crop": crop,
            "crop_year": crop_year,
            "prediction": {
                "yield_per_acre": round(predicted_yield, 1),
                "confidence_interval": f"{round(ci_low, 1)} - {round(ci_high, 1)}",
                "confidence_level": confidence.value,
                "model_used": model_used.value
            },
            "projected_production": {
                "acres": acres,
                "total_bushels": round(projected_production, 0),
                "vs_yield_potential": f"{round(predicted_yield / yield_potential * 100, 1)}%"
            },
            "factors": {
                "yield_potential": yield_potential,
                "historical_average": round(hist_avg, 1),
                "yield_trend": f"{slope:+.1f} bu/year" if slope else "N/A",
                "weather_adjustment": f"{weather_adjustment:+.1f} bu/ac" if weather_adjustment else "None",
                "weather_details": weather_factors
            },
            "recommendations": recommendations,
            "message": f"Predicted yield: {round(predicted_yield, 1)} bu/acre ({confidence.value} confidence)"
        }

    def compare_yield_scenarios(
        self,
        field_id: str,
        field_name: str,
        crop: str,
        acres: float,
        scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare yield predictions under different scenarios"""
        results = []

        for i, scenario in enumerate(scenarios):
            prediction = self.predict_yield(
                field_id=field_id,
                field_name=field_name,
                crop=crop,
                crop_year=date.today().year,
                acres=acres,
                historical_yields=scenario.get("historical_yields"),
                soil_type=scenario.get("soil_type", "default"),
                current_conditions=scenario.get("conditions")
            )

            results.append({
                "scenario": scenario.get("name", f"Scenario {i+1}"),
                "predicted_yield": prediction["prediction"]["yield_per_acre"],
                "total_production": prediction["projected_production"]["total_bushels"],
                "confidence": prediction["prediction"]["confidence_level"]
            })

        # Find best/worst
        best = max(results, key=lambda x: x["predicted_yield"])
        worst = min(results, key=lambda x: x["predicted_yield"])

        return {
            "field_name": field_name,
            "crop": crop,
            "acres": acres,
            "scenarios_compared": len(results),
            "results": results,
            "summary": {
                "best_scenario": best["scenario"],
                "best_yield": best["predicted_yield"],
                "worst_scenario": worst["scenario"],
                "worst_yield": worst["predicted_yield"],
                "yield_range": round(best["predicted_yield"] - worst["predicted_yield"], 1)
            }
        }

    # =========================================================================
    # PRESCRIPTION GENERATOR
    # =========================================================================

    def create_zone(
        self,
        field_id: str,
        zone_name: str,
        zone_type: str,
        acres: float,
        avg_yield: float,
        yield_potential: float,
        soil_properties: Dict[str, float] = None,
        polygon_coords: List[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """Create a management zone within a field"""
        try:
            ztype = ZoneType(zone_type)
        except ValueError:
            return {"error": f"Invalid zone type: {zone_type}"}

        zone_id = self._next_id("zone")

        # Generate recommendations based on zone type
        recommendations = []
        if ztype == ZoneType.LOW_PRODUCTIVITY:
            recommendations.append("Consider drainage improvements")
            recommendations.append("Soil sampling for nutrient deficiencies")
            recommendations.append("Reduce input rates to match yield potential")
        elif ztype == ZoneType.HIGH_PRODUCTIVITY:
            recommendations.append("Maximize inputs to capture full potential")
            recommendations.append("Consider premium seed placement")
        elif ztype == ZoneType.PROBLEM_AREA:
            recommendations.append("Investigate root cause of poor performance")
            recommendations.append("Consider soil remediation or alternative use")

        zone = ManagementZone(
            id=zone_id,
            field_id=field_id,
            zone_name=zone_name,
            zone_type=ztype,
            acres=acres,
            avg_yield=avg_yield,
            yield_potential=yield_potential,
            soil_properties=soil_properties or {},
            recommendations=recommendations,
            polygon_coords=polygon_coords or []
        )

        self.zones[zone_id] = zone

        return {
            "id": zone_id,
            "zone_name": zone_name,
            "type": zone_type,
            "acres": acres,
            "yield_performance": f"{round(avg_yield / yield_potential * 100, 1)}% of potential",
            "recommendations": recommendations,
            "message": f"Zone '{zone_name}' created with {acres} acres"
        }

    def generate_seeding_prescription(
        self,
        field_id: str,
        crop: str,
        crop_year: int,
        seed_cost_per_unit: float,
        units_per_bag: int = 80000  # seeds per bag for corn
    ) -> Dict[str, Any]:
        """Generate variable rate seeding prescription"""
        field_zones = [z for z in self.zones.values() if z.field_id == field_id]

        if not field_zones:
            return {"error": f"No zones defined for field {field_id}"}

        prescription_id = self._next_id("prescription")

        crop_rates = SEEDING_RATES.get(crop, SEEDING_RATES["corn"])

        zone_prescriptions = []
        total_acres = 0
        total_seeds = 0

        for zone in field_zones:
            rate = crop_rates.get(zone.zone_type, crop_rates[ZoneType.MEDIUM_PRODUCTIVITY])
            zone_seeds = rate * zone.acres

            zone_prescriptions.append({
                "zone_name": zone.zone_name,
                "zone_type": zone.zone_type.value,
                "acres": zone.acres,
                "seeding_rate": rate,
                "total_seeds": zone_seeds
            })

            total_acres += zone.acres
            total_seeds += zone_seeds

        avg_rate = total_seeds / total_acres if total_acres > 0 else 0
        total_bags = math.ceil(total_seeds / units_per_bag)
        estimated_cost = total_bags * seed_cost_per_unit

        prescription = Prescription(
            id=prescription_id,
            field_id=field_id,
            prescription_type=PrescriptionType.SEEDING,
            crop=crop,
            crop_year=crop_year,
            created_date=date.today(),
            zones=zone_prescriptions,
            total_acres=total_acres,
            avg_rate=avg_rate,
            total_product=total_bags,
            estimated_cost=estimated_cost,
            notes=f"Variable rate seeding for {crop}"
        )

        self.prescriptions[prescription_id] = prescription

        # Compare to flat rate
        flat_rate = crop_rates[ZoneType.MEDIUM_PRODUCTIVITY]
        flat_seeds = flat_rate * total_acres
        flat_bags = math.ceil(flat_seeds / units_per_bag)
        flat_cost = flat_bags * seed_cost_per_unit
        savings = flat_cost - estimated_cost

        return {
            "id": prescription_id,
            "field_id": field_id,
            "crop": crop,
            "prescription_type": "seeding",
            "zones": zone_prescriptions,
            "summary": {
                "total_acres": total_acres,
                "average_rate": round(avg_rate, 0),
                "total_bags": total_bags,
                "estimated_cost": round(estimated_cost, 2)
            },
            "vs_flat_rate": {
                "flat_rate": flat_rate,
                "flat_rate_bags": flat_bags,
                "flat_rate_cost": round(flat_cost, 2),
                "vr_savings": round(savings, 2),
                "savings_per_acre": round(savings / total_acres, 2) if total_acres > 0 else 0
            },
            "message": f"Seeding prescription created - potential savings of ${savings:,.2f}"
        }

    def generate_nitrogen_prescription(
        self,
        field_id: str,
        crop: str,
        crop_year: int,
        nitrogen_price_per_lb: float,
        soil_nitrogen_credit: float = 30,
        previous_crop: str = "corn"
    ) -> Dict[str, Any]:
        """Generate variable rate nitrogen prescription"""
        field_zones = [z for z in self.zones.values() if z.field_id == field_id]

        if not field_zones:
            return {"error": f"No zones defined for field {field_id}"}

        prescription_id = self._next_id("prescription")

        # Legume credit
        legume_credit = 40 if previous_crop in ["soybeans", "peanuts"] else 0

        zone_prescriptions = []
        total_acres = 0
        total_nitrogen = 0

        for zone in field_zones:
            # Calculate N rate based on yield goal
            yield_goal = zone.yield_potential * 0.95  # Target 95% of potential

            if crop == "corn":
                base_rate = yield_goal * 1.2  # 1.2 lbs N per bu goal
                rate = max(0, base_rate - soil_nitrogen_credit - legume_credit)
            else:
                base_rate = yield_goal * 0.12  # Simplified for other crops
                rate = max(0, base_rate - soil_nitrogen_credit)

            zone_nitrogen = rate * zone.acres

            zone_prescriptions.append({
                "zone_name": zone.zone_name,
                "zone_type": zone.zone_type.value,
                "acres": zone.acres,
                "yield_goal": round(yield_goal, 0),
                "nitrogen_rate": round(rate, 0),
                "total_nitrogen_lbs": round(zone_nitrogen, 0)
            })

            total_acres += zone.acres
            total_nitrogen += zone_nitrogen

        avg_rate = total_nitrogen / total_acres if total_acres > 0 else 0
        estimated_cost = total_nitrogen * nitrogen_price_per_lb

        prescription = Prescription(
            id=prescription_id,
            field_id=field_id,
            prescription_type=PrescriptionType.NITROGEN,
            crop=crop,
            crop_year=crop_year,
            created_date=date.today(),
            zones=zone_prescriptions,
            total_acres=total_acres,
            avg_rate=avg_rate,
            total_product=total_nitrogen,
            estimated_cost=estimated_cost,
            notes=f"Variable rate nitrogen for {crop}"
        )

        self.prescriptions[prescription_id] = prescription

        return {
            "id": prescription_id,
            "field_id": field_id,
            "crop": crop,
            "prescription_type": "nitrogen",
            "credits_applied": {
                "soil_nitrogen": soil_nitrogen_credit,
                "legume_credit": legume_credit,
                "previous_crop": previous_crop
            },
            "zones": zone_prescriptions,
            "summary": {
                "total_acres": total_acres,
                "average_rate": round(avg_rate, 0),
                "total_nitrogen_lbs": round(total_nitrogen, 0),
                "estimated_cost": round(estimated_cost, 2),
                "cost_per_acre": round(estimated_cost / total_acres, 2) if total_acres > 0 else 0
            },
            "message": f"Nitrogen prescription created - {round(total_nitrogen, 0)} lbs total"
        }

    # =========================================================================
    # FIELD ZONE ANALYTICS
    # =========================================================================

    def analyze_field_productivity(
        self,
        field_id: str,
        field_name: str,
        total_acres: float,
        yield_data: List[Dict[str, Any]]  # [{year, yield, zone_yields: {zone: yield}}]
    ) -> Dict[str, Any]:
        """Analyze field productivity patterns and recommend zones"""
        if not yield_data:
            return {"error": "No yield data provided"}

        # Overall field statistics
        yields = [d["yield"] for d in yield_data]
        avg_yield = statistics.mean(yields)
        yield_std = statistics.stdev(yields) if len(yields) > 1 else 0
        cv = (yield_std / avg_yield * 100) if avg_yield > 0 else 0

        # Trend analysis
        if len(yields) >= 3:
            recent_avg = statistics.mean(yields[-3:])
            historical_avg = statistics.mean(yields[:-3]) if len(yields) > 3 else yields[0]
            trend = "improving" if recent_avg > historical_avg * 1.05 else \
                   "declining" if recent_avg < historical_avg * 0.95 else "stable"
        else:
            trend = "insufficient_data"

        # Zone analysis if zone data provided
        zone_analysis = []
        if yield_data[0].get("zone_yields"):
            zone_names = list(yield_data[0]["zone_yields"].keys())
            for zone_name in zone_names:
                zone_yields = [d["zone_yields"].get(zone_name, 0) for d in yield_data if d.get("zone_yields")]
                zone_avg = statistics.mean(zone_yields) if zone_yields else 0
                zone_cv = (statistics.stdev(zone_yields) / zone_avg * 100) if len(zone_yields) > 1 and zone_avg > 0 else 0

                # Classify zone
                if zone_avg > avg_yield * 1.1:
                    zone_type = ZoneType.HIGH_PRODUCTIVITY
                elif zone_avg < avg_yield * 0.8:
                    zone_type = ZoneType.LOW_PRODUCTIVITY
                elif zone_cv > 25:
                    zone_type = ZoneType.VARIABLE
                else:
                    zone_type = ZoneType.MEDIUM_PRODUCTIVITY

                zone_analysis.append({
                    "zone_name": zone_name,
                    "avg_yield": round(zone_avg, 1),
                    "cv": round(zone_cv, 1),
                    "vs_field_avg": f"{round((zone_avg - avg_yield) / avg_yield * 100, 1):+}%",
                    "classification": zone_type.value,
                    "recommendation": self._get_zone_recommendation(zone_type, zone_avg, avg_yield)
                })

        # Recommendations
        recommendations = []
        if cv > 20:
            recommendations.append("High yield variability - consider zone management")
        if trend == "declining":
            recommendations.append("Declining trend - review soil health and fertility program")
        if any(z["classification"] == "problem_area" for z in zone_analysis):
            recommendations.append("Problem areas identified - prioritize investigation")

        return {
            "field_id": field_id,
            "field_name": field_name,
            "total_acres": total_acres,
            "years_analyzed": len(yield_data),
            "field_statistics": {
                "average_yield": round(avg_yield, 1),
                "yield_range": f"{round(min(yields), 1)} - {round(max(yields), 1)}",
                "coefficient_of_variation": f"{round(cv, 1)}%",
                "trend": trend
            },
            "zone_analysis": zone_analysis,
            "recommendations": recommendations,
            "management_zones_suggested": len(set(z["classification"] for z in zone_analysis))
        }

    def _get_zone_recommendation(self, zone_type: ZoneType, zone_avg: float, field_avg: float) -> str:
        """Get recommendation for zone type"""
        if zone_type == ZoneType.HIGH_PRODUCTIVITY:
            return "Maximize inputs to capture full potential"
        elif zone_type == ZoneType.LOW_PRODUCTIVITY:
            return "Reduce inputs, investigate limiting factors"
        elif zone_type == ZoneType.VARIABLE:
            return "High variability - consider drainage or soil testing"
        else:
            return "Maintain current management"

    def calculate_zone_roi(
        self,
        field_id: str,
        zones: List[Dict[str, Any]],  # [{zone_name, acres, vr_yield, flat_yield}]
        price_per_unit: float,
        vr_cost_per_acre: float = 5.0  # Extra cost for variable rate
    ) -> Dict[str, Any]:
        """Calculate ROI of zone management vs flat rate"""
        total_acres = sum(z["acres"] for z in zones)
        total_vr_cost = total_acres * vr_cost_per_acre

        zone_results = []
        total_vr_revenue = 0
        total_flat_revenue = 0

        for zone in zones:
            vr_revenue = zone["acres"] * zone["vr_yield"] * price_per_unit
            flat_revenue = zone["acres"] * zone["flat_yield"] * price_per_unit
            zone_benefit = vr_revenue - flat_revenue

            zone_results.append({
                "zone_name": zone["zone_name"],
                "acres": zone["acres"],
                "vr_yield": zone["vr_yield"],
                "flat_yield": zone["flat_yield"],
                "yield_increase": round(zone["vr_yield"] - zone["flat_yield"], 1),
                "revenue_increase": round(zone_benefit, 2)
            })

            total_vr_revenue += vr_revenue
            total_flat_revenue += flat_revenue

        gross_benefit = total_vr_revenue - total_flat_revenue
        net_benefit = gross_benefit - total_vr_cost
        roi_pct = (net_benefit / total_vr_cost * 100) if total_vr_cost > 0 else 0

        return {
            "field_id": field_id,
            "analysis": {
                "total_acres": total_acres,
                "price_per_unit": price_per_unit,
                "vr_implementation_cost": round(total_vr_cost, 2)
            },
            "zone_results": zone_results,
            "summary": {
                "gross_revenue_increase": round(gross_benefit, 2),
                "net_benefit": round(net_benefit, 2),
                "benefit_per_acre": round(net_benefit / total_acres, 2) if total_acres > 0 else 0,
                "roi_percentage": round(roi_pct, 1)
            },
            "recommendation": "Implement zone management" if net_benefit > 0 else "Continue flat rate management"
        }

    # =========================================================================
    # DECISION SUPPORT AI
    # =========================================================================

    def get_planting_recommendation(
        self,
        field_id: str,
        field_name: str,
        crop: str,
        target_date: date,
        soil_temp: float,
        soil_moisture: str,  # "dry", "optimal", "wet", "saturated"
        forecast: Dict[str, Any]  # {"rain_chance": 0-100, "temps": [high, low]}
    ) -> Dict[str, Any]:
        """Get AI recommendation for planting timing"""
        rec_id = self._next_id("recommendation")

        window = PLANTING_WINDOWS.get(crop, PLANTING_WINDOWS["corn"])
        optimal_start = date(target_date.year, *window["optimal_start"])
        optimal_end = date(target_date.year, *window["optimal_end"])
        late_plant = date(target_date.year, *window["late_plant"])

        reasoning = []
        priority = "medium"
        recommendation = ""
        confidence = ConfidenceLevel.MEDIUM

        # Soil temperature check
        min_soil_temp = {"corn": 50, "soybeans": 55, "cotton": 65, "rice": 55}.get(crop, 50)
        if soil_temp < min_soil_temp:
            reasoning.append(f"Soil temp ({soil_temp}F) below minimum ({min_soil_temp}F)")
            recommendation = "WAIT - Soil too cold"
            priority = "low"
        elif soil_temp >= min_soil_temp + 5:
            reasoning.append(f"Soil temp ({soil_temp}F) is optimal for {crop}")

        # Soil moisture check
        if soil_moisture == "saturated":
            reasoning.append("Soil saturated - equipment will cause compaction")
            recommendation = "WAIT - Too wet"
            priority = "low"
        elif soil_moisture == "wet":
            reasoning.append("Soil wet - marginal conditions")
            if not recommendation:
                recommendation = "CAUTION - Monitor conditions"
        elif soil_moisture == "optimal":
            reasoning.append("Soil moisture is ideal")
        elif soil_moisture == "dry":
            reasoning.append("Soil dry - may need irrigation after planting")

        # Timing check
        if target_date < optimal_start:
            reasoning.append(f"Before optimal window (starts {optimal_start.strftime('%b %d')})")
            if not recommendation:
                recommendation = "WAIT - Too early"
        elif target_date > late_plant:
            reasoning.append(f"Past late plant date ({late_plant.strftime('%b %d')})")
            recommendation = "URGENT - Plant immediately or consider prevented planting"
            priority = "high"
        elif target_date > optimal_end:
            reasoning.append(f"Past optimal window (ended {optimal_end.strftime('%b %d')})")
            priority = "high"
            if not recommendation:
                recommendation = "PLANT NOW - Declining yield potential"
        elif optimal_start <= target_date <= optimal_end:
            reasoning.append("Within optimal planting window")
            if not recommendation:
                recommendation = "GO - Good conditions for planting"
                confidence = ConfidenceLevel.HIGH

        # Weather forecast check
        if forecast:
            rain_chance = forecast.get("rain_chance", 0)
            if rain_chance > 70:
                reasoning.append(f"High rain chance ({rain_chance}%) in forecast")
                if "WAIT" not in recommendation:
                    recommendation = "CAUTION - Rain expected"

            temps = forecast.get("temps", [])
            if temps and min(temps) < 32:
                reasoning.append("Frost risk in forecast")
                recommendation = "WAIT - Frost risk"
                priority = "low"

        # Default recommendation
        if not recommendation:
            recommendation = "GO - Conditions acceptable"

        # Economic impact
        days_from_optimal = (target_date - optimal_end).days if target_date > optimal_end else 0
        yield_penalty = days_from_optimal * 0.5  # 0.5% per day late

        economic_impact = {
            "days_past_optimal": max(0, days_from_optimal),
            "estimated_yield_penalty": f"{round(yield_penalty, 1)}%",
            "bushels_per_acre_loss": round(180 * yield_penalty / 100, 1) if crop == "corn" else 0
        }

        # Create recommendation
        rec = DecisionRecommendation(
            id=rec_id,
            recommendation_type=RecommendationType.PLANTING,
            field_id=field_id,
            field_name=field_name,
            recommendation=recommendation,
            reasoning=reasoning,
            confidence=confidence,
            timing_window=f"{optimal_start.strftime('%b %d')} - {optimal_end.strftime('%b %d')}",
            priority=priority,
            weather_factors=forecast or {},
            economic_impact=economic_impact,
            created_date=date.today(),
            valid_until=target_date + timedelta(days=3)
        )

        self.recommendations[rec_id] = rec

        return {
            "id": rec_id,
            "field_name": field_name,
            "crop": crop,
            "target_date": target_date.isoformat(),
            "recommendation": recommendation,
            "priority": priority,
            "confidence": confidence.value,
            "reasoning": reasoning,
            "planting_window": {
                "optimal_start": optimal_start.isoformat(),
                "optimal_end": optimal_end.isoformat(),
                "late_plant_date": late_plant.isoformat()
            },
            "conditions": {
                "soil_temp": f"{soil_temp}F (min: {min_soil_temp}F)",
                "soil_moisture": soil_moisture,
                "forecast": forecast
            },
            "economic_impact": economic_impact
        }

    def get_spray_recommendation(
        self,
        field_id: str,
        field_name: str,
        product_type: str,  # "herbicide", "fungicide", "insecticide"
        target_date: date,
        weather: Dict[str, Any]  # {temp, wind, humidity, rain_forecast_hours}
    ) -> Dict[str, Any]:
        """Get AI recommendation for spray timing"""
        rec_id = self._next_id("recommendation")

        reasoning = []
        priority = "medium"
        recommendation = ""
        confidence = ConfidenceLevel.MEDIUM

        temp = weather.get("temp", 70)
        wind = weather.get("wind", 5)
        humidity = weather.get("humidity", 60)
        rain_hours = weather.get("rain_forecast_hours", 24)

        # Temperature check
        if temp < SPRAY_TIMING["min_temp"]:
            reasoning.append(f"Temperature ({temp}F) too low - reduced efficacy")
            recommendation = "WAIT - Too cold"
            priority = "low"
        elif temp > SPRAY_TIMING["max_temp"]:
            reasoning.append(f"Temperature ({temp}F) too high - volatilization risk")
            recommendation = "WAIT - Too hot"
            priority = "low"
        else:
            reasoning.append(f"Temperature ({temp}F) acceptable")

        # Wind check
        if wind > SPRAY_TIMING["max_wind"]:
            reasoning.append(f"Wind ({wind} mph) too high - drift risk")
            recommendation = "WAIT - Too windy"
            priority = "low"
        elif wind > SPRAY_TIMING["max_wind"] - 3:
            reasoning.append(f"Wind ({wind} mph) marginal - use drift reducing nozzles")
        else:
            reasoning.append(f"Wind ({wind} mph) acceptable")

        # Humidity check
        if product_type == "herbicide" and humidity > SPRAY_TIMING["max_humidity_herbicide"]:
            reasoning.append(f"High humidity ({humidity}%) may reduce herbicide efficacy")
        if product_type == "fungicide" and humidity < SPRAY_TIMING["min_humidity_fungicide"]:
            reasoning.append(f"Low humidity ({humidity}%) - fungicide may dry too quickly")

        # Rain forecast
        if rain_hours < SPRAY_TIMING["no_rain_hours"]:
            reasoning.append(f"Rain expected in {rain_hours} hours - product may wash off")
            if not recommendation:
                recommendation = "WAIT - Rain expected"
            priority = "low"
        else:
            reasoning.append(f"No rain for {rain_hours}+ hours - good conditions")

        # Final recommendation
        if not recommendation:
            if all([
                SPRAY_TIMING["min_temp"] <= temp <= SPRAY_TIMING["max_temp"],
                wind <= SPRAY_TIMING["max_wind"],
                rain_hours >= SPRAY_TIMING["no_rain_hours"]
            ]):
                recommendation = "GO - Good spray conditions"
                confidence = ConfidenceLevel.HIGH
            else:
                recommendation = "CAUTION - Check marginal conditions"

        rec = DecisionRecommendation(
            id=rec_id,
            recommendation_type=RecommendationType.SPRAYING,
            field_id=field_id,
            field_name=field_name,
            recommendation=recommendation,
            reasoning=reasoning,
            confidence=confidence,
            timing_window="Next 4-6 hours" if "GO" in recommendation else "Wait for conditions",
            priority=priority,
            weather_factors=weather,
            economic_impact={},
            created_date=date.today(),
            valid_until=target_date + timedelta(days=1)
        )

        self.recommendations[rec_id] = rec

        return {
            "id": rec_id,
            "field_name": field_name,
            "product_type": product_type,
            "target_date": target_date.isoformat(),
            "recommendation": recommendation,
            "priority": priority,
            "confidence": confidence.value,
            "reasoning": reasoning,
            "conditions": {
                "temperature": f"{temp}F (range: {SPRAY_TIMING['min_temp']}-{SPRAY_TIMING['max_temp']}F)",
                "wind": f"{wind} mph (max: {SPRAY_TIMING['max_wind']} mph)",
                "humidity": f"{humidity}%",
                "rain_free_hours": rain_hours
            },
            "optimal_conditions": SPRAY_TIMING
        }

    def get_harvest_recommendation(
        self,
        field_id: str,
        field_name: str,
        crop: str,
        current_moisture: float,
        weather_forecast: Dict[str, Any],  # {rain_days, avg_temp, frost_risk}
        price_trend: str = "stable"  # "rising", "falling", "stable"
    ) -> Dict[str, Any]:
        """Get AI recommendation for harvest timing"""
        rec_id = self._next_id("recommendation")

        # Target moisture levels
        target_moisture = {
            "corn": 15.5,
            "soybeans": 13.0,
            "wheat": 13.5,
            "rice": 12.5
        }.get(crop, 15.0)

        dry_discount_per_point = {
            "corn": 0.015,  # 1.5 cents per point per bushel
            "soybeans": 0.02
        }.get(crop, 0.02)

        reasoning = []
        priority = "medium"
        recommendation = ""
        confidence = ConfidenceLevel.MEDIUM

        moisture_diff = current_moisture - target_moisture

        # Moisture analysis
        if moisture_diff > 5:
            reasoning.append(f"Moisture ({current_moisture}%) well above target - significant dry cost")
            recommendation = "WAIT - Too wet to harvest efficiently"
        elif moisture_diff > 2:
            reasoning.append(f"Moisture ({current_moisture}%) above target - drying cost applies")
            if weather_forecast.get("rain_days", 0) > 2:
                reasoning.append("Rain in forecast - consider harvesting to avoid delays")
                recommendation = "HARVEST - Beat the rain"
                priority = "high"
        elif moisture_diff >= 0:
            reasoning.append(f"Moisture ({current_moisture}%) near target")
            recommendation = "GO - Good harvest conditions"
            confidence = ConfidenceLevel.HIGH
        else:
            reasoning.append(f"Moisture ({current_moisture}%) below target - possible field losses")
            recommendation = "HARVEST NOW - Minimize shatter losses"
            priority = "high"

        # Weather factors
        rain_days = weather_forecast.get("rain_days", 0)
        if rain_days > 3:
            reasoning.append(f"{rain_days} days with rain in forecast - harvest window limited")
            priority = "high"

        frost_risk = weather_forecast.get("frost_risk", False)
        if frost_risk:
            reasoning.append("Frost risk - monitor crop closely")
            if crop in ["soybeans", "cotton"]:
                priority = "high"

        # Price factors
        if price_trend == "falling":
            reasoning.append("Prices trending down - consider harvesting and selling")
        elif price_trend == "rising":
            reasoning.append("Prices trending up - consider storage after harvest")

        # Calculate drying costs
        drying_cost_per_bu = max(0, moisture_diff * 0.04) if moisture_diff > 0 else 0  # ~4 cents per point

        economic_impact = {
            "moisture_vs_target": f"{moisture_diff:+.1f}%",
            "estimated_drying_cost": f"${drying_cost_per_bu:.2f}/bu" if drying_cost_per_bu > 0 else "None",
            "price_trend": price_trend
        }

        if not recommendation:
            recommendation = "MONITOR - Conditions acceptable"

        return {
            "id": rec_id,
            "field_name": field_name,
            "crop": crop,
            "recommendation": recommendation,
            "priority": priority,
            "confidence": confidence.value,
            "reasoning": reasoning,
            "moisture_analysis": {
                "current": f"{current_moisture}%",
                "target": f"{target_moisture}%",
                "difference": f"{moisture_diff:+.1f}%"
            },
            "weather_factors": weather_forecast,
            "economic_impact": economic_impact
        }

    def get_recommendation_types(self) -> Dict[str, Any]:
        """Get available recommendation types"""
        return {
            "types": [
                {"id": t.value, "name": t.value.title()}
                for t in RecommendationType
            ]
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_precision_intelligence_service: Optional[PrecisionIntelligenceService] = None


def get_precision_intelligence_service() -> PrecisionIntelligenceService:
    """Get or create the precision intelligence service singleton"""
    global _precision_intelligence_service
    if _precision_intelligence_service is None:
        _precision_intelligence_service = PrecisionIntelligenceService()
    return _precision_intelligence_service
