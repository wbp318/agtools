"""
Spray Timing Data Models

Data classes for spray timing evaluation and recommendations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime


class SprayType(str, Enum):
    """Types of spray applications."""
    HERBICIDE = "herbicide"
    INSECTICIDE = "insecticide"
    FUNGICIDE = "fungicide"
    GROWTH_REGULATOR = "growth_regulator"
    DESICCANT = "desiccant"


class RiskLevel(str, Enum):
    """Spray condition risk levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    MARGINAL = "marginal"
    POOR = "poor"
    DO_NOT_SPRAY = "do_not_spray"


class DiseasePressure(str, Enum):
    """Disease pressure levels."""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


@dataclass
class WeatherCondition:
    """Weather conditions for spray timing evaluation."""
    datetime_str: str = ""
    temp_f: float = 75.0
    humidity_pct: float = 50.0
    wind_mph: float = 5.0
    wind_direction: str = "N"
    precip_chance_pct: float = 0.0
    precip_amount_in: float = 0.0
    cloud_cover_pct: float = 30.0
    dew_point_f: float = 55.0

    def to_dict(self) -> dict:
        """Convert to dictionary for API request."""
        return {
            "datetime": self.datetime_str or datetime.now().isoformat(),
            "temp_f": self.temp_f,
            "humidity_pct": self.humidity_pct,
            "wind_mph": self.wind_mph,
            "wind_direction": self.wind_direction,
            "precip_chance_pct": self.precip_chance_pct,
            "precip_amount_in": self.precip_amount_in,
            "cloud_cover_pct": self.cloud_cover_pct,
            "dew_point_f": self.dew_point_f,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WeatherCondition":
        return cls(
            datetime_str=data.get("datetime", ""),
            temp_f=data.get("temp_f", 75),
            humidity_pct=data.get("humidity_pct", 50),
            wind_mph=data.get("wind_mph", 5),
            wind_direction=data.get("wind_direction", "N"),
            precip_chance_pct=data.get("precip_chance_pct", 0),
            precip_amount_in=data.get("precip_amount_in", 0),
            cloud_cover_pct=data.get("cloud_cover_pct", 30),
            dew_point_f=data.get("dew_point_f", 55),
        )


@dataclass
class EvaluateConditionsRequest:
    """Request for evaluating current spray conditions."""
    weather: WeatherCondition = field(default_factory=WeatherCondition)
    spray_type: str = "herbicide"
    product_name: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "weather": self.weather.to_dict(),
            "spray_type": self.spray_type,
            "product_name": self.product_name,
        }


@dataclass
class ConditionAssessment:
    """Assessment of a single weather factor."""
    factor: str
    status: str  # "suitable", "marginal", "unsuitable"
    value: float
    message: str = ""


@dataclass
class SprayEvaluation:
    """Result of spray condition evaluation."""
    risk_level: str
    overall_score: float  # 0-100
    conditions: List[ConditionAssessment]
    concerns: List[str]
    recommendations: List[str]
    can_spray: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "SprayEvaluation":
        evaluation = data.get("evaluation", data)

        conditions = []
        conditions_data = evaluation.get("conditions_assessment", {})
        for factor, assessment in conditions_data.items():
            if isinstance(assessment, dict):
                conditions.append(ConditionAssessment(
                    factor=factor,
                    status=assessment.get("status", "unknown"),
                    value=assessment.get("value", 0),
                    message=assessment.get("message", ""),
                ))

        risk = evaluation.get("risk_level", "unknown")

        return cls(
            risk_level=risk,
            overall_score=evaluation.get("overall_score", 0),
            conditions=conditions,
            concerns=evaluation.get("concerns", []),
            recommendations=evaluation.get("recommendations", []),
            can_spray=risk not in ["poor", "do_not_spray"],
        )


@dataclass
class SprayWindow:
    """A suitable time window for spraying."""
    start_time: str
    end_time: str
    duration_hours: float
    quality_rating: float
    risk_level: str
    benefits: List[str]
    concerns: List[str]


@dataclass
class FindWindowsRequest:
    """Request for finding spray windows in a forecast."""
    forecast: List[WeatherCondition] = field(default_factory=list)
    spray_type: str = "herbicide"
    min_window_hours: float = 3.0
    product_name: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "forecast": [w.to_dict() for w in self.forecast],
            "spray_type": self.spray_type,
            "min_window_hours": self.min_window_hours,
            "product_name": self.product_name,
        }


@dataclass
class FindWindowsResponse:
    """Response with available spray windows."""
    windows: List[SprayWindow]
    best_window: Optional[SprayWindow] = None
    total_hours_available: float = 0

    @classmethod
    def from_dict(cls, data: dict) -> "FindWindowsResponse":
        windows = []
        for w in data.get("spray_windows", []):
            windows.append(SprayWindow(
                start_time=w.get("window_start", ""),
                end_time=w.get("window_end", ""),
                duration_hours=w.get("duration_hours", 0),
                quality_rating=w.get("quality_rating", 0),
                risk_level=w.get("risk_level", "unknown"),
                benefits=w.get("key_benefits", []),
                concerns=w.get("concerns", []),
            ))

        best = None
        if windows:
            best = max(windows, key=lambda w: w.quality_rating)

        total_hours = sum(w.duration_hours for w in windows)

        return cls(
            windows=windows,
            best_window=best,
            total_hours_available=total_hours,
        )


@dataclass
class CostOfWaitingRequest:
    """Request for cost of waiting analysis."""
    current_conditions: WeatherCondition = field(default_factory=WeatherCondition)
    forecast: List[WeatherCondition] = field(default_factory=list)
    spray_type: str = "fungicide"
    acres: float = 160
    product_cost_per_acre: float = 20.0
    application_cost_per_acre: float = 8.50
    target_pest_or_disease: str = ""
    current_pressure: str = "moderate"
    crop: str = "corn"
    yield_goal: float = 200
    grain_price: float = 4.50

    def to_dict(self) -> dict:
        return {
            "current_conditions": self.current_conditions.to_dict(),
            "forecast": [w.to_dict() for w in self.forecast],
            "spray_type": self.spray_type,
            "acres": self.acres,
            "product_cost_per_acre": self.product_cost_per_acre,
            "application_cost_per_acre": self.application_cost_per_acre,
            "target_pest_or_disease": self.target_pest_or_disease,
            "current_pressure": self.current_pressure,
            "crop": self.crop,
            "yield_goal": self.yield_goal,
            "grain_price": self.grain_price,
        }


@dataclass
class CostOfWaitingResult:
    """Result of cost of waiting analysis."""
    recommendation: str  # "SPRAY NOW", "WAIT", "SPRAY NOW (with caution)"
    reasoning: str
    cost_to_spray_now: float
    cost_to_wait: float
    yield_loss_risk: float
    efficacy_risk: float
    action_items: List[str]
    spray_now_analysis: Dict
    wait_analysis: Dict

    @classmethod
    def from_dict(cls, data: dict) -> "CostOfWaitingResult":
        spray_now = data.get("spray_now_analysis", {})
        economic = data.get("economic_analysis", {})

        return cls(
            recommendation=data.get("recommendation", ""),
            reasoning=data.get("reasoning", ""),
            cost_to_spray_now=economic.get("cost_to_spray_now", spray_now.get("application_cost", 0)),
            cost_to_wait=economic.get("cost_to_wait", 0),
            yield_loss_risk=data.get("yield_loss_risk", 0),
            efficacy_risk=spray_now.get("expected_efficacy", 1.0),
            action_items=data.get("action_items", []),
            spray_now_analysis=spray_now,
            wait_analysis=data.get("spray_in_3_days_analysis", data.get("wait_analysis", {})),
        )


@dataclass
class DiseasePressureRequest:
    """Request for disease pressure assessment."""
    weather_history: List[WeatherCondition] = field(default_factory=list)
    crop: str = "corn"
    growth_stage: str = "VT"

    def to_dict(self) -> dict:
        return {
            "weather_history": [w.to_dict() for w in self.weather_history],
            "crop": self.crop,
            "growth_stage": self.growth_stage,
        }


@dataclass
class DiseaseRisk:
    """Risk assessment for a single disease."""
    disease_name: str
    risk_level: str  # minimal, low, moderate, high, severe
    contributing_factors: List[str]
    recommendation: str


@dataclass
class DiseasePressureResponse:
    """Response with disease pressure assessment."""
    risks: List[DiseaseRisk]
    highest_risk_disease: Optional[str] = None
    overall_pressure: str = "low"

    @classmethod
    def from_dict(cls, data: dict) -> "DiseasePressureResponse":
        risks = []
        risk_data = data.get("disease_risk_assessment", data.get("risks", {}))

        if isinstance(risk_data, dict):
            for disease, assessment in risk_data.items():
                if isinstance(assessment, dict):
                    risks.append(DiseaseRisk(
                        disease_name=disease,
                        risk_level=assessment.get("risk_level", "unknown"),
                        contributing_factors=assessment.get("contributing_factors", []),
                        recommendation=assessment.get("recommendation", ""),
                    ))

        # Find highest risk
        highest = None
        risk_order = ["minimal", "low", "moderate", "high", "severe"]
        max_risk_idx = -1

        for risk in risks:
            try:
                idx = risk_order.index(risk.risk_level.lower())
                if idx > max_risk_idx:
                    max_risk_idx = idx
                    highest = risk.disease_name
            except ValueError:
                pass

        overall = risk_order[max_risk_idx] if max_risk_idx >= 0 else "low"

        return cls(
            risks=risks,
            highest_risk_disease=highest,
            overall_pressure=overall,
        )


@dataclass
class GrowthStageTimingResponse:
    """Response for growth stage timing guidance."""
    timing_recommendation: str
    considerations: List[str]
    suggested_products: List[str]
    growth_stage: str
    crop: str
    spray_type: str

    @classmethod
    def from_dict(cls, data: dict) -> "GrowthStageTimingResponse":
        return cls(
            timing_recommendation=data.get("timing_recommendation", ""),
            considerations=data.get("considerations", []),
            suggested_products=data.get("suggested_products", []),
            growth_stage=data.get("growth_stage", ""),
            crop=data.get("crop", ""),
            spray_type=data.get("spray_type", ""),
        )
