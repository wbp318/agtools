"""
Sustainability Router
AgTools v6.13.2

Handles:
- Sustainability metrics and scorecards
- Carbon tracking
- Water usage tracking
- Climate/GDD data
- Conservation practices
"""

from typing import Optional
from datetime import date

from fastapi import APIRouter, HTTPException, Depends, Request

from middleware.auth_middleware import get_current_active_user, AuthenticatedUser
from middleware.rate_limiter import limiter, RATE_MODERATE
from services.sustainability_service import (
    get_sustainability_service,
    InputCategory,
    CarbonSource,
    SustainabilityPractice,
    InputUsageCreate,
    InputUsageResponse,
    CarbonEntryCreate,
    CarbonEntryResponse,
    WaterUsageCreate,
    WaterUsageResponse,
    PracticeRecordCreate,
    PracticeRecordResponse,
    SustainabilityScorecard,
    SustainabilityReport
)
from services.climate_service import (
    get_climate_service,
    GDDRecordCreate,
    GDDRecordResponse,
    PrecipitationCreate,
    PrecipitationResponse,
    ClimateSummary
)

router = APIRouter(prefix="/api/v1", tags=["Sustainability"])


# ============================================================================
# INPUT USAGE TRACKING
# ============================================================================

@router.get("/sustainability/inputs", tags=["Sustainability"])
async def list_input_usage(
    field_id: Optional[int] = None,
    category: Optional[InputCategory] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List input usage records."""
    service = get_sustainability_service()
    return service.list_input_usage(
        field_id=field_id,
        category=category,
        date_from=date_from,
        date_to=date_to
    )


@router.post("/sustainability/inputs", response_model=InputUsageResponse, tags=["Sustainability"])
@limiter.limit(RATE_MODERATE)
async def record_input_usage(
    request: Request,
    input_data: InputUsageCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Record input usage (fertilizer, pesticide, etc.). Rate limited: 30/minute."""
    service = get_sustainability_service()
    result, error = service.record_input_usage(input_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


# ============================================================================
# CARBON TRACKING
# ============================================================================

@router.get("/sustainability/carbon", tags=["Sustainability"])
async def list_carbon_entries(
    field_id: Optional[int] = None,
    source: Optional[CarbonSource] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List carbon footprint entries."""
    service = get_sustainability_service()
    return service.list_carbon_entries(
        field_id=field_id,
        source=source,
        date_from=date_from,
        date_to=date_to
    )


@router.post("/sustainability/carbon", response_model=CarbonEntryResponse, tags=["Sustainability"])
@limiter.limit(RATE_MODERATE)
async def record_carbon_entry(
    request: Request,
    carbon_data: CarbonEntryCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Record carbon footprint entry. Rate limited: 30/minute."""
    service = get_sustainability_service()
    result, error = service.record_carbon_entry(carbon_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


# ============================================================================
# WATER USAGE
# ============================================================================

@router.get("/sustainability/water", tags=["Sustainability"])
async def list_water_usage(
    field_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List water usage records."""
    service = get_sustainability_service()
    return service.list_water_usage(
        field_id=field_id,
        date_from=date_from,
        date_to=date_to
    )


@router.post("/sustainability/water", response_model=WaterUsageResponse, tags=["Sustainability"])
@limiter.limit(RATE_MODERATE)
async def record_water_usage(
    request: Request,
    water_data: WaterUsageCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Record water usage. Rate limited: 30/minute."""
    service = get_sustainability_service()
    result, error = service.record_water_usage(water_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


# ============================================================================
# CONSERVATION PRACTICES
# ============================================================================

@router.get("/sustainability/practices", tags=["Sustainability"])
async def list_practices(
    field_id: Optional[int] = None,
    practice: Optional[SustainabilityPractice] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List conservation practice records."""
    service = get_sustainability_service()
    return service.list_practices(
        field_id=field_id,
        practice=practice
    )


@router.post("/sustainability/practices", response_model=PracticeRecordResponse, tags=["Sustainability"])
@limiter.limit(RATE_MODERATE)
async def record_practice(
    request: Request,
    practice_data: PracticeRecordCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Record a conservation practice. Rate limited: 30/minute."""
    service = get_sustainability_service()
    result, error = service.record_practice(practice_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


# ============================================================================
# SCORECARDS AND REPORTS
# ============================================================================

@router.get("/sustainability/scorecard", response_model=SustainabilityScorecard, tags=["Sustainability"])
async def get_sustainability_scorecard(
    field_id: Optional[int] = None,
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get sustainability scorecard."""
    service = get_sustainability_service()
    return service.get_scorecard(field_id=field_id, year=year)


@router.get("/sustainability/report", response_model=SustainabilityReport, tags=["Sustainability"])
async def get_sustainability_report(
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get comprehensive sustainability report."""
    service = get_sustainability_service()
    return service.get_report(year=year)


# ============================================================================
# CLIMATE/GDD TRACKING
# ============================================================================

@router.get("/climate/gdd", tags=["Climate"])
async def list_gdd_records(
    field_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List GDD (Growing Degree Day) records."""
    service = get_climate_service()
    return service.list_gdd_records(
        field_id=field_id,
        date_from=date_from,
        date_to=date_to
    )


@router.post("/climate/gdd", response_model=GDDRecordResponse, tags=["Climate"])
@limiter.limit(RATE_MODERATE)
async def record_gdd(
    request: Request,
    gdd_data: GDDRecordCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Record GDD data. Rate limited: 30/minute."""
    service = get_climate_service()
    result, error = service.record_gdd(gdd_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@router.get("/climate/gdd/accumulated", tags=["Climate"])
async def get_accumulated_gdd(
    field_id: int,
    crop_type: str,
    planting_date: date,
    end_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get accumulated GDD and growth stage estimate from planting date."""
    service = get_climate_service()
    accumulated, entries = service.get_accumulated_gdd(field_id, crop_type, planting_date, end_date)
    return {
        "accumulated": accumulated,
        "total_gdd": accumulated,
        "entries_count": len(entries),
        "field_id": field_id,
        "crop_type": crop_type,
        "planting_date": planting_date.isoformat(),
        "end_date": (end_date or date.today()).isoformat()
    }


@router.get("/climate/gdd/summary", tags=["Climate"])
async def get_gdd_summary(
    field_id: int,
    crop_type: str,
    planting_date: date,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get GDD summary with crop stage predictions for a specific field."""
    service = get_climate_service()
    return service.get_gdd_summary(field_id, crop_type, planting_date)


# ============================================================================
# PRECIPITATION
# ============================================================================

@router.get("/climate/precipitation", tags=["Climate"])
async def list_precipitation(
    field_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List precipitation records."""
    service = get_climate_service()
    return service.list_precipitation(
        field_id=field_id,
        date_from=date_from,
        date_to=date_to
    )


@router.post("/climate/precipitation", response_model=PrecipitationResponse, tags=["Climate"])
@limiter.limit(RATE_MODERATE)
async def record_precipitation(
    request: Request,
    precip_data: PrecipitationCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Record precipitation data. Rate limited: 30/minute."""
    service = get_climate_service()
    result, error = service.record_precipitation(precip_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@router.get("/climate/summary", response_model=ClimateSummary, tags=["Climate"])
async def get_climate_summary(
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get climate summary for the season."""
    service = get_climate_service()
    return service.get_climate_summary(year=year)
