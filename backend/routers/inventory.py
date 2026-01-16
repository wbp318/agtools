"""
Inventory Management Router
AgTools v6.13.2

Handles:
- Inventory items (CRUD operations)
- Inventory transactions
- Inventory alerts and reporting
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
from services.inventory_service import (
    get_inventory_service,
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemResponse,
    InventorySummary,
    InventoryCategory,
    TransactionCreate,
    TransactionResponse,
    TransactionType,
    InventoryAlert,
    QuickPurchaseRequest,
    AdjustQuantityRequest
)

router = APIRouter(prefix="/api/v1", tags=["Inventory"])


# ============================================================================
# INVENTORY MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/inventory", response_model=List[InventoryItemResponse], tags=["Inventory"])
async def list_inventory(
    category: Optional[InventoryCategory] = None,
    search: Optional[str] = None,
    storage_location: Optional[str] = None,
    low_stock_only: bool = False,
    expiring_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    List inventory items with optional filters.

    - **category**: Filter by category (seed, fertilizer, herbicide, etc.)
    - **search**: Search by name, manufacturer, or product code
    - **storage_location**: Filter by storage location
    - **low_stock_only**: Only show items below minimum quantity
    - **expiring_only**: Only show items expiring within 30 days
    """
    inv_service = get_inventory_service()
    return inv_service.list_items(
        category=category,
        search=search,
        storage_location=storage_location,
        low_stock_only=low_stock_only,
        expiring_only=expiring_only,
        limit=limit,
        offset=offset
    )


@router.post("/inventory", response_model=InventoryItemResponse, tags=["Inventory"])
@limiter.limit(RATE_MODERATE)
async def create_inventory_item(
    request: Request,
    item_data: InventoryItemCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new inventory item. Rate limited: 30/minute."""
    inv_service = get_inventory_service()
    item, error = inv_service.create_item(item_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return item


@router.get("/inventory/summary", response_model=InventorySummary, tags=["Inventory"])
async def get_inventory_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get summary statistics for inventory."""
    inv_service = get_inventory_service()
    return inv_service.get_inventory_summary()


@router.get("/inventory/categories", tags=["Inventory"])
async def get_inventory_categories(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of inventory categories for dropdowns."""
    inv_service = get_inventory_service()
    return inv_service.get_categories()


@router.get("/inventory/locations", tags=["Inventory"])
async def get_storage_locations(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of unique storage locations."""
    inv_service = get_inventory_service()
    return inv_service.get_storage_locations()


@router.get("/inventory/alerts", response_model=List[InventoryAlert], tags=["Inventory"])
async def get_inventory_alerts(
    expiry_days: int = 30,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get inventory alerts (low stock and expiring items).

    Returns items that are below minimum quantity or expiring within the specified days.
    """
    inv_service = get_inventory_service()
    return inv_service.get_alerts(expiry_days=expiry_days)


@router.get("/inventory/{item_id}", response_model=InventoryItemResponse, tags=["Inventory"])
async def get_inventory_item(
    item_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get inventory item by ID."""
    inv_service = get_inventory_service()
    item = inv_service.get_item_by_id(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return item


@router.put("/inventory/{item_id}", response_model=InventoryItemResponse, tags=["Inventory"])
@limiter.limit(RATE_MODERATE)
async def update_inventory_item(
    request: Request,
    item_id: int,
    item_data: InventoryItemUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update inventory item. Rate limited: 30/minute."""
    inv_service = get_inventory_service()
    item, error = inv_service.update_item(item_id, item_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return item


@router.delete("/inventory/{item_id}", tags=["Inventory"])
async def delete_inventory_item(
    item_id: int,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Delete inventory item (soft delete). Manager/admin only."""
    inv_service = get_inventory_service()
    success, error = inv_service.delete_item(item_id, user.id)

    if not success:
        raise HTTPException(status_code=400, detail=error or "Failed to delete item")

    return {"message": "Inventory item deleted successfully"}


# ============================================================================
# INVENTORY TRANSACTION ENDPOINTS
# ============================================================================

@router.post("/inventory/transaction", response_model=TransactionResponse, tags=["Inventory"])
@limiter.limit(RATE_MODERATE)
async def record_inventory_transaction(
    request: Request,
    trans_data: TransactionCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record an inventory transaction. Rate limited: 30/minute.

    Use positive quantity for additions (purchase, return, adjustment up).
    Use negative quantity for deductions (usage, waste, adjustment down).
    """
    inv_service = get_inventory_service()
    transaction, error = inv_service.record_transaction(trans_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return transaction


@router.get("/inventory/{item_id}/transactions", response_model=List[TransactionResponse], tags=["Inventory"])
async def get_item_transactions(
    item_id: int,
    transaction_type: Optional[TransactionType] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 100,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get transaction history for an inventory item."""
    inv_service = get_inventory_service()
    return inv_service.get_item_transactions(
        item_id,
        transaction_type=transaction_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )


@router.post("/inventory/purchase", response_model=InventoryItemResponse, tags=["Inventory"])
@limiter.limit(RATE_MODERATE)
async def quick_purchase(
    request: Request,
    purchase_data: QuickPurchaseRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Quick purchase entry. Rate limited: 30/minute.

    Adds quantity to inventory and records a purchase transaction.
    """
    inv_service = get_inventory_service()
    item, error = inv_service.quick_purchase(purchase_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return item


@router.post("/inventory/adjust", response_model=InventoryItemResponse, tags=["Inventory"])
@limiter.limit(RATE_MODERATE)
async def adjust_quantity(
    request: Request,
    adjust_data: AdjustQuantityRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Adjust inventory quantity (for counts, corrections). Rate limited: 30/minute.

    Sets the quantity to the new value and records an adjustment transaction.
    """
    inv_service = get_inventory_service()
    item, error = inv_service.adjust_quantity(adjust_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return item
