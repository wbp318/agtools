"""
GenFin Accounting Router
AgTools v6.13.2

Handles:
- Chart of accounts
- Customers, vendors, employees
- Invoices, bills, checks
- Payroll
- Financial reports
- Recurring transactions
- Bank feeds
- Fixed assets
- Multi-entity management
- 1099 tracking
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel

from middleware.auth_middleware import get_current_active_user, require_manager, AuthenticatedUser
from middleware.rate_limiter import limiter, RATE_STANDARD, RATE_MODERATE, RATE_RELAXED

router = APIRouter(prefix="/api/v1/genfin", tags=["GenFin"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str

class AccountResponse(BaseModel):
    id: int
    name: str
    account_type: str
    account_number: Optional[str] = None
    sub_type: Optional[str] = None
    description: Optional[str] = None
    balance: Optional[float] = 0

class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]
    total: int

class CustomerResponse(BaseModel):
    customer_id: str
    display_name: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = "active"
    balance: Optional[float] = 0

    model_config = {"extra": "allow"}

class CustomerListResponse(BaseModel):
    customers: List[Dict[str, Any]]
    total: int

class VendorResponse(BaseModel):
    vendor_id: str
    display_name: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = "active"
    balance: Optional[float] = 0

    model_config = {"extra": "allow"}

class VendorListResponse(BaseModel):
    vendors: List[Dict[str, Any]]
    total: int

class EmployeeResponse(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = "active"

    model_config = {"extra": "allow"}

class EmployeeListResponse(BaseModel):
    employees: List[Dict[str, Any]]
    total: int

class InvoiceLineResponse(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float

class InvoiceResponse(BaseModel):
    id: int
    customer_id: int
    invoice_number: Optional[str] = None
    invoice_date: date
    due_date: date
    status: str
    total: float
    balance_due: Optional[float] = None
    lines: Optional[List[InvoiceLineResponse]] = None
    memo: Optional[str] = None

class InvoiceListResponse(BaseModel):
    invoices: List[InvoiceResponse]
    total: int

class BillResponse(BaseModel):
    id: int
    vendor_id: int
    bill_number: Optional[str] = None
    bill_date: date
    due_date: date
    status: str
    total: float
    balance_due: Optional[float] = None
    memo: Optional[str] = None

class BillListResponse(BaseModel):
    bills: List[BillResponse]
    total: int

class CheckResponse(BaseModel):
    id: int
    bank_account_id: int
    check_number: Optional[str] = None
    payee_name: str
    check_date: date
    amount: float
    status: str
    memo: Optional[str] = None

class CheckListResponse(BaseModel):
    checks: List[CheckResponse]
    total: int

class BankAccountResponse(BaseModel):
    id: int
    account_name: str
    account_type: str
    account_number: Optional[str] = None
    routing_number: Optional[str] = None
    balance: float

class BankAccountListResponse(BaseModel):
    accounts: List[BankAccountResponse]
    total: int

class TrialBalanceResponse(BaseModel):
    as_of_date: date
    accounts: List[Dict[str, Any]]
    total_debits: float
    total_credits: float

class BalanceSheetResponse(BaseModel):
    as_of_date: date
    assets: Dict[str, Any]
    liabilities: Dict[str, Any]
    equity: Dict[str, Any]

class ProfitLossResponse(BaseModel):
    """P&L Response - matches service output format"""
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    revenue: Dict[str, Any]
    expenses: Optional[Dict[str, Any]] = None
    operating_expenses: Optional[Dict[str, Any]] = None
    net_income: float

    model_config = {"extra": "allow"}

class CashFlowReportResponse(BaseModel):
    """Cash Flow Response - matches service output format"""
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    operating: Optional[Dict[str, Any]] = None
    operating_activities: Optional[Dict[str, Any]] = None
    investing: Optional[Dict[str, Any]] = None
    investing_activities: Optional[Dict[str, Any]] = None
    financing: Optional[Dict[str, Any]] = None
    financing_activities: Optional[Dict[str, Any]] = None
    net_change: Optional[float] = None
    net_change_in_cash: Optional[float] = None

    model_config = {"extra": "allow"}

class AgingReportResponse(BaseModel):
    """Aging Report - matches service output format"""
    as_of_date: Optional[str] = None
    # Service returns nested 'aging' dict
    aging: Optional[Dict[str, Any]] = None
    # Or flat fields for legacy format
    current: Optional[float] = None
    days_1_30: Optional[float] = None
    days_31_60: Optional[float] = None
    days_61_90: Optional[float] = None
    over_90: Optional[float] = None
    total: Optional[float] = None
    details: Optional[List[Dict[str, Any]]] = None

    model_config = {"extra": "allow"}

class PayScheduleResponse(BaseModel):
    id: int
    name: str
    frequency: str
    next_pay_date: date

class PayScheduleListResponse(BaseModel):
    schedules: List[PayScheduleResponse]
    total: int

class PayRunResponse(BaseModel):
    id: int
    schedule_id: int
    pay_date: date
    status: str
    total_gross: float
    total_net: float

class PayRunListResponse(BaseModel):
    pay_runs: List[PayRunResponse]
    total: int

class BankFeedSummaryResponse(BaseModel):
    pending_count: int
    matched_count: int
    total_pending_amount: float

class BankFeedTransactionResponse(BaseModel):
    id: int
    bank_account_id: int
    transaction_date: date
    amount: float
    description: str
    status: str

class BankFeedTransactionListResponse(BaseModel):
    transactions: List[BankFeedTransactionResponse]
    total: int

class FixedAssetResponse(BaseModel):
    id: int
    name: str
    category: str
    purchase_date: date
    purchase_price: float
    depreciation_method: str
    useful_life_years: int
    salvage_value: float
    accumulated_depreciation: Optional[float] = 0
    book_value: Optional[float] = None

class FixedAssetListResponse(BaseModel):
    assets: List[FixedAssetResponse]
    total: int

class FixedAssetsSummaryResponse(BaseModel):
    """Fixed Assets Summary - matches service output format"""
    total_assets: int
    total_purchase_price: Optional[float] = None
    total_accumulated_depreciation: Optional[float] = None
    total_book_value: Optional[float] = None
    total_cost: Optional[float] = None
    by_category: Dict[str, Any]

    model_config = {"extra": "allow"}

class GenFinEntityResponse(BaseModel):
    id: int
    name: str
    entity_type: str
    tax_id: Optional[str] = None
    status: Optional[str] = "active"

class GenFinEntityListResponse(BaseModel):
    entities: List[GenFinEntityResponse]
    total: int

class EntitiesSummaryResponse(BaseModel):
    total_entities: int
    by_type: Dict[str, int]


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health", response_model=HealthResponse, tags=["GenFin"])
@limiter.limit(RATE_RELAXED)
async def genfin_health_check(request: Request):
    """GenFin health check endpoint."""
    return {"status": "ok", "service": "genfin"}


# ============================================================================
# CHART OF ACCOUNTS
# ============================================================================

# Note: GET/POST /accounts endpoints are in main.py with proper Pydantic model support


# ============================================================================
# CUSTOMERS
# ============================================================================

@router.get("/customers", response_model=CustomerListResponse, tags=["Customers"])
async def list_customers(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List customers."""
    from services.genfin_receivables_service import genfin_receivables_service

    customers = genfin_receivables_service.list_customers(status=status)
    return {"customers": customers, "total": len(customers)}


@router.post("/customers", response_model=CustomerResponse, tags=["Customers"])
async def create_customer(
    display_name: str,
    company_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new customer."""
    from services.genfin_receivables_service import genfin_receivables_service

    result = genfin_receivables_service.create_customer(
        display_name=display_name,
        company_name=company_name,
        email=email,
        phone=phone
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create customer"))

    return result.get("customer")


@router.get("/customers/{customer_id}", response_model=CustomerResponse, tags=["Customers"])
async def get_customer(
    customer_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get customer details."""
    from services.genfin_receivables_service import genfin_receivables_service

    customer = genfin_receivables_service.get_customer(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


# ============================================================================
# VENDORS
# ============================================================================

@router.get("/vendors", response_model=VendorListResponse, tags=["Vendors"])
async def list_vendors(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List vendors."""
    from services.genfin_payables_service import genfin_payables_service

    vendors = genfin_payables_service.list_vendors(status=status)
    return {"vendors": vendors, "total": len(vendors)}


@router.post("/vendors", response_model=VendorResponse, tags=["Vendors"])
async def create_vendor(
    display_name: str,
    company_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new vendor."""
    from services.genfin_payables_service import genfin_payables_service

    result = genfin_payables_service.create_vendor(
        display_name=display_name,
        company_name=company_name,
        email=email,
        phone=phone
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create vendor"))

    return result.get("vendor")


@router.get("/vendors/{vendor_id}", response_model=VendorResponse, tags=["Vendors"])
async def get_vendor(
    vendor_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get vendor details."""
    from services.genfin_payables_service import genfin_payables_service

    vendor = genfin_payables_service.get_vendor(vendor_id)

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return vendor


# ============================================================================
# EMPLOYEES
# ============================================================================

@router.get("/employees", response_model=EmployeeListResponse, tags=["Employees"])
async def list_genfin_employees(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List employees."""
    from services.genfin_payroll_service import genfin_payroll_service

    result = genfin_payroll_service.list_employees(status=status)
    # Service returns {"employees": [...], "total": N}
    return result


@router.post("/employees", response_model=EmployeeResponse, tags=["Employees"])
async def create_genfin_employee(
    first_name: str,
    last_name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new employee."""
    from services.genfin_payroll_service import genfin_payroll_service

    result = genfin_payroll_service.create_employee(
        first_name=first_name,
        last_name=last_name,
        email=email or "",
        phone=phone or ""
    )

    if not result or not result.get("employee_id"):
        raise HTTPException(status_code=400, detail="Failed to create employee")

    return result


@router.get("/employees/{employee_id}", response_model=EmployeeResponse, tags=["Employees"])
async def get_genfin_employee(
    employee_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get employee by ID."""
    from services.genfin_payroll_service import genfin_payroll_service

    result = genfin_payroll_service.get_employee(employee_id)
    if not result:
        raise HTTPException(status_code=404, detail="Employee not found")

    return result


# ============================================================================
# DIRECT DEPOSIT
# ============================================================================

class DirectDepositRequest(BaseModel):
    routing_number: str
    account_number: str
    account_type: str = "checking"
    amount_type: str = "full"  # "full" or "fixed"
    fixed_amount: Optional[float] = None


class DirectDepositResponse(BaseModel):
    employee_id: str
    routing_number: str
    account_number_last4: str
    account_type: str
    status: str


@router.get("/employees/{employee_id}/direct-deposit", response_model=DirectDepositResponse, tags=["Direct Deposit"])
async def get_direct_deposit(
    employee_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get direct deposit info for an employee."""
    from services.genfin_payroll_service import genfin_payroll_service

    emp = genfin_payroll_service.get_employee(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    return {
        "employee_id": employee_id,
        "routing_number": emp.get("bank_routing_number", ""),
        "account_number_last4": emp.get("bank_account_number", "")[-4:] if emp.get("bank_account_number") else "",
        "account_type": emp.get("bank_account_type", "checking"),
        "status": "active" if emp.get("has_direct_deposit") else "inactive"
    }


@router.put("/employees/{employee_id}/direct-deposit", response_model=DirectDepositResponse, tags=["Direct Deposit"])
async def update_direct_deposit(
    employee_id: str,
    dd_request: DirectDepositRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update direct deposit info for an employee."""
    from services.genfin_payroll_service import genfin_payroll_service

    result = genfin_payroll_service.update_employee(
        employee_id,
        bank_routing_number=dd_request.routing_number,
        bank_account_number=dd_request.account_number,
        bank_account_type=dd_request.account_type,
        payment_method="direct_deposit"
    )

    if not result.get("success", True):
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to update"))

    return {
        "employee_id": employee_id,
        "routing_number": dd_request.routing_number,
        "account_number_last4": dd_request.account_number[-4:],
        "account_type": dd_request.account_type,
        "status": "active"
    }


# ============================================================================
# TAX WITHHOLDINGS
# ============================================================================

class TaxWithholdingRequest(BaseModel):
    filing_status: str
    federal_allowances: int = 0
    federal_additional: float = 0.0
    state_allowances: int = 0
    state_additional: float = 0.0
    is_exempt: bool = False


class TaxWithholdingResponse(BaseModel):
    employee_id: str
    filing_status: str
    federal_allowances: int
    federal_additional: float
    state_allowances: int
    state_additional: float
    is_exempt: bool


class TaxWithholdingListResponse(BaseModel):
    withholdings: List[TaxWithholdingResponse]
    total: int


@router.get("/tax/withholdings", response_model=TaxWithholdingListResponse, tags=["Tax"])
async def list_tax_withholdings(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List tax withholding settings for all employees."""
    from services.genfin_payroll_service import genfin_payroll_service

    employees = genfin_payroll_service.list_employees()
    withholdings = []

    for emp in employees.get("employees", []):
        withholdings.append({
            "employee_id": emp.get("employee_id", ""),
            "filing_status": emp.get("filing_status", "single"),
            "federal_allowances": emp.get("federal_allowances", 0),
            "federal_additional": emp.get("federal_additional_withholding", 0.0),
            "state_allowances": emp.get("state_allowances", 0),
            "state_additional": emp.get("state_additional_withholding", 0.0),
            "is_exempt": emp.get("is_exempt", False)
        })

    return {"withholdings": withholdings, "total": len(withholdings)}


@router.get("/employees/{employee_id}/tax-withholding", response_model=TaxWithholdingResponse, tags=["Tax"])
async def get_tax_withholding(
    employee_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get tax withholding info for an employee."""
    from services.genfin_payroll_service import genfin_payroll_service

    emp = genfin_payroll_service.get_employee(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    return {
        "employee_id": employee_id,
        "filing_status": emp.get("filing_status", "single"),
        "federal_allowances": emp.get("federal_allowances", 0),
        "federal_additional": emp.get("federal_additional_withholding", 0.0),
        "state_allowances": emp.get("state_allowances", 0),
        "state_additional": emp.get("state_additional_withholding", 0.0),
        "is_exempt": False
    }


@router.put("/employees/{employee_id}/tax-withholding", response_model=TaxWithholdingResponse, tags=["Tax"])
async def update_tax_withholding(
    employee_id: str,
    tax_request: TaxWithholdingRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update tax withholding for an employee."""
    from services.genfin_payroll_service import genfin_payroll_service

    result = genfin_payroll_service.update_employee(
        employee_id,
        filing_status=tax_request.filing_status,
        federal_allowances=tax_request.federal_allowances,
        federal_additional_withholding=tax_request.federal_additional,
        state_allowances=tax_request.state_allowances,
        state_additional_withholding=tax_request.state_additional,
        is_exempt=tax_request.is_exempt
    )

    if not result.get("success", True):
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to update"))

    return {
        "employee_id": employee_id,
        "filing_status": tax_request.filing_status,
        "federal_allowances": tax_request.federal_allowances,
        "federal_additional": tax_request.federal_additional,
        "state_allowances": tax_request.state_allowances,
        "state_additional": tax_request.state_additional,
        "is_exempt": tax_request.is_exempt
    }


# ============================================================================
# INVOICES
# ============================================================================

# Note: GET/POST /invoices endpoints are in main.py with proper Pydantic model support


# ============================================================================
# BILLS
# ============================================================================

# Note: GET/POST /bills endpoints are in main.py with proper Pydantic model support


# ============================================================================
# CHECKS
# ============================================================================

# Note: GET/POST /checks endpoints are in main.py with proper Pydantic model support


# ============================================================================
# BANK ACCOUNTS
# ============================================================================

# Note: GET/POST /bank-accounts endpoints are in main.py with proper Pydantic model support


# ============================================================================
# FINANCIAL REPORTS
# ============================================================================

@router.get("/reports/trial-balance", response_model=TrialBalanceResponse, tags=["Reports"])
@limiter.limit(RATE_MODERATE)
async def get_trial_balance(
    request: Request,
    as_of_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get trial balance report. Rate limited: 30/minute."""
    from services.genfin_reports_service import genfin_reports_service

    return genfin_reports_service.get_trial_balance(as_of_date=as_of_date)


@router.get("/reports/balance-sheet", response_model=BalanceSheetResponse, tags=["Reports"])
@limiter.limit(RATE_MODERATE)
async def get_balance_sheet(
    request: Request,
    as_of_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get balance sheet report. Rate limited: 30/minute."""
    from services.genfin_reports_service import genfin_reports_service

    return genfin_reports_service.get_balance_sheet(as_of_date=as_of_date)


@router.get("/reports/profit-loss", response_model=ProfitLossResponse, tags=["Reports"])
@limiter.limit(RATE_MODERATE)
async def get_profit_loss(
    request: Request,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get profit and loss statement. Rate limited: 30/minute."""
    from services.genfin_reports_service import genfin_reports_service

    return genfin_reports_service.get_profit_loss(
        start_date=start_date,
        end_date=end_date
    )


@router.get("/reports/cash-flow", response_model=CashFlowReportResponse, tags=["Reports"])
@limiter.limit(RATE_MODERATE)
async def get_cash_flow_report(
    request: Request,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get cash flow report. Rate limited: 30/minute."""
    from services.genfin_reports_service import genfin_reports_service

    return genfin_reports_service.get_cash_flow(
        start_date=start_date,
        end_date=end_date
    )


@router.get("/reports/ar-aging", response_model=AgingReportResponse, tags=["Reports"])
@limiter.limit(RATE_MODERATE)
async def get_ar_aging(
    request: Request,
    as_of_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get accounts receivable aging report. Rate limited: 30/minute."""
    from services.genfin_receivables_service import genfin_receivables_service

    return genfin_receivables_service.get_ar_aging(as_of_date=as_of_date)


@router.get("/reports/ap-aging", response_model=AgingReportResponse, tags=["Reports"])
@limiter.limit(RATE_MODERATE)
async def get_ap_aging(
    request: Request,
    as_of_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get accounts payable aging report. Rate limited: 30/minute."""
    from services.genfin_payables_service import genfin_payables_service

    return genfin_payables_service.get_ap_aging(as_of_date=as_of_date)


# ============================================================================
# PAYROLL
# ============================================================================

# Note: GET /payroll/schedules and GET /payroll/runs are in main.py
# They return list format directly rather than wrapped responses

@router.post("/payroll/schedules", response_model=PayScheduleResponse, tags=["Payroll"])
async def create_pay_schedule(
    name: str,
    frequency: str,
    next_pay_date: date,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Create a pay schedule."""
    from services.genfin_payroll_service import genfin_payroll_service

    result = genfin_payroll_service.create_pay_schedule(
        name=name,
        frequency=frequency,
        next_pay_date=next_pay_date
    )

    return result


# ============================================================================
# BANK FEEDS
# ============================================================================

# Note: Bank feeds endpoints are in main.py with proper method names and Pydantic models


# ============================================================================
# FIXED ASSETS
# ============================================================================

# Note: GET/POST /fixed-assets endpoints are in main.py with proper Pydantic model support

@router.get("/fixed-assets/summary", response_model=FixedAssetsSummaryResponse, tags=["Fixed Assets"])
async def get_fixed_assets_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get fixed assets summary."""
    from services.genfin_fixed_assets_service import genfin_fixed_assets_service

    return genfin_fixed_assets_service.get_service_summary()


# ============================================================================
# ENTITIES (MULTI-COMPANY)
# ============================================================================

# Note: GET /entities endpoint is in main.py with proper Pydantic model support

@router.get("/entities/summary", response_model=EntitiesSummaryResponse, tags=["Entities"])
async def get_entities_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get entities summary."""
    from services.genfin_entity_service import get_entity_service

    entity_service = get_entity_service()
    return entity_service.get_service_summary()


