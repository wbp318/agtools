"""
Fields and Field Operations Router
AgTools v6.13.2

Handles:
- Field management (CRUD operations)
- Field operations logging
- Operation history
"""

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from middleware.auth_middleware import (
    get_current_active_user,
    require_manager,
    AuthenticatedUser
)
from middleware.rate_limiter import limiter, RATE_STANDARD, RATE_MODERATE
from services.field_service import (
    get_field_service,
    FieldCreate,
    FieldUpdate,
    FieldResponse,
    FieldSummary,
    CropType as FieldCropType,
    SoilType,
    IrrigationType as FieldIrrigationType
)
from services.field_operations_service import (
    get_field_operations_service,
    OperationCreate,
    OperationUpdate,
    OperationResponse,
    OperationsSummary,
    FieldOperationHistory,
    OperationType
)

router = APIRouter(prefix="/api/v1", tags=["Fields"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class FieldListResponse(BaseModel):
    """Response for field list endpoint"""
    count: int
    fields: List[FieldResponse]


class OperationListResponse(BaseModel):
    """Response for operation list endpoint"""
    count: int
    operations: List[OperationResponse]


# ============================================================================
# FIELD MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/fields", response_model=FieldListResponse, tags=["Fields"])
async def list_fields(
    farm_name: Optional[str] = None,
    current_crop: Optional[str] = None,
    soil_type: Optional[str] = None,
    irrigation_type: Optional[str] = None,
    search: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    List all fields with optional filters.

    Filters:
    - farm_name: Filter by farm grouping
    - current_crop: Filter by crop type (corn, soybean, wheat, etc.)
    - soil_type: Filter by soil type (clay, loam, sandy, etc.)
    - irrigation_type: Filter by irrigation (none, center_pivot, drip, etc.)
    - search: Search by field or farm name
    """
    field_service = get_field_service()

    crop_enum = FieldCropType(current_crop) if current_crop else None
    soil_enum = SoilType(soil_type) if soil_type else None
    irrig_enum = FieldIrrigationType(irrigation_type) if irrigation_type else None

    fields = field_service.list_fields(
        farm_name=farm_name,
        current_crop=crop_enum,
        soil_type=soil_enum,
        irrigation_type=irrig_enum,
        search=search
    )

    return FieldListResponse(count=len(fields), fields=fields)


@router.post("/fields", response_model=FieldResponse, tags=["Fields"])
@limiter.limit(RATE_MODERATE)
async def create_field(
    request: Request,
    field_data: FieldCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new field. Rate limited: 30/minute."""
    field_service = get_field_service()

    field, error = field_service.create_field(field_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return field


@router.get("/fields/summary", response_model=FieldSummary, tags=["Fields"])
async def get_field_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get summary statistics for all fields."""
    field_service = get_field_service()
    return field_service.get_field_summary()


@router.get("/fields/farms", tags=["Fields"])
async def get_farm_names(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of unique farm names for filtering."""
    field_service = get_field_service()
    return {"farms": field_service.get_farm_names()}


@router.get("/fields/{field_id}", response_model=FieldResponse, tags=["Fields"])
async def get_field(
    field_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get field by ID."""
    field_service = get_field_service()
    field = field_service.get_field_by_id(field_id)

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    return field


@router.put("/fields/{field_id}", response_model=FieldResponse, tags=["Fields"])
@limiter.limit(RATE_MODERATE)
async def update_field(
    request: Request,
    field_id: int,
    field_data: FieldUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update a field. Rate limited: 30/minute."""
    field_service = get_field_service()

    field, error = field_service.update_field(field_id, field_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    return field


@router.delete("/fields/{field_id}", tags=["Fields"])
async def delete_field(
    field_id: int,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Delete a field (soft delete). Manager/admin only."""
    field_service = get_field_service()

    success, error = field_service.delete_field(field_id, user.id)

    if not success:
        raise HTTPException(status_code=400, detail=error or "Failed to delete field")

    return {"message": "Field deleted successfully"}


# ============================================================================
# FIELD OPERATIONS ENDPOINTS
# ============================================================================

@router.get("/operations", response_model=OperationListResponse, tags=["Operations"])
async def list_operations(
    field_id: Optional[int] = None,
    operation_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    operator_id: Optional[int] = None,
    farm_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    List field operations with optional filters.

    Filters:
    - field_id: Filter by specific field
    - operation_type: spray, fertilizer, planting, harvest, tillage, scouting, irrigation, other
    - date_from/date_to: Date range filter
    - operator_id: Filter by who performed the operation
    - farm_name: Filter by farm
    - limit/offset: Pagination
    """
    ops_service = get_field_operations_service()

    op_type_enum = OperationType(operation_type) if operation_type else None

    operations = ops_service.list_operations(
        field_id=field_id,
        operation_type=op_type_enum,
        date_from=date_from,
        date_to=date_to,
        operator_id=operator_id,
        farm_name=farm_name,
        limit=limit,
        offset=offset
    )

    return OperationListResponse(count=len(operations), operations=operations)


@router.post("/operations", response_model=OperationResponse, tags=["Operations"])
@limiter.limit(RATE_MODERATE)
async def create_operation(
    request: Request,
    op_data: OperationCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Log a new field operation. Rate limited: 30/minute.

    Operation types: spray, fertilizer, planting, harvest, tillage, scouting, irrigation, seed_treatment, cover_crop, other
    """
    ops_service = get_field_operations_service()

    operation, error = ops_service.create_operation(op_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return operation


@router.get("/operations/summary", response_model=OperationsSummary, tags=["Operations"])
async def get_operations_summary(
    field_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get summary statistics for operations.

    Returns total operations, operations by type, and cost summaries.
    """
    ops_service = get_field_operations_service()

    return ops_service.get_operations_summary(
        field_id=field_id,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/operations/{operation_id}", response_model=OperationResponse, tags=["Operations"])
async def get_operation(
    operation_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get operation by ID."""
    ops_service = get_field_operations_service()
    operation = ops_service.get_operation_by_id(operation_id)

    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    return operation


@router.put("/operations/{operation_id}", response_model=OperationResponse, tags=["Operations"])
@limiter.limit(RATE_MODERATE)
async def update_operation(
    request: Request,
    operation_id: int,
    op_data: OperationUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update an operation. Rate limited: 30/minute."""
    ops_service = get_field_operations_service()

    operation, error = ops_service.update_operation(operation_id, op_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    return operation


@router.delete("/operations/{operation_id}", tags=["Operations"])
async def delete_operation(
    operation_id: int,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Delete an operation (soft delete). Manager/admin only."""
    ops_service = get_field_operations_service()

    success, error = ops_service.delete_operation(operation_id, user.id)

    if not success:
        raise HTTPException(status_code=400, detail=error or "Failed to delete operation")

    return {"message": "Operation deleted successfully"}


@router.get("/fields/{field_id}/operations", response_model=FieldOperationHistory, tags=["Operations"])
async def get_field_operation_history(
    field_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get complete operation history for a specific field.

    Returns field info, all operations, and summary statistics.
    """
    ops_service = get_field_operations_service()

    history = ops_service.get_field_operation_history(field_id)

    if not history:
        raise HTTPException(status_code=404, detail="Field not found")

    return history
