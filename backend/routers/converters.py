"""
Measurement Converter API Router

Provides endpoints for imperial to metric conversions
for agricultural spray applications.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.measurement_converter_service import (
    get_measurement_converter_service
)


router = APIRouter(prefix="/api/v1/convert", tags=["Measurement Converter"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class SprayRateConversionRequest(BaseModel):
    """Request to convert a spray application rate."""
    value: float = Field(..., description="Numeric value to convert", gt=0)
    unit: str = Field(
        ...,
        description="Unit of the value (gal_per_acre, fl_oz_per_acre, pt_per_acre, qt_per_acre, lb_per_acre, oz_per_acre)"
    )


class RateStringConversionRequest(BaseModel):
    """Request to convert a rate string like '32 fl oz/acre'."""
    rate_string: str = Field(..., description="Rate string to parse and convert, e.g., '32 fl oz/acre'")


class VolumeConversionRequest(BaseModel):
    """Request to convert a volume."""
    value: float = Field(..., description="Volume value to convert", gt=0)
    unit: str = Field(..., description="Unit (gal, fl_oz, qt, pt)")


class WeightConversionRequest(BaseModel):
    """Request to convert a weight."""
    value: float = Field(..., description="Weight value to convert", gt=0)
    unit: str = Field(..., description="Unit (lb, oz)")


class SimpleConversionRequest(BaseModel):
    """Request for simple conversions (area, speed, pressure, temperature)."""
    value: float = Field(..., description="Value to convert")


class TankMixRequest(BaseModel):
    """Request to calculate tank mix amounts."""
    tank_size_liters: float = Field(..., description="Tank size in liters", gt=0)
    application_rate_l_per_ha: float = Field(..., description="Carrier application rate in L/ha", gt=0)
    field_size_ha: float = Field(..., description="Field size in hectares", gt=0)
    product_rate_l_per_ha: Optional[float] = Field(None, description="Product rate in L/ha", gt=0)


class TankMixImperialRequest(BaseModel):
    """Request to calculate tank mix from imperial inputs."""
    tank_size_gallons: float = Field(..., description="Tank size in gallons", gt=0)
    application_rate_gpa: float = Field(..., description="Gallons per acre", gt=0)
    field_size_acres: float = Field(..., description="Field size in acres", gt=0)
    product_rate_per_acre: Optional[float] = Field(None, description="Product rate per acre", gt=0)
    product_unit: str = Field("fl_oz", description="Product unit (fl_oz, pt, qt, gal)")


class BatchConversionRequest(BaseModel):
    """Request to convert multiple values."""
    conversions: List[Dict[str, Any]] = Field(
        ...,
        description="List of conversion requests, each with 'value' and 'unit'"
    )


class RecommendationConversionRequest(BaseModel):
    """Request to convert an AgTools recommendation."""
    recommendation: Dict[str, Any] = Field(..., description="AgTools recommendation object")


class ConversionResponse(BaseModel):
    """Standard conversion response."""
    imperial_value: float
    imperial_unit: str
    imperial_display: str
    metric_value: float
    metric_unit: str
    metric_display: str


class TankMixResponse(BaseModel):
    """Tank mix calculation response."""
    tank_size_liters: float
    application_rate_l_per_ha: float
    field_size_ha: float
    product_per_tank_liters: float
    tanks_needed: int
    coverage_per_tank_ha: float
    total_product_needed_liters: float
    leftover_liters: float


class ServiceSummaryResponse(BaseModel):
    """Service capabilities summary."""
    supported_rate_units: List[str]
    supported_volume_units: List[str]
    supported_weight_units: List[str]
    product_categories: List[str]
    total_reference_products: int
    conversion_constants: Dict[str, float]


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/summary", response_model=ServiceSummaryResponse)
async def get_converter_summary():
    """Get a summary of the converter service capabilities."""
    service = get_measurement_converter_service()
    return service.get_service_summary()


@router.post("/spray-rate", response_model=ConversionResponse)
async def convert_spray_rate(request: SprayRateConversionRequest):
    """
    Convert a spray application rate from imperial to metric.

    Supported units:
    - gal_per_acre: Gallons per acre -> L/ha
    - fl_oz_per_acre: Fluid ounces per acre -> mL/ha or L/ha
    - pt_per_acre: Pints per acre -> L/ha
    - qt_per_acre: Quarts per acre -> L/ha
    - lb_per_acre: Pounds per acre -> kg/ha
    - oz_per_acre: Ounces per acre -> g/ha or kg/ha
    """
    service = get_measurement_converter_service()
    try:
        result = service.convert_spray_rate(request.value, request.unit)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rate-string", response_model=ConversionResponse)
async def convert_rate_string(request: RateStringConversionRequest):
    """
    Parse and convert a rate string like '32 fl oz/acre' to metric.

    Supports formats like:
    - "32 fl oz/acre"
    - "2 pt/acre"
    - "1.5 lb/acre"
    - "1 qt/ac"
    """
    service = get_measurement_converter_service()
    try:
        result = service.convert_rate_string(request.rate_string)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/volume", response_model=ConversionResponse)
async def convert_volume(request: VolumeConversionRequest):
    """Convert a volume from imperial to metric."""
    service = get_measurement_converter_service()
    try:
        result = service.convert_volume(request.value, request.unit)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/weight", response_model=ConversionResponse)
async def convert_weight(request: WeightConversionRequest):
    """Convert a weight from imperial to metric."""
    service = get_measurement_converter_service()
    try:
        result = service.convert_weight(request.value, request.unit)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/area", response_model=ConversionResponse)
async def convert_area(request: SimpleConversionRequest):
    """Convert acres to hectares."""
    service = get_measurement_converter_service()
    return service.convert_area(request.value)


@router.post("/speed", response_model=ConversionResponse)
async def convert_speed(request: SimpleConversionRequest):
    """Convert mph to km/h."""
    service = get_measurement_converter_service()
    return service.convert_speed(request.value)


@router.post("/pressure", response_model=ConversionResponse)
async def convert_pressure(request: SimpleConversionRequest):
    """Convert PSI to bar."""
    service = get_measurement_converter_service()
    return service.convert_pressure(request.value)


@router.post("/temperature", response_model=ConversionResponse)
async def convert_temperature(request: SimpleConversionRequest):
    """Convert Fahrenheit to Celsius."""
    service = get_measurement_converter_service()
    return service.convert_temperature(request.value)


@router.post("/tank-mix", response_model=TankMixResponse)
async def calculate_tank_mix(request: TankMixRequest):
    """
    Calculate tank mix amounts for a spray application.

    Given tank size, application rate, and field size (all in metric),
    calculates how much product per tank and how many tanks needed.
    """
    service = get_measurement_converter_service()
    try:
        result = service.calculate_tank_mix(
            request.tank_size_liters,
            request.application_rate_l_per_ha,
            request.field_size_ha,
            request.product_rate_l_per_ha
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tank-mix-imperial")
async def calculate_tank_mix_imperial(request: TankMixImperialRequest):
    """
    Calculate tank mix from imperial inputs, returning both unit systems.

    Takes gallons, acres, etc. and returns calculations in both
    imperial and metric.
    """
    service = get_measurement_converter_service()
    try:
        result = service.calculate_tank_mix_imperial(
            request.tank_size_gallons,
            request.application_rate_gpa,
            request.field_size_acres,
            request.product_rate_per_acre,
            request.product_unit
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reference-products")
async def get_reference_products(
    category: Optional[str] = Query(None, description="Filter by category (herbicide, fungicide, insecticide, adjuvant)"),
    search: Optional[str] = Query(None, description="Search by product name or active ingredient")
):
    """
    Get reference products with application rates in both imperial and metric.

    Returns common agricultural chemicals with their typical rates.
    """
    service = get_measurement_converter_service()
    return service.get_reference_products(category, search)


@router.post("/batch")
async def batch_convert(request: BatchConversionRequest):
    """
    Convert multiple values in a single request.

    Each item in the conversions list should have:
    - value: The numeric value
    - unit: The unit (gal_per_acre, fl_oz_per_acre, etc.)
    """
    service = get_measurement_converter_service()
    return {"results": service.batch_convert(request.conversions)}


@router.post("/recommendation")
async def convert_recommendation(request: RecommendationConversionRequest):
    """
    Convert an AgTools spray recommendation, adding metric equivalents.

    Takes a recommendation object and adds _metric versions of all rate fields.
    """
    service = get_measurement_converter_service()
    return service.convert_recommendation(request.recommendation)
