"""
Grants Router
AgTools v6.13.0

Handles:
- Grant programs and NRCS practices
- Grant applications
- Compliance tracking
- Carbon programs
"""

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from middleware.auth_middleware import get_current_active_user, require_manager, AuthenticatedUser

router = APIRouter(prefix="/api/v1", tags=["Grants"])


# ============================================================================
# GRANT PROGRAMS
# ============================================================================

@router.get("/grants/programs", tags=["Grants"])
async def list_grant_programs(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List available grant programs."""
    from services.grant_service import get_grant_service

    service = get_grant_service()
    return service.list_programs()


@router.get("/grants/programs/{program_id}", tags=["Grants"])
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

@router.get("/grants/nrcs-practices", tags=["Grants"])
async def list_nrcs_practices(
    category: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List NRCS conservation practices."""
    from services.grant_service import get_grant_service, NRCS_PRACTICES

    if category:
        practices = [p for p in NRCS_PRACTICES if p.get("category") == category]
    else:
        practices = NRCS_PRACTICES

    return {"practices": practices}


@router.get("/grants/benchmarks", tags=["Grants"])
async def get_benchmarks(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get benchmark data for grant applications."""
    from services.grant_service import BENCHMARK_DATA

    return {"benchmarks": BENCHMARK_DATA}


# ============================================================================
# CARBON PROGRAMS
# ============================================================================

@router.get("/grants/carbon-programs", tags=["Grants"])
async def list_carbon_programs(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List carbon credit programs."""
    from services.grant_service import CARBON_PROGRAMS

    return {"programs": CARBON_PROGRAMS}


# ============================================================================
# PRECISION AG TECHNOLOGIES
# ============================================================================

@router.get("/grants/technologies", tags=["Grants"])
async def list_precision_ag_technologies(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List precision ag technologies for grant applications."""
    from services.grant_enhancement_service import TECHNOLOGY_BENEFITS

    return {"technologies": TECHNOLOGY_BENEFITS}


@router.get("/grants/data-requirements", tags=["Grants"])
async def get_grant_data_requirements(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get data requirements for grant applications."""
    from services.grant_enhancement_service import GRANT_DATA_REQUIREMENTS

    return {"requirements": GRANT_DATA_REQUIREMENTS}


# ============================================================================
# GRANT APPLICATIONS
# ============================================================================

@router.get("/grants/applications", tags=["Grant Applications"])
async def list_grant_applications(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List grant applications."""
    from services.grant_operations_service import get_grant_operations_service

    service = get_grant_operations_service()
    return service.list_applications(status=status)


@router.post("/grants/applications", tags=["Grant Applications"])
async def create_grant_application(
    program_id: str,
    title: str,
    description: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new grant application."""
    from services.grant_operations_service import get_grant_operations_service

    service = get_grant_operations_service()
    result = service.create_application(
        program_id=program_id,
        title=title,
        description=description,
        created_by=user.id
    )

    return result


@router.get("/grants/applications/{application_id}", tags=["Grant Applications"])
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


@router.put("/grants/applications/{application_id}/status", tags=["Grant Applications"])
async def update_application_status(
    application_id: int,
    status: str,
    notes: Optional[str] = None,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Update grant application status."""
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

@router.get("/grants/compliance", tags=["Compliance"])
async def get_compliance_status(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get overall compliance status."""
    from services.grant_operations_service import get_grant_operations_service

    service = get_grant_operations_service()
    return service.get_compliance_status()


@router.get("/grants/compliance/requirements", tags=["Compliance"])
async def get_compliance_requirements(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get compliance requirements."""
    from services.grant_operations_service import COMPLIANCE_REQUIREMENTS

    return {"requirements": COMPLIANCE_REQUIREMENTS}
