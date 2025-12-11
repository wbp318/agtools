"""
AgTools Calculation Engines

Offline calculation implementations for:
- Economic thresholds
- Yield response curves
- Spray timing evaluation
- Cost estimates
"""

from core.calculations.yield_response import (
    OfflineYieldCalculator,
    get_offline_yield_calculator,
    EORResult,
    YieldCurveResult,
    YieldPoint,
    ResponseModel,
    SoilTestLevel,
    DEFAULT_CROP_PARAMETERS,
    PREVIOUS_CROP_N_CREDITS
)

from core.calculations.spray_timing import (
    OfflineSprayCalculator,
    get_offline_spray_calculator,
    SprayEvaluation,
    ConditionAssessment,
    WeatherCondition,
    RiskLevel,
    SprayType,
    SPRAY_THRESHOLDS
)

__all__ = [
    # Yield Response
    "OfflineYieldCalculator",
    "get_offline_yield_calculator",
    "EORResult",
    "YieldCurveResult",
    "YieldPoint",
    "ResponseModel",
    "SoilTestLevel",
    "DEFAULT_CROP_PARAMETERS",
    "PREVIOUS_CROP_N_CREDITS",
    # Spray Timing
    "OfflineSprayCalculator",
    "get_offline_spray_calculator",
    "SprayEvaluation",
    "ConditionAssessment",
    "WeatherCondition",
    "RiskLevel",
    "SprayType",
    "SPRAY_THRESHOLDS",
]
