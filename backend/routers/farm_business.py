"""
Farm Business Router
AgTools v6.13.2

Handles:
- Entity management
- Labor management
- Land/lease management
- Cash flow management
- Market intelligence
- Research/field trials
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from middleware.auth_middleware import get_current_active_user, require_manager, AuthenticatedUser
from middleware.rate_limiter import limiter, RATE_MODERATE

router = APIRouter(prefix="/api/v1", tags=["Farm Business"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class EntityResponse(BaseModel):
    id: int
    name: str
    entity_type: str
    tax_id: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None

class EntityListResponse(BaseModel):
    entities: List[EntityResponse]
    total: int

class EmployeeResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    employee_type: str
    pay_type: str
    pay_rate: float
    status: Optional[str] = "active"
    created_at: Optional[datetime] = None

class EmployeeListResponse(BaseModel):
    employees: List[EmployeeResponse]
    total: int

class TimeEntryResponse(BaseModel):
    id: int
    employee_id: int
    work_date: date
    hours: float
    description: Optional[str] = None
    created_at: Optional[datetime] = None

class TimeEntryListResponse(BaseModel):
    entries: List[TimeEntryResponse]
    total: int

class LeaseResponse(BaseModel):
    id: int
    landlord_name: str
    acres: float
    lease_type: str
    annual_rent: float
    start_date: date
    end_date: date
    status: Optional[str] = "active"
    created_at: Optional[datetime] = None

class LeaseListResponse(BaseModel):
    leases: List[LeaseResponse]
    total: int

class CashTransactionResponse(BaseModel):
    id: int
    transaction_date: date
    amount: float
    category: str
    description: Optional[str] = None
    transaction_type: str  # income or expense

class CashTransactionListResponse(BaseModel):
    transactions: List[CashTransactionResponse]
    total: int

class CashFlowSummaryResponse(BaseModel):
    year: int
    total_income: float
    total_expenses: float
    net_cash_flow: float
    by_category: Dict[str, float]

class CashFlowForecastResponse(BaseModel):
    months: List[Dict[str, Any]]
    projected_balance: float

class MarketPricesResponse(BaseModel):
    prices: Dict[str, float]

class MarketingContractResponse(BaseModel):
    id: int
    crop: str
    quantity: float
    price: float
    delivery_date: date
    buyer: Optional[str] = None
    status: str

class MarketingContractListResponse(BaseModel):
    contracts: List[MarketingContractResponse]
    total: int

class InsuranceRatesResponse(BaseModel):
    rates: Dict[str, Any]

class TrialResponse(BaseModel):
    id: int
    name: str
    trial_type: str
    field_id: int
    start_date: date
    end_date: Optional[date] = None
    status: Optional[str] = "active"
    created_at: Optional[datetime] = None

class TrialDetailResponse(TrialResponse):
    treatments: Optional[List[Dict[str, Any]]] = None
    measurements: Optional[List[Dict[str, Any]]] = None

class TrialListResponse(BaseModel):
    trials: List[TrialResponse]
    total: int

class TrialAnalysisResponse(BaseModel):
    trial_id: int
    statistics: Dict[str, Any]
    recommendations: Optional[List[str]] = None


# ============================================================================
# ENTITY MANAGEMENT
# ============================================================================

@router.get("/entities", response_model=EntityListResponse, tags=["Entities"])
async def list_entities(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List farm entities."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    return service.list_entities()


@router.post("/entities", response_model=EntityResponse, tags=["Entities"])
@limiter.limit(RATE_MODERATE)
async def create_entity(
    request: Request,
    name: str,
    entity_type: str,
    tax_id: Optional[str] = None,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Create a new entity. Rate limited: 30/minute."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    result = service.create_entity(
        name=name,
        entity_type=entity_type,
        tax_id=tax_id,
        created_by=user.id
    )

    return result


@router.get("/entities/{entity_id}", response_model=EntityResponse, tags=["Entities"])
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

@router.get("/labor/employees", response_model=EmployeeListResponse, tags=["Labor"])
async def list_employees(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List employees."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    return service.list_employees(status=status)


@router.post("/labor/employees", response_model=EmployeeResponse, tags=["Labor"])
@limiter.limit(RATE_MODERATE)
async def create_employee(
    request: Request,
    first_name: str,
    last_name: str,
    employee_type: str,
    pay_type: str,
    pay_rate: float,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Create a new employee record. Rate limited: 30/minute."""
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


@router.get("/labor/time-entries", response_model=TimeEntryListResponse, tags=["Labor"])
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


@router.post("/labor/time-entries", response_model=TimeEntryResponse, tags=["Labor"])
@limiter.limit(RATE_MODERATE)
async def create_time_entry(
    request: Request,
    employee_id: int,
    work_date: date,
    hours: float,
    description: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a time entry. Rate limited: 30/minute."""
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

@router.get("/land/leases", response_model=LeaseListResponse, tags=["Land"])
async def list_leases(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List land leases."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    return service.list_leases(status=status)


@router.post("/land/leases", response_model=LeaseResponse, tags=["Land"])
@limiter.limit(RATE_MODERATE)
async def create_lease(
    request: Request,
    landlord_name: str,
    acres: float,
    lease_type: str,
    annual_rent: float,
    start_date: date,
    end_date: date,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Create a new lease. Rate limited: 30/minute."""
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


@router.get("/land/leases/{lease_id}", response_model=LeaseResponse, tags=["Land"])
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

@router.get("/cashflow/transactions", response_model=CashTransactionListResponse, tags=["Cash Flow"])
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


@router.get("/cashflow/summary", response_model=CashFlowSummaryResponse, tags=["Cash Flow"])
async def get_cash_flow_summary(
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get cash flow summary."""
    from services.enterprise_operations_service import get_enterprise_operations_service

    service = get_enterprise_operations_service()
    return service.get_cash_flow_summary(year=year)


@router.get("/cashflow/forecast", response_model=CashFlowForecastResponse, tags=["Cash Flow"])
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

@router.get("/market/prices", response_model=MarketPricesResponse, tags=["Market"])
async def get_market_prices(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get current commodity prices."""
    from services.farm_intelligence_service import CURRENT_PRICES

    return {"prices": CURRENT_PRICES}


@router.get("/market/contracts", response_model=MarketingContractListResponse, tags=["Market"])
async def list_marketing_contracts(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List marketing contracts."""
    from services.farm_intelligence_service import get_farm_intelligence_service

    service = get_farm_intelligence_service()
    return service.list_contracts(status=status)


@router.get("/market/insurance-rates", response_model=InsuranceRatesResponse, tags=["Market"])
async def get_insurance_rates(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get crop insurance rates."""
    from services.farm_intelligence_service import INSURANCE_RATES

    return {"rates": INSURANCE_RATES}


# ============================================================================
# RESEARCH/FIELD TRIALS
# ============================================================================

@router.get("/research/trials", response_model=TrialListResponse, tags=["Research"])
async def list_trials(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List field trials."""
    from services.research_service import get_research_service

    service = get_research_service()
    return service.list_trials(status=status)


@router.post("/research/trials", response_model=TrialResponse, tags=["Research"])
@limiter.limit(RATE_MODERATE)
async def create_trial(
    request: Request,
    name: str,
    trial_type: str,
    field_id: int,
    start_date: date,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new field trial. Rate limited: 30/minute."""
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


@router.get("/research/trials/{trial_id}", response_model=TrialDetailResponse, tags=["Research"])
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


@router.get("/research/trials/{trial_id}/analysis", response_model=TrialAnalysisResponse, tags=["Research"])
async def get_trial_analysis(
    trial_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get statistical analysis for a trial."""
    from services.research_service import get_research_service

    service = get_research_service()
    return service.get_trial_analysis(trial_id)
