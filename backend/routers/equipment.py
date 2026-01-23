"""
Equipment and Maintenance Router
AgTools v6.13.2

Handles:
- Equipment management (CRUD operations)
- Maintenance records and alerts
- Equipment usage logging
"""

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, HTTPException, Depends, Request

from middleware.auth_middleware import (
    get_current_active_user,
    require_manager,
    AuthenticatedUser
)
from middleware.rate_limiter import limiter, RATE_MODERATE
from services.equipment_service import (
    get_equipment_service,
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    EquipmentSummary,
    EquipmentType,
    EquipmentStatus,
    MaintenanceCreate,
    MaintenanceResponse,
    MaintenanceType,
    MaintenanceAlert,
    EquipmentUsageCreate,
    EquipmentUsageResponse
)

router = APIRouter(prefix="/api/v1", tags=["Equipment"])


# ============================================================================
# EQUIPMENT MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/equipment", response_model=List[EquipmentResponse], tags=["Equipment"])
async def list_equipment(
    equipment_type: Optional[EquipmentType] = None,
    status: Optional[EquipmentStatus] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    List all equipment with optional filters.

    - **equipment_type**: Filter by type (tractor, combine, sprayer, etc.)
    - **status**: Filter by status (available, in_use, maintenance, retired)
    - **search**: Search by name, make, model, or serial number
    """
    equip_service = get_equipment_service()
    return equip_service.list_equipment(
        equipment_type=equipment_type,
        status=status,
        search=search,
        limit=limit,
        offset=offset
    )


@router.post("/equipment", response_model=EquipmentResponse, tags=["Equipment"])
@limiter.limit(RATE_MODERATE)
async def create_equipment(
    request: Request,
    equip_data: EquipmentCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new equipment record. Rate limited: 30/minute."""
    equip_service = get_equipment_service()
    equipment, error = equip_service.create_equipment(equip_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return equipment


@router.get("/equipment/summary", response_model=EquipmentSummary, tags=["Equipment"])
async def get_equipment_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get summary statistics for equipment fleet."""
    equip_service = get_equipment_service()
    return equip_service.get_equipment_summary()


@router.get("/equipment/types", tags=["Equipment"])
async def get_equipment_types(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of equipment types for dropdowns."""
    equip_service = get_equipment_service()
    return equip_service.get_equipment_types()


@router.get("/equipment/statuses", tags=["Equipment"])
async def get_equipment_statuses(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of equipment statuses for dropdowns."""
    equip_service = get_equipment_service()
    return equip_service.get_equipment_statuses()


@router.get("/equipment/{equipment_id}", response_model=EquipmentResponse, tags=["Equipment"])
async def get_equipment(
    equipment_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get equipment by ID."""
    equip_service = get_equipment_service()
    equipment = equip_service.get_equipment_by_id(equipment_id)

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return equipment


@router.put("/equipment/{equipment_id}", response_model=EquipmentResponse, tags=["Equipment"])
@limiter.limit(RATE_MODERATE)
async def update_equipment(
    request: Request,
    equipment_id: int,
    equip_data: EquipmentUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update equipment. Rate limited: 30/minute."""
    equip_service = get_equipment_service()
    equipment, error = equip_service.update_equipment(equipment_id, equip_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return equipment


@router.delete("/equipment/{equipment_id}", tags=["Equipment"])
async def delete_equipment(
    equipment_id: int,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Retire equipment (soft delete). Manager/admin only."""
    equip_service = get_equipment_service()
    success, error = equip_service.delete_equipment(equipment_id, user.id)

    if not success:
        raise HTTPException(status_code=400, detail=error or "Failed to delete equipment")

    return {"message": "Equipment retired successfully"}


@router.post("/equipment/{equipment_id}/hours", response_model=EquipmentResponse, tags=["Equipment"])
async def update_equipment_hours(
    equipment_id: int,
    new_hours: float,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update equipment hour meter reading."""
    equip_service = get_equipment_service()
    equipment, error = equip_service.update_hours(equipment_id, new_hours, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return equipment


# ============================================================================
# MAINTENANCE ENDPOINTS
# ============================================================================

@router.get("/maintenance", response_model=List[MaintenanceResponse], tags=["Maintenance"])
async def list_maintenance(
    equipment_id: Optional[int] = None,
    maintenance_type: Optional[MaintenanceType] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List maintenance records with optional filters."""
    equip_service = get_equipment_service()
    return equip_service.list_maintenance(
        equipment_id=equipment_id,
        maintenance_type=maintenance_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )


@router.post("/maintenance", response_model=MaintenanceResponse, tags=["Maintenance"])
@limiter.limit(RATE_MODERATE)
async def create_maintenance(
    request: Request,
    maint_data: MaintenanceCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Log a maintenance record. Rate limited: 30/minute."""
    equip_service = get_equipment_service()
    maintenance, error = equip_service.create_maintenance(maint_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return maintenance


@router.get("/maintenance/alerts", response_model=List[MaintenanceAlert], tags=["Maintenance"])
async def get_maintenance_alerts(
    days_ahead: int = 30,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get upcoming maintenance alerts.

    Returns equipment that has maintenance due within the specified number of days,
    or is overdue for service.
    """
    equip_service = get_equipment_service()
    return equip_service.get_maintenance_alerts(days_ahead=days_ahead)


@router.get("/maintenance/types", tags=["Maintenance"])
async def get_maintenance_types(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of maintenance types for dropdowns."""
    equip_service = get_equipment_service()
    return equip_service.get_maintenance_types()


@router.get("/equipment/{equipment_id}/maintenance", response_model=List[MaintenanceResponse], tags=["Maintenance"])
async def get_equipment_maintenance_history(
    equipment_id: int,
    limit: int = 50,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get maintenance history for specific equipment."""
    equip_service = get_equipment_service()
    return equip_service.get_equipment_maintenance_history(equipment_id, limit=limit)


# ============================================================================
# EQUIPMENT USAGE ENDPOINTS
# ============================================================================

@router.get("/equipment/{equipment_id}/usage", response_model=List[EquipmentUsageResponse], tags=["Equipment"])
async def get_equipment_usage_history(
    equipment_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 100,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get usage history for specific equipment."""
    equip_service = get_equipment_service()
    return equip_service.get_equipment_usage_history(
        equipment_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )


@router.post("/equipment/usage", response_model=EquipmentUsageResponse, tags=["Equipment"])
@limiter.limit(RATE_MODERATE)
async def log_equipment_usage(
    request: Request,
    usage_data: EquipmentUsageCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Log equipment usage (hours, fuel, operator). Rate limited: 30/minute."""
    equip_service = get_equipment_service()
    usage, error = equip_service.log_usage(usage_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return usage
