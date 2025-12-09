"""
AgTools Data Models Package

Dataclasses and type definitions for API responses.
"""

from .yield_response import (
    Crop,
    Nutrient,
    SoilTestLevel,
    ResponseModel,
    YieldCurvePoint,
    YieldCurveRequest,
    YieldCurveResponse,
    EORRequest,
    EORResult,
    RateComparison,
    CompareRatesRequest,
    CompareRatesResponse,
    PriceSensitivityRequest,
    PriceSensitivityCell,
    PriceSensitivityResponse,
    MultiNutrientRequest,
    MultiNutrientResult,
    PriceRatioGuide,
)

from .spray import (
    SprayType,
    RiskLevel,
    DiseasePressure,
    WeatherCondition,
    EvaluateConditionsRequest,
    ConditionAssessment,
    SprayEvaluation,
    SprayWindow,
    FindWindowsRequest,
    FindWindowsResponse,
    CostOfWaitingRequest,
    CostOfWaitingResult,
    DiseasePressureRequest,
    DiseaseRisk,
    DiseasePressureResponse,
    GrowthStageTimingResponse,
)

from .pricing import (
    ProductCategory,
    Region,
    PriceTrend,
    BuyRecommendation,
    ProductPrice,
    GetPricesResponse,
    SetPriceRequest,
    SetPriceResponse,
    BulkPriceUpdate,
    BulkUpdateRequest,
    BulkUpdateResponse,
    BuyRecommendationRequest,
    PriceAnalysis,
    BuyRecommendationResponse,
    InputCostItem,
    InputCostSummary,
    InputCostRequest,
    InputCostResponse,
    PriceAlert,
    PriceAlertsResponse,
    SupplierComparisonRequest,
    SupplierComparison,
    SupplierComparisonResponse,
)

__all__ = [
    # Yield Response
    "Crop", "Nutrient", "SoilTestLevel", "ResponseModel",
    "YieldCurvePoint", "YieldCurveRequest", "YieldCurveResponse",
    "EORRequest", "EORResult",
    "RateComparison", "CompareRatesRequest", "CompareRatesResponse",
    "PriceSensitivityRequest", "PriceSensitivityCell", "PriceSensitivityResponse",
    "MultiNutrientRequest", "MultiNutrientResult", "PriceRatioGuide",
    # Spray Timing
    "SprayType", "RiskLevel", "DiseasePressure",
    "WeatherCondition", "EvaluateConditionsRequest",
    "ConditionAssessment", "SprayEvaluation",
    "SprayWindow", "FindWindowsRequest", "FindWindowsResponse",
    "CostOfWaitingRequest", "CostOfWaitingResult",
    "DiseasePressureRequest", "DiseaseRisk", "DiseasePressureResponse",
    "GrowthStageTimingResponse",
    # Pricing
    "ProductCategory", "Region", "PriceTrend", "BuyRecommendation",
    "ProductPrice", "GetPricesResponse",
    "SetPriceRequest", "SetPriceResponse",
    "BulkPriceUpdate", "BulkUpdateRequest", "BulkUpdateResponse",
    "BuyRecommendationRequest", "PriceAnalysis", "BuyRecommendationResponse",
    "InputCostItem", "InputCostSummary", "InputCostRequest", "InputCostResponse",
    "PriceAlert", "PriceAlertsResponse",
    "SupplierComparisonRequest", "SupplierComparison", "SupplierComparisonResponse",
]
