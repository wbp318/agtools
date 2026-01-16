"""
Farm Business Router
AgTools v6.13.0

Handles:
- Entity management
- Labor management
- Land/lease management
- Cash flow management
- Market intelligence
- Research/field trials
"""

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from middleware.auth_middleware import get_current_active_user, require_manager, AuthenticatedUser

router = APIRouter(prefix="/api/v1", tags=["Farm Business"])


# ============================================================================
# ENTITY MANAGEMENT
# ============================================================================

@router.get("/entities", tags=["Entities"])
async def list_entities(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List farm entities."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    return service.list_entities()


@router.post("/entities", tags=["Entities"])
async def create_entity(
    name: str,
    entity_type: str,
    tax_id: Optional[str] = None,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Create a new entity."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    result = service.create_entity(
        name=name,
        entity_type=entity_type,
        tax_id=tax_id,
        created_by=user.id
    )

    return result


@router.get("/entities/{entity_id}", tags=["Entities"])
async def get_entity(
    entity_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get entity details."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    entity = service.get_entity(entity_id)

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return entity


# ============================================================================
# LABOR MANAGEMENT
# ============================================================================

@router.get("/labor/employees", tags=["Labor"])
async def list_employees(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List employees."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    return service.list_employees(status=status)


@router.post("/labor/employees", tags=["Labor"])
async def create_employee(
    first_name: str,
    last_name: str,
    employee_type: str,
    pay_type: str,
    pay_rate: float,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Create a new employee record."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    result = service.create_employee(
        first_name=first_name,
        last_name=last_name,
        employee_type=employee_type,
        pay_type=pay_type,
        pay_rate=pay_rate,
        created_by=user.id
    )

    return result


@router.get("/labor/time-entries", tags=["Labor"])
async def list_time_entries(
    employee_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List time entries."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    return service.list_time_entries(
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to
    )


@router.post("/labor/time-entries", tags=["Labor"])
async def create_time_entry(
    employee_id: int,
    work_date: date,
    hours: float,
    description: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a time entry."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    result = service.create_time_entry(
        employee_id=employee_id,
        work_date=work_date,
        hours=hours,
        description=description,
        created_by=user.id
    )

    return result


# ============================================================================
# LAND/LEASE MANAGEMENT
# ============================================================================

@router.get("/land/leases", tags=["Land"])
async def list_leases(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List land leases."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    return service.list_leases(status=status)


@router.post("/land/leases", tags=["Land"])
async def create_lease(
    landlord_name: str,
    acres: float,
    lease_type: str,
    annual_rent: float,
    start_date: date,
    end_date: date,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Create a new lease."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    result = service.create_lease(
        landlord_name=landlord_name,
        acres=acres,
        lease_type=lease_type,
        annual_rent=annual_rent,
        start_date=start_date,
        end_date=end_date,
        created_by=user.id
    )

    return result


@router.get("/land/leases/{lease_id}", tags=["Land"])
async def get_lease(
    lease_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get lease details."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    lease = service.get_lease(lease_id)

    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    return lease


# ============================================================================
# CASH FLOW MANAGEMENT
# ============================================================================

@router.get("/cashflow/transactions", tags=["Cash Flow"])
async def list_cash_transactions(
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List cash flow transactions."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    return service.list_cash_transactions(
        category=category,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/cashflow/summary", tags=["Cash Flow"])
async def get_cash_flow_summary(
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get cash flow summary."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    return service.get_cash_flow_summary(year=year)


@router.get("/cashflow/forecast", tags=["Cash Flow"])
async def get_cash_flow_forecast(
    months_ahead: int = 12,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get cash flow forecast."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    return service.get_cash_flow_forecast(months_ahead=months_ahead)


# ============================================================================
# MARKET INTELLIGENCE
# ============================================================================

@router.get("/market/prices", tags=["Market"])
async def get_market_prices(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get current commodity prices."""
    from services.farm_intelligence_service import get_farm_intelligence_service, CURRENT_PRICES

    return {"prices": CURRENT_PRICES}


@router.get("/market/contracts", tags=["Market"])
async def list_marketing_contracts(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List marketing contracts."""
    from services.farm_intelligence_service import get_farm_intelligence_service

    service = get_farm_intelligence_service()
    return service.list_contracts(status=status)


@router.get("/market/insurance-rates", tags=["Market"])
async def get_insurance_rates(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get crop insurance rates."""
    from services.farm_intelligence_service import INSURANCE_RATES

    return {"rates": INSURANCE_RATES}


# ============================================================================
# RESEARCH/FIELD TRIALS
# ============================================================================

@router.get("/research/trials", tags=["Research"])
async def list_trials(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List field trials."""
    from services.research_service import get_research_service

    service = get_research_service()
    return service.list_trials(status=status)


@router.post("/research/trials", tags=["Research"])
async def create_trial(
    name: str,
    trial_type: str,
    field_id: int,
    start_date: date,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new field trial."""
    from services.research_service import get_research_service

    service = get_research_service()
    result = service.create_trial(
        name=name,
        trial_type=trial_type,
        field_id=field_id,
        start_date=start_date,
        created_by=user.id
    )

    return result


@router.get("/research/trials/{trial_id}", tags=["Research"])
async def get_trial(
    trial_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get trial details with treatments and measurements."""
    from services.research_service import get_research_service

    service = get_research_service()
    trial = service.get_trial(trial_id)

    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    return trial


@router.get("/research/trials/{trial_id}/analysis", tags=["Research"])
async def get_trial_analysis(
    trial_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get statistical analysis for a trial."""
    from services.research_service import get_research_service

    service = get_research_service()
    return service.get_trial_analysis(trial_id)
