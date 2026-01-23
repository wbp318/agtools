"""
GenFin Reports Service - P&L, Balance Sheet, Cash Flow, Custom Reports
Complete financial reporting for farm operations
SQLite persistent storage implementation
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid
import sqlite3
import json

from .genfin_core_service import genfin_core_service, AccountType, AccountSubType


class ReportType(Enum):
    """Report types"""
    PROFIT_LOSS = "profit_loss"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    TRIAL_BALANCE = "trial_balance"
    GENERAL_LEDGER = "general_ledger"
    AR_AGING = "ar_aging"
    AP_AGING = "ap_aging"
    CUSTOM = "custom"


class ReportPeriod(Enum):
    """Report period options"""
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    YTD = "ytd"
    CUSTOM = "custom"


@dataclass
class SavedReport:
    """Saved/scheduled report configuration"""
    report_id: str
    name: str
    report_type: ReportType
    parameters: Dict
    created_by: str
    is_scheduled: bool = False
    schedule_frequency: str = ""  # daily, weekly, monthly
    last_run: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


class GenFinReportsService:
    """
    GenFin Financial Reports Service

    Complete financial reporting:
    - Profit & Loss Statement
    - Balance Sheet
    - Cash Flow Statement
    - Trial Balance
    - General Ledger
    - AR/AP Aging
    - Comparative reports
    - Custom report builder

    Uses SQLite for persistent storage.
    """

    _instance = None

    def __new__(cls, db_path: str = "agtools.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "agtools.db"):
        if self._initialized:
            return

        self.db_path = db_path
        self._init_tables()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Create database tables if they don't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Saved reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_saved_reports (
                    report_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    is_scheduled INTEGER DEFAULT 0,
                    schedule_frequency TEXT DEFAULT '',
                    last_run TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            conn.commit()

    # ==================== PROFIT & LOSS ====================

    def get_profit_loss(
        self,
        start_date: str = None,
        end_date: str = None,
        compare_prior_period: bool = False,
        compare_prior_year: bool = False,
        group_by_month: bool = False,
        class_id: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> Dict:
        """Generate Profit & Loss Statement"""
        # Handle null dates with sensible defaults
        if start_date is None:
            start_date = date(date.today().year, 1, 1).isoformat()
        if end_date is None:
            end_date = date.today().isoformat()

        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Get all revenue and expense accounts
        revenue_accounts = []
        expense_accounts = []
        cogs_accounts = []

        coa = genfin_core_service.get_chart_of_accounts()

        for acct in coa["revenue"]:
            balance = self._get_account_balance_for_period(
                acct["account_id"], s_date, e_date, class_id, location_id
            )
            if balance != 0:
                revenue_accounts.append({
                    "account_id": acct["account_id"],
                    "account_number": acct["account_number"],
                    "account_name": acct["name"],
                    "balance": balance
                })

        for acct in coa["expenses"]:
            balance = self._get_account_balance_for_period(
                acct["account_id"], s_date, e_date, class_id, location_id
            )
            if balance != 0:
                account_info = genfin_core_service.get_account(acct["account_id"])
                sub_type = account_info.get("sub_type", "") if account_info else ""

                entry = {
                    "account_id": acct["account_id"],
                    "account_number": acct["account_number"],
                    "account_name": acct["name"],
                    "balance": balance
                }

                if sub_type == "cost_of_goods":
                    cogs_accounts.append(entry)
                else:
                    expense_accounts.append(entry)

        # Calculate totals
        total_revenue = sum(a["balance"] for a in revenue_accounts)
        total_cogs = sum(a["balance"] for a in cogs_accounts)
        gross_profit = total_revenue - total_cogs
        total_expenses = sum(a["balance"] for a in expense_accounts)
        net_income = gross_profit - total_expenses

        # Build comparison data if requested
        comparison = None
        if compare_prior_period or compare_prior_year:
            comparison = {}

            if compare_prior_period:
                period_days = (e_date - s_date).days
                prior_end = s_date - timedelta(days=1)
                prior_start = prior_end - timedelta(days=period_days)

                prior_revenue = sum(
                    self._get_account_balance_for_period(a["account_id"], prior_start, prior_end)
                    for a in revenue_accounts
                )
                prior_cogs = sum(
                    self._get_account_balance_for_period(a["account_id"], prior_start, prior_end)
                    for a in cogs_accounts
                )
                prior_expenses = sum(
                    self._get_account_balance_for_period(a["account_id"], prior_start, prior_end)
                    for a in expense_accounts
                )

                comparison["prior_period"] = {
                    "start_date": prior_start.isoformat(),
                    "end_date": prior_end.isoformat(),
                    "total_revenue": round(prior_revenue, 2),
                    "gross_profit": round(prior_revenue - prior_cogs, 2),
                    "total_expenses": round(prior_expenses, 2),
                    "net_income": round(prior_revenue - prior_cogs - prior_expenses, 2)
                }

            if compare_prior_year:
                py_start = date(s_date.year - 1, s_date.month, s_date.day)
                py_end = date(e_date.year - 1, e_date.month, e_date.day)

                py_revenue = sum(
                    self._get_account_balance_for_period(a["account_id"], py_start, py_end)
                    for a in revenue_accounts
                )
                py_cogs = sum(
                    self._get_account_balance_for_period(a["account_id"], py_start, py_end)
                    for a in cogs_accounts
                )
                py_expenses = sum(
                    self._get_account_balance_for_period(a["account_id"], py_start, py_end)
                    for a in expense_accounts
                )

                comparison["prior_year"] = {
                    "start_date": py_start.isoformat(),
                    "end_date": py_end.isoformat(),
                    "total_revenue": round(py_revenue, 2),
                    "gross_profit": round(py_revenue - py_cogs, 2),
                    "total_expenses": round(py_expenses, 2),
                    "net_income": round(py_revenue - py_cogs - py_expenses, 2)
                }

        # Monthly breakdown if requested
        monthly_data = None
        if group_by_month:
            monthly_data = self._get_monthly_breakdown(
                s_date, e_date, revenue_accounts, cogs_accounts, expense_accounts
            )

        return {
            "report_type": "Profit & Loss Statement",
            "period_start": start_date,
            "period_end": end_date,
            "generated_at": datetime.now().isoformat(),
            "revenue": {
                "accounts": sorted(revenue_accounts, key=lambda a: a["account_number"]),
                "total": round(total_revenue, 2)
            },
            "cost_of_goods_sold": {
                "accounts": sorted(cogs_accounts, key=lambda a: a["account_number"]),
                "total": round(total_cogs, 2)
            },
            "gross_profit": round(gross_profit, 2),
            "gross_margin_percent": round((gross_profit / total_revenue * 100) if total_revenue > 0 else 0, 2),
            "operating_expenses": {
                "accounts": sorted(expense_accounts, key=lambda a: a["account_number"]),
                "total": round(total_expenses, 2)
            },
            "net_income": round(net_income, 2),
            "net_margin_percent": round((net_income / total_revenue * 100) if total_revenue > 0 else 0, 2),
            "comparison": comparison,
            "monthly_breakdown": monthly_data
        }

    def _get_account_balance_for_period(
        self,
        account_id: str,
        start_date: date,
        end_date: date,
        class_id: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> float:
        """Get account balance for a specific period"""
        balance = 0.0

        # Get account info
        account = genfin_core_service.get_account(account_id)
        if not account:
            return 0.0

        # Query journal entries for this period
        with genfin_core_service._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT l.debit, l.credit, l.class_id, l.location_id
                FROM genfin_journal_entry_lines l
                JOIN genfin_journal_entries e ON l.entry_id = e.entry_id
                WHERE l.account_id = ?
                AND e.status IN ('posted', 'reconciled')
                AND e.entry_date >= ?
                AND e.entry_date <= ?
            """
            params = [account_id, start_date.isoformat(), end_date.isoformat()]

            if class_id:
                query += " AND l.class_id = ?"
                params.append(class_id)
            if location_id:
                query += " AND l.location_id = ?"
                params.append(location_id)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                if account["account_type"] == "revenue":
                    balance += (row['credit'] or 0) - (row['debit'] or 0)
                elif account["account_type"] == "expense":
                    balance += (row['debit'] or 0) - (row['credit'] or 0)

        return round(balance, 2)

    def _get_monthly_breakdown(
        self,
        start_date: date,
        end_date: date,
        revenue_accounts: List,
        cogs_accounts: List,
        expense_accounts: List
    ) -> List[Dict]:
        """Get monthly P&L breakdown"""
        months = []
        current = date(start_date.year, start_date.month, 1)

        while current <= end_date:
            # End of month
            if current.month == 12:
                month_end = date(current.year, 12, 31)
            else:
                month_end = date(current.year, current.month + 1, 1) - timedelta(days=1)

            if month_end > end_date:
                month_end = end_date

            month_revenue = sum(
                self._get_account_balance_for_period(a["account_id"], current, month_end)
                for a in revenue_accounts
            )
            month_cogs = sum(
                self._get_account_balance_for_period(a["account_id"], current, month_end)
                for a in cogs_accounts
            )
            month_expenses = sum(
                self._get_account_balance_for_period(a["account_id"], current, month_end)
                for a in expense_accounts
            )

            months.append({
                "month": current.strftime("%Y-%m"),
                "month_name": current.strftime("%B %Y"),
                "revenue": round(month_revenue, 2),
                "cogs": round(month_cogs, 2),
                "gross_profit": round(month_revenue - month_cogs, 2),
                "expenses": round(month_expenses, 2),
                "net_income": round(month_revenue - month_cogs - month_expenses, 2)
            })

            # Next month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

        return months

    # ==================== BALANCE SHEET ====================

    def get_balance_sheet(
        self,
        as_of_date: str = None,
        compare_prior_period: bool = False,
        compare_prior_year: bool = False
    ) -> Dict:
        """Generate Balance Sheet"""
        # Handle null date with sensible default
        if as_of_date is None:
            as_of_date = date.today().isoformat()

        report_date = datetime.strptime(as_of_date, "%Y-%m-%d").date()

        # Get all accounts with balances
        assets = {"current": [], "fixed": [], "other": []}
        liabilities = {"current": [], "long_term": []}
        equity = []

        total_assets = 0.0
        total_liabilities = 0.0
        total_equity = 0.0

        # Get all active accounts
        all_accounts = genfin_core_service.list_accounts(active_only=True, include_balances=False)

        for account in all_accounts:
            balance = genfin_core_service.get_account_balance(account["account_id"], as_of_date)

            if balance == 0:
                continue

            entry = {
                "account_id": account["account_id"],
                "account_number": account["account_number"],
                "account_name": account["name"],
                "balance": balance
            }

            account_type = account["account_type"]
            sub_type = account["sub_type"]

            if account_type == "asset":
                total_assets += balance
                if sub_type in ["cash", "bank", "accounts_receivable", "inventory", "prepaid_expense"]:
                    assets["current"].append(entry)
                elif sub_type in ["fixed_asset", "accumulated_depreciation"]:
                    assets["fixed"].append(entry)
                else:
                    assets["other"].append(entry)

            elif account_type == "liability":
                total_liabilities += balance
                if sub_type in ["accounts_payable", "credit_card", "short_term_loan",
                               "payroll_liability", "sales_tax_payable"]:
                    liabilities["current"].append(entry)
                else:
                    liabilities["long_term"].append(entry)

            elif account_type == "equity":
                total_equity += balance
                equity.append(entry)

        # Calculate retained earnings (Net Income for the year)
        year_start = date(report_date.year, 1, 1)
        ytd_income = self._calculate_net_income(year_start, report_date)

        if ytd_income != 0:
            equity.append({
                "account_id": "ytd_income",
                "account_number": "3999",
                "account_name": "Current Year Earnings",
                "balance": round(ytd_income, 2)
            })
            total_equity += ytd_income

        # Comparison data
        comparison = None
        if compare_prior_period or compare_prior_year:
            comparison = {}

            if compare_prior_year:
                py_date = date(report_date.year - 1, report_date.month, report_date.day)
                py_assets = 0.0
                py_liabilities = 0.0

                for account in all_accounts:
                    balance = genfin_core_service.get_account_balance(account["account_id"], py_date.isoformat())
                    if account["account_type"] == "asset":
                        py_assets += balance
                    elif account["account_type"] == "liability":
                        py_liabilities += balance

                comparison["prior_year"] = {
                    "date": py_date.isoformat(),
                    "total_assets": round(py_assets, 2),
                    "total_liabilities": round(py_liabilities, 2),
                    "total_equity": round(py_assets - py_liabilities, 2)
                }

        return {
            "report_type": "Balance Sheet",
            "as_of_date": as_of_date,
            "generated_at": datetime.now().isoformat(),
            "assets": {
                "current_assets": {
                    "accounts": sorted(assets["current"], key=lambda a: a["account_number"]),
                    "total": round(sum(a["balance"] for a in assets["current"]), 2)
                },
                "fixed_assets": {
                    "accounts": sorted(assets["fixed"], key=lambda a: a["account_number"]),
                    "total": round(sum(a["balance"] for a in assets["fixed"]), 2)
                },
                "other_assets": {
                    "accounts": sorted(assets["other"], key=lambda a: a["account_number"]),
                    "total": round(sum(a["balance"] for a in assets["other"]), 2)
                },
                "total": round(total_assets, 2)
            },
            "liabilities": {
                "current_liabilities": {
                    "accounts": sorted(liabilities["current"], key=lambda a: a["account_number"]),
                    "total": round(sum(a["balance"] for a in liabilities["current"]), 2)
                },
                "long_term_liabilities": {
                    "accounts": sorted(liabilities["long_term"], key=lambda a: a["account_number"]),
                    "total": round(sum(a["balance"] for a in liabilities["long_term"]), 2)
                },
                "total": round(total_liabilities, 2)
            },
            "equity": {
                "accounts": sorted(equity, key=lambda a: a["account_number"]),
                "total": round(total_equity, 2)
            },
            "total_liabilities_and_equity": round(total_liabilities + total_equity, 2),
            "is_balanced": abs(total_assets - (total_liabilities + total_equity)) < 0.01,
            "comparison": comparison
        }

    def _calculate_net_income(self, start_date: date, end_date: date) -> float:
        """Calculate net income for a period"""
        total_revenue = 0.0
        total_expenses = 0.0

        all_accounts = genfin_core_service.list_accounts(active_only=True)

        for account in all_accounts:
            if account["account_type"] == "revenue":
                total_revenue += self._get_account_balance_for_period(
                    account["account_id"], start_date, end_date
                )
            elif account["account_type"] == "expense":
                total_expenses += self._get_account_balance_for_period(
                    account["account_id"], start_date, end_date
                )

        return total_revenue - total_expenses

    # ==================== CASH FLOW ====================

    def get_cash_flow(self, start_date: str = None, end_date: str = None) -> Dict:
        """Generate Cash Flow Statement"""
        # Handle null dates with sensible defaults
        if start_date is None:
            start_date = date(date.today().year, 1, 1).isoformat()
        if end_date is None:
            end_date = date.today().isoformat()

        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Get beginning and ending cash balances
        beginning_cash = 0.0
        ending_cash = 0.0

        all_accounts = genfin_core_service.list_accounts(active_only=True)

        for account in all_accounts:
            if account["sub_type"] in ["cash", "bank"]:
                # Beginning balance (day before start)
                prev_day = s_date - timedelta(days=1)
                beginning_cash += genfin_core_service.get_account_balance(
                    account["account_id"], prev_day.isoformat()
                )
                # Ending balance
                ending_cash += genfin_core_service.get_account_balance(
                    account["account_id"], end_date
                )

        # Operating activities
        net_income = self._calculate_net_income(s_date, e_date)

        # Adjustments for non-cash items
        depreciation = 0.0
        for account in all_accounts:
            if account["sub_type"] == "depreciation":
                depreciation += self._get_account_balance_for_period(
                    account["account_id"], s_date, e_date
                )

        # Changes in working capital
        ar_change = self._get_balance_change("accounts_receivable", s_date, e_date)
        inventory_change = self._get_balance_change("inventory", s_date, e_date)
        prepaid_change = self._get_balance_change("prepaid_expense", s_date, e_date)
        ap_change = self._get_balance_change("accounts_payable", s_date, e_date)
        accrued_change = self._get_balance_change("payroll_liability", s_date, e_date)

        operating_cash_flow = (
            net_income +
            depreciation -
            ar_change -
            inventory_change -
            prepaid_change +
            ap_change +
            accrued_change
        )

        # Investing activities
        fixed_asset_change = self._get_balance_change("fixed_asset", s_date, e_date)
        investing_cash_flow = -fixed_asset_change  # Purchases are negative

        # Financing activities
        loan_change = (
            self._get_balance_change("short_term_loan", s_date, e_date) +
            self._get_balance_change("long_term_loan", s_date, e_date)
        )
        equity_change = self._get_balance_change("owner_equity", s_date, e_date)
        draws = self._get_balance_change("owner_draw", s_date, e_date)

        financing_cash_flow = loan_change + equity_change - draws

        # Net change
        net_change = operating_cash_flow + investing_cash_flow + financing_cash_flow

        return {
            "report_type": "Cash Flow Statement",
            "period_start": start_date,
            "period_end": end_date,
            "generated_at": datetime.now().isoformat(),
            "beginning_cash": round(beginning_cash, 2),
            "operating_activities": {
                "net_income": round(net_income, 2),
                "adjustments": {
                    "depreciation": round(depreciation, 2),
                    "ar_change": round(-ar_change, 2),
                    "inventory_change": round(-inventory_change, 2),
                    "prepaid_change": round(-prepaid_change, 2),
                    "ap_change": round(ap_change, 2),
                    "accrued_liabilities_change": round(accrued_change, 2)
                },
                "total": round(operating_cash_flow, 2)
            },
            "investing_activities": {
                "fixed_asset_purchases": round(-fixed_asset_change if fixed_asset_change > 0 else 0, 2),
                "fixed_asset_sales": round(-fixed_asset_change if fixed_asset_change < 0 else 0, 2),
                "total": round(investing_cash_flow, 2)
            },
            "financing_activities": {
                "loan_proceeds": round(loan_change if loan_change > 0 else 0, 2),
                "loan_payments": round(-loan_change if loan_change < 0 else 0, 2),
                "equity_contributions": round(equity_change if equity_change > 0 else 0, 2),
                "owner_draws": round(-draws, 2),
                "total": round(financing_cash_flow, 2)
            },
            "net_change_in_cash": round(net_change, 2),
            "ending_cash": round(ending_cash, 2),
            "reconciliation_check": round(beginning_cash + net_change, 2)
        }

    def _get_balance_change(self, sub_type: str, start_date: date, end_date: date) -> float:
        """Get change in balance for accounts of a specific subtype"""
        change = 0.0
        prev_day = start_date - timedelta(days=1)

        all_accounts = genfin_core_service.list_accounts(active_only=True)

        for account in all_accounts:
            if account["sub_type"] == sub_type:
                beginning = genfin_core_service.get_account_balance(
                    account["account_id"], prev_day.isoformat()
                )
                ending = genfin_core_service.get_account_balance(
                    account["account_id"], end_date.isoformat()
                )
                change += ending - beginning

        return round(change, 2)

    # ==================== OTHER REPORTS ====================

    def get_trial_balance(self, as_of_date: str) -> Dict:
        """Generate Trial Balance"""
        return genfin_core_service.get_trial_balance(as_of_date)

    def get_general_ledger(
        self,
        start_date: str,
        end_date: str,
        account_ids: List[str] = None
    ) -> Dict:
        """Generate General Ledger report"""
        accounts_data = []

        if account_ids:
            accounts_to_include = account_ids
        else:
            all_accounts = genfin_core_service.list_accounts(active_only=True)
            accounts_to_include = [a["account_id"] for a in all_accounts]

        for account_id in accounts_to_include:
            ledger = genfin_core_service.get_account_ledger(account_id, start_date, end_date)
            if "error" not in ledger:
                accounts_data.append(ledger)

        return {
            "report_type": "General Ledger",
            "period_start": start_date,
            "period_end": end_date,
            "generated_at": datetime.now().isoformat(),
            "accounts": sorted(accounts_data, key=lambda a: a["account"]["account_number"])
        }

    def get_income_by_customer(self, start_date: str, end_date: str) -> Dict:
        """Get income breakdown by customer"""
        from .genfin_receivables_service import genfin_receivables_service

        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        customer_income = {}

        # Use list method instead of direct dict access
        invoices = genfin_receivables_service.list_invoices(start_date=start_date, end_date=end_date)

        for invoice in invoices:
            if invoice.get("status") == "voided":
                continue

            cust_id = invoice.get("customer_id")
            if cust_id not in customer_income:
                customer = genfin_receivables_service.get_customer(cust_id)
                customer_income[cust_id] = {
                    "customer_id": cust_id,
                    "customer_name": customer.get("display_name", "Unknown") if customer else "Unknown",
                    "invoice_count": 0,
                    "total_sales": 0.0
                }

            customer_income[cust_id]["invoice_count"] += 1
            customer_income[cust_id]["total_sales"] += invoice.get("total", 0)

        results = sorted(
            customer_income.values(),
            key=lambda x: x["total_sales"],
            reverse=True
        )

        return {
            "report_type": "Income by Customer",
            "period_start": start_date,
            "period_end": end_date,
            "generated_at": datetime.now().isoformat(),
            "customers": results,
            "total_income": round(sum(c["total_sales"] for c in results), 2)
        }

    def get_expenses_by_vendor(self, start_date: str, end_date: str) -> Dict:
        """Get expense breakdown by vendor"""
        from .genfin_payables_service import genfin_payables_service

        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        vendor_expenses = {}

        # Use list method instead of direct dict access
        bills = genfin_payables_service.list_bills(start_date=start_date, end_date=end_date)

        for bill in bills:
            if bill.get("status") == "voided":
                continue

            vendor_id = bill.get("vendor_id")
            if vendor_id not in vendor_expenses:
                vendor = genfin_payables_service.get_vendor(vendor_id)
                vendor_expenses[vendor_id] = {
                    "vendor_id": vendor_id,
                    "vendor_name": vendor.get("display_name", "Unknown") if vendor else "Unknown",
                    "bill_count": 0,
                    "total_expenses": 0.0
                }

            vendor_expenses[vendor_id]["bill_count"] += 1
            vendor_expenses[vendor_id]["total_expenses"] += bill.get("total", 0)

        results = sorted(
            vendor_expenses.values(),
            key=lambda x: x["total_expenses"],
            reverse=True
        )

        return {
            "report_type": "Expenses by Vendor",
            "period_start": start_date,
            "period_end": end_date,
            "generated_at": datetime.now().isoformat(),
            "vendors": results,
            "total_expenses": round(sum(v["total_expenses"] for v in results), 2)
        }

    def get_account_transactions(
        self,
        account_id: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """Get all transactions for an account"""
        return genfin_core_service.get_account_ledger(account_id, start_date, end_date)

    # ==================== FINANCIAL RATIOS ====================

    def get_financial_ratios(self, as_of_date: str) -> Dict:
        """Calculate key financial ratios"""
        report_date = datetime.strptime(as_of_date, "%Y-%m-%d").date()
        year_start = date(report_date.year, 1, 1)

        # Get balance sheet data
        current_assets = 0.0
        inventory = 0.0
        total_assets = 0.0
        current_liabilities = 0.0
        total_liabilities = 0.0
        total_equity = 0.0

        all_accounts = genfin_core_service.list_accounts(active_only=True)

        for account in all_accounts:
            balance = genfin_core_service.get_account_balance(account["account_id"], as_of_date)

            if account["account_type"] == "asset":
                total_assets += balance
                if account["sub_type"] in ["cash", "bank", "accounts_receivable",
                                           "inventory", "prepaid_expense"]:
                    current_assets += balance
                    if account["sub_type"] == "inventory":
                        inventory += balance

            elif account["account_type"] == "liability":
                total_liabilities += balance
                if account["sub_type"] in ["accounts_payable", "credit_card",
                                           "short_term_loan", "payroll_liability"]:
                    current_liabilities += balance

            elif account["account_type"] == "equity":
                total_equity += balance

        # Get P&L data
        net_income = self._calculate_net_income(year_start, report_date)
        total_revenue = sum(
            self._get_account_balance_for_period(a["account_id"], year_start, report_date)
            for a in all_accounts
            if a["account_type"] == "revenue"
        )

        # Calculate ratios
        current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
        quick_ratio = (current_assets - inventory) / current_liabilities if current_liabilities > 0 else 0
        debt_to_equity = total_liabilities / total_equity if total_equity > 0 else 0
        debt_ratio = total_liabilities / total_assets if total_assets > 0 else 0
        profit_margin = (net_income / total_revenue * 100) if total_revenue > 0 else 0
        roa = (net_income / total_assets * 100) if total_assets > 0 else 0
        roe = (net_income / total_equity * 100) if total_equity > 0 else 0

        return {
            "report_type": "Financial Ratios",
            "as_of_date": as_of_date,
            "generated_at": datetime.now().isoformat(),
            "liquidity_ratios": {
                "current_ratio": round(current_ratio, 2),
                "current_ratio_status": "Good" if current_ratio >= 1.5 else "Caution" if current_ratio >= 1.0 else "Poor",
                "quick_ratio": round(quick_ratio, 2),
                "quick_ratio_status": "Good" if quick_ratio >= 1.0 else "Caution" if quick_ratio >= 0.5 else "Poor"
            },
            "leverage_ratios": {
                "debt_to_equity": round(debt_to_equity, 2),
                "debt_ratio": round(debt_ratio, 2),
                "debt_ratio_percent": round(debt_ratio * 100, 1)
            },
            "profitability_ratios": {
                "profit_margin_percent": round(profit_margin, 2),
                "return_on_assets_percent": round(roa, 2),
                "return_on_equity_percent": round(roe, 2)
            },
            "underlying_data": {
                "current_assets": round(current_assets, 2),
                "current_liabilities": round(current_liabilities, 2),
                "total_assets": round(total_assets, 2),
                "total_liabilities": round(total_liabilities, 2),
                "total_equity": round(total_equity, 2),
                "net_income_ytd": round(net_income, 2),
                "total_revenue_ytd": round(total_revenue, 2)
            }
        }

    # ==================== SAVED REPORTS ====================

    def save_report_config(
        self,
        name: str,
        report_type: str,
        parameters: Dict,
        created_by: str,
        is_scheduled: bool = False,
        schedule_frequency: str = ""
    ) -> Dict:
        """Save a report configuration"""
        report_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_saved_reports
                (report_id, name, report_type, parameters, created_by, is_scheduled, schedule_frequency, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (report_id, name, report_type, json.dumps(parameters), created_by,
                  1 if is_scheduled else 0, schedule_frequency, now))
            conn.commit()

        return {
            "success": True,
            "report_id": report_id,
            "name": name
        }

    def run_saved_report(self, report_id: str) -> Dict:
        """Run a saved report"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_saved_reports WHERE report_id = ?", (report_id,))
            row = cursor.fetchone()

            if not row:
                return {"error": "Saved report not found"}

            report_type = row['report_type']
            params = json.loads(row['parameters'])

            # Update last_run
            cursor.execute("""
                UPDATE genfin_saved_reports SET last_run = ? WHERE report_id = ?
            """, (datetime.now().isoformat(), report_id))
            conn.commit()

        if report_type == "profit_loss":
            return self.get_profit_loss(**params)
        elif report_type == "balance_sheet":
            return self.get_balance_sheet(**params)
        elif report_type == "cash_flow":
            return self.get_cash_flow(**params)
        elif report_type == "trial_balance":
            return self.get_trial_balance(**params)
        else:
            return {"error": "Unknown report type"}

    def list_saved_reports(self) -> List[Dict]:
        """List all saved reports"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_saved_reports")
            rows = cursor.fetchall()

            return [
                {
                    "report_id": row['report_id'],
                    "name": row['name'],
                    "report_type": row['report_type'],
                    "is_scheduled": bool(row['is_scheduled']),
                    "schedule_frequency": row['schedule_frequency'],
                    "last_run": row['last_run'],
                    "created_by": row['created_by'],
                    "created_at": row['created_at']
                }
                for row in rows
            ]

    def get_service_summary(self) -> Dict:
        """Get GenFin Reports service summary"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM genfin_saved_reports")
            saved_reports_count = cursor.fetchone()['count']

        return {
            "service": "GenFin Reports",
            "version": "1.0.0",
            "available_reports": [
                "Profit & Loss Statement",
                "Balance Sheet",
                "Cash Flow Statement",
                "Trial Balance",
                "General Ledger",
                "Income by Customer",
                "Expenses by Vendor",
                "Financial Ratios",
                "Account Transactions"
            ],
            "features": [
                "Comparative Reporting (Prior Period/Year)",
                "Monthly Breakdown",
                "Class/Location Filtering",
                "Saved Report Configurations",
                "Scheduled Reports"
            ],
            "saved_reports_count": saved_reports_count
        }


# Singleton instance
genfin_reports_service = GenFinReportsService()
