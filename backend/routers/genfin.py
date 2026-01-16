"""
GenFin Accounting Router
AgTools v6.13.0

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

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from middleware.auth_middleware import get_current_active_user, require_manager, AuthenticatedUser

router = APIRouter(prefix="/api/v1/genfin", tags=["GenFin"])


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health", tags=["GenFin"])
async def genfin_health_check():
    """GenFin health check endpoint."""
    return {"status": "ok", "service": "genfin"}


# ============================================================================
# CHART OF ACCOUNTS
# ============================================================================

@router.get("/accounts", tags=["Accounts"])
async def list_accounts(
    account_type: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List chart of accounts."""
    from services.genfin_core_service import genfin_core_service

    return genfin_core_service.list_accounts(account_type=account_type)


@router.post("/accounts", tags=["Accounts"])
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


@router.get("/accounts/{account_id}", tags=["Accounts"])
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

@router.get("/customers", tags=["Customers"])
async def list_customers(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List customers."""
    from services.genfin_receivables_service import genfin_receivables_service

    return genfin_receivables_service.list_customers(status=status)


@router.post("/customers", tags=["Customers"])
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

    return result


@router.get("/customers/{customer_id}", tags=["Customers"])
async def get_customer(
    customer_id: int,
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

@router.get("/vendors", tags=["Vendors"])
async def list_vendors(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List vendors."""
    from services.genfin_payables_service import genfin_payables_service

    return genfin_payables_service.list_vendors(status=status)


@router.post("/vendors", tags=["Vendors"])
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

    return result


@router.get("/vendors/{vendor_id}", tags=["Vendors"])
async def get_vendor(
    vendor_id: int,
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

@router.get("/employees", tags=["Employees"])
async def list_genfin_employees(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List employees."""
    from services.genfin_payroll_service import genfin_payroll_service

    return genfin_payroll_service.list_employees(status=status)


@router.post("/employees", tags=["Employees"])
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
        email=email,
        phone=phone
    )

    return result


# ============================================================================
# INVOICES
# ============================================================================

@router.get("/invoices", tags=["Invoices"])
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


@router.post("/invoices", tags=["Invoices"])
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


@router.get("/invoices/{invoice_id}", tags=["Invoices"])
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

@router.get("/bills", tags=["Bills"])
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


@router.post("/bills", tags=["Bills"])
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

@router.get("/checks", tags=["Checks"])
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


@router.post("/checks", tags=["Checks"])
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

@router.get("/bank-accounts", tags=["Banking"])
async def list_bank_accounts(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List bank accounts."""
    from services.genfin_banking_service import genfin_banking_service

    return genfin_banking_service.list_bank_accounts()


@router.post("/bank-accounts", tags=["Banking"])
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

@router.get("/reports/trial-balance", tags=["Reports"])
async def get_trial_balance(
    as_of_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get trial balance report."""
    from services.genfin_reports_service import genfin_reports_service

    return genfin_reports_service.get_trial_balance(as_of_date=as_of_date)


@router.get("/reports/balance-sheet", tags=["Reports"])
async def get_balance_sheet(
    as_of_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get balance sheet report."""
    from services.genfin_reports_service import genfin_reports_service

    return genfin_reports_service.get_balance_sheet(as_of_date=as_of_date)


@router.get("/reports/profit-loss", tags=["Reports"])
async def get_profit_loss(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get profit and loss statement."""
    from services.genfin_reports_service import genfin_reports_service

    return genfin_reports_service.get_profit_loss(
        start_date=start_date,
        end_date=end_date
    )


@router.get("/reports/cash-flow", tags=["Reports"])
async def get_cash_flow_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get cash flow report."""
    from services.genfin_reports_service import genfin_reports_service

    return genfin_reports_service.get_cash_flow(
        start_date=start_date,
        end_date=end_date
    )


@router.get("/reports/ar-aging", tags=["Reports"])
async def get_ar_aging(
    as_of_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get accounts receivable aging report."""
    from services.genfin_reports_service import genfin_reports_service

    return genfin_reports_service.get_ar_aging(as_of_date=as_of_date)


@router.get("/reports/ap-aging", tags=["Reports"])
async def get_ap_aging(
    as_of_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get accounts payable aging report."""
    from services.genfin_reports_service import genfin_reports_service

    return genfin_reports_service.get_ap_aging(as_of_date=as_of_date)


# ============================================================================
# PAYROLL
# ============================================================================

@router.get("/payroll/schedules", tags=["Payroll"])
async def list_pay_schedules(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List pay schedules."""
    from services.genfin_payroll_service import genfin_payroll_service

    return genfin_payroll_service.list_pay_schedules()


@router.post("/payroll/schedules", tags=["Payroll"])
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


@router.get("/payroll/runs", tags=["Payroll"])
async def list_pay_runs(
    status: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List pay runs."""
    from services.genfin_payroll_service import genfin_payroll_service

    return genfin_payroll_service.list_pay_runs(status=status)


# ============================================================================
# RECURRING TRANSACTIONS
# ============================================================================

@router.get("/recurring", tags=["Recurring"])
async def list_recurring_templates(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List recurring transaction templates."""
    from services.genfin_recurring_service import genfin_recurring_service

    return genfin_recurring_service.list_templates()


@router.post("/recurring", tags=["Recurring"])
async def create_recurring_template(
    template_type: str,
    name: str,
    frequency: str,
    amount: float,
    next_date: date,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a recurring transaction template."""
    from services.genfin_recurring_service import genfin_recurring_service

    result = genfin_recurring_service.create_template(
        template_type=template_type,
        name=name,
        frequency=frequency,
        amount=amount,
        next_date=next_date
    )

    return result


# ============================================================================
# BANK FEEDS
# ============================================================================

@router.get("/bank-feeds/summary", tags=["Bank Feeds"])
async def get_bank_feed_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get bank feed summary."""
    from services.genfin_bank_feeds_service import genfin_bank_feeds_service

    return genfin_bank_feeds_service.get_summary()


@router.get("/bank-feeds/transactions", tags=["Bank Feeds"])
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

@router.get("/fixed-assets", tags=["Fixed Assets"])
async def list_fixed_assets(
    category: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List fixed assets."""
    from services.genfin_fixed_assets_service import genfin_fixed_assets_service

    return genfin_fixed_assets_service.list_assets(category=category)


@router.post("/fixed-assets", tags=["Fixed Assets"])
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


@router.get("/fixed-assets/summary", tags=["Fixed Assets"])
async def get_fixed_assets_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get fixed assets summary."""
    from services.genfin_fixed_assets_service import genfin_fixed_assets_service

    return genfin_fixed_assets_service.get_service_summary()


# ============================================================================
# ENTITIES (MULTI-COMPANY)
# ============================================================================

@router.get("/entities", tags=["Entities"])
async def list_genfin_entities(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List entities (companies)."""
    from services.genfin_core_service import genfin_core_service

    return genfin_core_service.list_entities()


@router.get("/entities/summary", tags=["Entities"])
async def get_entities_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get entities summary."""
    from services.genfin_core_service import genfin_core_service

    return genfin_core_service.get_entities_summary()


# ============================================================================
# 1099 TRACKING
# ============================================================================

@router.get("/1099/summary", tags=["1099"])
async def get_1099_summary(
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get 1099 tracking summary."""
    from services.genfin_1099_service import genfin_1099_service

    return genfin_1099_service.get_summary(year=year)


@router.get("/1099/vendors", tags=["1099"])
async def list_1099_vendors(
    year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List vendors requiring 1099."""
    from services.genfin_1099_service import genfin_1099_service

    return genfin_1099_service.list_1099_vendors(year=year)
