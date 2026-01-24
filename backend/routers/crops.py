"""
Crops Router
AgTools v6.13.2

Handles:
- Seed and planting management
- Crop cost analysis
- Profitability analysis
"""

from typing import Optional
from datetime import date

from fastapi import APIRouter, HTTPException, Depends, Request

from middleware.auth_middleware import get_current_active_user, AuthenticatedUser
from middleware.rate_limiter import limiter, RATE_STANDARD, RATE_MODERATE
from services.crop_cost_analysis_service import (
    get_crop_cost_analysis_service,
    CropAnalysisSummary,
    FieldComparisonMatrix
)
from services.profitability_service import (
    get_profitability_service,
    BreakEvenRequest,
    BreakEvenResponse,
    InputROIRequest,
    InputROIResponse,
    ScenarioRequest,
    ScenarioResponse,
    BudgetTrackerRequest,
    BudgetTrackerResponse
)

router = APIRouter(prefix="/api/v1", tags=["Crops"])


# ============================================================================
# SEED & PLANTING MANAGEMENT
# ============================================================================

@router.get("/seeds", tags=["Seeds"])
async def list_seeds(
    crop_type: Optional[str] = None,
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List seed inventory."""
    from services.seed_planting_service import get_seed_planting_service

    service = get_seed_planting_service()
    # Note: year parameter kept for API compatibility but not used by service
    return service.list_seeds(crop_type=crop_type)


@router.post("/seeds", tags=["Seeds"])
async def create_seed_record(
    variety_name: str,
    crop_type: str,
    brand: Optional[str] = None,
    trait_package: Optional[str] = None,
    units_purchased: Optional[float] = None,
    cost_per_unit: Optional[float] = None,
    purchase_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a seed inventory record."""
    from services.seed_planting_service import get_seed_planting_service

    service = get_seed_planting_service()
    result = service.create_seed(
        variety_name=variety_name,
        crop_type=crop_type,
        brand=brand,
        trait_package=trait_package,
        units_purchased=units_purchased,
        cost_per_unit=cost_per_unit,
        purchase_date=purchase_date,
        created_by=user.id
    )

    return result


@router.get("/seeds/{seed_id}", tags=["Seeds"])
async def get_seed(
    seed_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get seed details."""
    from services.seed_planting_service import get_seed_planting_service

    service = get_seed_planting_service()
    seed = service.get_seed(seed_id)

    if not seed:
        raise HTTPException(status_code=404, detail="Seed not found")

    return seed


@router.get("/planting-records", tags=["Planting"])
async def list_planting_records(
    field_id: Optional[int] = None,
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List planting records."""
    from services.seed_planting_service import get_seed_planting_service

    service = get_seed_planting_service()
    return service.list_planting_records(field_id=field_id, year=year)


@router.post("/planting-records", tags=["Planting"])
async def create_planting_record(
    field_id: int,
    seed_id: int,
    planting_date: date,
    acres_planted: float,
    seeding_rate: Optional[float] = None,
    row_spacing: Optional[float] = None,
    planting_depth: Optional[float] = None,
    notes: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a planting record."""
    from services.seed_planting_service import get_seed_planting_service

    service = get_seed_planting_service()
    result = service.create_planting_record(
        field_id=field_id,
        seed_id=seed_id,
        planting_date=planting_date,
        acres_planted=acres_planted,
        seeding_rate=seeding_rate,
        row_spacing=row_spacing,
        planting_depth=planting_depth,
        notes=notes,
        created_by=user.id
    )

    return result


# ============================================================================
# CROP COST ANALYSIS
# ============================================================================

@router.get("/crop-analysis/summary", response_model=CropAnalysisSummary, tags=["Crop Analysis"])
@limiter.limit(RATE_STANDARD)
async def get_crop_analysis_summary(
    request: Request,
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get crop cost analysis summary. Rate limited: 60/minute."""
    service = get_crop_cost_analysis_service()
    return service.get_summary(crop_year=year or 2026)


@router.get("/crop-analysis/comparison", response_model=FieldComparisonMatrix, tags=["Crop Analysis"])
@limiter.limit(RATE_STANDARD)
async def get_field_comparison(
    request: Request,
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get field-by-field comparison. Rate limited: 60/minute."""
    service = get_crop_cost_analysis_service()
    return service.get_field_comparison(crop_year=year or 2026)


@router.get("/crop-analysis/crops", tags=["Crop Analysis"])
async def get_crop_comparison(
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get crop type comparison."""
    service = get_crop_cost_analysis_service()
    return service.get_crop_comparison(crop_year=year or 2026)


@router.get("/crop-analysis/crops/{crop_type}", tags=["Crop Analysis"])
async def get_crop_detail(
    crop_type: str,
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get detailed analysis for a specific crop."""
    service = get_crop_cost_analysis_service()
    return service.get_crop_detail(crop_type, crop_year=year or 2026)


@router.get("/crop-analysis/field/{field_id}/history", tags=["Crop Analysis"])
async def get_field_history(
    field_id: int,
    years: int = 5,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get multi-year history for a field."""
    service = get_crop_cost_analysis_service()
    return service.get_field_history(field_id, years=years)


@router.get("/crop-analysis/years", tags=["Crop Analysis"])
async def get_year_over_year(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get year-over-year comparison."""
    service = get_crop_cost_analysis_service()
    return service.get_year_over_year(start_year=start_year, end_year=end_year)


@router.get("/crop-analysis/roi", tags=["Crop Analysis"])
async def get_roi_analysis(
    group_by: str = "field",
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get ROI analysis."""
    service = get_crop_cost_analysis_service()
    return service.get_roi_breakdown(crop_year=year or 2026, group_by=group_by)


@router.get("/crop-analysis/trends", tags=["Crop Analysis"])
async def get_trend_data(
    metric: str = "cost_per_acre",
    years: int = 5,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get trend data for charting."""
    service = get_crop_cost_analysis_service()
    return service.get_trend_data(metric=metric, years=years)


# ============================================================================
# PROFITABILITY ANALYSIS
# ============================================================================

@router.post("/profitability/break-even", response_model=BreakEvenResponse, tags=["Profitability"])
@limiter.limit(RATE_MODERATE)
async def calculate_break_even(
    request: Request,
    break_even_request: BreakEvenRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Calculate break-even analysis. Rate limited: 30/minute."""
    service = get_profitability_service()
    return service.calculate_break_even(break_even_request)


@router.post("/profitability/input-roi", response_model=InputROIResponse, tags=["Profitability"])
async def calculate_input_roi(
    request: InputROIRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Calculate ROI for a specific input."""
    service = get_profitability_service()
    return service.calculate_input_roi(request)


@router.post("/profitability/scenario", response_model=ScenarioResponse, tags=["Profitability"])
async def run_scenario(
    request: ScenarioRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Run a what-if scenario analysis."""
    service = get_profitability_service()
    return service.run_scenario(request)


@router.post("/profitability/budget-tracker", response_model=BudgetTrackerResponse, tags=["Profitability"])
async def track_budget(
    request: BudgetTrackerRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Track budget vs actual."""
    service = get_profitability_service()
    return service.track_budget(request)


@router.get("/profitability/summary", tags=["Profitability"])
async def get_profitability_summary(
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get overall profitability summary."""
    # Return stub - service method not yet implemented
    return {
        "year": year or 2026,
        "message": "Profitability summary not yet implemented",
        "status": "pending"
    }
