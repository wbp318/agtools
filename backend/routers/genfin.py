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

    class Config:
        extra = "allow"

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

    class Config:
        extra = "allow"

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

    class Config:
        extra = "allow"

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
    start_date: date
    end_date: date
    revenue: Dict[str, Any]
    expenses: Dict[str, Any]
    net_income: float

class CashFlowReportResponse(BaseModel):
    start_date: date
    end_date: date
    operating: Dict[str, Any]
    investing: Dict[str, Any]
    financing: Dict[str, Any]
    net_change: float

class AgingReportResponse(BaseModel):
    as_of_date: date
    current: float
    days_1_30: float
    days_31_60: float
    days_61_90: float
    over_90: float
    total: float
    details: List[Dict[str, Any]]

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
    total_assets: int
    total_purchase_price: float
    total_accumulated_depreciation: float
    total_book_value: float
    by_category: Dict[str, float]

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

@router.get("/accounts", response_model=AccountListResponse, tags=["Accounts"])
async def list_accounts(
    account_type: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List chart of accounts."""
    from services.genfin_core_service import genfin_core_service

    return genfin_core_service.list_accounts(account_type=account_type)


@router.post("/accounts", response_model=AccountResponse, tags=["Accounts"])
async def create_account(
    name: str,
    account_type: str,
    account_number: Optional[str] = None,
    sub_type: Optional[str] = None,
    description: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new account."""
    from services.genfin_core_service import genfin_core_service

    result = genfin_core_service.create_account(
        name=name,
        account_type=account_type,
        account_number=account_number,
        sub_type=sub_type,
        description=description
    )

    return result


@router.get("/accounts/{account_id}", response_model=AccountResponse, tags=["Accounts"])
async def get_account(
    account_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get account details."""
    from services.genfin_core_service import genfin_core_service

    account = genfin_core_service.get_account(account_id)

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return account


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

@router.get("/invoices", response_model=InvoiceListResponse, tags=["Invoices"])
async def list_invoices(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List invoices."""
    from services.genfin_receivables_service import genfin_receivables_service

    return genfin_receivables_service.list_invoices(
        status=status,
        customer_id=customer_id
    )


@router.post("/invoices", response_model=InvoiceResponse, tags=["Invoices"])
async def create_invoice(
    customer_id: int,
    invoice_date: date,
    due_date: date,
    lines: List[dict],
    memo: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new invoice."""
    from services.genfin_receivables_service import genfin_receivables_service

    result = genfin_receivables_service.create_invoice(
        customer_id=customer_id,
        invoice_date=invoice_date,
        due_date=due_date,
        lines=lines,
        memo=memo
    )

    return result


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse, tags=["Invoices"])
async def get_invoice(
    invoice_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get invoice details."""
    from services.genfin_receivables_service import genfin_receivables_service

    invoice = genfin_receivables_service.get_invoice(invoice_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return invoice


# ============================================================================
# BILLS
# ============================================================================

@router.get("/bills", response_model=BillListResponse, tags=["Bills"])
async def list_bills(
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List bills."""
    from services.genfin_payables_service import genfin_payables_service

    return genfin_payables_service.list_bills(
        status=status,
        vendor_id=vendor_id
    )


@router.post("/bills", response_model=BillResponse, tags=["Bills"])
async def create_bill(
    vendor_id: int,
    bill_date: date,
    due_date: date,
    lines: List[dict],
    memo: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new bill."""
    from services.genfin_payables_service import genfin_payables_service

    result = genfin_payables_service.create_bill(
        vendor_id=vendor_id,
        bill_date=bill_date,
        due_date=due_date,
        lines=lines,
        memo=memo
    )

    return result


# ============================================================================
# CHECKS
# ============================================================================

@router.get("/checks", response_model=CheckListResponse, tags=["Checks"])
async def list_checks(
    bank_account_id: Optional[int] = None,
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List checks."""
    from services.genfin_banking_service import genfin_banking_service

    return genfin_banking_service.list_checks(
        bank_account_id=bank_account_id,
        status=status
    )


@router.post("/checks", response_model=CheckResponse, tags=["Checks"])
async def create_check(
    bank_account_id: int,
    payee_name: str,
    check_date: date,
    amount: float,
    expenses: Optional[List[dict]] = None,
    memo: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Write a check."""
    from services.genfin_banking_service import genfin_banking_service

    result = genfin_banking_service.create_check(
        bank_account_id=bank_account_id,
        payee_name=payee_name,
        check_date=check_date,
        amount=amount,
        expenses=expenses,
        memo=memo
    )

    return result


# ============================================================================
# BANK ACCOUNTS
# ============================================================================

@router.get("/bank-accounts", response_model=BankAccountListResponse, tags=["Banking"])
async def list_bank_accounts(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List bank accounts."""
    from services.genfin_banking_service import genfin_banking_service

    return genfin_banking_service.list_bank_accounts()


@router.post("/bank-accounts", response_model=BankAccountResponse, tags=["Banking"])
async def create_bank_account(
    account_name: str,
    account_type: str,
    account_number: Optional[str] = None,
    routing_number: Optional[str] = None,
    opening_balance: float = 0,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new bank account."""
    from services.genfin_banking_service import genfin_banking_service

    result = genfin_banking_service.create_bank_account(
        account_name=account_name,
        account_type=account_type,
        account_number=account_number,
        routing_number=routing_number,
        opening_balance=opening_balance
    )

    return result


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
    from services.genfin_reports_service import genfin_reports_service

    return genfin_reports_service.get_ar_aging(as_of_date=as_of_date)


@router.get("/reports/ap-aging", response_model=AgingReportResponse, tags=["Reports"])
@limiter.limit(RATE_MODERATE)
async def get_ap_aging(
    request: Request,
    as_of_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get accounts payable aging report. Rate limited: 30/minute."""
    from services.genfin_reports_service import genfin_reports_service

    return genfin_reports_service.get_ap_aging(as_of_date=as_of_date)


# ============================================================================
# PAYROLL
# ============================================================================

@router.get("/payroll/schedules", response_model=PayScheduleListResponse, tags=["Payroll"])
async def list_pay_schedules(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List pay schedules."""
    from services.genfin_payroll_service import genfin_payroll_service

    return genfin_payroll_service.list_pay_schedules()


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


@router.get("/payroll/runs", response_model=PayRunListResponse, tags=["Payroll"])
async def list_pay_runs(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List pay runs."""
    from services.genfin_payroll_service import genfin_payroll_service

    return genfin_payroll_service.list_pay_runs(status=status)


# ============================================================================
# BANK FEEDS
# ============================================================================

@router.get("/bank-feeds/summary", response_model=BankFeedSummaryResponse, tags=["Bank Feeds"])
async def get_bank_feed_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get bank feed summary."""
    from services.genfin_bank_feeds_service import genfin_bank_feeds_service

    return genfin_bank_feeds_service.get_summary()


@router.get("/bank-feeds/transactions", response_model=BankFeedTransactionListResponse, tags=["Bank Feeds"])
async def list_bank_feed_transactions(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List bank feed transactions."""
    from services.genfin_bank_feeds_service import genfin_bank_feeds_service

    return genfin_bank_feeds_service.list_transactions(status=status)


# ============================================================================
# FIXED ASSETS
# ============================================================================

@router.get("/fixed-assets", response_model=FixedAssetListResponse, tags=["Fixed Assets"])
async def list_fixed_assets(
    category: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List fixed assets."""
    from services.genfin_fixed_assets_service import genfin_fixed_assets_service

    return genfin_fixed_assets_service.list_assets(category=category)


@router.post("/fixed-assets", response_model=FixedAssetResponse, tags=["Fixed Assets"])
async def create_fixed_asset(
    name: str = Query(...),
    category: str = Query(...),
    purchase_date: date = Query(...),
    purchase_price: float = Query(...),
    depreciation_method: str = Query("straight_line"),
    useful_life_years: int = Query(7),
    salvage_value: float = Query(0),
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a fixed asset."""
    from services.genfin_fixed_assets_service import genfin_fixed_assets_service

    result = genfin_fixed_assets_service.create_asset(
        name=name,
        category=category,
        purchase_date=purchase_date,
        purchase_price=purchase_price,
        depreciation_method=depreciation_method,
        useful_life_years=useful_life_years,
        salvage_value=salvage_value
    )

    return result


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

@router.get("/entities", response_model=GenFinEntityListResponse, tags=["Entities"])
async def list_genfin_entities(
    active_only: bool = True,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List entities (companies)."""
    from services.genfin_entity_service import get_entity_service

    entity_service = get_entity_service()
    entities = entity_service.list_entities(active_only)

    # Convert service EntityResponse objects to router's simpler GenFinEntityResponse format
    entity_list = [
        {
            "id": e.id,
            "name": e.name,
            "entity_type": e.entity_type,
            "tax_id": e.tax_id,
            "status": e.status
        }
        for e in entities
    ]
    return {"entities": entity_list, "total": len(entity_list)}


@router.get("/entities/summary", response_model=EntitiesSummaryResponse, tags=["Entities"])
async def get_entities_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get entities summary."""
    from services.genfin_entity_service import get_entity_service

    entity_service = get_entity_service()
    return entity_service.get_service_summary()


