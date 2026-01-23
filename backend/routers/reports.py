"""
Reports and Data Export Router
AgTools v6.13.2

Handles:
- Operations, financial, equipment, inventory reports
- Cost tracking and expense management
- Data export (CSV, Excel, PDF)
- Dashboard export
"""

from typing import List, Optional, Dict, Any
from datetime import date

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from pydantic import BaseModel

from middleware.auth_middleware import get_current_active_user, AuthenticatedUser
from middleware.rate_limiter import limiter, RATE_MODERATE
from services.reporting_service import (
    get_reporting_service,
    OperationsReport,
    FinancialReport,
    EquipmentReport,
    InventoryReport,
    FieldPerformanceReport,
    DashboardSummary
)
from services.cost_tracking_service import (
    get_cost_tracking_service,
    ExpenseCategory,
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    ExpenseListResponse,
    AllocationCreate,
    AllocationResponse,
    ExpenseWithAllocations,
    ColumnMapping,
    ImportPreview,
    ImportResult,
    ImportBatchResponse,
    SavedMappingResponse,
    CostPerAcreReport,
    CategoryBreakdown,
    CropCostSummary
)

router = APIRouter(prefix="/api/v1", tags=["Reports"])


# ============================================================================
# REPORTING ENDPOINTS
# ============================================================================

@router.get("/reports/operations", response_model=OperationsReport, tags=["Reports"])
@limiter.limit(RATE_MODERATE)
async def get_operations_report(
    request: Request,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get operations report with aggregations. Rate limited: 30/minute."""
    report_service = get_reporting_service()
    return report_service.get_operations_report(date_from, date_to, field_id)


@router.get("/reports/financial", response_model=FinancialReport, tags=["Reports"])
@limiter.limit(RATE_MODERATE)
async def get_financial_report(
    request: Request,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get financial analysis report. Rate limited: 30/minute."""
    report_service = get_reporting_service()
    return report_service.get_financial_report(date_from, date_to)


@router.get("/reports/equipment", response_model=EquipmentReport, tags=["Reports"])
@limiter.limit(RATE_MODERATE)
async def get_equipment_report(
    request: Request,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get equipment utilization report. Rate limited: 30/minute."""
    report_service = get_reporting_service()
    return report_service.get_equipment_report(date_from, date_to)


@router.get("/reports/inventory", response_model=InventoryReport, tags=["Reports"])
async def get_inventory_report(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get inventory status report."""
    report_service = get_reporting_service()
    return report_service.get_inventory_report()


@router.get("/reports/fields", response_model=FieldPerformanceReport, tags=["Reports"])
async def get_field_performance_report(
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get field performance report."""
    report_service = get_reporting_service()
    return report_service.get_field_performance_report(year)


@router.get("/reports/dashboard", response_model=DashboardSummary, tags=["Reports"])
async def get_dashboard_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get dashboard summary with KPIs."""
    report_service = get_reporting_service()
    return report_service.get_dashboard_summary()


# ============================================================================
# COST TRACKING - EXPENSES
# ============================================================================

@router.get("/costs/expenses", response_model=ExpenseListResponse, tags=["Cost Tracking"])
async def list_expenses(
    category: Optional[ExpenseCategory] = None,
    field_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    vendor: Optional[str] = None,
    unallocated_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List expenses with optional filters."""
    cost_service = get_cost_tracking_service()
    return cost_service.list_expenses(
        user_id=user.id,
        category=category,
        vendor=vendor,
        unallocated_only=unallocated_only,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )


@router.post("/costs/expenses", response_model=ExpenseResponse, tags=["Cost Tracking"])
@limiter.limit(RATE_MODERATE)
async def create_expense(
    request: Request,
    expense_data: ExpenseCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new expense. Rate limited: 30/minute."""
    cost_service = get_cost_tracking_service()
    expense, error = cost_service.create_expense(expense_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return expense


@router.get("/costs/expenses/{expense_id}", response_model=ExpenseWithAllocations, tags=["Cost Tracking"])
async def get_expense(
    expense_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get expense with allocations."""
    cost_service = get_cost_tracking_service()
    expense = cost_service.get_expense_with_allocations(expense_id)

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    return expense


@router.put("/costs/expenses/{expense_id}", response_model=ExpenseResponse, tags=["Cost Tracking"])
async def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update an expense."""
    cost_service = get_cost_tracking_service()
    expense, error = cost_service.update_expense(expense_id, expense_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return expense


@router.delete("/costs/expenses/{expense_id}", tags=["Cost Tracking"])
async def delete_expense(
    expense_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Delete an expense."""
    cost_service = get_cost_tracking_service()
    success = cost_service.delete_expense(expense_id, user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Expense not found or already deleted")

    return {"message": "Expense deleted successfully"}


# ============================================================================
# COST TRACKING - ALLOCATIONS
# ============================================================================

@router.get("/costs/expenses/{expense_id}/allocations", response_model=List[AllocationResponse], tags=["Cost Tracking"])
async def get_expense_allocations(
    expense_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get allocations for an expense."""
    cost_service = get_cost_tracking_service()
    return cost_service.get_allocations(expense_id)


@router.post("/costs/expenses/{expense_id}/allocations", response_model=List[AllocationResponse], tags=["Cost Tracking"])
async def create_allocations(
    expense_id: int,
    allocations: List[AllocationCreate],
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create allocations for an expense."""
    cost_service = get_cost_tracking_service()
    result, error = cost_service.set_allocations(expense_id, allocations, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


class AutoCategorizeRequest(BaseModel):
    description: str
    amount: Optional[float] = None
    vendor: Optional[str] = None


class AutoCategorizeResponse(BaseModel):
    suggested_category: str
    confidence: float
    alternatives: List[Dict[str, Any]] = []


@router.post("/costs/expenses/auto-categorize", response_model=AutoCategorizeResponse, tags=["Cost Tracking"])
async def auto_categorize_expense(
    request: AutoCategorizeRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Auto-categorize an expense based on description."""
    # Simple keyword-based categorization
    description = request.description.lower()
    vendor = (request.vendor or "").lower()

    categories = {
        "seed": ["seed", "planting", "corn seed", "soybean seed", "cover crop"],
        "fertilizer": ["fertilizer", "nitrogen", "phosphate", "potash", "urea", "anhydrous"],
        "chemical": ["herbicide", "pesticide", "fungicide", "roundup", "dicamba", "insecticide"],
        "fuel": ["fuel", "diesel", "gas", "gasoline", "propane"],
        "equipment": ["equipment", "tractor", "combine", "planter", "implement"],
        "repairs": ["repair", "maintenance", "parts", "service"],
        "labor": ["labor", "wage", "employee", "payroll"],
        "insurance": ["insurance", "crop insurance", "liability"],
        "rent": ["rent", "land rent", "cash rent", "lease"],
        "utilities": ["utility", "electric", "water", "phone", "internet"],
        "other": []
    }

    suggested = "other"
    confidence = 0.3
    alternatives = []

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in description or keyword in vendor:
                suggested = category
                confidence = 0.85
                break
        if confidence > 0.5:
            break

    # Add alternatives
    for category in ["seed", "fertilizer", "chemical", "fuel", "equipment"]:
        if category != suggested:
            alternatives.append({"category": category, "confidence": 0.2})

    return {
        "suggested_category": suggested,
        "confidence": confidence,
        "alternatives": alternatives[:3]
    }


# ============================================================================
# COST TRACKING - REPORTS
# ============================================================================

@router.get("/costs/reports/per-acre", response_model=CostPerAcreReport, tags=["Cost Tracking"])
async def get_cost_per_acre_report(
    year: Optional[int] = None,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get cost per acre report."""
    cost_service = get_cost_tracking_service()
    return cost_service.get_cost_per_acre_report(year=year, field_id=field_id)


@router.get("/costs/reports/by-category", response_model=List[CategoryBreakdown], tags=["Cost Tracking"])
async def get_costs_by_category(
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get costs broken down by category."""
    cost_service = get_cost_tracking_service()
    return cost_service.get_costs_by_category(year=year)


@router.get("/costs/reports/by-crop", response_model=List[CropCostSummary], tags=["Cost Tracking"])
async def get_costs_by_crop(
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get costs broken down by crop."""
    cost_service = get_cost_tracking_service()
    return cost_service.get_costs_by_crop(year=year)


@router.get("/costs/categories", tags=["Cost Tracking"])
async def get_expense_categories(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of expense categories."""
    return {"categories": [e.value for e in ExpenseCategory]}


# ============================================================================
# COST TRACKING - IMPORT
# ============================================================================

@router.post("/costs/import/csv/preview", response_model=ImportPreview, tags=["Cost Tracking"])
async def preview_csv_import(
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Preview CSV import before processing."""
    cost_service = get_cost_tracking_service()

    content = await file.read()
    result = cost_service.preview_csv_import(content.decode('utf-8'), file.filename)

    return result


@router.post("/costs/import/csv", response_model=ImportResult, tags=["Cost Tracking"])
@limiter.limit(RATE_MODERATE)
async def import_csv(
    request: Request,
    file: UploadFile = File(...),
    mapping: Optional[ColumnMapping] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Import expenses from CSV file. Rate limited: 30/minute."""
    cost_service = get_cost_tracking_service()

    content = await file.read()
    result = cost_service.import_csv(
        content.decode('utf-8'),
        file.filename,
        mapping,
        user.id
    )

    return result


@router.get("/costs/imports", response_model=List[ImportBatchResponse], tags=["Cost Tracking"])
async def list_import_batches(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List import batch history."""
    cost_service = get_cost_tracking_service()
    return cost_service.list_import_batches()


@router.get("/costs/mappings", response_model=List[SavedMappingResponse], tags=["Cost Tracking"])
async def list_saved_mappings(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List saved column mappings."""
    cost_service = get_cost_tracking_service()
    return cost_service.list_saved_mappings()
