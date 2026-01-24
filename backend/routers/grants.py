"""
Grants Router
AgTools v6.13.2

Handles:
- Grant programs and NRCS practices
- Grant applications
- Compliance tracking
- Carbon programs
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from middleware.auth_middleware import get_current_active_user, require_manager, AuthenticatedUser
from middleware.rate_limiter import limiter, RATE_MODERATE

router = APIRouter(prefix="/api/v1", tags=["Grants"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class GrantProgramResponse(BaseModel):
    id: str
    name: str
    agency: str
    description: Optional[str] = None
    max_funding: Optional[float] = None
    deadline: Optional[date] = None
    eligibility: Optional[List[str]] = None

class GrantProgramListResponse(BaseModel):
    programs: List[GrantProgramResponse]
    total: int

class NRCSPracticeResponse(BaseModel):
    code: str
    name: str
    category: str
    description: Optional[str] = None
    payment_rate: Optional[float] = None

class NRCSPracticeListResponse(BaseModel):
    practices: List[Dict[str, Any]]

class BenchmarksResponse(BaseModel):
    benchmarks: Dict[str, Any]

class CarbonProgramResponse(BaseModel):
    id: str
    name: str
    price_per_ton: Optional[float] = None
    verification_required: Optional[bool] = None

class CarbonProgramListResponse(BaseModel):
    programs: List[Dict[str, Any]]

class TechnologyResponse(BaseModel):
    technologies: Dict[str, Any]

class DataRequirementsResponse(BaseModel):
    requirements: Dict[str, Any]

class GrantApplicationResponse(BaseModel):
    id: int
    program_id: str
    title: str
    description: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    submitted_at: Optional[datetime] = None

class GrantApplicationListResponse(BaseModel):
    applications: List[GrantApplicationResponse]
    total: int

class ComplianceStatusResponse(BaseModel):
    overall_status: str
    items: List[Dict[str, Any]]
    score: Optional[float] = None

class ComplianceRequirementsResponse(BaseModel):
    requirements: List[Dict[str, Any]]


# ============================================================================
# GRANT PROGRAMS
# ============================================================================

@router.get("/grants/programs", response_model=GrantProgramListResponse, tags=["Grants"])
async def list_grant_programs(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List available grant programs."""
    from services.grant_service import get_grant_service

    service = get_grant_service()
    return service.list_programs()


@router.get("/grants/programs/{program_id}", response_model=GrantProgramResponse, tags=["Grants"])
async def get_grant_program(
    program_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get details for a specific grant program."""
    from services.grant_service import get_grant_service

    service = get_grant_service()
    program = service.get_program(program_id)

    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    return program


# ============================================================================
# NRCS PRACTICES
# ============================================================================

@router.get("/grants/nrcs-practices", response_model=NRCSPracticeListResponse, tags=["Grants"])
async def list_nrcs_practices(
    category: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List NRCS conservation practices."""
    from services.grant_service import NRCS_PRACTICES

    # Convert dict of NRCSPractice objects to list of dicts
    practices_list = [
        {
            "code": p.code,
            "name": p.name,
            "category": p.category.value if hasattr(p.category, 'value') else p.category,
            "description": p.description,
            "payment_rate": p.payment_rate,
            "carbon_benefit": p.carbon_benefit,
            "soil_health_points": p.soil_health_points,
            "water_quality_points": p.water_quality_points,
            "biodiversity_points": p.biodiversity_points,
            "eligible_programs": p.eligible_programs,
            "documentation_required": p.documentation_required,
            "verification_method": p.verification_method
        }
        for p in NRCS_PRACTICES.values()
    ]

    if category:
        practices_list = [p for p in practices_list if p.get("category") == category]

    return {"practices": practices_list}


@router.get("/grants/benchmarks", response_model=BenchmarksResponse, tags=["Grants"])
async def get_benchmarks(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get benchmark data for grant applications."""
    from services.grant_service import BENCHMARK_DATA

    return {"benchmarks": BENCHMARK_DATA}


# ============================================================================
# CARBON PROGRAMS
# ============================================================================

@router.get("/grants/carbon-programs", response_model=CarbonProgramListResponse, tags=["Grants"])
async def list_carbon_programs(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List carbon credit programs."""
    from services.grant_service import CARBON_PROGRAMS

    # Convert dict to list format expected by response model
    programs_list = [
        {"id": program.value, **info}
        for program, info in CARBON_PROGRAMS.items()
    ]
    return {"programs": programs_list}


# ============================================================================
# PRECISION AG TECHNOLOGIES
# ============================================================================

@router.get("/grants/technologies", response_model=TechnologyResponse, tags=["Grants"])
async def list_precision_ag_technologies(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List precision ag technologies for grant applications."""
    from services.grant_enhancement_service import TECHNOLOGY_BENEFITS

    return {"technologies": TECHNOLOGY_BENEFITS}


@router.get("/grants/data-requirements", response_model=DataRequirementsResponse, tags=["Grants"])
async def get_grant_data_requirements(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get data requirements for grant applications."""
    from services.grant_enhancement_service import GRANT_DATA_REQUIREMENTS

    return {"requirements": GRANT_DATA_REQUIREMENTS}


# ============================================================================
# GRANT APPLICATIONS
# ============================================================================

@router.get("/grants/applications", response_model=GrantApplicationListResponse, tags=["Grant Applications"])
async def list_grant_applications(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List grant applications."""
    from services.grant_operations_service import get_grant_operations_service

    service = get_grant_operations_service()
    return service.list_applications(status=status)


@router.post("/grants/applications", response_model=GrantApplicationResponse, tags=["Grant Applications"])
@limiter.limit(RATE_MODERATE)
async def create_grant_application(
    request: Request,
    program_id: str,
    title: str,
    description: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new grant application. Rate limited: 30/minute."""
    from services.grant_operations_service import get_grant_operations_service

    service = get_grant_operations_service()
    result = service.create_application(
        program_id=program_id,
        title=title,
        description=description,
        created_by=user.id
    )

    return result


@router.get("/grants/applications/{application_id}", response_model=GrantApplicationResponse, tags=["Grant Applications"])
async def get_grant_application(
    application_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get grant application details."""
    from services.grant_operations_service import get_grant_operations_service

    service = get_grant_operations_service()
    application = service.get_application(application_id)

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return application


@router.put("/grants/applications/{application_id}/status", response_model=GrantApplicationResponse, tags=["Grant Applications"])
@limiter.limit(RATE_MODERATE)
async def update_application_status(
    request: Request,
    application_id: int,
    status: str,
    notes: Optional[str] = None,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Update grant application status. Rate limited: 30/minute."""
    from services.grant_operations_service import get_grant_operations_service

    service = get_grant_operations_service()
    result = service.update_status(
        application_id=application_id,
        status=status,
        notes=notes,
        updated_by=user.id
    )

    return result


# ============================================================================
# COMPLIANCE
# ============================================================================

@router.get("/grants/compliance", response_model=ComplianceStatusResponse, tags=["Compliance"])
async def get_compliance_status(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get overall compliance status."""
    from services.grant_operations_service import get_grant_operations_service

    service = get_grant_operations_service()
    return service.get_compliance_status()


@router.get("/grants/compliance/requirements", response_model=ComplianceRequirementsResponse, tags=["Compliance"])
async def get_compliance_requirements(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get compliance requirements."""
    from services.grant_operations_service import COMPLIANCE_REQUIREMENTS

    return {"requirements": COMPLIANCE_REQUIREMENTS}
